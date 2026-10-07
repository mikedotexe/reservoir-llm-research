import Combine
import Foundation

/// One window's verified cases. Opening a file retains its embedded evidence in
/// memory; leaving the workspace never rereads sources or creates a saved copy.
@MainActor final class ResearchCasesViewModel: ObservableObject {
    typealias Loader = @Sendable (URL) async throws -> ResearchCaseCatalog
    enum Selection: Hashable {
        case bundled(String)
        case opened(String)
    }

    @Published private(set) var bundledCases: [ReviewedResearchCase] = []
    @Published private(set) var openedCases: [ReviewedResearchCase] = []
    @Published private(set) var selection: Selection?
    @Published private(set) var openedFilename = ""
    @Published private(set) var bundledError: String?
    @Published private(set) var openError: String?
    @Published private(set) var loadingBundled = false
    @Published private(set) var opening = false

    private let bundledURL: URL?
    private let loader: Loader
    private var attemptedBundledLoad = false
    private var openGeneration = UUID()
    private var openWorker: Task<ResearchCaseCatalog, Error>?
    private var openTask: Task<Void, Never>?

    convenience init() {
        self.init(bundledURL: Bundle.module.url(forResource: "research-cases-v1", withExtension: "json")
            ?? Bundle.module.url(forResource: "research-cases-v1", withExtension: "json", subdirectory: "Resources"))
    }

    init(bundledURL: URL?, loader: @escaping Loader = { try ResearchCaseCatalog.read(from: $0) }) {
        self.bundledURL = bundledURL
        self.loader = loader
    }

    var isLoading: Bool { loadingBundled || opening }

    var selectedCase: ReviewedResearchCase? {
        guard let selection else { return nil }
        return item(for: selection)
    }

    func loadBundledIfNeeded() {
        guard !attemptedBundledLoad else { return }
        attemptedBundledLoad = true
        guard let bundledURL else {
            bundledError = "The reviewed case catalog is missing from this package. You can still open an exported case."
            return
        }
        loadingBundled = true
        let loader = loader
        let worker = Task.detached(priority: .utility) { try await loader(bundledURL) }
        Task { [weak self] in
            let result = await worker.result
            guard let self else { return }
            self.loadingBundled = false
            do {
                self.bundledCases = try result.get().cases
            } catch {
                self.bundledError = "Included cases could not be verified: " + error.localizedDescription
            }
        }
    }

    func select(_ choice: Selection) {
        guard item(for: choice) != nil else { return }
        selection = choice
    }

    func open(_ url: URL?) {
        guard let url else { return }
        cancelOpening()
        let generation = openGeneration, loader = loader
        opening = true
        openError = nil
        let worker = Task.detached(priority: .userInitiated) {
            let catalog = try await loader(url)
            try Task.checkCancellation()
            return catalog
        }
        openWorker = worker
        openTask = Task { [weak self] in
            let result = await worker.result
            guard let self, self.openGeneration == generation else { return }
            self.opening = false
            self.openWorker = nil
            self.openTask = nil
            do {
                let catalog = try result.get()
                guard let first = catalog.cases.first else { throw ResearchCaseError("The case catalog is empty.") }
                self.openedCases = catalog.cases
                self.openedFilename = url.lastPathComponent
                self.selection = .opened(first.id)
            } catch {
                self.openError = "The file could not be opened. Your previous cases remain available. " + error.localizedDescription
            }
        }
    }

    func cancelOpening() {
        openGeneration = UUID()
        openWorker?.cancel()
        openTask?.cancel()
        openWorker = nil
        openTask = nil
        opening = false
    }

    private func item(for choice: Selection) -> ReviewedResearchCase? {
        switch choice {
        case .bundled(let id): return bundledCases.first { $0.id == id }
        case .opened(let id): return openedCases.first { $0.id == id }
        }
    }
}
