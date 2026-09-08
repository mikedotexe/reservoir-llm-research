// Run with ../check-evidence.sh. Concatenated after the production source
// files, so this harness exercises their real decoder and actor-backed monitor.
// The only writable fixture is supplied by the runner's private temporary dir.
import Foundation

// SwiftPM normally supplies this accessor. Tests pass an explicit fixture bundle.
extension Bundle { static var module: Bundle { .main } }

private struct FixtureFailure: LocalizedError {
    let message: String
    var errorDescription: String? { message }
}

@MainActor
private struct EvidenceFixtureChecks {
    private var passed = 0

    private mutating func check(_ condition: Bool, _ description: String) throws {
        guard condition else { throw FixtureFailure(message: "FAIL: \(description)") }
        passed += 1
        print("PASS \(passed): \(description)")
    }

    private func waitForPoll(_ monitor: LiveTelemetryMonitor, after previous: Date?) async throws {
        let deadline = Date().addingTimeInterval(8)
        while Date() < deadline {
            if let current = monitor.lastPollAt, previous == nil || current > previous! { return }
            try await Task.sleep(for: .milliseconds(50))
        }
        throw FixtureFailure(message: "Monitor did not finish a fixture poll within 8 seconds. \(monitor.lastError ?? monitor.statusText)")
    }

    mutating func run() async throws {
        guard CommandLine.arguments.count == 3 else {
            throw FixtureFailure(message: "Use check-evidence.sh to provide the test bundle and temporary health fixture.")
        }
        let bundleURL = URL(fileURLWithPath: CommandLine.arguments[1])
        let fixtureURL = URL(fileURLWithPath: CommandLine.arguments[2])
        guard let bundle = Bundle(url: bundleURL) else {
            throw FixtureFailure(message: "Cannot open the runner's temporary resource bundle.")
        }
        let store = try EvidenceStore.load(bundle: bundle)
        try check(store.historical.samples.count == 507 && store.geometry.samples.count == 1024
            && store.geometry.pca.dimensions == 128 && store.geometry.pca.components.count == 3,
            "Actual bundled replay and PCA evidence decode: 507 rows, 1024 states, 128 nodes, 3 axes")
        try check(store.historical.startDate != nil && store.historical.endDate != nil
            && store.historical.fillRange.lowerBound == store.historical.samples.map(\.fillPct).min()
            && store.geometry.pca.retainedFraction < 0.15
            && store.historical.controller.snapshot?.provenance?.engineTS != nil,
            "Recorded clocks, observed fill range, and projection loss remain available")

        let config = store.historical.controller.structuralConfig
        for result in try await liveStateChecks(basis: store.geometry.pca,
            fixtureURL: fixtureURL.deletingLastPathComponent().appendingPathComponent("activation.json")) {
            try check(result.condition, result.description)
        }
        for result in referenceZoneChecks(bands: store.historical.bands, configuration: config) {
            try check(result.condition, result.description)
        }
        var replayClock = ReplayClock()
        replayClock.start(at: 10, uptime: 100)
        let delayedPosition = replayClock.advance(uptime: 100.5, rate: 60)
        let nextPosition = replayClock.advance(uptime: 100.75, rate: 20)
        try check(abs(delayedPosition - 40) < 1e-10 && abs(nextPosition - 45) < 1e-10,
                  "Delayed playback wakeups preserve elapsed time, including a change of speed")
        replayClock.start(at: 3, uptime: 1000)
        let resumedPosition = replayClock.advance(uptime: 1000.5, rate: 20)
        let duplicatePosition = replayClock.advance(uptime: 1000.5, rate: 20)
        try check(abs(resumedPosition - 13) < 1e-10 && duplicatePosition == resumedPosition,
                  "Playback restart excludes paused time; duplicate wakeups invent no progress")
        let baseClockMs = Date().timeIntervalSince1970 * 1000
        var clock: [String: Any] = ["session_id": 1, "snapshot_sequence": 10,
                                   "engine_t_s": 100.0, "wall_clock_unix_ms": baseClockMs]
        var structural: [String: Any] = ["active": true, "target_fill_pct": config.targetFillPct,
            "error_pct": 5.0, "integral": 0.5, "recovery_impulse_active": false,
            "reentry_active": false, "low_fill_escape_active": false]
        func writeFixture() throws {
            let payload: [String: Any] = ["fill_pct": config.targetFillPct + 3,
                "provenance": clock,
                "stable_core": ["controller_mode": "stable_core_recovery", "stage": "hold", "structural_pi": structural]]
            try JSONSerialization.data(withJSONObject: payload).write(to: fixtureURL, options: .atomic)
        }
        try writeFixture()
        let monitor = LiveTelemetryMonitor()
        defer { monitor.stop() }
        try check(!monitor.isRunning && monitor.samples.isEmpty && monitor.lastPollAt == nil,
                  "Live monitor starts stopped and performs no implicit read")
        monitor.start(path: fixtureURL.path, config: config)
        try await waitForPoll(monitor, after: nil)
        guard let first = monitor.latest else {
            throw FixtureFailure(message: monitor.lastError ?? "Minimal health fixture was not accepted.")
        }
        try check(first.leak == nil && first.spectralValues.isEmpty && first.geomRadius == nil
            && first.sourceReportedFillRatePctPerS == nil && first.controller.gateFilterPi == nil
            && first.elapsedS == 100 && abs(first.sourceDate.timeIntervalSince1970 * 1000 - baseClockMs) < 0.01,
            "Unavailable leak/spectrum/radius stay missing; source clock is preserved")
        let expectedP = config.kp * min(1, max(0, (5 - config.deadbandPct) / 20))
        let derived = first.derived
        try check(derived != nil && abs(derived!.pTerm - expectedP) < 1e-12
            && abs(derived!.iTerm - config.ki * 0.5) < 1e-12
            && derived!.controllerInputFillPct == config.targetFillPct + 5
            && derived!.snapshotMinusControllerFillPct == -2,
            "P/I use recorded controller error/integral, independently of later snapshot fill")

        var lastPoll = monitor.lastPollAt
        try await waitForPoll(monitor, after: lastPoll)
        try check(monitor.samples.count == 1 && monitor.latest?.snapshotSequence == 10,
                  "Duplicate source sequence does not append an invented observation")

        clock["snapshot_sequence"] = 11
        clock["engine_t_s"] = 90.0
        clock["wall_clock_unix_ms"] = baseClockMs + 1000
        lastPoll = monitor.lastPollAt
        try writeFixture()
        try await waitForPoll(monitor, after: lastPoll)
        try check(monitor.samples.count == 1 && monitor.statusText == "Source engine time moved backwards"
            && monitor.lastError != nil, "Decreasing engine time is rejected within one session")

        clock["session_id"] = 2
        clock["snapshot_sequence"] = 1
        clock["engine_t_s"] = 1.0
        lastPoll = monitor.lastPollAt
        try writeFixture()
        try await waitForPoll(monitor, after: lastPoll)
        try check(monitor.samples.count == 1 && monitor.latest?.sessionId == 2
            && monitor.latest?.elapsedS == 1, "New session replaces the ring, preventing a line across an engine reset")

        clock["snapshot_sequence"] = 2
        clock["engine_t_s"] = 2.0
        clock["wall_clock_unix_ms"] = baseClockMs - 1000
        lastPoll = monitor.lastPollAt
        try writeFixture()
        try await waitForPoll(monitor, after: lastPoll)
        try check(monitor.samples.count == 1 && monitor.statusText == "Source wall clock moved backwards",
                  "Decreasing source wall time is rejected")

        clock.removeValue(forKey: "wall_clock_unix_ms")
        lastPoll = monitor.lastPollAt
        try writeFixture()
        try await waitForPoll(monitor, after: lastPoll)
        try check(monitor.samples.count == 1 && monitor.statusText == "Source unavailable"
            && monitor.lastError?.contains("wall_clock_unix_ms") == true,
            "Missing source time causes an explicit error; local poll time never substitutes")

        clock["wall_clock_unix_ms"] = Date().timeIntervalSince1970 * 1000
        clock["snapshot_sequence"] = 3
        clock["engine_t_s"] = 3.0
        structural["recovery_impulse_active"] = true
        lastPoll = monitor.lastPollAt
        try writeFixture()
        try await waitForPoll(monitor, after: lastPoll)
        try check(monitor.samples.count == 2 && monitor.latest?.derived == nil,
                  "Recovery-path observation does not acquire ordinary-path P/I terms")
        monitor.stop()
        try check(!monitor.isRunning && monitor.statusText == "Stopped", "Stopping disables further polling")
        print("\(passed) checks passed. Fixture-only reads; no live-system paths accessed.")
    }
}

Task { @MainActor in
    do {
        var checks = EvidenceFixtureChecks()
        try await checks.run()
        exit(0)
    } catch {
        print(error.localizedDescription)
        exit(1)
    }
}
dispatchMain()
