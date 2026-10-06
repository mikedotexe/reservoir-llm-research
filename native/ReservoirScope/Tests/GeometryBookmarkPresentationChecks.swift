import AppKit
import SwiftUI

@MainActor final class GeometryPresentation: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    func applicationDidFinishLaunching(_ notification: Notification) {
        Task { @MainActor in
            do {
                let packet = try GeometryBookmarkPacket.load(URL(fileURLWithPath: CommandLine.arguments[1]))
                let output = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
                try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
                window = NSWindow(contentRect: NSRect(x: 20, y: 20, width: 1100, height: 820), styleMask: [.titled], backing: .buffered, defer: false)
                window.isReleasedWhenClosed = false
                for width in [1100.0, 1380.0] {
                    for selection in [0, 1, 2, 3, 4] {
                        let view = NSHostingView(rootView: GeometryBookmarkExperience(packet: packet, selected: selection)
                            .frame(width: width, height: 820).background(Color(red: 0.035, green: 0.045, blue: 0.065)).preferredColorScheme(.dark))
                        window.contentView = view; window.setContentSize(NSSize(width: width, height: 820)); window.orderFrontRegardless()
                        try await Task.sleep(for: .milliseconds(250))
                        view.layoutSubtreeIfNeeded(); view.displayIfNeeded()
                        guard let bitmap = view.bitmapImageRepForCachingDisplay(in: view.bounds) else { throw GeometryBookmarkError.invalid("No view bitmap") }
                        view.cacheDisplay(in: view.bounds, to: bitmap)
                        guard let png = bitmap.representation(using: .png, properties: [:]) else { throw GeometryBookmarkError.invalid("No PNG") }
                        try png.write(to: output.appendingPathComponent("geometry-\(Int(width))-\(selection).png"))
                    }
                }
                print("Rendered ten geometry views at two supported desktop widths; visual inspection and interaction testing remain separate.")
                NSApp.terminate(nil)
            } catch { fputs("FAIL: \(error)\n", stderr); exit(1) }
        }
    }
}
@main struct GeometryPresentationRunner {
    static func main() { let app = NSApplication.shared; let delegate = GeometryPresentation(); app.delegate = delegate; app.setActivationPolicy(.accessory); app.run(); withExtendedLifetime(delegate) {} }
}
