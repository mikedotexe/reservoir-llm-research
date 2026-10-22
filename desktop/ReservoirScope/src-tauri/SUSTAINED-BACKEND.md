# Sustained backend contract

This backend owns one explicitly created personal synthetic session. It uses the new `reservoir-sustained-*` family and does not modify historical Essentials, action, exploration or native formats. It never starts a service, follows a historical path, contacts a Being, or resumes a request at startup.

## Clock, limits and lifecycle

`SustainedState` owns the numerical engine and a Rust worker. The WebView receives bounded latest-frame summaries through its subscribed Tauri Channel; its timers do not advance the engine. The worker holds the platform activity guard only while user-requested work is active. The publisher samples at 100 ms, and ordinary numerical pacing is 100–10,000 ms. There is no catch-up loop for missed wall time.

Defaults are seed 20260909, 30-step journal cadence, 10,800 maximum steps, 360 maximum prepared language attempts, six hours of active elapsed wall time, 256 MiB of owned storage, 1,000 ms pacing, leak 0.65, noise 0.02, retention 0.955 and regulation enabled. Simulated time is separately derived from the fixed 1/3-second numerical step. The first exhausted budget stops advancement. Retry consumes a new attempt identity. Turn IDs count observation opportunities, so they must not be substituted for attempt IDs.

The backend admits at most 1,000,000 steps, 10,000 attempts, 24 hours and 16–512 MiB. These are resource limits, not a qualification claim for a session of that size. The constant-memory numerical engine holds no growing history. A capped 10,000-row journal metadata catalog supports pagination without replaying the entire history on each page. It contains IDs, previews, status and hashes, not frames or covariance histories.

Pause prevents any newly prepared request from dispatching. A request already dispatched may settle and automatically save its accepted journal, but its feedback remains held until an explicit Start. The duration budget uses the same boundary rule: an in-flight request can finish within its independent request deadline; no new provider call or numerical application follows an exhausted duration budget. There is no final-step journal opportunity. The final allowed attempt may apply its already saved vector once before the attempt budget pauses the clock.

Stop cancels an outstanding request and invalidates its worker epoch. Late results cannot change the accepted state. A stopped session can be explicitly restored through recovery, which first verifies the complete chain and returns a paused session. Provider Retry always creates a new identity; it never resends an uncertain old attempt automatically. Skip binds the exact pending entry/attempt IDs and preserves previous applied feedback while excluding the skipped opportunity from future memory.

Sleep/wake notifications and the worker's wall-gap watchdog cancel outstanding work and require explicit recovery choices. The watchdog is a fallback, not a claim that every OS interruption has been physically qualified. Normal minimized execution is allowed while the app remains open. There are no launch agents, login items, daemons or background services.

## Save and application transaction

### Source repair awaiting separate package qualification

The October 13 reliability preparation reproduced false interruption when UI
publication blocked the watchdog on a long-held session mutex. The source repair
moves publication onto one dedicated thread with a capacity-one notification queue.
Numerical and watchdog threads request the latest snapshot without waiting for its
delivery. A slow reader cannot accumulate historical snapshots or block the clock.
The publisher holds only weak state ownership between deliveries and releases a
disconnected listener without removing a newer replacement subscription.

Worker cleanup explicitly publishes its settled controls. Every update also carries
a decimal `snapshotSequence`, allocated under the state lock, so a delayed command
reply cannot replace a newer terminal update with the same durable revision. This
process-local order is separate from scientific records, manifest revisions and
session generations. The frontend retains their existing identity checks as well.
The frozen 0.12 package used for the multi-hour run does not contain this repair;
its runtime measurements and the repair's tests/build remain separate receipts.

### Journal and feedback publication

The first sustained format requests plain journal prose. There is no WAIT/action JSON mode. V5 retains full observations but presents only RMS, separate sensory fill and coordinate distance in its prompt, followed by the latest physically reread saved-and-applied journal (under a choosing memory policy, the chosen one; under the 0.38.0 and 0.39.0 two-entry prompt versions, the chosen older entry and then the latest applied entry). Historical prompts preserve their original observations and wording. Full-text memory is distinct from the held 48-coordinate codec vector.

The normal transaction is:

1. Persist the prepared observation and prompt before dispatch. Then mark the core attempt started and hand it to the provider without another fallible disk operation in between. A crash can therefore leave a prepared checkpoint even if dispatch subsequently occurred; absence of a dispatch flag in that checkpoint is not proof that nothing was sent.
2. Receive a bounded response on the worker, outside the session mutex. Persist the response event and pending journal before attempting journal publication.
3. Write an immutable journal object, synchronize it, read it back and compare its typed entry to the exact pending entry. An identical existing object is resynchronized before retry succeeds.
4. Commit the save event, prepared feedback and complete continuation checkpoint through the manifest. Only then may the worker grant ephemeral application permission.
5. Apply that vector once at its designated next numerical step and durably retain its application event. Recovery resets ephemeral permission, and Start grants it only after the saved prepared checkpoint has been verified.

Storage failures hold the clock. Retry Save does not invoke the provider or generate a replacement reply. An installed-but-not-acknowledged manifest is reconciled only when it is an exact prefix of the engine's retained events. Conflicting uncommitted segment bytes are preserved as explicitly named orphans. They are never promoted merely because a file exists.

### Storage admission and terminal recovery

The reliability repair distinguishes ordinary publication from Stop, Skip and final
close. It sizes actual serialized candidates, reuses only byte-identical immutable
objects, and counts temporary manifest replacement and orphan-copy overlap without
assuming checkpoint cleanup has already succeeded. The quota is logical file bytes;
allocated filesystem space and physical free-space failures are separate concerns.

Ordinary execution has a conservative **8.125 MiB** low-water margin: one maximum
accepted segment, checkpoint and manifest transaction. A session can therefore stop
well before its displayed byte limit, particularly at the minimum 16 MiB setting.
The exact additional terminal allowance is computed by changing only an ephemeral
clone of the current engine. It covers the actual remaining Stop/cancel, Skip and
close sequence, including segment and object slots. Each terminal action consumes
its part of that allowance; final close does not reserve another future close.
Object-size limits still apply to every transaction.

The retained storage-hold diagnostic survives diagnostic trimming, Pause and explicit
restoration. It blocks new numerical steps, provider attempts and save retries from
spending terminal capacity. Ordinary publication after a paused response still checks
the future terminal path. A newly imposed hold must be observed before any subsequent
dispatch, journal publication or feedback application.

An inspected export is bound to the current committed generation and revision. A
newer volatile revision in the same active generation does not block exporting that
explicitly inspected prefix. The main current-snapshot export still refuses to
substitute an older prefix. Changed committed snapshots or replacement generations
must be inspected again.

## Bundle and verification

The app-owned `sustained-v1` store contains session directories with a small atomic `manifest.json`, immutable sequence-numbered segment envelopes, content-addressed complete checkpoints and immutable journal objects. Only the current and previous checkpoint objects are retained after a successful commit; cleanup failure does not turn a successful transaction into an event retry. The bounded event outbox applies backpressure before unbounded accumulation is possible.

Each segment envelope carries its sequence, previous envelope byte hash, core replay segment and full journal-object byte hashes. A journal object's timing metadata is therefore bound to the same immutable chain as its exact prompt, response, observation and encoded vector. The text SHA-256 is a separate identity and must not be presented as the hash of the entire journal file.

Whole-bundle verification checks exact seed-derived genesis, consecutive segment identities, core event/numerical replay, journal objects against core replay evidence, final checkpoint bytes and the manifest's durable cursor/count. A per-segment core result alone does not establish genesis or whole-history continuity. The explicit application CLI `--verify-sustained DIRECTORY` performs the same whole-bundle verification without starting a WebView, restoring a run or making HTTP requests.

Recovery catalog rows are metadata only. Inspect performs full verification. IPC converts full-width seed/RNG integers to decimal strings; that view is inert inspection data, not an original-file serialization. The exported bundle preserves the original committed file bytes. Uncommitted objects are reported, excluded from the exported committed prefix, and never silently accepted as journal history.

Export creates a new bundle directory below a user-selected destination. It does not overwrite an existing directory. It validates bounded object reads, replays the copied chain, uses no-replace directory publication and rejects application resources and managed-store destinations. An export guard spans the native folder dialog and copy/verification, so cooperative close cannot abandon it.

## Immutable journal prompt selection

The session config carries the core's typed `promptVersion`. Fresh defaults select
`reservoir-journal-v5`; a missing historical field selects v1 and serializes without
an added field, preserving old checkpoint and manifest interpretation. V2, v3 and v4 remain
supported as frozen historical contracts. Unknown versions are rejected. The
same selection enters seed-derived genesis, every checkpoint and whole-chain replay;
changing only a manifest's version cannot relabel existing evidence.

The journal IPC view names the owning prompt version without rewriting stored journal
objects. The frontend checks it against the accepted session, preserves prior content
on a rejected detail, and shows it inside Evidence. Restoring a historical session
never upgrades its prompt or starts generation. The open-ended invitations change
neither transport completion rules nor durable-save/feedback gates. Editorial
quality checks are offline evidence tools, not an eligibility filter.

## Journal measurement read model

For a validated stored journal, Rust returns `measurementReference` alongside the
inert observation and prose: current and previous step, comparison availability,
and eight bounded rows with key, label, unit, current value, optional prior value
and optional signed difference. The frontend checks the read-model shape and owning
step, then formats it; it does not infer metrics from prose or recompute differences.
Unsupported references leave prose and original evidence readable.

V4 and v5 observations retain a bounded `previousMeasurements` snapshot taken before the
current observation replaces the prior one. Its provenance is the previous reached
numerical observation, not the previous eligible journal. Checkpoint validation
checks dimensions, bounds and matching step identities; whole-chain replay checks
that the values match the actual predecessor. V1–v3 observations omit this field and
retain their typed bytes. A legacy prior-step identity alone does not authorize
inventing its scalar values. Existing sessions keep their prompt/observation contract
on restoration, and new defaults do not migrate old evidence.

## Evidence and close handling

### Retained writing budgets

Sustained `outputTokens` and `requestDeadlineSeconds` default to 1,024 and 180 for
new sessions, with integer ranges 256–2,048 and 60–180. Missing historical fields
mean 256/60; those values are omitted on serialization so typed legacy hashes stay
stable. The fields belong to configuration, specification and prepared requests.
Whole-history genesis verification rejects relabeling an existing run's budget.

The separate sustained transport uses the retained output ceiling for the HTTP
request and completeness check, and the retained deadline for the whole request.
Finite generation keeps its 256/60 policy. Both paths retain the one-MiB response
bound, cancellation, no redirects/retries and exact model checks. The normal
duration and interruption watchdogs remain independent of request allowance.
An explicit context limit must exceed the output ceiling; this is not proof of
token fit or provider processing. The frontend's new model configuration requests
8,192 context tokens and displays accepted writing ceilings inside journal Evidence.

Host bookkeeping timestamps are decimal epoch milliseconds: actual local dispatch, received response and publication attempt. Transport duration uses a monotonic clock. Scripted responses have no local-model dispatch timestamp and `requestStarted=false`. These fields do not authenticate a remote provider or establish a causal effect of words on the reservoir.

The immutable segment retains blocked response/failure events. The first UI provides journal pagination and checkpoint inspection; it does not yet provide a dedicated browser for every failed-attempt event. A generic `attemptBlocked` phase must not be relabeled as a codec failure or a provider failure without the corresponding evidence.

Close admission uses a nonblocking mutex barrier, not only dirty/running atomics. Pending requests, prepared feedback, uncommitted events and active exports prevent clean authorization. Explicit discard records a skipped opportunity and must become durable before exit is authorized. If quota prevents that write, the repair has one narrow legacy escape: after whole-prefix verification, a current committed **Ready** checkpoint may be retained unchanged while explicitly discarding only its volatile suffix. This is a process-local exit decision, not a saved stopped manifest or recovery of unsaved steps. It never selects an older Ready checkpoint over newer committed intent. Retained Language, Memory, Journal, Prepared or Blocked state still requires a durable decision; it cannot be silently discarded through that escape. Return from a close review clears the provisional closing gate; the shared app coordinator prevents an older asynchronous close from overriding a later Return.

Explicit **Checkpoint and quit** can preserve fully committed prepared feedback when no worker, export, unresolved journal/request or uncommitted event remains. It persists the stopped checkpoint without skipping the journal. Verified restore remains paused and does not authorize application; a later explicit Start applies that saved feedback once at its designated next step.

## Qualification limits

Focused automated tests cover deterministic rollover, an accelerated 1,001-step continuation, exact exports, physical memory read failure, quota refusal, journal publication/readback failure, manifest publication failure before and after installation, orphan preservation, exact-prefix reconciliation, prepared feedback recovery/application once, stale results, Pause/Stop with owned fake providers, explicit interruption, close/discard durability and full-width inspection values. These are software fault injections and accelerated runs.

They are not multi-hour battery, thermal, memory or storage measurements; real provider evaluation; physical power-loss testing; sleep/wake hardware qualification; or Windows/Linux packaged acceptance. Those remain separate recorded gates. No relaxed numerical tolerances or old-format support claims are introduced by this backend.
