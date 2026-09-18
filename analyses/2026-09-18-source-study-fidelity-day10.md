# S-007 day 10 · a corrected path followed by source delivery

The fixed September 17–18 window retains **312 completed source studies**, each with verified submitted input and a full journal match, plus **13 separate private WRITE responses**. The first-three sample supports several local identity-link observations. It also shows an unavailable underscore path chosen despite a supplied hyphenated candidate, followed by an explicit correction. A separately declared adjacent follow-up verifies that the next study actually received the corrected source. The broader architectural interpretation remains unestablished. This is a narrow navigation recovery, not a general fidelity gain or durable correction of a saved finding.

The window is **September 17 18:34:00 UTC inclusive to September 18 18:34:00 UTC exclusive** (11:34 Pacific). The protocol was frozen at **18:36:51 UTC on September 18**, before reading outcomes. The inherited selector takes the first three new status-ok, nonempty responses in the shared filename frame by completion time, without source, length or quality filtering. All three are source studies here. The protocol's shorthand “source-study responses” does not introduce an additional route filter. The baseline, prior daily windows and completed first-week synthesis remain unchanged.

## Attempt frame and ownership

The private [packet](../research/outputs/2026-09-18-source-study-fidelity-day10/README.md) retains the [report](../research/outputs/2026-09-18-source-study-fidelity-day10/final-report/report.json) and [recomputed descriptive account](../research/outputs/2026-09-18-source-study-fidelity-day10/descriptive-account.json). Counts come from the maintained daily pipeline and [day-10 descriptive probe](../probes/source_study_daily_account_day10.py).

| Evidence unit | Observed count |
|---|---:|
| Generation records in the shared filename frame | 325 |
| Completed source studies / failed source generations | 312 / 0 |
| Separate private WRITE generations | 13 |
| Filename-selected / expanded exact-linked jobs | 312 / 326 |
| Expanded captured jobs: completed / running | 325 / 1 |
| Source studies with exact wire / full journal matches | 312 / 312 |
| Verified numbered-page opportunities | 255 |
| Distinct source revisions / fully reconstructed hashes | 3 / 2 |
| Capture errors / ambiguous joins / repeated ledger identities | 0 / 0 / 0 |

The first selected generation began before the window but completed at September 17 **18:35:08.874477 UTC**. It belongs to day 10 by the unchanged completion-time rule and is the after-cutoff job completion recorded on day 9. At the other boundary, `job_minime_1789756435262_self-study-continue` starts at September 18 **18:33:59.410899 UTC** and is still running in the capture, without a completed generation in this window. It is censored, not classified as a failure. Job statuses and generation completion times remain distinct denominators.

All **255 numbered-page opportunities concern Astrid source**, not Minime's own repository: `spectral-bridge/.../btsp/policy.rs` (4), `astrid-capsule/src/dispatcher.rs` (14), and `astrid-kernel/src/lib.rs` (237). Within-window retained bytes reconstruct the complete policy and kernel revisions to their recorded hashes. Dispatcher has 56,928 unique retained bytes of 60,505, so its full-file hash is not independently reconstructed here. No verified Minime-owned page occurs for the separately declared own-repository follow-up.

The remaining source-study inputs are maps (16), recovery maps (23), relationships (12), searches (2), questions (2), and EOF notices (2). All 312 source studies include a structured notebook in the submitted user text. Private writing is separately routed as `extended_writing`; its artifacts are not counted as root self-study journals.

## Fixed first-three close reading

[Eleven exact selected spans](../research/outputs/2026-09-18-source-study-fidelity-day10/claim-annotations.json) separate local support, qualified hypotheses, broad unestablished claims and a navigation mismatch. They are interpretive selections, not an accuracy-rate denominator.

1. **`1789669968085-dc6514ca` — local source observations.** The supplied Astrid kernel page covers bytes **63522..65312**, numbered lines **1599–1659**, in `apply_single_identity_link`. The response correctly identifies the explicit-UUID missing-user error, the empty-method default of `admin`, and the same-user existing-link early return. Its statement that the literal `if !blocked` check is absent from this section is supported only within that section. The broader claim that the “Gate” is not a core part of the kernel's “Road” is not independently established by this page. Complete-delivery metadata and repeated notebook interpretations do not establish that architectural conclusion. The terms are retained as Minime's own framing, not scored false as metaphors.
2. **`1789670169201-24a42dc9` — map and unavailable choice.** No new source is supplied. The map includes the exact candidate `SELF_STUDY OPEN astrid/crates/astrid-kernel/src/lib.rs 1`, but the response selects `astrid_kernel` with an underscore. Its architectural account partly repeats supplied notebook material; the suggested request-pipeline location remains explicitly tentative. The next selected input confirms that the underscore request was unavailable.
3. **`1789670377814-38510127` — corrected authored choice.** The recovery input states that no requested source bytes were delivered and supplies the hyphenated candidate. Minime recognizes the spelling difference and selects the exact hyphenated command. Within the fixed sample, this establishes a corrected choice, not yet a subsequent delivery or an answer to the substantive architectural question.

The saved notebook question still asks whether the Kernel struct implements `if !blocked`; a saved Road/Gate note remains an interpretation. This bounded reading does not establish a persisted revision to either. It does not search the rest of the day for a more favorable architectural account.

## Separately declared adjacent follow-up

After reading the fixed sample, but before inspecting the next outcome, [the follow-up plan](../research/outputs/2026-09-18-source-study-fidelity-day10/sample-adjacent-followup-plan.json) selected only the immediately subsequent retained source study. It is labeled exploratory, not a prediction frozen before the daily window. No later success would replace a missing or failed next outcome.

That next response is **`1789670522196-a4e863ea`**, completed at September 17 **18:44:02.959977 UTC**. Its prompt carries the previous selected command, matching the third sample's retained wire request and response hashes. The indexed action's explicit parent is the third sample's action; the corrected command and linked job match the next generation. The verified input supplies Astrid kernel revision `d19f321c…` at **bytes 0..4438 (end exclusive)**, beginning at line 1 (the metadata endpoint is line 94). The authored response is retained in its journal.

This chain establishes **choice → linked action/job → actual source delivery**. It does not establish understanding, a corrected saved finding, durability across later exposures, or a causal effect of the earlier reader repair. Those remain different research questions. S-008's prospective durable-correction selection is unchanged.

## Context and verification

All 325 generations use the registered September 17 host era, **PID 71419**, model **`gemma4:12b`**, and effective output ceiling **4096**; none hits that ceiling. The exact source-study system prompt is unchanged (`6be5d665…`, 312 responses). The 13 private-writing responses use `2b0bce76…`, a newly encountered prompt hash. Its explicit `WRITE CONTINUE` / `WRITE REVISE` guidance and stop-on-omitted-NEXT wording match the retained reviewed interface patch. The old private prompt and exact diff remain preserved.

The new [context-v3 extension](../probes/source_study_daily_context_v3.py) freezes reviewed identities separately from the maintained report. It verifies actual prompt bytes, known host identity, structured notebook schemas and retained release cross-checks. Helper clock strata are descriptive: per-invocation helper binary and preparation identities remain unestablished. The private-writing route is not evidence of source-helper invocation.

The maintained final report is byte-identical to its preliminary build (`bb38b9c5…`). It verifies all **428 manifest-listed historical files across 11 packets**. Historical manifest identities are anchored to the pre-window ledger or its already sealed day-9 lineage, not newly trusted from current contents. The 11 exact quotations verify; maintained negative controls reject tampering. Context controls additionally reject unknown prompts, wrong routes, false host PIDs, unknown notebook fields and rehashed host or private-prompt contradictions. The first descriptive build used the wrong private route label and counted zero; that preparation artifact is retained explicitly, corrected to 13, and excluded from accepted results. The accepted notebook count checks actual inclusion status.

The packet includes retained inputs, a versioned manifest, frozen maintained code, reviewed extensions, negative controls and offline replay. Tracking advances only after the sealed replay passes. The daily schedule and first-three sampling rule remain unchanged; no model calls, live-system writes, source-reader execution, restarts or messages were performed.

## Post-seal completion receipt — September 18, 18:58 UTC

The **100-file sealed packet** passes its frozen replay from a separate directory under an operating-system sandbox denying network access and reads from the original research, Minime and Astrid directories. All 428 historical files, 325 generations, 11 claim spans and independent context/descriptive outputs verify. The external [offline replay receipt](../research/outputs/2026-09-18-source-study-fidelity-day10-replay.json) binds packet manifest `ecb5b585dab44808bf84761a401f73cf8772dcc3289f6f24615f4c3c996a4a04`.

Only after that pass, [the ledger transition](../research/outputs/2026-09-18-source-study-fidelity-day10-ledger-transition.json) advances **4,763 → 5,088 IDs**, through September 18 18:34 UTC. The next window ends September 19 18:34 UTC. Cadence, historical windows and first-week synthesis remain unchanged. The sealed analysis preserves the pre-finalization account; this paragraph records its subsequent completion without altering the packet.

## Board updates pending

The authenticated board channel is unavailable. Proposed finding card **`f-s007-day10-navigation-recovery`**, being `minime`, lane `finding`, status `verified`: the fixed sample corrects an unavailable underscore source path; the separately declared adjacent follow-up verifies the corrected source was delivered. Scope excludes architectural truth, persisted correction, durability and general fidelity gain. Evidence: this account, exact claim annotations, the follow-up plan and descriptive-account checks.

Proposed test card **`t-s007-day10-offline-replay`**, being `system`, lane `test`, status `verified`: maintained daily report, independent prompt/host context, lineage and sealed replay, supported by the external offline replay receipt above. Session log **`2026-09-18-source-study-fidelity-day10`**: completion-window accounting, separate private writing, exact navigation recovery and unresolved broader interpretation. No live intervention.
