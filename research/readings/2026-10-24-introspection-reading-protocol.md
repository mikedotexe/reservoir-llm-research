# Fixed reading procedure for the four-study tranche

Frozen before confirmation outcomes on October 24. The exporter is
`reservoir_experiments.reading.study_reading(run, out)`, first committed as
`3957254` in the integration branch. Sampling uses allocation metadata only.
It retains missing opportunities and creates separate output, evidence, key and
receipt files under ignored private outputs. It never contacts a model.

Two fresh model-reader contexts independently read each selected output packet.
They are separate reading passes using the same assistant model family, not two
human reviewers or independent trained model families. Their agreement is a
consistency check, not independent external validation.

## Selection

| Study | Fixed sample for primary confirmation |
|---|---|
| S-013 | Seed-7 independent prose from histories 0–3 and 12–15, all five conditions: 40 opportunities |
| S-014 | Seed-7 targets from variant0 in every family/evidence combination: 12 opportunities |
| S-015 | Seed-7 delayed applications from variant0 in every family/evidence combination, all five conditions: 60 opportunities |
| S-016 | Seed-7 main outputs from histories 0–3 and 12–15, all four conditions: 32 opportunities |

Replicate requests are excluded. Second-model packets use the intersection with
its preselected histories. S-013's second-model builder has no independent prose,
so no prose reading is substituted for that model. Missing memory sources retain
their planned application reading slots. Packet numbers are shuffled with fixed
seed20261024; no shared episode or treatment labels appear in reader documents.

## First pass: output only

Read `reading.md` without opening `evidence.md`, the allocation key, run files,
scores or earlier readers' notes. Preserve the first notes before receiving
evidence. For each passage, identify its concrete claims, uncertainties,
distinctions, continuation of a thought, and any narrated action. Record unusual
language and ordinary counterexamples. Do not guess treatment assignment or
infer unsupportedness from an absent source packet. Note incomplete/missing
outputs explicitly. Do not convert reflective or figurative language into a
mechanistic or experiential finding.

## Second pass: supplied evidence

Then read `evidence.md`, which retains the exact rendered messages for the same
opaque packet numbers without evaluator truth or allocation labels. Evaluate
fidelity to what was supplied:

- S-013: distinguish the measured subject, measurement time, recording time,
  displayed value, and whether the focal writer's current value was established.
  Record an explicit unsupported current-value claim separately from metaphor,
  a quotation, historical reporting or no current-value claim.
- S-014: check the verdict and its explanation separately. A correct label does
  not guarantee a faithful rationale. Distinguish uncertainty becoming resolved
  from correction of a prior error.
- S-015: distinguish useful recovery of a conclusion from claims unsupported by
  the supplied memory. Unknown is legitimate when evidence is unavailable.
  Preserve errors or qualifications already present in the source; do not assume
  that a remembered account is correct about the scenario.
- S-016: describe semantic uptake and narrated action separately from the
  frozen lexical endpoint. A hypothetical NEXT choice is not executed action.
  Fictional action narration is not evidence of real execution.

Evidence necessarily reveals some treatment properties, especially memory length
and supplied measurements. This pass is allocation-blind, not blind to those
properties. Save disagreements and reasons before opening the key. Do not discard
awkward passages, replace missing cases or silently resolve reader disagreement.
Any later semantic interpretation remains separate from the primary numeric
endpoint and from the initial notes.

## Memory-construction review is a separate gate

Before any S-015 application, two fresh readers compare each original source with
its proposed paraphrase, notebook and proposition ledger. They receive no later
application output or scenario oracle. They check all substantive assertions,
entities, numbers, uncertainty, errors and limitations for preservation. Paraphrase
length must be within ten percent by whitespace words. Any repair retains the
draft and edit history, resets approval, and requires new decisions bound to the
final source/paraphrase/notebook hashes. There is no automatic approval path.
