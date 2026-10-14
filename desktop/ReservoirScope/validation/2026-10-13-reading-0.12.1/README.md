# My reservoir reading and setup pass — source qualification

This directory records the completed frontend experience pass on 2026-10-13. Final integrated source checks passed **323 tests across 36 files** and `npx tsc --noEmit`. An isolated browser fixture was also visually exercised. **No production build or native packaged-app qualification of these changes is recorded here.** The running, frozen 0.12.0 reliability package remained separate; `0.12.1` names the intended follow-up work, not an already-qualified package.

## What changed

- Setup keeps the reply source visible: deterministic synthetic writing or an explicitly selected local Ollama endpoint and model. Local-model readiness remains an explicit action. Creating a session prepares local state; Start remains separate.
- The initial form shows writing cadence, requested pace, duration and storage, plus the accepted step and attempt ceilings. It explains that the first bound reached holds execution. Seed and detailed numerical controls are under a closed **Advanced settings** disclosure.
- Duration uses hours, minutes and seconds while preserving every valid integer duration from 1 through 86,400 seconds. Invalid drafts disable Create rather than silently rounding, clamping or reusing an earlier valid duration. Human-readable status durations do not replace the exact retained seconds in the measurements disclosure.
- The session header emphasizes saved journals, elapsed time against its limit, and storage against its budget. Live and retained step numbers remain visible. Numerical, simulated-time and attempt details are under **Session measurements and limits**.
- Journal text is readable prose, preserving line breaks and complete text. Saved/applied/skipped status and the first application boundary stay visible. Identity, hashes, prompt, numerical observation, memory, request timing, encoded feedback, application evidence and raw reply remain in a closed **Evidence** disclosure.
- Independent journal selection and **Follow latest** remain separate from the live numerical clock. Routine writing detail is collapsed; a storage or writing problem opens the review controls and shows an attention state. Diagnostics and exact accepted configuration remain available below the primary reading flow.

This pass changes presentation and frontend validation. It does not establish model quality, learning, new save durability, or recovery correctness. The source continues to distinguish journal text, full-text prompt memory, encoded feedback, reservoir state and the separate sensory field.

## Executed source checks

Commands ran from `desktop/ReservoirScope`. Times below are UTC; all earlier outcomes remain retained.

| Evidence | Result and scope | Execution interval |
| --- | --- | --- |
| [Setup focused receipt](setup-source-checks-01.json), [test log](setup-focused-01.log), [type log](setup-types-01.log) | 7 focused tests passed, including exhaustive round-trip coverage of all 86,400 valid integer durations, invalid-input rejection, source selection and no automatic create/start or readiness invocation; type check passed. | Tests 18:12:58.937318–18:12:59.977827; types 18:12:58.937840–18:13:02.223816 |
| [Journal focused first receipt](journal-focused-01.json), [log](journal-focused-01.log) | 3 tests passed and 1 assertion failed. The test expected a token count without the existing stop-reason prefix. This was not a production rendering fix. | 18:10:35.838072–18:10:36.771293 |
| [Journal focused second receipt](journal-focused-02.json), [log](journal-focused-02.log) | All 4 focused journal rendering tests passed after correcting that assertion. Source rendering keeps evidence inert and optional while preserving text and provenance. | 18:11:12.549514–18:11:13.069353 |
| [Integrated first receipt](integrated-01-qualification.json), [test log](integrated-01-frontend.log), [type log](integrated-01-types.log) | All 323 production tests passed, but the command **failed** because Vitest also discovered two copied test files in `source-before/` whose relative imports were unavailable. Type check passed. This run is not recorded as an overall pass. | 18:14:42.891838–18:14:46.390795 |
| [Integrated final receipt](integrated-02-qualification.json), [test log](integrated-02-frontend.log), [type log](integrated-02-types.log) | **323 tests / 36 files passed; type check passed.** Includes the attention-state color and repaired source-snapshot filenames. | 18:21:34.819000–18:21:39.229833 |

The [backup extension note](source-backup-extension-note.json) records renaming the retained source snapshots to `.txt`, preserving their contents while preventing test discovery. The failed integrated-01 logs and receipt are unchanged. The [before-edit inventory](before-edit.json) and retained `source-before/` files preserve the starting point.

The integrated-02 receipt contains identical before/after inventories of 112 source files. It binds the checked source without asserting a production build. Its frontend subprocess ran at 18:21:34.838827–18:21:36.877836; its type-check subprocess ran at 18:21:34.838919–18:21:39.229548.

## Receipt and source identities

SHA-256 identifies the exact evidence files. Complete source inventories remain in the receipts.

| File | SHA-256 |
| --- | --- |
| `before-edit.json` | `773574f4f28cfb8a7293f2ba4d6ebe0e5b626f7cbf724f31d7c9b0e482e33e92` |
| `setup-source-checks-01.json` | `e278d2d6459257746a65930cd390e47d57e1d62eabb424c6ec88d726b948c141` |
| `journal-focused-02.json` | `8826adef5698451e0a4746cfb0e428d57d1d914a9e98bf63c3f11970da04085d` |
| `integrated-01-qualification.json` | `ae83534aa91b7d1f7e2639487ec3235ef942a36f0c91494816973625df354b5c` |
| `integrated-02-qualification.json` | `75127d1ea4829b8f56779da5ce4673c222eab23b3f894489976f427da99272ba` |
| `integrated-02-frontend.log` | `b33ea110406b797e87ab259f7402145eebcb63367759306c450895a8db079e3d` |
| `integrated-02-types.log` | `68436e94592e2a07bfda62bed19b9f28cb234bfe95b6fd989df310b8f0802786` |
| `source-backup-extension-note.json` | `e4ac2c5fdbea8e0836bde025d7248f3560d57525e3b57975d5150cefdea0a365` |

Selected integrated-02 source identities:

| Source path | SHA-256 |
| --- | --- |
| `src/MyReservoir.tsx` | `7d390abb7f1c262eb6ef58b5816b748ae2a7f88b20f7c4ea214edf05060db40c` |
| `src/MyReservoirConfig.tsx` | `7f0203ab82a0a773f1b89a719fcf2d266674257c88cffda2b4e1c7aa22457f69` |
| `src/MyReservoirJournals.tsx` | `50292864df2cf6d7ce439b5e39197b5d7077f0253fc7976fd53aba392277808e` |
| `src/MyReservoirVisuals.tsx` | `eee94f36caed55836e40d2735c4eef0826456da2a9ab8ebc94f9d4dc7a120b5b` |
| `src/myReservoir.css` | `1fc4ac9c1c225c078882b9ada776ea28294c5f44e62b3499aa2115f1b4208004` |
| `src/sessionDuration.ts` | `3188acdac677a47a19772fd6f3bff836ea0f71b113410849ba9edd3a28d2db15` |

The receipt records the separate frozen package executable as 16,747,744 bytes, SHA-256 `f68a3752a628edf11ac6161a26e6979bb22dcf4c3ee1c63f10add2cea86ab40d`. These frontend edits were not built into that executable.

## Browser fixture and concurrent host work

[BROWSER-UI.md](BROWSER-UI.md) records the actual in-app-browser fixture checks and their limits. The owned Vite preview began at **18:16:59.981049Z**. The browser tab was closed first, and the owned server was stopped at **18:21:02.432561Z**, as recorded in [preview-closed.json](preview-closed.json).

That close preceded the reliability analysis late-window start, **18:21:05.920848Z**, by 3.488287 seconds. However, the final integrated source checks at **18:21:34.819000–18:21:39.229833Z overlapped that late window**. They are concurrent host work and must remain disclosed when interpreting the frozen app's resource measurements. This directory makes no CPU, GPU, energy or resource-isolation finding. Source edits and documentation work also do not turn that interval into an idle-host control.

## Limits and next qualification

The browser used mock session APIs, simulated state and synthetic prose. It did not exercise Tauri IPC, actual numerical execution, real model readiness/generation, automatic file publication, export dialogs, recovery, native close behavior, or backend storage admission. Inline screenshots were visually inspected during the tool session; no screenshot files were saved. The browser check preceded the final attention-color source adjustment, which is covered by integrated-02 source checks but still needs a final packaged visual check.

The following remain pending for a separately identified 0.12.1 package:

- Build and bind the final package to its source, executable and archive identities; do not reuse the frozen 0.12.0 package's qualification for these edits.
- Verify the calmer setup, exact duration validation, explicit source/readiness/Create/Start flow, and layout in the native webview.
- Read an earlier actual saved journal while new entries arrive; verify stable selection, Follow latest, complete inert prose and expandable evidence.
- Exercise actual held/error states and their Retry/Skip controls, committed-prefix export, and close/discard language against the repaired backend.
- Qualify relevant accessibility, keyboard navigation, window sizes and platform behavior separately; they are not established by this fixture.

A subsequent independent source review found no concrete blocker and confirmed the
controller hash matches the earlier quota and integrated frontend receipts. Its
additional packaged interaction checks are: invalidate a duration, collapse Advanced,
edit an unrelated field and confirm Create stays blocked until repaired; keyboard
open/close Writing and feedback across a new blocked transition; and keep an older
journal selected while newer saved entries arrive. This was a read-only source review,
not another test execution or native UI observation.

The [local-model selection handoff](REAL-MODEL-SELECTION.md) is prospective and separate. Its cached-model audit is not a model execution result. Historical receipts in this and earlier directories remain evidence of their own source/package states.
