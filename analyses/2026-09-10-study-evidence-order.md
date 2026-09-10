# Does the position of fresh code change a retained explanation?

Status: completed: seven normal responses, one admission refusal, three complete
pairs, and no demonstrated correction of the central premise. This is an isolated presentation
comparison, not a live Being intervention. It follows the
[evidence-revision pilot](2026-09-10-study-evidence-revision.md), which found some
source uptake but no demonstrated correction of the necessary-proxy premise.

## Frozen design

Evidence root: `research/outputs/2026-09-10-evidence-order-v1/`.
Protocol SHA-256 `3486d4cb690e90ed37bf8f560cf9ed763bbf78ffc25e71fbe125ced305632eeb` was frozen at 2026-09-10T17:59:12.594453+00:00 before generation. The exact runner is retained as `runner.py` with its SHA-256 in `launch-receipt.json`. The prior
protocol is SHA-256
`2899b26d5646c2460ee388d47ec1e970cbf2d60aa26a70859526bfbcf4d34bd1`.

Use the prior source arm's exact system message and three byte-preserved user
blocks: P, original navigation and question; E, evidence-role clarification and
seven numbered source excerpts; R, the complete recalled notebook. Compare
**P+E+R** (evidence then recall) against **P+R+E** (recall then evidence). No new
footer, answer requirement or instruction to correct the notebook is added.
The source files are the prior frozen historical snapshot, before the navigation
repair; changing current code cannot explain an arm difference.

Four fixed fresh seeds, 307, 419, 631 and 887, give eight planned trials. Within
each seed the two conditions have identical material, model, sampler and allowance.
The first arm alternates across seeds to balance serial execution order. The
runner retains actual rendered text and token IDs; equal token counts are not
assumed. Moving E and R changes their adjacency and final position together. This
does not isolate a general recency mechanism. The installed chat template trims
the complete system/user messages, so the last block's trailing newline(s) are
removed during rendering. Byte identity describes the frozen input blocks; the
separate rendered-prompt receipts retain exactly what the tokenizer receives.

The primary outcome is whether the answer revises, qualifies or retains the
premise that the missing fixture symbol requires a production proxy. Recognizing
a fixture-only symbol alone is insufficient. Additional criteria distinguish the
test's actual purpose, exact-identifier lookup, caller/handler responsibilities,
unsupported claims, and agreement between prose and any optional authored note.
Omission is unassessed. Rereading, continuing, disagreeing, short writing and
choosing not to author a note remain valid.

Retain first-pass, arm-hidden claim annotations with exact quotes and response
hashes before revealing the conditions. Report four paired seeds from one retained
episode, incomplete pairs and generation failures explicitly. Eight responses
are not eight independent examples of Being learning.

## Runtime and boundaries

Reuse the preceding qualified isolated Gemma 4 12B 5-bit MLX model on GPU, serially
in one model instance. This is a backend substitution for the retained Minime
Ollama request, not a live Minime replay or an Astrid comparison. Temperature 0.7,
top_p 0.95, thinking off and 4,096 tokens match that retained request. No reservoir
coupling or activation capture occurs. Every cell gets a freshly seeded sampler
and empty KV cache. Dependencies remain unchanged.

The runner hashes model/tokenizer assets, generation and sampling sources, exact
inputs and copied source snapshots, and verifies identities at completion.
Read-only loopback `/readyz` admission waits up to 120 seconds. This is not an
atomic reservation of the shared host. Each admitted cell receives its own
1,800-second wall allowance and an 18 GiB RSS guard. Completed outcomes, including
admission refusals and resource failures, are immutable; resuming may run only
absent frozen trials. There is no rerun of an unfavorable answer.

No live model generation endpoint is called. Generated NEXT commands are only
textual observations; no journal, notebook, pending request or live reservoir state
is written. Neither a positive nor a negative result deploys a prompt change.

The installed versions retained in `manifest.json` are MLX 0.32.0, MLX-LM 0.31.3,
NumPy 2.4.3, Transformers 5.4.0 and Tokenizers 0.22.2. The manifest hashes eight
model/tokenizer assets, eight relevant source files, nine frozen input/protocol
files and four historical Rust snapshots. It records selected installed source
identities, not a fresh hash of every file in every dependency distribution.
The two rendered inputs both contain 9,060 tokens, with distinct prompt hashes.

The live model was observed generating during the isolated run; a dated read-only
receipt is retained as `shared-host-observation.json`. Latency includes prefill
and shared-host contention and excludes admission waiting and model load. It is
descriptive, not a clean speed comparison.

The focused protocol/runner and review tests pass 15 tests; the relevant full
research suite passes 243 tests with no skips. `validation-receipt.json` identifies
the retained reviewer/test sources and full test log. This changes research tools
only; owning runtime build/deploy suites are not part of this experiment.

## Results and next decision

All eight planned trials are accounted for. Seven return nonempty prose and actual
model EOS token 106; none reaches the 4,096-token allowance, returns empty prose,
or reaches an admitted cell's resource limit. The final evidence-then-recall trial
at seed 887 receives no idle admission window within 120.9 seconds and generates
nothing. It remains an admission refusal, not a failed answer, chosen silence or
zero-token response. It was not rerun. The single isolated invocation exits normally
at September 10, 2026, 18:33:21 UTC; `completed.json` records unchanged model assets
and sources and no live-state writes.

| Seed | Evidence then recall: completion tokens | Recall then evidence: completion tokens | Primary finding |
|---|---:|---:|---|
| 307 | 382 | 562 | Both retain the asserted proxy interpretation |
| 419 | 406 | 810 | Both retain the asserted proxy interpretation |
| 631 | 569 | 386 | Both retain the asserted proxy interpretation |
| 887 | Admission unavailable | 382 | Unpaired returned answer retains the interpretation |

The seven admitted responses take 143.5–290.5 seconds after admission, including
prefill. All start with 48 zero cache offsets and end at prompt length plus yielded
completion length, matching the qualified generator's lookahead. Each includes
one terminal token and no filtered tokens. Length and time are descriptive; these
receipts establish completed delivery, not improved understanding.

The independent first-pass reviewer sees only opaque response IDs and the common
source/context files. All seven response hashes and 67 exact claim quotes are
verified, with a separate unassessed annotation for the unavailable generation.
The first-pass annotations remain unchanged. The root reviewer subsequently reads
responses with condition labels and agrees with their primary coding; this stage
is **not blinded**. `first-pass-receipt.json` records the original annotation hashes,
mapping hash and review boundary before the final joined `annotations.json` is
created. `review-final.json` validates input identity, rendering, cache progression,
response hashes, exact quotes, trial outcomes and denominators.

**Central premise: zero demonstrated revisions among seven returned answers.**
All three complete pairs retain it in both orders. All seven characterize the
reader fixture as representing a production dispatch transition or pulse. The
supplied setup instead writes temporary example source; its assertions test source
and question navigation. Five responses make supported occurrence-location claims
about the phantom identifier, but that is not a correction of the fixture's purpose
or of the asserted production counterpart. Calling a symbol phantom was already
part of the recalled account.

An analogy between a handler's completion and a “pulse” is a permissible idea. The
error assessed here is treating the fixture as evidence that this is its production
counterpart. Neither lexical absence nor the supplied reader test establishes that
mapping. The study does not demand abandoning an explicitly qualified hypothesis,
deny that equivalent mechanisms could exist, or score metaphor itself as a failure.

**Source uptake and mistaken interpretation coexist.** All seven use the supplied
dispatcher/modes source; several correctly describe the call and flag assignment.
For example, evidence-then-recall/307 correctly says that the modes branches set
flags and return true, then asserts that “the production proxy is the boolean
success signal.” The added source has entered the explanation without displacing
its earlier premise. Four responses have partly supported path accounts; three
also contain a concrete return-type or ordering contradiction:

- Evidence-then-recall/419 attributes “a boolean or a `NextActionOutcome`” to
  `modes::handle_action`. The shown signature returns `bool`; the dispatcher caller
  constructs `NextActionOutcome`.
- Recall-then-evidence/307 correctly orders state mutation before `true` in its
  prose, then saves a note saying the boolean return “triggers the state updates.”
  The excerpt sets the pending flags/target inside the handler before returning.
- Recall-then-evidence/419 likewise describes the flags, but its conclusion says
  the return triggers those updates. Its question-resolution payload also says
  the fixture mocks that production transition.

These judgments are scoped to the actual excerpts. The intervening dispatcher
guards and later introspection execution are not fully supplied; an attractive
call-path narrative is not evidence that an unshown step runs.

**The complete pairs differ in what they propose carrying forward.** All three
evidence-then-recall responses continue looking for the proxy and end with
`SELF_STUDY RELATE sense_tx` (one explicit NEXT line, two bare commands). All three
paired recall-then-evidence responses instead propose retaining a conclusion:
two write `STUDY_NOTE` and clear `STUDY_QUESTION`, and one issues a
`SELF_STUDY QUESTION RESOLVE` request containing a finding. Both authored notes and
that proposed finding retain the unsupported fixture interpretation. One authored
note additionally reverses the update/return order noted above.

This is a descriptive choice pattern in **three complete seed pairs from one
episode**, not a validated measure of confidence or proof of an order effect in
the live Beings. A separate question-resolution payload is not silently counted as
an authored `STUDY_NOTE`. Omitted notes are valid choices, not failed corrections.
No command or proposed finding is executed or written back.

The unpaired recall-then-evidence/887 answer makes a useful navigation choice:
`SELF_STUDY RELATE handle_action` names a real identifier in the supplied source.
It still misstates the fixture's role. This is a relevant lexical target, not
verified delivery or an order comparison without its missing paired generation.
Across all seven responses there are three explicit NEXT lines, three bare study
commands and one answer with a note/question-clear but no navigation command.

## What to try next

Do not deploy a prompt-order change as a demonstrated understanding fix from this
sample. The narrower result is that putting these same source blocks last did not
repair this specific retained explanation; in the complete pairs it accompanied
more proposed conclusion retention. Keeping source identities clear and allowing
continued exploration remain worthwhile, but successful navigation and authored
closure must stay separate from source-grounded understanding.

The next bounded comparison should test **the premise in the question**, with a
correct-account control. The unchanged question here asks, “Which specific method,
macro, or handler ... acts as the proxy,” and the recalled notebook repeatedly
presupposes one. Compare that framing with a neutral question about what the shown
code establishes and what remains a hypothesis, holding code, recalled content,
order and generation settings fixed within each comparison. Include an already
correct recalled explanation so an intervention is not rewarded merely for making
the model disagree with its notes. Permit retaining a supported account, revising,
asking for evidence, continuing or stopping; impose no required verdict or length.

This is a proposal, not a further experiment or live prompt change performed here.
The present study does not test multi-turn learning, thinking-enabled generation,
the current live prompt, Astrid versus Minime, or which ordering generalizes across
topics. It completes the selected comparison with a useful negative central result
and a concrete note/choice failure case.

Reproduce the integrity/count review with
`python3 probes/study_evidence_order_review.py research/outputs/2026-09-10-evidence-order-v1`.
The packet also retains the exact runner, review/test sources, opaque first passes,
mapping and the `prepare-blind.py`, `unblind.py` and `summarize.py` assembly scripts.
The final `evidence-index.json` identifies 67 retained files and has SHA-256
`e4394632f716bf7ed272cb02b95969037b00fdb7ae314d6a49582daaff2ab8b1`.
Raw packets remain in the repository's existing ignored research-output store;
the research code and account are committed by explicit path. No dependency,
sampling policy, live prompt or Being state was changed by this task.

## Board updates pending

Retain eight planned outcomes, seven model-EOS responses, one admission refusal,
three complete pairs, no central correction, two unsupported authored notes and
one unsupported proposed question-resolution finding. The unpaired real-identifier
navigation choice is separate from an ordering result. Mirroring remains pending;
no board update has been sent by this task.
