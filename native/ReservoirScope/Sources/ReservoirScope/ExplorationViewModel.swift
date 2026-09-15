import SwiftUI
import UniformTypeIdentifiers
import EssentialsCore

/// The timer only asks for a boundary. Each boundary records one actual step;
/// a delayed timer never batches missed steps or changes simulated dt.
@MainActor
final class ExplorationViewModel: ObservableObject {
    @Published var controls = ExplorationControls()
    @Published private(set) var frames: [ExplorationFrame] = []
    @Published var row = 0
    @Published var selectedNode = 0
    @Published private(set) var running = false
    @Published private(set) var replaying = false
    @Published private(set) var loading = false
    @Published private(set) var pulseQueued = false
    @Published private(set) var speed = 3.0
    @Published var seedText = "20260909"
    @Published var status = "Ready · send a pulse or take one step."
    @Published var error: String?
    @Published var source = ""
    @Published private(set) var saveIssue: String?
    private var engine: ExplorationEngine?
    private var nextBoundary: Double?
    private var generation = UUID()
    private var runID = UUID()
    private var loadTask: Task<Void, Never>?
    private var loadWorker: Task<ExplorationEngine, Error>?
    private var saveTail: Task<Result<Void, Error>, Never>?
    // A reset can release its visible trace before I/O finishes. Keep that immutable
    // snapshot here until the write succeeds, including when a destination fails.
    private var retainedSnapshots: [UUID: ExplorationRecord] = [:]
    private var lastQueuedCount: [UUID: Int] = [:]
    private let uptime: @MainActor () -> Double
    private let recordLoader: @Sendable (URL) async throws -> ExplorationRecord
    private let recordWriter: @Sendable (ExplorationRecord, URL) async throws -> Void
    private let workspaceURL: URL?

    init(uptime: @escaping @MainActor () -> Double = { ProcessInfo.processInfo.systemUptime },
         recordLoader: @escaping @Sendable (URL) async throws -> ExplorationRecord = { try ExplorationRecord.read(from: $0) },
         recordWriter: @escaping @Sendable (ExplorationRecord, URL) async throws -> Void = { record, url in
             try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
             try record.write(to: url)
         }, workspaceURL: URL? = nil) {
        self.uptime = uptime; self.recordLoader = recordLoader; self.recordWriter = recordWriter
        self.workspaceURL = workspaceURL ?? Self.packagedWorkspace
        do { engine = try ExplorationEngine(seed: 20260909) }
        catch { self.error = error.localizedDescription; status = "Could not prepare the reservoir." }
    }
    var frame: ExplorationFrame? { frames.indices.contains(row) ? frames[row] : nil }
    var state: [Double] { frame?.state ?? Array(repeating: 0, count: 32) }
    var record: ExplorationRecord? { engine?.record }
    var hasFrames: Bool { !frames.isEmpty }
    var atLimit: Bool { frames.count >= 1800 }
    var canRun: Bool { engine != nil && !loading && !atLimit }

    func startPause() {
        if running { pauseClock(); saveCurrent(); status = "Paused · \(frames.count) recorded steps"; return }
        guard canRun else { return }
        replaying = false; running = true; error = nil
        row = max(0, frames.count - 1)
        nextBoundary = uptime() + 1 / speed
        status = pulseQueued ? "Running · pulse queued for the next step" : "Running"
    }
    func step() {
        guard !loading else { return }
        pauseClock()
        advance(pulse: pulseQueued)
        saveCurrent()
    }
    func sendPulse() {
        guard canRun else { return }
        if running { pulseQueued = true; status = "Pulse queued for the next step" }
        else { pauseClock(); advance(pulse: true); saveCurrent() }
    }
    func reset() {
        guard let seed = UInt64(seedText.trimmingCharacters(in: .whitespacesAndNewlines)) else {
            error = "Enter a whole-number seed before resetting."; return
        }
        do {
            let replacement = try ExplorationEngine(seed: seed)
            pauseClock(); saveCurrent(); cancelLoading()
            generation = UUID(); runID = UUID(); engine = replacement
            frames = []; row = 0; selectedNode = 0; pulseQueued = false
            source = ""; error = nil; status = "Reset · controls kept, state returned to zero."
        } catch { self.error = error.localizedDescription }
    }
    func replay() {
        guard !loading, !frames.isEmpty else { return }
        if replaying { pauseClock(); status = "Replay paused"; return }
        if running { pauseClock(); saveCurrent() }
        running = false; replaying = true
        if row >= frames.count - 1 { row = 0 }
        nextBoundary = uptime() + 1 / speed
        status = "Replaying recorded steps"
    }
    func scrub(_ value: Double) {
        guard value.isFinite else { return }
        let wasRunning = running
        pauseClock()
        row = Int(min(Double(max(0, frames.count - 1)), max(0, value)))
        if wasRunning { saveCurrent() }
        status = frames.isEmpty ? "Ready" : "Inspecting recorded step \(row + 1)"
    }
    func changeSpeed(_ value: Double) {
        guard [1.0, 3, 10, 20].contains(value) else { return }
        speed = value
        if running || replaying { nextBoundary = uptime() + 1 / speed }
    }
    func tick() {
        guard !loading, running || replaying, let boundary = nextBoundary else { return }
        let now = uptime()
        guard now.isFinite, now >= boundary else { return }
        nextBoundary = now + 1 / speed
        if running {
            advance(pulse: pulseQueued)
            if frames.count % 30 == 0 || !running { saveCurrent() }
        } else if replaying {
            row = min(row + 1, max(0, frames.count - 1))
            if row >= frames.count - 1 { pauseClock(); status = "Replay complete" }
        }
    }
    func leave() {
        pauseClock(); cancelLoading(); saveCurrent()
        status = frames.isEmpty ? "Ready · send a pulse or take one step." : "Paused · recorded steps retained"
    }
    private func pauseClock() { running = false; replaying = false; nextBoundary = nil }
    private func advance(pulse: Bool) {
        guard !atLimit, var engine else { pauseClock(); status = "1,800 steps recorded · reset to start another exploration."; return }
        do {
            let frame = try engine.advance(controls: controls, pulse: pulse)
            self.engine = engine; frames.append(frame); row = frames.count - 1
            pulseQueued = false; error = nil
            status = running ? "Running · \(frames.count) recorded steps" : "Step \(frame.step) recorded"
            if atLimit { pauseClock(); status = "1,800 steps recorded · reset to start another exploration." }
        } catch { pauseClock(); self.error = error.localizedDescription; status = "Step could not be recorded · previous state retained" }
    }

    func open(_ url: URL) {
        pauseClock(); saveCurrent(); cancelLoading()
        generation = UUID(); let id = generation
        loading = true; error = nil; status = "Verifying recorded steps…"
        let loader = recordLoader
        let worker = Task.detached(priority: .userInitiated) {
            let record = try await loader(url)
            try Task.checkCancellation()
            let engine = try ExplorationEngine(record: record)
            try Task.checkCancellation()
            return engine
        }
        loadWorker = worker
        loadTask = Task { [weak self] in
            let result = await worker.result
            guard let self, self.generation == id else { return }
            self.loading = false; self.loadTask = nil; self.loadWorker = nil
            do {
                let engine = try result.get()
                self.engine = engine; self.frames = engine.record.frames
                self.runID = UUID(); self.row = 0; self.selectedNode = 0; self.pulseQueued = false
                if let last = self.frames.last { self.controls = last.controls }
                self.seedText = String(engine.seed); self.source = url.path
                self.status = "Verified · \(self.frames.count) recorded steps. Replay or continue from the latest step."
            } catch {
                self.error = error.localizedDescription
                self.status = "Could not open file · previous exploration retained"
            }
        }
    }
    private func cancelLoading() {
        guard loading else { return }
        generation = UUID(); loadTask?.cancel(); loadWorker?.cancel()
        loading = false; loadTask = nil; loadWorker = nil
    }
    func chooseFile() {
        pauseClock(); saveCurrent(); cancelLoading()
        let panel = NSOpenPanel(); panel.allowedContentTypes = [.json]
        panel.canChooseDirectories = false; panel.allowsMultipleSelection = false
        panel.message = "Open a recorded Essentials exploration."
        if panel.runModal() == .OK, let url = panel.url { open(url) }
    }
    func export() {
        pauseClock(); saveCurrent(); cancelLoading()
        guard let record, !record.frames.isEmpty else { return }
        let panel = NSSavePanel(); panel.allowedContentTypes = [.json]
        panel.nameFieldStringValue = "essentials-exploration-\(record.seed).json"
        panel.directoryURL = outputDirectory
        if panel.runModal() == .OK, let url = panel.url {
            do { try requireResearchDestination(url); enqueueSave(record, to: url, identity: runID, isExport: true) }
            catch { self.error = error.localizedDescription }
        }
    }
    private func saveCurrent() {
        guard let record, !record.frames.isEmpty else { return }
        guard lastQueuedCount[runID] != record.frames.count else { return }
        retainedSnapshots[runID] = record
        guard let directory = outputDirectory else { saveIssue = "Exploration retained in memory · research output folder unavailable."; return }
        do {
            try requireResearchDestination(directory)
            let url = directory.appendingPathComponent("exploration-\(runID.uuidString).json")
            enqueueSave(record, to: url, identity: runID, isExport: false)
        } catch { saveIssue = "Exploration retained in memory. Saving failed: " + error.localizedDescription }
    }
    private func enqueueSave(_ record: ExplorationRecord, to url: URL, identity: UUID, isExport: Bool) {
        let previous = saveTail, writer = recordWriter, id = generation, count = record.frames.count
        if !isExport { lastQueuedCount[identity] = count }
        let worker = Task.detached(priority: .utility) {
            if let previous { _ = await previous.value }
            do { try await writer(record, url); return Result<Void, Error>.success(()) }
            catch { return .failure(error) }
        }
        saveTail = worker
        Task { [weak self] in
            let result = await worker.value
            guard let self else { return }
            switch result {
            case .success:
                if self.retainedSnapshots[identity]?.frames.count == count { self.retainedSnapshots.removeValue(forKey: identity) }
                if self.generation == id && self.runID == identity && self.frames.count == count && !self.loading {
                    self.source = url.path; self.saveIssue = nil
                    if isExport && !self.running && !self.replaying { self.status = "Exported recorded exploration" }
                }
            case .failure(let failure):
                if self.lastQueuedCount[identity] == count { self.lastQueuedCount.removeValue(forKey: identity) }
                self.saveIssue = "A recorded exploration remains in memory. Saving failed: " + failure.localizedDescription
            }
        }
    }
    private var outputDirectory: URL? { workspaceURL?.appendingPathComponent("research/outputs/essentials", isDirectory: true) }
    private func requireResearchDestination(_ url: URL) throws {
        guard let workspaceURL else { throw SurfaceRenderError("The research workspace location is unavailable in this package.") }
        let root = workspaceURL.resolvingSymlinksInPath().standardizedFileURL.path
        let target = url.resolvingSymlinksInPath().standardizedFileURL.path
        guard target.hasPrefix(root + "/") else { throw SurfaceRenderError("Save this exploration inside the research workspace. Its live sibling projects are read-only.") }
    }
    private static var packagedWorkspace: URL? {
        guard let file = Bundle.module.url(forResource: "essentials-workspace", withExtension: "txt")
            ?? Bundle.module.url(forResource: "essentials-workspace", withExtension: "txt", subdirectory: "Resources"),
              let text = try? String(contentsOf: file, encoding: .utf8) else { return nil }
        return URL(fileURLWithPath: text.trimmingCharacters(in: .whitespacesAndNewlines), isDirectory: true)
    }
}
