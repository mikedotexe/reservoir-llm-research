# Finite session backend

The backend owns one finite in-memory numerical session, its scheduler, generation
and revision checks, journal filesystem, and retained checkpoints. Navigation and
WebView timers do not advance its numerical clock. Scripted recipes remain offline synthetic
experiments. An explicitly configured local model can now supply responses at
eligible finite-session boundaries; no live-system access is part of this feature.

## Explicit local models in 0.11

`SessionConfig.language` is additive and defaults to the existing scripted
configuration when absent. Operational model configuration is validated before an
accepted session can be replaced. Only original stages 3/4 and independent action
D–H permit `ollama`, including matched components and D/D observation. Original
stages use prose; actions require `responseFormat="json"`. Fixed replay, Explore,
stages 1/2, actions A–C and field-only regulation never invoke a model. Create,
Reset, configuration edits, navigation and subscription attachment do not send a
request. Readiness is a separate explicit operation and is not generation proof.

The session owns each provider operation. When a numerical or manual opportunity
has reached its boundary, the core prepares the exact prompt. F/G/H first reread
their required committed journal from the owned arm directory. The backend writes
bounded intent metadata, then dispatches an owned worker outside the session
mutex. The shared transport bounds the whole request to 60 seconds and one MiB;
its explicit HTTP loopback endpoint, no redirects/proxies/retries, response limits
and cancellation are tested separately. Context tokens come from the accepted
configuration; output tokens remain 256 and temperature zero. No service is
started and no model is pulled or substituted.

The live phase `awaitingLanguage` holds the numerical clock. The bounded summary
`pendingLanguage` names the operation, arm, turn and observed step, configured
endpoint/model, and state (`prepared`, `requesting`, or `compatibilityBlocked`).
It does not include prompt or growing history. `pendingWrites` continues to mean
filesystem work. Stop cancels the operation and retains the native terminal
cancellation; Reset or explicit close discard also invalidates it. A completion
must match the accepted session, generation and unique operation, and must not be
cancelled. Late results cannot append receipts, create journals or prepare
feedback. HTTP work never holds the numerical lock or waits for a WebView timer.

Pause leaves an already-dispatched request free to settle, but stops further
numerical scheduling. This finite implementation also pauses after a successful
provider boundary; Run/Step remains explicit after the response or journal save.
A required paired peer can be dispatched after the previous arm settles, with
both numerical clocks held. Component failure cancels an unstarted peer;
observation attempts its peer after an ordinary failure. Explicit Stop always
stops the whole pair. Exact request order comes from the core receipt, not from
response arrival order. Manual-step completions notify the same subscription as
Run completions, including while the workspace is hidden.

Transport failures remain language failures; invalid complete responses retain
response-validation outcomes. A response outside the independently qualified
codec/parser contract remains `compatibilityBlocked` with an explicit diagnostic.
It is not retried and cannot be exported as an accepted portable result; Stop
retains cancellation without introducing unqualified feedback. Valid WRITE still
requires actual atomic journal publication and exact readback. WAIT keeps the
previous held feedback. Provider acceptance never bypasses the existing save gate.

Recovery adds `pendingLanguage` with operation/session/generation identity, the
exact prepared prompt, accepted language configuration, and dispatch flag. It is
checked as bounded structural metadata against the checkpoint and prior portable
record. A pending pair also retains its already completed peer evidence. A crash can retain the older prepared checkpoint after dispatch began; a false
`requestStarted` in that historical snapshot is not proof that no later request
was sent. Recovery never repeats it. Compatibility-blocked response evidence
retains exact text up to 65,536 UTF-8 bytes, or an explicitly marked prefix plus
the original byte count and SHA-256; provider metadata has separate truncation
flags. Stop preserves it in `rejectedLanguage`, separately from the native
cancelled portable receipt. It remains inert evidence with no feedback eligibility.
The
current observed step can exceed the portable `durableStep`; the previous record
is still the last fully settled portable snapshot. Inspection/export does not
resume or repeat a request, prove that a provider is still running, or claim
numerical replay of an unresolved boundary. Older checkpoints without the new
field continue to decode without being rewritten.

## Fixed field-only controller scope in 0.10

`regulation` creates the native `uniform66-seed42-field98-v1` teaching study:
600 observations, field seed 98, common input seed 42, dt 1/3, initial retention
0.955, target 68%, and the fixed evaluation window 301–600. These controls are
locked and validated before replacing any accepted session. The generic form's
unused settings must retain their declared defaults. This recipe has two sensory
fields and no reservoir recurrence, language request, turn, journal, or return lane.

`RegulationSession` advances both fields transactionally under the existing
backend-owned session clock. Step, run, pause, stop, reset, generation/run-epoch
checks and cooperative close review use the same lifecycle as other recipes.
Navigation does not own that clock; Stop is terminal for the accepted session.
A reset creates a new identity and starts the fixed experiment again.

Subscription `frame` and `frames` are null for this recipe. Its separate bounded
`regulationFrames` carries baseline/regulated input (66 values), projected field
(32 values), spectrum (32 values), fill, used retention and actual next-step
control. The field vector is the native activated-input projection after RMS
normalization; it is not a reservoir state or the unprocessed weight product.
No covariance matrix or growing history travels on the channel. Before the first
step, no numerical frame is invented. `regulationSpec` carries the exact fixed
specification with both seed identities represented as decimal strings.

Selected frame reads return a separate `regulationFrame` and recompute evaluation
evidence only through that cursor. The evidence is absent through step 300,
partial from 301 through 599, and complete only at 600. Rewinding never retains a
future mean or completion label. Explicit `get_session_regulation_details` reads
return the 2112 projection weights plus at most 600 scalar trend points, bounded
by a requested cursor no later than the retained clock. It echoes session,
generation, revision and cursor; the frontend does not repeat this matrix read on
every channel update.

The native portable format requires all 600 frames. Before completion, Save to
Library and portable export are refused. Checkpoints instead include additive
`regulationProgress` with retained step, fixed specification and explicit portable
completion state. They keep `durableStep=0` and no record hash. This is bookkeeping
only: no partial numerical frames or resumable controller state are persisted.
Explicit progress export first checkpoints the current paused state and exports
that metadata through the existing recovery path. Stop and quit do not promote
partial metadata into a portable result. Recovery never automatically resumes it.
At completion the existing bounded atomic snapshot, Library verification and
record hash checks apply to the complete `essentials-regulation-v1` bytes.

## Standalone and matched action scope in 0.9

`actionA` through `actionH` select the native component ladder. The older
`journalD` and `journalE` recipe values remain accepted aliases for stages 4 and 5.
Existing Explore and original stage 1–4 recipes are unchanged. Action recipes retain `essentials-actions-v3`, with at most 600 frames and 128
action opportunities per arm. Standalone A–H remains available. Component pairs
B–H compare the selected stage on the right with the preceding stage on the left.
There is no predecessor for A, so an A pair is rejected. Observation compares two
D arms under independent generation, with sensory-only context on the
left and sensory plus reservoir coordinates on the right. Field-only controller
comparisons use the separate fixed `regulation` recipe described above.

The additive configuration fields are `actionMode` (`independentGeneration` or
`fixedReplay`, default independent), `actionInputStrength` (0–1, default 1), and
`actionBiasEnabled` (default false). Missing fields in old D/E checkpoints receive
those defaults. Recovery checks bind these fields, stage, seed, timing, numerical
controls, and comparison mode to the retained portable record. Old checkpoints
are read without being rewritten or resumed.

Fixed mode constructs the native deterministic scripted reference tape once when
the configuration is accepted. The complete retained tape travels in the portable
record. Its summary exposes format, authored origin, and packet count; it does not
claim an original external tape-file identity. External tape selection and custom
tapes are not supported. Tape replies retain `requestStarted=false` and the actual
packet ID. Independent replies use the explicitly accepted scripted or local-model configuration.

The additional 0.9 configuration fields are `actionComparePrevious` (default
false), `actionComparisonKind` (`components`, default, or `observation`), and
`actionForcingProfile` (`pulsedSensoryV1`, default, or `continuousSensoryV1`).
Continuous forcing is confined to observation. Observation requires D, comparison
enabled, and independent mode. Quiet observation uses explicit zero input strength,
zero noise and disabled bias; it is not an inferred state or a separate format.
Old checkpoints with absent fields retain standalone component defaults.

Both numerical arms are prepared before either is committed. Component journal
opportunities resolve left then right; observation alternates request order at
each opportunity. Both clocks wait until all eligible actions at that boundary
are resolved. Arm journals use separate owned directories even when a shared tape
produces identical entry IDs. `save_session_journal` binds session, generation,
arm and exact candidate entry ID under the session mutex. A late save of the left
candidate cannot save the next right candidate. The core preserves native
observation partner attempts after ordinary terminal arm failures. This
backend keeps physical-save errors retryable rather than finalizing a failure;
its explicit Stop stops the entire pair and cancels any unstarted peer. There is
no separate deliberate terminal-failure command in this tranche.

## Save and memory boundaries

WRITE candidates remain outside committed portable action history until actual
atomic journal publication, synchronization, and exact readback succeed. Failed
physical saves retain the same pending candidate and separate attempt diagnostics
for retry. Explicit stop can retain a terminal failed-save receipt. Neither a
pending nor a failed save becomes eligible for feedback or prompt memory.

At each F/G/H opportunity after a successful journal, the core names the latest
committed journal as required memory. The backend rereads that entry from its own
`sessions-v1/<session>/<arm>/<entry>.json` namespace. It validates ordinary owned
directories, owner marker, bounded regular-file bytes, parsed identity, content
hash, and exact entry equality. It never follows a path supplied in a receipt and
never substitutes the in-memory text for a missing, changed, or linked file.
Only confirmed readback lets the core prepare a prompt with that text. A real read
failure produces the native terminal `memoryRead` receipt, with expected entry ID
but no accepted memory text, reply, request, new journal, or new feedback. The
already completed numerical frame remains retained. If checkpoint storage also
fails, the in-memory failed receipt and its diagnostic remain available for
inspection/export; durable recovery still ends at the previous completed snapshot.

Memory reads resolve inside a bounded backend boundary operation. They do not
introduce a frontend-controlled retry state or a resumable crash checkpoint.
Manual requests use the existing `request_session_journal` command and force
WRITE in D–H. Its advertised eligibility comes from the core's actual boundary
and remaining-action-capacity checks.

Scheduled G/H WAIT commits a completed action with no journal-save or application
receipt. It preserves the previous held feedback and latest saved memory. The
backend checkpoints each committed action, including WAIT, in addition to the
existing 30-frame cadence and explicit lifecycle/save checkpoints. H exposes the
retention used for this frame separately from its controller's next-update output.

## Bounded reader data and lifecycle

Channel updates remain bounded summaries plus the latest aligned frame pair (or
one standalone frame), at most 10 Hz
while running. Full history and covariance matrices are not broadcast. Selected
turn reads expose actual committed journal text, original raw action JSON, exact
prompt, memory text and its retained hash, and journal identity/hash. A journal ID
or hash may describe a failed save; successful storage is indicated separately by
the save receipt. WAIT has no journal text in the main reply field.
`requestOrder` is nullable and comes only from the retained action receipt; no
order is guessed for original stage turns or other receipts lacking that field.

The scheduler's run epoch prevents stopped or replaced workers from mutating a
later session. The clean-close authorization uses a nonblocking mutex barrier and
closes the command gate atomically, including when a saved session has an in-flight
manual step. Dirty, pending, or busy sessions require explicit close review. The
macOS cooperative AppKit delegate hook and application menu use the same guard.
Force quit, crashes, power loss, and untested operating-system termination paths
are not covered by a close-dialog guarantee.

Internal checkpoint retention remains current plus previous completed portable
snapshot. A checkpoint with a pending WRITE can have a newer observed step than its
portable record's `durableStep`; those values are never presented as equivalent.
Recovery offers explicit inspection/export, never automatic numerical resumption.
For an unresolved pair, a bounded `pairedBoundary` checkpoint retains only the
current boundary's per-arm committed receipt and matching journal, alongside the
pending candidate and arm-tagged save attempts. Its metadata is checked against
configuration, arm stages, IDs, current clock, saved text hashes and relative
namespace. The previous portable record remains the last complete pair and may
have fewer frames. Partial checkpoint evidence is not numerical replay proof and
is not promoted to a portable comparison or automatically resumed. Checkpoint
export retains this distinction. A fresh SessionState can inspect a previous
process's checkpoint, but this test does not simulate physical power loss.

`tracks` describes each retained arm's actual portable outcome, counts, component
capabilities and observation channel. Global `phase` describes live execution.
Legacy `frame`, `turnCount` and `journalCount` remain right-arm values; `frames`
contains an aligned left/right pair. Selected frame/turn commands accept `trackId`
(default right) and echo it with generation/revision. No growing numerical history
or covariance is included in subscription updates.

## Qualification

Run from `desktop/ReservoirScope` with the pinned toolchain:

```sh
cargo test --locked -p reservoir-scope-desktop sessions::tests
cargo clippy --locked -p reservoir-scope-desktop --all-targets -- -D warnings
```

Tests cover both modes across A–H, successful memory exposure, missing/tampered/
linked saved journals, manual versus scheduled action policy, WAIT feedback
continuity, actual controller fields, old checkpoint defaults, configuration
tampering, save retry, terminal failure, worker generations, and close barriers.
Controller tests additionally cover complete 600-frame Library publication and
reopen, strict partial-record export refusal, prefix/rewind evidence, locked
configuration, metadata corruption, stopped checkpoint retry, generation and
worker replacement, and unsaved close review.
Paired tests additionally cover matched component modes, observation order and
forcing, arm-bound saves, separate journal namespaces, half-boundary reopen and
corruption rejection, and persistence failure after the first physical save.
Model tests additionally exercise explicit eligibility without contact on create,
manual-step subscription delivery, held clocks, cancel/reset and late completion,
actual loopback HTTP requests, model versus provider provenance, save-before-feedback,
observation failure ordering, unqualified responses and checkpoint failures. These
use isolated fake providers, not a real model service.
Independent unchanged Swift verification is recorded separately from backend
filesystem tests and packaged UI observations. No Windows/Linux execution, power
fault durability, long-running load, or human acceptance is implied by these tests.
