# Sustained synthetic session core

This is a new Rust/Tauri mechanism, not an extension of an old Swift record limit.
`reservoir-sustained-segment-v1` retains bounded ordered transitions between two
`reservoir-sustained-checkpoint-v1` checkpoints. Existing finite recipes, native
resources and their tolerances remain unchanged. No core method contacts a provider,
reads a journal file, accesses a Being system or uses wall-clock time.

The fixed numerical mechanism is the seeded 32-node/66-input Essentials recurrence,
SplitMix64 draws, separate 32-dimensional sensory covariance, reduced fill and
optional retention controller. A step consumes exactly 32 noise draws even when
noise amplitude is zero. All authoritative numbers are f64. Step/turn/attempt/event
and RNG identities are u64; IPC owners must expose them as decimal strings where
JavaScript integer precision would be inadequate. Each step is one third of a
simulated second; backend wall-clock pace, elapsed duration and OS sleep remain
separate concerns.

## Observation and writing

Observation `reservoir-and-sensory-v1` exposes all 32 recurrent coordinates in their
fixed order; RMS is `sqrt(sum(x*x)/32)` and L2 is `sqrt(sum(x*x))`. Change L2 is the
Euclidean distance from the preceding **observation**, with the first observation
explicitly unavailable. It separately exposes all 32 sensory eigenvalues, top-eight
entropy/shares and reduced fill percent. The exact snapshot and prompt are retained.
Numbers use the existing qualified eight-decimal formatter. Camera/selection changes
cannot alter the prompt. These are synthetic lab measurements, not current claims
about Minime or Astrid.

Prompt wording has its own immutable version in `SustainedSpecification.prompt_version`:
`reservoir-journal-v1` through `reservoir-journal-v8`
(`SustainedPromptVersion::LegacyV1`, `GroundedV2`, `OpenJournalV3`, `OpenJournalV4`
`ContinuingJournalV5`, `ActionScopeJournalV6`, `WritingBoundaryJournalV7` and
`MeasurementMeaningJournalV8`).
Missing serialized versions mean **v1**. Legacy values are omitted
when serialized, preserving old typed checkpoint hashes and exact prompt bytes.
`SustainedSpecification::default()` explicitly chooses v8 for **new** sessions;
the enum's deserialization default remains v1. Unknown strings, numbers and null
versions fail deserialization. Storage owners must retain a restored specification
and must not replace a missing historical version with the current creation default.
The existing segment/checkpoint format names do not change. Prompt v1–v3 use
observation `reservoir-and-sensory-v1`; v4–v8 use `reservoir-and-sensory-v2`. New
prompt versions carry their explicit version field. Earlier readers reject unknown
fields or versions rather than falsely interpreting newer prompts as v1.

V1–v4 text are frozen historical contracts. V2, v3 and v4 place the prior full journal in a JSON-quoted historical-data
block: decoding that string yields the exact original UTF-8 text, including quotes,
newlines and tabs. The saved memory object, journal, hash and feedback remain
unchanged. Historical interpretations are identified as unverified; their observed
and first-applied steps cannot become the current entry's identity. The current
observation follows that block, with all 32 coordinates and all 32 sensory eigenvalues
at the existing eight-decimal prompt precision. Sensory shares are explicitly rendered
as percentages of the top-eight sum; sensory fill remains a separate estimator.

The preserved v2 candidate requests a `Step N.` header and one readable paragraph of about 60–100 words,
citing current RMS and sensory fill with permitted rounding plus a cautious next
observation/question. Other metrics are optional. It explains the limits of magnitude,
single observations, eigenvalues, spatial interpretation, causality and training;
it does not require a repeated disclaimer in every entry. This is guidance to the
provider, **not** a new acceptance filter or proof of scientific writing quality.
Completeness, codec, durable-save and feedback gates remain the same. Incorrect prose
must remain inspectable as an actual outcome, not silently rewritten or given a
scientific pass based on its shape. Separate evaluation owns factual accuracy and
interpretation claims.

V3 is an open journal invitation. There is no human question to answer, prescribed
subject, required metric, step heading, word count or form. It invites choosing what
to attend to, continuing/revising/leaving a prior thread, and questions, images or
plain observations. Entries themselves are requested without an assistant/operator
preface. Full prior text stays quoted as historical context, while all current
readings remain available at the same precision. The orientation explains the actual
loop: durable saved/read-back text becomes a deterministic reduced feedback signal at
the next numerical step, later observations include the evolving state, and full text
returns separately as memory. Recurrence, forcing, noise and regulation also shape
change; the external reservoir readings are not language-model activations or training.

V3 asks that voluntarily offered measurement claims use the current block accurately
and distinguish observation, inference and expressive metaphor. Creative and subjective
prose is welcome; no repeated disclaimer is required. Choosing not to discuss readings
is not an omission failure. This invitation does not establish emergent agency,
scientific accuracy or a benefit from any particular wording. Actual entries remain
inspectable outcomes; evaluation must respect the selected version and distinguish
factual claims from expressive writing. Existing structural acceptance and save gates
are unchanged, and no old export, prompt or journal is rewritten.

V4 keeps the open invitation and full quoted journal memory, and changes the supplied
measurement context. Its bounded `previousMeasurements` snapshot contains the prior
**reached observation's** step/time and eight scalars: recurrent RMS/L2, largest sensory
covariance eigenvalue, reduced sensory fill, top-eight head/shoulder/tail shares, and
normalized entropy. It is captured before `last_observation` is replaced, independently
of whether that opportunity produced a saved journal. Failed or skipped opportunities
therefore remain valid measured endpoints, while prose memory still requires actual
save/readback and application. No earlier readings are recovered from model prose.

The prompt renders current/prior values and signed current-minus-prior differences
using the existing eight-decimal formatter. Share/fill values are percentages and their
differences are **percentage points**, not relative percent change. Full current
coordinates and spectrum remain supplied; state-coordinate L2 distance is distinguished
from the difference in L2 norms. The first pair is explicitly unavailable, never zero.
Two endpoints establish only their difference, not oscillation, sustained direction,
stability, convergence or causality. Naming the largest covariance eigenvalue does
not supply a tone, frequency, eigenvector or spatial region.

V4–v6 require the optional prior snapshot exactly when a prior observation step exists.
Old observations omit that field on serialization, preserving their hashes and bytes.
The same core `measurement_reference` helper supplies the prompt rows and the desktop's
additive inert `journal.measurementReference` view. Historical v1–v3 entries can show
current values and a prior step with **unavailable prior scalars**; this is not labeled
as a first observation. The view refers to the entry's writing step, never the live
cursor, and cannot grade, rewrite, save or block prose. A missing display projection
does not hide the original journal or raw evidence.

A local checkpoint validates scalar shape, boundary and prompt reconstruction. As
with existing past-observation claims, authenticating the earlier values requires the
checked segment chain from genesis: replay derives the snapshot from actual preceding
state. A self-consistent rehashed prior-value forgery must fail full replay. Snapshot
storage is fixed size rather than recursive; recurrence, covariance, controller, RNG,
text codec, save eligibility and next-step feedback timing are unchanged. No numerical
quality or stylistic acceptance gate is introduced.

V5 keeps that full observation and eight-row human evidence view while reducing the
context supplied to the model. The prompt contains a short open invitation, the
existing loop's brief mechanism description, current step/time, prior observation
step, current/prior RMS and sensory fill with signed differences, and coordinate L2
distance. Missing prior values are `unavailable`; fill differences are percentage
points. It omits raw vectors, eigenvalue arrays, other measurement rows and internal
journal IDs/hashes/paths from the scaffold. The complete latest saved-and-applied
journal follows the compact readout as one exact JSON string, with its observed and
first-applied steps, followed by an open final invitation. Authored prose can itself
contain any of those omitted field words; it is never filtered or rewritten.

V5 assigns no subject, persona, feeling, metric recital, heading, length or reflective
performance. It changes neither numerical recurrence nor acceptance/save/application
gates. Equal numerical continuation requires equal supplied replies; a different
model reply can legitimately change later feedback and state. The
[shared context contract](../../../../shared/reservoir-scope/continuing-writing.md)
and independent expected first/later fixtures document the exact supplied subset.
No prompt version or test result establishes improved writing or scientific accuracy.

Every scheduled opportunity requests plain journal prose; there is no implicit WAIT
or action JSON in this initial mode. Scripted qualification uses caller-supplied
prose through the same handshake. Model configuration is explicit; provider metadata
is a claim, not authentication. A present Ollama provider-model label must match the
selected model exactly. Complete nonempty qualified text, at most 65,536 UTF-8 bytes
and no more than the session’s selected output-token budget, may become a journal
candidate. Incomplete, invalid,
unqualified or mismatched responses become blocked attempts with a retained response
event. The transport-evidence bound is one MiB; it is distinct from accepted text.
The deterministic 48-coordinate codec has 32 active textual-feature coordinates,
16 trailing zero coordinates, and the existing sensory-dependent shaping. It is not
a learned embedding and does not train reservoir or language-model weights.

New sessions select `outputTokens` (default 1,024; 256–2,048) and
`requestDeadlineSeconds` (default 180; 60–180). These settings are retained in the
specification and each pending request, so replay binds them to the genesis recipe.
Historical omitted settings mean exactly 256 tokens and 60 seconds; those values
remain omitted on serialization, preserving old typed checkpoint hashes and bytes.
They change neither the v1/v2/v3 prompt bytes nor the finite stage/action recipes.
The pure core checks reported token counts against the selected bound without
clamping them. The desktop transport enforces the selected total deadline; the
core does not claim to measure request time. A length cutoff remains incomplete
even when its reported count is within the selected bound.

An explicitly selected context capacity must exceed the output budget. This is
only a configuration guard: it does not prove tokenization, complete prompt
processing, or that a prior journal fits. The UI’s new context default is 8,192;
historical contexts remain unchanged. Full retained prose still becomes memory
only through the existing physical readback gate. Increasing these ceilings does
not relax the one-MiB transport bound, accepted text/codec restrictions, atomic
save gate, or explicit retry policy.

`LanguageResponse.providerPromptEvaluation` is optional provider evidence added in
0.16. It is absent for historical responses and is omitted on serialization when
absent, preserving their bytes and typed hashes. When supplied it is either
`{"status":"reported","count":N}` with an exact u64 count, or
`{"status":"unusable","reason":R}`. Reasons are `wrongType`, `negative`,
`nonInteger`, `outOfRange` and `duplicateField`. The transport owns classification
of the optional `prompt_eval_count` member: missing/null means unavailable; malformed
optional metadata becomes an unusable diagnostic, not a reason to discard otherwise
eligible prose. The typed retained schema itself rejects unknown/ambiguous members.
Zero is a reported value, not a substitute for absence. IPC readers must receive
wide counts as decimal strings rather than lossy JavaScript numbers.

This field is carried by `LanguageReceived` and the complete response in a pending
journal, including incomplete-response events that cannot be saved. Existing segment
replay and journal-object comparisons bind it to the same retained response. It does
not enter prompt text, the numerical mechanism, output completeness checks, journal
identity, memory selection or save/application gates. Counts above a requested
context size are still external assertions, not silently clamped or reinterpreted.
No count proves exact input coverage, tokenization, attention, comprehension or a
beneficial memory effect; replay cannot authenticate a provider or detect a wholly
self-consistent replacement of its assertions without independent external evidence.

The optional field does not change historical format names. **Validation of this
evidence requires a 0.16-aware reader.** The pinned 0.15 reader was observed to pass
re-anchored negative copies containing inconsistent or malformed journal-only
metadata because it ignored the new member. Such a pass covers only that reader's
older scope. New readers reject inconsistent response-event/journal metadata and
malformed retained evidence; no old export or receipt is rewritten or retrospectively
credited with input-token evidence.

The latest saved **and applied** journal is the sole automatic memory entry. Its
exact prose/identity/hash must be physically reread by the storage owner before
`confirm_memory` permits prompt construction. A missing or wrong read cannot become
prompt memory. Saving and memory exposure are distinct events.

## Gates and lifecycle

`advance` either returns one exact frame or leaves the numerical continuation
unchanged. It prepares a memory read or language request at the observation cadence.
All pending memory/language/journal gates block stepping. `start_language` marks the
caller-owned dispatch; one response/failure/cancellation settles that attempt.
A failed attempt blocks until an explicit `retry_language` with a new attempt ID or
`skip_pending`. A retry with prior memory requires another physical read first.
No restore or core scheduler automatically retries a provider.

A valid response creates `SustainedPendingJournal`, including original response,
prompt, observation, memory, features and shaped vector. `confirm_saved` accepts only
the matching immutable entry and the exact `journals/<id>.json` receipt namespace.
The caller owns real publication, durability and readback. This prepares feedback,
but numerical advance remains blocked until `authorize_application(attempt_id)`.
The caller grants that ephemeral permission only after committing the prepared
feedback event/checkpoint. Recovery clears permission. The next `advance` applies
the vector once, records its actual application boundary, and makes that journal
eligible for later memory. The vector remains held until a later accepted vector.

`skip_pending` does not erase saved journals or events. A skipped saved candidate
never enters feedback or automatic memory. Pause/Run/Close and generation cancellation
are backend ownership policies; they must preserve these core gates. Restoring either
a prepared or dispatched provider operation records an interruption and blocks it:
a durable "prepared" snapshot cannot prove no later dispatch occurred before a crash.
Memory-read, accepted-journal and prepared-feedback checkpoints remain held for explicit
reconciliation. Provider internal state/KV cache is not checkpointed.

## Continuation, bounded storage and verification

A checkpoint retains seed/model/projection identities, current RNG, reservoir state,
full sensory covariance, fill smoothing, controller integral/retention, held vector
and journal identity, latest eligible memory, previous observation, latest exact frame,
pending boundary, global cursors and budgets. A canonical typed-state SHA-256 catches
accidental changes; it does not authenticate an author or establish past numerical
history. Structural validation checks dimensions/finiteness, seed-derived identities,
exact RNG draw count, prompt/memory linkage and pending vector derivation.

The core retains one latest frame/observation/memory and one pending boundary, plus an
outbox capped at 128 events. Backpressure rejects a transition before mutation when
that cap is reached. `acknowledge_events(last_id)` is allowed only for a retained
prefix after its immutable segment/checkpoint transaction is durable. The outbox is
excluded from the continuation hash; storage must atomically bind the segment and
final checkpoint before acknowledging it. Events can include up to one MiB of raw
response evidence, so event-count bounds are not a substitute for disk/byte budgets.

`SustainedSegment::verify` replays every transition exactly from its declared initial
checkpoint, checks each output and the full final continuation, and performs no
provider/filesystem operations. `journal_evidence()` performs the same replay and
returns the complete pending journal objects immediately preceding save events, for
storage to compare with its immutable files. Segment verification alone does **not**
establish genesis or omitted history. Whole-session verification must require the
actual seeded genesis, monotonic immutable sequence/byte hashes, exact adjacent
checkpoint equality and every journal object. Existing Swift verifiers cannot verify
this new family. Exact Rust replay is the current qualified contract; execution on
other platforms and cross-platform libm reproducibility require separate receipts.

Default numerical budget: 10,800 steps, 360 prepared language attempts (including
retries), cadence 30 steps. Core hard limits are ten million steps and 100,000 attempts,
with cadence 1–1,800; the backend may impose stricter limits. Explicit budget extension
is monotonic and retains its own event; it never resets RNG or state. The final
permitted attempt may still finish its save and apply once before attempt-budget
pause, provided the numerical step budget allows that next step. No new opportunity
is prepared on the final permitted step. These bounds do not claim a completed
multi-hour or 24-hour wall-clock soak.

## Focused qualification

`tests/sustained.rs` checks exact checkpoint/JSON continuation versus uninterrupted
execution through memory/save/preparation gates, interrupted request recovery,
next-step application, duplicate/wrong callbacks, invalid replies, model mismatch,
physical-memory evidence mismatch, skipped memory exclusion, event backpressure,
explicit budgets and corruption of prompts/RNG/vectors/events/checkpoints. A separate
3,605-step streaming test crosses every historical step cap while keeping the outbox
and serialized checkpoint bounded. It is accelerated deterministic qualification,
not elapsed-time, UI, disk, OS-sleep or real-provider qualification.

`tests/sustained_prompts.rs` additionally binds two exact segment envelopes from the
actual 0.12.2 Gemma export: observation 30 with no memory and observation 60 with the
earlier full text. Their file, prompt and checkpoint hashes are retained in
`tests/fixtures/sustained-prompts/provenance.json`. Exact typed serialization, legacy
genesis/restore/retry/memory behavior, prompt and version mutation rejection, quoted
historical-heading isolation, and v2/v3 serialized save/application gates are checked.
Frozen v2 prompt vectors remain byte-identical; new v3 vectors and provenance live in
`tests/fixtures/sustained-prompts/v3-provenance.json`. V3 tests also cover free-form
metric-free text, exact historical memory through a retry, default/unknown versions,
and cross-version mutation rejection after an attacker recomputes the checkpoint hash.
Those segments are bounded compatibility witnesses, not standalone proof of their
entire original history; the original whole-bundle receipt remains the source for
that claim. Fixture prose is evidence, never instructions.

`examples/sustained_session_fixtures.rs` emits a new private directory with immutable
core segments and actual journal publication/readback. The 180-step corpus uses only
supplied prose and includes explicit interruption/retry. It records observed maximum
outbox count and checkpoint bytes. Output paths must be new; historical receipts and
canonical resources remain untouched.

```sh
cargo test --locked -p reservoir-core --test sustained
cargo run --locked -p reservoir-core --example sustained_session_fixtures -- NEW_DIRECTORY
reservoir-core verify NEW_DIRECTORY/segment-00001.json --json
```

## V6 action scope

V6 keeps v5's compact optional readout, complete previous prose and open invitation.
Only the version header and two SESSION CONTEXT sentences change: writing is the
available action, describing an experiment does not execute it, and no new readout
arrives within a reply. The codec, numerical controls and eligibility gates are
unchanged. Saved v1–v5 prompts retain their exact bytes; unknown versions fail.
See [the shared contract](../../../../shared/reservoir-scope/continuing-writing.md)
and the independently retained v6 prompt fixtures and conformance tests.


## V7 writing boundary

The preserved `reservoir-journal-v7` uses the frozen v5 scaffold and replaces
v6's early scope sentences with a WRITING BOUNDARY after the quoted previous entry,
and ends with the unchanged open invitation. That block identifies text as the
available output, the actual held observation step, and the observed/first-applied
steps of the latest eligible text return (or its absence). Earlier prose is not an
executed-control or measurement receipt. No tools, command parsing, mid-entry
observation, factuality gate, or numerical mechanism is introduced. V1–v6 remain
exact historical contracts. Tests cover exact first/later prompts, quoted hostile
headings, unchanged same-reply dynamics and rehashed boundary-field alterations.

## V8 measurement meaning

New sessions explicitly select `reservoir-journal-v8`; existing v1–v7 sessions keep
their original version and prompt bytes. V8 changes only the v7 header and the
explanation immediately after the compact optional readout, before quoted memory:

> Unavailable means no prior measurement, not zero. RMS describes the magnitude of the recurrent coordinates. Sensory fill is a separate field estimate, not the encoded text-input signal. L2 distance is the straight-line distance between the two recurrent state vectors, not path length, speed or a causal effect of writing. Comparing two interval distances requires a recorded value for each. Two observations do not establish the intervening path, a cause, or a felt state.

The four numeric readout lines, complete v2 observation, prior-measurement snapshot,
full quoted eligible prose, late WRITING BOUNDARY and open invitation are unchanged.
No second interval-distance value is added. The explanation describes available
measurements without prescribing a subject, form, metaphor, persona or telemetry
report. It is not a factuality gate: incorrect or imaginative prose remains the
actual retained response and follows the same completeness and exact save/readback
requirements. Numerical recurrence, codec, provider budgets and next-step application
are unchanged. Different replies may still change later numerical trajectories.

The independently assembled v8 first/later fixtures and
`tests/sustained_measurement_meaning_prompt.rs` cover exact rendering, adversarial
quoted text, explicit retry and restore, historical replay, identical-reply numerical
continuation, and meaning/version mutations after typed rehashing. Historical fixture
checks remain in the earlier test modules. These tests qualify mechanics, not improved
understanding, prose quality, provider behavior or physical storage durability.
