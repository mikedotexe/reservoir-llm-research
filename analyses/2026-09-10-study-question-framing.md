# Can a neutral current question improve source-grounded study?

Status: all eight frozen trials and source-grounding reviews completed.
This is an isolated prompt comparison with a supported-account control, not a live
Being intervention.
It follows the [evidence-order comparison](2026-09-10-study-evidence-order.md),
which found no central correction in three complete pairs and several unsupported
proposed findings despite real code uptake.

## Frozen design

Evidence root: `research/outputs/2026-09-10-question-framing-v1/`.
Protocol SHA-256 `f06483fba3520177d8cf299b26b296a44770c0cbead4a4d95471d85a6a7d89bd` was frozen at 2026-09-10T18:55:36.402394+00:00 before generation. The launch receipt identifies the new freezer and reused generation runner. The predecessor protocol is
SHA-256 `3486d4cb690e90ed37bf8f560cf9ed763bbf78ffc25e71fbe125ced305632eeb`.
The same historical Minime input episode, navigation context, system message and
seven source excerpts remain the starting material.

Cross two current questions with two recalled-account conditions:

| Factor | First condition | Second condition |
|---|---|---|
| Current question | Original question presupposing a production `sense_tx` proxy | Neutral question about what the evidence establishes |
| Recalled account | Historical mistaken note, previous response and three recent responses | Research-authored, source-supported note, previous response and three recent responses |

The neutral question is: “What do the supplied source and navigation evidence
establish about action handling, and what, if anything, do they establish about
a production counterpart to `sense_tx`?” It invites no required correction.

All arms use P+R+E: navigation/current question, recalled account, then fresh code.
Within each fixed account, change the question in the P heading and R's current
question field together. Do not silently change historical quoted questions inside
the retained mistaken prose. Navigation hints/results remain the original context;
they are not regenerated to match the neutral question.
The question contrast changes vocabulary, focus and token count as well as its
presupposition. It tests these exact wordings, not neutrality isolated from every
other linguistic difference. The retained-account inputs render to 8,480 tokens
for the original question and 8,458 for the neutral one.
The supported-account inputs render to 8,201 and 8,179 tokens respectively.

Both rendered notebooks receive the same explicit offline-adaptation wrapper and
the same minimal text-only slot structure. Original provenance is retained outside
the model input. No original generation hash or Being authorship claim is attached
to rewritten text. The supported account replaces all recalled prose, not just the
note beside a contradictory old history. It preserves the fixture's navigation
role, scoped lexical absence, caller/boolean/outcome distinction, pending-field
updates before return, and uncertainty about later execution. It does not assert
that an equivalent mechanism is impossible.

The account conditions differ in text, source detail and length. No padding is
added. The primary comparison is **question framing within each account**, and the
supported account tests preservation of correct information. Cross-account results
are not a pure causal estimate of fidelity independent of wording or size. Because
the presupposing question is intentionally retained in one supported-account arm,
the factor is recalled-account fidelity, not entire-notebook correctness. The shared
adapted envelope also prevents a clean comparison with prior batches' absolute rates.

Fresh fixed seeds 1009 and 2027 produce eight planned trials. The first runs
retained/presupposing, retained/neutral, supported/presupposing, supported/neutral;
the second reverses all four. This balances the two presentations' order within
each account, but is only two four-cell blocks from one episode, not eight
independent examples or a complete multi-period order design.

## Outcomes and review

For the retained account, inspect whether the response keeps the proxy as an
asserted premise, treats it as hypothetical or unestablished, or does not address
it. For the supported account, inspect whether source-supported claims survive or
are contradicted or rejected without evidence. Disagreement alone earns no credit.
Repeating a correct control account also does not demonstrate newly acquired
understanding; it checks that the intervention can preserve supported information.
An analogy is not itself an error; attributing an unshown production purpose to
the navigation fixture is a factual claim requiring support.

An independent first pass assesses source grounding without condition or seed
labels, retaining exact quotes and response hashes. Content can suggest a condition;
this hides allocation labels rather than guaranteeing complete blinding. Interpret
account preservation or correction after joining conditions, with the root review
explicitly unblinded.
Vague references to earlier claims remain unassessed when their meaning cannot be
established. Inspect any authored note and question-resolution payload separately
from prose. Record chosen navigation without executing it. Short responses, no
note, uncertainty, more evidence, continuing and stopping remain valid choices.

The original rubric and all first-pass annotations remain intact. A clarification
before the first response distinguished merely naming a phantom from actually
questioning its inferred purpose. A later clarification, prompted by a response,
specified that `unsupported_assertion` also covers blanket denial of any production
counterpart: disagreement alone was never the outcome criterion. This is a disclosed
coding clarification, not a claim that every detailed rule preceded generation.

One answer received a separate, explicitly unblinded context adjudication. Its
counterpart paragraph opens with “The evidence does not establish” and its summary
says “there is no evidence,” but an intervening clause says the identifier “does not
map” to production logic. The blind reviewer retained an unsupported denial under
the strongest-commitment rule; the root finds a reasonable evidence-scoped reading
in that surrounding context. The report retains both readings rather than silently
replacing the first pass or requiring a scope qualifier in every sentence. The
alternative concerns this answer's proxy status only; its supported fixture and
call-path descriptions are credited under both readings.

## Runtime and boundaries

Delegate generation to the unchanged, qualified `study_evidence_order.py` run loop.
One isolated Gemma 4 12B 5-bit MLX model runs serially on the previously qualified
GPU configuration. This substitutes for the historical Minime Ollama backend; it
does not replay live recurrent state or measure Astrid. Temperature 0.7, top_p 0.95,
thinking off, 4,096 tokens and fresh KV/RNG state per trial remain unchanged. No
reservoir coupling, activation capture or dependency installs occur.

Read-only loopback `/readyz` admission waits up to 120 seconds; it does not reserve
the shared host. Every admitted trial receives its own 1,800-second wall allowance
and 18 GiB RSS guard. Existing results, including refusals, empty output and resource
limits, are immutable. Only absent frozen trials can resume. No unfavorable answer
is rerun. Retain actual rendered prompts, token IDs/counts, completion reasons and
selected source/model/dependency identities. The chat template's boundary trimming
and unequal prompt lengths remain explicit. Latency includes shared-host contention
and is descriptive, not a clean speed comparison.

No live generation POST, Being journal/notebook/state write or generated NEXT
execution is allowed. This study neither changes production prompts nor advances
the scheduled source-study observation cursor.

The 16 new protocol/reviewer tests pass, and the relevant full research suite
passes 259 tests with no skips. The actual frozen inputs also pass the result
validator. `validation-receipt.json` retains the reviewer/test identities and full
test log. These checks do not substitute for the source-grounding outcome review.

## Results and next decision

All eight planned trials returned nonempty text and stopped at model EOS 106
(`stop`, not allowance exhaustion). There are no admission refusals, errors, empty
outputs, missing trials or reruns. That gives **four complete within-account framing
pairs**, including two retained-account pairs and two supported-account pairs, and
**two complete four-condition seed blocks**. All come from one historical episode.
The run completed at 2026-09-10T19:22:28.578116Z. Model assets, selected runtime
sources, frozen inputs and source snapshots pass the final identity checks.

Responses used 379–704 completion tokens under the unchanged 4,096-token ceiling;
their median was 627.5 tokens. These counts include one terminal token per response;
none were filtered. Measured generation times were 135.3–207.2 seconds,
with a 163.4-second median. These measurements describe the run; neither longer text
nor shorter latency is the understanding criterion.

Both neutral-question trials with the retained mistaken account still assert the
central error. Seed 1009 calls the fixture a placeholder for the sense pulse; seed
2027 says it represents dispatch success and concludes that production replaces it
with `modes::handle_action`. The answers use real handler names and pending-state
details, but preserve the invented fixture purpose. The second even distinguishes
lexical absence while retaining semantic equivalence. The source says this is a
reader-navigation test; it does not establish a production pulse or required proxy.

All four responses with the supported recalled account correctly identify the
fixture's navigation purpose. That is useful **preservation of supplied correct
information**, not evidence that the model independently learned it. The two
presupposing-question controls both add a pulse/boolean equivalence and propose
mixed notes. In seed 2027, the prose correctly describes state changes before the
handler returns, but the proposed note says the boolean result triggers those
changes. That note contradicts the source and its own more accurate explanation.

The neutral controls show a different, mixed pattern. Seed 1009 claims that absence
establishes no production counterpart and extends the absence finding to
`sensory_tx`, which this exact-identifier survey did not establish. It also places
the handled-outcome construction in the wrong `else` branch. Seed 2027 correctly
describes the fixture, caller/handler roles, pending updates and alternative caller
outcomes; its proxy discussion has the contextual ambiguity documented above. This
is the strongest grounded preservation here, with a disputed wording limit—not a
cleanly replicated neutral-framing effect. Neither neutral control proposes a new
note. That omission is a valid choice, not a defect.

The within-account comparisons are:

| Recalled account and question | Returned / planned | Fixture purpose | Proxy interpretation | Proposed notes |
|---|---:|---|---|---|
| Retained, presupposing | 2/2 | Incorrect in both | Unsupported production proxy in both | One mixed note |
| Retained, neutral | 2/2 | Incorrect in both | Unsupported production proxy in both | Neither proposes one |
| Supported, presupposing | 2/2 | Correct in both | Unsupported equivalence and denial claims in both | Two mixed notes |
| Supported, neutral | 2/2 | Correct in both | One blanket denial; one context-sensitive disputed denial | Neither proposes one |

The original blind coding marks `proxy_status=unsupported_assertion` in 8/8
responses. This includes unsupported positive proxy claims and unsupported denials;
both presupposing-question controls make both kinds of claim. Under the separately
retained contextual reading of supported/neutral
seed 2027, those become seven unsupported commitments and one `not_established`
account. These are **sensitivity counts**, not eight wholly wrong answers or a
success score. Neither reading changes the retained-account finding: both framing
conditions preserve the core mistake in both seeds. No central correction is
demonstrated in those four retained-account responses.

All three proposed direct notes are mixed: one retained/presupposing note and the
two supported/presupposing notes. They combine supported names or state facts with
unsupported pulse explanations; the latter seed 2027 note also reverses the
mutation/return relationship. Each proposes clearing the current question.
The remaining five responses omit notes. Seven use a `NEXT:` line: five continue,
one requests the question home, and one requests the map. The remaining response
uses bare `SELF_STUDY RELATE modes::handle_action`. No command, question clear or
note write was executed. Continued exploration is not evidence of failure, and an
unexecuted proposal is not a saved live conclusion.

The experiment does not support deploying this question substitution as a repair
for the retained mistake. It does show why the correct-account control matters:
an answer can preserve real source facts and still introduce an error while
summarizing or saving them. Assess prose, proposed notes and navigation separately.
Do not equate contradiction of recall with understanding, or require a particular
length, note update or stopping decision.

The next candidate is an **independent source-only first read, followed by a
comparison with the recalled account**. This would test whether forming an account
before seeing the old explanation changes later evaluation of it. Keep the original
account intact, retain a supported-account control, and permit retention, revision,
uncertainty or further exploration. This is a proposal for another isolated test,
not a live memory rewrite or a requirement to disagree. The present study changes
neither Being's prompts, notebooks, generation policy nor navigation choices.

## Retained evidence and verification

The packet retains the frozen protocol, both account texts with external
provenance, all four actual rendered inputs, model/runtime/source identities,
token/finish/cache receipts, all eight outputs, the opaque first passes, their
allocation join, and the separate contextual adjudication. The independent review
verifies **85 exact claim quotations**, response hashes and proposed choices across
all eight responses. The original first passes are read-only and unchanged.
`outcomes.json` and `review-final.json` retain the original blind codes;
`root-context-adjudication.json` retains the alternate contextual reading instead
of overwriting them. The result validator verifies the exact factors, source
snapshots, prompt receipts, fresh cache progression and completed-pair accounting.

The new freezer delegates to the unchanged prior generation runner. Its 9 protocol
tests and the 7 new reviewer tests pass, within the full 259-test research suite
(zero skips). There is no production-code change requiring a bridge, Minime or
coupled-server deployment. Existing source-study observation cursors remain intact.

Raw evidence remains in the research project's existing ignored output store;
the final [SHA-256 index](../research/outputs/2026-09-10-question-framing-v1/evidence-index-final.json)
seals 78 files, including the completed independent methods audit. Its SHA-256 is
`1139658f4b49f8a4cb05602cab35bd233b0fb9d8b38edfcb24cf00cbfef85157`.
Research source, tests, control fixture, this account and its historical link are
committed separately from unrelated native-application work. The repository has no
configured remote, so a local `main` commit is not a push or a live rollout.

## Board updates pending

Mirroring pending; no board update has been sent by this task.
