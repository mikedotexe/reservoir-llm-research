import SwiftUI
import UniformTypeIdentifiers
import EssentialsCore

@MainActor final class RegulationExampleViewModel: ObservableObject {
    @Published private(set) var record: RegulationExampleRecord?
    @Published var row = 0
    @Published private(set) var loading = false
    @Published private(set) var playing = false
    @Published private(set) var saving = false
    @Published private(set) var error: String?
    @Published private(set) var savedLocation: String?
    private var loadedURL: URL?
    private var loadIdentity = UUID()
    var frame: RegulationExampleFrame? { record.flatMap { $0.frames.indices.contains(row) ? $0.frames[row] : nil } }
    var prefix: [RegulationExampleFrame] { record.map { Array($0.frames.prefix(row + 1)) } ?? [] }
    var completeWindowVisible: Bool { frame?.step == record?.specification.evaluationLastStep && record != nil }
    func open(_ supplied: URL?) {
        let url = supplied ?? Bundle.module.url(forResource: "example-regulation-controller", withExtension: "json")
            ?? Bundle.module.url(forResource: "example-regulation-controller", withExtension: "json", subdirectory: "Resources")
        guard let url else { error = "The packaged controller example is unavailable."; return }
        guard loadedURL != url else { return }
        let identity = UUID(); loadIdentity = identity; loading = true; playing = false; error = nil
        Task {
            do {
                let value = try await Task.detached(priority: .userInitiated) {
                    let value = try RegulationExampleRecord.read(from: url)
                    _ = try value.verify(); return value
                }.value
                guard loadIdentity == identity else { return }
                record = value; row = 0; loadedURL = url; loading = false
            } catch {
                guard loadIdentity == identity else { return }
                self.error = error.localizedDescription; loading = false
            }
        }
    }
    func play() { guard let record, !record.frames.isEmpty else { return }; if row >= record.frames.count - 1 { row = 0 }; playing.toggle() }
    func stop() { playing = false }
    func step() { playing = false; row = min(row + 1, max(0, (record?.frames.count ?? 1) - 1)) }
    func tick() {
        guard playing, let record else { return }
        row = min(row + 1, record.frames.count - 1)
        if row == record.frames.count - 1 { playing = false }
    }
    func scrub(_ value: Double) { playing = false; row = min(max(0, Int(value)), max(0, (record?.frames.count ?? 1) - 1)) }
    func nextCheckpoint() { if let step = [30, 300, 301, 600].first(where: { $0 > row + 1 }) { scrub(Double(step - 1)) } }
    func saveCopy() {
        guard let record else { return }
        let destination = ExperimentStore.defaultRoot.appendingPathComponent("Regulation", isDirectory: true)
            .appendingPathComponent("controller-\(UUID().uuidString).json")
        persist(record, to: destination)
    }
    func export() {
        stop(); guard let record else { return }
        let panel = NSSavePanel(); panel.allowedContentTypes = [.json]; panel.nameFieldStringValue = "reservoir-controller-example.json"
        if panel.runModal() == .OK, let url = panel.url { persist(record, to: url) }
    }
    private func persist(_ value: RegulationExampleRecord, to url: URL) {
        guard !saving else { return }; saving = true
        Task {
            do {
                try await Task.detached(priority: .utility) {
                    try ExperimentStore.requireLocalDestination(url)
                    try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
                    try value.write(to: url)
                }.value
                error = nil; savedLocation = url.path
            } catch { self.error = "The verified record is still open. Saving failed: " + error.localizedDescription }
            saving = false
        }
    }
}

struct RegulationExampleView: View {
    var url: URL? = nil
    var onClose: (() -> Void)? = nil
    @StateObject private var model = RegulationExampleViewModel()
    private let pulse = Timer.publish(every: 0.05, on: .main, in: .common).autoconnect()
    private let baseline = Color(red: 0.91, green: 0.68, blue: 0.40)
    private let regulated = Color(red: 0.35, green: 0.88, blue: 0.74)
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Can regulation reduce target error?").font(.title2.weight(.medium))
                    Text("Scripted mechanism example · separate from A–H · no journal or model calls")
                        .font(.caption).foregroundStyle(regulated)
                }
                Spacer()
                Button("Save copy") { model.saveCopy() }.disabled(model.record == nil || model.saving)
                Button("Export…") { model.export() }.disabled(model.record == nil || model.saving)
                if let onClose { Button("Done") { model.stop(); onClose() } }
            }
            if model.loading { ProgressView("Verifying the recorded mechanism…") }
            if model.saving { ProgressView("Saving the verified example…").font(.caption) }
            if let error = model.error {
                HStack {
                    Text(error).font(.caption).foregroundStyle(.orange).textSelection(.enabled)
                    if model.record != nil { Button("Retry save copy") { model.saveCopy() }.disabled(model.saving) }
                }
            }
            if let record = model.record {
                ScrollView {
                    VStack(alignment: .leading, spacing: 14) {
                        Text(record.specification.question).font(.headline)
                        Text("Both sensory fields receive the same seeded 66-coordinate input for 600 steps. Only the regulated field changes its retention.")
                            .font(.callout)
                        Text("Expected: lower mean absolute distance from 68% fill over the declared evaluation window, steps 301–600.")
                            .font(.caption)
                        summary(record)
                        GuidedLineTrace(title: "Fill · target 68%, deadband ±4 percentage points", series: [
                            .init(title: "Fixed retention", color: baseline, values: model.prefix.map { $0.baseline.fillPercent }),
                            .init(title: "Regulated", color: regulated, values: model.prefix.map { $0.regulated.fillPercent })], lower: 0, upper: 100, reference: 68)
                            .frame(height: 180)
                        GuidedLineTrace(title: "Retention used for each update", series: [
                            .init(title: "Fixed retention", color: baseline, values: model.prefix.map { $0.baseline.retentionUsed }),
                            .init(title: "Regulated", color: regulated, values: model.prefix.map { $0.regulated.retentionUsed })], lower: 0.82, upper: 0.995)
                            .frame(height: 135)
                        if let frame = model.frame {
                            HStack {
                                measurement("Fixed retention", fill: frame.baseline.fillPercent, retention: frame.baseline.retentionUsed)
                                measurement("Regulated", fill: frame.regulated.fillPercent, retention: frame.regulated.retentionUsed)
                                Spacer()
                                if let control = frame.regulated.control {
                                    Text("Next retention\n\(String(format: "%.5f", control.appliedRetention))").font(.caption.monospacedDigit())
                                }
                            }
                            DisclosureGroup("Exact common input at step \(frame.step)") {
                                Text(frame.input.enumerated().map { "[\($0.offset)] " + String(format: "%.17g", $0.element) }.joined(separator: "\n"))
                                    .font(.caption.monospaced()).textSelection(.enabled)
                            }.font(.caption)
                        }
                        Text("Interpretation: " + record.specification.alternativeExplanation).font(.caption).foregroundStyle(.secondary)
                        DisclosureGroup("Protocol and provenance") {
                            Text("Fixture: \(record.specification.fixture)\nInput seed: \(record.specification.inputSeed) · Field seed: \(record.specification.fieldSeed)\n" + record.specification.stoppingPoint)
                                .font(.caption).textSelection(.enabled)
                            if let saved = model.savedLocation { Text("Saved copy: " + saved).font(.caption2).textSelection(.enabled) }
                        }.font(.caption)
                    }
                }
                HStack {
                    Button(model.playing ? "Pause" : "Play") { model.play() }
                    Button("Step") { model.step() }.disabled(model.row >= record.frames.count - 1)
                    Button("Continue to checkpoint") { model.nextCheckpoint() }.disabled(model.row >= record.frames.count - 1)
                    Button("Replay") { model.scrub(0); model.play() }
                    Slider(value: Binding(get: { Double(model.row) }, set: model.scrub), in: 0...Double(max(1, record.frames.count - 1)), step: 1)
                        .accessibilityLabel("Controller example cursor")
                    Text("Step \(model.row + 1) / \(record.frames.count)").font(.caption.monospacedDigit())
                }.font(.caption)
            }
        }.padding(22).frame(minWidth: 850, minHeight: 760)
            .task(id: url) { model.open(url) }.onReceive(pulse) { _ in model.tick() }.onDisappear { model.stop() }
    }
    private func summary(_ record: RegulationExampleRecord) -> some View {
        Group {
            if let result = RegulationWindowEvidence.evaluate(record, cursorStep: model.frame?.step ?? 0) {
                Text("\(result.isComplete ? "Observed complete window" : "Partial window, not a final result"): mean absolute target error \(String(format: "%.3f", result.baselineMeanAbsoluteError)) points with fixed retention and \(String(format: "%.3f", result.regulatedMeanAbsoluteError)) with regulation (\(result.count) paired steps, \(result.firstStep)–\(result.lastStep)).")
                    .foregroundStyle(regulated)
            } else {
                Text("Not reached yet: the whole-window result becomes available at step 600. Current measurements are shown below.").foregroundStyle(.secondary)
            }
        }.font(.callout).padding(12).frame(maxWidth: .infinity, alignment: .leading)
            .background(regulated.opacity(0.08), in: RoundedRectangle(cornerRadius: 8))
    }
    private func measurement(_ title: String, fill: Double, retention: Double) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title).font(.caption.weight(.semibold))
            Text("Fill \(String(format: "%.2f", fill))% · error \(String(format: "%.2f", abs(fill - 68))) points\nRetention \(String(format: "%.5f", retention))")
                .font(.caption.monospacedDigit())
        }.frame(maxWidth: .infinity, alignment: .leading)
    }
}
