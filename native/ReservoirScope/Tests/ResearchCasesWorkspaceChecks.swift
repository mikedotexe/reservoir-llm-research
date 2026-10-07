import Foundation

private actor CaseLoadGate {
    private var pending: [String: CheckedContinuation<ResearchCaseCatalog, Error>] = [:]
    private var completed: Set<String> = []

    func load(_ url: URL) async throws -> ResearchCaseCatalog {
        let name = url.lastPathComponent
        let result: ResearchCaseCatalog = try await withCheckedThrowingContinuation { pending[name] = $0 }
        completed.insert(name)
        return result
    }
    func waiting(_ name: String) -> Bool { pending[name] != nil }
    func finished(_ name: String) -> Bool { completed.contains(name) }
    func succeed(_ name: String, _ catalog: ResearchCaseCatalog) {
        pending.removeValue(forKey: name)?.resume(returning: catalog)
    }
    func fail(_ name: String) {
        pending.removeValue(forKey: name)?.resume(throwing: ResearchCaseError("Delayed fixture rejected"))
    }
}

@main
enum ResearchCasesWorkspaceChecks {
    @MainActor static func main() async throws {
        guard CommandLine.arguments.count == 2 else { fatalError("Pass the bundled reviewed-case catalog") }
        var count = 0
        func check(_ condition: Bool, _ message: String) throws {
            guard condition else { throw ResearchCaseError("FAIL: " + message) }
            count += 1
        }
        func waitUntil(_ predicate: () async -> Bool) async throws {
            for _ in 0..<200 {
                if await predicate() { return }
                try await Task.sleep(for: .milliseconds(10))
            }
            throw ResearchCaseError("Timed out waiting for a controlled case load")
        }
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("research-cases-workspace-" + UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let bundled = directory.appendingPathComponent("bundled.json")
        try Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])).write(to: bundled)
        let model = ResearchCasesViewModel(bundledURL: bundled)
        try check(model.bundledCases.isEmpty && model.selectedCase == nil, "Construction does not read or select a case")
        model.loadBundledIfNeeded()
        try await waitUntil { !model.loadingBundled }
        try check(model.bundledCases.count == 2 && model.bundledError == nil, "Both unchanged bundled cases verify")
        try check(model.selection == nil, "The question list does not silently choose a case")
        let firstID = model.bundledCases[0].id
        let secondID = model.bundledCases[1].id
        model.select(.bundled(secondID))
        try check(model.selectedCase?.id == secondID, "An explicit question selects its exact case")
        try FileManager.default.removeItem(at: bundled)
        model.loadBundledIfNeeded()
        try check(model.bundledCases.count == 2 && model.selection == .bundled(secondID) && model.bundledError == nil,
                  "Returning uses retained cases and selection after their original file disappears")
        model.select(.bundled("missing"))
        try check(model.selection == .bundled(secondID), "An unavailable selection does not replace the current case")

        func fixture(_ id: String, question: String) -> ReviewedResearchCase {
            let text = "Synthetic supplied evidence only."
            return ReviewedResearchCase(id: id, title: "Synthetic open-case fixture", question: question,
                summary: "A fixture for window navigation, not a research finding.", author: "Synthetic", sourceOwner: "Synthetic",
                interval: "Synthetic interval", limits: ["No Being observation."],
                materials: [.init(id: "evidence", title: "Synthetic evidence", kind: "fixture", content: text,
                    sha256: ResearchCaseCatalog.digest(text), sourcePath: "/unavailable/original/source.txt", sourceSHA256: nil, note: nil)],
                claims: [.init(id: "claim", classification: .unresolved, materialID: "evidence", quote: text,
                    evidenceIDs: ["evidence"], explanation: "Fixture only.")],
                sequence: [.init(title: "Fixture supplied", detail: "Embedded synthetic material.", materialIDs: ["evidence"], status: .observed, timestamp: nil)])
        }
        let opened = directory.appendingPathComponent("opened.json")
        let collision = fixture(firstID, question: "Which catalog owns this selected question?")
        try ResearchCaseCatalog(cases: [collision]).encoded().write(to: opened)
        model.open(opened)
        try await waitUntil { !model.opening }
        try check(model.openedCases.count == 1 && model.openedFilename == opened.lastPathComponent && model.openError == nil,
                  "Opening retains a verified catalog and filename without saving an experiment")
        try check(model.selection == .opened(firstID) && model.selectedCase?.question == collision.question,
                  "Opened IDs cannot accidentally select a bundled case with the same ID")
        try FileManager.default.removeItem(at: opened)
        model.select(.bundled(firstID)); model.select(.opened(firstID)); model.loadBundledIfNeeded()
        try check(model.selectedCase?.question == collision.question && model.openedCases.count == 1,
                  "Switching and returning does not reopen the removed case file or historical source path")
        model.open(nil)
        try check(model.selection == .opened(firstID) && model.openedFilename == "opened.json" && model.openError == nil,
                  "Cancelling leaves the current opened case unchanged")
        let invalid = directory.appendingPathComponent("invalid.json")
        try Data("{}".utf8).write(to: invalid)
        model.open(invalid)
        try await waitUntil { !model.opening }
        try check(model.openError != nil && model.selectedCase?.question == collision.question && model.openedFilename == "opened.json",
                  "Invalid replacement reports a failure while preserving the previous catalog and selection")
        let previousError = model.openError
        model.open(nil)
        try check(model.openError == previousError && model.selectedCase?.question == collision.question,
                  "Cancelling after rejection also preserves the failure and retained evidence")
        var tampered = try JSONSerialization.jsonObject(with: ResearchCaseCatalog(cases: [collision]).encoded()) as! [String: Any]
        var cases = tampered["cases"] as! [[String: Any]]
        var materials = cases[0]["materials"] as! [[String: Any]]
        materials[0]["content"] = "Changed without resealing"
        cases[0]["materials"] = materials; tampered["cases"] = cases
        try JSONSerialization.data(withJSONObject: tampered).write(to: invalid)
        model.open(invalid)
        try await waitUntil { !model.opening }
        try check(model.openError?.contains("hash does not match") == true && model.selectedCase?.question == collision.question,
                  "Opening applies the existing embedded-evidence verification before replacement")
        let replacement = directory.appendingPathComponent("replacement.json")
        let newCase = fixture("replacement", question: "Did a successful replacement reset selection?")
        try ResearchCaseCatalog(cases: [newCase]).encoded().write(to: replacement)
        model.open(replacement)
        try await waitUntil { !model.opening }
        try check(model.openedCases.count == 1 && model.selection == .opened("replacement") && model.openError == nil,
                  "A verified replacement alone replaces the opened catalog and selects its first question")
        try check(model.bundledCases.count == 2 && model.openedFilename == "replacement.json",
                  "Replacing opened cases leaves the included catalog intact")
        let missing = ResearchCasesViewModel(bundledURL: nil)
        missing.loadBundledIfNeeded()
        try check(missing.bundledError != nil && missing.bundledCases.isEmpty, "Missing bundled data has a scoped error")
        missing.open(replacement)
        try await waitUntil { !missing.opening }
        try check(missing.selectedCase?.id == "replacement" && missing.openError == nil && missing.bundledError != nil,
                  "An explicit case can still open when the bundled catalog is unavailable")
        let broken = ResearchCasesViewModel(bundledURL: invalid)
        broken.loadBundledIfNeeded(); broken.open(replacement)
        try await waitUntil { !broken.isLoading }
        try check(broken.bundledError != nil && broken.selectedCase?.id == "replacement",
                  "A malformed bundled catalog does not prevent a verified explicit opening")

        let gate = CaseLoadGate()
        let delayed = ResearchCasesViewModel(bundledURL: directory.appendingPathComponent("included.json"),
            loader: { try await gate.load($0) })
        delayed.loadBundledIfNeeded()
        try await waitUntil { await gate.waiting("included.json") }
        try check(delayed.loadingBundled && delayed.bundledCases.isEmpty,
                  "A delayed catalog read yields to the main actor with visible loading state")
        await gate.succeed("included.json", ResearchCaseCatalog(cases: model.bundledCases))
        try await waitUntil { !delayed.loadingBundled }
        delayed.select(.bundled(secondID))
        delayed.open(directory.appendingPathComponent("older.json"))
        try await waitUntil { await gate.waiting("older.json") }
        try check(delayed.opening && delayed.selectedCase?.id == secondID,
                  "Existing evidence remains usable while a replacement verifies")
        delayed.select(.bundled(firstID))
        try check(delayed.selectedCase?.id == firstID && delayed.opening,
                  "Reading another retained question does not wait for the worker")
        delayed.open(directory.appendingPathComponent("newer.json"))
        try await waitUntil { await gate.waiting("newer.json") }
        await gate.succeed("newer.json", ResearchCaseCatalog(cases: [newCase]))
        try await waitUntil { !delayed.opening }
        try check(delayed.selection == .opened("replacement") && delayed.openedFilename == "newer.json",
                  "The newest requested catalog owns the selected case")
        await gate.succeed("older.json", ResearchCaseCatalog(cases: [collision]))
        try await waitUntil { await gate.finished("older.json") }
        try await Task.sleep(for: .milliseconds(30))
        try check(delayed.selectedCase?.id == "replacement" && delayed.openedFilename == "newer.json" && delayed.openError == nil,
                  "A late superseded completion cannot replace the newer catalog or error state")
        delayed.open(directory.appendingPathComponent("cancelled.json"))
        try await waitUntil { await gate.waiting("cancelled.json") }
        delayed.cancelOpening()
        try check(!delayed.opening && delayed.selectedCase?.id == "replacement", "Cancelling a pending load preserves the selected evidence")
        await gate.succeed("cancelled.json", ResearchCaseCatalog(cases: [collision]))
        try await waitUntil { await gate.finished("cancelled.json") }
        try await Task.sleep(for: .milliseconds(30))
        try check(delayed.selectedCase?.id == "replacement" && delayed.openedFilename == "newer.json" && delayed.openError == nil,
                  "A cancelled worker's late success does not install its catalog")
        delayed.open(directory.appendingPathComponent("failed.json"))
        try await waitUntil { await gate.waiting("failed.json") }
        await gate.fail("failed.json")
        try await waitUntil { !delayed.opening }
        try check(delayed.openError?.contains("Delayed fixture rejected") == true && delayed.selectedCase?.id == "replacement",
                  "A delayed failure reports its error while preserving the previous valid case")
        print("All \(count) research-case workspace checks passed. Retained bytes only; no UI, model, network or original-source reads.")
    }
}
