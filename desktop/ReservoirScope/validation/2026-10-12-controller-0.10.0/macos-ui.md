# 0.10.0 packaged Mac walkthrough

Executed October 12, 2026 (America/Los_Angeles; receipt timestamps use UTC), using
Codex native desktop control on macOS 27.0.1 arm64. This is agent UI observation,
separate from automated checks and collaborator acceptance. The exact ad-hoc-signed
package identity is in `package-before-ui.json`; production code had no test driver.
No model service, selected live feed or Being workspace was accessed.

## Observed behavior

- Launch shows version 0.10.0. Fresh experiments initially has no accepted session.
  Choosing **Controller study · two sensory fields** exposes the fixed 600-step study
  and removes editable reservoir/language parameters. Creation stays at step zero.
- Step once produces aligned field observations at step 1 / simulated time 1/3.
  Both fills are 10%; baseline retention stays 0.955 and regulated next retention is
  0.965. There are no reservoir surfaces, language turns or journal controls.
- Save to Library and portable export are disabled at step 1. Native Save creates
  `controller-progress-step1.json` in the isolated repository QA folder. It retains
  exactly that manual step, durable step zero, no record hash and no numerical frames.
- Stop preserves step 1 and disables further stepping/running. Cmd-Q opens unsaved
  review with Return, progress export and explicit discard choices; portable saving
  cannot bypass the format. Return leaves stopped evidence intact. Explicit reset
  records discard of that test prefix and creates a distinct session at step zero.
- Run reaches exactly 600 paired observations. The two spheres visibly render at
  the 1280 × 860 window size. Baseline fill is 80.69282004938178%; regulated fill is
  72.58776996999816%. Each has provenance, exact values, used retention and next
  retention. The full target-error window is 300 samples, with mean absolute errors
  11.924755885049205 and 4.159937143601519 percentage points respectively.
- Both renderers reached 125 reported draw calls during this run; subsequent idle
  observations retained that count. This is a UI counter observation, **not a GPU,
  frame-rate, latency, memory or battery measurement**. Deliberately losing the
  baseline context retains values and leaves the other field intact. Restore followed
  by scrolling the affected scene into view redraws it (126 calls). Offscreen rendering
  remains suspended. The exact-values toggle releases both graphics contexts.
- Historical keyboard inspection checks steps 300, 301, 599 and 600. Step 300 hides
  target-error evidence; the following cursors show respectively 1, 299 and 300
  evaluation samples. Rewinding does not retain a future completion label. Explicit
  detail reads through step 300 show a 300-point prefix, blank future extent, fixed
  fill/retention scales, dashed baseline versus solid regulated lines, and selectable
  rows of the shared 32 × 66 projection matrix.
- Native Save creates `controller-complete-600.json`. Save to Library confirms success;
  searching `controller` finds its **Created here** entry. Verify & open checks it and
  shows the separate recorded controller reader with 600 frames and verification passed.
- Cmd-Q after Library saving exits cleanly (process absence checked). Relaunch has no
  active fresh session. Recovery lists the discarded step-1 metadata and completed
  step-600 record separately. Partial recovery clearly says it has no numerical frames
  or resumable state and disables portable export. Complete recovery exports through
  native Save as `controller-recovered-600.json`, byte-identical to the earlier export.

Partial session: `session-1791869358308-95766-1`.
Complete session: `session-1791869451164-95766-2`.
Actual exports are under `target/qa/0.10-ui/`; their hashes and assertions are retained
in `recovery-export-equality.json`. Independent unchanged Swift/current Rust checks of
the actual complete dialog export, one-ULP corruption rejection and native prefix
agreement are in `packaged-export-conformance.json`.

## Limits and observations not promoted into qualification

The automation attempted Pause during the running UI, but the control tool rejected
its stale UI reference; the run completed before a refreshed click. Packaged Pause is
therefore not claimed by this account. Automated scheduler/pause/replacement checks
pass separately. Request-order disclosure is covered by desktop/frontend tests, not
a new packaged action-pair walkthrough in this tranche. No forced crash, power loss,
minimized long-running session, OS sleep, physical disk-full condition, minimum-macOS
installation, screen reader, Windows/Linux execution, measured GPU efficiency or
human acceptance was performed. Existing native and historical preview receipts remain
unchanged. This finite synthetic study is not a model connection or sustained journal loop.
