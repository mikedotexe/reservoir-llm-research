import Foundation
import CryptoKit

/// Explicit local exports from the shared reader. Source paths are labels, never opened.
struct GeometryBookmarkPacket {
    let body: GeometryBookmarkBody
    let digest: String
    let records: [GeometryBookmarkEntry]

    static func load(_ url: URL) throws -> Self {
        let file = try FileHandle(forReadingFrom: url)
        defer { try? file.close() }
        let data = try file.read(upToCount: 4 * 1024 * 1024 + 1) ?? Data()
        return try decode(data)
    }

    static func decode(_ data: Data) throws -> Self {
        try require(!data.isEmpty && data.count <= 4 * 1024 * 1024, "Packet must be at most 4 MiB")
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let envelope = try decoder.decode(GeometryBookmarkEnvelope.self, from: data)
        try require(envelope.format == "question-geometry-v1" && geometryHash(envelope.bodyJson) == envelope.bodySha256,
                    "Unsupported packet or changed body bytes")
        let body = try decoder.decode(GeometryBookmarkBody.self, from: Data(envelope.bodyJson.utf8))
        try require(body.format == envelope.format && ["astrid", "minime"].contains(body.owner), "Unknown geometry owner")
        try require(body.history.owner == nil || body.history.owner == body.owner, "Question owner mismatch")
        try require(body.history.records.isEmpty || body.history.owner != nil, "Missing history owner")
        try require(body.question.utf8.count <= 2000 && body.questionId.hasPrefix("q") && Int(body.questionId.dropFirst()) != nil,
                    "Invalid question identity")
        try require(body.history.records.count <= 64, "Geometry history exceeds 64 records")
        var previous = "empty"
        var seen: Set<String> = []
        var captures: [String: GeometryBookmarkSnapshot] = [:]
        var predictions: [String: GeometryBookmarkEntry] = [:]
        var positions: [String: Int] = [:]
        var entries: [GeometryBookmarkEntry] = []
        for (index, record) in body.history.records.enumerated() {
            let identity = geometryHash([record.previous, geometryHash(record.requestId), record.requestSha256, geometryHash(record.bodyJson)].joined(separator: "\n"))
            try require(record.previous == previous && record.id == identity && isGeometryHash(record.requestSha256)
                && !record.requestId.isEmpty && record.requestId.utf8.count <= 128 && seen.insert(record.requestId).inserted,
                "Broken geometry chain or conflicting operation identity")
            let entry = try GeometryBookmarkEntry.decode(Data(record.bodyJson.utf8), decoder: decoder)
            switch entry.kind {
            case "capture":
                guard let snapshot = entry.snapshot, let note = entry.note else { throw GeometryBookmarkError.invalid("Incomplete capture") }
                try authored(note); try snapshot.validate()
                captures[record.id] = snapshot
                try require(captures.count <= 4, "Four frozen intervals per question")
            case "prediction":
                guard let baseline = entry.baseline, captures[baseline] != nil,
                      let bound = entry.maximumRmsDistance, let expectation = entry.expectation else {
                    throw GeometryBookmarkError.invalid("Prediction has no earlier baseline or authored expectation")
                }
                try require(bound.isFinite && (0...2).contains(bound), "Invalid prediction bound")
                try authored(expectation); predictions[record.id] = entry
            case "comparison":
                guard let predictionID = entry.prediction, let prediction = predictions[predictionID],
                      let observationID = entry.observation, let observation = captures[observationID],
                      let baselineID = prediction.baseline, let baseline = captures[baselineID],
                      let pIndex = positions[predictionID], let oIndex = positions[observationID], oIndex > pIndex,
                      let bound = prediction.maximumRmsDistance, let measured = entry.rmsDistance, let matched = entry.thresholdMet else {
                    throw GeometryBookmarkError.invalid("Comparison references missing or misordered records")
                }
                let value = try GeometryBookmarkSnapshot.distance(baseline, observation)
                try require(entry.recipe == "mean-state-rms-distance-v1" && measured.isFinite
                    && abs(value - measured) <= 1e-12 && matched == (value <= bound), "Comparison does not match its frozen vectors")
            case "revision":
                guard let target = entry.target, positions[target] != nil, let text = entry.text else {
                    throw GeometryBookmarkError.invalid("Revision needs an earlier record and authored text")
                }
                try authored(text)
            default: throw GeometryBookmarkError.invalid("Unsupported geometry record kind")
            }
            positions[record.id] = index
            entries.append(entry); previous = record.id
        }
        return Self(body: body, digest: envelope.bodySha256, records: entries)
    }
}

private struct GeometryBookmarkEnvelope: Decodable { let format: String; let bodySha256: String; let bodyJson: String }
struct GeometryBookmarkBody: Decodable {
    let format: String
    let owner: String
    let questionId: String
    let question: String
    let history: GeometryBookmarkHistory
    let limits: String
}
struct GeometryBookmarkHistory: Decodable { let owner: String?; let records: [GeometryBookmarkRecord] }
struct GeometryBookmarkRecord: Decodable {
    let id: String
    let previous: String
    let requestId: String
    let requestSha256: String
    let bodyJson: String
}
struct GeometryBookmarkEntry: Decodable {
    let kind: String
    let snapshot: GeometryBookmarkSnapshot?
    let note: String?
    let baseline: String?
    let maximumRmsDistance: Double?
    let expectation: String?
    let prediction: String?
    let observation: String?
    let recipe: String?
    let rmsDistance: Double?
    let thresholdMet: Bool?
    let target: String?
    let text: String?

    static func decode(_ data: Data, decoder: JSONDecoder) throws -> Self {
        let entry = try decoder.decode(Self.self, from: data)
        let allowed: Set<String>
        switch entry.kind {
        case "capture": allowed = ["kind", "snapshot", "note"]
        case "prediction": allowed = ["kind", "baseline", "maximum_rms_distance", "expectation"]
        case "comparison": allowed = ["kind", "prediction", "observation", "recipe", "rms_distance", "threshold_met"]
        case "revision": allowed = ["kind", "target", "text"]
        default: throw GeometryBookmarkError.invalid("Unsupported geometry record kind")
        }
        guard let object = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw GeometryBookmarkError.invalid("Geometry record must be an object")
        }
        let unexpected = Set(object.keys).subtracting(allowed)
        try require(unexpected.isEmpty, "Unexpected fields for \(entry.kind): \(unexpected.sorted().joined(separator: ", "))")
        return entry
    }

    var authoredText: String? {
        switch kind {
        case "capture": return note
        case "prediction": return expectation
        case "revision": return text
        default: return nil
        }
    }
}
struct GeometryBookmarkFrame: Decodable {
    let tMs: UInt64
    let wallClockUnixMs: UInt64
    let activations: [Double]
    var rms: Double { sqrt(activations.reduce(0) { $0 + $1 * $1 } / 128) }
}
struct GeometryBookmarkSnapshot: Decodable {
    let sourceSha256: String
    let capturedAtUnixMs: UInt64
    let requestedSeconds: UInt64
    let source: String
    let scope: String
    let identity: String
    let frames: [GeometryBookmarkFrame]

    var gaps: [(UInt64, UInt64)] { zip(frames, frames.dropFirst()).filter { $1.tMs > $0.tMs && $1.tMs - $0.tMs > 1000 }.map { ($0.tMs, $1.tMs) } }
    var durationMs: UInt64 {
        guard let first = frames.first, let last = frames.last, last.tMs >= first.tMs else { return 0 }
        return last.tMs - first.tMs
    }
    var mean: [Double] { (0..<128).map { node in frames.reduce(0) { $0 + $1.activations[node] } / Double(frames.count) } }

    func validate() throws {
        try require(scope == "native_esn_128_activations" && identity == "boot_and_node_layout_unverified"
            && source == "minime/workspace/runtime/esn_activation_trace_v1.json" && isGeometryHash(sourceSha256), "Unsupported source identity")
        try require((1...60).contains(requestedSeconds) && (1...61).contains(frames.count), "Invalid interval limits")
        for frame in frames {
            try require(frame.activations.count == 128 && frame.activations.allSatisfy { $0.isFinite && (-1...1).contains($0) }, "Invalid activation vector")
        }
        for pair in zip(frames, frames.dropFirst()) {
            try require(pair.1.tMs > pair.0.tMs && pair.1.tMs - pair.0.tMs >= 1000 && pair.1.wallClockUnixMs > pair.0.wallClockUnixMs,
                        "Duplicate or reversed recorder clock")
        }
        let last = frames.last!
        try require(durationMs <= requestedSeconds * 1000 && capturedAtUnixMs >= last.wallClockUnixMs
            && capturedAtUnixMs - last.wallClockUnixMs <= 12_000, "Invalid capture clock or interval")
    }

    static func distance(_ baseline: Self, _ observation: Self) throws -> Double {
        try require(baseline.frames.count >= 2 && observation.frames.count >= 2, "Insufficient observations")
        try require(observation.frames[0].wallClockUnixMs > baseline.frames.last!.wallClockUnixMs
            && observation.frames[0].tMs > baseline.frames.last!.tMs, "Overlapping intervals or recorder restart")
        return sqrt(zip(baseline.mean, observation.mean).reduce(0) { $0 + pow($1.0 - $1.1, 2) } / 128)
    }
}

func geometryHash(_ text: String) -> String { SHA256.hash(data: Data(text.utf8)).map { String(format: "%02x", $0) }.joined() }
private func isGeometryHash(_ text: String) -> Bool { text.count == 64 && text.allSatisfy(\.isHexDigit) }
private func authored(_ text: String) throws { try require(!text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && text.utf8.count <= 2000, "Invalid authored text length") }
private func require(_ condition: Bool, _ reason: String) throws { if !condition { throw GeometryBookmarkError.invalid(reason) } }
enum GeometryBookmarkError: LocalizedError {
    case invalid(String)
    var errorDescription: String? { if case .invalid(let text) = self { return text }; return nil }
}
