// Actual native exploration view with synthetic inputs and a real AppKit event loop.
// File persistence is disabled; no live being or language provider is contacted.
import AppKit
import SwiftUI
import EssentialsCore

@MainActor private final class ExplorationLayoutChecks: NSObject, NSApplicationDelegate {
    private let model = ExplorationViewModel(recordWriter: { _, _ in },
        workspaceURL: URL(fileURLWithPath: "/controlled/research", isDirectory: true))
    private var host: NSView!
    private var window: NSWindow!
    private var timer: Timer?
    private var index = 0
    private var phase = 0
    private var phaseStarted = 0.0
    private var heldCount = 0
    private var checks = 0
    private var timings: [Double] = []
    private var callbackGaps: [Double] = []
    private var lastCallback = 0.0
    private var started = 0.0
    private var sizes: [[Double]] = []
    private var finalFrameCount = 0

    func applicationDidFinishLaunching(_ notification: Notification) {
        do {
            guard CommandLine.arguments.count == 2 else {
                throw SurfaceRenderError("Expected a report directory.")
            }
            let root = VStack(spacing: 0) {
                Text("EXPLORATION NATIVE CHECK").frame(height: 40)
                ExplorationExperience(model: model)
            }.frame(minWidth: 1100, minHeight: 820).preferredColorScheme(.dark)
            host = NSHostingView(rootView: root)
            window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1380, height: 940),
                styleMask: [.titled, .resizable], backing: .buffered, defer: false)
            window.isReleasedWhenClosed = false; window.contentView = host
            started = ProcessInfo.processInfo.systemUptime; lastCallback = started
            timer = Timer.scheduledTimer(withTimeInterval: 0.02, repeats: true) { [weak self] _ in
                MainActor.assumeIsolated { self?.advance() }
            }
        } catch { finish(error) }
    }

    private func check(_ condition: Bool, _ description: String) throws {
        guard condition else { throw SurfaceRenderError("FAIL: " + description) }
        checks += 1; print("PASS \(checks): \(description)"); fflush(stdout)
    }

    private func advance() {
        do {
            let now = ProcessInfo.processInfo.systemUptime
            if index >= 2 { callbackGaps.append(now - lastCallback) }
            lastCallback = now
            // The production view's own 30-Hz publisher advances the model.
            // This independent native timer only observes and operates controls.
            switch phase {
            case 0:
                if index == 1 { model.sendPulse() }
                else {
                    if index == 2 {
                        model.controls.recurrenceEnabled = true
                        model.controls.repeatInput = true
                        model.controls.sensoryEnabled = true
                    }
                    model.step()
                }
                if index == 5 {
                    try check(model.frames.count == 6 && !model.running, "Single steps remain paused and record six actual observations")
                    try check(model.frames[0].state.allSatisfy { $0 == 0 } && model.frames[1].pulse
                        && model.frames[1].state.contains { $0 != 0 },
                        "Default state stays quiet until a paused Send pulse records a visible response")
                    try check(model.frame?.spectral != nil,
                        "Compact layout includes the optional separate sensory-field display")
                    window.setContentSize(NSSize(width: 1100, height: 820))
                }
                if index == 10 {
                    try check(model.state.count == 32, "Exploration displays exactly 32 state coordinates")
                    try check(model.frames.allSatisfy { $0.state.count == 32 && $0.input.count == 66 },
                        "Recorded frames retain the actual 32-state / 66-input dimensions")
                    model.changeSpeed(20); model.startPause()
                    phase = 1; phaseStarted = now
                }
            case 1:
                if now - phaseStarted >= 1.5 {
                    try check(model.running && model.frames.count > 20, "The native event loop advances a paced exploration")
                    model.startPause(); heldCount = model.frames.count
                    phase = 2; phaseStarted = now
                }
            case 2:
                if now - phaseStarted >= 0.25 {
                    try check(!model.running && model.frames.count == heldCount, "Pause halts future observations while native timers continue")
                    model.scrub(1)
                    try check(model.row == 1 && model.state == model.frames[1].state,
                        "Scrubbing displays the exact historical state")
                    let historical = model.frame!.controls
                    model.controls.noiseAmplitude = 0.07
                    model.controls.recurrenceEnabled.toggle()
                    try check(model.frame!.controls == historical && model.controls != historical,
                        "Upcoming settings can change without rewriting the selected observation's controls")
                    model.startPause()
                    phase = 3; phaseStarted = now
                }
            case 3:
                if now - phaseStarted >= 0.4 {
                    try check(model.frame?.controls == model.controls,
                        "Resuming applies the upcoming controls at a new recorded boundary")
                    model.leave(); heldCount = model.frames.count
                    phase = 4; phaseStarted = now
                }
            default:
                if now - phaseStarted >= 0.25 {
                    try check(!model.running && !model.replaying && model.frames.count == heldCount,
                        "Leaving the exploration halts run and replay progression")
                    finalFrameCount = model.frames.count
                    try inspectRenderer()
                    try complete()
                    return
                }
            }
            let start = ProcessInfo.processInfo.systemUptime
            host.needsLayout = true; host.layoutSubtreeIfNeeded()
            let fitting = host.fittingSize
            let elapsed = ProcessInfo.processInfo.systemUptime - start
            if index >= 2 { timings.append(elapsed) }
            sizes.append([Double(fitting.width), Double(fitting.height)])
            index += 1
        } catch { finish(error) }
    }

    private func inspectRenderer() throws {
        func find(_ view: NSView) -> StateSurfaceMetalView? {
            if let surface = view as? StateSurfaceMetalView { return surface }
            for child in view.subviews { if let surface = find(child) { return surface } }
            return nil
        }
        guard let surface = find(host), let renderer = surface.renderer else {
            throw SurfaceRenderError("The actual native state-surface renderer was not attached.")
        }
        try check(renderer.nodeCount == 32 && renderer.mesh?.sitePositions.count == 32,
            "The attached renderer uses exactly 32 nodes and 32 exact markers")
        try check(surface.accessibilityLabel()?.contains("32 coordinates") == true,
            "The rendered surface exposes its actual coordinate count to accessibility")
        try check(renderer.pick(point: CGPoint(x: 200, y: 200), size: CGSize(width: 400, height: 400))
            .map { (0..<32).contains($0) } == true, "Surface picking resolves an actual exploration node")
    }

    private func complete() throws {
        timer?.invalidate(); timer = nil
        let maximum = timings.max() ?? .infinity, maximumGap = callbackGaps.max() ?? .infinity
        let sorted = timings.sorted(), median = sorted[sorted.count / 2]
        try check(median < 0.15 && maximum < 1 && maximumGap < 1,
            "Native sizing stays below 150-ms median and one-second individual pass / event-loop gap guards")
        let output = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        let report: [String: Any] = ["checks": checks, "recorded_frames": finalFrameCount,
            "heartbeat_count": index, "median_layout_seconds": median, "maximum_layout_seconds": maximum,
            "maximum_callback_gap_seconds": maximumGap, "elapsed_seconds": ProcessInfo.processInfo.systemUptime - started,
            "fitting_sizes": sizes, "pacing_source": "Production ExplorationExperience 30-Hz timer",
            "scope": "Unpresented native window and real AppKit event loop; no presented-window input latency claim"]
        try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
            .write(to: output.appendingPathComponent("layout.json"), options: .atomic)
        print("Exploration: \(checks) checks; \(finalFrameCount) frames; median \(median)s; maximum \(maximum)s; callback gap \(maximumGap)s.")
        exit(0)
    }
    private func finish(_ error: Error) { print(error.localizedDescription); fflush(stdout); exit(1) }
}

MainActor.assumeIsolated {
    let app = NSApplication.shared
    app.setActivationPolicy(.prohibited)
    let delegate = ExplorationLayoutChecks()
    app.delegate = delegate
    withExtendedLifetime(delegate) { app.run() }
}
