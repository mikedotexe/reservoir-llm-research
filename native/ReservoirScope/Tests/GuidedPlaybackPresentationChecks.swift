import AppKit
import SwiftUI
import EssentialsCore

private final class GuidedActivity: @unchecked Sendable {
    private let lock = NSLock()
    private var starts = 0
    private var writes = 0
    func started() { lock.lock(); starts += 1; lock.unlock() }
    func wrote() { lock.lock(); writes += 1; lock.unlock() }
    var counts: (Int, Int) { lock.lock(); defer { lock.unlock() }; return (starts, writes) }
}

/// Separate mounted host and model checks; actual controls are exercised through CUA.
@MainActor private final class GuidedPlaybackChecks: NSObject, NSApplicationDelegate {
    private let activity = GuidedActivity()
    private lazy var model = ActionComparisonViewModel(sessionFactory: { [activity] _, _ in
        activity.started(); throw SurfaceRenderError("The guided check must not start an experiment")
    }, recordWriter: { [activity] _, _ in activity.wrote() }, workspaceURL: output.appendingPathComponent("Library"))
    private var output: URL { URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true) }
    private var host: NSHostingView<AnyView>!
    private var window: NSWindow!
    private var checks: [String] = []
    private var accessibilityIdentifiers: [String] = []

    func applicationDidFinishLaunching(_ notification: Notification) {
        Task { @MainActor in
            do { try await run(); exit(0) }
            catch { fputs("FAIL: \(error)\n", stderr); exit(1) }
        }
    }
    private func check(_ condition: Bool, _ message: String) throws {
        guard condition else { throw SurfaceRenderError(message) }
        checks.append(message); print("PASS \(checks.count): \(message)"); fflush(stdout)
    }
    private func settle() async throws {
        try await Task.sleep(for: .milliseconds(150))
        host.layoutSubtreeIfNeeded()
    }
    private func loaded() async throws {
        for _ in 0..<100 {
            if !model.loading && model.record != nil { try await settle(); return }
            try await Task.sleep(for: .milliseconds(40))
        }
        throw SurfaceRenderError("Recording did not load: \(model.error ?? model.status)")
    }
    private func inspectAccessibility() {
        var seen = Set<ObjectIdentifier>()
        func visit(_ object: Any, depth: Int) {
            guard depth < 40, let element = object as? NSAccessibilityProtocol,
                  seen.insert(ObjectIdentifier(element as AnyObject)).inserted else { return }
            if let identifier = element.accessibilityIdentifier(), !identifier.isEmpty { accessibilityIdentifiers.append(identifier) }
            for child in element.accessibilityChildren() ?? [] { visit(child, depth: depth + 1) }
        }
        visit(host as Any, depth: 0)
    }
    private func fixture(_ name: String) throws -> URL {
        guard let url = Bundle.module.url(forResource: name, withExtension: "json") else {
            throw SurfaceRenderError("Missing fixture \(name)")
        }
        return url
    }
    private func root() -> AnyView {
        AnyView(ActionComparisonExperience(model: model, guided: true)
            .frame(minWidth: 1100, minHeight: 820).preferredColorScheme(.dark))
    }
    private func run() async throws {
        guard CommandLine.arguments.count == 2,
              ProcessInfo.processInfo.environment["RESERVOIR_SCOPE_PREFERENCES"]?.hasPrefix("org.reservoir-scope.guided-check.") == true else {
            throw SurfaceRenderError("Pass a report directory and an isolated preference suite")
        }
        host = NSHostingView(rootView: root())
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1100, height: 820),
            styleMask: [.titled, .resizable], backing: .buffered, defer: false)
        window.isReleasedWhenClosed = false; window.contentView = host
        try await loaded()
        try check(model.stage == .minimal && model.row == 0 && model.isRecording,
                  "The mounted guide opens A at its first recorded step with isolated preferences")
        let count = model.framesCount
        for width in [1100.0, 1380.0] {
            window.setContentSize(NSSize(width: width, height: 820)); try await settle()
            try check(abs(host.bounds.width - width) < 1 && abs(host.bounds.height - 820) < 1,
                      "The production guided view mounts at \(Int(width)) × 820")
            inspectAccessibility()
        }
        let tour = GuidedTourModel(defaults: ScopePreferences.store)
        tour.continueLesson(model); try await settle()
        try check(model.rightFrame?.step == 12 && !model.replaying && model.framesCount == count,
                  "The existing Continue model action reaches a saved checkpoint and stays paused")
        model.step(); try await settle()
        try check(model.rightFrame?.step == 13 && model.framesCount == count,
                  "The Step model action inspects one saved step without extending the recording")
        model.changeSpeed(20); model.run(); try await settle()
        try check(model.replaying && model.row > 12, "The mounted production timer advances saved evidence")
        host.rootView = AnyView(Text("Another workspace")); try await settle()
        let paused = model.row; try await settle()
        try check(!model.replaying && model.row == paused, "Removing the guided view pauses its playback")
        host.rootView = root(); try await loaded()
        try check(!model.replaying && model.framesCount == count, "Returning opens paused saved evidence")

        model.open(try fixture("example-component-5"), initialRow: 29); try await loaded()
        try check(model.rightAction.map { model.applicationStepAtCursor($0) == nil } == true,
                  "At E step 30 the future journal return stays hidden")
        tour.continueLesson(model); try await settle()
        try check(model.rightFrame?.step == 31 && model.rightAction.map { model.applicationStepAtCursor($0) == 31 } == true,
                  "The Continue model action exposes E return at its recorded application step")
        model.open(try fixture("example-component-8"), initialRow: 119); try await loaded()
        tour.continueLesson(model); try await settle()
        try check(tour.nextCheckpoint(model) == nil && model.rightFrame?.step == 120 && !model.replaying,
                  "The completed H lesson has no further checkpoint or automatic playback")
        model.open(try fixture("example-observation-active-scripted")); try await loaded()
        try check(model.comparisonKind == .observation && !tour.matches(model) && model.isRecording,
                  "The mounted separate comparison remains a recording outside the lesson catalog")
        model.step(); try await settle()
        try check(model.rightFrame?.step == 2, "The separate comparison supports recorded-step inspection")
        let imported = output.appendingPathComponent("imported-action.json")
        try Data(contentsOf: fixture("example-component-1")).write(to: imported)
        model.open(imported); try await loaded()
        try check(!tour.matches(model) && model.isRecording, "An opened file remains a recording outside the guided catalog")
        model.step(); try await settle()
        try check(model.rightFrame?.step == 2 && model.framesCount == count, "An opened record advances only its saved cursor")
        model.leave()
        try check(activity.counts == (0, 0), "No experiment session or record save occurred")
        let report: [String: Any] = ["outcome": "passed", "checks": checks, "widths": [1100, 1380], "height": 820,
            "experiment_sessions": activity.counts.0, "record_writes": activity.counts.1,
            "in_process_accessibility_identifiers": Array(Set(accessibilityIdentifiers)).sorted(),
            "actual_button_and_disclosure_interaction": "not_exercised; requires separate CUA check",
            "scope": "Unpresented production NSHostingView and model-driven cursor/lifecycle invariants. No accessibility permission, presented-app interaction or human acceptance claim."]
        try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
            .write(to: output.appendingPathComponent("guided-playback.json"))
    }
}

@main struct GuidedPlaybackRunner {
    static func main() {
        let app = NSApplication.shared; app.setActivationPolicy(.prohibited)
        let delegate = GuidedPlaybackChecks(); app.delegate = delegate
        withExtendedLifetime(delegate) { app.run() }
    }
}
