import Foundation
import CryptoKit

/// Frozen steward-side captures. Unknown telemetry remains optional; required
/// geometry and replay coordinates fail validation instead of acquiring defaults.
struct EvidenceStore: Sendable {
    let historical: ReservoirEvidence
    let geometry: StateGeometryEvidence
    let stateReplay: StateReplayEvidence?

    init(historical: ReservoirEvidence, geometry: StateGeometryEvidence, stateReplay: StateReplayEvidence? = nil) {
        self.historical = historical
        self.geometry = geometry
        self.stateReplay = stateReplay
    }

    static func load(bundle: Bundle = .module) throws -> EvidenceStore {
        let historical: ReservoirEvidence = try decodeResource("data", in: bundle)
        let geometry: StateGeometryEvidence = try decodeResource("state-geometry", in: bundle)
        try historical.validate()
        try geometry.validate()
        let replay: StateReplayEvidence?
        if let manifestURL = resourceURL("state-replay", in: bundle) {
            guard let geometryURL = resourceURL("state-geometry", in: bundle) else {
                throw EvidenceError.missingResource("state-geometry.json")
            }
            replay = try StateReplayEvidence.load(manifestURL: manifestURL, geometryURL: geometryURL, geometry: geometry)
        } else { replay = nil }
        return EvidenceStore(historical: historical, geometry: geometry, stateReplay: replay)
    }

    static func load(historicalURL: URL, geometryURL: URL) throws -> EvidenceStore {
        let historical: ReservoirEvidence = try decodeFile(historicalURL)
        let geometry: StateGeometryEvidence = try decodeFile(geometryURL)
        try historical.validate()
        try geometry.validate()
        let manifestURL = geometryURL.deletingLastPathComponent().appendingPathComponent("state-replay.json")
        let replay = FileManager.default.fileExists(atPath: manifestURL.path)
            ? try StateReplayEvidence.load(manifestURL: manifestURL, geometryURL: geometryURL, geometry: geometry) : nil
        return EvidenceStore(historical: historical, geometry: geometry, stateReplay: replay)
    }

    static func decoder() -> JSONDecoder {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }

    private static func resourceURL(_ name: String, in bundle: Bundle) -> URL? {
        bundle.url(forResource: name, withExtension: "json")
            ?? bundle.url(forResource: name, withExtension: "json", subdirectory: "Resources")
    }

    private static func decodeResource<T: Decodable>(_ name: String, in bundle: Bundle) throws -> T {
        guard let url = resourceURL(name, in: bundle) else {
            throw EvidenceError.missingResource("\(name).json")
        }
        return try decodeFile(url)
    }

    private static func decodeFile<T: Decodable>(_ url: URL) throws -> T {
        let data: Data
        do { data = try Data(contentsOf: url) }
        catch { throw EvidenceError.unreadable(url.lastPathComponent, error.localizedDescription) }
        guard data.count <= 2 * 1024 * 1024 else {
            throw EvidenceError.invalid("\(url.lastPathComponent) exceeds the 2 MiB evidence limit.")
        }
        do { return try decoder().decode(T.self, from: data) }
        catch let error as DecodingError { throw EvidenceError.decoding(url.lastPathComponent, describe(error)) }
        catch { throw EvidenceError.decoding(url.lastPathComponent, error.localizedDescription) }
    }

    private static func describe(_ error: DecodingError) -> String {
        switch error {
        case .keyNotFound(let key, let context):
            return "Missing \((context.codingPath + [key]).map(\.stringValue).joined(separator: "."))"
        case .typeMismatch(_, let context), .valueNotFound(_, let context), .dataCorrupted(let context):
            let path = context.codingPath.map(\.stringValue).joined(separator: ".")
            return "\(path.isEmpty ? "root" : path): \(context.debugDescription)"
        @unknown default: return error.localizedDescription
        }
    }
}

enum EvidenceError: LocalizedError, Sendable {
    case missingResource(String)
    case unreadable(String, String)
    case decoding(String, String)
    case invalid(String)

    var errorDescription: String? {
        switch self {
        case .missingResource(let name): return "Bundled evidence is missing: \(name)."
        case .unreadable(let name, let reason): return "Cannot read \(name): \(reason)"
        case .decoding(let name, let reason): return "Cannot decode \(name): \(reason)"
        case .invalid(let reason): return "Evidence validation failed: \(reason)"
        }
    }
}

func evidenceDate(_ text: String?) -> Date? {
    guard let text else { return nil }
    let formatter = ISO8601DateFormatter()
    formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    if let value = formatter.date(from: text) { return value }
    formatter.formatOptions = [.withInternetDateTime]
    return formatter.date(from: text)
}

struct ReservoirEvidence: Decodable, Sendable {
    let schemaVersion: Int
    let kind: String
    let subject: ReservoirSubject?
    let capture: JSONValue?
    let stats: ReservoirStatistics?
    let bands: ReferenceBands
    let definitions: [String: String]?
    let visualMapping: [String: String]?
    let controller: ControllerEvidence
    let sources: [String: EvidenceFile]?
    let samples: [ReservoirSample]

    var fillRange: ClosedRange<Double> {
        precondition(!samples.isEmpty, "Evidence must pass validation before displaying its fill range.")
        let values = samples.map(\.fillPct)
        return values.min()!...values.max()!
    }
    var startDate: Date? { samples.first.flatMap { evidenceDate($0.tUtc) } }
    var endDate: Date? { samples.last.flatMap { evidenceDate($0.tUtc) } }
    var durationSeconds: Double? {
        guard let first = samples.first, let last = samples.last else { return nil }
        return last.tS - first.tS
    }

    func validate() throws {
        guard schemaVersion == 1, kind == "reservoir_3d_evidence" else {
            throw EvidenceError.invalid("Unsupported historical evidence schema: \(kind), version \(schemaVersion).")
        }
        guard !samples.isEmpty else { throw EvidenceError.invalid("Historical replay has no samples.") }
        var lastTime: Double?
        for (index, sample) in samples.enumerated() {
            guard sample.tS.isFinite, sample.fillPct.isFinite, (0...100).contains(sample.fillPct),
                  sample.cascade.count == 3, sample.cascade.allSatisfy({ $0.isFinite }),
                  evidenceDate(sample.tUtc) != nil else {
                throw EvidenceError.invalid("Historical sample \(index) has invalid time, fill, or spectral components.")
            }
            if let lastTime, sample.tS <= lastTime {
                throw EvidenceError.invalid("Historical sample \(index) does not follow the previous elapsed time.")
            }
            lastTime = sample.tS
        }
        let thresholds = [bands.shelfMinPct, bands.targetPct, bands.shelfMaxPct, bands.strongRailPct, bands.forceRailPct]
        guard thresholds.allSatisfy({ $0.isFinite && (0...100).contains($0) }),
              thresholds == thresholds.sorted() else {
            throw EvidenceError.invalid("Reference fill bands are non-finite, unordered, or outside 0–100%.")
        }
    }
}

struct ReservoirSubject: Decodable, Sendable {
    let being: String?
    let subsystems: [String]?
    let esnNodes: Int?
    let sensoryFieldDimensions: Int?
    let note: String?
}

struct ReservoirStatistics: Decodable, Sendable {
    let n: Int?
    let nExactPairs: Int?
    let firstTUtc: String?
    let lastTUtc: String?
    let durationS: Double?
    let medianIntervalS: Double?
    let fillMinPct: Double?
    let fillMaxPct: Double?
    let fillMeanPct: Double?
}

struct ReservoirSample: Decodable, Sendable, Identifiable {
    let tUtc: String
    let tS: Double
    let sessionId: Int
    let fillPct: Double
    let fillRatePctPerS: Double?
    let cascade: [Double]
    let esnCovLambda1: Double?
    let geomRadius: Double?
    let geomRel: Double?
    let esnLeak: Double?
    let esnLambda: Double?
    let sourceIds: [Int?]?
    var id: String { "\(sessionId):\(tS)" }
    var date: Date? { evidenceDate(tUtc) }
}

struct ReferenceBands: Decodable, Sendable {
    let shelfMinPct: Double
    let shelfEntryPct: Double?
    let targetPct: Double
    let shelfMaxPct: Double
    let elevatedReleasePct: Double?
    let strongRailPct: Double
    let forceRailPct: Double
    let status: String?
    let note: String?
}

struct ControllerEvidence: Decodable, Sendable {
    let historicalStatus: String?
    let structuralConfig: StructuralPIConfiguration
    let snapshot: ControllerSnapshot?
    let gateFilterStatus: String?
    let formulas: [String: String]?
}

struct StructuralPIConfiguration: Decodable, Sendable {
    let targetFillPct: Double
    let deadbandPct: Double
    let kp: Double
    let ki: Double
    let maxOutput: Double
    let integralDecayPerStep: Double?
}

struct ControllerSnapshot: Decodable, Sendable {
    let tUtc: String?
    let capturedAtUtc: String?
    let source: EvidenceFile?
    let provenance: TelemetryProvenance?
    let observedFillPct: Double?
    let mode: String?
    let stage: String?
    let structuralPi: StructuralPISnapshot?
    let gateFilterPi: GateFilterPISnapshot?
    let gate: Double?
    let filter: Double?
    let derived: DerivedPIContributions?
    let note: String?
    var date: Date? { evidenceDate(tUtc) }
}

struct TelemetryProvenance: Decodable, Sendable {
    let engineTS: Double?
    let sessionId: Int?
    let snapshotSequence: Int?
    let wallClockUnixMs: Double?
    let targetProvenance: String?
    var date: Date? {
        guard let wallClockUnixMs, wallClockUnixMs.isFinite else { return nil }
        return Date(timeIntervalSince1970: wallClockUnixMs / 1000)
    }
}

struct StructuralPISnapshot: Decodable, Sendable {
    let active: Bool?
    let targetFillPct: Double?
    let errorPct: Double?
    let integral: Double?
    let drainWeight: Double?
    let appliedDrainWeight: Double?
    let appliedLiveWeight: Double?
    let fillSlopePctPerSec: Double?
    let dampingState: String?
    let drainGateReason: String?
    let drainSuppressedBySlope: Bool?
    let lowFillEscapeActive: Bool?
    let highFillDrainActive: Bool?
    let recoveryImpulseActive: Bool?
    let reentryActive: Bool?
    var controllerInputFillPct: Double? {
        guard let targetFillPct, let errorPct else { return nil }
        return targetFillPct + errorPct
    }
}

struct GateFilterPISnapshot: Decodable, Sendable {
    let kp: Double?
    let ki: Double?
    let derivedKp: Double?
    let derivedKi: Double?
    let maxStep: Double?
    let targetFill: Double?
    let targetGeomRel: Double?
    let targetLambda1Rel: Double?
    let rawEFill: Double?
    let effectiveEFill: Double?
    let eFill: Double?
    let eFillKind: String?
    let eGeom: Double?
    let eLam: Double?
    let integFill: Double?
    let integGeom: Double?
    let integLam: Double?
    let gateCmd: Double?
    let filtCmd: Double?
}

struct DerivedPIContributions: Decodable, Sendable {
    let pTerm: Double
    let iTerm: Double
    let piOutput: Double
    let controllerInputFillPct: Double
    let snapshotMinusControllerFillPct: Double?
    let status: String?
    let units: String?
    let note: String?
}

struct EvidenceFile: Decodable, Sendable {
    let path: String
    let sha256: String?
    let snapshotPath: String?
    let status: String?
    let line: Int?
}

struct StateGeometryEvidence: Decodable, Sendable {
    let schema: String
    let subject: String?
    let source: StateGeometrySource
    let timing: StateGeometryTiming
    let missingFields: [String]?
    let pca: PrincipalComponents
    let samples: [StateGeometrySample]

    func validate() throws {
        guard schema == "reservoir.state_geometry.v1" else {
            throw EvidenceError.invalid("Unsupported state geometry schema: \(schema).")
        }
        guard !samples.isEmpty, pca.rows == samples.count, pca.dimensions > 0,
              pca.mean.count == pca.dimensions, pca.components.count == 3,
              pca.components.allSatisfy({ $0.count == pca.dimensions && $0.allSatisfy(\.isFinite) }),
              pca.eigenvalues.count == pca.dimensions,
              pca.explainedVarianceRatio.count == pca.dimensions else {
            throw EvidenceError.invalid("PCA matrix dimensions do not match the captured rows and node count.")
        }
        guard pca.retainedFraction.isFinite, (0...1).contains(pca.retainedFraction),
              pca.normalization.referenceRadius.isFinite, pca.normalization.referenceRadius > 0 else {
            throw EvidenceError.invalid("PCA variance fraction or empirical radius is invalid.")
        }
        for (index, sample) in samples.enumerated() {
            guard sample.index == index, sample.pc.count == 3, sample.pc.allSatisfy(\.isFinite),
                  [sample.centeredNorm, sample.projectedNorm, sample.residualNorm].allSatisfy({ $0.isFinite && $0 >= 0 }) else {
                throw EvidenceError.invalid("State geometry row \(index) has invalid coordinates, distances, or ordinal index.")
            }
        }
    }
}

struct StateGeometrySource: Decodable, Sendable {
    let capturedAtUtc: String?
    let meta: JSONValue?
    let files: [String: EvidenceFile]?
    let consistency: SourceConsistency?
    var capturedAt: Date? { evidenceDate(capturedAtUtc) }
}

struct SourceConsistency: Decodable, Sendable {
    let status: String?
    let identicalBytesBeforeAfter: Bool?
    let identicalStatsBeforeAfter: Bool?
    let producerTransactionalPairGuarantee: Bool?
    let limitation: String?
}

struct StateGeometryTiming: Decodable, Sendable {
    let rowOrder: String?
    let rowUnit: String?
    let perRowTimestampsAvailable: Bool?
    let dumpElapsedMs: Double?
    let dumpElapsedOrigin: String?
    let cadenceNotes: String?
}

struct PrincipalComponents: Decodable, Sendable {
    let method: String?
    let fitScope: String?
    let frozen: Bool?
    let rows: Int
    let dimensions: Int
    let mean: [Double]
    let eigenvalues: [Double]
    let components: [[Double]]
    let componentOrientation: String?
    let componentSignRule: String?
    let explainedVarianceRatio: [Double]
    let retainedFraction: Double
    let omittedFraction: Double?
    let totalSampleVariance: Double?
    let participationRatio: Double?
    let reconstructionRmse: Double?
    let relativeReconstructionError: Double?
    let normalization: PCANormalization
    let metricDistinction: String?
}

struct PCANormalization: Decodable, Sendable {
    let referenceRadius: Double
    let definition: String?
    let pointRadiusDefinition: String?
    let distanceUnits: String?
}

struct StateGeometrySample: Decodable, Sendable, Identifiable {
    let index: Int
    let pc: [Double]
    let stateRms: Double
    let centeredRms: Double
    let projectedRms: Double
    let reconstructionRmse: Double
    let centeredNorm: Double
    let projectedNorm: Double
    let residualNorm: Double
    var id: Int { index }
}

/// Original retained activations paired only with geometry derived from those
/// same bytes. This capture has ordinal steps, no row timestamps or fill join.
struct StateReplayFrame: Sendable, Identifiable {
    let index: Int
    let activations: [Double]
    let geometry: StateGeometrySample
    var id: Int { index }
}

struct StateReplayEvidence: Sendable {
    let frames: [StateReplayFrame]
    let sourceSHA256: String
    let geometrySHA256: String
    let capturedAtUtc: String?
    var dimensions: Int { frames.first?.activations.count ?? 0 }
    var basisCompatibilityText: String {
        "Same retained activation bytes as the frozen basis; live node-layout identity remains unverified"
    }
    var timingText: String { "Recorded state order only · no per-row time or paired fill" }
    func frame(index: Int) -> StateReplayFrame? { frames.indices.contains(index) ? frames[index] : nil }
    func sourceIdentity(index: Int) -> String? {
        frame(index: index).map { "capture:\(sourceSHA256):row:\($0.index)" }
    }

    static func load(manifestURL: URL, geometryURL: URL, geometry: StateGeometryEvidence) throws -> Self {
        let manifestData = try boundedRead(manifestURL, maximum: 16 * 1024)
        let manifest: StateReplayManifest
        do { manifest = try EvidenceStore.decoder().decode(StateReplayManifest.self, from: manifestData) }
        catch { throw EvidenceError.decoding(manifestURL.lastPathComponent, error.localizedDescription) }
        // A fixed basename prevents a manifest from redirecting this read beyond
        // its evidence package. Validate dimensions before multiplication.
        guard manifest.schema == "reservoir.state_replay.v1", manifest.dtype == "<f4",
              manifest.layout == "row_major", manifest.binaryFile == "state-replay.bin",
              (2...1024).contains(manifest.rows), manifest.dimensions == 128,
              manifest.rows == geometry.pca.rows, manifest.dimensions == geometry.pca.dimensions,
              manifest.rowOrder == "oldest_to_newest", !manifest.perRowTimestampsAvailable,
              !manifest.pairedFillAvailable, manifest.nodeLayoutId == nil,
              geometry.timing.rowOrder == manifest.rowOrder,
              geometry.timing.perRowTimestampsAvailable == false else {
            throw EvidenceError.invalid("State replay must be a bounded 128-coordinate retained capture with ordinal rows and no invented time, fill, or node-layout identity.")
        }
        try geometry.validate()
        let geometryData = try boundedRead(geometryURL, maximum: 2 * 1024 * 1024)
        guard sha256(geometryData) == manifest.geometrySha256,
              manifest.sourceSha256 == geometry.source.files?["states"]?.sha256,
              manifest.capturedAtUtc == geometry.source.capturedAtUtc else {
            throw EvidenceError.invalid("State replay is not bound to this exact frozen geometry and retained source hash.")
        }
        let raw = try boundedRead(manifestURL.deletingLastPathComponent().appendingPathComponent(manifest.binaryFile),
                                  maximum: 1024 * 128 * 4)
        guard raw.count == manifest.rows * manifest.dimensions * 4,
              raw.count == manifest.byteCount, sha256(raw) == manifest.sourceSha256 else {
            throw EvidenceError.invalid("Retained activation byte count or SHA-256 does not match the replay manifest.")
        }
        let frames: [StateReplayFrame] = try raw.withUnsafeBytes { buffer in
            try (0..<manifest.rows).map { row in
                let values = (0..<manifest.dimensions).map { node -> Double in
                    let offset = (row * manifest.dimensions + node) * 4
                    let bits = UInt32(littleEndian: buffer.loadUnaligned(fromByteOffset: offset, as: UInt32.self))
                    return Double(Float(bitPattern: bits))
                }
                guard values.allSatisfy({ $0.isFinite && (-1...1).contains($0) }) else {
                    throw EvidenceError.invalid("Retained activation row \(row) has non-finite or out-of-range coordinates.")
                }
                return StateReplayFrame(index: row, activations: values, geometry: geometry.samples[row])
            }
        }
        return Self(frames: frames, sourceSHA256: manifest.sourceSha256,
                    geometrySHA256: manifest.geometrySha256, capturedAtUtc: manifest.capturedAtUtc)
    }

    private static func boundedRead(_ url: URL, maximum: Int) throws -> Data {
        let handle: FileHandle
        do { handle = try FileHandle(forReadingFrom: url) }
        catch { throw EvidenceError.unreadable(url.lastPathComponent, error.localizedDescription) }
        defer { try? handle.close() }
        let data = try handle.read(upToCount: maximum + 1) ?? Data()
        guard !data.isEmpty, data.count <= maximum else {
            throw EvidenceError.invalid("\(url.lastPathComponent) is empty or exceeds its bounded replay read limit.")
        }
        return data
    }

    private static func sha256(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }
}

private struct StateReplayManifest: Decodable {
    let schema: String
    let dtype: String
    let layout: String
    let binaryFile: String
    let rows: Int
    let dimensions: Int
    let byteCount: Int
    let sourceSha256: String
    let geometrySha256: String
    let capturedAtUtc: String?
    let rowOrder: String
    let perRowTimestampsAvailable: Bool
    let pairedFillAvailable: Bool
    let nodeLayoutId: String?
}

indirect enum JSONValue: Decodable, Sendable {
    case object([String: JSONValue])
    case array([JSONValue])
    case string(String)
    case number(Double)
    case bool(Bool)
    case null

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() { self = .null }
        else if let value = try? container.decode(Bool.self) { self = .bool(value) }
        else if let value = try? container.decode(Double.self) { self = .number(value) }
        else if let value = try? container.decode(String.self) { self = .string(value) }
        else if let value = try? container.decode([JSONValue].self) { self = .array(value) }
        else { self = .object(try container.decode([String: JSONValue].self)) }
    }
}
