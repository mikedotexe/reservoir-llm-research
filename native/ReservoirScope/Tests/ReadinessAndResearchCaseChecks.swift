import Foundation
import EssentialsCore

private final class RedirectFlag: @unchecked Sendable {
    private let lock = NSLock()
    private var flag = false
    func set(_ value: Bool) { lock.lock(); flag = value; lock.unlock() }
    var value: Bool { lock.lock(); defer { lock.unlock() }; return flag }
}
private final class InventoryFixture: @unchecked Sendable {
    struct Reply { let status: Int; let data: Data; let headers: [String: String]; let error: URLError?; let hang: Bool }
    private let lock = NSLock()
    private var reply = Reply(status: 200, data: Data(), headers: [:], error: nil, hang: false)
    private var requests: [URLRequest] = []
    func install(status: Int = 200, data: Data, headers: [String: String] = [:], error: URLError? = nil, hang: Bool = false) {
        lock.lock(); defer { lock.unlock() }
        reply = Reply(status: status, data: data, headers: headers, error: error, hang: hang); requests = []
    }
    func capture(_ request: URLRequest) -> Reply {
        lock.lock(); defer { lock.unlock() }; requests.append(request); return reply
    }
    var captured: [URLRequest] { lock.lock(); defer { lock.unlock() }; return requests }
}
private final class InventoryProtocol: URLProtocol, @unchecked Sendable {
    static let fixture = InventoryFixture()
    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        let reply = Self.fixture.capture(request)
        if reply.hang { return }
        if let error = reply.error { client?.urlProtocol(self, didFailWithError: error); return }
        let response = HTTPURLResponse(url: request.url!, statusCode: reply.status, httpVersion: "HTTP/1.1", headerFields: reply.headers)!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: reply.data)
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() {}
}
private actor AvailabilityGate {
    var pending: [String: CheckedContinuation<LocalModelAvailabilityReceipt, Error>] = [:]
    var callCount = 0
    func check(_ endpoint: String, _ model: String) async throws -> LocalModelAvailabilityReceipt {
        callCount += 1
        return try await withCheckedThrowingContinuation { pending[model] = $0 }
    }
    func waiting(_ model: String) -> Bool { pending[model] != nil }
    func release(_ model: String) {
        pending.removeValue(forKey: model)?.resume(returning: LocalModelAvailabilityReceipt(
            endpoint: "http://127.0.0.1:11435", requestedModel: model, matchedModel: model, digest: nil, checkedAt: Date(timeIntervalSince1970: 0)))
    }
}

@main struct ReadinessAndResearchCaseChecks {
    @MainActor static func main() async throws {
        var count = 0
        func check(_ value: Bool, _ text: String) throws {
            guard value else { throw ResearchCaseError("FAIL: " + text) }
            count += 1; print("PASS \(count): " + text)
        }
        func rejects(_ text: String, _ operation: () throws -> Void) throws {
            do { try operation() } catch { try check(true, text); return }
            throw ResearchCaseError("FAIL: did not reject " + text)
        }
        let preferenceName = "research-scope-test-" + UUID().uuidString
        let legacyName = "research-scope-legacy-" + UUID().uuidString
        defer { UserDefaults.standard.removePersistentDomain(forName: preferenceName); UserDefaults.standard.removePersistentDomain(forName: legacyName) }
        let isolated = ScopePreferences.resolve(["RESERVOIR_SCOPE_PREFERENCES": preferenceName, "RESERVOIR_SCOPE_GUIDED_PREFS": legacyName])
        isolated.set("isolated", forKey: "test-marker")
        try check(UserDefaults(suiteName: preferenceName)?.string(forKey: "test-marker") == "isolated", "Shared preference override selects the isolated suite")
        try check(UserDefaults(suiteName: legacyName)?.string(forKey: "test-marker") == nil, "Shared preference override takes precedence over legacy guided override")
        let legacy = ScopePreferences.resolve(["RESERVOIR_SCOPE_GUIDED_PREFS": legacyName])
        legacy.set("compatible", forKey: "test-marker")
        try check(UserDefaults(suiteName: legacyName)?.string(forKey: "test-marker") == "compatible", "Legacy guided preference override remains compatible")
        let endpoint = "http://127.0.0.1:11435"
        let valid = Data(#"{"models":[{"name":"phi3:mini","model":"phi3:mini","digest":"fixed-digest"}]}"#.utf8)
        let request = try LocalModelInventoryProbe.request(endpoint: endpoint, model: "phi3:mini")
        try check(request.httpMethod == "GET" && request.url?.path == "/api/tags" && request.httpBody == nil,
                  "Availability uses one inventory GET, without generation payload")
        try check(request.timeoutInterval == 5 && LocalModelInventoryProbe.maximumBytes == 1_048_576,
                  "Inventory timeout is five seconds with a one-MiB bound")
        for invalid in ["https://127.0.0.1:11435", "http://example.org:11435", "http://127.0.0.1", "http://localhost:11435/api", "http://user@localhost:11435"] {
            try rejects("Invalid endpoint rejected before transport: " + invalid) { _ = try LocalModelInventoryProbe.request(endpoint: invalid, model: "phi3:mini") }
        }
        try rejects("Empty model rejected before transport") { _ = try LocalModelInventoryProbe.request(endpoint: endpoint, model: " ") }
        let receipt = try LocalModelInventoryProbe.decode(valid, endpoint: endpoint, model: "phi3:mini")
        try check(receipt.matchedModel == "phi3:mini" && receipt.digest == "fixed-digest", "Exact model identity is returned from inventory")
        try rejects("A different tag is not silently substituted") { _ = try LocalModelInventoryProbe.decode(valid, endpoint: endpoint, model: "phi3") }
        try rejects("An alias model field cannot qualify a different name") {
            _ = try LocalModelInventoryProbe.decode(Data(#"{"models":[{"name":"another","model":"phi3:mini"}]}"#.utf8), endpoint: endpoint, model: "phi3:mini")
        }
        try rejects("Conflicting optional model identity is rejected") {
            _ = try LocalModelInventoryProbe.decode(Data(#"{"models":[{"name":"phi3:mini","model":"another"}]}"#.utf8), endpoint: endpoint, model: "phi3:mini")
        }
        try rejects("Malformed inventory rejected") { _ = try LocalModelInventoryProbe.decode(Data("{}".utf8), endpoint: endpoint, model: "phi3:mini") }
        try rejects("Conflicting exact matches rejected") {
            _ = try LocalModelInventoryProbe.decode(Data(#"{"models":[{"name":"x"},{"name":"x"}]}"#.utf8), endpoint: endpoint, model: "x")
        }
        let probe = LocalModelInventoryProbe {
            let configuration = URLSessionConfiguration.ephemeral
            configuration.protocolClasses = [InventoryProtocol.self]
            return configuration
        }
        InventoryProtocol.fixture.install(data: valid)
        let transportReceipt = try await probe.check(endpoint: endpoint, model: "phi3:mini")
        try check(transportReceipt.matchedModel == "phi3:mini" && InventoryProtocol.fixture.captured.count == 1,
                  "Production inventory transport performs exactly one mocked request")
        for status in [302, 503] {
            InventoryProtocol.fixture.install(status: status, data: valid, headers: ["Location": "http://example.org/forbidden"])
            var rejected = false
            do { _ = try await probe.check(endpoint: endpoint, model: "phi3:mini") } catch { rejected = true }
            try check(rejected && InventoryProtocol.fixture.captured.count == 1,
                      "HTTP \(status) rejected without another inventory request")
        }
        let delegate = InventoryNoRedirects()
        let blockedRedirect = RedirectFlag()
        let redirectSession = URLSession(configuration: .ephemeral)
        let redirectTask = redirectSession.dataTask(with: request)
        delegate.urlSession(redirectSession, task: redirectTask,
                            willPerformHTTPRedirection: HTTPURLResponse(url: request.url!, statusCode: 302, httpVersion: nil, headerFields: nil)!,
                            newRequest: URLRequest(url: URL(string: "http://example.org/forbidden")!)) { redirected in
            // The delegate invokes this synchronously; no request is resumed.
            blockedRedirect.set(redirected == nil)
        }
        redirectSession.invalidateAndCancel()
        try check(blockedRedirect.value, "Redirect delegate explicitly declines a redirect")
        InventoryProtocol.fixture.install(data: valid, headers: ["Content-Length": "1048577"])
        var announcedOversize = false
        do { _ = try await probe.check(endpoint: endpoint, model: "phi3:mini") } catch { announcedOversize = true }
        try check(announcedOversize, "Announced oversized inventory rejected")
        InventoryProtocol.fixture.install(data: Data(repeating: 32, count: 1_048_577))
        var streamedOversize = false
        do { _ = try await probe.check(endpoint: endpoint, model: "phi3:mini") } catch { streamedOversize = true }
        try check(streamedOversize, "Streamed oversized inventory rejected even without a size header")

        let gate = AvailabilityGate()
        let model = LocalModelReadiness { try await gate.check($0, $1) }
        let initialCalls = await gate.callCount
        try check(model.state == .unchecked && initialCalls == 0, "Creating readiness model performs no request")
        model.check(endpoint: "http://example.org:11435", model: "bad")
        try check(await gate.callCount == 0, "Invalid configuration does not invoke the injected probe")
        try check(model.lastAttempt?.endpoint == "http://example.org:11435" && model.lastAttempt?.requestedModel == "bad", "Unavailable check retains attempted identity and time")
        model.check(endpoint: endpoint, model: "cancelled")
        try await waitUntil { await gate.waiting("cancelled") }
        model.cancel(); await gate.release("cancelled"); await settle()
        try check(model.state == .cancelled && model.lastAttempt == nil, "Cancellation rejects a late successful response and clears checked identity")
        model.check(endpoint: endpoint, model: "old-setting")
        try await waitUntil { await gate.waiting("old-setting") }
        model.invalidate(); await gate.release("old-setting"); await settle()
        try check(model.state == .unchecked && model.lastAttempt == nil, "Editing settings invalidates and rejects the old result and identity")
        model.check(endpoint: endpoint, model: "older")
        try await waitUntil { await gate.waiting("older") }
        model.check(endpoint: endpoint, model: "newer")
        try await waitUntil { await gate.waiting("newer") }
        await gate.release("newer")
        try await waitUntil { if case .found = model.state { return true }; return false }
        await gate.release("older"); await settle()
        if case .found(let value) = model.state { try check(value.requestedModel == "newer", "Latest explicit check owns the displayed receipt") }
        else { throw ResearchCaseError("FAIL: expected newest receipt") }
        let timeoutModel = LocalModelReadiness { _, _ in throw URLError(.timedOut) }
        timeoutModel.check(endpoint: endpoint, model: "phi3:mini")
        try await waitUntil { if case .unavailable = timeoutModel.state { return true }; return false }
        if case .unavailable(let message) = timeoutModel.state { try check(message.contains("five seconds"), "Timeout has a specific availability explanation") }
        let absentModel = LocalModelReadiness { _, _ in throw URLError(.cannotConnectToHost) }
        absentModel.check(endpoint: endpoint, model: "phi3:mini")
        try await waitUntil { if case .unavailable = absentModel.state { return true }; return false }
        if case .unavailable(let message) = absentModel.state { try check(message.contains("Start your installed service separately"), "Connection refusal explains separate service startup") }

        let content = "Supplied code says: pub struct Kernel {\nA remembered claim remains unresolved.\n"
        let material: [String: Any] = ["id":"source","title":"Frozen source","kind":"supplied source","content":content,
            "sha256":ResearchCaseCatalog.digest(content),"sourcePath":"/unavailable/being/source.rs",
            "sourceSHA256":String(repeating:"a",count:64)]
        let claim: [String: Any] = ["id":"definition","classification":"supported","materialID":"source",
            "quote":"pub struct Kernel {","evidenceIDs":["source"],"explanation":"The supplied line contains this definition."]
        let item: [String: Any] = ["id":"test-case","title":"Reviewed fixture","question":"What was supplied?","summary":"A bounded reading.",
            "author":"Minime","sourceOwner":"Astrid","interval":"Frozen test interval","limits":["No runtime claim."],
            "materials":[material],"claims":[claim],"sequence":[
                ["title":"Read source","detail":"Recorded page supplied.","materialIDs":["source"],"status":"observed"],
                ["title":"Later outcome","detail":"Not checked.","materialIDs":[],"status":"notObserved"]]]
        func data(_ item: [String: Any], format: String = ResearchCaseCatalog.currentFormat) throws -> Data {
            try JSONSerialization.data(withJSONObject: ["format":format,"cases":[item]], options: [.sortedKeys])
        }
        let catalog = try ResearchCaseCatalog.decode(data(item))
        try check(catalog.cases.count == 1 && catalog.cases[0].author != catalog.cases[0].sourceOwner,
                  "Case preserves author separately from source ownership")
        let roundtrip = try ResearchCaseCatalog.decode(catalog.encoded())
        try check(roundtrip.cases[0].materials[0].content == content, "Selected-case export preserves exact embedded text")
        try check(roundtrip.cases[0].sequence[1].status == .notObserved, "Unobserved outcomes remain explicit")
        var changed = item; var alteredMaterial = material
        alteredMaterial["content"] = content + "Altered"; changed["materials"] = [alteredMaterial]
        try rejects("Altered embedded text rejected") { _ = try ResearchCaseCatalog.decode(data(changed)) }
        changed = item; var alteredClaim = claim; alteredClaim["quote"] = "not supplied"; changed["claims"] = [alteredClaim]
        try rejects("Absent exact quotation rejected") { _ = try ResearchCaseCatalog.decode(data(changed)) }
        changed = item; alteredClaim = claim; alteredClaim["evidenceIDs"] = ["missing"]; changed["claims"] = [alteredClaim]
        try rejects("Absent supporting evidence reference rejected") { _ = try ResearchCaseCatalog.decode(data(changed)) }
        changed = item; changed["materials"] = [material, material]
        try rejects("Duplicate material IDs rejected") { _ = try ResearchCaseCatalog.decode(data(changed)) }
        changed = item; changed["limits"] = []
        try rejects("Missing case limits rejected") { _ = try ResearchCaseCatalog.decode(data(changed)) }
        changed = item; alteredClaim = claim; alteredClaim["classification"] = "improved"; changed["claims"] = [alteredClaim]
        try rejects("Unknown interpretation labels rejected") { _ = try ResearchCaseCatalog.decode(data(changed)) }
        try rejects("Different case format rejected") { _ = try ResearchCaseCatalog.decode(data(item, format:"research-cases-v2")) }
        try rejects("Case byte bound enforced before decoding") { _ = try ResearchCaseCatalog.decode(Data(repeating:32,count:ResearchCaseCatalog.maximumBytes+1)) }
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("research-case-checks-" + UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let exported = directory.appendingPathComponent("case.json")
        try catalog.encoded().write(to: exported)
        let reopened = try ResearchCaseCatalog.readIfSupported(from: exported)
        try check(reopened?.cases[0].materials[0].sourcePath == "/unavailable/being/source.rs",
                  "Export reopens without accessing historical source paths")
        let numerical = directory.appendingPathComponent("existing-experiment.json")
        try Data(#"{"format":"essentials-actions-v3"}"#.utf8).write(to: numerical)
        try check(try ResearchCaseCatalog.readIfSupported(from: numerical) == nil,
                  "Existing numerical format remains routed to ExperimentStore")
        if CommandLine.arguments.count > 1 {
            let delivered = try ResearchCaseCatalog.read(from: URL(fileURLWithPath: CommandLine.arguments[1]))
            try check(delivered.cases.count == 2, "Both curated release cases verify")
            for item in delivered.cases {
                let exportedCase = try ResearchCaseCatalog(cases:[item]).encoded()
                let selected = try ResearchCaseCatalog.decode(exportedCase)
                try check(selected.cases.count == 1 && selected.cases[0].id == item.id,
                          "Curated case exports independently: " + item.id)
            }
        }
        print("All \(count) readiness and reviewed-case checks passed. Mocked inventory only; no model calls.")
    }
    @MainActor static func waitUntil(_ condition: () async -> Bool) async throws {
        for _ in 0..<1000 {
            if await condition() { return }
            try await Task.sleep(nanoseconds: 1_000_000)
        }
        throw ResearchCaseError("Timed out waiting for controlled test operation.")
    }
    static func settle() async { for _ in 0..<10 { await Task.yield() }; try? await Task.sleep(nanoseconds: 5_000_000) }
}
