# Reliability run and follow-up: complete

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

The frozen final 0.12.0 Mac package is running the prospective workload. This is an
execution update, separate from the pre-Start criteria frozen in
`prospective-freeze.json`. No two-hour pass or completed recovery is claimed here.

- Explicit Start was observed at **2026-10-13 16:31:05.920848 UTC**.
- Minimize completed at **16:38:59.247 UTC**. The conservative marker is
  **16:39:18.845510 UTC**, so the two-hour interval ends no earlier than
  **18:39:18.845510 UTC** / **11:39:18 Pacific**.
- The visible prelude lasted about eight minutes. A combined minimize/Dock inspection
  timed out; the app was rebound and explicitly raised before a fresh successful
  minimize. The earlier ambiguous interval is excluded. The marker is an operator
  declaration, not continuous independent window-state instrumentation.
- At the conservative minimized boundary, the manifest retained step **481**, **16**
  journals and **79** segments. At the 16:40:21 sample it retained step **541** and
  **18** journals, with no sampler errors so far. These are early progress readings.
- The step-30 journal remains selected, with Follow latest off. Its exact ID and
  text/object hashes are retained in `selected-journal-before.json`. The last UI read
  showed step 434 live, 14 saved journals and the unchanged old selection. Both render
  counters stayed at 98 while the graphics were offscreen during journal reading;
  this is a short behavior observation, not GPU or energy measurement.

Main-process sampling is active under PID 20466, selected app PID 17307. The owned
fixture is PID 17666 with a four-hour lifetime and 500-request ceiling. Verify exact
start/executable identities from `owned-process-identities.json` before later process
actions. The app's own active-duration ceiling is 7,800 seconds, expected near
18:41 UTC if uninterrupted; a late follow-up may observe exhausted-budget recovery.
Neither host power preferences nor any Being system was changed.

The finite `reservoir-reliability-qualification` thread follow-up checks every ten
minutes and follows `CONTINUE.md`. It should leave healthy early progress quiet,
finish actual recovery/resource analysis when due, and end after this tranche.
The app, provider and sampler each keep their independent bounds.

## Repair tested separately in source

Preparation reproduced a false watchdog interruption after a healthy 5.5-second
session-lock hold. The source repair separates publication from the watchdog with
one bounded coalescing queue, publishes final worker controls, and orders transient
snapshots independently of durable record revision. Frontend acceptance rejects
delayed old snapshots, including same-revision Stop replies.

- **161 desktop tests passed**, with strict desktop Clippy.
- **301 frontend tests passed**, with TypeScript validation.
- Sampler tests and the independent one-second CPU-unit check are retained separately.
- Rust before/after sources and patches match the frozen package's recorded baseline.
- The executable under measurement remains unchanged. The planned repair package is
  **0.12.1**, after the 0.12 run and recovery evidence are preserved.

Recovery, actual duration, resource trend interpretation, new-package UI checks,
24-hour operation, actual sleep/wake, real models, shared WebKit/GPU resources,
energy and Windows/Linux remain separate open checks. Update this status with actual
outcomes and link new receipts; preserve the prospective documents and raw logs.

## Natural storage-cap investigation

An isolated accelerated source harness filled the minimum 16 MiB session budget with
actual generated numerical history and scripted journals. It did not add filler files,
change a running quota, contact a provider, or touch the minimized session. Both
investigation profiles completed; that means the probes executed, not that recovery
passed. First-failure bundles and operation results are retained under
`target/qa/0.12-natural-quota-01`.

- With a journal every three steps, the journal reserve stopped publication at live
  step 114 with 37 retained journals and 12,764,948 owned bytes. Stop, explicit skip,
  close, export and recovery retained a valid committed record.
- With a journal every 1,800 steps, numerical history reached the cap at live step
  3,240 versus durable step 3,210, with one journal and 16,672,785 owned bytes. Retry,
  Stop and explicit-discard close failed to persist. Current-revision export was
  rejected because the live revision was newer than the retained manifest. Dropping
  the isolated state allowed verification/export and restoration of the valid
  3,210-step prefix; its 30 uncommitted steps were not recovered.

This is a confirmed baseline recovery defect, outside the existing journal-only
reserve. The separately qualified source repair below preserves the configured cap,
committed evidence and truthful treatment of discarded work. The frozen 0.12.0 binary
and its long-running session are unchanged.

## Interim resource analysis

`interim-phase-analysis-02.json` binds the first 159 samples (2,370.744 seconds
since sampler admission); it intentionally has no completion footer. There were no
sample errors, parse errors, detected sampling gaps, clock jumps or incomplete disk
scans in that prefix. This does not complete the two-hour interval or recovery.

The frozen early comparison window, minutes 10–25 after observed Start, now has
60 process samples. All-observed main-process median RSS was **68,313,088 bytes**
(about 65.15 MiB). Mean interval CPU, weighted by covered duration, was **0.9031% of
one core** over 885.247 sampled seconds; median threads were 23 and descriptors 13.
The 15 complete disk scans rose from 8,914,706 to 20,618,312 logical bytes over
840.240 seconds, about 47.8 MiB/hour over those scan endpoints. That short-window
growth rate is descriptive, not a promised capacity or duration.

The report also retains resource summaries excluding overlaps with documented
background test loads: median RSS 68,665,344 bytes and duration-weighted CPU 0.9005%
over 645.165 seconds. All functional progress and error evidence remains unfiltered.
The later minutes 110–125 window is still unexecuted; no early/late growth or leak
conclusion follows yet. Shared WebKit/GPU and provider resources remain excluded.

The final frontend source now passes **309 tests** and TypeScript validation.
`frontend-quota-final-03-qualification.json` records stable live/retained status,
explicit committed-prefix export/close wording and storage-reserve help. The exact
closed load interval is retained in `frontend-final-load-03.json`; the earlier second
receipt and its load interval remain separate historical checks.

At **17:39:08 UTC**, passive sample 279 still reports the selected original process
identity and phase `running`, with **3,751 durable steps and 125 journals**. The row
has no errors. This is continuing progress, not completion of the two-hour interval.

The final-source natural quota rerun has passed both profiles, followed by **169
desktop tests**, **150 core tests**, and strict workspace/all-target Clippy (the two
opt-in natural profiles ran separately). The closed interval is **17:32:34.913899–
17:40:11.274699 UTC**. `quota-repair-final-02-qualification.json` binds unchanged
source and frozen executable hashes before and after those commands. The repair sizes the actual
terminal transactions and reserves their object/segment capacity as well as bytes.
Inspected saved-prefix export tolerates a newer volatile revision in the same
generation. The limited explicit-discard escape requires verification of the current
committed Ready checkpoint; it cannot skip newer retained request or journal intent.
The natural profiles now stop without a volatile tail: cadence three retains step
75 and 24 journals in 8,284,793 bytes; cadence 1,800 retains step 1,740 and no journals
in 8,317,151 bytes. Stop, close, both export routes and explicit held restoration pass
for both. This is a conservative reserve under the 16 MiB quota, not a measured
physical-disk guarantee. See [QUOTA-REPAIR.md](QUOTA-REPAIR.md) and
`quota-repair-final-02-evidence.json` for exact source and owned-file evidence.

No repair package has been built over the frozen application. The two-hour minimized
interval, actual recovery and separate 0.12.1 package checks remain unfinished.

## Approved reading pass, source complete

The user approved simplifying setup, journal reading and routine status while
retaining visible failures and exact evidence. The separate reading validation
directory records **323 passing frontend tests / 36 files and TypeScript** in
`integrated-02-qualification.json`. This supersedes the earlier 309-test source
receipt for frontend qualification only; backend final02 remains applicable.
The actual browser fixture exercised exact 61-second duration editing, invalid
draft blocking, explicit preparation, journal prose and save-error recovery controls.
It did not exercise Tauri or alter the frozen app. Browser/server use ended at
18:21:02.432561 UTC. The final 18:21:34.819000–18:21:39.229833 UTC source-check load
overlaps the late resource window and must be included in sensitivity analysis.

The selected real-model candidate is the cached `gemma3:4b`, with exact manifest and
prospective owned-service configuration retained in the reading directory. Weight
verification, private copying, launch and actual-model outcomes are not yet executed.
The running reliability workload still uses only the owned synthetic fixture.
