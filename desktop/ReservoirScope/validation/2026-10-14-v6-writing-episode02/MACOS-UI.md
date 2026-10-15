# Native app execution and paused recovery

Used the unchanged qualified 0.18.0 app at the exact worktree package path in
[the reused package provenance](../2026-10-14-v6-writing-episode01/package-provenance-01.json).
No browser substitute, private application IPC, new build or model-service
discovery was used. This is an agent UI observation, not collaborator acceptance.

The native My reservoir form was prepared with all planned bounds before any
admission or endpoint contact. Episode01's software mismatch created no session.
After episode02's separate review, freeze and passed admission, the owned service
reported `http://127.0.0.1:63371`. Entering that endpoint enabled the readiness
button. Exactly one explicit check found `gemma3:4b` with the selected manifest
digest. Create produced a prepared session with zero steps/journals; the accepted
configuration matched the plan, including v6, context 8,192, output 1,024 and the
180-second request deadline.

[The Start witness](start-witness-01.json) bounds the one click at
16:10:14.987–16:10:15.167 UTC, with at least 1,163.168185 seconds of the owned
service lifetime remaining. The app showed Running at step 1. The separate
monotonic pre-click check also passed. The accepted session identity was
`sustained-1791994198871-1`, generation 1. Passive committed-manifest observations
followed; no control, prompt, retry or skip change was made during the episode.

The app held at step 240 with seven saved journals and eight retained attempts,
showing “Incomplete or token-limited response cannot become journal feedback.”
Retry and Skip were visible but unused. Export committed session bundle opened
the native parent-folder chooser. Go to Folder selected this episode's own
`target/qa/0.18-v6-writing-episode02/exports`. The chooser briefly disabled Open
while loading, then enabled it; the app confirmed an immutable bundle at
generation 1/revision 281. No user intervention was needed.

The [owned provider stopped](CLEANUP-RESULTS.md) before offline recovery. An
initial Quit was followed by an immediate app inventory still reporting it
running; the next accessibility observation showed the idle guide. That sequence
alone does not prove a quit/relaunch boundary. A second explicit Quit was followed
by a later app inventory with **no Tauri entry**. Opening the exact same package
then showed the idle guide. Neither idle launch restored or started a session.

Experiments → My reservoir → Inspect and recover → Read recovery catalog showed
the exact session as attemptBlocked, durable step 240, seven journals. Verify and
inspect completed; Restore paused for review produced Paused at step 240 with
seven saved journals/eight attempts. Resume explicitly was disabled and the
incomplete-response diagnosis remained visible. No Start, Retry or Skip followed.

The recovered session exported through the native chooser into a distinct
generation 2/revision 282 bundle. The app confirmed completion. Offline replay and
[file comparison](OFFLINE-RECOVERY.md) preserve all 45 nonmanifest files, including
the incomplete response, exactly. Only generation, revision and wrapper phase
changed. The core is still blocked; this is not a test of budget exhaustion,
forced-crash/power-loss recovery or real-model endurance while minimized.

The app is left paused for reading, with the owned model service stopped.
