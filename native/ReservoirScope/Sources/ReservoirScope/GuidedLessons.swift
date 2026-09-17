import Foundation
import EssentialsCore

enum GuidedExampleSource: String, Codable, CaseIterable, Identifiable {
    case scripted, recordedModel
    var id: Self { self }
    var title: String { self == .scripted ? "Scripted example" : "Recorded model run" }
}

enum LessonFocus: String, Codable {
    case inputState, recurrence, sensory, journal, feedback, memory, choice, regulation
}

struct GuidedLesson: Decodable, Identifiable {
    var id: Int { stage }
    let stage: Int
    let title: String
    let question: String
    let suggestedAction: String
    let expected: String
    let modelExpected: String
    let limitation: String
    let focus: LessonFocus
    let checkpoints: [Int]
    let scriptedFile: String
    let modelFile: String?
    var actionStage: ActionStage { ActionStage(rawValue: stage)! }
    func file(for source: GuidedExampleSource) -> String? { source == .recordedModel && stage >= 4 ? modelFile : scriptedFile }
}

struct GuidedLessonCatalog: Decodable {
    static let currentFormat = "reservoir-guided-lessons-v1"
    let format: String
    let lessons: [GuidedLesson]
    static func read(from url: URL) throws -> Self {
        let value = try JSONDecoder().decode(Self.self, from: Data(contentsOf: url))
        guard value.format == currentFormat, value.lessons.map(\.stage) == Array(1...8),
              value.lessons.allSatisfy({ lesson in
                  !lesson.question.isEmpty && !lesson.expected.isEmpty && !lesson.limitation.isEmpty
                  && (lesson.stage < 4 || lesson.modelFile != nil)
                  && !lesson.checkpoints.isEmpty && lesson.checkpoints == Array(Set(lesson.checkpoints)).sorted()
                  && lesson.checkpoints.allSatisfy { (1...600).contains($0) }
                  && [lesson.scriptedFile, lesson.modelFile].compactMap { $0 }.allSatisfy {
                      !$0.contains("/") && !$0.contains("..") && $0.hasSuffix(".json")
                  }
              }) else { throw NSError(domain: "GuidedLessons", code: 1,
                  userInfo: [NSLocalizedDescriptionKey: "The packaged lesson catalog is invalid."]) }
        return value
    }
}

enum LessonEvidenceState: String {
    case notYetObserved = "Not reached yet", observed = "Observed", differentResult = "Different outcome"
    case incomplete = "Incomplete evidence", notApplicable = "No matched comparison"
}
struct LessonEvidence {
    let state: LessonEvidenceState
    let observation: String
    let evidenceSteps: [Int]
}

/// Derives mechanical observations from the verified record prefix only. It never
/// judges prose quality or reads a later frame, action, journal or application.
enum GuidedEvidenceEvaluator {
    static let tolerance = 1e-12
    static func rms(_ values: [Double]) -> Double {
        values.isEmpty ? 0 : sqrt(values.reduce(0) { $0 + $1 * $1 } / Double(values.count))
    }
    static func delta(_ a: [Double], _ b: [Double]) -> Double {
        guard a.count == b.count else { return .infinity }
        return rms(zip(a, b).map { $1 - $0 })
    }
    static func evaluate(_ record: ActionComparisonRecord?, cursorStep: Int) -> LessonEvidence {
        guard let record, cursorStep > 0,
              let frame = record.right.frames.last(where: { $0.step <= cursorStep }) else {
            return result(.notYetObserved, "Open an example to inspect recorded evidence.")
        }
        let step = frame.step
        let right = record.right.frames.filter { $0.step <= step }
        let left = record.left?.frames.filter { $0.step <= step } ?? []
        let paired = !left.isEmpty && left.count == right.count && zip(left, right).allSatisfy { $0.step == $1.step }
        let firstDifference = paired ? zip(left, right).first(where: { delta($0.state, $1.state) > tolerance })?.1.step : nil
        let actions = record.right.actions.filter { $0.observedStep <= step }
        let saved = actions.filter { $0.status == .completed && $0.saveReceipt?.status == .saved }
        let journals = record.right.journals.filter { $0.observedStep <= step }
        if record.specification.comparisonKind == .observation {
            guard paired else { return result(.incomplete, "Both observation arms are required.") }
            let rightAction = actions.last
            let leftAction = record.left?.actions.last { $0.observedStep <= step }
            if let a = rightAction, let b = leftAction {
                let complete = a.status == .completed && b.status == .completed
                return result(complete ? .observed : .incomplete,
                    "States \(firstDifference == nil ? "match" : "differ") through step \(step). Opportunity \(a.observedStep): sensory arm \(b.status.rawValue), added-state arm \(a.status.rawValue). Different wording is not an improvement score.", [a.observedStep])
            }
            return result(.notYetObserved, "States match through step \(step); no writing opportunity has been reached.")
        }
        switch record.specification.stage {
        case .minimal:
            let quiet = rms(frame.externalInput) <= tolerance
            let previous = right.dropLast().last
            let decaying = quiet && previous.map { rms(frame.state) < rms($0.state) } == true
            return result(.observed, "Input is \(quiet ? "quiet" : "active"). State magnitude is \(number(rms(frame.state))).\(decaying ? " It is lower than at the preceding step." : "")", [step])
        case .recurrence:
            guard paired else { return result(.notApplicable, "This recording has one arm; a matched comparison is needed to isolate recurrence.", [step]) }
            if let firstDifference { return result(.observed, "The first state difference is at step \(firstDifference); matched inputs are retained.", [firstDifference]) }
            return result(step < 2 ? .notYetObserved : .differentResult, "The two recorded states still match through step \(step).", [step])
        case .sensoryObserver:
            guard frame.spectral != nil else { return result(.incomplete, "This step has no sensory measurement.", [step]) }
            return result(.observed, "A separate sensory spectrum is recorded at step \(step). " + (paired ? (firstDifference == nil ? "Reservoir states still match." : "Reservoir states differ; inspect the setup.") : "This is a single recorded arm."), [step])
        case .journalOutput:
            guard let action = actions.last else { return beforeJournal(step) }
            guard saved.contains(where: { $0.id == action.id }) else { return failedOrPending(action) }
            return result(.observed, "A journal was saved at step \(action.observedStep). " + (paired ? (firstDifference == nil ? "Writing has left the matched reservoir states unchanged." : "States differ; this recording does not isolate unchanged state.") : "There is no control arm for a state-effect comparison."), [action.observedStep])
        case .reservoirReturn:
            guard let action = saved.first(where: { $0.semanticVector != nil }) else {
                return actions.last.map(failedOrPending) ?? beforeJournal(step)
            }
            guard let applied = action.applicationStep, applied <= step else {
                return result(.notYetObserved, "Journal saved at \(action.observedStep); its return has not been applied at this cursor. Step forward to inspect the application.", [action.observedStep])
            }
            guard right.contains(where: { $0.step == applied && $0.semanticActionID == action.id }) else {
                return result(.incomplete, "The application receipt has no matching input frame.", [applied])
            }
            return result(.observed, "Journal saved at \(action.observedStep), first applied at \(applied). " + (paired ? firstDifference.map { "First state difference: step \($0)." } ?? "States still match through this cursor." : "The application is recorded; this run has no control arm."), [action.observedStep, applied])
        case .journalMemory:
            guard let action = actions.last(where: { $0.memoryEntryID != nil }) else {
                if let failed = actions.last, failed.status != .completed { return failedOrPending(failed) }
                return result(.notYetObserved, "No earlier journal is present in the prompt at this cursor. Continue to the next writing opportunity.")
            }
            guard let prior = journals.first(where: { $0.id == action.memoryEntryID }), prior.observedStep < action.observedStep,
                  prior.text == action.memoryText, action.prompt.contains(prior.text) else {
                return result(.incomplete, "Memory metadata does not establish exact earlier-journal inclusion.", [action.observedStep])
            }
            return result(.observed, "The journal from \(prior.observedStep) is included in the \(record.specification.language.backend == .ollama ? (action.requestStarted ? "submitted model" : "prepared, unsubmitted") : "prepared/scripted") prompt at \(action.observedStep). " + (record.specification.mode == .fixedReplay ? "Replies remain fixed in this scripted comparison." : "This establishes exposure, not improved writing."), [prior.observedStep, action.observedStep])
        case .actionChoice:
            if let wait = actions.first(where: { $0.chosenAction == .wait && $0.status == .completed }) {
                return result(wait.journalEntryID == nil && wait.saveReceipt == nil ? .observed : .incomplete,
                    "WAIT was chosen at step \(wait.observedStep); \(wait.journalEntryID == nil ? "no journal was written" : "unexpected journal evidence is present"). Earlier returned input remains until a later saved journal replaces it.", [wait.observedStep])
            }
            guard !actions.isEmpty else { return beforeJournal(step) }
            if let action = actions.last, action.status != .completed { return failedOrPending(action) }
            return result(.observed, "\(actions.count) completed writing choice\(actions.count == 1 ? "" : "s") so far. No WAIT has occurred at this cursor; writing is also a valid choice.", actions.map(\.observedStep))
        case .regulation:
            guard let fill = frame.fillPercent, let retention = frame.retentionUsed, let control = frame.control else {
                return result(.incomplete, "Fill, retention and controller evidence are required.", [step])
            }
            let atLimit = abs(control.appliedRetention - 0.995) < tolerance || abs(control.appliedRetention - 0.82) < tolerance
            let difference = paired ? " Reservoir states \(firstDifference == nil ? "remain matched" : "differ")." : " This is a single recorded arm."
            return result(.observed, "Fill \(number(fill))% against 68%; retention \(number(retention, 4)), next \(number(control.appliedRetention, 4)).\(atLimit ? " The controller is at a retention limit." : "")" + difference, [step])
        }
    }
    private static func beforeJournal(_ step: Int) -> LessonEvidence {
        result(.notYetObserved, "No writing opportunity at or before step \(step).")
    }
    private static func failedOrPending(_ action: ActionReceipt) -> LessonEvidence {
        result(.incomplete, "Opportunity at \(action.observedStep): \(action.saveReceipt?.status == .failed ? "journal save failed" : action.status.rawValue). No successful saved journal is established here.", [action.observedStep])
    }
    private static func result(_ state: LessonEvidenceState, _ observation: String, _ steps: [Int] = []) -> LessonEvidence {
        LessonEvidence(state: state, observation: observation, evidenceSteps: steps)
    }
    private static func number(_ value: Double, _ digits: Int = 3) -> String { String(format: "%.*f", digits, value) }
}

struct RegulationWindowEvidence {
    let count: Int
    let firstStep: Int
    let lastStep: Int
    let isComplete: Bool
    let baselineMeanAbsoluteError: Double
    let regulatedMeanAbsoluteError: Double
    static func evaluate(_ record: RegulationExampleRecord, cursorStep: Int) -> Self? {
        let spec = record.specification
        let visible = record.frames.filter { $0.step >= spec.evaluationFirstStep && $0.step <= min(cursorStep, spec.evaluationLastStep) }
        guard let first = visible.first, let last = visible.last else { return nil }
        let n = Double(visible.count)
        return Self(count: visible.count, firstStep: first.step, lastStep: last.step,
            isComplete: last.step == spec.evaluationLastStep,
            baselineMeanAbsoluteError: visible.reduce(0) { $0 + abs($1.baseline.fillPercent - spec.targetFillPercent) } / n,
            regulatedMeanAbsoluteError: visible.reduce(0) { $0 + abs($1.regulated.fillPercent - spec.targetFillPercent) } / n)
    }
}
