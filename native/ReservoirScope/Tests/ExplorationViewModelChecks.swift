import Foundation
import EssentialsCore

struct SurfaceRenderError: LocalizedError {
    let message: String
    init(_ message: String) { self.message = message }
    var errorDescription: String? { message }
}
private actor ExplorationLoader {
    private var pending: [String: CheckedContinuation<ExplorationRecord, Error>] = [:]
    func read(_ url: URL) async throws -> ExplorationRecord {
        try await withCheckedThrowingContinuation { pending[url.lastPathComponent] = $0 }
    }
    func waiting(_ name: String) -> Bool { pending[name] != nil }
    func release(_ name: String, record: ExplorationRecord) { pending.removeValue(forKey: name)?.resume(returning: record) }
    func fail(_ name: String) { pending.removeValue(forKey: name)?.resume(throwing: EssentialsError.invalid("Controlled file failure")) }
}
private actor ExplorationWriter {
    struct Write: Sendable { let record: ExplorationRecord; let url: URL }
    private(set) var writes: [Write] = []
    private var pending: CheckedContinuation<Void, Never>?
    var shouldDelay = false
    func write(_ record: ExplorationRecord, _ url: URL) async throws {
        writes.append(Write(record: record, url: url))
        if shouldDelay { await withCheckedContinuation { pending = $0 } }
    }
    func delay() { shouldDelay = true }
    func release() { shouldDelay = false; pending?.resume(); pending = nil }
    func waiting() -> Bool { pending != nil }
}
@MainActor private final class ExplorationClock { var now = 0.0 }
@MainActor private struct ExplorationViewModelChecks {
    var passed = 0
    mutating func check(_ condition: Bool, _ explanation: String) throws {
        guard condition else { throw SurfaceRenderError("FAIL: \(explanation)") }
        passed += 1; print("PASS \(passed): \(explanation)")
    }
    func wait(_ label: String, until condition: @MainActor () async -> Bool) async throws {
        for _ in 0..<1_000 {
            if await condition() { return }
            try await Task.sleep(for: .milliseconds(5))
        }
        throw SurfaceRenderError("Timed out: \(label)")
    }
    mutating func run() async throws {
        let clock = ExplorationClock(), writer = ExplorationWriter(), loader = ExplorationLoader()
        let model = ExplorationViewModel(uptime: { clock.now }, recordLoader: { try await loader.read($0) },
            recordWriter: { try await writer.write($0, $1) }, workspaceURL: URL(fileURLWithPath: "/controlled/research"))
        func file(_ name: String) -> URL { URL(fileURLWithPath: "/controlled/\(name)") }
        try check(model.frames.isEmpty && model.state == Array(repeating: 0, count: 32) && model.speed == 3,
            "Initial state is quiet with a three-step-per-second viewing pace")
        model.startPause(); clock.now = 0.32; model.tick()
        try check(model.frames.isEmpty && model.running, "Starting never invents a pulse or immediate step")
        clock.now = 1.0 / 3.0; model.tick()
        try check(model.frames.count == 1 && model.state.allSatisfy { $0 == 0 }, "The first quiet boundary records actual zero state")
        clock.now = 100; model.tick(); model.tick()
        try check(model.frames.count == 2, "A delayed timer advances at most one step without catch-up bursts")
        model.startPause(); clock.now = 1_000; model.tick()
        try check(!model.running && model.frames.count == 2, "Paused wall time creates no simulated steps")
        model.startPause(); clock.now = 1_000.1; model.tick()
        try check(model.frames.count == 2, "Resume starts a new viewing deadline excluding paused time")
        model.sendPulse(); model.sendPulse(); clock.now = 1_001; model.tick()
        try check(model.frames.count == 3 && model.frame?.pulse == true && model.state.contains { $0 != 0 },
            "Running pulse requests coalesce into one recorded pulse at the next boundary")
        model.startPause(); model.sendPulse()
        try check(!model.running && model.frames.count == 4 && model.frame?.pulse == true,
            "A paused pulse advances exactly one step")
        model.controls.leak = 0.2; model.controls.recurrenceEnabled = true; model.step()
        try check(model.frames.count == 5 && model.frame?.controls.leak == 0.2 && model.frame?.controls.recurrenceEnabled == true,
            "Edited controls are copied into the next recorded step")
        let historical = model.frames[1]
        model.scrub(1); model.controls.leak = 0.9
        try check(model.frame?.state == historical.state && model.frame?.controls.leak == historical.controls.leak,
            "Changing upcoming controls does not alter inspected historical state or controls")
        model.startPause()
        try check(model.row == 4, "Continue after scrubbing resumes the latest engine state")
        model.changeSpeed(20); clock.now += 0.04; model.tick()
        try check(model.frames.count == 5, "Speed changes rebase the viewing deadline")
        clock.now += 0.02; model.tick()
        try check(model.frames.count == 6 && model.frame?.time == 2, "Viewing speed never changes one-third-second simulation dt")
        model.leave(); clock.now += 500; model.tick()
        try check(!model.running && !model.replaying && model.frames.count == 6, "Leaving stops all progression and keeps history")
        model.scrub(0); model.replay(); clock.now += 0.06; model.tick()
        try check(model.row == 1 && model.frames.count == 6 && model.state == model.frames[1].state,
            "Replay selects raw saved states without creating or interpolating steps")
        model.scrub(5); model.replay()
        try check(model.row == 0 && model.replaying, "Replay from the end restarts at the first observation")
        model.leave()
        let fixture = model.record!
        try await wait("save requests") { (await writer.writes).count >= 1 }
        model.reset()
        try check(model.frames.isEmpty && model.controls.leak == 0.9 && model.controls.recurrenceEnabled,
            "Reset clears state and preserves chosen controls")
        model.seedText = "bad seed"; model.reset()
        try check(model.error != nil && model.frames.isEmpty, "Invalid reset seed is reported without replacing history")
        model.seedText = "43"; model.reset(); model.step()
        try check(model.record?.seed == 43 && model.frames.count == 1, "Seed changes take effect on Reset")
        try await wait("reset save") { (await writer.writes).contains { $0.record.frames.count == 6 } }
        let writes = await writer.writes
        let firstRunPaths = writes.filter { $0.record.seed == 20260909 }.map { $0.url.path }
        try check(Set(firstRunPaths).count == 1, "Autosaves update one atomic destination per exploration instead of creating duplicate runs")

        model.open(file("older")); try await wait("older loader") { await loader.waiting("older") }
        model.open(file("newer")); try await wait("newer loader") { await loader.waiting("newer") }
        await loader.release("newer", record: fixture)
        try await wait("newer imported") { !model.loading && model.frames.count == 6 }
        await loader.release("older", record: try ExplorationEngine(seed: 99).record)
        for _ in 0..<10 { await Task.yield() }
        try check(model.record?.seed == 20260909 && model.row == 0 && !model.running && !model.replaying,
            "The latest verified import opens paused at row zero; older reads cannot replace it")
        var expected = try ExplorationEngine(record: fixture)
        let next = try expected.advance(controls: model.controls, pulse: false)
        model.step()
        try check(model.state == next.state && model.frame?.step == 7,
            "Imported exploration continues exactly from its final state, not the inspected first row")
        model.open(file("reset")); try await wait("reset loader") { await loader.waiting("reset") }
        model.reset(); await loader.release("reset", record: fixture)
        for _ in 0..<10 { await Task.yield() }
        try check(model.frames.isEmpty && !model.loading, "Reset rejects a pending imported history")
        model.open(file("leave")); try await wait("leave loader") { await loader.waiting("leave") }
        model.leave(); await loader.release("leave", record: fixture)
        for _ in 0..<10 { await Task.yield() }
        try check(model.frames.isEmpty && !model.loading && !model.running, "Leaving rejects a late file result")
        model.sendPulse(); let retained = model.state
        model.open(file("bad")); try await wait("bad loader") { await loader.waiting("bad") }
        await loader.fail("bad")
        try await wait("failed import") { !model.loading && model.error != nil }
        try check(model.state == retained && model.frames.count == 1, "Malformed import retains the prior state and exposes its error")

        let delayedWriter = ExplorationWriter(); await delayedWriter.delay()
        let saving = ExplorationViewModel(recordWriter: { try await delayedWriter.write($0, $1) },
            workspaceURL: URL(fileURLWithPath: "/controlled/research"))
        saving.sendPulse(); try await wait("delayed save") { await delayedWriter.waiting() }
        saving.reset(); let resetStatus = saving.status
        await delayedWriter.release()
        for _ in 0..<10 { await Task.yield() }
        try check(saving.frames.isEmpty && saving.source.isEmpty && saving.status == resetStatus,
            "An old autosave completion cannot restore a reset source or overwrite its status")

        let failedSave = ExplorationViewModel(recordWriter: { _, _ in throw EssentialsError.invalid("Controlled save failure") },
            workspaceURL: URL(fileURLWithPath: "/controlled/research"))
        failedSave.sendPulse()
        try await wait("failed save diagnostic") { failedSave.saveIssue != nil }
        failedSave.reset()
        try check(failedSave.saveIssue?.contains("remains in memory") == true && failedSave.frames.isEmpty,
            "A failed save stays visible after Reset while its earlier snapshot remains retained")

        let capped = ExplorationViewModel(recordWriter: { _, _ in }, workspaceURL: URL(fileURLWithPath: "/controlled/research"))
        for _ in 0..<1800 { capped.step() }
        capped.startPause(); capped.sendPulse(); capped.step()
        try check(capped.frames.count == 1800 && capped.atLimit && !capped.running,
            "The finite 1,800-step boundary pauses safely and refuses extra state updates")
        print("\(passed) exploration lifecycle checks passed; injected memory I/O only, no model or live files.")
    }
}
Task { @MainActor in
    do { var checks = ExplorationViewModelChecks(); try await checks.run(); exit(0) }
    catch { print(error.localizedDescription); exit(1) }
}
dispatchMain()
