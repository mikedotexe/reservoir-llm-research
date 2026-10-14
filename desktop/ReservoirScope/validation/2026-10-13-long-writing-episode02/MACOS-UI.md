# Native twelve-turn session and paused recovery

The parent operated the actual unchanged 0.16.0 r2 application through native UI.
Its executable SHA-256 is
`73872388b56d2483054497aa8513e3659f79df255699d6bca29041cafd258d`.
This account describes agent UI checks, separately from offline verification,
prose interpretation and future human acceptance.

## Start and completion

The [before-Start binding](bound-before-start-01.json) retains the prepared
session `sustained-1791938932286-3`, generation 3/revision 1, at step zero with
zero journals. One explicit readiness check matched the privately staged Gemma3:4b
manifest at the owned `http://127.0.0.1:58180` endpoint. Accepted configuration
matches the frozen plan: v4, seed 20261013, observations every 30 steps, 361 steps,
twelve attempts, 900 active seconds, 64 MiB, one-second pacing, 8,192 requested
context tokens, 1,024 output tokens and a 180-second request deadline.

[Native Start](native-start-01.json) was observed running at step 1, with no durable
numerical step yet. Its receipt was written after the observation, not at the
click. [Preparation review](PREPARATION-AUDIT.md) preserves that timing limitation.
The [midrun view](ui-midrun.txt) showed six saved entries at live step 195, retained
through 181, with Follow latest on. No pause, retry, skip or control change was made.

[Completion](native-completion-01.json) showed twelve saved journals and twelve
attempts at live/durable step 361, Run budget reached, with Pause and Resume disabled.
The UI displayed 9 minutes 56 seconds; the exported manifest retains 596,666 ms.
The final journal belongs to observation 360 and first application 361. These
boundaries do not certify the model's prose or authenticate provider execution.

## Two real exports and one clean relaunch

The first Export committed session bundle action opened the native folder chooser.
Go to Folder selected the new episode's owned `target/qa/0.16-long-writing-episode02/exports`
parent. Return and Open worked in this episode. The UI confirmed publication and
displayed [export revision 423](ui-export-receipt.txt), producing the distinct
`sustained-1791938932286-3-3-423` bundle. No live-store copy substituted for export.

After run completion the parent created the exact owned supervisor's stop-request
file. Its supervised process finished successfully; [cleanup](CLEANUP-RESULTS.md)
keeps the ownership proof and lifetime separate. The parent then used Cmd-Q, checked
[`isRunning=false`](native-quit-01.json), and relaunched the exact same app path.
[My reservoir was idle](ui-relaunched-idle.txt), offering Create rather than resuming.

The parent opened Inspect and recover, read the catalog, selected the exact
completed session, verified its committed chain, then chose Restore paused for
review. [Recovery](native-recovery-01.json) showed generation 4, twelve journals,
live/durable step 361 and disabled Resume. It performed no provider readiness,
generation, retry or reconnection. Accepted configuration stayed unchanged.

A second native folder chooser exported `sustained-1791938932286-3-4-424` into the
same parent, leaving the original directory intact. [The native confirmation](ui-recovered-exported.txt)
reported revision 424. [Offline recovery checks](RECOVERY-RESULTS.md) own the
separate replay and exact file comparisons. The final app remains paused with the
last entry selected and Recorded measurements, Evidence, configuration and recovery
disclosures closed. The full journal texts are retained even though macOS
accessibility text observations truncate long text nodes.

These are clean-relaunch and exhausted-budget checks on this Mac/package. They
are not a physical crash/power-loss test, a minimized or multi-hour run, GPU/power
measurement, complete accessibility review or Windows/Linux acceptance.
