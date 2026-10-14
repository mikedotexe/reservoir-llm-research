# Reliability continuation — bounded tranche complete

## Completed bounded tranche — October 13, 2026

This follow-up is complete. Do not restart the soak, resume a budget, launch another
provider, or repeat the real-model run from this continuation file. The material
below preserves earlier progress and instructions; this closeout supersedes its
statements that the measured run or model rehearsal is still active.

- Frozen 0.12.0 completed **7211.206384167 actual seconds minimized**. Pause retained
  7100 steps and 236 journals. Explicit restore/resume later retained 7127 steps and
  237 journals with the previous files unchanged. Both native exports passed the
  pinned verifier. See [exports and recovery](EXPORTS-AND-RECOVERY.md).
- Separate forced-process interruption retained the committed prefix, made no
  automatic resend, accepted an explicit new retry, and preserved its exhausted
  attempt budget on restoration. See [the interruption account](PROCESS-INTERRUPTION-RESULTS.md).
- The sampler retained 523 valid samples. Minimized main-process median RSS was
  56.875 MiB and duration-weighted CPU 0.88861% of one core. The final settled
  thread/descriptor gate is incomplete; total WebKit/model resources and GPU energy
  were not measured. See [resource results](RESOURCE-RESULTS.md).
- Distinct **0.12.2** includes the independently tested watchdog/publication and
  storage-reserve repairs, calmer setup and journal reading, and a correction for
  stale historical errors. Its own native Checkpoint-and-quit/recovery regression
  and immutable export passed. The old soak does not qualify this build's duration.
- The selected cached **gemma3:4b** ran only in an owned private loopback service.
  The actual 0.12.2 app completed four journals, applying them at steps 31, 61, 91
  and 121; all three subsequent prompts retained the prior applied journal's exact
  text. Its separate native export passed pinned offline replay. The prose contains
  unsupported interpretations and stale labels; mechanism success is not writing
  quality or scientific validation. See [the final package account](../2026-10-13-reading-0.12.2/README.md)
  and [actual UI/export/quit observations](../2026-10-13-reading-0.12.2/REAL-MODEL-UI.md).
- Owned sampler, synthetic provider and qualification app stopped. The real-model
  supervisor retained an EPERM cleanup error; repeated scoped checks subsequently
  established absence of its exact server/supervisor and an empty original process
  group. That failure remains distinct from the verified absence. No Being system
  or service was contacted or altered.

The finite automation is **paused**, confirmed by the app tool and on-disk status
in [the closeout receipt](automation-closeout.json). Next work is a versioned, more grounded writing prompt
and reading review, preserving these original journals and numerical contracts.
Pointer activation after restoration still needs human/native review: keyboard
activation succeeded, while several tool click attempts did not. The 24-hour,
actual host sleep/wake, total-app/GPU-energy and Windows/Linux gates remain open.

## Earlier progress, retained

This is an authorized continuation of the user's request for multi-hour reliability,
resource measurements, minimized operation and recovery. It is a software qualification
run with an owned synthetic HTTP fixture. It does not access or modify Being systems.

## Latest continuation checkpoint — 19:01 UTC

The actual frozen 0.12.0 capture and recovery work are complete. The conservative
untouched minimized interval was **7,211.206384167 seconds**; Pause settled
live/durable step **7100**, elapsed **7721.255 / 7800 seconds**, with 236 journals.
The owned sampler was stopped with its 523-sample footer after 7836.242203583 seconds;
this was an intentional shorter capture, not a completed 9000-second run. The root UI
retained the selected step-30 journal with Follow latest off. Do not rerun the soak.

Two native exports passed the pinned frozen CLI and independent history checks:
`target/qa/0.12-reliability/exports-multi-hour/sustained-1791908510756-1-1-8283`
(7100 steps, 236 journals, 1180 segments) and
`sustained-1791908510756-1-2-8319` (7127 steps, 237 journals, 1186 segments).
Normal Cmd-Q, idle relaunch, explicit paused Restore and explicit Resume/Pause were
observed. All 1180 previous segments and 236 journals remained byte-identical; the
only new request observed 7110 and applied 7111 with memory from 7080. Budgets remained
unchanged, elapsed time continued to 7748.510 seconds. See `EXPORTS-AND-RECOVERY.md`.
The first export also rejected all 13 scratch-copy corruption controls. No originals
were mutated and no model service was contacted by offline verification.

A separate bounded interruption fixture is also complete. Root killed exact owned
PID 76635 during held synthetic POST 238, then confirmed absence before releasing the
handler. Idle relaunch and explicit Restore did not resend it (POST count 238).
Explicit Retry created attempt 2; requests 239–242 saved journals observed 3/6/9/12,
applied 4/7/10/13, with no accepted response/journal/application for interrupted
attempt 1. Native export `sustained-1791917410760-3-4-40` passed pinned replay and
independent request/save/memory checks. The preserved three-file pre-kill prefix
matches its receipt, and its first segment remains exact in the export. The
independent passive capture missed idle and is honestly labeled post-recovery;
use the root restored-count receipt for no-autoresend evidence. See
`PROCESS-INTERRUPTION-RESULTS.md` and `process-interruption-01-export-evidence.json`.
This is process interruption, not physical power-loss qualification.

The five-attempt limit reached step 13 / 4 journals at 29.836 seconds. Another quit,
idle relaunch and explicit Restore retained 5/5 attempts and disabled Resume;
POST count stayed 242. Root then quit the final frozen process PID 79294. Its absence
and the unchanged f68a… binary are recorded in `frozen-package-final-stop.json` at
**18:59:17.489858 UTC**. No frozen app process is retained as active by this checkpoint.
All initial/relaunch PIDs below are historical and require fresh identity checks
before any later action.

A separate agent is building the distinct 0.12.1 source repair/presentation package;
its package identity and native UI checks remain pending. The frozen verifier is
preserved at `target/qa/0.12-reliability/export-verification-01/reservoir-scope-desktop-frozen`.
Do not substitute the rebuilt app for that frozen evidence. Resource analysis and
any remaining owning-fixture cleanup belong to root. The owned real-model helper
has 10 passing synthetic tests and peer review; real-model staging/runtime are still
separate from these results and require their own receipts. Preserve the source
qualification and model plan below rather than restarting the completed soak.

## Exact run identity

- Repository: `/Users/v/other/reservoir-llm-research`.
- Prospective configuration and complete frozen app inventory: `run-plan.json`.
- App: `desktop/ReservoirScope/target/release/bundle/macos/Reservoir Scope Tauri Preview.app`.
- Running binary SHA-256: `f68a3752a628edf11ac6161a26e6979bb22dcf4c3ee1c63f10add2cea86ab40d`.
- Initial app PID: **17307**. Recheck executable path and process start identity before any process action; PID alone is not sufficient.
- Session: **sustained-1791908510756-1**.
- Owned session directory: `/Users/v/Library/Application Support/research.reservoir.scope.tauri/sustained-v1/sustained-1791908510756-1`.
- Fixture directory: `desktop/ReservoirScope/target/qa/0.12-reliability/provider`.
- Fixture identity: its `endpoint.json`; initial PID **17666**, endpoint `http://127.0.0.1:57314`, model `reservoir-fixture:reliability-0.12`.
- Fixture process expires after four hours and admits at most 500 generation requests. It is not a real model.
- App budget: 7,800 active seconds, 10,000 steps, 400 attempts, 256 MiB; pace 1,000 ms, journal cadence 30, seed 20261013.
- UI action times and declared phases: `ui-markers.jsonl` (created when actions execute).
- Sampler invocation/identity and output: `sampler-launch.json` and the path it records (created when launched).
- Successful fresh Minimize action acknowledged at **16:38:59.247 UTC**; the conservative
  recorded interval begins **16:39:18.845510 UTC** on October 13. Do not restore the app
  before **18:39:18.845510 UTC** unless a failure requires investigation. The earlier
  Dock-inspection attempt timed out; it is excluded from the claimed minimize window.
- The visible prelude therefore took about eight minutes, leaving about two minutes
  between the two-hour minimized target and the app's duration bound near 18:41 UTC.
  A late follow-up may legitimately find the budget exhausted.
- Sampler PID **20466**, 15-second samples in `samples-01.jsonl`, 60-second disk scans,
  9,000-second bounded lifetime; its exact source is `macos_reliability-capture-01.py`.
- Finite thread follow-up ID: `reservoir-reliability-qualification` (10-minute checks).
- Exact app/provider/sampler process starts are in `owned-process-identities.json`;
  use them before scoped cleanup, not an assumed reusable PID.

The source tree may contain a tested watchdog fix which is **not in this frozen app**.
Do not rebuild over the running app or ascribe that fix to its measurements.
The source repair has passed 161 desktop tests, strict Clippy, 301 frontend tests and
TypeScript validation. See `publisher-final-01-qualification.json`,
`frontend-full-source-tests.json` and `frontend-snapshot-source-checks.json`.
Package it with a new version (planned **0.12.1**) after the measured 0.12 app stops.

A subsequent isolated natural-quota investigation confirmed a second repair for that
package: sparse numerical history can exhaust the hard quota and trap Stop, discard
close and both export routes behind an unpersistable live revision. Read
`natural-quota-01-evidence.json` and `RUN-STATUS.md`, then any later quota repair
receipts. The original source-only publisher receipts predate this storage repair;
do not use them as qualification of later edits. Frontend source now clarifies exact
live/retained steps and offers explicit committed-prefix inspection. Finish backend
reserve, durable export and explicit-discard regressions before building the new
candidate. The running 0.12 binary still has both known baseline defects.

**Source qualification is now complete:** final02 passes two natural 16 MiB profiles,
169 desktop tests, 150 core tests and strict workspace/all-target Clippy. See
`quota-repair-final-02-qualification.json`, `quota-repair-final-02-evidence.json` and
`QUOTA-REPAIR.md`. Source and frozen package hashes were unchanged across checks.
Frontend final03 passes 309 tests and TypeScript validation, with exact load envelope
in `frontend-final-load-03.json`. Preserve these receipts and do not repeat full suites
without further source changes or a specific unresolved concern. Build the separate
0.12.1 only after preserving the frozen run and recovery. The exact quota-source load
interval, usable directly by the final analyzer, is 17:32:34.913899–17:40:11.274699 UTC.

**Subsequent approved presentation pass:** the planned 0.12.1 now also includes calmer
setup, exact h/m/s duration validation, compact running status, complete journal prose
and a closed Evidence disclosure. Required save/attempt actions stay visible. Final
source checks pass **323 frontend tests / 36 files and TypeScript**; see
`../2026-10-13-reading-0.12.1/integrated-02-qualification.json` and that directory's
README. The browser-only fixture checks are separate from native qualification.
Its owned Vite server and browser closed at **18:21:02.432561 UTC**, before the fixed
late resource window. Final source checks ran **18:21:34.819000–18:21:39.229833 UTC**;
include that load overlap in sensitivity analysis. Preserve the earlier failed test
receipt: all 323 production tests passed, but two copied source-backup tests were
accidentally discovered; backups now have `.txt` suffixes and final checks pass.

The user delegated model choice. Cached **gemma3:4b** is selected in
`../2026-10-13-reading-0.12.1/model-selection.json`; its five referenced objects still
need validation and an owned private copy. No real service has been contacted or
started. Do that separately only after the frozen capture/recovery and new package
qualification. Keep HOME unchanged, never use an existing service/default endpoint,
and follow the audited owned-service recipe in `REAL-MODEL-SELECTION.md`.

## While the minimized interval is still running

1. Read only the selected run's latest bounded sample, manifest, fixture log tail and
   marker file. Confirm the known process identities remain alive and durable steps,
   journals and segments keep advancing. Keep initial sample errors and missing intervals.
2. Do not activate, inspect through CUA, rebuild, export, or pause this app during the
   uninterrupted interval. CUA can restore a minimized window. No claim of independent
   WebKit/GPU process attribution is available from the main-process sampler.
3. Wait for at least 7,200 actual seconds since the recorded minimized marker. The
   actual eight-minute visible interval plus two hours minimized leaves roughly two
   minutes before the duration bound. A delayed follow-up may find the bound already
   reached; that is an honest separate boundary outcome, not permission to extend it.
   If a follow-up starts within three minutes of the target, finish independent
   read-only preparation and use waits of at most 60 seconds until the target, then
   proceed. Do not restore early to accommodate the scheduling cadence.
4. If progress stalls for over 120 seconds, the app exits, or an interruption/storage/
   provider failure appears, preserve the evidence and investigate. An interrupted run
   does not qualify as an uninterrupted two-hour soak. Do not silently restart or resend.
5. Record meaningful changes in this directory and the roadmap. Preserve old receipts.

## Finish the interval and recover

1. Record a pre-restore marker and manifest summary, then bind the app by bundle ID
   `research.reservoir.scope.tauri` through CUA. Read fresh UI state. Verify the selected
   old journal, live clock, current phase, render behavior and usable controls. Record
   the actual minimized duration and any uncertainty about external user interaction.
2. Pause if still running. Let an already-dispatched response settle; do not invent an
   applied receipt for prepared feedback. Record pause/settlement and stop the primary
   measurement interval. Do not count inspection/replay workload as minimized runtime.
   Signal only the identity-matched owned sampler with SIGTERM and retain its footer
   before any app rebuild. An intentional capture shorter than its 9,000-second ceiling
   must retain that stop reason and its exact coverage; do not relabel it a completed
   9,000-second capture. Separate recovery processes need separate sampling identities.
3. Export the committed bundle through the native folder dialog into a fresh directory
   under `target/qa/0.12-reliability`. Verify it with this exact binary's
   `--verify-sustained DIRECTORY`; record verifier wall time and process memory separately.
4. Qualify explicit Checkpoint and quit, process absence, relaunch without HTTP or
   automatic restoration, inspection and explicit paused restoration. If budget remains,
   explicitly Start, advance a short amount, Pause and export a new snapshot. If the
   budget is exhausted, verify that it stays exhausted and do not report successful
   continuation under unchanged bounds.
5. Test process-interruption recovery with a **separate**, deliberately bounded owned
   synthetic session if needed. Bind any termination only to the exact app executable,
   process-start identity and test session. Preserve the last committed prefix and
   orphan diagnostics. A forced process exit is not physical power-loss qualification.
   Pending/unknown requests must not resend automatically; new Retry needs a new ID.
6. Analyze the real samples with `scripts/macos_reliability.py analyze`. Include covered
   duration, sampling gaps, per-phase CPU/RSS/threads/FDs, logical and allocated storage,
   file counts, durable progress, journal counts and measurement overhead/limitations.
   Main-process RSS is not total app/WebKit memory and CPU is not GPU energy.
7. Verify journal prompts, memory and save/application continuity with the retained
   fixture requests and whole-bundle checks. Reuse the previous tranche's copy-only
   corruption checker where its assumptions apply; do not mutate the originals.
8. Use the completed source qualification above, then package the distinctly identified
   0.12.1 follow-up only after the frozen app has stopped. Its own package/UI checks
   remain separate from the old binary's multi-hour result. Update roadmap, parity
   ledger and validation account with exact executed evidence and remaining gates.
9. Stop only the owned fixture/sampler/app after qualification, preserving logs and
   bundles. Pause this finite follow-up automation when the tranche is complete or a
   concrete user prerequisite prevents further safe progress. Do not leave a monitoring
   automation running indefinitely after the qualification work ends.

Read `README.md` and `RECOVERY-CHECKLIST.md` here for the prospective criteria. The
24-hour gate, real models, actual system sleep/wake, GPU watts/utilization and
Windows/Linux remain separate unless executed evidence specifically closes them.
