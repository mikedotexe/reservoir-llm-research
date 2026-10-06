import AppKit
import SwiftUI

@MainActor private final class GeometryHostSwitch: ObservableObject {
    @Published var visible = true
    var appearances = 0
    var disappearances = 0
}

private struct GeometryLifecycleHost: View {
    @ObservedObject var workspace: GeometryHostSwitch
    @ObservedObject var model: GeometryBookmarkViewModel
    var body: some View {
        if workspace.visible {
            GeometryBookmarkExperience(model: model)
                .onAppear { workspace.appearances += 1 }
                .onDisappear { workspace.disappearances += 1 }
        } else {
            Text("Another workspace").frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }
}

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
                try await checkViewLifetime(output: output)
                NSApp.terminate(nil)
            } catch { fputs("FAIL: \(error)\n", stderr); exit(1) }
        }
    }

    private func checkViewLifetime(output: URL) async throws {
        var checks = 0
        func check(_ condition: Bool, _ text: String) throws {
            guard condition else { throw GeometryBookmarkError.invalid("Lifecycle check failed: " + text) }
            checks += 1
        }
        let fixture = URL(fileURLWithPath: CommandLine.arguments[1])
        let temporary = output.appendingPathComponent("lifecycle-opened-copy.json")
        try Data(contentsOf: fixture).write(to: temporary)
        let model = GeometryBookmarkViewModel()
        model.open(temporary)
        try check(model.packet != nil && model.error == nil, "Explicit fixture import succeeds")
        let digest = model.packet!.digest
        model.select(2); model.frame = 2; model.coordinatesExpanded = true
        let workspace = GeometryHostSwitch()
        let view = NSHostingView(rootView: GeometryLifecycleHost(workspace: workspace, model: model)
            .frame(width: 1100, height: 820).background(Color(red: 0.035, green: 0.045, blue: 0.065)).preferredColorScheme(.dark))
        window.contentView = view; window.setContentSize(NSSize(width: 1100, height: 820))
        try await Task.sleep(for: .milliseconds(150))
        try check(workspace.appearances == 1, "Imported view is initially mounted")
        // The source disappears after import. Returning must use retained bytes;
        // a hidden file watcher or automatic reopen cannot provide this result.
        try FileManager.default.removeItem(at: temporary)
        workspace.visible = false
        try await Task.sleep(for: .milliseconds(150))
        try check(workspace.disappearances == 1, "Switch removes the geometry view")
        workspace.visible = true
        try await Task.sleep(for: .milliseconds(150))
        try check(workspace.appearances == 2, "Return reconstructs the geometry view")
        try check(model.packet?.digest == digest, "Packet bytes survive reconstruction with source absent")
        try check(model.selected == 2 && model.frame == 2, "Selected record and frame survive")
        try check(model.coordinatesExpanded, "Coordinate disclosure survives")
        try check(model.filename == temporary.lastPathComponent && model.error == nil, "Filename survives without reread error")
        model.open(nil)
        try check(model.packet?.digest == digest && model.selected == 2 && model.frame == 2, "Cancelled selection preserves reading state")
        let invalid = output.appendingPathComponent("lifecycle-rejected.json")
        try Data("{}".utf8).write(to: invalid)
        model.open(invalid)
        try check(model.error != nil && model.packet?.digest == digest, "Rejected import preserves retained packet")
        try check(model.selected == 2 && model.frame == 2 && model.coordinatesExpanded, "Rejected import preserves reading position")
        workspace.visible = false
        try await Task.sleep(for: .milliseconds(150))
        workspace.visible = true
        try await Task.sleep(for: .milliseconds(150))
        try check(model.packet?.digest == digest && model.error != nil && model.selected == 2 && model.frame == 2,
                  "Return after rejection preserves error and retained context")
        model.open(fixture)
        try check(model.error == nil && model.selected == 0 && model.frame == 0 && !model.coordinatesExpanded,
                  "Successful replacement resets reading position and clears error")
        let receipt: [String: Any] = ["checks": checks, "outcome": "passed", "view_mounts": workspace.appearances,
            "view_unmounts": workspace.disappearances, "source_removed_before_return": true,
            "scope": "Synthetic mounted SwiftUI host removes and recreates the production geometry experience. Actual full-app navigation and newcomer acceptance remain separate."]
        try JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys])
            .write(to: output.appendingPathComponent("lifecycle-checks.json"))
        print("Geometry view lifecycle: \(checks) checks passed; memory-only packet and reading position survive view reconstruction.")
    }
}
@main struct GeometryPresentationRunner {
    static func main() { let app = NSApplication.shared; let delegate = GeometryPresentation(); app.delegate = delegate; app.setActivationPolicy(.accessory); app.run(); withExtendedLifetime(delegate) {} }
}
