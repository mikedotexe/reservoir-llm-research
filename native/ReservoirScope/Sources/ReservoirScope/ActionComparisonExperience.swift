import SwiftUI
import EssentialsCore

struct ActionComparisonExperience: View {
    @ObservedObject var model: ActionComparisonViewModel
    @StateObject private var camera = StateSurfaceCamera()
    @State private var presentation: StateSurfacePresentation = .topography
    @State private var height = 0.16
    @State private var inspectedArm: ActionArm = .right
    @State private var surfaceFailures: [String: String] = [:]
    private let pulse = Timer.publish(every: 1.0 / 30, on: .main, in: .common).autoconnect()
    private let mint = Color(red: 0.35, green: 0.88, blue: 0.74)
    private let previousColor = Color(red: 0.91, green: 0.68, blue: 0.40)
    private var node: Int { min(31, max(0, model.selectedNode)) }
    private var activeRecord: ActionRunRecord? { inspectedArm == .left ? model.leftRecord : model.rightRecord }
    private var activeFrame: ActionFrame? { inspectedArm == .left ? model.leftFrame : model.rightFrame }
    private var activeAction: ActionReceipt? {
        guard let record = activeRecord else { return nil }
        if let id = model.selectedActionID { return record.actions.first { $0.id == id } }
        let step = activeFrame?.step ?? 0
        return record.actions.last { $0.observedStep <= step }
    }

    var body: some View {
        GeometryReader { geometry in
            HStack(spacing: 0) {
                sidebar.frame(width: 204)
                Divider()
                VStack(alignment: .leading, spacing: 8) {
                    heading
                    controls
                    comparisonNote
                    displays
                    if model.isComparison {
                        ActionDifferenceTrace(left: model.leftRecord?.frames ?? [], right: model.rightRecord?.frames ?? [],
                                              node: node, row: model.row).frame(height: 63)
                        if model.record?.specification.stage == .regulation {
                            HStack(spacing: 12) {
                                ActionSensoryTrace(left: model.leftRecord?.frames ?? [], right: model.rightRecord?.frames ?? [],
                                                   row: model.row, isFill: true)
                                ActionSensoryTrace(left: model.leftRecord?.frames ?? [], right: model.rightRecord?.frames ?? [],
                                                   row: model.row, isFill: false)
                            }.frame(height: 43)
                        }
                    }
                    actionTimeline
                    playback
                }.padding(16).frame(maxWidth: .infinity, maxHeight: .infinity)
                Divider()
                ScrollView { inspector.padding(16) }.frame(width: 292)
            }.frame(width: geometry.size.width, height: geometry.size.height)
        }
        .onReceive(pulse) { _ in model.tick() }
        .onDisappear { model.leave() }
        .onChange(of: model.isComparison) { _, paired in if !paired { inspectedArm = .right } }
    }

    private var sidebar: some View {
        VStack(alignment: .leading, spacing: 13) {
            Text("ESSENTIALS").font(.system(size: 18, weight: .medium, design: .rounded)).tracking(2)
            Text("One addition at a time").font(.caption).foregroundStyle(.secondary)
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 10) {
                    ForEach(ActionStage.allCases) { stage in
                        Button { model.select(stage) } label: {
                            HStack(alignment: .top, spacing: 8) {
                                Text(letter(stage)).font(.system(.caption, design: .monospaced).weight(.semibold))
                                    .frame(width: 24, height: 24)
                                    .background(stage == model.stage ? mint.opacity(0.25) : .white.opacity(0.06), in: Circle())
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(shortTitle(stage)).font(.caption.weight(.medium))
                                    if stage == model.stage {
                                        Text(stage.addedFeature).font(.caption2).foregroundStyle(.secondary)
                                            .fixedSize(horizontal: false, vertical: true)
                                    }
                                }
                                Spacer(minLength: 0)
                            }.padding(7).frame(maxWidth: .infinity, alignment: .leading)
                                .background(stage == model.stage ? mint.opacity(0.08) : .clear,
                                            in: RoundedRectangle(cornerRadius: 7))
                        }.buttonStyle(.plain)
                    }
                    Divider()
                    runSettings
                    Divider()
                    studyNotes
                    Button { model.loadExample() } label: { Label("Open example", systemImage: "play.rectangle") }
                        .font(.caption).disabled(model.running || model.working)
                }.padding(.trailing, 3)
            }
        }.padding(14).background(.white.opacity(0.025))
    }

    private var runSettings: some View {
        VStack(alignment: .leading, spacing: 9) {
            eyebrow("FOR THE NEXT RUN")
            Picker("Reply mode", selection: $model.mode) {
                Text("Fixed tape").tag(ActionComparisonMode.fixedReplay)
                Text("Independent").tag(ActionComparisonMode.independentGeneration)
            }.pickerStyle(.segmented).labelsHidden().controlSize(.small)
                .disabled(model.running || model.working)
            Text(model.mode == .fixedReplay
                 ? "Replay the same retained words and codec vectors to isolate feedback mechanics."
                 : "Each arm receives its own observations, memory and action choices.")
                .font(.caption2).foregroundStyle(.secondary)
            if model.mode == .fixedReplay {
                Text("Fixed replies cannot show whether memory improves writing.")
                    .font(.caption2).foregroundStyle(.secondary)
            }
            if model.mode == .independentGeneration {
                Toggle("Use a local model", isOn: $model.localModel).font(.caption).toggleStyle(.checkbox)
                    .disabled(model.running || model.working)
                if model.localModel {
                    TextField("Model endpoint", text: $model.endpoint).textFieldStyle(.roundedBorder)
                        .accessibilityLabel("Action model endpoint")
                    TextField("Model name", text: $model.modelName).textFieldStyle(.roundedBorder)
                        .accessibilityLabel("Action model name")
                } else {
                    Text("Scripted replies are a reproducible fixture. They do not demonstrate adaptive writing.")
                        .font(.caption2).foregroundStyle(.secondary)
                }
            } else {
                Text("The declared scripted tape is replayed without calling a model.")
                    .font(.caption2).foregroundStyle(.secondary)
            }
            HStack {
                Text("Seed").font(.caption)
                TextField("Seed", text: $model.seedText).textFieldStyle(.roundedBorder).font(.caption.monospacedDigit())
            }.disabled(model.running || model.working)
        }.font(.caption)
    }

    private var studyNotes: some View {
        DisclosureGroup("Before running") {
            VStack(alignment: .leading, spacing: 8) {
                note("Question", text: $model.question)
                note("Expected difference", text: $model.expectedDifference)
                note("Other explanations", text: $model.alternatives)
                note("Stopping point", text: $model.stoppingPoint)
            }.padding(.top, 6).disabled(model.running || model.working)
        }.font(.caption)
    }
    private func note(_ title: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(title).font(.caption2).foregroundStyle(.secondary)
            TextField(title, text: text, axis: .vertical).lineLimit(2...4)
                .textFieldStyle(.roundedBorder).font(.caption2)
        }
    }

    private var heading: some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack {
                Text("Actions & comparisons").font(.system(size: 21, weight: .medium))
                Spacer(minLength: 6)
                Button("Open…") { model.chooseFile() }.disabled(model.running || model.working)
                Button("Export…") { model.export() }.disabled(model.record == nil || model.running || model.working)
            }
            HStack(spacing: 7) {
                Circle().fill(model.running ? mint : .gray).frame(width: 5, height: 5)
                Text(model.status).font(.caption).foregroundStyle(.secondary).lineLimit(2)
                Spacer(minLength: 4)
                if let frame = model.rightFrame {
                    Text("Step \(frame.step) · \(number(frame.time, 2)) s").font(.caption.monospacedDigit())
                }
            }
            if let error = model.error { Text(error).font(.caption).foregroundStyle(.orange).textSelection(.enabled) }
            if let issue = model.saveIssue { Text(issue).font(.caption).foregroundStyle(.orange).textSelection(.enabled) }
        }
    }

    private var controls: some View {
        HStack(spacing: 7) {
            Button { model.run() } label: {
                Label("Run", systemImage: "play.fill").padding(.horizontal, 10).padding(.vertical, 5)
                    .background(mint.opacity(model.canRun ? 1 : 0.35), in: RoundedRectangle(cornerRadius: 5))
                    .foregroundStyle(.black)
            }.buttonStyle(.plain).disabled(!model.canRun)
            Button("Stop") { model.stop() }.disabled(!model.running && !model.working)
            Button("Step") { model.step() }.disabled(model.running || model.working || model.loading)
            Button("Reset") { model.reset() }.disabled(model.running || model.working)
            Button("Write journal") { model.writeJournal() }.disabled(!model.canWrite)
                .help("Request an explicit writing action at the current boundary. This is a human request.")
            Spacer(minLength: 3)
            Button("Compare with previous") { model.compareWithPrevious() }.disabled(!model.canCompare)
        }.font(.caption)
    }

    private var comparisonNote: some View {
        VStack(alignment: .leading, spacing: 4) {
            if let record = model.record {
                let spec = record.specification
                Text(record.left == nil ? spec.stage.title : "\(letter(record.left!.stage)) → \(letter(spec.stage)) · Added: \(spec.stage.addedFeature)")
                    .font(.caption.weight(.medium)).foregroundStyle(mint)
                Text("Seed \(spec.seed) · leak \(number(spec.leak, 2)) · input \(number(spec.inputStrength, 2)) · noise \(number(spec.noiseAmplitude, 2)) · bias \(spec.biasEnabled ? "on" : "off")")
                    .font(.caption2).foregroundStyle(.secondary)
                Text(spec.mode == .fixedReplay
                     ? "Matched external forcing; retained words and vectors stay fixed."
                     : "Matched setup; each arm's replies can change its later trajectory.")
                    .font(.caption2).foregroundStyle(.secondary)
                if spec.stage == .journalMemory && spec.mode == .fixedReplay {
                    Text("Memory exposure differs; fixed writing may leave states identical. Choose Independent to test coupled writing.")
                        .font(.caption2).foregroundStyle(.secondary)
                }
                if spec.stage == .regulation && spec.mode == .fixedReplay {
                    Text("Complete inputs match. State may stay identical; inspect fill and retention for the controller's effect.")
                        .font(.caption2).foregroundStyle(.secondary)
                }
            } else {
                Text(model.stage.title + " · " + model.stage.addedFeature).font(.caption.weight(.medium)).foregroundStyle(mint)
                Text("One-third simulated second per step. Scheduled opportunities at steps 30–270.")
                    .font(.caption2).foregroundStyle(.secondary)
            }
        }
    }

    private var displays: some View {
        VStack(spacing: 7) {
            HStack(spacing: 8) {
                Picker("State display", selection: $presentation) {
                    ForEach(StateSurfacePresentation.allCases) { Text($0.title).tag($0) }
                }.pickerStyle(.segmented).labelsHidden().controlSize(.small).frame(width: 172)
                if presentation == .topography {
                    Text("Height").font(.caption2).foregroundStyle(.secondary)
                    Slider(value: $height, in: 0...0.20).controlSize(.small).frame(width: 76)
                        .accessibilityLabel("Shared comparison height")
                }
                Spacer(minLength: 4)
                Button { camera.reset() } label: { Label("Reset view", systemImage: "arrow.counterclockwise") }
                    .font(.caption2)
            }
            HStack(spacing: 9) {
                if let left = model.leftRecord {
                    statePanel(title: left.stage.title, frame: model.leftFrame, color: previousColor,
                               empty: model.framesCount == 0 ? "Initial state" : "No matching observation")
                }
                statePanel(title: model.rightRecord?.stage.title ?? model.stage.title, frame: model.rightFrame,
                           color: mint, empty: model.framesCount == 0 ? "Initial state" : "No matching observation")
            }.frame(minHeight: 190, maxHeight: .infinity)
            Text((model.isComparison ? "Shared camera, cursor and scales · −1 to +1" : "Activation −1 to +1")
                 + (presentation == .topography ? " · contours every 0.2" : "")
                 + " · value map, not wiring")
                .font(.system(size: 9)).foregroundStyle(.secondary)
        }.frame(maxHeight: .infinity)
    }
    private func statePanel(title: String, frame: ActionFrame?, color: Color, empty: String) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(title).font(.caption.weight(.medium)).foregroundStyle(color).lineLimit(1)
            ZStack(alignment: .topLeading) {
                if frame != nil || empty == "Initial state" {
                    StateSurfaceScene(input: StateSurfaceRenderInput(values: frame?.state ?? Array(repeating: 0, count: 32),
                        lower: -1, upper: 1, fillPct: 100, relief: presentation == .topography ? height : 0.10,
                        cutaway: false, selectedNode: node, flatLighting: presentation == .surface, presentation: presentation),
                        accessibilitySubject: title + " comparison reservoir",
                        onSelect: { model.selectedNode = $0 }, onMetrics: {
                            if surfaceFailures[title] != $0.fallback { surfaceFailures[title] = $0.fallback }
                        }, camera: camera)
                }
                Text(frame.map { "Step \($0.step) · 32 actual coordinates" } ?? empty)
                    .font(.system(size: 9)).foregroundStyle(.secondary).padding(9).allowsHitTesting(false)
                if let failure = surfaceFailures[title] {
                    Text(failure).font(.caption2).foregroundStyle(.orange).padding(9)
                }
            }.frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(.black.opacity(0.22), in: RoundedRectangle(cornerRadius: 10))
                .clipShape(RoundedRectangle(cornerRadius: 10))
        }.frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var actionTimeline: some View {
        VStack(alignment: .leading, spacing: 3) {
            eyebrow("ACTION OPPORTUNITIES · CLICK TO INSPECT")
            if let left = model.leftRecord { actionRow(left, color: previousColor) }
            if let right = model.rightRecord { actionRow(right, color: mint) }
            if model.rightRecord == nil { Text("No action has been requested.").font(.caption2).foregroundStyle(.secondary) }
        }
    }
    private func actionRow(_ arm: ActionRunRecord, color: Color) -> some View {
        HStack(spacing: 7) {
            Text(letter(arm.stage)).font(.caption2.monospaced()).foregroundStyle(color).frame(width: 14)
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    Rectangle().fill(.white.opacity(0.08)).frame(height: 1)
                    ForEach(arm.actions) { action in
                        Button {
                            if !model.running && !model.working { model.scrub(Double(max(0, action.observedStep - 1))) }
                            inspectedArm = arm.arm; model.selectedActionID = action.id
                        } label: {
                            Text(action.chosenAction == .wait ? "–" : String(action.id))
                                .font(.system(size: 9, design: .monospaced)).frame(width: 19, height: 19)
                                .background(color.opacity(action.status == .completed ? 0.24 : 0.08), in: Circle())
                                .overlay(Circle().stroke(model.selectedActionID == action.id && inspectedArm == arm.arm ? color : .clear, lineWidth: 1))
                        }.buttonStyle(.plain)
                            .help("Action \(action.id) · source step \(action.observedStep) · \(action.status.rawValue)")
                            .position(x: 10 + max(0, geometry.size.width - 20) * Double(action.observedStep) / Double(max(1, model.record?.specification.steps ?? 300)), y: 10)
                    }
                }
            }.frame(height: 21)
        }
    }

    private var playback: some View {
        VStack(spacing: 6) {
            HStack(spacing: 8) {
                Button(model.replaying ? "Pause replay" : "Replay") { model.replay() }
                    .disabled(model.running || model.working || model.framesCount == 0)
                Slider(value: Binding(get: { Double(model.row) }, set: { model.scrub($0) }),
                       in: 0...Double(max(1, model.framesCount - 1)), step: 1)
                    .disabled(model.running || model.working || model.framesCount < 2)
                    .accessibilityLabel("Shared comparison cursor")
                Text("\(model.framesCount == 0 ? 0 : model.row + 1) / \(model.framesCount)")
                    .font(.caption2.monospacedDigit()).frame(minWidth: 56, alignment: .trailing)
            }.font(.caption)
            HStack(spacing: 6) {
                Text("Viewing pace").foregroundStyle(.secondary)
                ForEach([1.0, 3, 10, 20], id: \.self) { speed in
                    Button(String(Int(speed))) { model.changeSpeed(speed) }.buttonStyle(.plain)
                        .padding(.horizontal, 7).padding(.vertical, 3)
                        .background(model.speed == speed ? mint.opacity(0.22) : .white.opacity(0.04), in: Capsule())
                }
                Text("steps / second").foregroundStyle(.secondary)
                Spacer()
            }.font(.caption2)
        }
    }

    private var inspector: some View {
        // Receipt sections are bounded. Keeping their geometry materialized
        // avoids lazy disclosure re-layout when accessibility reveals text.
        VStack(alignment: .leading, spacing: 16) {
            coordinateInspector
            Divider()
            if model.isComparison {
                Picker("Inspect arm", selection: $inspectedArm) {
                    Text("Previous").tag(ActionArm.left)
                    Text("Current").tag(ActionArm.right)
                }.pickerStyle(.segmented).labelsHidden().controlSize(.small)
            }
            Text(activeRecord?.stage.title ?? model.stage.title).font(.caption.weight(.medium))
            if let record = activeRecord, !record.actions.isEmpty {
                Picker("Action", selection: Binding(get: { model.selectedActionID ?? 0 }, set: { model.selectedActionID = $0 == 0 ? nil : $0 })) {
                    Text("Latest at cursor").tag(0)
                    ForEach(record.actions) { Text("\($0.id) · step \($0.observedStep)").tag($0.id) }
                    if let id = model.selectedActionID, !record.actions.contains(where: { $0.id == id }) {
                        Text("\(id) · unavailable in this arm").tag(id)
                    }
                }.font(.caption)
            }
            if let action = activeAction { actionInspector(action) }
            else { Text("No action receipt at this cursor or selected opportunity.").font(.caption).foregroundStyle(.secondary) }
            Divider()
            Text("Writing observes the separate sensory field fed by input. Reservoir activations are not part of this prompt; recurrence alone does not change that observation.")
                .font(.caption2).foregroundStyle(.secondary)
            if let tape = model.record?.tape {
                DisclosureGroup("Fixed reply tape") {
                    Text(tape.origin).font(.caption2).textSelection(.enabled)
                    metric("Packets", String(tape.packets.count))
                    Text("Words and reference-shaped codec vectors were retained before the comparison.")
                        .font(.caption2).foregroundStyle(.secondary)
                }.font(.caption)
            }
            if !model.source.isEmpty {
                DisclosureGroup("Saved session") { Text(model.source).font(.caption2).textSelection(.enabled) }.font(.caption)
            }
            if let spec = model.record?.specification {
                DisclosureGroup("Recorded setup and question") {
                    VStack(alignment: .leading, spacing: 8) {
                        metric("Reply mode", spec.mode.title)
                        metric("Planned steps", String(spec.steps))
                        metric("Opportunity interval", "\(spec.turnEvery) steps")
                        metric("Step duration", "1/3 second")
                        metric("Initial sensory retention", number(spec.initialRetention, 5))
                        disclosure("Question", text: spec.question)
                        disclosure("Expected difference", text: spec.expectedDifference)
                        disclosure("Other explanations", text: spec.alternatives)
                        disclosure("Stopping point", text: spec.stoppingPoint)
                    }.padding(.top, 6)
                }.font(.caption)
            }
        }
    }
    private var coordinateInspector: some View {
        VStack(alignment: .leading, spacing: 8) {
            eyebrow("EXACT COORDINATE")
            HStack {
                Text("Node \(node)").font(.headline)
                Spacer()
                Stepper("Selected node", value: $model.selectedNode, in: 0...31).labelsHidden()
            }
            if model.isComparison {
                metric("Previous", model.leftFrame.map { number($0.state[node], 6) } ?? "Unavailable")
                metric("Current", model.rightFrame.map { number($0.state[node], 6) } ?? "Unavailable")
                metric("Current − previous", pairedValue { $1.state[node] - $0.state[node] })
                metric("State difference · RMS", pairedValue { differenceRMS($0.state, $1.state) })
                metric("External difference · RMS", pairedValue { differenceRMS($0.externalInput, $1.externalInput) })
                metric("Semantic difference · RMS", pairedValue { differenceRMS($0.semanticInput, $1.semanticInput) })
            } else { metric("State", model.rightFrame.map { number($0.state[node], 6) } ?? "0 · initial") }
            Text("Differences compare matching recorded steps. They are not measures of writing quality.")
                .font(.caption2).foregroundStyle(.secondary)
            if let frame = activeFrame {
                metric("Sensory leading mode", frame.spectral.map { number($0.eigenvalues[0], 5) } ?? "Unavailable")
                metric("Reduced fill", frame.fillPercent.map { number($0, 2) + "%" } ?? "Unavailable")
                metric("Retention used", frame.retentionUsed.map { number($0, 5) } ?? "Unavailable")
                metric("Next retention", frame.control.map { number($0.appliedRetention, 5) } ?? "No controller update")
                disclosure("Actual input · 66 coordinates", text: vector(frame.input))
                if let spectral = frame.spectral {
                    disclosure("Sensory spectrum · 32 values", text: vector(spectral.eigenvalues))
                }
            }
        }
    }
    private func actionInspector(_ action: ActionReceipt) -> some View {
        VStack(alignment: .leading, spacing: 9) {
            eyebrow("REQUEST → COMPLETION → SAVE → RETURN")
            metric("Opportunity", "\(action.id) · step \(action.observedStep)")
            metric("Requested by", action.trigger == .manual ? "Human button" : "Schedule")
            metric("Requested action", action.requestedAction.map(actionTitle)
                ?? (action.tapePacketID == nil ? "Write-or-wait choice requested" : "Choice replayed from tape"))
            metric("Chosen action", action.chosenAction.map(actionTitle) ?? "No valid choice")
            metric("Action outcome", action.status.rawValue.capitalized)
            metric(action.tapePacketID == nil ? "Reply complete" : "Tape response complete", action.providerComplete.map { $0 ? "Yes" : "No" } ?? "Unavailable")
            metric("Provider model", action.providerModel ?? "Unavailable")
            metric("Stop reason", action.stopReason ?? "Unavailable")
            if let tokens = action.tokenCount { metric("Output tokens", String(tokens)) }
            if let failure = action.failure { Text(failure).font(.caption2).foregroundStyle(.orange).textSelection(.enabled) }
            disclosure(action.requestStarted ? "Exact request prompt" : "Prepared prompt · not sent", text: action.prompt)
            disclosure(action.tapePacketID == nil ? "Provider output" : "Replayed response", text: action.rawReply ?? "No response retained")
            Divider()
            if let save = action.saveReceipt {
                metric("Journal saved", save.status == .saved ? "Yes" : "Failed")
                disclosure("Journal entry ID / hash", text: save.entryID + "\n" + save.sha256)
                if let path = save.relativePath { disclosure("Journal location", text: path) }
                if let failure = save.failure { Text(failure).font(.caption2).foregroundStyle(.orange).textSelection(.enabled) }
                if save.status == .saved, let entry = activeRecord?.journals.first(where: { $0.id == save.entryID }) {
                    disclosure("Complete saved journal", text: entry.text)
                }
            } else { metric("Journal saved", action.chosenAction == .wait ? "No journal from WAIT" : "No successful save receipt") }
            Divider()
            metric("Journal memory", action.failurePhase == .memoryRead ? "Read failed"
                : action.memoryText == nil ? "No prior journal"
                : action.requestStarted ? "Included in request" : "Loaded into prepared context")
            if let id = action.memoryEntryID { disclosure(action.failurePhase == .memoryRead ? "Expected entry ID" : "Memory entry ID", text: id) }
            if let text = action.memoryText { disclosure(action.requestStarted ? "Exact memory in request" : "Exact memory prepared", text: text) }
            Text(action.requestStarted ? "This records context exposure, not proof of understanding."
                 : "Prepared context was not sent to a model in this replay or failed attempt.")
                .font(.caption2).foregroundStyle(.secondary)
            Divider()
            metric("Codec return", action.applicationStep.map { "Applied at step \($0)" }
                ?? (action.semanticVector == nil ? "Not prepared" : "Prepared; not applied"))
            if let values = action.encodedFeatures { disclosure("Encoded text features", text: vector(values)) }
            if let values = action.semanticVector { disclosure("Exact 48-coordinate return", text: vector(values)) }
            if let packetID = action.tapePacketID {
                metric("Fixed tape packet", String(packetID))
                if let packet = model.record?.tape?.packets.first(where: { $0.id == packetID }) {
                    metric("Reference observation", "Step \(packet.referenceStep)")
                    disclosure("Reference sensory eigenvalues", text: vector(packet.referenceEigenvalues))
                }
            }
            Text("Only completed, saved journals can return. The last 16 codec features are unavailable; the vector does not preserve recoverable journal text.")
                .font(.caption2).foregroundStyle(.secondary)
        }
    }
    private func pairedValue(_ operation: (ActionFrame, ActionFrame) -> Double) -> String {
        guard let left = model.leftFrame, let right = model.rightFrame, left.step == right.step else { return "Unavailable" }
        return number(operation(left, right), 6)
    }
    private func differenceRMS(_ a: [Double], _ b: [Double]) -> Double {
        guard a.count == b.count, !a.isEmpty else { return .nan }
        return sqrt(zip(a, b).reduce(0) { $0 + ($1.1 - $1.0) * ($1.1 - $1.0) } / Double(a.count))
    }
    private func disclosure(_ title: String, text: String) -> some View {
        DisclosureGroup(title) { Text(text).font(.caption2).textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading) }
            .font(.caption)
    }
    private func metric(_ title: String, _ value: String) -> some View {
        HStack(alignment: .firstTextBaseline) {
            Text(title).font(.caption2).foregroundStyle(.secondary)
            Spacer(minLength: 5)
            Text(value).font(.system(.caption2, design: .monospaced)).multilineTextAlignment(.trailing).textSelection(.enabled)
        }
    }
    private func eyebrow(_ text: String) -> some View { Text(text).font(.system(size: 9, weight: .medium)).tracking(0.7).foregroundStyle(.secondary) }
    private func letter(_ stage: ActionStage) -> String { String(stage.title.prefix(1)) }
    private func shortTitle(_ stage: ActionStage) -> String { stage.title.components(separatedBy: " · ").last ?? stage.title }
    private func actionTitle(_ action: JournalAction) -> String { action == .writeJournal ? "Write journal" : "Wait" }
    private func number(_ value: Double, _ digits: Int) -> String { value.isFinite ? String(format: "%.*f", digits, value) : "Unavailable" }
    private func vector(_ values: [Double]) -> String { values.enumerated().map { "\($0.offset): \(number($0.element, 8))" }.joined(separator: "\n") }
}

private struct ActionDifferenceTrace: View {
    let left: [ActionFrame]
    let right: [ActionFrame]
    let node: Int
    let row: Int
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("Node \(node) · current − previous").font(.caption2)
                Spacer()
                Text("Fixed scale −2 to +2").font(.caption2).foregroundStyle(.secondary)
            }
            Canvas { context, size in
                var zero = Path(); zero.move(to: CGPoint(x: 0, y: size.height / 2)); zero.addLine(to: CGPoint(x: size.width, y: size.height / 2))
                context.stroke(zero, with: .color(.white.opacity(0.16)), style: StrokeStyle(lineWidth: 1, dash: [3, 4]))
                let count = min(left.count, right.count)
                guard count > 1 else { return }
                var line = Path(), continuing = false
                for index in 0..<count {
                    guard left[index].step == right[index].step,
                          left[index].state.indices.contains(node), right[index].state.indices.contains(node) else { continuing = false; continue }
                    let delta = right[index].state[node] - left[index].state[node]
                    let point = CGPoint(x: size.width * CGFloat(index) / CGFloat(count - 1),
                                        y: size.height * CGFloat(2 - delta) / 4)
                    if continuing { line.addLine(to: point) } else { line.move(to: point); continuing = true }
                }
                context.stroke(line, with: .color(.cyan), lineWidth: 1.5)
                if (0..<count).contains(row) {
                    let x = size.width * Double(row) / Double(count - 1)
                    var cursor = Path(); cursor.move(to: CGPoint(x: x, y: 0)); cursor.addLine(to: CGPoint(x: x, y: size.height))
                    context.stroke(cursor, with: .color(.white.opacity(0.7)), lineWidth: 1)
                }
            }
        }.accessibilityLabel("Exact recorded difference for node \(node), current minus previous. Fixed scale minus two to plus two.")
    }
}

private struct ActionSensoryTrace: View {
    let left: [ActionFrame]
    let right: [ActionFrame]
    let row: Int
    let isFill: Bool
    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(isFill ? "Fill · 0–100%" : "Retention · 0.82–0.995")
                .font(.system(size: 9)).foregroundStyle(.secondary)
            Canvas { context, size in
                let count = max(left.count, right.count)
                guard count > 1 else { return }
                for (frames, color) in [(left, Color(red: 0.91, green: 0.68, blue: 0.40)), (right, Color(red: 0.35, green: 0.88, blue: 0.74))] {
                    var path = Path(), continuing = false
                    for (index, frame) in frames.enumerated() {
                        guard let value = isFill ? frame.fillPercent : frame.retentionUsed else { continuing = false; continue }
                        let normalized = isFill ? value / 100 : (value - 0.82) / (0.995 - 0.82)
                        let point = CGPoint(x: size.width * Double(index) / Double(count - 1), y: size.height * (1 - normalized))
                        if continuing { path.addLine(to: point) } else { path.move(to: point); continuing = true }
                    }
                    context.stroke(path, with: .color(color), lineWidth: 1.4)
                }
                if (0..<count).contains(row) {
                    let x = size.width * Double(row) / Double(count - 1)
                    var cursor = Path(); cursor.move(to: CGPoint(x: x, y: 0)); cursor.addLine(to: CGPoint(x: x, y: size.height))
                    context.stroke(cursor, with: .color(.white.opacity(0.5)), lineWidth: 1)
                }
            }
        }.accessibilityLabel(isFill ? "Paired reduced fill, fixed scale zero to one hundred percent. Previous in orange, current in green."
            : "Paired sensory retention, fixed scale 0.82 to 0.995. Previous in orange, current in green.")
    }
}
