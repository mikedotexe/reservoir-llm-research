# Native state surface and direct-shaping rehearsal

September 7, 2026 (Pacific). S-002 remains ongoing. The research-local viewer
iteration is complete: **Reservoir Scope 0.5.0, build 7**, adds State surface and
Response lab. The [build receipt](../native/ReservoirScope/build-receipt.json)
and [independent artifact identity](../research/outputs/2026-09-07-state-surface/artifact-identity.json)
identify the verified executable, fifteen matching Swift sources and five matching
resources. Strict signature verification passed. This build does not implement
the proposed producer observer or a live action for either being.

## What is now visible

**State surface** carries the actual 128 activation values from the retained
1,024-row native capture, or the vector from an accepted live v1 recorder
observation. The fixed Fibonacci index map is a drawing convention; nearby sites
do not assert recurrent connectivity. Exact site markers and the coordinate
inspector expose the values beneath the smooth field. Signed activation,
magnitude, deviation from the captured mean, selected covariance-mode
reconstruction and omitted residual use fixed scales. The captured basis stays
fixed, and live compatibility remains provisional because v1 lacks a node-layout
and weight-instance identity.

Metal evaluates the spatial color field. The CPU constructs bounded radial relief
when the accepted field or display parameters change, checks the complete closed
triangle volume, then supplies immutable shared GPU buffers. The deformation
preserves the declared volume, reduces near empty/full, and falls back explicitly
if constraints cannot be met. The smooth reference ghost remains separate from
the relief. A lobe crossing a reference line is not a regulator event. Cut faces
carry no inferred activation field, and picking rejects the opaque cap.

The retained vectors have no paired fill or individual timestamps. Their default
**68% preview size** is expressly unmeasured. Live state and fill come from the
same accepted recorder frame; separate health snapshots are not joined to old
vectors. Raw state playback uses row order, with no interpolated states. The
existing 0.8-second easing remains a presentation effect in Fill and Reference
Zones. It is never used to measure response or recovery.

**Response lab** uses a distinct, pinned **esn-divide simulated parent** example.
It provides control, perturbed state and signed delta surfaces; full-state
separation; the declared return threshold; exact coordinate inspection; and raw
boundaries 0–64. Boundary zero already contains the displacement. Its 68% preview
size and three boundaries per playback second are drawing choices, not observed
fill or reservoir time. Both the sidebar and render name the simulation. The
view imports a completed paired comparison; it does not execute an intervention.

See [the mapping guide](../native/ReservoirScope/docs/STATE-SURFACE.md) and
[animation provenance](../native/ReservoirScope/docs/ANIMATION-DATA.md) for the
formulas, source identities and controls.

## Correctness and native inspection

All **172 native checks** passed on final sources; the complete logs and exit
codes are retained in [checks](../research/outputs/2026-09-07-state-surface/checks/results.json):
42 existing evidence/source/reference/playback checks, 17 fill-transition checks,
17 fill-renderer checks, 30 surface-math checks, 19 surface-data checks, 22
surface-renderer checks and 25 response-data checks.

The surface checks cover 52 synthetic closed meshes, with maximum relative
volume error **4.0197405571217625e−8**. All 1,024 retained vectors reproduce the
captured PCA scores and distances within the declared tolerance (maximum score
error **4.440892098500626e−16**, distance error **6.661338147750939e−16**). Eleven
GPU field commands and six offscreen correctness frames check field agreement,
determinism, relief, cutaway, picking, invalid-input clearing and idle behavior.
Maximum GPU/CPU field disagreement was **1.7881393432617188e−7** activation units,
below the preregistered **3e−6** tolerance. These are implementation checks, not
evidence that the map is lossless or useful to either being.

The final signed build opened on M1 Max. Native UI inspection confirmed both
new views, simulation-specific sidebar evidence, fixed scale switching, exact
coordinate readouts and the response slider. Boundary one displayed full-state
separation **0.000242546** and coordinate-zero difference **+0.000223125**.
State surface scrubbing advanced raw node values; full and cutaway renders were
visually inspected. Playback is stopped and the full State surface is left ready
for exploration. Earlier implementation playback was also observed in use, but
these interactions are not a measured latency or usability study. No final-build
live-network ingestion or presented-window timing experiment was run.

## Rendering measurements on both Macs

The [protocol](../native/ReservoirScope/docs/STATE-SURFACE-PROFILING.md) specified
three consecutive retained runs on each host before timing. The final build ran
on local **M1 Max** first, then **M4 Pro Mac mini (`volya`)**, through an isolated
temporary copy of the same app and staged sources. All six completed reports
passed [independent comparison](../research/outputs/2026-09-07-state-surface/profiles/comparison.md):
**540 measured frames**, plus 144 warmups, across signed color, signed relief and
relief with cutaway. Each case uses 1280 × 800 pixels, 4× MSAA and fixed 68%
preview volume. All raw frame timings and artifact hashes are retained.

For the full signed-relief case, the three run medians were:

| Host | CPU update, ms | GPU command, ms | Serial wall, ms |
|---|---|---|---|
| M1 Max | 0.504, 0.458, 0.450 | 0.144, 0.124, 0.138 | 1.538, 1.083, 1.115 |
| M4 Pro | 0.289, 0.272, 0.280 | 1.897, 1.907, 1.882 | 2.352, 2.448, 2.341 |

CPU preparation was lower on M4 Pro in these runs; its completed GPU commands
took longer in this case. Other scenarios also varied across runs. Background
activity was uncontrolled and host order was fixed, not randomized, so these observations do not diagnose
the cause or establish a general chip ranking. Peak sampled Metal allocation was
**38.062 MiB** on M1 Max and **38.203 MiB** on M4 Pro. All before/after thermal
snapshots were nominal, and low-power mode was off. The complete comparison
retains each run's median and p95 rather than selecting a fastest run.

No window is presented by this workload. These are serial offscreen durations,
not display FPS, input latency, live reader cost, energy, memory bandwidth or
Neural Engine performance. The production view and the profiler share the
renderer; the profiler does not load the Response fixture. Its four workload
resource hashes are complemented by the final receipt's five bundle-resource
hashes.

A prior six-run **build 6** set is preserved separately in
[the pre-review archive](../research/outputs/2026-09-07-state-surface/build6-before-ui-review/reason.json).
Native visual review then found unrelated Minime sidebar evidence in Response
and a wrapped picker label. Build 7 corrects those UI labels/layout only. All
completed build 6 runs remain intact; a complete new protocol sequence measured
build 7. The two sets are not pooled or relabeled. The historical response
consumer receipt also retains its pre-review source identity.

## Direct shaping: what the rehearsal establishes

Mike's request made a separate direct-state action worth specifying. The
[STATE_NUDGE proposal](../proposals/2026-09-07-direct-reservoir-shaping.md) records
the precise source distinction: esn-divide's injection edits a **copied
simulation state**; current PERTURB selects input features; Astrid's SHAPE adjusts
codec weights; and the inspected Minime rehearsal records a ledger event without
performing the numerical replay. None establishes an existing native direct-state
action shared by both beings.

The [preregistered experiment](../research/outputs/2026-09-07-direct-shaping/protocol.json)
used the retained simulated parent with 128 state coordinates and 66 input
features. It tested **54 signed one-shot state displacements**, three predetermined
starts and 64 follow-up boundaries. The copies received identical recorded input,
leak, bridge drive and transition residual. Three no-op controls were bit-identical;
the unperturbed replay matched retained reference states within **1.82e−7**.
An independent run from retained input copies reproduced all **57 trajectory
arrays exactly** ([receipt](../research/outputs/2026-09-07-direct-shaping/retained-replay-check.json)).

All 54 comparisons fell below 10% of their initial full-state separation for at
least eight consecutive boundaries, starting at boundary two or three. No
transient growth above the initial displacement was observed beyond floating
point roundoff. This is a scoped result for that conditional fixture. Clipping
occurred, and all **nine derivative comparisons were excluded** by the declared
rule. There is no successful derivative validation, native checkpoint parity,
independently evolving controller counterfactual, live operating envelope or
behavioral finding here. The [complete results](../research/outputs/2026-09-07-direct-shaping/results.json)
retain every tested outcome.

## The next implementation boundary

STATE_NUDGE is proposed as one bounded signed displacement along a registered
state direction, applied once at a successful native update boundary. Its receipt
must distinguish requested, accepted and actual displacement, with exact before/
after state and consumed-control references. The default policy rejects inadequate
headroom; optional uniform attenuation records its factor. Stopping later actions
does not undo a changed history. A shared-coupling authority adapter is presently
missing; it must not be disguised as either being's self-owned control.

The next substantive step is a native checkpoint rehearsal with no-op parity,
followed by the same paired response experiment. The existing shared observer
and PERTURB destination outcomes remain producer prerequisites for live causal
receipts. The proposal contains exact hooks, a diff sketch, tests, being-facing
review and rollback for the owning repository workflow. Native-window profiling
also remains open. No sibling source, live workspace, service or being prompt
was changed during this research-local iteration.


## Board publication

The parent viewer card is **done** for this bounded iteration, the STATE_NUDGE
contract is **done** for proposal preparation, and the new simulated-fixture
finding is **verified** only within the declared fixture. All three records and
the September 7 session log were saved and read back through the authenticated
board UI. [The publication receipt](../board/reservoir-observatory.json) retains
exact titles and coordination tags; the UI did not expose database IDs. Prior
planning and viewer receipts remain archived separately.
