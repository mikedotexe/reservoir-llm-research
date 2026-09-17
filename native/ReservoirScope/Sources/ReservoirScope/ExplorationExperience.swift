import SwiftUI
import EssentialsCore

/// Direct manipulation of the small reservoir, with exact observations retained.
struct ExplorationExperience: View {
    @ObservedObject var model: ExplorationViewModel
    @State private var cutaway = false
    @State private var presentation: StateSurfacePresentation = .topography
    @State private var topographyHeight = 0.16
    @State private var surfaceMetrics: StateSurfaceMetrics?
    private let clock = Timer.publish(every: 1.0 / 30, on: .main, in: .common).autoconnect()
    private let mint = Color(red: 0.35, green: 0.88, blue: 0.74)
    private let inputColor = Color(red: 1, green: 0.69, blue: 0.36)
    private var applied: ExplorationControls { model.frame?.controls ?? model.controls }
    private var node: Int { min(31, max(0, model.selectedNode)) }

    var body: some View {
        GeometryReader { size in
            HStack(spacing: 0) {
                controlPanel.frame(width: 258)
                Divider()
                VStack(alignment: .leading, spacing: 12) {
                    heading
                    ExplorationFlow(frame: model.frame, controls: applied)
                    surface
                    if let spectrum = model.frame?.spectral {
                        spectrumBars(spectrum)
                    }
                    ExplorationActivity(frames: model.frames, row: model.row)
                        .frame(height: 88)
                    playback
                }.padding(18).frame(maxWidth: .infinity, maxHeight: .infinity)
                Divider()
                ScrollView { inspector.padding(16) }.frame(width: 286)
            }.frame(width: size.size.width, height: size.size.height)
        }
        .onReceive(clock) { _ in model.tick() }
        .safeAreaInset(edge: .top) { if let issue = model.saveIssue { HStack { Text(issue); Button("Retry save") { model.retrySaves() }; Button("Export retained") { model.exportRetained() } }.font(.caption).padding(8) } }
        .onDisappear { model.leave() }
    }

    private var heading: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("Build the reservoir").font(.system(size: 24, weight: .medium))
                Spacer()
                Button("Open…") { model.chooseFile() }
                Button("Export…") { model.export() }.disabled(!model.hasFrames)
            }
            Text("Give it a signal. Change one thing. Watch what remains.")
                .font(.callout).foregroundStyle(.secondary)
            HStack(spacing: 7) {
                Circle().fill(model.running ? mint : Color.gray).frame(width: 5, height: 5)
                Text(model.status).font(.caption).foregroundStyle(.secondary).lineLimit(2)
                Spacer(minLength: 4)
                Text("Step \(model.frame?.step ?? 0) · \(number(model.frame?.time ?? 0, 2)) s")
                    .font(.system(.caption, design: .monospaced))
            }
            if let error = model.error {
                Text(error).font(.caption).foregroundStyle(.orange).textSelection(.enabled)
            }
            if let issue = model.saveIssue {
                Text(issue).font(.caption).foregroundStyle(.orange).textSelection(.enabled)
            }
        }
    }

    private var controlPanel: some View {
        VStack(alignment: .leading, spacing: 13) {
            Text("ESSENTIALS").font(.system(size: 19, weight: .medium, design: .rounded)).tracking(2)
            Text("A reservoir you can explore").font(.caption).foregroundStyle(.secondary)
            Button { model.startPause() } label: {
                Label(model.running ? "Pause reservoir" : model.hasFrames ? "Continue reservoir" : "Start reservoir",
                      systemImage: model.running ? "pause.fill" : "play.fill")
                    .frame(maxWidth: .infinity).padding(.vertical, 7)
                    .background(mint.opacity(model.canRun || model.running ? 1 : 0.35), in: RoundedRectangle(cornerRadius: 6))
                    .foregroundStyle(.black)
            }.buttonStyle(.plain)
                .disabled(!model.canRun && !model.running)
            HStack {
                Button("Step") { model.step() }.disabled(model.running || model.atLimit || model.loading)
                Button("Send pulse") { model.sendPulse() }.disabled(model.atLimit || model.loading)
                Spacer(minLength: 0)
                Button("Reset") { model.reset() }.disabled(model.loading)
            }.font(.caption)
            Text("Starts quiet. A pulse supplies one step of input; Start lets time advance.")
                .font(.caption2).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
            Divider()
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 17) {
                    VStack(alignment: .leading, spacing: 8) {
                        eyebrow("SETTINGS FOR THE NEXT STEP")
                        Text("Changes take effect at the next recorded step.")
                            .font(.caption2).foregroundStyle(.secondary)
                    }
                    VStack(alignment: .leading, spacing: 7) {
                        Toggle("Recurrent feedback", isOn: $model.controls.recurrenceEnabled)
                            .toggleStyle(.switch).controlSize(.small).tint(mint)
                        Text("Feed the previous state back through the seeded connections.")
                            .font(.caption2).foregroundStyle(.secondary)
                        knob("Feedback strength", value: $model.controls.recurrenceStrength, range: 0...1, digits: 2)
                            .disabled(!model.controls.recurrenceEnabled)
                        Text("Full strength: maximum absolute row sum 0.9.")
                            .font(.caption2).foregroundStyle(.secondary)
                    }
                    VStack(alignment: .leading, spacing: 7) {
                        Toggle("Repeat external input", isOn: $model.controls.repeatInput)
                            .toggleStyle(.switch).controlSize(.small).tint(inputColor)
                        Text("Synthetic bursts: 12 steps on, 18 steps off. This is separate from recurrent feedback.")
                            .font(.caption2).foregroundStyle(.secondary)
                        knob("Input strength", value: $model.controls.inputStrength, range: 0...1, digits: 2)
                    }
                    Divider()
                    VStack(alignment: .leading, spacing: 7) {
                        knob("Leak · new-state mix", value: $model.controls.leak, range: 0...1, digits: 2)
                        Text("0 keeps the old state. 1 takes the full tanh proposal. Noise is added afterward.")
                            .font(.caption2).foregroundStyle(.secondary)
                    }
                    knob("Seeded noise · ±", value: $model.controls.noiseAmplitude, range: 0...0.2, digits: 3)
                    Toggle("Constant bias", isOn: $model.controls.biasEnabled)
                        .font(.caption).toggleStyle(.checkbox)
                    Divider()
                    VStack(alignment: .leading, spacing: 7) {
                        Toggle("Observe sensory field", isOn: $model.controls.sensoryEnabled)
                            .font(.caption).toggleStyle(.checkbox)
                        Text("The same input also feeds a separate 32-dimensional field. Enabling it starts a fresh covariance.")
                            .font(.caption2).foregroundStyle(.secondary)
                        if model.controls.sensoryEnabled {
                            knob("Field retention", value: $model.controls.retention, range: 0.82...0.995, digits: 3)
                        }
                    }
                    Divider()
                    HStack {
                        Text("Seed").font(.caption)
                        TextField("Seed for Reset", text: $model.seedText)
                            .font(.caption.monospacedDigit()).textFieldStyle(.roundedBorder)
                    }
                    Text("Reset uses this seed and keeps the current settings. Each session retains up to 1,800 exact steps.")
                        .font(.caption2).foregroundStyle(.secondary)
                    Text("For text feedback, a language voice, and regulation, choose Stage experiments above.")
                        .font(.caption2).foregroundStyle(mint.opacity(0.85))
                }.padding(.trailing, 3)
            }
        }.padding(17).background(.white.opacity(0.025))
    }

    private var surface: some View {
        ZStack(alignment: .topLeading) {
            StateSurfaceScene(input: StateSurfaceRenderInput(
                values: model.state, lower: -1, upper: 1, fillPct: 100,
                relief: presentation == .topography ? topographyHeight : 0.10,
                cutaway: cutaway, selectedNode: node,
                flatLighting: presentation == .surface, presentation: presentation),
                accessibilitySubject: "Essentials exploration reservoir",
                onSelect: { model.selectedNode = $0 },
                onMetrics: { if surfaceMetrics != $0 { surfaceMetrics = $0 } })
            VStack(alignment: .leading, spacing: 6) {
                presentationControls
                VStack(alignment: .leading, spacing: 4) {
                    eyebrow("32 ACTUAL STATE COORDINATES")
                    Text(presentation == .topography
                         ? "State landscape · contours every 0.2"
                         : "Fixed display size · activation −1 to +1")
                        .font(.caption2).foregroundStyle(.secondary)
                }.allowsHitTesting(false)
            }.padding(13)
            VStack {
                Spacer()
                HStack(spacing: 6) {
                    Text(presentation == .topography ? "−1 · valley" : "−1").font(.caption2.monospacedDigit())
                    LinearGradient(colors: [
                        Color(.sRGBLinear, red: 0.52, green: 0.30, blue: 0.92),
                        Color(.sRGBLinear, red: 0.10, green: 0.17, blue: 0.23),
                        Color(.sRGBLinear, red: 0.14, green: 0.91, blue: 0.79)],
                        startPoint: .leading, endPoint: .trailing)
                        .frame(width: 92, height: 6).clipShape(Capsule())
                    Text(presentation == .topography ? "+1 · peak" : "+1").font(.caption2.monospacedDigit())
                    Spacer()
                    Toggle("Cutaway", isOn: $cutaway).font(.caption).toggleStyle(.checkbox)
                }.padding(12)
            }
        }.frame(minHeight: 255, maxHeight: .infinity)
            .background(.black.opacity(0.2), in: RoundedRectangle(cornerRadius: 12))
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .overlay(alignment: .center) {
                if let fallback = surfaceMetrics?.fallback {
                    Text(fallback).font(.caption).foregroundStyle(.orange).padding()
                }
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

    private var playback: some View {
        VStack(alignment: .leading, spacing: 9) {
            HStack {
                Button { model.replay() } label: {
                    Label(model.replaying ? "Pause replay" : "Replay",
                          systemImage: model.replaying ? "pause.fill" : "play.fill")
                }.disabled(model.running || !model.hasFrames || model.loading)
                Slider(value: Binding(get: { Double(model.row) }, set: { model.scrub($0) }),
                       in: 0...Double(max(1, model.frames.count - 1)), step: 1)
                    .disabled(model.running || model.frames.count < 2)
                    .accessibilityLabel("Exploration recorded step")
                Text("\(model.hasFrames ? model.row + 1 : 0) / \(model.frames.count)")
                    .font(.caption.monospacedDigit()).frame(minWidth: 62, alignment: .trailing)
            }
            HStack(spacing: 7) {
                Text("Viewing pace").font(.caption2).foregroundStyle(.secondary)
                ForEach([1.0, 3, 10, 20], id: \.self) { pace in
                    Button("\(Int(pace))") { model.changeSpeed(pace) }
                        .buttonStyle(.plain).font(.caption2.monospacedDigit())
                        .padding(.horizontal, 8).padding(.vertical, 4)
                        .background(model.speed == pace ? mint.opacity(0.23) : .white.opacity(0.05), in: Capsule())
                }
                Text("steps / second").font(.caption2).foregroundStyle(.secondary)
                Spacer()
            }
            Text(presentation == .topography
                 ? "⅓ simulated second per step. Height and contours share a state-value map, not network wiring or physical shape."
                 : "One step is ⅓ simulated second. The drawing map identifies coordinates, not network wiring.")
                .font(.caption2).foregroundStyle(.secondary)
        }
    }

    private var inspector: some View {
        LazyVStack(alignment: .leading, spacing: 17) {
            VStack(alignment: .leading, spacing: 9) {
                eyebrow("EXACT COORDINATE")
                HStack {
                    Text("Node \(node)").font(.headline)
                    Spacer()
                    Text(number(model.state[node], 6))
                        .font(.system(.title3, design: .monospaced)).foregroundStyle(mint)
                }
                LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 3), count: 8), spacing: 4) {
                    ForEach(0..<32, id: \.self) { index in
                        Button { model.selectedNode = index } label: {
                            Text(String(index)).font(.system(size: 10, design: .monospaced))
                                .frame(maxWidth: .infinity).padding(.vertical, 5)
                                .background(index == node ? mint.opacity(0.3) : .white.opacity(0.05),
                                            in: RoundedRectangle(cornerRadius: 3))
                        }.buttonStyle(.plain)
                            .help("Node \(index): \(number(model.state[index], 8))")
                    }
                }
            }
            Divider()
            VStack(alignment: .leading, spacing: 8) {
                eyebrow("HOW THIS NODE CHANGED")
                if let frame = model.frame {
                    metric("Previous state", number(frame.previousState[node], 6))
                    Text("Before tanh · shared scale −6 to +6").font(.caption2).foregroundStyle(.secondary)
                    component("Input drive", value: frame.inputDrive[node], color: inputColor)
                    component("Recurrent drive", value: frame.recurrentDrive[node], color: mint)
                    component("Bias", value: frame.biasDrive[node], color: .purple)
                    metric("tanh proposal", number(frame.proposal[node], 6))
                    Divider()
                    metric("Previous × \(number(1 - frame.controls.leak, 2))",
                           number((1 - frame.controls.leak) * frame.previousState[node], 6))
                    metric("Proposal × \(number(frame.controls.leak, 2))",
                           number(frame.controls.leak * frame.proposal[node], 6))
                    metric("Added noise", number(frame.noise[node], 6))
                    metric("Final · clipped to ±1", number(frame.state[node], 6))
                } else {
                    Text("Send a pulse or take a step to inspect the complete update.")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
            Divider()
            VStack(alignment: .leading, spacing: 8) {
                eyebrow("APPLIED AT THE CURSOR")
                if let frame = model.frame {
                    metric("Recurrent feedback", frame.controls.recurrenceEnabled ? "On" : "Off")
                    metric("Feedback strength", number(frame.controls.recurrenceStrength, 2))
                    metric("Repeated input", frame.controls.repeatInput ? "On" : "Off")
                    metric("Single pulse", frame.pulse ? "Yes" : "No")
                    metric("Input strength", number(frame.controls.inputStrength, 2))
                    metric("Leak", number(frame.controls.leak, 2))
                    metric("Noise bound", "±" + number(frame.controls.noiseAmplitude, 3))
                    metric("Bias", frame.controls.biasEnabled ? "On" : "Off")
                    metric("Sensory field", frame.controls.sensoryEnabled ? "On" : "Off")
                    if frame.controls.sensoryEnabled { metric("Field retention", number(frame.controls.retention, 3)) }
                } else {
                    Text("No recorded settings yet. The controls on the left set the next step.")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
            Divider()
            VStack(alignment: .leading, spacing: 8) {
                eyebrow("ACTUAL INPUT · 66 COORDINATES")
                if let frame = model.frame {
                    metric("Video · 0–7 RMS", number(rms(Array(frame.input[0..<8])), 5))
                    metric("Audio · 8–15 RMS", number(rms(Array(frame.input[8..<16])), 5))
                    metric("Auxiliary · 16–17", "0")
                    metric("Semantic · 18–65", "0 · no language loop")
                    DisclosureGroup("All input values") {
                        Text(frame.input.enumerated().map { "\($0.offset): \(number($0.element, 6))" }.joined(separator: "\n"))
                            .font(.system(.caption2, design: .monospaced)).textSelection(.enabled)
                    }.font(.caption)
                } else { Text("No applied input yet.").font(.caption).foregroundStyle(.secondary) }
            }
            if let spectrum = model.frame?.spectral {
                Divider()
                VStack(alignment: .leading, spacing: 8) {
                    eyebrow("SEPARATE SENSORY FIELD")
                    metric("Leading eigenvalue", number(spectrum.eigenvalues[0], 5))
                    metric("Top-eight entropy", number(spectrum.entropy, 5))
                    Text("This covariance receives the input directly. It is not a covariance of reservoir states; no fill is estimated here.")
                        .font(.caption2).foregroundStyle(.secondary)
                }
            }
            Divider()
            Text("Recurrent feedback connects state to later state. Repeated input supplies fresh external drive. Leak also preserves part of the previous state when feedback is off.")
                .font(.caption2).foregroundStyle(.secondary)
            if !model.source.isEmpty {
                DisclosureGroup("Saved source") {
                    Text(model.source).font(.caption2).textSelection(.enabled)
                }.font(.caption)
            }
        }
    }

    private func spectrumBars(_ spectrum: SpectralMeasurement) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack {
                eyebrow("INPUT → SEPARATE SENSORY FIELD")
                Spacer()
                Text("Leading 8 modes · scale 0–32").font(.caption2).foregroundStyle(.secondary)
            }
            HStack(alignment: .bottom, spacing: 6) {
                ForEach(0..<8, id: \.self) { index in
                    VStack(spacing: 2) {
                        Text(number(spectrum.eigenvalues[index], 2)).font(.system(size: 9, design: .monospaced))
                        ZStack(alignment: .bottom) {
                            RoundedRectangle(cornerRadius: 2).fill(.white.opacity(0.04))
                            RoundedRectangle(cornerRadius: 2).fill(mint.opacity(0.7))
                                .frame(height: max(0, min(32, spectrum.eigenvalues[index])) / 32 * 30)
                        }.frame(height: 30)
                        Text("λ\(index + 1)").font(.caption2).foregroundStyle(.secondary)
                    }.frame(maxWidth: .infinity)
                }
            }
        }
    }

    private func knob(_ title: String, value: Binding<Double>, range: ClosedRange<Double>, digits: Int) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack {
                Text(title).font(.caption)
                Spacer()
                Text(number(value.wrappedValue, digits)).font(.caption.monospacedDigit())
            }
            Slider(value: value, in: range).controlSize(.small).accessibilityLabel(title)
        }
    }
    private func component(_ name: String, value: Double, color: Color) -> some View {
        VStack(spacing: 3) {
            metric(name, number(value, 6))
            GeometryReader { size in
                let half = size.size.width / 2
                ZStack(alignment: .leading) {
                    Rectangle().fill(.white.opacity(0.04))
                    Rectangle().fill(color.opacity(0.8))
                        .frame(width: abs(value) / 6 * half)
                        .offset(x: value < 0 ? half - abs(value) / 6 * half : half)
                    Rectangle().fill(.white.opacity(0.35)).frame(width: 1).offset(x: half)
                }
            }.frame(height: 6)
        }
    }
    private func metric(_ name: String, _ value: String) -> some View {
        HStack(alignment: .firstTextBaseline) {
            Text(name).font(.caption).foregroundStyle(.secondary)
            Spacer(minLength: 6)
            Text(value).font(.system(.caption, design: .monospaced)).textSelection(.enabled)
        }
    }
    private func eyebrow(_ text: String) -> some View {
        Text(text).font(.system(size: 9, weight: .medium)).tracking(1).foregroundStyle(.secondary)
    }
    private func number(_ value: Double, _ digits: Int) -> String { String(format: "%.*f", digits, value) }
    private func rms(_ values: [Double]) -> Double {
        values.isEmpty ? 0 : sqrt(values.reduce(0) { $0 + $1 * $1 } / Double(values.count))
    }
}

private struct ExplorationFlow: View {
    let frame: ExplorationFrame?
    let controls: ExplorationControls
    private let green = Color(red: 0.35, green: 0.88, blue: 0.74)
    var body: some View {
        VStack(spacing: 5) {
            HStack(spacing: 5) {
                block("Input", value: rms(frame?.input), color: .orange)
                Image(systemName: "arrow.right").foregroundStyle(.secondary)
                block("tanh proposal", value: rms(frame?.proposal), color: .purple)
                Image(systemName: "arrow.right").foregroundStyle(.secondary)
                block("Leaky mix + noise", value: rms(frame?.state), color: green)
            }.font(.caption2)
            HStack(spacing: 5) {
                Image(systemName: "arrow.turn.up.left")
                Text(controls.recurrenceEnabled
                     ? "Previous state → recurrent drive → tanh · RMS \(String(format: "%.4f", rms(frame?.recurrentDrive)))"
                     : "Recurrent feedback off · units still keep the leaky share of their previous state")
                    .lineLimit(2)
            }.font(.caption2).foregroundStyle(controls.recurrenceEnabled ? green : .secondary)
            Text("tanh takes weighted input + recurrent drive + bias. The leaky mix comes next.")
                .font(.system(size: 9)).foregroundStyle(.secondary)
        }
        .accessibilityElement(children: .combine)
    }
    private func block(_ title: String, value: Double, color: Color) -> some View {
        VStack(spacing: 3) {
            Text(title).foregroundStyle(.secondary)
            Text("RMS " + String(format: "%.4f", value)).font(.system(.caption, design: .monospaced)).foregroundStyle(color)
        }.padding(.vertical, 7).frame(maxWidth: .infinity)
            .background(color.opacity(0.065), in: RoundedRectangle(cornerRadius: 7))
    }
    private func rms(_ values: [Double]?) -> Double {
        guard let values, !values.isEmpty else { return 0 }
        return sqrt(values.reduce(0) { $0 + $1 * $1 } / Double(values.count))
    }
}

private struct ExplorationActivity: View {
    let frames: [ExplorationFrame]
    let row: Int
    private let colors: [Color] = [.orange, Color(red: 0.35, green: 0.88, blue: 0.74), .cyan]
    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack(spacing: 12) {
                key("External input", color: colors[0])
                key("Recurrent drive", color: colors[1])
                key("State", color: colors[2])
                Spacer()
                Text("RMS · fixed 0–1").font(.caption2).foregroundStyle(.secondary)
            }
            Canvas { context, size in
                var middle = Path()
                middle.move(to: CGPoint(x: 0, y: size.height / 2))
                middle.addLine(to: CGPoint(x: size.width, y: size.height / 2))
                context.stroke(middle, with: .color(.white.opacity(0.09)), style: StrokeStyle(lineWidth: 1, dash: [3, 4]))
                guard frames.count > 1 else { return }
                for kind in 0..<3 {
                    var line = Path()
                    for (index, frame) in frames.enumerated() {
                        let values = kind == 0 ? frame.input : kind == 1 ? frame.recurrentDrive : frame.state
                        let rms = sqrt(values.reduce(0) { $0 + $1 * $1 } / Double(values.count))
                        let point = CGPoint(x: size.width * Double(index) / Double(frames.count - 1),
                                            y: size.height * (1 - rms))
                        if index == 0 { line.move(to: point) } else { line.addLine(to: point) }
                    }
                    context.stroke(line, with: .color(colors[kind].opacity(0.9)), lineWidth: 1.4)
                }
                let x = size.width * Double(row) / Double(frames.count - 1)
                var cursor = Path()
                cursor.move(to: CGPoint(x: x, y: 0)); cursor.addLine(to: CGPoint(x: x, y: size.height))
                context.stroke(cursor, with: .color(.white.opacity(0.7)), lineWidth: 1)
            }
        }.accessibilityLabel("Recorded external input, recurrent drive and state RMS. Fixed scale zero to one.")
    }
    private func key(_ title: String, color: Color) -> some View {
        HStack(spacing: 4) {
            Circle().fill(color).frame(width: 4, height: 4)
            Text(title).font(.system(size: 9))
        }
    }
}
