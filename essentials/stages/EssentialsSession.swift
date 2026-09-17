import Foundation

/// Runs contain simulated steps only: waiting for language never advances the clock.
public actor EssentialsSession {
    private let backendOverride: (any LanguageBackend)?
    private let languageTimeout: Duration
    private var running = false
    private var stopped = false
    private var activeReply: ReplyGate?
    public init(backend: (any LanguageBackend)? = nil, languageTimeout: Duration = .seconds(60)) {
        self.backendOverride = backend; self.languageTimeout = min(.seconds(60), max(.milliseconds(1), languageTimeout))
    }
    public func stop() {
        stopped = true
        activeReply?.finish(.failure(CancellationError()))
    }
    public func run(spec: RunSpecification,
                    onFrame: @escaping @Sendable (EssentialsFrame) async -> Void = { _ in },
                    onStatus: @escaping @Sendable (String) async -> Void = { _ in }) async throws -> RunRecord {
        try spec.validate()
        guard !running else { throw EssentialsError.invalid("This session already has a running experiment.") }
        running = true; stopped = false
        defer { running = false; activeReply = nil }
        let model = try ReservoirModel(seed: spec.seed)
        var engine = try ReservoirEngine(model: model, leak: spec.leak)
        var field = try SensoryField(seed: spec.seed ^ Recipe.fieldSeed)
        var fill = ReducedFill()
        var controller = try RetentionController(initialRetention: spec.initialRetention)
        var retention = spec.initialRetention
        var generator = SplitMix64(seed: spec.seed ^ Recipe.noiseSeed)
        var semantic = Array(repeating: 0.0, count: 48)
        var semanticTurnID: Int?
        let backend: any LanguageBackend
        if let backendOverride { backend = backendOverride }
        else if spec.language.backend == .ollama { backend = try OllamaLanguageBackend(configuration: spec.language) }
        else { backend = ScriptedLanguageBackend() }
        var record = RunRecord(recipeVersion: RunRecord.currentRecipeVersion, specification: spec, model: model,
                               projectionWeights: spec.stage == .reservoir ? [] : field.projectionWeights,
                               frames: [], turns: [], status: .stopped, failure: nil)
        record.frames.reserveCapacity(spec.steps)
        await onStatus("Running \(spec.stage.title)")
        for step in 1...spec.steps {
            if stopped || Task.isCancelled { break }
            var input = Recipe.forcing(step: step, dt: spec.dt)
            input.replaceSubrange(18..<66, with: semantic)
            let noise = (0..<32).map { _ in generator.nextSigned() * spec.noiseAmplitude }
            let state = try engine.step(input: input, noise: noise)
            let spectral = spec.stage == .reservoir ? nil : try field.step(input: input, retention: retention)
            let usedRetention = spectral == nil ? nil : retention
            let fillPercent = spec.stage == .regulation ? (100 * fill.update(eigenvalues: spectral!.eigenvalues, dt: spec.dt)) : nil
            let control: ControlMeasurement?
            if spec.stage == .regulation && spec.regulationEnabled {
                control = controller.update(fillPct: fillPercent!)
                retention = control!.appliedRetention
            } else { control = nil }
            if let semanticTurnID, record.turns[semanticTurnID - 1].applicationStep == nil {
                record.turns[semanticTurnID - 1].applicationStep = step
            }
            let frame = EssentialsFrame(step: step, time: Double(step) * spec.dt, input: input, state: state,
                                        noise: noise, spectral: spectral, fillPercent: fillPercent,
                                        retentionUsed: usedRetention, control: control, semanticTurnID: semanticTurnID)
            record.frames.append(frame)
            await onFrame(frame)
            if stopped || Task.isCancelled { break }
            if spec.stage != .reservoir && step % spec.turnEvery == 0 && step < spec.steps {
                let id = record.turns.count + 1
                let prompt = Recipe.prompt(spec: spec, frame: frame)
                var turn = LanguageTurn(id: id, observedStep: step, applicationStep: nil, prompt: prompt,
                                        contextKind: spec.stage == .spectralBridge ? .preparedExampleContext : .languageRequest,
                                        reply: nil, rawReply: nil, providerModel: nil, stopReason: nil, tokenCount: nil, encodedFeatures: nil, semanticVector: nil,
                                        status: .cancelled, failure: nil,
                                        backend: spec.stage == .spectralBridge ? "example" : spec.language.backend.rawValue,
                                        model: spec.stage.rawValue >= 3 ? spec.language.model : nil)
                do {
                    let response: LanguageResponse
                    if spec.stage == .spectralBridge {
                        response = LanguageResponse(text: Recipe.exampleTexts[(id - 1) % Recipe.exampleTexts.count], providerModel: "essentials-examples-v1", stopReason: "example")
                    } else {
                        await onStatus("Waiting for reply \(id) · simulated time paused at \(String(format: "%.3f", frame.time)) s")
                        guard !stopped && !Task.isCancelled else { throw CancellationError() }
                        let gate = ReplyGate(); activeReply = gate
                        response = try await boundedReply(backend: backend, request: LanguageRequest(turnID: id, prompt: prompt),
                                                       timeout: languageTimeout, gate: gate)
                        activeReply = nil
                    }
                    guard !stopped && !Task.isCancelled else { throw CancellationError() }
                    let reply = response.text
                    turn.rawReply = reply.utf8.count <= 65_536 ? reply : String(reply.prefix(16_000)); turn.providerModel = response.providerModel
                    turn.stopReason = response.stopReason; turn.tokenCount = response.tokenCount
                    guard response.complete, response.stopReason != "length", (response.tokenCount.map { $0 >= 0 && $0 <= 256 } ?? true) else {
                        throw EssentialsError.language("Language response was incomplete or exceeded its 256-token limit (stop reason: \(response.stopReason ?? "unknown")).")
                    }
                    guard !reply.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty, reply.utf8.count <= 65_536 else {
                        throw EssentialsError.language("Reply was empty or exceeded the text limit.")
                    }
                    let features = TextCodec.encode(reply)
                    semantic = TextCodec.applySpectralFeedback(features, measurement: spectral!)
                    turn.reply = reply; turn.encodedFeatures = features; turn.semanticVector = semantic; turn.status = .completed
                    semanticTurnID = id
                    record.turns.append(turn)
                    await onStatus("Running \(spec.stage.title)")
                } catch {
                    let cancelled = stopped || Task.isCancelled || error is CancellationError
                    turn.status = cancelled ? .cancelled : .failed
                    turn.failure = error.localizedDescription
                    record.turns.append(turn)
                    if !cancelled { record.status = .failed; record.failure = error.localizedDescription }
                    break
                }
            }
        }
        if record.status != .failed { record.status = record.frames.count == spec.steps ? .completed : .stopped }
        await onStatus(record.status == .completed ? "Run complete" : record.status == .failed ? "Run failed: \(record.failure ?? "Language error")" : "Run stopped")
        return record
    }
}

enum Recipe {
    static let fieldSeed: UInt64 = 0x53454E534F5259
    static let noiseSeed: UInt64 = 0x4E4F495345
    static let exampleTexts = [
        "A bright movement arrives. I notice its change and wonder what will remain when it is quiet.",
        "I remember the earlier rhythm. The sound is softer now, and I can wait with this steady pattern.",
        "Several shapes move together. I feel curious and hopeful about a different possibility."
    ]
    /// First 18 coordinates retain video (0..<8), audio (8..<16), auxiliary (16..<18).
    /// The 12-step-on / 18-step-off envelope makes persistence after input visible.
    static func forcing(step: Int, dt: Double, continuous: Bool = false) -> [Double] {
        var input = Array(repeating: 0.0, count: 66)
        guard continuous || (step - 1) % 30 < 12 else { return input }
        let time = Double(step - 1) * dt
        for index in 0..<8 { input[index] = 0.45 + 0.35 * sin(time * (0.19 + Double(index) * 0.07) + Double(index)) }
        for index in 8..<16 { input[index] = 0.3 + 0.25 * sin(time * (0.31 + Double(index - 8) * 0.11) + Double(index) * 0.7) }
        // Auxiliary values are left at zero; no environment data are read.
        return input
    }
    static func prompt(spec: RunSpecification, frame: EssentialsFrame) -> String {
        let spectral = frame.spectral!
        let format: (Double) -> String = { String(format: "%.8f", locale: Locale(identifier: "en_US_POSIX"), $0) }
        let values = spectral.eigenvalues.prefix(8).map(format).joined(separator: ", ")
        return """
        Essentials experimental reconstruction · \(spec.stage.title)
        This is a standalone, synthetic 32-node reservoir and a separate 32-dimensional sensory field.
        Step \(frame.step); simulated seconds \(format(frame.time)).
        Sensory field eigenvalues (top 8 of 32; covariance trace normalization on nonzero input): [\(values)]
        Top-eight normalized entropy: \(format(spectral.entropy)).
        Shares within the leading eight modes: head \(format(spectral.headShare)); shoulder \(format(spectral.shoulderShare)); tail \(format(spectral.tailShare)).
        Reduced active-mode fill: \(frame.fillPercent.map { format($0) + "%" } ?? "unavailable in this stage").
        Write one short observation about this pattern and what to notice next. Your complete reply will be encoded into the 48-coordinate semantic lane on the next step. Embedding features are unavailable. Do not claim that this describes Minime or Astrid.
        """
    }
}
