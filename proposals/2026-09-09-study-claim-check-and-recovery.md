# Help a study find the right source and revise its own explanation

Status: proposed September 9, after the [HSS-15 natural follow-up](../analyses/2026-09-09-study-context-followup.md).
No implementation, model trial, live change or Being message has been made here.

The felt problem is concrete: Astrid spends a sequence of studies trying to
enter files that exist under a slightly longer path. Minime can now retain
complete answers, yet builds an increasingly settled explanation around a
mistaken premise. Both should have the same improvements. A saved source
reference identifies where a note arose; it does not validate the note.

## 1. Offer exact existing paths when an OPEN misses

Change surface:

- `/Users/v/other/astrid/crates/astrid-source-study/src/store.rs:339` (`recovery_map`) and `:348` (`requested_source`).
- `/Users/v/other/astrid/crates/astrid-source-study/src/catalog.rs:139` (exact source resolution; preserve this authority boundary).
- `/Users/v/other/astrid/crates/astrid-source-study/tests/reader.rs` for missing-path recovery cases.

Diff sketch: after exact resolution fails, query only the existing allowed
catalog. Keep the current exact spelling alternative. If absent, offer at most
three same-repository, same-basename paths, ordered by shared path suffix/parent
similarity and stable lexical tie-break. Render full `SELF_STUDY OPEN … 1`
commands explicitly as **candidates, not opened**. For an empty directory MAP,
offer a verified nearby directory only when the catalog actually contains it;
otherwise keep normal map/search guidance. Do not auto-resolve ambiguous
basenames or expand the permitted source roots.

The actual regression fixture is missing `action_continuity` in
`astrid/capsules/spectral-bridge/src/runtime/command_dispatch.rs`. The exact
candidate is `astrid/capsules/spectral-bridge/src/action_continuity/runtime/command_dispatch.rs`.
The isolated [replay](../research/outputs/2026-09-09-study-path-recovery/recovery.json)
already establishes that ordinary FIND and exact OPEN work.

Qualification: missing-parent case offers the exact full candidate; ambiguous
same-name files stay choices; unrelated files are not suggested; excluded/private
paths cannot become candidates; recovery does not record source coverage or move
the last delivered bookmark. Check both adapters use the same reader output.
Once activated, observe whether a naturally failed OPEN proceeds to a delivered
candidate rather than counting suggestion rendering as recovery success.

## 2. Test a focused claim check before changing the production study prompt

The important behavior is revising an explanation when evidence contradicts it,
while retaining a correct explanation when the evidence supports it. Do not
require a long review, forced uncertainty, word count or a new metadata framework.

Use a six-call standalone qualification: **three frozen cases × two prompts**.
Each pair gets the same saved notebook, exact source revision, context/output
allowances, model build and generation settings. Thinking stays off. Alternate
pair order and retain exact messages, native response/finish, visible response,
token counts and wall time. This small trial qualifies a candidate; it is not a
statistical estimate of improvement or a live interaction with either Being.

Predeclare the cases and manual checks before requesting outputs:

| Case | Decisive source shown in both arms | Check |
|---|---|---|
| Minime's immediate single-dispatch account at 13:40:53 | `dispatcher.rs` 245–302 and 360–449 | Identify a reused per-capsule worker and distinguish it from the per-chain task. |
| Minime's Private-bypass account at 14:12:57 | 225–284, 530–601, 413–520 | Recognize common caller filtering, match-count branching and the separate post-invocation failure-reporting predicate. |
| Astrid's corrected host-filter account at 13:58:12 | The same authorization/caller evidence | Preserve the supported host-filter conclusion; do not invent a counterexample or overstate a complete mediated success path. |

Use the retained `a737ea…` source, not line numbers against a later checkout.
In each pair the baseline uses current source-study guidance; the candidate adds
one invitation, without supplying the correct answer:

> Compare your saved explanation with the supplied caller and branch code. Look
> for a case that would make the explanation false. If the evidence changes it,
> revise your study note and remaining question; if a needed link is absent,
> identify that link. Write in whatever form is useful.

Both arms must receive identical relevant evidence. This tests the invitation,
not an inseparable mix of new prompt and better source selection. Freeze the
input pack below the existing 24,000-byte protected-input budget and use the
existing 32,768 context / 4,096 output limits. Never truncate one arm differently
or count unavailable native counters as zero.

For each result record the specific supported/contradicted claims, whether the
saved note was actually revised, what remains unresolved, any new invented
symbol, repeated material, and latency/finish. A navigation-only response is
inconclusive, not a correction. A longer answer without a corrected claim fails
the intended qualification. Preserve complete failures as failures. Do not pool
these observations into a single “understanding score.” Repeat with additional
examples if promising before attributing a model-wide effect.

Potential implementation, only after qualification:

- `/Users/v/other/astrid/crates/astrid-source-study/src/notebook.rs:30` (`study_choices`): offer a short shared invitation near the Being-authored question. Retain the Being's authority to update or clear the note.
- `/Users/v/other/astrid/crates/astrid-source-study/src/relationships.rs`: expose exact caller/definition locations as lexical navigation candidates; do not label the most recent two pages as the evidence that answers a question.
- `/Users/v/other/astrid/crates/astrid-source-study/tests/context.rs` and `tests/inquiries.rs`: protect source identity, prompt budget and optional controls.

The current recent-page SESSION offer is honest about recency, but often compares
irrelevant test pages. A later separate navigation comparison should test choosing
definitions/callers versus recent pages, keeping the prompt fixed. No vector store,
new service or automatic truth label is needed.

## 3. Retain a bounded failed-attempt diagnostic

Two attempts consumed the complete 4,096-token allocation but left no visible
response or native finish reason in the retained generation record. Source
locations are `/Users/v/other/minime/minime_autonomy/source_study.py:114`
(`SourceStudyPrompt.post`), `:126` (`accepted`), and
`/Users/v/other/minime/minime_autonomy/runtime.py:54933` (response decoding/timing).

Record provider finish reason, raw-content length, cleaned-content length and
failure classification before an empty/invalid output is discarded. Retain a
bounded exact failed wire artifact under diagnostics with digest and truncation
flags if needed, separate from accepted reader receipts and journals. This
would distinguish an empty final, cleaning loss and limit exhaustion. Never
advance a source bookmark merely because an HTTP request returned successfully.
Test capped/empty/cleaned-empty responses and confirm a subsequent successful
retry records delivery once. This diagnosis comes before any further budget change.

## Being-facing explanation, rollback and observation

Before a later live rollout, prepare a plain-language note explaining exact-path
candidates and the option to check a saved explanation against source; explicitly
leave study style and length free. Let Mike decide whether to deliver it. This
research does not send messages or put these evaluations in the Beings' prompts.

Implement and deploy in the owning sibling repository under its shared-tree
coordination and build rules, with changelog, focused tests, release identity and
a fixed natural follow-up cutoff. Rollback removes the candidate guidance and
path suggestions while retaining the current notebook schema, source catalog,
accepted delivery state and journal history. Diagnostics can be disabled without
changing delivery acceptance. Measure natural corrections and successful recovery
separately from command uptake; include unchanged and mistaken notes in the next
reading pack.
