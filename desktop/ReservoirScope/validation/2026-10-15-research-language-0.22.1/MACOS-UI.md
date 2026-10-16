# Native inspection — 0.22.1

Inspected the actual archive-bound macOS app through the native desktop-control
interface on October 15, 2026. This is agent inspection, not collaborator acceptance.
The launch and close receipts bind owned PID 82443 and its isolated QA Library.
The pre-existing native macOS Reservoir Scope app was not selected or changed.

## Observed

- App chrome shows Reservoir Scope and About this preview. The misleading global
  My reservoir badge and cross-platform slogan/footer are absent.
- About initially shows Preview 0.22.1, separate app storage and remaining platform
  qualification. Technical checks are closed. Opening them loads the exact 32- and
  128-coordinate reference scenes, both 3D-ready, and identifies macos/aarch64,
  0.22.1 and matching bundled hashes. Closing About removes those diagnostics.
- Guided tour, Research cases, Geometry bookmarks, Observatory and Library have
  the revised headings. Cases/geometry entry controls and their temporary-viewing
  meaning remain visible. Those files were not imported or exported in this check.
- The Observatory welcome screen was visually inspected at 1280×860. Independent
  recordings, missing state timestamps/paired fill and optional exact-value mode
  remain clear. No clipped title or overlapping control was observed at this size.
- Experiment subtabs read Library, Recording, My reservoir and New experiment.
  Recording/New experiment entry screens display the matching headings. No finite
  experiment was started. Library displays 22 included records and explicitly says
  the managed-file scan is incomplete; it does not imply complete coverage.
- My reservoir starts with Offline example writing and closed Advanced settings.
  The only configuration change was Maximum numerical steps: 10800 → 31. Cadence
  stayed 30, pace 1000 ms, seed 20260909 and all other defaults remained unchanged.
  Create displayed Ready · not started at live/saved step 0. Start was separate.
- The run reached its cap, showing Run limit reached, live step 31, saved through
  step 31, one saved journal, and 31 seconds displayed running time. This is a
  short scripted check, not real-model writing or endurance evidence. The cap held
  execution automatically; no manual Pause behavior was requalified.
- Journal showed the full synthetic text, Saved · feedback applied, observed step
  30 and first application at step 31. Recorded measurements and Evidence started
  closed. Opening Evidence exposed reservoir-journal-v8, no configured model,
  requestStarted=false, prompt, save/readback identity and application evidence.
  The script's prose is unchanged and is not evidence of model voice or continuity.
- Surface graphics counters were absent from the primary view and Graphics
  diagnostics remained closed. The counter's location inside that disclosure was
  source-reviewed; its expanded rendering was not rechecked natively. Context-loss
  behavior/performance was not retested.
- Native Cmd+Q ended the owned app without a discard prompt after the saved capped
  run. PID absence was independently checked; stdout/stderr were empty. Ten files
  in the isolated Library are retained and hashed in ui-close-01.json.

The app inherited its existing guide reading preference (lesson H); the QA Library
is isolated storage, not a claim that every WebView preference was reset. This run
left the scripted QA files intact. It contacted no model provider or live feed.

## Limits

No fresh real-model session, save-failure injection, new native export/recovery
interchange test, compact-window resize, screen-reader acceptance, resource capture,
Windows or Linux check was performed. Existing behavioral tests cover save/error,
readiness and historical evidence presentation; these are separate from this UI pass.
Remaining setup repetition and technical source labels can be reviewed with the
broader navigation/compact-layout task, without changing scientific meanings.
