# A measured state surface for Reservoir Scope

September 7, 2026, Pacific. Design audit for [S-002](../research/studies/S-002-reservoir-observatory.md), following Mike's proposed surface carrying internal state and modes. This note recommends a native viewer implementation; it does not report a new experiment or a change to either being. Source siblings were read only. The inspected `esn-divide` working tree remains based on `2cb226ef48ac5a40935ead9e4e0230c92d884f5c`, with modified and untracked files; its temporal-analysis files are among the untracked sources. These are working-tree observations, not claims about that commit alone.

## Decision

Build an optional **State surface** on the existing fill sphere. Preserve the measured volume encoding and put a fixed, inspectable map of actual reservoir coordinates on that surface. The visual plan includes true volume-preserving displacement: first establish color and lighting relief as the testable mapping foundation, then deliver actual shape under the mesh-volume checks below. Keep the Reference Zones view geometrically exact so its regulator annotations retain their meaning.

The surface can be visually rich without pretending to be liquid mechanics. Changing patches will mean changing values at named native coordinate indexes. A modal view will show which part of that pattern a selected frozen basis reconstructs. Neither motion nor smoothness will be labeled calmness, stability, pressure, or an unmeasured response to an input.

There are three independent quantities in this proposal:

| Channel | Meaning |
|---|---|
| Enclosed fill volume | The co-recorded sensory EigenFill estimate, using the app's existing cube-root radius mapping. |
| Surface field | A declared map of the native ESN state, its deviation from a frozen reference, or a mode reconstruction. |
| Regulator annotations | Recorded stage/control information and configured references, with their existing source and timing qualifications. |

The data can share one object while retaining separate definitions. Fill is not computed from the 128 activation values: [the activation-source audit](2026-09-06-reservoir-live-state-readiness.md#existing-v1-schema-and-what-its-clocks-mean) traces it to the sensory-field estimator.

## What the current app actually provides

The renderer is already native Metal. `ReservoirScene.swift` constructs a concentric fill sphere with `radius = cbrt(fill / 100)`, renders a planar cut face, and draws the reference arcs independently. This is not a horizontal pool or a physical meniscus. Its Metal vertex function applies camera transforms and simple lighting to CPU-produced vertices. Fixed reference buffers are now reused during fill easing. See [fill construction](../native/ReservoirScope/Sources/ReservoirScope/ReservoirScene.swift:439), [shared-buffer submission](../native/ReservoirScope/Sources/ReservoirScope/ReservoirScene.swift:383), and [shader](../native/ReservoirScope/Sources/ReservoirScope/ReservoirScene.swift:765).

The existing live parser already validates the full 128-value vector before projecting it. But [LiveStateSample](../native/ReservoirScope/Sources/ReservoirScope/LiveState.swift:108) publishes derived geometry only; the raw values remain inside the decoder's private trace. A state surface therefore needs an explicit validated activation array in its presentation model. Painting a surface from `geomRel`, `lambda1Rel`, or the three trajectory coordinates would not reveal the unretained nodes.

The bundled [PCA model](../native/ReservoirScope/Sources/ReservoirScope/Evidence.swift:364) includes the frozen mean, all covariance eigenvalues, and three component vectors. The recorded geometry rows contain scores and norms, not all raw activations. A replay surface can use the existing retained raw capacity capture through a new bounded, hashed research resource; the exporter must not invent per-row times or attach the separate morning fill series. Live activation observations already supply fill and state together at recorder time. Their node-layout compatibility with the old PCA fit remains unverified.

The [prior-art analysis](2026-09-06-reservoir-3d-prior-art.md#same-session-extension-actual-reservoir-state-geometry-recovered) reports that this frozen three-component fit retains **14.3524%** of its capture's temporal variance. That is a result of the retained-input probe over **1,024 rows × 128 coordinates**, not a claim about all later observations. A surface showing only that reconstruction must keep omitted variation visible. Per-observation squared-distance retention is a different quantity and is already available in the live consumer.

## A fixed atlas, with no invented anatomical positions

Give each native coordinate index one permanent surface site. For the first implementation use a deterministic, approximately equal-area spherical layout keyed by index, and save its algorithm/version, orientation, and explicit index-to-site table. This is a drawing layout: near neighbors on it are not asserted to be connected, similar, or physically adjacent. Keep it fixed while observing; a layout recomputed from each state would create motion that belongs to the layout algorithm.

Provide two linked representations on the same sphere:

1. Exact-value site markers or cells, selectable to show the coordinate index, raw signed activation, and selected reference-relative value. These are the inspectable observations.
2. A smoothly blended field between the sites, used for color and apparent relief. This is an interpolation of the observations, not an additional state variable.

One concrete field is `s(ω) = Σ w_i(ω) y_i`, with fixed nonnegative weights summing to one at every surface direction `ω`. Local weights can be precomputed from angular distance to the fixed sites. This preserves a constant input field and bounds each blended value by its contributing values. It can cancel positive and negative values, so the exact-value markers and a magnitude mode are essential; a neutral blended patch does not prove inactive nodes. Interpolation need not equal a node's value exactly at its site, which is another reason the marker uses the original value.

Suggested field selector:

| Field | Definition and visible meaning |
|---|---|
| Signed activation | `y_i = x_i`; opposite colors mean opposite numerical signs, not healthy/unhealthy or hot/cold. |
| Activation magnitude | `y_i = abs(x_i)`; a sequential scale answers which coordinates have larger absolute activation. |
| Change from reference | `y_i = x_i − μ_i`; the fit identifier and compatibility warning stay visible. |
| Selected mode reconstruction | The selected frozen components' contribution to reference-centered state. |
| Omitted component | Reference-centered state minus the selected reconstruction. |

Use a fixed declared color scale for comparison across time, with an explicit out-of-range indicator. Do not normalize each frame by its own maximum: that would make a tiny fluctuation appear as strong as a large one. Magnitude and signed deviation require different legends. Node identity across a restart or layout change must not be inferred from a matching dimension alone; without producer identity, the current live mode remains a provisional index map.

This atlas does not claim mathematical topology. The mesh still has the same connectivity as a sphere; bumps change geometry. A future connectivity-based arrangement would be a separate named map requiring the relevant weight matrix, node-order identity, and a stated layout objective. It should be compared with the index layout before assigning meaning to apparent clusters.

## Modes can paint the surface; eigenvalues cannot locate them

For frozen orthonormal component vectors `v_k` and reference-centered state `z = x − μ`, compute:

```
a_k = dot(v_k, z)
q_i = sum over selected k of a_k * v_k[i]
e_i = z_i - q_i
```

Paint `q` on the same node atlas, with a switch to `e` and the full `z`. A selected-mode inspector can separately show its signed loading `v_k[i]`, current score `a_k`, and reference-window covariance eigenvalue. This makes a mode a distributed pattern over coordinates; its eigenvalue is one scalar describing variation along that direction in the fitted window. A whole mode is not a force attached to a particular node.

Changing the sign of both a stored component and its score leaves `q` unchanged. Freeze the basis identity and sign convention; if a future refit is offered, show an explicit reference change. Near-degenerate component directions can rotate within their subspace, so comparing a selected subspace can be more defensible than declaring a newly numbered eigenvector to be the same mode.

This is a state reconstruction. It neither measures a changing recurrent spectrum nor simulates the system's response. The existing covariance eigenvalues have no imaginary parts from which to infer a swirl. Arbitrary sine waves, rotations, and damped oscillators should not be added to this measured mode view.

The sibling offers useful later machinery: [FrozenPcaBasis](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/division_evidence.py:18>) keeps a shared reference; [one_step_state_jacobian](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/temporal_jacobian.py:26>) takes recurrent/input matrices, applied leak, state/input and optional clipping information; [window modes](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/temporal_jacobian.py:454>) are singular directions of a window-mean propagator. These are different objects from covariance principal components. Their operator, horizon, input state and frozen-control scope must accompany any later surface layer. The current live recorder does not export the inputs needed to reconstruct those operators.

## True displacement: preserve volume and separate the references

Color plus lighting relief leaves the silhouette and volume unchanged. It is the smallest first rendering change. If lighting relief is used, label it as apparent relief, keep the quantitative color legend independent of lighting, and offer flat lighting for inspection. Lighting should never silently change the value implied by the legend.

For true relief, an ordinary `r = base + displacement` changes volume even when displacement averages to zero. The continuum volume is `V = (1/3) ∫ r(ω)^3 dΩ`, so a zero-mean radius offset does not suffice. One conceptual encoding is `r(ω) = R [f + β g(ω)]^(1/3)`, where `f = fill/100`, `g` has zero spherical-area mean, and `β` is bounded so the bracket remains between zero and one. This conserves the continuum volume, but a triangle renderer must also check the volume of the mesh it actually draws.

A concrete mesh implementation is safer to specify directly:

1. Use a fixed, closed, consistently oriented triangulated unit sphere. Let its enclosed volume be `V_unit`.
2. Form positive candidate radial displacements from the declared state field.
3. Compute the candidate closed-mesh volume from oriented tetrahedra: `V_candidate = Σ dot(p_a, cross(p_b, p_c)) / 6`.
4. Multiply every candidate position by `cbrt(f * V_unit / V_candidate)`. The resulting mesh has the same volume as the existing unit mesh scaled by `cbrt(f)`.
5. If any radius crosses the outer sphere, or the candidate is invalid, reduce relief amplitude and recompute. A bounded backoff with the undeformed sphere as fallback avoids assuming the constraint is monotonic. Handle zero and full fill explicitly with zero displacement.

The mesh-volume ratio can be exact to numerical tolerance while the triangulated sphere still approximates the ideal sphere. Report and test these separately. A cutaway render uses the corresponding full closed mesh for its volume check; the visible half alone cannot be inserted into the closed-volume formula. Recompute displaced normals from actual geometry.

Relief amplitude must fall near the empty/full endpoints; color can still show the state there. Preserve the smooth measured-fill circle or ghost sphere as a reference. A local bump crossing the drawn 74% radius must never be called a regulator breach: those references classify the scalar fill estimate, not a local node value. The Reference Zones lens should continue to use the exact smooth radius and its existing annotations, with at most a linked color strip for the selected surface sector.

## Native GPU path and animation rules

Upload a fixed unit mesh and fixed interpolation weights once. On each accepted observation, provide a bounded immutable set of node values, optional reconstruction values, and source/reference identifiers. Evaluate the surface field and lighting in Metal. The changing fill radius belongs in a uniform rather than a rebuilt sphere mesh. A first color implementation needs no per-frame eigendecomposition and no Neural Engine model.

For a mutable shared-buffer implementation, protect each in-flight observation buffer until its GPU commands complete. Shared memory does not remove CPU/GPU ordering requirements. Apple's [CPU/GPU synchronization sample](https://developer.apple.com/documentation/metal/synchronizing-cpu-and-gpu-work) uses multiple resource instances and completion tracking for this purpose. Compare this change with the existing immutable-buffer path in the same bounded renderer harness before claiming a speedup.

Apply the existing smoothing contract consistently: either hold observed fields, or offer a clearly labeled transition between accepted observations. The exact node inspector and measured-fill marker update immediately. Do not extrapolate motion, interpolate through source resets, invent a source cadence, or let stale input keep rippling. If both shape and color are eased, their displayed snapshot mixture should be the same and use one clock. This is presentation interpolation, not evidence that the reservoir followed the intervening path. Respect Reduce Motion and the user's explicit app-level choice.

In particular, the current **0.8-second smootherstep** is a chosen display duration. A surface settling in 0.8 seconds says nothing about the reservoir's settling time. A later perturbation-response mode must default to raw measured observation/step times and uninterpolated recorded states, with a visible event marker and source coverage. Optional visual easing belongs to a separately labeled viewing option; response estimates must use the original observations. A dropped or unsampled interval stays a gap. The response mode must not inherit a synthetic ripple, damping constant, or easing-derived recovery curve.

The existing [six-run GPU comparison](2026-09-06-reservoir-native-profiling.md) measured an earlier app without this field. It demonstrates an available native GPU path, not the performance of the proposed surface. Profile the new shader and its real window behavior on M4 Pro after implementation; continue to distinguish serial offscreen command time from displayed frame rate.

## Bounded next implementation and acceptance checks

The next viewer slice should finish when a steward can select one live observation, inspect its coordinate values, see the same values as a surface field, and switch to the frozen reconstruction and omitted component without changing reference identity or fill. Implement color/apparent relief first, using actual validated activations retained in the consumer, followed by the genuine volume-preserving shape slice. Add a replay resource from retained raw evidence for deterministic renderer checks. No producer change is needed for this provisional read-only view; producer identity and successful-step instrumentation remain prerequisites for stronger live dynamical claims.

Those producer needs belong to the existing [input-lineage and regulator-trace implementation plan](../proposals/2026-09-07-input-lineage-and-regulator-trace.md), which explicitly specifies one coherent v2 observer rather than competing recorders. Its manifest supplies boot/session, vector layout, build identity and clock anchors; successful-step records supply previous/new state references, final input, consumed controls and applied leak. Reuse those identities and publication limits for the surface and later response view. This proposal does not create a second telemetry schema or authorize producer implementation here.

Before calling that slice complete, test:

- Constant, one-coordinate, equal-and-opposite, and zero fixtures: exact markers preserve the inputs; blended fields preserve constants; cancellation remains evident in the exact values and magnitude view.
- No per-frame normalization, coordinate reordering, PCA refit, or time-derived animation: identical observations produce identical fields in a fixed camera.
- Reconstruction algebra: a state in the selected span has zero omitted component within tolerance; a state perpendicular to it is retained entirely as residual; simultaneous component/score sign reversal leaves the rendered reconstruction unchanged.
- Provenance failures: incompatible dimensions, non-finite/sanitized input, source changes, clock resets, stale frames, and missing reference identity remain visible rather than borrowing another source's field.
- Renderer correctness: a fixed CPU reference and Metal field agree within declared precision; the new option off reproduces the current image; field colors and selection remain legible at ordinary and magnified sizes, with accessibility settings.
- Once displacement is implemented: actual closed-mesh volume matches the undeformed fill volume at endpoints and intermediate fills; positive radii, outer containment and normals pass; cutaway and full views share the same checked geometry; Reference Zones classifications remain unchanged by relief.
- Measured resource bounds and interaction: idle, incoming observation, transition, orbit and source switch have distinct traces; the app stops drawing after settling; source reads and renderer buffers stay bounded.

These are proposed acceptance checks, not tests run in this design audit. They make a compelling measured surface achievable now while giving later perturbation and sensitivity experiments an honest place to appear.

## Source-search record

The read-only audit inspected the files linked above, the native README, `Evidence.swift`, `LiveState.swift`, `ReservoirScene.swift`, `probes/reservoir_3d_state_geometry.py`, and the prior-art/readiness analyses. It searched the sibling visualization modules for `FrozenPcaBasis`, `eigenvector`, `eigenvalue`, `singular`, `jacobian`, and `frozen`; then read the positive source sections directly. No activation file or live database was read for this note, and no new numerical reservoir finding is asserted. Hold Shelf coordination belongs to the parent S-002 planning session.
