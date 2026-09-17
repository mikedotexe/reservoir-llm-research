import SwiftUI
import UniformTypeIdentifiers

struct ResearchCaseView: View {
    let researchCase: ReviewedResearchCase
    @State private var expanded: Set<String> = []
    @State private var exportError: String?
    @State private var exporting = false

    var body: some View {
        ScrollViewReader { proxy in
            VStack(alignment: .leading, spacing: 12) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 5) {
                        Text(researchCase.title).font(.title2.weight(.semibold))
                        Text("Reviewed research case · recorded evidence · read-only")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    Spacer()
                    Button(exporting ? "Exporting…" : "Export case…") { exportCase() }.disabled(exporting)
                }
                if let exportError { Text(exportError).foregroundStyle(.orange).font(.caption).textSelection(.enabled) }
                ScrollView {
                    VStack(alignment: .leading, spacing: 22) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text(researchCase.question).font(.title3)
                            Text(researchCase.summary)
                            Text("Author: " + researchCase.author).font(.caption)
                            Text("Source owner: " + researchCase.sourceOwner).font(.caption)
                            Text("Evidence interval: " + researchCase.interval).font(.caption)
                        }
                        VStack(alignment: .leading, spacing: 10) {
                            sectionTitle("What happened")
                            ForEach(Array(researchCase.sequence.enumerated()), id: \.offset) { _, event in
                                VStack(alignment: .leading, spacing: 6) {
                                    Text(event.title).font(.headline)
                                    Text(event.status == .observed ? "Observed in the retained evidence" : "Not observed in this case")
                                        .font(.caption).foregroundStyle(event.status == .observed ? Color.mint : Color.orange)
                                    if let timestamp = event.timestamp { Text(timestamp).font(.caption).foregroundStyle(.secondary) }
                                    Text(event.detail)
                                    evidenceLinks(event.materialIDs, proxy: proxy)
                                }.padding(12).frame(maxWidth: .infinity, alignment: .leading)
                                    .background(.white.opacity(0.035), in: RoundedRectangle(cornerRadius: 8))
                            }
                        }
                        VStack(alignment: .leading, spacing: 10) {
                            sectionTitle("What the evidence supports")
                            Text("These are reviewed interpretations. File verification checks embedded text, hashes, quotations and references; it does not prove an interpretation.")
                                .font(.caption).foregroundStyle(.secondary)
                            ForEach(researchCase.claims) { claim in
                                VStack(alignment: .leading, spacing: 7) {
                                    Text(claim.classification.title).font(.headline)
                                        .foregroundStyle(claim.classification == .contradicted ? Color.orange : Color.mint)
                                    Text("“" + claim.quote + "”").textSelection(.enabled)
                                    Text(claim.explanation).font(.callout)
                                    evidenceLinks([claim.materialID] + claim.evidenceIDs.filter { $0 != claim.materialID }, proxy: proxy)
                                }.padding(12).frame(maxWidth: .infinity, alignment: .leading)
                                    .background(.white.opacity(0.035), in: RoundedRectangle(cornerRadius: 8))
                            }
                        }
                        VStack(alignment: .leading, spacing: 8) {
                            sectionTitle("What remains uncertain")
                            ForEach(Array(researchCase.limits.enumerated()), id: \.offset) { _, limit in
                                Text("• " + limit).fixedSize(horizontal: false, vertical: true)
                            }
                        }
                        VStack(alignment: .leading, spacing: 10) {
                            sectionTitle("Exact supplied and recorded material")
                            Text("Everything below is embedded in this case. Historical paths identify sources and are never opened.")
                                .font(.caption).foregroundStyle(.secondary)
                            ForEach(researchCase.materials) { material in
                                DisclosureGroup(isExpanded: Binding(
                                    get: { expanded.contains(material.id) },
                                    set: { if $0 { expanded.insert(material.id) } else { expanded.remove(material.id) } }
                                )) {
                                    VStack(alignment: .leading, spacing: 8) {
                                        if let note = material.note { Text(note).font(.caption) }
                                        ScrollView {
                                            Text(material.content).font(.system(.caption, design: .monospaced))
                                                .frame(maxWidth: .infinity, alignment: .leading).textSelection(.enabled)
                                        }.frame(minHeight: 140, maxHeight: 320)
                                            .padding(10).background(.black.opacity(0.18), in: RoundedRectangle(cornerRadius: 6))
                                        Text("Embedded text SHA-256: " + material.sha256).font(.caption2).textSelection(.enabled)
                                        if let path = material.sourcePath {
                                            Text("Historical source: " + path).font(.caption2).textSelection(.enabled)
                                        }
                                        if let hash = material.sourceSHA256 {
                                            Text("Recorded source artifact SHA-256: " + hash).font(.caption2).textSelection(.enabled)
                                        }
                                    }.padding(.top, 8)
                                } label: {
                                    VStack(alignment: .leading, spacing: 3) {
                                        Text(material.title).font(.headline)
                                        Text(material.kind).font(.caption).foregroundStyle(.secondary)
                                    }
                                }.padding(10).background(.white.opacity(0.025), in: RoundedRectangle(cornerRadius: 8))
                                    .id("material-" + material.id)
                            }
                        }
                    }.padding(.trailing, 8)
                }
            }.padding(22)
        }.navigationTitle("Reviewed research case")
    }
    private func sectionTitle(_ text: String) -> some View { Text(text).font(.title3.weight(.semibold)) }
    private func evidenceLinks(_ ids: [String], proxy: ScrollViewProxy) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            ForEach(Array(Set(ids)).sorted(), id: \.self) { id in
                if let material = researchCase.material(id) {
                    Button("Show evidence: " + material.title) {
                        expanded.insert(id)
                        withAnimation { proxy.scrollTo("material-" + id, anchor: .top) }
                    }.font(.caption).buttonStyle(.link)
                }
            }
        }
    }
    @MainActor private func exportCase() {
        let panel = NSSavePanel(); panel.allowedContentTypes = [.json]
        let filename = researchCase.id.filter { $0.isASCII && ($0.isLetter || $0.isNumber || $0 == "-" || $0 == "_") }
        panel.nameFieldStringValue = (filename.isEmpty ? "reviewed-research-case" : filename) + ".json"
        panel.message = "Export this case with its embedded evidence. Reopen it through Runs & examples → Import."
        guard panel.runModal() == .OK, let url = panel.url else { return }
        let item = researchCase
        exporting = true; exportError = nil
        Task {
            do {
                try await Task.detached(priority: .utility) {
                    try ResearchCaseCatalog(cases: [item]).encoded().write(to: url, options: .atomic)
                }.value
            } catch { exportError = "The case remains open. Export failed: " + error.localizedDescription }
            exporting = false
        }
    }
}
