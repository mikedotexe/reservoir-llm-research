# Observatory reference fields and state spectrum — 0.22.0

October 15, 2026. This tranche adds magnitude, deviation, reconstruction and residual
inspection to the retained state surface, plus its complete 128-value sample
covariance spectrum. The state row, coordinate, field, reconstruction modes and
trajectory projection remain linked. Field/mode/projection preferences now survive
workspace navigation within the running application.

Source checks, the distinct macOS package, scoped native interaction and a bounded
main-process resource measurement completed. Full Observatory, other-platform and
collaborator acceptance remain open.

Production journal prompt v8, the reservoir experiment engine, saves, feedback,
portable formats and original recordings remain unchanged. No model, live feed or
Being service is part of this qualification.

## Meaning and implementation

Rust owns the field calculations. Original Float32 activations are promoted to
double precision; the frozen full-capture mean and retained components supply
deviation, ordered scores, centered reconstruction and residual. Reconstruction
does not add the mean back. Four UI choices cover PC1, PC2, PC3 and all three.
Fixed ranges are signed activation ±1, magnitude 0–1 and derived fields ±2; exact
values remain unclipped. The selected raw activation stays visible beside the
chosen field. Missing reference data is unavailable, never a zero measurement.

The 128 eigenvalues describe the retrospectively fitted whole-capture state sample
covariance, with denominator 1,023. Only three component vectors were retained.
The whole-capture variance share, a selected row's reconstructed squared deviation,
and the independent sensory-direction/fill history remain distinct. This is no
new clock, full-phase-space picture, causal attribution or live measurement.

The spectrum uses a static SVG and a closed exact-value table. Field selection
reuses the existing surface renderer; no new WebGL context or continuous timer is
added. See [the reading contract](../../RECORDED-STATE-FIELDS.md) and
[backend contract](../../crates/reservoir-core/OBSERVATORY.md).

## Executed preparation and source checks

- [Independent Swift oracle](native-field-oracle-01.json): unchanged native
  `StateSurface.swift` supplies seven cases and all eight mode subsets, including
  synthetic offset/range/sign cases and four actual retained rows. All 56 selections
  pass the focused Rust comparison. Its source/provenance and generator are retained.
- [Focused Rust checks](field-checks-02.json): 12 core and 7 desktop checks pass.
  The initial compiler errors are retained in `field-checks-01.json`; corrected
  iterator references were tested in attempt 02.
- [Frontend checks](frontend-checks-02.json): 413 tests in 45 files plus TypeScript
  pass with unchanged sources. Attempt 01 stopped before testing because a copied
  Node path named an absent version; its receipt is preserved alongside the helper
  correction. New checks cover exact backend vectors, fixed range/missingness,
  mode selection, row-energy meaning, spectrum validity and navigation preferences.
- [Full Rust checks](rust-checks-01.json): 224 core and 199 desktop tests pass,
  with two existing opt-in desktop tests ignored. Reference/resource checks,
  formatting and strict all-target Clippy for both crates pass on unchanged sources.
- [Sampler checks](sampler-checks-01.json): ten synthetic tests pass. These exercise
  the measurement helper, not actual app resource use.
- [Prior package preservation](prior-package-preserved-01.json): the complete 0.21
  app, archive and verifier pin were copied and checked byte-for-byte under
  `target/qa/0.22-prior-0.21-preserved`. Prior receipts remain unchanged.

## Package and native checks

The [locked build](package-build-01.json) passed in 133.4 seconds on unchanged
sources. [Archive verification](archive-check-01.json) binds all 46 app files,
the independent executable pin and the archive. The prior full app and original
archive/pin remain exact. Version/build is **0.22.0**, with application identity
`research.reservoir.scope.tauri`. [Signature capture](qualification-before-ui-01.json)
records verified local signing; it is an ad hoc signature, not notarization or
public distribution acceptance.

| Artifact | SHA-256 |
| --- | --- |
| Executable and `target/qa/0.22-pinned/reservoir-scope-desktop` | `788b636ec898f9863e146e7dfe67c380910ae38943b0b178f6e22b8e8d794051` |
| `ReservoirScopeTauriPreview-0.22.0-macos-arm64.tar.gz` | `9d4359f695289c24a0fefc7949ae731354cea29b83cced4eb953640307ce48d2` |

[Native observations](MACOS-UI.md) and the [functional receipt](ui-functional-01.json)
record exact fields at rows 0 and 511, fixed scales, spectrum provenance, context
loss/restore and exact-value mode. Navigation preserved row 511, PC1 residual and
PC2/PC3 axes. The resize gesture did not alter the window size; compact layout is
still unqualified. This is scoped agent UI inspection, not human acceptance.
The [reporting correction](ui-functional-correction-01.json) corrects an undercount
of recovered input-guard refresh requests from one to two; the original receipt is retained.

## Bounded resource observation and cleanup

The [frozen measurement](measurement-freeze-01.json) completed 121 samples over its
600-second bound, with no sampler or analysis errors. [Analysis](main-process-analysis-01.json)
uses only intervals wholly inside the four declared windows. Main-process CPU was
approximately 0.00451% paused, 3.04087% during playback, 0.00247% minimized and
0.00285% restored-paused, where 100% is one core. See
[the complete resource account](RESOURCE-RESULTS.md) for interval coverage, RSS,
limits and [independent review](FINAL-RESOURCE-REVIEW.md).

The [native boundary witnesses](resource-ui-witnesses-01.json) retained one draw
before/after the first idle window and 605 before/after restored idle. The app
returned paused at row 603. Playback-start rows were not sampled synchronously
with phase markers; before/after witnesses include transitions and cannot establish
a settled-window frame rate. No UI queries occurred inside the minimized window.
Minimized playback is paused, a different workload from active playback.

[Cleanup](ui-cleanup-01.json) confirms normal Command-Q exit, the exact owned PID
absent, unchanged executable and empty stdout/stderr. No other process was stopped.
The [final source/package comparison](postbuild-source-review-01.json) confirms all
134 frontend and 164 Rust check inputs remain exact, as do the 46 app files,
archive, executable pin and preserved prior package. Only three current-status
Markdown documents changed inside the 343-file build inventory after packaging;
the updated root roadmap is identified separately.
The [prospective plan](QUALIFICATION-PLAN.md) and [resource protocol](RESOURCE-PROTOCOL.md)
remain distinct from executed receipts.

## Boundaries

This is a bounded Observatory tranche, not complete M3 or collaborator acceptance.
Remaining native drawing controls, compact layouts, accessibility and platform
workflows still need their own checks. A short main-process sample cannot establish
total WebKit/GPU memory or CPU, graphics efficiency, energy, frame pacing, thermals
or long-run reliability. Historical save/export/recovery and writing evidence stays
bound to its original builds; this tranche does not requalify it by inheritance.
