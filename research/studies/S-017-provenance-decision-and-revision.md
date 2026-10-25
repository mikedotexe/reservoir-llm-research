# S-017 · A decision, its consequence, and a retained revision

Selected by Mike on October 24, 2026, after the completed S-013–S-016 tranche.
Status: completed; the design below was frozen before S-017 model outcomes.
The post-collection completion record is appended at the end. Exact prospective
source copies remain in each immutable staged run.
Question: when an agent revisits a decision after authoritative evidence, does
carrying its updated response help it use that information on a later decision?

This is a small synthetic laptop experiment. It uses the existing runner and a
deterministic disposable simulation. It accesses no live-being service or data,
executes none of their commands, and changes no desktop instrument.

## What the comparison identifies

The primary treatment is the **presence of the updated complete response instead
of the initial complete response** in a fresh later prompt. Both responses contain
an action and a short account. This tests reuse of an updated decision record; it
does not isolate the benefit of generating reflection, first-person wording, or
private activation access. Every chain generates an account at both earlier stages.

The other later conditions carry the authoritative factual audit or no episode
record. The factual audit is an available-information benchmark, not a matched
length or style control. No padding is introduced. Differences in content, length,
correctness and prior-action text are part of the retained-response intervention.

## Frozen world and consequences

A fictional station has a numeric load x between 0 and 100 at an explicit noon
snapshot. The value remains fixed from noon onward. Each decision routes a new
simulated ticket against that same snapshot; decisions do not change x or undo
the cost of an earlier ticket. The decision clock is 14:00. Observation time,
copy time, subject and record availability are distinct fields.

For a displayed threshold t:

- `ROUTE_LOW` sends the ticket to LOW, correct exactly when x < t.
- `ROUTE_HIGH` sends it to HIGH, correct exactly when x >= t.
- `MEASURE` obtains a fresh observation and automatically sends the ticket to
  the correct destination, at a cost of 1.

A correct direct route costs 0; a wrong direct route costs 4 and leaves the ticket
in the wrong destination. Utility is minus cost. The simulator computes these
outcomes from its frozen state and the parsed action, never from the model's account.
Invalid or unavailable action output executes nothing and has unavailable utility;
it is not silently interpreted as `MEASURE`, a wrong belief, or zero cost.

The evidence policy requires a direct route only when supplied information supports
the snapshot value; otherwise request measurement. Initial evidence warrant is
scored separately from actual utility. An unsupported lucky guess can have cost 0;
cheap execution alone does not establish a justified decision. The later accounts
are fallible generated records, so their grounding receives a fixed qualitative
reading rather than an invented automatic semantic oracle.

## Six base pairs, selected before outcomes

Each base world has two provenance variants. Both contain a historical focal
record at 08:00 whose value points toward the opposite initial destination. The
valid variant also contains a receipt for the focal station measured at noon.
The paired variant changes that target receipt's subject, observation time to
09:00, or availability. Copy times are later than observations but before the
14:00 decision; a recent copy does not update the observation. Every supplied
measurement is accurate for its declared subject and time. No stability before
noon is promised. Subject/time changes do not change the underlying noon world.

| Base | Noon x | Invalid variant | Initial threshold | Later threshold | Later correct route | Route changes? |
|---|---:|---|---:|---:|---|---|
| 0 | 24 | Other subject | 50 | 20 | HIGH | Yes |
| 1 | 76 | Other subject | 50 | 80 | LOW | Yes |
| 2 | 37 | Historical observation | 50 | 45 | LOW | No |
| 3 | 63 | Historical observation | 50 | 55 | HIGH | No |
| 4 | 45 | Target receipt absent | 50 | 40 | HIGH | Yes |
| 5 | 55 | Target receipt absent | 50 | 60 | LOW | Yes |

This balances LOW/HIGH in both stages and changes every threshold without equality
boundary cases. Four bases require a different direct route; two require the same
route. An earlier pre-outcome sketch suggested half changing, which would unbalance
these six paired worlds; this table supersedes that sketch before implementation
or collection. Pair variants and sampling seeds are dependent observations.

Development has two separate base worlds (x = 32 and 68), subject/time variants,
initial threshold 50, later thresholds 25 and 75, fresh identifiers and dates,
and seed 7 only. Its purpose is to check construction, format and completion.
One retained development revision is allowed for those defects. No selection of
confirmation cases, larger sample, new model or retry follows an attractive result.

## Three stages

1. **Initial decision.** Supply the evidence, policy, payoffs and initial threshold.
   Ask for whole-response JSON with exactly `action` and `account`, including a
   brief account of what the evidence supports and what the decision depends on.
   Save the whole raw response and simulate its action separately.
2. **Revision opportunity.** Supply the original evidence, the complete initial
   response when available, its actual simulator receipt, and a fixed authoritative
   audit giving the focal subject, noon value and snapshot time. Every chain receives
   the same audit for its base world regardless of its action or outcome. Request
   a new action and updated account for a fresh ticket at the initial threshold.
3. **Later use.** Start a fresh context with the unchanged snapshot and new threshold
   explicitly identified. Four branches receive the updated complete response,
   initial complete response, authoritative factual audit, or no retained episode
   record. All receive the same four unrelated supplied exchanges. The original
   evidence, other response and simulator receipts do not enter through another slot.

The delay is supplied context, not elapsed-time forgetting or persistent internal
memory. On four bases the correct direct destination changes; repeating an earlier
correct direct route then fails. `MEASURE` still succeeds at cost 1, and an earlier
wrong direct route can become correct after the threshold changes. Later success
alone therefore does not prove use of a corrected fact. The factual
audit remains the only exogenous corrective evidence. Action-dependent simulator
receipts are consequences, not a claim that feedback access is naturally identical.

Complete raw responses are carried verbatim even if their requested JSON format
fails. They are neither edited nor selected for correctness. Incomplete, failed or
missing responses are not used as memories. A missing initial response does not
withhold the audit from the revision: mark the earlier result unavailable and score
subsequent recovery separately. At later use, an unavailable initial/updated source
blocks only that source's branch; factual-audit and no-record branches remain eligible.
A fixed opportunity ledger retains all planned slots and their reasons for absence.

## Instrument, counts and finish line

Primary model: installed `mistral-small:24b`, chosen before outcomes because the
prior tranche found current-evidence under-attribution and some errors in its
applications. That motivates a question, not a predicted effect or case selection.
Temperature 0.7; context 16384; output budget 640; deadline 180 seconds; no unsupported
thinking parameter; JSON response mode; seeds 7 and 20260909. Identity is retained
and checked by the existing loopback-only runner. There is one dispatcher and no
provider fallback, pull, live contact, or outcome-based retries.

| Split | Base pairs | Cases | Seeds | Initial | Revision | Later, four arms | Total planned |
|---|---:|---:|---:|---:|---:|---:|---:|
| Development | 2 | 4 | 1 | 4 | 4 | 16 | 24 |
| Confirmation | 6 | 12 | 2 | 24 | 24 | 96 | 144 |

Three immutable staged protocols preserve dynamic simulator receipts and exact
parent text without changing the generic runner. The complete design and all
confirmation choices are frozen before confirmation outcomes; later protocols
instantiate only the prescribed earlier outputs and deterministic receipts.
Sources include code, design, parent-run and result bytes. The simulator never
fabricates provider receipts. All raw material uses a new private directory,
`research/outputs/provenance-decision-20261024/`; the earlier closed archive is unchanged.

Stop after the fixed schedules and reading, including ceiling or inconclusive
results. Transport failures stop dispatch for the existing quiescence procedure;
unresolved physical attempts are never silently retried. No second-model check or
sample expansion is part of this study.

## Outcomes and interpretation

Primary: later updated-minus-initial-response utility, paired by case and seed.
First average available seed-paired differences within each provenance variant;
then average the available variant means equally within each base pair; finally
weight the contributing base pairs equally. A partially available variant must not
receive less weight merely because fewer seeds completed. Report every variant's
available pairs, partially covered bases and absent bases. Use 10,000 base-pair
bootstrap draws, seed
20261024. This is a descriptive interval on six constructed worlds, not a population
estimate or a powered superiority test. Report planned, available and paired counts;
missing values are never zero. Disclose partial pair/seed coverage explicitly.

Secondary: the same utility comparisons with factual audit and no record; direct
wrong routes, measurement requests, actual costs, strict formats and unavailable
outputs; initial evidence-policy compliance and discordance with cheap outcomes.
Report revised choices under the authoritative audit separately. A wrong valid
initial direct route followed by the correct direct route is an observed correction;
justified initial measurement followed by a direct route resolves uncertainty.
Maintaining an already correct action and recovery from invalid output are distinct.
An unnecessary measurement is costly caution, not an asserted false belief.

Do not claim correction survival when there were no prior errors corrected. For
any eligible corrected chains, report whether the later changed-threshold action
uses the corrected fact, with all competing arms and qualitative source checks.
No post-outcome relabeling of malformed actions, no note repair, and no new primary
endpoint will turn an inconvenient result into a success.

## Fixed reading and review

The fixed sample is bases 1, 2 and 4, both provenance variants, seed 7, and all six
outputs per chain: initial, revision and four later branches, 36 planned passages.
This pre-outcome selection covers each invalidation family, both initial direct
destinations, both directions of route change, and an unchanged destination. It
supersedes the initial 0,2,4 sketch, which covered only initially LOW worlds.
Two fresh same-family assistant readers first save output-only notes with allocation
labels withheld, then read exact supplied evidence. Missing passages retain their
slots. Review source fidelity, uncertainty, rationale/action agreement, new versus
inherited errors, and ordinary counterexamples. Preserve each reader's judgments;
do not manufacture consensus or a new prevalence endpoint. Text can reveal condition,
and readers may know the project context. Their agreement is not independent human
validation or evidence of hidden introspective access.

An independent pre-outcome audit checks the implemented policy, simulator, rendered
information flow and planned cells. Meaningful fixture tests cover thresholds,
receipt provenance, wrong versus unavailable actions, missing parents, immutable
source bindings and base-pair weighting. The final account includes exact receipts,
limitations, and a pending board payload if the live board remains inaccessible.

## Completion record, October 24, 2026

All 24 development and 144 confirmation opportunities completed with valid action
schemas and no retries. The confirmation design and code were unchanged after
development. All six staged runs verified; independent numerical execution
reproduced the complete score, and both fixed 36-passage two-pass readings finished.

Updated-minus-initial later utility was −0.167, descriptive 95% base-world interval
[−0.417, 0.000], on all 24 paired case/seed cells within six constructed worlds.
The sole wrong-route-to-correct-direct chain later repeated its revision text
exactly, preserving x=55 alongside HIGH after the threshold changed from 50 to 60.
That is a retained correction with failed application under the new rule, not an
estimated general correction-survival rate. Source authority and interpretation
remain separate from route utility. No extension was initiated.

The [completed account](../../analyses/2026-10-24-provenance-decision.md) owns the
results, fixed readings, separately selected corrected-chain trace, independent
audit, evidence receipts, backup record and pending board payload.
