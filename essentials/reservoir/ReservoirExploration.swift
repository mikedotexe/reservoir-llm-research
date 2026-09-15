import Foundation

/// Controls are recorded at the step where they actually apply. Defaults are quiet.
public struct ExplorationControls: Codable, Sendable, Equatable {
    public var leak: Double
    public var recurrenceEnabled: Bool
    public var recurrenceStrength: Double
    public var repeatInput: Bool
    public var inputStrength: Double
    public var noiseAmplitude: Double
    public var biasEnabled: Bool
    public var sensoryEnabled: Bool
    public var retention: Double

    public init(leak: Double = 0.65, recurrenceEnabled: Bool = false, recurrenceStrength: Double = 1,
                repeatInput: Bool = false, inputStrength: Double = 1, noiseAmplitude: Double = 0,
                biasEnabled: Bool = false, sensoryEnabled: Bool = false, retention: Double = 0.955) {
        self.leak = leak; self.recurrenceEnabled = recurrenceEnabled; self.recurrenceStrength = recurrenceStrength
        self.repeatInput = repeatInput; self.inputStrength = inputStrength; self.noiseAmplitude = noiseAmplitude
        self.biasEnabled = biasEnabled; self.sensoryEnabled = sensoryEnabled; self.retention = retention
    }

    public func validate() throws {
        guard leak.isFinite, (0...1).contains(leak), recurrenceStrength.isFinite,
              (0...1).contains(recurrenceStrength), inputStrength.isFinite, (0...1).contains(inputStrength),
              noiseAmplitude.isFinite, (0...0.2).contains(noiseAmplitude), retention.isFinite,
              (0.82...0.995).contains(retention) else {
            throw EssentialsError.invalid("Exploration controls require leak/strengths 0–1, noise 0–0.2, and retention 0.82–0.995.")
        }
    }
}

public struct ExplorationFrame: Codable, Sendable, Identifiable {
    public var id: Int { step }
    public let step: Int
    public let time: Double
    public let controls: ExplorationControls
    public let pulse: Bool
    public let input: [Double]
    public let previousState: [Double]
    /// These three contributions are raw pre-tanh drives, not leaky state increments.
    public let inputDrive: [Double]
    public let recurrentDrive: [Double]
    public let biasDrive: [Double]
    /// tanh of the complete drive, before leaky integration and explicit noise.
    public let proposal: [Double]
    public let state: [Double]
    public let noise: [Double]
    public let spectral: SpectralMeasurement?
}

public struct ExplorationEngine: Sendable {
    public static let maximumSteps = 1_800
    public static let dt = 1.0 / 3.0
    public let seed: UInt64
    /// Original seeded weights. Per-step controls never rewrite this source model.
    public let model: ReservoirModel
    public let projectionWeights: [Double]
    public private(set) var frames: [ExplorationFrame] = []
    private var state = [Double](repeating: 0, count: 32)
    private var noiseGenerator: SplitMix64
    private var sensoryField: SensoryField?

    public init(seed: UInt64 = 20260909) throws {
        self.seed = seed
        model = try ReservoirModel(seed: seed)
        projectionWeights = try SensoryField(seed: seed ^ Recipe.fieldSeed).projectionWeights
        noiseGenerator = SplitMix64(seed: seed ^ Recipe.noiseSeed)
    }

    public init(record: ExplorationRecord) throws {
        self = try record.reconstructedEngine()
    }

    public var record: ExplorationRecord {
        ExplorationRecord(seed: seed, model: model, projectionWeights: projectionWeights, frames: frames)
    }

    fileprivate mutating func retainVerifiedHistory(_ original: [ExplorationFrame]) throws {
        // Keep the imported measurements byte-for-byte in subsequent exports,
        // including any valid alternative basis of a degenerate eigenspace.
        frames = original
        state = original.last?.state ?? [Double](repeating: 0, count: 32)
        if let spectral = original.last?.spectral {
            sensoryField = try SensoryField(dimension: 32, inputCount: 66,
                                           projection: projectionWeights, covariance: spectral.covariance)
        } else { sensoryField = nil }
    }

    @discardableResult
    public mutating func advance(controls: ExplorationControls, pulse: Bool = false) throws -> ExplorationFrame {
        try controls.validate()
        guard frames.count < Self.maximumSteps else {
            throw EssentialsError.invalid("Exploration reached 1,800 steps. Export this history or reset to begin another run.")
        }
        let step = frames.count + 1
        let unscaled: [Double]
        if pulse { unscaled = Recipe.forcing(step: 1, dt: Self.dt) }
        else if controls.repeatInput { unscaled = Recipe.forcing(step: step, dt: Self.dt) }
        else { unscaled = [Double](repeating: 0, count: 66) }
        let input = unscaled.map { $0 * controls.inputStrength }
        let strength = controls.recurrenceEnabled ? controls.recurrenceStrength : 0
        let recurrence = model.recurrentWeights.map { $0 * strength }
        var weights = model.inputWeights
        if !controls.biasEnabled { for row in 0..<32 { weights[row * 67 + 66] = 0 } }
        let controlledModel = try ReservoirModel(nodeCount: 32, inputCount: 66,
                                                recurrentWeights: recurrence, inputWeights: weights)
        var reservoir = try ReservoirEngine(model: controlledModel, leak: controls.leak, state: state)
        var generator = noiseGenerator
        // Always consume exactly 32 samples, even at zero amplitude.
        let noise = (0..<32).map { _ in generator.nextSigned() * controls.noiseAmplitude }
        let nextState = try reservoir.step(input: input, noise: noise)
        var inputDrive = [Double](repeating: 0, count: 32)
        var recurrentDrive = [Double](repeating: 0, count: 32)
        var biasDrive = [Double](repeating: 0, count: 32)
        var proposal = [Double](repeating: 0, count: 32)
        for row in 0..<32 {
            biasDrive[row] = weights[row * 67 + 66]
            // Accumulate total drive in ReservoirEngine's exact numerical order.
            var drive = biasDrive[row]
            for column in 0..<66 {
                let contribution = weights[row * 67 + column] * input[column]
                inputDrive[row] += contribution; drive += contribution
            }
            for column in 0..<32 {
                let contribution = recurrence[row * 32 + column] * state[column]
                recurrentDrive[row] += contribution; drive += contribution
            }
            proposal[row] = tanh(drive)
        }
        var nextField = sensoryField
        let spectral: SpectralMeasurement?
        if controls.sensoryEnabled {
            if nextField == nil { nextField = try SensoryField(seed: seed ^ Recipe.fieldSeed) }
            spectral = try nextField!.step(input: input, retention: controls.retention)
        } else { nextField = nil; spectral = nil }
        let frame = ExplorationFrame(step: step, time: Double(step) * Self.dt, controls: controls,
                                     pulse: pulse, input: input, previousState: state, inputDrive: inputDrive,
                                     recurrentDrive: recurrentDrive, biasDrive: biasDrive, proposal: proposal,
                                     state: nextState, noise: noise, spectral: spectral)
        // Commit only after every calculation succeeded.
        state = nextState; noiseGenerator = generator; sensoryField = nextField
        frames.append(frame)
        return frame
    }
}

public struct ExplorationRecord: Codable, Sendable {
    public static let currentFormat = "essentials-exploration-v1"
    public let format: String
    public let seed: UInt64
    public let model: ReservoirModel
    public let projectionWeights: [Double]
    public let frames: [ExplorationFrame]

    public init(format: String = ExplorationRecord.currentFormat, seed: UInt64, model: ReservoirModel,
                projectionWeights: [Double], frames: [ExplorationFrame]) {
        self.format = format; self.seed = seed; self.model = model
        self.projectionWeights = projectionWeights; self.frames = frames
    }

    public static func read(from url: URL) throws -> ExplorationRecord {
        let attributes = try url.resourceValues(forKeys: [.fileSizeKey, .isRegularFileKey])
        guard attributes.isRegularFile == true, (attributes.fileSize ?? Int.max) <= 256 * 1_024 * 1_024 else {
            throw EssentialsError.invalid("Exploration must be a regular JSON file no larger than 256 MB.")
        }
        let data = try Data(contentsOf: url)
        guard data.count <= 256 * 1_024 * 1_024 else { throw EssentialsError.invalid("Exploration exceeds 256 MB.") }
        let record = try JSONDecoder().decode(Self.self, from: data)
        try record.validateStructure()
        return record
    }

    public func write(to url: URL) throws {
        _ = try verify()
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        let data = try encoder.encode(self)
        guard data.count <= 256 * 1_024 * 1_024 else { throw EssentialsError.invalid("Exploration exceeds 256 MB.") }
        try data.write(to: url, options: .atomic)
    }

    @discardableResult
    public func verify() throws -> VerificationReport {
        _ = try reconstructedEngine()
        return VerificationReport(checkedSteps: frames.count, checkedTurns: 0)
    }

    /// Cheap bounded shape validation. A reader must call verify() or construct
    /// ExplorationEngine(record:) before treating the numerical history as verified.
    public func validateStructure() throws {
        try Self.require(format == Self.currentFormat, "Unknown exploration format.")
        try Self.require(frames.count <= ExplorationEngine.maximumSteps, "Exploration exceeds 1,800 steps.")
        try Self.require(model.nodeCount == 32 && model.inputCount == 66, "Exploration model must be 32 nodes and 66 inputs.")
        try Self.vector(projectionWeights, count: 2_112, name: "projection weights")
        for (index, frame) in frames.enumerated() {
            try frame.controls.validate()
            try Self.require(frame.step == index + 1 && frame.time.isFinite, "Invalid exploration step or clock.")
            try Self.vector(frame.input, count: 66, name: "input")
            for (name, values) in [("previous state", frame.previousState), ("input drive", frame.inputDrive),
                                   ("recurrent drive", frame.recurrentDrive), ("bias drive", frame.biasDrive),
                                   ("proposal", frame.proposal), ("state", frame.state), ("noise", frame.noise)] {
                try Self.vector(values, count: 32, name: name)
            }
            try Self.require(frame.controls.sensoryEnabled == (frame.spectral != nil), "Sensory measurement presence disagrees with its control.")
            if let measurement = frame.spectral {
                try Self.require(measurement.dimension == 32, "Exploration sensory dimension must be 32.")
                try Self.vector(measurement.fieldVector, count: 32, name: "sensory vector")
                try Self.vector(measurement.eigenvalues, count: 32, name: "sensory eigenvalues")
                try Self.vector(measurement.covariance, count: 1_024, name: "sensory covariance")
                try Self.vector(measurement.eigenvectors, count: 1_024, name: "sensory eigenvectors")
                try Self.require([measurement.entropy, measurement.headShare, measurement.shoulderShare, measurement.tailShare].allSatisfy(\.isFinite),
                                 "Nonfinite exploration spectral summary.")
            }
        }
    }

    fileprivate func reconstructedEngine() throws -> ExplorationEngine {
        try validateStructure()
        var replay = try ExplorationEngine(seed: seed)
        try Self.require(model == replay.model, "Exploration weights do not match their seed.")
        try Self.require(projectionWeights == replay.projectionWeights, "Exploration projection does not match its seed.")
        for frame in frames {
            try frame.controls.validate()
            try Self.vector(frame.input, count: 66, name: "input")
            for (name, values) in [("previous state", frame.previousState), ("input drive", frame.inputDrive),
                                   ("recurrent drive", frame.recurrentDrive), ("bias drive", frame.biasDrive),
                                   ("proposal", frame.proposal), ("state", frame.state), ("noise", frame.noise)] {
                try Self.vector(values, count: 32, name: name)
            }
            try Self.require(frame.state.allSatisfy { abs($0) <= 1 }, "Exploration state exceeds the clip bounds.")
            let expected = try replay.advance(controls: frame.controls, pulse: frame.pulse)
            try Self.require(frame.step == expected.step, "Exploration steps are not contiguous.")
            try Self.near(frame.time, expected.time, "simulated time")
            try Self.near(frame.input, expected.input, "actual input")
            try Self.near(frame.previousState, expected.previousState, "previous state")
            try Self.near(frame.inputDrive, expected.inputDrive, "input drive")
            try Self.near(frame.recurrentDrive, expected.recurrentDrive, "recurrent drive")
            try Self.near(frame.biasDrive, expected.biasDrive, "bias drive")
            try Self.near(frame.proposal, expected.proposal, "proposal")
            try Self.near(frame.noise, expected.noise, "realized noise")
            try Self.near(frame.state, expected.state, "resulting state")
            switch (frame.spectral, expected.spectral) {
            case (nil, nil): break
            case (let actual?, let expected?): try Self.verifySpectral(actual, expected: expected)
            default: throw EssentialsError.verification("Exploration sensory measurement disagrees with the recorded enable state.")
            }
        }
        try replay.retainVerifiedHistory(frames)
        return replay
    }

    private static func verifySpectral(_ value: SpectralMeasurement, expected: SpectralMeasurement) throws {
        try require(value.dimension == 32, "Exploration sensory dimension must be 32.")
        try vector(value.fieldVector, count: 32, name: "sensory vector")
        try vector(value.eigenvalues, count: 32, name: "sensory eigenvalues")
        try vector(value.covariance, count: 1_024, name: "sensory covariance")
        try vector(value.eigenvectors, count: 1_024, name: "sensory eigenvectors")
        try require(value.eigenvalues.allSatisfy { $0 >= 0 }, "Negative sensory eigenvalue.")
        try near(value.fieldVector, expected.fieldVector, "sensory vector")
        try near(value.covariance, expected.covariance, "sensory covariance")
        try near(value.eigenvalues, expected.eigenvalues, "sensory eigenvalues")
        try near(value.entropy, expected.entropy, "top-eight entropy")
        try near(value.headShare, expected.headShare, "top-eight head share")
        try near(value.shoulderShare, expected.shoulderShare, "top-eight shoulder share")
        try near(value.tailShare, expected.tailShare, "top-eight tail share")
        // A repeated eigenvalue has no unique basis. Verify the stored basis against
        // its matrix instead of insisting on one LAPACK sign/basis choice.
        for mode in 0..<32 {
            let offset = mode * 32
            var norm = 0.0
            for row in 0..<32 {
                let component = value.eigenvectors[offset + row]
                norm += component * component
                var product = 0.0
                for column in 0..<32 { product += value.covariance[row * 32 + column] * value.eigenvectors[offset + column] }
                try near(product, value.eigenvalues[mode] * component, "sensory eigenvector residual")
            }
            try near(norm, 1, "sensory eigenvector norm")
            for previous in 0..<mode {
                var dot = 0.0
                for coordinate in 0..<32 { dot += value.eigenvectors[offset + coordinate] * value.eigenvectors[previous * 32 + coordinate] }
                try near(dot, 0, "sensory eigenvector orthogonality")
            }
        }
    }

    private static func require(_ condition: Bool, _ message: String) throws {
        if !condition { throw EssentialsError.verification(message) }
    }
    private static func vector(_ values: [Double], count: Int, name: String) throws {
        try require(values.count == count && values.allSatisfy(\.isFinite), "Invalid exploration \(name) dimensions or values.")
    }
    private static func near(_ actual: Double, _ expected: Double, _ name: String) throws {
        try require(actual.isFinite && expected.isFinite && abs(actual - expected) <= 2e-7 * max(1, abs(expected)),
                    "Exploration \(name) does not reproduce its numerical history.")
    }
    private static func near(_ actual: [Double], _ expected: [Double], _ name: String) throws {
        try require(actual.count == expected.count, "Exploration \(name) dimensions differ.")
        for index in actual.indices { try near(actual[index], expected[index], name) }
    }
}
