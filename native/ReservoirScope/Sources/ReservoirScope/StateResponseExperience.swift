import Foundation
import CryptoKit

struct StateResponseFailure: LocalizedError {
    let message: String
    init(_ message: String) { self.message = message }
    var errorDescription: String? { message }
}

/// Strictly bounded, bundled simulated-parent evidence. The state atlas can be
/// reused as an index drawing map, but the Minime PCA basis and fill cannot.
struct StateResponseEvidence: Decodable {
    struct Frame: Decodable {
        let sampleIndex: Int
        let originalBoundaryStep: Int
        let control: [Double]
        let intervention: [Double]
        let delta: [Double]
        let separationL2: Double
    }
    struct Summary: Decodable {
        let requestedSignedL2: Double
        let actualInitialL2: Double
        let peakGainOverInitial: Double
        let returnBoundary: Int?
        let returnStatus: String
    }
    let schema: String
    let subject: String
    let scope: String
    let runId: String
    let selection: String
    let nodeCount: Int
    let nodeLayout: String
    let modelHashes: [String: String]
    let clock: String
    let controls: String
    let displayRules: [String]
    let resultSummary: Summary
    let sourceResultsSha256: String
    let frames: [Frame]

    static let retainedSHA256 = "fe97623dcccb4b089ce4e0a1b5cc99ec902793efed8fbfcf1041ce8c865e9100"
    static let maximumBytes = 1_048_576
    static let returnFraction = 0.1
    static let returnDwell = 8
    var fixedDeltaScale: Double { abs(resultSummary.requestedSignedL2) }
    var returnThreshold: Double { resultSummary.actualInitialL2 * Self.returnFraction }
    var plotMaximum: Double { max(fixedDeltaScale, frames.map(\.separationL2).max() ?? 0) }
    var evidenceIdentity: String { "fixture:\(Self.retainedSHA256):\(runId)" }
    func frame(at index: Int) -> Frame? { frames.indices.contains(index) ? frames[index] : nil }

    static func load(bundle: Bundle = .module) throws -> Self {
        guard let url = bundle.url(forResource: "state-response", withExtension: "json")
                ?? bundle.url(forResource: "state-response", withExtension: "json", subdirectory: "Resources") else {
            throw StateResponseFailure("The retained simulation response is missing from this app.")
        }
        return try load(url: url)
    }
    static func load(url: URL, expectedSHA256: String = retainedSHA256) throws -> Self {
        let handle = try FileHandle(forReadingFrom: url)
        defer { try? handle.close() }
        let data = try handle.read(upToCount: maximumBytes + 1) ?? Data()
        return try decode(data: data, expectedSHA256: expectedSHA256)
    }
    static func decode(data: Data, expectedSHA256: String = retainedSHA256) throws -> Self {
        guard !data.isEmpty, data.count <= maximumBytes else { throw StateResponseFailure("Response evidence exceeds its bounded resource size.") }
        let actualSHA = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
        guard actualSHA == expectedSHA256 else { throw StateResponseFailure("Response evidence does not match its retained byte identity.") }
        guard let raw = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              Set(raw.keys) == Set(["schema", "subject", "scope", "run_id", "selection", "node_count", "node_layout",
                  "model_hashes", "reference_basis", "fill", "clock", "controls", "display_rules", "result_summary", "source_results_sha256", "frames"]),
              raw["reference_basis"] is NSNull, raw["fill"] is NSNull,
              let rawFrames = raw["frames"] as? [[String: Any]], rawFrames.count == 65,
              rawFrames.allSatisfy({ Set($0.keys) == Set(["sample_index", "original_boundary_step", "control", "intervention", "delta", "separation_l2"]) }) else {
            throw StateResponseFailure("The simulation has no fill, PCA basis or measured seconds. Unsupported evidence fields were rejected.")
        }
        let decoder = JSONDecoder(); decoder.keyDecodingStrategy = .convertFromSnakeCase
        let result = try decoder.decode(Self.self, from: data)
        try result.validate()
        return result
    }
    private func validate() throws {
        func require(_ condition: Bool, _ message: String) throws {
            if !condition { throw StateResponseFailure(message) }
        }
        func isHash(_ value: String) -> Bool { value.count == 64 && value.allSatisfy { "0123456789abcdef".contains($0) } }
        try require(schema == "research.state_response_preview.v1" && nodeCount == 128 && frames.count == 65,
                    "Response schema or dimensions are unsupported.")
        try require(subject == "esn-divide simulated parent; not live Minime"
            && clock == "simulation boundary indices only; no measured seconds"
            && scope == "harness parent; fixed recorded controls and additive transition residual; no cloned adaptive controller, no native checkpoint parity claim"
            && nodeLayout == "captured esn-divide parent index order; not established compatible with native Minime node identity"
            && controls == "Identical recorded inputs, leak, bridge and transition residual; no adaptive controller replica",
                    "Response provenance cannot be relabeled as live or native evidence.")
        try require(runId == "s0:coordinate_0:dose+0.001" && !selection.isEmpty && !displayRules.isEmpty,
                    "Response example identity is unsupported.")
        try require(isHash(sourceResultsSha256) && Set(modelHashes.keys) == Set(["model/parent/wres", "model/parent/win"])
            && modelHashes.values.allSatisfy(isHash), "Response source/model hashes are missing or malformed.")
        let summaryValues = [resultSummary.requestedSignedL2, resultSummary.actualInitialL2, resultSummary.peakGainOverInitial]
        try require(summaryValues.allSatisfy(\.isFinite) && fixedDeltaScale == 0.001 && resultSummary.actualInitialL2 > 0,
                    "The declared fixed displacement scale is invalid.")
        for (index, frame) in frames.enumerated() {
            try require(frame.sampleIndex == index && frame.originalBoundaryStep == 200 + index,
                        "Response boundary order is missing, duplicated or changed.")
            try require(frame.control.count == 128 && frame.intervention.count == 128 && frame.delta.count == 128,
                        "A response frame has an invalid coordinate count.")
            try require(frame.control.allSatisfy { $0.isFinite && abs($0) <= 1 }
                && frame.intervention.allSatisfy { $0.isFinite && abs($0) <= 1 }
                && frame.delta.allSatisfy(\.isFinite) && frame.separationL2.isFinite && frame.separationL2 >= 0,
                        "Response coordinates must be finite and bounded.")
            try require(frame.delta.indices.allSatisfy { abs(frame.delta[$0] - (frame.intervention[$0] - frame.control[$0])) <= 1e-14 },
                        "Response delta does not equal its paired state difference.")
            let separation = sqrt(frame.delta.reduce(0) { $0 + $1 * $1 })
            try require(abs(separation - frame.separationL2) <= 1e-12,
                        "Response distance does not match its full coordinate vector.")
        }
        let first = frames[0]
        try require(abs(first.delta[0] - resultSummary.requestedSignedL2) <= 1e-14
            && first.delta.dropFirst().allSatisfy { abs($0) <= 1e-14 }
            && abs(first.separationL2 - resultSummary.actualInitialL2) <= 1e-12,
                    "Boundary zero must contain the declared coordinate-zero displacement.")
        let peak = (frames.map(\.separationL2).max() ?? 0) / resultSummary.actualInitialL2
        try require(abs(peak - resultSummary.peakGainOverInitial) <= 1e-10,
                    "Response peak summary disagrees with the full path.")
        let firstReturn = (1...(frames.count - Self.returnDwell)).first { start in
            frames[start..<(start + Self.returnDwell)].allSatisfy { $0.separationL2 <= returnThreshold }
        }
        try require(firstReturn == resultSummary.returnBoundary
            && resultSummary.returnStatus == (firstReturn == nil ? "not_returned_within_64_steps" : "observed"),
                    "Response return summary disagrees with its declared threshold and dwell.")
    }
}

#if !STATE_RESPONSE_DATA_CHECKS
import SwiftUI

private enum StateResponseField: String, CaseIterable, Identifiable {
    case delta = "Delta", control = "Control", intervention = "Perturbed"
    var id: Self { self }
    func values(_ frame: StateResponseEvidence.Frame) -> [Double] {
        switch self { case .delta: frame.delta; case .control: frame.control; case .intervention: frame.intervention }
    }
}

struct SimulationStateResponseExperience: View {
    @State private var result: Result<StateResponseEvidence, Error>?
    var body: some View {
        Group {
            switch result {
            case .success(let evidence): StateResponseLoadedExperience(evidence: evidence)
            case .failure(let error): ContentUnavailableView("Simulation response unavailable", systemImage: "waveform.path",
                description: Text(error.localizedDescription))
            case nil: ProgressView("Loading retained simulation response…")
            }
        }.task {
            // Keep bounded resource decoding out of parent-view refreshes.
            if result == nil { result = Result { try StateResponseEvidence.load() } }
        }
    }
}

private struct StateResponseLoadedExperience: View {
    let evidence: StateResponseEvidence
    @State private var row = 0
    @State private var field: StateResponseField = .delta
    @State private var selectedNode = 0
    @State private var playing = false
    @State private var replayClock = ReplayClock()
    @State private var metrics: StateSurfaceMetrics?
    private let pulse = Timer.publish(every: 1.0 / 30, on: .main, in: .common).autoconnect()
    private var frame: StateResponseEvidence.Frame { evidence.frames[row] }
    private var scale: Double { field == .delta ? evidence.fixedDeltaScale : 1 }
    private var values: [Double] { field.values(frame) }

    var body: some View {
        HStack(spacing: 0) {
            main.padding(20).frame(maxWidth: .infinity, maxHeight: .infinity)
            Divider()
            ScrollView { inspector.padding(20) }.frame(width: 295)
        }
        .onDisappear { playing = false }
        .onReceive(pulse) { _ in
            guard playing else { return }
            row = min(64, Int(replayClock.advance(uptime: ProcessInfo.processInfo.systemUptime, rate: 3)))
            if row == 64 { playing = false }
        }
    }
    private var main: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    caption("ESN-DIVIDE SIMULATION")
                    Text("A gesture, then its response").font(.title2.weight(.medium))
                    Text("Paired states · identical recorded forcing · one direct state displacement")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                Picker("Surface", selection: $field) {
                    ForEach(StateResponseField.allCases) { Text($0.rawValue).tag($0) }
                }.pickerStyle(.segmented).labelsHidden().accessibilityLabel("Response surface field").frame(width: 230)
            }
            ZStack(alignment: .bottomLeading) {
                StateSurfaceScene(input: StateSurfaceRenderInput(values: values, lower: -scale, upper: scale,
                    fillPct: 68, relief: 0.28, cutaway: false, selectedNode: selectedNode),
                    accessibilitySubject: "esn-divide simulated parent",
                    onSelect: { selectedNode = $0 }, onMetrics: { metrics = $0 })
                    .accessibilityLabel("ESN-divide simulation \(field.rawValue) surface. Fixed coordinate atlas; no measured fill.")
                VStack(alignment: .leading, spacing: 4) {
                    Text(row == 0 ? "Boundary 0 · the displacement is already applied" : "Boundary \(row) after displacement")
                    Text("ESN-DIVIDE SIMULATION · fixed preview size, no fill measurement").foregroundStyle(.secondary)
                    Text("128 coordinates · index map only · no Minime PCA basis").foregroundStyle(.secondary)
                }.font(.caption).padding(12).background(.black.opacity(0.7), in: RoundedRectangle(cornerRadius: 8))
                    .padding(12).allowsHitTesting(false)
            }.frame(minHeight: 260, maxHeight: .infinity).clipShape(RoundedRectangle(cornerRadius: 12))
            legend
            HStack {
                Button {
                    if playing { playing = false } else {
                        if row == 64 { row = 0 }
                        replayClock.start(at: Double(row), uptime: ProcessInfo.processInfo.systemUptime)
                        playing = true
                    }
                } label: { Label(playing ? "Pause" : "Play slowly", systemImage: playing ? "pause.fill" : "play.fill") }
                Button("Injected boundary") { playing = false; row = 0 }
                Text("Boundary \(row) / 64").monospacedDigit()
                Spacer()
                Text("3 boundaries / playback sec")
                    .font(.caption2).foregroundStyle(.secondary)
            }
            Slider(value: Binding(get: { Double(row) }, set: { row = Int($0); playing = false }), in: 0...64, step: 1)
                .accessibilityLabel("Raw simulation boundary, zero is the injected state")
            StateResponseDistancePlot(evidence: evidence, selected: row).frame(height: 115)
            Text("Raw boundaries, no easing. Playback seconds are not measured reservoir time.")
                .font(.caption).foregroundStyle(.secondary)
        }
    }
    private var inspector: some View {
        VStack(alignment: .leading, spacing: 14) {
            caption("THE DECLARED GESTURE")
            Text("Coordinate 0 · +0.001").font(.headline).monospacedDigit()
            Text("The control starts unchanged. The perturbed copy receives one state displacement, then both follow the same recorded inputs, leak, bridge drive and transition residual.")
                .font(.caption).foregroundStyle(.secondary)
            info("Current full-state separation", number(frame.separationL2))
            info("Observed peak / initial separation", String(format: "%.3f×", evidence.resultSummary.peakGainOverInitial))
            info("Return threshold", "10% of initial · \(number(evidence.returnThreshold))")
            Text("This pair falls below that threshold at boundary \(evidence.resultSummary.returnBoundary ?? -1), for at least eight consecutive boundaries.")
                .font(.caption).foregroundStyle(.secondary)
            Text("A conditional simulated response, not a stability test or evidence about either being's experience. Clipping occurs in this simulation. It is not a native checkpoint replay, and its unclipped derivative validation is unestablished.")
                .font(.caption).foregroundStyle(.orange)
            Divider(); caption("INSPECT AN EXACT COORDINATE")
            HStack {
                Text("Coordinate \(selectedNode)").font(.headline).monospacedDigit()
                Spacer()
                Stepper("Coordinate", value: $selectedNode, in: 0...127).labelsHidden()
                    .accessibilityLabel("Simulation coordinate index, from zero")
            }
            info("Control", signed(frame.control[selectedNode]))
            info("Perturbed", signed(frame.intervention[selectedNode]))
            info("Exact difference", signed(frame.delta[selectedNode]))
            nodeGrid
            Text("The same sphere sites identify the same simulation coordinates. Neighboring patches are a drawing convention, not a claim about network connections.")
                .font(.caption).foregroundStyle(.secondary)
            Divider(); caption("EVIDENCE IDENTITY")
            info("Original simulation boundary", "\(frame.originalBoundaryStep)")
            Text(evidence.runId).font(.system(size: 10, design: .monospaced)).textSelection(.enabled)
            Text("State and model belong to the retained esn-divide benchmark. Preview volume is fixed at 68%; it is not a measured fill value. No wall-clock or PCA join is made.")
                .font(.caption).foregroundStyle(.secondary)
            Text("Resource SHA-256\n\(StateResponseEvidence.retainedSHA256)\n\nResults SHA-256\n\(evidence.sourceResultsSha256)")
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
                Text(field == .delta ? "Delta scale fixed to declared displacement; no frame normalization" : "Signed state scale fixed at −1…1")
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
    private func caption(_ value: String) -> some View { Text(value).font(.system(size: 10, weight: .medium)).tracking(1).foregroundStyle(.secondary) }
    private func signed(_ value: Double) -> String { String(format: "%+.6g", value) }
    private func number(_ value: Double) -> String { String(format: "%.6g", value) }
    private func info(_ title: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 3) { Text(title).font(.caption).foregroundStyle(.secondary); Text(value).font(.system(.body, design: .monospaced)) }
    }
}

private struct StateResponseDistancePlot: View {
    let evidence: StateResponseEvidence
    let selected: Int
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text("Full-state separation · L2").font(.caption)
                Spacer()
                Text("Dashed line: 10% return threshold").font(.caption2).foregroundStyle(.secondary)
            }
            Canvas { context, size in
                let top = 4.0, height = max(1, size.height - 8)
                func point(_ row: Int, _ value: Double) -> CGPoint {
                    CGPoint(x: Double(row) / 64 * size.width, y: top + (1 - value / evidence.plotMaximum) * height)
                }
                var response = Path()
                for frame in evidence.frames {
                    let p = point(frame.sampleIndex, frame.separationL2)
                    if frame.sampleIndex == 0 { response.move(to: p) } else { response.addLine(to: p) }
                }
                context.stroke(response, with: .color(.cyan), lineWidth: 2)
                var threshold = Path(); threshold.move(to: point(0, evidence.returnThreshold)); threshold.addLine(to: point(64, evidence.returnThreshold))
                context.stroke(threshold, with: .color(.orange.opacity(0.8)), style: StrokeStyle(lineWidth: 1, dash: [4, 4]))
                let current = point(selected, evidence.frames[selected].separationL2)
                var marker = Path(); marker.move(to: CGPoint(x: current.x, y: 0)); marker.addLine(to: CGPoint(x: current.x, y: size.height))
                context.stroke(marker, with: .color(.white.opacity(0.35)), lineWidth: 1)
                context.fill(Path(ellipseIn: CGRect(x: current.x - 3, y: current.y - 3, width: 6, height: 6)), with: .color(.white))
            }
            HStack { Text("0 · injected"); Spacer(); Text("16"); Spacer(); Text("32"); Spacer(); Text("48"); Spacer(); Text("64 boundaries") }
                .font(.caption2).foregroundStyle(.secondary)
        }.accessibilityElement(children: .ignore)
            .accessibilityLabel("Full-state distance at boundary \(selected): \(evidence.frames[selected].separationL2). Threshold \(evidence.returnThreshold). Plot is simulation boundaries, not seconds.")
    }
}
#endif
