// Headless MainActor lifecycle checks with controlled I/O and language waits.
// The actual view model and shared core run; no file panels or HTTP requests open.
import Foundation
import EssentialsCore

struct SurfaceRenderError: LocalizedError {
    let message: String
    init(_ message: String) { self.message = message }
    var errorDescription: String? { message }
}

private actor ControlledLoader {
    private var pending: [String: CheckedContinuation<RunRecord, Error>] = [:]
    private var completed: Set<String> = []
    func read(_ url: URL) async throws -> RunRecord {
        let name = url.lastPathComponent
        defer { completed.insert(name) }
        // Deliberately ignores cancellation to represent a blocked filesystem
        // read that completes after the user has changed their selection.
        return try await withCheckedThrowingContinuation { pending[name] = $0 }
    }
    func waiting(_ name: String) -> Bool { pending[name] != nil }
    func finished(_ name: String) -> Bool { completed.contains(name) }
    func release(_ name: String, _ record: RunRecord) { pending.removeValue(forKey: name)?.resume(returning: record) }
    func fail(_ name: String) { pending.removeValue(forKey: name)?.resume(throwing: EssentialsError.invalid("Controlled load failure")) }
}

private actor DelayedLanguage: LanguageBackend {
    private var continuation: CheckedContinuation<String, Never>?
    private var entered = false
    func reply(to request: LanguageRequest) async throws -> String {
        entered = true
        // Deliberately returns late even after its task is cancelled.
        return await withCheckedContinuation { continuation = $0 }
    }
    func waiting() -> Bool { entered && continuation != nil }
    func release() { continuation?.resume(returning: "A late reply must never alter the stopped run."); continuation = nil }
}

@MainActor private final class CheckClock { var now = 0.0 }

@MainActor private struct EssentialsViewModelChecks {
    var passed = 0
    mutating func check(_ condition: Bool, _ description: String) throws {
        guard condition else { throw SurfaceRenderError("FAIL: \(description)") }
        passed += 1; print("PASS \(passed): \(description)")
    }
    func wait(_ description: String, until condition: @MainActor () async -> Bool) async throws {
        for _ in 0..<1000 {
            if await condition() { return }
            try await Task.sleep(for: .milliseconds(5))
        }
        throw SurfaceRenderError("Timed out: \(description)")
    }
    func settle(_ name: String, loader: ControlledLoader) async throws {
        try await wait("load completion \(name)") { await loader.finished(name) }
        for _ in 0..<5 { await Task.yield() }
    }
    mutating func run() async throws {
        let fixture = try await EssentialsSession().run(spec: RunSpecification(stage: .reservoir, seed: 42, steps: 8))
        let other = try await EssentialsSession().run(spec: RunSpecification(stage: .spectralBridge, seed: 43, steps: 3))
        let loader = ControlledLoader(), clock = CheckClock()
        let model = EssentialsViewModel(recordLoader: { try await loader.read($0) }, uptime: { clock.now })
        func url(_ name: String) -> URL { URL(fileURLWithPath: "/controlled/\(name)") }

        model.open(url("stage"))
        try await wait("stage loader") { await loader.waiting("stage") }
        model.select(.spectralBridge)
        await loader.release("stage", fixture); try await settle("stage", loader: loader)
        try check(model.stage == .spectralBridge && model.record == nil && model.frames.isEmpty && !model.loading,
            "A late open cannot replace a newer stage selection")

        model.open(url("reset")); try await wait("reset loader") { await loader.waiting("reset") }
        model.reset(); await loader.release("reset", fixture); try await settle("reset", loader: loader)
        try check(model.record == nil && model.frames.isEmpty && model.status.hasPrefix("Reset"),
            "Reset invalidates a pending read without restoring the old run")

        model.open(url("hidden")); try await wait("hidden loader") { await loader.waiting("hidden") }
        model.stop(); await loader.release("hidden", fixture); try await settle("hidden", loader: loader)
        try check(!model.loading && model.record == nil && !model.playing,
            "Leaving Essentials cancels a pending open and pauses playback")

        model.open(url("older")); try await wait("older loader") { await loader.waiting("older") }
        model.open(url("newer")); try await wait("newer loader") { await loader.waiting("newer") }
        await loader.release("newer", fixture)
        try await wait("newer displayed") { model.record?.specification.seed == 42 && !model.loading }
        await loader.release("older", other); try await settle("older", loader: loader)
        try check(model.stage == .reservoir && model.record?.specification.seed == 42 && model.frames.count == 8,
            "Two overlapping opens retain the most recently requested file")

        model.speed = 1; model.replay(); clock.now = 0.75; model.tick()
        try check(model.row == 0 && model.playing, "Substep replay progress does not interpolate observed state values")
        model.changeSpeed(2); clock.now = 1; model.tick()
        try check(model.row == 1, "Changing speed preserves fractional progress at the old speed")
        clock.now = 1.125; model.replay()
        try check(!model.playing && model.row == 1, "Pausing records progress through the pause boundary")
        clock.now = 500; model.replay(); clock.now = 500.25; model.tick()
        try check(model.row == 2 && model.playing, "Resume excludes paused time and preserves the partial step")
        model.scrub(7); model.replay()
        try check(model.row == 0 && model.playing, "Replay restarts a completed trace at its first recorded step")
        model.changeSpeed(40); clock.now += 1; model.tick()
        try check(model.row == 7 && !model.playing, "Playback clamps at the final frame without inventing new state")

        model.open(url("bad")); try await wait("bad loader") { await loader.waiting("bad") }
        await loader.fail("bad")
        try await wait("bad error") { !model.loading && model.error != nil }
        try check(model.record?.specification.seed == 42 && model.frames.count == 8 && !model.playing,
            "A failed open retains the previous run and exposes the error")

        let delayed = DelayedLanguage(), runLoader = ControlledLoader()
        let running = EssentialsViewModel(sessionFactory: { EssentialsSession(backend: delayed) },
            recordLoader: { try await runLoader.read($0) })
        running.select(.llmLoop); running.stepCount = 90
        running.open(url("late-run")); try await wait("late-run loader") { await runLoader.waiting("late-run") }
        running.run(); try await wait("language wait") { await delayed.waiting() }
        await runLoader.release("late-run", fixture); try await settle("late-run", loader: runLoader)
        try check(running.running && running.stage == .llmLoop && running.record == nil && running.frames.count == 30,
            "Starting Run invalidates an older open while preserving the active language wait")
        running.select(.reservoir); running.reset()
        try check(running.stage == .llmLoop && running.frames.count == 30 && running.running,
            "Stage selection and reset cannot replace an active run")
        let held = running.frames.last?.time
        try await Task.sleep(for: .milliseconds(25))
        try check(running.frames.count == 30 && running.frames.last?.time == held,
            "Waiting for a full reply never advances simulated time")
        running.stop()
        try await wait("cancelled record retained") { !running.running && running.record != nil }
        try check(running.record?.status == .stopped && running.record?.frames.count == 30
            && running.record?.turns.last?.status == .cancelled && running.record?.turns.last?.reply == nil
            && running.record?.turns.last?.applicationStep == nil,
            "Stopping a pending reply retains completed frames and the cancelled turn without feedback")
        await delayed.release()
        for _ in 0..<5 { await Task.yield() }
        try check(running.record?.frames.count == 30 && running.record?.turns.last?.status == .cancelled
            && running.record?.turns.last?.reply == nil,
            "A backend that completes late cannot mutate the retained stopped run")
        running.select(.reservoir); running.select(.llmLoop)
        try check(running.record?.status == .stopped && running.frames.count == 30,
            "A stopped stage remains available after switching away and back")
        print("\(passed) Essentials view-model lifecycle checks passed; controlled memory fixtures only, no HTTP or live files.")
    }
}

Task { @MainActor in
    do { var checks = EssentialsViewModelChecks(); try await checks.run(); exit(0) }
    catch { print(error.localizedDescription); exit(1) }
}
dispatchMain()
