# Packaged 0.12.1 reading and recovery check

Executed on October 13, 2026 with the package in [qualification.json](qualification.json), binary `e66533cfd3371d8cdf80ce9969fae702b957987fad2a1a12974945c33842f43c`. This is a short native macOS check, separate from the frozen 0.12.0 two-hour run. It found one presentation defect; a distinctly identified 0.12.2 follow-up is being prepared. No real model ran during this check.

The actual native window showed the simpler setup: source choice, four selected limits and a closed Advanced settings section. Its layout was visually inspected at 1280×860. Setting seconds to 60 disabled Create. Closing Advanced and changing context tokens did not revive the invalid draft. Repairing the duration to 0 hours, 1 minute, 1 second showed exactly 61 seconds; the saved configuration retained 61. Source selection and Create did not start an experiment. The explicit readiness check contacted only the owned synthetic fixture.

The [bounded synthetic plan](packaged-synthetic-plan.json) used seed 20261015, cadence 10, 1,000-ms pace, 31 steps, four attempts and 32 MiB. Its session was `sustained-1791918426303-1`. The first explicit Start reached step 10 and retained the fixture's HTTP 503 failure with zero journals. Retry and Skip were visible; the review disclosure could be closed and reopened with Space. Cmd-Q from this fully committed blocked state exited directly. That action did not exercise the close-review dialog.

Relaunch showed idle setup. Explicit catalog inspection and Restore retained the failed opportunity without sending another request. Explicit Retry then Cmd-Q displayed the close-review dialog, paused at step 10 with a successfully saved journal prepared for step 11. Return to app and Resume delivered new snapshots, numerical frames and journal updates through step 31. The original four-attempt ceiling held execution with three saved journals. The earlier failed attempt remained part of history.

After the bound was reached, selecting the step-10 journal turned Follow latest off. Its full prose stayed readable, with first application at 11. Opening Evidence exposed the retained identity, readback hash, exact prompt, raw reply and feedback/application information. This particular selection happened after execution ended; it is not a claim of selection retention while new journals arrived.

Native folder export succeeded at revision 56 into `target/qa/0.12.1-reading/exports/sustained-1791918426303-1-2-56`. Cmd-Q then exited cleanly; [the final UI receipt](packaged-synthetic-final-ui.json) records process absence at 19:11:50.113197 UTC. Independent replay and request joins have separate receipts in this directory. The [first UI receipt](packaged-synthetic-first-ui.json) preserves the setup, failure and first quit observations.

## Defect retained for the follow-up

After Retry succeeded, the paused Prepared close-review panel still displayed the earlier HTTP 503 diagnostic as a current alert. It appeared again when the run reached its attempt limit. The journal itself was saved and applied correctly; the defect was the presentation of historical diagnostics during a different attention state. The fix must keep that diagnostic in history, show actual current failures, and avoid presenting the resolved failure as a current obstacle. These observations belong to 0.12.1 and must not be described as checks of the later fix.

Inline screenshots were inspected; no screenshot files were saved. The Checkpoint and quit button, physical power loss, total WebKit/GPU resources, other operating systems and collaborator acceptance were not qualified by this check.
