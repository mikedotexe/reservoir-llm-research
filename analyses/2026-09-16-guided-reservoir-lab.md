# Reservoir Scope 0.13 · a guided journey from state to journal

Completed September 16, 2026 (America/Los_Angeles), for version 0.13.0 build 17. Evidence files named below are retained in `native/ReservoirScope/validation/0.13.0/Verification evidence/`. Automated and agent-operated checks do not establish newcomer comprehension.

This implements Mike’s accepted [product review](2026-09-16-reservoir-scope-product-review.md). The [guided user guide](../native/ReservoirScope/docs/GUIDED-TOUR.md) explains the route. The complete release verification evidence is retained in [the versioned validation directory](../native/ReservoirScope/validation/0.13.0/VERIFICATION.md). This is product and synthetic-mechanism work under S-009; S-007’s daily ledger, automation and the live Beings remain untouched.

Delivery: `/Users/mikepurvis/Applications/Reservoir Scope 0.13.app` and `/Users/mikepurvis/Downloads/Reservoir-Scope-0.13.0-arm64.zip`. The matching headless runner, guide, acceptance worksheet and evidence are inside the archive. Final archive identity is in `native/ReservoirScope/validation/0.13.0/delivery-receipt.json`.

## Implemented behavior

The default Guided tour follows A–H using verified local recordings, meaningful checkpoints, stage-specific evidence, and separate expected, observed, and interpretation text. Journal-bearing stages offer scripted examples and existing recorded model runs. Information-flow labels distinguish the separate sensory field, supplied model context, journal memory, and next-step feedback. Experiments remain available separately, and the example browser groups guided examples, recorded writing, comparisons, saved runs, and preparation history.

Recording playback only moves its cursor. In E, Step moves from a journal saved at 30 to its recorded application at 31 without creating a session or changing the record. Active experiments traverse existing history before computing another step; failed or cancelled runs require explicit new-experiment preparation. Viewing an existing recording does not create a library copy. Save recovery, cancellation, late-response rejection, and quit-time persistence remain covered.

New action records use `essentials-actions-v3`, with an explicit forcing profile; v1/v2 replay and verification remain supported. The separate controller example uses `essentials-regulation-v1` and the headless `regulation` command. Its visible partial-window summaries use only observations at or before the cursor.

## Automated and presented checks

| Check | Recorded result | Evidence |
|---|---|---|
| Shared numerical core | 65 tests, zero failures | `core-tests.log` |
| Native action lifecycle | 67 checks passed | `actions-ui.log` |
| Guided evidence and controller summaries | 37 checks passed; no provider calls | `guided-checks.log` |
| Comparison view/layout | 23 checks passed, including H at 1100 × 820 | `comparison-layout.log` and its receipt |
| Presented inspector | 5 checks; seven disclosures expanded by an independent accessibility client; ten native scrolls | `local-inspector/layout.json` and `accessibility.log` |
| Guided presentation | A–H scripted and D–H recorded-model routes: 13 cases | `presentation-route.json`, screenshots and accessibility captures |
| Navigation | Seven checks: controller partial/final results, active observation, grouped browser, D import routing, guided progress restoration, stopped experiment preparation | `presentation-navigation.json` |
| Action CLI validation | Nine pairs; 12 malformed exports rejected | `action_cli_smoke.log` |
| Provider failure handling | Five action HTTP cases and five original language HTTP cases passed | `action_http_smoke.log`, `http_smoke.log` |

The presented tour used an 1100-pixel-wide window with an 820-pixel content height (852 including its title bar). These were agent-operated checks. Earlier failed navigation and remote inspector attempts remain in the evidence directory; the later successful receipts above are the reported results. On the final binary, actual Tab and Space reached Continue (A, step 1→12), opened evidence, and reached Step (12→13). Focus and before/after cursor captures are retained in the keyboard check files. This is a bounded keyboard control check, not a keyboard-only newcomer acceptance test.

## Disconnected operation and portability

A copied application and its bundled runner were exercised with network access denied and the repository, original source roots, and mounted paths unreadable. All 21 bundled records verified; fresh 120-step scripted runs completed for all eight stages. Production native view-model/store checks separately created 31 steps per stage with the 300-step interactive default, persisted journals, flushed for termination, and reopened records in new model instances. They also verified E's recorded 30→31 transition, imported the controller record, retained legacy formats, and rejected two altered imports. See `disconnected-final/receipt.json` and `disconnected-final/native-exports/native-store-receipt.json`.

The presented app used the same network/source-path denial policy; launch profiles are retained in `presentation-pid.json` and `final-presentation-pid.json`. Final preparation-history inspection confirms the unavailable report, correction explanation and separate correction export are visible. A separate-account check copied exports from `mikepurvis` to account `v`: all eight stage exports and the controller export verified with the original account paths, repository paths, mounted paths, and network denied. This is a nine-record headless portability check, not a second-account GUI usability test. See `cross-account-receipt.json`.

All 19 examples retained from 0.12.0 are byte-identical, including six full model recordings and four preparation attempts. The two added records are the active-input scripted observation comparison and the controller mechanism example. See `retained-example-identity.json`.

## What the added examples establish

The active-state scripted comparison qualifies matched trajectories and prompt transport at steps 30, 60, and 90. Maximum absolute state at those opportunities is respectively 0.8369444562, 0.6268849798, and 0.8202865093, exceeding the declared 0.25 threshold. Scripted output does not establish an effect on model writing.

The attempted preparation of a new active-state `phi3:mini` recording stopped when the explicit loopback endpoint refused its inventory connection. Its receipt records `unavailable`, an empty attempts list, and no generation requests. Existing model recordings remain available offline. No service startup, model download, provider substitution, or live retry was performed.

A review identified that this unavailable preparation's inherited prompt version was 1 while its manifest described the version-2 40-word instruction. No model output was produced under the inconsistent declaration. The original unavailable receipt is retained unchanged. A separately frozen amendment declares version 2 for future qualified preparation. Two mocked preparation checks passed without network or model calls. This amendment is not a new recording attempt. Evidence: `active-observation-preparation/guided-observation-amendment.json` and its mock qualification. The original receipt and correction can each be exported from the app’s preparation history.

The controller example reproduces the established 600-step synthetic qualification with field seed 98, input seed 42, and identical 66-coordinate input. Across the declared 300 paired observations at steps 301–600, mean absolute error from the 68% target is **11.924755885 percentage points** with fixed retention and **4.159937144** with regulation. This establishes lower target error for this fixed mechanism example. It contains no reservoir or journal component and does not imply that the short H example attains its target.

## Remaining acceptance and final package identity

The uncoached, approximately fifteen-minute first-time human researcher check is **pending**. `NEWCOMER-CHECK.md` records the tasks and fields for reporting actual answers, evidence, time, and assistance. Automated checks and agent-operated screenshots are not substitutes.

- Application: **0.13.0 build 17**. App and matching standalone runner both pass ad-hoc signature verification.
- Packaged identity: `release-identity.json`, SHA-256 `395afb9e8423831aee741e9f38eb9747d7c6c2405ff8ea6bc2cb1e18aee3fd5f`.
- Source identity: 53 exact source hashes, base commit `69c4195f40db4b9ea83e7e498143ad8de266b100`, and 39 sealed resources. The base commit alone does not describe the uncommitted research build.
- Matching runner SHA-256: `273c8d553365590637b1439b09067200d9564108cfaa712451201c7584d752de`.
- Final binary checks: all 21 records and eight fresh scripted stages pass the disconnected qualification again. Actual process quit/reopen restores E, scripted source, step 31, paused; minimum-width experiment workspace and missing-model-setting explanation are readable. No guide visit adds a saved-run copy. See `final-source-receipt.json`, `disconnected-final/receipt.json`, and `final-presentation-receipt.json`.
- Archive: `Reservoir-Scope-0.13.0-arm64.zip`. Its final SHA-256 and extracted-copy verification are recorded in the adjacent `Reservoir-Scope-0.13.0-arm64.receipt.json`, avoiding a self-referential archive hash.

This release is for trusted Apple-silicon research Macs running macOS 14 or later. Public notarization is outside its scope. Live Beings and daily fidelity tracking were not modified.

## Final archive identity

The extracted archive verifies with network and original source paths denied: 21 records, ad-hoc app and runner signatures, and byte-identical standalone/bundled runner. Archive size 115128375 bytes; SHA-256 `6ed812508b3d57221d3434b417001996b8b67dc93f65d6cceb0ab39119504173`. The app was also installed alongside the previous version and opened at A, scripted, step 1, paused.

## Board updates pending

Board mirroring remains pending because the Artifact connector/authenticated board-control surface is unavailable. The pending update should link this verification account, the guided release implementation, its immutable preparation evidence, the final package identity, and the still-pending human newcomer check. No board update is claimed. `pending-board-updates.json` retains the proposed card updates and session log.

The earlier automated core, lifecycle and lesson checks precede final presentation-only changes. Final disconnected, source identity, signing, minimum-width presentation and actual quit/reopen checks use the delivered application. The numerical runner is byte-identical to the previously cross-account-qualified runner.
