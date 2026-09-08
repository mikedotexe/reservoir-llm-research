import SwiftUI

/// Replay uses the retained vectors only. Its selectable preview volume is not
/// joined to the unrelated historical fill series. Live v1 supplies co-recorded fill.
struct StateSurfaceExperience: View {
    let evidence: EvidenceStore
    let liveSample: LiveStateSample?
    let followsState: Bool
    let healthOnly: Bool
    let sourceStatus: String
    let sourceFresh: Bool
    var onFollow: (Bool) -> Void
    var onChooseFile: () -> Void
    @State private var row = 0
    @State private var playing = false
    @State private var replayClock = ReplayClock()
    @State private var field: StateSurfaceField = .signedActivation
    @State private var selectedModes = -1
    @State private var selectedNode = 0
    @State private var relief = 0.28
    @State private var reliefEnabled = true
    @State private var cutaway = false
    @State private var showSites = true
    @State private var flatLighting = false
    @State private var previewFill = 68.0
    @State private var metrics: StateSurfaceMetrics?
    private let pulse = Timer.publish(every: 0.05, on: .main, in: .common).autoconnect()
    private var replay: StateReplayEvidence? { evidence.stateReplay }
    private var activations: [Double]? { followsState ? liveSample?.activations : healthOnly ? nil : replay?.frame(index: row)?.activations }
    private var sourceIdentity: String { followsState ? liveSample?.id ?? "waiting" : replay?.sourceIdentity(index: row) ?? "missing" }
    private var fill: Double { followsState ? (liveSample?.fillPct ?? .nan) : previewFill }
    private var values: StateSurfaceValues? {
        guard let activations else { return nil }
        return try? StateSurfaceMath.field(field, activations: activations, mean: evidence.geometry.pca.mean,
            components: evidence.geometry.pca.components, selectedModes: selectedModes < 0 ? [0,1,2] : [selectedModes])
    }
    private var referenceIsQualified: Bool { followsState && field.requiresReference }
    private var count: Int { replay?.frames.count ?? 0 }
    var body: some View {
        HStack(spacing: 0) {
            center.padding(20).frame(maxWidth: .infinity, maxHeight: .infinity)
            Divider()
            ScrollView { inspector.padding(20) }.frame(width: 290)
        }
        .onChange(of: followsState) { _, _ in playing = false; metrics = nil }
        .onChange(of: healthOnly) { _, _ in playing = false; metrics = nil }
        .onReceive(pulse) { _ in
            guard playing, !followsState, !healthOnly, count > 0 else { return }
            row = min(count-1, Int(replayClock.advance(uptime: ProcessInfo.processInfo.systemUptime, rate: 20)))
            if row == count-1 { playing = false }
        }
    }
    private var center: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: 4) {
                    caption(followsState ? "CO-RECORDED FILL" : "PREVIEW VOLUME · FILL NOT RECORDED")
                    Text(fill.isFinite ? String(format:"%.1f%%",fill) : "Waiting").font(.system(size: 30, weight: .light, design: .rounded)).monospacedDigit()
                }
                Spacer()
                VStack(alignment: .trailing, spacing: 4) {
                    caption("SURFACE FIELD")
                    Text(field.title).font(.callout)
                }
            }
            ZStack(alignment: .bottomLeading) {
                if let values, fill.isFinite {
                    StateSurfaceScene(input: StateSurfaceRenderInput(values: values.values,
                        lower: values.scale.lowerBound, upper: values.scale.upperBound,
                        fillPct: fill, relief: reliefEnabled ? relief : 0, cutaway: cutaway,
                        selectedNode: selectedNode, showSites: showSites, flatLighting: flatLighting),
                        onSelect: { selectedNode = $0 }, onMetrics: { if metrics != $0 { metrics = $0 } })
                    VStack(alignment: .leading, spacing: 4) {
                        Text("128 coordinates · fixed drawing map")
                        Text("Dashed circles = exact volume reference · color scale stays fixed").foregroundStyle(.secondary)
                        if followsState && !sourceFresh { Text("Retained observation · source is stale or unavailable").foregroundStyle(.orange) }
                        if referenceIsQualified { Text("Reference comparison is provisional: node identity is unavailable").foregroundStyle(.orange) }
                        if fill == 0 { Text("No volume-bearing surface at zero · inspect values at right").foregroundStyle(.secondary) }
                    }.font(.caption).padding(12).background(.black.opacity(0.65), in: RoundedRectangle(cornerRadius: 8)).padding(12).allowsHitTesting(false)
                } else {
                    ContentUnavailableView(healthOnly ? "This feed has no node values" : "Waiting for state vectors", systemImage: "circle.hexagongrid",
                        description: Text(healthOnly ? "Choose Live state & fill to show a surface from the same recorder observation." : sourceStatus))
                    VStack { Spacer(); Button("Follow state snapshots") { onFollow(true) }.padding(24) }
                }
            }.frame(minHeight: 330, maxHeight: .infinity).clipShape(RoundedRectangle(cornerRadius: 12))
            HStack {
                Text("Drag to orbit · click a patch to inspect · scroll to zoom").font(.caption).foregroundStyle(.secondary)
                Spacer(); Toggle("Cutaway", isOn: $cutaway).toggleStyle(.checkbox)
            }
            HStack(spacing: 14) {
                Toggle("Follow state snapshots", isOn: Binding(get: { followsState }, set: { onFollow($0) })).toggleStyle(.switch).controlSize(.small)
                if followsState { Button("Choose file…", action: onChooseFile).font(.caption) }
                Spacer()
                Text("Observed samples · no temporal easing").font(.caption).foregroundStyle(.secondary)
            }
            if followsState {
                Text(sourceStatus).font(.caption).foregroundStyle(.secondary).lineLimit(2)
            } else if !healthOnly && count > 0 {
                HStack {
                    Button {
                        if playing { playing = false } else {
                            if row == count-1 { row = 0 }
                            replayClock.start(at: Double(row), uptime: ProcessInfo.processInfo.systemUptime); playing = true
                        }
                    } label: { Label(playing ? "Pause" : "Play", systemImage: playing ? "pause.fill" : "play.fill") }
                    Text("State \(row+1) / \(count)").monospacedDigit()
                    Spacer(); Text("20 rows/sec · ordinal replay").font(.caption).foregroundStyle(.secondary)
                }
                Slider(value: Binding(get: { Double(row) }, set: { row = Int($0); playing = false }), in: 0...Double(count-1), step: 1).accessibilityLabel("Surface state row")
            }
            colorLegend
        }
    }
    private var inspector: some View {
        VStack(alignment: .leading, spacing: 15) {
            caption("READ THE SURFACE")
            Picker("Field", selection: $field) { ForEach(StateSurfaceField.allCases) { Text($0.title).tag($0) } }
            if field.requiresReference {
                Text(followsState ? "Same-size live vectors; compatibility with the old network's node order is unverified." : "Frozen reference fitted to this exact retained capture.")
                    .font(.caption).foregroundStyle(followsState ? Color.orange : Color.secondary)
            }
            if field == .reconstruction || field == .residual {
                Picker("Modes", selection: $selectedModes) {
                    Text("All three captured modes").tag(-1)
                    ForEach(0..<3) { Text("PC\($0+1)").tag($0) }
                }
                Text("Three modes retain 14.35% of reference-window variance. This is not a live variance estimate.").font(.caption).foregroundStyle(.secondary)
                if let values, let energy = values.centeredEnergy, energy > 0, let retained = values.reconstructedEnergy {
                    info("This state's distance² reconstructed", String(format:"%.2f%%",100*retained/energy))
                }
            }
            Toggle("Surface relief", isOn: $reliefEnabled).toggleStyle(.switch).controlSize(.small)
            if reliefEnabled {
                Slider(value: $relief, in: 0...0.35).accessibilityLabel("Surface relief strength")
                Text(String(format:"Requested strength %.3f · applied %.3f", relief, metrics?.appliedRelief ?? 0)).font(.caption).monospacedDigit()
                Text("Relief reduces near empty/full. Flattening there is a drawing constraint, not a calmer state.").font(.caption).foregroundStyle(.secondary)
            }
            Toggle("Exact node markers", isOn: $showSites).toggleStyle(.checkbox)
            Toggle("Flat color lighting", isOn: $flatLighting).toggleStyle(.checkbox)
            if !followsState && !healthOnly {
                Divider(); caption("PREVIEW SIZE")
                Slider(value: $previewFill, in: 0...100).accessibilityLabel("Preview volume, not measured fill")
                Text("This capture has no fill measurements. This control changes only its display size.").font(.caption).foregroundStyle(.secondary)
            }
            Divider(); caption("INSPECT A COORDINATE")
            HStack {
                Text("Node \(selectedNode+1)").font(.headline).monospacedDigit()
                Spacer(); Stepper("Node", value: $selectedNode, in: 0...127).labelsHidden().accessibilityLabel("Inspect surface node")
            }
            if let values {
                info("Raw signed activation", format(values.activations[selectedNode]))
                info(field.title, format(values.values[selectedNode]))
                if (!followsState || field.requiresReference), let residual = values.residual { info("Omitted by selected modes", format(residual[selectedNode])) }
                if values.outOfRangeCount > 0 { Text("\(values.outOfRangeCount) values exceed the display scale; exact values remain here.").font(.caption).foregroundStyle(.orange) }
                nodeGrid(values)
            }
            Text("Each square is one exact coordinate. The smooth sphere blends nearby sites in this drawing map; proximity does not mean a recurrent connection.").font(.caption).foregroundStyle(.secondary)
            Divider(); caption("MEASUREMENT & DISPLAY")
            Text(followsState ? "State and fill share one recorder observation. Exact successful-step time, applied leak and node-layout identity are absent in v1." : "Original state vectors, in capture order. No per-row time, leak or fill was retained.").font(.caption).foregroundStyle(.secondary)
            Text(sourceIdentity).font(.system(size: 9, design: .monospaced)).foregroundStyle(.secondary).textSelection(.enabled).lineLimit(4)
            if let metrics {
                info("Closed-mesh volume error", metrics.volumeError.isFinite ? String(format:"%.2e",metrics.volumeError) : "Unavailable")
                if let fallback = metrics.fallback { Text(fallback).font(.caption).foregroundStyle(.orange) }
            }
            Text("GPU field + lighting · checked volume · no synthetic ripples").font(.caption2).foregroundStyle(.secondary)
        }
    }
    private var colorLegend: some View {
        VStack(spacing: 4) {
            LinearGradient(colors: field.scale.lowerBound < 0 ? [Self.color(field.scale.lowerBound,scale:field.scale),Self.color(0,scale:field.scale),Self.color(field.scale.upperBound,scale:field.scale)] : [Self.color(0,scale:field.scale),Self.color(1,scale:field.scale)], startPoint: .leading, endPoint: .trailing).frame(height: 7).clipShape(Capsule())
            HStack { Text(format(field.scale.lowerBound)); Spacer(); Text("Fixed scale · signed values are not health ratings"); Spacer(); Text(format(field.scale.upperBound)) }.font(.caption2).foregroundStyle(.secondary)
        }
    }
    private func nodeGrid(_ values: StateSurfaceValues) -> some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible(),spacing: 2),count: 16),spacing: 2) {
            ForEach(0..<128) { i in
                Button { selectedNode = i } label: {
                    Rectangle().fill(Self.color(values.values[i], scale: values.scale)).frame(height: 11)
                        .overlay(Rectangle().stroke(i == selectedNode ? Color.white : .clear,lineWidth: 1.5))
                }.buttonStyle(.plain).accessibilityLabel("Node \(i+1), \(format(values.values[i]))")
                    .help("Node \(i+1) · \(format(values.values[i]))")
            }
        }
    }
    static func color(_ value: Double, scale: ClosedRange<Double>) -> Color {
        let t = min(1,max(0,(value-scale.lowerBound)/(scale.upperBound-scale.lowerBound)))
        let low = SIMD3<Double>(0.52,0.30,0.92), middle = SIMD3<Double>(0.10,0.17,0.23), high = SIMD3<Double>(0.14,0.91,0.79)
        let rgb = scale.lowerBound >= 0 ? middle*(1-t)+high*t : t < 0.5 ? low*(1-2*t)+middle*(2*t) : middle*(2-2*t)+high*(2*t-1)
        return Color(.sRGBLinear, red: rgb.x, green: rgb.y, blue: rgb.z, opacity: 1)
    }
    private func caption(_ text: String) -> some View { Text(text).font(.system(size:10,weight:.medium)).tracking(1.2).foregroundStyle(.secondary) }
    private func format(_ value: Double) -> String { String(format:"%+.4f",value) }
    private func info(_ title: String, _ value: String) -> some View { VStack(alignment:.leading,spacing:3) { Text(title).font(.caption).foregroundStyle(.secondary); Text(value).font(.system(.body,design:.monospaced)) } }
}
