import Foundation
import CryptoKit

private struct StateSurfaceDataFailure: LocalizedError {
    let description: String
    var errorDescription: String? { description }
}

/// Read-only original resources, writable copied fixtures in a temporary folder.
/// Every retained row is checked against its existing frozen PCA export. Failure
/// fixtures then exercise hash, size, timing, identity and float validation.
private struct StateSurfaceDataChecks {
    private var passed = 0
    private mutating func check(_ condition: Bool, _ description: String) throws {
        guard condition else { throw StateSurfaceDataFailure(description: "FAIL: \(description)") }
        passed += 1
        print("PASS \(passed): \(description)")
    }
    private func rejects(_ work: () throws -> Void) -> Bool {
        do { try work(); return false } catch { return true }
    }
    private func sha(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }

    mutating func run() throws {
        guard CommandLine.arguments.count == 3 else {
            throw StateSurfaceDataFailure(description: "Use check-state-surface-data.sh")
        }
        let resources = URL(fileURLWithPath: CommandLine.arguments[1])
        let fixture = URL(fileURLWithPath: CommandLine.arguments[2])
        let geometryURL = resources.appendingPathComponent("state-geometry.json")
        let store = try EvidenceStore.load(historicalURL: resources.appendingPathComponent("data.json"), geometryURL: geometryURL)
        guard let replay = store.stateReplay else { throw StateSurfaceDataFailure(description: "Actual retained replay did not load") }
        try check(replay.frames.count == 1024 && replay.dimensions == 128 && replay.frames.allSatisfy { $0.activations.count == 128 },
                  "Original retained binary decodes 1024 ordered states of 128 coordinates")
        try check(replay.sourceSHA256 == "09ea4db8212809085aa2e07a040975f3095d7ef79d06eb8ba7404cc2424e282f"
            && replay.geometrySHA256 == sha(try Data(contentsOf: geometryURL))
            && replay.sourceIdentity(index: 1023) == "capture:\(replay.sourceSHA256):row:1023"
            && replay.frame(index: -1) == nil && replay.frame(index: 1024) == nil,
                  "Every row has a retained-byte source identity; out-of-range selection is unavailable")
        try check(replay.frames[0].activations.prefix(4) == [0.35750484466552734, 0.25459182262420654, -0.662847638130188, 0.4724888205528259],
                  "Little-endian Float32 decoding preserves original signed values exactly")
        let basis = store.geometry.pca
        var maximumProjectionError = 0.0
        var maximumNormError = 0.0
        for row in replay.frames {
            let centered = zip(row.activations, basis.mean).map(-)
            let scores = basis.components.map { axis in zip(centered, axis).reduce(0.0) { $0 + $1.0 * $1.1 } }
            maximumProjectionError = max(maximumProjectionError, zip(scores, row.geometry.pc).map { abs($0 - $1) }.max()!)
            let residual = centered.indices.map { node in
                centered[node] - scores.indices.reduce(0.0) { $0 + scores[$1] * basis.components[$1][node] }
            }
            let norm = sqrt(centered.reduce(0) { $0 + $1 * $1 })
            let residualNorm = sqrt(residual.reduce(0) { $0 + $1 * $1 })
            maximumNormError = max(maximumNormError, abs(norm - row.geometry.centeredNorm), abs(residualNorm - row.geometry.residualNorm))
        }
        try check(maximumProjectionError < 1e-12 && maximumNormError < 1e-12,
                  "All 1024 raw states independently reproduce retained PCA scores and full/residual distances within 1e-12")
        try check(replay.timingText.contains("no per-row time or paired fill")
            && replay.basisCompatibilityText.contains("live node-layout identity remains unverified"),
                  "Replay identifies its same-byte basis while keeping row time, fill alignment and live node identity unknown")

        let originalManifest = try Data(contentsOf: resources.appendingPathComponent("state-replay.json"))
        let originalRaw = try Data(contentsOf: resources.appendingPathComponent("state-replay.bin"))
        let originalGeometry = try Data(contentsOf: geometryURL)
        let manifestURL = fixture.appendingPathComponent("state-replay.json")
        let binaryURL = fixture.appendingPathComponent("state-replay.bin")
        let fixtureGeometryURL = fixture.appendingPathComponent("state-geometry.json")
        var fields = try JSONSerialization.jsonObject(with: originalManifest) as! [String: Any]
        func writeManifest() throws {
            try JSONSerialization.data(withJSONObject: fields, options: [.sortedKeys]).write(to: manifestURL)
        }
        func reset() throws {
            fields = try JSONSerialization.jsonObject(with: originalManifest) as! [String: Any]
            try originalManifest.write(to: manifestURL)
            try originalRaw.write(to: binaryURL)
            try originalGeometry.write(to: fixtureGeometryURL)
        }
        func load() throws -> StateReplayEvidence {
            try StateReplayEvidence.load(manifestURL: manifestURL, geometryURL: fixtureGeometryURL, geometry: store.geometry)
        }
        try reset()
        var corrupted = originalRaw
        corrupted[0] ^= 1
        try corrupted.write(to: binaryURL)
        try check(rejects { _ = try load() }, "A one-bit change in retained activation bytes is rejected")
        try originalRaw.dropLast().write(to: binaryURL)
        try check(rejects { _ = try load() }, "A truncated retained state cannot become a shorter valid replay")
        try (originalRaw + Data([0])).write(to: binaryURL)
        try check(rejects { _ = try load() }, "Extra binary bytes exceed the bounded capture read")
        try reset()
        try (originalGeometry + Data([32])).write(to: fixtureGeometryURL)
        try check(rejects { _ = try load() }, "Different frozen geometry bytes fail the manifest binding")
        try reset()
        fields["rows"] = Int.max
        try writeManifest()
        try check(rejects { _ = try load() }, "Oversized dimensions are rejected before multiplying byte counts")
        for (key, value) in [("per_row_timestamps_available", true as Any), ("paired_fill_available", true as Any),
                             ("node_layout_id", "invented" as Any), ("binary_file", "../outside.bin" as Any)] {
            try reset(); fields[key] = value; try writeManifest()
            try check(rejects { _ = try load() }, "Unsupported replay claim or path rejected: \(key)")
        }
        try reset()
        try Data(repeating: 32, count: 16 * 1024 + 1).write(to: manifestURL)
        try check(rejects { _ = try load() }, "Replay manifest reads are bounded to 16 KiB")

        // Rebind synthetic corrupt floats through all three hashes so rejection
        // must come from numeric validation rather than an earlier hash check.
        for (bits, description) in [(UInt32(0x7fc00000), "NaN"), (UInt32(0x7f800000), "infinity"),
                                    (Float(1.01).bitPattern, "activation outside −1…1")] {
            try reset()
            var changed = originalRaw
            var little = bits.littleEndian
            withUnsafeBytes(of: &little) { changed.replaceSubrange(0..<4, with: $0) }
            var geometryFields = try JSONSerialization.jsonObject(with: originalGeometry) as! [String: Any]
            var source = geometryFields["source"] as! [String: Any]
            var files = source["files"] as! [String: Any]
            var states = files["states"] as! [String: Any]
            states["sha256"] = sha(changed); files["states"] = states; source["files"] = files; geometryFields["source"] = source
            let changedGeometry = try JSONSerialization.data(withJSONObject: geometryFields, options: [.sortedKeys])
            let decodedGeometry = try EvidenceStore.decoder().decode(StateGeometryEvidence.self, from: changedGeometry)
            fields["source_sha256"] = sha(changed); fields["geometry_sha256"] = sha(changedGeometry)
            try changed.write(to: binaryURL); try changedGeometry.write(to: fixtureGeometryURL); try writeManifest()
            try check(rejects { _ = try StateReplayEvidence.load(manifestURL: manifestURL, geometryURL: fixtureGeometryURL, geometry: decodedGeometry) },
                      "Hash-consistent synthetic \(description) is rejected as invalid numeric evidence")
        }

        let values = replay.frames[0].activations
        let summary: [String: Double] = ["mean": values.reduce(0, +) / 128,
            "abs_mean": values.reduce(0) { $0 + abs($1) } / 128,
            "rms": sqrt(values.reduce(0) { $0 + $1 * $1 } / 128),
            "min": values.min()!, "max": values.max()!, "saturation_fraction": 0,
            "positive_fraction": 0.5, "finite_fraction": 1]
        let frame: [String: Any] = ["t_ms": 1000, "wall_clock_unix_ms": 1_788_757_903_000,
            "fill_pct": 63.5, "stage": "hold", "geom_rel": 1.0, "lambda1_rel": 0.8,
            "summary": summary, "top_active_node_indexes": Array(0..<8), "activations": values]
        let payload: [String: Any] = ["policy": "esn_activation_trace_v1", "updated_at_unix_ms": 1_788_757_903_000,
            "reservoir_dim": 128, "sample_interval_ms": 1000, "retained_secs": 180, "frames": [frame]]
        let batch = try LiveStateBatch.decode(data: JSONSerialization.data(withJSONObject: payload), basis: basis)
        try check(batch.samples[0].activations == values && batch.samples[0].fillPct == 63.5
            && batch.samples[0].basisCompatibilityText.contains("unverified"),
                  "Live decoder preserves every validated coordinate beside its co-recorded fill and unverified layout compatibility")
        print("\(passed) state-surface data checks passed; 1024 retained rows, synthetic failure fixtures only. Maximum PCA error \(maximumProjectionError), norm error \(maximumNormError).")
    }
}

do {
    var checks = StateSurfaceDataChecks()
    try checks.run()
} catch {
    print(error.localizedDescription)
    exit(1)
}
