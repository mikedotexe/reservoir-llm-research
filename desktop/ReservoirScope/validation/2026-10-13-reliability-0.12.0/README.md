# Prospective 0.12.0 macOS reliability qualification

**Status: protocol prepared; this document records no completed long run.** The
result, exact interval, samples, interruptions and package identity must be recorded
separately after execution. A short walkthrough, accelerated numerical test, or
background sampler that outlives a stopped session does not complete this protocol.
Earlier [0.12 qualification](../2026-10-13-sustained-0.12.0/README.md) remains historical.

The question is whether the actual packaged My reservoir can keep its owned numerical
and journal loop progressing for more than two hours, including at least two hours
minimized, with inspectable resource use and recoverable committed evidence. This is
an application reliability check using an owned synthetic HTTP fixture. It is not a
study of a Being, a real model, learning, response quality or energy efficiency.

## Candidate, ownership and run configuration

Use the already built **final 0.12.0 macOS arm64 application**. The expected executable
SHA-256 is `f68a3752a628edf11ac6161a26e6979bb22dcf4c3ee1c63f10add2cea86ab40d`.
Confirm the actual executable path, digest, PID and process start time before the run;
retain a new receipt rather than treating that expected digest as a measurement.
A rebuilt or altered candidate needs a distinct run and source/package receipt.
No shipping source change is part of this qualification.

The prospective [run plan](run-plan.json) identifies application PID `17307` and
session `sustained-1791908510756-1`, prepared at step zero, with an ephemeral owned
fixture. It also records a known baseline issue: a separately reproduced session-lock
delay can falsely trigger the packaged watchdog's interruption detector. The source
correction being tested separately is **not in this selected binary**. Preserve any
occurrence as a baseline outcome; do not silently substitute a rebuilt app mid-run.

Root owns the packaged UI and the new fixture. The sampler observes only the selected
application PID and selected owned session directory. Do not discover, sample, stop,
restart, instrument or read the workspaces of unrelated processes or the Beings.
Do not prevent host sleep by changing settings: an actual interruption is evidence to
classify, not an interval to conceal. An existing host configuration may be recorded.

The selected prospective workload is:

| Setting | Value and meaning |
|---|---|
| Seed | Decimal string `20261013` |
| Numerical pace | `1000` ms between free numerical steps |
| Writing cadence | Every `30` numerical steps |
| Maximum steps | `10000` |
| Maximum prepared attempts | `400`, including retries |
| Maximum running duration | `7800` seconds / 130 minutes |
| Per-session storage | `268435456` logical bytes / 256 MiB |
| Leak / seeded noise / initial retention | `0.65` / `0.02` / `0.955` |
| Regulation | Enabled |
| Language | Explicit new loopback fixture endpoint and exact fixture model identity |
| Context / output / temperature | `4096` / `256` / `0` |
| Reply format | Plain prose; no JSON response-format request |
| Fixture delay | `200` ms per successful synthetic response |
| Fixture safety bounds | At most `500` requests and four hours of fixture lifetime |
| Process sampling | Every `15` seconds for at most `9000` seconds |
| Owned-directory sampling | Every fourth process sample, approximately `60` seconds |

Create prepares local state; Start is explicit. Neither navigation nor inspection may
start the experiment. The fixture must retain exact request bodies, response identities
and timestamps. Mark these as controlled synthetic responses, even though the app
uses its real local-model HTTP transport. No existing model service is contacted.

The provider's request count, the session's prepared-attempt count, journal count and
application count are different quantities. Do not replace one with another. Record
all four where available, including any discrepancy and its retained explanation.

## Timing and storage expectations, not measured outcomes

The numerical timestep remains **one third of a simulated second**. One second of
wall pacing is separate; HTTP latency, filesystem work, scheduling and pauses add
wall time while the numerical clock may be held. For a 200 ms response every 30
steps, the idealized arithmetic is:

```
7800 / (1 + 0.2 / 30) = approximately 7748 numerical steps
7800 / (30 + 0.2)     = approximately 258 writing opportunities
```

These are planning estimates excluding storage, scheduling and other work, not required
counts or a timing guarantee. The 10000-step and 400-attempt caps should leave duration
as the first planned numerical/runtime bound for this workload. The sampler's 150-minute
window includes a terminal tail and must never be reported as 150 minutes of active work.

A prior, different short fixture exported 181 steps, 30 journals and 149 segments in
10,690,170 bytes. That [retained receipt](../2026-10-13-sustained-0.12.0/actual-ui-export-qualification.json)
used cadence six; it is not a measured storage rate for this cadence-30 run. Its 181
serialized `advanced` events measured 3423–4019 bytes, median 3627, using compact Python
JSON re-encoding for a sizing estimate. Combining the median step cost with the prior
non-step overhead gives an illustrative estimate of about **110 MiB** for 7748 steps
and 258 similarly short replies:

```
(10690170 - 181 * 3627) / 30 * 258 + 7748 * 3627
```

This estimate is sensitive to response length, segment boundaries, metadata and
serialization. The actual scan decides. A 256 MiB budget has planning headroom but
is not a promise that the run reaches its duration bound. A correct early quota stop
can pass the budget-stop behavior while leaving the two-hour duration criterion
incomplete. Never delete retained journals, enlarge limits silently, or merge separate
runs to manufacture a duration pass. Exports and fixture/sampler logs are separate
copies outside the per-session quota and must be counted separately when discussing
total test storage.

Sizing evidence was read only from the previously exported owned fixture under
`target/qa/0.12-ui/sustained-1791904148347-1-1-333`. The receipt SHA-256 is
`1017385e658f94285f13ff472f974b9088a62332efe151a35453f3c9761eb6b0`.
The sizing query, included to keep these numbers reproducible, was:

```python
import json, statistics
from pathlib import Path
root = Path('target/qa/0.12-ui/sustained-1791904148347-1-1-333')
sizes = []
for path in sorted((root / 'segments').glob('segment-*.json')):
    for event in json.loads(path.read_text())['segment']['events']:
        kind = event.get('kind', {})
        if isinstance(kind, dict) and ('advanced' in kind or kind.get('type') == 'advanced'):
            sizes.append(len(json.dumps(event, separators=(',', ':'), ensure_ascii=False).encode()))
print(len(sizes), min(sizes), statistics.median(sizes), max(sizes))
```

## Observation sequence

Record actual timestamps and uncertainty; the minutes below are scheduling targets.
Use a monotonic elapsed clock for durations and retain UTC observations for matching
artifacts. Do not subtract pauses or missing intervals without naming them.

1. **Before Start:** verify the candidate and selected session directory; identify the
   fixture PID/endpoint/model and its distinct output directory. Capture Create and the
   accepted configuration. Confirm zero generation requests before explicit Start.
   Start the sampler against this exact app PID and session, then explicitly Start.
2. **First approximately five minutes visible:** confirm actual surface and separate
   fill, automatic journals and next-step application. Select an older journal once at
   least three exist. Record its entry ID, exact text hash, observed step and first
   application status. Leave Follow latest off; record the live numerical step and
   graphics counters separately. Opening exact prompt/memory details must not change
   requests, source coordinates or journal selection.
3. **Minimize for at least 7200 uninterrupted seconds:** retain a confirmed minimized
   timestamp, then leave the app minimized. The owned sampler and fixture may continue;
   neither may start, resume or advance the session. Avoid repetitive UI inspections
   that would restore the app and invalidate the minimized interval. A process that
   merely remains alive is insufficient: retained manifests and fixture events must
   show continuing numerical/journal progress within the interval.
4. **Return at approximately minute 125:** record the restoration action and observed
   UI. The earlier journal must remain selected with the same exact text/hash while
   the live state reflects current progress and the new-entry indicator is nonzero.
   Then explicitly Follow latest and confirm its independently selected entry matches
   the newest returned page. Do not require the original selection to persist across
   application quit; that is a different, currently unpromised behavior.
5. **Finish deliberately:** use the [recovery checklist](RECOVERY-CHECKLIST.md). Either
   pause before the duration budget, leaving time for a same-session continuation test,
   or observe the 7800-second budget stop and test recovery of that exhausted session.
   Do not require an exhausted budget to resume. Keep terminal samples and freeze the
   committed bundle before heavy whole-history verification or export measurement.

Actual sleep/wake, a process restart, an unexpected hold, fixture expiry, missing
samples or a shorter minimize interval must be retained. Such an interval may answer
a recovery question but cannot be counted as uninterrupted minimized execution.

## Acceptance criteria and explicit incomplete outcomes

Report each row as observed pass, observed failure, incomplete or unexecuted, with
artifact references. Do not infer a blanket pass from a zero exit status.

| Criterion | Required evidence |
|---|---|
| Exact candidate | Before/after executable digests match the selected shipping binary; PID and start identity remain attributable throughout the claimed continuous interval. |
| Actual duration | Start-to-finish observations establish more than 7200 seconds of actual packaged-session progress, with at least 7200 uninterrupted seconds minimized. State exact conservative lower bounds; sampler uptime alone is insufficient. |
| Continuing work | Ordered committed steps, attempts and journals advance through the minimized window. Any gap exceeding 120 seconds under the 200 ms fixture is explained by retained boundary/host evidence; unexplained stalls are not a pass. |
| Journal continuity | Whole-bundle verifier accepts genesis, ordered segments, exact journal evidence, memory and application boundaries. No duplicated accepted attempt, forged journal, implicit retry or unrecorded application. |
| Stable reading | The selected older entry ID and exact text remain unchanged across new entries and minimization. Live step and new-entry count advance separately. Follow latest moves only after the explicit action. |
| UI return | The restored window is usable; surface, fill, status and exact coordinate reading share the returned current frame. Record observed delays without claiming a precise latency if the UI tool cannot time them. |
| Storage bounds | Selected-directory logical byte observations remain within the stated quota; any quota hold is visible and leaves inspectable evidence. Allocated bytes are separately reported and may differ. No journal-history pruning to continue. |
| Recovery | Verify and inspect starts no request. Restore changes generation and stays held. Previously saved/applied evidence remains exact; any later Start is explicit and any application occurs once at its recorded numerical boundary. |
| Terminal behavior | At the first actual bound or explicit Pause/Stop, no new numerical progression/request is silently scheduled. A dispatched request may settle within its own bounded deadline; preparation still cannot apply beyond an exhausted budget. |
| Sampling coverage | Report attempted/valid samples, gaps and identity failures. The expected schedule is approximately 600 intervals in 9000 seconds, not a forced exact row count. Missing measurements remain unknown. |

A successful uninterrupted run and successful recovery are separate results. A
controlled interruption may produce valid recovery evidence without passing the
uninterrupted-duration criterion. Correct quota/failure handling is also distinct
from sustained progress at the selected workload.

## Resource attribution and analysis

The backend agent's [sampler protocol](PROTOCOL.md) owns exact CLI arguments and artifact
schemas. It observes the selected PID with its executable/start identity, reads bounded
progress metadata, and scans only the selected owned directory. It neither controls
the UI nor launches a run. Measurement commands and tool hashes belong in its receipt.

| Quantity | Attribution and limits |
|---|---|
| Cumulative CPU / interval CPU | Main app process only. Derive interval CPU from the difference in process CPU time divided by monotonic elapsed sample time; state whether 100% means one fully occupied logical CPU. This excludes separate webview/fixture/sampler processes. |
| RSS | Resident bytes for the selected process at sample instants. RSS is not allocated memory, private memory, total webview memory, GPU memory or a leak diagnosis. Missing/failed reads are not zeros. |
| Thread / file-descriptor count | Sampled task counts for that PID. Transient peaks between samples are unobserved; enumeration failure is explicit. |
| Logical disk bytes | Sum of the sampler's declared ordinary-file scope, with manifest progress and known-directory counts. Retain scan start/end or duration because writes can occur during a scan. |
| Allocated disk bytes | Filesystem block allocation for that same scope, separately from logical bytes/quota accounting. Compression, sparse allocation and metadata can change the relation. |
| GPU work | Visible app render counters and source policy can establish redraw behavior at observed boundaries. Main-process CPU and RSS cannot identify actual GPU utilization or device power. |
| WebKit helpers | A generic WebContent/GPU process name or parent relationship is insufficient to attribute a shared service to this app. Do not enumerate or sum unrelated helpers. If reliable app ownership cannot be established, report helper/GPU-process memory unmeasured. |

Analyze comparable phases separately: initial visible warm-up; early minimized;
late minimized; restored visible; paused/terminal. Report sample counts, median/p95/max,
first/last observations and the fitted trend with its window. Do not combine an
expensive final verifier with steady-run samples. For a suggested comparable pair,
use minutes 10–25 and 110–125 only if both were actually minimized, continuously
progressing and sufficiently sampled. These windows are dependent observations from
one machine and one session, not independent repeated trials.

The following are **prospective investigation triggers**, not previously established
product performance guarantees or automatic pass thresholds:

- Compare early/late minimized median RSS. Growth exceeding the greater of 64 MiB or
  25% of the early median, or a clear sustained upward trend, requires investigation
  before claiming stable observed main-process memory use.
- A five-minute interval of main-process RSS above 512 MiB, or CPU above one fully
  occupied logical CPU, warrants an explicit operator review and bounded-stop decision.
  Do not manipulate other workloads to erase the observation. Neither level alone
  proves a leak or causal GPU problem.
- A final settled file-descriptor/thread median more than 16 above its comparable
  early median warrants explanation. Successful repeated creation is not part of this
  one-session run, so do not infer that an increasing count is intended pooling.
- A scan approaching 90% of the logical storage budget warrants recording the projected
  remaining margin; allow the declared safe budget behavior or stop explicitly. Do not
  silently increase the quota. A physical disk-health concern takes priority over
  completing the planned time window.

A result may therefore be “functional duration passed; observed resource trend needs
investigation.” Report measured numbers and scope rather than “no memory leak,” “low
power,” “GPU efficient,” or “energy improved.” The fixture is deliberately cheap and
cannot qualify real-model host pressure or throughput.

## Graphics checks without inventing GPU telemetry

Source review establishes separate one-million-pixel render budgets, DPR at most two,
and dimensions at most 4096/hardware limit for each surface or sphere. These are
per-renderer limits, not one combined app-wide budget. Both schedulers gate draws on
visibility/context and retain only the latest pending invalidation. My reservoir also
preserves same-session/generation/step frame identity across status updates.

Use actual UI counter checks as a separate short prelude or aftermath, rather than
interrupting the required two-hour minimized interval:

- At a deliberately held provider boundary, keep the visible camera, selection and
  window unchanged. Observe stable surface/fill frame counters across a bounded wait
  while status remains usable. The hold must remain below the transport deadline;
  record that this is a synthetic hold, not inference latency.
- Scroll both graphics hosts completely out of view or navigate away. Confirm numerical
  progress and the selected reading continue independently. Navigation unmounts graphics,
  so remount counters restart and cannot be treated as cumulative GPU work.
- Across minimization, record counters before/after only when the same renderer mount
  survives. A bounded redraw on restore is expected for the latest state/size; replaying
  every hidden numerical step is not. A before/after counter can include transition or
  restore draws and cannot alone prove precisely zero hidden draws.
- Return at a paused/held boundary for a clean count comparison where feasible. Avoid
  asserting a fixed “one redraw” if resize, context recovery or camera input occurred.
- Exact-values mode releases the 3D contexts and preserves actual values. It is a
  useful behavior check, not a measurement of hardware memory or watts.

The implementation anchors are `src/renderPolicy.ts`, `src/fillSpherePolicy.ts`,
`src/SurfaceView.tsx`, `src/fillSphereRenderer.ts`, `src/myReservoirController.ts` and
`src/MyReservoirVisuals.tsx`, as bound by the final package's source receipt. No source
inspection alone proves the long-run webview behaved that way.

## Evidence to retain and claims left open

Before execution, freeze this prospective account and the sampler protocol by hash.
Root records the chosen endpoint/model/configuration, package/process identity and
actual launch/minimize/restore/finish decisions. Preserve raw process/disk JSONL,
fixture requests/responses, a bounded UI observation log, immutable bundle(s), whole-chain
verification, final resource analysis and a completion account. Use filenames declared
in [PROTOCOL.md](PROTOCOL.md); later changes need an append-only amendment or a new run.
Final evidence must explicitly state any missing or aborted phase.

The [recovery checklist](RECOVERY-CHECKLIST.md) separates normal quit/relaunch, saved
feedback continuation, exhausted-budget recovery, and optional separately identified
interruption/crash cases. Do not call normal quit a crash or host sleep a minimized run.

Even a complete pass leaves 24-hour operation, real models, macOS minimum-version
coverage, Windows/Linux, physical power-loss/disk-full behavior, energy measurement,
GPU-process attribution and broader accessibility/collaborator acceptance unqualified.
The primary result is one measured packaged application run under the stated workload.
