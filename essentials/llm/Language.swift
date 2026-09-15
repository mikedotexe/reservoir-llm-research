import Foundation

public enum LanguageKind: String, Codable, Sendable { case scripted, ollama }

public struct LanguageConfiguration: Codable, Sendable, Equatable {
    public var backend: LanguageKind
    public var endpoint: String?
    public var model: String?
    public static let scripted = LanguageConfiguration()
    public init(backend: LanguageKind = .scripted, endpoint: String? = nil, model: String? = nil) {
        self.backend = backend; self.endpoint = endpoint; self.model = model
    }
    public func validate() throws {
        if backend == .ollama {
            guard let endpoint, let url = URL(string: endpoint), url.scheme == "http",
                  ["localhost", "127.0.0.1", "[::1]", "::1"].contains(url.host ?? ""),
                  url.port != nil, url.user == nil, url.password == nil,
                  url.query == nil, url.fragment == nil,
                  url.path.isEmpty || url.path == "/",
                  let model, !model.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
                  model.utf8.count <= 256 else {
                throw EssentialsError.invalid("Ollama requires an explicit separate http loopback endpoint with a port and a model name.")
            }
        }
    }
}

public struct LanguageRequest: Sendable {
    public let turnID: Int
    public let prompt: String
    public init(turnID: Int, prompt: String) { self.turnID = turnID; self.prompt = prompt }
}
public struct LanguageResponse: Sendable {
    public let text: String
    public let providerModel: String?
    public let stopReason: String?
    public let tokenCount: Int?
    public let complete: Bool
    public init(text: String, providerModel: String? = nil, stopReason: String? = nil,
                tokenCount: Int? = nil, complete: Bool = true) {
        self.text = text; self.providerModel = providerModel; self.stopReason = stopReason
        self.tokenCount = tokenCount; self.complete = complete
    }
}
public protocol LanguageBackend: Sendable {
    func reply(to request: LanguageRequest) async throws -> String
    func response(to request: LanguageRequest) async throws -> LanguageResponse
}
public extension LanguageBackend {
    func response(to request: LanguageRequest) async throws -> LanguageResponse {
        LanguageResponse(text: try await reply(to: request))
    }
}
public struct ScriptedLanguageBackend: LanguageBackend {
    public static let replies = [
        "I notice a steady pattern and a quiet change. I remember the earlier signal and will watch what persists.",
        "The broad field carries several shapes together. I wonder whether another rhythm will change the balance.",
        "I feel curious about this new pattern. Let me hold the bright signal briefly and listen for what returns.",
        "A narrow pattern remains while other movements fade. I can compare this moment with the last and try a different thought."
    ]
    public init() {}
    public func reply(to request: LanguageRequest) async throws -> String {
        try Task.checkCancellation()
        return Self.replies[(request.turnID - 1) % Self.replies.count]
    }
    public func response(to request: LanguageRequest) async throws -> LanguageResponse {
        LanguageResponse(text: try await reply(to: request), providerModel: "essentials-script-v1", stopReason: "scripted")
    }
}

/// A fresh session per request; no discovery, model listing, pulls, or service startup.
public struct OllamaLanguageBackend: LanguageBackend {
    public let configuration: LanguageConfiguration
    public init(configuration: LanguageConfiguration) throws {
        try configuration.validate()
        guard configuration.backend == .ollama else { throw EssentialsError.invalid("Expected an Ollama configuration.") }
        self.configuration = configuration
    }
    public func reply(to request: LanguageRequest) async throws -> String {
        let result = try await response(to: request)
        guard result.complete else { throw EssentialsError.language("Ollama reply was incomplete.") }
        return result.text
    }
    public func response(to request: LanguageRequest) async throws -> LanguageResponse {
        try configuration.validate()
        let endpoint = URL(string: configuration.endpoint!)!.appendingPathComponent("api/chat")
        var http = URLRequest(url: endpoint)
        http.httpMethod = "POST"; http.timeoutInterval = 60
        http.setValue("application/json", forHTTPHeaderField: "Content-Type")
        http.httpBody = try JSONSerialization.data(withJSONObject: [
            "model": configuration.model!, "stream": false,
            "messages": [["role": "user", "content": request.prompt]],
            "options": ["num_predict": 256, "temperature": 0]
        ])
        let settings = URLSessionConfiguration.ephemeral
        settings.timeoutIntervalForRequest = 60; settings.timeoutIntervalForResource = 60
        let session = URLSession(configuration: settings, delegate: NoRedirects(), delegateQueue: nil)
        defer { session.invalidateAndCancel() }
        let (bytes, response) = try await session.bytes(for: http)
        guard let status = response as? HTTPURLResponse, status.statusCode == 200 else {
            throw EssentialsError.language("Ollama returned a non-success response.")
        }
        var data = Data()
        for try await byte in bytes {
            guard data.count < 1_048_576 else { throw EssentialsError.language("Ollama response exceeded 1 MB.") }
            data.append(byte)
        }
        try Task.checkCancellation()
        return try Self.decodeResponse(data)
    }
    static func decodeResponse(_ data: Data) throws -> LanguageResponse {
        struct Response: Decodable {
            struct Message: Decodable { let content: String }
            let done: Bool; let message: Message; let eval_count: Int?
            let model: String?; let done_reason: String?
        }
        let decoded = try JSONDecoder().decode(Response.self, from: data)
        let isComplete = decoded.done && decoded.done_reason != "length"
            && (decoded.eval_count.map({ $0 >= 0 && $0 <= 256 }) ?? true)
        return LanguageResponse(text: decoded.message.content, providerModel: decoded.model,
                                stopReason: decoded.done_reason, tokenCount: decoded.eval_count, complete: isComplete)
    }
}
private final class NoRedirects: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
    func urlSession(_ session: URLSession, task: URLSessionTask,
                    willPerformHTTPRedirection response: HTTPURLResponse,
                    newRequest request: URLRequest,
                    completionHandler: @escaping @Sendable (URLRequest?) -> Void) { completionHandler(nil) }
}

/// Completion arbitration does not wait for a backend that ignores cancellation.
/// A late response is discarded after timeout/stop; it can never become feedback.
final class ReplyGate: @unchecked Sendable {
    private let lock = NSLock()
    private var continuation: CheckedContinuation<LanguageResponse, Error>?
    private var result: Result<LanguageResponse, Error>?
    private var tasks: [Task<Void, Never>] = []
    func install(_ continuation: CheckedContinuation<LanguageResponse, Error>) {
        lock.lock()
        if let result { lock.unlock(); continuation.resume(with: result) }
        else { self.continuation = continuation; lock.unlock() }
    }
    func add(_ task: Task<Void, Never>) {
        lock.lock(); let done = result != nil
        if !done { tasks.append(task) }; lock.unlock()
        if done { task.cancel() }
    }
    func finish(_ result: Result<LanguageResponse, Error>) {
        lock.lock()
        guard self.result == nil else { lock.unlock(); return }
        self.result = result
        let continuation = self.continuation; self.continuation = nil
        let pending = tasks; tasks = []; lock.unlock()
        for task in pending { task.cancel() }
        continuation?.resume(with: result)
    }
}

func boundedReply(backend: any LanguageBackend, request: LanguageRequest,
                  timeout: Duration, gate: ReplyGate) async throws -> LanguageResponse {
    try await withTaskCancellationHandler {
        try await withCheckedThrowingContinuation { continuation in
            gate.install(continuation)
            gate.add(Task {
                do { gate.finish(.success(try await backend.response(to: request))) }
                catch { gate.finish(.failure(error)) }
            })
            gate.add(Task {
                do { try await Task.sleep(for: timeout); gate.finish(.failure(EssentialsError.language("Language request timed out."))) }
                catch { /* The response or cancellation won. */ }
            })
        }
    } onCancel: { gate.finish(.failure(CancellationError())) }
}
