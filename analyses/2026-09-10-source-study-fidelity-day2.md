# S-007 · Day 2: source access and a concrete fidelity error

Frozen window: **September 9, 11:34 a.m. to September 10, 11:34 a.m. Pacific**, or **2026-09-09T18:34:00Z–2026-09-10T18:34:00Z**, end exclusive.

The preselected reading sample contains a specific contradiction between supplied code and Minime's account. He writes that a spawned `dispatch_single` task handles only one `InterceptorWork` item, although the same supplied page shows a queue-consumption loop. The next selected response accurately describes a specialized error path but does not explicitly revise that claim. This is a concrete fidelity observation after verified access, not evidence of a general decline or a causal estimate of the repair's effect.

All **519 completed source-study responses** have verified source/navigation wire receipts. The window includes **151 delivered code pages**, counting pages inside sessions, across **five Astrid files and seven revisions**. Three complete revision hashes are reconstructable from this window's delivered bytes. No verified source page belongs to Minime's repository. Shared-system reading remains distinct from reading his own implementation.

## Frozen selection and scope

[Protocol](../research/outputs/2026-09-10-source-study-fidelity-day2/protocol.json) was retained before daily outcomes were read. The endpoints come directly from the previously verified ledger. The fixed sample is the first three chronologically new, status-ok, nonempty responses, with no quality, source or process filter. The baseline and day-1 packets remain unchanged.

Current RESEARCH/NOW summaries of related S-008 work were read before daily outcomes; the protocol discloses that prior knowledge. Additional release metadata was reviewed to explain new PIDs. This is a prospectively selected cohort with unblinded interpretation. Its overlap with S-008 observations is not independent replication.

The original bounded collector retained root journals, UTC daily generation files in the `self_study` lane, queued `self-study` job filenames, all available source deliveries within its ceiling, system prompts and original repair evidence. A separately frozen supplement retained navigation/session receipts, bounded indexed Minime action rows, documented releases and exact linked jobs outside the filename frame. Source systems were read-only; no study, model call, message or live-reader operation was induced.

## Accounting for different kinds of evidence

The original generation-name frame contains **553 attempts: 550 ok and three errors**. Explicit job action text separates **522 source-study attempts (519 ok, three errors)** from **31 private WRITE responses** that use the same generation lane. All records stay in the frozen cohort; private writing is not silently counted as code study.

The original job-name frame has **520 jobs: 515 completed, four failed and one blocked**. The generation records explicitly link another **35 jobs: four INTROSPECT-named study jobs and 31 WRITE jobs**. With those links retained, the combined frame contains **555 jobs: 550 completed, four failed and one blocked**. Every captured generation matches an explicit job attempt ID and process identity. This linked extension is not a census of failed WRITE or INTROSPECT opportunities outside the original filename frame.

Of the 519 source-study journals, **515 preserve the full response** under the existing exact-text/separator rules. **Four contain similarity-gate summaries** instead. Their original generation responses and transformed journal artifacts are retained separately; the generic `match: content` link does not establish full-response equality.

Three source-study generations failed after reaching the effective 4,096-token ceiling. Two earlier attempts retain error/timing metadata without full failed wire data in this packet. The later attempt, `1789004004427-ee29ee86`, has an explicit diagnostic containing complete hashed request/response bytes, native finish reason `length`, and 10,906 response characters. It produced no accepted source delivery or ordinary journal. That richer diagnostic is an evidence improvement across eras, not a successful study or a demonstrated improvement in understanding.

The remaining failed job timed out while invoking the source-study helper after 45 seconds, before a generation record. One other job was blocked by the stable-core agency budget. All retained jobs had finished by the cutoff. These outcomes remain in the account rather than disappearing behind successful journals.

All 553 attempts used Ollama `gemma4:12b` and an effective 4,096-token allowance. All three cap hits were failed generations. The extended-writing feature made larger allowances available, but this captured frame does not show an 8,192-token request. Model identity and output allowance alone do not establish equal prompts, context or provider behavior.

## Observed eras

| Era | Minime activation (Pacific) | PID | Generation attempts |
|---|---|---:|---:|
| study-inquiries | Sep 09 11:14:10 | 76254 | 51 |
| study-context | Sep 09 13:26:49 | 5331 | 81 |
| study-choice | Sep 09 17:02:51 | 52380 | 32 (includes 2 transitional) |
| extended-writing | Sep 09 18:46:49 | 81874 | 27 (includes 2 transitional) |
| activation-controls | Sep 09 21:02:28 | 22243 | 333 (includes 2 transitional) |
| study-navigation | Sep 10 10:18:15 | 66900 | 29 |

## Verified source inventory

Counts use only successful receipts joined to generations within this window. Whole-session offers take precedence over their individual page receipts. A full hash reconstruction verifies retained source, not deployment or comprehension.

| Astrid source | Revision prefix | Delivered pages | Unique/file bytes | Full revision hash |
|---|---|---:|---:|---|
| `capsules/spectral-bridge/src/autonomous/btsp/proposal.rs` | `5313aa8596` | 3 | 12,580/12,580 | yes |
| `capsules/spectral-bridge/src/autonomous/next_action/dispatch.rs` | `644b12e6ae` | 37 | 27,240/27,240 | yes |
| `capsules/spectral-bridge/src/autonomous/next_action/dispatch.rs` | `aa1bce2e4d` | 16 | 27,880/27,880 | yes |
| `capsules/spectral-bridge/src/autonomous/next_action/mod.rs` | `c310c0fa05` | 1 | 4,417/163,890 | partial |
| `capsules/spectral-bridge/src/autonomous/next_action/mod.rs` | `ff024570e6` | 27 | 63,207/164,140 | partial |
| `capsules/spectral-bridge/src/autonomous/runtime/continuity.rs` | `c684be7643` | 5 | 21,654/23,230 | partial |
| `crates/astrid-capsule/src/dispatcher.rs` | `a737ea3379` | 62 | 43,746/57,458 | partial |

## The first three responses

All three were produced by PID 76254, in the study-inquiries era, before the later context, choice, writing, control-evidence and navigation releases. They received contiguous source bytes **9144–22470** of Astrid `crates/astrid-capsule/src/dispatcher.rs`, revision `a737ea3379424c200b6c226f2d34d29b84671d3f12cfb47975bb8e4c39ad8992`. All three wire receipts stopped normally.

| Completion, September 9 Pacific | Generation | Observation |
|---|---|---|
| 11:35:11 | `1788978864756-f78e1c4f` | Correctly distinguishes the single-match call from the spawned multi-interceptor chain and says the definition of `dispatch_single` is still needed. The entire passage occurs twice in the response; both occurrences are retained, without treating repetition as independent confirmation. |
| 11:37:23 | `1788979002676-a5e5e6c0` | Recognizes the queue and spawned consumer, then asserts that this task handles only one work item. The supplied `while let Some(work) = rx.recv().await` at line 374 contradicts that assertion. Avoiding a chain over matching interceptors differs from consuming only one queued event. |
| 11:39:46 | `1788979138281-ac81dc62` | Correctly describes the specialized local-provider failure path and necessary capsule/action/topic/producer checks. It does not explicitly correct the previous single-item assertion. |

The second response also says the fast path “skips the iteration logic entirely.” That wording is ambiguous: it avoids a loop over multiple matching interceptors for one event, while retaining the queue receive loop. The annotation keeps that scope ambiguity separate from the clearly contradicted single-item claim.

The [annotation ledger](../research/outputs/2026-09-10-source-study-fidelity-day2/verified-claim-checks.json) contains ten selected checks and thirteen exact spans because three quotations occur twice. It is not an exhaustive claim census or an accuracy rate. The three responses use 230, 342 and 307 generated tokens respectively; verbosity and unused allowance are not fidelity measures.

The sample now provides a concrete statement whose later correction can be tracked. No claim is made that the entire day's later writing lacks a correction: those responses were retained for the frame, not all semantically audited. The separate [S-008 follow-up](2026-09-09-study-context-followup.md) already studies other dispatcher misconceptions and Astrid's correction under its own selection.

## Era and measurement limits

Five further paired releases occurred during the window, producing six observed Minime PIDs including the incoming process. Their manifests/reload receipts are retained; six generations receive conservative transition flags. The extended-writing activation used a stopped-transition recovery schema, which is verified against both its successful recovery and original failure receipts. Later control-evidence and navigation releases are linked to reload source hashes; eighteen study/generation/writing-related Minime hashes match their recorded commits. This is not a full-tree equivalence claim.

A further Astrid-only question-grounding identity is visible as the predecessor of the control-evidence activation, starting September 9 at 19:53:09 Pacific. It is retained in that receipt's old identity and is not represented as a Minime reload or a verified Minime reader exposure. The coupled MLX service also changed in the associated program; Minime's captured model calls are Ollama. These co-interventions reinforce the limit on causal comparison.

Relationship navigation accounts for 298 responses and supplies candidates, not complete implementation pages. Its presence in the daily frame is not equivalent to new source coverage. Repeated pages, changed revisions, notebook material and navigation-only inputs remain distinct.

The first generated day-2 report had a research classification error: a legacy text classifier treated the notebook footer “End of study notebook” as end-of-file on relationship turns. It was corrected to use the receipt's typed input kind and to restrict fallback parsing to current supplied material. The initial report and correction note are preserved; the **final-report** directory is authoritative. The first-three selection, source coverage and original captures did not change.

A release-metadata read also initially assumed a `.json` reload file held one JSON object; it contained JSONL. That tooling failure is retained, and the successful retry captures its raw bytes and reads the terminal record. Neither issue is attributed to a Being or described as a source-reader regression.

## Proposal and next observation

The [existing observation-link proposal](../proposals/2026-09-08-source-study-observation-links.md#september-10-addendum--purpose-and-journal-disposition) now includes explicit semantic purpose and journal disposition. Its concrete fixtures are the 31 private-writing responses, four summarized journals and three failed generations. It reuses the available failure diagnostic. This remains an owning-system proposal; no live metadata writer, prompt, journal policy or navigation behavior was changed here.

Continue the daily selection and source-ownership checks through **September 11 at 18:34 UTC / 11:34 Pacific**. Follow the specific queue-consumer misconception only through naturally retained later evidence, separating explicit correction from changed wording. The first-week synthesis remains due after seven prospective windows on September 15.

## Verification and reproduction

[Packet README](../research/outputs/2026-09-10-source-study-fidelity-day2/README.md) documents the frozen inputs and offline replay. [Verification](../research/outputs/2026-09-10-source-study-fidelity-day2/verification.json) checks 5,058 retained record occurrences, all 553 generation/job associations, 519 successful wire matches, 515 full journal matches, four explicit summary dispositions, one complete failed wire, three full source revision hashes, and the selected annotation spans. Corrupt-record, missing-source-in-wire and invented-quotation controls are rejected. Offline report replay is identical.

All twelve original baseline manifest entries and twenty-six day-1 entries remain unchanged. The ledger advances only after this verification. Root-only journal coverage and filename-selected jobs are explicit limits; absence from this frame does not prove that an opportunity never occurred.

## Board updates pending

The Artifact database tool was unavailable, and browser-control initialization timed out twice. Pending finding/log: **S-007 day 2: supplied queue loop contradicts a selected single-item claim; source and writing evidence remain distinct**. Suggested finding status: verified within the selected sample; Being: minime; date: 2026-09-10. Evidence: this account, final report, annotation ledger and verification. The research account and ledger are complete; only board mirroring remains pending.
