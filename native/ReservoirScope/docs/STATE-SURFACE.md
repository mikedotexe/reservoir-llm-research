# Reading the state surface

Reservoir Scope 0.5 adds a **State surface** view: a fixed map of Minime's 128
native reservoir coordinates, rendered as color and real surface relief. Select
a patch to inspect its underlying coordinate, or use the grid and node selector
to reach values on the far side of the sphere. Drag to orbit, scroll to zoom,
and press Space or double-click to reset the camera.

The companion [Response lab](#response-lab-watch-a-declared-state-displacement)
uses the same GPU drawing map for a separate paired simulation. Its evidence
and controls are described below, independently of the Minime observation view.

The surface brings two measurements into one object. Its **volume** represents
the reported sensory-field fill when a co-recorded observation is available.
Its **color and shape** represent the selected field of native reservoir values.
Fill is not the fraction of these 128 coordinates that are active. The smooth
dashed circles preserve the volume reference independently of local bumps.

The native viewer is a steward instrument. It reads evidence and renders it;
opening this view does not send an action or an image to either being.

## Start with the source

| Source | What the surface uses | What its size means |
|---|---|---|
| **Recorded** | The original 1,024 retained rows, each containing 128 signed activation values | **Preview volume**, initially 68%. This capture has no paired fill; the preview slider changes display size only. |
| **Live state & fill** | The latest accepted activation frame and its co-recorded fill and stage | That frame's reported fill. The source's recorder time is not an authenticated successful-step time. |
| **Live fill & control** | No state surface: this feed has no node vectors | The viewer asks for the state source rather than attaching unrelated vectors to a health reading. |

**Follow state snapshots** selects the activation source. **Choose file…** can
select an existing `esn_activation_trace_v1.json`. The live reader preserves
validated coordinates from that file; it does not reconstruct them from the
three-dimensional trajectory. It accepts at most 180 frames of 128 coordinates
under a 2 MiB file limit and waits two seconds between completed reads.

Recorded Play advances at a chosen presentation pace of **20 rows per second**.
This is ordinal replay, not a recovered sampling rate. Each row remains an
actual saved observation. Pausing and scrubbing select its stored order without
inventing a row timestamp. The separate historical fill replay is never joined
to these rows. The capture timestamp, `2026-09-07T05:11:52.328Z`, describes the
file observation, not every activation row.

Live v1 has no authenticated node-layout, boot/session or successful-step
identity, and no applied leak or exact controller link. Its index map is
therefore provisional. Reference-based live fields visibly retain that
qualification: equal vector length alone cannot prove that a coordinate still
belongs to the same node as in the old fit. A stale or failed source can leave
the last accepted observation visible, clearly labeled as retained. It does
not generate continuing ripples.

See [Animation data and provenance](ANIMATION-DATA.md) for the existing fill
estimator, historical pairing, recorder clocks and live-reader limits.

## Read color before interpreting shape

The selector offers five numerical fields. The scale stays fixed across time;
small observations are not enlarged to fill the color range.

| Field | Coordinate value shown | Fixed display scale |
|---|---|---|
| **Signed activation** | The saved or observed value `xᵢ` | −1 to +1 |
| **Activation magnitude** | `abs(xᵢ)` | 0 to 1 |
| **Change from reference** | `xᵢ − μᵢ`, using the frozen capture's mean | −2 to +2 |
| **Selected mode reconstruction** | The part of the reference-centered state reconstructed by the selected captured components | −2 to +2 |
| **Omitted component** | The reference-centered state remaining after that reconstruction | −2 to +2 |

Purple and turquoise indicate opposite numerical signs. They are not health,
comfort, pressure or temperature ratings. Magnitude uses a sequential dark-to-
turquoise scale. Values beyond the displayed range are counted in the inspector;
their numerical values remain available even when the color has reached its
endpoint. Inspector numbers are formatted to four decimal places.

The **exact node grid** shows each coordinate's unblended selected-field value.
Its markers on the sphere represent the same values; the selected marker is
gold to distinguish selection. Between markers, the sphere blends the values
through a fixed smooth drawing map. Opposite signs can cancel in that blend.
A neutral patch therefore does not establish inactive underlying nodes; the
magnitude view and node inspector expose the difference.

Lighting makes actual relief easier to see, while changing perceived color.
Enable **Flat color lighting** when comparing with the legend or grid. The
native legend/grid use linear sRGB colors to match the Metal color mapping into
its sRGB display target. Surface colors still blend across triangles, and the
unblended numeric inspector remains the source for precise reading.

## What the map and modes mean

Every coordinate has a permanent, approximately uniform site on a sphere. The
map version is `index-fibonacci-128-v1`. The interface labels nodes 1–128; source
array indexes are 0–127 in the same order. Nearby patches are nearby in this
drawing convention, not necessarily connected in the recurrent weight matrix.
The map does not move or refit to make a frame look more organized.

At each mesh vertex, fixed nonnegative interpolation weights sum to one. A
spherical Gaussian blends all 128 values, preserving constant fields and
bounding each blend by its contributing values. A site marker uses the raw
coordinate value, independently of that blend, and is positioned at its ray's
intersection with the actual rendered triangle, with a small visibility offset.
The [mapping implementation](../Sources/ReservoirScope/StateSurface.swift)
contains the atlas and its exact kernel.

**PC1**, **PC2**, **PC3**, and **All three captured modes** refer to the frozen
capture's covariance components. They reconstruct distributed coordinate
patterns. For reference-centered state `z = x − μ`, a component's score is
`aₖ = dot(vₖ, z)`, its contribution is `aₖ vₖ`, and the omitted component is
`z − Σ aₖ vₖ` over the selected modes. Changing a component's sign also changes
its score's sign, leaving its reconstructed pattern unchanged.

All three components retain **14.3524%** of the reference capture's centered
temporal variance. The remaining **85.6476%** is outside that three-component
reconstruction. These are properties of the frozen fit, not a live variance
estimate. The inspector separately reports the selected reconstruction's share
of the current state's squared distance from the reference mean. A covariance
mode is not a recurrent eigenvalue, a force on one node, or a stability verdict.
The [retained-input analysis](../../../analyses/2026-09-06-reservoir-3d-prior-art.md)
records the fit and its interpretation.

## Relief preserves volume

**Surface relief** displaces the mesh itself. The CPU forms a positive radial
candidate from the selected field and fixed scale, then measures the complete,
closed triangle mesh's signed volume. It uniformly rescales that candidate to
the undeformed mesh's volume at the selected fill fraction. If a point would
leave the container, it reduces relief and checks again. Invalid candidates
fall back to the undeformed sphere.

This preserves the actual triangle mesh's fill-volume ratio. A triangulated
sphere remains an approximation to an ideal sphere; the two volumes are not
silently treated as identical. The underlying smooth reference retains the
existing cube-root relation `r/R = cbrt(fill/100)`.

Requested and applied relief strengths appear together. Relief reduces near
empty and full, and becomes zero at both endpoints. That flattening is a display
constraint, not evidence of a calmer state. At zero volume, inspect the values
in the grid and numeric panel. In recorded mode, a larger preview size can make
the same observation easier to examine without implying a measured fill change.

The dashed volume-reference circles remain visible through the shape as ghost
references. A lobe passing one of them does not mean scalar fill crossed a
regulator threshold. **Reference Zones** retains its existing smooth geometry
and annotations; surface relief does not move those thresholds.

**Cutaway** renders part of the same checked full mesh. Its dark planar cap is
an unmeasured section, not a picture of hidden state inside the sphere. Clicking
that cap does not select a coordinate behind it. The complete mesh, rather than
the visible half alone, supplies the volume check.

## Motion and the native GPU

This view uses **observed samples without temporal easing**. Shape and color
change together when an accepted observation, field, or display setting changes.
Orbiting changes only the camera. The existing 0.8-second smoothing option in
Fill sphere and Reference Zones does not animate this state surface. Neither a
display transition nor a static-looking patch measures reservoir recovery.

Swift prepares the selected field and validates the displaced mesh on the CPU.
Metal evaluates the fixed weighted field and lighting while rendering. The
atlas weights persist in GPU-accessible shared memory; observation and geometry
buffers are immutable generations retained while their GPU commands use them.
This uses the GPU without suggesting that shared memory eliminates copying or
synchronization. No Neural Engine model is involved.

The Metal view draws on demand for evidence, setting, camera and window changes;
it does not run a continuous time-driven surface animation. Its implementation
is in [StateSurfaceScene.swift](../Sources/ReservoirScope/StateSurfaceScene.swift),
with controls and labels in
[StateSurfaceExperience.swift](../Sources/ReservoirScope/StateSurfaceExperience.swift).
Performance results and the final packaged build have separate receipts; the
existence of this implementation is not itself a frame-rate measurement.

## Response lab: watch a declared state displacement

**Response lab** reuses the GPU surface for a separate, clearly labeled
**esn-divide simulation**. It contains one paired example from the retained
[direct-shaping experiment](../../../proposals/2026-09-07-direct-reservoir-shaping.md).
These are simulated parent states, not the Minime capture used above and not
live evidence from either being. The sidebar observation-source picker is disabled in this tab. The Response
source selector distinguishes native action receipts from this bundled experiment.

The control copy starts unchanged. A second copy receives a single **+0.001
displacement in coordinate 0** at its initial state boundary. Both then receive
identical recorded inputs, applied leak, bridge drive and the stored transition
residual. That residual is a retained correction to the simulated transition;
it is not the omitted PCA component. No adaptive controller is cloned here.
This operation changes copied state directly, while the existing live PERTURB
mechanism routes an input. The experiment does not implement the proposed live
state action.

The view contains **65 paired boundaries**, numbered 0–64. Boundary 0 already
includes the displacement; it is not a pre-action frame. The inspector also
shows the source simulation's boundary index, 200–264 for this example. Select:

| Surface | Values | Fixed color scale |
|---|---|---|
| **Delta** | Perturbed minus control, coordinate by coordinate | −0.001 to +0.001, tied to the declared displacement |
| **Control** | The unchanged-start copy's state | −1 to +1 |
| **Perturbed** | The displaced-start copy's state | −1 to +1 |

The coordinate inspector shows both states and their exact difference, while
the plot measures the distance between their complete 128-coordinate vectors.
Response coordinates are labeled **0–127** to match the experiment's original
index order. Reusing the sphere's sites is a drawing convention; it does not
establish shared node identity with Minime. No Minime PCA basis is applied.

The sphere has a fixed **68% preview volume**. This example has no fill
measurement or measured elapsed seconds. **Play slowly** advances at three
boundaries per playback second for inspection; the slider selects raw
boundaries without easing. Playback duration is not reservoir recovery time.

In this displayed pair, the largest full-state separation equals the initial
displacement. Separation falls below **10% of that initial amount beginning at
boundary 2**, and remains there for the required eight consecutive boundaries.
The threshold and dwell were declared in the
[experiment protocol](../../../research/outputs/2026-09-07-direct-shaping/protocol.json).
They describe this conditional comparison. They do not certify stability,
safe live amplitudes, persistent influence or either being's experience.
Clipping occurs in the retained experiment, and neither native replay parity
nor the protocol's unclipped derivative validation is established.

The [bundled response evidence](../Sources/ReservoirScope/Resources/state-response.json)
retains the paired vectors and their identity. Its consumer verifies the
resource hash, numerical differences, full-state distances, boundary order and
return summary, and rejects invented fill, timing or reference-basis claims.
The [native consumer receipt](../../../research/outputs/2026-09-07-direct-shaping/native-response-receipt.json)
records 25 data and failure-fixture checks. The complete experiment's trajectories
also passed a separate
[retained-input reproduction](../../../research/outputs/2026-09-07-direct-shaping/retained-replay-check.json).
These checks have narrower scopes than final app packaging, visual review or
GPU performance profiling.

## Native action receipts: the exact application boundary

Version 0.6 adds **Native action receipts** beside the separate esn-divide source.
The native source accepts `research.native_action_response.v1`, initially restricted
to an **isolated Minime native ESN rehearsal**. It does not accept a live-being label
under that schema. A producer artifact can be bundled as
`Resources/native-action-response.json`; otherwise **Open receipt file…** imports
one explicitly. The viewer does not submit an action or write to its source. The producer changes
are staged in an isolated implementation checkout; this is not an enabled action
in either being's running system.

The [bundled native example](../../../research/outputs/2026-09-07-native-state-actions/native-action-response.json)
contains eight actual applied pulse receipts, plus admission and completion events.
Its source is the staged native producer, not the former esn-divide simulation or
a hand-authored animation. The [independent producer verification](../../../research/outputs/2026-09-07-native-state-actions/final/candidate-run/verification.json)
and [37 consumer checks](../validation/0.6.0/native-action-consumer.log) retain the
separate source-execution and viewer-validation evidence. The imported file hash
is `15441269152bb282e2456d4d08fddae398879e4b0410cd08f71e80282f09e807`.

Each surface frame is an `applied` or `no_op` engine receipt with all 128 original
Float32 coordinates, a successful native step ID, action and pattern identities,
model and node-layout identities, requested amount, actual attenuation, effective
leak and realized per-coordinate noise. Admission, completed, cancellation,
rejection and failure events remain events; they do not become invented geometry.

| Native surface | Exactly what it shows |
|---|---|
| **Ordinary step** | This same native step's result after its normal update, noise and clipping, immediately before the action. It is not a separately continued no-action trajectory. |
| **Applied result** | The immediate state after this action at that boundary, before the later ordinary geometry work. |
| **Action difference** | `Float32(applied[i] - ordinary[i])` for every original coordinate. This is the applied displacement, not the later response or a counterfactual effect. |

The staged producer drains outstanding GPU work at active gesture boundaries so
its receipt can identify a successfully checked boundary. Ordinary steps retain
the repaired asynchronous path. The measured `boundary_wait_us` is displayed
separately from the supplied rehearsal clock; this waiting cost must not be
presented as a free or fully asynchronous action path. No GPU performance claim
follows from the viewer's receipt playback.

State colors keep the fixed −1…1 scale. The difference scale is symmetric and
fixed to the largest absolute coordinate difference in the **entire accepted
bundle**, with a `1e-9` display floor for an all-zero bundle. It never renormalizes
each pulse. A replacement bundle can establish a new scale, so the legend is part
of the observation. Original Float32 values remain available to nine significant
digits in the coordinate inspector. Full-state L2 and maximum coordinate change
are recomputed from the complete difference; a displayed positive or negative
requested amount remains distinct from the actual headroom-limited application.

The same Metal drawing atlas is reused, with explicit index mapping and no PCA
association. The sphere uses **68% preview volume** because fill is absent from
this contract. Shape is an expressive drawing of observed values with the existing
volume-preserving relief; it is not a physical membrane, eigenmode geometry or a
measured stability boundary.

**Inspect sequence** advances three pulse receipts per playback second, without
easing or interpolating states. The action-size plot uses bars at the original
successful native step IDs. Gaps stay gaps, and no connected recovery curve is
invented. The `observed_at_unix_ms` field in this rehearsal wrapper contains a **supplied
rehearsal clock**, used to test expiry deterministically. It is explicitly labeled
that way; it is neither measured wall time nor measured reservoir elapsed time. Effective leak is the selected value
at that boundary; it does not reconstruct a controller path between receipts.

**Follow receipt file** is opt-in, read-only polling of complete atomic research
bundle replacements. A reader caps each file at 8 MiB and each bundle at 1,024
receipts, then waits two seconds after each read. It validates off the main UI
actor, replaces the complete displayed batch, and never stitches sessions together.
Identical files do not create new observations. Existing overlapping application
receipts and source hashes must remain unchanged within the same native identity;
backward successful steps are rejected. A new native identity replaces the whole
batch. Errors retain the prior bundle with a visible unavailable-source label.
Waiting for a new file does not imply a new native step; no polling or file timestamp
is substituted for the engine's identity. Following a research artifact is not a
connection to the beings' running action systems.

The importer computes a SHA-256 identity for its actual input bytes. Named source
hashes and the pattern hash remain **producer declarations**: the viewer validates
their format and preserves them, but does not independently authenticate the
producer or establish that a source hash produced the supplied vectors. Native
rehearsal verification belongs to the producer's retained experiment and receipt.

The dedicated consumer checks run without opening a live source:

```sh
native/ReservoirScope/check-native-action-response.sh
# Also validate a retained producer artifact when available:
native/ReservoirScope/check-native-action-response.sh path/to/native-action-response.json
```

The synthetic checks cover exact Float32 coordinate differences, UInt64 step IDs
above `2^53`, requested/applied separation, event exclusion, finite bounded states,
all-vector distances, dimensional and byte limits, absent fill/PCA/timing claims,
and atomic replacement continuity. Supplying a real artifact adds an end-to-end
check of that producer output through the same decoder. These checks and a viewer
build do not establish a live operating envelope or a being's use of the action.

## Reproduce the evidence and checks

The [replay manifest](../Sources/ReservoirScope/Resources/state-replay.json)
binds the retained binary to its exact frozen geometry with SHA-256 hashes.
The viewer checks sizes, signed finite coordinate values, row order and the
absence of invented fill/timing joins before publishing the replay. The retained
activation binary contains 524,288 original bytes; it is not a reconstruction
from the three PCA scores.

From the research repository root, verify the package against the retained
research inputs without reading a live source:

```sh
python3 probes/reservoir_state_surface_replay.py --check
native/ReservoirScope/check-state-surface.sh
native/ReservoirScope/check-state-surface-data.sh
native/ReservoirScope/check-state-surface-renderer.sh
native/ReservoirScope/check-state-response.sh
```

The dedicated checks have separate scopes:

| Suite | Coverage |
|---|---|
| 30 mapping checks | Fixed atlas, fields, modal/residual identities, exact markers, positive radii, containment, normals and volume preservation across 52 synthetic meshes |
| 19 data checks | Original retained rows, package and geometry identity, malformed/mismatched evidence and live-coordinate preservation |
| 22 renderer checks | CPU/Metal field agreement for 11 fixtures, deterministic images, actual relief, cutaway/picking and clearing across six offscreen frames |
| 25 response-data checks | The separate simulated pair's byte identity, coordinate differences, full-state distances, boundary/return summaries and rejection of fabricated provenance |

The mapping sweep's maximum relative volume error was approximately
`4.02 × 10⁻⁸`; its declared acceptance bound is `2 × 10⁻⁶`. These are synthetic
geometry checks, not observations of reservoir stability. Renderer correctness
checks use bounded offscreen commands and establish neither presented frame
rate nor a comparison between Macs. Consult the [build receipt](../build-receipt.json)
for the packaged executable's validation and the
[profiling guide](PROFILING.md) for the separate measurement scope.
