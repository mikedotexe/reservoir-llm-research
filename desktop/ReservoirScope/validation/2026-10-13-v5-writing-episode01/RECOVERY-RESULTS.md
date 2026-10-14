# V5 writing episode: clean-quit recovery

The recovered native export passed the exact pinned 0.17.0 production verifier.
All 72 non-manifest files are byte-identical to the original qualified export:
59 segments, 12 journal objects and the final checkpoint. Both exports contain
73 files. Only the manifest's restore metadata changed.

| Field | Original | Recovered |
| --- | --- | --- |
| Generation | `1` | `2` |
| Revision | `423` | `424` |
| Wrapper phase | `budgetReached` | `paused` |

The [comparison receipt](recovery-equality-01.json) records every file identity,
the exact differences, the pinned replay command/result and before/after checks.
The [checker](check_recovery_01.py) was prepared before handoff and executed once,
at 2026-10-14 02:12:23.727076–02:12:24.237412 UTC. It did not rerun the main checker,
read app-owned live data, inspect processes, operate UI or contact a provider.

The original still matches its [passing qualification](real-model-export-01/receipt.json).
Its twelve-slot outcome remains complete: 12 reached opportunities, 12 dispatched
attempts, 12 complete responses, 12 saved journals and 12 once-only applications;
zero slots remain unstarted. Exact prompts, full prior prose, optional provider
input-count evidence, observations, readback receipts and numerical history are
unchanged. The core checkpoint remains `ready`. Recovery introduced no new retained
event, response, journal or application.

Step 361 and the 12-attempt limit are both reached. Retained active elapsed time is
653,082 milliseconds, below the configured 900-second limit. These resource facts
are separate from writing completion: an exhausted limit could accompany a partial
episode, although this particular retained episode completed all twelve applications.
The paused wrapper does not renew any budget or change the underlying core state.
The checker does not infer current UI control availability from these flags.

The original export contains 6,304,053 bytes; the recovered export contains
6,304,046 bytes. The difference is entirely the shorter manifest phase value.
Both inputs and the original qualification receipt remained unchanged through
the audit. The pinned executable matched before and after replay:

`7d46719838495b7a9ba57eea69ac9c940bb81f2fdc47cd12b761d97bb472d081`

The immutable export directories are:

- Original: `target/qa/0.17-v5-writing-episode01/exports/sustained-1791942995555-1-1-423`.
- Recovered: `target/qa/0.17-v5-writing-episode01/exports/sustained-1791942995555-1-2-424`.

Root separately reported model shutdown before quit, a [confirmed clean quit](ui-quit-observed-01.json),
idle relaunch, explicit Verify/inspect and Restore into paused generation 2, with
Resume disabled at the original step limit. Those are parent-observed native actions,
not observations made by this script. The offline comparison establishes exact
preservation across the supplied exports; it does not qualify crash/power-loss
durability, continued execution, full provider-context processing or writing quality.

Receipt SHA-256:
`5abe4d8e0c62491406a61985a64d7f8d8aa2a17c2605c090f47a8b9dc7927f74`.
