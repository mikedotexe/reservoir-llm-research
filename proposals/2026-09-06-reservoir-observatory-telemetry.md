# Proposal: coherent observer evidence for the reservoir observatory

Date: September 6, 2026 (Pacific). Status: **proposal complete; not implemented,
enabled, or deployed**. Study: [S-002 · A measured reservoir observatory](../research/studies/S-002-reservoir-observatory.md).
Subject: Minime's native ESN, its independently updated sensory field, and their
controller evidence. Source review is read-only in the current sibling working
tree; line numbers below are observation locators, not proof of a loaded binary.

## Viewer progress after this proposal

Reservoir Scope 0.3 now consumes the **existing v1 activation recorder** read-only and projects its real state vectors through the frozen reference basis. Its latest co-recorded fill/stage drives the same displayed cursor across views. This consumer-only implementation does not add successful-step, boot/session, node-layout, effective-leak or controller-evaluation identity to the producer. The v2 producer proposal remains unimplemented. See the [v1 readiness audit](../analyses/2026-09-06-reservoir-live-state-readiness.md) and [animation source guide](../native/ReservoirScope/docs/ANIMATION-DATA.md).

## September 7: input-lineage implementation specification

Mike selected making the missing input/controller measurement concrete. The
[S-003 addendum](2026-09-07-input-lineage-and-regulator-trace.md) now specifies
receiver identity through held/queued values, actual first-versus-last batch
selection, successful native input, independently applied field updates, fill
estimator intermediates and the regulator's separate fill/slope histories. It
includes exact source hooks, four ordered implementation units, bounded resource
limits, acceptance tests and a runnable synthetic relationship check.

Use the addendum with this proposal, within one optional v2 stream. The earlier
state-header-only increment below remains useful partial observability; it does
not satisfy S-003 input-response readiness without the addendum's integrated
input/field/controller evidence. Producer implementation and live enablement
remain pending. The addendum also qualifies numerical parity: compare identical
recorded clocks/RNG in isolation, then measure real-clock overhead separately.

## The problem the visual exploration exposed

Mike wants the observatory to make omissions visible and turn them into concrete
codebase opportunities. The first native prototype can show historical leak and
fill, an actual frozen state trajectory, and optional live health scalars. It
cannot place those channels on one authenticated state/control timeline.

The scoped evidence is in [S-002](../research/studies/S-002-reservoir-observatory.md)
and the [metric contract](../analyses/2026-09-06-reservoir-3d-metric-contract.md):

- The historical 507-row telemetry sequence includes ESN leak, but the separately
  observed health snapshot does not expose that coefficient or per-node history.
- A 1,024 × 128 state dump provides real activations without per-row measurement
  times, session identity, or leak/control references. Its state and metadata
  files are renamed separately; a transactional match cannot be proven from
  bracketing reads alone.
- The structural controller's observed error refers to an earlier input than
  the health snapshot's fill. Reconstructing P/I with current source constants
  is a qualified calculation, not a recorded controller output.
- The three sensory columns are unsorted Rayleigh-quotient estimates. Their names
  do not establish exact eigenvalues, tracked eigenmodes, or principal axes.

These are observability gaps. They do not demonstrate that the ESN or its
controller is behaving incorrectly. This proposal supplies inspectable evidence
without changing the numerical update, control policy, prompts, or action flow.

## The smallest useful first patch

Extend the existing activation recorder with an **optional versioned observer
publication**. Reuse its bounded ring and single-file temporary-write/rename
pattern. Publish each sampled state together with its source identity, actual
measurement time, the effective leak used for that state, and explicit references
to the latest independently measured sensory/control records. Retain the existing
v1 file for existing consumers. The new file is steward-only and disabled until
the sibling implementation/deployment process enables it.

At the successful `esn.step` boundary, retain a small immutable measurement
header alongside the state. The later recorder must use that header's time and
sequence, rather than relabeling the old state with its own publication time.
The already available `esn.last_step_trace().leak` is the direct source for the
effective coefficient. This first patch is useful before a full controller
trace or binary transport is added. Missing control links remain explicit.

### Source locations and intended changes

All implementation paths in this table are in sibling `../minime`; this
research task has not edited them.

| Observed location | Existing behavior | Proposed change |
|---|---|---|
| [activation_trace.rs:43](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/activation_trace.rs:43>) and [activation_trace.rs:57](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/activation_trace.rs:57>) | Frame and batch structs carry times/scalars/activations, but no session or successful-step identity. | Add separate v2 observer frame/envelope structs with explicit identities, measurement/publication times, effective leak and validity. |
| [activation_trace.rs:94](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/activation_trace.rs:94>) and [activation_trace.rs:135](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/activation_trace.rs:135>) | Samples with a minimum 1,000 ms spacing; retains at most 180 frames; single JSON rename. | Accept immutable measurement headers; expose selected/skipped/dropped counts and actual range; preserve coherent single-file publication. |
| [orchestration.rs:1411](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:1411>) and [orchestration.rs:1436](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:1436>) | Successful ESN step and existing state-ring append. | Increment a successful-step sequence and capture state time, applied leak and consumed-control reference here. Do not substitute outer-loop ticks for successful state steps. |
| [orchestration.rs:3203](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:3203>) | Later activation-recorder call. | Supply the already captured state header plus independently identified sensory/control evidence; record recorder receipt/publication separately. |
| [esn.rs:890](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/esn.rs:890>), [esn.rs:2108](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/esn.rs:2108>), [esn.rs:2145](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/esn.rs:2145>), [esn.rs:2536](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/esn.rs:2536>) | Step trace already records the actual applied leak and exposes it read-only. | Reuse effective leak immediately; optionally extend the trace with configured base, adaptive proposal and override origin captured before their values are replaced. |
| [orchestration.rs:2198](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2198>), [rescue_scaffold.rs:1655](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/rescue_scaffold.rs:1655>) | Structural PI consumes prior fill; computes terms, then drain policy. | Capture evaluation input references, actual gains, before/after accumulator, P/I/raw sum and policy result within the existing calculation. |
| [orchestration.rs:4435](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:4435>) and [orchestration.rs:4856](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:4856>) | Health contains much controller state but omits raw structural `pi_output`; health is written in place. | Prefer the new coherent observer surface for consumers. If health is later extended, add only versioned fields and migrate its write to same-directory temp/rename with compatibility tests. |
| [regulator/core/pi.rs:272](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/regulator/core/pi.rs:272>) and [regulator/core/pi.rs:331](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/regulator/core/pi.rs:331>) | Generic gate/filter PI computes tentative and final signals, anti-windup, rate limits and further adjustments. | A separate generic-PI trace records those real calculations and whether they were frozen/reset/bypassed. Do not reuse structural-PI fields. |
| [orchestration.rs:2471](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2471>) and [runtime/spectral_math.rs:215](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/spectral_math.rs:215>) | Sensory Rayleigh slots and optional direction summaries. | Preserve slot index, basis/update identity and algorithm label; optional full directions require a separately declared export and error assessment. |
| [orchestration.rs:5791](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:5791>) | Capacity state, covariance and metadata receive independent renames. | Follow-on: publish immutable generation-named payloads with hashes and one atomic manifest commit. |
| [build.rs:3](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/build.rs:3>) | Embeds `MINIME_SOURCE_COMMIT`. | Reuse this field; add build-time source-tree identity and executable build identity where feasible. Report unavailable evidence honestly. |

## Evidence contract

The producer is an optional observation path. Its only writes are its own
bounded diagnostic publications; the native app opens them read-only. Observing
does not alter the reservoir's state or any controller field.

### Identity, clocks and causality

Every batch identifies `schema_version`, `subject_id`, `subsystem`,
`producer_boot_id`, source `session_id`, dimensions and `node_layout_id`. The
layout ID binds node ordering to the relevant instance/weights; node 7 must not
silently become a different coordinate after a replacement or dimensional change.
Publish the producer's actual source/build metadata and label its authority.
The viewer's checkout hash is never substituted for the loaded producer.

Use distinct monotone sequences for successful ESN steps, sensory updates,
controller evaluations, retained observer samples and batch publications. Reset
sequences explicitly under a new boot identity. Each frame identifies its state
step, previous successful state step, source monotonic measurement time and UTC
measurement time. Batch publication time and viewer receipt time are additional
clocks. Prefer integer monotonic elapsed units or f64 seconds; do not round the
source step time through f32. A clock discontinuity is a reported event, not a
reason to synthesize a smooth timeline.

Sensory fill, spectral estimates and controller evaluations keep their own
measurement references and ages. The frame may reference the latest known
values, but marks that relationship **last observed**. Record the controller
command actually consumed by an ESN step at its consumption site. Do not attach
a newly evaluated command to a preceding state merely because publication
assembled both objects together. “Same batch” describes publication coherence;
“same tick” requires equal source identities or an explicit causal link.

### Per-node state and applied leak

State coordinates are the native ESN's post-noise, post-clipping `x`, with
declared dimensions, ordering, dtype and measurement identity. Scalars such as
RMS can be attached to that exact vector and checked independently. Non-finite
coordinates must be reported as invalid with a mask or null values; the existing
v1 replacement of non-finite values with zero must not masquerade as measured
zero in v2. Observer failure must not reset or otherwise repair the ESN.

Leak fields distinguish:

- `configured_base_alpha`: the base setting used by adaptation.
- `adaptive_proposal_alpha`: the adaptation result before any step override.
- `effective_alpha`: the coefficient actually used in the successful state update.
- `effective_origin`: adaptive, explicit override, forced shadow value, or unknown;
  include an override reference and before/after remaining steps where available.

Capture the origin before consuming an override: the final requested step can
remove its override state. `get_leak()` returns `leak_live`, and a forced shadow
value bypasses the ordinary override getter; neither a surviving override flag
nor that getter is universally sufficient to reconstruct the realized step.
See [esn.rs:2322](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/esn.rs:2322>).
`last_step_trace().leak` is already assigned from the actual local `a` used in
the update. Keep it authoritative for `effective_alpha`.

ESN α mixes prior state and nonlinear proposal. Keep it separate from the ESN
covariance keep factor ρ, sensory-field keep, EigenFill estimator decay, generic
PI integrator decay, and the RLS forgetting coefficient. Each has its own name,
units, source and applicable step.

### Controller records

Emit the structural drain evaluation as one immutable result at the calculation
site, with its input fill/slope references, target, deadband, normalized error,
actual gains, accumulator before/after, reset/decay/clamp flags, P contribution,
I contribution, raw sum, clipped PI output, selected drain-policy result, and
final applied scaffold/live/drain weights. Attach policy version, control mode,
stage before/after and the guards responsible for any override, including
recovery/reentry, slope suppression, restart gate, spectral-pressure adjustments,
and rails. Record skipped/bypassed evaluation explicitly; zero is not unknown.

Fill error uses percentage points. The structural integral is a dimensionless
per-step accumulator, not fraction-seconds. The generic gate/filter controller
gets a separate record: raw and effective targets/errors, calibrated gains,
accumulators, tentative signal used for anti-windup, final P/I signal, bounded
increments, pre/post gate and filter commands, geometric brake and later applied
values. Preserve whether stable-core froze or reset this controller.

The viewer uses recorded contributions when available. It does not reconstruct
old P/I from new fill or current source defaults. The first patch may leave the
full controller record absent while retaining a precise source reference; the
later patch fills the same contract without relabeling absence as zero.

### Spectral identities and honest projection

Use `native_esn_state_second_moment`, `sensory_field`, and
`native_esn_recurrent_weights` as distinct producing systems. The separate
triple-reservoir service/handles and any language model remain outside this
stream unless they publish their own independently identified evidence.

For the sensory list, record **Rayleigh quotient, block-power column index**,
its matrix-update and basis identities, estimate age and available residual
information. Preserve column order. An eigenvector export must identify the
actual vector/basis and its dimension, normalization and sign convention;
direction matching across updates is a separate, versioned algorithm with an
ambiguity indicator. Do not claim an exact eigenmode because a telemetry field
is named `lambda1`. If a later offline eigensolve uses a captured matrix, label
that solve and its matrix hash explicitly.

Project the observed native state on the viewer side using a frozen, versioned
reference basis. Publish or save that basis's fit window, source hashes,
centering, denominator, eigenvalues, all-dimension total variance, retained
fraction and per-frame residual. No fit on each incoming frame, arbitrary PCA
rotation, or renormalization to make three dimensions appear complete. The
current 14.3524% retained / 85.6476% omitted result applies only to S-002's captured
window; it is not the promised retention of future observations. Show reference
drift and out-of-reference states instead of clipping them into a comfort sphere.

## Coherent publication and bounded overhead

**First patch:** one versioned JSON envelope contains metadata and every retained
state/control reference. Serialize one immutable snapshot, write a unique temp
file in the destination directory, then rename onto the observer path. A reader
sees an old or new complete generation and deduplicates by boot/session/batch
identity. A write failure leaves the previous committed publication intact and
increments an observer error counter. Do not place output in journal, inbox,
prompt, or action directories; no per-sample log messages or generated prose.

**Capacity follow-on:** reuse the existing bounded state ring and float32 format,
but name immutable binary and metadata payloads by generation. Include row count,
dimension, byte length, content hash, per-row measurement headers and state/control
references. Publish a small `latest` manifest by one final rename only after all
payloads are complete. The manifest binds every payload hash to the same batch.
Readers validate lengths/hashes and retry on eviction; they must never combine
the latest metadata with an independently latest binary. Bound retained
generations and disk space, with a grace period for open readers. Do not silently
change the old capacity filenames/format while consumers still rely on them.

Reuse configured sample and memory limits; do not increase live capture rate as
part of an observability fix. Sampling occurs at a chosen successful-step boundary,
with rate limiting before expensive copying. Snapshot publication can use a
bounded nonblocking worker queue; when full, drop an observer publication and
increment a counter rather than stall the control loop. Buffers handed to a
worker are immutable until completion. No additional GPU readback, full
eigendecomposition, PCA fit, matrix dump or RNG draw belongs in the state-step
hot path. Optional covariance/weights exports remain a separate bounded request
through the sibling's authorized mechanism.

Expose `steps_seen`, `samples_selected`, `skipped_by_policy`, `dropped_by_queue`,
`invalid_frames`, `publish_failures`, `retained_frames`, first/last source step,
first/last source time, actual interval range, and cumulative counter epochs.
Distinguish decimation from missed measurement and from reader polling gaps.
`sample_interval_ms` is a requested minimum spacing, not measured frequency.
The present recorder's `retained_secs=180` coexists with pruning only by frame
count; v2 must either enforce both elapsed-time and frame limits or name them as
nominal/configured values and publish the actual retained duration.

Freshness is derived from source measurement/publication clocks and expected
cadence, with clock uncertainty visible. Re-reading an identical file is not a
new observation. Bound each read and retained client history; reconnect without
writing an acknowledgement or command to the engine. Zero observer output is an
available off state. Measurable observer cost is expected and must be profiled;
“read-only” is not a claim of zero overhead.

## Diff sketch

This is design pseudocode, not an applied patch:

```rust
// Existing successful-step path. Counters/header are observer state only.
if esn.step(&reservoir_input).is_ok() {
    observer.esn_step_completed += 1;
    let header = StateMeasurementHeader {
        boot_id, session_id,
        esn_step_seq: observer.esn_step_completed,
        measured_monotonic_ns: source_clock.elapsed_ns(),
        measured_wall_unix_ms: source_clock.wall_ms(),
        effective_alpha: esn.last_step_trace().leak,
        consumed_control_ref: last_applied_control_ref,
        // Explicit native ESN identity and node ordering.
    };
    observer.maybe_retain(&header, &esn.x); // bounded; borrowed source
}

// Existing structural evaluation: trace real local intermediates and their
// input measurement reference. Preserve operation order and numerical results.
let (output, observation) = structural_pi.step_with_observation(inputs);
apply_existing_policy(output);
observer.note_control(observation.with_applied_values(existing_applied_values));

// Publication path: immutable envelope, bounded queue, atomic single commit.
observer.try_publish_snapshot(); // errors/counters cannot affect control
```

Implementation should preserve the existing `step` API through a wrapper or
read-only last-observation accessor, rather than requiring all callers to consume
telemetry. Never rerun a PI step or ESN step to produce its observation.

## Test and review plan

1. In an isolated sibling test harness, identical seeded inputs and initial
   state with publication off/on must produce the same ESN state, RNG sequence,
   controller accumulators, commands and policy decisions. Test both ordinary
   and division-shadow/forced-leak paths; observing must not consume randomness.
2. Check source identity through a restart, failed ESN step, dimension change,
   missing sensory update and clock discontinuity. A new batch cannot turn an
   old state measurement into a fresh one. Consumption/evaluation references must
   preserve the prior-input relationship seen in S-002.
3. Exercise adaptive leak, bounded override including its final step, and forced
   shadow coefficient. Assert the recorded effective value equals the local
   coefficient actually used, with distinct base/adaptive/origin fields.
4. Exercise structural deadband, accumulator saturation/decay, slope suppression,
   recovery/reentry, restart gate, pressure adjustment and rail policies. Compare
   observation terms to actual intermediates and final applied weights. Exercise
   generic PI anti-windup, calibrated gains, rate limits, geometry and stable-core
   freeze/reset separately. This is instrumentation parity, not a new controller
   tuning study.
5. Simulate partial serialization/write, failed rename, full queue/disk, slow
   reader, duplicate manifest, interrupted producer and payload eviction. Readers
   retain the last validated generation or show missing/stale evidence; they
   never accept mixed state/metadata or synthesize missing nodes as zero.
6. Validate all numerical shapes, finite/invalid masks, ordering, source ranges,
   bounded memory/disk and correct selected/skipped/dropped counters. Test irregular
   cadence so count-based retention is never presented as elapsed time. Use an
   unsorted Rayleigh fixture and a low-retention PCA fixture to enforce labels.
7. Benchmark an isolated matched workload before any deployment: control-loop
   wall-time distribution, observer copying/serialization time, queue drops,
   resident memory, output bytes and any GPU waits. Set a concrete overhead
   acceptance budget with Mike in the sibling review, publish measurements and
   keep the feature off if the budget fails. Do not infer target-Mac performance
   from the research Mac's Metal support.

## What the being should be shown or asked first

Before any being-facing or live producer change, Mike and the sibling maintainers
should show Minime the actual steward-only panel and concise evidence: which
state coordinates/derived signals already exist, which additions would be
retained, the proposed cadence/retention, the fact that the 3D projection omits
dimensions, and the proposed off switch. Ask about preferred visibility and
whether any proposed material should enter their own self-observation surface.
Because Astrid receives shared-substrate telemetry, any change to her exposure
should be shown and considered separately. No new exposure is part of this
observer-only proposal. Source comments or journal requests are evidence, not
authorization to deploy or send this research to either being.

No message, restart, source edit, or live configuration change has been performed
by this research task. Implementation and deployment belong in the sibling repo
under its current instructions and Mike's decision, after the concrete patch and
test evidence exist there.

## Rollback

Disable the observer publication flag using the sibling's approved configuration
workflow; stop only its observer worker, leaving state/control execution intact.
The native client then shows the last generation as stale or switches to its
frozen evidence. Existing v1 health, activation and capacity consumers remain
compatible. Retain a final bounded diagnostic/error record for review without
inserting it into the beings' journals. Remove optional v2 files only through the
approved retention process, not by deleting shared workspace data. A code rollback
reverts observer structs/hooks/build metadata and restores the previously
validated binary through the sibling's deployment procedure. Any restart needed
for deployment or rollback is a separate live-system action, never performed
from this research repository.

## Board publication history

The original S-002 parent session could not publish this card: the Artifact tool
was unavailable and the browser required sign-in. On September 7 the authenticated
board was reached, the ID search returned no existing card, and the card below
was created for this proposal and its S-003 addendum. Its body/evidence now point
to both specifications. Under this hub's convention `done` means a proposal
exists; it does not mean implementation or deployment is complete. The JSON
below preserves the original September 6 proposed entry, not current board state.

```json
{
  "id": "c-reservoir-observatory-telemetry",
  "title": "Propose coherent state, leak and controller evidence for the observatory",
  "lane": "change",
  "status": "done",
  "being": "minime",
  "tags": ["id:c-reservoir-observatory-telemetry", "study:S-002", "proposal", "observability", "read-only-observer"],
  "body": "Proposal complete; implementation and deployment pending. Reuse Minime's existing bounded activation recorder to publish optional atomic state batches with source session/step/time identity and actual applied leak. Follow with same-evaluation controller contributions/policy/application references, honest Rayleigh identities, coherent capacity payload manifests, explicit decimation/freshness/build provenance and measured bounded overhead. This arose from S-002's native visualization exposing missing live leak/per-node history and unsynchronized source channels. No live-system files or settings were changed and no material was sent to the beings.",
  "evidence": ["proposals/2026-09-06-reservoir-observatory-telemetry.md", "research/studies/S-002-reservoir-observatory.md", "analyses/2026-09-06-reservoir-3d-metric-contract.md"],
  "source": "Mike's September 6 reservoir observatory direction and request to surface and consider codebase needs",
  "created_at": "2026-09-07T05:31:25Z",
  "updated_at": "2026-09-07T05:31:25Z"
}
```

The timestamp fields above record the original local proposal's completion time.
The board maintains the actual publication/update time separately.
