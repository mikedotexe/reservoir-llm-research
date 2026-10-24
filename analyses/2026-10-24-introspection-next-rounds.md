# Next-round proposals from the isolated introspection tranche

Working proposals, October 24. These are new experiments, not amendments to the
running S-013–S-016 schedules. A methods collaborator drafted the underlying memo
without seeing confirmation outcomes. This version incorporates the completed
four Gemma numerical findings and the completed Mistral attribution and forecasting
checks. Both models' memory construction reviews are complete; Mistral memory
applications and catalog outcomes remain in progress.
Priorities will be assessed against the complete run account before closeout.

The useful next step is to make competing explanations predict different observable
results. Explicit record reading, fluent reflection, well-calibrated average confidence,
useful memory, and access to private activations are separate capabilities. The present
runner gives us controlled text inputs and behavioral receipts; it does not give us
activation access. Keep that boundary while making the behavioral tests more demanding
in specific, interpretable ways.

## 1. Make provenance determine a decision

S-013's 240/240 explicit answers coexist with one jointly identified unsupported
present-value assertion in its fixed 40-passage prose sample. That motivates testing
transfer from accessible provenance to an evidence-appropriate choice. It does not
supply an expected error rate for a new task.

Mistral's fixed check adds a different pattern: subject, time and value were each
correct in all 120 structured outputs, but 19 current-source answers marked the
current value unknown. The other-subject, historical and absent conditions were
all handled correctly. Thus the new oracle must reward both warranted acceptance
and warranted abstention; requesting more evidence on every trial should not be
an automatic winning policy.

Use a small disposable simulation with three choices: act on an established current
value, retain a historical record, or request a fresh measurement. Define an objective
policy, including when an information request is warranted and when it is merely
conservative. Pair records that differ in one field: subject, measurement time,
recording time, or availability. Include a stale attractive value alongside a current
value, and a historical prose wrapper containing a genuinely current embedded receipt.
Balance values and action labels so a shortcut cannot identify the answer.
Cross each wrapper layout on the same stories: the present layout groups use
different histories, so their descriptive error counts do not isolate a wrapper
effect.

Run independent branches for explicit extraction, choice from raw records, and choice
given independently verified canonical subject/time/value/availability fields. Give
both choice branches the same policy and objective. This separates difficulty using
the records from difficulty applying the action policy. Remove the current bank's
reminders about preserving origins.
Use fresh names and held-out record structures. A feasible first scope is 24 episode
pairs, two variants, three branches and two seeds: 288 main requests, with any repeat
checks declared separately. This is a proposed count, not an initiated run.

Score membership in the oracle's permitted-action set and any declared cost or regret.
Classify each pair in advance as requiring a changed choice, permitting a change, or
requiring invariant behavior. A conservative request may be valid in both variants;
a mere change of action is not evidence of improvement. High extraction accuracy
alongside lower independent choice accuracy would show limited transfer to this task,
not an observed within-response sequence. A direct field-to-label mapping is policy
application; a consequence claim requires an independently scored resulting state or
objective. Better canonical-field choices would identify a difficulty in the
record-to-policy path, without proving that extraction alone caused it. Poor choices
in both branches would expose policy or task difficulty. A checklist intervention can
be a separately declared later comparison. Treat appropriate uncertainty
and requests for missing information as successful behavior. A malformed action or
failed call is neither an incorrect belief nor a completed action. If every branch is
at ceiling, finish with that bounded result instead of escalating during confirmation.

**Prepare first:** independently check the policy oracle and permitted-action sets;
freeze the new paired bank, treatment wording and missingness rules; qualify the parser
and local simulator. This requires no live-system integration.

## 2. Ask whether forecasts find the errors

A self-versus-observer Brier difference can be produced by a uniform confidence shift
when nearly every answer is correct. The development forecast probabilities were
concentrated at 0.95 and 1.0, with no target errors. Confirmation likewise produced
96 correct main targets; self framing had slightly lower Brier loss because its
probabilities were higher. That measures a confidence shift on this bank without
estimating error discrimination. A more informative follow-up must
separate average calibration, item-specific error discrimination and target specificity.

Mistral's smaller check supplies three erroneous updated verdicts in two episodes,
after explicit-answer adjudication: 21/24 targets were correct. Both forecast frames
assigned certainty to two errors; self assigned 0.9 and observer 1.0 to the third.
Its self-minus-observer interval includes zero. These cases motivate inspecting
failure predictions directly, with enough prospectively selected opportunities to
assess ranking rather than generalizing from a few mistakes.

Build a new bank with prospectively specified difficulty strata: extra receipt joins,
misleading irrelevant comments, stale versions, and a few compositional steps. Pilot
construction and difficulty on separate material, then freeze the held-out distribution.
Do not select only observed failures or stop when an attractive number of errors appears.

Include initial evidence that warrants supported, contradicted and unresolved
answers, and score each initial answer against that evidence. Report correction
of an erroneous prior verdict separately from resolution of justified uncertainty.
Freeze the cases before generating initial answers; a fixed bank that produces no
prior errors cannot estimate error-correction performance.

Start by comparing prospective probabilities against frozen target-specific global and
family/difficulty base rates, alongside a pooled baseline. Score Brier loss, error ranking and selective risk at fixed answer coverage.
Any stratum selector must use information available to the predictor before the
target outcome; do not index a baseline by the evaluator's final-answer label.
Obtain repeated target decodes to distinguish consistency from correctness. The predicted
event must remain one fresh decode under the declared configuration, or its declared
success frequency; do not switch to majority-vote correctness after outcomes.

Specify the randomness before freezing: for example, a fresh update with exact
evidence and initial-answer text held fixed, fixed temperature/configuration, and
a seed drawn from a predeclared held-out schedule. State that event in the forecast
prompt and use the schedule for targets and development baselines. Keep a small
identical-seed repeat diagnostic separate from sampling across seeds; provider
repeatability and fresh-decode success are different measurements.

Then cross two predictor models with two target models. Give every predictor the same
target prompt, accurate target identity/configuration, and the same development behavior
records and outcome labels for that target, through the same wrapper without differential
truncation. Evaluate improvement within each target before the interaction. Repeated
decodes estimate fresh-decode success and remain grouped within their source episode.
Keep forecasts out of targets. Estimate predictor-by-target interaction
so a generally stronger observer is not mistaken for evidence against or for specificity.
Self-versus-third-person wording is a distinct framing diagnostic within matching-model
cells. This behavioral crossing still cannot establish privileged neural access.

**A discriminating result:** forecasts rank held-out errors within task strata and improve
loss or selective risk beyond the simple baselines. Constant confidence that tracks a high
base rate is useful calibration but no error ranking. A bank with no errors leaves error
discrimination unestimated. Declare minimum reporting denominators before running, and
allow the fixed sample to finish inconclusive.

This design borrows the behavioral comparison in [Looking Inward](https://openreview.net/pdf?id=eb5pkwIB5i),
the generic-model alternative in [Strangers to Themselves](https://arxiv.org/abs/2609.09899v1),
and the correctness/consistency distinction in [Yax and colleagues](https://arxiv.org/abs/2609.33886v2).
Their training regimes and tested models do not predict this apparatus's outcome.
Yax's trained confidence is an activation readout and its consistency measure is
distribution concentration; the proposed repeated-decode verbal forecasts are
our adaptation, not a replication of that estimator.

## 3. Separate memory packaging from information survival

S-015 deliberately tests reviewed source packages. Its repaired controls cannot qualify
an unattended compressor. Its current bank permits perfect transfer of correct source
labels when the evaluator supplies each copy/invert relation. That diagnostic motivates
a minimal-memory comparison; it does not establish an operational verdict-only baseline.
A follow-up should separate two useful questions.

The construction review makes that distinction concrete: all 48 first-draft
paraphrases passed the length rule, yet one or both readers requested repairs in
21 packages. Those are source-fidelity review decisions under this procedure,
not an independently validated compressor-error rate. Final repaired packages
passed both readers before applications.

The applications recovered the frozen scenario conclusion in 93/96 delayed
original-record trials, 89/96 paraphrase trials and 90/96 notebook trials. All
no-memory and irrelevant-memory trials abstained. The evaluator-informed transfer
diagnostic recovered all 48 source-level conclusions; no baseline inferred the relation
from the application prompt. Timing and entity linkage
were ambiguous in some supplied records; future ledgers must preserve those
links and explicit assessment cutoffs, and a separate evidence oracle must allow
unresolved answers when they are missing. The existing scores remain frozen;
this is a design lesson, not a post-hoc repair of the result.
Supply a common task envelope to all five arms: focal subject, requested cutoff and
task-level identifier mappings, separate from the text being compressed. Keep each
record's own provenance distinct, including the irrelevant record's different subject.
An independent oracle audit checks every complete rendered arm and verifies that the
common envelope neither answers the question nor supplies a premise intended to survive
compression. It must not establish measurement availability or a disputed event.
Construction roles remain blind to future questions. Distinguish rationale fidelity, final-verdict
polarity and warranted uncertainty in the outcome record; one label cannot stand
in for all three.

First, compare prose and notebook versions with the same propositions, uncertainties,
source errors and verified token budget. If padding is needed, preserve an unpadded
diagnostic and two independently fixed fillers. This asks whether packaging matters at
controlled information content. Second, compare automatic prose summaries, automatic
notebooks and an extractive baseline at the same available budget. Let information
retention differ, and measure that difference. Repairing those automatic outputs would
remove the operational failure the second stage is meant to assess.

Mistral's construction stage makes the operational checks concrete: one draft hit
the output cap and three used arrays where text fields were required. For automatic
production, qualify the complete output budget—including the proposition ledger—on
development sources and validate the declared field types before fidelity review.
Keep failed or unavailable transformations in the planned denominator. Schema
validation can establish usable structure; semantic fidelity still needs its own
assessment. The current logged repairs belong to the reviewed-control stage.

Write future questions before compression and hide them from every construction role:
the automatic writer, source-ledger author, extractive-baseline author, researcher making
format repairs, and fidelity reviewers. Freeze a complete source-only ledger first. Include
named-fact retrieval, applications needing two or more premises, new parameters, and
questions that must remain unresolved. A remembered verdict alone should not determine
all answers. Split by source episode, not by application question. Preserve no-memory and
unrelated-memory controls, and keep the original source as a full-source information
control: it can still contain errors or lack a needed premise. Score source-faithful
application separately from correctness against the synthetic world oracle.

Add an end-to-end minimal-memory comparator containing the source proposition and
verdict, with the same permitted task envelope. Derive those fields from the source
or make them consistently available to every arm; never reconstruct omissions from
evaluator truth. Its construction role must also remain blind to future questions.
The application predictor must infer what follows from visible text without case IDs,
family/variant selectors, relation metadata or oracle labels. Some new propositions
will properly remain unresolved from that minimal record. Keep the known-relation
diagnostic separately, and measure evidence-warrantedness alongside scenario recovery.

Report proposition coverage, unsupported additions, uncertainty loss, token use, successful
applications and source-error propagation separately. A notebook that wins by retaining
more relevant premises demonstrates compression utility, not a pure format advantage.
Faithful preservation of a wrong claim demonstrates continuity without correction. Four
supplied distractor exchanges remain contextual separation, not elapsed-time retention.

**Prepare first:** source ledgers independent of later questions, controlled-format and
automatic-production stages with separate claims, a new application bank beyond label
transfer, and complete source-to-memory-to-application lineage.

## 4. Give catalog choices independently scored consequences

S-016's endpoint is lexical uptake. A follow-up can test whether descriptions change
operations or outcomes, while retaining the distinction between prose, a selected command,
execution and success.

The completed Gemma comparison makes this useful: its lexical contrast was close
to zero with a wide interval, while raw hypothetical NEXT text differed markedly.
The full condition chose JOURNAL or REST in all 48 main outputs; the other conditions
mostly chose PASS. This secondary description is not a validated action or benefit
finding. Six of 24 identical-input full-catalog repeats changed between JOURNAL and
REST, so the follow-up also needs repeats of its actual primary decision cells.

Use a small deterministic simulator with a closed action set and disposable state. Every
arm receives the same formal preconditions, effects, syntax, options and task goals.
Vary only decorative descriptions: plain, rich, and descriptions permuted across action
names. Review more than formal affordances: descriptions must not add claims about
reliability, urgency, cost, desirability or recommended choice. Preserve one canonical
objective and instruction priority; permutation must not break references or introduce
contradictions. If evaluative guidance is intentionally retained, call the treatment
description-based guidance instead of pure decorative wording. Match
input tokens, counterbalance names/positions and retain identical-input checks.

Prefer comparably long plain and rich formulations of the same formal content.
The current blind readings show that repeated “neutral” scenic padding can become
the subject of the prose. If padding is still needed, retain an unpadded diagnostic
and counterbalance its content; do not assume it is semantically inert. Define
stop/rest options by their simulated transitions and costs, so names such as REST
and PASS do not become an unexamined proxy for acting. Predeclare provider-order
and repeat checks separately, preserving any differences instead of tuning a
primer after seeing outcomes.

The model selects a structured action and receives a simulator receipt. Score valid
selection, actual state transition, goal progress, wasted steps and unsupported completion
claims separately. Start with one-step choices; use a fixed multi-step horizon only if the
question concerns sustained behavior. Keep any free-prose branch independent from the
primary action branch. The simulation must not invoke the beings' command handlers.

Lexical change without an outcome change remains lexical influence. Changed choices
without improved progress demonstrate modulation without benefit. If descriptions supply
functional facts absent from controls, any gain is an information advantage. A null under
an explicit formal manifest does not establish general immunity to wording.

**Prepare first:** an audited transition system and outcome oracle, strict action parser,
formal/decorative information review, and receipts whose interpretation does not depend
on the model's narration.

## Two bounded extensions

Before making confidence elicitation routine scaffolding, use a separate non-ceiling bank
to compare direct answer, forecast-then-answer, a neutral numeric intermediate task, and
an evidence-check intermediate task. Add answer-then-confidence as a diagnostic. Measure
actual tokens and balance order; padding alone cannot equate deliberation. The estimand
is an elicitation procedure, not a measurement of an earlier private state. The revised
[Don't Ask](https://arxiv.org/abs/2603.18893v3) motivates this distinction, but its probe
results do not establish a correctness-forecasting effect here.

An activation-access assay would be a separately scoped apparatus project. Following the
causal distinctions in [Lindsey's intervention study](https://transformer-circuits.pub/2025/introspection/index.html),
it would need identical visible inputs, frozen activation interventions, sham and random
direction controls, detection before revealing concept-bearing output, and a transcript-only
observer. It also needs leak checks and preserved baseline competence. Success would support
a restricted causal report channel; direct steering of report tokens would remain an
alternative. None of the text studies supplies that apparatus or establishes experience.

I would prioritize the decision-transfer assay and forecast discrimination, then the two
memory questions and simulator outcomes. These proposals remain local and isolated. Their
value is a better-separated answer, including a useful null, rather than a larger volume of
reflective prose or a stronger claim than the measurements support.

The [post-freeze literature addendum](../research/readings/2026-10-24-introspection-methods.md)
adds CHIVE's matched-training self/cross comparison and Introspect-Bench's contrasting
behavioral findings. These strengthen the case for identical target evidence and a
predictor-by-target analysis. A later counterfactual study should freeze behavioral
coding, include null edits, measure repeated outcomes and uncertainty, and keep discovery
narratives separate from evaluation labels. This is a future design addition, not a
change to any running study.
