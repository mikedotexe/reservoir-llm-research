import AppKit
import SwiftUI
import EssentialsCore

@MainActor final class CasePresentation: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    let output = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
    func applicationDidFinishLaunching(_ notification: Notification) {
        Task { @MainActor in
            do {
                try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
                let cases = try ResearchCaseCatalog.read(from: URL(fileURLWithPath: CommandLine.arguments[1])).cases
                window = NSWindow(contentRect: NSRect(x: 20, y: 20, width: 760, height: 580), styleMask: [.titled], backing: .buffered, defer: false)
                window.isReleasedWhenClosed = false; window.appearance = NSAppearance(named: .darkAqua)
                for item in cases {
                    let view = NSHostingView(rootView: NavigationStack { ResearchCaseView(researchCase: item) }.frame(width: 760, height: 580).background(Color(red: 0.10, green: 0.10, blue: 0.11)).preferredColorScheme(.dark))
                    window.contentView = view; window.setContentSize(NSSize(width: 760, height: 580)); window.orderFrontRegardless()
                    try await Task.sleep(for: .milliseconds(350))
                    try capture(view, item.id + "-top")
                    @MainActor func scrolls(_ v: NSView) -> [NSScrollView] {
                        if let scroll = v as? NSScrollView { return [scroll] }
                        var result: [NSScrollView] = []
                        for child in v.subviews { result += scrolls(child) }
                        return result
                    }
                    guard let scroll = scrolls(view).first, let document = scroll.documentView else { throw NSError(domain: "No case scroll view", code: 1) }
                    for (name, fraction) in [("middle", 0.50), ("bottom", 1.0)] {
                        let y = max(0, document.bounds.height - scroll.contentView.bounds.height) * fraction
                        scroll.contentView.scroll(to: NSPoint(x: 0, y: y)); scroll.reflectScrolledClipView(scroll.contentView)
                        try await Task.sleep(for: .milliseconds(150)); try capture(view, item.id + "-" + name)
                    }
                }
                for found in [true, false] {
                    let state = LocalModelReadiness(probe: { endpoint, model in
                        if !found { throw URLError(.cannotConnectToHost) }
                        return LocalModelAvailabilityReceipt(endpoint: endpoint, requestedModel: model, matchedModel: model, digest: String(repeating: "f", count: 64), checkedAt: Date(timeIntervalSince1970: 1789677000))
                    })
                    let view = NSHostingView(rootView: LocalModelReadinessView(model: state, endpoint: "http://127.0.0.1:11434", modelName: "phi3:mini").padding(24).frame(width: 760, height: 580, alignment: .topLeading).background(Color(red: 0.10, green: 0.10, blue: 0.11)).preferredColorScheme(.dark))
                    window.contentView = view; window.setContentSize(NSSize(width: 760, height: 580))
                    state.check(endpoint: "http://127.0.0.1:11434", model: "phi3:mini")
                    try await Task.sleep(for: .milliseconds(300))
                    try capture(view, found ? "readiness-found" : "readiness-unavailable")
                }
                print("PASS: two real cases at 760x580, three scroll positions each; two mocked readiness states. No network or model calls. Visual review remains separate.")
                NSApp.terminate(nil)
            } catch { fputs("FAIL: \(error)\n", stderr); exit(1) }
        }
    }
    func capture(_ view: NSView, _ name: String) throws {
        view.layoutSubtreeIfNeeded(); view.displayIfNeeded()
        guard let bitmap = view.bitmapImageRepForCachingDisplay(in: view.bounds) else { throw NSError(domain: "Bitmap unavailable", code: 2) }
        view.cacheDisplay(in: view.bounds, to: bitmap)
        guard let data = bitmap.representation(using: .png, properties: [:]) else { throw NSError(domain: "PNG unavailable", code: 3) }
        try data.write(to: output.appendingPathComponent(name + ".png"))
    }
}
@main struct Run {
    static func main() { let app = NSApplication.shared; let delegate = CasePresentation(); app.delegate = delegate; app.setActivationPolicy(.regular); app.run(); withExtendedLifetime(delegate) {} }
}
