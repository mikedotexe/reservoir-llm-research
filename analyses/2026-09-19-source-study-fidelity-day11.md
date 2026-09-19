# S-007 day 11 — supported local reading, unresolved policy inference

**Status: verification blocked.** The bounded evidence and fixed reading are retained, but a new Minime process lacks the historical restart/deployment receipt required by S-007. The ledger has not advanced.

The fixed three responses describe several local source mechanisms accurately: capsule restart ordering, guarded unload attempts, loading order, and session-allowance cleanup when the final connection closes. Their current page ranges are also correct. Claims about guaranteed readiness and a general blocked-policy or state-purge mechanism go beyond the source fragments supplied in these turns. No general fidelity gain or causal effect is established.

## Frozen frame and accounting

The window is September 18 18:34–September 19 18:34 UTC. The protocol was frozen at September 19 18:36:16.628558 UTC before new outcomes were read, SHA256 `c09d9c4f8309cd5e9796553a6126ef91e93294073e4f606edfb6e62ab1312426`. Its original wording remains unchanged. The inherited close-reading selector takes the first three newly completed status-ok nonempty responses in the shared filename frame after ledger deduplication; it does not filter on source, apparent quality, length or PID. All three selected responses are source studies.

The retained report contains 314 generation records: 302 completed source studies and 12 separate extended-writing responses sharing the filename lane. All 314 have status ok. It reports 302 verified source-study wire joins, no capture/join errors, and no unverified receipt associations. These are reproducible report outputs, not a successful final-verification receipt; verified input delivery is not a claim that the prose is correct.

The source-study journal associations comprise 301 full-response matches and one explicitly captured similarity summary, generation `1789808838598-fe9fcdd7`, completed September 19 09:09:13.684443 UTC. That summary is not a full raw-response match. The 12 private-writing rows remain separate; no source-study journal failure is inferred from their different output route. No later response prose was read for this draft.

The filename-selected source-study job frame contains 302 jobs, while explicit links expand the retained job frame to 315. The expanded records all eventually say completed, but this is not a within-window completion denominator. At the far boundary, `job_minime_1789842762527_self-study-open-astrid-crates-astrid-capsule-src` starts at September 19 18:32:46.763825UTC and finishes at 18:34:37.993649UTC, after the cutoff; it has no generation completing in this window.

## Source exposure and ownership

All 236 verified numbered-source opportunities concern Astrid's repository. The report reconstructs both complete revision hashes:

| Source | Page opportunities | Verified full revision |
|---|---:|---|
| `astrid/crates/astrid-kernel/src/lib.rs` |174|`d19f321c54b299e1204d6e0db5a81792e056f9140b4a82bfbac76468c603d92b`|
| `astrid/crates/astrid-capsule/src/dispatcher.rs` |62|`24d8975b088175e9f51ca9d2f7545429aaff42bf68b183bed2009650ca955719`|

Minime is the author. No Minime-repository source page is present in this captured source-study route. Full revision delivery establishes retained exposure and byte identity, not complete understanding or deployed behavior.

## Fixed close reading

| Generation | Completion UTC on September 18 | Supplied current source |
|---|---|---|
| `1789756440859-24cb6c91` |18:36:50.454282|Astrid kernel lines 294–399; bytes 13047..17225|
| `1789756712280-a580b0a8` |18:41:48.740746|Astrid kernel lines 400–496; bytes 17225..21579|
| `1789756980012-caac49d9` |18:46:31.725832|Astrid kernel lines 497–600; bytes 21579..25780|

The first response follows retrieval of a capsule's source directory before unregister/reload and the Arc::get_mut guard on an unload attempt. The second correctly identifies cycle fallback and calls that wait for uplink readiness before the other load group. The third recognizes the `result == Ok(1)` branch clearing session-scoped allowances and the bounded mutable-access retry loop. These are source-supported observations with stated local limits; they do not establish that the live system took those paths.

Readiness is a narrower inference than the response suggests. The supplied pages show `await_capsule_readiness` calls, but not the helper's body or its success/timeout conditions. The load loops log failures without an immediate return. Therefore “fully ready” and “Once all capsules are loaded and ready” exceed what the displayed call sites establish. A comment about avoiding discovery polling with arbitrary timeouts is not a shown readiness-helper timeout branch.

The open inquiry remains the location and meaning of `if !blocked`. The first two responses retain tentative location language. The third more definitively attributes blocked state to EventDispatcher or similar middleware and generalizes state purging to capsule unload or session end. The current source shows a specific session-scoped allowance clear, not the general policy decision or a universal purge. These stronger conclusions remain unestablished here, not demonstrated false.

All three prompts carry the same saved note distinguishing failed infrastructure from policy-enforced blocked states. The second and third notebooks also carry their preceding selected response under the exact wire-response hash. This verifies memory transport; repetition is not independent corroboration and no causal role for notebook content is inferred. No sampled response revises its saved note, question or findings. All three choose CONTINUE; no later delivery or correction was read as an adjacent follow-up.

The first response belongs to the previous day's censored job, but the clocks must stay separate: job creation 18:33:55.263882 and job start 18:33:59.410899 precede the cutoff; model generation start 18:34:00.859 is inside this window. Generation completion 18:36:50.454282 and job finish 18:37:19.956724 are also inside it. Selection is by generation completion.

Eleven exact, unique claim spans are retained in `claim-annotations.json`; the independent account is `draft-close-reading.md`. They distinguish local support, tentative hypotheses and claims not established by supplied evidence. The selected spans are not an accuracy-rate denominator. No metaphors are scored false, and no exhaustive search for later corrections is claimed.

## Verification blocked at an unresolved host release

The initial maintained verifier rejects 263 generations under the unregistered Minime PID **81688**. The other 51 rows use registered PID **71419**, including all three fixed readings. The new process snapshot records a start at September 18 **17:43:15 Pacific** (September 19 00:43:15 UTC), but the bounded search has not located its historical restart/deployment receipt. Current loaded-source status agrees with the staged 82-file candidate; this current witness is retained separately and is not substituted for historical reload evidence.

The preserved source-study prompts divide into 47 inputs with the earlier `6be5d665…` prompt and 255 with `5a0864f2…`. Twelve private-writing prompts retain `2b0bce76…`. The new 6,335-byte adapted prompt matches the staged source prompt and its source-input inventory. It shortens existing guidance, describes non-test call/match-site candidates in RELATE, and adds optional two-anchor STUDY_RELATION instructions. These are supplied-context changes, not evidence of successful uptake or better writing.

Eight deterministic partial checks bind the prompt, source inventory and bridge activation. Bridge activation records PID 77906 → 82935 at September 18 **17:46:13 Pacific**. Its stage manifest is `c2c40c35…`; helper artifact `02a973ca…`; source inventory `1e465895…`. The staged tree was dirty, so HEAD alone does not identify released content. These checks do not establish the historical Minime reload or the helper binary used by each generation. All 302 source notebooks fit the known schemas; no new unknown schema is accepted.

The bounded receipt search covered declared research release inventories, source-study steward notes, the owning stage/activation transaction, runtime reload metadata, the current startup witness and a final top-level temporary-file inventory. Original plans, limits, errors and observed absences remain in the private packet. No unrelated session logs or general journal search were used. The initial context definition and its unknown-prompt rejection remain unchanged; there is no fabricated successful context or release receipt.

**This window is retained but not finally verified.** A reviewed final input manifest and report reproduce the original 314-row report exactly, preserving its unknown-era flags. Exact quotation checks, retained-file integrity and numerical accounting can be reproduced independently; they do not make the failed release check pass. The maintained migration has not regressed: its existing rule correctly refuses the unknown identity, and the prior workflow would not supply the missing release evidence.

The tracking ledger remains byte-identical at **5,088 IDs**, through September 18 18:34 UTC. Its next window remains this frozen September 18–19 interval. The 314 records are not entered as verified, and the prospective 5,402 total is not the current ledger count. The first-week synthesis and schedule remain unchanged.

## Recovery boundary

Resume this same frozen window when the owning Minime restart receipt is available. Retain a new verification attempt and a separate explicitly hashed release supplement referring to this packet; do not modify the sealed capture, change its first-three sample, recollect for a more favorable result, or widen the window to include another day. Only successful complete verification permits the ledger to advance. Subsequent daily windows remain separate. This is a research-evidence gap, not a request to restart or modify a Being.

The external integrity replay receipt distinguishes a faithfully reproduced verification refusal from successful research verification. The sealed packet and blocker account are useful negative evidence; human receipt clarification remains pending.

## Reproducible accounting scope

[Private packet and replay instructions](../research/outputs/2026-09-19-source-study-fidelity-day11/README.md). The original capture/protocol, final declaration, retained report, exact annotations and partial release review stay separate.

Counts above use the maintained report and `probes/source_study_daily_descriptive.py`: generation_count; studies grouped by actual_route, status, journal_status and pid; verified_receipt_matches; source_progress; sources; and jobs_without_window_generation. Only the three close_reading_ids supplied prose for interpretation. The independent selector uses retained generation created_at as completion time, status ok, nonempty response text and exclusion from tracking-before.seen_generations, ordered by completion then generation_id. Offline reproduction follows no original source paths; the separately declared capture and release collectors were read-only.

## Post-seal replay receipt — September 19, 18:55 UTC

The **109-file packet** is sealed as `5d0c7e7afc49adbfe3f828a07a6f4c21f3f217bcf3f0e6bab11381bf6a8553bc`. Its frozen replay ran in an isolated directory with network access and reads from the original research, Beings and worktree paths denied. It reproduced 314 report rows, the 263 unknown-era rows, 11 exact claim spans, 528 historical files and the explicit release-verification refusal. **Integrity replay passed; research verification remains blocked.** A zero replay exit means that the retained refusal reproduced, not that this daily window passed final verification.

The external [blocked replay receipt](../research/outputs/2026-09-19-source-study-fidelity-day11-blocked-replay.json) and [pending-window record](../research/outputs/source-study-fidelity-pending.json) preserve that distinction. The initial staging script encountered an older-ledger field mismatch after sealing; its failure is retained. A separate corrected runner stages the exact history paths declared in the input manifest without changing the sealed packet. No ledger advance occurred; its SHA remains `8a3066d03a957c632ba2dd27f728cc024cb79836d559834c1d8a5231140e8a1b`.

The sealed analysis preserves the pre-finalization account. This paragraph records subsequent offline reproduction and the pending recovery path. The requested historical restart/deployment receipt remains missing.

## Board updates pending

The authenticated board channel is unavailable. Proposed finding card `f-s007-day11-lifecycle-scope` (minime, finding), verification card `t-s007-day11-host-release` (system, test, parked pending the owning receipt), and session log `2026-09-19-source-study-fidelity-day11` remain pending mirroring to the Hold Shelf board. The bounded result is locally supported mechanism reading alongside unestablished readiness/policy generalization; final release-era and packet verification must be completed before describing the daily window as verified. No live intervention, message, model call or forced study occurred in this research task.
