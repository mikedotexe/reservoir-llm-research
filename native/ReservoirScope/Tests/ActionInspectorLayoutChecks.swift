// Presented-window inspector regression: actual accessibility disclosure actions,
// native scrolling, and an independent heartbeat. No files or providers are used.
import AppKit
import ApplicationServices
import SwiftUI
import EssentialsCore

private final class InspectorActionJournals: ActionJournalStore, @unchecked Sendable {
    private let lock = NSLock()
    private var entries: [String: JournalEntry] = [:]
    func save(_ entry: JournalEntry, arm: ActionArm) throws -> JournalSaveReceipt {
        lock.lock(); defer { lock.unlock() }; entries[arm.rawValue + "/" + entry.id] = entry
        return JournalSaveReceipt(status: .saved, entryID: entry.id, sha256: entry.sha256,
            relativePath: arm.rawValue + "/" + entry.id + ".json")
    }
    func read(entryID: String, arm: ActionArm) throws -> JournalEntry {
        lock.lock(); defer { lock.unlock() }
        guard let value = entries[arm.rawValue + "/" + entryID] else { throw SurfaceRenderError("Missing test journal") }
        return value
    }
}

@MainActor private final class ActionInspectorLayoutChecks: NSObject, NSApplicationDelegate {
    private let model = ActionComparisonViewModel(sessionFactory: { spec, _ in
        try ActionComparisonSession(specification: spec, journalStore: InspectorActionJournals())
    }, recordWriter: { _, _ in }, workspaceURL: URL(fileURLWithPath: "/controlled/research"))
    private var host: NSView!
    private var window: NSWindow!
    private var timer: Timer?
    private var phase = 0
    private var lastAction = 0.0
    private var started = 0.0
    private var lastCallback = 0.0
    private var gaps: [Double] = []
    private var checks = 0
    private var beats = 0
    private var client: Process?
    private var scrollCount = 0

    func applicationDidFinishLaunching(_ notification: Notification) {
        let root = VStack(spacing: 0) {
            Text("INSPECTOR REGRESSION · SYNTHETIC DATA").frame(height: 44)
            ActionComparisonExperience(model: model)
        }.frame(minWidth: 1100, minHeight: 820).preferredColorScheme(.dark)
        host = NSHostingView(rootView: root)
        window = NSWindow(contentRect: NSRect(x: 80, y: 80, width: 1100, height: 820),
            styleMask: [.titled, .resizable], backing: .buffered, defer: false)
        window.title = "Inspector regression · synthetic data"
        window.isReleasedWhenClosed = false; window.contentView = host
        window.orderFrontRegardless()
        started = ProcessInfo.processInfo.systemUptime; lastCallback = started
        model.step()
        timer = Timer.scheduledTimer(withTimeInterval: 0.03, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated { self?.advance() }
        }
    }
    private func check(_ condition: Bool, _ name: String) throws {
        guard condition else { throw SurfaceRenderError("FAIL: " + name) }
        checks += 1; print("PASS \(checks): \(name)"); fflush(stdout)
    }
    private func scrollInspector(bottom: Bool) throws {
        func collect(_ view: NSView) -> [NSScrollView] {
            (view as? NSScrollView).map { [$0] } ?? view.subviews.flatMap(collect)
        }
        guard let scroll = collect(host).max(by: { $0.convert(.zero, to: host).x < $1.convert(.zero, to: host).x }),
              let document = scroll.documentView else { throw SurfaceRenderError("No native inspector scroll view") }
        let y = bottom ? max(0, document.bounds.height - scroll.contentView.bounds.height) : 0
        scroll.contentView.scroll(to: NSPoint(x: 0, y: y)); scroll.reflectScrolledClipView(scroll.contentView)
        print("Scrolled inspector to \(y) / \(document.bounds.height)"); fflush(stdout)
    }
    private func advance() {
        do {
            let now = ProcessInfo.processInfo.systemUptime
            if beats >= 2 { gaps.append(now - lastCallback) }
            lastCallback = now; beats += 1
            if now - started > 20 { throw SurfaceRenderError("Inspector timed out in phase \(phase)") }
            host.layoutSubtreeIfNeeded()
            switch phase {
            case 0 where !model.working:
                try check(model.framesCount == 1 && model.canWrite, "Presented Step enables manual journal action")
                model.writeJournal(); phase = 1
            case 1 where !model.working:
                try check(model.rightAction?.saveReceipt?.status == .saved, "Presented journal action completes and saves")
                phase = 2; lastAction = now
            case 2 where now - lastAction > 0.15:
                let output = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
                let log = output.appendingPathComponent("accessibility.log")
                FileManager.default.createFile(atPath: log.path, contents: nil)
                let process = Process()
                process.executableURL = URL(fileURLWithPath: CommandLine.arguments[0])
                process.arguments = ["--ax-client", String(ProcessInfo.processInfo.processIdentifier)]
                process.standardOutput = try FileHandle(forWritingTo: log)
                process.standardError = process.standardOutput
                try process.run(); client = process
                phase = 3; lastAction = now
            case 3:
                if now - lastAction > 0.24 {
                    try scrollInspector(bottom: scrollCount % 2 == 0)
                    scrollCount += 1; lastAction = now
                }
                if let client, !client.isRunning {
                    try check(client.terminationStatus == 0, "Separate accessibility client expands all seven exact-data disclosures")
                    model.step(); phase = 4; lastAction = now
                }
            case 4 where !model.working && now - lastAction > 0.2:
                try check(model.framesCount == 2 && model.rightAction?.applicationStep == 2,
                    "Step remains usable with expanded journal, prompt and codec inspectors")
                try scrollInspector(bottom: false); phase = 5; lastAction = now
            case 5 where now - lastAction > 0.3:
                try check((gaps.max() ?? .infinity) < 1 && scrollCount > 0,
                    "The expanded and scrolled inspector keeps native callbacks below the one-second guard")
                try complete(); return
            default: break
            }
        } catch { print(error.localizedDescription); fflush(stdout); exit(1) }
    }
    private func complete() throws {
        timer?.invalidate(); model.leave()
        let report: [String: Any] = ["checks": checks, "expanded_disclosures": inspectorLabels, "native_scrolls": scrollCount,
            "heartbeats": beats, "maximum_callback_gap_seconds": gaps.max() ?? 0,
            "elapsed_seconds": ProcessInfo.processInfo.systemUptime - started,
            "scope": "Presented native NSHostingView, separate AXUIElement client performs actual disclosure presses, concurrent AppKit scrolling; synthetic local session"]
        let output = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
            .write(to: output.appendingPathComponent("layout.json"), options: .atomic)
        print("Inspector: \(checks) checks; gap \(gaps.max() ?? 0)s."); fflush(stdout)
        window.orderOut(nil); exit(0)
    }
}

private let inspectorLabels = ["Actual input · 66 coordinates", "Sensory spectrum · 32 values", "Prepared prompt · not sent", "Replayed response", "Complete saved journal", "Encoded text features", "Exact 48-coordinate return"]

private func inspectAccessibility(pid: pid_t) throws {
    guard AXIsProcessTrusted() else { throw SurfaceRenderError("Accessibility permission is required for this native regression") }
    let application = AXUIElementCreateApplication(pid)
    AXUIElementSetMessagingTimeout(application, 1)
    func value(_ element: AXUIElement, _ name: String) -> CFTypeRef? {
        var output: CFTypeRef?
        return AXUIElementCopyAttributeValue(element, name as CFString, &output) == .success ? output : nil
    }
    func label(_ element: AXUIElement) -> String {
        (value(element, kAXTitleAttribute) as? String) ?? (value(element, kAXDescriptionAttribute) as? String) ?? ""
    }
    func tree() -> [AXUIElement] {
        var result: [AXUIElement] = [], seen = Set<CFHashCode>()
        func visit(_ element: AXUIElement, _ depth: Int) {
            guard depth < 35, seen.insert(CFHash(element)).inserted else { return }
            result.append(element)
            for child in (value(element, kAXChildrenAttribute) as? [AXUIElement]) ?? [] { visit(child, depth + 1) }
        }
        visit(application, 0); return result
    }
    for name in inspectorLabels {
        let elements = tree()
        guard let element = elements.first(where: { label($0) == name }) else {
            print(elements.map(label).filter { !$0.isEmpty }.joined(separator: " | "))
            throw SurfaceRenderError("Missing exact disclosure: " + name)
        }
        let outcome = AXUIElementPerformAction(element, kAXPressAction as CFString)
        guard outcome == .success else { throw SurfaceRenderError("Could not expand \(name): \(outcome.rawValue)") }
        print("Expanded: \(name)"); fflush(stdout)
        Thread.sleep(forTimeInterval: 0.22)
        let expanded = tree()
        guard expanded.count > elements.count else {
            throw SurfaceRenderError("Expanded content did not become accessible after " + name)
        }
        print("Accessible elements after expansion: \(expanded.count)"); fflush(stdout)
    }
}

if CommandLine.arguments.count > 2 && CommandLine.arguments[1] == "--ax-client" {
    do { try inspectAccessibility(pid: pid_t(CommandLine.arguments[2])!); exit(0) }
    catch { print(error.localizedDescription); fflush(stdout); exit(1) }
}
MainActor.assumeIsolated {
    let app = NSApplication.shared
    app.setActivationPolicy(.accessory)
    let delegate = ActionInspectorLayoutChecks()
    app.delegate = delegate
    withExtendedLifetime(delegate) { app.run() }
}
