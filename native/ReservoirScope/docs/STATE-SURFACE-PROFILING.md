# State surface: fixed offscreen comparison protocol

Protocol written September 7, 2026, before running the new workload. This extends
the earlier native profiling experiment; its results are a separate workload.

Use the same signed native application executable and resource bytes on the local
Mac and `volya`. Run `--profile-surface --profile-output <result.json>` with
`--profile-source-directory <staged Sources/ReservoirScope>` when staged source is
available. Do not compare different executable, source, atlas or capture hashes.
The output retains each measured frame, not just summaries.

Retain **three consecutive runs on each host**, numbered 1, 2 and 3. Keep the
first completed run; do not select the fastest run or replace a slow completed
run. Finish one host's three runs before starting the other host's sequence, so
no two profiling jobs overlap. Use the final fixed application binary for all
six reports. Name reports `m1-max-run1.json`, `m1-max-run2.json`,
`m1-max-run3.json`, `m4-pro-run1.json`, `m4-pro-run2.json`, and
`m4-pro-run3.json`. Host background activity remains uncontrolled; run order
and host are not randomized. A failed/incomplete attempt is recorded separately
with its reason and is not silently treated as a completed measurement.

The independent comparison probe, `probes/reservoir_state_surface_profile_compare.py`,
requires all six reports, verifies their executable/source/resource hashes,
workload and mesh records, and recomputes each run's median and interpolated p95
from raw measured frames. Run medians remain separate, including the first run.
The six-run report is descriptive; it does not pool frames as independent host
replicates. Supply `--output-prefix <research path>` to retain JSON and Markdown
results. Input file SHA-256 hashes are included in the comparison receipt.

The subject is the actual `StateSurfaceRenderer`, using the original 1,024 × 128
retained activation capture and fixed atlas `index-fibonacci-128-v1`. The three
cases are signed activation color with zero relief; signed activation color with
0.14 requested relief; and the latter with the defined back-half cutaway/cap.
All cases use **68 percent preview fill**, a chosen render parameter. The retained
state capture has no paired fill or row timestamps. Its ordinal rows are never
interpreted as a sampling interval or synchronized with historical fill.

Each case renders 8 warmup rows and then 30 measured rows at 1280 × 800 pixels.
Each phase independently selects `floor(i × (1024 − 1)/(n − 1))`, including both
capture endpoints. Use 4× MSAA if supported and record the actual sample count;
different sample counts are different workloads. The camera remains at its default,
exact sites are visible and selected coordinate is fixed at index zero. The fixed
color scale is −1…1. No playback smoothing or live reader is active.

One command buffer is submitted and completed before the next observation update.
Record CPU update, CPU encode-and-submit, completion-wait wall time, total serial
frame wall time, and valid post-completion GPU command timestamps separately.
Pipeline/atlas construction, evidence decoding and target creation are outside
the measured frame intervals, with construction duration retained separately.
Record per-frame actual relief, volume error, buffer bytes and vertex count.
The rendering portion has a 45-second ceiling and rejects serious/critical thermal
pressure; an incomplete run produces no completed report.

Record executable, available Swift source and four evidence resource hashes,
device name, hardware/CPU model, OS, low-power/thermal snapshots, physical/unified
memory properties and sampled Metal resource allocation. No window is presented.
Source/resource/executable hashes are checked before and after the workload; a
change rejects the report. The rendering deadline is checked between commands
and after each completion; it is not a driver-level GPU timeout.
These serial offscreen durations do not establish display FPS, interactive input
latency, compositor cost, power/energy, Neural Engine use, memory bandwidth or a
general hardware ranking. Host background work remains uncontrolled.

Before profiling, `check-state-surface-renderer.sh` runs GPU field checks against
the CPU atlas for constant, one-coordinate, opposed-coordinate and selected
retained vectors. Its explicit tolerance is 3e-6 activation units for Float32
GPU accumulation versus the CPU reference. It also checks deterministic offscreen
frames, meaningful color/relief/cutaway differences, picking and idle updates.
These are correctness tests, not timing samples.
