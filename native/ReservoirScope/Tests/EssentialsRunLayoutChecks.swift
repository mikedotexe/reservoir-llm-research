// Real 300-step model.run() and AppKit event-loop responsiveness; no HTTP provider.
import AppKit
import SwiftUI
import EssentialsCore

@MainActor private final class EssentialsRunLayoutChecks: NSObject, NSApplicationDelegate {
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
    private var stopRequestedAt: Double?
    private var stopRequestedFrames: Int?
    private var fixture: RunRecord!
    private var stopCase = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        do {
            guard CommandLine.arguments.count == 4, ["complete", "stop"].contains(CommandLine.arguments[3]) else {
                throw SurfaceRenderError("Expected a regulation fixture, report path, and complete or stop mode.")
            }
            fixture = try RunRecord.read(from: URL(fileURLWithPath: CommandLine.arguments[1]))
            stopCase = CommandLine.arguments[3] == "stop"
            model.stage = .regulation; model.stepCount = 300
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
            model.run()
        } catch { finish(error) }
    }

    private func advance() {
        guard model.running else { complete(); return }
        let now = ProcessInfo.processInfo.systemUptime
        callbackGaps.append(now - lastCallback); lastCallback = now
        let start = ProcessInfo.processInfo.systemUptime
        host.needsLayout = true; host.layoutSubtreeIfNeeded()
        let fitting = host.fittingSize
        let elapsed = ProcessInfo.processInfo.systemUptime - start
        timings.append(elapsed)
        sizes.append([Double(fitting.width), Double(fitting.height)])
        print("run heartbeat \(index) frames=\(model.frames.count) layout=\(elapsed)"); fflush(stdout)
        index += 1
        if stopCase && stopRequestedAt == nil && model.frames.count >= 90 {
            stopRequestedFrames = model.frames.count
            stopRequestedAt = ProcessInfo.processInfo.systemUptime
            model.stop()
        }
    }

    private func complete() {
        timer?.invalidate(); timer = nil
        do {
            let finished = ProcessInfo.processInfo.systemUptime
            guard let record = model.record, !record.frames.isEmpty else {
                throw SurfaceRenderError("Real run did not retain its steps: " + model.status)
            }
            if stopCase {
                guard let request = stopRequestedAt, let count = stopRequestedFrames,
                      record.status == .stopped, record.frames.count >= count, record.frames.count < 300,
                      finished - request < 1 else {
                    throw SurfaceRenderError("Stop did not retain its committed frames within one second.")
                }
            } else {
                guard record.status == .completed, record.frames.count == 300 else {
                    throw SurfaceRenderError("Real run did not retain all 300 completed steps: " + model.status)
                }
            }
            callbackGaps.append(finished - lastCallback)
            let completionStart = ProcessInfo.processInfo.systemUptime
            host.needsLayout = true; host.layoutSubtreeIfNeeded(); _ = host.fittingSize
            let completionSeconds = ProcessInfo.processInfo.systemUptime - completionStart
            let maximum = timings.max() ?? 0, maximumGap = callbackGaps.max() ?? .infinity
            let sorted = timings.sorted(), median = sorted.isEmpty ? 0 : sorted[sorted.count / 2]
            let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
            guard try encoder.encode(record.frames) == encoder.encode(Array(fixture.frames.prefix(record.frames.count))),
                  try encoder.encode(model.frames) == encoder.encode(record.frames) else {
                throw SurfaceRenderError("Presented and retained steps must exactly match the canonical experiment.")
            }
            if !stopCase {
                guard try encoder.encode(record) == encoder.encode(fixture) else {
                    throw SurfaceRenderError("The complete run differs from the canonical experiment.")
                }
            }
            var report: [String: Any] = ["stage": 4, "mode": stopCase ? "stop" : "complete",
                "retained_frames": record.frames.count, "heartbeat_count": index, "median_layout_seconds": median,
                "maximum_layout_seconds": maximum, "maximum_callback_gap_seconds": maximumGap,
                "completion_layout_seconds": completionSeconds, "elapsed_seconds": finished - started,
                "median_layout_limit_seconds": 0.15, "single_pass_limit_seconds": 1.0,
                "canonical_frames_exact": true, "presented_frames_exact": true,
                "fitting_sizes": sizes, "scope": "Unpresented native window and real AppKit event loop; no presented-window input latency claim"]
            if let request = stopRequestedAt, let count = stopRequestedFrames {
                report["stop_requested_frames"] = count
                report["stop_to_retained_record_seconds"] = finished - request
            } else { report["canonical_record_exact"] = true }
            try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
                .write(to: URL(fileURLWithPath: CommandLine.arguments[2]), options: .atomic)
            print("Real regulation run (\(stopCase ? "stop" : "complete")): \(record.frames.count) exact steps; median \(median)s; maximum \(maximum)s; callback gap \(maximumGap)s; completion \(completionSeconds)s.")
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
    let delegate = EssentialsRunLayoutChecks()
    app.delegate = delegate
    withExtendedLifetime(delegate) { app.run() }
}
