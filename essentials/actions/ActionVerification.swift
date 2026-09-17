import Foundation

extension ActionComparisonRecord {
    public static func read(from url: URL) throws -> Self {
        let attributes = try url.resourceValues(forKeys: [.isRegularFileKey, .fileSizeKey])
        guard attributes.isRegularFile == true, (attributes.fileSize ?? Int.max) <= ActionRules.maximumRecordBytes else {
            throw EssentialsError.invalid("Action comparison must be a regular JSON file no larger than 256 MB.")
        }
        let data = try Data(contentsOf: url)
        guard data.count <= ActionRules.maximumRecordBytes else { throw EssentialsError.invalid("Action comparison exceeds 256 MB.") }
        let record = try JSONDecoder().decode(Self.self, from: data)
        try record.validateStructure()
        return record
    }
    public func write(to url: URL) throws {
        _ = try verify()
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        let data = try encoder.encode(self)
        guard data.count <= ActionRules.maximumRecordBytes else { throw EssentialsError.invalid("Action comparison exceeds 256 MB.") }
        try data.write(to: url, options: .atomic)
    }
    public func validateStructure() throws { try ActionComparisonVerifier.validateStructure(self) }
    @discardableResult
    public func verify() throws -> VerificationReport { try ActionComparisonVerifier.verify(self) }
}

/// Replays numeric dynamics and all recorded action effects. Provider and storage
/// receipts are historical evidence, not independently authenticated service events.
/// Verification never calls a backend or follows a saved journal path.
public enum ActionComparisonVerifier {
    public static func validateStructure(_ record: ActionComparisonRecord) throws {
        try record.specification.validate()
        try require(ActionComparisonRecord.supportedFormats.contains(record.format), "Unknown action comparison format.")
        let spec = record.specification
        let legacy = record.format == ActionComparisonRecord.legacyFormat
        try require(record.format == ActionComparisonRecord.currentFormat || spec.forcingProfile == .pulsedSensoryV1,
                    "Legacy action records cannot change the input profile.")
        try require(!legacy || (spec.comparisonKind == .components && spec.promptVersion == 1), "Legacy record cannot change observation channels.")
        for run in [record.left, record.right].compactMap({ $0 }) {
            let expected: JournalObservationChannel = spec.comparisonKind == .observation && run.arm == .right ? .sensoryAndReservoir : .sensory
            try require(legacy ? run.observationChannel == nil : run.observationChannel == expected, "Observation channel differs from declared comparison.")
            for action in run.actions {
                if legacy { try require(action.requestOrder == nil, "Legacy record contains v2 request metadata.") }
                else if action.requestStarted {
                    let rightFirst = spec.comparisonKind == .observation && action.id % 2 == 0
                    let expectedOrder = record.left?.stage.hasJournal != true ? 1 : (run.arm == (rightFirst ? .right : .left) ? 1 : 2)
                    try require(action.requestOrder == expectedOrder, "Request order differs from the declared alternating sequence.")
                } else { try require(action.requestOrder == nil, "No backend request started for the claimed order.") }
            }
        }
        try require(record.right.stage == spec.stage && record.right.arm == .right, "Right arm differs from its selected version.")
        let hasLeft = spec.comparePrevious && spec.stage.previous != nil
        try require((record.left != nil) == hasLeft, "Comparison arm availability disagrees with specification.")
        if let left = record.left {
            try require(left.stage == (spec.comparisonKind == .observation ? .journalOutput : spec.stage.previous) && left.arm == .left, "Left arm is not the preceding version.")
            try require(left.frames.count == record.right.frames.count, "Comparison arms have different step counts.")
            if left.stage.hasJournal && record.right.stage.hasJournal {
                try require(left.actions.count == record.right.actions.count,
                            "Comparison arms have different action opportunity counts.")
                for (a, b) in zip(left.actions, record.right.actions) {
                    try require(a.observedStep == b.observedStep && a.trigger == b.trigger,
                                "Comparison arms did not receive the same action opportunities.")
                    if spec.comparisonKind == .components && (a.status == .failed || a.status == .cancelled || a.failurePhase == .journalSave) {
                        try require(b.status == .cancelled && b.failurePhase == .cancelled && !b.requestStarted
                                    && b.memoryText == nil && b.rawReply == nil,
                                    "Right arm executed despite a failed or cancelled preceding left action.")
                    }
                }
            }
        }
        try require((record.tape != nil) == (spec.mode == .fixedReplay), "Replay tape availability disagrees with mode.")
        if let tape = record.tape {
            try require(tape.format == ActionReplyTape.currentFormat && tape.origin == ActionRules.tapeOrigin,
                        "Unrecognized tape format or reference origin.")
            try require(tape.seed == spec.seed && tape.inputStrength == spec.inputStrength && tape.retention == spec.initialRetention
                        && tape.turnEvery == spec.turnEvery && tape.packets.count == spec.steps - 1, "Tape reference configuration differs.")
            for (index, packet) in tape.packets.enumerated() {
                try require(packet.id == index + 1 && packet.referenceStep == packet.id, "Invalid tape reference boundary.")
                try text(packet.text, limit: ActionRules.maximumTextBytes, name: "tape text")
                try vector(packet.referenceEigenvalues, count: 32, name: "tape reference spectrum")
                try vector(packet.encodedFeatures, count: 48, name: "tape codec features")
                try vector(packet.semanticVector, count: 48, name: "tape semantic vector")
                try require(packet.encodedFeatures.suffix(16).allSatisfy { $0 == 0 }
                            && packet.semanticVector.suffix(16).allSatisfy { $0 == 0 }, "Tape populates unavailable codec features.")
            }
        }
        let arms = [record.left, record.right].compactMap { $0 }
        let failed = arms.contains { $0.status == .failed }
        let completed = arms.allSatisfy { $0.status == .completed }
        try require(record.status == (failed ? .failed : completed ? .completed : .stopped), "Comparison status disagrees with its arms.")
        try require(record.failure == (failed ? (record.left?.failure ?? record.right.failure) : nil), "Comparison failure differs from arm failure.")
        for run in arms {
            try require(run.frames.count <= spec.steps && run.actions.count <= ActionRules.maximumActions && run.journals.count <= run.actions.count,
                        "Action record exceeds configured frame/action bounds.")
            try require(run.model.nodeCount == 32 && run.model.inputCount == 66, "Invalid action reservoir dimensions.")
            try vector(run.model.recurrentWeights, count: 1024, name: "recurrent weights")
            try vector(run.model.inputWeights, count: 2144, name: "input weights")
            try vector(run.projectionWeights, count: run.stage.rawValue >= 3 ? 2112 : 0, name: "sensory projection")
            try require((run.status == .completed) == (run.frames.count == spec.steps), "Run completion disagrees with its frame count.")
            if run.status == .failed { try text(run.failure, limit: 4096, name: "run failure") }
            else { try require(run.failure == nil, "Nonfailed arm carries a failure.") }
            try require(run.stage.hasJournal || (run.actions.isEmpty && run.journals.isEmpty), "A pre-journal version contains actions.")
            for (index, frame) in run.frames.enumerated() {
                try require(frame.step == index + 1, "Action frames must be contiguous.")
                try near(frame.time, Double(frame.step) * spec.dt, "action clock")
                try vector(frame.input, count: 66, name: "actual input")
                try vector(frame.externalInput, count: 66, name: "external input")
                try vector(frame.semanticInput, count: 48, name: "semantic input")
                try require(frame.semanticInput.suffix(16).allSatisfy { $0 == 0 }, "Unavailable semantic input coordinates are nonzero.")
                try vector(frame.previousState, count: 32, name: "previous state")
                try vector(frame.state, count: 32, name: "state")
                try vector(frame.noise, count: 32, name: "noise")
                try require(frame.state.allSatisfy { abs($0) <= 1 }, "State exceeds clipping limits.")
                try require((frame.spectral != nil) == (run.stage.rawValue >= 3), "Sensory availability disagrees with version.")
                if let spectral = frame.spectral { try spectralStructure(spectral) }
                try require((frame.fillPercent != nil) == (frame.spectral != nil) && (frame.retentionUsed != nil) == (frame.spectral != nil),
                            "Sensory/fill availability differs.")
                try require((frame.control != nil) == (run.stage == .regulation), "Control availability differs from version.")
            }
            for (index, action) in run.actions.enumerated() {
                try require(action.id == index + 1 && action.observedStep > 0 && action.observedStep <= run.frames.count
                            && action.observedStep < spec.steps && (index == 0 || action.observedStep > run.actions[index - 1].observedStep),
                            "Invalid, duplicated or out-of-order action boundary.")
                try require(action.trigger == .manual || action.observedStep % spec.turnEvery == 0, "Scheduled action is off its declared clock.")
                try require(action.trigger != .manual || action.observedStep % spec.turnEvery != 0, "Manual action duplicates a scheduled boundary.")
                try text(action.prompt, limit: 131_072, name: "action prompt")
                if let raw = action.rawReply { try text(raw, limit: 65_536, name: "raw reply", empty: true) }
                if let memory = action.memoryText { try text(memory, limit: 65_536, name: "memory text") }
                for value in [action.failure, action.providerModel, action.stopReason] {
                    if let value { try text(value, limit: 4096, name: "action metadata", empty: true) }
                }
                if let vector = action.encodedFeatures {
                    try self.vector(vector, count: 48, name: "prepared features")
                    try require(vector.suffix(16).allSatisfy { $0 == 0 }, "Unavailable prepared features are nonzero.")
                }
                if let vector = action.semanticVector {
                    try self.vector(vector, count: 48, name: "prepared semantic vector")
                    try require(vector.suffix(16).allSatisfy { $0 == 0 }, "Unavailable prepared semantic features are nonzero.")
                }
                if spec.mode == .fixedReplay, let phase = action.failurePhase {
                    try require([ActionFailurePhase.memoryRead, .journalSave, .cancelled].contains(phase),
                                "Fixed tape claims an impossible provider or response-validation failure.")
                }
                if action.status == .cancelled {
                    try require(action.observedStep == run.frames.count && action.id == run.actions.count && run.status == .stopped,
                                "An interrupted action cannot be resumed as a matched comparison.")
                }
            }
            try require(Set(run.journals.map(\.id)).count == run.journals.count, "Duplicate journal identities.")
            for journal in run.journals {
                try text(journal.text, limit: 65_536, name: "journal text")
                try require(journal.sha256 == ActionRules.hash(journal.text), "Journal content hash differs.")
            }
        }
    }

    public static func verify(_ record: ActionComparisonRecord) throws -> VerificationReport {
        try validateStructure(record)
        if let actual = record.tape {
            let expected = try ActionReplyTape.make(specification: record.specification)
            for (a, e) in zip(actual.packets, expected.packets) {
                try require(a.id == e.id && a.referenceStep == e.referenceStep && a.text == e.text && a.choice == e.choice,
                            "Tape text/choice differs from the declared prerecorded reference.")
                try near(a.referenceEigenvalues, e.referenceEigenvalues, "tape reference spectrum")
                try near(a.encodedFeatures, e.encodedFeatures, "tape raw codec")
                try near(a.semanticVector, e.semanticVector, "tape reference-shaped vector")
            }
        }
        var steps = 0, actions = 0
        for run in [record.left, record.right].compactMap({ $0 }) {
            try verify(run, specification: record.specification, tape: record.tape)
            steps += run.frames.count; actions += run.actions.count
        }
        // Matched settings are owned once by the comparison specification. Check
        // full applied inputs specifically for fixed-tape G/H control isolation.
        if record.specification.mode == .fixedReplay, record.specification.stage == .regulation, let left = record.left {
            for (a, b) in zip(left.frames, record.right.frames) { try near(a.input, b.input, "controller comparison full input") }
        }
        if record.specification.comparisonKind == .observation, let left = record.left {
            try require(left.frames.count == record.right.frames.count && left.actions.count == record.right.actions.count,
                        "Observation comparison must retain both arms at every boundary.")
            for (a,b) in zip(left.frames, record.right.frames) {
                try near(a.state, b.state, "matched observed reservoir state")
                try near(a.input, b.input, "matched observation input")
                try near(a.spectral!.eigenvalues, b.spectral!.eigenvalues, "matched sensory observation")
            }
            for (a,b) in zip(left.actions, record.right.actions) {
                try require(a.observedStep == b.observedStep && a.trigger == b.trigger, "Unmatched observation opportunity.")
            }
        }
        return VerificationReport(checkedSteps: steps, checkedTurns: actions)
    }

    private static func verify(_ run: ActionRunRecord, specification spec: ActionComparisonSpecification,
                               tape: ActionReplyTape?) throws {
        var engine = try ActionArmEngine(spec: spec, stage: run.stage, arm: run.arm)
        try require(run.model.recurrentWeights == engine.record.model.recurrentWeights
                    && run.model.inputWeights == engine.record.model.inputWeights
                    && run.projectionWeights == engine.record.projectionWeights, "Seeded action weights/projection differ.")
        var actionIndex = 0, journalIndex = 0
        for frame in run.frames {
            try engine.advance()
            let expected = engine.record.frames.last!
            try near(frame.input, expected.input, "actual action input")
            try near(frame.externalInput, expected.externalInput, "external forcing")
            try near(frame.semanticInput, expected.semanticInput, "semantic input")
            try near(frame.previousState, expected.previousState, "previous action state")
            try near(frame.state, expected.state, "resulting action state")
            try near(frame.noise, expected.noise, "realized action noise")
            try require(frame.semanticActionID == expected.semanticActionID, "Applied semantic action identity differs.")
            try optional(frame.fillPercent, expected.fillPercent, "reduced fill")
            try optional(frame.retentionUsed, expected.retentionUsed, "applied retention")
            if let a = frame.spectral, let e = expected.spectral { try spectral(a, expected: e) }
            if let a = frame.control, let e = expected.control {
                try near(a.error, e.error, "control error"); try near(a.integral, e.integral, "control integral")
                try near(a.requestedRetention, e.requestedRetention, "requested retention")
                try near(a.appliedRetention, e.appliedRetention, "next-step retention")
            }
            let action = actionIndex < run.actions.count && run.actions[actionIndex].observedStep == frame.step ? run.actions[actionIndex] : nil
            if let action {
                try verify(action, frame: frame, run: run, engine: &engine, tape: tape, journalIndex: &journalIndex)
                actionIndex += 1
            } else if run.stage.hasJournal && frame.step % spec.turnEvery == 0 && frame.step < spec.steps && frame.step < run.frames.count {
                throw EssentialsError.verification("Run advanced beyond a missing scheduled action.")
            }
        }
        try require(actionIndex == run.actions.count && journalIndex == run.journals.count, "Unlinked actions or journal entries remain.")
        let failed = run.actions.last { $0.status == .failed || $0.failurePhase == .journalSave }
        try require((failed != nil) == (run.status == .failed), "Arm failure status is unsupported by its action history.")
        if let failed {
            try require(failed.observedStep == run.frames.count && failed.id == run.actions.count && run.failure == failed.failure,
                        "A failed action did not stop its arm at the recorded boundary.")
        }
        if run.status == .completed && run.stage.hasJournal {
            for step in stride(from: spec.turnEvery, to: spec.steps, by: spec.turnEvery) {
                try require(run.actions.contains { $0.observedStep == step }, "Completed run is missing a scheduled opportunity.")
            }
        }
    }

    private static func verify(_ action: ActionReceipt, frame: ActionFrame, run: ActionRunRecord,
                               engine: inout ActionArmEngine, tape: ActionReplyTape?, journalIndex: inout Int) throws {
        let latest = run.stage.hasMemory ? engine.record.journals.last : nil
        let beforeExposure = action.failurePhase == .memoryRead || (action.status == .cancelled && !action.requestStarted && action.memoryText == nil)
        let memory = beforeExposure ? nil : latest
        try require(action.memoryEntryID == latest?.id && action.memoryText == memory?.text, "Journal exposure does not match the last saved entry.")
        try require(action.prompt == ActionRules.prompt(stage: run.stage, frame: frame, memory: memory, forceJournal: action.trigger == .manual, channel: run.observationChannel ?? .sensory, comparison: engine.spec.comparisonKind, promptVersion: engine.spec.promptVersion),
                    "Prompt differs from actual sensory observation, policy or saved memory.")
        try require(action.requestedAction == (run.stage.hasChoice && action.trigger != .manual ? nil : .writeJournal), "Requested action differs from its policy.")
        try require(action.tapePacketID == (tape == nil ? nil : frame.step), "Action does not reference its actual tape boundary.")
        try require(!action.requestStarted || tape == nil, "A replayed response claims a provider request.")
        if action.failurePhase == .memoryRead {
            try require(latest != nil && action.status == .failed && !action.requestStarted, "Invalid failed memory-read receipt.")
        } else if action.status != .cancelled && tape == nil {
            try require(action.requestStarted, "Independent response lacks a started request.")
        }
        if action.status != .completed {
            try text(action.failure, limit: 4096, name: "failed/cancelled action diagnostic")
            try require(action.failurePhase != nil && action.chosenAction == nil && action.journalEntryID == nil
                        && action.saveReceipt == nil && action.encodedFeatures == nil && action.semanticVector == nil && action.applicationStep == nil,
                        "An unsuccessful action produced journal or feedback effects.")
            if action.status == .cancelled {
                try require(action.failurePhase == .cancelled && action.rawReply == nil && action.rawReplyByteCount == nil
                            && action.providerComplete == nil && action.providerModel == nil && action.stopReason == nil && action.tokenCount == nil,
                            "Cancelled request retained a late provider outcome.")
            } else if action.failurePhase == .responseValidation {
                let response = try response(action)
                let rejected: Bool
                do { _ = try ActionRules.parse(response, stage: action.trigger == .manual ? .journalOutput : run.stage); rejected = false }
                catch { rejected = true }
                try require(rejected || (action.rawReplyByteCount ?? 0) > ActionRules.maximumTextBytes,
                            "A valid complete reply was incorrectly marked invalid.")
            } else {
                try require([ActionFailurePhase.language, .memoryRead].contains(action.failurePhase!)
                            && action.rawReply == nil && action.rawReplyByteCount == nil && action.providerComplete == nil
                            && action.providerModel == nil && action.stopReason == nil && action.tokenCount == nil,
                            "Provider-free failure carries an unsupported response.")
            }
            engine.record.actions.append(action)
            return
        }
        let response = try response(action)
        try require(action.rawReplyByteCount == response.text.utf8.count, "Completed response has truncated raw text.")
        let parsed = try ActionRules.parse(response, stage: action.trigger == .manual ? .journalOutput : run.stage)
        try require(action.chosenAction == parsed.0, "Parsed choice disagrees with the raw response.")
        if let tape {
            let packet = tape.packets[frame.step - 1]
            let choice: JournalAction = run.stage.hasChoice && action.trigger != .manual ? packet.choice : .writeJournal
            try require(response.text == ActionRules.envelope(action: choice, text: packet.text)
                        && response.providerModel == "essentials-action-tape-v1" && response.stopReason == "replayed"
                        && response.complete && response.tokenCount == nil, "Replayed response differs from the fixed tape.")
        }
        if parsed.0 == .wait {
            try require(action.failure == nil && action.failurePhase == nil && action.journalEntryID == nil && action.saveReceipt == nil
                        && action.encodedFeatures == nil && action.semanticVector == nil && action.applicationStep == nil,
                        "WAIT produced a journal, reset semantic state or applied new feedback.")
        } else {
            let entry = JournalEntry(id: ActionRules.journalID(actionID: action.id, step: frame.step, text: parsed.1),
                actionID: action.id, observedStep: frame.step, text: parsed.1, sha256: ActionRules.hash(parsed.1))
            try require(action.journalEntryID == entry.id, "Journal identity differs from completed text.")
            guard let save = action.saveReceipt else { throw EssentialsError.verification("Completed journal lacks a storage outcome.") }
            try require(save.entryID == entry.id && save.sha256 == entry.sha256, "Journal storage receipt refers to different content.")
            if save.status == .failed {
                try text(action.failure, limit: 4096, name: "save failure")
                try require(action.failurePhase == .journalSave && save.failure == action.failure && save.relativePath == nil
                            && action.encodedFeatures == nil && action.semanticVector == nil && action.applicationStep == nil,
                            "Failed save became eligible for feedback.")
            } else {
                try require(action.failure == nil && action.failurePhase == nil && save.failure == nil
                            && save.relativePath == "\(run.arm.rawValue)/\(entry.id).json", "Invalid saved-journal receipt or path.")
                try require(journalIndex < run.journals.count && run.journals[journalIndex] == entry, "Saved journal is missing or changed in portable export.")
                journalIndex += 1; engine.record.journals.append(entry)
                let features = TextCodec.encode(entry.text)
                let vector = tape.map { $0.packets[frame.step - 1].semanticVector }
                    ?? TextCodec.applySpectralFeedback(features, measurement: frame.spectral!)
                guard let recordedFeatures = action.encodedFeatures, let recordedVector = action.semanticVector else {
                    throw EssentialsError.verification("Saved journal lacks prepared codec evidence.")
                }
                try near(recordedFeatures, features, "journal codec features")
                try near(recordedVector, vector, "journal applied-vector preparation")
                let application = run.stage.hasFeedback && frame.step < run.frames.count ? frame.step + 1 : nil
                try require(action.applicationStep == application, "Journal feedback did not first apply at the next actual step.")
                if run.stage.hasFeedback { engine.semantic = vector; engine.semanticActionID = action.id }
            }
        }
        engine.record.actions.append(action)
    }

    private static func response(_ action: ActionReceipt) throws -> LanguageResponse {
        guard let raw = action.rawReply, let complete = action.providerComplete, let bytes = action.rawReplyByteCount,
              bytes >= raw.utf8.count else { throw EssentialsError.verification("Response metadata or raw byte count is missing.") }
        return LanguageResponse(text: raw, providerModel: action.providerModel, stopReason: action.stopReason, tokenCount: action.tokenCount, complete: complete)
    }
    private static func require(_ condition: Bool, _ message: String) throws { try ActionRules.require(condition, message) }
    private static func text(_ value: String?, limit: Int, name: String, empty: Bool = false) throws {
        guard let value, value.utf8.count <= limit, empty || !value.isEmpty else { throw EssentialsError.verification("Invalid or missing \(name).") }
    }
    private static func vector(_ values: [Double], count: Int, name: String) throws {
        try require(values.count == count && values.allSatisfy(\.isFinite), "Invalid \(name) dimensions or finite values.")
    }
    private static func near(_ a: Double, _ e: Double, _ name: String) throws {
        try require(a.isFinite && e.isFinite && abs(a - e) <= 2e-7 * max(1, abs(e)), "\(name) does not replay.")
    }
    private static func near(_ a: [Double], _ e: [Double], _ name: String) throws {
        try require(a.count == e.count, "\(name) dimensions differ.")
        for index in a.indices { try near(a[index], e[index], name) }
    }
    private static func optional(_ a: Double?, _ e: Double?, _ name: String) throws {
        switch (a, e) { case (nil, nil): break; case (let a?, let e?): try near(a, e, name)
        default: throw EssentialsError.verification("\(name) availability differs.") }
    }
    static func spectralStructure(_ m: SpectralMeasurement) throws {
        try require(m.dimension == 32, "Invalid sensory dimension.")
        try vector(m.eigenvalues, count: 32, name: "spectrum"); try vector(m.eigenvectors, count: 1024, name: "basis")
        try vector(m.covariance, count: 1024, name: "covariance"); try vector(m.fieldVector, count: 32, name: "field vector")
        try require(m.eigenvalues.allSatisfy { $0 >= 0 } && (1..<32).allSatisfy { m.eigenvalues[$0] <= m.eigenvalues[$0 - 1] + 1e-8 },
                    "Invalid descending spectrum.")
    }
    static func spectral(_ a: SpectralMeasurement, expected e: SpectralMeasurement) throws {
        try near(a.fieldVector, e.fieldVector, "projected field"); try near(a.covariance, e.covariance, "sensory covariance")
        try near(a.eigenvalues, e.eigenvalues, "spectrum"); try near(a.entropy, e.entropy, "entropy")
        try near(a.headShare, e.headShare, "head share"); try near(a.shoulderShare, e.shoulderShare, "shoulder share")
        try near(a.tailShare, e.tailShare, "tail share")
        for mode in 0..<32 {
            let v = Array(a.eigenvectors[(mode * 32)..<((mode + 1) * 32)])
            try near(v.reduce(0) { $0 + $1 * $1 }, 1, "mode norm")
            for row in 0..<32 {
                var product = 0.0
                for col in 0..<32 { product += a.covariance[row * 32 + col] * v[col] }
                try near(product, a.eigenvalues[mode] * v[row], "mode residual")
            }
            for previous in 0..<mode {
                var dot = 0.0
                for coordinate in 0..<32 { dot += v[coordinate] * a.eigenvectors[previous * 32 + coordinate] }
                try near(dot, 0, "mode orthogonality")
            }
        }
    }
}
