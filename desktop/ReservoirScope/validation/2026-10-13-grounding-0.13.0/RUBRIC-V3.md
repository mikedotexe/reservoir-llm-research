# Open-writing review contract

This contract replaces the unexecuted v2 writing requirements, as recorded in [SUPERSESSION-01](SUPERSESSION-01.md). It applies to `reservoir-journal-v3`. No model response is prescribed a heading, metric, topic, length, stance or creative form. The evaluation is an offline reading aid and never a feedback/save gate.

## Separate questions

1. **Did the mechanism work?** Record every attempt, real stop/completeness outcome, exact save/readback, actual next-step application, full-text memory exposure and failure. A missing or incomplete response is a mechanical outcome, not a judgment on creative expression. Preserve all attempts; no additional requests to replace difficult results.
2. **What was written?** Describe topic/form, any continuation or revision, questions, images, uncertainty, repetition or departure from prior writing. Short, long, poetic, analytical, conversational or otherwise unanticipated forms are all admissible. No metric omission, absent step heading or word-count target is a failure.
3. **What information was available?** Distinguish current typed readout, actual prior journal text, app-rendered metadata and unknown exposure. A saved wrapper is not automatically supplied context. Quoted memory is historical writing; exact inclusion establishes availability, not understanding or causal influence.
4. **If a literal factual claim is made, is it supported?** Identify its subject and time before checking it. Compare voluntary numerical claims with appropriate current or explicitly attributed prior evidence, allowing stated precision and units. Keep recurrent state separate from the sensory field. For interpretive claims, distinguish supported, contradicted, not established and unresolved, with exact excerpts and the relevant evidence.
5. **What is imaginative or exploratory?** Do not read every image, metaphor, fictional scene, question or self-description as a mechanistic/scientific proposition. Creative language is not automatically a hallucination or an emergence claim. Where literalness is ambiguous, retain that ambiguity instead of imposing a verdict.

No composite score, forbidden-word pass/fail, or requirement to make a scientific claim is used. An entry with no numerical assertion does not fail grounding; it simply supplies no numerical claim to check. A careful denial of an inference is different from an unsupported assertion. An evaluator's uncertainty is not grounds to block an otherwise complete, saved response.

## Deterministic harness role

The amended [harness](../../scripts/journal_quality.py), ruleset `open-writing-review-2`, accepts v3 with no required metrics or opening. Its v3 length-target field is null. Word count and detected formatting are descriptive only. Recognized numerical/step claims still produce comparison candidates, including unit/precision and possible lexical carryover flags, but every candidate requires a reader to establish whether it asserts a present literal fact. A detected mismatch is not automatically an error in fiction, quotation or metaphor.

The known extraction grammar and bounds from the [historical technical rubric](RUBRIC.md#what-the-deterministic-part-recognizes) still describe what the parser can and cannot find; its old v2 mandatory coverage/style instructions are superseded. Negated, historical, conditional and future clauses are conservatively routed to review. Inference cue words only locate passages, including potentially responsible caveats. Claims outside the grammar must also be read. No recognized claims, no cues, or neat formatting ever yields an automatic quality pass.

CLI usage is unchanged except `--prompt-version reservoir-journal-v3` and `--protocol <run-plan-v3.json>`. It still requires material hash-bound to a passing unchanged-export receipt and retained version metadata. Keep each output and the original model text immutable; source changes after the prospective freeze require a new named revision and an explanation.

## Prospective result boundary

Review all outcomes from the [four-attempt plan](run-plan-v3.json), including unsuccessful or unstarted opportunities. The output cap remains 256 tokens; that is a runtime resource bound, not a desired literary length. A cutoff does not authorize a retry, larger budget or editing the saved record.

The known v1 entries may be used as descriptive context, not as a rubric that requires v3 to mimic or negate them. Later trajectories differ with feedback text. Do not turn a more appealing entry into a causal prompt benefit, general accuracy result, autonomy measure, or claim of emergence/consciousness. A successful result for this work is a faithful account of the writing, the mechanism and their limits.
