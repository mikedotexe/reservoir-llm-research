import Foundation

/// Playback position follows elapsed monotonic time, independent of redraw or
/// timer frequency. Call start again after a pause, scrub, or mode change.
struct ReplayClock {
    private(set) var position = 0.0
    private var lastUptime = 0.0

    mutating func start(at position: Double, uptime: Double) {
        self.position = position
        lastUptime = uptime
    }

    @discardableResult
    mutating func advance(uptime: Double, rate: Double) -> Double {
        let elapsed = max(0, uptime - lastUptime)
        lastUptime = max(lastUptime, uptime)
        position += elapsed * rate
        return position
    }
}
