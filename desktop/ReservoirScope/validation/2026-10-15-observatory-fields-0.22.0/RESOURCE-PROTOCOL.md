# Short passive resource measurement: Observatory 0.22

Prospective, operator-controlled characterization of the exact owned native app.
No measurement has run merely because this file or its helper exists. The lead
owns app launch/UI actions and permits execution only after checks/builds finish.
No other app is closed or changed. No model, network endpoint, session journal,
process inventory, `sudo`, power preference or system service is involved.

## Four settled windows

Keep the same normal window size and recorded state track. Make the field/spectrum
views visible. Record selected source/row, viewport, visible renderer counters and
whether graphics or table fallback is active. Use row 0 before the playback window
and 4 rows/second, which stays inside the 1,024-row recording for 60 seconds.

For each phase, perform the UI transition, mark `settling`, leave it alone for at
least 15 seconds, then mark the named phase and leave it alone for at least 60
seconds. Close that window with `settling` or final `end` **before** any next UI
inspection or transition, so those actions are excluded from the settled window.
After the UI transition, mark `settling` again and wait at least 15 seconds before
the next named phase. Repeated settling markers are intentional. Record monotonic
markers on the same host/boot as capture.

1. `visible-idle`: visible state view, playback paused, no camera/pointer changes.
2. `playback`: visible state view playing at 4 rows/second from row 0. Record the
   actual settled start/end rows; settling itself advances playback.
3. `minimized`: minimize while playback is active. Visibility handling intentionally
   pauses recorded playback. Do not query, raise or inspect the UI in this window.
4. `restored-idle`: restore, verify playback remains paused, then settle and measure.

The minimized window is a paused workload, not a throughput comparison with active
playback. Operator marks declare these conditions; they are not automatic window
state detection. UI tools can alter visibility, so capture before/after witnesses
only at visible boundaries and keep the minimized interval untouched.

Record `frames drawn` from the exposed renderer diagnostics at each visible
boundary. A counter is cumulative for that renderer instance, can reset on remount,
and counts draw submissions, not presented display frames, FPS, GPU work or frame
latency. Restore/resize/selection may legitimately cause new draws. A before/after
minimize counter delta cannot localize every draw to the hidden interval; report
the transition uncertainty instead of claiming exact zero GPU use.

## Bounded capture

`sample_owned_app.py` reuses the unchanged qualified libproc metric reader from
`scripts/macos_reliability.py` at the hash embedded in the helper. It does not use
that sampler's sustained-session/disk mode. The only target is the main PID from
the explicit owned launch receipt, with executable hash/path and process-start
identity checked. It checks process identity at every sample, including the last,
and checks executable bytes again at completion. It reads no
command lines, sockets, other processes, prompts or journals.

Capture is every 5 seconds, at most 600 seconds, at most 2 MiB, with exclusive
JSONL output. Each sample records monotonic/wall time, cumulative CPU, RSS, threads
and descriptor count where available. Metric failures remain explicit. The helper
never sends a signal to the target app. Interrupting the sampler stops only its
own collection and leaves an incomplete-status footer.

Root supplies the exact final launch-receipt hash. Templates from the desktop root:

```sh
python3 validation/2026-10-15-observatory-fields-0.22.0/sample_owned_app.py sample \
  --launch-receipt validation/2026-10-15-observatory-fields-0.22.0/ui-launch-01.json \
  --expected-launch-sha256 EXACT_FINAL_LAUNCH_RECEIPT_SHA256 \
  --output validation/2026-10-15-observatory-fields-0.22.0/main-process-samples-01.jsonl \
  --duration-seconds 600
```

Launch this bounded capture nonblockingly under the root's owned task execution,
retain its output/exit status, and perform UI phases while it runs. Do not create
a daemon or recurring automation. For each explicit boundary:

```sh
python3 validation/2026-10-15-observatory-fields-0.22.0/sample_owned_app.py mark \
  --output validation/2026-10-15-observatory-fields-0.22.0/resource-markers-01.jsonl \
  --phase visible-idle
```

Use the actual phase (`settling`, one of the four names, or `end`), not the example
unchanged for every boundary. After capture is terminal:

```sh
python3 validation/2026-10-15-observatory-fields-0.22.0/sample_owned_app.py analyze \
  --input validation/2026-10-15-observatory-fields-0.22.0/main-process-samples-01.jsonl \
  --markers validation/2026-10-15-observatory-fields-0.22.0/resource-markers-01.jsonl \
  --output validation/2026-10-15-observatory-fields-0.22.0/main-process-analysis-01.json
```

CPU is duration-weighted task time, with 100% meaning one core. Only intervals
wholly inside a closed declared phase and no longer than 7.5 seconds count. Crossing
and missing-sample intervals are excluded, with actual coverage reported. RSS,
threads and descriptors get count/minimum/median/maximum; no leak threshold is
invented. Missing observations are never treated as zero. Retain all raw errors,
terminal status and unclosed/short windows. Any build or other known background
work overlapping capture must be disclosed; avoid scheduling it here.

This measures the main process only. It excludes separate WebKit/GPU processes
and does not establish total application memory/CPU, energy, thermal behavior,
responsiveness, frame pacing, graphics acceleration, long-run reliability or any
Windows/Linux result. Renderer-counter evidence is reported separately from
process metrics. No new real-model quality or endurance claim belongs to this run.
