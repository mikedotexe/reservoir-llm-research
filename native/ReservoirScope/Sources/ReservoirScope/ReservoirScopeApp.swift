import SwiftUI
import Metal

@main
enum ReservoirScopeEntry {
    @MainActor static func main() {
        if ReservoirProfiler.runIfRequested(arguments: CommandLine.arguments) { return }
        if StateSurfaceProfiler.runIfRequested() { return }
        ReservoirScopeApp.main()
    }
}

struct ReservoirScopeApp: App {
    @NSApplicationDelegateAdaptor(ScopeApplicationDelegate.self) private var appDelegate
    var body: some Scene {
        WindowGroup("Reservoir Scope") {
            ScopeWorkspace()
        }
        .defaultSize(width: 1380, height: 940)
        .windowStyle(.titleBar)
        .commands { CommandGroup(replacing: .newItem) {} }
    }
}

private enum Palette {
    static let fill = Color(red: 0.24, green: 0.79, blue: 0.91)
    static let shelf = Color(red: 0.38, green: 0.82, blue: 0.62)
    static let rail = Color(red: 1.0, green: 0.62, blue: 0.34)
    static let leak = Color(red: 0.73, green: 0.61, blue: 0.98)
    static let panel = Color(red: 0.075, green: 0.09, blue: 0.12)
}

struct Observatory: View {
    let evidence: EvidenceStore
    private let recordedWatermarks: FillWatermarkMemoryHistory
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @AppStorage("smoothLiveFill", store: ScopePreferences.store) private var smoothLiveFill = true
    @AppStorage("allowFillMotionWithReducedMotion", store: ScopePreferences.store) private var allowFillMotionWithReducedMotion = false
    @StateObject private var live = LiveTelemetryMonitor()
    @StateObject private var stateLive = LiveStateMonitor()
    @State private var liveStateEnabled = false
    @State private var stateSourcePath = ""
    @State private var mode: ReservoirSceneMode = .fill
    @State private var historicalIndex = 0
    @State private var stateIndex = 0
    @State private var isPlaying = false
    @State private var replaySpeed = 20.0
    @State private var replayClock = ReplayClock()
    @State private var replayPosition = 0.0
    @State private var healthWatermarks = FillWatermarkMemory()
    @State private var activationWatermarks = FillWatermarkMemory()
    @State private var selectedZoneID = "target"
    @State private var cutaway = true
    @State private var showBands = true
    @State private var liveEnabled = false
    @State private var selectedComponent = 0
    @State private var selectedNode = 0
    @State private var sourcePath = ""
    @State private var showMethods = false
    init(evidence: EvidenceStore) {
        self.evidence = evidence
        recordedWatermarks = FillWatermarkMemoryHistory(observations: evidence.historical.samples.enumerated().map {
            FillWatermarkObservation(fillPct: $0.element.fillPct,
                sourceTime: $0.element.date?.timeIntervalSince1970 ?? .nan, ordinal: UInt64($0.offset))
        })
    }
    private let pulse = Timer.publish(every: 0.05, on: .main, in: .common).autoconnect()
    private var sample: ReservoirSample { evidence.historical.samples[historicalIndex] }
    private var state: StateGeometrySample { liveStateEnabled ? (stateLive.latest?.geometry ?? evidence.geometry.samples[0]) : evidence.geometry.samples[stateIndex] }
    private var inStateView: Bool { mode == .trajectory }
    private var usesLive: Bool { liveStateEnabled || (liveEnabled && !inStateView) }
    private var waitingForSource: Bool { liveStateEnabled ? stateLive.latest == nil : (usesLive && live.latest == nil) }
    private var sourceStatus: String { liveStateEnabled ? stateLive.statusText : live.statusText }
    private var currentFill: Double { liveStateEnabled ? (stateLive.latest?.fillPct ?? .nan) : usesLive ? (live.latest?.fillPct ?? .nan) : sample.fillPct }
    private var currentSpectrum: [Double] { liveStateEnabled ? [] : usesLive ? (live.latest?.spectralValues ?? []) : sample.cascade }
    private var currentLeak: Double? { liveStateEnabled ? nil : usesLive ? live.latest?.leak : sample.esnLeak }
    private var device: MTLDevice? { MTLCreateSystemDefaultDevice() }
    private var modelPoints: [[Double]] { liveStateEnabled ? stateLive.samples.map { $0.geometry.pc } : evidence.geometry.samples.map(\.pc) }
    private var selectedStateIndex: Int { liveStateEnabled ? max(0, stateLive.samples.count - 1) : stateIndex }
    private var currentProjectionFraction: Double? { guard !waitingForSource, state.centeredNorm > 0 else { return nil }; return pow(state.projectedNorm / state.centeredNorm, 2) }
    private var spectrumScale: Double { max(1, evidence.historical.samples.flatMap(\.cascade).max().map(sqrt) ?? 1) }

    private var bands: ReferenceBands { evidence.historical.bands }
    private var zones: [ReferenceZone] { ReferenceZone.catalog(bands: bands, configuration: evidence.historical.controller.structuralConfig) }
    private var selectedZone: ReferenceZone { zones.first { $0.id == selectedZoneID } ?? zones[0] }
    private var shelfRange: ClosedRange<Double> { bands.shelfMinPct...bands.shelfMaxPct }
    private var isZoneView: Bool { mode == .zones }
    private var fillMotionAllowed: Bool { !reduceMotion || allowFillMotionWithReducedMotion }
    private var smoothFill: Bool { usesLive && smoothLiveFill && fillMotionAllowed && (mode == .fill || isZoneView) }
    private var fillSourceContext: String {
        liveStateEnabled ? "state:\(stateSourcePath)" : usesLive ? "health:\(sourcePath):\(live.latest?.sessionId ?? -1)" : "recorded"
    }
    private var fillSourceTime: Double? { liveStateEnabled ? stateLive.latest.map { Double($0.tMs) / 1000 } : usesLive ? live.latest?.elapsedS : nil }
    private var fillSourceIsFresh: Bool {
        let date = liveStateEnabled ? stateLive.lastSourceDate : live.lastSourceDate
        let error = liveStateEnabled ? stateLive.lastError : live.lastError
        guard error == nil, let date else { return false }
        return (-5...12).contains(Date().timeIntervalSince(date))
    }
    private var watermarkSourceTime: Double {
        if liveStateEnabled { return activationWatermarks.latestSourceTime ?? .nan }
        if usesLive { return healthWatermarks.latestSourceTime ?? .nan }
        // Exported UTC is rounded to milliseconds; never place its selected
        // observation just ahead of the more precise elapsed replay clock.
        let origin = evidence.historical.samples[0].date?.timeIntervalSince1970 ?? 0
        return max(sample.date?.timeIntervalSince1970 ?? origin, origin + replayPosition)
    }
    private var watermarks: [FillWatermarkMemoryRange] {
        if liveStateEnabled { return activationWatermarks.ranges(at: watermarkSourceTime) }
        if usesLive { return healthWatermarks.ranges(at: watermarkSourceTime) }
        return recordedWatermarks.ranges(through: historicalIndex, at: watermarkSourceTime)
    }
    private var watermarkScope: String {
        liveStateEnabled ? "Activation batch · source time" : usesLive ? "Health · current session" : "Recorded · follows playhead"
    }

    var body: some View {
        HStack(spacing: 0) {
            sidebar.frame(width: 205)
            Divider()
            VStack(spacing: 0) {
                titlebar.padding(.horizontal, 24).padding(.top, 20).padding(.bottom, 14)
                Divider()
                if mode == .response {
                    StateResponseExperience()
                } else if mode == .surface {
                    StateSurfaceExperience(evidence: evidence, liveSample: stateLive.latest,
                        followsState: liveStateEnabled, healthOnly: liveEnabled,
                        sourceStatus: liveStateEnabled ? stateLive.statusText : "Select a retained capture or the live activation recorder.",
                        sourceFresh: fillSourceIsFresh,
                        onFollow: { selectFeed($0 ? "states" : "recorded") }, onChooseFile: chooseStateFile)
                } else {
                HStack(alignment: .top, spacing: 0) {
                    center.padding(20).frame(maxWidth: .infinity, maxHeight: .infinity)
                    Divider()
                    ScrollView { inspector.padding(20) }.frame(width: 290)
                }
                }
            }
        }
        .background(Color(red: 0.035, green: 0.045, blue: 0.065))
        .preferredColorScheme(.dark)
        .frame(minWidth: 1100, minHeight: 780)
        .onAppear {
            sourcePath = evidence.historical.controller.snapshot?.source?.path ?? ""
            if !sourcePath.isEmpty { stateSourcePath = URL(fileURLWithPath: sourcePath).deletingLastPathComponent().appendingPathComponent("runtime/esn_activation_trace_v1.json").path }
        }
        .onChange(of: mode) { _, _ in isPlaying = false }
        .onChange(of: replaySpeed) { old, _ in if isPlaying { advancePlayback(rate: old) } }
        .onReceive(pulse) { _ in advancePlayback() }
        .onReceive(live.$samples) { receiveHealthWatermarks($0) }
        .onReceive(stateLive.$samples) { receiveActivationWatermarks($0) }
        .onDisappear { isPlaying = false; live.stop(); stateLive.stop() }
        .sheet(isPresented: $showMethods) { methodsSheet }
    }

    private var sidebar: some View {
        VStack(alignment: .leading, spacing: 24) {
            VStack(alignment: .leading, spacing: 7) {
                Image(systemName: "circle.hexagongrid.fill").font(.system(size: 27)).foregroundStyle(Palette.fill)
                Text("RESERVOIR\nSCOPE").font(.system(size: 20, weight: .medium, design: .rounded)).tracking(2)
                Text("A research instrument").font(.caption).foregroundStyle(.secondary)
            }
            VStack(alignment: .leading, spacing: 8) {
                sectionLabel("OBSERVE")
                modeButton(.fill, "Fill sphere", "circle.lefthalf.filled")
                modeButton(.zones, "Reference zones", "scope")
                modeButton(.surface, "State surface", "globe")
                modeButton(.response, "Response lab", "arrow.triangle.branch")
                modeButton(.trajectory, "State trajectory", "point.3.connected.trianglepath.dotted")
                modeButton(.spectral, "Spectral magnitudes", "waveform.path")
            }
            VStack(alignment: .leading, spacing: 10) {
                sectionLabel("DATA SOURCE")
                Picker("Source", selection: Binding(get: { liveStateEnabled ? "states" : liveEnabled ? "health" : "recorded" }, set: { selectFeed($0) })) {
                    Text("Recorded").tag("recorded")
                    Text("Live fill & control").tag("health")
                    Text("Live state & fill").tag("states")
                }.labelsHidden().accessibilityLabel("Observation source").disabled(mode == .response)
                if mode == .response {
                    Text("Choose a source in Response lab").font(.caption2).foregroundStyle(.secondary)
                } else if liveStateEnabled {
                    Text("Co-recorded state and fill. Exact state-step timing is unavailable.").font(.caption2).foregroundStyle(.secondary)
                    Button("Choose state file…") { chooseStateFile() }.font(.caption)
                } else if liveEnabled {
                    Text("Live scalar snapshots. State trajectory remains the frozen capture.").font(.caption2).foregroundStyle(.secondary)
                }
                Divider()
                sectionLabel("EVIDENCE")
                if mode == .response {
                Text("Response sources").font(.callout)
                Text("Native action receipts\nSeparate esn-divide simulation").font(.caption).foregroundStyle(.secondary)
                Divider()
                Text("128 coordinates").font(.callout)
                Text("Exact states and differences\nSource identity inside each view").font(.caption).foregroundStyle(.secondary)
                Divider()
                Text("Preview volume").font(.callout)
                Text("68% display size\nNo measured fill or time").font(.caption).foregroundStyle(.secondary)
                } else {
                Text("Minime’s native ESN").font(.callout)
                Text("128 state dimensions\n512-D sensory field").font(.caption).foregroundStyle(.secondary)
                Divider()
                Text("Recorded replay").font(.callout)
                Text("Sep 6 · 09:09–09:29 PT\n507 paired observations").font(.caption).foregroundStyle(.secondary)
                Divider()
                Text("State capture").font(.callout)
                Text("1,024 recorded states\nSeparate source window").font(.caption).foregroundStyle(.secondary)
                }
            }
            Spacer()
            Button { showMethods = true } label: { Label("Mapping & sources", systemImage: "info.circle") }.buttonStyle(.plain)
            VStack(alignment: .leading, spacing: 5) {
                Label("Metal GPU", systemImage: "cpu").font(.caption)
                Text(device?.name ?? "GPU unavailable").font(.caption2).foregroundStyle(.secondary)
                Text(device?.hasUnifiedMemory == true ? "Unified memory available" : "Discrete GPU memory").font(.caption2).foregroundStyle(.secondary)
            }
        }.padding(20).background(Palette.panel.opacity(0.62))
    }

    private func modeButton(_ value: ReservoirSceneMode, _ title: String, _ icon: String) -> some View {
        Button { mode = value } label: {
            Label(title, systemImage: icon).font(.callout).frame(maxWidth: .infinity, alignment: .leading).padding(.vertical, 9).padding(.horizontal, 10)
                .background(mode == value ? Palette.fill.opacity(0.15) : .clear, in: RoundedRectangle(cornerRadius: 7))
                .foregroundStyle(mode == value ? Palette.fill : .primary)
        }.buttonStyle(.plain)
    }

    private var titlebar: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 6) {
                Text(mode == .response ? "Actions and observed state" : mode == .surface ? "A surface you can read" : inStateView ? "The shape of a changing state" : mode == .fill ? "A reservoir, made visible" : isZoneView ? "The reference zones, up close" : "Spectral structure, without invented geometry")
                    .font(.system(size: 22, weight: .medium))
                Text(mode == .response ? "Native application boundaries and a separate simulated response study" : mode == .surface ? "Actual node values, frozen modes and calibrated relief on a fixed map" : inStateView ? "A fixed PCA projection of actual 128-dimensional state vectors" : mode == .fill ? "Fill volume, reference comfort zones, and the control signals alongside them" : isZoneView ? "Select a boundary to explore the regulator’s intended operating limits" : "Three recorded sensory-covariance estimates, held in their original slot order")
                    .font(.callout).foregroundStyle(.secondary)
            }
            Spacer(minLength: 12)
            Text(mode == .response ? "RESPONSE LAB" : liveStateEnabled ? "LIVE STATE + FILL" : inStateView || mode == .surface ? "STATE CAPTURE" : usesLive ? "READ-ONLY LIVE" : "RECORDED")
                .font(.system(size: 10, weight: .medium, design: .monospaced)).tracking(1.2)
                .padding(.horizontal, 10).padding(.vertical, 7).background(Palette.fill.opacity(0.12), in: Capsule()).foregroundStyle(Palette.fill)
        }
    }

    private var center: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(alignment: .firstTextBaseline, spacing: 24) {
                if inStateView {
                    if liveStateEnabled {
                        readout("CURRENT DISTANCE² VISIBLE", currentProjectionFraction.map { percent($0 * 100) } ?? (waitingForSource ? "Waiting" : "Undefined"), color: Palette.fill)
                        readout("CO-RECORDED FILL", waitingForSource ? "Waiting" : percent(currentFill), color: Palette.rail)
                    } else {
                        readout("VARIANCE VISIBLE", percent(evidence.geometry.pca.retainedFraction * 100), color: Palette.fill)
                        readout("OUTSIDE THIS PROJECTION", percent((1 - evidence.geometry.pca.retainedFraction) * 100), color: Palette.rail)
                    }
                } else {
                    readout(usesLive ? "MEASURED FILL" : "FILL", waitingForSource ? "Waiting" : percent(currentFill), color: Palette.fill)
                    if isZoneView { readout("SELECTED REFERENCE", selectedZone.thresholdLabel, color: Palette.leak) }
                    else { readout("REPORTED LEAK α", number(currentLeak, digits: 3), color: Palette.leak) }
                }
                Spacer()
            }
            ZStack(alignment: .bottomLeading) {
                if waitingForSource || (usesLive && mode == .spectral && currentSpectrum.isEmpty) {
                    ContentUnavailableView(waitingForSource ? "Waiting for a source snapshot" : "Spectral directions are not in this feed", systemImage: "waveform.path", description: Text(waitingForSource ? sourceStatus : "This live source does not contain the sensory cascade. Recorded replay includes three direction estimates."))
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                ReservoirScene(mode: mode, fillPct: currentFill, points: modelPoints, selectedIndex: selectedStateIndex,
                    referenceRadius: inStateView ? evidence.geometry.pca.normalization.referenceRadius : spectrumScale,
                    cutaway: mode == .fill ? cutaway : false, showBands: isZoneView || showBands, spectralValues: currentSpectrum,
                    componentVariances: Array(evidence.geometry.pca.explainedVarianceRatio.prefix(3)),
                    zoneThresholds: zones.map(\.thresholdPct), selectedZonePct: selectedZone.thresholdPct,
                    zoneShelfBounds: [bands.shelfMinPct, bands.shelfMaxPct],
                    smoothFill: smoothFill, fillSourceIsFresh: fillSourceIsFresh,
                    fillSourceContext: fillSourceContext, fillSourceTime: fillSourceTime)
                    .id(mode)
                    .accessibilityLabel(inStateView ? "Three dimensional projected reservoir trajectory" : "Three dimensional reservoir geometry")
                }
                if isZoneView && !waitingForSource {
                    zoneAnnotation
                    ReferenceWatermarksView(ranges: watermarks, sourceTime: watermarkSourceTime,
                        scope: watermarkScope, reducedMotion: reduceMotion)
                }
                VStack(alignment: .leading, spacing: 4) {
                    Text(inStateView ? "Center = captured-window mean" : mode == .fill ? "Center → boundary = cube root of fill fraction" : isZoneView ? "Violet: \(selectedZone.title) · \(selectedZone.thresholdLabel)" : "Spoke length = square root of recorded estimate")
                    Text(smoothFill ? "Cyan eases toward fill · white dashes = latest reading" : inStateView ? "Sphere = frozen capture’s maximum full-state distance" : mode == .fill ? "Volume metaphor · not a spectral stability boundary" : isZoneView ? "Cyan = observed fill · green = reference shelf" : "Directions are schematic · not measured eigenvectors")
                        .foregroundStyle(.secondary)
                }.font(.caption).padding(12).background(.black.opacity(0.36), in: RoundedRectangle(cornerRadius: 8)).padding(12)
            }
            .frame(minHeight: 300, maxHeight: .infinity)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            HStack {
                Text(isZoneView ? "Fixed 12× lens · cube-root radii · 54–82% crop" : "Drag to orbit · scroll to zoom").font(.caption).foregroundStyle(.secondary)
                Spacer()
                if mode == .fill {
                    Toggle("Cutaway", isOn: $cutaway).toggleStyle(.checkbox)
                    Toggle("Reference zones", isOn: $showBands).toggleStyle(.checkbox)
                }
            }
                if inStateView { stateControls } else { telemetryControls }
        }
    }

    private var zoneAnnotation: some View {
        GeometryReader { geometry in
            let anchor = ReferenceLens.point(fillPct: selectedZone.thresholdPct, angle: 0.055,
                width: geometry.size.width, height: geometry.size.height)
            let labelWidth = min(190.0, max(110.0, anchor.x - 42))
            if anchor.x.isFinite && anchor.y.isFinite {
                Path { path in
                    path.move(to: CGPoint(x: 18, y: anchor.y - 6))
                    path.addLine(to: CGPoint(x: anchor.x - 14, y: anchor.y - 6))
                    path.addLine(to: CGPoint(x: anchor.x, y: anchor.y))
                }.stroke(Palette.leak.opacity(0.8), lineWidth: 1)
                Circle().fill(Palette.leak).frame(width: 5, height: 5)
                    .position(x: anchor.x, y: anchor.y)
                VStack(alignment: .leading, spacing: 3) {
                    Text(selectedZone.thresholdLabel).font(.system(size: 22, weight: .light, design: .rounded)).monospacedDigit()
                    Text(selectedZone.title).font(.caption)
                }.foregroundStyle(Palette.leak).padding(8)
                    .frame(width: labelWidth, alignment: .leading)
                    .background(.black.opacity(0.42), in: RoundedRectangle(cornerRadius: 7))
                    .position(x: 18 + labelWidth / 2, y: anchor.y - 43)
            }
        }.allowsHitTesting(false)
    }

    private var telemetryControls: some View {
        VStack(alignment: .leading, spacing: 12) {
            if mode == .fill || isZoneView {
                ViewThatFits(in: .horizontal) {
                    HStack(spacing: 22) { liveFillToggles }
                    VStack(alignment: .leading, spacing: 8) { liveFillToggles }
                }
                if usesLive {
                    Text(reduceMotion && !allowFillMotionWithReducedMotion
                        ? "Reduce Motion is on · enable Smooth fill transitions to allow gentle motion only here."
                        : reduceMotion && smoothLiveFill
                        ? "Gentle motion allowed in this app · measured readings still update immediately."
                        : smoothLiveFill
                        ? "0.8-second visual easing · readings and controller values update immediately."
                        : "Fill updates directly to each received reading.")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
            HStack(spacing: 14) {
                legend("Fill", Palette.fill); legend("Shelf \(number(bands.shelfMinPct, digits: 0))–\(number(bands.shelfMaxPct, digits: 0))%", Palette.shelf); legend("Rails \(number(bands.strongRailPct, digits: 0)) / \(number(bands.forceRailPct, digits: 0))%", Palette.rail)
                Spacer(); Text("Target \(number(bands.targetPct, digits: 0))%").font(.caption).foregroundStyle(.secondary)
            }
            if liveStateEnabled {
                SignalChart(title: "Co-recorded fill (%)", series: [stateLive.samples.map { (Double($0.tMs) / 1000, $0.fillPct) }], colors: [Palette.fill], selectedX: stateLive.latest.map { Double($0.tMs) / 1000 } ?? 0, referenceBand: shelfRange, fixedDomain: 0...100, onSelect: nil).frame(height: 96)
                activationStatus
            } else if usesLive {
                SignalChart(title: "Live fill (%)", series: [live.samples.map { ($0.elapsedS, $0.fillPct) }], colors: [Palette.fill], selectedX: live.latest?.elapsedS ?? 0, referenceBand: shelfRange, fixedDomain: 0...100, onSelect: nil).frame(height: 96)
                Text(live.statusText).font(.caption).foregroundStyle(.secondary).lineLimit(2)
            } else {
                SignalChart(title: "Fill (%)", series: [evidence.historical.samples.map { ($0.tS, $0.fillPct) }], colors: [Palette.fill], selectedX: sample.tS, referenceBand: shelfRange, fixedDomain: 56...80, onSelect: selectHistoricalTime).frame(height: 88)
                if !isZoneView { SignalChart(title: "Reported leak α", series: [evidence.historical.samples.compactMap { s in s.esnLeak.map { (s.tS, $0) } }], colors: [Palette.leak], selectedX: sample.tS, onSelect: selectHistoricalTime).frame(height: 88) }
                playbackBar
                Slider(value: Binding(get: { Double(historicalIndex) }, set: { selectHistoricalIndex(Int($0)) }), in: 0...Double(evidence.historical.samples.count - 1), step: 1).accessibilityLabel("Recorded observation")
            }
        }
    }

    @ViewBuilder private var liveFillToggles: some View {
        Toggle("Follow health snapshots", isOn: Binding(get: { liveEnabled }, set: { enableLive($0) }))
            .toggleStyle(.switch).controlSize(.small)
            .help("Follow the existing health feed in real time. Select Live state & fill in the sidebar to follow activation batches instead.")
        Toggle("Smooth fill transitions", isOn: Binding(get: { smoothLiveFill && fillMotionAllowed }, set: {
            smoothLiveFill = $0
            if reduceMotion { allowFillMotionWithReducedMotion = $0 }
        }))
            .toggleStyle(.switch).controlSize(.small).disabled(!usesLive)
            .help("Ease only the cyan surface. Measured values stay immediate. With Reduce Motion on, explicitly enabling this permits gentle fill motion only in this app.")
    }

    private var stateControls: some View {
        VStack(alignment: .leading, spacing: 10) {
            if liveStateEnabled {
                activationStatus
            } else {
                playbackBar
                Slider(value: Binding(get: { Double(stateIndex) }, set: { stateIndex = Int($0); isPlaying = false }), in: 0...Double(evidence.geometry.samples.count - 1), step: 1).accessibilityLabel("State row")
            }
            HStack {
                Text("Mode loadings").font(.callout)
                Picker("Principal component", selection: $selectedComponent) {
                    ForEach(0..<3) { i in Text("PC\(i+1)").tag(i) }
                }.pickerStyle(.segmented).labelsHidden().frame(width: 150)
                Spacer()
                Text("Signed weights · all 128 nodes").font(.caption).foregroundStyle(.secondary)
            }
            LoadingsChart(values: evidence.geometry.pca.components[selectedComponent], selected: $selectedNode).frame(height: 85)
            HStack {
                Text("Node \(selectedNode + 1) · loading \(number(evidence.geometry.pca.components[selectedComponent][selectedNode], digits: 4))").font(.caption).monospacedDigit()
                Spacer()
                Stepper("Node", value: $selectedNode, in: 0...127).labelsHidden().accessibilityLabel("Inspect node loading")
            }
        }
    }

    private var playbackBar: some View {
        HStack(spacing: 14) {
            Button { togglePlayback() } label: { Label(isPlaying ? "Pause" : "Play", systemImage: isPlaying ? "pause.fill" : "play.fill") }.keyboardShortcut(.space, modifiers: [])
            if inStateView {
                Text("Row \(stateIndex + 1) / \(evidence.geometry.samples.count)").font(.callout).monospacedDigit()
                Spacer()
                Text("20 rows/sec · ordinal playback").font(.caption).foregroundStyle(.secondary)
            } else {
                Text(displayDate(sample.tUtc)).font(.callout).monospacedDigit()
                Spacer()
                Picker("Playback speed", selection: $replaySpeed) {
                    ForEach([1.0, 5, 10, 20, 40], id: \.self) { speed in Text("\(Int(speed))×").tag(speed) }
                }.pickerStyle(.segmented).labelsHidden().frame(width: 225)
                    .help("Recorded seconds per playback second")
            }
        }
    }

    private var inspector: some View {
        VStack(alignment: .leading, spacing: 22) {
            if liveStateEnabled && waitingForSource {
                Text("Waiting for a valid activation snapshot").font(.headline)
                Text(sourceStatus).font(.caption).foregroundStyle(.secondary)
                if let error = stateLive.lastError { Text(error).font(.caption).foregroundStyle(Palette.rail) }
                Button("Choose state file…") { chooseStateFile() }
            } else if isZoneView {
                zonesInspector
            } else if inStateView {
                sectionLabel("MEASURED GEOMETRY")
                info("Distance in full state", number(state.centeredNorm, digits: 3))
                info("Distance visible in 3D", number(state.projectedNorm, digits: 3))
                info("Distance omitted", number(state.residualNorm, digits: 3))
                Text("All three distances use activation units from the same window mean.").font(.caption).foregroundStyle(.secondary)
                Divider()
                sectionLabel("COVARIANCE EIGENMODES")
                ForEach(0..<3) { i in
                    info("PC\(i+1) · λ = \(number(evidence.geometry.pca.eigenvalues[i], digits: 3))", percent(evidence.geometry.pca.explainedVarianceRatio[i] * 100))
                }
                Text(liveStateEnabled ? "This basis was fitted to the separate 1,024-state capture; it stays fixed for live projection. Its 14.35% fit-window retention is not the retention of incoming observations." : "PCA uses centered covariance of these saved states. The basis stays fixed throughout replay; component signs are a convention.").font(.caption).foregroundStyle(.secondary)
                HStack { legend("PC1", Palette.fill); legend("PC2", Palette.rail); legend("PC3", Palette.leak) }
                Divider()
                if liveStateEnabled {
                    activationInspector
                } else {
                    sectionLabel("CAPTURE LIMITS")
                    Text("Rows are ordered oldest to newest. Per-row timestamps, fill, and leak were not stored in this dump.").font(.caption).foregroundStyle(.secondary)
                    Text("This is a separate capture from the 20-minute telemetry replay. It does not show language-model activations.").font(.caption).foregroundStyle(.secondary)
                }
            } else {
                sectionLabel("STATE AT THE CURSOR")
                info(usesLive ? "Engine-reported fill slope" : "Backward fill difference", number(liveStateEnabled ? nil : usesLive ? live.latest?.sourceReportedFillRatePctPerS : sample.fillRatePctPerS, digits: 3) + " pp/s")
                info("ESN covariance λ₁ estimate", number(liveStateEnabled ? nil : usesLive ? live.latest?.esnCovLambda1 : sample.esnCovLambda1, digits: 3))
                info("State radius (RMS)", number(liveStateEnabled ? stateLive.latest?.geometry.stateRms : usesLive ? live.latest?.geomRadius : sample.geomRadius, digits: 3))
                info("Radius / rolling baseline", number(liveStateEnabled ? stateLive.latest?.geomRel : usesLive ? live.latest?.geomRel : sample.geomRel, digits: 3) + "×")
                Divider()
                sectionLabel("SENSORY SPECTRAL ESTIMATES")
                ForEach(0..<min(3,currentSpectrum.count), id: \.self) { i in
                    VStack(alignment: .leading, spacing: 5) { legend("Recorded slot \(i+1)", [Palette.fill,Palette.rail,Palette.leak][i]); Text(number(currentSpectrum[i], digits: 3)).font(.system(.body, design: .monospaced)) }
                }
                if currentSpectrum.isEmpty { Text("Unavailable in this live source").font(.caption).foregroundStyle(.secondary) }
                Text("Recorded Rayleigh estimates can cross. Slot order is preserved; these are not certified, tracked eigenmodes.").font(.caption).foregroundStyle(.secondary)
                Divider()
                sectionLabel("LEAK IS A MIXING COEFFICIENT")
                if let leak = currentLeak {
                    HStack(spacing: 0) {
                        Rectangle().fill(.gray.opacity(0.6)).frame(width: max(0, 240 * (1-leak)))
                        Rectangle().fill(Palette.leak)
                    }.frame(height: 8).clipShape(Capsule())
                    info("Previous-state weight 1 − α", percent((1-leak)*100))
                    info("New-proposal weight α", percent(leak*100))
                }
                Text("Illustrates the base update coefficient. Recurrence, inputs, noise, clipping, and possible overrides also matter; α is not a fill drain rate.").font(.caption).foregroundStyle(.secondary)
                Divider()
                controllerInspector
                Divider()
                if liveStateEnabled { activationInspector } else { liveInspector }
            }
        }
    }

    private var zonesInspector: some View {
        VStack(alignment: .leading, spacing: 16) {
            sectionLabel("EXPLORE A BOUNDARY")
            VStack(spacing: 4) {
                ForEach(zones) { zone in
                    Button { selectedZoneID = zone.id } label: {
                        HStack(spacing: 8) {
                            Circle().fill(zoneColor(zone)).frame(width: 6, height: 6)
                            Text(zone.title).font(.caption)
                            Spacer(minLength: 3)
                            Text(zone.thresholdLabel).font(.caption).monospacedDigit()
                        }.padding(.horizontal, 8).padding(.vertical, 8)
                            .background(selectedZoneID == zone.id ? Palette.leak.opacity(0.16) : .clear, in: RoundedRectangle(cornerRadius: 6))
                            .foregroundStyle(selectedZoneID == zone.id ? Palette.leak : .primary)
                    }.buttonStyle(.plain).accessibilityLabel("\(zone.title), \(zone.thresholdLabel)")
                }
            }
            VStack(alignment: .leading, spacing: 9) {
                Text(selectedZone.kind.rawValue.uppercased()).font(.system(size: 10, weight: .medium)).tracking(1).foregroundStyle(Palette.leak)
                Text(selectedZone.summary).font(.callout)
                Text(selectedZone.detail).font(.caption).foregroundStyle(.secondary)
                Text("Source · \(selectedZone.sourceLabel)").font(.caption2).foregroundStyle(.secondary).textSelection(.enabled)
            }
            Divider()
            sectionLabel("AT THIS OBSERVATION")
            Text(currentFill.isFinite ? "Observed fill is \(percent(currentFill)); \(number(currentFill - selectedZone.thresholdPct, digits: 2)) percentage points relative to the selected line." : "Waiting for an observed fill value.").font(.caption)
            if currentFill.isFinite && !(54...82).contains(currentFill) {
                Text("The measured fill is outside this 54–82% close-up. Its value remains visible above; the Fill sphere shows the whole volume.").font(.caption).foregroundStyle(Palette.rail)
            }
            if liveStateEnabled {
                info("Co-recorded stage", stateLive.latest?.stage ?? "Unavailable")
                Text("Stage and fill accompany this activation frame. The recorder does not identify the exact ESN step or controller evaluation.").font(.caption).foregroundStyle(.secondary)
            } else if usesLive, let controller = live.latest?.controller {
                info("Source-reported stage", controller.stage ?? "Unavailable")
                Text("This is the reported stage, not a classification inferred from the picture. Controller input can precede the displayed fill snapshot.").font(.caption).foregroundStyle(.secondary)
            } else {
                Text("Historical stage and P/I were not stored at this cursor. Threshold crossings alone cannot reconstruct the regulator’s actions.").font(.caption).foregroundStyle(.secondary)
            }
            DisclosureGroup("How the limits work together") {
                VStack(alignment: .leading, spacing: 10) {
                    Text(ReferenceZone.evidenceScope)
                    Text("The regulator combines stage hysteresis, fill slope, structural drainage, and bounded gate/filter adjustments. These are operating limits and responses; they do not establish a guaranteed safe region.")
                    Text("Beyond the main shelf: Discharge enters at 82% and an existing Discharge releases at or below 76%. Structural forced drainage also begins at 82%. These are additional current-source facts, not observed transitions in this replay.")
                    Text("The close-up’s 54–82% crop is framing only. It magnifies the original sphere uniformly by 12×, preserving how close 71.5% and 72% really are.")
                }.font(.caption).foregroundStyle(.secondary).padding(.top, 8)
            }
            Button { showMethods = true } label: { Label("How this animation gets its data", systemImage: "info.circle") }.font(.caption).buttonStyle(.plain).foregroundStyle(Palette.fill)
            Divider()
            controllerInspector
            Divider()
            if liveStateEnabled { activationInspector } else { liveInspector }
        }
    }

    private func zoneColor(_ zone: ReferenceZone) -> Color {
        switch zone.styleRole {
        case .shelf, .hysteresis: Palette.shelf
        case .target, .pi: Palette.leak
        case .strong, .force: Palette.rail
        }
    }

    private var controllerInspector: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionLabel("PI CONTROLLER")
            Text(liveStateEnabled ? "P/I unavailable in the activation feed" : usesLive ? "Current structural controller" : "Historical P/I unavailable").font(.callout)
            if liveStateEnabled {
                Text("A separate health snapshot is not joined to this frame. Exact controller links and applied leak need the proposed producer metadata.").font(.caption).foregroundStyle(.secondary)
            } else if let s = usesLive ? live.latest?.controller : evidence.historical.controller.snapshot {
                DisclosureGroup(usesLive ? "Inspect observed controller" : "Separate controller snapshot") {
                    VStack(alignment: .leading, spacing: 12) {
                        Text(displayDate(s.tUtc ?? "Unknown time")).font(.caption).foregroundStyle(.secondary)
                        info("Structural error", number(s.structuralPi?.errorPct, digits: 2) + " pp")
                        info("Integral · per step", number(s.structuralPi?.integral, digits: 4))
                        info("Derived P", number(s.derived?.pTerm, digits: 4))
                        info("Derived I", number(s.derived?.iTerm, digits: 4))
                        info("Derived clamped P + I", number(s.derived?.piOutput, digits: 4))
                        info("Controller input fill", percent(s.derived?.controllerInputFillPct))
                        info("Snapshot fill", percent(s.observedFillPct))
                        Text("Error refers to a prior input. P/I are reconstructed from current source constants; final drain also includes policy adjustments.").font(.caption).foregroundStyle(.secondary)
                    }.padding(.top, 12)
                }
            }
        }
    }

    private var activationStatus: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(stateLive.statusText).font(.caption).foregroundStyle(.secondary)
                Spacer()
                Text("\(stateLive.samples.count) recent frames").font(.caption).monospacedDigit()
            }
            if let latest = stateLive.latest {
                Text("Recorder observation · \(latest.sourceDate.formatted(date: .abbreviated, time: .standard)) · stage \(latest.stage)").font(.caption).foregroundStyle(.secondary)
            }
            if let error = stateLive.lastError { Text(error).font(.caption).foregroundStyle(Palette.rail).lineLimit(2) }
        }
    }

    private var activationInspector: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionLabel("LIVE ACTIVATION OBSERVATIONS")
            activationStatus
            if let latest = stateLive.latest {
                info("Full-state distance / reference radius", number(latest.geometry.centeredNorm / evidence.geometry.pca.normalization.referenceRadius, digits: 3) + "×")
                if latest.geometry.centeredNorm > evidence.geometry.pca.normalization.referenceRadius {
                    Text("This state is outside the captured full-state reference radius. The projection keeps its original scale.").font(.caption).foregroundStyle(Palette.rail)
                }
            }
            Text("Visible distance² is projected squared distance / full squared distance from the frozen reference mean. It describes this point; it is not a live variance estimate.").font(.caption).foregroundStyle(.secondary)
            if stateLive.latest?.geometry.centeredNorm == 0 {
                Text("At the reference mean, both distances are zero and their ratio is undefined.").font(.caption).foregroundStyle(.secondary)
            }
            Text(stateLive.continuityText).font(.caption).foregroundStyle(.secondary)
            Text("The v1 recorder publishes actual activations with fill and stage in one file. Its timestamps describe recorder observations, not authenticated ESN-step measurement times. Session, node-layout identity, applied leak and controller links are missing; coordinate compatibility with this frozen basis is unverified.").font(.caption).foregroundStyle(.secondary)
            Text("Each accepted batch replaces the displayed path. The app does not join separate batches or attach the health feed’s PI to these states.").font(.caption).foregroundStyle(.secondary)
            Button("Choose state file…") { chooseStateFile() }
            Button("Return to recorded evidence") { selectFeed("recorded") }
        }
    }

    private var liveInspector: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionLabel("READ-ONLY LIVE FEED")
            if mode != .fill && !isZoneView {
                Toggle("Follow health snapshots", isOn: Binding(get: { liveEnabled }, set: { enableLive($0) })).toggleStyle(.switch)
            }
            Text(live.statusText).font(.caption).foregroundStyle(.secondary)
            if let s = live.latest {
                Text("Source \(s.sourceDate.formatted(date: .abbreviated, time: .standard))\nSession \(s.sessionId) · snapshot \(s.snapshotSequence)").font(.caption2).foregroundStyle(.secondary).monospacedDigit()
            }
            if let error = live.lastError { Text(error).font(.caption).foregroundStyle(Palette.rail).lineLimit(4) }
            Button("Choose health.json…") { chooseHealthFile() }
            Text("Reads the existing file, then waits 2 seconds. No commands, writes, or control changes.").font(.caption).foregroundStyle(.secondary)
        }
    }

    private var methodsSheet: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("How the animation gets its data").font(.title2)
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text("Recorded telemetry → saved observations → radius → Metal").font(.headline).foregroundStyle(Palette.fill)
                    Text("The filling sphere and Reference Zones share the same cursor: 507 paired telemetry observations from Sep 6, 09:09–09:29 PT. A read-only probe extracts the cached evidence into a JSON file that is bundled with the app. Opening replay does not query a live database.")
                    Text("Each observation supplies its recorded fill percentage. The app maps that value to volume using r/R = ∛(fill/100). It does not integrate the slope or calculate fill from the three displayed spectral estimates. Upstream, EigenFill derives this fill signal from the sensory field’s spectral structure and smoothing.")
                    Text("Playback uses recorded elapsed seconds and a monotonic clock at the selected speed. It holds the last observation until the next timestamp is reached. The sphere adds no invented intermediate measurements; chart lines simply connect saved samples. At high speeds or during delayed redraws, some observations may pass between displayed frames.")
                    Text("Read-only live is optional. Follow health snapshots is always visible below the Fill and Reference Zones renders. The viewer reads a selected health.json, then waits 2 seconds before reading again. It accepts new source sequences and uses the source’s session and clocks; repeated snapshots do not become new observations. Missing fields stay unavailable, and stale or failed reads are labeled.")
                    Text("Smooth fill transitions eases the cyan surface toward each new live reading over 0.8 seconds. A bounded quintic ease-in/ease-out curve acts on fill percentage before the cube-root radius mapping, with no overshoot or prediction. White dashes mark the latest measured fill immediately, as do the number, chart, stage and controller annotations. The intermediate surface is a presentation effect, not extra measurements. First readings, source/session changes and recorder-clock resets snap. Reduce Motion is honored by default; explicitly enabling Smooth fill transitions while it is on allows gentle motion only in this app. Disabling smoothing snaps immediately. Recorded replay and state coordinates remain un-interpolated.")
                    Text("Live state & fill is a separate source choice. It reads the existing activation recorder, then waits 2 seconds. The latest accepted frame supplies both the 3D state and its co-recorded fill/stage across the views. Each batch contains at most 180 observations and replaces the displayed path. These are recorder timestamps; exact ESN-step time, applied leak and controller links are unavailable. Health P/I is never attached to this frame.")
                    Divider()
                    Text("What each view means").font(.headline)
                    Text("Reference Zones magnifies the fill sphere’s cut-face geometry 12×, then fits it to the window. This is not a fixed pixel zoom relative to the main sphere. All radii keep the same cube-root mapping; 54–82% is only the visible crop. The shelf and rails come from source-defined references, with different entry and release thresholds. The historical replay does not contain controller stages or P/I history, so the view cannot claim those controls were active at its cursor.")
                    Text("Recorded State trajectory is a separate capture of 1,024 real 128-D states, projected through one fixed, centered PCA basis. It plays at 20 rows per second in row order; this is not measured wall time. Live state uses the same frozen basis, without refitting or rescaling; its current distance² fraction is distinct from the old fit-window variance. Both files lack node-layout identity, so coordinate compatibility remains unverified. Reference drift and omitted distance stay visible.")
                    Text("Spectral spokes show square roots of recorded sensory covariance-direction estimates in their original slot order. Their directions are schematic, and they are distinct from PCA modes and recurrent-weight eigenvalues.")
                    Text("Metal renders the native 3D geometry using shared GPU buffers. The Neural Engine is not used. Source hashes, capture limits, formulas and reproduction commands are documented in native/ReservoirScope/docs/ANIMATION-DATA.md in the research project.").foregroundStyle(.secondary)
                }.textSelection(.enabled)
            }
            HStack { Spacer(); Button("Done") { showMethods = false }.keyboardShortcut(.defaultAction) }
        }.padding(28).frame(width: 700, height: 650)
    }

    private func advancePlayback(rate: Double? = nil) {
        guard isPlaying && !usesLive else { return }
        let position = replayClock.advance(uptime: ProcessInfo.processInfo.systemUptime,
                                           rate: inStateView ? 20 : (rate ?? replaySpeed))
        if inStateView {
            stateIndex = min(evidence.geometry.samples.count - 1, Int(position))
            if stateIndex == evidence.geometry.samples.count - 1 { isPlaying = false }
        } else {
            while historicalIndex + 1 < evidence.historical.samples.count && evidence.historical.samples[historicalIndex+1].tS <= position { historicalIndex += 1 }
            replayPosition = min(position, evidence.historical.samples.last!.tS)
            if historicalIndex == evidence.historical.samples.count - 1 { isPlaying = false }
        }
    }
    private func togglePlayback() {
        if isPlaying { advancePlayback(); isPlaying = false; return }
        if inStateView { if stateIndex == evidence.geometry.samples.count - 1 { stateIndex = 0 } }
        else { if historicalIndex == evidence.historical.samples.count - 1 { selectHistoricalIndex(0) } }
        replayClock.start(at: inStateView ? Double(stateIndex) : replayPosition, uptime: ProcessInfo.processInfo.systemUptime)
        isPlaying = true
    }
    private func selectHistoricalTime(_ t: Double) {
        let index = evidence.historical.samples.indices.min(by: { abs(evidence.historical.samples[$0].tS-t) < abs(evidence.historical.samples[$1].tS-t) }) ?? 0
        selectHistoricalIndex(index)
    }
    private func selectHistoricalIndex(_ index: Int) {
        historicalIndex = min(max(0, index), evidence.historical.samples.count - 1)
        replayPosition = sample.tS
        isPlaying = false
    }
    private func enableLive(_ enabled: Bool) {
        healthWatermarks.reset()
        if enabled { liveStateEnabled = false; stateLive.stop() }
        liveEnabled = enabled; isPlaying = false
        if enabled { live.start(path: sourcePath, config: evidence.historical.controller.structuralConfig) } else { live.stop() }
    }
    private func selectFeed(_ value: String) {
        isPlaying = false
        activationWatermarks.reset()
        if value == "states" {
            liveEnabled = false; live.stop(); liveStateEnabled = true
            stateLive.start(path: stateSourcePath, basis: evidence.geometry.pca)
        } else {
            liveStateEnabled = false; stateLive.stop()
            enableLive(value == "health")
        }
    }
    private func chooseStateFile() {
        let panel = NSOpenPanel(); panel.title = "Choose an existing activation trace"; panel.allowedContentTypes = [.json]; panel.canChooseDirectories = false; panel.allowsMultipleSelection = false
        if panel.runModal() == .OK, let url = panel.url { stateSourcePath = url.path; activationWatermarks.reset(); if liveStateEnabled { stateLive.start(path: stateSourcePath, basis: evidence.geometry.pca) } }
    }
    private func chooseHealthFile() {
        let panel = NSOpenPanel(); panel.title = "Choose an existing read-only health snapshot"; panel.allowedContentTypes = [.json]; panel.canChooseDirectories = false; panel.allowsMultipleSelection = false
        if panel.runModal() == .OK, let url = panel.url { sourcePath = url.path; healthWatermarks.reset(); if liveEnabled { live.start(path: sourcePath, config: evidence.historical.controller.structuralConfig) } }
    }

    private func receiveHealthWatermarks(_ samples: [LiveTelemetrySample]) {
        guard liveEnabled else { return }
        guard let latest = samples.last else { healthWatermarks.reset(); return }
        let context = "\(latest.sourcePath):\(latest.sessionId)"
        if healthWatermarks.context != context { healthWatermarks.reset(context: context) }
        // Consume every accepted sample. Empty polls cannot form a fresh range
        // or advance its age, and chart-buffer eviction does not erase memory.
        for sample in samples where sample.snapshotSequence >= 0 {
            healthWatermarks.observe(FillWatermarkObservation(fillPct: sample.fillPct,
                sourceTime: sample.sourceDate.timeIntervalSince1970, ordinal: UInt64(sample.snapshotSequence)), context: context)
        }
    }

    private func receiveActivationWatermarks(_ samples: [LiveStateSample]) {
        guard liveStateEnabled else { return }
        activationWatermarks.reset()
        // This bounded recorder supplies no boot identity. Rebuild from this
        // batch on a fixed UTC grid, so rolling its first row cannot move the
        // same observation into a different generation or reset its age.
        for sample in samples {
            activationWatermarks.observe(FillWatermarkObservation(fillPct: sample.fillPct,
                sourceTime: sample.sourceDate.timeIntervalSince1970, ordinal: sample.tMs),
                context: stateSourcePath, origin: 0)
        }
    }
    private func info(_ label: String, _ value: String) -> some View { VStack(alignment: .leading, spacing: 4) { Text(label).font(.caption).foregroundStyle(.secondary); Text(value).font(.system(.body, design: .monospaced)) } }
    private func sectionLabel(_ title: String) -> some View { Text(title).font(.system(size: 10, weight: .medium)).tracking(1.4).foregroundStyle(.secondary) }
    private func readout(_ label: String, _ value: String, color: Color) -> some View { VStack(alignment: .leading, spacing: 4) { sectionLabel(label); Text(value).font(.system(size: 30, weight: .light, design: .rounded)).foregroundStyle(color).monospacedDigit() } }
    private func legend(_ title: String, _ color: Color) -> some View { HStack(spacing: 5) { Circle().fill(color).frame(width: 5,height: 5); Text(title).font(.caption).foregroundStyle(.secondary) } }
}

private func number(_ value: Double?, digits: Int = 2) -> String { guard let value, value.isFinite else { return "Unavailable" }; return String(format: "%.*f", digits, value) }
private func percent(_ value: Double?) -> String { number(value, digits: 1) + (value == nil ? "" : "%") }
private func displayDate(_ value: String) -> String {
    let iso = ISO8601DateFormatter(); iso.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    guard let date = iso.date(from: value) else { return value }
    let f = DateFormatter(); f.timeZone = TimeZone(identifier: "America/Los_Angeles"); f.dateFormat = "MMM d · HH:mm:ss 'PT'"; return f.string(from: date)
}

struct SignalChart: View {
    let title: String
    let series: [[(Double,Double)]]
    let colors: [Color]
    let selectedX: Double
    var referenceBand: ClosedRange<Double>? = nil
    var fixedDomain: ClosedRange<Double>? = nil
    var onSelect: ((Double)->Void)?
    var body: some View {
        GeometryReader { proxy in
            let values = series.flatMap { $0 }.filter { $0.0.isFinite && $0.1.isFinite }
            let xlo = values.map(\.0).min() ?? 0, xhi = max(xlo + 1, values.map(\.0).max() ?? 1)
            let lo = values.map(\.1).min() ?? 0, hi = values.map(\.1).max() ?? 1
            let pad = max((hi-lo)*0.15, 0.001)
            let ylo = fixedDomain?.lowerBound ?? lo-pad, yhi = fixedDomain?.upperBound ?? hi+pad
            let left = 48.0, right = 8.0, top = 20.0, bottom = 14.0
            let width = max(1,proxy.size.width-left-right), height = max(1,proxy.size.height-top-bottom)
            Canvas { context, _ in
                func x(_ value: Double)->Double { left+(value-xlo)/(xhi-xlo)*width }
                func y(_ value: Double)->Double { top+(yhi-value)/(yhi-ylo)*height }
                context.draw(Text(title).font(.system(size: 11)).foregroundColor(.secondary), at: CGPoint(x:left,y:5), anchor: .topLeading)
                context.draw(Text(String(format: "%.3g",yhi)).font(.system(size:10)).foregroundColor(.secondary), at:CGPoint(x:left-7,y:top),anchor:.trailing)
                context.draw(Text(String(format: "%.3g",ylo)).font(.system(size:10)).foregroundColor(.secondary), at:CGPoint(x:left-7,y:top+height),anchor:.trailing)
                context.draw(Text(String(format: "%.0f s",xlo)).font(.system(size:10)).foregroundColor(.secondary),at:CGPoint(x:left,y:top+height+3),anchor:.topLeading)
                context.draw(Text(String(format: "%.0f s",xhi)).font(.system(size:10)).foregroundColor(.secondary),at:CGPoint(x:left+width,y:top+height+3),anchor:.topTrailing)
                var area = context; area.clip(to: Path(CGRect(x:left,y:top,width:width,height:height)))
                if let band = referenceBand { area.fill(Path(CGRect(x:left,y:y(band.upperBound),width:width,height:y(band.lowerBound)-y(band.upperBound))),with:.color(Palette.shelf.opacity(0.13))) }
                for (i,points) in series.enumerated() {
                    var path=Path(); for (j,p) in points.enumerated() { if j==0 {path.move(to:CGPoint(x:x(p.0),y:y(p.1)))} else {path.addLine(to:CGPoint(x:x(p.0),y:y(p.1)))} }
                    area.stroke(path,with:.color(colors[i % colors.count]),lineWidth:1.2)
                }
                var guide=Path();guide.move(to:CGPoint(x:x(selectedX),y:top));guide.addLine(to:CGPoint(x:x(selectedX),y:top+height));area.stroke(guide,with:.color(.white.opacity(0.65)),lineWidth:1)
            }
            .contentShape(Rectangle())
            .gesture(DragGesture(minimumDistance: 0).onChanged { v in onSelect?(xlo + min(1,max(0,(v.location.x-left)/width))*(xhi-xlo)) })
            .accessibilityLabel(title + ". Synchronized with the selected observation.")
        }
    }
}

struct LoadingsChart: View {
    let values: [Double]
    @Binding var selected: Int
    var body: some View {
        GeometryReader { proxy in
            Canvas { context, size in
                let maxAbs=max(0.0001,values.map(abs).max() ?? 1), mid=size.height/2, step=size.width/Double(values.count)
                var baseline=Path();baseline.move(to:CGPoint(x:0,y:mid));baseline.addLine(to:CGPoint(x:size.width,y:mid));context.stroke(baseline,with:.color(.secondary.opacity(0.35)),lineWidth:1)
                for (i,v) in values.enumerated() { let h=abs(v)/maxAbs*(mid-8);let rect=CGRect(x:Double(i)*step,y:v>=0 ? mid-h : mid,width:max(1,step-1),height:h);context.fill(Path(rect),with:.color(i==selected ? .white : v>=0 ? Palette.fill : Palette.leak)) }
            }
            .contentShape(Rectangle())
            .gesture(DragGesture(minimumDistance:0).onChanged { v in selected=min(values.count-1,max(0,Int(v.location.x/proxy.size.width*Double(values.count)))) })
            .accessibilityLabel("128 signed PCA component loadings. Use the node stepper to inspect each value.")
        }
    }
}
