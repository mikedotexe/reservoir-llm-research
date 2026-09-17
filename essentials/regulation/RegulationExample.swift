import Foundation

/// The already-qualified, field-only controller example. This is deliberately
/// separate from the A–H journal ladder and cannot enable a language backend.
public struct RegulationExampleSpecification: Codable, Sendable, Equatable {
    public let fixture: String
    public let fieldSeed: UInt64
    public let inputSeed: UInt64
    public let steps: Int
    public let dt: Double
    public let initialRetention: Double
    public let targetFillPercent: Double
    public let evaluationFirstStep: Int
    public let evaluationLastStep: Int
    public let question: String
    public let expectedDifference: String
    public let alternativeExplanation: String
    public let stoppingPoint: String

    public init() {
        fixture = "uniform66-seed42-field98-v1"
        fieldSeed = 98; inputSeed = 42; steps = 600; dt = 1.0 / 3.0
        initialRetention = 0.955; targetFillPercent = 68
        evaluationFirstStep = 301; evaluationLastStep = 600
        question = "Can sensory retention control reduce target error under this richer input?"
        expectedDifference = "Reproduce the known lower mean absolute target error in the controlled field over steps 301–600."
        alternativeExplanation = "The result depends on the declared synthetic input and reduced fill measure; it does not promise target attainment under other inputs."
        stoppingPoint = "600 steps, one fixed paired mechanism example; evaluate steps 301–600 without selecting a different window."
    }
    enum CodingKeys: String, CodingKey {
        case fixture, fieldSeed, inputSeed, steps, dt, initialRetention, targetFillPercent,
             evaluationFirstStep, evaluationLastStep, question, expectedDifference, alternativeExplanation, stoppingPoint
    }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self), d = Self()
        fixture = try c.decodeIfPresent(String.self, forKey: .fixture) ?? d.fixture
        fieldSeed = try c.decodeIfPresent(UInt64.self, forKey: .fieldSeed) ?? d.fieldSeed
        inputSeed = try c.decodeIfPresent(UInt64.self, forKey: .inputSeed) ?? d.inputSeed
        steps = try c.decodeIfPresent(Int.self, forKey: .steps) ?? d.steps
        dt = try c.decodeIfPresent(Double.self, forKey: .dt) ?? d.dt
        initialRetention = try c.decodeIfPresent(Double.self, forKey: .initialRetention) ?? d.initialRetention
        targetFillPercent = try c.decodeIfPresent(Double.self, forKey: .targetFillPercent) ?? d.targetFillPercent
        evaluationFirstStep = try c.decodeIfPresent(Int.self, forKey: .evaluationFirstStep) ?? d.evaluationFirstStep
        evaluationLastStep = try c.decodeIfPresent(Int.self, forKey: .evaluationLastStep) ?? d.evaluationLastStep
        question = try c.decodeIfPresent(String.self, forKey: .question) ?? d.question
        expectedDifference = try c.decodeIfPresent(String.self, forKey: .expectedDifference) ?? d.expectedDifference
        alternativeExplanation = try c.decodeIfPresent(String.self, forKey: .alternativeExplanation) ?? d.alternativeExplanation
        stoppingPoint = try c.decodeIfPresent(String.self, forKey: .stoppingPoint) ?? d.stoppingPoint
    }
    public func validate() throws {
        let d = Self()
        guard fixture == d.fixture, fieldSeed == d.fieldSeed, inputSeed == d.inputSeed,
              steps == d.steps, dt == d.dt, initialRetention == d.initialRetention,
              targetFillPercent == d.targetFillPercent, evaluationFirstStep == d.evaluationFirstStep,
              evaluationLastStep == d.evaluationLastStep else {
            throw EssentialsError.invalid("The controller mechanism example must retain its qualified seeds, 600 steps, controller and 301–600 evaluation window.")
        }
        guard [question, expectedDifference, alternativeExplanation, stoppingPoint].allSatisfy({ !$0.isEmpty && $0.utf8.count <= 4096 }) else {
            throw EssentialsError.invalid("Controller example study notes must be nonempty and at most 4 KiB each.")
        }
    }
}

public struct RegulationArmFrame: Codable, Sendable {
    public let spectral: SpectralMeasurement
    public let fillPercent: Double
    public let retentionUsed: Double
    /// Present only for the regulated arm; applies on the following step.
    public let control: ControlMeasurement?
}
public struct RegulationExampleFrame: Codable, Sendable, Identifiable {
    public var id: Int { step }
    public let step: Int
    public let time: Double
    /// Common full 66-coordinate input. No coordinates are journal returns.
    public let input: [Double]
    public let baseline: RegulationArmFrame
    public let regulated: RegulationArmFrame
}
public struct RegulationExampleSummary: Codable, Sendable {
    public let evaluationFirstStep: Int
    public let evaluationLastStep: Int
    public let evaluationCount: Int
    public let baselineMeanAbsoluteError: Double
    public let regulatedMeanAbsoluteError: Double
    public let baselineMeanFillPercent: Double
    public let regulatedMeanFillPercent: Double
    public let regulatedMinimumRetention: Double
    public let regulatedMaximumRetention: Double
}

public struct RegulationExampleRecord: Codable, Sendable {
    public static let currentFormat = "essentials-regulation-v1"
    public let format: String
    public let specification: RegulationExampleSpecification
    public let projectionWeights: [Double]
    public let frames: [RegulationExampleFrame]
    /// A reproducible whole-window summary; viewers must not expose it before
    /// the recorded cursor reaches the evaluation window's final step.
    public let summary: RegulationExampleSummary

    public static func generate(specification spec: RegulationExampleSpecification = .init()) throws -> Self {
        try spec.validate()
        var baseline = try SensoryField(seed: spec.fieldSeed), regulated = try SensoryField(seed: spec.fieldSeed)
        var baselineFill = ReducedFill(), regulatedFill = ReducedFill()
        var controller = try RetentionController(initialRetention: spec.initialRetention)
        var random = SplitMix64(seed: spec.inputSeed)
        var frames: [RegulationExampleFrame] = []
        frames.reserveCapacity(spec.steps)
        for step in 1...spec.steps {
            let input = (0..<66).map { _ in random.nextSigned() }
            let retention = controller.currentRetention
            let a = try baseline.step(input: input, retention: spec.initialRetention)
            let b = try regulated.step(input: input, retention: retention)
            let af = 100 * baselineFill.update(eigenvalues: a.eigenvalues, dt: spec.dt)
            let bf = 100 * regulatedFill.update(eigenvalues: b.eigenvalues, dt: spec.dt)
            let control = controller.update(fillPct: bf)
            frames.append(RegulationExampleFrame(step: step, time: Double(step) * spec.dt, input: input,
                baseline: RegulationArmFrame(spectral: a, fillPercent: af, retentionUsed: spec.initialRetention, control: nil),
                regulated: RegulationArmFrame(spectral: b, fillPercent: bf, retentionUsed: retention, control: control)))
        }
        return Self(format: currentFormat, specification: spec, projectionWeights: baseline.projectionWeights,
                    frames: frames, summary: summarize(frames, specification: spec))
    }

    public static func read(from url: URL) throws -> Self {
        let attributes = try url.resourceValues(forKeys: [.isRegularFileKey, .fileSizeKey])
        guard attributes.isRegularFile == true, (attributes.fileSize ?? Int.max) <= ActionRules.maximumRecordBytes else {
            throw EssentialsError.invalid("Controller example must be a regular JSON file no larger than 256 MB.")
        }
        let data = try Data(contentsOf: url)
        guard data.count <= ActionRules.maximumRecordBytes else { throw EssentialsError.invalid("Controller example exceeds 256 MB.") }
        let record = try JSONDecoder().decode(Self.self, from: data)
        try record.validateStructure()
        return record
    }
    public func write(to url: URL) throws {
        _ = try verify()
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        let data = try encoder.encode(self)
        guard data.count <= ActionRules.maximumRecordBytes else { throw EssentialsError.invalid("Controller example exceeds 256 MB.") }
        try data.write(to: url, options: .atomic)
    }
    public func validateStructure() throws {
        try specification.validate()
        try Self.require(format == Self.currentFormat, "Unknown controller example format.")
        try Self.require(frames.count == specification.steps, "Controller example must preserve all 600 paired observations.")
        try Self.vector(projectionWeights, count: 2112, name: "projection")
        for (index, frame) in frames.enumerated() {
            try Self.require(frame.step == index + 1, "Controller steps are not contiguous.")
            try Self.near(frame.time, Double(frame.step) * specification.dt, "clock")
            try Self.vector(frame.input, count: 66, name: "common input")
            try Self.require(frame.baseline.control == nil && frame.regulated.control != nil,
                             "Only the regulated field may contain controller outputs.")
            for arm in [frame.baseline, frame.regulated] {
                try ActionComparisonVerifier.spectralStructure(arm.spectral)
                try Self.require(arm.fillPercent.isFinite && (0...100).contains(arm.fillPercent)
                                 && arm.retentionUsed.isFinite && (0.82...0.995).contains(arm.retentionUsed),
                                 "Controller fill or retention is invalid.")
            }
        }
    }
    @discardableResult public func verify() throws -> VerificationReport {
        try validateStructure()
        let expected = try Self.generate(specification: specification)
        try Self.require(projectionWeights == expected.projectionWeights, "Controller field projection differs from its seed.")
        for (actual, expected) in zip(frames, expected.frames) {
            try Self.near(actual.input, expected.input, "common input")
            for (a, e) in [(actual.baseline, expected.baseline), (actual.regulated, expected.regulated)] {
                try ActionComparisonVerifier.spectral(a.spectral, expected: e.spectral)
                try Self.near(a.fillPercent, e.fillPercent, "fill")
                try Self.near(a.retentionUsed, e.retentionUsed, "retention used")
                if let a = a.control, let e = e.control {
                    try Self.near(a.error, e.error, "control error")
                    try Self.near(a.integral, e.integral, "control integral")
                    try Self.near(a.requestedRetention, e.requestedRetention, "requested retention")
                    try Self.near(a.appliedRetention, e.appliedRetention, "next-step retention")
                }
            }
        }
        let e = Self.summarize(frames, specification: specification), a = summary
        try Self.require(a.evaluationFirstStep == e.evaluationFirstStep && a.evaluationLastStep == e.evaluationLastStep
                         && a.evaluationCount == e.evaluationCount, "Controller evaluation window differs.")
        for (name, actual, expected) in [
            ("baseline target error", a.baselineMeanAbsoluteError, e.baselineMeanAbsoluteError),
            ("regulated target error", a.regulatedMeanAbsoluteError, e.regulatedMeanAbsoluteError),
            ("baseline mean fill", a.baselineMeanFillPercent, e.baselineMeanFillPercent),
            ("regulated mean fill", a.regulatedMeanFillPercent, e.regulatedMeanFillPercent),
            ("minimum retention", a.regulatedMinimumRetention, e.regulatedMinimumRetention),
            ("maximum retention", a.regulatedMaximumRetention, e.regulatedMaximumRetention)] {
            try Self.near(actual, expected, name)
        }
        return VerificationReport(checkedSteps: frames.count * 2, checkedTurns: 0)
    }
    private static func summarize(_ frames: [RegulationExampleFrame], specification spec: RegulationExampleSpecification) -> RegulationExampleSummary {
        let sample = frames.filter { (spec.evaluationFirstStep...spec.evaluationLastStep).contains($0.step) }
        let n = Double(sample.count)
        return RegulationExampleSummary(evaluationFirstStep: spec.evaluationFirstStep, evaluationLastStep: spec.evaluationLastStep,
            evaluationCount: sample.count,
            baselineMeanAbsoluteError: sample.reduce(0) { $0 + abs($1.baseline.fillPercent - spec.targetFillPercent) } / n,
            regulatedMeanAbsoluteError: sample.reduce(0) { $0 + abs($1.regulated.fillPercent - spec.targetFillPercent) } / n,
            baselineMeanFillPercent: sample.reduce(0) { $0 + $1.baseline.fillPercent } / n,
            regulatedMeanFillPercent: sample.reduce(0) { $0 + $1.regulated.fillPercent } / n,
            regulatedMinimumRetention: sample.map(\.regulated.retentionUsed).min()!,
            regulatedMaximumRetention: sample.map(\.regulated.retentionUsed).max()!)
    }
    private static func require(_ value: Bool, _ message: String) throws {
        guard value else { throw EssentialsError.verification(message) }
    }
    private static func vector(_ values: [Double], count: Int, name: String) throws {
        try require(values.count == count && values.allSatisfy(\.isFinite), "Invalid controller \(name).")
    }
    private static func near(_ a: Double, _ b: Double, _ name: String) throws {
        try require(a.isFinite && b.isFinite && abs(a - b) <= 1e-8 * max(1, abs(b)), "Controller \(name) differs.")
    }
    private static func near(_ a: [Double], _ b: [Double], _ name: String) throws {
        try require(a.count == b.count, "Controller \(name) dimensions differ.")
        for (a, b) in zip(a, b) { try near(a, b, name) }
    }
}
