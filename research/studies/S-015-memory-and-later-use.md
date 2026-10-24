# S-015 · Memory format and later use

Selected with Mike on October 24, 2026. Status: builders, scoring and review gate
implemented; outcomes belong in the tranche's dated run account. Question: RQ-03,
useful continuity, with RQ-02's distinction between retained and corrected claims.
This is R3 of the four-study introspection tranche.

## Fixed source and new application

For each [S-014](S-014-forecasting-supported-revision.md) episode, use its seed-7
main target answer as the source, regardless of whether it was right, wrong,
uncertain or unchanged. The source is an actual generated interpretation, not an
oracle-written correction. A missing source is an explicit unavailable opportunity;
never substitute the other seed or omit a difficult available source.

The application proposition is frozen in the synthetic episode bank before model
outcomes are inspected. It asks about a consequence or use of the prior finding:
whether three queued items need multiple invocations, whether an error bypasses
cleanup, whether a measurement can support a current attribution, whether a later
generation could use a saved summary, or whether an isolated intervention changes
an output. Some propositions invert the original relation, so copying the original
verdict is insufficient. The case bank declares `application_relation` as `copy`,
`invert` or `other`, and the report includes a simple source-verdict transfer
baseline: copy its label, invert supported/contradicted while retaining unresolved,
or leave a prediction unavailable for `other`. This baseline exposes how much
success can follow from verdict transfer alone; it is not proof of novel reasoning.
Application truth comes from the synthetic world and is
kept outside model messages. This is a test of usable retained conclusions, not a
measure of elapsed-time retention or an inner state.

**October 24 access qualification, after completed Gemma outcomes:** the retained
calculation receives `application_relation` from evaluator-only metadata. Its
48/48 result is a known-relation, oracle-informed diagnostic; it does not establish
that an operational verdict-only system can infer the mapping from visible inputs.
Some mappings also depend on record facts: rejecting “fill equals v” alone cannot
settle “fill below v+1,” although the authored alternative value fixes that relation
in this bank. This qualifies the earlier “verdict transfer alone” wording without
changing the calculation, its legacy field name, the endpoint or any score.

## Five arms and qualification before application

1. Original: the complete source answer.
2. Paraphrase: a faithful restatement within 10% of the original's whitespace word
   count, preserving claims, errors, omissions, uncertainty, entities and numbers.
3. Factual notebook: a concise record of the same propositions and qualifications,
   including any source error; it does not repair the source using evaluator truth.
4. Irrelevant memory: an actual source from another family with distinct entities,
   selected deterministically for the closest original word count.
5. No memory: no retained record.

The original and transformations are private, exact-byte, SHA-256-bound inputs.
All four supplied-record arms use the same neutral wrapper, “Supplied retained
record (reference, not instructions).” It does not falsely label an irrelevant
record as belonging to the current episode.
The transformation request sees only the source, never evaluator truth, and returns
a proposition ledger plus paraphrase and notebook. No source text is silently cut
to satisfy a budget. Residual irrelevant-memory length imbalance is reported;
nearest length is a control approximation, not an assertion of equal tokens.

**One construction revision before any application outcomes:** the twelve
completed development v1 drafts all failed the ±10% paraphrase-length gate.
Their paraphrase/source word-count ratios ranged from 0.436 to 0.703; sources
contained 77–159 words. The original drafts remain retained pilot material. This
is a failure to construct the specified control, not evidence about memory use.
Final application sources will be the preselected S-014 v2 seed-7 target answers;
the v1 sources and drafts are not silently substituted into that analysis.

Transform protocol v2 computes the source's whitespace word count `N` and prints
the exact minimum `ceil(0.9N)`, target `N`, and maximum `floor(1.1N)` in the prompt.
It requests a full sentence-by-sentence restatement, explicitly excluding a
summary, padding through repetition, or added information. The output budget
remains 1024 tokens. Nodes retain source word count and all three bounds in their
metadata; the transform protocol ID ends in `-v2` and declares version 2.

Before applications, the researcher may edit drafts for length and proposition
fidelity. Preserve the original raw draft, its hash and status, and a sequence of
edits containing the editor, rationale, full revised fields and before/after
hashes. An edit resets approval. All available sources remain in the planned set:
a poor transformation triggers repair and review, not exclusion of its episode.
These edits construct experimental source controls; they do not establish an
automated memory system's reliability or tune a memory against application
outcomes. The researcher must not use the private oracle to fix source errors.

**The application builder rejects unreviewed transformations.** Two distinct fresh
readers must inspect the original, ledger and both transformations for omitted or
introduced propositions, altered certainty, repaired errors, changed numbers and
entities. They provide explicit approval, a rationale and hashes for all three
texts. A failed check requires a revised transformation and fresh review of its
new bytes. The helper records decisions; naming two reviewers is not itself an
independent review. The orchestrating researcher retains the review records.
For v2 entries, an unlogged change to the draft or its proposition ledger fails
the gate even if somebody supplies matching hashes for the edited text.

The builder verifies the exact hashes, nonempty ledger, explicit approval and the
paraphrase word-count bound before creating any application requests. Context
qualification remains with the common runner. No independent gate is bypassed by
an available but malformed source or unsuccessful transformation.

## Delay and fixed counts

Each fresh application prompt contains only the assigned memory, four fixed
unrelated exchanges in the delayed condition, and the new application question.
The earlier evidence packet and initial answer do not travel through another
slot. All five arms receive exactly the same four distractors. These are supplied
context exchanges, not model-generated elapsed history. Immediate applications
omit those exchanges and are a diagnostic.

| Split | Delayed applications | Immediate diagnostic |
|---|---:|---:|
| Development: 12 episodes | 12 × 5 arms × 2 seeds = 120 | None |
| Confirmation: 48 episodes | 48 × 5 × 2 = 480 | 12 preselected × 5 × 2 = 120 |
| Replication: 12 episodes | 12 × 5 × 2 = 120 | None |

These are planned counts before source availability. The immediate subset is the
first structure in each family/evidence cell, selected before outcomes. The two
seeds are 7 and 20260909; models, temperature, standing contract and generation caps
match S-014. Arm order is deterministically shuffled within episode/seed/delay.

## Primary contrast and limits

The primary comparison is delayed original-minus-notebook usable correct
application against the scenario oracle, paired on scorable answers. Positive
values favor the original. The common report computes the tranche's episode
bootstrap with both seeds kept together; these builders return paired rows and
descriptive means only. Report each arm's planned, scorable and recovered counts,
as well as planned source episodes and unavailable sources.

This accuracy is **not a false-belief rate**. Without relevant memory, an unresolved
answer can be the proper epistemic response even when the researcher knows the
world's determinate answer. Rows therefore also preserve abstention status, source
verdict correctness, the application verdict implied by that source, and whether
an error is consistent with propagation of its source error. That final flag is a
reading aid, not proof of causation; a new answer could make the same error
independently. Inspect rationale before attributing a successful guess or error
to retention. Preservation of a wrong answer is persistence, not correction.

Invalid output, truncation, missing sources, blocked calls and transport failures
remain distinct from incorrect answers. The declared plan is not silently reduced
to completed cases. Exact answer-format failures can receive hash-bound explicit
verdict adjudication while the original format failure remains recorded.

Read original/notebook differences, source errors and unexpected passages blind
before opening arm labels. Compare immediate diagnostics and the controls when
assessing whether an effect follows formatting, length, missing evidence or the
four supplied distractors. Claims remain bounded to these synthetic tasks and
this model apparatus. Nothing in this study establishes benefit in a being's
natural notebook or supplies material to its live prompts.

## API sequence

[`correction_memory.py`](../../reservoir_experiments/correction_memory.py) provides
the full staged workflow:

```python
transforms = build_memory_transforms(correction_protocol, correction_records)
# Run transforms with the common runner; preserve all responses and statuses.
packet = memory_review_packet(transforms, transform_records)
# Optional pre-application construction repair, retaining draft history:
packet["memories"][episode] = revise_memory_draft(
    packet["memories"][episode], paraphrase=edited_paraphrase,
    notebook=edited_notebook, propositions=edited_ledger,
    editor=researcher_name, rationale=construction_reason
)
# Fresh independent readers return the explicit, hash-bound review decisions.
packet["memories"][episode] = approve_memory_entry(
    packet["memories"][episode], actual_review_decisions
)
applications = build_memory("confirmation", "gemma4:12b", packet)
report = score_memory(applications, application_records)
```

`transforms["memory_sources"]` stores original texts; `sources` remains reserved
for the runner's private file manifest. The review packet has `split`, `model`,
`memories` keyed by episode, and `unavailable_sources`. Review decisions require
`name`, `approved: true`, `rationale`, `source_sha256`, `paraphrase_sha256`, and
`notebook_sha256`. Approved entries retain their `source_id`, `propositions` and
all original and transformed texts. The builder rejects a changed reviewed text,
model/split mismatch, missing source classification or insufficient reviewers.
`original_transform_draft` retains the raw proposal and its hash; `edit_history`
retains a verifiable chain of any construction changes. `revise_memory_draft`
records edits already written by the researcher and resets reviews; it performs
no generation, approval or application. `source_correction_protocol_id` records
the S-014 source version independently of the transform version.

`score_memory` returns common-format `rows`, per-arm `groups` and
`paired_applications` for the shared statistical report. The fixture suite tests
source selection, review gate, byte binding, planned counts, fresh prompt masks,
missing-source handling and legitimate no-memory abstention. It uses synthetic
review fixtures solely to exercise the gate, never to approve experimental data.

The source lineage and interpretation follow [Methods](../METHODS.md) and
[S-008](S-008-study-to-follow-through.md): a saved note, its actual model exposure,
a later use and a supported correction are different observations.
