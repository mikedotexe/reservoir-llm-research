# Reservoir Scope: M1 Max and M4 Pro rendering profile

Date: September 6, 2026 Pacific. Study: [S-002](../research/studies/S-002-reservoir-observatory.md). Subject: the steward-side native renderer, not the ESN engine or a language model.

## Protocol and follow-up decision

Version 0.3.0 has a finite offscreen benchmark sharing the native renderer’s geometry, shaders, camera and encoder. The [protocol](../native/ReservoirScope/docs/PROFILING.md) specifies 1280×800 physical pixels, 4× MSAA, eight warmups and 30 measured frames per scene, across all four scenes. Source/data hashes and actual row selections must match between machines. Commands are serialized and GPU timestamps are read after completion. Every report retains raw samples, CPU update/encoding times, GPU command duration, serial wall duration, and thermal/power snapshots.

One initial run on each Mac completed. Before further measurements, the follow-up is fixed at **two additional runs on each host**, using the unchanged app, workload and evidence. This checks repeat variability after an initial observation of lower CPU preparation times but higher GPU command durations on the M4 Pro. All three runs will be retained; no fastest-run selection or general chip-speed ranking. The hosts’ other activity is uncontrolled and will not be interrupted. This is a short renderer experiment, not an interactive FPS, latency, sustained load or energy study.

The local host is an M1 Max MacBook Pro with 64 GiB. Mike supplied `volya` for SSH; read-only hardware identification established an M4 Pro Mac mini with 64 GiB and macOS 26.6.2. The already-built arm64 app was copied unchanged to a new `/tmp/reservoir-scope-profile.*` directory there. Only this finite steward-side renderer was executed; no being process, source, database or configuration was changed.

## Results

All six declared runs completed and were retained. The independent comparison
probe verified **720 measured frames**: six runs × four scenes × 30 frames, with
30 valid GPU timestamps in every scene/run. Eight warmup frames per scene remain
excluded from reported distributions. This is three repeated runs per physical
host, not 720 independent hardware experiments.

**The M4 Pro prepared scene geometry faster in every run-wise median, while its
GPU durations varied substantially across the three runs.** For Fill, CPU
update medians were 0.257–0.275 ms on M4 Pro and 0.479–0.526 ms on M1 Max. For
Reference Zones they were 0.435–0.457 ms and 0.705–0.787 ms respectively. Those
CPU-update intervals include geometry creation and shared-buffer allocation;
they do not isolate arithmetic or memory transfer.

The M4 Pro Fill GPU medians were **1.551, 0.394, 0.132 ms**, in acquisition order;
its Reference Zones medians were **1.923, 0.798, 0.180 ms**. M1 Max Fill GPU medians
were **0.109, 0.089, 0.083 ms**. The initial apparent GPU disadvantage therefore
changed considerably in repeats. We cannot assign its cause from these data:
background work, scheduling and driver/cache state were not independently
measured. Neither the initial run nor the fastest later run warrants a general
chip ranking.

### Comparison identity and independent checks

The [comparison probe](../probes/reservoir_native_profile_compare.py) reads only
retained reports. It requires exact agreement of executable identity, both
resource identities, app/build version, report schema, workload settings, scene
order, every measured source-row selection, draw counts, vertex counts and
geometry-buffer sizes. Runtime quantities `pipelineConstructionMs` and
`elapsedRenderingWorkMs` are outcomes, so they are compared as observations rather
than required to match. All other workload fields must match exactly.

It also checks every row against the declared deterministic selection formula,
recomputes count/minimum/median/p95/maximum from raw frames, and verifies those
values against the exported summaries. No cached report median is accepted
without that calculation. Percentiles use linear interpolation at `(n − 1) × p`.
Derived CPU preparation is calculated by adding update and encode times **within
each frame before** computing its quantiles; the full JSON output includes it
and the separate wait-wall distribution.

| Shared artifact | Bytes | SHA-256 |
|---|---:|---|
| ReservoirScope 0.3.0, build 3 | 2,055,184 | `3c69bff57a745fc1e06c6dfd64c4bf3ae1eb1905d67648f08a455590e97588a2` |
| data.json | 186,596 | `03ebfb620c2371023a39de308eb16c292d31b313ead7dcb07db5df3dd0c6749d` |
| state-geometry.json | 365,219 | `5e90207e7dfd1d395b249d3bb5d668afa0f86b6d3e0e6383eda7b9eb52514317` |

The measured app is **0.3.0**. A subsequent **0.3.1 viewer revision clarifies
interface/error labels**, including the frozen reference radius and undefined
zero-distance fraction. The renderer and profiling implementation were unchanged
in that refinement. These are measurements of the retained 0.3.0 binary, not
measurements attributed to a different executable hash. The
[build receipt](../native/ReservoirScope/build-receipt.json) distinguishes the
current viewer from this benchmark identity. No new performance runs are needed
to interpret a label-only change.

| Scene | Draws | Vertices | Geometry-buffer bytes |
|---|---:|---:|---:|
| Fill | 23 | 21,120 | 1,013,760 |
| Reference Zones | 25 | 24,112 | 1,157,376 |
| State trajectory | 18 | 4,522 | 217,056 |
| Spectral | 21 | 8,296 | 398,208 |

These counts match every measured frame of the corresponding scene in all six
reports. The same 507-record and 1,024-state captures supply the same 30 measured
row pairs. This establishes workload comparability; it does not establish equal
background load or equal OS scheduling.

### Every run, retained in acquisition order within each host

Verified 6 reports and 720 measured frames.

All times below are **milliseconds, median / p95**, recalculated from each run's 30 raw frames per scene.

| Report | Scene | CPU geometry/update | CPU encode/submit | GPU command | Serial wall |
|---|---|---:|---:|---:|---:|
| m1-max.json | fill | 0.526 / 2.327 | 0.049 / 0.104 | 0.109 / 1.392 | 1.236 / 3.559 |
| m1-max.json | zones | 0.705 / 2.264 | 0.035 / 0.079 | 0.094 / 0.882 | 1.623 / 3.192 |
| m1-max.json | trajectory | 0.234 / 0.949 | 0.045 / 0.108 | 0.206 / 0.883 | 1.101 / 3.136 |
| m1-max.json | spectral | 0.257 / 0.493 | 0.030 / 0.062 | 0.070 / 1.225 | 0.650 / 2.426 |
| m1-max-run2.json | fill | 0.479 / 1.088 | 0.033 / 0.062 | 0.089 / 0.517 | 1.118 / 2.424 |
| m1-max-run2.json | zones | 0.787 / 2.351 | 0.055 / 0.273 | 0.128 / 1.202 | 2.024 / 4.377 |
| m1-max-run2.json | trajectory | 0.192 / 0.452 | 0.036 / 0.065 | 0.177 / 0.431 | 0.806 / 2.709 |
| m1-max-run2.json | spectral | 0.294 / 1.488 | 0.035 / 0.083 | 0.066 / 0.426 | 0.839 / 2.504 |
| m1-max-run3.json | fill | 0.526 / 2.570 | 0.049 / 0.095 | 0.083 / 0.725 | 1.222 / 5.001 |
| m1-max-run3.json | zones | 0.742 / 2.981 | 0.034 / 0.086 | 0.091 / 0.505 | 1.716 / 3.401 |
| m1-max-run3.json | trajectory | 0.205 / 0.330 | 0.035 / 0.067 | 0.213 / 1.265 | 1.216 / 2.697 |
| m1-max-run3.json | spectral | 0.290 / 0.774 | 0.031 / 0.084 | 0.091 / 1.279 | 0.927 / 2.997 |
| m4-pro.json | fill | 0.275 / 0.309 | 0.032 / 0.063 | 1.551 / 4.305 | 1.984 / 4.855 |
| m4-pro.json | zones | 0.457 / 0.510 | 0.031 / 0.051 | 1.923 / 5.405 | 2.715 / 6.141 |
| m4-pro.json | trajectory | 0.111 / 0.145 | 0.017 / 0.032 | 0.794 / 3.313 | 1.100 / 3.595 |
| m4-pro.json | spectral | 0.159 / 0.203 | 0.019 / 0.039 | 1.290 / 2.929 | 1.614 / 3.241 |
| m4-pro-run2.json | fill | 0.270 / 0.346 | 0.021 / 0.043 | 0.394 / 2.206 | 0.886 / 2.713 |
| m4-pro-run2.json | zones | 0.453 / 0.555 | 0.028 / 0.077 | 0.798 / 2.101 | 1.597 / 2.790 |
| m4-pro-run2.json | trajectory | 0.117 / 0.150 | 0.016 / 0.041 | 0.671 / 2.011 | 0.952 / 2.309 |
| m4-pro-run2.json | spectral | 0.169 / 0.207 | 0.018 / 0.039 | 0.423 / 1.473 | 0.747 / 1.820 |
| m4-pro-run3.json | fill | 0.257 / 0.301 | 0.012 / 0.020 | 0.132 / 0.201 | 0.559 / 0.653 |
| m4-pro-run3.json | zones | 0.435 / 0.455 | 0.013 / 0.018 | 0.180 / 0.222 | 0.760 / 0.831 |
| m4-pro-run3.json | trajectory | 0.102 / 0.114 | 0.010 / 0.012 | 0.189 / 0.294 | 0.427 / 0.555 |
| m4-pro-run3.json | spectral | 0.146 / 0.173 | 0.011 / 0.016 | 0.056 / 0.179 | 0.344 / 0.484 |

| Report | Thermal before → after | Low power before → after | Peak sampled Metal MiB | Pipeline construction ms | Rendering work ms |
|---|---|---|---:|---:|---:|
| m1-max.json | fair → fair | False → False | 37.6094 | 324.175 | 234.250 |
| m1-max-run2.json | fair → fair | False → False | 37.6094 | 4.437 | 249.806 |
| m1-max-run3.json | fair → fair | False → False | 37.6094 | 45.221 | 268.115 |
| m4-pro.json | nominal → nominal | False → False | 37.7500 | 175.055 | 347.368 |
| m4-pro-run2.json | nominal → nominal | False → False | 37.7500 | 2.127 | 192.436 |
| m4-pro-run3.json | nominal → nominal | False → False | 37.7500 | 1.683 | 86.508 |

The memory column is the largest sampled **Metal resource allocation** from the
benchmark's device object, not total app memory, system pressure or a continuous
allocation peak. M1 Max used 39,436,288 bytes (37.6094 MiB) and M4 Pro used
39,583,744 bytes (37.7500 MiB), identically within each host's three reports.
End-of-run allocations were 38,584,320 and 38,731,776 bytes respectively. These
reports do not measure memory bandwidth or prove a zero-copy pipeline.

Both hosts reported 64 GiB physical memory, unified memory, and macOS 26.6.2
build 25G83. Before/after thermal snapshots were **fair** on the M1 Max and
**nominal** on the M4 Pro, with low-power mode disabled throughout the snapshots.
These coarse readings are relevant context, not a control for all host activity.
No clock rates, competing workloads or sustained power were recorded.

Pipeline construction is reported separately and excluded from frame timings.
It varied from 4.437 to 324.175 ms on M1 Max and 1.683 to 175.055 ms on M4 Pro.
This is not a cold-start measurement: process launch and prior driver/cache state
are not controlled. The rendering-work interval includes warmup and measured
loops plus their surrounding work, so it is not the sum of only measured frame
medians.

### What this resolves and the next useful measurement

The same packaged native graphics workload successfully ran on the actual
**M4 Pro Mac mini**, with valid completed GPU timings and small bounded resource
allocation. This establishes a working GPU path on the intended class of machine
and a reproducible baseline. The tested model is M4 **Pro**; these data say
nothing quantitative about a base M4 Mac mini or Neural Engine execution.

Reference Zones has the highest CPU-update median of the four scenes on both
hosts in all three runs. Source inspection shows
[`ReservoirRenderer.update`](../native/ReservoirScope/Sources/ReservoirScope/ReservoirScene.swift)
rebuilds all scene buffers whenever the scene state changes, including fixed
reference arcs and shells. A concrete optimization candidate is to retain those
fixed meshes and update only the observed fill/selection geometry. Its benefit
has not been measured; the stable geometry-update contribution makes it a more
specific experiment than attributing the variable GPU times to a shader defect.

Before changing rendering architecture, the distinct next observation is an
interactive profile of the real window while following live activations:
separate file decode/projection, SwiftUI updates, mesh rebuilds, presentation and
input response. The current offscreen pass excludes all live ingestion and
SwiftUI/display work. A controlled mesh-caching comparison could then use this
same finite workload, unchanged data and visual checks, retaining all declared
runs. No optimization or Neural Engine migration is justified solely by these
short offscreen timings.

This study makes **no displayed-FPS, input-latency, energy, memory-bandwidth,
sustained-throughput, reservoir-engine-speed or general chip-speed claim**.
Per-run p95 is descriptive of 30 serial commands. It is neither a confidence
interval nor a guaranteed tail latency in the live viewer. Three host runs and
uncontrolled background activity do not support a narrow statistical hardware
comparison.

## Reproduce from the retained evidence

From the research repository root:

```sh
python3 probes/reservoir_native_profile_compare.py --markdown
python3 probes/reservoir_native_profile_compare.py
```

The first command prints the run-wise tables above. The second prints complete
JSON with comparison identity, report hashes, environments, all recomputed
metric distributions and per-run source times. Both are read-only; no profiling,
SSH, live telemetry read or database query is performed. Explicit report paths
can be supplied for a separately labeled comparison. Any comparison mismatch or
invalid summary fails rather than producing a table.

The audit also checked known quantile examples (`[0, 10] → p95 9.5`;
`[1, 3, 9] → median 3`) and six altered in-memory reports. Changed executable
hash, width, measured row, geometry count, exported p95 and missing GPU timing
were each rejected. Source files and the six original reports were unchanged
by these checks.

| Retained report | UTC start | SHA-256 |
|---|---|---|
| [m1-max.json](../research/outputs/2026-09-06-native-profiling/m1-max.json) | 2026-09-07T06:09:24Z | `04dea996793866dfa9b86b7f774cb1e6cdeeed9bceb322b05e1f31cf7b5bd305` |
| [m1-max-run2.json](../research/outputs/2026-09-06-native-profiling/m1-max-run2.json) | 2026-09-07T06:14:43Z | `95ea30799f8eef7bf6df598f140efda82b3523eadc2e6d34fe0a90ec0a69dd4b` |
| [m1-max-run3.json](../research/outputs/2026-09-06-native-profiling/m1-max-run3.json) | 2026-09-07T06:15:11Z | `b8193db36a32f20e1e2ea958b8c00f79fd268166f1f0e327d429d970f91fd72e` |
| [m4-pro.json](../research/outputs/2026-09-06-native-profiling/m4-pro.json) | 2026-09-07T06:11:22Z | `94f06cbf0a8e9321360d1b9233dcda4d6369f65ba3f39b314c1f656ce0e2a6da` |
| [m4-pro-run2.json](../research/outputs/2026-09-06-native-profiling/m4-pro-run2.json) | 2026-09-07T06:14:43Z | `3f37c8cae59ce9638594d2b10793414ec6bf06974850d9f2721a5783180eb88e` |
| [m4-pro-run3.json](../research/outputs/2026-09-06-native-profiling/m4-pro-run3.json) | 2026-09-07T06:15:11Z | `1a32aeab77428b03778c9df81538ebb2d8fea1b81473a19362e826da4a415ade` |

## Board coordination

The parent observatory task owns the session's S-002/Hold Shelf result update.
This independent comparison made no board writes. Attach this analysis and the
six retained reports, preserving the distinction between the completed renderer
experiment, live observation geometry, and the proposed exact producer timing.
