import SwiftUI

private enum ScopeSubject: String, CaseIterable, Identifiable {
    case baseline = "Minime & Astrid", essentials = "Essentials"
    var id: Self { self }
}
private enum EssentialsWorkspaceMode: String, CaseIterable, Identifiable {
    case explore = "Explore", stages = "Stage experiments", actions = "Actions & comparisons"
    var id: Self { self }
}
private enum EssentialsArea: String, CaseIterable, Identifiable {
    case guided = "Guided tour", experiments = "Experiments"
    var id: Self { self }
}

/// Subject selection stays usable even when a baseline evidence file is absent.
struct ScopeWorkspace: View {
    @State private var subject: ScopeSubject = CommandLine.arguments.contains("--observatory") ? .baseline : .essentials
    @State private var baseline: Result<EvidenceStore, Error>?
    @StateObject private var experiments = EssentialsViewModel()
    @StateObject private var exploration = ExplorationViewModel()
    @StateObject private var actions = ActionComparisonViewModel()
    @StateObject private var geometry = GeometryBookmarkViewModel()
    @State private var essentialsMode: EssentialsWorkspaceMode = .actions
    @State private var essentialsArea: EssentialsArea = .guided
    @State private var regulationURL: URL?
    @State private var libraryVisible = false
    @State private var geometryBookmarks = false

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 18) {
                Image(systemName: "circle.hexagongrid.fill").foregroundStyle(.cyan)
                Picker("System", selection: $subject) {
                    ForEach(ScopeSubject.allCases) { Text($0.rawValue).tag($0) }
                }.pickerStyle(.segmented).labelsHidden().frame(width: 260)
                if subject == .essentials {
                    Picker("Essentials area", selection: Binding(get: { essentialsArea }, set: { value in
                        experiments.stop(); exploration.leave(); actions.leave()
                        regulationURL = nil; essentialsArea = value
                    })) {
                        ForEach(EssentialsArea.allCases) { Text($0.rawValue).tag($0) }
                    }.pickerStyle(.segmented).labelsHidden().frame(width: 250)
                    if essentialsArea == .experiments {
                        Picker("Experiment workspace", selection: $essentialsMode) {
                            ForEach(EssentialsWorkspaceMode.allCases) { Text($0.rawValue).tag($0) }
                        }.labelsHidden().frame(width: 180)
                    }
                } else {
                    Picker("Observation view", selection: $geometryBookmarks) {
                        Text("Observatory").tag(false)
                        Text("Geometry bookmarks").tag(true)
                    }.pickerStyle(.segmented).frame(width: 300)
                }
                Spacer()
                Button("Runs & examples") { experiments.stop(); exploration.leave(); actions.leave(); libraryVisible = true }
                if subject != .essentials || essentialsArea == .guided {
                    Text(subject == .essentials ? "EXPERIMENTAL WORK" : "SHARED RESERVOIR · RESEARCH OBSERVATIONS")
                        .font(.system(size: 10, weight: .medium)).tracking(1.4).foregroundStyle(.secondary).lineLimit(1)
                }
            }.padding(.horizontal, 22).padding(.vertical, 12)
            Divider()
            if subject == .essentials {
                if let regulationURL {
                    RegulationExampleView(url: regulationURL, onClose: { self.regulationURL = nil })
                } else if essentialsArea == .guided || essentialsMode == .actions {
                    ActionComparisonExperience(model: actions, guided: essentialsArea == .guided, onTryExperiment: {
                        essentialsMode = .actions; essentialsArea = .experiments
                    })
                } else if essentialsMode == .explore {
                    ExplorationExperience(model: exploration)
                } else if essentialsMode == .stages {
                    EssentialsExperience(model: experiments)
                }
            } else if geometryBookmarks {
                GeometryBookmarkExperience(model: geometry)
            } else {
                switch baseline {
                case .success(let evidence): Observatory(evidence: evidence)
                case .failure(let error):
                    ContentUnavailableView("Baseline evidence could not load", systemImage: "doc.questionmark",
                        description: Text(error.localizedDescription + "\nEssentials remains available using the switch above."))
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                case nil:
                    ProgressView("Opening recorded evidence…").frame(maxWidth: .infinity, maxHeight: .infinity)
                }
            }
        }
        .frame(minWidth: 1100, minHeight: 820)
        .background(Color(red: 0.035, green: 0.045, blue: 0.065))
        .preferredColorScheme(.dark)
        .task(id: subject) {
            if subject == .baseline, baseline == nil { baseline = Result { try EvidenceStore.load() } }
        }
        .onChange(of: subject) { _, value in
            if value != .essentials { experiments.stop(); exploration.leave(); actions.leave() }
        }
        .onChange(of: essentialsMode) { _, value in
            regulationURL = nil
            if value != .stages { experiments.stop() }
            if value != .explore { exploration.leave() }
            if value != .actions { actions.leave() }
        }
        .sheet(isPresented: $libraryVisible) {
            ExperimentLibraryView { url, format in
                subject = .essentials
                essentialsArea = .experiments
                regulationURL = nil
                if format == "essentials-regulation-v1" { regulationURL = url }
                else if format == "essentials-exploration-v1" { essentialsMode = .explore; exploration.open(url) }
                else if format == "essentials-v1" { essentialsMode = .stages; experiments.open(url) }
                else { essentialsMode = .actions; actions.open(url) }
                libraryVisible = false
            }
        }
        .onAppear {
            ExperimentLifecycle.shared.prepare = {
                let a = await actions.flushForTermination()
                let b = await exploration.flushForTermination()
                let c = await experiments.flushForTermination()
                return a && b && c
            }
        }
        .onDisappear { experiments.stop(); exploration.leave(); actions.leave() }
    }
}
