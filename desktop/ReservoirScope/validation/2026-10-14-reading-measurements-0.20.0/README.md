# Reading measurements and journals · 0.20.0

October 14, 2026. The macOS ARM64 package passed source checks, fourteen historical replays, fixed synthetic HTTP/save/application checks, seven reanchored rejection cases and native export/recovery checks. Existing v7 journals were also read in the new reader. **No real-model v8 writing episode was run in this qualification.**

The [protocol](PROTOCOL.md), [prompt template](PROMPT-V8-TEMPLATE.txt), [qualification plan](QUALIFICATION-PLAN.md) and [native plan](NATIVE-QUALIFICATION-PLAN.md) describe the intended scope. The [prospective freeze](prospective-freeze-01.json) bound 45 inputs before the fixture and native session. [MACOS-UI.md](MACOS-UI.md) records actual controls, observations and limits.

## What changed

Fresh sessions use `reservoir-journal-v8`. Its compact readout explains recurrent RMS, distinguishes sensory fill from encoded text input, and identifies L2 distance as displacement between two recorded state vectors. Two observations do not establish an intervening path, cause or felt state. Apart from the version header and this explanation, the v7 prompt remains intact: exact prior saved/applied text, late writing boundary and open invitation. Full observation-v2 evidence remains retained. Historical versions remain identifiable rather than being rewritten as v8.

The reader adds Earlier/Later entry navigation and an explicit Pause following selection. Journal prose stays unchanged; current live progress and the selected entry's recorded measurements remain distinct.

## Executed checks

| Check | Retained outcome |
| --- | --- |
| Rust core | 219 passed; the final receipt carries the first run's result after verifying unchanged core inputs |
| Desktop Rust | 198 passed, 2 ignored; strict all-target core and desktop Clippy passed |
| Frontend | 375 tests in 40 files passed; TypeScript passed |
| Pure qualification helpers | 41 tests passed |
| Package | Locked, SDK-bound build and reference check passed; 46 package files verified |
| Historical exports | All 14 selected cases passed; 665 files preserved |
| Synthetic wire/save/application | Five exact responses; four complete replies saved/applied, fifth incomplete and held |
| Reanchored negative exports | Seven expected production-verifier rejections; original passed before and after |
| Clean recovery | Both exports passed; all 27 nonmanifest files remained byte-identical |

The failed initial [Rust check](rust-checks-01.json) and [frontend check](frontend-checks-01.json), with their logs, remain preserved. They are not replaced by the corrective [Rust run 02](rust-checks-02.json) and [frontend run 02](frontend-checks-02.json). The Rust rerun explicitly records its unchanged-input reuse of the 219 core tests and the corrected desktop test expectations plus v8 comparison coverage. [Helper checks](synthetic-harness-tests-01.json) bind their own unchanged sources; these pure tests did not launch a provider or app.

## Exact package and preserved history

The [build receipt](package-build-01.json) binds the final source inventory before and after the build. [Archive verification](archive-check-01.json) binds version/build `0.20.0`, bundle identifier `research.reservoir.scope.tauri`, extracted resources and the pinned executable.

- Pinned executable SHA-256: `cc5d3dce19076dbc1ff3b850cd99a72a410c8fa797d951cb11f4068ecaab1cfd`.
- Archive SHA-256: `23fe012b90bca660773c63f58bd1bc916c26c9b74a0081b7e59d0603ec117e25`.

[Pre-UI package verification](qualification-before-ui-01.json) passed local codesign verification with an **ad-hoc signature and no TeamIdentifier**. This is not notarization, public distribution approval or user acceptance.

The previous full 0.19 app, archive and pin were [copied and verified before replacement](prior-package-preserved-01.json). The [prior v7 evidence inventory](prior-v7-evidence-inventory-01.json) preserves the refused episodes separately from completed episode 03. The [preparation source capture](source-before-preparation-01.json) is a dated inventory, not the final build freeze.

[Historical production replay](historical-replay-01.json) verified selected v1, v3, v4, v5, v6 and v7 exports, including complete twelve-entry original/recovered pairs. All 665 selected files, associated basis receipts and the pin remained unchanged. No historical v2 export was selected; generated v2 compatibility tests are a separate source-level check. Replay contacted no models.

## Synthetic session and recovery

The [fixed configuration](packaged-ui-plan-01.json) used the unchanged, explicitly synthetic provider. Session `sustained-1792004958844-1` saved replies at steps 10, 20, 30 and 40 and first applied them once at 11, 21, 31 and 41. The fifth response at 50 was incomplete: it produced no journal or new feedback. The final core remained blocked with four journals and 22 segments. No retry, skip, cancellation, budget extension or second Start was used.

The [original export checker](original-export-evidence-01.json) joined exact request/prompt/response hashes, the v8 explanation and unchanged late boundary, full prior text for all four memory reads, wide/absent/unusable provider metadata, and numerical save/application evidence. Optional provider counts did not become a save gate or proof of full-context processing.

After clean quit, idle relaunch and explicit paused Restore, the [recovered export](recovered-export-evidence-01.json) passed the same checker. [Direct comparison](recovery-comparison-01.json) found 28 files in each export and 27 identical nonmanifest files. Only manifest generation 1→2, revision 76→77 and wrapper phase `attemptBlocked`→`paused` changed. The core stayed blocked; Resume remained disabled. This qualifies the observed clean recovery, not crash or power-loss recovery.

The [stopped-provider receipt](provider-stopped-01.json) retains eight exact fixture files and records one readiness GET, five generation POSTs, five completed response writes and no unplanned requests. Explicit stop ended its recorded lifetime at 206.250198 seconds. Parent-observed tool exit 0 is attributed separately; the file audit did not make a fresh process-absence or endpoint probe.

[Seven tamper cases](reanchored-tamper-01.json) changed clock, recorded return, authority, boundary presence/location, manifest version or the v8 explanation. The six prompt mutations repaired outer byte/hash anchors while preserving typed core payloads; the manifest-version substitution is a separate seventh case. The packaged verifier rejected each for the intended semantic mismatch. [Execution continuity](tamper-execution-continuity-01.json) preserves the original positive bundle, executable and helpers. Separate core tests cover typed-checkpoint rehashing; these Python mutations do not claim that scope.

## Native reading with preserved v7 prose

[Native observations](MACOS-UI.md) distinguish the four-entry synthetic navigation check from frontend tests for asynchronous arrival and page boundaries. The selected entry's measurements remained tied to that entry, and changing entries reset Measurements and Evidence to closed.

The [historical v7 reader check](v7-reader-native-01.json) then restored the completed owned session `sustained-1792001665258-1` paused, without readiness, Start, Resume, Retry or a model operation. Earlier selected entry 11 at observed/applied steps 330/331; Later selected entry 12 at 360/361. Evidence retained the explicit v7 identity. All 72 managed nonmanifest files stayed unchanged; only generation 2→3 and revision 424→425 changed, with the wrapper still paused. Prior immutable exports were preserved. The app was left paused at step 361, entry 12 selected and Follow latest off.

## Limits and next observation

This tranche establishes bounded software and agent-operated native behavior on this macOS ARM64 package. It establishes no improvement in real v8 prose, model understanding, creativity, causal fidelity or provider context coverage; no new GPU, energy, endurance, crash/power-loss, Windows/Linux or accessibility qualification; and no human acceptance. No Being system was contacted or modified.

A real-v8 writing assessment remains a separate future episode. It needs its own prospective configuration, exact package/runtime/model identities, unchanged resource-admission and isolated-service safeguards, bounded lifetime and complete accounting of every planned opportunity. Full prose should then be read against what was actually supplied and retained, separating literal claims from imagery and continuity from repetition. This synthetic qualification neither launches that episode nor supplies its outcome.
