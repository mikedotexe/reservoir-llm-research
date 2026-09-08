import Foundation
import CryptoKit

struct NativeActionResponseFailure: LocalizedError {
    let message: String
    init(_ message: String) { self.message = message }
    var errorDescription: String? { message }
}

/// A receipt describes the immediate action at one successful native boundary.
/// `before` is the ordinary result of that same step, never a counterfactual run.
struct NativeActionResponse: Sendable {
    struct Identity: Decodable, Equatable, Sendable {
        let engineSessionId: String
        let modelId: String
        let nodeLayoutId: String
        let nodeCount: Int
        var text: String { "\(engineSessionId) · \(modelId) · \(nodeLayoutId)" }
    }
    struct Receipt: Decodable, Equatable, Sendable {
        let schemaVersion: Int
        let commandId: String
        let intentId: String
        let identity: Identity
        let patternId: String
        let patternSha256: String
        let direction: [Float]
        let status: String
        let observedAtUnixMs: UInt64
        let successfulStepId: UInt64?
        let pulseIndex: Int?
        let successOffset: UInt32?
        let requestedAmount: Float?
        let before: [Float]?
        let after: [Float]?
        let delta: [Float]?
        let attenuation: Float?
        let actualL2: Double?
        let maxAbsDelta: Float?
        let clipped: Bool
        let boundaryWaitUs: UInt64?
        let effectiveLeak: Float?
        let realizedNoise: [Float]?
        let reason: String?
        var hasState: Bool { status == "applied" || status == "no_op" }
        var isBoundary: Bool { hasState || status == "headroom_rejected" }
        var frameID: String { "\(commandId):\(successfulStepId ?? 0):\(pulseIndex ?? -1)" }
    }
    private struct Payload: Decodable {
        let schema: String
        let subject: String
        let scope: String
        let sourceHashes: [String: String]
        let clock: String
        let receipts: [Receipt]
    }
    let sourceHashes: [String: String]
    let receipts: [Receipt]
    let frames: [Receipt]
    let fileSHA256: String
    static let maximumBytes = 8 * 1024 * 1024
    static let maximumReceipts = 1024
    static let subject = "Minime native ESN rehearsal"
    static let scope = "isolated research copy; no running being"
    static let clock = "successful native step ids; supplied rehearsal clock is not measured wall time"
    var boundaries: [Receipt] { receipts.filter(\.isBoundary) }
    var identity: Identity? { boundaries.first?.identity }
    // One fixed scale for the entire accepted bundle. Never normalize each frame.
    var deltaScale: Double { max(1e-9, frames.compactMap(\.delta).flatMap { $0 }.map { abs(Double($0)) }.max() ?? 0) }
    var replacementKey: String { identity?.text ?? receipts.first?.identity.text ?? "empty" }

    static func read(url: URL) throws -> Self {
        let handle = try FileHandle(forReadingFrom: url)
        defer { try? handle.close() }
        let data = try handle.read(upToCount: maximumBytes + 1) ?? Data()
        return try decode(data: data)
    }
    static func decode(data: Data) throws -> Self {
        func require(_ ok: Bool, _ message: String) throws {
            if !ok { throw NativeActionResponseFailure(message) }
        }
        func hash(_ value: String) -> Bool { value.count == 64 && value.allSatisfy { "0123456789abcdef".contains($0) } }
        try require(!data.isEmpty && data.count <= maximumBytes, "Native receipts must be a nonempty JSON file of at most 8 MiB.")
        guard let raw = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              Set(raw.keys) == Set(["schema", "subject", "scope", "source_hashes", "fill", "reference_basis", "clock", "receipts"]),
              raw["fill"] is NSNull, raw["reference_basis"] is NSNull else {
            throw NativeActionResponseFailure("Native rehearsal receipts cannot claim a measured fill, reference basis or unsupported wrapper field.")
        }
        let receiptKeys: Set<String> = ["schema_version", "command_id", "intent_id", "identity", "pattern_id", "pattern_sha256", "direction", "status", "observed_at_unix_ms", "successful_step_id", "pulse_index", "success_offset", "requested_amount", "before", "after", "delta", "attenuation", "actual_l2", "max_abs_delta", "clipped", "boundary_wait_us", "effective_leak", "realized_noise", "reason"]
        guard let rawReceipts = raw["receipts"] as? [[String: Any]], rawReceipts.allSatisfy({ receipt in
            guard Set(receipt.keys).isSubset(of: receiptKeys), let identity = receipt["identity"] as? [String: Any] else { return false }
            return Set(identity.keys) == Set(["engine_session_id", "model_id", "node_layout_id", "node_count"])
        }) else { throw NativeActionResponseFailure("Unsupported receipt fields or native identity fields were rejected.") }
        let decoder = JSONDecoder(); decoder.keyDecodingStrategy = .convertFromSnakeCase
        let payload = try decoder.decode(Payload.self, from: data)
        try require(payload.schema == "research.native_action_response.v1" && payload.subject == subject
            && payload.scope == scope && payload.clock == clock, "Expected isolated native rehearsal receipts with successful-step identities; live evidence is a separate contract.")
        try require(!payload.sourceHashes.isEmpty && payload.sourceHashes.count <= 32
            && payload.sourceHashes.allSatisfy { !$0.key.isEmpty && $0.key.count <= 128 && hash($0.value) }, "Native source hashes are absent or malformed.")
        try require(!payload.receipts.isEmpty && payload.receipts.count <= maximumReceipts, "A native bundle must contain 1–1024 receipts.")
        let statuses: Set<String> = ["accepted", "applied", "no_op", "completed", "headroom_rejected", "expired", "cancelled", "superseded", "suspended", "identity_mismatch", "step_failed"]
        var frames: [Receipt] = [], boundaryFrames: [Receipt] = [], frameIDs: Set<String> = []
        for receipt in payload.receipts {
            try require(receipt.schemaVersion == 1 && statuses.contains(receipt.status), "Unsupported native action receipt version or status.")
            try require([receipt.commandId, receipt.intentId, receipt.patternId, receipt.identity.engineSessionId,
                receipt.identity.modelId, receipt.identity.nodeLayoutId].allSatisfy { !$0.isEmpty && $0.count <= 512 }
                && receipt.identity.nodeCount == 128 && hash(receipt.patternSha256), "Receipt action, model or coordinate identity is invalid.")
            try require(receipt.direction.count == 128 && receipt.direction.allSatisfy(\.isFinite), "Receipt direction is invalid.")
            if receipt.isBoundary {
                guard let before = receipt.before, let after = receipt.after, let delta = receipt.delta,
                      let step = receipt.successfulStepId, let pulse = receipt.pulseIndex,
                      let amount = receipt.requestedAmount, let attenuation = receipt.attenuation,
                      let l2 = receipt.actualL2, let maximum = receipt.maxAbsDelta,
                      let leak = receipt.effectiveLeak, let noise = receipt.realizedNoise,
                      receipt.successOffset != nil, receipt.boundaryWaitUs != nil else {
                    throw NativeActionResponseFailure("Applied receipts require their successful step, actual state, noise, leak and application measurements.")
                }
                try require(step > 0 && pulse >= 0 && [before, after, delta, noise].allSatisfy { $0.count == 128 && $0.allSatisfy(\.isFinite) }, "Applied receipt dimensions or successful-step identity are invalid.")
                try require(before.allSatisfy { abs($0) <= 1 } && after.allSatisfy { abs($0) <= 1 }
                    && amount.isFinite && attenuation.isFinite && (0...1).contains(attenuation)
                    && leak.isFinite && (0...1).contains(leak) && l2.isFinite && l2 >= 0 && maximum.isFinite,
                    "Applied controls and state must be finite and within their declared native bounds.")
                try require(zip(zip(after, before), delta).allSatisfy { ($0.0.0 - $0.0.1).bitPattern == $0.1.bitPattern }, "The action delta must equal Float32 applied minus ordinary state.")
                let expectedL2 = sqrt(delta.reduce(0.0) { $0 + Double($1) * Double($1) })
                try require(abs(expectedL2 - l2) <= 1e-12 * max(1, expectedL2)
                    && maximum == delta.map(abs).max(), "Action measurements disagree with all 128 observed coordinates.")
                try require((receipt.status != "no_op" && receipt.status != "headroom_rejected") || delta.allSatisfy { $0 == 0 }, "A no-op or headroom rejection cannot contain a state change.")
                try require(receipt.status != "headroom_rejected" || (attenuation == 0 && l2 == 0 && maximum == 0 && !receipt.clipped), "A headroom rejection must report zero applied amount.")
                try require(frameIDs.insert(receipt.frameID).inserted, "A native action boundary is duplicated.")
                if let previous = boundaryFrames.last {
                    try require(receipt.identity == previous.identity && step > previous.successfulStepId!, "A bundle cannot splice native identities or reverse successful steps.")
                }
                boundaryFrames.append(receipt)
                if receipt.hasState { frames.append(receipt) }
            } else {
                try require(receipt.before == nil && receipt.after == nil && receipt.delta == nil,
                    "Admission, terminal and failed events cannot present an applied state.")
            }
        }
        return Self(sourceHashes: payload.sourceHashes, receipts: payload.receipts, frames: frames,
            fileSHA256: SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined())
    }

    /// Atomic files replace complete batches. Overlapping applied receipts are immutable.
    func validateReplacement(of previous: Self) throws {
        guard (identity ?? receipts.first?.identity) == (previous.identity ?? previous.receipts.first?.identity) else { return }
        guard sourceHashes == previous.sourceHashes else {
            throw NativeActionResponseFailure("Source code identity changed within the same native session.")
        }
        let old = Dictionary(uniqueKeysWithValues: previous.boundaries.map { ($0.frameID, $0) })
        for frame in boundaries {
            if let prior = old[frame.frameID], frame != prior { throw NativeActionResponseFailure("An already observed native boundary changed in the same source identity.") }
        }
        if let before = previous.boundaries.last?.successfulStepId,
           (boundaries.last?.successfulStepId ?? 0) < before {
            throw NativeActionResponseFailure("The native source moved backwards; the retained batch remains visible.")
        }
    }
}
