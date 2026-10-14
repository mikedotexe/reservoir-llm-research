# Preview 0.5.1 — packaged macOS checks

October 12, 2026, after the user's unlock/retry. Agent-operated checks on macOS
27.0.1 arm64, in the actual packaged WebView at a 1280 × 860 window. These are not
collaborator/steward acceptance or minimum-OS qualification. Candidate identities are
bound by `qualification.json`, `archive-check.json` and `selected-case-dialog-proof.json`.
Binary SHA-256: `f94545553fbd4122ab6d505210b6d0ab0c5639ea6d96154188fd1eecb7042d46`.

## Recorded evidence and repaired layout

- The header identified 0.5.1. Entering Observatory showed explicit opening with no
  playback. Opening retained recordings yielded 507 history rows and 1,024 state
  rows, separately labeled and navigated.
- First historical fill was 67.31251478%, radius 0.8763924052334318, UTC label
  2026-09-06T16:09:01.158Z, elapsed zero, session 5316. Initial interval and backward
  fill difference were unavailable. Sensory slots retained 4.72739172, 3.07596111,
  1.20072341; the ESN-state covariance lambda1 remained a separate 19.45121193.
- Screenshots confirmed readable UTC/measurement columns, fill exact-value columns
  and geometry summaries. The 0.5 nested-grid defect was repaired; no source values
  were changed. Reference zones and their interpretation limits remained visible.
- Clocked playback advanced from row 0 through row 5. Pause held row 7 at elapsed
  16.55498743 seconds. Exact-values mode showed its explicit fallback and retained
  row/value data; returning to 3D rebuilt a usable view.
- State row 0 / coordinate 0 displayed 0.35750484466552734. Pasting 1023 into the row
  field selected the final row, disabled Play/Next, and selecting coordinate 127
  displayed -0.14477211236953735 with a fixed -1…+1 ordinal history plot. There was no
  invented per-row timestamp or paired fill.
- Surface picking selected coordinate 45; keyboard Right orbited, and Reset camera
  restored the whole surface. The signed scale and exact values remained available.
- State playback started at row 10, then navigation to Research cases stopped it.
  After export/reopen tasks, Observatory returned paused at row 31 with coordinate
  45 retained. A later observation still showed row 31.

## Graphics observations and limits

- Offscreen fill view initially reported zero draws. Entering view produced one.
  Repeated idle observations retained the count; this demonstrates the displayed
  event-driven behavior only, not GPU utilization, power consumption or 30-fps acceptance.
- Explicit fill context loss displayed its loss/fallback state while exact values
  remained available. Restore requested while offscreen completed when the canvas
  returned to view, with the draw count moving from one to two.
- Explicit state-surface context loss likewise retained exact values/selection, and
  Restore returned WebGL2 ready, moving from one to two draws. Selection remained
  coordinate 45 at row 31.
- A window-corner drag did not change the observed window dimensions. Consequently
  compact-window/resize qualification is not claimed from that attempt. Smaller
  effective areas, text enlargement, screen readers, GPU/power/memory measurements
  and broader lifecycle stress remain open.

## Library and native dialogs

- Library opened without Refresh. Searching controller showed both the bundled
  regulation record and the retained managed import with enabled Verify & open.
  Opening the bundled record completed numerical verification and displayed the
  600-frame baseline sensory-field track at step 1, with its explicit absence of a
  reservoir-state vector or language model. The preceding 0.5 supplement separately
  records the initial 0.4-to-0.5 catalog repair and preserved recent-access entry.
- Loaded the reviewed catalog and explicitly chose “A journal-led repair, with
  natural benefit still unobserved” (`annotation-repair-20260907`). Native Save wrote
  `target/qa/0.5.1-selected-case-export.json`; the UI identified it as a new one-case
  catalog and retained the original catalog/hash.
- Export SHA-256: `087f45ad6e4a6ecee1d94318838b280ec5f49df3501be675d3043d316305d4ce`.
  Original catalog SHA-256:
  `3998951c6eaa4f414ff7ce0cef643f19078001e47c980be521255175743d0652`.
- Cancelling a second native Save kept the same selected case and catalog. Native
  Open then reopened the exported derivative, verified its embedded hashes and
  references and displayed its external origin, one case and identical export hash.
- Independent unchanged Swift and Rust both accepted that exact dialog-created file.
  It equaled native construction of the selected bundled case, including all six
  materials, four claims and four sequence entries. See `selected-case-dialog-proof.json`.

## Basic lifecycle and remaining gates

Command-Q was followed by a successful fresh launch of 0.5.1. Observatory again
required explicit opening and did not restore playback. It was reopened for review
and left paused at the first fill sample.

No model, live feed or Being service was contacted or changed. No pending-write,
crash-recovery or long-session behavior is inferred from these read-only/review flows.
Windows 11, Ubuntu 24.04, minimum macOS 14, clean-machine installation, full
accessibility, measured performance and collaborator acceptance remain unexecuted.
