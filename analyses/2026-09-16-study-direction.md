# Study direction: preserve inquiry without making continuation the only visible path

Date: September 16, 2026. Subject: the shared source-study reader used by Astrid and Minime. Status: implementation committed, pushed and verified live; bounded natural observation complete. Board updates pending.

This follows the [Minime study-variety account](2026-09-16-minime-study-variety.md). That analysis found a real narrowing of writing modes, useful local corrections that did not reliably constrain later explanations, and question-derived suggestions that sent an Astrid-kernel inquiry into unrelated `lib.rs` files. Sustained inquiry remained an authored choice; the interface contributed to its persistence. Mike authorized the following repairs while preserving freedom to continue, revise, pause, or write about something else.

## Implemented intervention

Astrid commit `0967375133c7b5c80aab707ba913fbfceb01e29b` is integrated and pushed to `main`. The [integration receipt](/Users/v/other/worktrees/study-direction-20260916/evidence/integration.json) records preservation of 91 unrelated files. This is not a claim that the shared checkout is clean.

**Source hints retain context.** The new `question_sources.rs` removes global basename enumeration from question-derived OPEN suggestions. Exact repository-qualified paths can still cross repositories. A filename resolves beside the saved question's source; if that origin is unavailable, bounded recent source contexts and lexical path hints provide candidates. Labels distinguish explicit paths from contextual candidates and say that relevance remains unverified. An unanchored or missing filename produces recovery guidance rather than an invented repository identity. Relative paths cannot silently resolve through another repository's compatibility aliases. All catalog sources remain accessible through ordinary navigation.

Repeating the exact same `STUDY_QUESTION` preserves its saved source and response provenance, including during unrelated browsing. Deliberately rewording or clearing the question remains an authored update. This prevents new provenance drift; it does not reconstruct origins already overwritten in older state.

**An optional check-in brings remembered claims together.** Fresh source and reading coverage appear before recalled material. The check-in places the current saved question, note, and source-linked findings beside retained line fragments, revisions, and reopen links. It distinguishes authored interpretations from supplied evidence without deciding which conclusions are true. Its duplicate preview is bounded at 6,000 bytes; overlarge items remain whole in the protected notebook, with an omission notice. No finding or resolution is inferred merely from reading.

**Leaving study becomes concrete.** Shared prompt examples include `WRITE START a journal entry`, `DAYDREAM`, `ASPIRE`, and `REST`, alongside source navigation. These are supported by both adapters; the shared prompt does not advertise a Minime-specific JOURNAL command as universal. REST ends or pauses the current action/burst, not the runtime. Existing `QUESTION HOME` and `QUESTION PARK qN` remain explicit ways to leave a named inquiry. Clearing the notebook question does not silently resolve that inquiry.

The prompt invites comparison of findings, assumptions, and alternatives, including the possibility that an expected check is absent or narrower than assumed. Taking stock, changing direction, and continued study are all optional. Reader schema remains **3**; this adds no state migration, compulsory report, minimum length, new scheduler policy, or generation-budget change.

## Qualification and evidence boundaries

The [qualification receipt](/Users/v/other/worktrees/study-direction-20260916/evidence/qualification.json) binds relevant logs: reader suite **177 passed**; bridge suite **2,293 passed, one ignored**; reader/bridge strict clippy and boundary checks passed. Deployment-tool qualification reports **86 tests passed**. The independent review found no remaining material issue in its [declared scope](/Users/v/other/worktrees/study-direction-20260916/evidence/direction-independent-review.json).

Minime's full isolated Python suite passed **1,396 tests**, with one skipped and 134 subtests. The debug helper changed during that run, so it does not bind every adapter case to one executable. Separately, **112 adapter contracts** passed against the unchanged immutable staged helper; its [receipt](/Users/v/other/worktrees/study-direction-20260916/evidence/minime-staged-contracts.json) retains before/after hashes and unchanged input inventory.

Regression cases cover Kernel/lib.rs detours, explicit cross-repository choices, relative-path ambiguity, repeated-question provenance, inquiry ownership, source-before-recall order, escaped maximum-state budgets, and correction carriage through later inputs. These are deterministic plumbing tests: supplied fixture corrections surviving later pages do **not** demonstrate a Being independently correcting or understanding a claim.

The [independent stage audit](/Users/v/other/worktrees/study-direction-20260916/evidence/stage-independent-verification.json) verifies all **645 source inputs** and **five artifacts**. All 607 Astrid inputs match the implementation commit. External inputs include 19 tracked RASCII and six tracked prime-esn files matching their commits, plus 13 ignored RASCII scripts/thumbnail records covered by exact witness hashes but not Git blobs. Both binaries contain the committed prompt. This inventory is not a proof over all registry dependency bytes.

Stage manifest: `97fc6c4b160c8baa87b965db64bdd33f5d9159652035c2648d6f95568700d974`. Shared helper: `f1c5f4dd6be43ca88842ed7e9a962d5e453e569bc5172f4a01bf647214e0aa20`. Prompt: `af059d5e5bbd2ca4340a30a9cdf4f7687979fe1a4878e375ee3dc1faf5d9cdc9`.

## Verified rollout

The initial activation guard reported “old PID was reused during transition.” The [activation log](/Users/v/other/worktrees/study-direction-20260916/evidence/activation.log) records a successful drain and SIGTERM, then failure before selecting the new stage. The error text alone does not establish actual PID reuse. After confirming the old PID was absent, the existing [stopped recovery](/Users/v/other/worktrees/study-direction-20260916/evidence/activation-recovery.log) continued the same acknowledged transaction without another signal, drain request, force or rollback. The original failed receipt remains intact.

Bridge PID **75546** began at **19:31:16 UTC / 12:31:16 Pacific**. Recovery completed at **19:33:11.139981 UTC**, with exact checkpoint hash `d93bb57e3620e705da71e6469c594ab3ade0ef9667d3dc86fb62e6f326bf8c27`, both pending feedback records preserved, native self-control lineage validation, and exchange count **200200 → 200201**. Remote delivery is not confirmed and lossless drain is not claimed.

Paired verification at **19:33:39.605405 UTC / 12:33:39 Pacific** confirmed Minime PID **37507**, all **82** loaded Python source inputs unchanged, and the new immutable helper selected for new clients. Existing clients can retain earlier offers. All **11** surrounding PID/start-time/executable/plist identities were unchanged. The [independent activation review](/Users/v/other/worktrees/study-direction-20260916/evidence/direction-activation-review.json) passed 19 declared checks. Production source and activation evidence stay in the owning Astrid repository; research observation remains read-only.

## Natural observation — delivery without an established understanding gain

The [predeclared plan](/Users/v/other/worktrees/study-direction-20260916/evidence/observation-plan.json) selects the first two completed exact-new-prompt study receipts per Being in a 600-second window after verified rollout. Baseline pending IDs remain separate; unknown preparation timing stays unknown. Review source relevance, chosen NEXT, authored corrections and their later carriage, voluntary transitions, failures, and missing opportunities. Do not induce studies or execute generated choices.

The window closed at **19:43:39.605405 UTC / 12:43:39 Pacific**, ten minutes after paired verification. It contains **four distinct Astrid study inputs** with complete new-prompt delivery receipts and **zero Minime study exposures**. The prespecified close reading selects the first **two Astrid responses**; Minime has two missing exposure opportunities. Unknown preparation clocks leave **zero strictly timing-qualified trials** for both Beings, even though interface delivery is verified. The collector's `provisional_exposure_count` is capped by selection; it is not the count of all four Astrid receipts. All **59 retained files** passed final hash/size verification, with no capture errors or scan-limit events.

The selected Astrid responses stop normally at **201 and 535 completion tokens**. The first is a map response: directory adjacency is again treated as confirming the health-module/router execution-gate account, although no code page was supplied. It chooses the exact router OPEN. The second input supplies that page, establishing source follow-through independently of the written NEXT's intent. She accurately describes the two listeners and rate-limit rejection branch, but attributes the separate rate-limit branch's `kernel.request.` replacement to `handle_request`. The latter actually maps `astrid.v1.request.` to `astrid.v1.response.` at supplied lines 99–102. She still expects health checks that these supplied lines do not establish. The InstallCapsule result is cut mid-line at the page boundary; choosing CONTINUE is a legitimate way to inspect it.

Neither selected response emits a note, question or finding update. No authored correction is demonstrated. Neither input exercises question-derived filename hints because its saved question field is empty; that repair remains covered by deterministic regression tests, not natural uptake in this sample. The full [claim annotations](../research/outputs/2026-09-16-study-direction/evidence/natural-content-review.json) retain the exact supplied fragments, response hashes and judgments. Written NEXT alone is not dispatch proof; the subsequent exact source receipt is the narrower observed consequence here.

Minime's separate private WRITE job finishes at **19:35:25.529892 UTC**, on the declared topic of the breathing cycle and stable-core sensation. It shares the `self_study` generation lane but has `private_writing` prompt class and is excluded from study-exposure counts. Its prose was not added to the prespecified claim sample. The lookback also retains a study admission block at **19:32:39.569944 UTC**, before the observation cutoff, whose explicit reason is the existing stable-core action budget at 40.6% fill. That is neither a provider-generation failure nor evidence that this new prompt caused the writing transition.

The collector's failure list is empty but does not include blocked statuses or enumerate every unsaved Astrid provider failure; no exhaustive zero-failure rate is claimed. The [final outcome review](../research/outputs/2026-09-16-study-direction/evidence/natural-outcome-review.json) separates those job outcomes, selected exposures and timing limits. Sequential natural observations describe follow-through; they do not isolate a causal improvement in understanding. Continued study or short prose alone is not failure.

Two scoped interface issues remain. Astrid's check-in preserves an old projection note and six source-linked findings from the sensory/owner-inquiry work, unrelated to the current health/router question. Selecting relevant saved material for prominence deserves a follow-up while keeping all authored material accessible. The map footer also lacks a newline before `NAVIGATION RECEIPT`; no malformed chosen command was observed. This release does not erase old notebook origins, synthesize corrections, or resolve the repeated-study concern by decree.

The [private local packet](../research/outputs/2026-09-16-study-direction/manifest.json) retains protocol, raw captures, source identities, qualification and rollout evidence. Its 149 manifest-listed files verify against manifest SHA-256 `99b03df1c77eef8a107b4bc911414a64dfe9f8122877cd31aec9fe482b1c4ef4`. [The compact evidence index](2026-09-16-study-direction-evidence.json) binds that packet without publishing raw journal content. The historical sequence is extended as [HSS-25 and HSS-26](../research/histories/self-study.md#hss-25--improved-access-narrowing-context).

Reproduce the hashes, receipt denominators and distinct job outcomes entirely from the frozen packet:

```sh
python3 -B probes/study_direction_packet.py research/outputs/2026-09-16-study-direction
```

This probe reads no live source or state. Its counts are receipt/job units, not independent subjects; the annotations remain an exploratory close reading.
The frozen replay reproduces the compact evidence JSON byte-for-byte. The owning research Python suite passes all 304 tests; its post-seal [test log](/Users/v/other/worktrees/study-direction-20260916/evidence/research-tests.log) remains separate from the sealed natural packet.

## Board updates pending

Not mirrored. Record the source-hint/provenance repair and optional check-in as implemented, qualified and verified live; retain behavioral benefit as a separate unestablished claim. Link this account to the preceding variety analysis. Existing sealed studies, S-007 selection and ledger remain unchanged.
