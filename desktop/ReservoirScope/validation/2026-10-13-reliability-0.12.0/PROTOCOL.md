# Passive resource capture protocol

This supplemental document describes the measurement procedure and schema for the selected packaged Tauri 0.12.0 app. It was completed after the actual run began; it is not the frozen prospective acceptance plan. The acceptance documents and their pre-Start hashes are identified in `prospective-freeze.json`. The script only observes an explicitly selected PID and its selected application-owned sustained session directory. It does not launch, control, resume, kill or contact the application, provider or any Being. The operator owns app actions and the bounded synthetic provider. The [acceptance plan](README.md), [run plan](run-plan.json) and [recovery checklist](RECOVERY-CHECKLIST.md) determine the experiment; this file defines capture and analysis.

## Frozen workload and capture window

The intended workload uses seed `20261013`, 1,000 ms pacing, a writing opportunity every 30 numerical steps, maximum 10,000 steps / 400 prepared attempts / 7,800 active seconds / 268,435,456 storage bytes, whichever limit is reached first. The owned synthetic provider has bounded 200 ms latency. These are plan values, not observed completions. The actual accepted configuration, package identity and launch markers are retained separately; actual timing is governed by those records.

The actual capture started before the operator pressed Start. The observed post-Start marker is `2026-10-13T16:31:05.920848Z`; it does not assert an exact earlier dispatch time. For a new attempt, start the sampler before Start. Keep the app visible for approximately five minutes, then minimize for at least two hours. Pause near 7,500 seconds to leave active-duration capacity for deliberate recovery. The sampler runs for up to 9,000 seconds, sampling the selected PID every 15 seconds and scanning owned directory metadata every fourth sample (nominally 60 seconds). It stops early on PID/start/executable changes, process loss, explicit sampler termination or its output bound. Every early end remains an incomplete window; a new process requires a new capture file and identity.

The current target is app PID `17307`, prepared session `sustained-1791908510756-1`. PID is an observed launch identity, not a reusable default. Confirm the current run plan before using the command. The sampler additionally requires the full executable path, binary SHA-256, process start seconds and microseconds obtained directly through libproc. It rejects a mismatched executable or binary and checks the process identity before and after metric reads.

## Launch without blocking an assistant turn

The following is a reusable shell template, not the actual launch transcript. The actual attempt used detached `subprocess.Popen`, retained in `sampler-launch.json`, with redirected output `sampler-process-01.log` and capture `samples-01.jsonl`. Run the template from `desktop/ReservoirScope`. Preserve the sampler source used at admission because its hash is included in the header. Use new filenames for every attempt; capture and analysis use exclusive creation and do not overwrite prior files.

```sh
cp -n scripts/macos_reliability.py validation/2026-10-13-reliability-0.12.0/macos_reliability-capture-01.py
nohup python3 validation/2026-10-13-reliability-0.12.0/macos_reliability-capture-01.py sample \
  --pid 17307 \
  --executable 'target/release/bundle/macos/Reservoir Scope Tauri Preview.app/Contents/MacOS/reservoir-scope-desktop' \
  --expected-sha256 f68a3752a628edf11ac6161a26e6979bb22dcf4c3ee1c63f10add2cea86ab40d \
  --session '/Users/v/Library/Application Support/research.reservoir.scope.tauri/sustained-v1/sustained-1791908510756-1' \
  --output validation/2026-10-13-reliability-0.12.0/samples-01.jsonl \
  --duration-seconds 9000 --interval-seconds 15 --disk-every 4 \
  --max-output-bytes 16777216 \
  > validation/2026-10-13-reliability-0.12.0/sampler-launch-01.log 2>&1 < /dev/null &
```

Record the returned sampler PID in the launch evidence, distinct from the application and synthetic provider PIDs. A detached owned `subprocess.Popen` invocation with the same argument array and redirected streams is also suitable. The sampler itself creates no automation, service or launch agent. Root separately configured the finite `reservoir-reliability-qualification` thread heartbeat every ten minutes to revisit this running attempt and its minimized-duration gate; that orchestration is outside the sampler. The sampler remains independent of the WebView and does not keep the Mac awake or modify power preferences.

On an intentional early end, signal only the recorded sampler PID with SIGTERM. It writes a footer with that reason; it does not terminate the app. Missing footer after a killed sampler or host loss remains explicit. Process exit normally ends sampling with status `process-or-path-unavailable`; exit code 2 means an observed early end, while admission errors return 1 and completion returns 0. Inspect the footer and launch log rather than treating exit code alone as reliability evidence.

## Explicit UI phase markers

The sampler never infers visibility, minimization or user activity from CPU use, renderer counters or manifest phase. Write operator markers immediately after the corresponding observed UI action into a separate JSONL file. The marker monotonic clock must come from the same host and boot as the sampler:

```python
import datetime, json, time
marker = {
    "phase": "minimized",  # e.g. prepared, visible, minimized, paused, restored
    "wallUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "monotonicNs": str(time.monotonic_ns()),
    "note": "Operator observed native minimize; screenshot evidence retained separately."
}
with open("validation/2026-10-13-reliability-0.12.0/ui-markers.jsonl", "a") as output:
    output.write(json.dumps(marker) + "\n")
```

Markers are declarations by the operator, not automatic window-state measurement. Preserve actual event timestamps; do not backdate them to meet a duration criterion. App pause, OS sleep, sampler gaps and a user reading a journal describe different events and should have separate markers or notes. Never replace an interrupted interval with an apparently continuous one.

## JSONL schema and bounds

The `reservoir-macos-reliability-v1` stream has one header, bounded sample records and a footer. Each line is independently parseable JSON.

- Header: run UUID; wall UTC and monotonic nanoseconds; selected PID, start identity, executable path/SHA/stat identity; selected session path; sampler source SHA, Python/macOS/architecture, Mach timebase; requested timing and byte/scan bounds; attribution limitations.
- Sample: sequence; wall UTC/epoch nanoseconds and monotonic nanoseconds; actual elapsed and sample execution duration; selected-PID RSS/virtual bytes, cumulative CPU ticks and converted nanoseconds, interval CPU percent, thread/running-thread counts and descriptor count; bounded manifest fields and exact sampled manifest SHA; optional disk scan; explicit component errors. Wide time values are decimal strings.
- Manifest projection: format, session ID, generation, revision, phase, current and durable steps, active elapsed milliseconds, journal/segment counts, last segment/checkpoint hashes. Configuration, prompts, journal bodies, endpoint names and diagnostics are excluded. The whole manifest is read at most 128 KiB to compute its digest; only this scalar allowlist is retained.
- Disk scan: total regular-file logical bytes, allocated blocks × 512, regular-file/directory/entry counts, free and user-available volume bytes, scan duration, completeness/errors and whether the sampled manifest stayed unchanged across the scan. Only the selected root and its direct `segments`, `checkpoints`, `journals` directories are scanned. No journal/segment/checkpoint file contents are read. Symlinks, unexpected nested directories and special files are excluded and make coverage incomplete.
- Footer: actual elapsed, observed sample count, end reason, final executable hash if readable and any final errors. It does not claim app acceptance or successful recovery.

Capture stops at 16 MiB by default (4 KiB reserved for footer), with a hard configurable ceiling of 64 MiB. Lines are capped at 256 KiB. Each disk scan is capped at 120,100 entries and five seconds; incomplete scans do not become valid size measurements in the analysis. Descriptor enumeration is capped at 65,536 descriptors and never collects their paths. Each output line is flushed and synchronized; this introduces a small periodic I/O load. The scan is not an atomic filesystem snapshot, including when its manifest digest remains unchanged. Measurements exclude directory inode allocation and external APFS metadata.

## Metric semantics and source qualification

The sampler uses macOS `proc_pidinfo` for one PID. `PROC_PIDTBSDINFO` binds process start seconds/microseconds; `PROC_PIDTASKINFO` returns resident bytes, cumulative user/system task time and thread counts; `PROC_PIDLISTFDS` supplies only a descriptor count. The implementation matches the pinned macOS 26.2 SDK struct sizes (136-byte BSD info and 96-byte task info), rejects partial API responses and checks executable path with `proc_pidpath`.

Current XNU fills task CPU counters in Mach time units and passes them through the BSD handler. The sampler converts with the host's `mach_timebase_info` ratio, then computes CPU delta divided by actual monotonic interval; 100% is one CPU core and multi-thread work may exceed 100%. See Apple's [task counter implementation](https://github.com/apple-oss-distributions/xnu/blob/main/osfmk/kern/bsd_kern.c) and [proc info handler](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/proc_info.c). This is not the decaying `ps %cpu` measure and must not be confused with other Darwin APIs' time units.

The retained [one-second CPU-unit check](sampler-cpu-unit-check.json) compares this conversion against Python `time.process_time_ns()` on the sampler-owned Python process. It is a measurement-method check, not a measurement of the app or a multi-hour reliability result. Focused tests use synthetic filesystem fixtures and the test process; they exercise identity/ABI, no-follow bounded reads, metadata-only disk counting, missing footers, clock/step regressions, marker windows and summary calculations.

## Analysis

Keep the raw capture and phase markers unchanged. Analyze a retained complete or incomplete capture into a new output file:

```sh
python3 scripts/macos_reliability.py analyze \
  --input validation/2026-10-13-reliability-0.12.0/samples-01.jsonl \
  --markers validation/2026-10-13-reliability-0.12.0/ui-markers.jsonl \
  --output validation/2026-10-13-reliability-0.12.0/analysis-01.json
```

Optional `--from-elapsed` and `--to-elapsed` select a predeclared numeric window. Analysis binds the exact input SHA and reports parsed/selected sample counts, actual endpoints, sampling gaps, wall-versus-monotonic discontinuities, missing footer/partial records, errors and manifest progress/regressions. Per-metric statistics include first/last, min/max, median, nearest-rank p95 and descriptive least-squares change per hour. Incomplete disk scans are excluded from size distributions. Operator intervals include their own metric summaries; a CPU interval crossing a phase boundary is excluded from that phase summary. Analysis never declares a pass, leak, plateau, GPU efficiency or energy benefit from these statistics.

Read-only analysis accepts at most 64 MiB / 100,000 records. Marker input is bounded to 128 KiB / 128 markers. No code in this harness opens arbitrary services, reads unrelated process command lines, enumerates the host process tree, or authenticates a provider. Shared WebKit/GPU processes are deliberately outside the selected-PID totals. A stable main-process RSS cannot establish stable total application memory. Free-space changes are volume-wide and cannot be attributed to the app. CPU/RSS may change with unrelated host load, caching, compression and scheduling. APFS block sharing makes summed `st_blocks` different from unique physical storage consumption.

Pair resource summaries with actual renderer counters/screenshots, operator responsiveness observations, final bundle verification, journal/application identities and explicit quit/relaunch/restore evidence from the acceptance checklist. A sampled durable cursor alone does not establish replay correctness, no duplicate application, physical crash durability or automatic resumption behavior.
