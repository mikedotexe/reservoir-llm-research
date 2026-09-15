import Foundation

public enum RunVerifier {
    public static func validateStructure(_ run: RunRecord) throws {
        try run.specification.validate()
        let spec = run.specification
        try require(run.recipeVersion == RunRecord.currentRecipeVersion, "Unknown recipe version.")
        try require(run.model.nodeCount == 32 && run.model.inputCount == 66, "Expected a 32 × 66 reservoir.")
        try vector(run.model.recurrentWeights, count: 1_024, name: "recurrent weights")
        try vector(run.model.inputWeights, count: 2_144, name: "input weights")
        try vector(run.projectionWeights, count: spec.stage == .reservoir ? 0 : 2_112, name: "sensory projection")
        try require(run.frames.count <= spec.steps, "Run has more steps than its recipe.")
        if run.status == .completed { try require(run.frames.count == spec.steps, "Completed run is missing steps.") }
        if run.status == .failed { try require(!(run.failure ?? "").isEmpty, "Failed run lacks its failure.") }
        else { try require(run.failure == nil, "Nonfailed run has a failure.") }
        try require(run.turns.count <= (spec.steps - 1) / spec.turnEvery, "Too many language turns.")
        if spec.stage == .reservoir { try require(run.turns.isEmpty, "Reservoir-only stage cannot contain language turns.") }
        for (index, frame) in run.frames.enumerated() {
            try require(frame.step == index + 1, "Steps must be contiguous and one-based.")
            try near(frame.time, Double(frame.step) * spec.dt, "Step \(frame.step) simulated time")
            try vector(frame.input, count: 66, name: "input")
            try vector(frame.state, count: 32, name: "state")
            try require(frame.state.allSatisfy { abs($0) <= 1 }, "Clipped state exceeded [-1, 1].")
            try vector(frame.noise, count: 32, name: "noise")
            if let id = frame.semanticTurnID { try require(id > 0 && id <= run.turns.count, "Invalid semantic turn reference.") }
            if spec.stage == .reservoir {
                try require(frame.spectral == nil && frame.retentionUsed == nil && frame.fillPercent == nil && frame.control == nil && frame.semanticTurnID == nil, "Stage 1 has unavailable measurements.")
            } else {
                guard let spectral = frame.spectral, let retention = frame.retentionUsed else {
                    throw EssentialsError.verification("Spectral stage is missing its field measurement.")
                }
                try require(spectral.dimension == 32, "Sensory field dimension must be 32.")
                try vector(spectral.eigenvalues, count: 32, name: "eigenvalues")
                try vector(spectral.eigenvectors, count: 1_024, name: "eigenvectors")
                try vector(spectral.covariance, count: 1_024, name: "covariance")
                try vector(spectral.fieldVector, count: 32, name: "field vector")
                try require(spectral.eigenvalues.allSatisfy { $0 >= 0 }, "Negative sensory eigenvalue.")
                for i in 1..<32 { try require(spectral.eigenvalues[i] <= spectral.eigenvalues[i - 1] + 1e-8, "Eigenvalues are not descending.") }
                for value in [spectral.entropy, spectral.headShare, spectral.shoulderShare, spectral.tailShare] {
                    try require(value.isFinite && value >= -1e-8 && value <= 1 + 1e-8, "Invalid spectral summary.")
                }
                try require(retention.isFinite && (0.82...0.995).contains(retention), "Invalid retention.")
                if spec.stage == .regulation {
                    guard let fill = frame.fillPercent else { throw EssentialsError.verification("Stage 4 lacks reduced fill.") }
                    try require(fill.isFinite && (0...100).contains(fill), "Invalid reduced fill.")
                    try require((frame.control != nil) == spec.regulationEnabled, "Controller availability disagrees with recipe.")
                    if let control = frame.control {
                        try require([control.error, control.integral, control.requestedRetention, control.appliedRetention].allSatisfy(\.isFinite), "Nonfinite controller value.")
                        try require((0.82...0.995).contains(control.appliedRetention), "Controller retention outside bounds.")
                    }
                } else { try require(frame.fillPercent == nil && frame.control == nil, "Reduced fill/controller is unavailable before stage 4.") }
            }
        }
        for (index, turn) in run.turns.enumerated() {
            try require(turn.id == index + 1 && turn.observedStep == turn.id * spec.turnEvery && turn.observedStep <= run.frames.count, "Invalid turn ordering or observation step.")
            try require(turn.prompt.utf8.count <= 65_536 && !turn.prompt.isEmpty, "Invalid retained prompt.")
            if let reply = turn.reply { try require(!reply.isEmpty && reply.utf8.count <= 65_536, "Invalid retained reply.") }
            if let raw = turn.rawReply { try require(raw.utf8.count <= 65_536, "Retained provider output exceeds text limit.") }
            if let tokens = turn.tokenCount, turn.status == .completed { try require(tokens >= 0, "Invalid provider token count.") }
            for metadata in [turn.providerModel, turn.stopReason] { try require((metadata?.utf8.count ?? 0) <= 1_024, "Oversized response metadata.") }
            if turn.status == .completed {
                guard turn.reply != nil, let encoded = turn.encodedFeatures, let semantic = turn.semanticVector else {
                    throw EssentialsError.verification("Completed turn lacks full feedback evidence.")
                }
                try vector(encoded, count: 48, name: "encoded features")
                try vector(semantic, count: 48, name: "semantic vector")
                try require(turn.failure == nil && turn.rawReply == turn.reply, "Completed turn lacks complete raw response evidence.")
                try require(turn.stopReason != "length" && (turn.tokenCount.map { $0 <= 256 } ?? true), "Incomplete provider response was used as feedback.")
                if let application = turn.applicationStep {
                    try require(application == turn.observedStep + 1 && application <= run.frames.count, "Feedback was not applied on the next step.")
                } else {
                    try require(run.status == .stopped && turn.observedStep == run.frames.count && index == run.turns.count - 1, "Completed feedback missing application step.")
                }
            } else {
                try require(index == run.turns.count - 1 && turn.observedStep == run.frames.count,
                            "Unsuccessful turn must end the run.")
                try require(turn.reply == nil && turn.encodedFeatures == nil && turn.semanticVector == nil && turn.applicationStep == nil,
                            "Incomplete reply must not produce feedback.")
                try require(!(turn.failure ?? "").isEmpty, "Unsuccessful turn lacks diagnostic.")
                try require(turn.status == .failed ? run.status == .failed : run.status == .stopped, "Turn outcome disagrees with run outcome.")
            }
            try require(turn.contextKind == (spec.stage == .spectralBridge ? .preparedExampleContext : .languageRequest), "Prepared context/request kind disagrees with stage.")
            let expectedBackend = spec.stage == .spectralBridge ? "example" : spec.language.backend.rawValue
            try require(turn.backend == expectedBackend, "Turn backend disagrees with recipe.")
            try require(turn.model == (spec.stage.rawValue >= 3 ? spec.language.model : nil), "Turn model disagrees with recipe.")
        }
        if spec.stage != .reservoir {
            let requiredAppliedTurns = max(0, run.frames.count - 1) / spec.turnEvery
            try require(run.turns.count >= requiredAppliedTurns, "Run advanced beyond a scheduled turn without retaining it.")
            try require(run.turns.prefix(requiredAppliedTurns).allSatisfy { $0.status == .completed && $0.applicationStep != nil }, "Run advanced past an unsuccessful language turn.")
        }
        if run.status == .completed && spec.stage != .reservoir {
            try require(run.turns.count == (spec.steps - 1) / spec.turnEvery, "Completed run is missing language turns.")
        }
    }

    /// Reconstructs every step from saved weights, input and noise. Does not contact a model.
    @discardableResult
    public static func verify(_ run: RunRecord) throws -> VerificationReport {
        try validateStructure(run)
        let spec = run.specification
        let expectedModel = try ReservoirModel(seed: spec.seed)
        try near(run.model.recurrentWeights, expectedModel.recurrentWeights, "Seeded recurrent weights")
        try near(run.model.inputWeights, expectedModel.inputWeights, "Seeded input weights")
        var engine = try ReservoirEngine(model: run.model, leak: spec.leak)
        var field = try SensoryField(seed: spec.seed ^ Recipe.fieldSeed)
        if spec.stage != .reservoir { try near(run.projectionWeights, field.projectionWeights, "Seeded sensory projection") }
        var fill = ReducedFill()
        var controller = try RetentionController(initialRetention: spec.initialRetention)
        var retention = spec.initialRetention
        var noiseGenerator = SplitMix64(seed: spec.seed ^ Recipe.noiseSeed)
        for frame in run.frames {
            var expectedInput = Recipe.forcing(step: frame.step, dt: spec.dt)
            let turn = run.turns.last { $0.applicationStep.map { $0 <= frame.step } ?? false }
            try require(frame.semanticTurnID == turn?.id, "Step \(frame.step) semantic reference is not the current applied turn.")
            if let semantic = turn?.semanticVector { expectedInput.replaceSubrange(18..<66, with: semantic) }
            try near(frame.input, expectedInput, "Step \(frame.step) actual input")
            let expectedNoise = (0..<32).map { _ in noiseGenerator.nextSigned() * spec.noiseAmplitude }
            try near(frame.noise, expectedNoise, "Step \(frame.step) seeded noise")
            try near(frame.state, try engine.step(input: frame.input, noise: frame.noise), "Step \(frame.step) recurrence")
            if let stored = frame.spectral {
                try near(frame.retentionUsed!, retention, "Step \(frame.step) applied retention")
                let measured = try field.step(input: frame.input, retention: retention)
                try near(stored.fieldVector, measured.fieldVector, "Field input")
                try near(stored.covariance, measured.covariance, "Covariance")
                try near(stored.eigenvalues, measured.eigenvalues, "Sensory eigenvalues")
                try near(stored.entropy, measured.entropy, "Entropy")
                try near(stored.headShare, measured.headShare, "Head share")
                try near(stored.shoulderShare, measured.shoulderShare, "Shoulder share")
                try near(stored.tailShare, measured.tailShare, "Tail share")
                // Eigenvector sign and degenerate bases can vary across LAPACK builds.
                // Check their mathematical meaning rather than requiring identical vectors.
                try verifyEigenvectors(stored)
                if spec.stage == .regulation {
                    let measuredFill = 100 * fill.update(eigenvalues: measured.eigenvalues, dt: spec.dt)
                    try near(frame.fillPercent!, measuredFill, "Reduced active-mode fill")
                    if let storedControl = frame.control {
                        let expected = controller.update(fillPct: measuredFill)
                        try near(storedControl.error, expected.error, "Controller error")
                        try near(storedControl.integral, expected.integral, "Controller integral")
                        try near(storedControl.requestedRetention, expected.requestedRetention, "Requested retention")
                        try near(storedControl.appliedRetention, expected.appliedRetention, "Next-step retention")
                        retention = expected.appliedRetention
                    }
                }
            }
        }
        for turn in run.turns {
            let observation = run.frames[turn.observedStep - 1]
            try require(turn.prompt == Recipe.prompt(spec: spec, frame: observation), "Prompt differs from the retained spectral observation.")
            if let reply = turn.reply {
                let features = TextCodec.encode(reply)
                try near(turn.encodedFeatures!, features, "Text codec features")
                try near(turn.semanticVector!, TextCodec.applySpectralFeedback(features, measurement: observation.spectral!), "Spectral feedback encoding")
                if spec.stage == .spectralBridge {
                    try require(reply == Recipe.exampleTexts[(turn.id - 1) % Recipe.exampleTexts.count], "Supplied example text differs from recipe.")
                }
            }
        }
        return VerificationReport(checkedSteps: run.frames.count, checkedTurns: run.turns.count)
    }
    private static func verifyEigenvectors(_ measurement: SpectralMeasurement) throws {
        let n = measurement.dimension
        for mode in 0..<n {
            let v = Array(measurement.eigenvectors[(mode * n)..<((mode + 1) * n)])
            try near(v.reduce(0) { $0 + $1 * $1 }, 1, "Eigenvector norm")
            for row in 0..<n {
                var product = 0.0
                for column in 0..<n { product += measurement.covariance[row * n + column] * v[column] }
                try near(product, measurement.eigenvalues[mode] * v[row], "Eigenvector residual")
            }
            for previous in 0..<mode {
                var dot = 0.0
                for coordinate in 0..<n { dot += v[coordinate] * measurement.eigenvectors[previous * n + coordinate] }
                try near(dot, 0, "Eigenvector orthogonality")
            }
        }
    }
    private static func require(_ condition: Bool, _ message: String) throws {
        if !condition { throw EssentialsError.verification(message) }
    }
    private static func vector(_ values: [Double], count: Int, name: String) throws {
        try require(values.count == count && values.allSatisfy(\.isFinite), "Invalid \(name) dimensions or nonfinite value.")
    }
    private static func near(_ actual: Double, _ expected: Double, _ name: String) throws {
        try require(actual.isFinite && expected.isFinite && abs(actual - expected) <= 2e-7 * max(1, abs(expected)), "\(name) does not replay (\(actual), expected \(expected)).")
    }
    private static func near(_ actual: [Double], _ expected: [Double], _ name: String) throws {
        try require(actual.count == expected.count, "\(name) dimensions differ.")
        for i in actual.indices { try near(actual[i], expected[i], "\(name)[\(i)]") }
    }
}
