// Concatenated after the production models by check-fill-watermark-memory.sh.
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
private func sample(_ fill: Double, _ time: Double,
                    _ ordinal: UInt64) -> FillWatermarkObservation {
    FillWatermarkObservation(fillPct: fill, sourceTime: time, ordinal: ordinal)
}
private func close(_ actual: Double, _ expected: Double) -> Bool {
    abs(actual - expected) < 0.000_000_001
}

var memory = FillWatermarkMemory()
check(memory.ranges(at: 10).isEmpty && memory.latestSourceTime == nil,
      "No observation means no line, even when the presentation clock advances")
let first = sample(60, 10, 0)
let initialized = memory.observe(first, context: "replay")
let initialRange = memory.ranges(at: 10)[0]
check(initialized.accepted && initialized.contextReset && memory.origin == 10
      && initialRange.startTime == 10
      && initialRange.snapshot == FillWatermarkSnapshot(high: first, low: first, count: 1),
      "The first valid measured sample establishes the default source origin and both marks")
check(initialRange.opacity(at: 10) == 1 && initialRange.isCollecting(at: 10),
      "A newly observed generation begins bright and collecting")
memory.observe(sample(55, 20, 1), context: "replay")
memory.observe(sample(70, 39.999, 2), context: "replay")
let firstGathered = memory.ranges(at: 39.999)[0]
check(firstGathered.snapshot.high?.fillPct == 70
      && firstGathered.snapshot.low?.fillPct == 55 && firstGathered.snapshot.count == 3,
      "Rising and falling measured fill shape the collecting high and low marks")
check(memory.ranges(at: 40).count == 1
      && memory.ranges(at: 40)[0].opacity(at: 40) == 0.5,
      "At half-life an old line reaches half opacity without seeding an unobserved successor")
memory.observe(sample(62, 40, 3), context: "replay")
let overlap = memory.ranges(at: 40)
check(overlap.map(\.startTime) == [10, 40]
      && overlap.map { $0.opacity(at: 40) } == [0.5, 1],
      "A measurement exactly thirty source seconds later starts a bright successor beside the half-faded line")
check(!overlap[0].isCollecting(at: 40) && overlap[1].isCollecting(at: 40),
      "The retiring generation freezes precisely when the successor begins collecting")
memory.observe(sample(80, 50, 4), context: "replay")
memory.observe(sample(45, 60, 5), context: "replay")
let shapedSuccessor = memory.ranges(at: 60)
check(shapedSuccessor[0].snapshot == firstGathered.snapshot
      && shapedSuccessor[1].snapshot.high?.fillPct == 80
      && shapedSuccessor[1].snapshot.low?.fillPct == 45,
      "Later extremes shape only the new generation and leave the fading old measurements unchanged")
check(close(shapedSuccessor[0].opacity(at: 60), 1.0 / 6)
      && close(shapedSuccessor[1].opacity(at: 60), 2.0 / 3),
      "Both generations fade continuously by source age, independently of their fill values")
check(memory.ranges(at: 69.999).count == 2
      && memory.ranges(at: 70).map(\.startTime) == [40],
      "An old generation remains just before sixty seconds and disappears at its exact lifetime")
memory.observe(sample(65, 70, 6), context: "replay")
check(memory.ranges(at: 70).map(\.startTime) == [40, 70],
      "The third generation replaces the expired first generation without keeping a third visible line")
memory.observe(sample(65, 70, 7), context: "replay")
let tieRange = memory.ranges(at: 70).last!
check(tieRange.snapshot.count == 2 && tieRange.snapshot.high?.ordinal == 6
      && tieRange.snapshot.low?.ordinal == 6,
      "Equal fill and equal source time may count as a distinct ordered sample while retaining the first extreme")

let pausedRanges = memory.ranges(at: 75)
check((0..<100).allSatisfy { _ in memory.ranges(at: 75) == pausedRanges }
      && pausedRanges.last!.opacity(at: 75) == memory.ranges(at: 75).last!.opacity(at: 75),
      "Repeated display frames at a paused source clock change neither geometry nor fading")
check(memory.ranges(at: 69).isEmpty,
      "The live accumulator does not leak its latest observation into an earlier source time")
check(memory.ranges(at: 130).isEmpty,
      "A source gap can expire all measured lines without manufacturing new fill")
memory.observe(sample(61, 200, 8), context: "replay")
check(memory.ranges(at: 200).map(\.startTime) == [190]
      && memory.ranges(at: 200)[0].snapshot.count == 1
      && close(memory.ranges(at: 200)[0].opacity(at: 200), 5.0 / 6),
      "The first measurement after a long gap joins its fixed source-time generation at its actual age")

let acceptedRanges = memory.ranges(at: 200)
for invalidFill in [Double.nan, .infinity, -.infinity, -0.1, 100.1] {
    let result = memory.observe(sample(invalidFill, 10_000, 100), context: "replay")
    check(!result.accepted && memory.latestSourceTime == 200
          && memory.ranges(at: 200) == acceptedRanges,
          "Invalid measured fill \(invalidFill) cannot advance the accepted clock or retire marks")
}
for invalidTime in [Double.nan, .infinity, -.infinity] {
    let result = memory.observe(sample(99, invalidTime, 100), context: "replay")
    check(!result.accepted && memory.latestSourceTime == 200
          && memory.ranges(at: 200) == acceptedRanges,
          "Invalid source time \(invalidTime) cannot create a generation")
}
check(!memory.observe(sample(99, 10_000, 8), context: "replay").accepted
      && !memory.observe(sample(99, 10_000, 7), context: "replay").accepted
      && memory.latestSourceTime == 200 && memory.ranges(at: 200) == acceptedRanges,
      "Duplicate and earlier ordinals cannot move the accepted source clock even with a later claimed timestamp")
check(!memory.observe(sample(99, 199, 100), context: "replay").accepted
      && memory.ranges(at: 200) == acceptedRanges,
      "A newer ordinal with a backward source timestamp cannot erase or reshape a generation")
check(!memory.observe(sample(99, 201, 100), context: "replay", origin: 0).accepted
      && memory.origin == 10 && memory.latestSourceTime == 200,
      "An established context cannot silently change its fixed generation origin")
check(memory.observe(sample(62, 201, 9), context: "replay").accepted,
      "Rejected observations do not consume ordinals needed by subsequent valid measurements")
check([Double.nan, .infinity, -.infinity].allSatisfy { memory.ranges(at: $0).isEmpty },
      "An invalid presentation clock produces no visible marks")

let newContext = memory.observe(sample(0, 0, 0), context: "health/session-b")
check(newContext.accepted && newContext.contextReset && memory.origin == 0
      && memory.ranges(at: 0).count == 1 && memory.ranges(at: 0)[0].snapshot.count == 1,
      "A new source context clears old generations and may restart its clock and ordinal")
memory.observe(sample(100, 1, 1), context: "health/session-b")
check(memory.ranges(at: 1)[0].snapshot.low?.fillPct == 0
      && memory.ranges(at: 1)[0].snapshot.high?.fillPct == 100,
      "Exactly empty and full are valid measured extrema")
let invalidNewContext = memory.observe(sample(.nan, 0, 0), context: "health/session-c")
check(!invalidNewContext.accepted && invalidNewContext.contextReset
      && memory.context == "health/session-c" && memory.origin == nil
      && memory.latestSourceTime == nil && memory.ranges(at: 1).isEmpty,
      "An invalid first sample in a new context cannot inherit the previous source's lines")
check(!memory.observe(sample(60, 10, 0), context: "health/session-c", origin: 11).accepted
      && !memory.observe(sample(60, 10, 0), context: "health/session-c", origin: .nan).accepted
      && memory.origin == nil,
      "A future or invalid explicit origin is rejected without establishing the new source clock")
memory.observe(sample(61, 10, 0), context: "health/session-c")
memory.reset(context: "reset-source")
check(memory.context == "reset-source" && memory.origin == nil
      && memory.latestSourceTime == nil && memory.ranges(at: 10).isEmpty,
      "An explicit reset can establish a context while clearing every observation and generation")
memory.reset()
check(memory.context == nil && memory.ranges(at: 100).isEmpty,
      "An unscoped reset clears the source identity too")

let recording = [sample(60, 100, 0), sample(80, 105, 1), sample(40, 120, 2),
                 sample(62, 130, 3), sample(75, 140, 4), sample(50, 150, 5),
                 sample(65, 160, 6)]
let history = FillWatermarkMemoryHistory(observations: recording)
let forward = history.ranges(through: 5, at: 155)
check(forward.map(\.startTime) == [100, 130]
      && forward[0].snapshot.high?.fillPct == 80 && forward[0].snapshot.low?.fillPct == 40
      && forward[1].snapshot.high?.fillPct == 75 && forward[1].snapshot.low?.fillPct == 50,
      "A replay jump consumes all skipped measured extremes in both visible generations")
let rewind = history.ranges(through: 1, at: 105)
check(rewind.count == 1 && rewind[0].startTime == 100
      && rewind[0].snapshot.high?.fillPct == 80 && rewind[0].snapshot.low?.fillPct == 60
      && rewind[0].snapshot.count == 2,
      "Rewinding restores the earlier generation and excludes every future low and successor")
check(history.ranges(through: 5, at: 155) == forward,
      "Replaying after a rewind deterministically reconstructs the same source-time memories")
check(history.ranges(through: 6, at: 160).map(\.startTime) == [130, 160],
      "Recorded playback expires and replaces generations at the same exact boundaries as live observation")
check(history.ranges(through: -1, at: 100).isEmpty
      && FillWatermarkMemoryHistory(observations: []).ranges(through: 0, at: 100).isEmpty,
      "An empty recording or negative cursor exposes no watermark history")
check(history.count == recording.count
      && history.ranges(through: Int.max, at: 160) == history.ranges(through: 6, at: 160),
      "Recorded cursor indexing is retained and a cursor beyond the recording uses its final prefix")
check(history.ranges(through: 5, at: 149).isEmpty,
      "A mismatched recorded prefix cannot present measurements from later than its source clock")
let malformed = FillWatermarkMemoryHistory(observations: [
    sample(.nan, 0, 0), sample(60, 100, 1), sample(99, 10_000, 1),
    sample(99, 90, 2), sample(50, 110, 3)
])
check(malformed.ranges(through: 0, at: 0).isEmpty
      && malformed.ranges(through: 3, at: 100)[0].snapshot.count == 1
      && malformed.ranges(through: 4, at: 110)[0].snapshot.low?.fillPct == 50,
      "Malformed recorded observations retain their cursor positions without poisoning later valid prefixes")

let epochBatchA = [sample(60, 100, 100), sample(70, 110, 110),
                  sample(50, 125, 125), sample(65, 135, 135)]
let epochBatchB = [sample(70, 110, 110), sample(50, 125, 125),
                  sample(65, 135, 135), sample(68, 145, 145)]
let epochBatchC = [sample(50, 125, 125), sample(65, 135, 135),
                  sample(68, 145, 145), sample(55, 155, 155)]
let batchA = FillWatermarkMemoryHistory(observations: epochBatchA, origin: 0).ranges(through: 3, at: 135)
let batchB = FillWatermarkMemoryHistory(observations: epochBatchB, origin: 0).ranges(through: 3, at: 145)
let batchC = FillWatermarkMemoryHistory(observations: epochBatchC, origin: 0).ranges(through: 3, at: 155)
check(batchA.map(\.startTime) == [90, 120] && batchB.map(\.startTime) == [90, 120],
      "Replacement activation batches use the same thirty-second epoch grid despite differing first observations")
check(batchA[0].snapshot.low?.fillPct == 60 && batchB[0].snapshot.low?.fillPct == 70,
      "A replacement batch reports only its own retained measurements and does not pretend to retain missing observations")
check(batchC.map(\.startTime) == [120, 150]
      && batchC[0].snapshot.high?.fillPct == 68 && batchC[0].snapshot.low?.fillPct == 50,
      "An epoch-aligned rolling batch replaces the oldest generation without resetting the newer interval")

let fadeRange = FillWatermarkMemoryRange(startTime: 1_000,
    snapshot: FillWatermarkSnapshot(high: first, low: first, count: 1))
let fading = (0...600).map { fadeRange.opacity(at: 1_000 + Double($0) / 10) }
check(fading.first == 1 && fading.last == 0
      && fading.allSatisfy { (0...1).contains($0) }
      && zip(fading, fading.dropFirst()).allSatisfy { $0 >= $1 }
      && fadeRange.opacity(at: 1_030) == 0.5,
      "Normal motion fades monotonically and linearly from full brightness to zero over sixty source seconds")
check(fadeRange.opacity(at: 1_000, reducedMotion: true) == 1
      && fadeRange.opacity(at: 1_029.999, reducedMotion: true) == 1
      && fadeRange.opacity(at: 1_030, reducedMotion: true) == 0.35
      && fadeRange.opacity(at: 1_059.999, reducedMotion: true) == 0.35
      && fadeRange.opacity(at: 1_060, reducedMotion: true) == 0,
      "Reduce Motion uses stable collecting and retiring levels while preserving the same measured lifetime")
check(fadeRange.opacity(at: 999) == 0 && !fadeRange.isCollecting(at: 999)
      && [Double.nan, .infinity, -.infinity].allSatisfy {
          fadeRange.opacity(at: $0) == 0 && !fadeRange.isCollecting(at: $0)
      }, "A future range and an invalid display clock cannot produce a visible or collecting line")

var longRun = FillWatermarkMemory()
var bounded = true
for ordinal in 0..<10_000 {
    let time = Double(ordinal) * 1.75
    longRun.observe(sample(Double(ordinal % 101), time, UInt64(ordinal)), context: "long-run")
    let ranges = longRun.ranges(at: time)
    bounded = bounded && ranges.count <= 2 && ranges.allSatisfy { $0.snapshot.count > 0 }
}
check(bounded, "A long observed stream retains at most two nonempty measured generations")
var coarseClock = FillWatermarkMemory()
check(!coarseClock.observe(sample(60, Double.greatestFiniteMagnitude, 0), context: "coarse").accepted
      && coarseClock.latestSourceTime == nil,
      "A finite clock too coarse to resolve the display lifetime cannot create an immortal line")
var exactOrdinal = FillWatermarkMemory()
let large: UInt64 = 9_007_199_254_740_992
exactOrdinal.observe(sample(60, 0, large), context: "large-ordinal")
check(exactOrdinal.observe(sample(70, 0, large + 1), context: "large-ordinal").accepted
      && exactOrdinal.ranges(at: 0)[0].snapshot.high?.ordinal == large + 1,
      "Large adjacent source ordinals remain exact without conversion to a floating-point identity")

print("\(passed) fill watermark memory checks passed.")
