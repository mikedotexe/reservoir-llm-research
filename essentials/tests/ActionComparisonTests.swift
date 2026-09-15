import XCTest
@testable import EssentialsCore

final class ActionComparisonTests: XCTestCase, @unchecked Sendable {
    private func directory() throws -> URL {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("essentials-actions-test-\(UUID())", isDirectory: true)
        try FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        addTeardownBlock { try? FileManager.default.removeItem(at: url) }
        return url
    }
    private func session(_ spec: ActionComparisonSpecification, backend: (any LanguageBackend)? = nil,
                         timeout: Duration = .seconds(60)) throws -> ActionComparisonSession {
        try ActionComparisonSession(specification: spec, journalStore: LocalActionJournalStore(directory: directory()),
                                    backend: backend, languageTimeout: timeout)
    }
    private func run(_ stage: ActionStage, steps: Int = 34, mode: ActionComparisonMode = .fixedReplay,
                     backend: (any LanguageBackend)? = nil) async throws -> ActionComparisonRecord {
        try await session(ActionComparisonSpecification(stage: stage, mode: mode, steps: steps), backend: backend).run()
    }
    private func json(_ record: ActionComparisonRecord) throws -> [String: Any] {
        try JSONSerialization.jsonObject(with: JSONEncoder().encode(record)) as! [String: Any]
    }
    private func decode(_ object: [String: Any]) throws -> ActionComparisonRecord {
        try JSONDecoder().decode(ActionComparisonRecord.self, from: JSONSerialization.data(withJSONObject: object))
    }

    func testDefaultsAndBoundsAreExplicit() throws {
        let spec = try JSONDecoder().decode(ActionComparisonSpecification.self, from: Data("{\"stage\":5,\"mode\":\"fixedReplay\"}".utf8))
        XCTAssertEqual(spec.steps, 300); XCTAssertEqual(spec.turnEvery, 30); XCTAssertFalse(spec.biasEnabled)
        XCTAssertEqual(spec.dt, 1.0 / 3); XCTAssertFalse(spec.question.isEmpty)
        var bad = spec; bad.steps = 601; XCTAssertThrowsError(try bad.validate())
        bad = spec; bad.turnEvery = 0; XCTAssertThrowsError(try bad.validate())
        bad = spec; bad.turnEvery = 1; XCTAssertThrowsError(try bad.validate())
        bad = spec; bad.noiseAmplitude = .nan; XCTAssertThrowsError(try bad.validate())
        bad = spec; bad.question = ""; XCTAssertThrowsError(try bad.validate())
        XCTAssertThrowsError(try JSONDecoder().decode(ActionComparisonSpecification.self, from: Data("{\"stage\":9}".utf8)))
    }

    func testAllEightVersionsRunReplayAndExposeOnlyAvailableMechanisms() async throws {
        for stage in ActionStage.allCases {
            let record = try await run(stage)
            XCTAssertEqual(record.status, .completed, "\(stage)")
            XCTAssertEqual(record.right.frames.count, 34)
            XCTAssertEqual(record.left != nil, stage != .minimal)
            XCTAssertEqual(record.right.actions.count, stage.hasJournal ? 1 : 0)
            XCTAssertEqual(record.right.frames[0].spectral != nil, stage.rawValue >= 3)
            XCTAssertEqual(record.right.frames[0].fillPercent != nil, stage.rawValue >= 3)
            XCTAssertEqual(record.right.frames[0].control != nil, stage == .regulation)
            XCTAssertEqual(try record.verify().checkedSteps, stage == .minimal ? 34 : 68)
        }
    }

    func testRecurrenceChangesStateAndPassiveObserverAndJournalDoNot() async throws {
        let recurrence = try await run(.recurrence)
        XCTAssertEqual(recurrence.left!.frames[0].state, recurrence.right.frames[0].state)
        XCTAssertNotEqual(recurrence.left!.frames[1].state, recurrence.right.frames[1].state)
        for stage in [ActionStage.sensoryObserver, .journalOutput] {
            let record = try await run(stage)
            XCTAssertEqual(record.left!.frames.map(\.state), record.right.frames.map(\.state))
            XCTAssertEqual(record.left!.frames.map(\.input), record.right.frames.map(\.input))
        }
    }

    func testFixedJournalGateFirstChangesStateOnFollowingStep() async throws {
        let record = try await run(.reservoirReturn)
        let left = record.left!, right = record.right
        XCTAssertEqual(left.actions[0].rawReply, right.actions[0].rawReply)
        XCTAssertEqual(left.actions[0].prompt, right.actions[0].prompt)
        XCTAssertEqual(left.actions[0].semanticVector, right.actions[0].semanticVector)
        XCTAssertFalse(right.actions[0].requestStarted)
        XCTAssertNil(left.actions[0].applicationStep); XCTAssertEqual(right.actions[0].applicationStep, 31)
        XCTAssertEqual(Array(left.frames.prefix(30)).map(\.state), Array(right.frames.prefix(30)).map(\.state))
        XCTAssertNotEqual(left.frames[30].state, right.frames[30].state)
        XCTAssertEqual(right.frames[30].semanticInput, right.actions[0].semanticVector)
        XCTAssertTrue(right.actions[0].semanticVector!.suffix(16).allSatisfy { $0 == 0 })
        XCTAssertEqual(left.frames.map(\.externalInput), right.frames.map(\.externalInput))
    }

    func testTapeReferenceIsFrozenExternalOnlyAndNotCurrentFeedbackField() async throws {
        let record = try await run(.reservoirReturn, steps: 65)
        let tape = record.tape!
        XCTAssertEqual(tape.packets.count, 64)
        XCTAssertEqual(tape.packets[59].referenceStep, 60)
        XCTAssertEqual(record.right.actions[1].semanticVector, tape.packets[59].semanticVector)
        XCTAssertNotEqual(tape.packets[59].referenceEigenvalues, record.right.frames[59].spectral!.eigenvalues)
        XCTAssertEqual(tape, try ActionReplyTape.make(specification: record.specification))
        try record.verify()
    }

    func testMemoryExposureChangesActualPromptAndPromptSensitiveReply() async throws {
        let record = try await run(.journalMemory, steps: 65, mode: .independentGeneration, backend: PromptSensitiveActionBackend())
        let left = record.left!, right = record.right
        XCTAssertEqual(left.journals[0].text, right.journals[0].text)
        XCTAssertNil(left.actions[1].memoryEntryID)
        XCTAssertEqual(right.actions[1].memoryEntryID, right.journals[0].id)
        XCTAssertEqual(right.actions[1].memoryText, right.journals[0].text)
        XCTAssertTrue(right.actions[1].prompt.contains(right.journals[0].text))
        XCTAssertTrue(right.actions[1].requestStarted)
        XCTAssertNotEqual(left.journals[1].text, right.journals[1].text)
        XCTAssertNotEqual(left.frames[60].state, right.frames[60].state)
        try record.verify()
    }

    func testFixedRepliesDoNotPretendToMeasureMemoryInfluence() async throws {
        let record = try await run(.journalMemory, steps: 65)
        XCTAssertNotEqual(record.left!.actions[1].prompt, record.right.actions[1].prompt)
        XCTAssertEqual(record.left!.actions.map(\.rawReply), record.right.actions.map(\.rawReply))
        XCTAssertEqual(record.left!.frames.map(\.state), record.right.frames.map(\.state))
        XCTAssertFalse(record.right.actions[1].requestStarted)
        try record.verify()
    }

    func testChoiceWaitHoldsPriorSemanticAndControllerUsesMatchedFullInput() async throws {
        for stage in [ActionStage.actionChoice, .regulation] {
            let record = try await run(stage, steps: 92)
            let wait = record.right.actions[2]
            XCTAssertEqual(wait.chosenAction, .wait); XCTAssertNil(wait.journalEntryID); XCTAssertNil(wait.applicationStep)
            XCTAssertEqual(record.right.frames[90].semanticInput, record.right.frames[89].semanticInput)
            XCTAssertEqual(record.right.frames[90].semanticActionID, 2)
            if stage == .regulation {
                XCTAssertEqual(record.left!.frames.map(\.input), record.right.frames.map(\.input))
                XCTAssertNotEqual(record.left!.frames.map(\.fillPercent), record.right.frames.map(\.fillPercent))
                XCTAssertNotNil(record.left!.frames[0].fillPercent)
                XCTAssertNil(record.left!.frames[0].control)
                XCTAssertEqual(record.right.frames[1].retentionUsed, record.right.frames[0].control?.appliedRetention)
            }
            try record.verify()
        }
    }

    func testManualWriteUsesCurrentBoundaryOnceAndForcedChoice() async throws {
        let session = try session(ActionComparisonSpecification(stage: .actionChoice, steps: 94))
        do { _ = try await session.writeJournal(); XCTFail("No implicit step permitted") } catch {}
        _ = try await session.advance()
        var record = try await session.writeJournal()
        XCTAssertEqual(record.stepCount, 1)
        XCTAssertEqual(record.right.actions[0].observedStep, 1)
        XCTAssertEqual(record.right.actions[0].tapePacketID, 1)
        XCTAssertEqual(record.right.actions[0].requestedAction, .writeJournal)
        XCTAssertTrue(record.right.actions[0].prompt.contains("requested action is WRITE_JOURNAL"))
        do { _ = try await session.writeJournal(); XCTFail("Duplicate manual action accepted") } catch {}
        record = try await session.run()
        XCTAssertEqual(record.right.actions.map(\.observedStep), [1, 30, 60, 90])
        XCTAssertEqual(record.right.actions[0].applicationStep, 2)
        try record.verify()
    }

    func testJournalStoreIsImmutableAndExportReplaysAfterStoreRemoval() async throws {
        let directory = try directory(), store = try LocalActionJournalStore(directory: directory.appendingPathComponent("journals"))
        let session = try ActionComparisonSession(specification: .init(stage: .journalMemory, steps: 64), journalStore: store)
        let record = try await session.run()
        XCTAssertEqual(record.status, .completed)
        let entry = record.right.journals[0]
        XCTAssertEqual(try store.read(entryID: entry.id, arm: .right), entry)
        XCTAssertEqual(try store.save(entry, arm: .right), record.right.actions[0].saveReceipt)
        let changed = JournalEntry(id: entry.id, actionID: entry.actionID, observedStep: entry.observedStep,
                                   text: "changed", sha256: ActionRules.hash("changed"))
        XCTAssertThrowsError(try store.save(changed, arm: .right))
        let export = directory.appendingPathComponent("comparison.json")
        try record.write(to: export)
        try FileManager.default.removeItem(at: store.directory)
        let restored = try ActionComparisonRecord.read(from: export)
        XCTAssertEqual(restored.right.journals, record.right.journals)
        try restored.verify()
    }

    func testVerifierRejectsUnmatchedManualJournalOpportunityEvenWhenStateIsUnchanged() async throws {
        let session = try session(.init(stage: .reservoirReturn, steps: 4))
        _ = try await session.advance(); _ = try await session.writeJournal()
        let record = try await session.run()
        var object = try json(record)
        var left = object["left"] as! [String: Any]
        left["actions"] = []; left["journals"] = []
        object["left"] = left
        XCTAssertThrowsError(try decode(object).verify())
    }

    func testVerifierRejectsImpossiblePairedExecutionAndFixedProviderFailure() async throws {
        let specification = ActionComparisonSpecification(stage: .reservoirReturn, steps: 4)
        let failing = try ActionComparisonSession(specification: specification, journalStore: RejectingActionStore())
        _ = try await failing.advance()
        let failed = try await failing.writeJournal()
        try failed.verify()
        let successful = try session(specification)
        _ = try await successful.advance()
        let good = try await successful.writeJournal()
        var splice = try json(failed)
        splice["right"] = try json(good)["right"]
        XCTAssertThrowsError(try decode(splice).verify())

        var impossible = try json(failed)
        var left = impossible["left"] as! [String: Any]
        var actions = left["actions"] as! [[String: Any]]
        actions[0]["status"] = "failed"; actions[0]["failurePhase"] = "language"
        for key in ["chosenAction", "journalEntryID", "saveReceipt", "rawReply", "rawReplyByteCount", "providerModel", "stopReason", "tokenCount", "providerComplete"] {
            actions[0].removeValue(forKey: key)
        }
        left["actions"] = actions; impossible["left"] = left
        XCTAssertThrowsError(try decode(impossible).verify())
    }

    func testSaveFailurePreservesCompletionButPreventsAnyReturn() async throws {
        let spec = ActionComparisonSpecification(stage: .reservoirReturn, comparePrevious: false, steps: 34)
        let session = try ActionComparisonSession(specification: spec, journalStore: RejectingActionStore())
        let record = try await session.run()
        XCTAssertEqual(record.status, .failed); XCTAssertEqual(record.stepCount, 30)
        XCTAssertEqual(record.right.actions[0].status, .completed)
        XCTAssertEqual(record.right.actions[0].saveReceipt?.status, .failed)
        XCTAssertEqual(record.right.actions[0].failurePhase, .journalSave)
        XCTAssertNil(record.right.actions[0].semanticVector); XCTAssertTrue(record.right.journals.isEmpty)
        try record.verify()
    }

    func testMemoryReadFailureDoesNotBecomeAnExposureOrGeneration() async throws {
        let store = FailingSecondReadActionStore(base: try LocalActionJournalStore(directory: directory()))
        let session = try ActionComparisonSession(specification: .init(stage: .journalMemory, comparePrevious: false, steps: 64), journalStore: store)
        let record = try await session.run()
        XCTAssertEqual(record.status, .failed); XCTAssertEqual(record.stepCount, 60)
        XCTAssertEqual(record.right.actions[1].failurePhase, .memoryRead)
        XCTAssertEqual(record.right.actions[1].memoryEntryID, record.right.journals[0].id)
        XCTAssertNil(record.right.actions[1].memoryText); XCTAssertFalse(record.right.actions[1].requestStarted)
        XCTAssertNil(record.right.actions[1].rawReply)
        try record.verify()
    }

    func testIncompleteInvalidAndOversizedRepliesNeverBecomeJournalFeedback() async throws {
        let good = ActionRules.envelope(action: .writeJournal, text: "A bright signal remains.")
        let responses = [LanguageResponse(text: good, complete: false), LanguageResponse(text: good, stopReason: "length"),
                         LanguageResponse(text: good, tokenCount: 257), LanguageResponse(text: good, tokenCount: -1),
                         LanguageResponse(text: "not JSON"), LanguageResponse(text: "{\"action\":\"DELETE\",\"text\":\"x\"}"),
                         LanguageResponse(text: ActionRules.envelope(action: .wait, text: "")),
                         LanguageResponse(text: good + String(repeating: " ", count: 70_000))]
        for response in responses {
            let s = try session(.init(stage: .reservoirReturn, mode: .independentGeneration, comparePrevious: false, steps: 32),
                                backend: ImmediateActionBackend(response: response))
            let record = try await s.run()
            XCTAssertEqual(record.status, .failed); XCTAssertTrue(record.right.journals.isEmpty)
            XCTAssertEqual(record.right.actions[0].failurePhase, .responseValidation)
            XCTAssertNil(record.right.actions[0].semanticVector)
            try record.verify()
        }
    }

    func testCancelledPairedRequestIsTerminalAndLateCompletionCannotApply() async throws {
        let backend = SuspendedActionBackend()
        let session = try session(.init(stage: .reservoirReturn, mode: .independentGeneration, steps: 34), backend: backend)
        let task = Task { try await session.run() }
        await backend.waitForRequest()
        let waiting = await session.snapshot()
        XCTAssertEqual(waiting.stepCount, 30)
        await session.stop()
        let record = try await task.value
        XCTAssertEqual(record.status, .stopped)
        XCTAssertEqual(record.left?.actions[0].status, .cancelled)
        XCTAssertEqual(record.right.actions[0].status, .cancelled)
        XCTAssertFalse(record.right.actions[0].requestStarted)
        await backend.finish()
        do { _ = try await session.advance(); XCTFail("Cancelled comparison resumed") } catch {}
        let afterLateReply = await session.snapshot()
        XCTAssertNil(afterLateReply.right.actions[0].semanticVector)
        try record.verify()
    }

    func testTimeoutAndObservationCallbackPreserveTheActualBoundary() async throws {
        let backend = SuspendedActionBackend(), observed = ActionObservedSteps()
        let session = try session(.init(stage: .journalOutput, mode: .independentGeneration, comparePrevious: false, steps: 34),
                                  backend: backend, timeout: .milliseconds(30))
        for _ in 1..<30 { _ = try await session.advance() }
        let task = Task { try await session.advance(onObservation: { await observed.append($0.stepCount) }) }
        await backend.waitForRequest()
        let observedSteps = await observed.values
        XCTAssertEqual(observedSteps, [30])
        let record = try await task.value
        XCTAssertEqual(record.status, .failed); XCTAssertEqual(record.stepCount, 30)
        XCTAssertEqual(record.right.actions[0].failurePhase, .language)
        await backend.finish()
        try record.verify()
    }

    func testFiniteRunOwnershipAndBetweenBoundaryStop() async throws {
        let session = try session(.init(stage: .recurrence, steps: 4))
        let caught = ActionObservedSteps()
        let stopped = try await session.run(onFrame: { record in
            if record.stepCount == 1 {
                do { _ = try await session.advance(); await caught.append(-1) } catch { await caught.append(1) }
                do { _ = try await session.run(); await caught.append(-2) } catch { await caught.append(2) }
                await session.stop()
            }
        })
        XCTAssertEqual(stopped.stepCount, 1)
        let ownershipChecks = await caught.values
        XCTAssertEqual(ownershipChecks, [1, 2])
        let resumed = try await session.run()
        XCTAssertEqual(resumed.status, .completed); try resumed.verify()
    }

    func testDeterministicRecordsAndVerifierRejectsTampering() async throws {
        let a = try await run(.journalMemory, steps: 64), b = try await run(.journalMemory, steps: 64)
        let encoder = JSONEncoder(); encoder.outputFormatting = .sortedKeys
        XCTAssertEqual(try encoder.encode(a), try encoder.encode(b))
        let base = try json(a)
        let mutations: [(inout [String: Any]) -> Void] = [
            { $0["format"] = "essentials-v1" },
            { var right = $0["right"] as! [String: Any]; var frames = right["frames"] as! [[String: Any]]; frames[30]["state"] = [0]; right["frames"] = frames; $0["right"] = right },
            { var right = $0["right"] as! [String: Any]; var actions = right["actions"] as! [[String: Any]]; actions[0]["applicationStep"] = 30; right["actions"] = actions; $0["right"] = right },
            { var right = $0["right"] as! [String: Any]; var actions = right["actions"] as! [[String: Any]]; actions[1]["memoryText"] = "invented"; right["actions"] = actions; $0["right"] = right },
            { var right = $0["right"] as! [String: Any]; var actions = right["actions"] as! [[String: Any]]; actions[0]["prompt"] = "invented"; right["actions"] = actions; $0["right"] = right },
            { var tape = $0["tape"] as! [String: Any]; var packets = tape["packets"] as! [[String: Any]]; packets[29]["text"] = "invented"; tape["packets"] = packets; $0["tape"] = tape },
            { var right = $0["right"] as! [String: Any]; var journals = right["journals"] as! [[String: Any]]; journals[0]["text"] = "changed"; right["journals"] = journals; $0["right"] = right },
            { var left = $0["left"] as! [String: Any]; left["stage"] = 4; $0["left"] = left }
        ]
        for mutate in mutations {
            var object = base; mutate(&object)
            XCTAssertThrowsError(try decode(object).verify())
        }
    }
}

private struct ImmediateActionBackend: LanguageBackend {
    let response: LanguageResponse
    func reply(to request: LanguageRequest) async throws -> String { response.text }
    func response(to request: LanguageRequest) async throws -> LanguageResponse { response }
}
private struct PromptSensitiveActionBackend: LanguageBackend {
    func reply(to request: LanguageRequest) async throws -> String {
        ActionRules.envelope(action: .writeJournal, text: request.prompt.contains("<journal>")
            ? "I remember the earlier bright rhythm and feel curious about its hopeful return."
            : "A dark silent shape passes.")
    }
}
private struct RejectingActionStore: ActionJournalStore {
    func save(_ entry: JournalEntry, arm: ActionArm) throws -> JournalSaveReceipt { throw EssentialsError.invalid("Fixture refused storage.") }
    func read(entryID: String, arm: ActionArm) throws -> JournalEntry { throw EssentialsError.invalid("Fixture has no entry.") }
}
private final class FailingSecondReadActionStore: ActionJournalStore, @unchecked Sendable {
    let base: LocalActionJournalStore
    private let lock = NSLock()
    private var reads = 0
    init(base: LocalActionJournalStore) { self.base = base }
    func save(_ entry: JournalEntry, arm: ActionArm) throws -> JournalSaveReceipt { try base.save(entry, arm: arm) }
    func read(entryID: String, arm: ActionArm) throws -> JournalEntry {
        lock.lock(); reads += 1; let fail = reads > 1; lock.unlock()
        if fail { throw EssentialsError.invalid("Fixture cannot read saved memory.") }
        return try base.read(entryID: entryID, arm: arm)
    }
}
private actor ActionObservedSteps {
    var values: [Int] = []
    func append(_ step: Int) { values.append(step) }
}
private actor SuspendedActionBackend: LanguageBackend {
    private var continuation: CheckedContinuation<String, Never>?
    private var requested = false
    func reply(to request: LanguageRequest) async throws -> String {
        requested = true
        return await withCheckedContinuation { continuation = $0 }
    }
    func waitForRequest() async {
        while !requested { try? await Task.sleep(for: .milliseconds(1)) }
    }
    func finish() {
        continuation?.resume(returning: ActionRules.envelope(action: .writeJournal, text: "A late bright reply."))
        continuation = nil
    }
}
