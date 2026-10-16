# Activation resource audit — 2026-10-16

The first pilot stopped on a resource refusal. Its retained evidence does not
establish an owned-worker leak or identify what caused the pressure change. The
new prospective comparison retains the same Rust admission thresholds and adds a
bounded preparation observation before each arm. No old attempt is reopened.

## Retained observations

Source: `research/outputs/activation-0.26.0-20261015/pilot-01/`.

| Condition | Admission | Retained outcome |
| --- | --- | --- |
| Decaying trace | Pressure 1, reported free percentage 36 | Six complete journals, step 121, process return code 0 |
| No steering | Pressure 2, reported free percentage 32 | Refused before worker creation, step 0, process return code 1 |
| Recurrent | No attempt | Stopped after the refusal |

The trace admission file is
`condition-1/activation-1792119989350565000/admission-1792119989435615000.json`
(SHA-256 `5c191b752f1e7e06d44113a28f3b3bb889da94bda1a67d804d8444b34389ecf8`).
The refusal is
`condition-2/activation-1792120110083861000/admission-1792120110170014000.json`
(SHA-256 `e89f81cbd0514cb56dfbe8e9f3a42bf53a137bf16d23b1f42599607dfb9640aa`).
The failed condition has no worker protocol, stderr, or initialization artifact.
The trace has one initialization, 19 protocol responses, and an empty retained
worker stderr file. Empty stderr is not itself proof of process cleanup.

The reported 32% satisfied the percentage threshold, but pressure 2 failed the
separate requirement for pressure 1. Both conditions must hold. These are two
host observations, not a continuous resource trace or a process-level allocation
measurement. They cannot distinguish retained host caches, delayed resource
reclamation, other workloads, or other causes. None is established here.

## Ownership path and its limits

In `desktop/ReservoirScope/src-tauri/src/activation.rs`, the worker is local to
`execute()`. Success, failure and cancellation exit that scope. `Worker::drop`
calls `terminate_owned`: kill the owned child, wait for it, join any blocked input
writer, then close stdin. Drop also joins the stderr reader and publishes its
bounded output. The run thread clears `busy` only after `execute()` and cleanup
return. The headless main waits for `busy` to clear, and the pilot launcher waits
for that subprocess to exit before considering the next arm.

Thus the normal source path provides no intended overlap of model workers. The
retained pilot has no separate child PID, termination timestamp, or kill/wait
success receipt; those operation results are discarded. Source inspection and a
later process inventory do not reconstruct that missing historical telemetry.
The existing blocked-pipe tests separately establish bounded cancellation and
reaping for a synthetic worker. No material cleanup defect was found in this
read-only audit, and no backend change is proposed.

A single new observation at `2026-10-16T15:08:13.924239+00:00` found pressure 2,
reported free percentage 27, no research-root-matched activation worker, and the
desktop app PID 72433 at 41,312 KiB RSS. All four resource commands and the scoped
process inventory succeeded. It is retained privately as
`research/outputs/activation-comparison-20261016/resource-audit-observation-01.json`.
No further sample was taken in this audit. This current unhealthy observation
without an owned model worker weakens a simple "the model worker is still alive"
explanation; it does not establish the earlier cause or guarantee later readiness.

## Next comparison's resource observations

The audit initially recommended a fixed settling interval followed by exactly
three samples that must all be healthy. The selected protocol instead freezes a
bounded preparation window: at most 120 seconds, observations every 10 seconds,
and three consecutive healthy samples (pressure 1 and free percentage at least
25). An unhealthy or unknown sample resets the streak. Window expiry holds the
new comparison without model dispatch; an actual Rust admission refusal or model
failure ends it without retry. These are different preparation policies. The
selected change is prospective and explicit, not a reinterpretation of the old
refusal. Every observation remains evidence, including those before a healthy
streak. The selected runner, rather than this audit probe, owns that waiting rule.

The companion `probes/2026-10-16-activation-resource-audit.py` performs fixed-count
read-only observations and writes a new JSON file. It starts no model, changes no
process, and never repeats an admission.
Its process inventory retains only workers/apps matched to explicitly scoped
research paths. A healthy observation does not guarantee later headroom: the
unchanged Rust pressure-1/free-at-least-25% check still runs immediately before
each worker load, and a refusal stops the new comparison.

Example for an independent, fixed-count observation (not the selected runner's
preparation window):

```sh
python3 -B probes/2026-10-16-activation-resource-audit.py \
  --samples 3 --interval-seconds 15 \
  --output /absolute/new-comparison/before-condition-1.json
```

Pass `--owned-root` for any separately installed research app bundle that should
be included. The probe never emits unrelated process arguments. This note and
probe add evidence; all prior pilot records remain unchanged.
