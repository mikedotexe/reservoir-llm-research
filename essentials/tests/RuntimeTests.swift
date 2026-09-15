import XCTest
@testable import EssentialsCore

final class RuntimeTests: XCTestCase, @unchecked Sendable {
    func testRecipeDefaultsAndBounds() throws {
        let spec = try JSONDecoder().decode(RunSpecification.self, from: Data("{\"stage\":3}".utf8))
        XCTAssertEqual(spec.steps, 300); XCTAssertEqual(spec.dt, 1.0 / 3.0)
        XCTAssertEqual(spec.language.backend, .scripted)
        var invalid = spec; invalid.steps = -1
        XCTAssertThrowsError(try invalid.validate())
        invalid = spec; invalid.noiseAmplitude = .nan
        XCTAssertThrowsError(try invalid.validate())
        XCTAssertThrowsError(try JSONDecoder().decode(RunSpecification.self, from: Data("{\"stage\":5}".utf8)))
    }
    func testAllStagesReplayAndAvailability() async throws {
        for stage in EssentialsStage.allCases {
            let run = try await EssentialsSession().run(spec: RunSpecification(stage: stage, steps: 36, noiseAmplitude: 0.01))
            XCTAssertEqual(run.status, .completed)
            XCTAssertEqual(try RunVerifier.verify(run).checkedSteps, 36)
            XCTAssertEqual(run.frames[0].state.count, 32)
            XCTAssertEqual(run.frames[0].spectral != nil, stage != .reservoir)
            XCTAssertEqual(run.frames[0].fillPercent != nil, stage == .regulation)
            XCTAssertEqual(run.turns.count, stage == .reservoir ? 0 : 1)
            if let turn = run.turns.first {
                XCTAssertEqual(turn.contextKind, stage == .spectralBridge ? .preparedExampleContext : .languageRequest)
                XCTAssertTrue(turn.prompt.contains("Top-eight normalized entropy:"))
                XCTAssertTrue(turn.prompt.contains("Shares within the leading eight modes:"))
                XCTAssertFalse(turn.prompt.contains("Sensory entropy:"))
            }
            XCTAssertTrue(run.frames[0].input[16..<18].allSatisfy { $0 == 0 })
            XCTAssertTrue(run.frames[12].input[0..<18].allSatisfy { $0 == 0 })
            XCTAssertTrue(run.frames[12].state.contains { abs($0) > 1e-6 })
        }
    }
    func testExactLanguageFeedbackAndFrozenSimulation() async throws {
        let backend = SuspendedBackend()
        let session = EssentialsSession(backend: backend)
        let running = Task { try await session.run(spec: RunSpecification(stage: .llmLoop, steps: 34)) }
        await backend.waitForRequest()
        let request = await backend.request!
        XCTAssertTrue(request.prompt.contains("Step 30"))
        await backend.finish("I remember the bright sound and feel curious about what returns.")
        let run = try await running.value
        let turn = try XCTUnwrap(run.turns.first)
        XCTAssertEqual(turn.observedStep, 30); XCTAssertEqual(turn.applicationStep, 31)
        XCTAssertEqual(run.frames[29].time, 10)
        XCTAssertEqual(run.frames[30].time, 31.0 / 3.0, accuracy: 1e-12)
        XCTAssertTrue(run.frames[29].input[18..<66].allSatisfy { $0 == 0 })
        XCTAssertEqual(Array(run.frames[30].input[18..<66]), turn.semanticVector)
        XCTAssertEqual(turn.encodedFeatures, TextCodec.encode(turn.reply!))
        XCTAssertEqual(run.frames[30].semanticTurnID, 1)
        try RunVerifier.verify(run)
    }
    func testStopRejectsLateFeedback() async throws {
        let backend = SuspendedBackend()
        let session = EssentialsSession(backend: backend)
        let running = Task { try await session.run(spec: RunSpecification(stage: .llmLoop, steps: 34)) }
        await backend.waitForRequest()
        await session.stop()
        let run = try await running.value
        XCTAssertEqual(run.status, .stopped); XCTAssertEqual(run.frames.count, 30)
        XCTAssertEqual(run.turns.first?.status, .cancelled)
        XCTAssertNil(run.turns.first?.semanticVector)
        await backend.finish("This late reply must never reach a state update.")
        try RunVerifier.verify(run)
    }
    func testStopDuringWaitingStatusDoesNotDispatchProvider() async throws {
        let backend = CountingBackend()
        let session = EssentialsSession(backend: backend)
        let run = try await session.run(spec: RunSpecification(stage: .llmLoop, steps: 34), onStatus: { status in
            if status.hasPrefix("Waiting") { await session.stop() }
        })
        XCTAssertEqual(run.status, .stopped); XCTAssertEqual(run.frames.count, 30)
        let calls = await backend.calls
        XCTAssertEqual(calls, 0)
        try RunVerifier.verify(run)
    }
    func testTaskCancellationRejectsLateFeedback() async throws {
        let backend = SuspendedBackend()
        let session = EssentialsSession(backend: backend)
        let running = Task { try await session.run(spec: RunSpecification(stage: .llmLoop, steps: 34)) }
        await backend.waitForRequest(); running.cancel()
        let run = try await running.value
        XCTAssertEqual(run.status, .stopped)
        XCTAssertNil(run.turns.first?.applicationStep)
        await backend.finish("Late task response.")
        try RunVerifier.verify(run)
    }
    func testTimeoutRetainsFailureAndNeverAppliesReply() async throws {
        let backend = SuspendedBackend()
        let session = EssentialsSession(backend: backend, languageTimeout: .milliseconds(25))
        let running = Task { try await session.run(spec: RunSpecification(stage: .llmLoop, steps: 34)) }
        await backend.waitForRequest()
        let run = try await running.value
        XCTAssertEqual(run.status, .failed); XCTAssertEqual(run.frames.count, 30)
        XCTAssertTrue(run.failure?.contains("timed out") == true)
        XCTAssertEqual(run.turns.first?.status, .failed)
        XCTAssertNil(run.turns.first?.reply)
        await backend.finish("Late timeout response.")
        try RunVerifier.verify(run)
    }
    func testBackendFailureAndEmptyReplyDoNotBecomeFeedback() async throws {
        for backend in [ImmediateBackend(value: ""), ImmediateBackend(value: nil)] {
            let run = try await EssentialsSession(backend: backend).run(spec: RunSpecification(stage: .llmLoop, steps: 34))
            XCTAssertEqual(run.status, .failed); XCTAssertEqual(run.frames.count, 30)
            XCTAssertNil(run.turns.first?.semanticVector)
            try RunVerifier.verify(run)
        }
    }
    func testSeededRepeatabilityAndRoundTrip() async throws {
        let spec = RunSpecification(stage: .regulation, steps: 45, noiseAmplitude: 0.015)
        let a = try await EssentialsSession().run(spec: spec)
        let b = try await EssentialsSession().run(spec: spec)
        let encoder = JSONEncoder(); encoder.outputFormatting = .sortedKeys
        XCTAssertEqual(try encoder.encode(a), try encoder.encode(b))
        let file = FileManager.default.temporaryDirectory.appendingPathComponent("essentials-roundtrip-\(UUID()).json")
        defer { if FileManager.default.fileExists(atPath: file.path) { try? FileManager.default.removeItem(at: file) } }
        try a.write(to: file)
        let read = try RunRecord.read(from: file)
        XCTAssertEqual(try encoder.encode(a), try encoder.encode(read))
        try RunVerifier.verify(read)
    }
    func testEnabledDisabledHaveSameForcingNoiseAndReplies() async throws {
        var spec = RunSpecification(stage: .regulation, steps: 90, noiseAmplitude: 0.01)
        let enabled = try await EssentialsSession().run(spec: spec)
        spec.regulationEnabled = false
        let disabled = try await EssentialsSession().run(spec: spec)
        XCTAssertEqual(enabled.turns.map(\.reply), disabled.turns.map(\.reply))
        for (a, b) in zip(enabled.frames, disabled.frames) {
            XCTAssertEqual(Array(a.input[0..<18]), Array(b.input[0..<18]))
            XCTAssertEqual(a.noise, b.noise)
            XCTAssertNil(b.control)
            XCTAssertEqual(b.retentionUsed, 0.955)
        }
        XCTAssertNotEqual(enabled.frames.map(\.retentionUsed), disabled.frames.map(\.retentionUsed))
        XCTAssertTrue(disabled.frames.contains { ($0.fillPercent ?? 0) < 64 })
        try RunVerifier.verify(enabled); try RunVerifier.verify(disabled)
    }
    func testMalformedAndTamperedRecordsAreRejected() async throws {
        let run = try await EssentialsSession().run(spec: RunSpecification(stage: .llmLoop, steps: 34))
        let data = try JSONEncoder().encode(run)
        for mutation in ["state", "time", "covariance", "link", "prompt", "codec", "version", "dimension"] {
            var json = try XCTUnwrap(JSONSerialization.jsonObject(with: data) as? [String: Any])
            var frames = json["frames"] as! [[String: Any]]
            var turns = json["turns"] as! [[String: Any]]
            switch mutation {
            case "state": var values = frames[0]["state"] as! [Double]; values[0] += 0.01; frames[0]["state"] = values
            case "time": frames[0]["time"] = -1
            case "covariance": var spectral = frames[0]["spectral"] as! [String: Any]; var matrix = spectral["covariance"] as! [Double]; matrix[2] += 0.1; spectral["covariance"] = matrix; frames[0]["spectral"] = spectral
            case "link": turns[0]["applicationStep"] = 32
            case "prompt": turns[0]["prompt"] = "An unrelated observation."
            case "codec": var values = turns[0]["semanticVector"] as! [Double]; values[0] += 0.1; turns[0]["semanticVector"] = values
            case "version": json["recipeVersion"] = "unknown-future-recipe"
            default: frames[0]["state"] = [0.0]
            }
            json["frames"] = frames; json["turns"] = turns
            let malformed = try JSONDecoder().decode(RunRecord.self, from: JSONSerialization.data(withJSONObject: json))
            XCTAssertThrowsError(try RunVerifier.verify(malformed), mutation)
        }
    }
    func testProviderCompletionMetadataAndIncompleteOutput() async throws {
        let cases: [(Bool, String, Int, Bool)] = [(true, "stop", 256, true), (true, "length", 256, false), (false, "stop", 12, false), (true, "stop", 257, false), (true, "stop", -1, false)]
        for (done, reason, tokens, complete) in cases {
            let data = try JSONSerialization.data(withJSONObject: ["done": done, "done_reason": reason, "eval_count": tokens, "model": "actual-provider-model", "message": ["content": "I notice a brighter pattern."]])
            let response = try OllamaLanguageBackend.decodeResponse(data)
            XCTAssertEqual(response.complete, complete)
            XCTAssertEqual(response.providerModel, "actual-provider-model")
            let run = try await EssentialsSession(backend: MetadataBackend(value: response)).run(spec: RunSpecification(stage: .llmLoop, steps: 31))
            XCTAssertEqual(run.status, complete ? .completed : .failed)
            let turn = try XCTUnwrap(run.turns.first)
            XCTAssertEqual(turn.providerModel, "actual-provider-model")
            XCTAssertEqual(turn.stopReason, reason); XCTAssertEqual(turn.tokenCount, tokens)
            XCTAssertEqual(turn.rawReply, "I notice a brighter pattern.")
            XCTAssertEqual(turn.semanticVector != nil, complete)
            try RunVerifier.verify(run)
        }
    }
    func testLocalEndpointMustBeExplicitAndCannotRedirectToRemote() throws {
        for endpoint in [nil, "http://127.0.0.1", "https://127.0.0.1:11435", "http://example.com:11435", "http://localhost:11435/api", "http://user@localhost:11435"] {
            XCTAssertThrowsError(try LanguageConfiguration(backend: .ollama, endpoint: endpoint, model: "separate-test-model").validate())
        }
        XCTAssertNoThrow(try LanguageConfiguration(backend: .ollama, endpoint: "http://127.0.0.1:11435", model: "separate-test-model").validate())
        XCTAssertThrowsError(try LanguageConfiguration(backend: .ollama, endpoint: "http://127.0.0.1:11435", model: " ").validate())
    }
}
private actor SuspendedBackend: LanguageBackend {
    var request: LanguageRequest?
    private var continuation: CheckedContinuation<String, Never>?
    private var waiters: [CheckedContinuation<Void, Never>] = []
    func reply(to request: LanguageRequest) async throws -> String {
        self.request = request
        return await withCheckedContinuation { continuation in
            self.continuation = continuation
            for waiter in waiters { waiter.resume() }; waiters = []
        }
    }
    func waitForRequest() async {
        if request != nil { return }
        await withCheckedContinuation { waiters.append($0) }
    }
    func finish(_ text: String) { continuation?.resume(returning: text); continuation = nil }
}
private struct ImmediateBackend: LanguageBackend {
    let value: String?
    func reply(to request: LanguageRequest) async throws -> String {
        if let value { return value }
        throw EssentialsError.language("Injected provider failure.")
    }
}

private struct MetadataBackend: LanguageBackend {
    let value: LanguageResponse
    func reply(to request: LanguageRequest) async throws -> String { value.text }
    func response(to request: LanguageRequest) async throws -> LanguageResponse { value }
}

private actor CountingBackend: LanguageBackend {
    var calls = 0
    func reply(to request: LanguageRequest) async throws -> String { calls += 1; return "A complete reply." }
}
