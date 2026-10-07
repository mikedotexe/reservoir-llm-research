import Combine
import Foundation

/// One window's explicitly opened packet and reading position. Memory only:
/// hiding the view never reopens its file or writes a copy to disk.
@MainActor final class GeometryBookmarkViewModel: ObservableObject {
    enum Origin: Equatable { case openedFile, syntheticExample }

    @Published private(set) var packet: GeometryBookmarkPacket?
    @Published private(set) var origin: Origin?
    @Published private(set) var selected: Int
    @Published var frame = 0.0
    @Published var coordinatesExpanded = false
    @Published private(set) var error: String?
    @Published private(set) var filename = ""

    init(packet: GeometryBookmarkPacket? = nil, selected: Int = 0) {
        self.packet = packet
        self.selected = selected
        self.origin = packet == nil ? nil : .openedFile
    }

    func select(_ index: Int) {
        guard let packet, packet.records.indices.contains(index) else { return }
        selected = index
        frame = 0
    }

    func open(_ url: URL?) {
        guard let url else { return }
        replace(with: url, origin: .openedFile)
    }

    func loadSyntheticExample(from bundle: Bundle = .module) {
        guard let url = bundle.url(forResource: "synthetic-geometry-example", withExtension: "json")
            ?? bundle.url(forResource: "synthetic-geometry-example", withExtension: "json", subdirectory: "Resources") else {
            error = "The synthetic geometry example is missing from this package. You can still open an exported packet."
            return
        }
        replace(with: url, origin: .syntheticExample)
    }

    private func replace(with url: URL, origin: Origin) {
        do {
            let opened = try GeometryBookmarkPacket.load(url)
            packet = opened
            self.origin = origin
            selected = 0
            frame = 0
            coordinatesExpanded = false
            filename = url.lastPathComponent
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
    }
}
