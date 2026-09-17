import SwiftUI
import UniformTypeIdentifiers

struct ExperimentLibraryView: View {
    let open: (URL, String) -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var examples: [ExperimentStore.Entry] = []
    @State private var runs: [ExperimentStore.Entry] = []
    @State private var researchCases: [ReviewedResearchCase] = []
    @State private var importedCases: [ReviewedResearchCase] = []
    @State private var selectedCase: ReviewedResearchCase?
    @State private var caseVisible = false
    @State private var error: String?
    @State private var loading = false
    @State private var preparationVisible = false
    @State private var preparationReport: Data?
    @State private var preparationRetry: Data?
    @State private var preparationAmendment: Data?
    @State private var preparationSummary: String?
    @State private var preparationRetrySummary: String?
    private enum PreparationExport { case original, retry, amendment }
    private struct CatalogItem: Decodable {
        let id: String; let title: String; let file: String; let format: String; let provenance: String
        let group: String?; let order: Int?; let lessonID: String?
    }
    var body: some View {
        NavigationStack {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                VStack(alignment: .leading) {
                    Text("Runs & examples").font(.title2.weight(.semibold))
                    Text("Local experiments and reviewed cases · opening evidence never calls a model").font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                Button("Import…") { chooseImport() }.disabled(loading)
                Button("Refresh") { Task { await refresh() } }.disabled(loading)
                Button("Done") { dismiss() }
            }
            if loading { ProgressView("Reading the local library…") }
            if let error { Text(error).font(.caption).foregroundStyle(.orange).textSelection(.enabled) }
            List {
                Section("Guided examples") { ForEach(group("guided")) { entry in row(entry) } }
                Section("Recorded model writing") { ForEach(group("model")) { entry in row(entry) } }
                Section("Separate comparisons & mechanisms") { ForEach(group("comparison")) { entry in row(entry) } }
                Section("Reviewed research cases") {
                    ForEach(researchCases) { item in caseRow(item, imported: false) }
                    if !importedCases.isEmpty {
                        Text("Opened from a file · read-only for this browser session").font(.caption).foregroundStyle(.secondary)
                        ForEach(importedCases) { item in caseRow(item, imported: true) }
                    }
                }
                Section("Saved on this Mac") {
                    if runs.isEmpty { Text("Your saved experiments will appear here.").foregroundStyle(.secondary) }
                    ForEach(runs) { entry in row(entry) }
                }
                Section {
                    DisclosureGroup("Preparation history · all attempts retained", isExpanded: $preparationVisible) {
                        if let preparationSummary {
                            VStack(alignment: .leading, spacing: 6) {
                                Text(preparationSummary).font(.caption).textSelection(.enabled)
                                Button("Export original preparation report…") { exportPreparation(.original) }
                                if preparationAmendment != nil {
                                    Text("A prompt-version mismatch was corrected before generation. The original unavailable attempt is retained; no model request was made.")
                                        .font(.caption).foregroundStyle(.secondary)
                                    Button("Export protocol correction…") { exportPreparation(.amendment) }
                                }
                            }.padding(.vertical, 6)
                        }
                        if let preparationRetrySummary {
                            VStack(alignment: .leading, spacing: 6) {
                                Text(preparationRetrySummary).font(.caption).textSelection(.enabled)
                                Text("This later retry is separate from the original attempt and protocol correction. Every recorded outcome is retained.")
                                    .font(.caption).foregroundStyle(.secondary)
                                Button("Export September 16 retry report…") { exportPreparation(.retry) }
                            }.padding(.vertical, 6)
                        }
                        ForEach(group("preparation")) { entry in row(entry) }
                    }
                }
            }
            Text(ExperimentStore.defaultRoot.path).font(.caption2).foregroundStyle(.secondary).textSelection(.enabled)
        }.padding(22).task { await refresh() }
        .navigationDestination(isPresented: $caseVisible) {
            if let selectedCase { ResearchCaseView(researchCase: selectedCase) }
        }
        }.frame(minWidth: 760, minHeight: 580)
    }
    private func caseRow(_ item: ReviewedResearchCase, imported: Bool) -> some View {
        Button { selectedCase = item; caseVisible = true } label: {
            HStack {
                Image(systemName: "text.book.closed")
                VStack(alignment: .leading, spacing: 4) {
                    Text(item.title).font(.body)
                    Text((imported ? "Imported reviewed case" : "Reviewed research case") + " · " + item.interval)
                        .font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                Image(systemName: "chevron.right")
            }.padding(.vertical, 5).contentShape(Rectangle())
        }.buttonStyle(.plain)
    }
    private func group(_ name: String) -> [ExperimentStore.Entry] {
        examples.filter { $0.group == name }.sorted { $0.order == $1.order ? $0.id < $1.id : $0.order < $1.order }
    }
    private func row(_ entry: ExperimentStore.Entry) -> some View {
        Button { open(entry.url, entry.format) } label: {
            HStack {
                Image(systemName: entry.bundled ? "shippingbox" : "doc.text")
                VStack(alignment: .leading, spacing: 4) {
                    Text(entry.title).font(.body)
                    Text(entry.detail).font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                Image(systemName: "arrow.up.right")
            }.padding(.vertical, 5).contentShape(Rectangle())
        }.buttonStyle(.plain)
    }
    @MainActor private func refresh() async {
        loading = true; error = nil
        preparationReport = nil; preparationSummary = nil
        preparationRetry = nil; preparationRetrySummary = nil; preparationAmendment = nil
        do {
            let catalog = Bundle.module.url(forResource: "examples-index", withExtension: "json")
                ?? Bundle.module.url(forResource: "examples-index", withExtension: "json", subdirectory: "Resources")
            if let catalog {
                let items = try JSONDecoder().decode([CatalogItem].self, from: Data(contentsOf: catalog))
                examples = try items.map { item in
                    guard !item.file.contains("/"), !item.file.contains(".."), item.file.hasSuffix(".json") else {
                        throw NSError(domain: "ExperimentLibrary", code: 1, userInfo: [NSLocalizedDescriptionKey: "Invalid bundled example filename."])
                    }
                    return ExperimentStore.Entry(id: item.id, title: item.title, detail: item.provenance, format: item.format,
                        url: catalog.deletingLastPathComponent().appendingPathComponent(item.file), bundled: true,
                        group: item.group ?? "guided", order: item.order ?? 0, lessonID: item.lessonID)
                }
                let reportURL = catalog.deletingLastPathComponent().appendingPathComponent("guided-observation-recording.json")
                preparationAmendment = try? Data(contentsOf: catalog.deletingLastPathComponent().appendingPathComponent("guided-observation-amendment.json"))
                if FileManager.default.fileExists(atPath: reportURL.path) {
                    let data = try Data(contentsOf: reportURL)
                    let report = try JSONSerialization.jsonObject(with: data) as? [String: Any]
                    preparationReport = data
                    preparationSummary = "Original active-state model preparation: " + (report?["status"] as? String ?? "unknown")
                        + ". " + (report?["error"] as? String ?? "One bounded attempt; all recorded outcomes retained.")
                }
                let retryURL = catalog.deletingLastPathComponent().appendingPathComponent("guided-observation-retry-20260916.json")
                if FileManager.default.fileExists(atPath: retryURL.path) {
                    let data = try Data(contentsOf: retryURL)
                    let report = try JSONSerialization.jsonObject(with: data) as? [String: Any]
                    preparationRetry = data
                    let status = report?["status"] as? String ?? "unknown"
                    let attempt = (report?["attempts"] as? [[String: Any]])?.first
                    var details: [String] = []
                    if let steps = attempt?["steps"] as? Int { details.append("\(steps) steps") }
                    if let requests = attempt?["request_count"] as? Int { details.append("\(requests) requests") }
                    if let counts = attempt?["journal_counts"] as? [String: Int], !counts.isEmpty {
                        details.append("\(counts.values.reduce(0, +)) saved journals")
                    }
                    if let verified = attempt?["verified"] as? Bool {
                        details.append(verified ? "record verification passed" : "record verification failed")
                    }
                    preparationRetrySummary = "Active-state model retry · September 16, 2026: " + status + ". "
                        + (details.isEmpty ? "" : details.joined(separator: " · ") + ". ")
                        + (report?["error"] as? String ?? (status == "failed"
                            ? "Partial recording retained." : "One bounded retry; all recorded outcomes retained."))
                }
            } else { examples = []; error = "The example catalog is missing from this package." }
            if let casesURL = Bundle.module.url(forResource: "research-cases-v1", withExtension: "json")
                ?? Bundle.module.url(forResource: "research-cases-v1", withExtension: "json", subdirectory: "Resources") {
                do {
                    researchCases = try await Task.detached(priority: .utility) { try ResearchCaseCatalog.read(from: casesURL).cases }.value
                } catch { researchCases = []; self.error = "Reviewed cases could not be verified: " + error.localizedDescription }
            } else {
                researchCases = []; error = "The reviewed research case catalog is missing from this package."
            }
            runs = try await Task.detached(priority: .utility) { try ExperimentStore().entries() }.value
        } catch { self.error = error.localizedDescription }
        loading = false
    }
    @MainActor private func exportPreparation(_ source: PreparationExport) {
        let data: Data?
        let filename: String
        switch source {
        case .original: data = preparationReport; filename = "active-state-preparation.json"
        case .retry: data = preparationRetry; filename = "active-state-retry-20260916.json"
        case .amendment: data = preparationAmendment; filename = "active-state-protocol-correction.json"
        }
        guard let data else { return }
        let panel = NSSavePanel(); panel.allowedContentTypes = [.json]
        panel.nameFieldStringValue = filename
        guard panel.runModal() == .OK, let url = panel.url else { return }
        do { try data.write(to: url, options: .atomic) }
        catch { self.error = error.localizedDescription }
    }
    @MainActor private func chooseImport() {
        let panel = NSOpenPanel(); panel.allowedContentTypes = [.json]; panel.allowsMultipleSelection = false
        panel.message = "Import a portable experiment or open an exported research case. Original paths are not followed."
        guard panel.runModal() == .OK, let url = panel.url else { return }
        loading = true
        Task {
            do {
                let cases = try await Task.detached(priority: .utility) { () throws -> ResearchCaseCatalog? in
                    if let cases = try ResearchCaseCatalog.readIfSupported(from: url) { return cases }
                    _ = try ExperimentStore().importVerified(url)
                    return nil
                }.value
                if let cases {
                    importedCases = cases.cases
                    selectedCase = cases.cases.first; caseVisible = true; loading = false; error = nil
                } else { await refresh() }
            } catch { self.error = error.localizedDescription; loading = false }
        }
    }
}
