# Natural 16 MiB quota investigation, before repair

Two isolated accelerated scripted profiles generated real session objects with the unchanged storage implementation. No filler, quota mutation, live app access or provider calls occurred. The first-failure bundles, volatile checkpoints/events, exact outcomes and inventories are retained in [natural-quota-01-evidence.json](natural-quota-01-evidence.json). This investigation precedes any quota implementation repair and remains immutable.

| Profile | First failure | Terminal behavior |
| --- | --- | --- |
| Cadence 3 | Step 114, 37 saved journals, 12,764,948 retained bytes; candidate 38 had no physical saved journal. | Journal retry stayed guarded. Stop, explicit Skip, discard-close, exact current export, fresh-state prefix export and restore succeeded. |
| Cadence 1800 | Live 3240, durable 3210, 1 journal, 16,672,785 retained bytes; 30 unsaved Advanced events. | Retry/checkpoint, Stop and discard-close failed budget. No pending language opportunity existed to Skip. Clean close refused; current-revision export failed stale. Dropping isolated in-memory state allowed verification/export/restore of the valid 3210-step prefix, with 30 unsaved steps lost. |

The 4 MiB journal reserve protects the frequent-journal case but not numerical history growth between journal opportunities. Existing Stop/discard attempts retain the whole unsaved numerical suffix and cannot fit it. The owned prefix remains valid; the ordinary close path is trapped until a separate explicit rollback/discard path or process loss releases it. This is a confirmed case, not a prevalence estimate or actual multi-hour/physical-crash result.

The two tests passed as investigative probes in 199.69 seconds; the expected observations include the confirmed application failure. Exact command, source hashes and load interval 16:46:27.633588Z–16:49:54.436979Z are in `natural-quota-01-command.json`. Strict desktop all-target Clippy passed separately 16:50:29.783681Z–16:50:34.669918Z. Exclude these intervals from quiet-host resource comparisons. Only opt-in test/support files were added for this investigation. Before-repair source copies are retained alongside this note; old publisher and frozen-package receipts are unchanged.
