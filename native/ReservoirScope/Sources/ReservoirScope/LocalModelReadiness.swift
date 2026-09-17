import Foundation
import SwiftUI
import EssentialsCore

struct LocalModelAvailabilityReceipt: Equatable, Sendable {
    let endpoint: String
    let requestedModel: String
    let matchedModel: String
    let digest: String?
    let checkedAt: Date
}

struct LocalModelCheckAttempt: Equatable, Sendable {
    let endpoint: String
    let requestedModel: String
    let checkedAt: Date
}

enum LocalModelAvailabilityState: Equatable {
    case unchecked
    case checking
    case found(LocalModelAvailabilityReceipt)
    case unavailable(String)
    case cancelled
}

enum LocalModelInventoryError: LocalizedError {
    case invalidResponse, tooLarge, httpStatus(Int), missingModel(String), duplicateModel(String)
    var errorDescription: String? {
        switch self {
        case .invalidResponse: return "The endpoint did not return a valid model inventory."
        case .tooLarge: return "The model inventory exceeded the 1 MiB limit."
        case .httpStatus(let code): return "The inventory request returned HTTP \(code). Redirects are not followed."
        case .missingModel(let model): return "The service responded, but the exact model name “\(model)” was not found."
        case .duplicateModel(let model): return "The inventory contains conflicting entries for “\(model)”."
        }
    }
}

/// One explicit inventory request. It does not load a model, generate, pull, or start a service.
struct LocalModelInventoryProbe: Sendable {
    static let maximumBytes = 1_048_576
    static let timeout: TimeInterval = 5
    let configuration: @Sendable () -> URLSessionConfiguration
    init(configuration: @escaping @Sendable () -> URLSessionConfiguration = { .ephemeral }) {
        self.configuration = configuration
    }
    static func request(endpoint: String, model: String) throws -> URLRequest {
        try LanguageConfiguration(backend: .ollama, endpoint: endpoint, model: model).validate()
        let url = URL(string: endpoint)!.appendingPathComponent("api/tags")
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = timeout
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        return request
    }
    func check(endpoint: String, model: String) async throws -> LocalModelAvailabilityReceipt {
        let request = try Self.request(endpoint: endpoint, model: model)
        try Task.checkCancellation()
        let settings = configuration()
        settings.timeoutIntervalForRequest = Self.timeout
        settings.timeoutIntervalForResource = Self.timeout
        settings.urlCache = nil
        settings.httpCookieStorage = nil
        settings.connectionProxyDictionary = [:]
        let session = URLSession(configuration: settings, delegate: InventoryNoRedirects(), delegateQueue: nil)
        defer { session.invalidateAndCancel() }
        let (bytes, response) = try await session.bytes(for: request)
        guard let http = response as? HTTPURLResponse else { throw LocalModelInventoryError.invalidResponse }
        guard http.statusCode == 200 else { throw LocalModelInventoryError.httpStatus(http.statusCode) }
        if response.expectedContentLength > Int64(Self.maximumBytes) { throw LocalModelInventoryError.tooLarge }
        var data = Data()
        for try await byte in bytes {
            try Task.checkCancellation()
            guard data.count < Self.maximumBytes else { throw LocalModelInventoryError.tooLarge }
            data.append(byte)
        }
        try Task.checkCancellation()
        return try Self.decode(data, endpoint: endpoint, model: model)
    }
    static func decode(_ data: Data, endpoint: String, model: String, checkedAt: Date = Date()) throws -> LocalModelAvailabilityReceipt {
        guard data.count <= maximumBytes else { throw LocalModelInventoryError.tooLarge }
        struct Inventory: Decodable {
            struct Model: Decodable { let name: String; let model: String?; let digest: String? }
            let models: [Model]
        }
        let inventory: Inventory
        do { inventory = try JSONDecoder().decode(Inventory.self, from: data) }
        catch { throw LocalModelInventoryError.invalidResponse }
        let matches = inventory.models.filter { $0.name == model }
        guard let match = matches.first else { throw LocalModelInventoryError.missingModel(model) }
        guard matches.count == 1 else { throw LocalModelInventoryError.duplicateModel(model) }
        guard match.model == nil || match.model == model else { throw LocalModelInventoryError.invalidResponse }
        return LocalModelAvailabilityReceipt(endpoint: endpoint, requestedModel: model,
            matchedModel: match.name, digest: match.digest, checkedAt: checkedAt)
    }
}

private final class InventoryNoRedirects: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
    func urlSession(_ session: URLSession, task: URLSessionTask,
                    willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest,
                    completionHandler: @escaping @Sendable (URLRequest?) -> Void) { completionHandler(nil) }
}

@MainActor final class LocalModelReadiness: ObservableObject {
    @Published private(set) var state: LocalModelAvailabilityState = .unchecked
    @Published private(set) var lastAttempt: LocalModelCheckAttempt?
    private var operation: Task<Void, Never>?
    private var requestID = UUID()
    private let probe: @Sendable (String, String) async throws -> LocalModelAvailabilityReceipt
    init(probe: @escaping @Sendable (String, String) async throws -> LocalModelAvailabilityReceipt = {
        try await LocalModelInventoryProbe().check(endpoint: $0, model: $1)
    }) { self.probe = probe }

    var checking: Bool { if case .checking = state { return true }; return false }
    func check(endpoint: String, model: String) {
        invalidate()
        let endpoint = endpoint.trimmingCharacters(in: .whitespacesAndNewlines)
        let model = model.trimmingCharacters(in: .whitespacesAndNewlines)
        lastAttempt = LocalModelCheckAttempt(endpoint: endpoint, requestedModel: model, checkedAt: Date())
        do { _ = try LocalModelInventoryProbe.request(endpoint: endpoint, model: model) }
        catch { state = .unavailable(error.localizedDescription); return }
        let id = UUID(); requestID = id
        let probe = self.probe
        state = .checking
        operation = Task { [weak self] in
            do {
                let result = try await probe(endpoint, model)
                guard !Task.isCancelled, let self, self.requestID == id else { return }
                self.state = .found(result); self.operation = nil
            } catch {
                guard !Task.isCancelled, let self, self.requestID == id else { return }
                let message: String
                if let urlError = error as? URLError, urlError.code == .timedOut {
                    message = "The local service did not respond within five seconds."
                } else if let urlError = error as? URLError,
                          [.cannotConnectToHost, .cannotFindHost, .networkConnectionLost, .notConnectedToInternet].contains(urlError.code) {
                    message = "The local service could not be reached. Start your installed service separately and check the address."
                } else { message = error.localizedDescription }
                self.state = .unavailable(message); self.operation = nil
            }
        }
    }
    func cancel() {
        requestID = UUID(); operation?.cancel(); operation = nil
        state = .cancelled; lastAttempt = nil
    }
    func invalidate() {
        requestID = UUID(); operation?.cancel(); operation = nil
        state = .unchecked; lastAttempt = nil
    }
}

struct LocalModelReadinessView: View {
    @ObservedObject var model: LocalModelReadiness
    let endpoint: String
    let modelName: String
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Button(model.checking ? "Checking…" : "Check local model") {
                    model.check(endpoint: endpoint, model: modelName)
                }.disabled(model.checking)
                if model.checking { Button("Cancel") { model.cancel() } }
            }.font(.caption)
            switch model.state {
            case .unchecked:
                Text("Availability has not been checked.").foregroundStyle(.secondary)
            case .checking:
                Text("Reading the local model inventory…").foregroundStyle(.secondary)
            case .cancelled:
                Text("Check cancelled.").foregroundStyle(.secondary)
            case .unavailable(let message):
                Text(message).foregroundStyle(.orange).textSelection(.enabled)
                if let attempt = model.lastAttempt {
                    Text("Check for “" + attempt.requestedModel + "” at " + attempt.endpoint).textSelection(.enabled)
                    Text(attempt.checkedAt.formatted(date: .abbreviated, time: .standard)).foregroundStyle(.secondary)
                }
            case .found(let receipt):
                Text("Installed model found: " + receipt.matchedModel).foregroundStyle(.mint)
                Text("Checked " + receipt.checkedAt.formatted(date: .omitted, time: .standard))
                    .foregroundStyle(.secondary)
                if let digest = receipt.digest {
                    DisclosureGroup("Reported model identity") {
                        Text(digest).font(.caption2.monospaced()).textSelection(.enabled)
                    }
                }
            }
            Text("Checks availability only. It does not test generation or start the local service.")
                .foregroundStyle(.secondary)
        }.font(.caption2).fixedSize(horizontal: false, vertical: true)
    }
}
