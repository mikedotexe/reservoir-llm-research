# Native episode 02: writing, reading, export and paused recovery

This account summarizes the parent operator's retained native UI receipts for the unchanged **0.15.0 macOS arm64 package**. Its executable SHA-256 is `18949732cf48c926003ffcf7b5b216bccc32ea071d0bff8a411e841eaba123d5`. Writing accuracy is reviewed separately; showing a recorded value does not validate the prose.

## Explicit start and independent reading

The separately identified episode passed its single host admission. The [pre-Start binding](bound-before-start-01.json) records the accepted v4 configuration, exact Gemma manifest, owned endpoint and 1,162.76 seconds remaining on the 1,200-second service lifetime, above the required 960 seconds. Create remained prepared at step zero. After one explicit readiness check, [native Start](native-start-01.json) began session `sustained-1791932015615-3`, generation 3, around 22:54:01 UTC. The prior refused episode and scripted exports remain separate.

[During reading](native-reading-01.json), the first saved journal belonged to observation 30 and was first applied at 31. It stayed selected with Follow latest off while the engine reached 60 and waited for the second writing response. Its reference still showed observation-30 values and unavailable prior measurements; the live cursor did not substitute new values into the selected entry.

The [completion receipt](native-completion-01.json) records 121 steps, four attempts and four saved journals, applied at 31/61/91/121. Step 30 remained selected. Pause and Resume were disabled at the reached budget, and export was enabled. No retry, skip or extra comparison request occurred. The UI showed 4 minutes 28 seconds; the verified original manifest retains **268,158 milliseconds of session running time**. This differs from the [supervisor's 325.916913-second lifetime](CLEANUP-RESULTS.md), which includes readiness and idle time.

Selecting the [final journal reference](native-final-reference-01.json) showed observation 120, prior observation 90 and application step 121 while the live state was 121. Its fill values were 14.991311840032465% and 12.307786573702538%, with a +2.6835252663299265 percentage-point difference. These are retained measurements at the writing boundary, not a claim about the journal's interpretation.

## Native exports and recovery

The [original export](native-export-01.json) used the actual native folder chooser and produced generation 3 / revision 143 with 121 steps, four journals and 19 segments. The [independent export receipt](real-model-export-01/receipt.json) confirms **25 files**, 1,912,042 bytes, passing pinned whole-chain replay and unchanged originals.

The [recovery receipt](native-recovery-01.json) records clean quit with `isRunning=false` confirmed before relaunch. The same package relaunched idle. The operator selected the exact owned session, verified and inspected it, then explicitly restored it **paused** at generation 4 / revision 144. Resume remained disabled at the exhausted budget; no reconnect or Start was requested. Accepted configuration and the final journal's 120/90 reference were unchanged.

A second native export contains **25 files**. All **24 non-manifest files are byte-identical** to the original. Only manifest generation `3→4`, revision `143→144` and phase `budgetReached→paused` changed. The checkpoint hash remained `61ad06d295046cea7035eb5c4cc50713c6b3b4f49332c8517654f78e2b5a2254`; the recovered bundle is 1,912,035 bytes. [Pinned recovered replay](recovered-cli-01.json) passed with no diagnostics or model contact.

The owned model service was stopped separately after completion; its scoped cleanup is recorded in [CLEANUP-RESULTS.md](CLEANUP-RESULTS.md). This is agent-operated native workflow evidence, not a physical crash/power-loss test, a new minimized-duration or GPU/power qualification, broad accessibility/human acceptance, or Windows/Linux acceptance. This account itself performed no UI, process or model actions.
