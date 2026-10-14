# Incremental offline sessions

`session.rs` runs the original bounded stage 1–4 recipes and standalone A–H
action experiments. `comparison.rs` adds paired component and observation
sessions. `exploration.rs` supplies the existing
incremental Explore engine. There is no provider, filesystem, scheduler or wall
clock in these engines. These are isolated synthetic mechanisms, not observations
of the current Astrid or Minime systems.

## Supported contracts

- `StageSession` accepts the existing `RunSpecification` with a scripted backend,
  up to 3,000 steps. Each call returns one frame. Stage 2 uses the three prepared
  examples; stages 3–4 use the existing four scripted replies. They retain original
  `essentials-v1` turns. Stages 3–4 may instead hold an explicit Ollama-configured
  language opportunity for the caller to dispatch and settle. A language turn is
  not a journal-save receipt.
- `ExplorationEngine` retains its existing 1,800-step contract, including per-step
  controls and explicit pulses. Its portable record is an exploration prefix.
- `ActionSession` (the source-compatible alias of `JournalSession`) accepts an
  `ActionSpecification` for standalone components A–H (stages 1–8), independent
  scripted generation or fixed replay, one right arm, up to 600 steps and 128
  actions. Existing validation permits pulsed sensory forcing here. It emits
  `essentials-actions-v3`. Independent D–H may also use the pending-language
  handshake. Its standalone 0.8 API remains compatible.
- `comparison::ActionComparisonSession` accepts paired components B–H (right
  stage 2–8 against its predecessor), in independent scripted or fixed-replay
  mode. It also accepts the native separate D/D observation comparison:
  independent scripted mode, sensory observation on the left, sensory plus the
  actual 32 reservoir coordinates on the right, pulsed or continuous forcing.
  The same 600-step/128-action bounds apply. A has no predecessor and is rejected
  by this pair constructor. Independent D–H component comparisons and D/D
  observation comparisons support the same caller-owned provider handshake.
  Fixed replies remain scripted and never initiate a provider opportunity.

All existing numerical, seed, prompt, bounds and verification rules remain in
effect. Journal D/E uses the separate 32-dimensional sensory observation in its
prompt, not a newly invented observation of reservoir coordinates. The text codec
is the existing deterministic textual-feature codec, not a learned embedding.
Actions A/B have no sensory observer or reduced fill; C–H do. A disables recurrent
weights while retaining leaky state, and B enables recurrence. D prepares features
and a spectral feedback vector after save but leaves the feedback gate closed.
E–H make that saved vector eligible for the next step. F–H require rereading the
latest saved journal before supplying its prose as prompt memory. G/H permit a
scheduled WAIT. Only H introduces the sensory retention controller: a frame's
`retentionUsed` precedes its `control.appliedRetention`, which applies next step.

## Pending language and supplied responses

The 0.11 core adds no network client. Accepting an Ollama `LanguageConfiguration`
means the caller may fulfill a pending operation; it is not a model discovery,
readiness, dispatch, or authenticity claim. The existing pure scripted and fixed
tape paths still settle synchronously and create no `PendingLanguage`.

`session::PendingLanguage` retains `turn_id`, `observed_step`, the exact
`configuration` and `prompt`, `request_started`, and optional `request_order`.
Its serde names are camelCase. Stage and journal engines expose the borrowed
`pending_language()`. The pair engine returns `(Arm, &PendingLanguage)` for its
current ordered opportunity. The additive settlement API is:

| Method | Effect |
| --- | --- |
| `start_language(id, step)` | Mark actual caller-owned dispatch; rejects a wrong boundary or second dispatch |
| `confirm_language(id, step, &LanguageResponse)` | Settle one supplied complete, incomplete or invalid response under the native stage/action rules |
| `fail_language(id, step, reason)` | Retain a dispatched operation's provider-free failure, such as transport failure or timeout |
| `cancel_language(id, step, reason)` | Retain explicit cancellation before or after dispatch; later responses are rejected |

Pair methods take `Arm` before the same arguments. The backend must additionally
bind session identity, generation and operation identity, and arbitrate timeout,
stop and response races outside the core. All core methods are synchronous and
contain no filesystem or network calls. `LanguageResponse` contains `text`,
`provider_model`, `stop_reason`, optional signed `token_count`, and `complete`.
The provider-model label is retained metadata; the native contract does not prove
which model produced the text or require that its label equal a configured alias.

Every pending opportunity blocks numerical advance. Stage views may borrow
`record()`, but portable export must use `portable_record()`, which rejects an
unresolved language boundary. Journal and pair `record()` already reject all
pending memory, language and save boundaries. Pausing may leave a dispatched
response outstanding; settling it does not advance a numerical step. Stop is
terminal: stages cancel their pending operation, and a pair cancels an unstarted
peer instead of dispatching it. A standalone journal caller explicitly cancels its
language operation before ordinary `stop()`, just as it must resolve memory/save.

For original stages, a complete nonempty bounded reply prepares the existing
48-coordinate text feedback and first applies it at the next recorded step.
Incomplete, length-limited, excessive/negative-token, empty, oversized, failed or
cancelled replies cannot produce feedback. The original stage format retains no
`requestStarted` field; its pending DTO distinguishes preparation from dispatch.

For D–H, any latest saved memory must be physically reread and confirmed **before**
the prompt is exposed to the caller's provider. A valid WRITE response creates the
existing pending journal candidate. It does not claim a save or become eligible
for feedback until the storage owner confirms atomic save/readback. A valid WAIT
creates no journal or new vector and preserves the previously held feedback.
Manual opportunities still require WRITE. Component failures cancel the unstarted
partner; observation-comparison failures still attempt the partner in the native
alternating order. Request ordinals become retained claims only at actual dispatch.

Unqualified Unicode, ambiguous Foundation-versus-serde JSON and unrepresentable
retained metadata are compatibility limits, not fabricated native response failures.
They leave the opportunity pending without save or feedback. A received response
may be confirmed only once: another response cannot replace it, and it cannot be
rewritten as a provider-free failure. Explicit cancellation/discard remains possible.
The backend owns bounded raw-response diagnostics/checkpoint evidence for that
unresolved outcome; the core does not invent an unsupported portable receipt. This
session implementation follows the native cancellation path and omits unaccepted
response text from its portable turn. The original stage verifier also permits
inert `rawReply` diagnostics on cancelled turns; it still forbids accepted `reply`,
features, semantic vectors or application. Action cancellation has the stricter
native no-response-outcome contract.

Core response fixtures use supplied typed values; they do not contact a model.
`tests/session_language.rs` covers stage 30→31, exact dispatch and wrong-boundary
guards, all independent D–H and their preceding-component pairs, observation order,
WRITE/save/memory/WAIT, failures, cancellations and compatibility-blocked responses.
The pre-existing session suites continue to check scripted and fixed-tape behavior.
`examples/language_session_fixtures.rs` generates separate original-format records
using injected provider outcomes and actual fixture-directory journal writes and
reads. A new output directory is required; earlier qualification corpora remain
unchanged. Run it for independent unchanged Swift verification:

```sh
cargo test --locked -p reservoir-core --test session_language
cargo run --locked -p reservoir-core --example language_session_fixtures -- NEW_LANGUAGE_OUTPUT_DIRECTORY
```

The generator's manifest explicitly distinguishes supplied-response fixtures from
HTTP transport, model execution, app storage and provider-authentication evidence.

The 0.11 check retained in
`validation/2026-10-13-models-0.11.0/fixture-conformance-final.json` accepted all
63 generated originals in unchanged Swift and Rust, rejected 567 targeted
corruptions in both, and accepted six inert-raw stage-cancellation compatibility
controls. The first receipt remains alongside it: all originals passed, but six
controls incorrectly assumed native stage cancellation prohibited raw diagnostics.
Only that checker assumption was corrected; the corpus and verifiers did not
change. This bounds numerical/text compatibility of supplied responses, not actual
provider execution or app persistence. The checker is reusable for explicit exports:

```sh
python3 scripts/check_language_session_conformance.py \
  --swift PATH_TO_UNCHANGED_ESSENTIALS_RUN --rust PATH_TO_RESERVOIR_CORE \
  --swift-baseline validation/2026-10-12-fresh-0.7.0/fixture-conformance.json \
  --output NEW_RECEIPT.json RECORD.json [MORE_RECORDS.json ...]
```

## Journal save boundary

At a scheduled nonfinal boundary, `advance()` returns the observed frame and
creates a `PendingJournal`. At a nonscheduled nonfinal boundary,
`request_action()` can create one manual opportunity. The earlier D/E
`request_journal()` API remains available. There can be only one action
per step. Manual requests reserve enough of the 128-action limit for remaining
scheduled opportunities.

The pending candidate contains the immutable entry, content hash, relative path,
prompt and complete scripted JSON reply. It stays outside the portable action
history. While it exists:

- `advance()`, ordinary `stop()` and `record()` return an explanatory error.
- No journal has been claimed saved, and no candidate vector becomes eligible.
- A backend may retry the same candidate after a write/readback failure while
  preserving its separate durable attempt log.

The storage owner must atomically publish, synchronize and read the actual entry,
then call `confirm_saved(receipt, readback)`. The core requires saved status, no
failure, matching ID/hash, `right/<entry.id>.json`, and exact decoded readback.
It validates supplied evidence; it cannot authenticate a filesystem itself.
Only then does it prepare the codec/vector and append the journal and completed
action. E–H's `applicationStep` remains absent until the next frame is actually
recorded. D's remains absent permanently.

An explicit `fail_pending(reason)` records the completed response, failed storage
receipt and `journalSave` failure, without a saved journal, codec or vector. The
session becomes terminal. This historical failed outcome can never be rewritten
to success. Only a candidate that is still pending can be retried. A user-facing
“stop and retain failed save” operation must call this explicitly; exporting a
pending session may not silently omit the candidate or manufacture a failed
projection that can later resume. Explicit discard is a separate backend action.

These engines are in-memory execution objects, not a crash-resumable checkpoint
format. Durable attempt recovery and app snapshot storage belong to the backend.
Portable verification of retained save receipts still does not authenticate the
original physical save, even when the app creates its own receipts correctly.

## Memory, WAIT and fixed replay

When F–H has a latest saved journal, an action opportunity produces
`PendingMemory` rather than a reply. Its entry is the expected immutable value,
not proof of physical rereading. The backend reads the fixed owned
`right/<entry.id>.json` path and supplies the result to `confirm_memory()`.
Only an exact match permits a prompt containing that text and the subsequent
scripted/tape response. A mismatch leaves the candidate unresolved. An actual
read failure may be finalized with `fail_memory()`: terminal `memoryRead`, failed
status, expected memory ID but no exposed text, started request, response, save or
new feedback. `cancel_memory()` instead records an explicit terminal cancellation
before reading. Both preserve native distinctions. Unresolved memory also blocks
portable snapshots, further numerical steps and ordinary stop.

Scheduled independent scripted G/H selects WAIT on every third action ID; manual
opportunities always force WRITE. A WAIT still requires the F–H memory read before
its prompt, then commits a completed response without a new journal, save receipt,
codec/vector or application boundary. Previously held feedback remains in place.
The fixed script does not adapt its text to memory. Recorded exposure is not a
claim of useful memory, learned behavior or language-model benefit.

Fixed replay builds `ActionReplyTape::make()` once before execution. It contains
every nonfinal boundary, including potential manual boundaries. Its reference
field receives the configured external forcing, zero semantic input and fixed
initial retention. Response text, choice and vector are indexed by observed step,
not action ID. Manual G/H overrides a tape WAIT to WRITE while using the same
packet text/vector. F–H still rereads its actual saved journal and retains the
exact prompt, but tape receipts declare no started provider request. The saved
feedback vector comes from the precomputed reference, not the current arm's
covariance. This keeps fixed G/H inputs identical while H changes sensory
retention. A standalone session is not itself a matched-pair runner, and these
scripted mechanisms do not establish language-model benefit.

## Paired boundary and per-arm storage

`ActionComparisonSession::advance()` prepares both arms' next numerical state,
including RNG, recurrence, covariance, fill and control, before committing either
frame. Scheduled action capacity is checked before numerical preparation; manual
admission reserves capacity for the remaining schedule in both arms. The returned
`ComparisonFrame` contains both actual frames at one boundary. Current numerical
state is copied for the transaction; growing record history is not copied.

After the frame pair, opportunities run in the unchanged native order. Component
pairs attempt left then right, skipping a journal-free arm; the right D arm
therefore has request ordinal 1 when paired with C. Observation pairs alternate
left/right first on odd/even opportunity IDs. Independent scripted receipts
retain the resulting request ordinal. Tape receipts retain no started provider
request or request ordinal, and both arms reference a single tape frozen before
the session. Shared tape storage uses `Arc` internally.

`pending_memory()` and `pending_journal()` return `(Arm, &Pending...)` for only
the current opportunity. `confirm_memory(arm, entry)` and
`confirm_saved(arm, receipt, entry)` reject the wrong arm and perform the same
content checks as the standalone engine. Successful resolution starts the next
eligible arm without advancing either numerical clock. Paths are
`left/<id>.json` or `right/<id>.json`. Equal journal IDs/text on both arms do not
permit the backend to replace the required physical read of the selected arm's
owned file. A WAIT still rereads required memory, commits immediately, and lets
the coordinator continue to the next arm.

Unresolved storage blocks `advance()`, manual actions and `record()` for the whole
pair. The first arm's real saved receipt remains committed while its partner is
pending; it cannot be silently removed or projected into a fully resolved
portable record. Backend checkpoint recovery can retain partial-boundary evidence
separately, but these engines do not resume from that evidence.

`fail_pending(arm, reason)` records terminal journal-save failure, and
`fail_memory(arm, reason)` records terminal read failure before memory exposure.
For component pairs, first-arm failure creates a cancellation-before-request
receipt for the unstarted peer. For observation pairs, the peer is still attempted
after first-arm failure, including the even-ID right-first order. Thus
`is_failed()` may be true while a partner still has pending storage: callers must
resolve that boundary before exporting or treating it as finished.

Explicit `stop(reason)` is terminal. A pending prepared WRITE becomes a retained
save failure; a pending memory read becomes cancellation before exposure. Any
unstarted peer is cancelled, including in an observation pair. If the first arm
already saved, that save remains in history. A resolved between-action stop
retains a valid stopped prefix. Failed or cancelled outcomes never resume or
become successful receipts.

Borrowed `run(arm)`, `frames(arm)`, `actions(arm)`, `journals(arm)`,
`specification()` and `tape()` allow bounded backend views without snapshotting
the history. Portable `record()` clones only at explicit snapshot boundaries.
Single-arm `JournalSession::run()` and `specification()` are also borrowed.

Both observation arms remain stage D: saving text cannot alter their reservoir
or sensory inputs. Active/quiet forcing and exact coordinate exposure are
retained conditions, not evidence that a fixed scripted response benefits from
seeing coordinates. The separate `essentials-regulation-v1` field-only 600-step
controller creation workflow is deferred; its existing verifier/reader remains
available and is not represented as an A–H session.

## State ownership and tests

Stage and journal advance compute with local RNG, recurrence, sensory covariance,
fill and controller state before committing a frame. A computation error cannot
consume an unrecorded noise draw or mutate half a boundary. Stage `record()` is
borrowed; journal `frames()`, `actions()`, `journals()` and `pending_journal()` are
borrowed views. Only explicit journal `record()` snapshots clone growing history.
`pending_memory()` and `tape()` are also borrowed; `can_request_action()` reports
manual eligibility without preparing an action or cloning history.
Scheduling and synchronization are the backend's responsibility; no web timer
drives numerical steps.

`tests/session.rs` tests ten mechanisms: exact agreement with the existing stage
batch implementation, step 30→31 application, stopped prefixes, D's closed gate,
pending/incorrect save proofs, terminal failure, manual/scheduled boundaries,
reserved action capacity, unsupported inputs, and negative mutations.
`tests/session_actions.rs` adds nine tests covering all 16 A–H/mode combinations,
passive observer/output stages, actual readback protocol, memory-before-WAIT,
manual forcing and tape lookup, H's next-step controller, terminal read/cancellation
outcomes, targeted negative mutations and exact manual eligibility. These core
unit tests inject readback evidence; they do not claim physical storage tests.

`tests/session_comparisons.rs` adds eleven tests for all 14 component/mode pairs,
active and quiet observation with alternating order, two-arm save gating and
arm/path rejection, component left/right failure, observation partner attempts
after failure, memory failure/cancellation, manual tape-WAIT override, stop after
the first save, negative order/channel/path/controller mutations and reserved
manual capacity. The focused final 0.9 run passed 29 tests across all three
session test binaries; its exact command and output are retained in
`validation/2026-10-12-comparisons-0.9.0/core-focused-tests.log`. The later prompt
repair run passed 30 session tests plus the formatter oracle test, retained in
`validation/2026-10-12-comparisons-0.9.0/core-prompt-fix-focused.log`.

The first independent paired qualification exposed a quiet-input prompt mismatch:
the exact same double bits for `0.870983875` formatted as `0.87098387` with Rust's
binary precision formatting and `0.87098388` with the native locale-aware
Foundation formatter. `prompt_number.rs` now supplies shared shortest-decimal,
eight-place ties-to-even formatting for both original-stage and action prompts,
preserving signed zero. Numerical values and verification tolerances are
unchanged. `tests/fixtures/swift-prompt-fixed8-v1.json` retains 1,173 bit-exact Swift
oracle vectors and the native source identities, including decimal ties and
neighbors, signed zero, bounded random prompt values and tiny/large probes. This
qualifies the measured Foundation contract, not all locales, every double or
future Foundation releases. The failed initial corpus/receipt is preserved.

`examples/comparison_session_fixtures.rs` creates a new caller-selected directory
for independent qualification. It covers complete component pairs, stopped
prefixes, manual requests, actual per-arm file-save/read failures, explicit stop,
and active/quiet pulsed/continuous observation pairs in both request orders.
Successful save and memory confirmations follow reads of actual harness-created
files in separate arm namespaces. The manifest binds the generated portable
records. This fixture harness does not qualify application storage, UI, platform
durability or scientific usefulness. Run it with:

```sh
cargo run --locked -p reservoir-core --example comparison_session_fixtures -- NEW_OUTPUT_DIRECTORY
```

`examples/session_fixtures.rs` generates 23 original-format qualification records
in a caller-selected new directory. Successful journal fixtures use real local
no-clobber publication, file/directory sync and readback before confirmation. A
separate fixture captures a real filesystem error explicitly finalized as a
failed save. This harness qualifies core export mechanics; it is not a substitute
for the app backend's storage/lifecycle tests.

`examples/action_session_fixtures.rs` separately generates 36 A–H fixtures, with
all stage/mode combinations, stopped memory/WAIT prefixes, manual forced WRITE,
actual missing-file memory failures, explicit cancellation and actual save
failures after memory exposure. It performs real fixture-directory save/readback
and rereads before confirmation. The original 0.7 fixture harness and retained
qualification outputs remain separate.

Run from `desktop/ReservoirScope`, with the project's pinned toolchain:

```sh
cargo test --locked -p reservoir-core --test session
cargo test --locked -p reservoir-core --test session_actions
cargo clippy --locked -p reservoir-core --all-targets -- -D warnings
cargo run --locked -p reservoir-core --example session_fixtures -- NEW_OUTPUT_DIRECTORY
cargo run --locked -p reservoir-core --example action_session_fixtures -- NEW_ACTION_OUTPUT_DIRECTORY
```

On the qualified macOS development host these commands use the per-process
`DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer` and
`SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk`.
Independent unchanged Swift runner results are retained separately by the release
qualification process; creating a fixture does not itself establish Swift parity.
