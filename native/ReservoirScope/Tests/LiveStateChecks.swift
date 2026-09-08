import Foundation

/// Fixture-only checks, concatenated with the production models by the runner.
/// The supplied URL must be inside the runner's private temporary directory.
@MainActor
func liveStateChecks(basis recordedBasis: PrincipalComponents, fixtureURL: URL) async throws
    -> [(condition: Bool, description: String)] {
    var results: [(condition: Bool, description: String)] = []
    func check(_ condition: Bool, _ description: String) throws {
        guard condition else { throw LiveStateFixtureError.failed(description) }
        results.append((true, description))
    }
    func rejects(_ action: () throws -> Void) -> Bool {
        do { try action(); return false } catch { return true }
    }
    var mean = Array(repeating: 0.0, count: 128)
    mean[0] = 0.1
    let axes = (0..<3).map { component in (0..<128).map { $0 == component ? 1.0 : 0.0 } }
    var basisFields: [String: Any] = ["frozen": true, "rows": 2, "dimensions": 128,
        "mean": mean, "components": axes, "eigenvalues": Array(repeating: 1.0, count: 128),
        "explained_variance_ratio": Array(repeating: 1.0 / 128, count: 128),
        "retained_fraction": 3.0 / 128, "normalization": ["reference_radius": 0.1]]
    func basisFromFields() throws -> PrincipalComponents {
        try EvidenceStore.decoder().decode(PrincipalComponents.self,
            from: JSONSerialization.data(withJSONObject: basisFields, options: [.sortedKeys]))
    }
    let basis = try basisFromFields()
    let clock = UInt64(Date().timeIntervalSince1970 * 1000)
    var values = Array(repeating: 0.0, count: 128)
    values[0] = 0.3; values[1] = -0.4; values[2] = 0.5; values[3] = 0.2
    func frame(_ elapsed: UInt64, wall: UInt64, fill: Double = 68) -> [String: Any] {
        let summary: [String: Double] = ["mean": values.reduce(0, +) / 128,
            "abs_mean": values.reduce(0) { $0 + abs($1) } / 128,
            "rms": sqrt(values.reduce(0) { $0 + $1 * $1 } / 128),
            "min": values.min()!, "max": values.max()!, "saturation_fraction": 0,
            "positive_fraction": 3.0 / 128, "finite_fraction": 1]
        return ["t_ms": elapsed, "wall_clock_unix_ms": wall, "fill_pct": fill,
                "stage": "hold", "geom_rel": 1.0, "lambda1_rel": 0.8,
                "summary": summary, "top_active_node_indexes": [2, 1, 0, 3, 4, 5, 6, 7],
                "activations": values]
    }
    var frames = [frame(10_000, wall: clock - 3_000), frame(12_500, wall: clock - 500)]
    var payload: [String: Any] = ["policy": "esn_activation_trace_v1", "reservoir_dim": 128,
        "sample_interval_ms": 1000, "retained_secs": 180]
    func data() throws -> Data {
        payload["frames"] = frames
        payload["updated_at_unix_ms"] = frames.last?["wall_clock_unix_ms"]
        return try JSONSerialization.data(withJSONObject: payload, options: [.sortedKeys])
    }
    let firstData = try data()
    let first = try LiveStateBatch.decode(data: firstData, basis: basis)
    let geometry = first.samples[0].geometry
    try check(zip(geometry.pc, [0.2, -0.4, 0.5]).allSatisfy { abs($0 - $1) < 1e-12 }
        && abs(geometry.centeredNorm * geometry.centeredNorm - 0.49) < 1e-12
        && abs(geometry.projectedNorm * geometry.projectedNorm - 0.45) < 1e-12
        && abs(geometry.residualNorm - 0.2) < 1e-12
        && geometry.centeredNorm > basis.normalization.referenceRadius,
        "Live geometry uses the frozen mean and axes, preserves residual distance, and never clips to the historical radius")
    try check(first.samples[1].tMs - first.samples[0].tMs == 2_500
        && first.samples[1].wallClockUnixMs == clock - 500
        && first.samples[1].fillPct == 68 && first.samples[1].stage == "hold"
        && abs(first.samples[0].retainedDistanceFraction! - 0.45 / 0.49) < 1e-12,
        "Recorder times, co-recorded fill/stage, and per-state retained distance remain distinct from nominal cadence and fit variance")
    try validateLiveStateBasis(recordedBasis)
    try check(try LiveStateBatch.decode(data: firstData, basis: recordedBasis).samples.count == 2,
        "The actual bundled frozen PCA basis accepts finite 128-node activation frames")
    basisFields["components"] = [axes[0], axes[0], axes[2]]
    try check(rejects { try validateLiveStateBasis(basisFromFields()) }, "Non-orthogonal PCA axes are rejected before live projection")
    basisFields["components"] = axes
    basisFields["mean"] = [0.0]
    try check(rejects { try validateLiveStateBasis(basisFromFields()) }, "A mean with the wrong node count is rejected")

    payload["policy"] = "esn_activation_trace_v2"
    try check(rejects { _ = try LiveStateBatch.decode(data: data(), basis: basis) }, "An unaudited activation policy is rejected")
    payload["policy"] = "esn_activation_trace_v1"
    frames[0]["activations"] = Array(values.dropLast())
    try check(rejects { _ = try LiveStateBatch.decode(data: data(), basis: basis) }, "Every frame's node count is validated independently of the header")
    frames[0] = frame(10_000, wall: clock - 3_000)
    var sanitizedSummary = frames[0]["summary"] as! [String: Double]
    sanitizedSummary["finite_fraction"] = 127.0 / 128
    frames[0]["summary"] = sanitizedSummary
    try check(rejects { _ = try LiveStateBatch.decode(data: data(), basis: basis) }, "A producer-sanitized vector is withheld instead of displaying replacement zeros as measured state")
    frames[0] = frame(10_000, wall: clock - 3_000, fill: 101)
    try check(rejects { _ = try LiveStateBatch.decode(data: data(), basis: basis) }, "Invalid fill is rejected rather than visually clamped")
    frames[0] = frame(10_000, wall: clock - 3_000)
    frames[1] = frames[0]
    try check(rejects { _ = try LiveStateBatch.decode(data: data(), basis: basis) }, "Duplicate source frames are rejected")
    frames = [frame(12_500, wall: clock - 500), frame(10_000, wall: clock - 3_000)]
    try check(rejects { _ = try LiveStateBatch.decode(data: data(), basis: basis) }, "Reversed recorder clocks are rejected")
    frames = (0..<181).map { frame(UInt64($0) * 2500, wall: clock + UInt64($0) * 2500) }
    try check(rejects { _ = try LiveStateBatch.decode(data: data(), basis: basis) }
        && rejects { _ = try LiveStateBatch.decode(data: Data(repeating: 32, count: 2 * 1024 * 1024 + 1), basis: basis) },
        "Frame-count and 2 MiB limits bound both decoded geometry and file reads")

    var continuity = LiveStateContinuity()
    _ = try continuity.accept(first)
    let duplicate = try continuity.accept(first)
    if case .unchanged = duplicate {
        try check(true, "Identical bytes do not invent a fresh activation observation")
    } else { throw LiveStateFixtureError.failed("Identical batch was replaced") }
    frames = [frame(10_000, wall: clock - 3_000), frame(12_500, wall: clock - 500, fill: 69)]
    try check(rejects { _ = try continuity.accept(LiveStateBatch.decode(data: data(), basis: basis)) }
        && continuity.accepted?.samples.last?.fillPct == 68,
        "Changed contents at the same source clock preserve the last accepted batch and raise an error")
    frames = [frame(12_500, wall: clock - 500, fill: 69), frame(15_000, wall: clock + 2_000)]
    try check(rejects { _ = try continuity.accept(LiveStateBatch.decode(data: data(), basis: basis)) },
        "A new batch cannot rewrite an already observed overlapping frame")
    frames = [frame(12_500, wall: clock - 500), frame(15_000, wall: clock + 2_000)]
    _ = try continuity.accept(LiveStateBatch.decode(data: data(), basis: basis))
    try check(continuity.accepted?.samples.count == 2 && continuity.accepted?.samples.first?.tMs == 12_500,
        "Rolling source batches replace the full displayed batch instead of appending or bridging snapshots")
    frames = [frame(1_000, wall: clock + 3_000)]
    let reset = try continuity.accept(LiveStateBatch.decode(data: data(), basis: basis))
    if case .replaced(let description) = reset {
        try check(description.contains("restarted") && description.contains("unverified")
            && continuity.accepted?.samples.count == 1,
            "A recorder clock reset starts a replacement batch and explicitly leaves boot identity unverified")
    } else { throw LiveStateFixtureError.failed("Recorder reset did not replace the batch") }

    let monitor = LiveStateMonitor()
    defer { monitor.stop() }
    try check(!monitor.isRunning && monitor.samples.isEmpty && monitor.lastPollAt == nil,
        "Activation monitoring starts stopped with no implicit file access")
    try firstData.write(to: fixtureURL, options: .atomic)
    monitor.start(path: fixtureURL.path, basis: basis)
    try await waitForLiveStatePoll(monitor, after: nil)
    let observedAt = monitor.latest?.receivedAt
    let firstPoll = monitor.lastPollAt
    try await waitForLiveStatePoll(monitor, after: firstPoll)
    try check(monitor.samples.count == 2 && monitor.latest?.receivedAt == observedAt
        && monitor.lastError == nil && monitor.statusText.contains("Waiting"),
        "Actual read-only polling holds identical bytes without refreshing their observation time")
    let previousPoll = monitor.lastPollAt
    try Data("{}".utf8).write(to: fixtureURL, options: .atomic)
    try await waitForLiveStatePoll(monitor, after: previousPoll)
    try check(monitor.samples.count == 2 && monitor.latest?.receivedAt == observedAt
        && monitor.lastError != nil && monitor.statusText.contains("retaining"),
        "A malformed source keeps the last accepted geometry with an explicit error")
    monitor.stop()
    try check(!monitor.isRunning && monitor.statusText == "Stopped", "Stopping activation monitoring disables further polling")
    return results
}

@MainActor
private func waitForLiveStatePoll(_ monitor: LiveStateMonitor, after previous: Date?) async throws {
    let deadline = Date().addingTimeInterval(8)
    while Date() < deadline {
        if let current = monitor.lastPollAt, previous == nil || current > previous! { return }
        try await Task.sleep(for: .milliseconds(40))
    }
    throw LiveStateFixtureError.failed("Activation poll did not finish: \(monitor.lastError ?? monitor.statusText)")
}

private enum LiveStateFixtureError: LocalizedError {
    case failed(String)
    var errorDescription: String? { switch self { case .failed(let text): return "Live-state fixture failure: \(text)" } }
}
