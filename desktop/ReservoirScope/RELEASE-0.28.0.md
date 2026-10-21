# 0.28.0 — Field noise and feedback scale for My reservoir

**Unqualified local source candidate, October 21, 2026.** Two numerical settings are
added to sustained sessions so that retention regulation can reach its 64–72% fill
band. Historical sessions, the earlier mechanism and every other workspace are unchanged.

## Why

The first laptop session with `mistral-small:24b` (38 entries, about 800 steps) held
sensory fill near 12–15% with retention pinned at its 0.995 rail. An offline replay
that reproduces the recorded fill to four decimals shows the cause is structural: the
field receives sixteen forcing channels for twelve steps in thirty plus one constant
text vector, which spans about twelve of its 32 modes, so the controller has nothing
to regulate. Removing the text vector entirely only reaches the mid thirties. Uniform
noise on the field inputs with the text vector scaled down settled fill inside the
band with retention near 0.955. The [dated account](../../analyses/2026-10-21-laptop-first-sustained-session.md)
and `probes/desktop_fill_replay.py` hold the tables.

## What changed

- `SustainedSpecification` gains `sensoryNoiseAmplitude` (0–1, legacy 0) and
  `feedbackScale` (0–2, legacy 1). Legacy values serialize as omitted fields, so old
  manifests, checkpoints and their typed hashes are byte-for-byte unchanged and keep
  mechanism `essentials32-splitmix64-codec48-held-feedback-v1`. Any other values
  identify `essentials32-splitmix64-codec48-scaled-feedback-field-noise-v2`.
- Each step under v2 adds uniform noise to all 66 field inputs from a SplitMix64
  stream seeded by `seed ^ FIELD_NOISE_SEED` and indexed by step (draws 66t+1..66t+66),
  so checkpoints carry no extra RNG state and the 32-draw reservoir accounting is
  untouched. The frame records the exact field noise (`sensoryNoise`, omitted under v1);
  continuation validation recomputes it and the scaled input, and rejects tampering.
- The held vector is multiplied by the feedback scale as it enters the reservoir and
  the field; the stored held vector stays unscaled.
- Fresh sessions default to noise 0.5 and scale 0.4, which replay settles near 70% fill
  with the controller resting inside its band; 0.4/0.5 settled at the band's lower edge. Both appear under Advanced
  settings → Numerical settings with range validation; Create is gated on valid values.
- Version 0.28.0 in `package.json`, `tauri.conf.json` and `src-tauri/Cargo.toml`.

## Checks run on this source

| Check | Result |
|---|---|
| `cargo test --locked -p reservoir-core` | 237 tests across 28 suites pass, including the new file below |
| `tests/sustained_field_noise.rs` (new) | 5 tests: legacy serialization and mechanism identity, deterministic non-overlapping noise, scaled input and tamper rejection, restored continuation equals uninterrupted, 420-step comparison (legacy 15.59% fill at retention 0.995; v2 69.78% at 0.955) |
| `cargo test --locked -p reservoir-scope-desktop` | 254 pass, 2 ignored, 0 fail (existing config literals accept the new fields through serde defaults) |
| `npm test` | 54 files, 499 tests pass (two new) |
| `npm run build` | TypeScript and Vite pass |
| macOS package | **not produced**: `tauri build` fails on this host because the release profile's thin LTO yields proc-macro dylibs that macOS 27.0.1 refuses to load ("mis-aligned LINKEDIT string pool", seen for `serde_derive`, `phf_macros`, `zerofrom_derive`); the same failure occurs with and without `--target`. This is toolchain behaviour (Rust 1.94.1 on this Xcode), not a change in this source. The debug `tauri dev` build runs. |

## First live session on this source

A fresh session with `mistral-small:24b` and the defaults reached the band on the
laptop: fill 87.2% at step 30 (the initial-covariance transient), 56.9% at step 60
after the first feedback, 64.8% at 90, 69.0% at 120 and 69.7% at 150, with retention
resting at 0.955 from step 100 on and spectral entropy of the top eight modes staying
near 0.85–0.91 instead of collapsing to 0.2. The offline replay had predicted 59, 66,
69 and 70 at those steps. Sentence-level repetition between consecutive entries still
rose (0.35, 0.52, 0.81), as expected with temperature zero and the full previous entry
returned; the band fixes the field, not the decoding.

No human acceptance, platform qualification or writing result is claimed. Whether
the settled band changes what a model writes is the next observation, not a result.
