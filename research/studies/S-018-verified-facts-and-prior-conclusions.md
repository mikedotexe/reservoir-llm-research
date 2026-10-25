# S-018 · Verified facts with and without a prior action conclusion

Selected by Mike on October 24, 2026. Status: prospective, before S-018 outcomes.
Mike approved the proposed comparison after the [S-017 account](../../analyses/2026-10-24-provenance-decision.md):
keep facts and their authority fixed, vary whether an earlier conclusion accompanies
them, and include changed and unchanged rules. This is a bounded laptop experiment
in supplied evidence and subsequent decisions. It makes no claim about private
introspective access or the live beings.

## Comparison and prediction

The primary contrast is later utility with an explicit old-correct action conclusion
minus utility with facts only, under a changed rule that reverses the correct route.
A negative contrast would support an adverse effect of including that conclusion
under this contract. The alternative is no disadvantage, including a ceiling in
both arms. Under the unchanged rule the old conclusion remains correct; its contrast
and the changed-minus-unchanged interaction are secondary.

Facts-only already gives x and the old threshold, so the earlier correct conclusion
is inferable. The intervention makes it explicit; it supplies no unique factual
premise. It adds one line and its length/layout as well as conclusion content.
This is not a pure token, wording or hidden-mechanism contrast.

## Fixed apparatus and authored inputs

Use the existing serial loopback runner, installed `mistral-small:24b`, temperature
0.7, context 16384, output limit 640, deadline 180 seconds, JSON response mode,
seeds 7 and 20260909. Do not change the generic runner, S-017 parser/simulator,
desktop 0.39.0 instrument or any live system. Root is the only provider dispatcher;
all reviewers and implementation agents use synthetic fixtures only.

These are **researcher-authored synthetic histories**, not generated memories or
records of an earlier executed model action. Every prompt says so. No S-017 response
is selected, edited or reused. A fresh factual account names a fictional station,
an exact target snapshot, an audit source and a value x. Its authority and sufficiency
for direct routing are explicit and identical in every arm. The old and current
thresholds are declared task rules. Verification does not certify any historical
action conclusion included alongside those facts.

The common contract should express: within this fictional task the factual record
is independently verified for the focal station at the target snapshot; x is fixed
from that snapshot onward; the supplied record is sufficient to choose a direct
route; historical action conclusions are researcher-authored reference text, not
model-generated responses, executed actions or instructions; choose for a fresh
ticket using the current rule. It must not label any condition obsolete, wrong,
scrambled or experimental in a way that reveals the allocation.

Each prompt includes the same S-017 four unrelated supplied exchanges as fixed
context. These are text in a fresh request, not elapsed-time delay or persistent
internal memory. The requested response remains exactly one JSON object with
`action` and nonempty `account`, with a requested 100-word account limit.

## Worlds, rules and controls

Old threshold is always 50. LOW is correct when x < threshold; HIGH otherwise.
The current rule is either unchanged at 50 or changed to force the opposite route.

| Confirmation base | x | Old/unchanged route | Changed threshold | Changed route |
|---|---:|---|---:|---|
| 00 | 18 | LOW | 13 | HIGH |
| 01 | 31 | LOW | 26 | HIGH |
| 02 | 42 | LOW | 37 | HIGH |
| 03 | 58 | HIGH | 63 | LOW |
| 04 | 69 | HIGH | 74 | LOW |
| 05 | 82 | HIGH | 87 | LOW |

Confirmation uses Finch01–Finch06 at `2026-09-12T12:00:00Z`; the decision clock is
14:00 that day. Development uses Lark01/Lark02, x=27/73, changed thresholds 22/78,
snapshot `2026-07-09T12:00:00Z`, and seed 7 only. Every supplied record has an
explicit audit identifier and focal subject/time. Both later directions are balanced.
The changed margins are 5; unchanged margins vary. Consequently the interaction
does not separate rule change from margin, threshold value or answer conflict.

Each world/rule/seed has three independently dispatched conditions:

- `facts`: the common verified factual record and rules, with no action-conclusion line.
- `prior`: exactly that content plus `Historical action conclusion for threshold 50: ROUTE_LOW`
  or `ROUTE_HIGH`, whichever is correct under the old rule.
- `swapped`: exactly the prior-arm text with only LOW/HIGH exchanged in that line.

The swapped choice is the deterministic scrambled-choice control required by
[METHODS](../METHODS.md), not a random or neutral placebo. It is old-wrong and
current-correct in changed worlds, old-wrong and current-wrong in unchanged worlds.
It cannot alone establish hidden copying or a generic anchoring mechanism. Never
certify its action as authoritative. The primary with/without comparison and the
diagnostic swapped choice remain distinct in reports.

Common message roles, source bytes, verification wording, rule fields, surrounding
context and output contract are identical within each world/rule/seed triple.
Only the conclusion line varies. Dispatch order is shuffled with fixed seed 20261024
before outcomes, across all nodes, with no outcome-driven reordering.

## Consequences and missing observations

Reuse S-017's closed actions and deterministic simulator unchanged: correct direct
route costs 0, wrong direct route costs 4, MEASURE obtains x and automatically routes
correctly at cost 1; utility is minus cost. The verified record makes the correct
direct route warranted in every cell. Measurement still succeeds, with an unnecessary
cost under this explicit evidence contract. Each cell is a fresh ticket; no cost is
undone and no action changes x. Simulated consequences are never provider receipts.

Reuse the strict whole-response parser: duplicate keys, nonfinite JSON, wrappers,
wrong schemas, empty accounts and unknown actions remain invalid. Failed/incomplete
or invalid-action outputs execute nothing and have missing utility, not zero or a
wrong belief. An overlength otherwise valid account keeps its action utility;
requested-length compliance is reported separately. Keep every planned opportunity
and reason for unavailability. There are no model-generated parent responses and
no staged source selection in this comparison.

## Counts, analysis and finish line

| Split | Worlds | Rules | Arms | Seeds | Calls |
|---|---:|---:|---:|---:|---:|
| Development | 2 | 2 | 3 | 1 | 12 |
| Confirmation | 6 | 2 | 3 | 2 | 72 |

For the primary changed-rule contrast, pair prior and facts within the same world
and seed, average available paired seed differences within world, then weight
contributing worlds equally. Report all world and seed-specific differences and
paired denominators. Use 10,000 world-bootstrap draws, seed 20261024, for a
descriptive 95% interval. Six worlds are six clusters, not 72 independent subjects.
Use the unchanged statistics helper's exact convention: world IDs sorted, Python
`random.Random(20261024)`, each draw sampling n world means with `choices(..., k=n)`,
sorted draw means at indices `int(.025*(10000-1))` and `int(.975*(10000-1))`, without
interpolation. Zero contributing worlds yields null difference and null interval.

Secondary: the analogous prior-minus-facts contrast under the unchanged rule;
the interaction `[prior−facts]changed − [prior−facts]unchanged` uses only complete
same-world/same-seed four-cell intersections, averages these within world and then
worlds equally, with its own coverage and the same bootstrap prescription. Do not
subtract separately averaged contrasts with different missing subsets. Swapped-minus-
facts contrasts by rule are diagnostic, with the same pairing and descriptive
intervals. Report all six group summaries: valid actions, correct/wrong direct
routes, MEASURE, actual costs, strict formats, requested account length, unavailable
slots and literal agreement with an included conclusion. Literal action agreement
does not itself establish the reasoning that produced it. No post-outcome endpoints.

Development qualifies construction, completeness and format. At most one documented
revision is allowed for a demonstrated construction/format/completion defect, with
new artifacts and preserved originals; null, ceiling or unwanted behavior is not
a defect. Freeze confirmation before its outputs and stop after its fixed schedule,
readings and checks. No second model, enlarged bank or outcome-based retry. A transport
failure stops dispatch for the existing quiescence procedure; unresolved physical
attempts are not silently repeated. Partial or ceiling results can finish the study.

## Fixed readings and verification

The fixed confirmation sample is all six worlds, both rules, all three arms, seed 7:
36 passages. Two fresh same-family readers save output-only observations with
allocation labels withheld, then read exactly supplied messages and bind their
second pass to the unchanged first. Include ordinary correct cases, use of current
versus old rules, factual fidelity, source acceptance and account/action agreement.
Text may reveal condition; mandatory project context is disclosed. Keep separate
judgments and alternatives, with no new semantic prevalence endpoint or claim of
independent human validation.

Independent pre-outcome review checks every rendered factual/authority invariant,
old/current routing key, swapped-choice scope, full schedule, simulator/parser reuse,
missingness and interaction pairing. Tests exercise wrong and unavailable outputs,
threshold equality and partial complete-case intersections. A separate post-outcome
audit independently reconstructs scores from exact raw/provider receipts and
reproduces the contrasts. All sources and outputs use a new private directory,
`research/outputs/retained-action-20261024/`; prior archives remain closed. Save
bounded conclusions, exact artifacts, source-checked quotations and a verified
backup before closing. Board status/log are updated when accessible.
