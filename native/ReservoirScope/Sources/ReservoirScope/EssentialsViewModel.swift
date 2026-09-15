import SwiftUI
import UniformTypeIdentifiers
import EssentialsCore

@MainActor
final class EssentialsViewModel: ObservableObject {
    @Published var stage: EssentialsStage = .reservoir
    @Published var frames: [EssentialsFrame] = []
    @Published var record: RunRecord?
    @Published var row = 0
    @Published var selectedNode = 0
    @Published var running = false
    @Published private(set) var loading = false
    @Published var playing = false
    @Published var status = "Choose a stage, then Run or open its example."
    @Published var error: String?
    @Published var source = ""
    @Published var speed = 20.0
    @Published var seedText = "20260909"
    @Published var stepCount = 300
    @Published var noiseEnabled = false
    @Published var regulationEnabled = true
    @Published var localModel = false
    @Published var endpoint = ""
    @Published var modelName = ""
    private var session: EssentialsSession?
    private var runTask: Task<Void, Never>?
    private var loadTask: Task<Void, Never>?
    private var loadWorker: Task<RunRecord, Error>?
    private var generation = UUID()
    private var saved: [EssentialsStage: RunRecord] = [:]
    private var clock = ReplayClock()
    private var replayPosition = 0.0
    private let sessionFactory: @MainActor () -> EssentialsSession
    private let recordLoader: @Sendable (URL) async throws -> RunRecord
    private let uptime: @MainActor () -> Double

    init(sessionFactory: @escaping @MainActor () -> EssentialsSession = { EssentialsSession() },
         recordLoader: @escaping @Sendable (URL) async throws -> RunRecord = { url in
             try Task.checkCancellation()
             let record = try RunRecord.read(from: url)
             try Task.checkCancellation()
             _ = try RunVerifier.verify(record)
             try Task.checkCancellation()
             return record
         }, uptime: @escaping @MainActor () -> Double = { ProcessInfo.processInfo.systemUptime }) {
        self.sessionFactory = sessionFactory; self.recordLoader = recordLoader; self.uptime = uptime
    }

    var frame: EssentialsFrame? { frames.indices.contains(row) ? frames[row] : nil }
    var state: [Double] { frame?.state ?? Array(repeating: 0, count: 32) }
    var turn: LanguageTurn? {
        guard let frame, let record else { return nil }
        return record.turns.last { $0.observedStep <= frame.step }
    }
    var canRun: Bool {
        !running && UInt64(seedText) != nil &&
        (!localModel || stage.rawValue < 3 || (!endpoint.trimmingCharacters(in: .whitespaces).isEmpty && !modelName.isEmpty))
    }

    func select(_ next: EssentialsStage) {
        guard !running else { return }
        cancelLoading()
        generation = UUID()
        playing = false; stage = next; error = nil; selectedNode = 0
        if let previous = saved[next] { display(previous, source: "Previous run of this stage") }
        else { frames = []; record = nil; row = 0; replayPosition = 0; source = ""; status = "Ready · " + next.title }
    }

    func run() {
        guard canRun, let seed = UInt64(seedText) else { return }
        var spec = RunSpecification(stage: stage, seed: seed, steps: stepCount)
        spec.noiseAmplitude = noiseEnabled ? 0.02 : 0
        spec.regulationEnabled = regulationEnabled
        if localModel && stage.rawValue >= 3 {
            spec.language = LanguageConfiguration(backend: .ollama,
                endpoint: endpoint.trimmingCharacters(in: .whitespacesAndNewlines),
                model: modelName.trimmingCharacters(in: .whitespacesAndNewlines))
        }
        do { try spec.validate() } catch { self.error = error.localizedDescription; return }
        cancelLoading()
        let id = UUID(); generation = id
        let engine = sessionFactory(); session = engine
        running = true; playing = false; frames = []; record = nil; row = 0; selectedNode = 0
        replayPosition = 0
        error = nil; source = ""; status = "Running · " + stage.title
        runTask = Task { [weak self] in
            do {
                let completed = try await engine.run(spec: spec, onFrame: { [weak self] frame in
                    await self?.receive(frame, generation: id)
                }, onStatus: { [weak self] message in
                    await self?.receiveStatus(message, generation: id)
                })
                guard let self, self.generation == id else { return }
                self.running = false; self.session = nil; self.runTask = nil
                self.saved[completed.specification.stage] = completed
                self.record = completed; self.frames = completed.frames
                self.row = max(0, completed.frames.count - 1)
                self.replayPosition = Double(self.row)
                self.status = "\(completed.status.rawValue.capitalized) · \(completed.frames.count) recorded steps"
                self.error = completed.failure
                self.saveGenerated(completed)
            } catch {
                guard let self, self.generation == id else { return }
                self.running = false; self.session = nil; self.runTask = nil
                self.status = "Run stopped"; self.error = error.localizedDescription
            }
        }
    }

    private func receive(_ frame: EssentialsFrame, generation id: UUID) {
        guard generation == id else { return }
        frames.append(frame); row = frames.count - 1
        replayPosition = Double(row)
    }
    private func receiveStatus(_ message: String, generation id: UUID) {
        guard generation == id else { return }
        status = message
    }
    func stop() {
        cancelLoading()
        if playing { tick() }
        playing = false
        guard running else { return }
        status = "Stopping at the current boundary…"
        runTask?.cancel()
        if let session { Task { await session.stop() } }
    }
    func reset() {
        guard !running else { return }
        cancelLoading()
        generation = UUID()
        playing = false; frames = []; record = nil; row = 0; selectedNode = 0
        replayPosition = 0
        error = nil; source = ""; status = "Reset · the next run starts from the same seed."
    }
    func replay() {
        guard !running, !frames.isEmpty else { return }
        if playing { tick(); playing = false; return }
        if row >= frames.count - 1 { row = 0; replayPosition = 0 }
        clock.start(at: replayPosition, uptime: uptime())
        playing = true
    }
    func scrub(_ value: Double) {
        playing = false; row = min(max(0, Int(value)), max(0, frames.count - 1))
        replayPosition = Double(row)
    }
    func tick() {
        guard playing, !running, !frames.isEmpty else { return }
        replayPosition = min(Double(frames.count - 1), clock.advance(uptime: uptime(), rate: speed))
        row = Int(replayPosition)
        if row >= frames.count - 1 { playing = false }
    }
    func changeSpeed(_ value: Double) {
        if playing { tick(); clock.start(at: replayPosition, uptime: uptime()) }
        speed = value
    }

    func chooseFile() {
        guard !running else { return }
        let panel = NSOpenPanel(); panel.allowedContentTypes = [.json]
        panel.canChooseDirectories = false; panel.allowsMultipleSelection = false
        panel.message = "Open a saved Essentials experiment. Replaying a run does not contact a model."
        if panel.runModal() == .OK, let url = panel.url { open(url) }
    }
    func loadExample() {
        guard !running else { return }
        let name = "essentials-stage-\(stage.rawValue)"
        if let url = Bundle.module.url(forResource: name, withExtension: "json")
            ?? Bundle.module.url(forResource: name, withExtension: "json", subdirectory: "Resources") {
            open(url)
        } else { error = "This app does not contain the example for this stage. You can generate it with Run." }
    }
    func open(_ url: URL) {
        guard !running else { return }
        cancelLoading()
        playing = false; error = nil; status = "Verifying saved steps…"
        let id = UUID(); generation = id
        loading = true
        let loader = recordLoader
        let worker = Task.detached(priority: .userInitiated) { try await loader(url) }
        loadWorker = worker
        loadTask = Task { [weak self] in
            let result = await worker.result
            guard let self, self.generation == id else { return }
            self.loading = false; self.loadTask = nil; self.loadWorker = nil
            do {
                let next = try result.get()
                self.saved[next.specification.stage] = next
                self.display(next, source: url.path)
                self.status = "Verified replay · \(next.frames.count) recorded steps"
            } catch {
                self.error = error.localizedDescription
                self.status = "File could not be opened · previous run retained"
            }
        }
    }
    private func display(_ value: RunRecord, source: String) {
        playing = false; replayPosition = 0
        record = value; frames = value.frames; stage = value.specification.stage
        row = 0; selectedNode = 0; self.source = source
        seedText = String(value.specification.seed); stepCount = value.specification.steps
        noiseEnabled = value.specification.noiseAmplitude > 0
        regulationEnabled = value.specification.regulationEnabled
        status = "\(value.status.rawValue.capitalized) · \(value.frames.count) recorded steps"
    }

    private func cancelLoading() {
        guard loading else { return }
        generation = UUID()
        loadTask?.cancel(); loadWorker?.cancel()
        loadTask = nil; loadWorker = nil; loading = false
        status = record == nil ? "Ready · " + stage.title : "Recorded run retained"
    }

    func export() {
        guard let record, !running else { return }
        let panel = NSSavePanel(); panel.allowedContentTypes = [.json]
        panel.nameFieldStringValue = "essentials-stage-\(record.specification.stage.rawValue)-\(record.specification.seed).json"
        panel.directoryURL = outputDirectory
        if panel.runModal() == .OK, let url = panel.url {
            do {
                try requireResearchDestination(url)
                writeRecord(record, to: url, createDirectory: false, successStatus: "Exported recorded run")
            }
            catch { self.error = error.localizedDescription }
        }
    }
    private var workspace: URL? {
        guard let path = Bundle.module.url(forResource: "essentials-workspace", withExtension: "txt")
            ?? Bundle.module.url(forResource: "essentials-workspace", withExtension: "txt", subdirectory: "Resources"),
              let text = try? String(contentsOf: path, encoding: .utf8) else { return nil }
        return URL(fileURLWithPath: text.trimmingCharacters(in: .whitespacesAndNewlines), isDirectory: true).resolvingSymlinksInPath()
    }
    private var outputDirectory: URL? { workspace?.appendingPathComponent("research/outputs/essentials", isDirectory: true) }
    private func requireResearchDestination(_ url: URL) throws {
        guard let workspace else { throw SurfaceRenderError("The research workspace location is unavailable in this package.") }
        let resolved = url.resolvingSymlinksInPath().standardizedFileURL.path
        guard resolved.hasPrefix(workspace.path + "/") else {
            throw SurfaceRenderError("Save this experiment inside the research workspace. Its live sibling projects are read-only.")
        }
    }
    private func saveGenerated(_ run: RunRecord) {
        guard let directory = outputDirectory else { status += " · Export to save"; return }
        do {
            try requireResearchDestination(directory)
            let name = "stage-\(run.specification.stage.rawValue)-\(UUID().uuidString).json"
            let url = directory.appendingPathComponent(name)
            writeRecord(run, to: url, createDirectory: true, successStatus: status)
        } catch { self.error = "Run retained in memory. Saving failed: " + error.localizedDescription }
    }

    private func writeRecord(_ run: RunRecord, to url: URL, createDirectory: Bool, successStatus: String) {
        let id = generation
        status = successStatus + " · Saving…"
        Task { [weak self] in
            let result = await Task.detached(priority: .utility) {
                if createDirectory {
                    try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
                }
                try run.write(to: url)
            }.result
            guard let self, self.generation == id else { return }
            self.status = successStatus
            do { try result.get(); self.source = url.path }
            catch { self.error = "Run retained in memory. Saving failed: " + error.localizedDescription }
        }
    }
}
