import Foundation

/// One short memory of measured fill. It gathers extrema for its first thirty
/// source seconds, then keeps those measurements unchanged while it fades out.
/// This is a display interval, not a claim about an engine cycle or boot session.
struct FillWatermarkMemoryRange: Equatable, Sendable {
    let startTime: Double
    let snapshot: FillWatermarkSnapshot

    func isCollecting(at sourceTime: Double) -> Bool {
        guard sourceTime.isFinite else { return false }
        return sourceTime >= startTime
            && sourceTime < startTime + FillWatermarkMemory.stride
    }

    func opacity(at sourceTime: Double, reducedMotion: Bool = false) -> Double {
        guard sourceTime.isFinite, sourceTime >= startTime else { return 0 }
        let age = sourceTime - startTime
        guard age < FillWatermarkMemory.lifetime else { return 0 }
        if reducedMotion { return isCollecting(at: sourceTime) ? 1 : 0.35 }
        return 1 - age / FillWatermarkMemory.lifetime
    }
}

struct FillWatermarkMemoryUpdate: Equatable, Sendable {
    let accepted: Bool
    let contextReset: Bool
}

/// Overlapping, fixed source-time generations. Only an accepted observation can
/// create a range: a gap never seeds a new mark with a held or eased fill value.
/// A fresh range starts every thirty seconds and survives for sixty seconds;
/// therefore no more than two nonempty ranges can be visible at once.
struct FillWatermarkMemory: Sendable {
    static let lifetime: TimeInterval = 60
    static let stride: TimeInterval = 30

    private(set) var context: String?
    private(set) var origin: Double?
    private(set) var latestSourceTime: Double?
    private var latestOrdinal: UInt64?
    private var retainedRanges: [FillWatermarkMemoryRange] = []

    mutating func reset(context: String? = nil) {
        self.context = context
        origin = nil
        latestSourceTime = nil
        latestOrdinal = nil
        retainedRanges = []
    }

    /// `origin` is fixed by the first accepted sample. Omit it to begin at that
    /// sample's source time. An explicit zero anchors bounded activation batches
    /// to the same epoch grid without claiming continuity between the batches.
    /// Rejected observations change neither the accepted clock nor the origin.
    @discardableResult
    mutating func observe(_ observation: FillWatermarkObservation,
                          context: String,
                          origin requestedOrigin: Double? = nil) -> FillWatermarkMemoryUpdate {
        let contextReset = self.context != context
        if contextReset { reset(context: context) }
        let rejection = FillWatermarkMemoryUpdate(accepted: false, contextReset: contextReset)
        guard observation.isValid else { return rejection }
        if let latestOrdinal, observation.ordinal <= latestOrdinal { return rejection }
        if let latestSourceTime, observation.sourceTime < latestSourceTime { return rejection }
        if let requestedOrigin {
            guard requestedOrigin.isFinite,
                  requestedOrigin <= observation.sourceTime else { return rejection }
            if let origin, requestedOrigin != origin { return rejection }
        }

        let chosenOrigin = origin ?? requestedOrigin ?? observation.sourceTime
        let offset = observation.sourceTime - chosenOrigin
        guard offset.isFinite else { return rejection }
        let start = chosenOrigin + floor(offset / Self.stride) * Self.stride
        let collectionEnd = start + Self.stride
        let expiration = start + Self.lifetime
        // At extreme Double magnitudes the source clock cannot resolve these
        // intervals. Reject rather than invent a boundary or an immortal mark.
        guard start.isFinite, collectionEnd.isFinite, expiration.isFinite,
              collectionEnd > start, expiration > collectionEnd,
              observation.sourceTime >= start,
              observation.sourceTime < collectionEnd else { return rejection }

        self.origin = chosenOrigin
        latestSourceTime = observation.sourceTime
        latestOrdinal = observation.ordinal
        retainedRanges.removeAll { observation.sourceTime >= $0.startTime + Self.lifetime }

        if let index = retainedRanges.firstIndex(where: { $0.startTime == start }) {
            let old = retainedRanges[index].snapshot
            retainedRanges[index] = FillWatermarkMemoryRange(startTime: start,
                snapshot: FillWatermarkSnapshot(
                    high: old.high.map { observation.fillPct > $0.fillPct ? observation : $0 }
                        ?? observation,
                    low: old.low.map { observation.fillPct < $0.fillPct ? observation : $0 }
                        ?? observation,
                    count: old.count + 1))
        } else {
            retainedRanges.append(FillWatermarkMemoryRange(startTime: start,
                snapshot: FillWatermarkSnapshot(high: observation, low: observation, count: 1)))
        }
        return FillWatermarkMemoryUpdate(accepted: true, contextReset: contextReset)
    }

    /// `sourceTime` is the trusted presentation clock of the selected source.
    /// Advancing it may retire existing marks, but cannot create a new range.
    /// Use the matching history prefix to rewind; this live accumulator cannot
    /// reconstruct observations from before its latest accepted source sample.
    func ranges(at sourceTime: Double) -> [FillWatermarkMemoryRange] {
        guard sourceTime.isFinite, let latestSourceTime,
              sourceTime >= latestSourceTime else { return [] }
        return retainedRanges.filter { $0.opacity(at: sourceTime) > 0 }
    }
}

/// Inclusive recorded prefixes retain all intervening measurements when the
/// playhead skips frames, and never carry future extrema back through a seek.
/// Each prefix stores only its two possible active generations.
struct FillWatermarkMemoryHistory: Sendable {
    private let prefixes: [FillWatermarkMemory]
    var count: Int { prefixes.count }

    init(observations: [FillWatermarkObservation], origin: Double? = nil) {
        var memory = FillWatermarkMemory()
        prefixes = observations.map {
            memory.observe($0, context: "recorded-memory", origin: origin)
            return memory
        }
    }

    func ranges(through index: Int, at sourceTime: Double) -> [FillWatermarkMemoryRange] {
        guard index >= 0, !prefixes.isEmpty else { return [] }
        return prefixes[min(index, prefixes.count - 1)].ranges(at: sourceTime)
    }
}
