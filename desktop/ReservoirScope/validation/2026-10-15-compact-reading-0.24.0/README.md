# Compact reading and native zoom — 0.24.0

Executed October 15, 2026 local time (October 16 UTC). This tranche improves reading
while a session writes, exposes native interface zoom, and fixes compact-layout
rules. Production `reservoir-journal-v8`, numerical behavior, provider transport and
saved-record formats remain unchanged. This is not a new writing experiment.

## Changes and source checks

History windows now anchor to an accepted saved-entry identity, hash and chronological
position. Older/Newer overlap one boundary row; at most one offset correction handles
arrivals. The selected journal retains its own ordinal outside the displayed window.
Late reads cannot replace a pinned entry or a newer explicit Follow latest intent.
Failed adjacent reads preserve both the previous page and prose.

Seven bounded Evidence regions are keyboard-focusable and named. The skip link stays
above sticky navigation; focus rings remain visible. Library metadata rows use the
intended label/value layout. History and Library heights respond to the viewport,
and the Observatory compact breakpoint includes the configured minimum width.
Native View → Zoom In / Zoom Out / Actual Size controls scale the main webview from
75% to 200%, in 25-point increments, with platform shortcuts. Zoom is process-local;
no saved scientific values or preferences change.

- [Full frontend checks](frontend-checks-01.json): **427 tests in 46 files**, plus
  TypeScript/Vite and frozen-reference checks.
- [Fresh Rust qualification](rust-checks-01.json): **224 core and 203 desktop tests**,
  with **two opt-in desktop tests ignored**; format, resource and both strict Clippy
  checks pass. These are rerun results, not prior-build test reuse.
- [Package/build](package-build-01.json), [archive identity](archive-check-01.json)
  and [pre-UI qualification](qualification-before-ui-01.json) bind the distinct
  **46-file macOS Apple-silicon package** and local ad hoc signature.
- Independent file-only reviews found no further controller/zoom blocker. Passing
  source checks and agent review do not substitute for collaborator acceptance.

## Native results and limits

[MACOS-UI.md](MACOS-UI.md) records the actual interactions. The bounded offline
session created 36 journals and held at live/saved step 361. Pinning, refresh,
Older/Newer history, crossing a full twenty-row boundary, workspace return and
explicit Follow latest all worked while new entries arrived. Keyboard focus,
Evidence Page Down, menu/keyboard zoom and reset were observed in the packaged app.

The **0.24 window was 1830 × 1050** after native maximization. The preserved 0.23
baseline reached 900 × 860, but repeated resize gestures did not establish smaller
0.24 geometry. Therefore **900 × 700 and 720 × 600 acceptance remain open**.
A 200% zoom observation is recorded separately from native-window dimensions.
No screen-reader, collaborator, minimum-OS or Windows/Linux acceptance is claimed.

No real model, readiness request, selected live input or Being system was accessed.
This short synthetic run does not measure GPU/power, whole-app resources or endurance.
Native export and restore dialogs were not repeated. Broader attributed resource
measurements and the outstanding compact-window checks are the next bounded work.

## Preservation and replay

The [prior-package preservation](prior-package-preserved-01.json) retains exact copies
of the prior app, archive, pinned executable and 346 source/roadmap files. The
[baseline close record](baseline-ui-close-01.json) records a desktop-tool relaunch
after its first quit and the second normal quit; no session or model was started
in that reopened baseline window.

The [prospective UI plan](ui-plan-01.json), [isolated launch](ui-launch-01.json) and
[normal close](ui-close-01.json) identify the bounded 0.24 session and owned PID 9390.
The initial [post-quit wrapper refusal](ui-session-check-01.json) happened before
replay because it counted the legitimate `owner` bookkeeping file as a session.
That result and the original helper are preserved. Follow-up replay is recorded
separately; the retained application session is not restarted or changed.

The corrected [attempt02 replay](ui-session-check-02.json) is **verified_complete**:
all 36 journals and the contiguous numerical/save/application history pass the
same-build offline verifier. **All 217 session files remain byte-exact**. No recorded
provider dispatch occurred. [Six helper discovery checks](ui-session-helper-tests-01.json)
cover the ownership file, extra entries and symlinks; the initial failed wrapper
receipt remains unchanged. This is a verification retry, not a second application run.
