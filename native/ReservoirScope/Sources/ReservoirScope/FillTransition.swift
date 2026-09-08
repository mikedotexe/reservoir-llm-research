import Foundation

/// Presentation-only fill easing. Observations, source clocks, controller values,
/// and charts remain unchanged. The caller supplies a monotonic animation clock.
struct FillTransition {
    static let duration: TimeInterval = 0.8

    private var from: Double?
    private var target: Double?
    private var startedAt: TimeInterval = 0
    private var context: String?
    private var latestSourceTime: Double?

    init() {}

    func value(at uptime: TimeInterval) -> Double? {
        guard let target, let from else { return nil }
        guard uptime.isFinite else { return target }
        let progress = min(1, max(0, (uptime - startedAt) / Self.duration))
        if progress == 0 { return from }
        if progress == 1 { return target }
        // Quintic smootherstep has zero velocity and acceleration at each end.
        let curve = min(1, max(0, progress * progress * progress
            * (progress * (progress * 6 - 15) + 10)))
        return min(max(from, target), max(min(from, target), from + (target - from) * curve))
    }

    func isAnimating(at uptime: TimeInterval) -> Bool {
        guard let from, let target, uptime.isFinite else { return false }
        return from != target && uptime < startedAt + Self.duration && value(at: uptime) != target
    }

    mutating func receive(_ target: Double, at uptime: TimeInterval, animated: Bool,
                          context: String, sourceTime: Double?) {
        guard target.isFinite, (0...100).contains(target), uptime.isFinite else { return }
        let sourceTime = sourceTime.flatMap { $0.isFinite ? $0 : nil }
        let contextChanged = self.context != context
        let sourceRestarted = !contextChanged && sourceTime.map { time in
            latestSourceTime.map { time < $0 } ?? false
        } == true
        let mustSnap = self.target == nil || contextChanged || sourceRestarted || !animated
        let displayed = value(at: uptime) ?? target

        self.context = context
        if contextChanged || sourceRestarted {
            latestSourceTime = sourceTime
        } else if let sourceTime {
            latestSourceTime = max(latestSourceTime ?? sourceTime, sourceTime)
        }

        if mustSnap {
            from = target
            self.target = target
            startedAt = uptime
        } else if self.target != target {
            from = displayed
            self.target = target
            startedAt = uptime
        }
    }
}
