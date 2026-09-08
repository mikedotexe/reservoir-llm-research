# Observed watermarks in Reference zones

Mike requested a slower default pace, adjacent speed buttons and persistent high/low fill marks that make a newly observed extreme visible. Reservoir Scope **0.7.0 build 9** implements that refinement in the steward's native app. This is a visualization change within S-002, not a reservoir intervention or a new regulator boundary.

## Result and evidence semantics

Recorded fill defaults to **20×**, with **1×, 5×, 10×, 20× and 40×** adjacent buttons and a highlighted selection. Gold High water and blue Low water cards occupy the right side of the lens. Each keeps its measured percentage and first source timestamp. Their curved ticks and leaders use the exact cube-root radius and fixed orthographic projection already used by Metal. Values outside the 54–82% crop remain labeled without a falsely clipped geometry marker.

The recorded range includes every observation from the capture start through the playhead, including rows skipped between redraws. Seeking rebuilds the prefix quietly, and rewinding removes future extrema. Health marks retain all accepted observations since following began in the current source/session, surviving chart-buffer eviction. Activation marks describe only the current batch because the recorder supplies no boot identity. A new, overlapping, advancing batch can highlight a strict new extreme; replacement batches begin quietly. Replacing an evicted batch extremum cannot inherit the old observation's glow.

A strict new record brightens and settles over three monotonic display seconds with a quadratic fade. Equal values retain their original timestamp within the declared range. The first sample initializes both marks quietly; stale reads and repeated polls create no new highlight. Measured values and geometry remain independent of cyan fill easing. Reduce Motion keeps static marks, including when the separate fill-transition override is enabled. The [animation guide](../native/ReservoirScope/docs/ANIMATION-DATA.md#observed-high-and-low-water-marks) gives the source-by-source contract.

## Verification

All **121 targeted checks** pass: 39 watermark model checks, 42 evidence/source/reference/playback checks and 40 offscreen view checks. The [build receipt](../native/ReservoirScope/build-receipt.json) and [validation directory](../native/ReservoirScope/validation/0.7.0/) retain the result and exact packaged source/resource/signature identity. All 19 Swift source files and six resources match the final signed app. Earlier build receipts and profiling scopes remain preserved.

The offscreen harness rendered the actual overlay and extracted production lens projection at 524×300 and 840×469: separated, equal and outside-crop extrema, each at resting and new-record emphasis. It retained 12 final PNGs with source hashes. Visual inspection found and corrected a compact-layout header/card overlap; preliminary images remain under `watermark-view/preview-before-compact-fix/`. Timestamp text was also made more legible. The initial compile error from passing a projection tuple to a CGPoint API was corrected before any successful build; its log is retained.

The final app was opened and visually inspected. Its highlighted speed changed from 20× to 10× and back. At recorded index 5 it showed high 75.44% at 09:09:10 Pacific and low 67.31% at 09:09:01, covering six observations. Rewind to index 0 restored both marks to the initial 67.31% and count one. Independent retained-data expectations come from [the prefix probe](../probes/reference_watermark_expectations.py); the [runtime QA record](../native/ReservoirScope/validation/0.7.0/runtime-qa.json) identifies the displayed build and limits.

Reproduce from the research root:

```sh
native/ReservoirScope/check-fill-watermarks.sh
native/ReservoirScope/check-evidence.sh
native/ReservoirScope/check-watermark-view.sh
python3 probes/reference_watermark_expectations.py
native/ReservoirScope/build-app.sh
python3 native/ReservoirScope/verify-app-identity.py --output native/ReservoirScope/validation/0.7.0/artifact-identity.json
```

The new live-source integration is fixture-tested and independently reviewed; no fresh live feed was attached during this iteration. Brightness endpoints were checked offscreen, with the native window inspected under its existing accessibility preferences. There is no new display-performance, energy or M4 measurement. No being source, live process, prompt or action was changed. The hub's separate selected inquiry remains preserved.

The Hold Shelf card is saved as done, and the dated trace entry was read back after saving. The [publication receipt](../board/reference-watermarks.json) retains the card tag and log title.
