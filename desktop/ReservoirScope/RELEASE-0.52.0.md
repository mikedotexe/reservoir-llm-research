# 0.52.0 · Journal-first desktop workspace

Local UI development on `codex/journal-desktop-ui`, based on the 0.51.0
implementation and three-model startup checkpoint `431db82`. Mike requested a
more efficient layout, stable journal reading, clearer small fill changes and
less explanatory content in the everyday view.

## Reading and controls

The journal leads the running workspace. Its article stays mounted in a fixed
reading pane while a new entry loads. Routine loading messages occupy an
existing status slot instead of inserting rows above the prose. Scrolling into
the entry, selecting text or interacting with its evidence holds the entry;
later arrivals appear on Follow latest. Explicitly following again returns the
reader to the top and loads the newest entry. Holding a reading never pauses
the reservoir. The initial empty state also reserves the navigation space.

Status, transport and live measurements occupy separate cards on the right,
without a dividing sidebar. At 1000 CSS pixels and below, Session controls opens
the same controls as a floating panel. Escape from the panel closes it and
returns focus to its button. Folder, refresh, previous/next, start/resume and
pause use icons with accessible labels and tooltips; stop retains its descriptive
label, including Cancel request and stop when a request is active.

Scheduled outcomes start expanded. Journal history, exploration details and
session settings/export/recovery remain available in disclosures. Existing
recovery warnings and explicit operations are preserved. The application header
is one compact row. About remains in the existing native macOS application menu
(Help on other platforms); its duplicate page button is removed. Technical
diagnostics remain at the bottom of the app.

## Fill display

My reservoir now uses an SVG quadrant cross-section, retaining the original
spherical volume encoding: radius is the cube root of fill/100. A separate,
explicitly labelled 10× linear ruler covers a 10-percentage-point window to
make smaller changes visible. The window recentres in 5-point increments and
its endpoints are always shown. Exact percentage, provenance and position stay
in Measurement details. Invalid or missing values are not rendered as zero.
No extra smoothing, inferred topology or new measurements are introduced.
Other workspaces retain their original sphere display.

## Qualification and scope

- Frontend: 614 passed, one pre-existing skipped; TypeScript and production Vite
  build passed. New numerical display checks cover bounds, zero/missing/invalid
  values, exact provenance and retained volume scaling.
- Interactive synthetic fixture at 1280×860 and 720×860: automatic following
  retained article and pane identity without moving page/pane offsets. Scrolling
  held the selected entry; an arrival left page scroll at 131 and reader scroll
  at 560, with a new-entry indicator. Explicit Follow latest loaded the newest
  entry. Compact controls and keyboard dismissal worked; no horizontal overflow
  was observed at the compact width.
- A distinct ad-hoc signed native app, `research.reservoir.scope.journal-preview`,
  builds at 0.52.0. Its preview store is a byte-verified copy of the stopped Gemma
  compact-scanner session, separate from both originals and running sessions.
  Native verification and paused restoration passed: 31 entries, saved through
  step 930, with entry 31 at step 900 visible in the journal-first layout. The
  preview remains paused; its retained writing-attention boundary was not retried
  or skipped, and no model request was started.
  Private build, store and UI qualification receipts are under
  `research/outputs/journal-ui-20261115/`.

The synthetic fixture is repeatable through Vite at
`validation/2026-11-15-journal-ui/preview.html`; it makes no model calls or store
writes. Its manual append button measures rendered offsets and DOM identity.
Native inspection uses real saved history. Numerical dynamics, prompts, session
contracts, persistence and request scheduling are unchanged; no new backend
behavior is claimed. The ongoing three-model 0.51.0 runs keep their existing
binaries and settings. This preview is not a published sharing release.
