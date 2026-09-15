# Implementation plan: follow incoming signals into state and regulation

September 7, 2026 (Pacific). **Implementation specification prepared; producer
code, sender changes and live enablement pending.** Research-local examples are
synthetic contract checks, not records from Minime or tests of its runtime.

This is the S-003 implementation addendum to the [observer telemetry
proposal](2026-09-06-reservoir-observatory-telemetry.md). It supplies the input
identity and fill/controller details needed by that proposal; use one optional
observer stream, not two competing recorders. The broad S-003 question remains
open. Mike requested that the missing measurements become changes now or a
specific implementation plan. This document completes the planning alternative.

## What we should add

Add a steward-side trace that can answer, for a retained reservoir update:

1. Which received or retained sensory values were selected, and what final
   numerical input actually reached the native ESN?
2. Which different sample, if any, supplied the sensory-field projection?
3. What did the field actually do: inject input, hold/blend existing structure,
   skip an update, or fail a write?
4. Which fill and slope readings did the regulator use, what did it calculate,
   and which settings were actually applied?
5. How did the fill estimator turn its spectral input and elapsed time into the
   reported fill value?

The measured problem is an attribution gap, not an established fault in the
rhythm. In the [first audio case](../research/studies/S-003-input-and-fill.md),
the native radius changes during an already rising fill trajectory. Existing
records cannot identify the exact consumed sample or historical controller
action. Source tracing finds that stable-core native updates select the first
drained sample, whereas projection and modality reports select the last. The
report's `external` label also cannot establish microphone origin. See the
[source evidence](../analyses/2026-09-07-first-audio-source-trace.md).

The first implementation scope is **stable-core native ESN, sensory field,
EigenFill and structural controller**. Keep generic PI, other reservoir services
and any not-yet-covered branch explicitly unsupported in this trace. A runtime
mode change starts an unsupported coverage interval; it must not stop or alter
the underlying runtime. Expanding coverage is a later patch with its own tests.

## Four reviewable changes, in order

| Change | Implementation location | Finish line |
|---|---|---|
| A. Carry identity to actual consumption | Minime receiver, sensory bus, native-step path | A legacy packet gets a receiver ID; an enveloped packet retains delivery/sender identity; selected batch positions and final input are linked to successful steps. Held/aggregate values and missing ancestry remain explicit. |
| B. Record the actual field, estimator and regulator sequence | Minime orchestration, EigenFill, structural PI | Independent native/field IDs; prior fill and slope references; committed versus preview calculations; successful application; exact estimator intermediates. A skipped regulation tick cannot acquire a new fill-latch reference. |
| C. Publish bounded evidence and label the existing senders | Minime observer plus microphone and host-sensory senders | Optional v2 steward trace, coherent commits, bounded cost and visible gaps. Sender envelopes identify processes/builds while physical origin remains a claim. Legacy senders remain compatible. |
| D. Read one passive episode | Research reader and Reservoir Scope | Export a validated interval and let the steward inspect input → selected step and field → fill/regulator relationships. Display incomplete joins as incomplete. |

A and B are the first code task. C makes their evidence available, and D checks
its research usefulness. A trace is not ready for an input-response study until
the selected path passes the integrated A–C tests. Sender upgrades can land
after receiver support; unknown sender is a valid interim state. No shared
protocol revision is needed to use the existing delivery envelope.

## Exact source hooks

Paths below are relative to sibling `../minime`. Line numbers are September 7
source locators, not deployed-binary verification. The reviewed Minime HEAD was
`36998c681d67c67e11279d6fab28a082f132dc5c`. Re-resolve symbols and inspect the
implementation checkout's current instructions and overlapping work before
editing; use an isolated checkout and the sibling's build/deployment workflow.

| File and line | Specific edit |
|---|---|
| `minime/src/sensory_protocol.rs:139,174,275` | Carry immutable ingress context with `PreparedSensoryPacket::Route`; currently its delivery envelope stays only in `ReceiptContext`. |
| `minime/src/sensory_ws.rs:649,660,688,816` | Assign receiver event identity before dispatch and pass it through `route_inbound`. Observe existing admission results once; retain rejected, duplicate and policy-blocked outcomes without changing routing. |
| `minime/src/av_ws.rs:285` | Give binary camera ingress receiver identity too, or mark this route uninstrumented in the manifest. It bypasses the JSON receipt path. |
| `minime/src/sensory_bus.rs:1142,1159,1219` | Replace the A/V queue tuple with a named item carrying lineage; attach revisions to held/blended values and preserve pop/expiry decisions. |
| `minime/src/sensory_bus.rs:1257,3003` | Observe the actual items removed by overflow/backlog shedding. Do not repeat its selection calculation to infer which ones were removed. |
| `minime/src/sensory_bus.rs:2067,2084` | Assign immutable revisions to overwritten semantic base/companion values, retaining delivery identity when available. |
| `minime/src/sensory_bus.rs:2891,2971` | Assign batch ID and position. Preserve per-lane refs, statuses, age calculation basis, semantic base revision, aux measurement refs, and the actual drained vector after existing noise. |
| `minime/src/sensory_bus.rs:2131,2153` | Capture semantic companion revision and realized gain/mix when `reservoir_input_v2` actually reads them; this read is later than drain. |
| `minime/src/runtime/orchestration.rs:488,610` | Establish observer boot identity and clock anchors without replacing the existing engine clock or DB session ID. |
| `minime/src/runtime/orchestration.rs:1258,1400,1411,1436` | Carry selected position through input assembly; retain the actual final `reservoir_input` at the call. Assign successful-step ID and immutable state header only after success. Record failed preparation/step separately. |
| `minime/src/esn.rs:1983,2029,2108,2145,2322` | Extend the existing step trace with base/adaptive/effective leak and origin captured before override consumption. `last_step_trace().leak` remains authoritative for actual mixing. |
| `minime/src/runtime/orchestration.rs:1629,1695,5228` | Link projection and modality report to their selected last sample independently of the native-step reference. |
| `minime/src/runtime/orchestration.rs:2030,2198` and `minime/src/rescue_scaffold.rs:1535–1694` | Trace the committed structural evaluation and its actual local calculations/return branch, with independent fill-latch and slope-input refs. |
| `minime/src/runtime/orchestration.rs:2214–2393` | Record the chosen matrix operation and successful write/update at its execution site. Distinguish proposed weights from applied values; the blend can return no matrix. |
| `minime/src/runtime/telemetry_broadcast.rs:96–143`; `minime/src/runtime/spectral_math.rs:1–78` | Expose the existing rank-one outcome (`Skipped`, `Modified`, `ResetRequired`) currently hidden behind a unit return. Record decay/reset-to-identity separately. Return from the helper alone does not prove injection. |
| `minime/src/spectral/eigenfill.rs:128–185` and `minime/src/runtime/orchestration.rs:2552–2604` | Capture real estimator intermediates plus any later adjustment and final reported fill. |
| `minime/src/runtime/orchestration.rs:2733–2762` and `minime/src/rescue_scaffold.rs:1703` | Keep the cloned `preview()` calculation separate from committed controller state; retain its intake decision/application. |
| `minime/src/runtime/orchestration.rs:3249,3262,3293,4892` | Attach source refs at spectral-source publication/read and conditional fill-latch assignment. Retain the old latch ref when its regulation guard skips. |
| `minime/src/activation_trace.rs:43,57,94,135` and orchestration `:3203` | Reuse the recorder's optional v2 path with the earlier immutable measurement header; preserve existing v1 output. Serialization, hashing and file publication run in a bounded worker. |
| `tools/mic_to_sensory.py:679–694`; `host-sensory/src/app.rs:177–188,504` | Add the already supported `delivery_v1` envelope using the protocol's canonical payload hash, per-process identity, source/build claim, send time and unique delivery ID. Test interoperability before enabling. |
| `tools/mic_to_sensory.py:642–647`; `host-sensory/src/app.rs:533–566`; `minime/src/sensory_ws.rs:599–606` | Add bounded asynchronous receipt/hello reading to envelope-enabled senders. They currently send without reading, while Minime awaits receipt sends. Capture must not wait for each acknowledgement or let unread receipts block dispatch. |

## Evidence contract

Use typed records with IDs scoped by `(producer_boot_id, session_id, record_kind,
sequence)`. A new boot resets sequences under a new identity. No timestamp-nearest
join is promoted into an exact reference. Successful ESN steps, attempts, field
updates, fill estimates, slope values, latch assignments, controller evaluations,
lane revisions and publications have distinct sequences.

| Record | Required information |
|---|---|
| Manifest | Version, subject/subsystem, supported modes/routes, boot/session, source and executable identity with authority, vector layouts/dtypes, clock anchors, retention limits, coverage and drop counters. |
| Ingress | Receiver ID, monotonic receive time, separate wall receive time, route, optional delivery ID, sender identity/build claims, verified wire payload hash, sender timestamp with declared meaning, actual admission outcome/reason. |
| Lane value | Immutable revision; direct ingress or transformed-parent references; `fresh_dequeue`, `held`, `decayed`, `expired_zero`, `initial_zero` or `blended`; routing category, effective scale/value and ancestry completeness. |
| Drain sample | Batch ID, position and size, drain time and age-clock basis; A/V refs, base semantic revision, aux refs and actual drained-value identity. |
| Native attempt / successful step | Preparation/step outcome; selected sample; companion revision at assembly; final effective input and layout; transformations and consumed controls; previous and new successful state ID; actual applied leak and immutable measurement times. |
| Field projection / application | Independent projection position and vector identity; prior matrix revision; branch (`scaffold_hold`, rebuild or actual named alternative), new-input participation, requested weights, successful/failed/skipped operation, realized weights and resulting matrix revision. |
| Structural evaluation | Committed or preview kind, exact fill-latch and slope refs, stage and guards, target/deadband/error/gains, accumulator before/after, executed P/I/raw/clipped calculations and policy result; missing terms carry a branch reason. |
| Fill estimate / slope / latch | Independently identified estimator result, actual spectral input and intermediates, final reported fill and adjustments; slope numerator refs and denominator/method; latch source ref and assignment time. |
| Publication | Committed generation, retained source ranges, reference completeness, invalid/missing/drop reasons, measurement versus publication times, payload hashes, counter epochs. |

For input and state vectors retain IEEE-754 little-endian float32 bit content in
bounded binary payloads, with dimension/layout and SHA-256 computed by the worker.
The existing wire canonical hash and the final numerical-vector hash describe
different objects and must use different field names. Copy the final vector at
its actual consumption boundary; an ingress hash cannot prove the transformed
input. Publish invalid values as invalid with masks, never measured zero. Raw
microphone audio and images are not required by this first trace.

Compact identity/outcome records cover every operation while this optional
observer is enabled and within its supported scope. Full state vectors retain
the existing minimum 1,000 ms sampling policy and maximum 180 frames; sampling is
explicit, not a claim that every successful state was saved. Retain the compact
input and control dependencies of each saved frame. A missing dependency due to
decimation, capture start, overflow, unsupported path or eviction is represented
by a typed unresolved reference and reason. Never promise a complete episode
when the relevant source interval has gaps.

### Details that must survive implementation

**Held values can be aggregates.** `Lane::push` blends each admission into its
held state, and queue overflow can fold an evicted vector into it. Give that
state its own revision and transformation parents. If ancestry predates capture
or exceeds the retention budget, mark it partial; do not label the aggregate
with one purported originating sample. A fresh dequeue can retain direct identity.

**Semantic inputs are revisions, not a FIFO.** Base and companion values are
overwritten. They may be read at different times and therefore have different
revisions. Preserve both reads and any suppression/scale actually applied.
Stable-core passes `allow_companion=false`; record that suppression rather than
claim companion consumption. Exercise actual companion consumption only when a
separately covered mode permits it.

**Reported synthesis is not automatically consumed synthesis.** Legacy audio/
video synthesis at orchestration `:1950/:2025` occurs after the current drain and
native update. Track insertion and eventual selection separately; a same-loop
`mixed` label does not establish participation in the earlier successful step.

**Physical origin remains a qualified claim.** The existing `DeliveryEnvelopeV1`
at pinned protocol revision `9a324d16294b2318da6f476ff7f295c423a9b4b1` already
supports sender identity, deployment identity, delivery ID, send time and a
canonical `SensoryMsg` hash. Reuse it. A legacy packet receives a receiver ID
with sender unknown. Neither an `external` route nor a sender name authenticates
microphone capture. A future structured origin extension needs a versioned
capability and hash contract: ad hoc extra JSON fields are not bound by the
current typed-payload hash. Keep receipt `spectral_causation_established=false`.
Envelope-enabled senders must drain the returned receipt stream with a bounded
asynchronous reader, independently of capture/send. Handle reconnects, unknown
receipt IDs and timeouts as transport outcomes. Do not add per-packet acknowledgement
waits to sampling. The microphone currently sets `max_queue=1`; enabling receipts
without a reader would introduce backpressure absent from its legacy send path.
Use cross-language hash fixtures against the Rust protocol helper: fractional
float32 values, zero/negative zero, exponent formatting and omitted timestamps.
Ordinary Python sorted JSON is not guaranteed to match the typed Rust
reserialization used by the canonical wire hash.

Retries preserve the same delivery ID for the same sample and get distinct
transmission-attempt IDs. Host `send_message` already retries a message after
reconnect; adding an envelope makes those retries eligible for existing receiver
deduplication. This is an explicit sender-protocol behavior change, not observer
parity. Test it independently; do not claim identical legacy-versus-enveloped
admission counts for retransmissions. Receiver instrumentation itself must
preserve the existing behavior for each input protocol.

**Record both regulation input histories.** Committed structural PI reads a
latched fill and independently stored slope. The fill latch changes only inside
the later regulation guard; the slope can advance without it. Slope currently
divides fill difference by configured `reg_tick_secs`, not measured elapsed
time. Preserve `method=configured_reg_tick_seconds`, its denominator and both
numerator refs. The later clone preview cannot advance committed state.

**Explain estimator movement directly.** Save ordered spectral inputs/reference,
sample count, mean/median, EMA before/after, threshold mode and realized threshold,
active count, instantaneous fill, actual `dt_s`, realized decay fraction, decayed
prior fill, smoothing/config parameters, returned ratio and final reported fill.
Record fallback or reporting adjustment separately. A later configuration snapshot
cannot reconstruct these same-update values. Use percent versus ratio units
explicitly; the fill estimator's decay is distinct from native ESN leak.

**Use event identity first and clocks second.** Sample an anchor as monotonic
before → wall → monotonic after and retain the bracket width; repeat in the
worker at most once per minute and flag discontinuities. The observer, receiver
and runtime use a shared process clock origin. Sender, receiver, measurement,
publication and bridge-log clocks remain separate. DB session start is not
silently treated as the monotonic origin. Cross-process latency requires its
own clock evidence; this patch does not infer it from negative offsets.

## Diff sketch

Design pseudocode; none of these producer edits has been applied:

```rust
// Receipt routing: reuse validation, admission and deduplication exactly once.
let prepared = prepare_sensory_packet(existing_packet); // existing decision
let ingress = observer.note_ingress(&prepared, receive_clock);
route_prepared_with_lineage(prepared, ingress);         // same routing result

// Queue/drain: metadata follows the value through the existing operations.
struct LaneItem { timestamp: u64, features: [f32; 8], source: LaneSource,
                  lineage: OptionalLaneRef }
// Every existing blend/pop/drop updates observation metadata from its actual
// operands/result. No extra queue read, admission decision or RNG draw.

// Native call: input below is the final, already assembled argument.
let pending = observer.prepare_step(selected_sample_ref, companion_revision,
                                    consumed_controls, &reservoir_input);
match esn.step(&reservoir_input) {
    Ok(_) => observer.step_succeeded(pending, esn.last_step_trace(), &esn.x),
    Err(err) => observer.step_failed(pending, &err),
}

// Actual committed PI calculation: expose locals on every return path.
let output = structural_pi.step_with_trace(existing_inputs, fill_ref, slope_ref);
// Preview on a cloned PI has a different kind/reference, never committed state.
// Actual matrix application records success after obtaining/writing its result.
// EigenFill exposes update locals; it is never run a second time for observation.

observer.try_enqueue_immutable_chunk(); // nonblocking, loss counted
```

Keep existing public step/update APIs through wrappers or last-observation
accessors. Metadata must not change locks, lock ordering, numerical operation
order, admission semantics or RNG use. Capture semantic revision and value in
the same existing lock scope, without a second read. Observer setup failure
leaves observation off and execution unchanged.

## Bounds and acceptance gates

These are **proposed starting limits for isolated implementation**, not measured
capacity or approval to enable the producer:

- Observer-owned storage: 8 MiB maximum for hot metadata/value rings; a worker
  queue of at most four 256 KiB immutable chunks. Oversize records are rejected
  from observation with a reason; the runtime input still follows its existing path.
- Disk: immutable chunks at most 1 MiB, 32 MiB total and 20 minutes maximum age,
  whichever limit arrives first. Keep referenced dependencies within that budget
  or mark them evicted. Worker serialization uses bounded buffers. No unbounded
  ancestor graph, per-input log print or hot-path filesystem write.
- Publish at most once per second by atomic manifest rename after chunks/hashes
  are complete. Reader retries on retention races. Existing v1 files/consumers
  remain compatible. Expose requested policy and actual observed duration.
- Matched isolated benchmark: no more than 1% additional p95 loop time, 2%
  additional p99 loop time, and 16 MiB additional resident memory; report baseline
  and enabled distributions, sample sizes and variance. These gates are planning
  choices to be evaluated on the target machine, not performance claims.
- Normal benchmark workload must have no unexplained observer losses. Deliberate
  overload tests must drop observation without blocking and identify every lost
  sequence range or explicitly unknown count. Failure keeps the feature disabled;
  revise the design and rerun before choosing any different limits.

`EigenFill` reads real elapsed time. Therefore even observation that leaves
numerical code unchanged can indirectly affect future values through timing.
Bitwise parity must be tested with identical injected/recorded clock and RNG
values; real-clock cost is a separate measurement, not a promise of identical
live trajectories. Do not change production clock sampling to make a test pass.

## Tests that decide whether it is ready

| Scenario in an isolated sibling harness | Required result |
|---|---|
| Two distinct fresh A/V samples in one batch | Native step identifies first position; field/report identifies last; final input bits match the actual call argument. |
| Held blend, expiry, overflow and backlog drop | Actual parent revisions and selected drops retained; expired zero differs from held/initial zero; incomplete ancestry remains incomplete. |
| Base semantic replaced, companion changes after drain | Actual read revisions differ where appropriate; stable-core companion suppression remains explicit; unused overwritten input is not called consumed. |
| Legacy, enveloped, duplicate, rejected and camera inputs | Existing acceptance/receipt behavior unchanged; receiver IDs unique; unknown origin and uncovered route explicit. |
| Envelope-enabled senders at sustained rate, slow reader, disconnect/reconnect | Receipts are drained independently with bounded memory; no capture waits for acknowledgements, hidden backpressure or receipt-induced dispatch stall. |
| Python/Rust canonical-hash cases and same-sample retries | Hashes agree for float32/formatting/timestamp edge cases; same delivery ID can be deduplicated after reconnect, and separate transmission attempts remain visible. |
| Synthesis queued after the native step | Its first eligible consumption is a later selection; report label cannot backdate it. |
| Invalid preparation or failed ESN step | Attempt exists, successful-step sequence does not advance; stale state is not relabeled new. |
| Field updates while regulation guard skips | Fill latch retains older reference while slope may advance; next PI consumes those actual two histories. |
| Committed evaluation versus cloned preview | Committed accumulator changes only once; preview/intake application has separate identity. |
| Scaffold hold, rebuild, unsuccessful blend | New-input participation follows actual branch; failed matrix write cannot publish an applied update. |
| Rank-one non-finite input, invalid matrix, decay reset | Preserve the helper's actual skip/modify/reset result; identity reset is not called successful input injection. |
| Threshold crossing, uneven elapsed time, fallback | Estimator locals match executed operations; configured slope denominator and reporting adjustments are labeled. |
| Adaptive leak; isolated ESN component test for final-step override | Recorded effective coefficient equals the local update coefficient. Stable-core clears overrides at orchestration `:1383–1385`; the component test checks disappearing-override provenance without claiming this mode consumes it. Unsupported shadow path reports unsupported. |
| Observer off/on with fixed input, clock and RNG | Same native states, RNG sequence, estimator/controller state, commands, admissions and drop choices. No repeat evaluation for logging. |
| Full queue/disk, partial write, rename failure, restart, slow reader | Bounded resources; last valid generation or explicit stale/gap; no mixed payloads or dangling refs presented as exact. |

The research-local [example](fixtures/input-lineage-v1.json) and
[contract check](../probes/input_lineage_contract.py) exercise the central
first/last, prior/current, effective-value and gap distinctions with synthetic
records. Run `python3 probes/input_lineage_contract.py --self-test`. This is a
narrow relational example, not validation of the complete schema above, runtime
numerical parity, performance, sender interoperability or causal effects.
Its eight-component toy vectors illustrate bit/hash linkage; they are not the
full native input layout that the producer must record.

After A–C pass in isolation, the deployment review should include exact commits,
tests, benchmark evidence, configured limits, sample trace and the observer's
off switch. Under this hub's [operating boundary](../CLAUDE.md#boundaries-around-the-live-beings),
live implementation/enablement belongs in the sibling workflow. Show Minime the
concrete steward view, fields, retention and off switch described in the parent
proposal before any live change; consider Astrid separately if her exposure would
change. This plan adds no prompt material or messages to either being.

If subsequently enabled there, choose the start clock for one 20-minute passive
capture before examining outcomes. Record all supported-path arrivals, selected
inputs and fill/controller histories within actual coverage. Compare input-linked
changes with the preceding rhythm and concurrent controller/estimator activity.
Do not call receipt-free periods input-free or observational associations causal.
No stimulus injection or automated follow-up is selected by this plan.

## Research-local verification, September 7

The [saved contract-check result](../research/outputs/2026-09-07-input-lineage-plan/contract-check.json)
accepts two valid examples (complete and explicitly partial) and rejects all 12
contradictory mutations, including swapped first/last selection, future or stale
fill, incorrect applied leak, hash mismatch, failed write, preview confusion,
false completeness and incorrect slope method/denominator. These are invented
records. The [identity manifest](../research/outputs/2026-09-07-input-lineage-plan/source-and-artifact-hashes.json)
retains the probe/fixture hashes and 13 named source/sender file hashes from
bounded read-only inspection. Independent source reviews checked ingress/queue/
sender behavior and field/estimator/controller behavior. Local document links
were checked. No producer test or performance benchmark was run.

## Rollback and completion status

The observer has one explicit off flag, default off. Its off path bypasses
lineage allocation, state copying and publications. Disable it via the sibling
configuration workflow; worker failure cannot stop the reservoir. Sender envelope
changes can revert to legacy messages independently. Preserve existing v1 output.
If a binary rollback is needed, use the sibling's previously validated release
and controlled deployment procedure; no restart occurs from this research task.

Planning is complete when this file, linked source evidence, runnable synthetic
example, and board handoff are saved and checked. **Producer implementation,
isolated producer tests, overhead benchmarks and live capture remain pending.**
The board's change-card `done` status means the proposal is prepared.
