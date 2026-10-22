# 0.35.0 — Difference-signal channel

**Unqualified local source candidate, October 21, 2026, on top of 0.34.0.** The
self-observation spec's M5, built for [S-011](../../research/studies/S-011-self-observation-stack.md)
after a planning pass with Mike: the reservoir receives a small, gain-limited signal of its
own recent motion. Nothing is shown to the model; the channel is numerical, and every
model arm that uses it runs beside an identical arm without it.

## What changed

- Six optional specification fields, default off: `differenceGain` (0; −1..1, sign selects
  ±W_d), `differenceTau` (3), `differenceDeadBand` (0.02), `differenceClip` (0.2),
  `differenceWatchdog` (true), `differenceWatchdogFillStd` (10). Omitted, the request,
  checkpoint, frame and identity bytes are exactly 0.34.0's; a test replays a segment
  recorded by the 0.34.0 binary (`tests/fixtures/sustained-prompts/v34-gain-zero-segment.json`).
- Pipeline per step with a nonzero gain: `d_raw = (x[t] − x_look)/(t − t_look)` from the
  state at the last observation step (zero before the first), `d_f += (d_raw − d_f)/(τ+1)`,
  per-coordinate dead band, projection by a fixed seeded 48×32 Gaussian matrix
  (`difference_matrix`, seed ^ `DIFFERENCE_SEED`), gain, clip, `−0.0` normalised; added into
  `input[18..66)` after the scaled held vector, before both the reservoir and the field step.
  The entry-effect counterfactual keeps the channel on both sides.
- Evidence: frame `differenceInput` (48) and `differenceGainUsed`; continuation
  `differenceFiltered`, `differenceReference` and step, `differenceFillWindow`, two counters,
  `differenceGainDropped`; `validate_state` recomputes the contribution from the stored
  filtered vector and checks the reference against the last observation. Mechanism
  identities `…-codec48-…-difference-v4` and `…-embedding32-…-difference-v4`.
- Watchdog, pure helpers `difference_watchdog_update`/`difference_watchdog_verdict`: trailing
  90-step fill standard deviation above the bound; fill outside 15–98% for 60 steps; more
  than half the nodes beyond |x| > 0.95 for 30 steps. On trigger the gain is 0 for the rest
  of the session and the drop is recorded on the frame and the continuation.
- Found on the first ladder twins (S-011, October 21): with regulation on, the fill's
  start-up climb alone gives a trailing-90-step standard deviation of 14.6–16.9 in the window
  ending at step 90, above the default bound of 10, so a nonzero gain with the defaults is
  dropped at step 90 before the channel has done anything. Set `differenceWatchdogFillStd`
  above the start-up value (the ladder uses 34) until a versioned warm-up lands in 0.36.0.
  The shipped dead band 0.02 is below the gain-0 motion floor (RMS 0.050–0.055 per
  coordinate), where the spec's rule gives about 0.105.
- Tauri config carries the fields to the specification and the manifest; Advanced settings
  gain a "Difference signal (research)" group with its explanation. Version 0.35.0.

## Checks run on this source

| Check | Result |
|---|---|
| `cargo test --locked -p reservoir-core` | 257 tests pass, including `tests/sustained_difference_channel.rs` (7) and the 0.34.0 witness replay |
| `cargo test --locked -p reservoir-scope-desktop` | 261 pass, 3 ignored, 0 fail |
| `npm test` | 59 files, 505 tests pass |
| `npm run build` | TypeScript and Vite pass |
| `cargo fmt --check`, `cargo clippy --workspace --all-targets` | clean |
| macOS package | not attempted; see the 0.28.0 record |

Results of the numerical ladder and the arms belong to S-011's dated account. No human
acceptance, platform qualification or writing result is claimed.
