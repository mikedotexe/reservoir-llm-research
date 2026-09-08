// Concatenated after the production model by check-fill-transition.sh.
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
private func close(_ actual: Double?, _ expected: Double) -> Bool {
    actual.map { abs($0 - expected) < 1e-10 } ?? false
}
private func receive(_ model: inout FillTransition, _ fill: Double, _ uptime: Double,
                     _ sourceTime: Double?, animated: Bool = true, context: String = "health/session-1") {
    model.receive(fill, at: uptime, animated: animated, context: context, sourceTime: sourceTime)
}

var model = FillTransition()
check(model.value(at: 0) == nil && !model.isAnimating(at: 0), "No observation creates no displayed fill")
receive(&model, 58, 10, 100)
check(close(model.value(at: 10), 58) && !model.isAnimating(at: 10), "The first valid observation snaps to its actual value")
receive(&model, 78, 11, 101)
check(close(model.value(at: 11), 58) && close(model.value(at: 11.4), 68)
    && close(model.value(at: 11.8), 78) && !model.isAnimating(at: 11.8),
    "A transition reaches its exact endpoint after 0.8 seconds with the expected midpoint")
let ascending = (0...160).compactMap { model.value(at: 11 + Double($0) / 200) }
check(ascending.count == 161 && ascending.allSatisfy { (58...78).contains($0) }
    && zip(ascending, ascending.dropFirst()).allSatisfy { $0 <= $1 },
    "Rising fill remains monotonic and never crosses beyond either observed endpoint")
check(close(model.value(at: 11.1), 58.321044921875)
    && close(model.value(at: 11.7), 77.678955078125),
    "The curve eases near both ends instead of moving at a constant speed")
receive(&model, 54, 12, 102)
let descending = (0...160).compactMap { model.value(at: 12 + Double($0) / 200) }
check(descending.count == 161 && descending.allSatisfy { (54...78).contains($0) }
    && zip(descending, descending.dropFirst()).allSatisfy { $0 >= $1 }
    && close(model.value(at: 12.8), 54),
    "Falling fill remains monotonic and ends exactly without undershoot")

receive(&model, 74, 13, 103)
let beforeInterruption = model.value(at: 13.3)
receive(&model, 60, 13.3, 104)
check(model.value(at: 13.3) == beforeInterruption && close(model.value(at: 14.1), 60),
    "A new target starts from the displayed position with no jump")
let beforeDuplicate = model.value(at: 13.6)
receive(&model, 60, 13.6, 105)
check(model.value(at: 13.6) == beforeDuplicate && close(model.value(at: 14.1), 60)
    && !model.isAnimating(at: 14.1), "An unchanged target advances the source clock without restarting easing")
receive(&model, 72, 14.2, 104.5)
check(close(model.value(at: 14.2), 72) && !model.isAnimating(at: 14.2),
    "A clock decrease after a duplicate fill is still detected and snaps")
receive(&model, 70, 14.3, 104.6)
check(close(model.value(at: 14.3), 72) && model.isAnimating(at: 14.3),
    "A restarted source establishes a new clock baseline for subsequent observations")

receive(&model, 70, 14.4, 1, context: "health/session-2")
check(close(model.value(at: 14.4), 70) && !model.isAnimating(at: 14.4),
    "Changing source or session snaps even when the target is unchanged")
receive(&model, 80, 15, 2, context: "health/session-2")
receive(&model, 80, 15.1, 2, animated: false, context: "health/session-2")
check(close(model.value(at: 15.1), 80) && !model.isAnimating(at: 15.1),
    "Disabling animation or enabling Reduce Motion snaps an in-flight duplicate target")
receive(&model, 60, 16, 3, context: "health/session-2")
for invalid in [Double.nan, .infinity, -.infinity, -1, 101] {
    receive(&model, invalid, 16.2, 1000, context: "invalid-source")
}
check(close(model.value(at: 16.4), 70) && close(model.value(at: 16.8), 60),
    "Invalid fill cannot replace the valid transition or contaminate its source identity")
receive(&model, 72, 17, 4, context: "health/session-2")
check(close(model.value(at: 17), 60) && model.isAnimating(at: 17),
    "Rejected observations do not advance the accepted source clock")
check(close(model.value(at: 500), 72) && !model.isAnimating(at: 500),
    "Missing or stale future readings finish the bounded transition and never extrapolate")

receive(&model, 0, 501, nil, animated: false, context: "unknown-clock")
receive(&model, 100, 502, nil, context: "unknown-clock")
check(close(model.value(at: 502.4), 50) && close(model.value(at: 502.8), 100),
    "Valid extreme fills and unavailable source clocks keep the same bounded presentation mapping")
receive(&model, 50, .nan, 500, context: "invalid-clock")
check(close(model.value(at: 503), 100) && !model.isAnimating(at: 503),
    "An invalid animation clock cannot replace the accepted value")
print("\(passed) fill transition checks passed.")
