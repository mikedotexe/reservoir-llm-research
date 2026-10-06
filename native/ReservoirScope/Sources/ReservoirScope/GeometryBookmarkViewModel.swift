import Combine
import Foundation

/// One window's explicitly opened packet and reading position. Memory only:
/// hiding the view never reopens its file or writes a copy to disk.
@MainActor final class GeometryBookmarkViewModel: ObservableObject {
    @Published private(set) var packet: GeometryBookmarkPacket?
    @Published private(set) var selected: Int
    @Published var frame = 0.0
    @Published var coordinatesExpanded = false
    @Published private(set) var error: String?
    @Published private(set) var filename = ""

    init(packet: GeometryBookmarkPacket? = nil, selected: Int = 0) {
        self.packet = packet
        self.selected = selected
    }

    func select(_ index: Int) {
        guard let packet, packet.records.indices.contains(index) else { return }
        selected = index
        frame = 0
    }

    func open(_ url: URL?) {
        guard let url else { return }
        do {
            let opened = try GeometryBookmarkPacket.load(url)
            packet = opened
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
