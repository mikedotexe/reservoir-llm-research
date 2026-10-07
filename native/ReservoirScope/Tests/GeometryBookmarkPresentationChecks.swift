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
                let fixture = URL(fileURLWithPath: CommandLine.arguments[1])
                let output = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
                try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
                let bundle = try exampleBundle(named: "valid", data: Data(contentsOf: fixture), output: output)
                try checkSyntheticOrigin(bundle: bundle, output: output)
                window = NSWindow(contentRect: NSRect(x: 20, y: 20, width: 1100, height: 820), styleMask: [.titled], backing: .buffered, defer: false)
                window.isReleasedWhenClosed = false
                let example = GeometryBookmarkViewModel()
                example.loadSyntheticExample(from: bundle)
                for width in [1100.0, 1380.0] {
                    try await render(GeometryBookmarkViewModel(), width: width, name: "geometry-\(Int(width))-empty", output: output)
                    for selection in [0, 1, 2, 3, 4] {
                        example.select(selection)
                        try await render(example, width: width, name: "geometry-\(Int(width))-\(selection)", output: output)
                    }
                }
                print("Rendered empty geometry and five synthetic records at two supported desktop widths; visual inspection and interaction testing remain separate.")
                try await checkViewLifetime(output: output, bundle: bundle)
                NSApp.terminate(nil)
            } catch { fputs("FAIL: \(error)\n", stderr); exit(1) }
        }
    }

    private func render(_ model: GeometryBookmarkViewModel, width: Double, name: String, output: URL) async throws {
        let view = NSHostingView(rootView: GeometryBookmarkExperience(model: model)
            .frame(width: width, height: 820).background(Color(red: 0.035, green: 0.045, blue: 0.065)).preferredColorScheme(.dark))
        window.contentView = view; window.setContentSize(NSSize(width: width, height: 820)); window.orderFrontRegardless()
        try await Task.sleep(for: .milliseconds(250))
        view.layoutSubtreeIfNeeded(); view.displayIfNeeded()
        guard let bitmap = view.bitmapImageRepForCachingDisplay(in: view.bounds) else { throw GeometryBookmarkError.invalid("No view bitmap") }
        view.cacheDisplay(in: view.bounds, to: bitmap)
        guard let png = bitmap.representation(using: .png, properties: [:]) else { throw GeometryBookmarkError.invalid("No PNG") }
        try png.write(to: output.appendingPathComponent(name + ".png"))
    }

    private func exampleBundle(named name: String, data: Data?, output: URL) throws -> Bundle {
        let url = output.appendingPathComponent("\(name)-example.bundle", isDirectory: true)
        let resources = url.appendingPathComponent("Contents/Resources", isDirectory: true)
        try FileManager.default.createDirectory(at: resources, withIntermediateDirectories: true)
        let info = ["CFBundleIdentifier": "research.geometry.fixture.\(name)", "CFBundlePackageType": "BNDL"]
        try PropertyListSerialization.data(fromPropertyList: info, format: .xml, options: 0)
            .write(to: url.appendingPathComponent("Contents/Info.plist"))
        if let data { try data.write(to: resources.appendingPathComponent("synthetic-geometry-example.json")) }
        guard let bundle = Bundle(url: url) else { throw GeometryBookmarkError.invalid("Could not create test bundle") }
        return bundle
    }

    private func checkSyntheticOrigin(bundle: Bundle, output: URL) throws {
        var checks = 0
        func check(_ condition: Bool, _ text: String) throws {
            guard condition else { throw GeometryBookmarkError.invalid("Synthetic example check failed: " + text) }
            checks += 1
        }
        let model = GeometryBookmarkViewModel()
        try check(model.packet == nil && model.origin == nil, "A new window has no automatically loaded packet or origin")
        model.loadSyntheticExample(from: bundle)
        try check(model.packet != nil && model.origin == .syntheticExample && model.error == nil,
                  "A verified bundled resource establishes synthetic origin")
        try check(model.filename == "synthetic-geometry-example.json" && model.packet?.records.count == 5,
                  "The stable bundled name loads all five records")
        let digest = model.packet!.digest
        model.select(2); model.frame = 2; model.coordinatesExpanded = true
        model.open(nil)
        try check(model.origin == .syntheticExample && model.packet?.digest == digest && model.selected == 2 && model.frame == 2,
                  "Cancel keeps the example and its reading position")
        let invalid = output.appendingPathComponent("origin-rejected.json")
        try Data("{}".utf8).write(to: invalid)
        model.open(invalid)
        try check(model.error != nil && model.origin == .syntheticExample && model.packet?.digest == digest,
                  "An invalid opened file cannot relabel or replace the example")
        try check(model.selected == 2 && model.frame == 2 && model.coordinatesExpanded,
                  "An invalid opened file keeps all example reading state")
        let missing = try exampleBundle(named: "missing", data: nil, output: output)
        model.loadSyntheticExample(from: missing)
        try check(model.error?.contains("missing from this package") == true && model.packet?.digest == digest && model.origin == .syntheticExample,
                  "A missing resource leaves the existing example intact")
        let damaged = try exampleBundle(named: "damaged", data: Data("{}".utf8), output: output)
        model.loadSyntheticExample(from: damaged)
        try check(model.error != nil && model.packet?.digest == digest && model.origin == .syntheticExample,
                  "An invalid bundled resource cannot replace the example")
        try check(model.selected == 2 && model.frame == 2 && model.coordinatesExpanded,
                  "Failed example loads preserve reading state")
        let fixture = URL(fileURLWithPath: CommandLine.arguments[1])
        model.open(fixture)
        try check(model.error == nil && model.origin == .openedFile && model.filename == fixture.lastPathComponent,
                  "A successful explicit file open replaces the source label, even with identical bytes")
        model.select(4)
        model.loadSyntheticExample(from: damaged)
        try check(model.error != nil && model.origin == .openedFile && model.packet?.digest == digest && model.selected == 4,
                  "A failed example load cannot relabel an opened file")
        model.loadSyntheticExample(from: bundle)
        try check(model.error == nil && model.origin == .syntheticExample && model.selected == 0 && model.frame == 0 && !model.coordinatesExpanded,
                  "A successful example load resets reading position and establishes its origin")
        let anotherWindow = GeometryBookmarkViewModel()
        try check(anotherWindow.packet == nil && anotherWindow.origin == nil,
                  "A second window does not restore the first window's packet")
        try JSONSerialization.data(withJSONObject: ["outcome": "passed", "checks": checks,
            "scope": "Bundled synthetic lookup and explicit origin changes; no automatic loading, persistence or producer claim."], options: [.prettyPrinted, .sortedKeys])
            .write(to: output.appendingPathComponent("synthetic-origin-checks.json"))
        print("Geometry synthetic origin: \(checks) checks passed; successful validated loads alone change source origin.")
    }

    private func checkViewLifetime(output: URL, bundle: Bundle) async throws {
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
        try check(model.packet != nil && model.error == nil && model.origin == .openedFile, "Explicit fixture import succeeds with file origin")
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
        try check(model.packet?.digest == digest && model.origin == .openedFile, "Packet bytes and origin survive reconstruction with source absent")
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
        model.loadSyntheticExample(from: bundle)
        model.select(3)
        workspace.visible = false
        try await Task.sleep(for: .milliseconds(150))
        workspace.visible = true
        try await Task.sleep(for: .milliseconds(150))
        try check(model.origin == .syntheticExample && model.packet?.digest == digest && model.selected == 3,
                  "Reconstructed view preserves the example's explicit synthetic origin and selection")
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
