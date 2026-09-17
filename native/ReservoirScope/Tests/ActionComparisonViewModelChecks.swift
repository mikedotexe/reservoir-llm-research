import Foundation
import EssentialsCore

struct SurfaceRenderError: LocalizedError {
    let message: String
    init(_ message: String) { self.message = message }
    var errorDescription: String? { message }
}
private final class MemoryActionJournals: ActionJournalStore, @unchecked Sendable {
    private let lock = NSLock()
    private var entries: [String: JournalEntry] = [:]
    private var reads = 0
    let fail: Bool
    init(fail: Bool = false) { self.fail = fail }
    func save(_ entry: JournalEntry, arm: ActionArm) throws -> JournalSaveReceipt {
        lock.lock(); defer { lock.unlock() }
        if fail { throw EssentialsError.invalid("Controlled journal save failure") }
        entries[arm.rawValue + "/" + entry.id] = entry
        return JournalSaveReceipt(status: .saved, entryID: entry.id, sha256: entry.sha256,
            relativePath: arm.rawValue + "/" + entry.id + ".json")
    }
    func read(entryID: String, arm: ActionArm) throws -> JournalEntry {
        lock.lock(); defer { lock.unlock() }; reads += 1
        guard let value = entries[arm.rawValue + "/" + entryID] else { throw EssentialsError.invalid("Missing controlled journal") }
        return value
    }
    var readCount: Int { lock.lock(); defer { lock.unlock() }; return reads }
}
private final class SessionFactoryCounter: @unchecked Sendable {
    private let lock = NSLock()
    private var count = 0
    func record() { lock.lock(); defer { lock.unlock() }; count += 1 }
    var calls: Int { lock.lock(); defer { lock.unlock() }; return count }
}
private actor ActionWriter {
    struct Write: Sendable { let record: ActionComparisonRecord; let url: URL }
    private(set) var writes: [Write] = []
    private var gate: CheckedContinuation<Void, Never>?
    private var delayNext = false
    private var failNext = false
    private var failedStage: ActionStage?
    func failStage(_ stage: ActionStage) { failedStage = stage }
    func delay() { delayNext = true }
    func fail() { failNext = true }
    func waiting() -> Bool { gate != nil }
    func release() { gate?.resume(); gate = nil }
    func write(_ record: ActionComparisonRecord, _ url: URL) async throws {
        writes.append(.init(record: record, url: url))
        if delayNext { delayNext = false; await withCheckedContinuation { gate = $0 } }
        if failNext || (record.specification.stage == failedStage && url.lastPathComponent == "run.json") { failNext = false; throw EssentialsError.invalid("Controlled record save failure") }
    }
}
private actor ActionLoader {
    private var pending: [String: CheckedContinuation<ActionComparisonRecord, Error>] = [:]
    func read(_ url: URL) async throws -> ActionComparisonRecord {
        try await withCheckedThrowingContinuation { pending[url.lastPathComponent] = $0 }
    }
    func waiting(_ key: String) -> Bool { pending[key] != nil }
    func release(_ key: String, _ record: ActionComparisonRecord) { pending.removeValue(forKey: key)?.resume(returning: record) }
    func fail(_ key: String) { pending.removeValue(forKey: key)?.resume(throwing: EssentialsError.invalid("Controlled import failure")) }
}
private actor DelayedActionBackend: LanguageBackend {
    private var gate: CheckedContinuation<String, Error>?
    private(set) var requests: [LanguageRequest] = []
    func reply(to request: LanguageRequest) async throws -> String {
        requests.append(request)
        return try await withCheckedThrowingContinuation { gate = $0 }
    }
    func waiting() -> Bool { gate != nil }
    func release() {
        gate?.resume(returning: "{\"action\":\"WRITE_JOURNAL\",\"journal\":\"I notice a quiet change and remember the earlier pattern.\"}")
        gate = nil
    }
}
@MainActor private final class ActionClock { var now = 0.0 }
@MainActor private struct ActionComparisonViewModelChecks {
    var passed = 0
    mutating func check(_ value: Bool, _ text: String) throws {
        guard value else { throw SurfaceRenderError("FAIL: " + text) }
        passed += 1; print("PASS \(passed): \(text)")
    }
    func wait(_ text: String, until condition: @MainActor () async -> Bool) async throws {
        for _ in 0..<2_000 {
            if await condition() { return }
            try await Task.sleep(for: .milliseconds(5))
        }
        throw SurfaceRenderError("Timed out: " + text)
    }
    func idle(_ model: ActionComparisonViewModel) async throws {
        try await wait("operation finished") { !model.working && !model.loading }
    }
    func make(clock: ActionClock = ActionClock(), store: MemoryActionJournals = MemoryActionJournals(),
              writer: ActionWriter = ActionWriter(), loader: ActionLoader = ActionLoader(),
              backend: (any LanguageBackend)? = nil, factoryCounter: SessionFactoryCounter = SessionFactoryCounter()) -> ActionComparisonViewModel {
        ActionComparisonViewModel(uptime: { clock.now }, sessionFactory: { spec, _ in
            factoryCounter.record()
            return try ActionComparisonSession(specification: spec, journalStore: store, backend: backend)
        }, recordLoader: { try await loader.read($0) }, recordWriter: { try await writer.write($0, $1) },
            workspaceURL: URL(fileURLWithPath: "/controlled/research"), preferences: UserDefaults(suiteName: "reservoir-actions-checks-" + UUID().uuidString)!)
    }
    mutating func run() async throws {
        let clock = ActionClock(), writer = ActionWriter(), loader = ActionLoader(), store = MemoryActionJournals()
        let model = make(clock: clock, store: store, writer: writer, loader: loader)
        try check(model.stage == .minimal && model.framesCount == 0 && model.rightState == Array(repeating: 0, count: 32) && model.speed == 3,
            "Actions starts with a quiet display and three-step-per-second pace")
        model.select(.minimal); model.run(); try await idle(model)
        try check(model.running && model.framesCount == 0, "Run prepares a session without advancing a hidden step")
        clock.now = 0.32; model.tick()
        try check(model.framesCount == 0, "The first recorded step waits for the viewing boundary")
        clock.now = 1.0 / 3; model.tick(); try await idle(model)
        try check(model.framesCount == 1 && model.rightFrame?.time == 1.0 / 3, "Paced advance records exact one-third-second simulation time")
        clock.now = 100; model.tick(); model.tick(); try await idle(model)
        try check(model.framesCount == 2, "A late timer cannot create catch-up bursts")
        model.stop(); clock.now = 1_000; model.tick()
        try check(model.framesCount == 2 && !model.running, "Stop excludes paused wall time from simulation")
        model.run(); clock.now += 0.1; model.tick()
        try check(model.framesCount == 2, "Resume waits for a fresh pacing deadline")
        model.changeSpeed(20); clock.now += 0.051; model.tick(); try await idle(model)
        try check(model.framesCount == 3 && model.rightFrame?.time == 1, "Viewing speed never changes simulated dt")
        model.stop(); model.scrub(0)
        let original = model.rightState
        model.replay(); clock.now += 0.051; model.tick()
        try check(model.row == 1 && model.framesCount == 3 && model.rightState == model.rightRecord?.frames[1].state,
            "Replay selects exact historical vectors without creating observations")
        model.scrub(0); model.step()
        try check(model.row == 1 && model.framesCount == 3 && !model.working,
            "Step in active-session history moves only the recorded cursor")
        model.scrub(0); model.run()
        try check(model.row == 2 && model.framesCount == 3 && original == model.rightRecord?.frames[0].state,
            "Resume after scrubbing restores the latest session without changing historical values")
        model.leave(); clock.now += 100; model.tick()
        try check(!model.running && !model.replaying && model.framesCount == 3, "Leaving stops both clocks")
        let minimal = model.record!
        let switching = make()
        switching.run(); switching.select(.regulation); switching.compareWithPrevious(); switching.run(); try await idle(switching)
        try check(switching.running && switching.record?.specification.stage == .regulation
            && switching.leftRecord?.stage == .actionChoice && switching.framesCount == 0,
            "Rapid selection during preparation exposes only the fully prepared newest pair")
        switching.stop()
        for _ in 0..<6 { switching.step(); try await idle(switching) }
        try check(switching.framesCount == 6 && switching.leftState == switching.rightState,
            "Fixed G/H starts with identical realized inputs and states after a rapid workspace change")
        model.select(.reservoirReturn); model.localModel = true
        try check(model.canCompare && model.canRun, "Fixed replay remains runnable with blank optional local-model fields")
        model.compareWithPrevious(); model.run(); try await idle(model); model.stop(); model.step(); try await idle(model)
        try check(model.isComparison && model.leftRecord?.stage == .journalOutput && model.rightFrame?.step == 1 && model.leftFrame?.step == 1,
            "Compare with previous prepares two arms on one shared cursor")
        try check(model.record?.specification.language.backend == .scripted && model.externalDifferences.allSatisfy { $0 == 0 }
            && model.coordinateDifferences.allSatisfy { $0 == 0 }, "Fixed replay avoids backend configuration and starts with matched forcing and state")
        try check(model.canWrite, "Manual writing is available at step one before the first scheduled boundary")
        model.writeJournal(); try await idle(model)
        try check(model.framesCount == 1 && model.leftAction?.saveReceipt?.status == .saved && model.rightAction?.saveReceipt?.status == .saved,
            "Manual writing saves both journals without secretly advancing time")
        try check(model.leftAction?.applicationStep == nil && model.rightAction?.applicationStep == nil && !model.canWrite,
            "A completed journal is not claimed as applied before the next step and cannot repeat at the same boundary")
        model.writeJournal(); model.step(); try await idle(model)
        try check(model.rightRecord?.actions.count == 1 && model.rightAction?.applicationStep == 2 && model.leftAction?.applicationStep == nil,
            "The saved E journal enters only the next step while D keeps its feedback gate closed")
        try check(model.externalDifferences.allSatisfy { $0 == 0 } && model.semanticDifferences.contains { $0 != 0 }
            && model.coordinateDifferences.contains { $0 != 0 }, "Separate differences expose semantic return and resulting state under identical external inputs")
        model.scrub(0)
        try check(model.applicationStepAtCursor(model.rightAction!) == nil, "An application recorded after the cursor is not displayed as already applied")
        model.scrub(1)
        let paired = model.record!
        _ = try paired.verify()
        try check(paired.right.actions[0].rawReply != nil && paired.right.journals[0].text == paired.left?.journals[0].text,
            "A verified comparison retains exact replies, portable journals and application receipts")
        model.select(.journalMemory); model.mode = .independentGeneration; model.localModel = false
        model.step(); try await idle(model); model.writeJournal(); try await idle(model)
        let previousJournal = model.rightRecord!.journals[0]
        model.step(); try await idle(model); model.writeJournal(); try await idle(model)
        try check(model.rightAction?.memoryEntryID == previousJournal.id && model.rightAction?.memoryText == previousJournal.text && store.readCount >= 3,
            "The next memory prompt reads the completed saved journal with exact text")
        _ = try model.record!.verify()
        model.reset()
        try check(model.framesCount == 0 && model.mode == .independentGeneration && model.stage == .journalMemory,
            "Reset clears the experiment while preserving selected version and settings")
        model.localModel = true
        try check(!model.canRun, "Independent language requires an explicitly supplied endpoint and model")
        model.select(.sensoryObserver)
        try check(model.canRun, "Versions without language do not require a model configuration")
        model.localModel = false
        model.open(URL(fileURLWithPath: "/controlled/slow")); try await wait("first import") { await loader.waiting("slow") }
        model.open(URL(fileURLWithPath: "/controlled/new")); try await wait("second import") { await loader.waiting("new") }
        await loader.release("new", paired); try await idle(model)
        await loader.release("slow", minimal); try await Task.sleep(for: .milliseconds(30))
        try check(model.record?.specification.stage == .reservoirReturn && model.row == 0 && !model.running,
            "Only the newest verified file can replace the paused display")
        model.open(URL(fileURLWithPath: "/controlled/bad")); try await wait("bad import") { await loader.waiting("bad") }
        await loader.fail("bad"); try await idle(model)
        try check(model.record?.stepCount == paired.stepCount && model.error != nil, "Malformed imports preserve the prior record and display the failure")
        model.open(URL(fileURLWithPath: "/controlled/reset")); try await wait("reset import") { await loader.waiting("reset") }
        model.reset(); await loader.release("reset", paired); try await Task.sleep(for: .milliseconds(30))
        try check(model.record == nil && !model.loading, "Reset invalidates an unfinished import")

        let delayed = DelayedActionBackend(), delayedWriter = ActionWriter(), delayedClock = ActionClock()
        let pending = make(clock: delayedClock, writer: delayedWriter, backend: delayed)
        pending.select(.reservoirReturn); pending.mode = .independentGeneration; pending.compareWithPrevious(); pending.run(); try await idle(pending); pending.stop()
        for _ in 0..<29 { pending.step(); try await idle(pending) }
        pending.step(); try await wait("scheduled provider wait") { await delayed.waiting() }
        try check(pending.working && pending.framesCount == 30 && pending.rightFrame?.step == 30,
            "The committed observation appears while its language request pauses simulated time")
        let awaitingState = pending.rightState
        pending.stop(); try await idle(pending)
        try check(pending.framesCount == 30 && pending.rightAction?.status == .cancelled && pending.leftAction?.status == .cancelled && pending.rightRecord?.journals.isEmpty == true && !pending.canWrite,
            "Stop retains a cancelled action without admitting incomplete journal feedback")
        _ = try pending.record!.verify()
        await delayed.release(); try await Task.sleep(for: .milliseconds(30))
        try check(pending.rightState == awaitingState && pending.rightAction?.status == .cancelled,
            "An uncooperative late response cannot replace the cancellation or numerical state")
        pending.step(); try await idle(pending)
        try check(pending.framesCount == 30 && !pending.canStep && !pending.canRun,
            "Step at a cancelled boundary preserves that session instead of starting another")
        pending.prepareExperiment(); pending.step(); try await idle(pending)
        try check(pending.framesCount == 1 && pending.isComparison && pending.rightRecord?.actions.isEmpty == true,
            "Preparing a new experiment explicitly permits a fresh matched session after cancellation")
        pending.writeJournal(); try await wait("manual provider wait") { await delayed.waiting() }
        pending.reset(); await delayed.release(); try await Task.sleep(for: .milliseconds(50))
        try check(pending.record == nil && !pending.working && !pending.running,
            "Reset during writing rejects every late display callback")
        try await wait("cancelled journal archived") { (await delayedWriter.writes).contains { $0.record.stepCount == 1 && $0.record.right.actions.last?.status == .cancelled } }
        try check((await delayedWriter.writes).last?.record.right.actions.last?.status == .cancelled,
            "The detached session still saves the final cancelled request as research evidence")
        pending.select(.journalMemory); pending.select(.reservoirReturn)
        try check(pending.rightAction?.status == .cancelled && !pending.canWrite,
            "Revisiting a version shows its final retained outcome without reviving the interrupted session")

        let failed = make(store: MemoryActionJournals(fail: true))
        failed.select(.reservoirReturn); failed.mode = .independentGeneration; failed.step(); try await idle(failed); failed.writeJournal(); try await idle(failed)
        try check(failed.record?.status == .failed && failed.rightAction?.saveReceipt?.status == .failed
            && failed.rightRecord?.journals.isEmpty == true && failed.rightAction?.applicationStep == nil,
            "A failed journal save is visible and cannot open the feedback gate")
        _ = try failed.record!.verify()
        let savingWriter = ActionWriter(), saving = make(writer: savingWriter)
        saving.select(.minimal); await savingWriter.delay(); saving.step(); try await idle(saving)
        try await wait("delayed record save") { await savingWriter.waiting() }
        saving.reset(); let resetStatus = saving.status
        await savingWriter.release(); try await Task.sleep(for: .milliseconds(50))
        try check(saving.record == nil && saving.source.isEmpty && saving.status == resetStatus,
            "An old save completion cannot restore a reset source or overwrite its status")
        await savingWriter.fail(); saving.step(); try await idle(saving)
        try await wait("failed record save") { saving.saveIssue != nil }
        saving.reset()
        try check(saving.saveIssue != nil && saving.record == nil, "Failed record saving remains visible after reset")
        try await wait("research save paths") { !(await writer.writes).isEmpty }
        try check((await writer.writes).allSatisfy { $0.url.path.hasPrefix("/controlled/research/Actions/") && $0.url.lastPathComponent == "run.json" },
            "Autosaves use atomic-writer destinations isolated by research session")
        let progressiveClock = ActionClock(), progressive = make(clock: progressiveClock)
        progressive.select(.journalOutput); progressive.run(); try await idle(progressive)
        progressive.nextJournal()
        try check(progressive.running && progressive.framesCount == 0,
            "Next opportunity can arm its stopping point during an already-running experiment")
        for _ in 0..<30 { progressiveClock.now += 1; progressive.tick(); try await idle(progressive) }
        try check(progressive.framesCount == 30 && !progressive.running && progressive.rightAction?.saveReceipt?.status == .saved,
            "Next journal stops at the first completed scheduled opportunity")
        progressive.scrub(0); progressive.selectedActionID = 1
        try check(progressive.rightAction == nil, "A selected future journal never leaks into an earlier cursor position")
        progressive.selectObservationComparison(); progressive.compareWithPrevious(); progressive.run(); try await idle(progressive)
        progressive.stop(); progressive.step(); try await idle(progressive); progressive.writeJournal(); try await idle(progressive)
        try check(progressive.leftRecord?.stage == .journalOutput && progressive.rightRecord?.stage == .journalOutput
            && progressive.record?.specification.mode == .independentGeneration && progressive.rightAction?.prompt.contains("x[31]=") == true
            && progressive.leftAction?.prompt.contains("x[31]=") == false,
            "Observation comparison uses two independent stage-D arms with different declared observation access")
        try check(progressive.leftState == progressive.rightState, "Observation comparison retains the identical measured trajectory")
        _ = try progressive.record!.verify()
        // The teaching walkthrough must be safe even when replay has no session
        // and local model settings are deliberately absent.
        let replaySession = try ActionComparisonSession(specification: ActionComparisonSpecification(
            stage: .reservoirReturn, steps: 120), journalStore: MemoryActionJournals())
        let replayFixture = try await replaySession.run()
        _ = try replayFixture.verify()
        let replayLoader = ActionLoader(), replayWriter = ActionWriter(), replayClock = ActionClock()
        let factoryCounter = SessionFactoryCounter(), replayBackend = DelayedActionBackend()
        let playback = make(clock: replayClock, writer: replayWriter, loader: replayLoader,
            backend: replayBackend, factoryCounter: factoryCounter)
        playback.open(URL(fileURLWithPath: "/controlled/example-E.json"), initialRow: 29)
        try await wait("recorded E open") { await replayLoader.waiting("example-E.json") }
        await replayLoader.release("example-E.json", replayFixture); try await idle(playback)
        try check(playback.isRecording && playback.row == 29 && !playback.running && !playback.replaying,
            "Opening restores the requested cursor and remains paused")
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        let identityBefore = try encoder.encode(playback.record!)
        let journalsBefore = playback.rightRecord!.journals.count
        playback.step()
        try check(playback.row == 30 && playback.rightFrame?.step == 31 && playback.rightAction?.applicationStep == 31,
            "Recorded E advances from journal at 30 to its actual feedback application at 31")
        try check(try encoder.encode(playback.record!) == identityBefore && playback.rightRecord!.journals.count == journalsBefore,
            "Replay Step preserves record identity, frame history, and journal count")
        playback.localModel = true; playback.mode = .independentGeneration
        playback.endpoint = ""; playback.modelName = ""; playback.seedText = "not a seed"
        playback.run(); replayClock.now += 1; playback.tick()
        try check(playback.row == 31 && playback.replaying && !playback.running && factoryCounter.calls == 0,
            "Recorded Play ignores generation settings and never creates a session")
        playback.stop(); playback.scrub(119); playback.step(); playback.run(); playback.nextJournal()
        try check(playback.row == 119 && playback.framesCount == 120 && !playback.canRun && !playback.canStep && !playback.working,
            "End-of-record controls cannot generate new observations")
        playback.replay()
        try check(playback.row == 0 && playback.replaying, "Replay restarts at the first saved observation")
        playback.stop(); playback.select(.journalOutput); playback.select(.reservoirReturn)
        try check(playback.isRecording && playback.framesCount == 120, "Revisiting an opened example keeps playback semantics")
        try check(await playback.flushForTermination(), "Quit needs no save for an unchanged recording")
        let playbackWrites = await replayWriter.writes, playbackRequests = await replayBackend.requests
        try check(playbackWrites.isEmpty && factoryCounter.calls == 0 && playbackRequests.isEmpty,
            "Opening, playback, switching stages, stopping, and quitting create no library copy or model request")
        playback.prepareExperiment()
        try check(playback.record == nil && !playback.working && !playback.running && factoryCounter.calls == 0,
            "Try an experiment prepares a stopped configuration without creating a session")
        // Restore explicit settings, then start the prepared configuration.
        playback.seedText = "20260909"; playback.localModel = false; playback.mode = .fixedReplay
        playback.run(); try await idle(playback)
        try check(factoryCounter.calls == 1 && playback.record?.specification.steps == 300 && playback.running,
            "Explicit Start creates one new experiment using the 300-step interactive default")
        playback.stop()
        let compareLoader = ActionLoader(), compareCounter = SessionFactoryCounter()
        let comparePreparation = make(loader: compareLoader, factoryCounter: compareCounter)
        comparePreparation.open(URL(fileURLWithPath: "/controlled/compare-E.json"))
        try await wait("compare source open") { await compareLoader.waiting("compare-E.json") }
        await compareLoader.release("compare-E.json", replayFixture); try await idle(comparePreparation)
        comparePreparation.compareWithPrevious()
        try check(comparePreparation.record == nil && !comparePreparation.running && !comparePreparation.working && compareCounter.calls == 0,
            "Compare with previous prepares the matched configuration without starting generation")
        comparePreparation.step(); try await idle(comparePreparation)
        try check(compareCounter.calls == 1 && comparePreparation.leftRecord?.stage == .journalOutput && comparePreparation.rightFrame?.step == 1,
            "Step explicitly begins a prepared comparison with matched initial conditions")
        comparePreparation.stop()
        let actionSession = try ActionComparisonSession(specification: ActionComparisonSpecification(
            stage: .actionChoice, steps: 120), journalStore: MemoryActionJournals())
        let actionFixture = try await actionSession.run()
        let opportunityLoader = ActionLoader(), opportunityCounter = SessionFactoryCounter()
        let opportunities = make(loader: opportunityLoader, factoryCounter: opportunityCounter)
        opportunities.open(URL(fileURLWithPath: "/controlled/choice.json"), initialRow: 59)
        try await wait("choice open") { await opportunityLoader.waiting("choice.json") }
        await opportunityLoader.release("choice.json", actionFixture); try await idle(opportunities)
        opportunities.nextJournal()
        try check(opportunities.rightFrame?.step == 90 && opportunities.rightAction?.chosenAction == .wait && opportunityCounter.calls == 0,
            "Next journal opportunity includes WAIT without generating a journal")
        opportunities.open(URL(fileURLWithPath: "/controlled/failure.json"))
        try await wait("failure open") { await opportunityLoader.waiting("failure.json") }
        // The saved failure above occurs at step one, so use a scheduled failure
        // at 30 to verify navigation from a preceding cursor.
        let failureSession = try ActionComparisonSession(specification: ActionComparisonSpecification(
            stage: .reservoirReturn, steps: 120), journalStore: MemoryActionJournals(fail: true))
        let failureFixture = try await failureSession.run()
        await opportunityLoader.release("failure.json", failureFixture); try await idle(opportunities)
        opportunities.nextJournal()
        try check(opportunities.rightFrame?.step == 30 && opportunities.leftAction?.saveReceipt?.status == .failed && opportunities.rightAction?.status == .cancelled && opportunityCounter.calls == 0,
            "Next journal opportunity preserves failed writing and its cancelled paired outcome")
        // Component D and the observation study share a stage number, not a
        // navigation identity. Both must survive alternating selections.
        let componentD = progressive.record // preserve the currently displayed observation pair
        progressive.select(.journalOutput)
        try check(progressive.record?.specification.comparisonKind == .components && progressive.rightRecord?.actions.count == 1,
            "Returning to D restores its component record rather than the observation comparison")
        progressive.selectObservationComparison()
        try check(progressive.record?.specification.comparisonKind == .observation && progressive.record?.stepCount == componentD?.stepCount,
            "The observation comparison has its own retained navigation record")
        let recoveryWriter = ActionWriter(), recovery = make(writer: recoveryWriter)
        await recoveryWriter.fail(); recovery.step(); try await idle(recovery)
        try await wait("recovery save failure") { recovery.saveIssue != nil }
        recovery.retrySaves(); try await wait("recovery saved") { recovery.saveIssue == nil }
        try check(await recovery.flushForTermination(), "Retry saves retained evidence and quit waits for persistence")
        let oldWriter = ActionWriter(), oldFailure = make(writer: oldWriter)
        await oldWriter.failStage(.minimal); oldFailure.step(); try await idle(oldFailure)
        try await wait("old failure retained") { oldFailure.saveIssue != nil }
        oldFailure.select(.recurrence); oldFailure.step(); try await idle(oldFailure)
        try await wait("detached failed record archived") {
            (await oldWriter.writes).filter { $0.record.specification.stage == .minimal }.count >= 3
        }
        oldFailure.exportRetained(to: URL(fileURLWithPath: "/controlled/recovered.json"))
        try await wait("retained export completed") { oldFailure.saveIssue == nil }
        let exportedWrites = await oldWriter.writes
        try check(oldFailure.stage == .recurrence && exportedWrites.contains {
            $0.url.lastPathComponent == "recovered.json" && $0.record.specification.stage == .minimal
        }, "An offscreen failed record exports to another destination without replacing the current experiment")
        print("\(passed) action lifecycle checks passed; memory journals, controlled clocks and fake providers only.")
    }
}
Task { @MainActor in
    do { var checks = ActionComparisonViewModelChecks(); try await checks.run(); exit(0) }
    catch { print(error.localizedDescription); exit(1) }
}
dispatchMain()
