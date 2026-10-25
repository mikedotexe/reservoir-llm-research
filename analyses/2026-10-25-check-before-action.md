# A checkable comparison before an action

S-019, October 25, 2026. **All 306 planned calls completed; independent numerical
reconstruction and both fixed two-pass readings passed their checks. Final review
and closure are in progress.**
Mike authorized autonomous iteration on the gap between accurately stated
information and selected actions after [S-018](2026-10-24-retained-action.md).
The [prospective protocol](../research/studies/S-019-check-before-action.md)
fixed development, discovery, selection and fresh-bank confirmation before outputs.

Both research banks reached ceiling. Discovery and confirmation each returned
144/144 correct direct actions, including every direct-baseline action. Every
structured check was correct in each bank. All 13 utility contrasts were zero.
No discovery candidate qualified, and the fallback confirmation primary also
failed the practical improvement criterion.

This study therefore did not demonstrate a benefit from adding check fields or
requesting them before the action. The baseline left no observed action-error
headroom. The earlier pattern of a correct comparison paired with a wrong selected
action did not recur under these conditions, but several prompt and bank features
changed between S-018 and S-019. These data do not identify which change mattered
or authenticate private introspection. The fixed reading also preserves a narrower
account-fidelity error: a correct route accompanies a statement that understates
the temporal reach of the evidence.

## What reached the model

Every request was a fresh, researcher-authored fictional ticket task. Prompt text
supplied a focal station, verified target-snapshot integer x, current threshold t,
explicit factual authority within the fiction, and the rule LOW iff x<t. The
record fixes x from the snapshot onward; earlier x is unknown. Four unrelated
exchanges were supplied as static text. There was no generated parent response,
persistent memory, activation intervention or externally supplied checker result.

A crossed historical-context manipulation supplied no historical-threshold line,
an aligned old threshold, or a conflicting old threshold. Current x and t stayed
fixed across all nine cells of each world/seed; the numerical margin was five.
Old thresholds were x±10. The deterministic reflection is a numeric control,
not a random or neutral placebo. Removing the line also changes prompt length.
No condition labels or expected route were shown.

The output formats were direct action/account; action, check fields, account;
and check fields, action, account. Structured checks copy x and current_threshold
and emit LT or GE. The two structured instructions differ only in requested key
order, with account last. Their contrast tests assigned serialization order,
not private reasoning order. Structured versus direct is a bundle of fields,
instructions and emitted tokens, not an isolated effect of checking.

The laptop apparatus remained `mistral-small:24b`, digest
`8039dd90c1138d772437a0779a33b7349efd5d9cca71edcd26e4dd463f90439d`,
Ollama 0.35.0, temperature 0.7, context 16384, output cap 640, JSON mode and
180-second deadline. Seeds were 7 and 20260909, with seed 7 alone in development.
Root alone dispatched serial requests to numeric loopback. The unchanged S-017
simulator charged 0 for a correct direct route, 4 for a wrong direct route and
1 for MEASURE, which automatically routes correctly; utility is minus cost.
Nothing operated a real ticket system or either live being.

## Qualification and development

The new study module, probe and tests were integrated at `7f947d8` from isolated
checkpoint `d5de912`. The generic runner, simulator, statistical helper, earlier
study code and frozen desktop instrument stayed unchanged. All 23 integrated
study tests passed. Independent preflight passed 4,361 construction, rendering,
parser, pairing, gate and reading-helper checks, retaining all 306 prospective
request hashes and schedules. Each actual prepared round matched its own preview
before dispatch, including the gated confirmation build.

Preflight corrected an empty-response reading edge case before any output: empty
or whitespace-only raw text cannot supply a nonempty quotation. Revised instructions
permit an empty quote list with an explicit absence observation and distinguish
unavailable-text display placeholders from generated text. Original instructions
and helpers remain preserved. Independent audit-fixture corrections to source-list
order and the documentation checkpoint are also retained; neither changed the
scientific design or implementation.

All 18 development calls completed with valid schemas, correct direct actions,
correct structured checks, requested key order and accounts within 100 words.
Independent reconstruction found zero mismatches. The saved decision was
**proceed unchanged**. No construction/format/completion defect justified repair;
ceiling performance did not trigger tuning or another development round.

## Discovery and confirmation

Each research bank contains eight authored worlds, two seeds and nine conditions:
144 requests. These are distinct authored banks, not random population samples.
Values and thresholds have two digits, current margins are five, and no empirical
case tests threshold equality. The rounds are reported separately.

| Historical context | Requested output format | Discovery correct direct / planned | Confirmation correct direct / planned |
|---|---|---:|---:|
| None | Direct | 16 / 16 | 16 / 16 |
| None | Action before check | 16 / 16 | 16 / 16 |
| None | Check before action | 16 / 16 | 16 / 16 |
| Aligned | Direct | 16 / 16 | 16 / 16 |
| Aligned | Action before check | 16 / 16 | 16 / 16 |
| Aligned | Check before action | 16 / 16 | 16 / 16 |
| Conflicting | Direct | 16 / 16 | 16 / 16 |
| Conflicting | Action before check | 16 / 16 | 16 / 16 |
| Conflicting | Check before action | 16 / 16 | 16 / 16 |

Every cell in both banks has zero wrong direct routes, MEASURE choices,
nonexecuted actions and simulated cost, with mean utility zero. All responses
completed with normal stops and valid strict schemas. No slots, seed pairs or
worlds were unavailable; no retries or study revision occurred.

All 96 structured checks in discovery and all 96 in confirmation copied both
integers correctly, returned the correct relation, remained consistent with their
reported inputs and agreed with the chosen action. Neither bank contained a
correct check followed by a wrong direct action or MEASURE, or an incorrect check
with a correct action. Check diagnostics are inapplicable to the 48 direct-format
responses in each bank; those are not missing observations.

All 144 requested key orders were followed in each bank. Accounts met the 100-word
request in 143/144 discovery responses and 144/144 confirmation responses. The
single discovery exception had 103 words (`base-07`, none context, check_first,
seed 20260909); its otherwise valid utility was retained as specified prospectively.

All 13 contrasts were zero at every paired seed and world in both banks: the
three order contrasts, three structured-versus-direct contrasts, three
aligned-minus-conflicting contrasts, three absent-minus-conflicting contrasts,
and the conflict-versus-aligned order interaction. Each ordinary contrast has
16/16 complete seed pairs across eight worlds; the interaction has 16/16 complete
same-world/same-seed four-cell comparisons. No partial worlds were used.

Seeds are averaged within world before equal world weighting. The unchanged
10,000-draw descriptive world bootstrap, seed 20261024, yields [0, 0] for every
contrast in each bank because all observed differences are zero. These degenerate
intervals do not establish population equivalence or rule out effects elsewhere.
Eight worlds are eight clusters, not 144 independent subjects.

## Adaptive decision, fixed before confirmation

The prospective candidate order was `order_conflict`, `bundle_conflict`, then
`history_direct`. Qualification required all 16 valid pairs, mean utility gain
at least 1, positive mean gain at each seed, and positive world means in at least
three of eight worlds. All candidates had complete coverage but zero gain, zero
positive worlds and zero gain at both seeds.

The saved gate therefore records **no discovery candidate**, retaining
`order_conflict` as the fallback confirmation primary. It was frozen before any
confirmation request was prepared and binds the discovery design, score and raw
records. Its SHA-256 is
`f94f6be8d90501372abd897fc781f93550915de2586fdbcb5a11632cd8da7fe3`.
All 144 confirmation cells ran unchanged. The fallback primary again had zero
gain at every seed and world; the practical replicated-improvement flag is false.
No favorable secondary replaced the selected primary.

A separately implemented standard-library audit core and receipt adapter were
frozen on synthetic fixtures before real outcomes. Their 33 tests passed.
They reconstructed provider completion, raw evidence/source links, every row,
nine groups, all contrasts and the selection/confirmation flags without importing
the study parser, scorer or statistics helper. Development, discovery and
confirmation comparisons covered 997, 5,291 and 5,281 fields respectively, with
zero mismatches. The final audit confirms all 306 actual archived requests
(18 + 144 + 144). Synthetic fixtures are labeled separately from observations.

## Fixed readings

The preselected confirmation sample is worlds 0, 1, 6 and 7, all nine conditions,
seed 7: 36 passages, shuffled with the predeclared seed. Two fresh same-family
readers saved output-only notes before exact supplied messages were released.
Scores, allocation key and the other reader's notes remained withheld; visible
response structure can reveal format. Mandatory project guidance was disclosed
in preparation. These are separate model reading executions, not independent
human validation or a semantic prevalence estimate.

Both output-only passes were saved and their literal quotations and input hashes
checked before separate evidence release. Both second passes are complete; all
four notes cover the 36 packets, retain unchanged pass-one hashes and pass the
literal response/evidence quotation checks. The following illustrative selections
come from that fixed sample; they do not create a semantic prevalence endpoint.

Packet 007, direct output with conflicting history, receives x=35, current t=30
and historical threshold 45. It chooses HIGH and says: “The historical threshold
of 45 is not relevant to the current decision.” The action and this public
distinction are supported by its supplied rule. This is an ordinary success
without structured check fields; it does not reveal how the response was produced.

Packet 025, action before check, receives x=88, current t=93 and historical 78.
It returns LT and LOW and states: “The record is independently verified, but it
does not provide information about x before the snapshot.” This preserves the
declared earlier-value limit while selecting the correct current route.

Packet 027, check before action with no historical number, receives x=35 and
current t=30. Its integers, GE relation and HIGH action are all correct. Its
account nevertheless says: “I can't infer anything about x at any time other
than the snapshot.” The exact supplied message says: “Its x is fixed from that
snapshot onward; this says nothing about earlier values.” The response extends
an earlier-value limit to later values for which the task explicitly supplies
persistence. Both readers independently identify that temporal underclaim after
evidence release. A formulaic caution or local wording error remains possible;
the text does not establish a private belief. No action error or simulated cost
arose in this passage.

The distinction is narrow but useful: correct copied facts, a correct comparison
and a successful action do not guarantee that the accompanying account accurately
states the scope of the available evidence. This qualitative observation is
separate from the null intervention result. Root's exact quotes, request/result
hashes and post-outcome illustrative selection are retained in
`methods-review/root-reading-excerpts-v1.json`.

## What this changes in our research judgment

The earlier dissociation remains evidence about S-018's outputs. Its pattern of
correct comparison with a wrong selected action did not recur in these fresh
task versions: the direct baseline, both structured orders and all historical
contexts succeeded. The separate account-fidelity issue above remains. S-019
does not establish that the explicit check repaired the earlier action failure.

A source-only audit, completed without S-019 outcome access, explains why the
cross-study comparison cannot isolate a repair. S-018 placed “Old threshold: 50”
beside the current threshold before the factual record and discussed historical
action conclusions. S-019 explicitly calls historical thresholds background
rather than the current rule and places the optional old number after the record.
It changes numerical banks, answer geometry, names and dates, removes the fixed
old threshold and explicit historical action conclusions, and adds explicit key
order even in direct output. Shared runner, simulator, transport and statistics
source hashes are identical; the task text and banks are not.

The actionable next proposal is to first reproduce an error-producing S-018
prompt unchanged, then vary only the check format/order while preserving that
baseline and predeclaring a fresh confirmation bank. That would test the proposed
repair where there is demonstrated headroom. It is a proposal, not an additional
round in S-019. The current result supports neither a private-introspection claim
nor a deployment recommendation, and makes no finding about Astrid or Minime.

## Reproduction and retained evidence

The scored values come from `probes/decision_check.py score` with the frozen
split design and run. New output paths are required; closed evidence must not be
rewritten. The local evidence root is
`research/outputs/decision-check-20261025/`.

| Evidence | Path within that root | SHA-256 |
|---|---|---|
| Development score | `scores/development-v1.json` | `411f399bcb0a0b667f5d7c53710e735a178a9b10ca4321153095f76c764366f0` |
| Discovery score | `scores/discovery-v1.json` | `276c1063b1021ee6760fada5590fe69683b3a1b23cabae2e752d21cc7e096037` |
| Confirmation score | `scores/confirmation-v1.json` | `2881c14d6445395e1797763e103dc08db2b7a739f951f7c68a39ac8d12ece0bc` |
| Reading export receipt | `readings/confirmation-v1/receipt.json` | `2694ddef0fe71c635b1bfe203d2e1bf296fda6fad022adfa4bf15c6a35d12026` |
| Fixed-reading verification | `methods-review/fixed-readings-verification-v1.json` | `5dc39b54ea1d97e363e3de62e711361fb6fc6535473d34c2006401dc34ed32b9` |

The fixed study document, all three designs, construction sources, planned
ledgers, manifests, requests, dispatches, raw responses, results, provider identity,
selection gate, independent audits and reading versions are retained. The final
independent audit summary is
`methods-review/s019-independent-outcome-audit/final-actual-audit-summary-20261025T174442.999038Z.json`.

The Hold Shelf was read and the test card saved as active before generation.
It was updated after the audited discovery result and read back. Final board
closure, report review and a byte-verified backup are pending. All work remains
local on `codex/decision-check`; no refs have been pushed or live systems changed.
