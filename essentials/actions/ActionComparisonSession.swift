import Foundation

/// Owns both numerical arms and their finite action opportunities. Waiting for a
/// response or journal storage never advances either arm's simulated clock.
public actor ActionComparisonSession {
    public let specification: ActionComparisonSpecification
    private let journalStore: any ActionJournalStore
    private let backend: any LanguageBackend
    private let timeout: Duration
    private let tape: ActionReplyTape?
    private var left: ActionArmEngine?
    private var right: ActionArmEngine
    private var busy = false
    private var running = false
    private var stopped = false
    private var activeReply: ReplyGate?

    public init(specification: ActionComparisonSpecification,
                journalStore: any ActionJournalStore, backend: (any LanguageBackend)? = nil,
                languageTimeout: Duration = .seconds(60)) throws {
        try specification.validate()
        self.specification = specification; self.journalStore = journalStore
        timeout = min(.seconds(60), max(.milliseconds(1), languageTimeout))
        if let backend { self.backend = backend }
        else if specification.language.backend == .ollama { self.backend = try OllamaLanguageBackend(configuration: specification.language) }
        else { self.backend = ScriptedActionLanguageBackend() }
        tape = specification.mode == .fixedReplay ? try ActionReplyTape.make(specification: specification) : nil
        if specification.comparePrevious, let previous = specification.stage.previous {
            left = try ActionArmEngine(spec: specification, stage: specification.comparisonKind == .observation ? .journalOutput : previous, arm: .left)
        }
        right = try ActionArmEngine(spec: specification, stage: specification.stage, arm: .right)
    }

    public func snapshot() -> ActionComparisonRecord {
        let failed = left?.record.status == .failed || right.record.status == .failed
        let completed = right.record.status == .completed && (left?.record.status == .completed || left == nil)
        return ActionComparisonRecord(format: ActionComparisonRecord.currentFormat, specification: specification,
            tape: tape, left: left?.record, right: right.record, status: failed ? .failed : completed ? .completed : .stopped,
            failure: failed ? (left?.record.failure ?? right.record.failure) : nil)
    }

    /// Cancels a pending provider request. An interrupted action ends this session;
    /// its partial output is never encoded or retried. Between-action stops can resume.
    public func stop() {
        stopped = true
        activeReply?.finish(.failure(CancellationError()))
    }

    private func begin(ownedRun: Bool = false) throws {
        guard !busy && (!running || ownedRun) else { throw EssentialsError.invalid("An action step or finite run is already in progress.") }
        guard snapshot().status != .failed, right.record.frames.count < specification.steps else {
            throw EssentialsError.invalid("This action experiment has failed or completed; reset to start another.")
        }
        guard !right.record.actions.contains(where: { $0.status == .cancelled }),
              !(left?.record.actions.contains(where: { $0.status == .cancelled }) ?? false) else {
            throw EssentialsError.invalid("An action was interrupted. Start a new comparison to preserve matched action exposure.")
        }
        guard !Task.isCancelled else { throw CancellationError() }
        busy = true; stopped = false
    }

    @discardableResult
    public func advance(onObservation: @escaping @Sendable (ActionComparisonRecord) async -> Void = { _ in }) async throws -> ActionComparisonRecord {
        try await advance(ownedRun: false, onObservation: onObservation)
    }
    private func advance(ownedRun: Bool, onObservation: @escaping @Sendable (ActionComparisonRecord) async -> Void = { _ in }) async throws -> ActionComparisonRecord {
        try begin(ownedRun: ownedRun)
        defer { busy = false; activeReply = nil }
        let next = right.record.frames.count + 1
        if next < specification.steps && next % specification.turnEvery == 0 {
            guard right.record.actions.count < ActionRules.maximumActions,
                  (left?.record.actions.count ?? 0) < ActionRules.maximumActions else {
                throw EssentialsError.invalid("Reached the 128-action limit. Save and reset this experiment.")
            }
        }
        // Use copies so a numerical error cannot advance just one comparison arm.
        var nextLeft = left, nextRight = right
        try nextLeft?.advance(); try nextRight.advance()
        left = nextLeft; right = nextRight
        await onObservation(snapshot())
        if next < specification.steps && next % specification.turnEvery == 0 {
            await actBoth(trigger: .scheduled)
        }
        return snapshot()
    }

    @discardableResult
    public func writeJournal() async throws -> ActionComparisonRecord {
        try begin()
        defer { busy = false; activeReply = nil }
        guard right.canAct else {
            throw EssentialsError.invalid("Write journal needs an eligible version and one completed, unused, nonfinal boundary (maximum 128 actions).")
        }
        await actBoth(trigger: .manual)
        return snapshot()
    }

    public func run(onFrame: @escaping @Sendable (ActionComparisonRecord) async -> Void = { _ in },
                    onStatus: @escaping @Sendable (String) async -> Void = { _ in }) async throws -> ActionComparisonRecord {
        guard !busy && !running else { throw EssentialsError.invalid("An action step or finite run is already in progress.") }
        running = true
        defer { running = false }
        stopped = false
        await onStatus("Running \(specification.stage.title) · \(specification.mode.title)")
        while !stopped && !Task.isCancelled && snapshot().status != .failed && right.record.frames.count < specification.steps {
            let record = try await advance(ownedRun: true)
            await onFrame(record)
        }
        let record = snapshot()
        await onStatus(record.status == .completed ? "Comparison complete" : record.status == .failed ? "Comparison failed" : "Comparison stopped")
        return record
    }

    private func actBoth(trigger: ActionTrigger) async {
        let observation = specification.comparisonKind == .observation
        let number = right.record.actions.count + 1
        let order: [ActionArm] = left == nil ? [.right] : observation && number % 2 == 0 ? [.right, .left] : [.left, .right]
        var priorFailed = false
        var eligibleOrder = 0
        for arm in order {
            guard var engine = arm == .left ? left : right, engine.canAct else { continue }
            if !stopped && !Task.isCancelled && (observation || !priorFailed) {
                eligibleOrder += 1
                await act(&engine, trigger: trigger, requestOrder: eligibleOrder)
            } else {
                let latest = engine.record.stage.hasMemory ? engine.record.journals.last : nil
                var receipt = engine.receipt(trigger: trigger, tape: tape, memory: nil, memoryExpectedID: latest?.id)
                receipt.status = .cancelled; receipt.failurePhase = .cancelled
                receipt.failure = "Paired action stopped before this request started."
                engine.record.actions.append(receipt)
            }
            priorFailed = priorFailed || engine.record.status == .failed
            if arm == .left { left = engine } else { right = engine }
        }
    }

    private func act(_ engine: inout ActionArmEngine, trigger: ActionTrigger, requestOrder: Int) async {
        let latest = engine.record.stage.hasMemory ? engine.record.journals.last : nil
        var memory: JournalEntry?
        if let latest {
            do {
                let loaded = try journalStore.read(entryID: latest.id, arm: engine.record.arm)
                guard loaded == latest else { throw EssentialsError.invalid("Saved journal read differs from the completed entry.") }
                memory = loaded
            } catch {
                var receipt = engine.receipt(trigger: trigger, tape: tape, memory: nil, memoryExpectedID: latest.id)
                receipt.status = .failed; receipt.failurePhase = .memoryRead; receipt.failure = ActionRules.failureText(error)
                engine.record.actions.append(receipt); engine.record.status = .failed; engine.record.failure = receipt.failure
                return
            }
        }
        var receipt = engine.receipt(trigger: trigger, tape: tape, memory: memory)
        do {
            let response: LanguageResponse
            if let tape {
                let packet = tape.packets[receipt.observedStep - 1]
                let choice: JournalAction = engine.record.stage.hasChoice && trigger != .manual ? packet.choice : .writeJournal
                response = LanguageResponse(text: ActionRules.envelope(action: choice, text: packet.text),
                    providerModel: "essentials-action-tape-v1", stopReason: "replayed")
            } else {
                guard !stopped && !Task.isCancelled else { throw CancellationError() }
                receipt.requestStarted = true; receipt.requestOrder = requestOrder
                let gate = ReplyGate(); activeReply = gate
                response = try await boundedReply(backend: backend, request: LanguageRequest(turnID: receipt.id, prompt: receipt.prompt),
                                                  timeout: timeout, gate: gate)
                activeReply = nil
            }
            guard !stopped && !Task.isCancelled else { throw CancellationError() }
            // Bound every provider-owned field, including incomplete attempts.
            receipt.rawReply = String(response.text.prefix(16_000))
            receipt.rawReplyByteCount = response.text.utf8.count
            if response.text.utf8.count <= ActionRules.maximumTextBytes { receipt.rawReply = response.text }
            receipt.providerModel = response.providerModel.map { String($0.prefix(256)) }
            receipt.stopReason = response.stopReason.map { String($0.prefix(256)) }
            receipt.tokenCount = response.tokenCount; receipt.providerComplete = response.complete
            let parsed: (JournalAction, String)
            do { parsed = try ActionRules.parse(response, stage: trigger == .manual ? .journalOutput : engine.record.stage) }
            catch { receipt.failurePhase = .responseValidation; throw error }
            receipt.chosenAction = parsed.0; receipt.status = .completed
            if parsed.0 == .writeJournal {
                let entry = JournalEntry(id: ActionRules.journalID(actionID: receipt.id, step: receipt.observedStep, text: parsed.1),
                    actionID: receipt.id, observedStep: receipt.observedStep, text: parsed.1, sha256: ActionRules.hash(parsed.1))
                receipt.journalEntryID = entry.id
                do {
                    let saved = try journalStore.save(entry, arm: engine.record.arm)
                    guard saved.status == .saved, saved.entryID == entry.id, saved.sha256 == entry.sha256,
                          saved.relativePath == "\(engine.record.arm.rawValue)/\(entry.id).json", saved.failure == nil,
                          try journalStore.read(entryID: entry.id, arm: engine.record.arm) == entry else {
                        throw EssentialsError.invalid("Journal save/readback receipt was not valid.")
                    }
                    receipt.saveReceipt = saved
                } catch {
                    receipt.saveReceipt = JournalSaveReceipt(status: .failed, entryID: entry.id, sha256: entry.sha256,
                        relativePath: nil, failure: ActionRules.failureText(error))
                    receipt.failurePhase = .journalSave; receipt.failure = ActionRules.failureText(error)
                    engine.record.actions.append(receipt); engine.record.status = .failed; engine.record.failure = receipt.failure
                    return
                }
                engine.record.journals.append(entry)
                let features = TextCodec.encode(parsed.1)
                receipt.encodedFeatures = features
                // Preparation is recorded even when the D-version gate is off.
                let vector = tape.map { $0.packets[receipt.observedStep - 1].semanticVector }
                    ?? TextCodec.applySpectralFeedback(features, measurement: engine.record.frames.last!.spectral!)
                receipt.semanticVector = vector
                if engine.record.stage.hasFeedback {
                    engine.semantic = vector; engine.semanticActionID = receipt.id
                }
            }
            engine.record.actions.append(receipt)
        } catch {
            let cancelled = stopped || Task.isCancelled || error is CancellationError
            receipt.status = cancelled ? .cancelled : .failed
            receipt.failurePhase = cancelled ? .cancelled : (receipt.failurePhase ?? .language)
            receipt.failure = ActionRules.failureText(error)
            engine.record.actions.append(receipt)
            if !cancelled { engine.record.status = .failed; engine.record.failure = receipt.failure }
        }
    }
}
