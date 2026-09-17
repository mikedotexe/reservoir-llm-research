import SwiftUI
import EssentialsCore

struct ActionComparisonExperience: View {
    @ObservedObject var model: ActionComparisonViewModel
    var guided = false
    var onTryExperiment: () -> Void = {}
    @StateObject private var tour = GuidedTourModel()
    @StateObject private var readiness = LocalModelReadiness()
    @State private var evidenceVisible = false
    @State private var regulationVisible = false
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
        if let id = model.selectedActionID { return record.actions.first { $0.id == id && $0.observedStep <= model.row + 1 } }
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
                    ScrollView {
                        VStack(alignment: .leading, spacing: 8) {
                    if guided && model.comparisonKind == .components { lessonCard }
                    else { comparisonNote }
                    informationFlow
                    primaryEvidence
                    journalPane
                    if !primaryShowsState {
                        DisclosureGroup("Reservoir state and coordinates") { displays.frame(height: 240) }
                            .font(.caption)
                    }
                    actionTimeline
                    playback
                        }
                    }
                }.padding(16).frame(maxWidth: .infinity, maxHeight: .infinity)
                if !guided || evidenceVisible {
                    Divider()
                    ScrollView { inspector.padding(16) }.frame(width: 292)
                }
            }.frame(width: geometry.size.width, height: geometry.size.height)
        }
        .onAppear { if guided { tour.start(model) } }
        .onChange(of: guided) { _, value in readiness.invalidate(); if value { tour.resume(model) } }
        .onChange(of: model.endpoint) { _, _ in readiness.invalidate() }
        .onChange(of: model.modelName) { _, _ in readiness.invalidate() }
        .onChange(of: model.localModel) { _, _ in readiness.invalidate() }
        .onChange(of: model.mode) { _, _ in readiness.invalidate() }
        .onChange(of: model.running) { _, value in if value { readiness.invalidate() } }
        .onChange(of: model.row) { _, _ in if guided { tour.remember(model) } }
        .sheet(isPresented: $regulationVisible) { RegulationExampleView(onClose: { regulationVisible = false }) }
        .onReceive(pulse) { _ in model.tick() }
        .onDisappear { readiness.invalidate(); model.leave() }
        .onChange(of: model.isComparison) { _, paired in if !paired { inspectedArm = .right } }
    }

    private var primaryShowsState: Bool {
        model.comparisonKind == .components && [.minimal, .recurrence, .reservoirReturn].contains(model.stage)
    }
    private var prefixLeft: [ActionFrame] { (model.leftRecord?.frames ?? []).filter { $0.step <= model.row + 1 } }
    private var prefixRight: [ActionFrame] { (model.rightRecord?.frames ?? []).filter { $0.step <= model.row + 1 } }
    private func selectStage(_ stage: ActionStage) {
        if guided { tour.open(stage, model: model) } else { model.select(stage) }
    }
    private var lessonCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            if let error = tour.error { Text(error).foregroundStyle(.orange) }
            if let lesson = tour.lesson(model.stage), tour.matches(model) {
                Text(lesson.question).font(.title3.weight(.medium))
                if model.stage.hasJournal {
                    Picker("Example source", selection: Binding(get: { tour.source }, set: { tour.choose($0, model: model) })) {
                        ForEach(GuidedExampleSource.allCases) { Text($0.title).tag($0) }
                    }.pickerStyle(.segmented).disabled(model.loading || model.working)
                    Text(tour.source == .scripted ? "Fixed words make each mechanism reproducible. No model is contacted."
                         : "Real model writing retained from a completed preparation run. Playback makes no new request.")
                        .font(.caption).foregroundStyle(.secondary)
                } else { Text("Scripted example · no journal component yet").font(.caption).foregroundStyle(mint) }
                Text(lesson.suggestedAction).font(.callout)
                let evidence = GuidedEvidenceEvaluator.evaluate(model.record, cursorStep: model.rightFrame?.step ?? 0)
                VStack(alignment: .leading, spacing: 6) {
                    Text("Expected: " + (tour.source == .recordedModel && model.stage.hasJournal ? lesson.modelExpected : lesson.expected))
                    Text(evidence.state.rawValue + ": " + evidence.observation).foregroundStyle(mint)
                    Text("Interpretation: " + lesson.limitation).foregroundStyle(.secondary)
                }.font(.caption).fixedSize(horizontal: false, vertical: true)
                HStack {
                    Button(tour.nextCheckpoint(model).map { "Continue to step \($0)" }
                           ?? (model.stage == .regulation ? "Tour complete" : "Continue to next component")) { tour.continueLesson(model) }
                        .disabled(model.loading || model.working || (model.stage == .regulation && tour.nextCheckpoint(model) == nil))
                    Button(evidenceVisible ? "Hide evidence details" : "Show evidence details") { evidenceVisible.toggle() }
                    Spacer()
                    Text("\(letter(model.stage)) of H").foregroundStyle(.secondary)
                }.font(.caption)
                if model.stage == .regulation {
                    Button("Compare target error with sustained input…") { model.leave(); regulationVisible = true }.font(.caption)
                }
            } else if model.loading {
                ProgressView("Opening the verified lesson…")
            } else {
                Text("This record is outside the guided example catalog.").font(.headline)
                Text(GuidedEvidenceEvaluator.evaluate(model.record, cursorStep: model.rightFrame?.step ?? 0).observation)
                    .font(.caption)
                Button("Open this component’s guided example") { tour.open(model.stage, model: model) }.font(.caption)
            }
        }.padding(14).background(mint.opacity(0.075), in: RoundedRectangle(cornerRadius: 10))
    }
    private var informationFlow: some View {
        DisclosureGroup("What information reaches the journal?") {
            VStack(alignment: .leading, spacing: 5) {
                Text("Input  →  Reservoir state").font(.callout.monospaced())
                if model.stage.rawValue >= ActionStage.sensoryObserver.rawValue {
                    Text("Input  →  Separate sensory field  →  Sensory measurements").font(.callout.monospaced())
                }
                if model.stage.hasJournal {
                    Text("Sensory measurements  →  Prompt  →  Reply  →  Saved journal").font(.callout.monospaced())
                    if model.comparisonKind == .observation {
                        Text("Added-state arm only: indexed reservoir coordinates + step  →  Prompt").foregroundStyle(mint)
                    } else {
                        Text("The reservoir picture and coordinates are not included in this prompt.").foregroundStyle(.secondary)
                    }
                    if model.stage.hasFeedback { Text("E: Saved journal  →  Encoded next input  →  Reservoir and sensory field") }
                    if model.stage.hasMemory { Text("F: Earlier saved journal  →  Later prompt") }
                    if model.stage.hasChoice { Text("G: WRITE saves a journal; WAIT leaves the earlier return in place") }
                    if model.stage == .regulation { Text("H: Measured fill  →  Controller  →  Next sensory retention") }
                } else { Text("No prompt, model response or journal exists at this stage.").foregroundStyle(.secondary) }
                Text("Scripted examples use local prompt context and fixed replies. Only model recordings or fresh generation contain submitted model requests.")
                    .foregroundStyle(.secondary)
            }.font(.caption).padding(.vertical, 8).textSelection(.enabled)
        }.font(.caption)
    }
    @ViewBuilder private var primaryEvidence: some View {
        if model.comparisonKind == .observation {
            promptPanels
            spectralPanel
        } else {
            switch model.stage {
            case .minimal:
                GuidedLineTrace(title: "Input and resulting state · RMS magnitude", series: [
                    .init(title: "Input", color: previousColor, values: prefixRight.map { GuidedEvidenceEvaluator.rms($0.externalInput) }),
                    .init(title: "State", color: mint, values: prefixRight.map { GuidedEvidenceEvaluator.rms($0.state) })], lower: 0, upper: 1)
                    .frame(height: 100)
                displays.frame(height: 240)
            case .recurrence:
                displays.frame(height: 240)
                ActionDifferenceTrace(left: prefixLeft, right: prefixRight, node: node, row: model.row).frame(height: 85)
            case .sensoryObserver:
                spectralPanel
            case .journalOutput:
                promptPanels
            case .reservoirReturn:
                feedbackPanel
                displays.frame(height: 240)
                ActionDifferenceTrace(left: prefixLeft, right: prefixRight, node: node, row: model.row).frame(height: 70)
            case .journalMemory:
                memoryPanel
                promptPanels
            case .actionChoice:
                choicePanel
            case .regulation:
                regulationPanel
            }
        }
    }
    private var spectralPanel: some View {
        VStack(alignment: .leading, spacing: 9) {
            Text("SEPARATE SENSORY MEASUREMENT").font(.caption.weight(.semibold))
            Text("Measured eigenvalues of the sensory field. These are numerical measurements, not reservoir node values.")
                .font(.caption).foregroundStyle(.secondary)
            HStack(alignment: .top, spacing: 16) {
                if let left = model.leftFrame, let spectrum = left.spectral {
                    GuidedSpectrum(title: "Previous / sensory arm", values: spectrum.eigenvalues,
                        upper: spectrumUpper, color: previousColor)
                } else if model.isComparison { Text("Previous component: no sensory observer").font(.caption).frame(maxWidth: .infinity) }
                if let spectrum = model.rightFrame?.spectral {
                    GuidedSpectrum(title: model.comparisonKind == .observation ? "Added-state arm" : "Current sensory field", values: spectrum.eigenvalues, upper: spectrumUpper, color: mint)
                } else { Text("No measurement at this cursor.").font(.caption) }
            }.frame(height: 155)
            if let fill = model.rightFrame?.fillPercent { Text("Current reduced fill: \(number(fill, 2))% · step \(model.row + 1)").font(.caption.monospacedDigit()) }
        }.padding(12).background(.white.opacity(0.035), in: RoundedRectangle(cornerRadius: 8))
    }
    private var spectrumUpper: Double { max(0.001, max(model.leftFrame?.spectral?.eigenvalues.max() ?? 0, model.rightFrame?.spectral?.eigenvalues.max() ?? 0)) }
    private var promptPanels: some View {
        HStack(alignment: .top, spacing: 12) {
            if let left = model.leftRecord, left.stage.hasJournal { promptPanel(run: left, action: model.leftAction) }
            if let right = model.rightRecord { promptPanel(run: right, action: model.rightAction) }
        }
    }
    private func promptPanel(run: ActionRunRecord, action: ActionReceipt?) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            Text((action?.requestStarted == true ? (model.record?.specification.language.backend == .ollama ? "Exact submitted model prompt" : "Scripted backend prompt") : "Prepared prompt · not sent") + " · " + (run.arm == .left ? "Previous / control" : "Current"))
                .font(.caption.weight(.semibold))
            Text((run.observationChannel ?? .sensory).title).font(.caption2).foregroundStyle(mint)
            ScrollView {
                Text(action?.prompt ?? "No writing opportunity has been reached at this cursor.")
                    .font(.system(size: 12, design: .monospaced)).textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }.frame(height: guided ? 160 : 120)
        }.padding(10).frame(maxWidth: .infinity).background(.white.opacity(0.04), in: RoundedRectangle(cornerRadius: 8))
    }
    private var feedbackPanel: some View {
        VStack(alignment: .leading, spacing: 7) {
            Text("SAVE → PREPARE RETURN → NEXT INPUT").font(.caption.weight(.semibold))
            if let action = model.rightAction {
                Text("Observed \(action.observedStep)  →  \(action.saveReceipt?.status == .saved ? "Journal saved" : "No successful save")  →  "
                     + (model.applicationStepAtCursor(action).map { "Applied at \($0)" } ?? "Not applied at this cursor"))
                    .font(.callout.monospacedDigit())
                if let encoded = action.semanticVector {
                    Text("Prepared return: 48 coordinates · RMS \(number(GuidedEvidenceEvaluator.rms(encoded), 4))")
                        .font(.caption).foregroundStyle(.secondary)
                }
            } else { Text("Continue to the first saved journal.").font(.caption) }
        }.padding(12).background(mint.opacity(0.07), in: RoundedRectangle(cornerRadius: 8))
    }
    private var memoryPanel: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("EARLIER JOURNAL IN THE CURRENT PROMPT").font(.caption.weight(.semibold))
            if let action = model.rightAction, let memory = action.memoryText {
                Text("Opportunity \(action.observedStep) · \(model.record?.specification.language.backend == .ollama ? (action.requestStarted ? "included in submitted model request" : "prepared context · not submitted") : "included in scripted context")")
                    .font(.caption).foregroundStyle(mint)
                ScrollView { Text(memory).font(.system(size: 13)).textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading) }
                    .frame(height: 125)
            } else { Text("No earlier journal is supplied at this cursor. Continue to step 60 in the example.").font(.caption).foregroundStyle(.secondary) }
        }.padding(12).background(.white.opacity(0.04), in: RoundedRectangle(cornerRadius: 8))
    }
    private var choicePanel: some View {
        HStack(alignment: .top, spacing: 12) {
            if let left = model.leftRecord { choiceColumn(left, action: model.leftAction) }
            if let right = model.rightRecord { choiceColumn(right, action: model.rightAction) }
        }
    }
    private func choiceColumn(_ run: ActionRunRecord, action: ActionReceipt?) -> some View {
        VStack(alignment: .leading, spacing: 7) {
            Text(run.stage.title).font(.caption.weight(.medium))
            Text(action?.chosenAction.map(actionTitle) ?? "No choice yet").font(.title2.weight(.medium)).foregroundStyle(mint)
            if let action {
                Text("Opportunity \(action.observedStep) · \(action.status.rawValue)").font(.caption)
                Text(action.chosenAction == .wait ? "No journal; the earlier returned input remains." : action.saveReceipt?.status == .saved ? "Journal saved; inspect its subsequent application." : "No successful saved journal is established.")
                    .font(.caption).foregroundStyle(.secondary)
            }
        }.frame(maxWidth: .infinity, minHeight: 115, alignment: .topLeading)
            .padding(12).background(.white.opacity(0.04), in: RoundedRectangle(cornerRadius: 8))
    }
    private var regulationPanel: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("SENSORY REGULATION · TARGET 68%, DEADBAND ±4 POINTS").font(.caption.weight(.semibold))
            GuidedLineTrace(title: "Reduced fill · %", series: [
                .init(title: "Previous", color: previousColor, values: prefixLeft.compactMap(\.fillPercent)),
                .init(title: "Current", color: mint, values: prefixRight.compactMap(\.fillPercent))], lower: 0, upper: 100, reference: 68)
                .frame(height: 125)
            GuidedLineTrace(title: "Retention used by each field update", series: [
                .init(title: "Previous", color: previousColor, values: prefixLeft.compactMap(\.retentionUsed)),
                .init(title: "Current", color: mint, values: prefixRight.compactMap(\.retentionUsed))], lower: 0.82, upper: 0.995)
                .frame(height: 100)
            Text("A controller update sets the next field retention. It does not directly change reservoir coordinates. This example includes limited control authority.")
                .font(.caption).foregroundStyle(.secondary)
            Button("Open sustained-input target-error comparison…") { model.leave(); regulationVisible = true }.font(.caption)
        }.padding(12).background(.white.opacity(0.035), in: RoundedRectangle(cornerRadius: 8))
    }

    private var sidebar: some View {
        VStack(alignment: .leading, spacing: 13) {
            Text("ESSENTIALS").font(.system(size: 18, weight: .medium, design: .rounded)).tracking(2)
            Text("One addition at a time").font(.caption).foregroundStyle(.secondary)
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 10) {
                    ForEach(ActionStage.allCases) { stage in
                        Button { selectStage(stage) } label: {
                            HStack(alignment: .top, spacing: 8) {
                                Text(letter(stage)).font(.system(.caption, design: .monospaced).weight(.semibold))
                                    .frame(width: 24, height: 24)
                                    .background(stage == model.stage && model.comparisonKind == .components ? mint.opacity(0.25) : .white.opacity(0.06), in: Circle())
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(shortTitle(stage)).font(.caption.weight(.medium))
                                    if stage == model.stage && model.comparisonKind == .components {
                                        Text(stage.addedFeature).font(.caption2).foregroundStyle(.secondary)
                                            .fixedSize(horizontal: false, vertical: true)
                                    }
                                }
                                Spacer(minLength: 0)
                            }.padding(7).frame(maxWidth: .infinity, alignment: .leading)
                                .background(stage == model.stage && model.comparisonKind == .components ? mint.opacity(0.08) : .clear,
                                            in: RoundedRectangle(cornerRadius: 7))
                        }.buttonStyle(.plain)
                    }
                    Divider()
                    Button {
                        if guided {
                            let url = Bundle.module.url(forResource: "example-observation-active-scripted", withExtension: "json")
                                ?? Bundle.module.url(forResource: "example-observation-active-scripted", withExtension: "json", subdirectory: "Resources")
                            if let url { tour.remember(model); model.open(url) }
                            else { model.error = "The packaged active-state scripted comparison is unavailable." }
                        } else { model.selectObservationComparison() }
                    } label: {
                        Text(guided ? "Active-state comparison · scripted" : "What can the journal observe?").font(.caption).foregroundStyle(mint)
                            .multilineTextAlignment(.leading).fixedSize(horizontal: false, vertical: true)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }.buttonStyle(.plain)
                    HStack {
                        Button("Previous") { if let p = model.stage.previous { selectStage(p) } }.disabled(model.stage.previous == nil)
                        Button("Next") { if let n = ActionStage(rawValue: model.stage.rawValue + 1) { selectStage(n) } }.disabled(model.stage == .regulation)
                    }.font(.caption)
                    Divider()
                    if guided {
                        Text("Eight components · explore them in any order").font(.caption2).foregroundStyle(.secondary)
                        Button("Try an experiment") { tour.remember(model); model.prepareExperiment(); onTryExperiment() }.font(.caption)
                        Text("Examples play locally. New experiments have their own settings and records.")
                            .font(.caption2).foregroundStyle(.secondary)
                    } else {
                        DisclosureGroup("Experiment settings") { runSettings.padding(.top, 8); studyNotes }
                            .font(.caption)
                        Button { model.loadExample() } label: { Label("Open example", systemImage: "play.rectangle") }
                            .font(.caption).disabled(model.running || model.working)
                    }
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
                .disabled(model.running || model.working || model.comparisonKind == .observation)
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
                    Text("JSON · 4,096-token context · 256-token output · temperature 0").font(.caption2).foregroundStyle(.secondary)
                    LocalModelReadinessView(model: readiness, endpoint: model.endpoint, modelName: model.modelName)
                        .disabled(model.running || model.working)
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
                Text(model.comparisonKind == .observation ? "What can the journal observe?" : guided ? "From input to journal" : "Actions & comparisons").font(.system(size: 21, weight: .medium))
                Spacer(minLength: 6)
                Button("Open…") { model.chooseFile() }.disabled(model.running || model.working)
                Button("Export…") { model.export() }.disabled(model.record == nil || model.running || model.working)
            }
            HStack(spacing: 7) {
                Circle().fill(model.running || model.replaying ? mint : .gray).frame(width: 5, height: 5)
                Text(model.status).font(.caption).foregroundStyle(.secondary).lineLimit(2)
                Spacer(minLength: 4)
                if let frame = model.rightFrame {
                    Text("Step \(frame.step) · \(number(frame.time, 2)) s").font(.caption.monospacedDigit())
                }
            }
            if !model.isRecording && model.stage.hasJournal && model.mode == .independentGeneration && model.localModel &&
                (model.endpoint.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || model.modelName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty) {
                Text("Choose a local endpoint and installed model in Experiment settings before starting.")
                    .font(.caption).foregroundStyle(.secondary)
            }
            if let error = model.error { Text(error).font(.caption).foregroundStyle(.orange).textSelection(.enabled) }
            if let issue = model.saveIssue { HStack { Text(issue).font(.caption).foregroundStyle(.orange); Button("Retry save") { model.retrySaves() }; Button("Export retained") { model.exportRetained() } } }
        }
    }

    private var controls: some View {
        VStack(alignment: .leading, spacing: 6) {
        HStack(spacing: 7) {
            Button { model.run() } label: {
                Label(model.isRecording ? "Play" : "Run", systemImage: "play.fill").padding(.horizontal, 10).padding(.vertical, 5)
                    .background(mint.opacity(model.canRun ? 1 : 0.35), in: RoundedRectangle(cornerRadius: 5))
                    .foregroundStyle(.black)
            }.buttonStyle(.plain).disabled(!model.canRun)
            Button("Stop") { model.stop() }.disabled(!model.running && !model.replaying && !model.working)
            Button("Step") { model.step() }.disabled(!model.canStep)
            Button("Next journal") { model.nextJournal() }.disabled(!model.stage.hasJournal || model.working || model.loading)
            Button("Replay") { model.replay() }.disabled(model.framesCount == 0 || model.working)
        }
        HStack(spacing: 7) {
            if !guided {
                Button("Write journal") { model.writeJournal() }.disabled(!model.canWrite)
                    .help("Request an explicit writing action at the current boundary. This is a human request.")
                if model.isRecording { Button("New experiment") { model.prepareExperiment() } }
            }
            Spacer(minLength: 3)
            Button(model.comparisonKind == .observation ? "Compare observations" : "Compare with previous") {
                if guided {
                    tour.remember(model); model.compareWithPrevious(); onTryExperiment()
                } else { model.compareWithPrevious() }
            }.disabled(model.loading || model.working || model.stage.previous == nil)
        }
        }.font(.caption)
    }

    private var comparisonNote: some View {
        VStack(alignment: .leading, spacing: 4) {
            if let record = model.record {
                let spec = record.specification
                Text(spec.comparisonKind == .observation ? "Sensory-only ↔ sensory + reservoir · stage D in both arms" : record.left == nil ? spec.stage.title : "\(letter(record.left!.stage)) → \(letter(spec.stage)) · Added: \(spec.stage.addedFeature)")
                    .font(.caption.weight(.medium)).foregroundStyle(mint)
                Text("Seed \(spec.seed) · leak \(number(spec.leak, 2)) · input \(number(spec.inputStrength, 2)) · noise \(number(spec.noiseAmplitude, 2)) · bias \(spec.biasEnabled ? "on" : "off")")
                    .font(.caption2).foregroundStyle(.secondary)
                Text(spec.comparisonKind == .observation ? "Identical measured trajectory. Feedback, memory, choice and regulation are off." : spec.mode == .fixedReplay
                     ? "Matched external forcing; retained words and vectors stay fixed."
                     : "Matched setup; each arm's replies can change its later trajectory.")
                    .font(.caption2).foregroundStyle(.secondary)
                if spec.comparisonKind == .observation {
                    Text(spec.forcingProfile == .continuousSensoryV1 ? "Active-state example · sensory input remains active at writing opportunities."
                         : "Quiet-state example · writing opportunities follow 18 quiet steps.")
                        .font(.caption).foregroundStyle(mint)
                    if guided {
                        Button(evidenceVisible ? "Hide evidence details" : "Show evidence details") { evidenceVisible.toggle() }
                            .font(.caption)
                    }
                }
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
                    statePanel(title: model.comparisonKind == .observation ? "Sensory measurements only" : left.stage.title, frame: model.leftFrame, color: previousColor,
                               empty: model.framesCount == 0 ? "Initial state" : "No matching observation")
                }
                statePanel(title: model.comparisonKind == .observation ? "Sensory + reservoir coordinates" : model.rightRecord?.stage.title ?? model.stage.title, frame: model.rightFrame,
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

    private var journalPane: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("JOURNAL AT THE CURSOR").font(.system(size: 10, weight: .semibold)).tracking(1)
                Spacer()
                Text(model.provenance).font(.caption2).foregroundStyle(mint)
            }
            if !model.stage.hasJournal {
                Text("No journal component yet. Stage D adds writing; the preceding stages expose numerical behavior.")
                    .font(.caption).foregroundStyle(.secondary)
            } else {
                HStack(alignment: .top, spacing: 12) {
                    if let left = model.leftRecord { journalColumn(left, action: model.leftAction) }
                    if let right = model.rightRecord { journalColumn(right, action: model.rightAction) }
                    else { Text("Run or open an example to inspect the first journal opportunity.").font(.caption) }
                }
            }
        }.padding(10).background(.white.opacity(0.04), in: RoundedRectangle(cornerRadius: 8))
    }
    private func journalColumn(_ run: ActionRunRecord, action: ActionReceipt?) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(model.comparisonKind == .observation ? (run.observationChannel ?? .sensory).title : run.stage.title).font(.caption.weight(.medium)).foregroundStyle(mint)
            if !run.stage.hasJournal {
                Text("No journal component in this arm.").font(.caption).foregroundStyle(.secondary).frame(height: 100)
            } else if model.journalPending {
                Text("Journal opportunity pending at step \(model.row + 1) · simulated time is paused.").font(.caption).foregroundStyle(.secondary).frame(height: 100)
            } else if let action {
                Text("Observed step \(action.observedStep) · \(action.saveReceipt?.status == .failed ? "journal save failed" : action.status.rawValue)" + (action.requestOrder.map { " · request \($0)" } ?? ""))
                    .font(.caption2).foregroundStyle(.secondary)
                if action.status == .failed && action.rawReply != nil && !run.journals.contains(where: { $0.id == action.journalEntryID }) {
                    Text(action.providerComplete == false ? "No saved journal · incomplete response retained below." : "No saved journal · response retained below.")
                        .font(.caption2).foregroundStyle(.orange)
                }
                ScrollView {
                    Text(run.journals.first(where: { $0.id == action.journalEntryID })?.text
                         ?? (action.chosenAction == .wait ? "WAIT · no journal was written." : action.rawReply ?? action.failure ?? "No completed journal at this opportunity."))
                        .font(.system(size: 13)).textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading)
                }.frame(height: guided ? 170 : 120)
            } else {
                Text("No journal opportunity at or before this step.")
                    .font(.caption).foregroundStyle(.secondary).frame(height: 100)
            }
        }.frame(maxWidth: .infinity, alignment: .leading)
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
                    ForEach(arm.actions.filter { $0.observedStep <= model.row + 1 }) { action in
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
            if primaryShowsState { coordinateInspector; Divider() }
            if model.isComparison {
                Picker("Inspect arm", selection: $inspectedArm) {
                    Text(model.comparisonKind == .observation ? "Sensory" : "Previous").tag(ActionArm.left)
                    Text(model.comparisonKind == .observation ? "+ State" : "Current").tag(ActionArm.right)
                }.pickerStyle(.segmented).labelsHidden().controlSize(.small)
            }
            Text(activeRecord?.stage.title ?? model.stage.title).font(.caption.weight(.medium))
            if let record = activeRecord, !record.actions.isEmpty {
                Picker("Action", selection: Binding(get: { model.selectedActionID ?? 0 }, set: { model.selectedActionID = $0 == 0 ? nil : $0 })) {
                    Text("Latest at cursor").tag(0)
                    ForEach(record.actions.filter { $0.observedStep <= model.row + 1 }) { Text("\($0.id) · step \($0.observedStep)").tag($0.id) }
                    if let id = model.selectedActionID, !record.actions.contains(where: { $0.id == id }) {
                        Text("\(id) · unavailable in this arm").tag(id)
                    }
                }.font(.caption)
            }
            if let action = activeAction { actionInspector(action) }
            else { Text("No action receipt at this cursor or selected opportunity.").font(.caption).foregroundStyle(.secondary) }
            if !primaryShowsState { DisclosureGroup("Exact coordinates and measurements") { coordinateInspector } }
            Divider()
            Text(model.comparisonKind == .observation ? "Both arms share the same trajectory. Only the designated arm receives the 32 indexed reservoir coordinates." : "Writing observes the separate sensory field fed by input. Reservoir activations are not part of this prompt; recurrence alone does not change that observation.")
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
                metric(model.comparisonKind == .observation ? "Sensory arm" : "Previous", model.leftFrame.map { number($0.state[node], 6) } ?? "Unavailable")
                metric(model.comparisonKind == .observation ? "Added-state arm" : "Current", model.rightFrame.map { number($0.state[node], 6) } ?? "Unavailable")
                metric("Right − left", pairedValue { $1.state[node] - $0.state[node] })
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
            metric("Codec return", model.applicationStepAtCursor(action).map { "Applied at step \($0)" }
                ?? (action.semanticVector == nil ? "Not prepared" : "Prepared; not applied at this cursor"))
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
                Text("Node \(node) · right − left").font(.caption2)
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
        }.accessibilityLabel("Exact recorded difference for node \(node), right minus left. Fixed scale minus two to plus two.")
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
