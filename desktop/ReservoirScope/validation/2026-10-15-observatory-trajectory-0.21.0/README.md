# Observatory retained trajectory — 0.21.0

October 15, 2026. This bounded product tranche links the existing signed state surface
to a selectable view of the retained PCA trajectory. It does not change journal
prompt v8, the numerical engine, saves, feedback, source recordings or file formats.
Source checks, the distinct macOS build/archive and scoped native interaction checks
completed. This is agent qualification of one workflow; full Observatory, other-platform
and collaborator acceptance remain open.

## Change and interpretation

The complete 1,024-row state capture provides PC1/PC2, PC1/PC3 and PC2/PC3 views.
Selecting a retained point, a keyboard-adjacent row or an endpoint uses the existing
accepted-frame controller. The surface, projection marker and exact values share
that row. Selection pauses playback; failed and stale reads retain the last accepted
row. The whole capture supplies one equal, signed axis scale for every projection.
The native UI check references [exact original values](ui-reference-values.json).

The projection uses a frozen, retrospectively fitted basis. Its rows have no clock,
measured cadence or paired fill. A line connects retained rows for inspection; it
neither invents an observation nor establishes the intervening path. The independent
507-sample fill recording and its three unsorted sensory direction estimates remain
unchanged. [Reading and rendering contract](../../RECORDED-TRAJECTORY.md).

One SVG is mounted at a time, with memoized geometry and path strings. It adds no
WebGL context or continuous animation timer. The signed surface keeps its existing
renderer. These are implementation bounds, not GPU/power measurements.

## Evidence layers

- [Frontend receipt](frontend-checks-01.json): 393 tests in 42 files and TypeScript
  pass on unchanged sources. The eighteen new checks cover exact complete coverage,
  fixed equal axes, missing/nonfinite/sparse data, gaps, deterministic retained-row
  picking, overlapping points, keyboard boundaries and static accessible markup.
- [Rust receipt](rust-checks-01.json): 219 core and 198 desktop tests passed; two
  opt-in desktop tests remain ignored. Reference/resource checks, formatting and
  strict Clippy for both crates passed. These are new executions on the bound sources.
- [Prior-package preservation](prior-package-preserved-01.json): all 46 app files,
  the 0.20 archive and pinned executable were copied and hash-checked before overwrite.
  The old package and historical qualification remain independently identifiable.
- [Build receipt](package-build-01.json) and [archive verification](archive-check-01.json):
  the locked macOS build passed in 115.6 seconds, with source unchanged during the
  build. The 46-file bundle, archive members and executable pin were verified.
- [Native interaction account](MACOS-UI.md) and [observation receipt](native-ui-01.json):
  pointer selection chose row 389, Right selected 390 and End selected 1023.
  PC2/PC3 retained the row and fixed scale; row 512 matched exact source values.
  Graphics loss/recovery preserved the selected evidence, and navigation paused
  playback at row 548. The app was quit afterward. No model or feed was contacted.
- [Independent final review](FINAL-REVIEW.md) and [post-build comparison](postbuild-source-review-01.json):
  all 128 frontend and 162 Rust qualification inputs remain exact; the 333-file
  build inventory differed only in three named post-build documents. Both new and
  preserved package identities matched. The review's then-pending README wording
  is finalized here; its original bytes and comparison receipt remain untouched.

## Package identity

The Apple-silicon preview is version/build **0.21.0**, bundle identifier
`research.reservoir.scope.tauri`. Its [identity/signing capture](qualification-before-ui-01.json)
records successful local deep/strict signature verification, an **ad hoc** signature
and no TeamIdentifier. This is not notarization, a distribution identity or human
acceptance. That capture's default unexecuted check labels are separate from the
executed frontend, Rust and build receipts linked above.

| Artifact | SHA-256 |
| --- | --- |
| App executable and `target/qa/0.21-pinned/reservoir-scope-desktop` | `c4b51f576063eebb11ac0e754ebfe16e6b92cde4849cf0fa5e94412221130128` |
| `ReservoirScopeTauriPreview-0.21.0-macos-arm64.tar.gz` | `33409bd66ed9e059097038d8dc8cb36c560607ce2141e5c9dcc344565b5ccd0f` |

The app and archive are under `target/release/bundle/macos/`. The independently
preserved 0.20 full app, archive and pin remain under `target/qa/0.21-prior-0.20-preserved/`;
the original 0.20 archive and pin also remain exact.

## Remaining scope

This is one Observatory inspection workflow, not completed M3 parity. Reference-field
magnitude/deviation/reconstruction/residual controls, full-capture state-spectrum
inspection, broader accessibility and other-platform visual checks remain. The
current package still needs measured GPU/power/contention and long-duration work.
The native resize attempt did not visibly change the window, so compact layout is
not qualified here. PC1/PC3, exact overlap picking and broader keyboard/screen-reader
coverage remain separate. Projection choice resets on workspace remount while the
accepted row stays retained. Minimize/Raise preserved that row but was not a measured
minimized-duration or GPU-suppression test. Historical save/export/recovery checks
were not repeated by this presentation-only tranche.

The separate diagnostic memory-policy change and source-role comparison have their
own [attempt](../2026-10-15-context-sources-03/README.md). They do not alter the
production writing prompt or turn diagnostic replies into saved app journals.
