# Regulation essentials

## Standalone use

From the repository root on macOS, build the shared package with
`ESSENTIALS_BUILD_DIR=/tmp/essentials-standalone essentials/build.sh`. Save this
public `EssentialsCore` example as `/tmp/regulation-example.swift`. It closes the
field/controller loop on synthetic input without a reservoir or language model:

```swift
import EssentialsCore

var field = try SensoryField(seed: 98)
var random = SplitMix64(seed: 42)
var estimator = ReducedFill()
var controller = RetentionController()
for _ in 0..<120 {
    let input = (0..<66).map { _ in random.nextSigned() }
    let measured = try field.step(input: input, retention: controller.currentRetention)
    let fillFraction = estimator.update(eigenvalues: measured.eigenvalues, dt: 1.0 / 3.0)
    controller.update(fillPct: 100 * fillFraction) // Retention changes on the NEXT step.
}
print("Reduced fill percent:", 100 * estimator.fill)
print("Next retention:", controller.currentRetention)
```

Compile and run the independent example:

```sh
swiftc -I /tmp/essentials-standalone/lib -L /tmp/essentials-standalone/lib -lEssentialsCore -framework Accelerate /tmp/regulation-example.swift -o /tmp/regulation-example
/tmp/regulation-example
```

Create the research output directory first with `mkdir -p research/outputs/essentials`.

For the assembled four-part recipe with scripted replies:
`/tmp/essentials-standalone/bin/essentials-run run --config essentials/stages/04-regulation.json --output research/outputs/essentials/regulation-run.json`.

## Equations and source relationship

Reduced active-mode fill counts **all 32 sensory eigenvalues** exceeding 0.12
times their current mean. It divides active count by 32, uses a 0.04 minimum only
if a mode is active, and smooths with `F_next = .10 F_instant + .90 (1-.006 dt) F`.
The decay factor is capped at 0.15 per update. Initial smoothed fill is zero.
Identity covariance has broad rank under this definition; native RMS is unrelated.

The controller targets 68% with a ±4-point deadband. Signed error outside that
band is divided by 20. Tentative integral is `clamp(.85 I + e, -1, 1)`;
`u=clamp(.55 e + .04 I, -.12, .12)` and requested retention is
`clamp(.955-u, .82, .995)`. Integration stops in a saturated error direction.
Applied retention slews at most .01 each step and acts on the **next** field update.
The controller changes actual covariance retention; it never edits a fill label.

Source mapping: Minime `spectral/eigenfill.rs` fixed-survival rank and smoothing
idea; `regulator/core/pi.rs` error scaling and bounded PI; `rescue_scaffold.rs`
target/deadband/gain constants; `runtime/orchestration.rs` fill-sensitive retention.
Inspected commit `c9c2a70fb8dbb3fd51725839fce853cc8d576db5`, September 9, 2026.

This symmetric small retention PI is a new experiment. Production uses a leading
cascade, extra estimator history, multiple controllers, recovery, drainage and
scaffold blending. Its current-runtime and fixed-survival fill policies differ.
These controls do not reproduce either complete production policy. Target
attainment depends on the forcing: insufficiently varied input can make the target
unreachable. No extra stimulus is invented to hide that outcome.

The retained [numerical qualification](../examples/regulation-qualification.json)
is emitted by `tests/MechanismTests.swift`. Its paired 600-step fixture holds all
input vectors fixed, evaluates steps 301–600 (n=300), and changes only retention.
Mean absolute target error is 11.925 percentage points at fixed retention and
4.160 with the controller. This is improvement in that fixture, not convergence:
the regulated fill ranges from 68.683% to 74.235%. Separate 120-step rank-one and
zero-field tests leave fill at 3.929% and 0% while retention saturates at 0.995.
The report includes exact values, source hashes, and the repeatable test command.
