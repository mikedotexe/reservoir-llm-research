# Measuring the native renderer

The viewer includes a small, repeatable offscreen profile. It renders the **same
four scenes, with the same geometry, Metal shaders, and camera transforms** as the
native window. It measures CPU work and completed GPU commands separately. It
does not connect to telemetry or change a running reservoir.

This experiment asks: **How much work does each current scene require at a fixed
pixel size on the tested Mac?** It does not estimate the speed of the reservoir
engine, a language model, or the Neural Engine.

## Run it

From this repository:

```sh
native/ReservoirScope/profile-app.sh --output /tmp/reservoir-profile.json
```

This builds the current viewer locally, runs the finite profile, and saves JSON.
The report also goes to standard output. To profile an already built app without
changing it:

```sh
native/ReservoirScope/profile-app.sh \
  --app "$HOME/.cache/reservoir-research/ReservoirScope-build/current/Reservoir Scope.app" \
  --output /tmp/reservoir-profile.json
```

An unchanged app bundle can be copied to another compatible Apple silicon Mac.
The executable can run without the repository or a visible window:

```sh
"/path/Reservoir Scope.app/Contents/MacOS/ReservoirScope" \
  --profile --profile-output /tmp/reservoir-profile.json
```

The app's normal launch still opens the native viewer. `--profile` takes an early
entry path before SwiftUI starts and exits when the report completes. No live
reader is started, and it does not discover or contact another computer.

## Fixed workload

The default is **1280 × 800 physical pixels**, with 4× multisample antialiasing if
the device supports it (otherwise 1×, recorded in the report). Each of Fill sphere,
Reference zones, State trajectory, and Spectral magnitudes receives **8 warmup
frames and 30 measured frames**: 152 completed commands altogether. Targets are
allocated once and reused. Rendering stops with an error if its in-process work
exceeds 20 seconds or the host reports serious or critical thermal pressure.
This ceiling begins after evidence loading, pipeline construction, and target
allocation; it does not bound operating-system launch delays. A GPU command
already submitted is waited on before continuing.

Each measured sequence spans the full bundled capture using
`floor(ordinal × (sampleCount − 1) / (frameCount − 1))`. The frozen telemetry capture
and frozen state capture retain their separate identity: the profile does not
pretend they were simultaneous. Fill, spectral slots, and selected PCA rows come
from recorded data; no simulated reservoir updates or invented activations are
introduced. The whole captured PCA trajectory is supplied to the renderer.

The camera remains at its native initial pose. Fill uses its cutaway and reference
bands; the zones lens selects the configured target. The report includes every
measured row index, draw count, vertex count, and geometry-buffer byte count.
Warmups use the same selection rule in a separate sequence and are excluded from
distributions.

Optional `--width`, `--height`, `--warmups`, and `--frames` arguments to the script
change the workload. Their direct executable equivalents begin `--profile-`.
Limits are 320–2560 pixels wide, 240–1600 high, 0–20 warmups and 1–120 measurements
per scene. Change these only for a separately labeled experiment; compare reports
with identical settings.

## What the times mean

| Field | Includes | Excludes |
|---|---|---|
| `cpuUpdateMs` | Scene comparison, rebuilding geometry, creating its immutable shared Metal buffers | Evidence decoding, state projection before this benchmark, UI layout |
| `cpuEncodeSubmitMs` | Creating and labeling a command buffer, encoding the shared renderer's draws, committing | Waiting for GPU completion |
| `gpuCommandMs` | Completed command-buffer GPU end time minus start time; includes the render pass and multisample resolve | CPU preparation, display presentation and compositing |
| `waitWallMs` | Host time from commit return through `waitUntilCompleted` return | Geometry generation and encoding |
| `serialFrameWallMs` | Host time from scene update through completed GPU command | Evidence loading, pipeline and target setup, SwiftUI and window work |

GPU timestamps are read **after completion**, as required by Apple's
[command-buffer timing documentation](https://developer.apple.com/documentation/metal/mtlcommandbuffer/gpustarttime).
If they are zero or unavailable, that GPU observation remains absent; the report's
GPU sample count exposes the missing measurements. CPU and wall intervals use the
monotonic process uptime clock. The report keeps raw observations and summarizes
count, minimum, median, p95 and maximum. Percentiles use linear interpolation at
`(n − 1) × p`; p95 describes these 30 frames, not a guaranteed service level.

Only one command is in flight. Waiting deliberately makes each observation
attributable to its selected scene. These are **serial rendering costs**, not a
measurement of pipelined frame throughput or a prediction of displayed FPS.
Shader/pipeline construction is recorded separately and may benefit from driver
caches; it is not an app cold-start measure.

## Comparison and provenance

Every successful report includes SHA-256 hashes and sizes for the executable,
`data.json`, and `state-geometry.json`. For the closest cross-Mac comparison, copy
one complete built app unchanged and require these hashes plus workload version,
dimensions, sample count, and row sequences to match. Rebuilding separately may
change the executable even from identical source.

The script can also record hashes of the local Swift source files. These describe
the source directory present at measurement time; when `--app` selects an
arbitrary prebuilt bundle, they are **not proof** of which source produced it.
The executable and resource hashes are the comparison identity.

Device name, hardware model, OS version, physical memory, processor counts,
unified-memory capability, and before/after thermal and low-power states accompany
the timings. Reports omit serial numbers, hostnames and device registry IDs.
Other host activity is uncontrolled, so a short difference is evidence about
these runs and this workload, not the chips' general relative speed. Preserve
individual reports if a later repeat is warranted; do not select only the fastest.

## Memory and the Neural Engine

The renderer uploads geometry through immutable `.storageModeShared` buffers.
Apple silicon allows CPU and GPU access to the same system-memory resource;
creating a buffer with `makeBuffer(bytes:)` still copies the CPU-side vertex array.
The offscreen color and depth targets use private storage, accessible to the GPU.
These choices follow Apple's [resource storage guidance for Apple GPUs](https://developer.apple.com/documentation/metal/choosing-a-resource-storage-mode-for-apple-gpus).

`hasUnifiedMemory` records the device's reported
[shared memory architecture](https://developer.apple.com/documentation/metal/mtldevice/hasunifiedmemory).
`currentAllocatedSize` is sampled from this Metal device object before setup,
after target allocation, and after frames. Its largest sampled value is resource
allocation, not total application memory, measured bandwidth, or system pressure.
The report does not claim that memory use is zero-copy throughout the app.

No Core ML or Neural Engine work runs in this experiment. Neural Engine support
would require a suitable inference workload and a separate measurement. This
viewer currently uses the CPU for geometry and Metal for graphics.

## Implementation and limits

- [Profiling.swift](../Sources/ReservoirScope/Profiling.swift) owns workload selection,
  offscreen targets, clocks, bounds, hashes and the JSON report.
- [ReservoirScene.swift](../Sources/ReservoirScope/ReservoirScene.swift) owns the
  geometry, shaders and shared `encodeScene` path used by the window and profile.
- [profile-app.sh](../profile-app.sh) provides build-or-reuse invocation.

The offscreen pass is useful for attributing rendering costs. The next distinct
measurement would be an interactive Instruments session on a representative Mac,
including SwiftUI layout, actual window size and backing scale, presentation,
input response, and sustained resource use. This profile alone cannot establish
those properties or energy use.
