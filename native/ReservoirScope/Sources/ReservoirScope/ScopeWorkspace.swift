import SwiftUI

private enum ScopeSubject: String, CaseIterable, Identifiable {
    case baseline = "Minime & Astrid", essentials = "Essentials"
    var id: Self { self }
}
private enum EssentialsWorkspaceMode: String, CaseIterable, Identifiable {
    case explore = "Explore", stages = "Stage experiments", actions = "Actions & comparisons"
    var id: Self { self }
}

/// Subject selection stays usable even when a baseline evidence file is absent.
struct ScopeWorkspace: View {
    @State private var subject: ScopeSubject = CommandLine.arguments.contains("--essentials") ? .essentials : .baseline
    @State private var baseline: Result<EvidenceStore, Error>?
    @StateObject private var experiments = EssentialsViewModel()
    @StateObject private var exploration = ExplorationViewModel()
    @StateObject private var actions = ActionComparisonViewModel()
    @State private var essentialsMode: EssentialsWorkspaceMode = .explore

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 18) {
                Image(systemName: "circle.hexagongrid.fill").foregroundStyle(.cyan)
                Picker("System", selection: $subject) {
                    ForEach(ScopeSubject.allCases) { Text($0.rawValue).tag($0) }
                }.pickerStyle(.segmented).labelsHidden().frame(width: 260)
                if subject == .essentials {
                    Picker("Essentials workspace", selection: $essentialsMode) {
                        ForEach(EssentialsWorkspaceMode.allCases) { Text($0.rawValue).tag($0) }
                    }.pickerStyle(.segmented).labelsHidden().frame(width: 420)
                }
                Spacer()
                Text(subject == .essentials ? "EXPERIMENTAL WORK" : "SHARED RESERVOIR · RESEARCH OBSERVATIONS")
                    .font(.system(size: 10, weight: .medium)).tracking(1.4).foregroundStyle(.secondary).lineLimit(1)
            }.padding(.horizontal, 22).padding(.vertical, 12)
            Divider()
            if subject == .essentials {
                if essentialsMode == .explore {
                    ExplorationExperience(model: exploration)
                } else if essentialsMode == .stages {
                    EssentialsExperience(model: experiments)
                } else {
                    ActionComparisonExperience(model: actions)
                }
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
            if value != .stages { experiments.stop() }
            if value != .explore { exploration.leave() }
            if value != .actions { actions.leave() }
        }
        .onDisappear { experiments.stop(); exploration.leave(); actions.leave() }
    }
}
