import SwiftUI
import EssentialsCore

struct EssentialsExperience: View {
    @ObservedObject var model: EssentialsViewModel
    @State private var cutaway = false
    @State private var presentation: StateSurfacePresentation = .topography
    @State private var topographyHeight = 0.16
    @State private var surfaceMetrics: StateSurfaceMetrics?
    private let pulse = Timer.publish(every: 1.0 / 30, on: .main, in: .common).autoconnect()
    private let accent = Color(red: 0.35, green: 0.88, blue: 0.74)
    private var selectedValue: Double { model.state[min(model.selectedNode, model.state.count - 1)] }

    var body: some View {
        // The experiment fills its assigned window area. Changing measurements
        // must not feed back into NSHostingView's intrinsic window-size search.
        GeometryReader { geometry in
        HStack(spacing: 0) {
            stageSidebar.frame(width: 218)
            Divider()
            VStack(spacing: 0) {
                header
                Divider()
                HStack(spacing: 0) {
                    center.padding(20).frame(maxWidth: .infinity, maxHeight: .infinity)
                    Divider()
                    ScrollView { inspector.padding(18) }.frame(width: 306)
                }
            }
        }.frame(width: geometry.size.width, height: geometry.size.height)
        }
        .onReceive(pulse) { _ in model.tick() }
        .onDisappear { model.stop() }
    }

    private var stageSidebar: some View {
        VStack(alignment: .leading, spacing: 18) {
            VStack(alignment: .leading, spacing: 7) {
                Text("ESSENTIALS").font(.system(size: 21, weight: .medium, design: .rounded)).tracking(2)
                Text("Rebuild. Observe. Compare.").font(.caption).foregroundStyle(.secondary)
            }.padding(.bottom, 12)
            ForEach(EssentialsStage.allCases) { stage in
                Button { model.select(stage) } label: {
                    HStack(alignment: .top, spacing: 11) {
                        Text(String(stage.rawValue)).font(.system(.body, design: .monospaced).weight(.medium))
                            .frame(width: 27, height: 27)
                            .background(model.stage == stage ? accent.opacity(0.2) : .white.opacity(0.06), in: Circle())
                        VStack(alignment: .leading, spacing: 5) {
                            Text(stage.title.components(separatedBy: " · ").last ?? stage.title).font(.callout.weight(.medium))
                            Text(stageSubtitle(stage)).font(.caption2).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
                        }
                        Spacer(minLength: 0)
                    }.padding(10).frame(maxWidth: .infinity, alignment: .leading)
                        .background(model.stage == stage ? accent.opacity(0.10) : .clear, in: RoundedRectangle(cornerRadius: 9))
                        .foregroundStyle(model.stage == stage ? accent : .primary)
                }.buttonStyle(.plain).disabled(model.running)
            }
            Divider()
            VStack(alignment: .leading, spacing: 8) {
                eyebrow("SMALL MODEL, ORIGINAL LANES")
                Text("32 reservoir nodes\n32 sensory-field coordinates\n66 input coordinates").font(.caption).lineSpacing(5)
                Text("The two 32-dimensional spaces have different jobs.").font(.caption2).foregroundStyle(.secondary)
            }
            Spacer()
            Button { model.loadExample() } label: { Label("Open stage example", systemImage: "play.rectangle") }
                .font(.caption).disabled(model.running)
            Text("Examples use scripted replies. Local-model runs are configured separately.")
                .font(.caption2).foregroundStyle(.secondary)
        }.padding(18).background(Color.white.opacity(0.025))
    }

    private var header: some View {
        HStack(alignment: .top, spacing: 16) {
            VStack(alignment: .leading, spacing: 6) {
                Text("Stage \(model.stage.title)")
                    .font(.system(size: 23, weight: .medium))
                Text(model.stage.explanation).font(.callout).foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            Spacer(minLength: 8)
            VStack(alignment: .trailing, spacing: 8) {
                HStack {
                    Button("Open…") { model.chooseFile() }.disabled(model.running)
                    Button("Export…") { model.export() }.disabled(model.record == nil || model.running)
                }
                Text(model.record?.specification.language.backend == .ollama ? "LOCAL MODEL RUN" : "SCRIPTED / SYNTHETIC")
                    .font(.system(size: 9, weight: .medium)).tracking(1).foregroundStyle(accent)
            }
        }.padding(.horizontal, 22).padding(.vertical, 17)
    }

    private var center: some View {
        VStack(alignment: .leading, spacing: 12) {
            controls
            HStack(spacing: 8) {
                Circle().fill(model.running ? accent : Color.gray).frame(width: 5, height: 5)
                Text(model.status).font(.caption).foregroundStyle(.secondary).lineLimit(2)
                Spacer()
                if let frame = model.frame {
                    Text("Step \(frame.step) · \(number(frame.time, 2)) simulated s")
                        .font(.system(.caption, design: .monospaced))
                }
            }
            if let error = model.error {
                Text(error).font(.caption).foregroundStyle(.orange).textSelection(.enabled)
                    .fixedSize(horizontal: false, vertical: true)
            }
            ZStack(alignment: .topLeading) {
                StateSurfaceScene(input: StateSurfaceRenderInput(
                    values: model.state, lower: -1, upper: 1, fillPct: 100,
                    relief: presentation == .topography ? topographyHeight : 0.10,
                    cutaway: cutaway, selectedNode: model.selectedNode,
                    flatLighting: presentation == .surface, presentation: presentation),
                    accessibilitySubject: "Essentials 32-node experimental reservoir",
                    onSelect: { model.selectedNode = $0 }, onMetrics: { if surfaceMetrics != $0 { surfaceMetrics = $0 } })
                VStack(alignment: .leading, spacing: 6) {
                    presentationControls
                    VStack(alignment: .leading, spacing: 4) {
                        Text(model.frame == nil ? "INITIAL STATE · READY TO RUN" : "ACTUAL RESERVOIR STATE")
                            .font(.system(size: 9, weight: .medium)).tracking(1.5)
                        Text(presentation == .topography
                             ? "State landscape · contours every 0.2"
                             : "Fixed display size · signed activation")
                            .font(.caption2).foregroundStyle(.secondary)
                    }.allowsHitTesting(false)
                }.padding(14)
                VStack {
                    Spacer()
                    HStack {
                        Text(presentation == .topography ? "−1 · valley" : "−1").font(.caption2.monospacedDigit())
                        LinearGradient(colors: [Color(.sRGBLinear, red: 0.52, green: 0.30, blue: 0.92), Color(.sRGBLinear, red: 0.10, green: 0.17, blue: 0.23), Color(.sRGBLinear, red: 0.14, green: 0.91, blue: 0.79)], startPoint: .leading, endPoint: .trailing)
                            .frame(width: 105, height: 6).clipShape(Capsule())
                        Text(presentation == .topography ? "+1 · peak" : "+1").font(.caption2.monospacedDigit())
                        Spacer()
                        Toggle("Cutaway", isOn: $cutaway).font(.caption).toggleStyle(.checkbox)
                    }.padding(14)
                }
            }.frame(minHeight: 280).background(.black.opacity(0.2), in: RoundedRectangle(cornerRadius: 12))
                .clipShape(RoundedRectangle(cornerRadius: 12))
            if let fallback = surfaceMetrics?.fallback {
                Text(fallback).font(.caption2).foregroundStyle(.orange)
            }
            if model.stage != .reservoir { spectralBars }
            EssentialsTrace(frames: model.frames, selected: model.row, stage: model.stage).frame(height: 60)
            HStack {
                Button { model.replay() } label: {
                    Label(model.playing ? "Pause replay" : "Replay", systemImage: model.playing ? "pause.fill" : "play.fill")
                }.disabled(model.running || model.frames.isEmpty)
                Slider(value: Binding(get: { Double(model.row) }, set: { model.scrub($0) }),
                    in: 0...Double(max(1, model.frames.count - 1)), step: 1)
                    .disabled(model.running || model.frames.count < 2).accessibilityLabel("Recorded step")
                Text("\(model.frames.isEmpty ? 0 : model.row + 1) / \(model.frames.count)")
                    .font(.caption.monospacedDigit()).frame(minWidth: 67, alignment: .trailing)
            }
            HStack(spacing: 7) {
                Text("Replay pace").font(.caption2).foregroundStyle(.secondary)
                ForEach([1.0, 5, 10, 20, 40], id: \.self) { speed in
                    Button("\(Int(speed))") { model.changeSpeed(speed) }
                        .buttonStyle(.plain).font(.caption2.monospacedDigit())
                        .padding(.horizontal, 8).padding(.vertical, 4)
                        .background(model.speed == speed ? accent.opacity(0.22) : .white.opacity(0.04), in: Capsule())
                }
                Text("steps / viewing second").font(.caption2).foregroundStyle(.secondary)
                Spacer()
            }
            Text(presentation == .topography
                 ? "Height and contours share the interpolated state field. This value map is not network wiring or physical shape."
                 : "Node positions identify coordinates. The surface between them is an interpolation.")
                .font(.caption2).foregroundStyle(.secondary)
        }
    }

    private var presentationControls: some View {
        HStack(spacing: 8) {
            Picker("State display", selection: $presentation) {
                Text("Surface").tag(StateSurfacePresentation.surface)
                Text("Topography").tag(StateSurfacePresentation.topography)
            }.pickerStyle(.segmented).labelsHidden().controlSize(.small).frame(width: 180)
            Spacer(minLength: 8)
            if presentation == .topography {
                Text("Height").font(.caption2).foregroundStyle(.secondary)
                Slider(value: $topographyHeight, in: 0...0.20)
                    .controlSize(.small).frame(width: 88)
                    .accessibilityLabel("Topography height exaggeration")
                    .help("Display exaggeration around a fixed neutral radius. Reservoir values stay unchanged. Contours remain at intervals of 0.2; the zero boundary is brighter.")
                Text(number(topographyHeight, 2)).font(.caption2.monospacedDigit())
                    .frame(width: 28, alignment: .trailing)
            }
        }
    }

    private var controls: some View {
        HStack(spacing: 9) {
            Button { model.run() } label: { Label("Run", systemImage: "play.fill") }
                .buttonStyle(.borderedProminent).tint(accent).foregroundStyle(.black).disabled(!model.canRun)
            Button { model.stop() } label: { Label("Stop", systemImage: "stop.fill") }.disabled(!model.running)
            Button("Reset") { model.reset() }.disabled(model.running)
            Spacer()
            if model.running { ProgressView().controlSize(.small) }
        }
    }

    private var spectralBars: some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack {
                eyebrow("SENSORY FIELD · LEADING 8 OF 32 MODES")
                Spacer()
                Text("Fixed scale 0–32").font(.caption2).foregroundStyle(.secondary)
            }
            HStack(alignment: .bottom, spacing: 8) {
                ForEach(0..<8, id: \.self) { index in
                    let value: Double? = model.frame?.spectral?.eigenvalues.indices.contains(index) == true
                        ? model.frame!.spectral!.eigenvalues[index] : nil
                    VStack(spacing: 3) {
                        Text(value.map { number($0, 2) } ?? "—").font(.system(size: 9, design: .monospaced)).foregroundStyle(.secondary)
                        ZStack(alignment: .bottom) {
                            RoundedRectangle(cornerRadius: 3).fill(.white.opacity(0.04))
                            RoundedRectangle(cornerRadius: 3).fill(accent.opacity(0.7))
                                .frame(height: max(0, min(32, value ?? 0)) / 32 * 38)
                        }.frame(height: 38)
                        Text("λ\(index + 1)").font(.caption2).foregroundStyle(.secondary)
                    }.frame(maxWidth: .infinity)
                }
            }
        }
    }

    private var inspector: some View {
        LazyVStack(alignment: .leading, spacing: 19) {
            VStack(alignment: .leading, spacing: 8) {
                eyebrow("EXACT COORDINATE")
                HStack(alignment: .firstTextBaseline) {
                    Text("Node \(model.selectedNode)").font(.headline)
                    Spacer()
                    Text(number(selectedValue, 6)).font(.system(.title3, design: .monospaced)).foregroundStyle(accent)
                }
                LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 3), count: 8), spacing: 4) {
                    ForEach(model.state.indices, id: \.self) { node in
                        Button { model.selectedNode = node } label: {
                            Text(String(node)).font(.system(size: 10, design: .monospaced))
                                .frame(maxWidth: .infinity).padding(.vertical, 5)
                                .background(node == model.selectedNode ? accent.opacity(0.3) : .white.opacity(0.05),
                                    in: RoundedRectangle(cornerRadius: 3))
                        }.buttonStyle(.plain).help("Node \(node): \(number(model.state[node], 8))")
                    }
                }
            }
            Divider()
            VStack(alignment: .leading, spacing: 9) {
                eyebrow("INPUT AT THIS STEP · RMS")
                ForEach(Array(zip(["Video · 0–7", "Audio · 8–15", "Aux · 16–17", "Semantic · 18–65"],
                    [0..<8, 8..<16, 16..<18, 18..<66])), id: \.0) { item in
                    metric(item.0, number(rms(model.frame?.input, range: item.1), 5))
                }
                if let frame = model.frame {
                    metric("Applied reply", frame.semanticTurnID.map { "Turn \($0)" } ?? "None")
                }
                DisclosureGroup("All 66 input values") {
                    Text((model.frame?.input ?? Array(repeating: 0, count: 66)).enumerated()
                        .map { "\($0.offset): \(number($0.element, 6))" }.joined(separator: "\n"))
                        .font(.system(.caption2, design: .monospaced)).textSelection(.enabled)
                }.font(.caption)
            }
            if model.stage != .reservoir {
                Divider()
                VStack(alignment: .leading, spacing: 9) {
                    eyebrow("SENSORY MEASUREMENTS")
                    metric("Leading eigenvalue", model.frame?.spectral.map { number($0.eigenvalues.first ?? 0, 5) } ?? "Unavailable")
                    metric("Top-eight entropy", model.frame?.spectral.map { number($0.entropy, 5) } ?? "Unavailable")
                    metric("Head share of top eight", model.frame?.spectral.map { number($0.headShare * 100, 1) + "%" } ?? "Unavailable")
                    metric("Retention used", model.frame?.retentionUsed.map { number($0, 5) } ?? "Unavailable")
                    if model.stage == .regulation {
                        metric("Reduced active-mode fill", model.frame?.fillPercent.map { number($0, 2) + "%" } ?? "Unavailable")
                        Text("Fill uses all 32 sensory modes. This experiment has its own fill definition.")
                            .font(.caption2).foregroundStyle(.secondary)
                    }
                }
            }
            if model.stage == .regulation {
                Divider()
                VStack(alignment: .leading, spacing: 8) {
                    eyebrow("RETENTION CONTROLLER")
                    metric("Target / band", "68% / 64–72%")
                    if let control = model.frame?.control {
                        metric("Error", number(control.error, 5))
                        metric("Integral", number(control.integral, 5))
                        metric("Requested retention", number(control.requestedRetention, 5))
                        metric("Next-step retention", number(control.appliedRetention, 5))
                    } else { Text("Controller disabled or no step yet.").font(.caption).foregroundStyle(.secondary) }
                }
            }
            if model.stage.rawValue >= 2 {
                Divider()
                turnInspector
            }
            Divider()
            settings
            if !model.source.isEmpty {
                Divider()
                DisclosureGroup("Saved source") { Text(model.source).font(.caption2).textSelection(.enabled) }.font(.caption)
            }
        }
    }

    private var turnInspector: some View {
        VStack(alignment: .leading, spacing: 9) {
            eyebrow(model.stage == .spectralBridge ? "EXAMPLE TEXT → SEMANTIC INPUT" : "OBSERVATION → REPLY → FEEDBACK")
            if let turn = model.turn {
                metric("Turn / outcome", "\(turn.id) / \(turn.status.rawValue)")
                metric("Observation step", String(turn.observedStep))
                metric("Applied at step", turn.applicationStep.map(String.init) ?? "Not applied")
                metric("Provider model", turn.providerModel ?? turn.model ?? turn.backend)
                metric("Stop reason", turn.stopReason ?? "Unavailable")
                if let count = turn.tokenCount { metric("Output tokens", String(count)) }
                DisclosureGroup(model.stage == .spectralBridge ? "Prepared example context" : "Exact supplied prompt") {
                    Text(turn.prompt).font(.caption2).textSelection(.enabled)
                }.font(.caption)
                DisclosureGroup("Complete reply") {
                    Text(turn.reply ?? turn.failure ?? "No completed reply").font(.caption2).textSelection(.enabled)
                }.font(.caption)
                if turn.reply == nil, let raw = turn.rawReply {
                    DisclosureGroup("Retained output · not applied") { Text(raw).font(.caption2).textSelection(.enabled) }.font(.caption)
                }
                DisclosureGroup("48 encoded feedback values") {
                    Text((turn.semanticVector ?? []).enumerated().map { "\($0.offset): \(number($0.element, 6))" }.joined(separator: "\n"))
                        .font(.system(.caption2, design: .monospaced)).textSelection(.enabled)
                }.font(.caption)
                Text("Embedding and narrative-embedding features are unavailable; coordinates 32–47 remain zero.")
                    .font(.caption2).foregroundStyle(.secondary)
            } else {
                Text(model.running ? "Turn records become available when the run stops. Inputs show any feedback already applied." : "Scrub beyond the first language boundary to inspect its prompt and reply.")
                    .font(.caption).foregroundStyle(.secondary)
            }
        }
    }

    private var settings: some View {
        VStack(alignment: .leading, spacing: 10) {
            eyebrow("NEXT RUN")
            HStack {
                Text("Seed").font(.caption); Spacer()
                TextField("Seed", text: $model.seedText).font(.caption.monospacedDigit()).frame(width: 133)
            }
            Picker("Steps", selection: $model.stepCount) {
                ForEach(Array(Set([90, 300, 900, 1800, model.stepCount])).sorted(), id: \.self) { Text(String($0)).tag($0) }
            }.font(.caption)
            Toggle("Seeded noise · ±0.02", isOn: $model.noiseEnabled).font(.caption)
            if model.stage == .regulation {
                Toggle("Enable regulation", isOn: $model.regulationEnabled).font(.caption)
                Text("Use the same seed and scripted replies for an on/off comparison.").font(.caption2).foregroundStyle(.secondary)
            }
            if model.stage.rawValue >= 3 {
                Picker("Voice", selection: $model.localModel) {
                    Text("Scripted replay").tag(false)
                    Text("Separate local Ollama").tag(true)
                }.font(.caption)
                if model.localModel {
                    TextField("Separate endpoint URL", text: $model.endpoint).font(.caption).textFieldStyle(.roundedBorder)
                    TextField("Local model name", text: $model.modelName).font(.caption).textFieldStyle(.roundedBorder)
                    Text("One voice · 256-token ceiling · 60-second deadline. Simulation waits for the complete reply.")
                        .font(.caption2).foregroundStyle(.secondary)
                }
            }
        }.disabled(model.running)
    }

    private func stageSubtitle(_ stage: EssentialsStage) -> String {
        switch stage {
        case .reservoir: "Input, recurrence, a lasting trace"
        case .spectralBridge: "A spectrum and a path for text"
        case .llmLoop: "One voice closes the loop"
        case .regulation: "See what the controller changes"
        }
    }
    private func eyebrow(_ text: String) -> some View {
        Text(text).font(.system(size: 9, weight: .medium)).tracking(1).foregroundStyle(.secondary)
    }
    private func metric(_ name: String, _ value: String) -> some View {
        HStack(alignment: .firstTextBaseline) {
            Text(name).font(.caption).foregroundStyle(.secondary)
            Spacer(minLength: 8)
            Text(value).font(.system(.caption, design: .monospaced)).textSelection(.enabled)
        }
    }
    private func number(_ value: Double, _ digits: Int) -> String { String(format: "%.*f", digits, value) }
    private func rms(_ values: [Double]?, range: Range<Int>) -> Double {
        guard let values, range.upperBound <= values.count else { return 0 }
        return sqrt(range.reduce(0) { $0 + values[$1] * values[$1] } / Double(range.count))
    }
}

private struct EssentialsTrace: View {
    let frames: [EssentialsFrame]
    let selected: Int
    let stage: EssentialsStage
    private var useFill: Bool { stage == .regulation }
    private var title: String {
        stage == .regulation ? "REDUCED ACTIVE-MODE FILL · 0–100%" :
            stage == .reservoir ? "RESERVOIR RMS · 0–1" : "TOP-EIGHT SPECTRAL ENTROPY · 0–1"
    }
    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(title)
                .font(.system(size: 9, weight: .medium)).tracking(1).foregroundStyle(.secondary)
            Canvas { context, size in
                if stage == .regulation {
                    let rect = CGRect(x: 0, y: size.height * 0.28, width: size.width, height: size.height * 0.08)
                    context.fill(Path(rect), with: .color(.green.opacity(0.13)))
                }
                guard frames.count > 1 else { return }
                var path = Path()
                for (index, frame) in frames.enumerated() {
                    let value = useFill ? (frame.fillPercent ?? 0) / 100
                        : stage == .reservoir ? sqrt(frame.state.reduce(0) { $0 + $1 * $1 } / Double(frame.state.count))
                        : frame.spectral?.entropy ?? 0
                    let point = CGPoint(x: size.width * Double(index) / Double(frames.count - 1),
                        y: size.height * (1 - min(1, max(0, value))))
                    if index == 0 { path.move(to: point) } else { path.addLine(to: point) }
                }
                context.stroke(path, with: .color(.cyan.opacity(0.8)), lineWidth: 1.4)
                let x = size.width * Double(selected) / Double(frames.count - 1)
                var cursor = Path(); cursor.move(to: CGPoint(x: x, y: 0)); cursor.addLine(to: CGPoint(x: x, y: size.height))
                context.stroke(cursor, with: .color(.white.opacity(0.65)), lineWidth: 1)
            }
        }.accessibilityLabel(title)
    }
}
