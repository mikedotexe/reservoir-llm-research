import SwiftUI
import UniformTypeIdentifiers

private actor NativeActionFileReader {
    func read(_ url: URL) throws -> NativeActionResponse { try NativeActionResponse.read(url: url) }
}

@MainActor
private final class NativeActionFileMonitor: ObservableObject {
    @Published var evidence: NativeActionResponse?
    @Published var path: URL?
    @Published var following = false
    @Published var status = "Choose a native rehearsal receipt file."
    @Published var error: String?
    private let reader = NativeActionFileReader()
    private var task: Task<Void, Never>?
    private var generation = UUID()

    func open(_ url: URL, follow: Bool = false) {
        stop()
        if path != url { evidence = nil }
        path = url; following = follow; error = nil
        let run = UUID(); generation = run
        status = "Reading native receipts…"
        task = Task { [weak self, reader] in
            repeat {
                let result: Result<NativeActionResponse, Error>
                do { result = .success(try await reader.read(url)) } catch { result = .failure(error) }
                guard let self, self.generation == run, !Task.isCancelled else { return }
                do {
                    let next = try result.get()
                    if let previous = self.evidence { try next.validateReplacement(of: previous) }
                    let unchanged = self.evidence?.fileSHA256 == next.fileSHA256
                    if !unchanged { self.evidence = next }
                    self.error = nil
                    self.status = follow ? (unchanged ? "Waiting for the next atomic receipt bundle" : "Following native rehearsal receipts") : "Imported native rehearsal receipts"
                } catch {
                    self.error = error.localizedDescription
                    self.status = self.evidence == nil ? "Receipt source unavailable" : "Source unavailable · retaining the previous bundle"
                }
                if !follow { return }
                do { try await Task.sleep(for: .seconds(2)) } catch { return }
            } while !Task.isCancelled
        }
    }
    func stop() { generation = UUID(); task?.cancel(); task = nil; following = false }
    func choose() {
        let panel = NSOpenPanel(); panel.allowedContentTypes = [.json]; panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false; panel.message = "Choose an isolated native rehearsal response bundle. This app only reads the file."
        if panel.runModal() == .OK, let url = panel.url { open(url) }
    }
    func loadExampleIfPresent() {
        guard path == nil else { return }
        if let url = Bundle.module.url(forResource: "native-action-response", withExtension: "json")
            ?? Bundle.module.url(forResource: "native-action-response", withExtension: "json", subdirectory: "Resources") { open(url) }
    }
}

struct StateResponseExperience: View {
    @State private var native = true
    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("Response source").font(.caption).foregroundStyle(.secondary)
                Picker("Response source", selection: $native) {
                    Text("Native action receipts").tag(true)
                    Text("esn-divide simulation").tag(false)
                }.pickerStyle(.segmented).labelsHidden().frame(width: 380)
                Spacer()
                Text(native ? "Isolated native rehearsal" : "Separate simulated parent").font(.caption).foregroundStyle(.secondary)
            }.padding(.horizontal, 20).padding(.vertical, 10)
            Divider()
            if native { NativeActionResponseExperience() } else { SimulationStateResponseExperience() }
        }
    }
}

private enum NativeActionField: String, CaseIterable, Identifiable {
    case delta = "Action difference", before = "Ordinary step", after = "Applied result"
    var id: Self { self }
    func values(_ frame: NativeActionResponse.Receipt) -> [Double] {
        switch self { case .delta: (frame.delta ?? []).map(Double.init)
        case .before: (frame.before ?? []).map(Double.init)
        case .after: (frame.after ?? []).map(Double.init) }
    }
}

private struct NativeActionResponseExperience: View {
    @StateObject private var monitor = NativeActionFileMonitor()
    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 12) {
                Button("Open receipt file…") { monitor.choose() }
                Toggle("Follow receipt file", isOn: Binding(get: { monitor.following }, set: { follow in
                    if let url = monitor.path { monitor.open(url, follow: follow) }
                })).toggleStyle(.switch).controlSize(.small).disabled(monitor.path == nil)
                Spacer()
                Text(monitor.status).font(.caption).foregroundStyle(.secondary).lineLimit(2)
                    .help(monitor.path?.path ?? "No receipt file selected")
            }.padding(.horizontal, 20).padding(.top, 12)
            if let error = monitor.error { Text(error).font(.caption).foregroundStyle(.orange).textSelection(.enabled).padding(.horizontal, 20).padding(.top, 6) }
            if let evidence = monitor.evidence {
                if evidence.frames.isEmpty {
                    ContentUnavailableView("No applied state boundary", systemImage: "clock",
                        description: Text("This bundle contains \(evidence.receipts.count) admission or terminal events. These events do not establish a state change."))
                    NativeActionEvents(receipts: evidence.receipts).padding(20)
                } else {
                    NativeActionLoadedExperience(evidence: evidence, following: monitor.following, sourceError: monitor.error != nil)
                        .id(evidence.fileSHA256)
                }
            } else {
                ContentUnavailableView("Native action receipts", systemImage: "arrow.triangle.branch",
                    description: Text("Open a completed native rehearsal bundle to inspect the ordinary step, actual applied result and exact immediate difference on the GPU surface."))
            }
        }.task { monitor.loadExampleIfPresent() }.onDisappear { monitor.stop() }
    }
}

private struct NativeActionLoadedExperience: View {
    let evidence: NativeActionResponse
    let following: Bool
    let sourceError: Bool
    @State private var row = 0
    @State private var field: NativeActionField = .delta
    @State private var selectedNode = 0
    @State private var playing = false
    @State private var replayClock = ReplayClock()
    @State private var metrics: StateSurfaceMetrics?
    private let pulse = Timer.publish(every: 1.0 / 30, on: .main, in: .common).autoconnect()
    private var frame: NativeActionResponse.Receipt { evidence.frames[min(row, evidence.frames.count - 1)] }
    private var scale: Double { field == .delta ? evidence.deltaScale : 1 }
    private var values: [Double] { field.values(frame) }
    var body: some View {
        HStack(spacing: 0) {
            main.padding(20).frame(maxWidth: .infinity, maxHeight: .infinity)
            Divider()
            ScrollView { inspector.padding(20) }.frame(width: 315)
        }.onAppear { if following { row = evidence.frames.count - 1 } }
        .onDisappear { playing = false }
        .onChange(of: following) { _, value in if value { playing = false; row = evidence.frames.count - 1 } }
        .onReceive(pulse) { _ in
            guard playing else { return }
            row = min(evidence.frames.count - 1, Int(replayClock.advance(uptime: ProcessInfo.processInfo.systemUptime, rate: 3)))
            if row == evidence.frames.count - 1 { playing = false }
        }
    }
    private var main: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    caption("MINIME NATIVE ESN · ISOLATED REHEARSAL")
                    Text("An action, at its actual boundary").font(.title2.weight(.medium))
                    Text("Ordinary step → applied result · immediate observed difference")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
            }
            Picker("Surface", selection: $field) { ForEach(NativeActionField.allCases) { Text($0.rawValue).tag($0) } }
                .pickerStyle(.segmented).labelsHidden().accessibilityLabel("Native action surface field")
            ZStack(alignment: .bottomLeading) {
                StateSurfaceScene(input: StateSurfaceRenderInput(values: values, lower: -scale, upper: scale,
                    fillPct: 68, relief: 0.28, cutaway: false, selectedNode: selectedNode),
                    accessibilitySubject: "isolated native Minime action rehearsal",
                    onSelect: { selectedNode = $0 }, onMetrics: { metrics = $0 })
                    .accessibilityLabel("Native \(field.rawValue) surface, successful step \(frame.successfulStepId!). No measured fill.")
                VStack(alignment: .leading, spacing: 4) {
                    Text("Successful native step \(frame.successfulStepId!) · pulse \(frame.pulseIndex!) · \(frame.status)")
                    Text("Fixed 68% preview size · fill was not measured").foregroundStyle(.secondary)
                    Text("128 original coordinates · fixed drawing map · no PCA join").foregroundStyle(.secondary)
                    if sourceError { Text("Retained bundle · source unavailable").foregroundStyle(.orange) }
                }.font(.caption).padding(12).background(.black.opacity(0.7), in: RoundedRectangle(cornerRadius: 8))
                    .padding(12).allowsHitTesting(false)
            }.frame(minHeight: 260, maxHeight: .infinity).clipShape(RoundedRectangle(cornerRadius: 12))
            legend
            HStack {
                Button {
                    if playing { playing = false } else {
                        if row == evidence.frames.count - 1 { row = 0 }
                        replayClock.start(at: Double(row), uptime: ProcessInfo.processInfo.systemUptime); playing = true
                    }
                } label: { Label(playing ? "Pause" : "Inspect sequence", systemImage: playing ? "pause.fill" : "play.fill") }
                    .disabled(following || evidence.frames.count < 2)
                Text("Pulse receipt \(row + 1) / \(evidence.frames.count)").monospacedDigit()
                Spacer(); Text("3 receipts / playback sec").font(.caption2).foregroundStyle(.secondary)
            }
            if evidence.frames.count > 1 {
                Slider(value: Binding(get: { Double(row) }, set: { row = Int($0); playing = false }),
                    in: 0...Double(evidence.frames.count - 1), step: 1).disabled(following)
                    .accessibilityLabel("Raw native pulse receipt")
            }
            NativeActionSizePlot(frames: evidence.frames, selected: row).frame(height: 80)
            Text("Raw action boundaries, no easing. Supplied rehearsal clocks and playback seconds do not measure recovery time.")
                .font(.caption).foregroundStyle(.secondary)
        }
    }
    private var inspector: some View {
        VStack(alignment: .leading, spacing: 13) {
            caption("REQUESTED AND APPLIED")
            Text(frame.patternId).font(.headline)
            info("Requested signed amount", signed(Double(frame.requestedAmount!)))
            info("Fraction of request applied", String(format: "%.6g", frame.attenuation!))
            info("Actual immediate L2 change", number(frame.actualL2!))
            info("Largest coordinate change", number(Double(frame.maxAbsDelta!)))
            info("Clipped / attenuated", frame.clipped ? "Yes" : "No")
            info("Effective leak at this step", number(Double(frame.effectiveLeak!)))
            info("Application boundary wait", "\(frame.boundaryWaitUs!) μs")
            Text("Ordinary is this same step after its usual update, noise and clipping. Applied is the immediate result of this action. Their difference does not measure a no-action counterfactual or the later response.")
                .font(.caption).foregroundStyle(.secondary)
            Divider(); caption("EXACT COORDINATE")
            HStack {
                Text("Coordinate \(selectedNode)").font(.headline).monospacedDigit(); Spacer()
                Stepper("Coordinate", value: $selectedNode, in: 0...127).labelsHidden()
            }
            info("Ordinary step", signed(Double(frame.before![selectedNode])))
            info("Applied result", signed(Double(frame.after![selectedNode])))
            info("Float32 action difference", signed(Double(frame.delta![selectedNode])))
            info("Actual step noise", signed(Double(frame.realizedNoise![selectedNode])))
            info("Requested direction weight", signed(Double(frame.direction[selectedNode])))
            nodeGrid
            Text("The GPU surface blends fixed sites. Select a site or square for its original value; neighboring patches do not imply network connections.")
                .font(.caption).foregroundStyle(.secondary)
            Divider(); caption("SUCCESSFUL STEP IDENTITY")
            info("Step / pulse offset", "\(frame.successfulStepId!) / \(frame.successOffset!)")
            info("Supplied rehearsal clock · ms", "\(frame.observedAtUnixMs)")
            Text("Session\n\(frame.identity.engineSessionId)\nModel\n\(frame.identity.modelId)\nNode layout\n\(frame.identity.nodeLayoutId)\nCommand\n\(frame.commandId)\nIntent\n\(frame.intentId)")
                .font(.system(size: 9, design: .monospaced)).textSelection(.enabled)
            Divider(); caption("SOURCE AND EVENTS")
            Text("Isolated native rehearsal, with no running being. The file's source hashes are producer declarations; the viewer validates structure and numerical consistency.")
                .font(.caption).foregroundStyle(.secondary)
            NativeActionEvents(receipts: evidence.receipts)
            Text("Imported file SHA-256\n\(evidence.fileSHA256)\n\nPattern SHA-256\n\(frame.patternSha256)\n\n" + evidence.sourceHashes.sorted { $0.key < $1.key }.map { "\($0.key)\n\($0.value)" }.joined(separator: "\n\n"))
                .font(.system(size: 9, design: .monospaced)).foregroundStyle(.secondary).textSelection(.enabled)
            if let fallback = metrics?.fallback { Text(fallback).font(.caption).foregroundStyle(.orange) }
        }
    }
    private var legend: some View {
        VStack(spacing: 3) {
            LinearGradient(colors: [color(-scale), color(0), color(scale)], startPoint: .leading, endPoint: .trailing)
                .frame(height: 6).clipShape(Capsule())
            HStack {
                Text(signed(-scale)); Spacer()
                Text(field == .delta ? "Fixed to largest |difference| in this complete bundle" : "Signed state scale fixed at −1…1")
                Spacer(); Text(signed(scale))
            }.font(.caption2).foregroundStyle(.secondary)
        }
    }
    private var nodeGrid: some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 2), count: 16), spacing: 2) {
            ForEach(0..<128) { index in
                Button { selectedNode = index } label: {
                    Rectangle().fill(color(values[index])).frame(height: 11)
                        .overlay(Rectangle().stroke(index == selectedNode ? Color.white : .clear, lineWidth: 1.5))
                }.buttonStyle(.plain).help("Coordinate \(index) · \(signed(values[index]))")
                    .accessibilityLabel("Coordinate \(index), \(signed(values[index]))")
            }
        }
    }
    private func color(_ value: Double) -> Color {
        let t = min(1, max(0, (value + scale) / (2 * scale)))
        let low = SIMD3<Double>(0.52, 0.30, 0.92), middle = SIMD3<Double>(0.10, 0.17, 0.23), high = SIMD3<Double>(0.14, 0.91, 0.79)
        let rgb = t < 0.5 ? low * (1 - 2 * t) + middle * (2 * t) : middle * (2 - 2 * t) + high * (2 * t - 1)
        return Color(.sRGBLinear, red: rgb.x, green: rgb.y, blue: rgb.z, opacity: 1)
    }
    private func caption(_ text: String) -> some View { Text(text).font(.system(size: 10, weight: .medium)).tracking(1).foregroundStyle(.secondary) }
    private func signed(_ value: Double) -> String { String(format: "%+.9g", value) }
    private func number(_ value: Double) -> String { String(format: "%.9g", value) }
    private func info(_ title: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 3) { Text(title).font(.caption).foregroundStyle(.secondary); Text(value).font(.system(.body, design: .monospaced)) }
    }
}

private struct NativeActionEvents: View {
    let receipts: [NativeActionResponse.Receipt]
    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            ForEach(Array(receipts.filter { !$0.hasState }.enumerated()), id: \.offset) { _, receipt in
                Text("\(receipt.status) · \(receipt.commandId)" + (receipt.reason.map { "\n\($0)" } ?? ""))
                    .font(.caption).foregroundStyle(receipt.status == "completed" ? Color.secondary : Color.orange).textSelection(.enabled)
            }
        }
    }
}

private struct NativeActionSizePlot: View {
    let frames: [NativeActionResponse.Receipt]
    let selected: Int
    private var maximum: Double { max(1e-9, frames.compactMap(\.actualL2).max() ?? 0) }
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Immediate action size per pulse · L2 · successful native step").font(.caption)
            Canvas { context, size in
                let first = frames.first!.successfulStepId!, span = max(1, frames.last!.successfulStepId! - first)
                for (index, frame) in frames.enumerated() {
                    let x = 5 + Double(frame.successfulStepId! - first) / Double(span) * max(1, size.width - 10)
                    let y = max(1, size.height - 3) * (1 - frame.actualL2! / maximum)
                    var bar = Path(); bar.move(to: CGPoint(x: x, y: size.height)); bar.addLine(to: CGPoint(x: x, y: y))
                    context.stroke(bar, with: .color(index == selected ? .white : .cyan.opacity(0.6)), lineWidth: 2)
                }
            }
            HStack { Text("\(frames.first!.successfulStepId!)"); Spacer(); Text("\(frames.last!.successfulStepId!)") }
                .font(.caption2).foregroundStyle(.secondary)
        }.accessibilityElement(children: .ignore)
            .accessibilityLabel("Immediate action size at successful step \(frames[selected].successfulStepId!): \(frames[selected].actualL2!). Bars are action boundaries, not a recovery trajectory.")
    }
}
