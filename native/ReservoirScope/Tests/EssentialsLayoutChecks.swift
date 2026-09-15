// Actual AppKit event-loop and SwiftUI sizing with synthetic stage-four data.
import AppKit
import SwiftUI
import EssentialsCore

@MainActor private final class EssentialsLayoutChecks: NSObject, NSApplicationDelegate {
    private var fixture: RunRecord!
    private let model = EssentialsViewModel()
    private var host: NSView!
    private var window: NSWindow!
    private var timer: Timer?
    private var index = 0
    private var timings: [Double] = []
    private var callbackGaps: [Double] = []
    private var lastCallback = 0.0
    private var started = 0.0
    private var sizes: [[Double]] = []

    func applicationDidFinishLaunching(_ notification: Notification) {
        do {
            guard CommandLine.arguments.count == 3 else { throw SurfaceRenderError("Expected a regulation fixture and report path.") }
            fixture = try RunRecord.read(from: URL(fileURLWithPath: CommandLine.arguments[1]))
            guard fixture.specification.stage == .regulation, fixture.frames.count >= 40 else {
                throw SurfaceRenderError("Layout check needs forty regulation frames.")
            }
            model.stage = .regulation; model.running = true
            let root = VStack(spacing: 0) {
                Text("ESSENTIALS LAYOUT CHECK").frame(height: 40)
                EssentialsExperience(model: model)
            }.frame(minWidth: 1100, minHeight: 820).preferredColorScheme(.dark)
            host = NSHostingView(rootView: root)
            window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1380, height: 940),
                styleMask: [.titled, .resizable], backing: .buffered, defer: false)
            window.isReleasedWhenClosed = false; window.contentView = host
            // Attach the actual native hierarchy without presenting a window.
            started = ProcessInfo.processInfo.systemUptime; lastCallback = started
            timer = Timer.scheduledTimer(withTimeInterval: 0.02, repeats: true) { [weak self] _ in MainActor.assumeIsolated { self?.advance() } }
        } catch { finish(error) }
    }

    private func advance() {
        guard index < 40 else { complete(); return }
        let now = ProcessInfo.processInfo.systemUptime
        if index >= 2 { callbackGaps.append(now - lastCallback) }
        lastCallback = now
        let width = index < 20 ? 1380.0 : 1100.0, height = index < 20 ? 940.0 : 820.0
        if index == 0 || index == 20 { window.setContentSize(NSSize(width: width, height: height)) }
        model.frames = Array(fixture.frames.prefix(index + 1)); model.row = index
        model.status = "Running regulation · step \(index + 1)"
        let start = ProcessInfo.processInfo.systemUptime
        host.needsLayout = true; host.layoutSubtreeIfNeeded()
        let fitting = host.fittingSize
        let elapsed = ProcessInfo.processInfo.systemUptime - start
        if index >= 2 { timings.append(elapsed) }
        sizes.append([Double(fitting.width), Double(fitting.height)])
        print("layout \(index) \(elapsed)"); fflush(stdout)
        index += 1
    }

    private func complete() {
        timer?.invalidate(); timer = nil
        do {
            model.running = false; model.record = fixture; model.frames = fixture.frames; model.row = fixture.frames.count - 1
            let completionStart = ProcessInfo.processInfo.systemUptime
            host.needsLayout = true; host.layoutSubtreeIfNeeded(); _ = host.fittingSize
            let completionSeconds = ProcessInfo.processInfo.systemUptime - completionStart
            let maximum = timings.max() ?? .infinity, maximumGap = callbackGaps.max() ?? .infinity
            let sorted = timings.sorted(), median = sorted[sorted.count / 2]
            let report: [String: Any] = ["stage": 4, "updated_frames": 40, "median_layout_seconds": median,
                "maximum_layout_seconds": maximum, "maximum_callback_gap_seconds": maximumGap,
                "completion_layout_seconds": completionSeconds, "elapsed_seconds": ProcessInfo.processInfo.systemUptime - started,
                "median_layout_limit_seconds": 0.15, "single_pass_limit_seconds": 1.0,
                "fitting_sizes": sizes, "scope": "Unpresented native window and real AppKit event loop; no presented-window input latency claim"]
            try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
                .write(to: URL(fileURLWithPath: CommandLine.arguments[2]), options: .atomic)
            print("Forty regulation updates: median \(median)s; maximum \(maximum)s; callback gap \(maximumGap)s; completion \(completionSeconds)s.")
            guard median < 0.15, maximum < 1, maximumGap < 1, completionSeconds < 1 else {
                throw SurfaceRenderError("Native layout exceeded the 150-ms median or one-second individual-pass guard.")
            }
            exit(0)
        } catch { finish(error) }
    }
    private func finish(_ error: Error) { print(error.localizedDescription); fflush(stdout); exit(1) }
}

MainActor.assumeIsolated {
    let app = NSApplication.shared
    app.setActivationPolicy(.prohibited)
    let delegate = EssentialsLayoutChecks()
    app.delegate = delegate
    withExtendedLifetime(delegate) { app.run() }
}
