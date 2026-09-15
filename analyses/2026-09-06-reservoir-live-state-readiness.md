# Live state geometry: what can be observed now

September 6, 2026, Pacific; bounded observation at September 7, 06:00:57 UTC.
Study: [S-002](../research/studies/S-002-reservoir-observatory.md).
Subject: Minime's native 128-node ESN. This is a read-only source/file audit;
no sibling code, runtime settings, database, or live process was changed.

**A real, recent per-node stream already exists.** The native viewer can read it
and project its observations onto the existing frozen PCA basis now. Its frames
also carry fill and regulator stage from the same recorder call, enabling one
observation cursor across these channels. However, these are recorder observation
times, not authenticated state-update times. Exact state/leak/controller causal
synchronization still requires the [observer publication proposal](../proposals/2026-09-06-reservoir-observatory-telemetry.md).

This qualifies the earlier broad description of missing live state geometry:
the capacity dump lacks per-row clocks, but an independent activation recorder
provides timestamped observations. Neither source supplies the proposed precise
step identity, effective leak, node-layout identity, or consumed-control reference.

## Available file and one bounded observation

The source resolves `workspace/runtime/esn_activation_trace_v1.json`
([orchestration.rs:256](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:256>)).
The file was present at
`/Volumes/M3 Volya._smb._tcp.local/other/minime/workspace/runtime/esn_activation_trace_v1.json`.
One read was bounded to 2 MiB; no active database scan was needed.

| Observation | Result |
|---|---|
| Read completed | 2026-09-07 06:00:57.861136 UTC |
| File bytes | 583,148 |
| SHA-256 | `f47fe52819ae40147c38f433bbbc1fc4158ca9f95d7aa3d145c0051d11c0a43e` |
| Envelope policy | `esn_activation_trace_v1` |
| Frames × coordinates | 180 × 128 |
| Recorder wall-clock range | 2026-09-07 05:53:46.494–06:00:57.246 UTC |
| Recorder engine-clock range | 554,533,381–554,964,139 ms |
| Actual engine-clock span | 430.758 seconds |
| Consecutive intervals, n = 179 | Median 2,367 ms; minimum 2,352 ms; maximum 3,197 ms |
| Consecutive wall-clock intervals, n = 179 | Minimum 2,352 ms; maximum 3,196 ms |
| Timestamp order | Both clocks strictly increasing in this file |
| Coordinate validity | All 23,040 exported coordinates finite; all 180 `finite_fraction` values equal 1 |
| Recorded stages | `elevated`, `hold` |
| Last co-published fill | 71.040886% |
| Last state RMS | 0.40191808, source summary |

This is one current-file observation, not a claim about uptime or all past
frames. The raw live file was not copied into the research record during this
audit; the summary and its hash preserve the inspected identity but cannot
reconstruct all vectors. A later file read will naturally return a later window.

## Existing v1 schema and what its clocks mean

The envelope and frame are declared at
[activation_trace.rs:43](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/activation_trace.rs:43>).

| Field | Source meaning and consumer treatment |
|---|---|
| `policy` | Format discriminator, currently `esn_activation_trace_v1`; reject unsupported policies. |
| `updated_at_unix_ms` | Wall time passed to the last retained recorder sample; **not** a timestamp taken after publication completes. |
| `reservoir_dim` | Last sampled vector length. Validate every frame length against this and the selected projection basis. |
| `sample_interval_ms` | Configured minimum spacing, 1,000 ms; not an observed 1 Hz rate. |
| `retained_secs` | Constant 180. Source prunes by frame count only; not an enforced 180-second window. The observed window was about 431 seconds. |
| `frames[]` | Oldest-to-newest insertion order, at most 180 retained frames. |
| `frames[].t_ms` | `start.elapsed().as_millis()` at the recorder call; engine-relative observation time, integer milliseconds. No session identifier accompanies it. |
| `frames[].wall_clock_unix_ms` | Wall clock sampled immediately before the recorder call. This and `t_ms` are nearby clock reads, not one atomic clock measurement. |
| `frames[].activations` | Copy of `esn.x` available at observation; array order is native index order. Non-finite coordinates are replaced by zero before serialization. |
| `frames[].fill_pct` | Current `eigenfill_pct` passed alongside the state, a sensory-field estimator. It is not a quantity computed from the 128 coordinates. |
| `frames[].stage` | Lowercase debug name of `stable_core_stage` at that recorder call. It is a recorded stage, not a stage reconstructed by the viewer. |
| `frames[].geom_rel`, `lambda1_rel` | Latest scalar values passed by orchestration. There are no separate scalar measurement identities or ages. |
| `frames[].summary` | `mean`, `abs_mean`, `rms`, `min`, `max`, `saturation_fraction`, `positive_fraction`, `finite_fraction`, computed from original finite coordinates. |
| `frames[].top_active_node_indexes` | Up to eight native indexes sorted by absolute sanitized activation, descending; ties use index order. These are active coordinates, not eigenmodes. |

The recorder checks the minimum interval before cloning, keeps a bounded deque,
serializes a snapshot, writes one temporary JSON file and renames it over the
published path ([activation_trace.rs:92](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/activation_trace.rs:92>),
[activation_trace.rs:135](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/activation_trace.rs:135>)).
The single publication binds its metadata and all retained vectors together.
It has no batch generation, frame sequence, boot/session identity, checksum,
success/drop counters, or runtime build identity. An atomic rename supports
complete-file observation; it does not add these absent identities.

## Why observation alignment is possible but exact step alignment is not

The successful native update occurs earlier during batch processing
([orchestration.rs:1411](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:1411>)).
Each successful update appends `esn.x` to the separate capacity ring at line 1436.
The activation recorder is later in the history-fire branch, entered through
`fired[2]` at line 2030, and called at
[orchestration.rs:3203](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:3203>).
Its rate is therefore limited by when that path runs as well as the 1,000 ms
minimum. There may have been multiple updates, or no new successful update,
before an observation. The file does not distinguish these cases.

Between the native update and the recorder, the structural PI consumes prior
`last_fill_pct` at
[orchestration.rs:2198](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2198>);
the sensory EigenFill estimate is formed later (line 2553), and stage selection
can change using it (line 2607). Consequently a co-published state, fill, and
stage describe what the recorder could observe together. They do not establish
which controller command produced that native state. The separate health
snapshot receives its own sequence and later clock readings at
[orchestration.rs:4410](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:4410>).
No exact join from an activation frame to that health sequence is published.

The effective leak used by an update is available internally in
`esn.last_step_trace().leak`, assigned from the applied coefficient at
[esn.rs:2145](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/esn.rs:2145>).
It is absent from activation v1. The historical `get_leak()` value is
`leak_live` ([esn.rs:2296](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/esn.rs:2296>));
it is not a universal substitute for an effective step coefficient when an
override or forced shadow value applies. The native state itself is integrated,
noise-adjusted and clipped at lines 2108–2152 before this later observation.

The existing capacity export remains a different source: 1,024 successful-step
vectors, no per-row clocks, independently renamed binary and metadata
([orchestration.rs:5791](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:5791>)).
Its metadata generation cannot be bound to the vectors by a producer hash.
Do not infer activation-v1 timestamps for capacity rows by matching row order.

## Precise contract for the native consumer now

The supported claim is **“recent activation observations, projected onto a fixed
reference basis; fill and stage observed by the same recorder.”** A suitable
clock label is **“recorder observation time.”** “Synchronized” must be qualified
as observation alignment, not successful-step/control synchronization.

1. Open only the selected file for reading, with an explicit byte bound and
   bounded poll frequency. Decode the whole envelope before replacing the last
   accepted view. Preserve last accepted evidence with an error/stale label
   when the next read fails; never manufacture a fresh state from a poll time.
2. Require the supported policy, a nonempty bounded frame list, matching
   dimensions, finite coordinates/scalars, supported fill range, plausible
   source clocks, and strictly increasing frame clocks. Require
   `summary.finite_fraction == 1` for unqualified vector geometry: v1 otherwise
   cannot identify which exported zeros replace invalid coordinates. Treat
   unknown stage strings as recorded but uninterpreted, not as a known stage.
3. Deduplicate identical observations. Byte hash, last-frame clock pair and
   overlapping frame content can expose unchanged/revised files; these are
   client checks, not authenticated producer sequence numbers. Report backward
   clocks, conflicting overlap, changed dimensions and inferred discontinuities.
   An observed new run must not silently extend the old trajectory. A restart
   may be detectable; continuity across every unseen restart is not provable.
4. Keep vector, co-published fill and stage on one selected activation frame.
   Display health P/I as separately timed evidence if it is shown. Do not attach
   its latest values to an old activation cursor or calculate controller history
   from the reference-zone defaults.
5. Project `x` as `score[k] = dot(component[k], x - referenceMean)` using the
   saved 128-dimensional mean and three 128-dimensional orthonormal components.
   Keep the basis frozen. The existing capture's reference radius is
   3.191930430700554 activation units, an empirical window envelope. Its original
   14.3524% retained variance describes the fit window only.
6. For each new vector calculate full centered norm, projected norm and residual
   norm, `sqrt(max(0, fullNorm² - projectedNorm²))`, with a numerical tolerance
   that also detects invalid basis geometry. Show out-of-reference distance and
   projection loss. Do not clip new states into the sphere or continually rescale
   the basis to hide drift. Equal dimension does not establish node-layout or
   weight-instance continuity; v1 lacks evidence to authenticate that assumption.
7. Hold each observation until the next source-time cursor. Any interpolated
   trail/transition would be a separately labeled display effect, not measured
   intermediate state. Native ESN leak is not drainage and remains unavailable
   for this source.

The smallest producer follow-on is still the proposed v2 immutable measurement
header captured at each selected successful update: boot/session/node layout,
step identity, actual state time, effective leak and explicit references to
independently measured control/sensory records. This audit did not implement or
enable that follow-on.

## Reproduction and source identity

The following read-only query reproduces the bounded observation summary on the
then-current file. Run from the research repository. It does not reproduce the
same window after the producer has replaced it.

```python
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math, statistics

path = Path("../minime/workspace/runtime/esn_activation_trace_v1.json")
with path.open("rb") as stream:
    raw = stream.read(2 * 1024 * 1024 + 1)
assert len(raw) <= 2 * 1024 * 1024, "read bound exceeded"
trace = json.loads(raw)
frames = trace["frames"]
intervals = [b["t_ms"] - a["t_ms"] for a, b in zip(frames, frames[1:])]
wall_intervals = [b["wall_clock_unix_ms"] - a["wall_clock_unix_ms"]
                  for a, b in zip(frames, frames[1:])]
def utc(frame):
    return datetime.fromtimestamp(frame["wall_clock_unix_ms"] / 1000,
                                  timezone.utc).isoformat()
print(json.dumps({
    "observed_at_utc": datetime.now(timezone.utc).isoformat(),
    "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
    "envelope": {k: v for k, v in trace.items() if k != "frames"},
    "frame_count": len(frames), "frame_keys": sorted(frames[0]),
    "dimensions": sorted({len(f["activations"]) for f in frames}),
    "wall_range_utc": [utc(frames[0]), utc(frames[-1])],
    "engine_range_ms": [frames[0]["t_ms"], frames[-1]["t_ms"]],
    "interval_range_ms": [min(intervals), max(intervals)],
    "median_interval_ms": statistics.median(intervals),
    "wall_interval_range_ms": [min(wall_intervals), max(wall_intervals)],
    "engine_increasing": all(d > 0 for d in intervals),
    "wall_increasing": all(d > 0 for d in wall_intervals),
    "all_coordinates_finite": all(math.isfinite(v) for f in frames
                                   for v in f["activations"]),
    "finite_fraction_range": [min(f["summary"]["finite_fraction"] for f in frames),
                               max(f["summary"]["finite_fraction"] for f in frames)],
    "stages": sorted({f["stage"] for f in frames}),
    "last_fill": frames[-1]["fill_pct"], "last_summary": frames[-1]["summary"]
}, indent=2))
```

Current source-file hashes were read separately. These identify reviewed files,
not the binary that produced the live JSON:

| Reviewed file | SHA-256 |
|---|---|
| `../minime/minime/src/activation_trace.rs` | `d8fd920b60445df2d5f9ad70ed48cbef0ab5f4dae2d4e34124f8945edd4f2288` |
| `../minime/minime/src/runtime/orchestration.rs` | `af2ec480922a7c277fcb39b6c55ee5900dd11fb49c696cdc20e8aeae10b003b4` |
| `../minime/minime/src/esn.rs` | `98e8fe727e9908e8939d5317d23e954425748edb45b2a737e5624a42166dfe92` |
| `visualizations/reservoir-3d/state-geometry.json` | `5e90207e7dfd1d395b249d3bb5d668afa0f86b6d3e0e6383eda7b9eb52514317` |

## Board updates pending

Attach this audit to S-002's observatory work card: existing activation v1 can
support moving per-node observations and co-published fill/stage now; exact
state-step, effective-leak and controller synchronization remains a producer
proposal. Record the observation window and link this analysis. No board write
was made by this bounded audit; the parent task owns the session's board update.
