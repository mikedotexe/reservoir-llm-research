# Fresh experiments: session and save contract

This tranche adds finite, explicitly started experiments to the Tauri application.
Its completion and executed checks belong to the current parity ledger and candidate
validation directory; this document specifies behavior and does not confer acceptance.

## What runs

Explore uses the existing 32-node, 66-input deterministic engine, with per-step
controls, explicit pulses and an optional separate sensory covariance field. It keeps
the native 1,800-step bound. Original stage recipes 1–4 retain their 3,000-step bound,
prepared/scripted replies, explicit local responses for stages 3/4, and existing
`essentials-v1` interpretation. Stage language
turns are not action-journal save receipts.

Standalone A–H and the 0.9 paired comparisons retain at most 600 steps / 128
opportunities per arm. Component B–H can compare with the preceding component;
A has no previous component. Execution qualification is recorded separately. Explicit
local models for independent D–H are available in 0.11; sustained personal sessions
remain subsequent work.

| Component | Added mechanism |
| --- | --- |
| A | Synthetic input and state without recurrence |
| B | Recurrent state |
| C | Separate sensory covariance observation |
| D | Durably saved and encoded journal output; state feedback gate closed |
| E | Saved writing returned on the next numerical step |
| F | Latest saved journal reread and quoted in the next prompt |
| G | Scheduled WRITE_JOURNAL or WAIT choice |
| H | Sensory-retention control with recorded current/next boundaries |

Independent scripted generation uses the native declared reply policy; its vector
is computed from the current retained sensory observation. Fixed replay constructs
all nonfinal tape packets before numerical execution using the native zero-semantic
reference field and fixed initial retention. A tape packet's vector remains fixed
even if the experiment's own covariance diverges. This tranche creates deterministic
tapes from accepted settings. A paired fixed run shares one precomputed tape;
arbitrary tape-file import remains outside this tranche. These remain existing
native format contracts, not new scientific claims.
Scripted and tape modes make no model request. Local mode requires explicit endpoint
and model configuration and an eligible opportunity. Nothing discovers, starts or
downloads a model; see [the transport contract](LOCAL-MODELS.md).

All supported families preserve their existing portable formats. Seeds cross the UI
boundary as decimal strings and are parsed as full-width integers in Rust. Imported
records retain original bytes; newly generated records are identified separately.

## Ownership and timing

Rust owns one current session, its seeded numerical state, finite scheduler, controls,
pending journal, receipts and persistence state. A session identity, generation and
monotonic revision bind each asynchronous result. A reset cannot accept updates from
the prior generation. Entering a workspace or inspecting a recovery entry starts no
experiment.

Step advances one numerical boundary. Run schedules finite steps in Rust. Waiting
for persistence does not advance simulated time. Pause stops scheduling while
preserving state; stop also resolves a pending journal as an explicit terminal
failure when that action is selected. Controls and pulses affect the next recorded
Explore boundary, never an already accepted frame.

The frontend receives bounded current views through commands and ordered channels;
it does not repeatedly receive growing records or decide what has been saved. Hidden
visualizations can suspend rendering independently of a finite backend run. Running
while minimized is a foundation for the selected future lifecycle, not a claim of
sustained-session, operating-system sleep or crash-resume qualification.

## Durable journals and feedback

An accepted scripted or local-model WRITE first becomes a pending journal candidate outside the committed
portable action list. Its observation step, exact prompt, response text and identity
are fixed. The backend publishes the journal to its application-owned session store
and reads it back. Only a matching successful save/readback permits the core to
commit a saved receipt, encode the text and make E–H feedback eligible.

The next numerical step records the application boundary. A journal observed at step
30 can therefore first apply at step 31. D records prepared features without turning
on E's feedback gate. Separate spectral feedback and recurrent state remain distinct;
the current teaching prompt must not be described as observing the entire phase space.

If publication or readback fails, numerical stepping stays blocked and the exact
candidate remains available for retry. Attempts and errors remain separate local
evidence. Retrying the save call before its outcome is committed does not rewrite a
terminal portable receipt. Exporting the enclosing record never grants eligibility.

The user can instead explicitly stop and retain the failed save. That finalizes a
native-compatible failed action receipt and terminal failed run, retaining the reply
and failure but no successful save, journal entry or applied feedback. A committed
failed outcome cannot later be rewritten into success or resumed. A pending record
cannot be silently exported as if the pending writing never existed.

## Memory, choice and control boundaries

F/G/H read the latest committed journal through the application storage owner before
a response is constructed. The core requires the exact retained entry, including
its identity, text and hash. The backend reads only its own bounded, validated session
files; neither a portable provenance path nor an imported journal can select an
external memory source. A failed read records memoryRead failure and no started
request. It cannot silently use the in-memory copy instead.

The successful memory entry and text remain in the receipt and exact reconstructed
prompt. This establishes retained context; actual dispatch is recorded separately
and does not prove provider receipt, learning or scientific benefit. A failed or merely pending journal never
enters memory. The full personal LLM loop remains future work.

G/H scheduled opportunities can retain WAIT with empty reply text and no new journal,
save receipt, encoding or application receipt. The previous held semantic input
continues. Manual journal opportunities always request writing, as in the native
contract, and remain bounded by the total opportunity limit.

H records the retention used at the current boundary and the controller output for
the next boundary. It controls the separate sensory covariance field, not reservoir
weights or a direct measured change to a live Being. A fixed tape's semantic vector
is not recomputed against H's altered covariance.

## Paired components and observation channels

Paired component runs share seed, forcing, noise draws and timing. Both numerical
arms advance transactionally before an opportunity starts. Independent scripted
replies receive each arm's own observations and saved memory; they do not promise
identical feedback vectors. Fixed mode uses a single precomputed tape for both
arms. Shared camera and cursor controls are presentation aids, never a claim that
the two scientific trajectories are equal. Exact values and text belong to their
selected arm.

The separate D/D observation comparison keeps inputs, state and sensory measurements
matched. Left context contains sensory measurements; right context additionally
contains the retained 32 recurrent coordinates at that same observed step. It uses
independent scripted or local-model replies with alternating left/right request order. Active and
quiet forcing are explicit settings. Neither arm applies feedback, reads journal
memory or regulates retention. A scripted run demonstrates what context was supplied,
not adaptive writing, learning, or benefit from the additional information.

Each arm's journals live in its own fixed storage namespace. Candidate saves are
bound to arm and journal identity as well as session generation; identical text and
IDs across arms do not make them the same save. Memory is reread only from that arm's
committed journal. A component's failed first action retains an unstarted cancellation
for its later partner. An observation failure still permits the partner's attempt;
explicit stopping cancels remaining work. Partial outcomes stay visible in portable
receipts and cannot be resumed into a different historical outcome.

A boundary can contain a committed first journal and pending second journal. This
is not yet a portable matched record with equal action opportunities. The local
checkpoint retains bounded receipt/journal evidence for that boundary alongside the
pending candidate and per-arm save attempts. Its previous complete portable snapshot
and durable step remain separate. Recovery inspection/export reveals the partial
boundary without manufacturing a portable verification result or resuming execution.

## Separate field-only controller comparison

The fixed `essentials-regulation-v1` study advances a baseline and regulated sensory
field transactionally under identical seeded 66-dimensional input. It contains no
reservoir recurrence or state, text encoder, journal, memory or model. The accepted
specification fixes field seed 98, input seed 42, 600 steps, dt 1/3, initial retention
0.955, target fill 68%, and evaluation window 301–600. Inert generic session defaults
are locked; changing them cannot silently change the study or replace an accepted run.

A controller result produced from observation n determines regulated retention at
n+1. Inspection returns separate field frames with exact input, projected coordinates,
spectrum, measured fill, used retention and next control. No empty reservoir frame is
invented. Two spheres share the native radial-volume fill interpretation and a fixed
0–100% scale. Prefix trends and the 32 × 66 seeded projection matrix are fetched by an
explicit cursor-owned read; they are not repeatedly streamed with numerical updates.
The trends show retained steps only. Evaluation and rewind follow native prefix rules.

The core publishes neither arm of a failed paired advance. Step, run, pause and stop
use the common session scheduler and generation barriers. Only all 600 observations
produce a valid portable record. Incomplete progress checkpoints contain specification,
retained step and lifecycle metadata; their durable step is zero, record hash absent,
and they do not contain recoverable numerical frames. The UI labels their explicit
export as progress metadata. Recovery never resumes a controller prefix or synthesizes
a stopped/failed native record. A full record is verified before Library publication
and retained for exact-byte recovery/export. Close/quit still reviews unsaved progress.

## Snapshots, Library publication and recovery

Persistence serializes writes for the current experiment and atomically publishes
completed snapshots. Checkpoint state, saved Library state and current numerical
state are separate. Recovery can expose a completed checkpoint and identify an
incomplete write; it must not invent the missing tail, a successful journal receipt
or an automatically resumed experiment.

Save to Library verifies and publishes a portable snapshot through the immutable
content-addressed store. Local creation/import time and provenance stay in metadata,
outside the scientific record. Created entries are labeled separately from imported
and bundled entries. An index failure does not erase an already published file, and
refresh can recover its index entry. Identical bytes retain their existing entry
and provenance rather than being overwritten by embedded ID.

Export uses an explicit native Save dialog. Failed saves retain evidence in memory
with a useful error and recovery action. Quit and window close must pause scheduling,
wait for pending writes and keep the app available while unsaved evidence requires a
decision. Explicit discard is separate from a successful save. A crash has weaker
guarantees: only completed, validated retained files are offered for inspection/export.

## macOS quit integration

The pinned Tao runtime delivers `applicationWillTerminate:` without the earlier
`applicationShouldTerminate:` veto. A packaged check exposed that a predefined
AppKit Quit item could therefore bypass Tauri's `ExitRequested` guard. The application
now routes its own Quit item through the session guard and installs the same guard
on the actual macOS delegate's cooperative termination callback. The narrow subclass
adds no ivars, preserves inherited lifecycle methods and refuses startup if the
expected delegate contract changes. This integration must be requalified when Tao,
Tauri or the macOS application lifecycle changes. It does not intercept force quit.

## Qualification gates

Meaningful automated checks cover step boundaries, pause/reset races, late updates,
write/readback failures, idempotent retry, terminal failure, export eligibility,
snapshot/index failure and recovered/incomplete files. Generated Explore, stage and
journal records must pass unchanged Swift verification, with changed-weight controls
rejected independently. Real desktop checks separately cover creation, stepping,
run/pause, reading journals, Save/Export, reset/close decisions and relaunch.

The full personal LLM loop still needs versioned continuation and qualified
observation contracts, automatic journal saves, budgets, sleep/recovery handling and bounded
soak tests. No live Being producer, prompt, workspace, runtime or research schedule
is changed by this implementation.
