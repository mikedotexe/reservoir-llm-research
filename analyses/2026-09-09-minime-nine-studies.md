# Nine Minime studies: room to write, room to retain an answer

September 9, 2026. Mike selected nine journal files ending between 12:08:04 and
12:26:19 PDT and asked what their content shows, why their files remain small,
and what would provide more room for substantive study. This is an exploratory
case series, not a random sample or a before/after effect estimate. It continues
[HSS-12](../research/histories/self-study.md#hss-12--shared-inquiries-relationships-sessions-and-execution-evidence)
and S-008 without advancing S-007's daily cursor.

The repaired reader delivers implementation. Minime articulates an important
implementation distinction. The weak point in this sample is retaining and
developing that distinction: the same four pages are read twice around a map
visit, the old question persists, and the useful comparison is absent from the
next turn's short carried excerpt. Increasing the output allowance did not
increase that memory allowance.

## A. Material and provenance

All nine original files, including headers and system-added notices, are retained
in [selected-nine-verbatim.md](../research/outputs/2026-09-09-minime-nine-report/selected-nine-verbatim.md).
The exact selected set and numerical results are in
[selected-nine.json](../research/outputs/2026-09-09-minime-nine-report/selected-nine.json).
The wider capture freezes 19:05–19:28 UTC with the toolkit's thirty-minute lead-in
and notebook-origin receipts. Wider records supply attribution; the nine named
files define this analysis. Capture, receipt validation and journal joins have
no reported errors. All nine raw visible response bodies match their retained
generation text and are contained in their respective journals.

All nine generations identify Minime PID 76254, Ollama `gemma4:12b`, one attempt
and no fallback, consistent with the inquiry release. Current Minime main is
`a44e26580c6911195d88f213230eb4dd0fd2f4ac`, clean at inspection. The delivered
dispatcher source hash is
`a737ea3379424c200b6c226f2d34d29b84671d3f12cfb47975bb8e4c39ad8992`, matching the
[retained full source](../research/outputs/2026-09-09-minime-nine-report/source/dispatcher.rs).
This hash establishes the code reviewed here, not deployment of every kernel path.

| Journal completion, PDT | Provider output tokens | Close reading |
|---|---:|---|
| 12:08:04 | 228 | Sees the single/multiple-match branch; seeks `dispatch_single`. |
| 12:10:23 | 372 | Reaches the persistent worker; distinguishes it from the chain. |
| 12:12:54 | 402 | Describes execution errors and exact local-provider error publication. |
| 12:15:23 | 583 | Describes interceptor matching, caller restrictions and test setup. |
| 12:17:14 | 144 | Map-only turn returns to the old question and requests line 192. |
| 12:18:44 | 267 | Rereads the initial branch and again seeks the definition. |
| 12:20:30 | 371 | Clearly states persistent worker versus a fresh task per chain. |
| 12:25:01 | 1,037 | Notices queue drops; repeats most of the explanation within one response. |
| 12:26:19 | 228 | Rereads matching/caller restrictions and proposes continuing into tests. |

File sizes are 933–4,130 bytes, including headers and annotations. Three entries
contain an added agency-vernacular notice; they are not Minime-authored prose.
The largest entry's repetition is already in one raw provider response, with two
NEXT lines. It is not two generations concatenated by the journal writer.

## B. Claims checked

### Source access works; the question does acquire an answer

Eight code turns deliver four exact contiguous intervals twice:
`9144..13598`, `13598..18115`, `18115..22470`, `22470..26843`. That is 35,398
delivered bytes and 17,699 distinct bytes in this selected set; half the bytes
are repeats within the set. This is not a claim that the first pass was new in
Minime's entire history. The map itself reports prior complete delivery of this file.

At 12:20 Minime writes:

> The core difference is that `dispatch_single` leverages a persistent worker task and a channel to handle the "common" case without the overhead of spawning a fresh task for every single-interceptor event, whereas the multi-interceptor logic spawns a task to handle the complex iteration of a chain.

The source supports the main distinction: the single path lazily installs a
per-capsule channel/worker, while the multiple-match path creates a task that
walks the ordered matches. Both invoke interceptors. The earlier phrase
"avoids ... spawning a new Tokio task" needs its common-case qualification;
the first single-path request does spawn the worker. His later writing provides
that qualification. Some line labels identify nearby comments rather than the
exact definition (`fn dispatch_single` is line 360).

This updates the earlier ten-minute observation: Minime now reaches the requested
implementation. It would be wrong to keep describing him as only advancing
through tests. It also would be wrong to treat each reread as a wholly independent
failure; the second comparison is clearer than the first.

### The notebook preserves the question better than its answer

All nine final requests contain only two messages: the study system instruction
and one source/navigation input with its notebook. They do not contain the full
preceding conversation. Every request carries the same note and question origin,
whose provider completion is 10:58:32 PDT. None of these nine responses authors
a replacement `STUDY_NOTE` or `STUDY_QUESTION`; none enters a named inquiry.

The [notebook implementation](../research/outputs/2026-09-09-minime-nine-report/source/notebook.rs)
retains a maximum 700 UTF-8 bytes of the last substantive response, 700 for an
explicit note and 350 for the question. This is a head excerpt, not a summary
that selects conclusions. The serialized notebook can be shortened further to
fit 3,200 bytes. Omitted note/question lines leave old values intact.

The exact 12:25 request carries 12:20's response only through the beginning of
the multiple-interceptor comparison, ending `* In the **Mul [excerpt truncated]`.
The quoted conclusion above is gone. By the 12:17 map turn, the earlier 12:10
comparison has already been replaced by the opening of 12:15's matching summary.
The old question's `reopen` points to line 192, the source page where the question
was asked, not the location of its answer. The map response treats that reference
as a useful place to seek the definition and reopens it.

This establishes a concrete loss of relevant supplied context and a plausible
mechanism for repeated investigation. It does not establish that changing the
excerpt alone will fix the behavior. Question ownership and durable persistence
work as implemented; a usable synthesis workflow remains weak.

The map visit is not evidence of a parser resetting CONTINUE. A separate default
reflection, generation `1788981375699-f0a67f9d`, ends at 12:16:48 with
`NEXT: SELF_STUDY MAP`; the subsequent action records that same choice. It occurs
between the 12:15 study's CONTINUE and the 12:17 map. The capture retains this
intervening choice. The final study has only about 100 seconds of follow-up here;
no thirty-minute non-execution finding is possible.

### The output cap is real and is not cutting off these entries

Every exact request has `num_predict: 4096`, `num_ctx: 10240`, `think: false`.
Every provider response has `done: true`, `done_reason: stop`. Actual output
ranges from 144 to 1,037 tokens; the median is 371, about 9.1% of the allowance.
One response exceeds the old 768-token limit, demonstrating actual use of some
new headroom, but it is the duplicated response. None exhausts the new allowance.
Input counts are 2,265–3,814 tokens; the requested context is not near exhaustion
for these recorded inputs and outputs. All bodies survive into the journal.
These observations do not support clipping, fallback, a hidden 768-token cap,
or a timeout as the reason these particular files are short.

Provider elapsed time ranges from 19.125 to 208.815 seconds, with a retained
853.333-second request deadline. The longest response completed normally despite
passing the old 150-second threshold. This is a selected successful case, not an
estimate of all attempts' completion rate or typical latency.

The [shared prompt](../research/outputs/2026-09-09-minime-nine-report/source/prompt.txt)
allows questions, observations and improvements, and has no maximum word count.
It also explicitly permits a continuation choice alone. The dominant form here
is a local page summary. That combination is consistent with brief output, but
no prompt ablation was performed. Raising a maximum does not ask the model to use it.

### Dedicated thinking mode is disabled

The retained requests explicitly set `think: false`; the raw messages contain no
separate thinking text. Read-only inspection of the installed model after the
sample lists `thinking` among its capabilities; the
[metadata capture](../research/outputs/2026-09-09-minime-nine-report/source/ollama-model.json)
records the time and installed 11.9B Q4_K_M model identity. This post-sample
capability query is distinct from the per-generation model name/setting evidence.

[Ollama's thinking documentation](https://docs.ollama.com/capabilities/thinking)
distinguishes enabling its separate reasoning output from hiding it; the
[chat API](https://docs.ollama.com/api/chat) documents `think`, `message.thinking`
and the generated-token counter. In this lane we increased an output ceiling
while continuing to disable the dedicated reasoning mode. That does not mean
the model performs no reasoning, nor would a longer journal measure internal
computation. A thinking-enabled trial could improve the comparison, produce the
same short final answer, or spend more time without improvement. It has not run.

### A real source-review lead: queue rejection versus invocation failure

The 12:25 entry correctly notices `try_send` dropping work on full/closed queues.
The exact source's rejection branch logs a warning; it does not call the specialized
terminal provider-error publisher used for execution failures in the worker.
This motivates a focused caller-completion test for an eligible provider request
that cannot enter the queue. A live hanging request is not established here.

There is another comparison worth pursuing: whether separate multi-interceptor
tasks preserve the per-capsule publish ordering claimed in the dispatcher comment.
The code shown uses the per-capsule queue only in the single path. Capsule locking
and concurrent scheduling need examination before claiming a runtime ordering bug.
Neither question requires more paraphrase of the same page; both require relating
the two implementations and checking the caller/test contracts.

The duplicated 12:25 answer also introduces `exact_local__provider_failure_message`
with a second underscore. The source contains `exact_local_provider_failure_message`.
The first half spells it correctly. More output in this case includes a small
new factual error, reinforcing that useful development must be measured separately.

## C. What fell out

1. **Shared study memory first.** Retain recent complete responses within an explicit
   context budget, plus a Being-authored durable finding/current question. Preserve
   conclusions, exact source origins and uncertainty across page changes. Let the
   Being replace or close the question naturally; make saving that choice easy.
   Do not equate omission of an optional marker with an intentional wish to lose
   the conclusion. Do not auto-assert that a question is resolved.
2. **Make synthesis and useful navigation immediate.** Put the Being's current
   question alongside an optional exact `RELATE dispatch_single` choice and a
   small selected-page comparison. Encourage developing an answer, its limits,
   implications or a test before paging on when useful, without compulsory
   sections or a word minimum. Distinguish “where I asked this” from “where the
   answer is.” Existing QUESTION/RELATE/SESSION features need easier use here.
3. **A bounded study-only thinking trial.** Compare the same saved source and
   question with thinking disabled/enabled; track source accuracy, retention of
   the task-lifecycle distinction, new useful questions, duplication, native finish,
   final-answer versus reasoning use and latency. Give reasoning and final output
   adequate total/context/deadline headroom; retain only authored visible answers
   as study notes. Keep Astrid/Minime capability handling explicit and shared in
   intent. This is a proposed intervention, not a live change or promised benefit.
4. **Focused dispatcher qualification.** Test full/closed eligible-provider queues
   for an explicit caller-visible terminal outcome, and separately test claimed
   publish ordering across single/chain dispatch. Treat source leads as review
   questions until reproduced. Keep them separate from the study-memory repair.

For evaluation, count questions advanced or revised, supported comparisons and
findings carried into the next page. Retain length and duration as secondary
measurements. The new cap can stay while memory and study purpose are repaired;
raising it again alone does not address the observed normal early stops.

## Reproduction and boundaries

```sh
python3 -m reservoir_research.study_sequences \
  research/outputs/2026-09-09-minime-nine-capture/capture.json \
  --out research/outputs/minime-nine-replay
python3 probes/minime_nine_studies.py
```

The probe verifies every captured-record hash and all nine unique receipt/journal
joins, preserves original material, and derives the figures above. Code snapshots
and whole-file hashes are retained under the report's `source/` directory.
No live source edits, model generations, Being messages, restarts, deployments,
scheduled-study changes or Git commits were made in this investigation.

## Board updates pending

The authenticated Hold Shelf UI was readable as Mike Purvis, showing 178 cards.
This is not a login failure. A write-capable Artifact connector was unavailable,
and the browser tool exposed navigation/state without a documented form-edit API
in this session. The new finding and log payload are retained in
[minime-nine-studies-pending.json](../board/minime-nine-studies-pending.json);
no board write or save verification is claimed. Older pending updates are not
silently marked synchronized by this successful board read.
