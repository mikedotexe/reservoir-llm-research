# Fading watermarks in Reference zones

Mike asked for both measured watermarks to decay, with another pair beginning to
form halfway through the fade. Reservoir Scope **0.7.1 build 10** implements
overlapping recent ranges in the native steward viewer. This supersedes the
persistent extrema and short record glow described in the
[0.7.0 account](2026-09-07-reference-watermarks.md). Fixed regulator references
retain their meanings; recent high and low measurements are a separate overlay.

## What a line means

Each pair collects measured high and low fill during a **30-source-second**
interval. The lines fade linearly over **60 source seconds** from that interval's
start, using `opacity = max(0, 1 - age / 60)`. At age 30 the pair freezes, half
faded, while the next interval begins collecting. A new pair appears only when
that interval receives an actual observation. At most two nonempty pairs remain
visible; a source-time gap can expire both without inventing replacement fill.

At the default **20× recorded playback**, a pair lasts three viewing seconds and
the next interval starts after 1.5 seconds. The existing adjacent
1×/5×/10×/20×/40× speed buttons remain. Speed changes presentation pace while
preserving which measurements belong to each range.

Solid arcs identify the forming pair; longer dashed arcs identify its fading
predecessor. The right-side cards keep one readable pair of percentages and
source timestamps, a FORMING/FADING label, and a small earlier-value annotation
when the generations overlap. An expired empty range reads “Waiting for recent
fill.” Geometry uses the existing measured fill-to-radius mapping and lens
projection. Values outside the lens crop retain their labels without a false
edge marker. Aging changes visibility, never the measured fill position.

## Clocks and provenance

Recorded intervals originate at the first saved source timestamp. Every sample
through the selected row contributes, including samples skipped between redraws.
The continuous replay clock drives opacity; exact fractional position survives
pause and resume. Rewind reconstructs the earlier prefix and excludes future
measurements. A guard accommodates rounding differences between saved UTC and
elapsed timestamps.

Health intervals originate at the first accepted observation after a Follow,
source or session reset. Only the watermark model's accepted source timestamps
advance their age. Repeated, rejected, unchanged stale or failed polls freeze
the retained view; a later accepted time jump can expire it. The accumulator
survives chart-buffer eviction.

Activation ranges contain only the current accepted batch. A fixed UTC grid,
with thirty-second boundaries, prevents movement of the batch's first row from
refreshing an observation's age or changing its interval. This is a display
convention, not evidence of boot continuity. Live clocks are never extrapolated
through missing observations. Neither source uses the eased cyan surface as a
measurement. The [animation guide](../native/ReservoirScope/docs/ANIMATION-DATA.md#observed-high-and-low-water-marks)
contains the complete source contract.

Reduce Motion preserves collection, overlap and expiry with static opacity:
1 while forming and 0.35 while retiring. It suppresses continuous fading; the
separate fill-easing permission does not override this behavior.

## Verification and limits

The final targeted checks pass: **52** interval-memory checks,
**42** evidence/source/reference/playback checks, and **85** offscreen view
checks, **179 total**. The model checks cover exact turnover boundaries,
pause, skipped observations, rewind, gaps, resets, rejected clocks and batch
replacement. The offscreen checks produced **28 final PNGs** using the exact
production model, SwiftUI overlay and extracted lens geometry at compact and
nominal sizes. Their [results](../native/ReservoirScope/validation/0.7.1/watermark-view/checks.json)
and [visual review](../native/ReservoirScope/validation/0.7.1/watermark-view/visual-review.json)
record readable overlap, older-geometry disappearance, out-of-crop labeling,
empty gaps and stable Reduce Motion rendering. Preliminary images before the
compact-label correction remain separately retained.

An independent [recorded-data probe](../probes/reference_watermark_memory.py)
reconstructs inclusive interval expectations from the bundled capture. At cursor
13, the older pair contains 13 measurements (high 75.44%, low 63.31%) and the
forming pair contains one (68.71% for both). At cursor 26, the first interval
has expired: its successor contains 13 measurements (74.73%, 59.90%) and the
newest contains one (66.02% for both). The
[expectation receipt](../native/ReservoirScope/validation/0.7.1/recorded-memory-expectations.json)
retains full precision, timestamps, counts and input identity. Final native
accessibility inspection matches both cursors and the final replay range. A
native-window screenshot at cursor 13 confirms readable overlapping guides and
cards against the Metal reference lens.

The [final artifact identity](../native/ReservoirScope/validation/0.7.1/artifact-identity.json)
verifies 20 packaged Swift sources and six resources against the workspace, plus
the bundle signature. The separate [runtime receipt](../native/ReservoirScope/validation/0.7.1/runtime-qa.json)
records the native checks, existing Reduce Motion setting, and an automation
delay during playback. Precise interactive pause latency was not measured.
This pass does not measure fresh live ingestion, M4 performance, presentation latency or
energy. No being's producer, runtime or controller was changed.

Reproduce from the research repository root:

```sh
native/ReservoirScope/check-fill-watermark-memory.sh
native/ReservoirScope/check-evidence.sh
native/ReservoirScope/check-watermark-view.sh
python3 probes/reference_watermark_memory.py
python3 native/ReservoirScope/verify-app-identity.py
```
