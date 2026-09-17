import SwiftUI
import EssentialsCore

@MainActor final class GuidedTourModel: ObservableObject {
    @Published private(set) var catalog: GuidedLessonCatalog?
    @Published private(set) var source: GuidedExampleSource = .scripted
    @Published private(set) var error: String?
    private var didStart = false
    private let defaults: UserDefaults
    private var catalogDirectory: URL?
    init(defaults: UserDefaults? = nil) {
        let preferences = defaults ?? ScopePreferences.store
        self.defaults = preferences
        if let saved = preferences.string(forKey: "guided.source"), let value = GuidedExampleSource(rawValue: saved) { source = value }
        do {
            guard let url = Bundle.module.url(forResource: "guided-lessons", withExtension: "json")
                ?? Bundle.module.url(forResource: "guided-lessons", withExtension: "json", subdirectory: "Resources") else {
                throw SurfaceRenderError("The packaged guided lesson catalog is unavailable.")
            }
            catalog = try GuidedLessonCatalog.read(from: url); catalogDirectory = url.deletingLastPathComponent()
        } catch { self.error = error.localizedDescription }
    }
    func lesson(_ stage: ActionStage) -> GuidedLesson? { catalog?.lessons.first { $0.stage == stage.rawValue } }
    func start(_ model: ActionComparisonViewModel) {
        guard !didStart else { return }; didStart = true
        resume(model)
    }
    func resume(_ model: ActionComparisonViewModel) {
        didStart = true
        let stage = ActionStage(rawValue: defaults.integer(forKey: "guided.stage")) ?? .minimal
        let row = max(0, defaults.integer(forKey: "guided.row"))
        open(stage, model: model, row: row)
    }
    func open(_ stage: ActionStage, model: ActionComparisonViewModel, row: Int = 0) {
        guard let lesson = lesson(stage), let directory = catalogDirectory else { return }
        // Early stages have no model-written alternative. Remember the preference
        // for the next journal-bearing stage without mislabeling this recording.
        guard let file = lesson.file(for: source) else { error = "This lesson has no recorded model example."; return }
        model.open(directory.appendingPathComponent(file), initialRow: row)
        defaults.set(stage.rawValue, forKey: "guided.stage")
        defaults.set(row, forKey: "guided.row")
    }
    func choose(_ value: GuidedExampleSource, model: ActionComparisonViewModel) {
        guard source != value else { return }
        source = value; defaults.set(value.rawValue, forKey: "guided.source")
        open(model.stage, model: model)
    }
    func remember(_ model: ActionComparisonViewModel) {
        guard didStart, !model.loading, matches(model) else { return }
        defaults.set(model.stage.rawValue, forKey: "guided.stage")
        defaults.set(model.row, forKey: "guided.row")
    }
    func matches(_ model: ActionComparisonViewModel) -> Bool {
        guard model.comparisonKind == .components, let lesson = lesson(model.stage),
              let directory = catalogDirectory, let file = lesson.file(for: source) else { return false }
        return model.record != nil && URL(fileURLWithPath: model.source).standardizedFileURL == directory.appendingPathComponent(file).standardizedFileURL
    }
    func nextCheckpoint(_ model: ActionComparisonViewModel) -> Int? {
        lesson(model.stage)?.checkpoints.first { $0 > (model.rightFrame?.step ?? 0) && $0 <= model.framesCount }
    }
    func continueLesson(_ model: ActionComparisonViewModel) {
        if let step = nextCheckpoint(model) { model.scrub(Double(step - 1)) }
        else if let next = ActionStage(rawValue: model.stage.rawValue + 1) { open(next, model: model) }
    }
}
