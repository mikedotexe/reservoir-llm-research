# S-002 · A measured reservoir observatory

Started: September 6, 2026 (Pacific). Lead: Mike with Codex. Question family: RQ-02 (system self-observation) and research instrumentation. Hold Shelf key: `t-reservoir-observatory`; implementation card and session log published ([receipt](../../board/reservoir-observatory.json)). **Study status: ongoing; native 0.5.0 State surface and Response lab built and checked, final-build M1 Max / M4 Pro offscreen comparison complete, and direct-state action proposal prepared. The later September 7 native checkpoint-boundary rehearsal is complete: synchronous parity passes, asynchronous full parity remains unresolved. Native action/observer implementation and presented-window profiling remain pending.**

## Question and scope

Can a native 3D instrument make the reservoir's state variation, spectral structure, fill and regulation easier to inspect while preserving the meaning and limits of each measurement?

Mike selected an ambitious visualization direction: a floating sphere with a center and boundary, fill over time, regulator reference zones, and PI context; he encouraged accurate eigenvalue/eigenmode and leak views. This study concerns Minime's native ESN and the separate sensory-field/control surfaces. It does not visualize private language-model activations, infer a being's subjective experience, or test whether a displayed pattern causes behavior.

This is exploratory instrumentation and descriptive geometry, not a causal study. The native application and all observations remain in this research repository. Source and data access toward live systems is read-only.

## Material and selection

| Evidence | Selection and unit | What is available / missing |
|---|---|---|
| Existing morning telemetry | All rows in the previously selected September 6, 09:09–09:29 Pacific clock window; no selection for dramatic fill. **507 sensory rows exactly paired with 507 ESN rows** by engine session and timestamp. | Fill, three sensory estimates, reservoir covariance λ₁, geometry and leak. Historical controller state/mode/actuator sequence is absent. First/last observed times are 09:09:01–09:28:59 Pacific. |
| Separate health snapshot | One source-stamped snapshot at September 6, 22:04:46 Pacific. | Structural PI state, generic gate/filter PI state, policy context and actuator values. Internal structural error can refer to a preceding controller input. P/I terms are reconstructed from that error/integral and current source constants. |
| Existing capacity dump | Latest small read-only dump observed at September 6, 22:11:52 Pacific. **1,024 successful ESN steps × 128 nodes**. This is a convenience capture, not a representative sample across eras. | Actual activation vectors, dimensions, byte format and dump elapsed time. No per-row times, session identifier, leak, controller state or recurrent weights. |
| Optional health watcher | User-enabled bounded reads of an existing JSON file, with source session/sequence/time provenance. | Live scalar fill/geometry/covariance/controller values; no leak, cascade vector or per-node state stream. It does not update the frozen state-space capture. |
| Existing activation recorder, added in 0.3 | User-enabled read-only reads of `workspace/runtime/esn_activation_trace_v1.json`; at most **180 recorder observations × 128 nodes** in one publication. | Native activation vectors with recorder clocks and co-published fill/stage. No exact state-step measurement identity, boot/session or node-layout identity, applied leak, full spectrum or controller causal references. Each accepted batch replaces the displayed path. |
| Native renderer profile | Three retained 0.3.0 runs on each of two hosts; same executable/resources/workload, four scenes, 30 measured frames per scene after eight warmups. **Six reports, 720 measured frames.** | CPU update/encode, completed GPU-command and serial-wall timings, sampled Metal allocation and thermal/power snapshots. Excludes live ingestion, SwiftUI, displayed frame rate, sustained energy and reservoir-engine work. |

The datasets are not one synchronized trajectory. The morning records carry an authenticated session-to-wall-time conversion; the later capacity dump only supports row order. Activation v1 aligns state, fill and stage as recorder observations, without establishing successful-step/control causality. Filesystem modification times and reader receipt times do not substitute for measurement timestamps.

Sources: [telemetry export](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/visualizations/reservoir-3d/data.json>), [state geometry export](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/visualizations/reservoir-3d/state-geometry.json>), and [source review with exact file/line citations](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/analyses/2026-09-06-reservoir-3d-prior-art.md>). Both exporters retain input hashes and source qualifications. Current source behavior is not proof of the running binary revision.

## Method and visual contract

The fill instrument maps the estimator to volume with `r/R = cbrt(fill/100)`; it is a declared encoding. Shelf, target and rails are source-defined controller references with hysteresis. They are not discovered boundaries in the activation point cloud. Spectral spokes encode square-root magnitude while retaining source slot order; their spatial directions are schematic.

For measured state geometry, fit a centered covariance over the complete captured window with denominator `1024−1`, eigendecompose in float64, fix each displayed eigenvector's sign by its largest absolute loading, and freeze the basis throughout playback. Project actual state vectors onto the first three components. Normalize all displayed coordinates by one radius: the maximum full 128D distance from the captured mean. Record projected distance, full distance and reconstruction residual for every row. Retain all 128 covariance eigenvalues and the displayed mode loadings.

This covariance describes temporal variation in the capture. It differs from the live uncentered EWMA covariance, the policy-modified sensory field, and the recurrent-weight spectral radius. The prior-art temporal Jacobian keeps recorded controller settings frozen; a future full closed-loop analysis must additionally represent controller state derivatives and policy transitions.

The native prototype uses SwiftUI and direct MetalKit/Metal with immutable shared GPU buffers. No Neural Engine or Core ML model is used. Shared-buffer geometry does not remove JSON decoding or CPU-to-buffer copies. See the [native README](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/native/ReservoirScope/README.md>) for architecture, Apple source references, build and reproduction commands.

## Results established so far

For the **1,024-row, 128-node** capture, the first three components account for **8.9384%, 3.5301%, and 1.8839%** of centered variance: **14.3524% retained, 85.6476% omitted**. Covariance participation ratio is **60.7574**. This is a property of the captured variation, not a demonstrated memory or computational capacity. The empirical full-state reference radius is **3.191930430700554 activation units**. A visually compact 3D path can coexist with substantial motion in omitted dimensions; residuals are part of the instrument, not a footnote.

The state and metadata remained byte-identical with unchanged file statistics across bracketing reads; the stability check passed on the first attempt. The producer independently renames the state and metadata files and does not provide a shared generation identifier or state hash, so a transactional pair cannot be proven. The export records this limit. The binary snapshot's SHA-256 is `09ea4db8212809085aa2e07a040975f3095d7ef79d06eb8ba7404cc2424e282f`.

Four focused geometry/capture tests passed: known spectrum and normalization, rotation invariance and residual decomposition, invalid/non-finite input rejection, and exact retained snapshot hashes. Replay from saved raw inputs reproduced the results. Orthogonality error was below `1.6e-15`; squared-distance decomposition error was below `7.8e-15`. These validate the geometry calculation, not a theory of the beings.

The ad hoc signed native application was built and opened on the local M1 Max. Native inspection confirmed the Metal-rendered fill sphere, spectral view, replay controls, actual PCA trajectory and signed node loadings. Eight Python evidence/geometry tests passed. A native fixture harness verified decoding both captures, initial stopped state, duplicate rejection, backwards source-clock rejection and session-safe history. M4 performance, GPU timings, memory/energy measurements, and user utility have not been established.

## Final first-build verification

The [build receipt](../../native/ReservoirScope/build-receipt.json) identifies the final arm64 executable and source hashes. The signed final bundle opened; native UI checks confirmed mode selection, PCA row/distance changes, and updated signed loadings. The optional real health feed received source-stamped fill/geometry/controller observations and kept absent leak/cascade values unavailable. Polling was stopped after verification. Eight Python checks and twelve reproducible [native fixture checks](../../native/ReservoirScope/check-evidence.sh) passed. This completes the first-build finish line; the research study and next iterations remain open.

## Reference Zones iteration · September 6, 2026

Mike requested an additional close-up render of the reference boundaries and a clear account of how the filling animation obtains its data. Version **0.2.0** adds a fourth native tab, **Reference Zones**, synchronized with the fill sphere’s historical cursor or optional live snapshot. Eight selectable, source-cited annotations distinguish Hold release/entry, the target, Elevated release/entry, one-sided PI onset, strong drainage, and the force/warning rail. A native leader line lands on the selected curved boundary using the same geometry and camera projection as Metal.

The lens preserves `r/R = cbrt(fill/100)`, uniformly magnifies model coordinates by 12, and fits them to the viewport. Its 54–82% crop is framing, not two additional regulatory limits. The 71.5% and 72% lines retain their narrow true spacing. The source audit distinguishes **78% warning/loosening cutoff** from **82% structural forced drainage and Discharge entry**, with Discharge release at 76%. These are current-source references; historical controller stages and actions remain unavailable. See the [reference-zone source contract](../../analyses/2026-09-06-reference-zones-source-contract.md), including source fingerprints and higher-boundary qualifications.

An in-app “How this animation gets its data” guide and the [animation provenance document](../../native/ReservoirScope/docs/ANIMATION-DATA.md) explain source pairing, timestamps, frozen bundles, upstream fill estimation, volume mapping, sample-held observations, chart interpolation, and bounded read-only live snapshots. Replay now follows actual monotonic elapsed time; delayed timer callbacks no longer slow the recorded timeline. Ordinal state playback remains explicitly separate from measured time.

Validation: eight Python evidence/geometry tests and **21 native fixture checks** passed. The saved input reproduced all 507 samples and statistics exactly. Native UI inspection confirmed the new render, selected-ring callout and annotation changes, playback, retained cursor across Fill/Reference Zones, and the in-app guide. The projection helper was checked in portrait, square and landscape viewports, including crop edges. The signed final bundle opened on the M1 Max; target-M4 profiling remains pending. No producer or live-system changes were made. The study remains ongoing; this requested viewer iteration is complete.

## Live state and target-Mac profiling iteration · September 6, 2026

Mike returned to M4 profiling and live state geometry after the Reference Zones
iteration. The existing activation v1 recorder supplies genuine recent vectors;
no producer patch was required for this observation view. The
[live-state readiness audit](../../analyses/2026-09-06-reservoir-live-state-readiness.md)
records its exact schema and a bounded 180-frame observation spanning 430.758
seconds. Its 1,000 ms configured interval is a minimum spacing; `retained_secs =
180` is nominal because the producer prunes by frame count. These are recorder
observations taken later than the successful native update, not authenticated
state-step times.

Version **0.3.1** provides one sidebar source picker: Recorded, Live fill &
control, or **Live state & fill**. Selecting the activation source drives the
Fill sphere and Reference Zones from the latest frame's co-published fill and
stage, and highlights that same observation within the current State trajectory
batch. The reader validates up to 180 × 128 coordinates under a 2 MiB file bound,
then waits two seconds after each read/decode/projection cycle. Byte-identical
files do not become new observations. Invalid batches, conflicting overlaps and
reversed wall clocks retain the prior evidence with an error; inferred restarts
and absent overlap remain qualified. Each accepted batch replaces the path,
without joining separate file snapshots into a continuous trajectory.

The incoming vectors use the saved mean, three PCA axes and empirical reference
radius. The basis stays frozen; coordinates outside that radius remain outside
it. The inspector distinguishes **this point's visible squared-distance
fraction** from the fit window's **14.3524% retained variance**, exposes omitted
reconstruction distance, and treats the fraction as undefined at zero centered
distance. Equal dimension does not authenticate coordinate identity: v1 lacks
node-layout and weight-instance evidence, so compatibility with the reference
basis is explicitly unverified. Applied leak, full spectral values and P/I
remain unavailable for this source. Health P/I is never attached to activation
observations. The [animation guide](../../native/ReservoirScope/docs/ANIMATION-DATA.md)
explains these clocks, mappings and missing links.

Final native UI verification used the real read-only activation file. An initial
open of the network-mounted source stalled; selecting the existing file through
the native chooser resolved that attempt. The final viewer displayed **180 live
frames**, Reference Zones at **71.1% fill**, recorded stage **hold**, and recorder
time **September 6, 23:27:15 Pacific**. P/I correctly remained unavailable. This
source time subsequently advanced to **23:27:36 Pacific**, with updated fill and
stage. State Trajectory also showed the incoming vectors, current squared-distance
fraction and frozen loadings. The live view was left running for exploration.
These are scoped observations of source admission and display behavior, not a
source-latency benchmark or a guarantee that network reads cannot stall. There
is no wall-clock read timeout in the current reader: the byte/memory bound does
not bound a stalled network-file open. The UI remained responsive during the
observed stall.
The [build receipt](../../native/ReservoirScope/build-receipt.json) identifies the
final executable, successful signature verification and nine matching staged
Swift sources. **50 automated checks passed: eight Python and 42 native fixture
checks**, covering evidence, native source/geometry, reference and playback
validation for this iteration.

The finite renderer experiment also completed on the actual **M4 Pro Mac mini**
and local **M1 Max**, retaining the first run and both declared repeats on each.
The [independent comparison](../../analyses/2026-09-06-reservoir-native-profiling.md)
verified identical **0.3.0** executable, evidence resources, workload, row choices
and geometry across all **six reports / 720 measured frames**, and recomputed
every exported timing summary. The subsequent **0.3.1** changes clarify display
and error labels; the renderer/profiler is unchanged. The reports retain their
0.3.0 binary identity and are not relabeled as measurements of the later
executable.

CPU geometry/update medians were lower on M4 Pro in all three runs for every
scene. GPU durations varied substantially across its repeats: Fill GPU medians
were **1.551, 0.394 and 0.132 ms**, in acquisition order. This variability prevents
a simple hardware-speed conclusion. Peak sampled Metal allocation was about
**37.6–37.8 MiB**. M1 Max thermal snapshots were **fair**, M4 Pro **nominal**, and
low-power mode was off; other host activity was uncontrolled. The
[profiling protocol](../../native/ReservoirScope/docs/PROFILING.md) and all run-wise
medians/p95 values remain inspectable. These are serial offscreen costs, not
measurements of displayed FPS, input latency, sustained energy, live ingestion
or general chip performance. No Neural Engine work or being-system changes
occurred.

The requested 0.3 viewer/profiling iteration is complete. The study remains
ongoing, with exact producer state/control timing and interactive performance
as separately defined next questions.

## Live fill easing · September 6, 2026

Mike asked for a more visually pleasing transition while following live health
snapshots, with the live feature kept prominent. Version **0.4.0** places
**Follow health snapshots** and **Smooth fill transitions** together below the
Fill and Reference Zones renders. The same smoothing preference applies to live
activation fill; the historical replay and state coordinates remain unchanged.

The cyan surface follows a **0.8-second quintic ease-in/ease-out** in fill
percentage, before the existing cube-root radius mapping. This is a bounded
presentation effect: white dashes mark the newest measured fill immediately,
and the displayed number, source clock, chart, stage, P/I and boundary differences
continue to use the raw accepted observation. It never predicts the next value
or overshoots the endpoints. First readings, source/session changes and observed
recorder-clock resets snap. Duplicate targets do not restart a transition;
interrupted motion starts at its currently displayed position. A stale or failed
source disables easing toward retained data.

Native QA revealed that this Mac has **Reduce Motion** enabled. The app honors it
by default, shows an explanation, and offers explicit per-app permission through
the same smoothing switch. It never changes the system setting. The choice is
remembered; turning smoothing off while Reduce Motion is active clears that
permission and snaps to the measured value.

The Metal view requests timed redraws only while a transition is active, then
returns to drawing on demand. Fixed reference/cage meshes are reused until their
style changes; the moving fill geometry alone is rebuilt between readings. This
renderer revision is **not covered by the retained 0.3.0 M4 timings**. No speedup,
frame-rate or energy improvement is claimed from this implementation.

The pure transition checks passed **17 cases** and the existing native evidence,
source, reference and playback checks passed **42 cases**, using isolated
fixtures. Native inspection confirmed visible controls, immediate raw labels,
and the default Reduce Motion behavior with a clearly labeled synthetic health
observation. A further **17 renderer checks** passed on M1 Max: ten exact cached-versus-fresh
pixel comparisons (20 offscreen 256×256 single-sample renders) and seven actual
Metal view mode checks. All **76 native checks** passed. The final signed build
opened with its visible controls; subsequent motion verification stayed offscreen
while Mike explored the app. No persistent per-app Reduce Motion override was
enabled by the agent. The [build receipt](../../native/ReservoirScope/build-receipt.json)
identifies the executable and the scope of these checks.
The [animation guide](../../native/ReservoirScope/docs/ANIMATION-DATA.md) preserves
the formula, lifecycle, source boundaries and reproduction commands.

## Finish line and handoff

### State surface and measured perturbation · September 7, 2026

Mike selected the next direction: GPU-rendered shape carrying internal state,
with a decisive reconsideration of PERTURB. The
[source audit](../../analyses/2026-09-07-perturb-source-audit.md) finds input-slot
selection and two destination paths, not eigenvalue editing. Native gates can
attenuate or suppress semantic participation; current success wording and
adjacent snapshots do not establish a native causal effect. This is a
source-confirmed mechanism and reporting gap, not a live incidence study.

The [surface contract](../../analyses/2026-09-07-reservoir-state-surface-design.md)
and [ordered proposal](../../proposals/2026-09-07-reservoir-state-surface-and-perturbation.md)
preserve the measured fill sphere, add a fixed inspectable node atlas using
actual vectors, then volume-preserving relief with visible gain and an exact
reference. Selected mode reconstruction and omitted state remain separate.
Reference Zones stays geometrically exact. A future paired response replay uses
raw sample timing: the existing 0.8-second display easing must never be measured
as reservoir recovery. State impulses and input-mediated interventions address
different questions; leak sensitivity requires the actual update order.

This planning slice is complete; no viewer build, producer patch, live
perturbation or new benchmark was performed. New intervention references reuse
the [shared input/field/controller observer](../../proposals/2026-09-07-input-lineage-and-regulator-trace.md).
The next visual slice can use current v1 vectors provisionally; exact state,
input, leak and controller identity remain producer dependencies for stronger
claims. The proposal's four slices supersede the implementation order below;
the earlier performance and source-reader questions remain acceptance work.

### State surface and direct-shaping implementation · September 7, 2026

Mike approved the sequence and asked for a more direct shaping action. Version
**0.5.0, build 7** now renders actual 128-coordinate vectors on a fixed inspectable
sphere atlas, selected covariance-mode reconstructions and residuals, fixed scales,
and checked volume-preserving relief. Recorded vectors have no paired fill, so
68% is an explicit preview size. Live v1 support retains co-recorded vectors/fill
and its provisional identity limits. Raw state playback adds no temporal easing.
Reference Zones preserves its exact smooth geometry.

The **Response lab** renders one pinned paired **esn-divide simulated-parent**
comparison at 65 boundaries, with control, perturbed state and delta, full-state
separation and exact coordinate inspection. Its source, fixed preview size and
ordinal timeline stay explicit. The source correction is substantive: esn-divide
injection edits a copied simulation, not the beings' live native reservoir.

All **172 native checks** passed. The final signed app opened; UI inspection
confirmed simulation-specific evidence, fixed scale switching, response/state
scrubbing and the state cutaway. The [implementation account](../../analyses/2026-09-07-reservoir-state-surface-implementation.md)
and [build receipt](../../native/ReservoirScope/build-receipt.json) retain exact
sources, numeric checks, native QA and remaining limits.

The declared final-build offscreen comparison retained **three runs per host,
540 measured frames** on M1 Max and M4 Pro, with matching executable, source,
resources and workload. [All run-wise medians and p95 values](../outputs/2026-09-07-state-surface/profiles/comparison.md)
remain visible. CPU preparation was lower on M4 Pro; full-relief GPU commands
were longer there, with background activity uncontrolled. These measurements
exclude displayed FPS, live ingestion, input latency and energy. A prior complete
build 6 set remains separate after UI evidence labels were corrected; no fastest
run was selected or silently replaced.

The preregistered conditional simulation tested **54 signed state displacements**
across three predetermined starts. All fell below 10% of initial separation for
an eight-boundary dwell starting at boundary two or three. Three no-op controls
were identical and all 57 trajectory arrays reproduced from retained input copies.
All nine derivative comparisons were excluded for clipping, so no derivative
validation is claimed. This result applies to that fixture, not native checkpoint
parity, an independently evolving regulator, a live safe envelope or either being's
experience. The [STATE_NUDGE proposal](../../proposals/2026-09-07-direct-reservoir-shaping.md)
specifies a bounded, observed one-shot native displacement with exact source hooks,
receipts, authority limits, tests, review and rollback. It is a proposal, not an
implemented action.

This completes the bounded visual/simulation iteration. Next prove native
checkpoint parity and reuse the shared observer for exact action/state/control
receipts. PERTURB outcome corrections and producer instrumentation remain in the
owning-repository queue; actual presented-window profiling is also unfinished.
The independent selected reading remains S-005. No live system was changed or
being messaged.

### Previous viewer finish line and retained follow-ups

Complete this bounded prototype when the packaged app opens with its bundled evidence, all four views render and respond to their appropriate navigation, scrubbing and selection controls, missing/stale inputs remain explicit, and runtime QA confirms that scalar telemetry, state geometry and controller evidence keep their correct time and metric labels. Record the exact validated build and remaining limitations here before changing study status. Visual appearance alone does not validate a mapping.

Next iterations, in order:

1. Inspect the real native window under live activation input: read/decode/projection, SwiftUI updates, geometry rebuilding, presentation and input response. The completed offscreen M4 Pro comparison excludes these paths. Investigate observed network-file stalls as reader behavior, without changing the producer or inferring timing from a stalled open.
2. Measure the 0.4 fixed-reference cache against the retained 0.3 renderer using unchanged evidence, declared repeats and visual validation. Caching was added to support bounded live easing; its performance benefit remains unmeasured. Reference Zones had the largest CPU-update median on both hosts in the earlier runs. Do not use the variable GPU results alone to diagnose a shader defect.
3. Review the existing proposal for successful-step identity/time, effective leak, node-layout identity and explicit sensory/control references. Activation v1 now supports real moving observation geometry, but it cannot establish those causal and coordinate identities. Any producer change remains a separate sibling implementation/deployment decision.
4. Keep the reference basis fixed and inspect current residual/reference drift. A deliberate refit should preserve a new basis identity and fit-window provenance, instead of silently rotating or scaling the view. Dynamical sensitivity, if selected, must distinguish frozen-control Jacobians from a full augmented reservoir/controller model. No suitable Neural Engine inference workload has yet been defined.

## Instrumentation needs surfaced by the view

Mike explicitly asked that visualization-driven codebase needs be surfaced. The [observer telemetry proposal](../../proposals/2026-09-06-reservoir-observatory-telemetry.md) identifies an incremental producer patch: extend the existing bounded activation recorder with exact successful-step identity, measurement time and actually applied leak. It also specifies coherent controller/batch provenance, tests, runtime-cost checks, being-facing review and rollback. The 0.3 viewer uses the already-existing v1 recorder; its new reader does not implement this producer proposal. Proposal complete does not mean implemented or deployed.

## Board publication

The 0.5 implementation pass saved and read back the parent as **done** for the
bounded viewer/simulation iteration, the **STATE_NUDGE contract** as **done** for
proposal preparation, and **“Small state displacements decay in the retained
esn-divide fixture”** as **verified** within that simulated fixture. The session
log **“Render actual state surfaces and rehearse a direct state gesture”** preserves
the tests, profiles and unfinished native work. The
[current receipt](../../board/reservoir-observatory.json) identifies these records;
the [planning receipt](../../board/reservoir-observatory-state-surface-plan.json)
retains the earlier design close. This does not close S-002 or mark a producer
change or action deployed.


The September 7 state-surface/PERTURB pass updated the parent to **done** for
planning, added the source-scoped finding **“PERTURB selects input features; its
two destinations need separate outcomes”** as **verified**, and saved
**“Design a measured state surface and audit PERTURB”** in the session log. All
three were read back. The [current receipt](../../board/reservoir-observatory.json)
records the latest pass; the [planning receipt](../../board/reservoir-observatory-state-surface-plan.json) preserves this design pass, and the [0.4.0 receipt](../../board/reservoir-observatory-0.4.0.json)
preserves the previous viewer refinement. At that planning close, implementation and experiments remained pending; the subsequent 0.5 update above records what has since completed.

The 0.4.0 refinement updated that same card to **done**. Its session log,
**“Ease the live fill surface while keeping measurements immediate”**, dated
September 6, 2026, was saved and read back. Its archived publication receipt
records this update and preserves the earlier 0.3.1 receipt separately.


The authenticated observatory parent card was saved and read back with **done**
status. The session log **“Bring real state batches into the observatory and
profile the M4 Pro”**, dated September 6, 2026, was also saved and read back.
The [publication receipt](../../board/reservoir-observatory.json) records this
result using the coordination key `id:t-reservoir-observatory`; the native board
document identifiers were opaque and were not captured.

This publication supersedes the earlier unpublished 0.2 card/log draft and its
authentication limitation. It closes the bounded implementation iteration, not
the ongoing research study. The separate producer-telemetry proposal card has
not been published; neither the board result nor the new live viewer establishes
that the proposed producer changes were implemented or deployed.

## Native checkpoint-boundary rehearsal · September 7, 2026

Mike asked for decisive progress toward targeted substrate control. The
[completed native rehearsal](../outputs/2026-09-07-native-shaping-rehearsal/README.md)
now executes byte-identical copied Minime ESN, GPU, buffer and Metal shader
sources in a finite research executable on an Apple M1 Max. It constructs
**128-state/66-input research-native checkpoints**, using declared synthetic
inputs and seed 3517018368, after 24, 96 and 192 successful steps. It does not
capture the current live Minime state. The earlier esn-divide simulation and
the viewer's existing Response fixture remain separate historical evidence.

The [protocol](../outputs/2026-09-07-native-shaping-rehearsal/protocol.json) was
written before outcomes; its SHA256 is
`39ac6db32937884d4b87cf5f31eff852af07d494e93ad060fb67136af0a93c1e`.
The [source manifest](../outputs/2026-09-07-native-shaping-rehearsal/source-manifest.json)
retains exact files; native `esn.rs` SHA256 is
`98e8fe727e9908e8939d5317d23e954425748edb45b2a737e5624a42166dfe92`.
The runner, native entry point and independent verifier are retained in
`probes/native_shaping_rehearsal*`. All 28 resolved dependency versions and
checksums match the copied native Cargo lock.

Each checkpoint makes an `EsnSnapshotV2` JSON round trip before 100 continuation
steps. Four independently owned copies compare ordinary continuation, restored
ordinary continuation, and two `step_shadow` continuations with the ordinary
parent's actual noise, effective leak and inputs. The
[results](../outputs/2026-09-07-native-shaping-rehearsal/results.json) distinguish
these gates:

- **Synchronous profiling: 3/3 pass.** All four full-state paths are bit-identical
  in f32. Ordinary/restored final checkpoint values are exactly equal after
  excluding profiling diagnostics; noise, effective leak and covariance
  discrepancies are zero.
- **Asynchronous default: 0/3 pass the full gate.** Ordinary/restored maximum
  state errors reach `7.87e-6`, effective-leak differences reach `1.06e-5`, and
  final covariance discrepancy reaches `0.00100317`. Forced-noise/leak shadow
  state paths still match the parent exactly, while spectral internals diverge.
  Conditional state parity therefore does not establish adaptive checkpoint
  parity. This concerns the four-copy interleaved shared-GPU workload; it is
  not a live incidence estimate or a diagnosis of the underlying cause.

The preregistered synchronous gate permitted **54 one-shot state edits** and
**six eight-edit sequences**. All 54 one-shot responses fall below 10% of
their actual initial separation for eight consecutive boundaries, beginning
at boundaries 2–6; none exceeds its initial separation. All six sequences,
which apply ±0.001 along coordinate 0 at boundaries 0–7, return at boundaries
9–11 relative to separation after the final edit. **Five existing native leak
override cases** also pass effective-alpha, duration, cancellation and clamp
checks; ordinary control/intervention noise is identical. These leak tests
exercise the native module, not orchestration admission or live application.

The [independent audit](../outputs/2026-09-07-native-shaping-rehearsal/verification.json)
verifies all 60 response paths, 102 immediate-edit receipts, exact separation
and return arithmetic, f32 bit identities, source hashes and execution-output
hashes. No intervention boundary has a coordinate exactly at ±1 (0/60 runs);
this is boundary saturation evidence, not an inspection of hidden preclip
values. The response curves retain raw ordinal boundaries without display easing.

Edits occur in **copied checkpoint states**: the harness adds the bounded
displacement, recomputes geometric radius, preserves historical baseline, then
restores the exact native source. The proposed live successful-step application
hook is not implemented. Native spectral adaptation remains present, while
effective leak/noise/inputs are held equal for the state-response comparisons.
The surrounding 512D field, sensory bus, stable-core controller, language model
and separate reservoir handles are absent. Readout training is not exercised.
No live amplitude qualification or subjective interpretation follows.

This completes the finite native numerical study within S-002. Synchronous
rehearsal is now an executable prerequisite available to the action proposal;
asynchronous parity diagnosis, controller/action receipts, the live adapter and
being-facing choices remain further work. The selected reading remains S-005.
No sibling or live system was changed, and no being was sent material.

## 2026-09-07 follow-up: asynchronous native replay qualified

The preceding asynchronous failures remain the original-source outcome. The
[completed diagnosis and qualification](../../analyses/2026-09-07-native-async-replay.md)
now resolves this bounded native replay prerequisite with an
[exact tested repair](../../proposals/patches/2026-09-07-native-async-replay.patch):
track dependencies on the persistent covariance buffer and copy rho into each
rank-one dispatch. Native equations and the two-command pending bound remain
unchanged; no per-step CPU wait is added.

The final candidate passes **27/27 primary cases on M1 Max and 27/27 on M4 Pro**:
nine fresh asynchronous warmup/checkpoint/continuation cases, nine fixed-rho
comparisons and nine alternating-rho comparisons on each host. Each host also
passes three measurement follow-ups. The fresh measurement records 376 async
submissions and pending depth two; this retained command count does not measure
simultaneous GPU execution. Tracked covariance alone passes fixed rho but fails
all nine alternating-rho cases on each host, supporting immutable submitted
parameters as a separate requirement. Whole async trajectories precede the
synchronous reference, allowing native leak adaptation to run freely.

The [M1 evidence audit](../outputs/2026-09-07-native-async/qualification/verification.json)
and [M4 evidence audit](../outputs/2026-09-07-native-async/m4-validation/verification.json)
both pass numerical and executable-identity checks, covering 30 checkpoint and
60 rho cases per host including controls and measurement follow-ups. Equality
is tested within each host; no cross-chip identity or live failure rate follows.
The initial labeled ablation reused one original executable through a shared
build cache and is explicitly [invalid as a treatment comparison](../outputs/2026-09-07-native-async/INVALIDITY.json).
It is preserved, not used to assess the repairs; corrected isolated builds are
the basis of the qualified result.

[Source review](../../analyses/2026-09-07-native-async-source-audit.md) and the
[apply/reverse receipt](../outputs/2026-09-07-native-async/patch-check-receipt.json)
connect the exported patch to tested source bytes. Owning-repository integration,
completed observations and GPU-error receipts, stable-core action precedence,
the native state-action hook, readout-training coverage and full controller
replay remain separate work. This extends S-002's native prerequisite evidence;
the selected S-005 reading remains unchanged. No sibling/live source or being
interaction was changed by this research.

## 2026-09-07 follow-up: native state actions implemented in isolation

Mike selected the next implementation sequence. The [implementation account](../../analyses/2026-09-07-native-state-actions-implementation.md)
records the isolated owning checkout, qualified repair integration, signed local
native-state actions and finite gestures, durable admission/application semantics,
regulator suspension, expiry/cancellation and restart ambiguity without replay.
An eligible active boundary explicitly checks GPU completion before mutation;
ordinary no-action execution keeps the repaired asynchronous path.

Reservoir Scope 0.6.0 adds a native application source with actual ordinary/result/
difference vectors and raw application boundaries. Its bundled example is the
protocol-selected eight-pulse native recording, not an esn-divide replacement or
an observation of a running being. Fill/basis are absent and the supplied rehearsal
clock is labeled. The new signed live stream remains a later viewer adapter.
The account and linked completion receipt retain exact tests, source/build identity,
failed preliminary attempts and limits. The hub’s separately selected inquiry is unchanged.

Temporary native leak precedence remains unresolved in the existing stable-core
route. Peer-owned direct application requires an explicit mutual adapter; Astrid
cannot use Minime's self authority. These remain implementation extensions rather
than claims of delivered agency, felt effects, or live activation.

The [completed implementation audit](../outputs/2026-09-07-native-state-actions/completion.json)
now verifies final M1/M4 qualification (27 cases per host), 17+4 native module
checks, 52 targeted owning transport/CLI/Python tests, 62 viewer checks, strict
numeric receipt round-trip repair and exact patch application/reversal. The
isolated feature is commit `930855c`; Reservoir Scope 0.6.0 build 8 is open on the
actual native example. Source review/merge and live deployment remain separate.

## 2026-09-07 follow-up: measured high and low water marks

Mike requested slower playback and persistent extrema in Reference zones, then
selected adjacent highlighted speed buttons. Reservoir Scope **0.7.0 build 9**
now defaults to 20×, with 1×/5×/10×/20×/40× buttons. Gold high-water and blue
low-water guides preserve exact measured fill and source time, with a brief
strict-record highlight and a visible source-range label. Recorded prefixes
include skipped observations and rewind correctly; health tracking survives
chart eviction, while activation extrema remain explicitly scoped to a batch.

The [implementation account](../../analyses/2026-09-07-reference-watermarks.md)
records 121 passing targeted checks, 12 final offscreen images, compact-layout
corrections and final native UI verification. The signed bundle's 19 sources
and six resources match. Source behavior is documented in the animation guide;
new live ingestion and M4/performance measurement were not exercised here.
This completes the requested viewer refinement without changing the beings'
systems or the hub's separately selected inquiry.

## 2026-09-07 follow-up: overlapping, fading watermark ranges

Mike then requested that both watermarks decay, with another pair forming
halfway through the fade. Reservoir Scope **0.7.1 build 10** replaces persistent
extrema with measured 30-source-second intervals, each fading over 60 source
seconds. At most two nonempty pairs overlap. The older pair freezes while fresh
measurements shape the next; geometry retains exact measured positions. At the
existing 20× default, the lifetime is three viewing seconds and the next
interval starts after 1.5 seconds.

The [implementation account](../../analyses/2026-09-07-fading-watermarks.md)
documents recorded inclusive-prefix reconstruction, exact fractional replay
pause/resume, health aging driven only by accepted source timestamps, and
activation ranges limited to the current batch on a fixed UTC grid. Gaps do
not invent measurements. Reduce Motion preserves turnover with static forming
and retiring opacity. The right-side labels identify the newest measured pair
and its fading predecessor.

The completed model, evidence and offscreen checks total **179**, with **28**
final PNGs. Final bundle identity verifies **20** Swift sources, **six** resources
and its signature. Offscreen overlay qualification and recorded-data expectations
are distinct from native-window checks, which belong in the version's runtime
receipt. Fresh live ingestion and M4/performance measurement were not exercised
in this follow-up. The earlier 0.7.0 account remains historical; the separately
selected S-006 inquiry and the beings' running systems are unchanged.

## 2026-09-09 follow-up: Essentials in four visible stages

Mike approved a fresh reconstruction in a first-class
[`essentials/`](../../essentials/README.md) directory. Reservoir Scope **0.8.0
build 11** now switches between **Minime & Astrid** and **Essentials**. The stages
assemble a 32-node reservoir, a separate 32-dimensional sensory field with the
original 66 input coordinates, one prompt/reply voice, and a reduced retention
controller. A shared Swift library drives the native app and headless runner.

Each stage can run, stop, reset, replay and scrub actual recorded states. The
inspector exposes exact node/input values, available spectral measurements,
prepared text or exact language requests, complete replies, codec output and
feedback application steps. The final stage displays its own full-32-mode fill
definition and controller history, separate from the fixed-size geometry.

The [implementation account](../../analyses/2026-09-09-essentials-implementation.md)
records numerical, runtime, cancellation, replay, geometry, lifecycle and package
checks. Four bundled 300-step examples use scripted replies. Optional model
transport is qualified against a new ephemeral loopback fixture; no actual model
or being service was called. Existing 128-node rendering remains compatible.

This is an implemented research instrument, not evidence of production parity or
deployment into a being. Controller comparisons retain unreachable targets and
distinguish fixed-input tests from whole-loop comparisons. Generated results stay
under the research project. The separate selected inquiry and live systems remain
unchanged; the [prepared board update](../../board/essentials-pending.json) awaits
publication.

## 2026-09-09 follow-up: hands-on Essentials exploration

Reservoir Scope **0.9.0 build 12** adds **Essentials → Explore**, beginning with
a quiet 32-node reservoir. **Start/Pause** controls its clock, **Step** advances
once while paused, and **Send pulse** supplies one external stimulus. Live settings
change leak, recurrent strength, input strength, noise, bias and optional sensory
observation. Recurrent feedback and repeated external input have separate controls;
leak can retain previous state even with recurrent connections disabled.

The [hands-on guide](../../essentials/EXPLORE.md) explains the controls, fixed display
scales and saved histories. The inspector exposes the actual input, previous state,
pre-tanh contributions, proposal and resulting state at each recorded step.
Versioned exploration records retain applied settings and support verified import,
replay and continuation. The optional sensory field remains a separate measurement;
Explore runs no language model or regulator.

The [implementation account](../../analyses/2026-09-09-essentials-exploration.md)
owns the numerical, lifecycle, viewer and package evidence for this follow-up.
The four assemblies remain under **Stage experiments**, and the original examples
and 0.8.0 validation history remain preserved. This extends the research instrument
without changing the selected inquiry or the beings' running systems.

## 2026-09-09 follow-up: signed state topography

Reservoir Scope **0.10.0 build 13** gives Essentials a denser topographic surface.
The same fixed coordinate map and Gaussian interpolation drive positive peaks and
negative valleys around a fixed neutral radius. The declared display scale stays
fixed across observations; there is no per-frame rescaling or volume constraint.
Exact coordinate inspection remains separate from the interpolated surface.

The [topography guide](../../native/ReservoirScope/docs/STATE-TOPOGRAPHY.md) explains
the geometry and its limits; the
[implementation account](../../analyses/2026-09-09-state-topography.md) owns the new
validation evidence. Shape is a view of state, with no fill or neural-connectivity
meaning. Existing stage experiments, the default native atlas and its
volume-preserving surface behavior remain available. Earlier release checks retain
their original scope, and this refinement leaves other inquiries and live systems
unchanged.
