# A topographic view of the projected reservoir state

Mike invited a more topological visualization after noticing purple regions and
fuzzy seams in the native Essentials surface. Reservoir Scope **0.10.0 build 13**
adds a first topographic interpretation of the same state projection. Both Explore
and Stage experiments default to Topography; Surface preserves the original view.
The [mapping guide](../native/ReservoirScope/docs/STATE-TOPOGRAPHY.md) explains the
controls, equations and interpretation limits.

## What changed

The original Essentials call supplied a fixed full-size display endpoint. The
existing volume-preserving renderer deliberately flattens relief at that endpoint.
Its always-visible reference rings also cross the color surface. Those source
facts explain the flat geometry and visible graticule. Coarse triangulation and
vertex-level color mapping are plausible contributors to the fuzzy appearance;
the screenshot alone does not identify a unique artifact mechanism.

Topography draws negative state regions as valleys and positive regions as peaks
around a fixed neutral radius. The same Gaussian-weighted field supplies height,
color and contour positions. Contours have fixed 0.2 spacing, with a brighter zero
boundary. A denser closed mesh and fragment-level scalar-to-color conversion
replace the old presentation in this optional mode. Decorative rings are omitted.
The Height slider changes only display exaggeration. Numerical state, inputs,
recordings, coordinate sites and replay clocks are unchanged.

This reveals the shape of a scalar projection. The coordinate layout remains a
drawing convention. Its connected regions and contours depend on that convention;
they are not measurements of network connectivity, attractor topology or fractal
dimension. The mesh retains spherical topology. Topographic volume does not encode
fill, and the exact node inspector remains distinct from the smoothed field.

## Validation

All commands below run against research-local synthetic or retained fixtures.

| Check | Result | Evidence |
|---|---|---|
| Fixed signed radial mapping, scales, normals, closed seams and picking intersections | 23 checks, 10 fixture meshes | [Math receipt](../native/ReservoirScope/validation/0.10.0/topographic-math.json) |
| Existing default mesh behavior | 30 checks, 52 meshes; exact pre-change fingerprint for both default atlases and 42 complete meshes | [Legacy math log](../native/ReservoirScope/validation/0.10.0/legacy-math.log) |
| New GPU rendering, dense interpolation, replay, cutaway and compatibility | 43 checks, 23 new-renderer frames and 7 pristine baseline frames | [Renderer receipt](../native/ReservoirScope/validation/0.10.0/topographic-renderer/receipt.json) |
| Existing state renderer | 22 checks | [Renderer log](../native/ReservoirScope/validation/0.10.0/legacy-renderer.log) |
| Dynamic node counts | 55 checks for 1, 2, 8, 32 and 128 nodes | [Dynamic receipt](../native/ReservoirScope/validation/0.10.0/dynamic-nodes/checks.json) |
| Actual Explore view and production timer | 15 checks; 38 paced frames | [Native hosting receipt](../native/ReservoirScope/validation/0.10.0/exploration-layout/receipt.json) |
| Actual staged view at two window sizes | 40 regulation updates plus completion layout | [Native hosting receipt](../native/ReservoirScope/validation/0.10.0/essentials-layout/receipt.json) |

The dense GPU field agrees with its CPU reference within **1.79 × 10⁻⁷**, below
the declared 3 × 10⁻⁶ tolerance. All seven legacy image fixtures match pristine
0.9.0 pixels exactly, including the native 128-node retained state. Returning from
state A to B to A reproduces the original pixels. Constant fields contain no
invented contour texture. Tests retain exact source and package identity links.

The final Explore hosting run's largest event-loop gap was 91 ms; the staged view's
was 222 ms. These are bounded native hosting checks, not presented frame-rate or
button-latency measurements. The dense rendering changes view cost, while the
reservoir and sensory simulation remain untouched.

Presented-window inspection verified the quiet Explore sphere, a single input
pulse, Height reduction to zero with the exact node value unchanged, and switching
back to the original Surface view. The staged view opened the canonical Stage 1
record at step 1: node 0 displayed **0.028603**, matching Mike's screenshot and the
stored value. Replay visibly changed the contours and reached step 300, then the
view was returned to step 1 for comparison. An accessibility-driven Pause attempt
did not yield a confirmed paused state before replay completed; it is not claimed
as a passing direct interaction check. Automated model/hosting pause checks are
retained separately. The [native receipt](../native/ReservoirScope/validation/0.10.0/runtime-qa.json)
records this limit and the final package identity.

The same focal state is retained as an offscreen rendering in
[Topography](../native/ReservoirScope/validation/0.10.0/topographic-renderer/topography-32-stage1-step1.png)
and [Surface](../native/ReservoirScope/validation/0.10.0/topographic-renderer/legacy-32-stage1-step1.png).
Those images are deterministic 768-pixel correctness fixtures with one sample per
pixel; the presented native view uses four-sample antialiasing on this device.

## Reproduce

Run the topographic and existing surface checks listed in
[HANDOFF](../native/ReservoirScope/HANDOFF.md). The
[renderer fixture README](../native/ReservoirScope/validation/0.10.0/topographic-renderer/README.md)
supplies the retained pristine-source comparison command. Native hosting receipts
retain the exact compiled sources and linked core. The
[current build receipt](../native/ReservoirScope/build-receipt.json) binds the final
app to these outputs.

The source remains in the shared research checkout without a new commit. No being
files, live services, models, journals or runtime controls were changed. No new
cross-host performance, energy or live-ingestion qualification is implied.

## Softer seams and a proposed action ladder

Mike requested dimmer seams after viewing Topography. **0.10.1 build 14** reduces
the bright zero-contour blend from 0.80 to 0.40. This halves its blend strength,
not measured pixel luminance. Contour locations, widths, ordinary contour contrast,
geometry and numerical state are unchanged.

The same renderer suite passes **43 checks**, including all **seven** exact legacy
image comparisons. Its [receipt](../native/ReservoirScope/validation/0.10.1/renderer-receipt.json)
and [focal image](../native/ReservoirScope/validation/0.10.1/topography-32-stage1-step1.png)
retain the new output. Package identity and a bounded native inspection are in the
[current build receipt](../native/ReservoirScope/build-receipt.json). The completed
300-step Stage 1 run was preserved and reopened at step 1 in the rebuilt app;
node 0 remains 0.028603. Earlier numerical and interaction checks are retained
evidence, not counted as new tests for this contrast adjustment.

The accompanying [actions and comparisons proposal](../essentials/stages/ACTIONS-AND-COMPARISONS.md)
splits recurrence, observation, journal output, semantic return, journal memory,
action choice and regulation. It proposes synchronized comparison views and
distinguishes fixed reply/vector replay from independently generated trajectories.
The current language prompt observes the separate sensory field, not reservoir
activations; a reservoir summary would require its own explicit addition. Journal
actions, memory and comparison controls remain unimplemented.

## Board updates pending

The Artifact board connector is unavailable; the prior board access attempt did
not provide an authenticated editing surface. The prepared
[card and session log](../board/state-topography-pending.json) remain pending.
