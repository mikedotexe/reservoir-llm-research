# Preview 0.6.0 — unlocked macOS walkthrough

Observed October 12, 2026, approximately 20:54–21:03 UTC, after the user confirmed
the desktop was unlocked. This supplements the earlier blocked `macos-ui.md`; that
account and the original qualification receipt remain unchanged.

## Artifact and scope

The actual shipping application was opened from
`target/release/bundle/macos/Reservoir Scope Tauri Preview.app`. Its visible header
identifies **0.6.0 · Responses & preparation**. Host: macOS 27.0.1, Apple silicon;
observed window: 1280×860. These are agent-operated packaged-app observations,
not collaborator acceptance or qualification of minimum macOS 14.

The binary SHA-256 remains
`334dae56872ab9b4f69c4f694c956db184d45e3d6e098c84bd647cdbf4eb89b3`.
The unchanged archive SHA-256 is
`ea92d5102922891490d8bcf115cd6aa642cd1c5c52522d70b7866d9e648090a5`.
The independent [supplemental export proof](supplemental-export-proofs-20261012T2100Z.json)
checks all 46 package/archive files and 42 resources against retained identities,
plus current strict codesign verification. Signing remains ad hoc, not notarized.
No implementation or dependency change, rebuild or new version was needed.

## Agent UI observations

| Workflow | Observed result |
| --- | --- |
| Native response loading | Observatory → Action responses explicitly loads the bundled rehearsal. Eight applied frames and ten receipt events appear; no live connection starts. |
| Native numerical presentation | Initial coordinate 0 is ordinary `0.24120637774467468`, applied `0.24133089184761047`, retained Float32 difference `0.00012451410293579102`. Difference scale is fixed at ±`0.00012451410293579102`. |
| Paired surfaces | Ordinary/applied surfaces both render in WebGL2 with ±1 scales. Dragging the left surface visibly moves both cameras to the same orientation. Both draw counters advance from 1 to 2. This is a functional rendering observation, not a GPU timing or efficiency measurement. |
| Exact selection | Keyboard entry into the coordinate and boundary number fields selects coordinate 127 and applied index 7 / successful native step 8. Ordinary `0.30066293478012085`, applied `0.30078744888305664`; full-state L2 `0.0010000046140803234`. |
| Non-applied events | Admission receipt 0 and completion receipt 9 open independently. Both explicitly state that the event does not establish an applied state change. Completion retains successful step 8. |
| Native export/reopen | Native Save exports `native-action-response.json`; UI acknowledges original-byte export. Cancelling a subsequent Save retains evidence. Native Open reopens the saved file successfully. |
| Invalid replacement | A test-only copy with `fill: 68` is selected through native Open. The app rejects the unsupported claim with a visible explanation and retains boundary 7, coordinate 127 and the accepted native evidence. |
| Context recovery | Lose graphics context produces a visible exact-values fallback. Restore context returns to WebGL2 ready with boundary 7 and coordinate 127 retained. |
| Separate simulation | Explicit load shows 65 samples, original boundary 200 at sample 0, paired delta `0.0010000000000000009`, fixed ±0.001 scale, return sample 2 and eight consecutive boundaries at or below 10% of initial separation. The UI identifies simulation indices rather than measured seconds or fill. |
| Playback/navigation | Inspect sequence starts simulation playback. Navigating to Experiments and returning shows it paused at sample 15 with the same accepted recording. Exact entry selects sample 64 / original boundary 264; coordinate 0 has identical control/perturbed values `-0.32094100746600834`, delta 0, full-state L2 0. |
| Exact-values mode | Selecting Exact values without 3D displays the table fallback while keeping simulation values and the selected final boundary available. |
| Simulation export | Native Save exports `state-response.json` with an original-byte acknowledgment. |
| Preparation reports | Original status is unavailable with no retained generation attempts; correction is frozen/not executed; the separate retry is failed with historical verification passed, 60 steps, four requests, two left journals and one right journal. |
| Report exports | Native Save exports all three reports independently. Each acknowledgment includes its source hash. Cancelling another retry export retains the selected retry report. |
| Current retry verification | Open retained retry recording navigates to the recording reader, preserves failed outcome and shows verification passed. Expanded details show 120 checked arm-steps, four checked turns, no provider calls, and the report-bound recording SHA `b36b925fa8820feaf8108e54ff710eb5627e7273c5275a09a243850c4b2f0f24`. |
| Library entry point | Preparation history is initially collapsed in the Library. Expanding it and opening earlier attempt 1 produces `example-preparation-1.json`, failed outcome, 30 frames and accepted verification passed. |
| Fill/state regression smoke | Independent bundled recordings open. The rendered fill sphere retains `67.31251478%`, radius `0.8763924052334318`, UTC `2026-09-06T16:09:01.158Z`, session 5316 and three distinct direction estimates. The separate 1,024-row replay explicitly has no row timestamps or paired fill; row 0 coordinate 0 is `0.35750484466552734`. |
| Quit/relaunch | Command-Q exits the app. A read-only process check, before another UI observation, finds no matching executable; see `unlocked-quit-process-check.json`. The same app relaunches and explicitly reloads native responses successfully. It is left open on paired native response surfaces. |

The first post-quit accessibility observation apparently relaunched the bound app;
it is not used as evidence of exit. The subsequent explicit quit/process check and
relaunch provide the bounded lifecycle observation above. No single-instance,
window-close, pending-write or crash-recovery gate is inferred from this check.

## Independent export checks

Five files created by the actual Save dialogs are retained under `target/qa/0.6-ui/`:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| native-action-response.json | 173481 | `15441269152bb282e2456d4d08fddae398879e4b0410cd08f71e80282f09e807` |
| state-response.json | 656181 | `fe97623dcccb4b089ce4e0a1b5cc99ec902793efed8fbfcf1041ce8c865e9100` |
| active-state-preparation.json | 2388 | `43af7942984d699c55a5a406bb3a49f070b520c20a9feb85f9b352b6162a3029` |
| active-state-protocol-correction.json | 4291 | `5618712f55d351768edee9ce54c5d4f7240ee2b2fd63735c92a671f2d8d84230` |
| active-state-retry-20260916.json | 3486 | `227c5f988dcce1d61d40ee0979185ff832f1a760317fa3994f55d27af0baf3bc` |

An independent agent compared all five exports byte for byte against the canonical,
staged, packaged and archived sources, including manifest hashes. Swift and Rust
response readers both accept the actual native/simulation exports and produce equal
complete decoded evidence. Both accept native unchanged replacement and reject the
deliberately altered fill fixture. The JSON proof records tool/source identities
and results separately from this parent agent's native-dialog observations.

These are original-byte retained-evidence exports, not newly generated Rust experiment
records. Fresh-experiment cross-engine verification remains a later gate.

## Remaining qualification

No new implementation test rerun was needed: executable sources and artifacts did
not change. Documentation continuity is recorded separately. This walkthrough
does not establish all M3 workflows, Windows/Linux, minimum macOS, clean-machine
installation, compact/resize/scaled layout, complete keyboard/screen-reader access,
precise canvas picking, single-instance routing, window-close behavior, repeated
open/close resource bounds, sustained sessions or measured GPU/FPS/power/memory.
Human collaborator and steward acceptance remain pending. No live Being runtime,
service, prompt, producer or research schedule was accessed or changed.
