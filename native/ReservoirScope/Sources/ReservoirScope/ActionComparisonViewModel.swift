import SwiftUI
import UniformTypeIdentifiers
import EssentialsCore

/// One paced opportunity advances the shared core session. Rendering can replay
/// its immutable records while provider work and journal writes remain off-main.
@MainActor
final class ActionComparisonViewModel: ObservableObject {
    @Published var stage: ActionStage = .minimal
    @Published private(set) var comparisonKind: ActionComparisonKind = .components
    @Published var mode: ActionComparisonMode = .fixedReplay
    @Published private(set) var record: ActionComparisonRecord?
    @Published var row = 0
    @Published var selectedNode = 0
    @Published var selectedActionID: Int?
    @Published private(set) var running = false
    @Published private(set) var journalPending = false
    @Published private(set) var working = false
    @Published private(set) var replaying = false
    @Published private(set) var loading = false
    @Published private(set) var speed = 3.0
    @Published var seedText = "20260909"
    @Published var localModel = false
    @Published var endpoint: String { didSet { preferences.set(endpoint, forKey: "experiment.endpoint") } }
    @Published var modelName: String { didSet { preferences.set(modelName, forKey: "experiment.model") } }
    @Published var question = "How does external input change a minimal reservoir?"
    @Published var expectedDifference = "Inspect the input, previous state, and resulting state before adding recurrence."
    @Published var alternatives = "External forcing, noise, model settings and display scale must remain matched; independently generated writing can also change the trajectory."
    @Published var stoppingPoint = "300 steps, nine scheduled opportunities; stop and retain evidence on failure."
    @Published var status = "Choose a version, then run it or compare with the preceding version."
    @Published var error: String?
    @Published var source = ""
    @Published private(set) var saveIssue: String?
    enum RecordOrigin: Equatable { case none, activeExperiment, bundledExample, openedFile, retainedExperiment }
    @Published private(set) var recordOrigin: RecordOrigin = .none

    private var session: ActionComparisonSession?
    private var operation: Task<Void, Never>?
    private var loadWorker: Task<ActionComparisonRecord, Error>?
    private var loadTask: Task<Void, Never>?
    private var generation = UUID()
    private var contextID = UUID()
    private var nextBoundary: Double?
    private var stopAtNextAction = false
    private var preparedComparePrevious = false
    private var experimentTemplate: ActionComparisonSpecification?
    private struct NavigationKey: Hashable {
        let stage: Int
        let kind: String
        init(_ stage: ActionStage, _ kind: ActionComparisonKind) { self.stage = stage.rawValue; self.kind = kind.rawValue }
        init(_ record: ActionComparisonRecord) { self.init(record.specification.stage, record.specification.comparisonKind) }
    }
    private var saved: [NavigationKey: ActionComparisonRecord] = [:]
    private var savedContexts: [NavigationKey: UUID] = [:]
    private var savedSources: [NavigationKey: String] = [:]
    private var savedOrigins: [NavigationKey: RecordOrigin] = [:]
    private var retained: [UUID: ActionComparisonRecord] = [:]
    private var saveRevisions: [UUID: UUID] = [:]
    private var saveFailures: [UUID: String] = [:]
    private var saveTail: Task<Result<Void, Error>, Never>?
    private let preferences: UserDefaults
    private let uptime: @MainActor () -> Double
    private let workspaceURL: URL?
    private let factory: @Sendable (ActionComparisonSpecification, URL) throws -> ActionComparisonSession
    private let loader: @Sendable (URL) async throws -> ActionComparisonRecord
    private let writer: @Sendable (ActionComparisonRecord, URL) async throws -> Void

    init(uptime: @escaping @MainActor () -> Double = { ProcessInfo.processInfo.systemUptime },
         sessionFactory: @escaping @Sendable (ActionComparisonSpecification, URL) throws -> ActionComparisonSession = { spec, directory in
             let store = try LocalActionJournalStore(directory: directory)
             let encoder = JSONEncoder(); encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
             try encoder.encode(spec).write(to: directory.appendingPathComponent("protocol.json"), options: .atomic)
             return try ActionComparisonSession(specification: spec, journalStore: store)
         }, recordLoader: @escaping @Sendable (URL) async throws -> ActionComparisonRecord = { url in
             let result = try ActionComparisonRecord.read(from: url)
             _ = try result.verify()
             return result
         }, recordWriter: @escaping @Sendable (ActionComparisonRecord, URL) async throws -> Void = { record, url in
             try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
             try record.write(to: url)
         }, workspaceURL: URL? = nil, preferences: UserDefaults = ScopePreferences.store) {
        self.preferences = preferences
        self.endpoint = preferences.string(forKey: "experiment.endpoint") ?? ""
        self.modelName = preferences.string(forKey: "experiment.model") ?? ""
        self.uptime = uptime; self.factory = sessionFactory; self.loader = recordLoader
        self.writer = recordWriter; self.workspaceURL = workspaceURL ?? ExperimentStore.defaultRoot
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
    func applicationStepAtCursor(_ action: ActionReceipt) -> Int? {
        guard let step = action.applicationStep, step <= (rightFrame?.step ?? 0) else { return nil }
        return step
    }
    private var cancelledSession: Bool {
        record?.right.actions.contains { $0.status == .cancelled } == true || record?.left?.actions.contains { $0.status == .cancelled } == true
    }
    var isRecording: Bool { record != nil && recordOrigin != .activeExperiment }
    private var canAdvanceSession: Bool {
        guard let record, session != nil else { return false }
        return record.status != .failed && !cancelledSession && record.stepCount < record.specification.steps
    }
    var canRun: Bool {
        guard !running, !replaying, !working, !loading else { return false }
        if isRecording { return framesCount > 0 && row < framesCount - 1 }
        if session != nil { return canAdvanceSession }
        return UInt64(seedText) != nil && languageReady
    }
    var canStep: Bool {
        guard !working, !loading else { return false }
        if record != nil && row < framesCount - 1 { return true }
        if isRecording { return false }
        if session != nil { return canAdvanceSession }
        return UInt64(seedText) != nil && languageReady
    }
    var canCompare: Bool { !working && !loading && (comparisonKind == .observation || stage.previous != nil) }
    var canWrite: Bool {
        guard !running, !replaying, !working, !loading, session != nil, row == framesCount - 1, let record,
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
        if let selectedActionID { return arm.actions.first { $0.id == selectedActionID && $0.observedStep <= row + 1 } }
        let step = max(leftFrame?.step ?? 0, rightFrame?.step ?? 0)
        return arm.actions.last { $0.observedStep <= step }
    }

    func select(_ next: ActionStage) {
        guard next != stage || comparisonKind != .components else { return }
        stopAtNextAction = false
        detachCurrent()
        comparisonKind = .components
        stage = next; row = 0; selectedNode = 0; selectedActionID = nil; error = nil
        restoreNavigation(next, kind: .components)
        experimentTemplate = nil; preparedComparePrevious = false
        question = record?.specification.question ?? "What changes when adding \(next.addedFeature.lowercased())?"
        expectedDifference = record?.specification.expectedDifference ?? next.addedFeature
        status = record == nil ? "Ready · \(next.title)" : "Retained recording · Play and Step inspect saved evidence"
    }
    private func restoreNavigation(_ stage: ActionStage, kind: ActionComparisonKind) {
        let key = NavigationKey(stage, kind)
        record = saved[key]
        source = savedSources[key] ?? ""
        recordOrigin = record == nil ? .none : (savedOrigins[key] == .bundledExample ? .bundledExample : savedOrigins[key] == .openedFile ? .openedFile : .retainedExperiment)
        if let context = savedContexts[key] { contextID = context }
        if let record {
            mode = record.specification.mode; seedText = String(record.specification.seed)
            localModel = record.specification.language.backend == .ollama
            question = record.specification.question; expectedDifference = record.specification.expectedDifference
            alternatives = record.specification.alternatives; stoppingPoint = record.specification.stoppingPoint
        }
    }
    var provenance: String {
        guard let record else { return localModel && mode == .independentGeneration ? "Fresh local generation" : "Scripted example" }
        if record.specification.language.backend == .ollama { return isRecording ? "Recorded model run" : "Fresh local generation" }
        return "Scripted example"
    }
    func selectObservationComparison() {
        guard comparisonKind != .observation else { return }
        stopAtNextAction = false
        detachCurrent(); stage = .journalOutput; comparisonKind = .observation
        restoreNavigation(stage, kind: .observation)
        experimentTemplate = nil; preparedComparePrevious = true
        mode = .independentGeneration; row = 0; selectedActionID = nil
        question = "What changes in a journal when measured reservoir coordinates are supplied?"
        expectedDifference = "Compare accounts with sensory measurements alone versus sensory measurements plus 32 indexed state values."
        alternatives = "Additional prompt content and model variability can change writing; difference is not an accuracy score."
        stoppingPoint = "300 matched steps; nine opportunities; retain both arms and stop on failure."
        status = record == nil ? "Stage D in both arms · identical trajectories · only observation access differs" : "Retained observation comparison · playback only"
    }
    func nextJournal() {
        guard !working, !loading, stage.hasJournal else { return }
        pauseClock()
        let opportunities = (record?.right.actions ?? []) + (record?.left?.actions ?? [])
        if let step = opportunities.map(\.observedStep).filter({ $0 > row + 1 }).min() {
            scrub(Double(step - 1)); return
        }
        guard !isRecording else { pauseClock(); status = "No later journal opportunity in this recording."; return }
        guard canRun else { status = "No further opportunity in this experiment. Prepare a new experiment to continue."; return }
        stopAtNextAction = true; run()
    }
    func retrySaves() { for (id, value) in retained { save(value, context: id) } }
    func run() {
        guard canRun else { return }
        if isRecording {
            replaying = true; nextBoundary = uptime() + 1 / speed; selectedActionID = nil
            status = "Playing saved evidence · no generation"
        } else { begin(comparePrevious: record?.specification.comparePrevious ?? preparedComparePrevious, singleStep: false) }
    }
    /// Preparing a configuration never creates a session or calls a provider.
    func prepareExperiment(comparePrevious: Bool? = nil) {
        guard !working, !loading else { return }
        var template = record?.specification ?? experimentTemplate
        let compare = comparePrevious ?? template?.comparePrevious ?? preparedComparePrevious
        detachCurrent(); record = nil; recordOrigin = .none; row = 0; selectedActionID = nil
        source = ""; error = nil; stopAtNextAction = false
        template?.steps = 300
        experimentTemplate = template
        preparedComparePrevious = comparisonKind == .observation || (compare && stage.previous != nil)
        stoppingPoint = "300 steps, nine scheduled opportunities; stop and retain evidence on failure."
        status = "Experiment prepared · Start or Step creates a new run"
    }
    func compareWithPrevious() {
        guard canCompare else { return }
        prepareExperiment(comparePrevious: true)
    }
    func step() {
        guard canStep else { return }
        stopAtNextAction = false; pauseClock()
        if record != nil, row < framesCount - 1 {
            row += 1; selectedActionID = nil
            status = "Inspecting recorded step \(row + 1)"
        } else if isRecording {
            status = "End of recording · prepare a new experiment to generate more steps"
        } else if canAdvanceSession {
            perform(manualJournal: false)
        } else if session == nil {
            begin(comparePrevious: preparedComparePrevious, singleStep: true)
        }
    }
    func writeJournal() {
        guard canWrite else { return }
        pauseClock(); row = max(0, framesCount - 1); selectedActionID = nil
        perform(manualJournal: true)
    }
    func reset() {
        stopAtNextAction = false
        detachCurrent(); record = nil; recordOrigin = .none; row = 0; selectedNode = 0; selectedActionID = nil
        experimentTemplate = nil; preparedComparePrevious = false
        source = ""; error = nil; status = "Reset · settings kept; previous records are retained for saving."
    }
    private func specification(comparePrevious: Bool) throws -> ActionComparisonSpecification {
        guard let seed = UInt64(seedText.trimmingCharacters(in: .whitespacesAndNewlines)) else { throw SurfaceRenderError("Enter a whole-number seed.") }
        var spec = experimentTemplate ?? ActionComparisonSpecification(stage: stage, seed: seed)
        spec.stage = stage; spec.comparisonKind = comparisonKind; spec.seed = seed
        spec.mode = comparisonKind == .observation ? .independentGeneration : mode
        spec.comparePrevious = comparisonKind == .observation || (comparePrevious && stage.previous != nil)
        spec.language = LanguageConfiguration(backend: .scripted)
        if localModel && spec.mode == .independentGeneration && stage.hasJournal { spec.language = LanguageConfiguration(backend: .ollama,
            endpoint: endpoint.trimmingCharacters(in: .whitespacesAndNewlines), model: modelName.trimmingCharacters(in: .whitespacesAndNewlines), contextTokens: 4096, responseFormat: "json") }
        spec.question = question; spec.expectedDifference = expectedDifference
        spec.alternatives = alternatives; spec.stoppingPoint = stoppingPoint
        try spec.validate(); return spec
    }
    private func begin(comparePrevious: Bool, singleStep: Bool) {
        if canAdvanceSession {
            row = max(0, framesCount - 1); selectedActionID = nil
            if singleStep { perform(manualJournal: false) }
            else { running = true; replaying = false; nextBoundary = uptime() + 1 / speed; status = "Resuming experiment at its latest recorded step" }
            return
        }
        let spec: ActionComparisonSpecification
        do { spec = try specification(comparePrevious: comparePrevious) }
        catch { self.error = error.localizedDescription; return }
        detachCurrent(); recordOrigin = .activeExperiment; record = nil; row = 0; selectedActionID = nil; source = ""; error = nil
        let id = generation, context = contextID
        guard let directory = sessionDirectory(context) else { error = "The local experiment store is unavailable."; status = "Could not start session"; return }
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
        journalPending = manualJournal
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
                self.journalPending = false; self.working = false; self.operation = nil; self.publish(value)
                if self.stopAtNextAction && value.right.actions.last?.observedStep == value.stepCount {
                    self.pauseClock(); self.stopAtNextAction = false
                }
                if value.status == .failed || self.cancelledSession || value.stepCount >= value.specification.steps { self.pauseClock() }
                if self.running { self.nextBoundary = self.uptime() + 1 / self.speed }
                if !self.running || value.stepCount % 30 == 0 || manualJournal { self.saveCurrent() }
                self.status = value.status == .failed ? "Stopped after a recorded failure" : self.running ? "Running · \(value.stepCount) recorded steps" : "Paused · \(value.stepCount) recorded steps"
                self.error = value.failure
            } catch {
                let value = await session.snapshot()
                guard let self, self.generation == id else { return }
                self.journalPending = false; self.working = false; self.operation = nil; self.pauseClock(); self.publish(value); self.saveCurrent()
                if error is CancellationError { self.status = "Stopped · completed observations retained" }
                else { self.error = error.localizedDescription; self.status = "Stopped · request outcome retained" }
            }
        }
    }
    private func receiveObservation(_ value: ActionComparisonRecord, generation id: UUID) {
        guard generation == id, working else { return }
        publish(value)
        journalPending = value.specification.stage.hasJournal && value.stepCount < value.specification.steps && value.stepCount % value.specification.turnEvery == 0
        status = value.specification.stage.hasJournal && value.stepCount < value.specification.steps && value.stepCount % value.specification.turnEvery == 0
            ? "Processing actions at step \(value.stepCount) · simulated time paused"
            : "Advancing the next recorded step…"
    }
    private func publish(_ value: ActionComparisonRecord) {
        record = value
        let key = NavigationKey(value)
        saved[key] = value; savedContexts[key] = contextID
        savedSources[key] = source; savedOrigins[key] = recordOrigin
        row = max(0, framesCount - 1)
    }
    func stop() {
        stopAtNextAction = false
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
        stopAtNextAction = false
        if replaying { pauseClock(); status = "Replay paused"; return }
        pauseClock(); saveCurrent()
        row = 0
        replaying = true; nextBoundary = uptime() + 1 / speed; selectedActionID = nil
        status = "Replaying shared recorded steps"
    }
    func scrub(_ value: Double) {
        guard value.isFinite, !working else { return }
        let wasRunning = running; stopAtNextAction = false; pauseClock()
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
            let key = NavigationKey(record)
            saved[key] = record; savedContexts[key] = oldContext
            savedSources[key] = source; savedOrigins[key] = recordOrigin
            if recordOrigin == .activeExperiment { save(record, context: oldContext) }
        }
        if recordOrigin == .activeExperiment { recordOrigin = record == nil ? .none : .retainedExperiment }
        generation = UUID(); contextID = UUID(); session = nil; operation = nil; working = false; journalPending = false
        oldOperation?.cancel()
        if let oldSession {
            Task { [weak self] in
                await oldSession.stop(); await oldOperation?.value
                let final = await oldSession.snapshot()
                let key = NavigationKey(final)
                if self?.savedContexts[key] == oldContext { self?.saved[key] = final }
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
    func loadExample(recordedModel: Bool = false) {
        let name = recordedModel
            ? (comparisonKind == .observation ? "example-model-observation" : "example-model-\(stage.rawValue)")
            : (comparisonKind == .observation ? "example-observation-scripted" : "example-component-\(stage.rawValue)")
        if let url = Bundle.module.url(forResource: name, withExtension: "json")
            ?? Bundle.module.url(forResource: name, withExtension: "json", subdirectory: "Resources") { open(url) }
        else { error = "The packaged action example is unavailable." }
    }
    func open(_ url: URL, initialRow: Int = 0) {
        stopAtNextAction = false
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
                let value = try result.get(); self.record = value
                let bundleRoot = Bundle.module.resourceURL?.standardizedFileURL.path ?? ""
                self.recordOrigin = !bundleRoot.isEmpty && url.standardizedFileURL.path.hasPrefix(bundleRoot + "/") ? .bundledExample : .openedFile
                let key = NavigationKey(value)
                self.saved[key] = value; self.savedContexts[key] = self.contextID
                self.savedSources[key] = url.path; self.savedOrigins[key] = self.recordOrigin
                self.comparisonKind = value.specification.comparisonKind
                self.experimentTemplate = nil; self.preparedComparePrevious = value.specification.comparePrevious
                self.localModel = value.specification.language.backend == .ollama
                self.stage = value.specification.stage; self.mode = value.specification.mode; self.seedText = String(value.specification.seed)
                self.question = value.specification.question; self.expectedDifference = value.specification.expectedDifference
                self.alternatives = value.specification.alternatives; self.stoppingPoint = value.specification.stoppingPoint
                self.row = min(max(0, initialRow), max(0, self.framesCount - 1)); self.selectedNode = 0; self.selectedActionID = nil; self.source = url.path
                self.status = "Verified recording · Play and Step inspect saved evidence; Try an experiment prepares a new run."
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
        guard !working else { return }
        let recovery = record.map { (contextID, $0) } ?? retained.first.map { ($0.key, $0.value) }
        guard let (exportID, record) = recovery else { return }
        let panel = NSSavePanel(); panel.allowedContentTypes = [.json]
        panel.nameFieldStringValue = "essentials-actions-\(record.specification.stage.id)-\(record.specification.seed).json"
        panel.directoryURL = outputDirectory
        if panel.runModal() == .OK, let url = panel.url {
            do { try requireResearchDestination(url); save(record, context: exportID, explicitURL: url) }
            catch { self.error = error.localizedDescription }
        }
    }
    func exportRetained(to destination: URL? = nil) {
        let recovery = saveFailures.keys.compactMap { id in retained[id].map { (id, $0) } }.first
            ?? retained.first.map { ($0.key, $0.value) }
        guard let (identity, value) = recovery else { return }
        var target = destination
        if target == nil {
            let panel = NSSavePanel(); panel.allowedContentTypes = [.json]
            panel.nameFieldStringValue = "recovered-actions-\(identity.uuidString).json"
            if panel.runModal() == .OK { target = panel.url }
        }
        if let target { save(value, context: identity, explicitURL: target) }
    }
    private func saveCurrent() { if recordOrigin == .activeExperiment, let record { save(record, context: contextID) } }
    private func save(_ value: ActionComparisonRecord, context: UUID, explicitURL: URL? = nil) {
        guard value.stepCount > 0 || !value.right.actions.isEmpty else { return }
        let revision = UUID()
        saveRevisions[context] = revision; retained[context] = value
        guard let url = explicitURL ?? sessionDirectory(context)?.appendingPathComponent("run.json") else { saveIssue = "Record retained in memory · local experiment store unavailable."; return }
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
    func flushForTermination() async -> Bool {
        stop(); await operation?.value
        retrySaves()
        if let saveTail { _ = await saveTail.value }
        for _ in 0..<100 {
            if retained.isEmpty { return true }
            if !saveFailures.isEmpty { return false }
            try? await Task.sleep(for: .milliseconds(20))
        }
        return retained.isEmpty
    }
    private var outputDirectory: URL? { workspaceURL?.appendingPathComponent("Actions", isDirectory: true) }
    private func sessionDirectory(_ id: UUID) -> URL? { outputDirectory?.appendingPathComponent(id.uuidString, isDirectory: true) }
    private func requireResearchDestination(_ url: URL) throws {
        try ExperimentStore.requireLocalDestination(url)
    }
}
