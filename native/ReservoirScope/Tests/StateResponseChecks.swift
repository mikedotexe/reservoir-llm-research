import Foundation
import CryptoKit

private struct StateResponseChecks {
    private var passed = 0
    private mutating func check(_ condition: Bool, _ description: String) throws {
        guard condition else { throw StateResponseFailure("FAIL: \(description)") }
        passed += 1; print("PASS \(passed): \(description)")
    }
    private func sha(_ data: Data) -> String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
    private func rejects(_ work: () throws -> Void) -> Bool { do { try work(); return false } catch { return true } }
    mutating func run() throws {
        guard CommandLine.arguments.count == 2 else { throw StateResponseFailure("Use check-state-response.sh") }
        let resource = URL(fileURLWithPath: CommandLine.arguments[1])
        let data = try Data(contentsOf: resource)
        let evidence = try StateResponseEvidence.load(url: resource)
        try check(evidence.frames.count == 65 && evidence.nodeCount == 128
            && evidence.frames.allSatisfy { $0.control.count == 128 && $0.intervention.count == 128 && $0.delta.count == 128 },
                  "The byte-bound retained response contains 65 paired 128-coordinate boundaries")
        try check(sha(data) == StateResponseEvidence.retainedSHA256
            && evidence.evidenceIdentity.contains(evidence.runId)
            && evidence.sourceResultsSha256.count == 64 && evidence.modelHashes.count == 2,
                  "The exact resource, source result, run and both model matrices retain their identities")
        try check(evidence.frame(at: -1) == nil && evidence.frame(at: 65) == nil
            && evidence.frames.first?.originalBoundaryStep == 200 && evidence.frames.last?.originalBoundaryStep == 264,
                  "The cursor addresses raw simulation boundaries 200–264 and rejects out-of-range access")
        try check(evidence.fixedDeltaScale == 0.001 && evidence.frames[0].delta.dropFirst().allSatisfy { $0 == 0 }
            && abs(evidence.frames[0].delta[0] - 0.001) < 1e-14 && evidence.frames.last?.separationL2 == 0,
                  "Boundary zero already contains the declared coordinate-zero impulse; a settled frame keeps the same scale")
        try check(evidence.resultSummary.returnBoundary == 2 && evidence.resultSummary.peakGainOverInitial == 1
            && evidence.frames[2..<10].allSatisfy { $0.separationL2 <= evidence.returnThreshold },
                  "Full vectors independently validate initial displacement, peak, threshold and eight-boundary return")
        try check(evidence.subject.contains("not live Minime") && evidence.clock.contains("no measured seconds")
            && evidence.scope.contains("no native checkpoint parity claim") && evidence.nodeLayout.contains("not established compatible"),
                  "The fixture distinguishes the simulated parent, ordinal time and unverified native compatibility")

        let original = try JSONSerialization.jsonObject(with: data) as! [String: Any]
        func encoded(_ mutation: (inout [String: Any]) -> Void) throws -> Data {
            var copy = original; mutation(&copy)
            return try JSONSerialization.data(withJSONObject: copy, options: [.sortedKeys])
        }
        func invalid(_ mutation: (inout [String: Any]) -> Void) throws -> Bool {
            let changed = try encoded(mutation)
            return rejects { _ = try StateResponseEvidence.decode(data: changed, expectedSHA256: sha(changed)) }
        }
        func mutateFrame(_ raw: inout [String: Any], at index: Int = 0, _ change: (inout [String: Any]) -> Void) {
            var frames = raw["frames"] as! [[String: Any]]
            change(&frames[index]); raw["frames"] = frames
        }
        var corrupted = data; corrupted[corrupted.count - 2] ^= 1
        try check(rejects { _ = try StateResponseEvidence.decode(data: corrupted) }, "A single changed byte fails the retained resource identity")
        try check(rejects { _ = try StateResponseEvidence.decode(data: Data(repeating: 32, count: StateResponseEvidence.maximumBytes + 1)) },
                  "Oversized evidence is refused before JSON decoding")
        try check(try invalid { $0["node_count"] = Int.max }, "Unsupported node dimensions are rejected")
        try check(try invalid { $0["frames"] = Array(($0["frames"] as! [[String: Any]]).dropLast()) }, "A missing boundary cannot silently shorten the replay")
        try check(try invalid { mutateFrame(&$0, at: 1) { $0["sample_index"] = 0 } }, "Duplicate or reordered sample boundaries are rejected")
        try check(try invalid { mutateFrame(&$0) { $0["original_boundary_step"] = 201 } }, "Original simulation-step identity is validated")
        try check(try invalid { mutateFrame(&$0) { $0["control"] = [0.0] } }, "A malformed vector is rejected even with a matching synthetic resource hash")
        try check(try invalid { mutateFrame(&$0) { var x = $0["control"] as! [Double]; x[0] = 1.01; $0["control"] = x } },
                  "Unbounded native-style activation values are rejected")
        try check(try invalid { mutateFrame(&$0) { var x = $0["delta"] as! [Double]; x[3] = 0.1; $0["delta"] = x } },
                  "A rendered delta must equal the exact paired state difference")
        try check(try invalid { mutateFrame(&$0) { $0["separation_l2"] = 0.1 } }, "Distance metadata must agree with all 128 coordinates")
        try check(try invalid { var s = $0["result_summary"] as! [String: Any]; s["return_boundary"] = 3; $0["result_summary"] = s },
                  "A wrong return claim is rejected by the threshold/dwell calculation")
        try check(try invalid { var s = $0["result_summary"] as! [String: Any]; s["peak_gain_over_initial"] = 2; $0["result_summary"] = s },
                  "A wrong amplification claim is rejected by the complete path")
        try check(try invalid { $0["fill"] = 68.0 }, "A fabricated measured fill cannot enter the simulation resource")
        try check(try invalid { $0["reference_basis"] = "native-minime-pca" }, "A fabricated native PCA join is rejected")
        try check(try invalid { $0["clock"] = "measured seconds" }, "Ordinal boundaries cannot be relabeled measured time")
        try check(try invalid { mutateFrame(&$0) { $0["elapsed_seconds"] = 0.5 } }, "Unrecorded per-frame seconds are rejected")
        try check(try invalid { $0["subject"] = "live Minime" }, "The simulated parent cannot be relabeled as live Minime")
        try check(try invalid { $0["source_results_sha256"] = "unknown" }, "Malformed source hashes are rejected")
        let notJSON = Data("{\"frames\":[NaN,Infinity]}".utf8)
        try check(rejects { _ = try StateResponseEvidence.decode(data: notJSON, expectedSHA256: sha(notJSON)) },
                  "Nonfinite JSON extensions cannot become numeric observations")
        print("\(passed) state-response checks passed; retained paired simulation and synthetic failure fixtures only.")
    }
}

do {
    var checks = StateResponseChecks(); try checks.run()
} catch {
    print(error.localizedDescription); exit(1)
}
