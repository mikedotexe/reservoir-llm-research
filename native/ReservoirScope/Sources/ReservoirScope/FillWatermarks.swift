import Foundation

/// A measured fill, never an interpolated display height. `ordinal` is a stable
/// source observation identity, increasing within a source/session context.
struct FillWatermarkObservation: Equatable, Sendable {
    let fillPct: Double
    let sourceTime: Double
    let ordinal: UInt64

    var isValid: Bool {
        fillPct.isFinite && (0...100).contains(fillPct) && sourceTime.isFinite
    }
}

struct FillWatermarkSnapshot: Equatable, Sendable {
    let high: FillWatermarkObservation?
    let low: FillWatermarkObservation?
    /// Number of valid, ordered observations in this scope, including ties.
    let count: Int

    static let empty = FillWatermarkSnapshot(high: nil, low: nil, count: 0)
}

struct FillWatermarkUpdate: Equatable, Sendable {
    let snapshot: FillWatermarkSnapshot
    let accepted: Bool
    let contextReset: Bool
    let newHigh: Bool
    let newLow: Bool
    let initialized: Bool
}

/// Observed-session extrema for a live source. A repeated poll must keep the
/// original ordinal; it cannot manufacture a new observation or a new record.
/// A source restart must supply a new context. Out-of-order samples in the same
/// context are rejected instead of implicitly erasing its established history.
struct FillWatermarkTracker: Sendable {
    private(set) var snapshot: FillWatermarkSnapshot = .empty
    private(set) var context: String?
    private var latestObservation: FillWatermarkObservation?

    mutating func reset(context: String? = nil) {
        self.context = context
        snapshot = .empty
        latestObservation = nil
    }

    @discardableResult
    mutating func observe(_ observation: FillWatermarkObservation,
                          context: String) -> FillWatermarkUpdate {
        let contextReset = self.context != context
        if contextReset { reset(context: context) }

        // Reset the old scope even if a new source's first sample is invalid:
        // a previous session's marks must never be labeled as the new session.
        guard observation.isValid else {
            return update(accepted: false, contextReset: contextReset)
        }
        if let latestObservation {
            guard observation.ordinal > latestObservation.ordinal,
                  observation.sourceTime >= latestObservation.sourceTime else {
                return update(accepted: false, contextReset: contextReset)
            }
        }

        let initialized = snapshot.count == 0
        let newHigh = snapshot.high.map { observation.fillPct > $0.fillPct } ?? true
        let newLow = snapshot.low.map { observation.fillPct < $0.fillPct } ?? true
        snapshot = FillWatermarkSnapshot(
            high: newHigh ? observation : snapshot.high,
            low: newLow ? observation : snapshot.low,
            count: snapshot.count + 1
        )
        latestObservation = observation
        return FillWatermarkUpdate(snapshot: snapshot, accepted: true,
            contextReset: contextReset, newHigh: newHigh, newLow: newLow,
            initialized: initialized)
    }

    private func update(accepted: Bool, contextReset: Bool) -> FillWatermarkUpdate {
        FillWatermarkUpdate(snapshot: snapshot, accepted: accepted,
            contextReset: contextReset, newHigh: false, newLow: false,
            initialized: false)
    }
}

/// Precomputed inclusive prefixes of a recorded source. Playback can jump over
/// frames without skipping an intervening extreme, and seeking backwards uses
/// the earlier prefix rather than retaining values from the future. Input order
/// is retained; invalid or out-of-order observations leave that prefix unchanged.
struct FillWatermarkHistory: Sendable {
    private let prefixes: [FillWatermarkSnapshot]
    var count: Int { prefixes.count }

    init(observations: [FillWatermarkObservation]) {
        var tracker = FillWatermarkTracker()
        prefixes = observations.map {
            tracker.observe($0, context: "recorded-history").snapshot
        }
    }

    func snapshot(through index: Int) -> FillWatermarkSnapshot {
        guard index >= 0, !prefixes.isEmpty else { return .empty }
        return prefixes[min(index, prefixes.count - 1)]
    }
}

/// Presentation only: a new record brightens, then settles over three seconds
/// of monotonic display time. It does not alter a mark's value or source clock.
enum FillWatermarkHighlight {
    static let duration: TimeInterval = 3

    static func intensity(elapsed: TimeInterval, reducedMotion: Bool = false) -> Double {
        guard !reducedMotion, elapsed.isFinite else { return 0 }
        let progress = min(1, max(0, elapsed / duration))
        let remaining = 1 - progress
        return remaining * remaining
    }
}
