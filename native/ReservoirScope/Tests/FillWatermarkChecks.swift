// Concatenated after the production model by check-fill-watermarks.sh.
import Foundation

private var passed = 0
@MainActor private func check(_ condition: Bool, _ description: String) {
    guard condition else {
        fputs("FAIL: \(description)\n", stderr)
        exit(1)
    }
    passed += 1
    print("PASS \(passed): \(description)")
}
private func sample(_ fill: Double, _ ordinal: UInt64,
                    time: Double? = nil) -> FillWatermarkObservation {
    FillWatermarkObservation(fillPct: fill, sourceTime: time ?? 1_700_000_000 + Double(ordinal),
                             ordinal: ordinal)
}

let observations = [sample(62, 0), sample(70, 1), sample(59, 2),
                    sample(65, 3), sample(70, 4), sample(59, 5),
                    sample(72, 6), sample(57, 7), sample(64, 8)]
let history = FillWatermarkHistory(observations: observations)
check(history.snapshot(through: -1) == .empty
      && FillWatermarkHistory(observations: []).snapshot(through: 0) == .empty,
      "No observed prefix produces no watermarks")
check(history.snapshot(through: 0) == FillWatermarkSnapshot(
    high: observations[0], low: observations[0], count: 1),
    "The first measured observation initializes both marks")
check(history.snapshot(through: 3) == FillWatermarkSnapshot(
    high: observations[1], low: observations[2], count: 4),
    "A fast playback jump includes highs and lows in skipped frames")
check(history.snapshot(through: 5).high == observations[1]
      && history.snapshot(through: 5).low == observations[2]
      && history.snapshot(through: 5).count == 6,
      "Tied extrema retain their first source observation and source time")
check(history.snapshot(through: 8) == FillWatermarkSnapshot(
    high: observations[6], low: observations[7], count: 9),
    "A later prefix uses actual later record values")
check(history.snapshot(through: 3).high == observations[1]
      && history.snapshot(through: 3).low == observations[2],
      "Rewinding excludes every future record")
check(history.snapshot(through: Int.max) == history.snapshot(through: 8)
      && history.count == observations.count,
      "A cursor beyond the source uses its final prefix without extrapolation")

var tracker = FillWatermarkTracker()
let initial = tracker.observe(observations[0], context: "health/session-a")
check(initial.accepted && initial.initialized && initial.newHigh && initial.newLow
      && initial.contextReset && initial.snapshot.count == 1,
      "Live initialization explicitly identifies its first sample and source scope")
let duplicate = tracker.observe(observations[0], context: "health/session-a")
check(!duplicate.accepted && !duplicate.newHigh && !duplicate.newLow
      && !duplicate.contextReset && duplicate.snapshot == initial.snapshot,
      "Repeated polling of one health snapshot changes neither marks nor count")
let conflictingDuplicate = tracker.observe(sample(99, 0), context: "health/session-a")
check(!conflictingDuplicate.accepted && conflictingDuplicate.snapshot == initial.snapshot,
      "A changed payload under an already accepted ordinal cannot replace a mark")
let rising = tracker.observe(observations[1], context: "health/session-a")
check(rising.accepted && rising.newHigh && !rising.newLow && !rising.initialized,
      "A genuine higher sample reports only a new high")
let falling = tracker.observe(observations[2], context: "health/session-a")
check(falling.accepted && !falling.newHigh && falling.newLow,
      "A genuine lower sample reports only a new low")
let tiedHigh = tracker.observe(sample(70, 3), context: "health/session-a")
check(tiedHigh.accepted && !tiedHigh.newHigh && !tiedHigh.newLow
      && tiedHigh.snapshot.high == observations[1] && tiedHigh.snapshot.count == 4,
      "A tied live high counts as a sample without restarting the record highlight")
let tiedLow = tracker.observe(sample(59, 4), context: "health/session-a")
check(tiedLow.accepted && !tiedLow.newHigh && !tiedLow.newLow
      && tiedLow.snapshot.low == observations[2],
      "A tied live low retains its first timestamp without a new highlight")
let beforeInvalid = tracker.snapshot
for invalid in [Double.nan, .infinity, -.infinity, -0.001, 100.001] {
    let outcome = tracker.observe(sample(invalid, 100), context: "health/session-a")
    check(!outcome.accepted && outcome.snapshot == beforeInvalid,
          "Invalid measured fill \(invalid) cannot contaminate extrema")
}
for invalidTime in [Double.nan, .infinity, -.infinity] {
    let outcome = tracker.observe(sample(99, 100, time: invalidTime), context: "health/session-a")
    check(!outcome.accepted && outcome.snapshot == beforeInvalid,
          "Invalid source time \(invalidTime) cannot create a timestamped record")
}
check(tracker.observe(sample(68, 5), context: "health/session-a").accepted,
      "Rejected invalid samples do not advance the accepted source ordinal")
let beforeOutOfOrder = tracker.snapshot
check(!tracker.observe(sample(100, 4, time: 1_700_000_099), context: "health/session-a").accepted
      && tracker.snapshot == beforeOutOfOrder,
      "An older ordinal is rejected even if its payload claims a later source clock")
check(!tracker.observe(sample(100, 100, time: 1_700_000_001), context: "health/session-a").accepted
      && tracker.snapshot == beforeOutOfOrder,
      "An older source clock is rejected even if its ordinal is newer")
check(tracker.observe(sample(71, 6, time: 1_700_000_005), context: "health/session-a").accepted,
      "Distinct ordered observations may share a coarse source timestamp")
let newContext = tracker.observe(sample(64, 0, time: 0), context: "health/session-b")
check(newContext.contextReset && newContext.initialized && newContext.accepted
      && newContext.snapshot.high?.fillPct == 64 && newContext.snapshot.low?.fillPct == 64
      && newContext.snapshot.count == 1,
      "A new source session resets history and may restart both source clocks")
let invalidNewContext = tracker.observe(sample(.nan, 1), context: "health/session-c")
check(invalidNewContext.contextReset && !invalidNewContext.accepted
      && tracker.snapshot == .empty && tracker.context == "health/session-c",
      "An invalid first sample in a new source never inherits the previous source's marks")
tracker.reset()
check(tracker.context == nil && tracker.snapshot == .empty,
      "An explicit reset clears source identity and observed marks")
tracker.reset(context: "health/session-d")
check(tracker.context == "health/session-d" && tracker.snapshot == .empty,
      "An explicit session reset can establish its next source identity")
let zero = tracker.observe(sample(0, 0), context: "health/session-d")
let full = tracker.observe(sample(100, 1), context: "health/session-d")
check(zero.accepted && full.accepted && full.snapshot.low?.fillPct == 0
      && full.snapshot.high?.fillPct == 100,
      "Exactly empty and full measured fills are valid extrema")

let malformed = FillWatermarkHistory(observations: [
    sample(.nan, 0), sample(63, 1), sample(101, 2), sample(69, 3),
    sample(99, 3), sample(20, 4, time: 1_700_000_002), sample(58, 5)
])
check(malformed.snapshot(through: 0) == .empty
      && malformed.snapshot(through: 2).count == 1,
      "Invalid recorded samples preserve original cursor indexing without inventing fill")
check(malformed.snapshot(through: 5).count == 2
      && malformed.snapshot(through: 5).high?.fillPct == 69
      && malformed.snapshot(through: 5).low?.fillPct == 63,
      "Recorded duplicate and out-of-order samples cannot create false extrema")
check(malformed.snapshot(through: 6).count == 3
      && malformed.snapshot(through: 6).low?.fillPct == 58,
      "A valid later recorded observation remains eligible after rejected samples")

// The UInt64 identity remains exact even beyond JavaScript's integer precision.
var largeOrdinal = FillWatermarkTracker()
let firstLarge: UInt64 = 9_007_199_254_740_992
largeOrdinal.observe(sample(60, firstLarge, time: 10), context: "large")
check(largeOrdinal.observe(sample(70, firstLarge + 1, time: 10), context: "large").newHigh
      && largeOrdinal.snapshot.high?.ordinal == firstLarge + 1,
      "Adjacent large source ordinals remain distinct without conversion to Double")

let intensities = (0...300).map { FillWatermarkHighlight.intensity(elapsed: Double($0) / 100) }
check(intensities.first == 1 && intensities.last == 0
      && intensities.allSatisfy { (0...1).contains($0) }
      && zip(intensities, intensities.dropFirst()).allSatisfy { $0 >= $1 },
      "The record highlight fades monotonically from bright to resting in three seconds")
check(FillWatermarkHighlight.intensity(elapsed: 1.5) == 0.25
      && FillWatermarkHighlight.intensity(elapsed: 30) == 0,
      "The highlight eases into its resting appearance and never extrapolates")
check([0.0, 1.5, 3.0].allSatisfy {
    FillWatermarkHighlight.intensity(elapsed: $0, reducedMotion: true) == 0
}, "Reduce Motion removes the brightness animation without changing measured marks")
check([Double.nan, .infinity, -.infinity].allSatisfy {
    FillWatermarkHighlight.intensity(elapsed: $0) == 0
}, "An invalid display clock cannot create a flashing mark")
print("\(passed) fill watermark checks passed.")
