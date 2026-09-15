import Foundation

public enum EssentialsError: Error, LocalizedError, Sendable {
    case invalid(String), language(String), verification(String)
    public var errorDescription: String? {
        switch self { case .invalid(let value), .language(let value), .verification(let value): return value }
    }
}
public enum EssentialsStage: Int, Codable, CaseIterable, Sendable, Identifiable {
    case reservoir = 1, spectralBridge, llmLoop, regulation
    public var id: Int { rawValue }
    public var title: String {
        switch self {
        case .reservoir: "1 · Reservoir"
        case .spectralBridge: "2 · Spectral bridge"
        case .llmLoop: "3 · LLM loop"
        case .regulation: "4 · Regulation"
        }
    }
    public var explanation: String {
        switch self {
        case .reservoir: "Seeded recurrence holds traces of a synthetic input after it ends. Each point is one of 32 actual state coordinates."
        case .spectralBridge: "The same 66-coordinate input feeds a separate 32-dimensional sensory field. Example text returns through the handcrafted semantic codec."
        case .llmLoop: "One voice receives the spectral observation. Its complete reply becomes semantic input on the next step; simulation pauses while it waits."
        case .regulation: "A reduced controller changes sensory covariance retention on the next step toward 68% reduced active-mode fill. This is an experimental fill definition."
        }
    }
}
public struct RunSpecification: Codable, Sendable, Equatable {
    public var stage: EssentialsStage
    public var seed: UInt64
    public var steps: Int
    public var dt: Double
    public var turnEvery: Int
    public var noiseAmplitude: Double
    public var leak: Double
    public var initialRetention: Double
    public var regulationEnabled: Bool
    public var language: LanguageConfiguration
    public init(stage: EssentialsStage = .reservoir, seed: UInt64 = 20260909, steps: Int = 300,
                dt: Double = 1.0 / 3.0, turnEvery: Int = 30, noiseAmplitude: Double = 0,
                leak: Double = 0.65, initialRetention: Double = 0.955,
                regulationEnabled: Bool = true, language: LanguageConfiguration = .scripted) {
        self.stage = stage; self.seed = seed; self.steps = steps; self.dt = dt
        self.turnEvery = turnEvery; self.noiseAmplitude = noiseAmplitude; self.leak = leak
        self.initialRetention = initialRetention; self.regulationEnabled = regulationEnabled; self.language = language
    }
    enum CodingKeys: String, CodingKey { case stage, seed, steps, dt, turnEvery, noiseAmplitude, leak, initialRetention, regulationEnabled, language }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        self.init(stage: try c.decode(EssentialsStage.self, forKey: .stage),
            seed: try c.decodeIfPresent(UInt64.self, forKey: .seed) ?? 20260909,
            steps: try c.decodeIfPresent(Int.self, forKey: .steps) ?? 300,
            dt: try c.decodeIfPresent(Double.self, forKey: .dt) ?? 1.0 / 3.0,
            turnEvery: try c.decodeIfPresent(Int.self, forKey: .turnEvery) ?? 30,
            noiseAmplitude: try c.decodeIfPresent(Double.self, forKey: .noiseAmplitude) ?? 0,
            leak: try c.decodeIfPresent(Double.self, forKey: .leak) ?? 0.65,
            initialRetention: try c.decodeIfPresent(Double.self, forKey: .initialRetention) ?? 0.955,
            regulationEnabled: try c.decodeIfPresent(Bool.self, forKey: .regulationEnabled) ?? true,
            language: try c.decodeIfPresent(LanguageConfiguration.self, forKey: .language) ?? .scripted)
    }
    public func validate() throws {
        guard (1...3_000).contains(steps), (1...3_000).contains(turnEvery),
              dt.isFinite, (0.001...10).contains(dt), noiseAmplitude.isFinite, (0...0.2).contains(noiseAmplitude),
              leak.isFinite, (0...1).contains(leak), initialRetention.isFinite,
              (0.82...0.995).contains(initialRetention) else {
            throw EssentialsError.invalid("Invalid recipe: steps/turn interval must be 1–3000, dt 0.001–10, noise 0–0.2, leak 0–1 and retention 0.82–0.995.")
        }
        try language.validate()
    }
}
public enum RunStatus: String, Codable, Sendable { case completed, stopped, failed }
public enum LanguageTurnStatus: String, Codable, Sendable { case completed, failed, cancelled }
public enum LanguageContextKind: String, Codable, Sendable { case preparedExampleContext, languageRequest }
public struct LanguageTurn: Codable, Sendable, Identifiable {
    public let id: Int
    public let observedStep: Int
    public var applicationStep: Int?
    public let prompt: String
    public let contextKind: LanguageContextKind
    public var reply: String?
    public var rawReply: String?
    public var providerModel: String?
    public var stopReason: String?
    public var tokenCount: Int?
    public var encodedFeatures: [Double]?
    public var semanticVector: [Double]?
    public var status: LanguageTurnStatus
    public var failure: String?
    public let backend: String
    public let model: String?
}
public struct EssentialsFrame: Codable, Sendable, Identifiable {
    public var id: Int { step }
    public let step: Int
    public let time: Double
    public let input: [Double]
    public let state: [Double]
    public let noise: [Double]
    public let spectral: SpectralMeasurement?
    public let fillPercent: Double?
    public let retentionUsed: Double?
    public let control: ControlMeasurement?
    public let semanticTurnID: Int?
}
public struct RunRecord: Codable, Sendable {
    public static let currentRecipeVersion = "essentials-v1"
    public let recipeVersion: String
    public let specification: RunSpecification
    public let model: ReservoirModel
    public let projectionWeights: [Double]
    public var frames: [EssentialsFrame]
    public var turns: [LanguageTurn]
    public var status: RunStatus
    public var failure: String?
    public static func read(from url: URL) throws -> RunRecord {
        let values = try url.resourceValues(forKeys: [.fileSizeKey, .isRegularFileKey])
        guard values.isRegularFile == true, (values.fileSize ?? Int.max) <= 256 * 1_024 * 1_024 else {
            throw EssentialsError.invalid("Run must be a regular JSON file no larger than 256 MB.")
        }
        let result = try JSONDecoder().decode(Self.self, from: Data(contentsOf: url))
        try result.validate(); return result
    }
    public func write(to url: URL) throws {
        try validate()
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        try encoder.encode(self).write(to: url, options: .atomic)
    }
    public func validate() throws { try RunVerifier.validateStructure(self) }
}
public struct VerificationReport: Sendable {
    public let checkedSteps: Int
    public let checkedTurns: Int
    public var summary: String { "Verified \(checkedSteps) steps and \(checkedTurns) language turns, including recurrence, spectra, feedback and regulation." }
}
