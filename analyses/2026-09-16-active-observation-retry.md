# Active-state journal comparison: retry and diagnosis

September 16, 2026. Mike explicitly asked to retry the unavailable active-state recording and diagnose the cause. This is a new, separately registered attempt under the frozen S-009 amendment; the original unavailable receipt and correction remain unchanged.


The original connection failure was caused by a stopped temporary local Ollama service. The previously qualified `phi3:mini` model was still installed and every model blob matched its recorded identity. An owned, loopback-only Ollama 0.32.15 service was started for one separately registered retry, then stopped. No download, provider substitution, automatic retry, or live Being change occurred.

The retry reached a different limit: the added-state response at step 60 copied the coordinate list until it reached the frozen 256-token ceiling. Its JSON was incomplete, so the app correctly admitted no journal from that response. The paired sensory-only request still completed, and the run stopped before step 90.

| Opportunity | Sensory-only arm | Added-state arm | Request order |
|---|---|---|---|
| 30 | Journal saved | Journal saved | Sensory, then added state |
| 60 | Journal saved | Incomplete response, no journal | Added state, then sensory |
| 90 | Not reached | Not reached | No requests |

Both arms retain identical numerical trajectories through all 60 recorded steps. The file contains four requests, three saved journals, and the full failed response. Verification succeeded; generation did not complete its planned 120-step run.

Open **Runs & examples → Separate comparisons & mechanisms → What can the journal observe? · active input**, choosing the **Recorded model run · phi3:mini · failed · 60 of 120 steps** entry. Use Next journal to inspect 30 and 60. Preparation history contains the original report, correction and separate retry report. Replay is offline.

The frozen settings were preserved: prompt version 2, JSON output, temperature 0, context 4096 and output limit 256. The 40-word instruction did not prevent array copying. A useful next study would separately qualify a constrained short-output format. Silently increasing this run’s limit or generating replacements would change the comparison.

The audit also retains selected factual discrepancies in the completed prose. There is no writing-quality score or evidence of a general improvement from adding coordinates. See **Evidence/OUTCOME-AUDIT.md** and the complete record. Human newcomer acceptance remains pending.

## Product follow-through and verification

Reservoir Scope 0.13.1 build 18 bundles the complete partial record and separate retry report. The browser shows the actual 60 of 120 steps, preserves original/correction/retry history, and exports each report separately. At the failed opportunity the journal pane says that no journal was saved and labels the retained incomplete response. The guide now explains that fresh generation requires an already-running local service.

All 22 copied-app records verify with network, model files, original source paths and the original recording folder denied. All 21 earlier example records, the original unavailable receipt and its amendment are byte-identical. The headless runner is byte-identical to 0.13.0, with its previous core and mechanism checks retained. Exact compiled-source identity matches 53 current source files. Only two presentation files and the build script changed among compiled-source identity entries; no numerical or model-request behavior was changed. See the [patch verification account](../native/ReservoirScope/validation/0.13.1/VERIFICATION.md).

Evidence and exact recipes are in `research/outputs/2026-09-16-active-observation-retry/`. The pre-run authorization, original model manifest/blob hashes, runtime identity, service lifecycle, model inventory, each raw response and journal, record verification, and independent audit are retained. `verify-outcome.py` reproduces the consistency and selected-fact checks without generation. Final native presentation and delivery receipts are in `native/ReservoirScope/validation/0.13.1/`.

This is a failed generation run with successfully preserved evidence. The observed truncation does not imply that every request with coordinates fails, and the first paired opportunity completed. No general writing-quality or fidelity gain is inferred. A future constrained-output trial should be separately specified before generation, preserving this attempt. Human newcomer acceptance remains pending. No live Being or S-007 daily process, ledger, or automation changed.

## Board updates pending

The Artifact connector remains unavailable; no board update is claimed. Pending finding: original local preparation availability was due to its intentionally stopped owned service; one authorized retry verified the qualified identity and produced a failed-but-verifiable 60-step paired record with four requests and three saved journals. Pending change: 0.13.1 exposes the partial run, request failure and separate preparation history. Pending question: qualify short-output reliability under a separately declared protocol. Link this account and the preserved evidence; retain the open human newcomer check.
