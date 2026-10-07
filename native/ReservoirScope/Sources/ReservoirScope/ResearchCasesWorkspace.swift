import SwiftUI
import UniformTypeIdentifiers

struct ResearchCasesWorkspace: View {
    @ObservedObject var model: ResearchCasesViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack(alignment: .top, spacing: 18) {
                VStack(alignment: .leading, spacing: 5) {
                    Text("Research cases").font(.title2.weight(.semibold))
                    Text("Choose a question, follow the reviewed account, then inspect its evidence.")
                        .font(.callout).foregroundStyle(.secondary)
                    Text("Read-only in this window. Opened cases are not added to your saved experiments.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                if model.opening {
                    Button("Cancel opening") { model.cancelOpening() }
                }
                Button("Open case…") { chooseCase() }.disabled(model.isLoading)
            }.padding(.horizontal, 22).padding(.vertical, 16)
            if model.isLoading {
                ProgressView(model.opening ? "Verifying the selected case…" : "Verifying included cases…")
                    .font(.caption).padding(.horizontal, 22).padding(.bottom, 12)
            }
            if let error = model.openError {
                Text(error).font(.caption).foregroundStyle(.orange).textSelection(.enabled)
                    .padding(.horizontal, 22).padding(.bottom, 12)
            }
            Divider()
            HSplitView {
                ScrollView {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Included questions").font(.headline)
                        if let error = model.bundledError {
                            Text(error).font(.caption).foregroundStyle(.orange).textSelection(.enabled)
                        }
                        ForEach(model.bundledCases) { item in
                            caseRow(item, selection: .bundled(item.id))
                        }
                        if !model.openedCases.isEmpty {
                            Divider().padding(.vertical, 4)
                            Text("Opened in this window").font(.headline)
                            Text(model.openedFilename).font(.caption).foregroundStyle(.secondary).textSelection(.enabled)
                            ForEach(model.openedCases) { item in
                                caseRow(item, selection: .opened(item.id))
                            }
                        }
                    }.padding(16)
                }.frame(minWidth: 270, idealWidth: 310, maxWidth: 380)
                Group {
                    if let item = model.selectedCase {
                        ResearchCaseView(researchCase: item).id(model.selection)
                    } else {
                        ContentUnavailableView("Choose a research question", systemImage: "text.book.closed",
                            description: Text("Each case keeps the question, recorded sequence, reviewed claims and limits beside its embedded evidence. You can also open an exported case."))
                    }
                }.frame(minWidth: 620, maxWidth: .infinity, maxHeight: .infinity)
            }
        }.onAppear { model.loadBundledIfNeeded() }
    }

    private func caseRow(_ item: ReviewedResearchCase, selection: ResearchCasesViewModel.Selection) -> some View {
        Button { model.select(selection) } label: {
            VStack(alignment: .leading, spacing: 6) {
                Text(item.question).font(.headline).fixedSize(horizontal: false, vertical: true)
                Text(item.title).font(.callout).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
                Text(item.interval).font(.caption).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
            }.frame(maxWidth: .infinity, alignment: .leading).padding(12)
                .background(model.selection == selection ? Color.cyan.opacity(0.12) : Color.white.opacity(0.035),
                            in: RoundedRectangle(cornerRadius: 8))
                .contentShape(Rectangle())
        }.buttonStyle(.plain)
            .accessibilityLabel(item.question + ". " + item.title + ". " + item.interval)
            .accessibilityAddTraits(model.selection == selection ? [.isSelected] : [])
    }

    @MainActor private func chooseCase() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.json]
        panel.allowsMultipleSelection = false
        panel.message = "Open a reviewed case read-only in this window. Embedded evidence is verified; historical source paths are never opened."
        guard panel.runModal() == .OK else { return }
        model.open(panel.url)
    }
}
