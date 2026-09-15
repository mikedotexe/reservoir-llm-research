import SwiftUI
import UniformTypeIdentifiers
import EssentialsCore

/// One paced opportunity advances the shared core session. Rendering can replay
/// its immutable records while provider work and journal writes remain off-main.
@MainActor
final class ActionComparisonViewModel: ObservableObject {
    @Published var stage: ActionStage = .reservoirReturn
    @Published var mode: ActionComparisonMode = .fixedReplay
    @Published private(set) var record: ActionComparisonRecord?
    @Published var row = 0
    @Published var selectedNode = 0
    @Published var selectedActionID: Int?
    @Published private(set) var running = false
    @Published private(set) var working = false
    @Published private(set) var replaying = false
    @Published private(set) var loading = false
    @Published private(set) var speed = 3.0
    @Published var seedText = "20260909"
    @Published var localModel = false
    @Published var endpoint = ""
    @Published var modelName = ""
    @Published var question = "What changes when saved journal text is returned through the semantic-input gate?"
    @Published var expectedDifference = "With identical text and codec vectors, only the reservoir-return arm should receive semantic input."
    @Published var alternatives = "External forcing, noise, model settings and display scale must remain matched; independently generated writing can also change the trajectory."
    @Published var stoppingPoint = "300 steps, nine scheduled opportunities; stop and retain evidence on failure."
    @Published var status = "Choose a version, then run it or compare with the preceding version."
    @Published var error: String?
    @Published var source = ""
    @Published private(set) var saveIssue: String?

    private var session: ActionComparisonSession?
    private var operation: Task<Void, Never>?
    private var loadWorker: Task<ActionComparisonRecord, Error>?
    private var loadTask: Task<Void, Never>?
    private var generation = UUID()
    private var contextID = UUID()
    private var nextBoundary: Double?
    private var saved: [ActionStage: ActionComparisonRecord] = [:]
    private var savedContexts: [ActionStage: UUID] = [:]
    private var retained: [UUID: ActionComparisonRecord] = [:]
    private var saveRevisions: [UUID: UUID] = [:]
    private var saveFailures: [UUID: String] = [:]
    private var saveTail: Task<Result<Void, Error>, Never>?
    private let uptime: @MainActor () -> Double
    private let workspaceURL: URL?
    private let factory: @Sendable (ActionComparisonSpecification, URL) throws -> ActionComparisonSession
    private let loader: @Sendable (URL) async throws -> ActionComparisonRecord
    private let writer: @Sendable (ActionComparisonRecord, URL) async throws -> Void

    init(uptime: @escaping @MainActor () -> Double = { ProcessInfo.processInfo.systemUptime },
         sessionFactory: @escaping @Sendable (ActionComparisonSpecification, URL) throws -> ActionComparisonSession = { spec, directory in
             try ActionComparisonSession(specification: spec, journalStore: LocalActionJournalStore(directory: directory))
         }, recordLoader: @escaping @Sendable (URL) async throws -> ActionComparisonRecord = { url in
             let result = try ActionComparisonRecord.read(from: url)
             _ = try result.verify()
             return result
         }, recordWriter: @escaping @Sendable (ActionComparisonRecord, URL) async throws -> Void = { record, url in
             try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
             try record.write(to: url)
         }, workspaceURL: URL? = nil) {
        self.uptime = uptime; self.factory = sessionFactory; self.loader = recordLoader
        self.writer = recordWriter; self.workspaceURL = workspaceURL ?? Self.packagedWorkspace
    }
    var leftRecord: ActionRunRecord? { record?.left }
    var rightRecord: ActionRunRecord? { record?.right }
    var isComparison: Bool { record?.left != nil }
    var framesCount: Int { max(leftRecord?.frames.count ?? 0, rightRecord?.frames.count ?? 0) }
    var leftFrame: ActionFrame? { leftRecord.flatMap { $0.frames.indices.contains(row) ? $0.frames[row] : nil } }
    var rightFrame: ActionFrame? { rightRecord.flatMap { $0.frames.indices.contains(row) ? $0.frames[row] : nil } }
    var leftState: [Double] { leftFrame?.state ?? Array(repeating: 0, count: 32) }
    var rightState: [Double] { rightFrame?.state ?? Array(repeating: 0, count: 32) }
    var coordinateDifferences: [Double] { differences(leftFrame?.state, rightFrame?.state) }
    var externalDifferences: [Double] { differences(leftFrame?.externalInput, rightFrame?.externalInput) }
    var semanticDifferences: [Double] { differences(leftFrame?.semanticInput, rightFrame?.semanticInput) }
    var leftAction: ActionReceipt? { action(in: leftRecord) }
    var rightAction: ActionReceipt? { action(in: rightRecord) }
    var waiting: Bool { working }
    private var cancelledSession: Bool {
        record?.right.actions.contains { $0.status == .cancelled } == true || record?.left?.actions.contains { $0.status == .cancelled } == true
    }
    var canRun: Bool { !running && !working && !loading && UInt64(seedText) != nil && languageReady }
    var canCompare: Bool { canRun && stage.previous != nil }
    var canWrite: Bool {
        guard !running, !working, !loading, session != nil, let record,
              record.right.stage.hasJournal, record.stepCount > 0,
              record.stepCount < record.specification.steps, record.status != .failed, !cancelledSession else { return false }
        return !record.right.actions.contains { $0.observedStep == record.stepCount }
    }
    private var languageReady: Bool {
        mode == .fixedReplay || !stage.hasJournal || !localModel || (!endpoint.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !modelName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
    }
    private func differences(_ a: [Double]?, _ b: [Double]?) -> [Double] {
        guard let a, let b, a.count == b.count else { return [] }
        return zip(a, b).map { $1 - $0 }
    }
    private func action(in arm: ActionRunRecord?) -> ActionReceipt? {
        guard let arm else { return nil }
        if let selectedActionID { return arm.actions.first { $0.id == selectedActionID } }
        let step = max(leftFrame?.step ?? 0, rightFrame?.step ?? 0)
        return arm.actions.last { $0.observedStep <= step }
    }

    func select(_ next: ActionStage) {
        guard next != stage else { return }
        detachCurrent()
        stage = next; row = 0; selectedNode = 0; selectedActionID = nil; error = nil; source = ""
        record = saved[next]
        question = "What changes when adding \(next.addedFeature.lowercased())?"
        expectedDifference = next.addedFeature
        status = record == nil ? "Ready · \(next.title)" : "Previous record retained · Run begins a new session"
    }
    func run() { guard canRun else { return }; begin(comparePrevious: record?.specification.comparePrevious ?? false, singleStep: false) }
    func compareWithPrevious() { guard canCompare else { return }; begin(comparePrevious: true, singleStep: false, forceNew: true) }
    func step() {
        guard !working, !loading else { return }
        pauseClock()
        if session != nil, let record, record.status != .failed, !cancelledSession, record.stepCount < record.specification.steps {
            perform(manualJournal: false)
        } else { begin(comparePrevious: record?.specification.comparePrevious ?? false, singleStep: true, forceNew: true) }
    }
    func writeJournal() { guard canWrite else { return }; pauseClock(); perform(manualJournal: true) }
    func reset() {
        detachCurrent(); record = nil; row = 0; selectedNode = 0; selectedActionID = nil
        source = ""; error = nil; status = "Reset · settings kept; previous records are retained for saving."
    }
    private func specification(comparePrevious: Bool) throws -> ActionComparisonSpecification {
        guard let seed = UInt64(seedText.trimmingCharacters(in: .whitespacesAndNewlines)) else { throw SurfaceRenderError("Enter a whole-number seed.") }
        var spec = ActionComparisonSpecification(stage: stage, mode: mode, comparePrevious: comparePrevious && stage.previous != nil, seed: seed)
        if localModel && mode == .independentGeneration && stage.hasJournal { spec.language = LanguageConfiguration(backend: .ollama,
            endpoint: endpoint.trimmingCharacters(in: .whitespacesAndNewlines), model: modelName.trimmingCharacters(in: .whitespacesAndNewlines)) }
        spec.question = question; spec.expectedDifference = expectedDifference
        spec.alternatives = alternatives; spec.stoppingPoint = stoppingPoint
        try spec.validate(); return spec
    }
    private func begin(comparePrevious: Bool, singleStep: Bool, forceNew: Bool = false) {
        let spec: ActionComparisonSpecification
        do { spec = try specification(comparePrevious: comparePrevious) }
        catch { self.error = error.localizedDescription; return }
        if !forceNew, session != nil, record?.specification == spec, record?.status != .failed, !cancelledSession,
           (record?.stepCount ?? 0) < spec.steps {
            row = max(0, framesCount - 1); selectedActionID = nil
            if singleStep { perform(manualJournal: false) }
            else { running = true; replaying = false; nextBoundary = uptime() + 1 / speed; status = "Running recorded actions" }
            return
        }
        detachCurrent(); record = nil; row = 0; selectedActionID = nil; source = ""; error = nil
        let id = generation, context = contextID
        guard let directory = sessionDirectory(context) else { error = "The packaged research output location is unavailable."; status = "Could not start session"; return }
        do { try requireResearchDestination(directory) }
        catch { self.error = error.localizedDescription; return }
        working = true; status = "Preparing matched inputs and journal storage…"
        let factory = factory
        operation = Task { [weak self] in
            let result = await Task.detached(priority: .userInitiated) {
                try Task.checkCancellation()
                return try factory(spec, directory)
            }.result
            guard let self, self.generation == id else {
                if case .success(let session) = result { await session.stop() }
                return
            }
            do {
                let session = try result.get()
                let initial = await session.snapshot()
                guard self.generation == id else { await session.stop(); return }
                self.session = session; self.publish(initial)
                self.working = false; self.operation = nil
                if singleStep { self.perform(manualJournal: false) }
                else { self.running = true; self.nextBoundary = self.uptime() + 1 / self.speed; self.status = "Running · \(spec.stage.title)" }
            } catch {
                guard self.generation == id else { return }
                self.working = false; self.operation = nil
                self.error = error.localizedDescription; self.status = "Could not start session"
            }
        }
    }
    private func perform(manualJournal: Bool) {
        guard let session, !working else { return }
        let id = generation
        working = true; nextBoundary = nil; selectedActionID = nil
        status = manualJournal ? "Writing journal · simulated time paused" : "Advancing the next recorded step…"
        operation = Task { [weak self] in
            do {
                let value: ActionComparisonRecord
                if manualJournal { value = try await session.writeJournal() }
                else {
                    value = try await session.advance(onObservation: { [weak self] observation in
                        await self?.receiveObservation(observation, generation: id)
                    })
                }
                guard let self, self.generation == id else { return }
                self.working = false; self.operation = nil; self.publish(value)
                if value.status == .failed || self.cancelledSession || value.stepCount >= value.specification.steps { self.pauseClock() }
                if self.running { self.nextBoundary = self.uptime() + 1 / self.speed }
                if !self.running || value.stepCount % 30 == 0 || manualJournal { self.saveCurrent() }
                self.status = value.status == .failed ? "Stopped after a recorded failure" : self.running ? "Running · \(value.stepCount) recorded steps" : "Paused · \(value.stepCount) recorded steps"
                self.error = value.failure
            } catch {
                let value = await session.snapshot()
                guard let self, self.generation == id else { return }
                self.working = false; self.operation = nil; self.pauseClock(); self.publish(value); self.saveCurrent()
                if error is CancellationError { self.status = "Stopped · completed observations retained" }
                else { self.error = error.localizedDescription; self.status = "Stopped · request outcome retained" }
            }
        }
    }
    private func receiveObservation(_ value: ActionComparisonRecord, generation id: UUID) {
        guard generation == id, working else { return }
        publish(value)
        status = value.specification.stage.hasJournal && value.stepCount < value.specification.steps && value.stepCount % value.specification.turnEvery == 0
            ? "Processing actions at step \(value.stepCount) · simulated time paused"
            : "Advancing the next recorded step…"
    }
    private func publish(_ value: ActionComparisonRecord) {
        record = value; saved[value.specification.stage] = value; savedContexts[value.specification.stage] = contextID
        row = max(0, framesCount - 1)
    }
    func stop() {
        pauseClock(); cancelLoading()
        if working {
            status = "Stopping · preserving the current request outcome…"
            operation?.cancel()
            if let session { Task { await session.stop() } }
            else { generation = UUID(); working = false; operation = nil; status = "Stopped before the session started" }
        } else { saveCurrent(); status = "Paused · recorded actions retained" }
    }
    func leave() { stop() }
    private func pauseClock() { running = false; replaying = false; nextBoundary = nil }
    func replay() {
        guard !working, !loading, framesCount > 0 else { return }
        if replaying { pauseClock(); status = "Replay paused"; return }
        pauseClock(); saveCurrent()
        if row >= framesCount - 1 { row = 0 }
        replaying = true; nextBoundary = uptime() + 1 / speed; selectedActionID = nil
        status = "Replaying shared recorded steps"
    }
    func scrub(_ value: Double) {
        guard value.isFinite, !working else { return }
        let wasRunning = running; pauseClock()
        row = Int(min(Double(max(0, framesCount - 1)), max(0, value))); selectedActionID = nil
        if wasRunning { saveCurrent() }
        status = framesCount == 0 ? "Ready" : "Inspecting recorded step \(row + 1)"
    }
    func changeSpeed(_ value: Double) {
        guard [1.0, 3, 10, 20].contains(value) else { return }
        speed = value
        if running || replaying { nextBoundary = uptime() + 1 / speed }
    }
    func tick() {
        guard !working, !loading, let deadline = nextBoundary, uptime() >= deadline else { return }
        if running { perform(manualJournal: false) }
        else if replaying {
            row = min(row + 1, max(0, framesCount - 1)); selectedActionID = nil
            nextBoundary = uptime() + 1 / speed
            if row >= framesCount - 1 { pauseClock(); status = "Replay complete" }
        }
    }

    /// Cancel an old operation, retain its final receipts off-screen, and invalidate
    /// every callback before the next source can replace the display.
    private func detachCurrent() {
        pauseClock(); cancelLoading()
        let oldSession = session, oldOperation = operation, oldContext = contextID
        if let record {
            saved[record.specification.stage] = record; savedContexts[record.specification.stage] = oldContext
            save(record, context: oldContext)
        }
        generation = UUID(); contextID = UUID(); session = nil; operation = nil; working = false
        oldOperation?.cancel()
        if let oldSession {
            Task { [weak self] in
                await oldSession.stop(); await oldOperation?.value
                let final = await oldSession.snapshot()
                if self?.savedContexts[final.specification.stage] == oldContext { self?.saved[final.specification.stage] = final }
                self?.save(final, context: oldContext)
            }
        }
    }
    func chooseFile() {
        stop()
        let panel = NSOpenPanel(); panel.allowedContentTypes = [.json]
        panel.canChooseDirectories = false; panel.allowsMultipleSelection = false
        panel.message = "Open an Actions comparison with its portable journal text."
        if panel.runModal() == .OK, let url = panel.url { open(url) }
    }
    func loadExample() {
        if let url = Bundle.module.url(forResource: "essentials-actions-feedback", withExtension: "json")
            ?? Bundle.module.url(forResource: "essentials-actions-feedback", withExtension: "json", subdirectory: "Resources") { open(url) }
        else { error = "The packaged action example is unavailable." }
    }
    func open(_ url: URL) {
        detachCurrent(); let id = generation
        loading = true; error = nil; status = "Verifying actions, journals and applied inputs…"
        let loader = loader
        let worker = Task.detached(priority: .userInitiated) {
            let record = try await loader(url); try Task.checkCancellation(); return record
        }
        loadWorker = worker
        loadTask = Task { [weak self] in
            let result = await worker.result
            guard let self, self.generation == id else { return }
            self.loading = false; self.loadTask = nil; self.loadWorker = nil
            do {
                let value = try result.get(); self.record = value; self.saved[value.specification.stage] = value; self.savedContexts[value.specification.stage] = self.contextID
                self.stage = value.specification.stage; self.mode = value.specification.mode; self.seedText = String(value.specification.seed)
                self.question = value.specification.question; self.expectedDifference = value.specification.expectedDifference
                self.alternatives = value.specification.alternatives; self.stoppingPoint = value.specification.stoppingPoint
                self.row = 0; self.selectedNode = 0; self.selectedActionID = nil; self.source = url.path
                self.status = "Verified replay · Run starts a new session; opening never contacts a model."
            } catch { self.error = error.localizedDescription; self.status = "Could not open file · previous record retained" }
        }
    }
    private func cancelLoading() {
        guard loading else { return }
        generation = UUID(); loadTask?.cancel(); loadWorker?.cancel()
        loadTask = nil; loadWorker = nil; loading = false
    }
    func export() {
        stop()
        guard let record, !working else { return }
        let panel = NSSavePanel(); panel.allowedContentTypes = [.json]
        panel.nameFieldStringValue = "essentials-actions-\(record.specification.stage.id)-\(record.specification.seed).json"
        panel.directoryURL = outputDirectory
        if panel.runModal() == .OK, let url = panel.url {
            do { try requireResearchDestination(url); save(record, context: contextID, explicitURL: url) }
            catch { self.error = error.localizedDescription }
        }
    }
    private func saveCurrent() { if let record { save(record, context: contextID) } }
    private func save(_ value: ActionComparisonRecord, context: UUID, explicitURL: URL? = nil) {
        guard value.stepCount > 0 || !value.right.actions.isEmpty else { return }
        let revision = UUID()
        saveRevisions[context] = revision; retained[context] = value
        guard let url = explicitURL ?? sessionDirectory(context)?.appendingPathComponent("run.json") else { saveIssue = "Record retained in memory · research output location unavailable."; return }
        do { try requireResearchDestination(url) } catch { saveIssue = error.localizedDescription; return }
        let previous = saveTail, writer = writer, id = generation
        let worker = Task.detached(priority: .utility) {
            if let previous { _ = await previous.value }
            do { try await writer(value, url); return Result<Void, Error>.success(()) }
            catch { return .failure(error) }
        }
        saveTail = worker
        Task { [weak self] in
            let result = await worker.value
            guard let self else { return }
            switch result {
            case .success:
                guard self.saveRevisions[context] == revision else { return }
                self.retained.removeValue(forKey: context)
                self.saveRevisions.removeValue(forKey: context)
                self.saveFailures.removeValue(forKey: context)
                self.saveIssue = self.saveFailures.values.first
                if self.generation == id && self.contextID == context && !self.working && !self.loading && !self.running {
                    self.source = url.path
                }
            case .failure(let error):
                guard self.saveRevisions[context] == revision else { return }
                self.saveFailures[context] = "An action record remains in memory. Saving failed: " + error.localizedDescription
                self.saveIssue = self.saveFailures[context]
            }
        }
    }
    private var outputDirectory: URL? { workspaceURL?.appendingPathComponent("research/outputs/essentials/actions", isDirectory: true) }
    private func sessionDirectory(_ id: UUID) -> URL? { outputDirectory?.appendingPathComponent(id.uuidString, isDirectory: true) }
    private func requireResearchDestination(_ url: URL) throws {
        guard let workspaceURL else { throw SurfaceRenderError("The research workspace location is unavailable in this package.") }
        let root = workspaceURL.resolvingSymlinksInPath().standardizedFileURL.path
        guard url.resolvingSymlinksInPath().standardizedFileURL.path.hasPrefix(root + "/") else {
            throw SurfaceRenderError("Save Actions records inside the research project. The live sibling projects are read-only.")
        }
    }
    private static var packagedWorkspace: URL? {
        guard let file = Bundle.module.url(forResource: "essentials-workspace", withExtension: "txt")
            ?? Bundle.module.url(forResource: "essentials-workspace", withExtension: "txt", subdirectory: "Resources"),
              let text = try? String(contentsOf: file, encoding: .utf8) else { return nil }
        return URL(fileURLWithPath: text.trimmingCharacters(in: .whitespacesAndNewlines), isDirectory: true)
    }
}
