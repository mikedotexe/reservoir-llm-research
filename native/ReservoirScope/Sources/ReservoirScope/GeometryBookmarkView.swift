import SwiftUI
import UniformTypeIdentifiers

/// No polling, automatic imports, model calls or writes back to the beings.
struct GeometryBookmarkExperience: View {
    @State private var packet: GeometryBookmarkPacket?
    @State private var selected = 0
    @State private var frame = 0.0
    @State private var error: String?
    @State private var filename = ""

    init(packet: GeometryBookmarkPacket? = nil, selected: Int = 0) {
        _packet = State(initialValue: packet)
        _selected = State(initialValue: selected)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                VStack(alignment: .leading, spacing: 5) {
                    Text("Geometry bookmarks").font(.title2)
                    Text(packet.map { "\($0.body.owner.capitalized) · \($0.body.questionId) · \(filename)" } ?? "No question packet selected")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                Button { open() } label: { Label("Open packet", systemImage: "folder") }
                    .help("Open an explicitly exported question-geometry-v1 packet")
            }.padding(20)
            if let error { Text(error).foregroundStyle(.red).textSelection(.enabled).padding(.horizontal, 20).padding(.bottom, 12) }
            Divider()
            if let packet {
                HSplitView {
                    VStack(alignment: .leading, spacing: 12) {
                        Text(packet.body.question).font(.headline).textSelection(.enabled).padding(.horizontal)
                        List(packet.records.indices, id: \.self, selection: Binding<Int?>(get: { selected }, set: { if let value = $0 { selected = value; frame = 0 } })) { index in
                            VStack(alignment: .leading, spacing: 5) {
                                Text("\(index + 1). \(packet.records[index].kind.capitalized)")
                                Text(packet.records[index].authoredText ?? comparisonLabel(packet.records[index]))
                                    .font(.caption).foregroundStyle(.secondary).lineLimit(3)
                            }.tag(index).padding(.vertical, 4)
                        }
                    }.padding(.top, 18).frame(minWidth: 240, idealWidth: 290, maxWidth: 360)
                    ScrollView {
                        if packet.records.indices.contains(selected) {
                            detail(packet.records[selected], record: packet.body.history.records[selected])
                        } else {
                            ContentUnavailableView("No geometry records", systemImage: "square.stack")
                        }
                    }.frame(minWidth: 610, maxWidth: .infinity, maxHeight: .infinity)
                }
                Divider()
                VStack(alignment: .leading, spacing: 4) {
                    Text("Observational coordinates only · boot and node-layout identity unverified · not a causal or felt-state test")
                    Text("Packet SHA256 \(packet.digest)").font(.system(.caption2, design: .monospaced)).textSelection(.enabled)
                    Text("Integrity checked; producer authenticity and historical novelty are not established.")
                }.font(.caption).foregroundStyle(.secondary).padding(16)
            } else {
                ContentUnavailableView("No geometry bookmark", systemImage: "bookmark",
                    description: Text("Explicit question exports only. Nothing is read from live workspaces automatically."))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }.frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func detail(_ entry: GeometryBookmarkEntry, record: GeometryBookmarkRecord) -> some View {
        VStack(alignment: .leading, spacing: 18) {
            Text(entry.kind.capitalized).font(.title3)
            Text(record.id).font(.system(.caption, design: .monospaced)).foregroundStyle(.secondary).textSelection(.enabled)
            if let text = entry.authoredText {
                Text("Authored account").font(.caption).foregroundStyle(.secondary)
                Text(text).textSelection(.enabled).fixedSize(horizontal: false, vertical: true)
            }
            if entry.kind == "capture", let snapshot = entry.snapshot {
                snapshotView(snapshot)
            }
            if entry.kind == "prediction", let expectation = entry.maximumRmsDistance {
                Text("Predicted maximum mean-state RMS distance: \(expectation, specifier: "%.6g")")
                reference("Baseline", entry.baseline)
            }
            if entry.kind == "comparison", let distance = entry.rmsDistance {
                Text(distance, format: .number.precision(.fractionLength(6))).font(.system(size: 28, weight: .medium, design: .monospaced))
                Text(comparisonLabel(entry)).foregroundStyle(entry.thresholdMet == true ? .cyan : .orange)
                Text("RMS difference between the two unweighted mean 128-node vectors. Sampling and gaps can affect the result; opposite movements can cancel in a mean.")
                    .font(.callout).foregroundStyle(.secondary)
                reference("Prediction", entry.prediction); reference("Observation", entry.observation)
                Text("Prediction was stored before the second capture. Its source interval can predate that prediction; this is not a prospective trial or proof that the result was previously unseen.")
                    .font(.caption).foregroundStyle(.secondary)
            }
            if entry.kind == "revision" { reference("Revises", entry.target) }
        }.padding(24).frame(maxWidth: .infinity, alignment: .leading)
    }

    @ViewBuilder private func snapshotView(_ snapshot: GeometryBookmarkSnapshot) -> some View {
        if snapshot.frames.isEmpty {
            ContentUnavailableView("No recorded frames", systemImage: "square.stack")
        } else {
            let index = min(snapshot.frames.count - 1, max(0, Int(frame)))
            let current = snapshot.frames[index]
            VStack(alignment: .leading, spacing: 14) {
                Text("\(snapshot.frames.count) states · \(snapshot.durationMs) ms observed · \(snapshot.requestedSeconds) s requested · \(snapshot.gaps.count) recorder gaps > 1000 ms")
                    .font(.callout).textSelection(.enabled)
                Text("128 node coordinates × retained frames (ordinal rows)").font(.caption).foregroundStyle(.secondary)
                GeometryCoordinateMap(snapshot: snapshot, selected: index).frame(height: 240)
                    .accessibilityLabel("Activation matrix, \(snapshot.frames.count) recorded frames and 128 nodes; fixed minus one to plus one scale")
                HStack {
                    Label("−1", systemImage: "square.fill").foregroundStyle(.cyan)
                    Text("0").foregroundStyle(.secondary)
                    Label("+1", systemImage: "square.fill").foregroundStyle(.orange)
                    Spacer(); Text("No PCA, interpolation or inferred eigenvectors")
                }.font(.caption)
                HStack {
                    Text("Frame \(index + 1) / \(snapshot.frames.count)").monospacedDigit().frame(width: 120, alignment: .leading)
                    Slider(value: $frame, in: 0...Double(max(1, snapshot.frames.count - 1)), step: 1)
                        .disabled(snapshot.frames.count == 1).accessibilityLabel("Recorded frame")
                }
                Text("Engine \(current.tMs) ms · \(Date(timeIntervalSince1970: Double(current.wallClockUnixMs) / 1000).formatted(.iso8601)) · state RMS \(current.rms, specifier: "%.6f")")
                    .font(.system(.caption, design: .monospaced)).textSelection(.enabled)
                if !snapshot.gaps.isEmpty {
                    Text("Recorder gaps (engine ms): " + snapshot.gaps.map { "\($0.0)..\($0.1)" }.joined(separator: ", "))
                        .font(.caption).foregroundStyle(.orange).textSelection(.enabled)
                }
                DisclosureGroup("Exact selected coordinates") {
                    Text(current.activations.enumerated().map { "\($0.offset): \($0.element)" }.joined(separator: "  "))
                        .font(.system(.caption, design: .monospaced)).textSelection(.enabled)
                }
                reference("Recorder SHA256", snapshot.sourceSha256)
            }
        }
    }

    @ViewBuilder private func reference(_ name: String, _ value: String?) -> some View {
        if let value { VStack(alignment: .leading, spacing: 4) {
            Text(name).font(.caption).foregroundStyle(.secondary)
            Text(value).font(.system(.caption, design: .monospaced)).textSelection(.enabled)
        } }
    }
    private func comparisonLabel(_ entry: GeometryBookmarkEntry) -> String {
        entry.thresholdMet.map { $0 ? "Numerical threshold met" : "Numerical threshold not met" } ?? "Selected numerical evidence"
    }
    private func open() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.json]; panel.allowsMultipleSelection = false
        guard panel.runModal() == .OK, let url = panel.url else { return }
        do { packet = try GeometryBookmarkPacket.load(url); selected = 0; frame = 0; filename = url.lastPathComponent; error = nil }
        catch { self.error = error.localizedDescription }
    }
}

private struct GeometryCoordinateMap: View {
    let snapshot: GeometryBookmarkSnapshot
    let selected: Int
    var body: some View {
        Canvas { context, size in
            let width = size.width / 128
            let height = size.height / Double(snapshot.frames.count)
            for (row, frame) in snapshot.frames.enumerated() {
                for (node, value) in frame.activations.enumerated() {
                    let rect = CGRect(x: Double(node) * width, y: Double(row) * height, width: width, height: height)
                    context.fill(Path(rect), with: .color((value < 0 ? Color.cyan : Color.orange).opacity(abs(value))))
                }
            }
            context.stroke(Path(CGRect(x: 0, y: Double(selected) * height, width: size.width, height: height)), with: .color(.white), lineWidth: 1)
        }.background(Color.black.opacity(0.3))
    }
}
