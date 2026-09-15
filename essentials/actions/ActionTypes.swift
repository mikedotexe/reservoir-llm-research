import Foundation

public enum ActionStage: Int, Codable, CaseIterable, Sendable, Identifiable {
    case minimal = 1, recurrence, sensoryObserver, journalOutput, reservoirReturn, journalMemory, actionChoice, regulation
    public var id: Int { rawValue }
    public var previous: ActionStage? { ActionStage(rawValue: rawValue - 1) }
    public var title: String {
        ["A · Minimal reservoir", "B · Recurrence", "C · Sensory observer", "D · Journal output",
         "E · Reservoir return", "F · Journal memory", "G · Action choice", "H · Regulation"][rawValue - 1]
    }
    public var addedFeature: String {
        ["Leaky state with external input", "Recurrent connections", "Separate sensory observation",
         "Completed and saved journal output", "Journal codec input on the next step",
         "Previous journal supplied in the next prompt", "WRITE_JOURNAL or WAIT choice",
         "Next-step sensory retention control"][rawValue - 1]
    }
    public var hasJournal: Bool { rawValue >= Self.journalOutput.rawValue }
    public var hasFeedback: Bool { rawValue >= Self.reservoirReturn.rawValue }
    public var hasMemory: Bool { rawValue >= Self.journalMemory.rawValue }
    public var hasChoice: Bool { rawValue >= Self.actionChoice.rawValue }
}

public enum ActionComparisonMode: String, Codable, CaseIterable, Sendable, Identifiable {
    case fixedReplay, independentGeneration
    public var id: String { rawValue }
    public var title: String { self == .fixedReplay ? "Replay identical replies" : "Generate independently" }
}
public enum ActionArm: String, Codable, Sendable { case left, right }
public enum JournalAction: String, Codable, Sendable { case writeJournal = "WRITE_JOURNAL", wait = "WAIT" }
public enum ActionTrigger: String, Codable, Sendable { case scheduled, manual }
public enum JournalSaveStatus: String, Codable, Sendable { case saved, failed }
public enum ActionFailurePhase: String, Codable, Sendable { case memoryRead, language, responseValidation, journalSave, cancelled }

public struct ActionComparisonSpecification: Codable, Sendable, Equatable {
    public var stage: ActionStage
    public var mode: ActionComparisonMode
    public var comparePrevious: Bool
    public var seed: UInt64
    public var steps: Int
    public var turnEvery: Int
    public var leak: Double
    public var noiseAmplitude: Double
    public var inputStrength: Double
    public var biasEnabled: Bool
    public var initialRetention: Double
    public var language: LanguageConfiguration
    public var question: String
    public var expectedDifference: String
    public var alternativeExplanation: String
    public var alternatives: String {
        get { alternativeExplanation }
        set { alternativeExplanation = newValue }
    }
    public var stoppingPoint: String
    public var dt: Double { 1.0 / 3.0 }
    public init(stage: ActionStage = .reservoirReturn, mode: ActionComparisonMode = .fixedReplay,
                comparePrevious: Bool = true, seed: UInt64 = 20260909, steps: Int = 300, turnEvery: Int = 30,
                leak: Double = 0.65, noiseAmplitude: Double = 0, inputStrength: Double = 1,
                biasEnabled: Bool = false, initialRetention: Double = 0.955,
                language: LanguageConfiguration = .scripted, question: String = "What changes when this mechanism is added?",
                expectedDifference: String = "Inspect the named feature against the preceding version.",
                alternativeExplanation: String = "Matched external inputs and explicit return channels separate the mechanisms.",
                stoppingPoint: String = "Stop at the configured finite step count; retain failures and waits.") {
        self.stage = stage; self.mode = mode; self.comparePrevious = comparePrevious; self.seed = seed
        self.steps = steps; self.turnEvery = turnEvery; self.leak = leak; self.noiseAmplitude = noiseAmplitude
        self.inputStrength = inputStrength; self.biasEnabled = biasEnabled; self.initialRetention = initialRetention
        self.language = language
        self.question = question; self.expectedDifference = expectedDifference
        self.alternativeExplanation = alternativeExplanation; self.stoppingPoint = stoppingPoint
    }
    enum CodingKeys: String, CodingKey {
        case stage, mode, comparePrevious, seed, steps, turnEvery, leak, noiseAmplitude, inputStrength, biasEnabled,
             initialRetention, language, question, expectedDifference, alternativeExplanation, stoppingPoint
    }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        let defaults = Self()
        self.init(stage: try c.decodeIfPresent(ActionStage.self, forKey: .stage) ?? defaults.stage,
            mode: try c.decodeIfPresent(ActionComparisonMode.self, forKey: .mode) ?? defaults.mode,
            comparePrevious: try c.decodeIfPresent(Bool.self, forKey: .comparePrevious) ?? defaults.comparePrevious,
            seed: try c.decodeIfPresent(UInt64.self, forKey: .seed) ?? defaults.seed,
            steps: try c.decodeIfPresent(Int.self, forKey: .steps) ?? defaults.steps,
            turnEvery: try c.decodeIfPresent(Int.self, forKey: .turnEvery) ?? defaults.turnEvery,
            leak: try c.decodeIfPresent(Double.self, forKey: .leak) ?? defaults.leak,
            noiseAmplitude: try c.decodeIfPresent(Double.self, forKey: .noiseAmplitude) ?? defaults.noiseAmplitude,
            inputStrength: try c.decodeIfPresent(Double.self, forKey: .inputStrength) ?? defaults.inputStrength,
            biasEnabled: try c.decodeIfPresent(Bool.self, forKey: .biasEnabled) ?? defaults.biasEnabled,
            initialRetention: try c.decodeIfPresent(Double.self, forKey: .initialRetention) ?? defaults.initialRetention,
            language: try c.decodeIfPresent(LanguageConfiguration.self, forKey: .language) ?? defaults.language,
            question: try c.decodeIfPresent(String.self, forKey: .question) ?? defaults.question,
            expectedDifference: try c.decodeIfPresent(String.self, forKey: .expectedDifference) ?? defaults.expectedDifference,
            alternativeExplanation: try c.decodeIfPresent(String.self, forKey: .alternativeExplanation) ?? defaults.alternativeExplanation,
            stoppingPoint: try c.decodeIfPresent(String.self, forKey: .stoppingPoint) ?? defaults.stoppingPoint)
    }
    public func validate() throws {
        guard (1...600).contains(steps), (1...600).contains(turnEvery), (!stage.hasJournal || (steps - 1) / turnEvery <= 128),
              leak.isFinite, (0...1).contains(leak),
              noiseAmplitude.isFinite, (0...0.2).contains(noiseAmplitude), inputStrength.isFinite,
              (0...1).contains(inputStrength), initialRetention.isFinite, (0.82...0.995).contains(initialRetention) else {
            throw EssentialsError.invalid("Actions require 1–600 steps/interval, leak/input strength 0–1, noise 0–0.2, and retention 0.82–0.995.")
        }
        try language.validate()
        guard [question, expectedDifference, alternativeExplanation, stoppingPoint].allSatisfy({ !$0.isEmpty && $0.utf8.count <= 4096 }) else {
            throw EssentialsError.invalid("Study notes must be nonempty and at most 4 KiB each.")
        }
    }
}

public struct ActionFrame: Codable, Sendable, Identifiable {
    public var id: Int { step }
    public let step: Int
    public let time: Double
    public let input: [Double]
    public let externalInput: [Double]
    public let semanticInput: [Double]
    public let previousState: [Double]
    public let state: [Double]
    public let noise: [Double]
    public let spectral: SpectralMeasurement?
    public let fillPercent: Double?
    public let retentionUsed: Double?
    public let control: ControlMeasurement?
    public let semanticActionID: Int?
}

public struct JournalEntry: Codable, Sendable, Identifiable, Equatable {
    public let id: String
    public let actionID: Int
    public let observedStep: Int
    public let text: String
    public let sha256: String
    public init(id: String, actionID: Int, observedStep: Int, text: String, sha256: String) {
        self.id = id; self.actionID = actionID; self.observedStep = observedStep; self.text = text; self.sha256 = sha256
    }
}
public struct JournalSaveReceipt: Codable, Sendable, Equatable {
    public let status: JournalSaveStatus
    public let entryID: String
    public let sha256: String
    /// A session-relative journal location, never an import-time path to execute.
    public let relativePath: String?
    public let failure: String?
    public init(status: JournalSaveStatus, entryID: String, sha256: String, relativePath: String?, failure: String? = nil) {
        self.status = status; self.entryID = entryID; self.sha256 = sha256
        self.relativePath = relativePath; self.failure = failure
    }
}

public struct ActionReceipt: Codable, Sendable, Identifiable {
    public let id: Int
    public let observedStep: Int
    public let trigger: ActionTrigger
    public let prompt: String
    public let requestedAction: JournalAction?
    public var rawReply: String?
    public var rawReplyByteCount: Int?
    public var chosenAction: JournalAction?
    public var status: LanguageTurnStatus
    public var failure: String?
    public var providerModel: String?
    public var stopReason: String?
    public var tokenCount: Int?
    public var providerComplete: Bool?
    public var requestStarted: Bool
    public var failurePhase: ActionFailurePhase?
    public var journalEntryID: String?
    public var saveReceipt: JournalSaveReceipt?
    public let memoryEntryID: String?
    public let memoryText: String?
    public var encodedFeatures: [Double]?
    public var semanticVector: [Double]?
    public var applicationStep: Int?
    public let tapePacketID: Int?
}

public struct ActionTapePacket: Codable, Sendable, Identifiable, Equatable {
    public let id: Int
    public let referenceStep: Int
    public let text: String
    public let choice: JournalAction
    public let referenceEigenvalues: [Double]
    public let encodedFeatures: [Double]
    public let semanticVector: [Double]
}
public struct ActionReplyTape: Codable, Sendable, Equatable {
    public static let currentFormat = "essentials-action-tape-v1"
    public let format: String
    public let origin: String
    public let seed: UInt64
    public let inputStrength: Double
    public let retention: Double
    public let turnEvery: Int
    public let packets: [ActionTapePacket]
}

public struct ActionRunRecord: Codable, Sendable {
    public let arm: ActionArm
    public let stage: ActionStage
    public let model: ReservoirModel
    public let projectionWeights: [Double]
    public var frames: [ActionFrame]
    public var actions: [ActionReceipt]
    public var journals: [JournalEntry]
    public var status: RunStatus
    public var failure: String?
}

public struct ActionComparisonRecord: Codable, Sendable {
    public static let currentFormat = "essentials-actions-v1"
    public let format: String
    public let specification: ActionComparisonSpecification
    public let tape: ActionReplyTape?
    public var left: ActionRunRecord?
    public var right: ActionRunRecord
    public var status: RunStatus
    public var failure: String?
    public var stepCount: Int { right.frames.count }
}

public protocol ActionJournalStore: Sendable {
    func save(_ entry: JournalEntry, arm: ActionArm) throws -> JournalSaveReceipt
    func read(entryID: String, arm: ActionArm) throws -> JournalEntry
}
