# Reservoir Scope

Continuing this work: [Agent handoff — main, shared paths, build and checks](HANDOFF.md).

September 15 source stabilization fixes Swift 6.2.4 type inference in reservoir
initialization and the action difference plot. [Offline source checks](validation/stabilization-20260915/source-checks.json)
qualify these sources separately from the unchanged [September 10 packaged build receipt](build-receipt.json).
Source staging now prunes files removed from the checkout before compilation.
The stabilization build was not installed or launched; no live system was contacted.

A native macOS observatory for Minime's reservoir telemetry and measured state geometry.
**Version 0.11.0 adds Actions & comparisons in Essentials.** Build through the
eight-version action ladder, write a local journal, and inspect its return through
the codec or the next prompt. Adjacent versions share cameras, cursor and fixed
viewing scales. Fixed reply/vector replay and independent generation have separate
labels and portable records. The [action guide](../../essentials/ACTIONS.md) and
[implementation account](../../analyses/2026-09-10-essentials-actions.md) explain
the controls, exact evidence and qualification.

**Version 0.10.1 softens the bright zero-contour seams** while preserving the state
mapping and fixed contour levels.
**Version 0.10.0 adds state topography in Essentials:** cyan peaks, purple valleys,
fixed contour levels and an adjustable Height control. Color, height and contours
share the same projected state values. The original Surface view remains available.
The [topography guide](docs/STATE-TOPOGRAPHY.md) explains the mapping and its limits.

**Version 0.9.0 adds hands-on Essentials exploration alongside the four stage experiments.**
Start or pause the reservoir, advance one step, send a pulse, enable recurrent feedback
or repeated external input, and adjust parameters while watching actual state.
The [exploration guide](../../essentials/EXPLORE.md) explains timing, each recorded
control, the separate sensory field, and replay. The numerical core verifies every
saved setting and update contribution.

Version 0.8.0 introduced the four runnable stages that rebuild the core mechanisms.
The top-level **Minime & Astrid / Essentials** switch selects existing observations or
fresh 32-node reconstructions. Run, Stop, Reset, Replay, scrubbing, exact node inspection,
and Open/Export use the shared [Essentials core](../../essentials/README.md).
The [implementation account](../../analyses/2026-09-09-essentials-implementation.md)
records its scope and checks; the [build receipt](build-receipt.json) identifies the package.
The [0.9.0 follow-up](../../analyses/2026-09-09-essentials-exploration.md) records the
interactive controls and their validation.

Essentials progresses through reservoir, spectral bridge, one-voice feedback, and
reduced regulation. Its default examples use scripted replies; an explicitly configured
separate local Ollama endpoint is optional. Surface has a fixed display size;
Topography uses a fixed neutral radius with signed state relief.
The experimental fill and spectral summaries retain their own definitions, separately
from production telemetry. The app packages the same headless runner as its UI core.

The preceding 0.7.1 release added overlapping, fading reference watermarks. Existing
views retain native action receipts, actual state surfaces and optional curved live-fill
transitions. The [animation guide](docs/ANIMATION-DATA.md#observed-high-and-low-water-marks)
and [state-surface guide](docs/STATE-SURFACE.md) preserve those mappings.

The retained previous **0.5.0 build 7** passed **172 native checks** and was visually inspected.
Its separate [state-surface comparison](../../research/outputs/2026-09-07-state-surface/profiles/comparison.md)
retains three runs per host and 540 measured frames on M1 Max and M4 Pro. These
are offscreen renderer costs, not presented FPS or live-ingestion latency. The
[implementation account](../../analyses/2026-09-07-reservoir-state-surface-implementation.md)
records exact build identity, evidence and the direct-shaping rehearsal's limits.

Three retained runs on an M1 Max and three on an M4 Pro Mac mini establish the earlier bounded graphics baseline; [results and limits](../../analyses/2026-09-06-reservoir-native-profiling.md). Every benchmark used the same **0.3.0** executable. Those results do not measure the new 0.4 transition loop or geometry cache.

The app is steward-side. It bundles saved research evidence and can optionally follow an existing `health.json` or `esn_activation_trace_v1.json` through bounded, read-only polling. It does not send commands to Minime or Astrid, modify their files, or expose research material to their prompts.

**How the filling animation gets its data:** [Animation data and provenance](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/native/ReservoirScope/docs/ANIMATION-DATA.md>) traces the exact saved-record pairing, source clocks, playback selection, cube-root volume mapping, live polling and controller limits, with source citations and a command to reproduce every recorded sample.

## Reference Zones watermarks in 0.7.1

A measured pair gathers the high and low fill over **30 source seconds** and its lines fade away over **60 source seconds**. At half-life the previous pair freezes and a fresh pair begins following incoming observations. At **20×**, that is a three-second lifetime with a new interval every 1.5 viewing seconds. Solid forming arcs overlap dashed earlier arcs; one readable label pair preserves the current values, source times and earlier fading values.

Recorded playback includes intervening samples even when redraws skip them. Pause preserves the exact fade position; rewinding rebuilds earlier ranges. Health ranges reset with Follow/source/session changes and age only on accepted source clocks. Activation ranges use only the current batch with stable UTC interval boundaries. Silence never manufactures a fresh line from held fill. **Reduce Motion** uses static forming/retiring contrast with the same replacement and expiry.

Five adjacent speed buttons retain **1×, 5×, 10×, 20× and 40×**, with **20× default** and the selected speed highlighted. The guides use exact cube-root geometry; values outside the crop stay labeled without false clipped marks. These are recent interval extrema, not new regulator limits or lifetime records. See the [animation guide](docs/ANIMATION-DATA.md#observed-high-and-low-water-marks) for precise source scopes and timing, and the [build receipt](build-receipt.json) for verification. The earlier [0.7.0 account](../../analyses/2026-09-07-reference-watermarks.md) retains the superseded persistent-range behavior.

## Native action receipts in 0.6

Response lab now has an explicit source selector. **Native action receipts** imports
an isolated native rehearsal bundle and renders each actual pulse's ordinary
same-step state, immediate applied result and full Float32 difference on the GPU.
Requested dose, actual attenuation, selected leak, per-node noise, successful step,
model/node layout, command and file identity remain inspectable. An action-size
bar plot uses original step IDs; playback uses raw receipts with no easing.
**esn-divide simulation** preserves the separately labeled earlier conditional pair.

The native sphere has a clearly labeled 68% preview size because these receipts
contain no fill. It applies no PCA join and makes no recovery or stability claim
from an immediate action difference. **Open receipt file…** reads a bounded JSON
bundle; **Follow receipt file** optionally follows complete atomic research bundle
replacements and exposes read errors while retaining the previous data. This viewer
path does not submit commands, enable an action, or attach to a live runtime.
The producer implementation is staged in an isolated checkout. Active gesture
boundaries drain and check GPU work; ordinary steps retain the repaired async
path. The displayed boundary wait is measured separately from the explicitly
supplied rehearsal clock, which is not measured wall time.
[Native receipt mapping and provenance](docs/STATE-SURFACE.md#native-action-receipts-the-exact-application-boundary)
documents the exact contract, validation, timing and display choices. Use
`check-native-action-response.sh` for the consumer checks; an optional path argument
also validates a retained native producer artifact. The current [build receipt](build-receipt.json)
identifies what was actually packaged and verified. The new [consumer log](validation/0.6.0/native-action-consumer.log) records 37 passing checks, including all eight applied boundaries in the actual staged native example.

## State surface and Response lab in 0.5

The new view gives each of the 128 native coordinates a permanent place on an inspectable sphere. Exact node markers and a selectable grid retain unblended values; a fixed smooth map supplies context between them. Signed activation, magnitude, change from reference, selected captured modes and omitted component each keep a fixed scale. Metal evaluates the field and lighting from accepted observations, while the CPU validates the actual displaced mesh's volume, containment and normals. Shared resources retain immutable observation generations through GPU use. No Neural Engine model is involved.

Recorded mode uses the **original 1,024 × 128 signed activation values**, bound by hashes to the frozen PCA fit. These rows have no paired fill or per-row time. Their sphere therefore starts at a clearly labeled **68% preview volume**, adjustable without changing the observation, and plays in ordinal order at a presentation pace of 20 rows/second. **Live state & fill** instead supplies state and fill from one recorder observation; node-layout compatibility with the historical fit remains provisional. **Live fill & control** has no node vectors, so it does not manufacture a state surface.

This surface uses raw observed samples without the other fill views' 0.8-second easing. Dashed ghost circles preserve the smooth volume reference through the relief. A dark cutaway cap is an unmeasured section. Exact values, projection loss, fixed scales, applied relief, stale-source status and source identity remain inspectable. Flat lighting and a matching linear-sRGB legend/grid help distinguish numerical color from shape shading.

**Response lab** now applies the same GPU map to a separate retained **esn-divide simulated parent**. It shows 65 paired boundaries after a single +0.001 state displacement in coordinate 0, with Delta, Control and Perturbed fields, exact coordinate inspection and a full-state separation plot. Both copies receive identical recorded forcing. Its fixed 68% size is a preview: it has no fill measurement, measured seconds or compatible Minime PCA basis. Raw boundary playback is deliberately slowed for inspection. This conditional comparison is separate from live native evidence or an enabled being action; the [direct-shaping proposal](../../proposals/2026-09-07-direct-reservoir-shaping.md) records the scope and owning-repository implementation path.

Read [State surface: mapping and provenance](docs/STATE-SURFACE.md) for the controls, equations, reference limitations, [Response lab](docs/STATE-SURFACE.md#response-lab-watch-a-declared-state-displacement) and reproduction commands. Dedicated checks cover mapping and geometry (30), retained/live data (19), bounded Metal correctness (22), and the separate response evidence (25). These scopes are separate from the earlier 0.4 validation below. Final packaging and performance results belong to their own receipts; the earlier 0.3 GPU comparison does not measure these new views.

## Architecture

- **SwiftUI** owns controls, evidence labels, traces and inspection panels.
- **MetalKit / direct Metal** renders the sphere, spectral indicators and measured trajectory. Geometry uses immutable `MTLBuffer` resources with `.storageModeShared`; camera uniforms are submitted with the draw. CPU ingestion still decodes JSON and copies data into buffers. The PCA basis is fitted offline by the research probe; incoming state vectors are projected onto those fixed axes on the CPU, without fitting a new PCA.
- **FillTransition.swift** applies a bounded 0.8-second quintic ease-in/ease-out curve to the live surface's fill percentage before the cube-root radius mapping. Numbers and annotations keep the latest observation. MetalKit requests 60 frames/second only while a transition is active, then returns to drawing on demand; this is a requested cadence, not a measured frame rate. Fixed fill/reference geometry is cached and invalidated when its scene or reference settings change.
- **FillWatermarks.swift** tracks ordered measured extrema and inclusive recorded prefixes. **ReferenceWatermarksView.swift** draws native labels and guides using the Metal lens's shared projection; a bounded brightness effect leaves values, source times and guide positions unchanged.
- **Evidence.swift** decodes and validates the two bundled datasets. Native rendering does not manufacture activation samples or eigenvectors.
- **LiveTelemetry.swift** optionally reads an existing health file, then waits two seconds before the next read. It caps each read at 2 MiB, retains up to 300 samples, and distinguishes source time from receipt time. It requires source session/sequence/time provenance, rejects backward sequences within a session, and reports stale or unavailable input. This feed updates scalar telemetry and controller displays; with this source selected, state trajectory remains the frozen capture.
- **NativeActionResponse.swift** validates complete native action bundles and computes their input-byte identity. **NativeActionResponseExperience.swift** provides the independent Response source selector, read-only optional file follower, raw application-boundary surface and requested/applied inspector.
- **LiveState.swift** reads the producer's existing bounded activation JSON, then waits two seconds. It validates at most 180 frames × 128 nodes under a 2 MiB read bound, projects each accepted batch through the frozen reference basis, and uses the latest frame's state, fill and stage together. A new batch replaces the displayed path; separate batches are never spliced together. Recorder clocks, continuity limits, stale input and errors remain visible.
- **Profiling.swift** runs a finite offscreen workload through the same renderer and records CPU/GPU timings, workload settings, device metadata and executable/resource hashes. It starts no live reader. See [Profiling](docs/PROFILING.md) for the exact experiment and its limits.

Apple documents the view in [MTKView](https://developer.apple.com/documentation/metalkit/mtkview/) and shared CPU/GPU resource storage in [Choosing a resource storage mode for Apple GPUs](https://developer.apple.com/documentation/metal/choosing-a-resource-storage-mode-for-apple-gpus/). No Core ML model or Neural Engine processing is used. [Core ML compute units](https://developer.apple.com/documentation/coreml/mlcomputeunits) would be relevant only for a future suitable inference workload.

## What each view means

| View | Mapping and evidence boundary |
|---|---|
| Fill | `r/R = (displayed_fill_pct/100)^(1/3)`. The displayed percentage equals reported fill in recorded mode, or eases toward it when live smoothing is enabled. The observed fill comes from EigenFill (with possible runtime policy bias outside stable-core). The configured shelf is 58–72%, with target 68% and reference rails at 74%/78%; stage transitions have hysteresis. These are controller references, not measured subjective comfort or activation-space boundaries. |
| Reference Zones | A close-up of the fill sphere's cut face, uniformly scaled 12× in model coordinates, then fitted to the viewport by an orthographic camera. This is not a fixed pixel-size ratio to the main sphere. It preserves the same cube-root radii and recorded cursor or optional live source. The 54–82% crop is framing, not extra controller limits. Eight selectable source annotations explain the shelf, target, entry/release hysteresis, one-sided PI allowance and rails. A native callout names the selected threshold and points directly to its arc, sharing the Metal view's projection. The 78% force/warning rail is distinguished from the separate 82% forced-drain policy. |
| Spectral indicators | Spoke length encodes the square root of recorded sensory covariance-direction estimates. Source slot order is retained; spoke directions are schematic. These values come from a separate sensory field modified by runtime policy. They do not provide physical mode directions or recurrent-weight spectral radius. |
| State trajectory | Each point projects an actual 128D ESN vector onto three fixed eigenvectors fitted to the saved window's centered covariance. The center remains that window's mean. A unit sphere denotes the maximum **full 128D** distance in that reference window, `3.191930430700554` activation units. Recorded mode shows its 1,024 saved states; Live state & fill shows the latest bounded activation batch. New observations retain this scale, even outside the reference radius. Native coordinate compatibility with the old basis is unverified because the v1 stream supplies no node-layout identity. |
| Controller | The structural PI and generic gate/filter PI are distinct. Observed structural error and integral allow algebraic P/I reconstruction using inspected source constants. This reconstruction is not a logged historical P/I sequence or proof of loaded binary gains; policy adjustments can change the applied drainage. |

Bundled sources remain separate:

- **507 exactly paired telemetry records**, September 6, 2026, 09:09:01–09:28:59 Pacific. Pairing requires identical engine session and timestamp. Historical fill, ESN covariance λ₁, RMS geometry and leak belong to this sequence; historical P/I, gate/filter, stage and controller-mode sequences were not retained.
- **One controller snapshot**, source time September 6, 22:04:46 Pacific. Its internal structural error can precede the snapshot's displayed fill. It is not synchronized with the morning replay.
- **1,024 states × 128 nodes**, captured September 6, 22:11:52 Pacific (`2026-09-07T05:11:52.328Z`). The first three components retain **14.3524%** of centered temporal variance; **85.6476%** is outside the view. Covariance participation ratio is **60.7574**, a description of this captured variation, not a measured memory capacity.

Bundled state rows are ordered oldest-to-newest but have no individual timestamps, session identifier, leak, PI state or weight matrices. Metadata `t_ms` is elapsed processing-loop time at the dump check; a 331 ms source sleep does not establish row cadence. Stable bracketing reads and hashes passed, but independently renamed state/metadata files lack a shared producer generation identifier. The export preserves that consistency limit. Current source inspection does not identify the loaded binary revision.

## Choosing the observation source

The sidebar's **Data source** picker applies across the observation tabs. Switching sources stops the other live reader and pauses recorded playback.

| Source | Fill sphere and Reference Zones | State trajectory | Controller / spectral / leak |
|---|---|---|---|
| **Recorded** | Selected sample from the 507-row historical replay | Separate frozen 1,024-state capture with ordinal playback | Separate controller snapshot; recorded sensory slots and ESN leak are available in their own historical sequence |
| **Live fill & control** | Latest accepted health snapshot | Separate frozen capture | Available health controller values and scalar ESN estimate; no full cascade or leak |
| **Live state & fill** | Fill and recorded stage accompanying the latest activation observation | Latest frame highlighted within the producer's current bounded batch | P/I, full spectral values and leak unavailable; health values are never attached to these states |

The state source is an existing `workspace/runtime/esn_activation_trace_v1.json`, selectable with **Choose state file…**. It holds actual activations plus fill and stage in one publication. Its timestamps identify **recorder observations**, taken after the relevant native updates; they do not authenticate successful-step measurement time or control causality. The file supplies no boot/session identity, node-layout identity, applied leak or controller references. See the [live-state readiness audit](../../analyses/2026-09-06-reservoir-live-state-readiness.md) for the source trace and observed schema.

The reader holds the latest accepted observation until another valid batch arrives. Optional surface easing changes only how the fill render approaches that observation, as described below. Source age over 12 seconds is labeled stale; a source clock more than 5 seconds ahead is reported. Failed reads retain the last accepted batch with an error. Byte-identical batches do not become new observations. Conflicting overlapping frames or reversed wall time are rejected; an engine clock restart with advancing wall time replaces the batch and reports unverified boot identity. No path is drawn between separately received batches.

During final 0.3.1 verification, the initial automatic open of the network-mounted activation file stalled while the app remained responsive. Selecting that same file with **Choose state file…** resolved the delay, after which live recorder times and geometry advanced. The cause was not established. The byte limit is not a wall-clock timeout: a stalled filesystem open can leave the viewer waiting. Read-timeout behavior belongs in the next interactive profiling pass.

The producer's `sample_interval_ms = 1000` is a minimum spacing, and `retained_secs = 180` is nominal: the current source prunes at 180 **frames**. A bounded observation on September 6 Pacific contained 180 frames spanning about 431 seconds. The viewer uses actual recorder clocks. Reads, decoding and projection take additional time beyond the two-second polling delay; it neither promises a 1 Hz stream nor animates every intermediate update.

For a live point, **visible distance²** is its projected squared distance divided by its full squared distance from the frozen reference mean. This describes that point, not variance across a live population. The original **14.3524%** PCA retention describes the reference fit window only. The inspector separately exposes the current full distance, omitted distance and reference-radius ratio; the sphere does not expand to hide drift.

### Live fill transitions

**Smooth fill transitions** defaults to on unless macOS **Reduce Motion** applies, remembers the steward's preference, and applies to either live source in Fill sphere and Reference Zones. The cyan surface eases toward each new fill reading over **0.8 seconds**. A white dashed ring or arc marks the latest observed fill immediately (within the Reference Zones crop); all numeric readouts, chart points, controller terms, recorded stages and distances to thresholds also update directly from that observation. The surface between readings is a presentation effect, not another measurement or a reconstructed control response.

The curve acts on percentage before the cube-root volume mapping and never overshoots its endpoints. A changed target starts from the currently displayed percentage; receiving the same target does not restart the motion. The first reading, a source/file or health-session change, and an observed backward recorder clock snap to the accepted value. Stale, failed or out-of-range-clock input also disables easing and snaps to the retained accepted observation. Turning smoothing off also snaps immediately. **Reduce Motion** is honored by default: the switch shows off, with an explanation. Explicitly turning it on while Reduce Motion is active permits fill motion in this app and remembers that choice; it does not change the Mac's accessibility setting. Turning it off while Reduce Motion is active removes that permission. After reaching the target, the surface stays still until another reading; there is no extrapolation.

Recorded replay and all state-trajectory coordinates remain uninterpolated. The [animation data guide](docs/ANIMATION-DATA.md#how-live-fill-moves-between-readings) gives the exact curve, freshness limits and rendering rules.

Recorded telemetry playback uses the actual saved timestamps and a monotonic elapsed clock at the chosen speed. In recorded replay, the sphere holds observed values between samples; it does not interpolate measurements or integrate the displayed slope. Chart segments connect observations for readability. “Mapping & sources” explains this pipeline inside the app, while the linked [animation data guide](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/native/ReservoirScope/docs/ANIMATION-DATA.md>) preserves the full trace and reproduction commands.

## Build and reproduce

Requires macOS 14+, Swift development tools, and Metal support. From the research repository root:

```sh
native/ReservoirScope/build-app.sh
open "$HOME/.cache/reservoir-research/ReservoirScope-build/current/Reservoir Scope.app"
```

The build script stages sources and existing research JSON on local disk, compiles with Swift, and creates an ad hoc signed application in the path it prints. Set `XDG_CACHE_HOME` to choose another cache root. Local build output avoids SMB resource-fork/signing problems. Source remains in this repository; there is no deployment or live-system step. `Package.swift` also supports opening the project with SwiftPM/Xcode.

Recompute geometry from the retained binary and metadata, with hash verification and no live reads:

```sh
/opt/homebrew/bin/python3.14 probes/reservoir_3d_state_geometry.py --replay visualizations/reservoir-3d/state-geometry.json
/opt/homebrew/bin/python3.14 -m unittest discover -s tests -p 'test_reservoir_3d_state_geometry.py' -v
```

The measured geometry and four focused tests passed; retained-input replay reproduced the result. `probes/reservoir_3d_capture.py --help` documents the separate telemetry exporter, including reuse of a frozen controller snapshot. Rebuild the app after intentionally updating its research datasets. The original raw inputs and hashes remain under `visualizations/reservoir-3d/`.

The live easing checks run with `native/ReservoirScope/check-fill-transition.sh` (17 cases). The bounded offscreen renderer checks run with `native/ReservoirScope/check-fill-renderer.sh` (17 cases, including ten exact cached-versus-fresh pixel comparisons and seven Metal view drawing-mode checks). These use local fixtures and open no windows or live sources. Together with the 42 existing native checks, **76 checks passed** for the earlier 0.4 iteration.

Run the reproducible native decoder/live-feed, reference-contract and playback-clock checks with `native/ReservoirScope/check-evidence.sh` (fixture data only), and the presentation-curve checks with `native/ReservoirScope/check-fill-transition.sh`. Eight Python capture/geometry checks also pass. The [build receipt](build-receipt.json) identifies the verified executable and current validation. The initial native app received actual health snapshots during the read-only runtime check; polling was stopped afterward. First launches of newly compiled executables were unusually slow on this host before opening successfully; no security settings were changed.

## Profiling and remaining source work

The [observer telemetry proposal](../../proposals/2026-09-06-reservoir-observatory-telemetry.md) preserves the codebase needs exposed by this visualization. Existing activation v1 now supplies live observation geometry; the proposal adds successful-step times and identities, effective leak, node-layout identity and precise control references. No live producer was changed.

Run the bounded [renderer profile](docs/PROFILING.md) with `native/ReservoirScope/profile-app.sh --output /tmp/reservoir-profile.json`. For a cross-Mac comparison, copy one complete app unchanged and match executable/resource hashes and workload settings. The offscreen experiment measures serial scene preparation and completed GPU commands; it excludes SwiftUI, presentation, live ingestion, sustained energy use and displayed frame rate. M4 findings require an actual report from that hardware.

The retained **0.3.0** [completed six-run comparison](../../analyses/2026-09-06-reservoir-native-profiling.md) verifies matching binaries, resources, row choices and geometry, and independently recomputes all timings from 720 measured frames. M4 Pro CPU geometry/update medians were lower in these runs; GPU durations varied substantially across its repeats. All runs remain visible, including the initial slower GPU observations. Sampled Metal allocation was about 37.6–37.8 MiB. These measurements support a working native GPU path on that Mac mini, without predicting displayed frame rate or ranking the chips generally.

Version 0.4 reuses fixed fill/reference buffers during surface transitions; this implementation change has not been profiled on the M4. An interactive Instruments session can separately measure idle, camera orbit, scrubbing and live polling, including CPU allocation, input latency and memory/energy behavior. Compare the shared-buffer path with a measured alternative before claiming a unified-memory speedup. Full closed-loop sensitivity requires the derivative of controller state and policy, beyond the sibling harness's Jacobian with recorded controls frozen. Consider Neural Engine execution only after defining and profiling a suitable Core ML inference model; it is not a replacement for Metal rendering or general PCA.

Research scope, finish line and Hold Shelf coordination: [S-002 study](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/research/studies/S-002-reservoir-observatory.md>). Source findings and measured PCA validation: [prior-art note](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/analyses/2026-09-06-reservoir-3d-prior-art.md>).
