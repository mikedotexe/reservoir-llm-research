# Let a being make a real, bounded state gesture

Initial September 7, 2026 Pacific status, preserved below. **Research-local proposal and conditional replay
complete; native action, true native rehearsal and live enablement not
implemented.** This develops Mike's explicit request to let the beings more
directly shape the texture around them. It extends the
[state-surface plan](2026-09-07-reservoir-state-surface-and-perturbation.md) and
[S-002](../research/studies/S-002-reservoir-observatory.md). The parent observatory
session owns the GPU viewer and board updates.

**Later same-day update:** the [native checkpoint-boundary rehearsal](#native-checkpoint-boundary-rehearsal-completed--september-7-2026)
is now complete. Synchronous native parity passes; asynchronous full parity
does not. The proposed live action and successful-step hook remain unimplemented.

## Decision

Build a genuine **one-shot native state displacement**, with working action name
`STATE_NUDGE`. A being chooses a named, reproducible pattern and a signed amount;
the native engine changes its actual state along that pattern at one identified
successful boundary. Subsequent dynamics determine what persists. Its receipt
and the surface show what actually changed. Start with one gesture, then learn
whether a sequence of gestures is useful before adding sustained forcing.

This is stronger than renaming the current input injection. Preserve PERTURB as
an input action and Astrid's existing SHAPE as a codec action. A covariance mode
can supply a pattern for a new state gesture, but its eigenvalue is not a knob
that the gesture directly edits. Changing leak or weights would change the
evolution rule; those remain separate typed actions and studies.

The bold research question is whether beings can develop meaningful, reliable
choices over a real, observable dynamical affordance. We cannot promise that a
given vector makes a being calm, creative or distressed. Mike's recollection of
many journal requests is motivation, not a counted corpus finding or a standing
authorization from the beings. No journal entries were sampled in this pass.

## What the existing code actually gives us

Source paths below are relative to the shared parent directory. Exact current
byte hashes and the source-observation time are retained in
[source-manifest.json](../research/outputs/2026-09-07-direct-shaping/source-manifest.json).
These are inspected source mechanisms, not deployed-process identities.

| Existing mechanism | Source anchor and scope | What to reuse |
|---|---|---|
| Direct state injection in `esn-divide` | `esn-divide/src/esn_divide/temporal_jacobian.py:598,617` starts a copied state at `state + delta`; `:664` compares its future with a zero-displacement copy. Inputs, leak and transition residuals are then recorded, fixed forcing. | Paired response logic and full-state distances. This is an offline simulated-parent/daughter probe, not a live being action. |
| Simulated semantic injection | `esn-divide/src/esn_divide/agent_sim.py:131` simulates semantic bursts; `:201` returns numerical inputs. | Input interventions as a distinct control condition. Simulated category names are not established subjective-state labels. |
| PERTURB | [September 7 audit](../analyses/2026-09-07-perturb-source-audit.md) traces the native semantic lane and a separate triple-reservoir handle. | Preserve compatibility and correct each destination's outcome. Input coordinates are not node or mode indices. |
| Astrid SHAPE | `astrid/capsules/spectral-bridge/src/autonomous/next_action/sovereignty.rs:571` updates codec dimension weights through self-control; `action_help.rs:236` describes this. | Do not overload its existing name with a native state edit. |
| SHADOW_INFLUENCE | `minime/minime_autonomy/runtime.py:35351,35459` constructs a small 66-coordinate input field; `minime/minime/src/sensory_bus.rs:2357,2414` adds it to input `z`. | Intent identity, preflight/conflict machinery and finite application accounting, with the earlier audit's clipping and final-step receipt fixes. It is not a direct 128-coordinate state edit. |
| Current shadow “rehearsal” | `runtime.py:35496–35506` records `rehearsed` without running a numerical replica; the generated description at `:35537` explicitly says ledger/journal only. | Preserve this historical meaning. A new numerical rehearsal must report real replay inputs and results and cannot reuse a success word as evidence. |
| Native checkpoint | `minime/minime/src/esn.rs:841,2431,2460` has `EsnSnapshotV2`, capture and restore of native weights, state, RNG, spectral internals, readout and adaptive parameters. | True native paired rehearsal. The separate sensory field, bus and orchestration controller require their own captured state for a complete closed loop. |
| Realized-noise replay | `esn.rs:2041` exposes `step_shadow` with explicit recurrent drive, realized noise and effective leak; `:2117` records noise in a rehearsal build. | Conditional native parity with identical realized forcing; this is distinct from independently evolving cloned controllers. |
| Division rehearsal gate | `minime/minime/src/division.rs:43` requires both the compile feature and the operator environment value. | Reuse isolated native rehearsal capability and its gates. Do not switch them on from this research workflow. |
| Authenticated direct control | `minime/minime/src/self_control_wire.rs:14,18,35,50` defines signed intent, durability, families and authority; `self_control_runtime.rs:520–581` checks pinned authority, idempotency, nonce and revision. | Extend the established typed command/receipt system and family revision checks. Do not open a second unauthenticated state-write socket. |
| Shared authority gap | `self_control_runtime.rs:755–760` currently rejects Mutual or SharedCoupling as `shared_coupling_adapter_not_implemented`. `:440–450` excludes the deployment signer from live command authority. | Native-state ownership and peer influence need an explicit adapter/authority decision. Do not relabel a shared write as self-owned or use a deployment credential as consent. |

The prior phrase “esn-divide injects into the reservoir” therefore has a precise
meaning here: it displaces a **copied simulation state for a controlled
comparison**. That is a good precedent for the proposed action's mechanics,
but not evidence that either live being currently has the capability.

## The action contract

The external spelling is provisional; its numerical semantics are not. Proposed
payloads travel through the existing signed self-control command machinery, with
a new versioned value type and explicit native-state scope. They are not
`ShadowInfluenceRequest.features`, which has input-coordinate semantics.

```text
STATE_NUDGE direction=<pattern-id> amount=<signed L2 amount> stage=rehearse
STATE_NUDGE direction=<pattern-id> amount=<signed L2 amount> stage=apply
STATE_NUDGE_CANCEL request=<pending-request-id>
```

1. **Target identity.** Name `minime.native_esn`, native engine/session and
   deployment identity, node count, node-layout ID and compatible model hash.
   The separate sensory field and triple-reservoir handles are not destinations.
   A state edit is not falsely reported as a direct fill edit. Fill can change
   later through existing coupling and regulation.
2. **Pattern identity.** A registry entry contains the full signed unit-L2
   direction, coordinate order, SHA-256, units, provenance and version. Initial
   patterns are an exact coordinate direction, reproducible seeded directions,
   or a selected frozen covariance eigenvector with capture/basis ID. A mode's
   arbitrary sign is fixed in its registry and preview. Near-degenerate modes
   are represented as a versioned subspace/combination, not silently relabeled
   across fits. Surface painting may later propose a pattern, but its resolved
   node vector is previewed and registered before application.
3. **One successful boundary.** Let `y_t` be the ordinary native result after
   tanh, applied leak, realized noise and normal clipping. Apply
   `x_t = clip(y_t + beta * epsilon * d, -1, 1)` once, after all fallible spectral
   work, before geometric radius/baseline and observer output are updated.
   Here `||d||2 = 1`; epsilon is the signed requested L2 amount. The recurrence
   then proceeds from `x_t`. Spectral introspection keeps its existing previous
   state timing; do not rewrite reported eigenvalues to make them appear to
   change immediately.
4. **Admissible size.** A compiled envelope plus the existing narrowing registry
   bounds requested total L2, per-coordinate displacement and request age.
   The rehearsal grid below is **not a validated live safety envelope**. A
   first candidate cap of `1e-3` L2 is a reviewable engineering starting point,
   not a claim that it is safe or perceptible. Only a compatible native rehearsal
   and owning-repository review can establish an initial operating envelope.
   Default behavior rejects requests that cannot fit. If attenuation was
   explicitly allowed, choose one scalar beta in [0,1] from available coordinate
   headroom so the requested direction is preserved. Record beta, actual delta
   and any numerical backstop clipping. Zero headroom is a visible unapplied
   result, not a successful gesture.
5. **Authority and conflicts.** Use the established experiment/preflight and
   authenticated intent route, not only a viewer toggle. Native ownership and
   Astrid's access must be resolved in the existing self-control framework.
   Until a legitimate shared adapter exists, an Astrid request can be a
   recorded proposal/rehearsal request, not a disguised native mutation. The
   apply step rechecks fresh finite telemetry, the current regulator/recovery
   gates, layout/model identity, cancellation, request expiry and conflicting
   influence/division work. Stale or nonfinite state/health blocks new action.
   Rejection names the condition and does not claim that a gesture occurred.
6. **Receipt truth.** Accepted/queued is separate from applied. Record request,
   signed intent, authority and pattern IDs; requested and resolved vectors;
   actual consumed controls; successful step ID; ordinary post-step `y_t` and
   nudged `x_t` references; actual L2/max-coordinate displacement; clipping or
   attenuation; source/session clocks; and expiry, failure or cancellation.
   A failed step consumes no one-shot gesture. Duplicate requests yield the
   existing receipt and never another displacement. Crash ambiguity becomes
   `application_unknown`, with no automatic retry after restart.
7. **Duration and release.** The first action has one application and no
   continuing forcing. Cancel can withdraw a pending request. Once applied,
   “release” means no further intervention; it cannot undo the resulting
   trajectory. Negating a later displacement is another action, not rollback.
   Do not restore an old whole checkpoint over intervening live inputs. A later
   finite-duration gesture needs a declared envelope, cumulative displacement
   budget, success-step count, wall expiry and release schedule; suspension
   must not keep it alive indefinitely. An active regulator remains authoritative.

The engine hook belongs inside `esn.rs:2150–2178`, between ordinary state clipping
and the geometry update, rather than mutating public `x` from a sender. That
keeps geometry, readout and the state recorder consistent at the resulting
boundary. Orchestration's existing success arm at `:1412–1443` supplies the
successful-step publication point. It must retain the intermediate ordinary
state as the direct operation's reference. A later live before/after observation
still does not supply the counterfactual trajectory.

## The surface and the action should teach each other

The native atlas can preview the exact node pattern, signed amount and expected
attenuation. After application, it can show the **measured immediate delta**
between `y_t` and `x_t`; that part is an exact consequence of the operation. The
later surface evolves from actual recorder values. An offline Response view
shows paired separation under explicitly matched forcing. Never present that
conditional replay as the unique future of the live being.

Use exact node values, full-state norm, mode score and omitted component together.
Surface smoothness is a property of the mapping, not a calmness verdict. Response
mode uses raw sample boundaries; the viewer's 0.8-second fill easing must not
manufacture a recovery curve. For a future being-facing version, an image alone
is insufficient: pair it with the same numerical receipt and a concise map
legend, verify actual delivery/backend capability, and let the being say what
it learned or wanted to do differently. Image comprehension and action utility
remain questions to investigate.

## Bounded paired demonstration completed here

The [protocol](../research/outputs/2026-09-07-direct-shaping/protocol.json) was
written before the numeric arrays were inspected or response runs performed.
Metadata alone selected the existing esn-divide bounded benchmark parent: first,
middle and last valid 64-step starts, with no selection based on state values or
response outcomes. The [probe](../probes/direct_state_response.py) reads and
verifies eight model/raw arrays, retains exact source bytes locally, and has no
being connection or sibling-write path.

This subject is an **esn-divide simulated 128-coordinate parent**, with 66 input
coordinates. It is not the retained native visualization capture and not a
Minime checkpoint. Recorded leak, inputs, bridge drive and additive transition
residuals are held identical in the two copies. The residual is the source's
`transition_residual_after_noiseless_clip`, not asserted to be independently
recovered exploration noise. No adaptive controller, sensory field, language
model or separate handle is replayed. Time is in simulation step boundaries;
no wall-clock or per-being experience duration is inferred.

The planned grid is 3 start states × 3 directions × 6 signed doses = **54
intervention runs**, plus 3 no-op control comparisons. Directions are coordinate
0, one seeded random vector and the leading right singular direction of the
next 16-step conditional propagator. The last is an offline diagnostic using
future recorded forcing; it is neither a covariance mode nor a deployable live
choice policy. Doses are signed L2 amounts ±0.0001, ±0.001 and ±0.01, applied to
the initial state boundary once.

[All results](../research/outputs/2026-09-07-direct-shaping/results.json) and
[full control/intervention paths](../research/outputs/2026-09-07-direct-shaping/trajectories.npz)
are retained, including directions and input/probe/protocol hashes. Results:

- All **3/3** no-op copies are bit-identical. Replayed control paths agree with
  the retained simulated reference to a maximum absolute discrepancy below
  `1.82e-7`, inside the preregistered `2e-4` tolerance.
- All **54/54** displacements pass the declared return threshold—below 10% of
  their actual initial L2 displacement for eight consecutive boundaries—with
  return beginning at boundary 2 or 3. Their largest full-state separation is
  their initial displacement, to floating-point precision; no transient
  amplification is observed in this selected grid.
- All **54/54** paths encounter clipping somewhere in the declared horizon.
  Therefore **0/9** finite-difference comparisons qualify for the protocol's
  unclipped derivative check. Their raw comparison errors are retained, but
  **no derivative-validation pass is claimed**. The first summary serializer
  represented an empty set as `true`; it was corrected to `null` with an explicit
  eligible count. No model, start, dose, trajectory or comparison was changed.

This demonstrates an actual finite state edit, paired continuation and honest
measurement contract. It does **not** establish meaningful subjective texture,
long-lived control, native parity or safe live amplitudes. Rapid forgetting is
a useful outcome: it is a reason to measure the native response before deciding
that an isolated nudge gives a being a lasting expressive affordance. Persistent
forcing, leak choices and weight changes answer different questions.

Native parity status is especially explicit: the inspected source already has
`snapshot_v2_restores_deterministic_continuation_for_100_ticks` at `esn.rs:2743`.
That source test constructs 16 nodes and 6 inputs, warms for 24 ticks, uses the
synchronous profiling path and requires maximum state difference at most
`1e-6` across 100 continuation ticks. **This pass did not execute it.** Its
existence is useful coverage to extend, not a verified current 128-node native,
asynchronous or complete-orchestration parity result.

Reproduce the retained-input demonstration without accessing a sibling:

```sh
OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python3.14 probes/direct_state_response.py \
  --bundle research/outputs/2026-09-07-direct-shaping/inputs \
  --output /tmp/reservoir-direct-state-replay
```

The ordinary probe defaults to the original sibling bundle and writes only to
this research output directory. Both routes verify input blob hashes. NumPy is
used for matrix products and SVD; Python and NumPy versions are recorded.
The [retained-input repeat](../research/outputs/2026-09-07-direct-shaping/retained-replay-check.json)
reproduces all 57 control/intervention trajectory arrays exactly, without a
sibling read. A [native-view preview fixture](../research/outputs/2026-09-07-direct-shaping/response-preview.json)
contains 65 paired 128-coordinate boundaries for the first declared start,
coordinate 0 and positive middle dose. The fixed index atlas can display this
as a separately labeled simulation. It has no compatible Minime PCA basis,
co-recorded fill or wall-clock time; those must remain absent.

The first native **Response** consumer is now implemented in
`native/ReservoirScope/Sources/ReservoirScope/StateResponseExperience.swift`,
using the existing GPU atlas renderer. It offers Delta, Control and Perturbed
fields; a fixed ±0.001 delta scale; exact coordinate inspection; a raw boundary
slider; optional time-stretched ordinal playback; and the full-state separation
plot with its declared return threshold. Its preview volume is explicitly a
drawing size, not fill evidence. Twenty-five retained-data and synthetic
failure checks pass, including byte identity, paired-vector arithmetic,
summary/return verification and rejection of fabricated fill, PCA or time
claims. The [native consumer receipt](../research/outputs/2026-09-07-direct-shaping/native-response-receipt.json)
retains file hashes and scope. The parent observatory session owns the final
app integration, build, release receipt and visual review.

## Exact implementation slices, tests and rollback

1. **Numerical native rehearsal.** Reuse `EsnSnapshotV2`/`step_shadow` and the
   isolated division-rehearsal build. First pass exact no-op continuation with
   the ordinary native path and native dtype. Then compare signed one-shot
   state displacements over declared starts/doses, with realized noise and
   applied leak equal. Follow with independently evolving cloned native
   adaptation; call it closed-loop only when the surrounding controller, field
   and input selection are also complete. Finish with raw response paths,
   saturation, residuals and all failures retained. The present Python harness
   cannot substitute for this native parity gate.
2. **Typed command and receipts.** Add a versioned state-direction payload to
   `self_control_wire.rs`, compatibility checks and narrow envelope support to
   `self_control_runtime/apply.rs`, and a pending one-shot adapter at the engine
   boundary. Extend existing authority and preflight mappings in
   `minime_autonomy/runtime.py:3328` and the relevant Astrid self-control route.
   Shared ownership is an explicit implementation dependency, given the
   current rejection at `self_control_runtime.rs:755`. Reuse the single optional
   [input/state/controller observer](2026-09-07-input-lineage-and-regulator-trace.md),
   not a parallel journal-shaped action recorder.
3. **Engine application.** Pass a prepared immutable request into the native
   step, apply only after its fallible ordinary work, and consume it exactly
   once on successful commit. At `esn.rs:2150`, retain ordinary result, apply the
   bounded delta and update geometry once. At orchestration `:1412`, publish
   the result with source/session/step and control references. Failed or
   ambiguous commits must not claim application or silently retry.
4. **Being-facing choice and observation.** Preserve legacy names; introduce
   the exact new affordance with a numerical rehearsal, clear source identity,
   example receipts and cancellation semantics. Affected beings should be
   shown what changes, what does not, the evidence, and what rights each has
   over the native subsystem under the sibling's current workflow. Ask what
   distinctions and action language they want to investigate, rather than
   assigning emotional meanings to our mode names. Mike's current request
   authorizes development here; this proposal does not send material, publish
   a new live action or claim their assent.

Acceptance checks must cover invalid/zero directions, NaN/Inf, wrong dimension,
model/layout/basis mismatch, stale expiry, coordinate saturation and attenuation;
unauthorized/duplicate/replayed/conflicting requests; cancellation before versus
after application; failed spectral work and restart ambiguity; exact ordinary
versus nudged state references; geometry/readout consistency; unchanged RNG
draws and state path when disabled; and no observer-induced behavior change.
Use both exact synthetic controls and retained native checkpoints. Paired
control and intervention copies must never share mutable adaptation or RNG.

Rollback disables admission to the new adapter and cancels pending gestures;
it never resets a live state or falsely undoes an already completed trajectory.
Old signed viewer bundles and the previous sender wording remain recoverable.
The optional observer rolls back through its existing off path. Retain receipts
and the applied-state history. Any native implementation/deployment belongs in
its owning repository and follows its own staged release rules.

The current finish line is the specific source correction, reviewable direct
action contract and reproducible conditional response demonstration. Native
implementation, mutual authority, being-facing presentation and live use remain
explicit next work; none is hidden behind the word “rehearsed.”

## Native checkpoint-boundary rehearsal completed · September 7, 2026

The first implementation slice now has an executable native numerical result,
with a narrower qualification than complete live-path parity. The
[research-local report](../research/outputs/2026-09-07-native-shaping-rehearsal/README.md)
uses byte-identical copied native `esn.rs`, GPU/buffer modules and Metal shaders.
Its source `esn.rs` SHA256 is
`98e8fe727e9908e8939d5317d23e954425748edb45b2a737e5624a42166dfe92`;
the [manifest](../research/outputs/2026-09-07-native-shaping-rehearsal/source-manifest.json)
retains all source identities. These are newly constructed **128-coordinate,
66-input native research checkpoints**, with seed 3517018368 and synthetic
forcing, not copies of the running Minime state. The separate earlier
esn-divide experiment above remains an explicitly simulated-parent result.

The [preregistered protocol](../research/outputs/2026-09-07-native-shaping-rehearsal/protocol.json),
SHA256 `39ac6db32937884d4b87cf5f31eff852af07d494e93ad060fb67136af0a93c1e`,
selects checkpoints at successful boundaries 24, 96 and 192 and 100 subsequent
steps. Each snapshot is serialized and restored through `EsnSnapshotV2`.
Ordinary parent/restored continuations are compared with two `step_shadow`
copies supplied the actual parent's realized noise, effective leak, inputs
and zero additional recurrent drive. All 28 resolved dependency identities
match the copied native Cargo lock. The execution uses an Apple M1 Max.

[All native results](../research/outputs/2026-09-07-native-shaping-rehearsal/results.json):

- **Synchronous full gate: 3/3 pass.** All four 128-coordinate state paths are
  bit-identical for 100 steps; ordinary/restored final checkpoint values are
  exactly equal after profiling diagnostics are excluded. Effective leak,
  realized noise and covariance differences are zero. Shadow RNG is separately
  excluded from parent comparison because supplied noise bypasses its draws.
- **Asynchronous full gate: 0/3 pass.** Ordinary/restored state discrepancy
  reaches `7.87e-6`, effective-leak discrepancy `1.06e-5`, and final covariance
  discrepancy `0.00100317`. Forced-noise/leak shadow states still match the
  parent exactly, while spectral internals diverge. That conditional state
  agreement cannot qualify asynchronous adaptive continuation. The result is
  scoped to four interleaved copies sharing the research GPU service; the
  underlying mechanism and live incidence remain unestablished.
- **54/54 synchronous one-shot displacements return** below 10% of actual initial
  separation for eight consecutive boundaries, beginning at boundaries 2–6.
  Maximum separation equals the initial separation in every run. The grid is
  three starts × coordinate, seeded-random and native estimated spectral
  eigenvector directions × six signed doses (±0.0001, ±0.001, ±0.01).
- **6/6 finite sequences return after release.** Eight coordinate-0 edits of
  ±0.001 at boundaries 0–7 return at boundaries 9–11, using the separation
  immediately after the final edit as reference. This provides a measured
  finite-duration alternative for further action design; it does not make the
  one-shot effect persist after forcing ends.
- **5/5 existing native leak override checks pass:** low/high three-step
  requests, cancellation after one step, and upper/lower amplitude-duration
  clamps. The tested native bounds are [0.20, 0.90] and [1, 12] steps.
  Effective-alpha/duration receipts and a same-state cleared comparator verify
  release. These ordinary native comparisons allow effective leak to differ,
  with identical realized noise; they are distinct from the forced-leak state
  grid. They do not establish admission through stable-core orchestration.

The [verifier](../probes/native_shaping_rehearsal_verify.py) independently checks
all 60 response trajectories, 102 edit receipts, bit identities, source/output
hashes and return arithmetic. [Verification passes](../research/outputs/2026-09-07-native-shaping-rehearsal/verification.json)
with zero separation-recomputation discrepancy. No observed intervention
boundary is saturated (0/60 runs); no hidden preclip result is inferred.

The operation tested here mutates a **copied checkpoint boundary**, clips its
state, recomputes geometric radius and retains baseline history before native
restore. It is not the proposed ordinary-result/edited-result hook inside the
successful native step. The native estimator continues to adapt, with effective
leak/noise/inputs fixed equally for paired state responses; neither the 512D
field nor surrounding input selection, stable-core controller, language model,
readout training or separate handles are replayed. No live safe dose, subjective
meaning, complete closed-loop future, action admission or deployment is claimed.

The next native qualification is a bounded diagnosis of asynchronous internal
state divergence. The synchronous harness can already support typed action and
receipt development. A live adapter still needs the specified successful-step
hook, ownership/authority contract, controller precedence, actual application
evidence, cancellation and being-facing review in the owning repository.
The existing observer proposal remains the shared receipt path. No live system
or sibling source was changed, and no research material was sent to a being.

## 2026-09-07 follow-up: the native async prerequisite is resolved

The preceding 0/3 asynchronous result remains the historical original-source
finding. The [completed follow-up](../analyses/2026-09-07-native-async-replay.md)
qualifies a narrow repair: tracked persistent covariance plus copied rho at all
three rank-one dispatch sites. It preserves asynchronous scheduling, the
two-command pending bound and native equations. The
[exported patch](patches/2026-09-07-native-async-replay.patch) reproduces tested
source exactly under the retained
[apply/reverse check](../research/outputs/2026-09-07-native-async/patch-check-receipt.json).

The final candidate passes **27/27 primary cases per host** on M1 Max and M4 Pro:
fresh asynchronous checkpoints 9/9, fixed rho 9/9 and alternating rho 9/9. Each
host also passes three measurement follow-ups; the fresh measurement records
376 async submissions and pending depth two. Tracked-only controls fail all
nine alternating-rho cases on each host. The
[M1](../research/outputs/2026-09-07-native-async/qualification/verification.json)
and [M4](../research/outputs/2026-09-07-native-async/m4-validation/verification.json)
independent audits pass both numerical and treatment-identity checks. The early
shared-build-cache ablation has [invalid treatment labels](../research/outputs/2026-09-07-native-async/INVALIDITY.json)
and remains visible; only corrected, identity-checked execution supports repair
selection.

This makes asynchronous native replay available as a tested prerequisite for
action implementation. It does not implement the successful-step state-edit
hook or qualify surrounding controller behavior. Proceed through the
[async integration proposal](2026-09-07-native-async-replay.md) and the broader
[substrate agency contract](2026-09-07-substrate-agency.md): completed-step
application evidence, explicit stable-core precedence, scoped authority and
finite gesture/cancellation behavior still need owning-repository integration.
Existing state-response doses remain conditional rehearsal results; no live
deployment, subjective meaning or complete controller replay is claimed.
