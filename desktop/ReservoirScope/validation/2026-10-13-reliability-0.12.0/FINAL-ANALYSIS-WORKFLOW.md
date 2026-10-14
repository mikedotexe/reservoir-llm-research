# Final analysis and scoped interruption preparation

This supplemental workflow was prepared while the selected 0.12.0 app remained minimized. It does not revise the frozen acceptance criteria in `prospective-freeze.json` and does not report a completed duration/recovery gate. It runs no application, sampler, provider, process-control or UI commands. Raw samples, original receipts and the shipping package are preserved.

## Freeze inputs after the interval

Root owns the finish/recovery sequence in [CONTINUE.md](CONTINUE.md). The conservative minimize boundary is `2026-10-13T16:39:18.845510Z` / monotonic `1105935210710958`. The earliest qualifying two-hour return is `18:39:18.845510Z`, provided the session actually continued and the interval was not interrupted. The earlier native action acknowledgment at `16:38:59.247Z` must not replace this conservative marker. The visible prelude took about eight minutes; report that actual deviation from the five-minute plan.

After Root ends primary capture deliberately, retain its footer and hash `samples-01.jsonl` and `ui-markers.jsonl`. A signal-terminated sampler is an intentional shorter capture with an explicit reason, not a completed 9,000-second sampler run. Exact package/PID/start identities, functional progress and declared window state are distinct evidence. Keep export/replay, quit/relaunch and short recovery activity outside the primary minimized resource window and use new sampling identities for a new process.

Do not execute the final report against a growing file and silently call it final. The wrapper below rejects a missing footer by default. `--allow-incomplete` is available only for an explicitly interim summary; its hashes bind the exact prefix read, not a future final file. A concurrent append between its two bounded reads is rejected. An actual missing/truncated line must be reported, not repaired by deleting it.

## Commands

Run from `desktop/ReservoirScope`. Use unique output names. First retain the full raw analysis, without exclusions:

```sh
python3 scripts/macos_reliability.py analyze \
  --input validation/2026-10-13-reliability-0.12.0/samples-01.jsonl \
  --markers validation/2026-10-13-reliability-0.12.0/ui-markers.jsonl \
  --output validation/2026-10-13-reliability-0.12.0/final-raw-analysis-01.json
```

Then produce supplemental per-phase and early/late summaries, retaining both all-observed resource statistics and a documented-background-load sensitivity analysis:

```sh
python3 validation/2026-10-13-reliability-0.12.0/analyze_run.py \
  --input validation/2026-10-13-reliability-0.12.0/samples-01.jsonl \
  --markers validation/2026-10-13-reliability-0.12.0/ui-markers.jsonl \
  --load-receipt validation/2026-10-13-reliability-0.12.0/publisher-final-01-qualification.json \
  --load-receipt validation/2026-10-13-reliability-0.12.0/sampler-analysis-02-qualification.json \
  --load-receipt validation/2026-10-13-reliability-0.12.0/natural-quota-01-command.json \
  --output validation/2026-10-13-reliability-0.12.0/final-phase-analysis-01.json
```

Add subsequent **closed, timestamped** source-test/replay receipts with additional `--load-receipt` arguments. The wrapper accepts `startedAtUtc` or `startedAt`, and `finishedAtUtc`, `endedAtUtc` or `endedAt`. It rejects a receipt without an ordered closed interval. The receipt bytes and hashes are included in output. Do not invent start/end times from file mtimes or conceal unfinished/untimed work. Where no complete interval exists, list the known load and timing uncertainty in the written account. Source-test exclusion is a sensitivity analysis, not a reconstruction of an idle host.

The wrapper and tests are local validation artifacts, not app/runtime source. It imports the corrected reusable analyzer whose qualified source is bound in `sampler-analysis-02-qualification.json`; it also records its own and the imported analyzer's current SHA. The capture implementation remains the retained `macos_reliability-capture-01.py` hash `108b03157d93804c187ba18e0ab747d5a5695af2857167839fcab307862c738c`.

## Known overlapping load at workflow preparation

| Work | Retained interval / evidence | Treatment |
|---|---|---|
| Full desktop tests plus strict Clippy | 16:31:50.400328–16:34:35.556782 UTC; `publisher-final-01-qualification.json` | Exclude overlapping resource intervals in sensitivity summary. It overlaps visible warm-up, so visible-versus-minimized CPU is not a clean causal comparison. |
| Frontend focused source tests | Vitest log starts 09:31:59 and 09:33:55 local / 16:31:59 and 16:33:55 UTC; `frontend-snapshot-*.log` | Within the desktop interval. TypeScript process boundaries are not fully timestamped. |
| Full frontend tests | Vitest start 09:35:11 local / 16:35:11 UTC, duration 972 ms; `frontend-full-source-tests.log` | Exact process launch/exit boundaries are not retained. List the visible-prelude load; do not present the receipt's later capture timestamp as test end. |
| Analyzer-window regression qualification | 16:44:53.692248–16:44:54.124044 UTC; `sampler-analysis-02-qualification.json` | Exclude overlapping CPU intervals and sample/scan points in sensitivity summary. |
| Natural-quota investigation | 16:46:27.633588–16:49:54.436979 UTC; `natural-quota-01-command.json` | Exclude overlapping resource measurements. Keep all functional progress/stall evidence during this period. |
| Natural-quota Clippy / ongoing repair work | `natural-quota-01-clippy.log` records 4.73 seconds but no complete wall-time bounds; later receipts may exist | Add exact intervals only when retained. Otherwise state unknown timing. |
| Sampler, synthetic fixture, Codex/editor and unrecorded host work | Present or possible across the run | Not measured as part of app PID. Their contention/thermal/cache effects cannot be removed from these observations. No “quiet host” or energy comparison claim. |

The table is an initial inventory, not a declaration that no later background work occurred. Record final source-test windows before drawing resource conclusions. Excluded main-process samples still reflect a real measured workload; keep the all-observed summary next to the sensitivity summary.

The source work subsequently completed. Add `frontend-final-load-02.json`,
`frontend-final-load-03.json`, `quota-repair-final-01-qualification.json` and
`quota-repair-final-02-qualification.json` as additional closed load receipts. The
final backend interval is **17:32:34.913899–17:40:11.274699 UTC**; the final frontend
interval is **17:30:15.073535–17:30:19.620296 UTC**. These do not describe every source
edit, compilation or host activity between the earlier investigation and final checks.
Retain that uncertainty rather than declaring all remaining samples idle-host data.

## Defensible statistics and coverage

- Report total parsed/valid samples, actual first/last monotonic/wall timestamps, footer reason, process identity failures, missing rows, component errors, incomplete disk scans, wall-clock jumps and sampling gaps. Do not replace elapsed duration with `sample_count × 15`.
- Report operator-declared prepared, visible, minimized, restored and paused/terminal intervals separately. Window state is not independently sampled. Root's restored marker closes minimized time; unknown external user interaction remains a limitation.
- RSS/thread/descriptor statistics are instantaneous selected-PID observations: median, nearest-rank p95, max, first/last and descriptive slope. Report counts and actual endpoints. RSS growth is not a leak diagnosis; helpers and GPU allocations are excluded.
- CPU percent describes the interval since the previous successful task read, not a point at the row timestamp. Include a CPU interval only when its entire span lies within the selected window. Remove any interval intersecting a documented load in the sensitivity summary. The wrapper reports a duration-weighted CPU mean as well as the ordinary sample distribution; 100% means one core. A failed read can make the next interval longer than 15 seconds. Wall-clock discontinuities invalidate simplistic matching to UTC-only load windows and need explicit review.
- Disk statistics use complete scans only: logical and allocated bytes separately, file count, first/last/net growth, actual scan endpoints and descriptive rate. A scan overlapping a documented load is excluded from the sensitivity summary using its entire bounded sample duration, conservatively longer than the disk scan itself. Free space is volume-wide; it is not app-attributed. A stable manifest across a scan does not make file metadata atomic.
- Always preserve unfiltered committed step/journal/segment progress, manifest phases and the 120-second unexplained-stall gate. Resource-load exclusion must never remove a functional failure or turn a stopped session into a continuous run.
- The prospective comparable windows remain minutes **10–25** and **110–125** relative to the observed Start marker. Do not relocate them after seeing results. The wrapper includes partial statistics but labels a window incomplete unless fully sampled and entirely inside an operator-declared minimized interval. If load exclusion leaves too few or uneven observations, report that limitation; no replacement cutoff or window is invented.
- Compare early/late median RSS against the frozen investigation trigger (greater of 64 MiB or 25%); compare final settled thread/FD median against the frozen +16 trigger. These remain investigation triggers, not automatic leak/pass classifiers. A five-minute high CPU/RSS claim requires actual interval coverage; isolated max/p95 alone is insufficient.

The final prose should say which functional rows passed, failed, remained incomplete or were unexecuted, then give main-process numbers with exact windows. Keep whole-chain numerical verification, selected-journal stability, native UI return, quota behavior and process recovery as separate findings. The source-only watchdog/publisher/quota repairs are not in the measured 0.12.0 binary and cannot be credited to it.

## Practical constraints for the separate interruption case

Read [PROCESS-INTERRUPTION-PROTOCOL.md](PROCESS-INTERRUPTION-PROTOCOL.md). That document's selected exact-PID forced exit is separate from the continuous minimized run and must occur only after the interval is finished and its evidence frozen. No process action was taken while preparing this workflow.

1. Prefer a new short owned synthetic session with enough remaining attempt/duration/storage budget. A duration-exhausted endurance session cannot prove later numerical continuation without changing its contract. Do not silently extend its budget.
2. The owned fixture has `hold` mode and a per-request `release-N` marker; its hold expires after 70 seconds, while the app transport's request deadline is 60 seconds. Observe the exact POST log entry, bind it to the held session/attempt/prompt, and take the intended forced-exit action **before that 60-second deadline**. Otherwise classify the observed timeout branch instead of claiming an in-flight crash. The fixture's four-hour lifetime and request cap must still have headroom. No other endpoint is in scope.
3. Preserve the last committed manifest, addressed checkpoint and immutable prefix inventory while the clock is held. A manifest can be replaced atomically: record exact bytes/hashes and verify that the referenced checkpoint was copied consistently. Do not mutate originals. If copying races with a commit, retry into a new evidence directory and retain the failed capture's explanation.
4. The prepared intent is durably written before actual provider dispatch. Therefore a crash checkpoint may have `request_started=false` although the fixture independently received the POST. That is uncertainty about a dispatched request, not proof that no request was sent. Preserve both channels; do not rewrite checkpoint fields to match the network log.
5. Match executable path, SHA, PID and process-start identity immediately before any one-process interruption. Never use broad process-name matching. Root controls this action. Keep the provider alive so the old held handler's late completion can be observed; `socketWriteCompleted=true` is not proof the dead app accepted a response.
6. Capture process absence, relaunch the identical package and retain a pre-Restore idle/request-count interval. Inspection must not dispatch. Explicit Restore may commit a new generation and an interrupted event; capture the original checkpoint before that mutation. Recovery is held, with no implicit resend. The backend conservatively converts an unresolved language checkpoint to blocked uncertainty.
7. Explicit Retry must produce a new attempt identity, with a fresh physical memory read when applicable; Skip must remain a retained decision. Verify the original committed segment prefix unchanged plus the expected new recovery/decision events. Prove no journal/application from abandoned attempt N and exactly one first application from accepted replacement N+1, then separately identify later held-vector reuse.
8. For the optional saved-Prepared branch, prove journal readback and a committed Prepared checkpoint before interruption. After relaunch/inspection/Restore, no numerical application or HTTP request should occur until explicit Start. This case tests retained feedback application once, independently of the held-request branch.

A process kill leaves the filesystem and OS alive. It cannot establish sudden-power-loss/fsync durability, host restart, actual sleep/wake handling or real-model reliability. Any failure to obtain the chosen boundary is an incomplete or different case, not permission to relabel it.
