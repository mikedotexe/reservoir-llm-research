# Direct personal sessions and one preparation-history reader — 0.23.0

This tranche makes My reservoir the initial, direct destination while retaining
all five original research destinations. Preparation history has one canonical
reader in Observatory; the Library links to it. Setup guidance is shorter without
changing numerical, source, persistence, prompt or run-limit contracts.

Current-source checks, the distinct package and scoped native navigation checks
passed. Production prompt remains `reservoir-journal-v8`; no provider,
model service, selected feed or Being system is used by this tranche.

## Changes and reading continuity

Workspace owners remain mounted. Navigation never calls Create, Start or Pause.
The preparation controller retains the selected report and invalidates late reads;
its visited view stays hidden while inactive so disclosures also survive return.
Observatory subviews now have their own document-scroll positions. The Library
retains its result scroll for an unchanged query, resetting for changed filters.
Cross-workspace shortcuts move keyboard focus to the workspace without forcing a
second scroll. Explicitly opening a new recording resets that reader position.

## Checks executed

- Full current frontend: **417 tests in 46 files**, TypeScript/Vite and frozen
  reference checks passed in [frontend-checks-01.json](frontend-checks-01.json).
- The new regressions cover a selected retry across leave/return without extra
  reads, and pinned journal text while inactive numerical updates arrive. Startup
  shell and direct preparation-route rendering checks supplement existing tests.
- A first draft startup test used the wrong API export, then exposed three readers
  without server-render snapshots. The isolated shell test now stubs those browser
  readers; it does not claim mounted native navigation coverage. The corrected
  focused check and full current suite pass.
- The preserved source snapshot initially doubled matching focused tests (84/4
  instead of 43/2). Vitest now explicitly excludes `target/**`; evidence copies
  remain byte-exact. Only the clean current-source 417/46 count is qualification.
- Prior Rust qualification is reused only after exact comparison of all 164 inputs,
  allowing the five application-version metadata substitutions. No Rust logic or
  prompt changed; these are not rerun Rust results.

## Actual package and UI

The 46-file macOS package built successfully, and its local ad hoc signature
verified. It is not notarized. [archive-check-01.json](archive-check-01.json) owns
full package/archive/pinned-executable identities; the app and prior source were
unchanged during the build. The executable SHA-256 is
`7b8245932cae928b069fe4ca6609597f94ad3a54dbd8a0082c30a505c26a024b`;
the archive SHA-256 is
`9862d89a0901cd86e6dc734afc6346a5164e09aef8a93edbfdc180afaed39c7c`.

[The native walkthrough](MACOS-UI.md) checked the direct entry, one history reader,
retained report/disclosure/scroll, verified retry opening, Library list position,
and a running scripted session across workspace visits. The 61-step run saved two
journals and applied them at 31/61. A pinned older entry remained selected as the
second arrived; Later entry opened it. Normal quit and exact owned-PID absence
passed. Same-build headless replay passed with all 13 session files unchanged.
Native export/recovery and real-model writing were not rerun.

## Preservation

The exact 0.22.1 app (46 files), archive and pinned executable were copied before
edits, together with all 344 inventoried source files and the root roadmap.
[prior-package-preserved-01.json](prior-package-preserved-01.json) records all 345
source/roadmap copies and hashes. Ignored package/source snapshots and the new QA
Library remain on disk. No prior receipt is relabeled as a current result.

## Closeout

[postbuild-review-01.json](postbuild-review-01.json) checks current qualified inputs,
package/archive/pin identity, all preserved 0.22.1 copies, local documentation links
and owned-app closure. The only source-inventory differences after the build are
four named living Markdown files; the root roadmap is tracked separately. These
documentation edits do not change packaged bytes or inherit new platform acceptance.

## Remaining boundary

Compact layouts, broader keyboard/screen-reader acceptance, attributed WebKit/GPU
resource measurement, current-build endurance, Windows/Linux and collaborator
usability remain separate work. Navigation simplification adds no new model-writing
or scientific-benefit claim.
