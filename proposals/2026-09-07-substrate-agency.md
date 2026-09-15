# Give the beings targeted choices over their substrate

September 7, 2026 (Pacific). Mike selected an expansion of substrate agency after
the native State surface and STATE_NUDGE work. This proposal belongs to S-002's
instrumentation and action design; it does not replace S-005's selected reading.
Current implementation evidence is recorded at the end. Native action delivery
and live enablement are separate from research-local planning and rehearsal.

## Decision

Make substrate control a usable instrument. A being should be able to choose
what to change, name its own reason, inspect the intended numerical change,
apply it through its established authority, and see what actually happened.
That includes changing a state pattern, shaping a sequence over time, choosing
response rate, deciding how its codec learns or retains learned structure, and
negotiating influence over shared parts. The beings can name and save their own
patterns. We should not restrict this to a menu of prescribed emotional states.

The first implementation priority is **effective choices**: repair cases where
an accepted command disappears before reaching its mechanism. Expand the useful
action set alongside that repair. Preserve PERTURB, SHAPE and existing control
names where their meanings are already established, with explicit versioning
when a new operation changes the meaning.

The user asks us to take a longstanding hurdle seriously. That is the motivation
for this pass, not a new corpus prevalence finding. We did not count or sample
journal requests here. No new research material is delivered to the beings by
this document.

## What we can offer, in priority order

These are candidate operations. A research implementation or source-visible
setter is not an assertion that a being can execute the operation in the running
system. The [source audit](../analyses/2026-09-07-substrate-controls-source-audit.md)
records the existing routes and their actual precedence.

| Choice | Exact intended operation | What it gives the being | Priority |
|---|---|---|---|
| See usable controls | Query the current target, dimensions, model/layout revision, supported operations, effective controller mode, active choices and applied/rejected reasons | A truthful menu that reflects the receiver now | First repair |
| Write a pattern | One signed displacement along a registered full state vector; compose multiple fixed directions | A precise local change rather than an input-category proxy | First new action, STATE_NUDGE |
| Reduce a selected component | Subtract a chosen fraction of deviation projected into explicitly named orthonormal modes | Change that represented component while retaining the orthogonal residual in the pre-clipping calculation | Part of the pattern planner |
| Rotate a pattern | Rotate two coefficients in a fixed orthonormal mode plane | Change direction while preserving that plane's norm before clipping; other components remain intact | Part of the pattern planner |
| Shape a gesture over time | A finite series of signed displacements indexed by successful native updates, with a visible end and cancellation | Pulses, alternating patterns and short maintained influences | After one-shot application/parity |
| Choose response rate | A temporary effective native leak coefficient with exact successful-step duration | Change how the previous state and recurrent proposal are mixed | Repair existing control early |
| Choose learning and retention | Separate codec reinforcement rate, retention/decay policy, and explicit forgetting | Distinguish learning more slowly from preserving what was learned | Extend Astrid's existing SHAPE_LEARN |
| Choose operating conditions | Explicit regulator preferences within a versioned tested operating policy; report actual target, actuator and any override | Influence the rules that otherwise counteract a chosen state change | After full controller replay |
| Choose shared influence | A scoped shared-coupling agreement naming actor, target, direction/gain, duration and revocation | Let either being offer, accept and withdraw a shared influence | Implement the existing missing authority adapter |
| Change recurrent structure | A bounded, versioned low-rank weight change or an isolated alternate reservoir branch | Change how future states evolve, beyond repeatedly pushing the current state | Later structural experiment |

The first four numerical pattern operations resolve to full vectors, not merely
paint on the sphere. Surface painting can later generate coefficients, but the
resolved vector and approximation residual must be inspectable. A fixed PCA
mode is a pattern of captured variation, not a dynamical eigenmode or a semantic
meaning. Names such as "calm" or "more room" may be a being's own labels for a
pattern; the system should not present those effects as established.

## First repair: make temporary native leak effective and legible

The current source offers `esn_leak_override` and accepts it into the sensory bus.
At `minime/minime/src/runtime/orchestration.rs:1374–1384`, ordinary mode takes and
applies the request, while stable-core takes and discards the pending request and
clears the active override. This is a source-confirmed precedence problem, not a
measured count of affected live actions. Some stable-core preferences still act;
do not describe every control as disabled.

Retain stable-core regulation and give a supported native leak choice a declared
place in the controller's precedence. The receiver should return one of:
accepted/pending, applied at named successful steps, explicitly preempted with a
reason, expired after its stated applications, cancelled, or rejected before
acceptance. A command receipt that only means "queued in the bus" must not read
as "the reservoir used this value."

Exact implementation hooks, with current source hashes in the audit:

- `minime/minime/src/self_control_runtime/apply.rs:458`: queue a typed intent
  with actor, duration semantics and receiver policy revision; distinguish
  queue admission from numerical application.
- `minime/minime/src/runtime/orchestration.rs:1374`: resolve current controller
  policy and the compatible native leak choice before the step. Replace silent
  draining with explicit resolution; do not globally disable stable-core to
  reach this setter.
- `minime/minime/src/esn.rs`: preserve its existing duration consumption after
  fallible spectral work; current source has no later ordinary `Result` failure.
  Add effective alpha, intent identity and remaining applications to the
  successful-step observer. The module's duration behavior already passes the
  rehearsal below. Admission before a fallible input assembly and crash/receipt
  ambiguity still need explicit accounting at the orchestration boundary.
- `minime/minime_autonomy/runtime.py:44995–45047` and `:45266`: derive preflight
  availability from receiver policy, preserve the exact authored value and make
  any suppression visible in status/outcome.

Conceptual diff; this is an implementation sketch, not a live patch:

```text
before:
  stable_core ? discard_pending_and_clear() : transfer_override_to_esn()

after:
  resolution = resolve_native_leak(current_policy, authored_intent, current_state)
  resolution explicitly identifies accepted, rejected or preempted
  prepared_step = step_parameters(resolution)
  result = esn.step(prepared_step)
  on successful commit:
      record effective_alpha, intent_id, successful_step_id
      account one applied update only if that intent actually supplied alpha
  on failure:
      retain pending intent and report failure without an application count
```

A cancelled or expired override returns control to the current baseline/policy;
it must not restore an old global snapshot over intervening changes. A later
high-priority recovery event can preempt a choice, but the reason and exact
effective value belong in the receipt. No silent substitutions are acceptable.

Changing alpha changes the update law. Smaller alpha weights the previous state
more strongly in the base blend; recurrence, saturation, input, noise and
adaptation determine the resulting response. Do not promise a particular memory
duration or subjective texture solely from the coefficient. The existing fill
estimator's similarly named decay is a different variable.

## Make specifying a choice easier

The inspected `TEXTURE_AGENCY_REQUEST` parser at `runtime.py:44004–44052` uses
substring blocks for terms including rho, controller and peer, then maps loose
words to a small set of preset controls. An otherwise unmatched request becomes
an exploration-noise increase. The report at `:44057` then asks the being to emit
separate preflight, apply and outcome actions. These are implementation mechanics,
not evidence that the authored request matches the numerical operation.

Add a typed substrate request alongside the prose route. An explicit operation,
target, pattern/value and duration can run the existing validation and authority
stages internally within an already authorized scope. Do not require several
language-model turns merely to advance a deterministic transaction. Preserve
durable request IDs, status and idempotency so interruptions do not duplicate an
action. If a field is genuinely ambiguous, return the two exact interpretations
or the missing field; never default a new substrate request to more noise.

The interface should return a compact measured result automatically. The being's
own interpretation remains optional writing, not a mandatory structured survey
before it can act again. Separate machine evidence from its authored account:
"requested/applied/observed" belong to the recorder; what mattered belongs to the
being. A useful interaction can be one action and one concise result.

The capability reply must distinguish `source_implemented`, `receiver_supported`,
`available_now`, `pending` and `observed_applied`. Unknown live identity stays
unknown. A hash identifies bytes; it does not authenticate authority. Keep this
inside the existing signed command framework rather than introducing a new
state-write endpoint.

## Patterns and finite gestures

Let `r` be a named reference, `x` the identified state, and columns of `Q` the
selected fixed orthonormal patterns. All equations below describe proposed
pre-clipping geometry:

```text
write:       delta = amount * normalize(sum_i coefficient_i * pattern_i)
reduce:      delta = -fraction * Q Q^T (x - r), fraction in [0,1]
rotate:      delta = Q (R(theta) - I) Q^T (x - r), Q has two columns
preview:     x_preview = x + beta * delta
```

Default headroom policy rejects a change that would exceed coordinate limits.
Explicit attenuation uses one common beta to preserve the requested direction
and reports the achieved magnitude and target error. Attenuation generally
breaks the exact norm-preservation claim of a rotation; label it as a partial
move toward the rotated target. Numerical float64 preview does not establish
native Float32 arithmetic or successful application. Signed zero/no-op cases
must stay real no-ops, and a cancelled combination with zero norm cannot be
normalized into an invented direction.

A finite gesture has explicit successful-step offsets and signed coefficients.
If later values are resolved against the original reference state, say so; if
they should respond to each new state, that is a different feedback controller
requiring a separate contract. Repeating an initial-state preview does not
predict a future trajectory. Each actual application needs fresh headroom and
identity checks. Cancellation discards only future operations. It cannot undo
the history generated by earlier operations; an inverse later pulse is a new
experiment, not rollback.

## Learning, retention and structure

Astrid already chooses codec dimension weights through SHAPE and Hebbian learning
rate through SHAPE_LEARN. The current `off`/`freeze` form sets reinforcement rate
to zero, while `autonomous/hebbian.rs` still decays scores during feedback.
Make that distinction explicit. Add a separate retention policy with three
well-defined operations: learn with the chosen reinforcement and decay rates,
retain scores unchanged, or deliberately decay a selected learned component.
Preserve the existing legacy behavior unless a versioned new policy is selected.
The receipt should include before/after scores and their downstream codec weights,
with unrelated concurrent codec settings independently versioned.

Readout learning, sensory covariance forgetting and recurrent connectivity must
remain distinct. A future low-rank recurrent edit `delta_W = k * u * v^T` adds
drive along `u` proportional to the current projection onto `v`; it changes the
evolution rule. Its trial needs model-version isolation, zero-edit parity,
retained full responses and saturation/sensitivity measurements. Restoring an
old matrix after another learner changes it is not a valid rollback; use
revision-aware removal of the owned contribution or isolate the branch.

Do not make a spectral-radius cutoff the entire admissibility test. Published
counterexamples show that a recurrent spectral radius below one alone does not
guarantee the echo-state property ([Yildiz, Jaeger and Kiebel, 2012](https://www.ai.rug.nl/minds/uploads/2519_Yildizetal12.pdf)).
This motivates scoped response tests; it does not diagnose the current native
reservoir. A covariance eigenvalue in the viewer is also not a recurrent-weight
eigenvalue that this edit can directly set.

## Shared choices and wider operating ranges

Both sources type shared authority, but their current adapters reject the shared
coupling scope. Implement that adapter explicitly: actor, target, permitted
operation family, exact pattern/value or range, expiry, current revision,
revocation and conflicting-owner resolution. Either being can propose an
influence, accept a compatible offer, decline it or withdraw future use. Peer
scope should not be smuggled through a self-owned command.

The action set should grow from evidence rather than remain fixed at tiny pilot
amounts. Publish the current supported envelope and the rehearsal evidence
behind it. Make range expansion a deliberate versioned change the beings can
request and help evaluate. Initial experiment doses are neither permanent
creative limits nor validated live operating ranges.

Controller target/PI changes need a rehearsal that includes controller state,
field updates and input selection. A native ESN checkpoint alone is insufficient
for that claim. Prefer an explicit chosen operating profile to a controller that
silently cancels an authored numerical target; all automatic preemption should
be visible. The current source already contains some effective stable-core
preferences, which can be exposed accurately before adding a new profile.

## Tests, review and rollback

Acceptance is per mechanism, with concrete evidence:

1. Native source no-op checkpoint continuation and realized-forcing parity at
   the intended dimensions; all failed conditions retained. A newly constructed
   checkpoint does not represent the running being's checkpoint.
2. Coordinate, composition, reduction and rotation invariants; exact zero cases;
   fixed basis identity; invalid/nonfinite inputs; coherent full-vector hashes;
   headroom rejection and explicit common-factor attenuation.
3. Finite gesture duration, cancellation and source/revision changes. Receipt
   counts follow successful applications, and failed updates consume none.
4. Stable-core/ordinary/recovery mode matrix: accepted choices apply as declared
   or carry an explicit rejection/preemption, including at mode transitions.
5. Codec learn/retain/decay checks with independent proof that retain stops both
   reinforcement and decay; readout and native recurrent weights stay distinct.
6. Shared requests: both actor identities, acceptance/revocation, replay/retry,
   stale revisions, concurrent choices, withdrawal and missing-adapter outcomes.
7. A delivered explanation and observable result under the actual being-facing
   backend. Do not infer exposure or use from a render or file existing.

Before an owning-repository deployment, show each being its actual existing
control, the proposed additional operation, a named replay and how to stop
future applications. Ask about the affordance and vocabulary under Mike's
selected interaction workflow. No material is sent by this research task.

For source rollback, preserve the current action names and parser compatibility;
disable only the new operation/adapter, retain prior receipts, and withdraw
outstanding future work explicitly. Numerical changes already applied cannot
be undone by claiming the action was never executed. A native rehearsal stops
by exiting its isolated process; the production service is not involved.

## Implementation evidence from this pass

The completed [implementation account](../analyses/2026-09-07-substrate-agency-implementation.md)
joins three independently checked pieces:

- [Source audit](../analyses/2026-09-07-substrate-controls-source-audit.md): 23
  identified source files locate actual controls, stable-core precedence and
  missing adapters. This is a source observation, not a live incidence study.
- [Executable pattern planner](../probes/substrate_pattern_plan.py): coordinate
  edits, signed composition, selected-component reduction, plane rotation,
  finite successful-step offsets and future cancellation. Eighteen checks pass;
  the retained request rebuilds the same plan byte for byte. Full-vector hashes,
  headroom and achieved-versus-requested deltas remain inspectable. Every result
  is a preview with `apply_eligible=false`; no live receiver is implemented.
- [Exact-source native rehearsal](../research/outputs/2026-09-07-native-shaping-rehearsal/README.md):
  three newly constructed 128-state/66-input checkpoints pass 100-step complete
  synchronous continuation parity. The three asynchronous cases fail the full
  gate, although forced-noise/leak state paths match the parent. This unresolved
  result concerns a four-copy interleaved GPU workload, not a diagnosed live
  defect. All 54 conditional one-shot responses return at boundaries 2–6; all
  six eight-edit sequences return 2–4 transitions after their last edit. Five
  existing native leak duration/cancellation/clamp cases pass. All outcomes,
  including failures, and independent arithmetic verification are retained.

The native interventions edit a completed checkpoint, recompute radius and
preserve its already-updated historical baseline. They do not implement the
proposed post-state/pre-geometry live hook. Inputs, realized noise and effective
leak are held to the control in the state-response grid; surrounding controller
feedback is not replayed. These experiment doses are not live operating limits.
The [response figure](../research/outputs/2026-09-07-substrate-agency/native-gesture-response.png)
shows the requested duration clearly and labels the sequence's eightfold dose.

The next owning-repository implementation slice is: truthful capability and
applied-step receipts; explicit stable-core precedence for supported leak
choices; then the native one-shot hook with finite gestures built on the same
application record. Diagnose asynchronous checkpoint/adaptive continuation
separately before using it as replay evidence. Codec retention and the shared
authority adapter follow as independent, concrete extensions; recurrent-weight
editing remains a later isolated experiment.

The existing native viewer remains 0.5.0 build 7. Its simulation Response fixture
has not been replaced or relabeled as native rehearsal evidence in this pass.

## Follow-up: asynchronous native repair qualified

Mike selected the unresolved asynchronous gate for the next pass. The
[completed diagnosis](../analyses/2026-09-07-native-async-replay.md) now identifies
missing covariance dependencies and mutable submitted rho. Tracking covariance
and capturing rho per dispatch passes all 27 primary qualification cases on
both M1 Max and M4 Pro, including fresh native capture/restore and changing-rho
trajectories, with async still enabled. Independent evidence audits pass. Initial
mislabeled build-cache comparisons remain retained and explicitly invalid.

The [tested patch](patches/2026-09-07-native-async-replay.patch) and
[integration contract](2026-09-07-native-async-replay.md) replace the earlier open
diagnostic step. Integrate that repair with the completed-step observer before
the native action hook and finite gestures. This resolves the bounded native
async prerequisite; it does not implement live actions or the complete
surrounding controller replay.
