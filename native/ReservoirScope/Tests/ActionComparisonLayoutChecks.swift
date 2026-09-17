// Actual comparison SwiftUI view with synthetic sessions and a real AppKit loop.
// Journals stay in memory; no persistence or provider requests leave this process.
import AppKit
import SwiftUI
import EssentialsCore

private final class LayoutActionJournals: ActionJournalStore, @unchecked Sendable {
    private let lock = NSLock()
    private var entries: [String: JournalEntry] = [:]
    func save(_ entry: JournalEntry, arm: ActionArm) throws -> JournalSaveReceipt {
        lock.lock(); defer { lock.unlock() }
        entries[arm.rawValue + "/" + entry.id] = entry
        return JournalSaveReceipt(status: .saved, entryID: entry.id, sha256: entry.sha256,
            relativePath: arm.rawValue + "/" + entry.id + ".json")
    }
    func read(entryID: String, arm: ActionArm) throws -> JournalEntry {
        lock.lock(); defer { lock.unlock() }
        guard let entry = entries[arm.rawValue + "/" + entryID] else { throw SurfaceRenderError("Missing in-memory journal") }
        return entry
    }
}

@MainActor private final class ActionComparisonLayoutChecks: NSObject, NSApplicationDelegate {
    private let model = ActionComparisonViewModel(sessionFactory: { spec, _ in
        try ActionComparisonSession(specification: spec, journalStore: LayoutActionJournals())
    }, recordWriter: { _, _ in }, workspaceURL: URL(fileURLWithPath: "/controlled/research"))
    private var host: NSView!
    private var window: NSWindow!
    private var timer: Timer?
    private var phase = 0
    private var phaseStarted = 0.0
    private var index = 0
    private var checks = 0
    private var started = 0.0
    private var lastCallback = 0.0
    private var heldCount = 0
    private var comparisonFrames = 0
    private var timings: [Double] = []
    private var callbackGaps: [Double] = []
    private var fittingSizes: [[Double]] = []
    private var surfaceSizes: [[String: Any]] = []

    func applicationDidFinishLaunching(_ notification: Notification) {
        guard CommandLine.arguments.count == 2 else { finish(SurfaceRenderError("Expected report directory")); return }
        let root = VStack(spacing: 0) {
            Text("ACTIONS & COMPARISONS NATIVE CHECK").frame(height: 44)
            ActionComparisonExperience(model: model)
        }.frame(minWidth: 1100, minHeight: 820).preferredColorScheme(.dark)
        host = NSHostingView(rootView: root)
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1380, height: 940),
            styleMask: [.titled, .resizable], backing: .buffered, defer: false)
        window.isReleasedWhenClosed = false; window.contentView = host
        started = ProcessInfo.processInfo.systemUptime; lastCallback = started
        model.select(.reservoirReturn)
        model.compareWithPrevious(); model.run()
        timer = Timer.scheduledTimer(withTimeInterval: 0.02, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated { self?.advance() }
        }
    }

    private func check(_ condition: Bool, _ description: String) throws {
        guard condition else { throw SurfaceRenderError("FAIL: " + description) }
        checks += 1; print("PASS \(checks): \(description)"); fflush(stdout)
    }
    private func next(_ value: Int, _ now: Double) { phase = value; phaseStarted = now }
    private func advance() {
        do {
            let now = ProcessInfo.processInfo.systemUptime
            if index >= 2 { callbackGaps.append(now - lastCallback) }
            lastCallback = now
            if now - started > 25 { throw SurfaceRenderError("Native comparison timed out in phase \(phase): \(model.status) \(model.error ?? "")") }
            switch phase {
            case 0 where !model.working:
                try check(model.isComparison && model.leftRecord?.stage == .journalOutput && model.rightRecord?.stage == .reservoirReturn,
                    "Compare creates the preceding D arm and selected E arm")
                model.stop(); model.step(); next(1, now)
            case 1 where !model.working:
                try check(model.framesCount == 1 && model.canWrite && !model.running,
                    "Step creates one paused boundary that enables manual Write journal")
                try check(model.leftState == model.rightState, "Paired states match before journal return")
                model.writeJournal(); next(2, now)
            case 2 where !model.working:
                try check(model.framesCount == 1 && model.rightRecord?.actions.count == 1 && model.leftRecord?.actions.count == 1,
                    "Manual writing records both action receipts without a hidden simulation step")
                try check(model.rightAction?.saveReceipt?.status == .saved && model.rightAction?.requestStarted == false
                    && model.rightAction?.tapePacketID != nil && model.rightAction?.applicationStep == nil,
                    "Replay retains a saved journal and prepared prompt without claiming a model request or early application")
                model.step(); next(3, now)
            case 3 where !model.working:
                try check(model.framesCount == 2 && model.rightAction?.applicationStep == 2 && model.leftAction?.applicationStep == nil,
                    "Only the return arm applies the saved journal at the next step")
                try check(model.externalDifferences.allSatisfy { $0 == 0 }
                    && model.semanticDifferences.contains { $0 != 0 } && model.coordinateDifferences.contains { $0 != 0 },
                    "Exact input and state differences expose the sole semantic-return intervention")
                next(4, now)
            case 4 where now - phaseStarted > 0.12:
                try inspectSurfaces("E pair · 1380 × 940", checkCamera: true)
                window.setContentSize(NSSize(width: 1100, height: 820)); next(5, now)
            case 5 where now - phaseStarted > 0.12:
                try inspectSurfaces("E pair · 1100 × 820", checkCamera: false)
                model.changeSpeed(20); model.run(); next(6, now)
            case 6 where now - phaseStarted > 1.2 && !model.working:
                try check(model.running && model.framesCount >= 5, "The production timer advances both arms without manual ticks or steps")
                model.stop(); heldCount = model.framesCount; next(7, now)
            case 7 where now - phaseStarted > 0.25 && !model.working:
                try check(!model.running && model.framesCount == heldCount, "Stop freezes further observations while the AppKit loop remains active")
                comparisonFrames = model.framesCount
                model.scrub(1)
                try check(model.leftFrame?.step == 2 && model.rightFrame?.step == 2
                    && model.leftState == model.leftRecord?.frames[1].state && model.rightState == model.rightRecord?.frames[1].state,
                    "The shared cursor restores both exact historical states at the same step")
                model.run(); model.select(.regulation)
                try check(!model.running && model.stage == .regulation, "Selecting another ladder version stops the previous run")
                model.compareWithPrevious(); model.run(); next(8, now)
            case 8 where !model.working:
                model.stop(); model.step(); next(9, now)
            case 9 where !model.working:
                if model.framesCount < 6 { model.step() }
                else {
                    print("H diagnostic: stage=\(model.stage.title) spec=\(model.record?.specification.stage.title ?? "nil") left=\(model.leftFrame?.step ?? -1) right=\(model.rightFrame?.step ?? -1) count=\(model.framesCount) paired=\(model.isComparison) maxDelta=\(model.coordinateDifferences.map { abs($0) }.max() ?? -1) error=\(model.error ?? "none")")
                    try check(model.leftFrame?.state == model.rightFrame?.state,
                        "H fixed-input comparison can retain identical reservoir states")
                    try check(model.leftFrame?.fillPercent != nil && model.rightFrame?.fillPercent != nil
                        && model.leftFrame?.retentionUsed != model.rightFrame?.retentionUsed,
                        "H retains both fill measurements and distinct sensory retention for the additional traces")
                    next(10, now)
                }
            case 10 where now - phaseStarted > 0.15:
                try check(model.leftFrame?.fillPercent != nil && model.rightFrame?.control != nil,
                    "H primary presentation has paired fill, retention and controller evidence at 1100 × 820")
                model.leave(); heldCount = model.framesCount; next(11, now)
            case 11 where now - phaseStarted > 0.25:
                try check(!model.running && !model.replaying && model.framesCount == heldCount,
                    "Leaving Actions stops run and replay progression")
                try complete(); return
            default: break
            }
            let start = ProcessInfo.processInfo.systemUptime
            host.needsLayout = true; host.layoutSubtreeIfNeeded()
            let fitting = host.fittingSize
            if index >= 2 { timings.append(ProcessInfo.processInfo.systemUptime - start) }
            fittingSizes.append([Double(fitting.width), Double(fitting.height)])
            index += 1
        } catch { finish(error) }
    }

    private func inspectSurfaces(_ label: String, checkCamera: Bool) throws {
        func collect(_ view: NSView) -> [StateSurfaceMetalView] {
            (view as? StateSurfaceMetalView).map { [$0] } ?? view.subviews.flatMap(collect)
        }
        let surfaces = collect(host)
        try check(surfaces.count == 2 && surfaces.allSatisfy { $0.renderer?.nodeCount == 32 && $0.renderer?.mesh?.sitePositions.count == 32 },
            "\(label): both actual renderers have 32 coordinates and 32 exact markers")
        let a = surfaces[0].bounds.size, b = surfaces[1].bounds.size
        print("Surface dimensions: \(a) and \(b)")
        try check(a.width >= 240 && a.height >= 165 && abs(a.width - b.width) <= 1 && abs(a.height - b.height) <= 1,
            "\(label): paired 3D views retain equal useful dimensions")
        surfaceSizes.append(["layout": label, "width": Double(a.width), "height": Double(a.height)])
        try check(surfaces.allSatisfy { $0.accessibilityLabel()?.contains("32 coordinates") == true },
            "\(label): each rendered surface exposes its actual count to accessibility")
        if checkCamera {
            let left = surfaces[0].renderer!, right = surfaces[1].renderer!
            let old = left.cameraPose
            left.orbit(dx: 14, dy: -4); right.zoom(delta: 8)
            try check(left.cameraPose == right.cameraPose && left.cameraPose != old,
                "The two renderers attached to the real comparison view share orbit and zoom")
            left.resetCamera()
        }
    }

    private func complete() throws {
        timer?.invalidate(); timer = nil
        let maximum = timings.max() ?? .infinity, maximumGap = callbackGaps.max() ?? .infinity
        let sorted = timings.sorted(), median = sorted[sorted.count / 2]
        try check(median < 0.15 && maximum < 1 && maximumGap < 1,
            "Native sizing stays below 150-ms median and one-second individual pass / event-loop gap guards")
        let report: [String: Any] = ["checks": checks, "E_recorded_frames": comparisonFrames,
            "H_recorded_frames": model.framesCount, "heartbeat_count": index,
            "median_layout_seconds": median, "maximum_layout_seconds": maximum,
            "maximum_callback_gap_seconds": maximumGap, "elapsed_seconds": ProcessInfo.processInfo.systemUptime - started,
            "fitting_sizes": fittingSizes, "surface_sizes": surfaceSizes,
            "pacing_source": "Production ActionComparisonExperience 30-Hz timer",
            "scope": "Unpresented native window and real AppKit event loop; no pixel approval or presented-window input latency claim"]
        let output = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
            .write(to: output.appendingPathComponent("layout.json"), options: .atomic)
        print("Actions: \(checks) checks; E \(comparisonFrames) frames; H \(model.framesCount) frames; median \(median)s; maximum \(maximum)s; callback gap \(maximumGap)s.")
        exit(0)
    }
    private func finish(_ error: Error) { print(error.localizedDescription); fflush(stdout); exit(1) }
}

MainActor.assumeIsolated {
    let app = NSApplication.shared
    app.setActivationPolicy(.prohibited)
    let delegate = ActionComparisonLayoutChecks()
    app.delegate = delegate
    withExtendedLifetime(delegate) { app.run() }
}
