import SwiftUI

private enum ScopeDestination: String, CaseIterable, Identifiable {
    case guided = "Guided tour", experiments = "Experiments", cases = "Research cases"
    case geometry = "Geometry bookmarks", observatory = "Observatory"
    var id: Self { self }
}
private enum EssentialsWorkspaceMode: String, CaseIterable, Identifiable {
    case explore = "Explore", stages = "Stage experiments", actions = "Actions & comparisons"
    var id: Self { self }
}

/// Each destination stays usable even when unrelated recorded evidence is absent.
/// Window-owned models keep explicit file selections alive across navigation.
struct ScopeWorkspace: View {
    @State private var destination: ScopeDestination = CommandLine.arguments.contains("--observatory") ? .observatory : .guided
    @State private var baseline: Result<EvidenceStore, Error>?
    @StateObject private var experiments = EssentialsViewModel()
    @StateObject private var exploration = ExplorationViewModel()
    @StateObject private var actions = ActionComparisonViewModel()
    @StateObject private var geometry = GeometryBookmarkViewModel()
    @StateObject private var researchCases = ResearchCasesViewModel()
    @State private var essentialsMode: EssentialsWorkspaceMode = .actions
    @State private var regulationURL: URL?
    @State private var libraryVisible = false

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 18) {
                Image(systemName: "circle.hexagongrid.fill").foregroundStyle(.cyan)
                Picker("Workspace", selection: Binding(get: { destination }, set: navigate)) {
                    ForEach(ScopeDestination.allCases) { Text($0.rawValue).tag($0) }
                }.pickerStyle(.segmented).labelsHidden().frame(maxWidth: 740)
                Spacer(minLength: 8)
                Button("Runs & examples") { stopExperiments(); libraryVisible = true }
            }.padding(.horizontal, 22).padding(.vertical, 12)
            if destination == .experiments {
                HStack {
                    Picker("Experiment workspace", selection: $essentialsMode) {
                        ForEach(EssentialsWorkspaceMode.allCases) { Text($0.rawValue).tag($0) }
                    }.pickerStyle(.segmented).frame(maxWidth: 530)
                    Spacer()
                    Text("New experiments do not start automatically").font(.caption).foregroundStyle(.secondary)
                }.padding(.horizontal, 22).padding(.bottom, 12)
            }
            Divider()
            switch destination {
            case .guided, .experiments:
                if let regulationURL {
                    RegulationExampleView(url: regulationURL, onClose: { self.regulationURL = nil })
                } else if destination == .guided || essentialsMode == .actions {
                    ActionComparisonExperience(model: actions, guided: destination == .guided, onTryExperiment: {
                        // The action model has just prepared an experiment; retain its
                        // settings and readiness message while stopping the other engines.
                        experiments.stop(); exploration.leave(); regulationURL = nil
                        essentialsMode = .actions; destination = .experiments
                    })
                } else if essentialsMode == .explore {
                    ExplorationExperience(model: exploration)
                } else {
                    EssentialsExperience(model: experiments)
                }
            case .cases:
                ResearchCasesWorkspace(model: researchCases)
            case .geometry:
                GeometryBookmarkExperience(model: geometry)
            case .observatory:
                switch baseline {
                case .success(let evidence): Observatory(evidence: evidence)
                case .failure(let error):
                    ContentUnavailableView("Baseline evidence could not load", systemImage: "doc.questionmark",
                        description: Text(error.localizedDescription + "\nOther workspaces remain available using the navigation above."))
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                case nil:
                    ProgressView("Opening recorded evidence…").frame(maxWidth: .infinity, maxHeight: .infinity)
                }
            }
        }
        .frame(minWidth: 1100, minHeight: 820)
        .background(Color(red: 0.035, green: 0.045, blue: 0.065))
        .preferredColorScheme(.dark)
        .task(id: destination) {
            if destination == .observatory, baseline == nil { baseline = Result { try EvidenceStore.load() } }
        }
        .onChange(of: essentialsMode) { _, value in
            regulationURL = nil
            if value != .stages { experiments.stop() }
            if value != .explore { exploration.leave() }
            if value != .actions { actions.leave() }
        }
        .sheet(isPresented: $libraryVisible) {
            ExperimentLibraryView(open: { url, format in
                navigate(to: .experiments)
                regulationURL = nil
                if format == "essentials-regulation-v1" { regulationURL = url }
                else if format == "essentials-exploration-v1" { essentialsMode = .explore; exploration.open(url) }
                else if format == "essentials-v1" { essentialsMode = .stages; experiments.open(url) }
                else { essentialsMode = .actions; actions.open(url) }
                libraryVisible = false
            }, openResearchCases: {
                navigate(to: .cases); libraryVisible = false
            })
        }
        .onAppear {
            ExperimentLifecycle.shared.prepare = {
                let a = await actions.flushForTermination()
                let b = await exploration.flushForTermination()
                let c = await experiments.flushForTermination()
                return a && b && c
            }
        }
        .onDisappear { stopExperiments() }
    }

    private func navigate(to value: ScopeDestination) {
        guard destination != value else { return }
        stopExperiments()
        regulationURL = nil
        destination = value
    }

    private func stopExperiments() {
        experiments.stop(); exploration.leave(); actions.leave()
    }
}
