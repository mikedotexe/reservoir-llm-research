import Foundation

private struct NativeActionResponseChecks {
    private var passed = 0
    private mutating func check(_ condition: Bool, _ description: String) throws {
        guard condition else { throw NativeActionResponseFailure("FAIL: \(description)") }
        passed += 1; print("PASS \(passed): \(description)")
    }
    private func rejects(_ work: () throws -> Void) -> Bool { do { try work(); return false } catch { return true } }
    mutating func run() throws {
        let hash = String(repeating: "a", count: 64)
        var before = Array(repeating: Float(0.1), count: 128), after = before
        before[2] = -0.7; after = before; after[0] += 0.001
        let delta = zip(after, before).map(-), noise = Array(repeating: Float(0), count: 128)
        var direction = noise; direction[0] = 1
        let l2 = sqrt(delta.reduce(0.0) { $0 + Double($1) * Double($1) })
        let identity: [String: Any] = ["engine_session_id": "rehearsal-session", "model_id": hash, "node_layout_id": "native-index-v1", "node_count": 128]
        let pulse: [String: Any] = ["schema_version": 1, "command_id": "command-1", "intent_id": "intent-1", "identity": identity,
            "pattern_id": "coordinate-0", "pattern_sha256": hash, "direction": direction, "status": "applied",
            "observed_at_unix_ms": UInt64(1_789_000_000_000), "successful_step_id": UInt64(9_007_199_254_740_993),
            "pulse_index": 0, "success_offset": 0, "requested_amount": Float(0.002), "before": before, "after": after,
            "delta": delta, "attenuation": Float(0.5), "actual_l2": l2, "max_abs_delta": delta.map(abs).max()!,
            "clipped": true, "boundary_wait_us": 28, "effective_leak": Float(0.3), "realized_noise": noise]
        var terminal = pulse
        terminal["status"] = "completed"
        for key in ["before", "after", "delta", "attenuation", "actual_l2", "max_abs_delta", "requested_amount", "effective_leak", "realized_noise", "pulse_index", "success_offset", "boundary_wait_us"] { terminal[key] = NSNull() }
        let wrapper: [String: Any] = ["schema": "research.native_action_response.v1", "subject": NativeActionResponse.subject,
            "scope": NativeActionResponse.scope, "source_hashes": ["esn_rs": hash], "fill": NSNull(), "reference_basis": NSNull(),
            "clock": NativeActionResponse.clock, "receipts": [pulse, terminal]]
        func encode(_ raw: [String: Any]) throws -> Data { try JSONSerialization.data(withJSONObject: raw, options: [.sortedKeys]) }
        func decode(_ raw: [String: Any]) throws -> NativeActionResponse { try NativeActionResponse.decode(data: encode(raw)) }
        func invalid(_ mutation: (inout [String: Any]) -> Void) throws -> Bool {
            var raw = wrapper; mutation(&raw); let data = try encode(raw)
            return rejects { _ = try NativeActionResponse.decode(data: data) }
        }
        func mutatePulse(_ raw: inout [String: Any], _ change: (inout [String: Any]) -> Void) {
            var receipts = raw["receipts"] as! [[String: Any]]; change(&receipts[0]); raw["receipts"] = receipts
        }
        let evidence = try decode(wrapper)
        try check(evidence.frames.count == 1 && evidence.receipts.count == 2 && evidence.frames[0].before == before
            && evidence.frames[0].after == after, "The importer retains all 128 ordinary and applied Float32 coordinates, apart from terminal events")
        try check(evidence.frames[0].delta == delta && evidence.frames[0].actualL2 == l2,
                  "The full immediate Float32 difference and L2 match the paired states")
        try check(evidence.frames[0].requestedAmount == 0.002 && evidence.frames[0].attenuation == 0.5 && evidence.frames[0].clipped,
                  "Requested dose and actual attenuated application remain distinct")
        try check(evidence.frames[0].successfulStepId == 9_007_199_254_740_993 && evidence.frames[0].effectiveLeak == 0.3
            && evidence.frames[0].realizedNoise == noise, "Step IDs preserve UInt64 precision and retain actual leak and per-node noise")
        try check(evidence.deltaScale == Double(delta.map(abs).max()!) && evidence.fileSHA256.count == 64,
                  "The complete bundle defines one fixed delta scale and a computed imported-file identity")
        try check(rejects { _ = try NativeActionResponse.decode(data: Data()) }, "Empty reads cannot replace accepted observations")
        try check(rejects { _ = try NativeActionResponse.decode(data: Data(repeating: 32, count: NativeActionResponse.maximumBytes + 1)) }, "The 8 MiB limit is enforced before JSON parsing")
        try check(try invalid { $0["subject"] = "live Minime" }, "A rehearsal cannot be relabeled as a running being")
        try check(try invalid { $0["fill"] = 68.0 }, "Unmeasured fill is rejected")
        try check(try invalid { $0["reference_basis"] = "native PCA" }, "An unverified PCA association is rejected")
        try check(try invalid { $0["clock"] = "reservoir elapsed seconds" }, "Observation clocks cannot become reservoir duration")
        try check(try invalid { $0["source_hashes"] = ["esn_rs": "unknown"] }, "Source hashes must have a complete SHA-256 representation")
        try check(try invalid { mutatePulse(&$0) { $0["after"] = [0.0] } }, "Malformed state dimensions are rejected")
        try check(try invalid { mutatePulse(&$0) { var x = after; x[4] = 1.1; $0["after"] = x } }, "Out-of-bounds native state is rejected")
        try check(try invalid { mutatePulse(&$0) { var x = delta; x[3] = 0.001; $0["delta"] = x } }, "A displayed difference must equal every original coordinate difference")
        try check(try invalid { mutatePulse(&$0) { $0["actual_l2"] = 0.5 } }, "Full-state action size is recomputed rather than trusted")
        try check(try invalid { mutatePulse(&$0) { $0["max_abs_delta"] = 0.5 } }, "Maximum displacement is independently validated")
        try check(try invalid { mutatePulse(&$0) { $0["status"] = "step_failed" } }, "A failed step cannot expose applied-state geometry")
        try check(try invalid { mutatePulse(&$0) { $0["status"] = "no_op" } }, "A no-op cannot conceal an actual state change")
        try check(try invalid { mutatePulse(&$0) { $0["successful_step_id"] = NSNull() } }, "Applied states require an exact successful-step ID")
        try check(try invalid { mutatePulse(&$0) { $0["effective_leak"] = NSNull() } }, "Applied states require effective leak")
        try check(try invalid { mutatePulse(&$0) { $0["realized_noise"] = NSNull() } }, "Applied states require the actual noise vector")
        try check(try invalid { $0["receipts"] = [pulse, pulse] }, "Duplicate pulse boundaries are rejected")
        try check(try invalid { var second = pulse; second["successful_step_id"] = 1; second["pulse_index"] = 1; $0["receipts"] = [pulse, second] }, "Successful steps cannot run backwards")
        try check(try invalid { var second = pulse; var id = identity; id["engine_session_id"] = "other"; second["identity"] = id; second["pulse_index"] = 1; $0["receipts"] = [pulse, second] }, "One bundle cannot splice native process identities")
        try check(try invalid { $0["receipts"] = Array(repeating: terminal, count: NativeActionResponse.maximumReceipts + 1) }, "The receipt-count limit is enforced")
        try evidence.validateReplacement(of: evidence)
        try check(true, "An unchanged atomic bundle is accepted without inventing new frames")
        var changed = wrapper
        mutatePulse(&changed) { $0["observed_at_unix_ms"] = UInt64(1_789_000_000_001) }
        let changedEvidence = try decode(changed)
        try check(rejects { try changedEvidence.validateReplacement(of: evidence) }, "An overlapping application receipt is immutable within its source")
        var older = wrapper
        mutatePulse(&older) { $0["successful_step_id"] = 1 }
        let olderEvidence = try decode(older)
        try check(rejects { try olderEvidence.validateReplacement(of: evidence) }, "An atomic file cannot replace an observed source with an older step")
        var newSession = wrapper
        mutatePulse(&newSession) { var id = identity; id["engine_session_id"] = "new-session"; $0["identity"] = id; $0["successful_step_id"] = 1 }
        let newEvidence = try decode(newSession); try newEvidence.validateReplacement(of: evidence)
        try check(newEvidence.replacementKey != evidence.replacementKey, "A new session replaces the whole path instead of joining it")
        try check(try invalid { mutatePulse(&$0) { $0["fill"] = 68.0 } }, "Unsupported per-receipt fields cannot add a hidden fill or timing claim")
        var sourceChanged = wrapper; sourceChanged["source_hashes"] = ["esn_rs": String(repeating: "b", count: 64)]
        let sourceEvidence = try decode(sourceChanged)
        try check(rejects { try sourceEvidence.validateReplacement(of: evidence) }, "Source hashes cannot change within an existing native session")
        var rejected = pulse
        rejected["status"] = "headroom_rejected"; rejected["before"] = before; rejected["after"] = before
        rejected["delta"] = noise; rejected["attenuation"] = Float(0); rejected["actual_l2"] = 0.0
        rejected["max_abs_delta"] = Float(0); rejected["clipped"] = false
        var rejectedWrapper = wrapper; rejectedWrapper["receipts"] = [rejected, terminal]
        let rejectionEvidence = try decode(rejectedWrapper)
        try check(rejectionEvidence.frames.isEmpty && rejectionEvidence.boundaries.count == 1,
                  "A headroom rejection retains its verified zero difference without becoming applied geometry")
        try check(try invalid { mutatePulse(&$0) { $0["status"] = "headroom_rejected" } },
                  "A rejected pulse cannot claim a positive actual state displacement")
        var zeroClock = wrapper; mutatePulse(&zeroClock) { $0["observed_at_unix_ms"] = UInt64(0) }
        let zeroClockEvidence = try decode(zeroClock)
        try check(zeroClockEvidence.frames[0].observedAtUnixMs == 0, "A supplied rehearsal clock may start at zero without being treated as a measured epoch")
        try check(try invalid { var second = pulse; second["pulse_index"] = 1; $0["receipts"] = [pulse, second] },
                  "The single-action native contract cannot have two pulses at one successful step")
        if CommandLine.arguments.count > 1 {
            let actual = try NativeActionResponse.read(url: URL(fileURLWithPath: CommandLine.arguments[1]))
            try check(!actual.frames.isEmpty, "The retained native producer artifact passes the same complete receipt validation")
            print("NATIVE ARTIFACT: \(actual.frames.count) applied boundaries; SHA-256 \(actual.fileSHA256)")
        }
        print("\(passed) native-action response checks passed; synthetic contracts and optional retained native artifact only.")
    }
}

do { var checks = NativeActionResponseChecks(); try checks.run() }
catch { print(error.localizedDescription); exit(1) }
