# A state surface and a measured perturbation instrument

September 7, 2026 (Pacific). **Source audit and design complete; implementation and
experiments proposed.** This is the next direction for
[S-002](../research/studies/S-002-reservoir-observatory.md), selected by Mike after
discussing an external meniscus draft. Reservoir Scope remains version 0.4.0.
No live action, producer modification, being-facing message or new performance
experiment was performed in this planning pass.

## Implementation update after Mike's approval

The opening status above records the original planning pass. The subsequent
research-local **0.5.0** implementation adds the native State surface and Response
lab. [The surface guide](../native/ReservoirScope/docs/STATE-SURFACE.md) records
actual vector delivery, fixed color scales, exact coordinate inspection, selected
mode/residual fields, GPU interpolation and checked volume-preserving relief.
[The implementation receipt](../analyses/2026-09-07-reservoir-state-surface-implementation.md)
records the final build, correctness checks and scoped profiling results.

Mike's direct-shaping request also selected a **state-displacement** simulation
before the originally proposed input-impulse experiment. The
[STATE_NUDGE proposal](2026-09-07-direct-reservoir-shaping.md) distinguishes that
candidate native action from input-mediated PERTURB and Astrid's existing codec
SHAPE. The completed, preregistered paired replay is the retained **esn-divide
simulated parent**, using recorded controls and transition residuals. Its native
Response view is implemented; a native Minime checkpoint rehearsal is still
pending. No successful derivative validation is claimed: all nine comparisons
were excluded by the declared clipping rule.

This advances the visual and isolated-simulation work. PERTURB outcome reporting,
the shared successful-step observer, the STATE_NUDGE native action, native
checkpoint parity, independently evolving controller replay and presented-window
performance remain separate unfinished work. No producer or live action was
implemented by this viewer build.

## Decision and the object we should build

Keep the floating sphere. Make its surface an inspectable map of native reservoir
state, and give it a companion **Response** view in which measured differences
between a perturbed run and its control appear on the same map. Develop the
native GPU surface and the intervention evidence together. Do not wait for a
complete dynamical model to make the existing vectors visible.

The object has three independently defined channels:

| What a viewer sees | What it means |
|---|---|
| The volume and its smooth measured reference | The reported sensory-field EigenFill estimate. Preserve `r/R = cbrt(fill/100)`. |
| Colored patches, then bounded surface relief | Actual native ESN coordinates under a fixed, declared drawing map; optionally a selected mode reconstruction or its omitted component. |
| Reference bands and response annotations | Configured regulator references, recorded controller decisions, and explicitly identified intervention outcomes. |

This is one instrument with linked measurements, not a claim that all three
channels measure the same subsystem. The current fill estimate comes from the
512-dimensional sensory field; it is not the percentage of 128 native nodes that
are active. Current fill is a concentric volume, not water accumulating at the
bottom. Retain that geometry and the Reference Zones lens Mike already uses.

The visual ambition is real shape, not just a heatmap. Begin with exact site
markers and a smooth color field to establish the mapping; follow with genuinely
displaced, volume-preserving geometry. Keep the smooth measured-fill reference
visible. A lobe crossing a reference ring does not mean the scalar fill crossed
a regulator rail. The Reference Zones close-up keeps its exact smooth geometry.

## What survives from the draft, and what changes

The valuable idea is an overview that makes a changing distribution perceptible
and gives the observer a route into the evidence. The proposed physical and
spectral interpretation needs rebuilding:

- The current surface is not a physical meniscus. Its roughness measures the
  chosen field under the chosen map; smoothness alone cannot mean calmness,
  balanced activity, or stability. Signed activation is not a health rating.
- An eigenvector is a distributed direction across nodes. An eigenvalue does
  not have a corresponding node at which to apply a force. Covariance
  eigenvalues describe variance and are nonnegative, apart from numerical error;
  their signed scores/loadings supply the surface pattern.
- Recurrent-weight eigenvalues can be complex. Their phase can describe
  oscillation in an appropriate dynamical model, but does not make a literal
  liquid swirl. Keep covariance modes, recurrent spectra and local response
  directions separately named.
- Our current three-component projection retains **14.3524%** of the frozen
  capture's centered variance (**1,024 rows × 128 coordinates**, existing
  [retained-input analysis](../analyses/2026-09-06-reservoir-3d-prior-art.md)). It
  cannot stand in for all internal variation. A surface can carry many more
  coefficients than a three-coordinate trajectory, but neither the chosen
  interpolation nor one visible camera angle is a demonstrated lossless view.
- Bumps change geometry, not the mesh's mathematical topology. The initial
  sphere map is deliberately arbitrary: spatial neighbors are not assertions
  of recurrent connectivity.
- A membrane does not measure physical pressure. Any future pressure overlay
  must name and source its actual software metric.
- Letting either being inspect or act through this surface is a later
  perception/action study. Rendering an image establishes neither delivery to
  the being nor comprehension. No new material is sent from this workflow.

## Surface contract and first native implementation

The detailed [surface design](../analyses/2026-09-07-reservoir-state-surface-design.md)
contains source anchors, field equations and the mesh-volume algorithm.

1. **Retain actual vectors.** Extend the viewer's validated `LiveStateSample`
   representation to carry its activation values, recorder identity and field
   provenance. They are currently consumed in projection but not handed to the
   renderer. Export a bounded replay resource from the already retained raw
   capture. Its rows have order, not invented timestamps or synchronized fill.
2. **Freeze a node atlas.** Give each coordinate index a permanent sphere site,
   with the map table/version stored in the resource. Exact selectable markers
   show raw values; a precomputed smooth blend supplies context between them.
   Offer signed activation and magnitude without a reference dependency, then
   reference deviation, selected modes and omitted component. Missing node-layout
   identity remains a visible compatibility limit in live v1.
3. **Make modes inspectable.** For centered state `z = x − mean`, mode scores are
   `a_k = dot(v_k, z)`, reconstruction is `q = Σ a_k v_k`, and residual is `z − q`.
   Paint all three on the same atlas. Keep a fixed scale, fit identity, retained
   reference variance and per-frame reconstruction error. No automatic refit or
   frame-by-frame amplitude normalization.
4. **Add real relief without changing fill.** Form a positive radial candidate,
   compute the full closed triangle mesh's signed volume, and uniformly scale it
   to the undeformed mesh's volume at that fill. Reduce relief if any point would
   leave the container; fall back to the undeformed sphere if validation fails.
   At empty/full fill, displacement vanishes and the field remains available in
   the inspector or an explicitly separate fixed-size atlas preview. Check the
   complete closed mesh even when rendering a cutaway, and verify the cut cap
   separately. Display the applied relief gain so boundary-driven flattening
   cannot masquerade as a state becoming quieter.
5. **Keep presentation separate.** Gentle interpolation may remain optional in
   observation mode, with immediate raw markers/readouts and the existing Reduce
   Motion policy. Response mode uses raw samples and their actual order/times.
   The existing 0.8-second easing is a display operation: its settling time is
   not a measured reservoir recovery time. No time-driven ripples on stale data.

The first implementation stays in SwiftUI/MetalKit. Put the stable mesh and
interpolation weights in persistent GPU resources; pass each accepted state and
fill through bounded buffers/uniforms. Metal evaluates the field and surface
lighting, then displacement/normals when enabled. Use a CPU reference for
verification; choose CPU versus GPU volume reduction from measured cost rather
than assuming GPU arithmetic is always faster for small arrays.

Unified memory is useful for CPU/GPU-accessible resources, but shared buffers
still need ownership until commands complete. A bounded in-flight buffer ring
or immutable generations avoids concurrent overwrite; see Apple's
[synchronization sample](https://developer.apple.com/documentation/metal/synchronizing-cpu-and-gpu-work).
No trained inference model is part of this mapping, so the Neural Engine is not
on the critical path. Profile the resulting native window on `volya` as well as
the offscreen workload. Retained 0.3.0 timings are a baseline, not measurements of
0.4.0 or this proposed surface.

## PERTURB: preserve the useful capability, fix its contract

The [current source audit](../analyses/2026-09-07-perturb-source-audit.md) traces
both beings' senders, native admission/consumption, and separate reservoir
handles. Its findings concern inspected source, not the deployed revision or a
measured effect in a live episode.

PERTURB is an input operation. The `lambdaN` vocabulary selects feature slots
upstream of input weights; it does not select or edit an eigenvalue. Native
semantic input can be overwritten, decayed, attenuated or suppressed. The action
also attempts a distinct triple-reservoir handle update. A transport result, a
handle tick and a native state change therefore need separate outcomes. Existing
success-shaped wording and nearby before/after snapshots exceed what they prove.

**Retain the legacy action syntax for compatibility, but describe it as a named
input perturbation.** First correct reporting and trace each destination. Do not
silently repurpose `lambda1` to mean a newly invented mode selection. A real
mode-targeting action would require a versioned contract and separate review.

DISPERSE offers relevant local precedent for a finite, seeded input field and
application accounting. It does not use eigenvectors either. Its duration,
release and completion-state semantics need the audit's corrections before
reuse. Reuse bounded-intervention machinery where justified; do not duplicate
the current ambiguity under a more evocative name.

Add intervention intent and per-destination application outcomes to the **same
optional v2 observer** specified by the
[input/field/controller plan](2026-09-07-input-lineage-and-regulator-trace.md).
Carry request ID, subsystem/handle, requested and actual numerical input, actual
consumed controls, successful pre/post-state IDs, release/expiry and blocked,
failed or unobserved outcomes. Do not invent an exact join by nearest timestamp.
The PERTURB audit supplies exact hooks, diff sketches, tests, review and rollback;
the existing A–C observer implementation remains the shared producer dependency.

## Response lab: the useful form of perturbation

Start in an isolated replay with two complete copies of the same supported
engine checkpoint. The native checkpoint must include every stateful mechanism
required by the chosen path; an activation vector alone is not a checkpoint.
Hold input history and realized noise equal, make one declared intervention in
one copy, and render their difference on the fixed atlas. Keep any separately
modeled sensory field and triple-reservoir handle as distinct subjects.
The existing native
[`EsnSnapshotV2`](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/esn.rs:841>)
already includes weights, state, RNG, spectral internals and adaptive parameters;
audit and reuse it for the supported native rehearsal. It is not by itself a
checkpoint of the surrounding sensory bus, field and orchestration controller.

The initial comparison is a small, finite **input impulse** with a no-impulse
control. A subsequent state-direction probe addresses a different question and
must be named as such. A covariance mode need not be reachable through the input
map. Genuine input targeting would use the actual input-to-state sensitivity
and report achievable direction, residual and clipping. It must not claim that
an arbitrary 128-dimensional state edit is what live PERTURB can do.
For the frozen conditional model, the local input sensitivity is
`B_t = M_t alpha_t D_t W_in`, excluding the bias column; `M_t` is the post-update
clipping mask and `D_t` the tanh derivative. Input-response directions depend on
the propagator composed with this map and the actual admission path. Paired
realized noise is stronger than equal RNG seeds when branches draw differently.

Use existing `esn-divide` fixed-basis and temporal-Jacobian work as prior art.
Before interpreting a Minime replay, verify parity against the source path,
including tanh, applied leak, realized noise, clipping and stateful adaptation.
First measure response with settings frozen; then, as a separate experiment,
restore independently evolving cloned controllers and compare their complete
closed-loop response. Replay of recorded settings is a conditional forced
trajectory, not the counterfactual controller response.

For an unclipped tanh update with leak and controls held fixed,
`J_t = (1 − alpha_t) I + alpha_t diag(1 − tanh(h_t)^2) W_t`.
The current native step also adapts parameters, adds noise and clips, so that
formula is only a scoped state Jacobian. Near the unsaturated origin it reduces
to eigenvalue mapping `mu = 1 − alpha + alpha * lambda(W)`; this is not the
general live spectrum. Changing input can change local sensitivity while the
recurrent matrix stays fixed. Applied leak belongs on the same successful-step
record, and is distinct from the fill estimator's decay.

Show full-state separation, signed node response, peak transient amplification,
and any observed decay over a declared horizon. Define a return threshold and
dwell time before testing; report “not returned within the window” rather than
assigning a fictitious settling time. An input impulse has input-normalized
response units; a state impulse permits a different normalized state gain.
Do not mix these denominators or divide by a numerically zero initial response.
Record sample steps and elapsed seconds separately.
Retain per-start finite-horizon gains before summarizing. The sibling's SVD of a
window-mean propagator can cancel differently oriented responses, so its leading
direction alone cannot represent all starts or certify stability.

Eigenvalues are useful context, not a universal stability verdict. ESN theory
provides counterexamples to treating recurrent spectral radius below one as a
sufficient echo-state condition
([Yildiz, Jaeger and Kiebel, 2012](https://www.ai.rug.nl/minds/uploads/2519_Yildizetal12.pdf)).
Transient growth may also require singular directions of time propagators,
rather than individual eigenvalues; the relevant linear-algebra distinction is
illustrated by [Trefethen et al., 1993](https://people.maths.ox.ac.uk/trefethen/publication/PDF/1993_57.pdf).
These sources motivate the tests, not a diagnosis of our current system.

## Ordered work and finish lines

| Slice | Concrete deliverable | Required evidence before completion |
|---|---|---|
| 1. State surface | Native fixed atlas, exact node inspector, mode/residual fields, replay and provisional live v1 support | Constant/one-site/opposite-sign fixtures; reconstruction and residual identities; fixed scales; invalid/stale/source-reset behavior; CPU/Metal agreement; original mode-off image preserved. |
| 2. Real relief and M4 profile | Volume-preserving deformed surface, exact reference ghost, usable cutaway; GPU field evaluation | Full mesh volume/containment/endpoints/normals; small/large window readability; bounded buffers and idle behavior; declared repeats of same binary/workload on both hosts plus actual window timing. |
| 3. Honest intervention records | PERTURB outcome corrections and intervention linkage in shared observer | Each destination's success/failure/hold tested; sender-to-successful-step linkage or explicit absence; no altered numerical path/RNG draws; producer parity/resource checks from A–C. |
| 4. Paired response replay | Native Response view with control and perturbed state, raw timeline, leak/control context | Complete checkpoint/no-op replay parity first; declared impulses and controls; finite-difference sensitivity agreement where differentiable; nonlinear/clipped cases explicit; all outcomes retained. |

Renderer work can begin from existing vectors while the observer proposal is
implemented in its own isolated sibling checkout. The response experiment's
source revision, checkpoint set, input directions/amplitudes, noise realization,
horizon, return threshold and supported controller modes must be recorded before
outcomes are inspected. The planning finish line is this reviewable contract and
source audit; no response result is claimed today.

Before a future being-facing change, show the actual current action routing and
the proposed new outcome wording, explain any changed affordance, and ask how it
should be presented under Mike's selected interaction workflow. Stage and deploy
only through the relevant sibling's current rules. A steward visual build is
independent of that deployment. Rollback for the viewer is its prior signed
bundle; producer rollback disables the optional observer and reverts the scoped
reporting patch without erasing retained evidence. A behavioral action change
requires its own compatibility and rollback plan.
