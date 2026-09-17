import Foundation
import EssentialsCore

@main struct GuidedLessonChecks {
    static func main() throws {
        guard CommandLine.arguments.count == 3 else {
            throw EssentialsError.invalid("Pass bundled resource directory and guided lesson catalog path.")
        }
        let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        let catalogURL = URL(fileURLWithPath: CommandLine.arguments[2])
        var checks = 0
        func check(_ value: Bool, _ message: String) throws {
            guard value else { throw EssentialsError.invalid("FAIL: " + message) }
            checks += 1; print("PASS \(checks): " + message)
        }
        let catalog = try GuidedLessonCatalog.read(from: catalogURL)
        try check(catalog.lessons.map(\.stage) == Array(1...8), "The tour contains each component exactly once")
        var records: [Int: ActionComparisonRecord] = [:]
        for lesson in catalog.lessons {
            let record = try ActionComparisonRecord.read(from: root.appendingPathComponent(lesson.scriptedFile))
            _ = try record.verify(); records[lesson.stage] = record
            try check(lesson.checkpoints.allSatisfy { $0 <= record.stepCount }, "Stage \(lesson.stage) checkpoints exist in its verified recording")
            if lesson.stage >= 4 {
                try check(lesson.file(for: .recordedModel) != lesson.scriptedFile, "Stage \(lesson.stage) has an explicit model alternative")
            } else {
                try check(lesson.file(for: .recordedModel) == lesson.scriptedFile && !lesson.actionStage.hasJournal,
                    "Stage \(lesson.stage) remains a numerical, journal-free lesson")
            }
        }
        func evidence(_ stage: Int, _ step: Int) -> LessonEvidence {
            GuidedEvidenceEvaluator.evaluate(records[stage], cursorStep: step)
        }
        try check(GuidedEvidenceEvaluator.evaluate(nil, cursorStep: 0).state == .notYetObserved,
            "An unopened lesson makes no observed claim")
        try check(evidence(1, 13).observation.contains("quiet") && evidence(1, 13).observation.contains("lower"),
            "A derives quiet input and decay from the visible frame pair")
        try check(evidence(2, 1).state == .notYetObserved && evidence(2, 2).evidenceSteps == [2],
            "B reveals the first matched difference only at step two")
        try check(evidence(3, 30).observation.contains("Reservoir states still match"),
            "C identifies measured sensory evidence with unchanged matched state")
        try check(evidence(4, 29).state == .notYetObserved && evidence(4, 30).state == .observed,
            "D cannot expose the journal before its opportunity")
        try check(evidence(5, 30).state == .notYetObserved && evidence(5, 30).evidenceSteps == [30],
            "E does not claim its future application at the saving cursor")
        try check(evidence(5, 31).evidenceSteps == [30, 31] && evidence(5, 31).observation.contains("First state difference: step 31"),
            "E links save, next-step application and observed divergence")
        try check(evidence(6, 59).state == .notYetObserved && evidence(6, 60).evidenceSteps == [30, 60],
            "F reveals exact memory inclusion at the later prompt only")
        try check(!evidence(6, 60).observation.contains("submitted model"),
            "Fixed scripted context does not claim submission to a model")
        try check(!evidence(7, 89).observation.contains("WAIT was chosen") && evidence(7, 90).observation.contains("WAIT was chosen"),
            "G hides the future WAIT result until its recorded boundary")
        try check(evidence(8, 120).observation.contains("retention limit") && evidence(8, 120).observation.contains("remain matched"),
            "H reports controller limits without inventing a reservoir-state effect")
        var missingArm = records[2]!
        missingArm.left = nil
        try check(GuidedEvidenceEvaluator.evaluate(missingArm, cursorStep: 30).state == .notApplicable,
            "A missing matched arm cannot establish a recurrence effect")
        var failedSave = records[4]!
        failedSave.right.actions[0].status = .failed
        failedSave.right.actions[0].saveReceipt = JournalSaveReceipt(status: .failed, entryID: "failed", sha256: "", relativePath: nil, failure: "disk unavailable")
        failedSave.right.actions[0].journalEntryID = nil
        try check(GuidedEvidenceEvaluator.evaluate(failedSave, cursorStep: 30).state == .incomplete,
            "A failed journal save cannot satisfy the journal lesson")
        var corruptObject = try JSONSerialization.jsonObject(with: JSONEncoder().encode(records[6]!)) as! [String: Any]
        var corruptRight = corruptObject["right"] as! [String: Any]
        var corruptActions = corruptRight["actions"] as! [[String: Any]]
        corruptActions[1]["memoryText"] = "Altered memory"
        corruptRight["actions"] = corruptActions; corruptObject["right"] = corruptRight
        let corrupt = try JSONDecoder().decode(ActionComparisonRecord.self, from: JSONSerialization.data(withJSONObject: corruptObject))
        try check(GuidedEvidenceEvaluator.evaluate(corrupt, cursorStep: 60).state == .incomplete,
            "The memory lesson checks exact earlier text, not only a memory flag")
        let modelG = try ActionComparisonRecord.read(from: root.appendingPathComponent("example-model-7.json"))
        _ = try modelG.verify()
        let actualChoice = GuidedEvidenceEvaluator.evaluate(modelG, cursorStep: 90)
        try check(actualChoice.state == .observed && actualChoice.observation.contains("No WAIT has occurred"),
            "All-WRITE recorded model outcomes remain valid observations")
        let modelD = try ActionComparisonRecord.read(from: root.appendingPathComponent("example-model-4.json"))
        try check(GuidedEvidenceEvaluator.evaluate(modelD, cursorStep: 30).observation.contains("no control arm"),
            "A single model recording is not presented as a controlled state effect")
        let regulation = try RegulationExampleRecord.read(from: root.appendingPathComponent("example-regulation-controller.json"))
        _ = try regulation.verify()
        try check(RegulationWindowEvidence.evaluate(regulation, cursorStep: 300) == nil,
            "No evaluation-window result leaks before step 301")
        let first = RegulationWindowEvidence.evaluate(regulation, cursorStep: 301)!
        try check(first.count == 1 && !first.isComplete && first.lastStep == 301,
            "The initial partial evaluation contains exactly one visible observation")
        let partial = RegulationWindowEvidence.evaluate(regulation, cursorStep: 450)!
        try check(partial.count == 150 && !partial.isComplete && partial.lastStep == 450,
            "Partial target-error summaries use only the visible prefix")
        let complete = RegulationWindowEvidence.evaluate(regulation, cursorStep: 600)!
        try check(complete.count == 300 && complete.isComplete
            && abs(complete.baselineMeanAbsoluteError - regulation.summary.baselineMeanAbsoluteError) < 1e-10
            && abs(complete.regulatedMeanAbsoluteError - regulation.summary.regulatedMeanAbsoluteError) < 1e-10,
            "The complete visible window agrees with the verified record summary")
        print("Guided lessons: \(checks) checks passed. No provider calls.")
    }
}
