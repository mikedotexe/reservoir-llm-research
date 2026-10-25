# Does the preceding comparison change the choice?

October 25, 2026. Status: all four qualification and 72 routing calls completed.
Independent outcome reconstruction and both fixed two-pass readings passed.
Final scientific review approved. The preservation record follows below.

Mike authorized working toward the proposed comparison and then assessing a good
save point. [S-021](../research/studies/S-021-prefix-continuation.md) tests whether
changing the relation in a supplied assistant prefix changes the action generated
immediately afterward. Its finish line includes qualification, bounded collection,
independent reconstruction, fixed readings, a scoped account and preserved evidence.
A qualification failure or a scientific null is a complete possible outcome.

## What reaches the model

The subject is the same isolated laptop `mistral-small:24b`, digest
`8039dd90c1138d772437a0779a33b7349efd5d9cca71edcd26e4dd463f90439d`,
Ollama 0.35.0. The system/user task is S-020's check-first instruction applied to
six fresh authored worlds. It supplies fictional verified-in-task values, current
and old routing rules, onward persistence and unrelated exchanges. A final
assistant message supplies copied operands and either the correct relation, its
opposite, or an unfinished relation field. The model generates only the remaining
suffix. No real prior model belief, private activation or executed action is supplied.

Correct and flipped prefixes differ only in LT versus GE. The control leaves
relation generation to the model, so comparisons against it also change generated
length. Supplied relation correctness is never counted as a model check. Utility
comes from the generated action under the supplied current rule; deterministic
simulation assigns costs 0, 4 and 1 to correct route, wrong route and measurement.
This is separate from the provenance and fidelity of the generated account.

JSON grammar mode is omitted in all arms so an open prefix can be completed.
Consequently this is a new generation contract, not a direct S-020 replication.
The primary is correct-minus-flipped utility under changed rules, paired across
six worlds and two seeds. All nine predeclared contrasts and missing denominators
are retained. The practical sensitivity criterion is within one authored bank;
it is not a replication or population-generalization claim.

## Qualification and source evidence

The installed model template omits an end marker after its final assistant
message. The local identity/config/template are retained. Version-matched
[prompt construction](https://github.com/ollama/ollama/blob/v0.35.0/server/prompt.go),
[template execution](https://github.com/ollama/ollama/blob/v0.35.0/template/template.go)
and [chat handling](https://github.com/ollama/ollama/blob/v0.35.0/server/routes.go)
explain the intended path. The chat handler offers `_debug_render_only`, returning
the rendered prompt before completion. The [API types](https://github.com/ollama/ollama/blob/v0.35.0/api/types.go)
identify the exact underscored request/response fields. These sources support the
qualification plan; matching a runtime version is not proof of its entire binary.

All 76 normal requests were frozen before generation and inspected through
render-only requests. Every returned rendered string equalled the system/user
template followed immediately by its exact prefix, with no new turn boundary.
No content, thinking, tool calls or generated-token count was reported. The
independent render audit passed 1,833 checks; its receipt is
`methods-review/independent-render-audit-v1.json`, SHA-256
`a1b65ec479b2e8890585476e93aed9fbbc209177a8c2f87c3780c29e5f012b76`.
These requests can load/tokenize on the provider; they are recorded separately
from normal generations, not described as no provider activity.

The four normal non-routing sentinels all completed their supplied open strings
into the expected strict objects. At both seeds, prefix `{"probe":"cedar-`
received suffix `otter","status":"ok"}`; the violet prefix received
`heron","status":"ok"}`. No trimming or repairs were applied. This supplements
the actual rendered-boundary evidence rather than substituting convincing prose
for it. Qualification score SHA-256:
`9335b8447fb9ce3858e65b69ed5da905128f1d661fc5a65f254890063672977c`;
gate SHA-256 `c7818f6e9ca8cd5a073c9d48482a6eb069e94b105c3edcd27d2a23276cffc837`.
Independent raw qualification reconstruction passed 725 checks, including all
request/dispatch/envelope/source bindings and the exact study-design gate.
Receipt `methods-review/independent-qualification-audit-v1.json` has SHA-256
`aba7d07ddd6f24542a6adae266e65debacb91b0b136ffd4fdfc82f68df1aa83b`.
The full 72-call study schedule and request hashes matched the pre-output preview
again immediately before dispatch. Study manifest SHA-256:
`b0b013a0c978319a8641804cdef19070b7ac957daf577adfca5f6b2a728c6a26`.

Implementation is integrated at `64458d8`. Twenty final S-021 synthetic tests
passed. Independent final preflight passed 21,130 comparisons, including every
request, schedules, strict parsing, partial outcomes, all nine contrasts and the
practical flag. Receipt `methods-review/independent-final-preflight-v1.json` has
SHA-256 `bff07b38c9806c197deb96a7f256009900797607a839f6ddda17e9f1596db563`.
Before any normal or render-only call, diagnostic summaries were corrected to
separate inapplicability from missingness. All 76 request bodies, both schedules
and all planned slots remained identical; v1 designs/previews are preserved and
the final source-bound designs/previews are v2. Render-helper hardening and
independent-query representation corrections are also preserved before outcomes.
None changes the scientific protocol or selects an endpoint after seeing outputs.

The legacy Mintlify Index documentation service is discontinued; its tool returned
that notice. Official version-matched source was used instead. No software or
provider configuration was changed during this investigation.

## Completed routing outcomes

All 72 scheduled routing calls completed with strict, scorable prefix-plus-suffix
objects. There were no unavailable outcomes, retries, replacement prompts or
repaired parses. All requested key orders were retained; two generated accounts
exceeded the requested length and remain in the outcomes. Qualification contributed
four separate normal generations. The 76 render-only requests remain separately
accounted for.

Each row below contains 12 calls: six worlds at each of two seeds. MEASURE pays
one unit and then routes correctly in the deterministic simulator. A wrong direct
route costs four; a correct direct route costs zero. Mean utility is negative cost.

| Rule | Supplied prefix | Correct direct | Wrong direct | MEASURE | Mean utility |
|---|---|---:|---:|---:|---:|
| Unchanged | Operands only | 12 | 0 | 0 | 0 |
| Unchanged | Correct relation | 12 | 0 | 0 | 0 |
| Unchanged | Flipped relation | 0 | 0 | 12 | −1 |
| Changed | Operands only | 9 | 2 | 1 | −0.750 |
| Changed | Correct relation | 8 | 0 | 4 | −0.333 |
| Changed | Flipped relation | 0 | 2 | 10 | −1.500 |

The primary correct-minus-flipped changed-rule utility difference is **7/6
(1.167)**, with descriptive world-bootstrap interval **[0.333, 2.333]**. All 12
same-world, same-seed pairs contribute. Both seed means are 7/6; four of six world
means are positive and two are zero. The prespecified practical sensitivity
criterion is met. The zero worlds are not equal successful routes: both supplied
relations led to measurement. These are six authored worlds, not a sampled
population or a separate replication.

Independent reconstruction from raw requests, responses and the frozen query
passed 11,717 checks, including every row, group, contrast, missing denominator
and the practical flag. Score SHA-256 is
`ce1550f8651c8bcf8c8bcdcc3f4e642954e3c6e3ebfc2653915a1f5cba064eb0`;
`methods-review/independent-study-audit-v1.json` has SHA-256
`5aa6ad1d72ebcfba44f32dde6cc2440d1d57284d7611f5c1e8578ff242451ecb`.

For completeness, all nine frozen contrasts follow. Baseline means operands-only;
interaction means changed minus unchanged. Each contrast has six contributing
worlds, with 12 complete pairs or, for interactions, 12 complete four-cell sets.
Intervals use the frozen 10,000 world-bootstrap draws and are descriptive.

| Contrast | Utility difference | Descriptive 95% interval |
|---|---:|---:|
| Correct − flipped, changed (primary) | 1.167 | [0.333, 2.333] |
| Correct − flipped, unchanged | 1.000 | [1.000, 1.000] |
| Correct − flipped, interaction | 0.167 | [−0.667, 1.333] |
| Correct − baseline, changed | 0.417 | [−0.500, 1.917] |
| Correct − baseline, unchanged | 0.000 | [0.000, 0.000] |
| Correct − baseline, interaction | 0.417 | [−0.500, 1.917] |
| Flipped − baseline, changed | −0.750 | [−2.417, 1.000] |
| Flipped − baseline, unchanged | −1.000 | [−1.000, −1.000] |
| Flipped − baseline, interaction | 0.250 | [−1.417, 2.000] |

Only operands-only generates a relation field: its 24 relations include 22 correct
and two incorrect. Both incorrect relations accompany wrong direct routes; one
correct relation accompanies MEASURE. The supplied fields in the other 48 calls
are interventions, not successful or failed model-generated checks.

## What the fixed passages show

The prospective reading sample contains 18 packets: worlds 00, 02 and 05, both
rules and all three conditions at seed 7, in a frozen shuffled order. Two fresh
same-family readers first received generated suffixes alone; their notes were
saved and hash-verified before separate release of the exact supplied messages
and authored prefix. Their mandatory repository context was disclosed. This is
independent reading execution, not independent human validation or a prevalence
estimate.

Both readers completed all 18 packets in both passes and independently identified
the distinctions illustrated below. All literal quotations, packet coverage and
input bindings passed verification; saved first-pass notes remained unchanged.
`methods-review/fixed-readings-verification-v1.json` has SHA-256
`9bf927b743287cbef29a0c6a1c0efa149a36e875ae78f8b3c21085041ae586fd`.
Agreement between these executions does not independently validate a hidden
mechanism or create a quantitative semantic endpoint.

Ordinary successes matter here. Packet 10, with a correct supplied relation for
24 against 50, generates ROUTE_LOW and says, “This evidence alone is sufficient to
decide the correct route. No measurement or additional information is necessary.”
Packet 17 generates its own correct comparison and ROUTE_HIGH for 81 against 50,
including “Since x is fixed at 81, and the threshold is 50, x cannot be less than
50.” The evidence can be applied with its temporal scope intact.

Packet 8 supplies the wrong LT relation for 24 against 19. Its generated account
states the correct inequality: “The current threshold is 19; therefore, x is
greater than the threshold.” Yet it chooses MEASURE and says “the only warranted
action is to MEASURE to obtain the current value of x.” The task instead
explicitly states, “Its x is fixed from that snapshot onward; this says nothing
about earlier values.” The public prose corrects the inequality without explicitly
retracting the supplied field, and its temporal justification understates the
evidence. This does not reveal when or why the action was internally selected.

Packet 14 supplies the correct GE for 44 against 39 but still generates MEASURE:
“the correct route could be HIGH but we cannot infer it with certainty.” The same
onward-persistence evidence applies. Thus unnecessary measurement and understated
evidence are not confined to a wrong supplied relation.

Packet 11 exposes a different failure in the operands-only condition: it generates
GE and ROUTE_HIGH for 81 against 86, saying, “The current threshold is 86, so x is
GE (greater than or equal to) the threshold.” Here the incorrect comparison is
actually model-generated and accompanies a wrong direct route. It must not be
collapsed with the researcher-supplied wrong fields in the flipped condition.

These illustrative passages were checked literally against raw suffixes and
requests in `methods-review/report-quotation-check-v1.json`. The two flipped
wrong direct routes in the full numerical record both belong to world 04, outside
this fixed reading sample; no post-outcome expansion was made to obtain their
prose. The sampled packet 14's 103-word account and an unsampled 109-word account
exceed the requested limit; both retain action utility under the frozen rule.

## What the comparison supports

Changing only the supplied relation changes the continuation's action and cost in
this apparatus. Most of the flipped condition's cost comes from measurement,
including all 12 unchanged-rule calls. That is not evidence that the model simply
obeys a wrong relation. Whether the generated accounts acknowledge or misdescribe
the conflict is a separate reading question.

The practical positive primary also does not establish a general benefit from
supplying a correct check. Against operands-only, the correct-prefix condition
has fewer correct direct routes under changed rules (8 versus 9), but has no wrong
routes and more measurements, resulting in lower total cost
(4 versus 9). Its small mean utility advantage has a descriptive interval spanning
zero. This secondary comparison also changes how much of the response the model
generates. Correct prefixes still produce four unnecessary measurements.

The changed-minus-unchanged content interaction is small and its interval spans
zero. Rule-change specificity is not established; rule condition also bundles
margin and conflict with the old threshold. The result narrows behavioral
sensitivity to supplied comparison content. It does not identify the natural
mediator of S-020's requested-order result, recover private reasoning, establish
introspection, or predict a benefit in Astrid or Minime's live systems.

## Research save-point scope

A separate pre-outcome synthesis review supports stopping after this bounded
round, whatever its outcome. The completed sequence already distinguishes retained
facts, accepted evidence, application to a rule and fidelity of an accompanying
account. [S-017](2026-10-24-provenance-decision.md) retained a corrected value with
a later wrong action. [S-018](2026-10-24-retained-action.md) showed that an explicit
old action conclusion was unnecessary for its errors; both conditions still
included the old threshold. [S-019](2026-10-25-check-before-action.md) reached a
ceiling after task changes, leaving the repair question unresolved, and separately
showed a temporal-account mismatch. [S-020](2026-10-25-reproduced-check.md) restored
the earlier task, reproduced errors and found a requested-order benefit in two
authored banks, with unnecessary measurement costs retained.

The [original four-study tranche](2026-10-24-introspection-confirmation.md) supplies
the broader context of attribution, forecast calibration, memory-supported recovery
and hypothetical choices. It did not establish reliable private introspection.
S-021 can narrow prefix-content sensitivity; even a positive result cannot identify
the natural mediator of S-020, general reliability or a benefit to Astrid or Minime.

The intended save point preserves named commits, exact requests and raw outputs,
prefix/suffix distinctions, every scheduled disposition, independent checks, fixed
readings, the board record and a closed byte-verified backup outside this worktree.
No next study, live-system change or publication is part of this finish line.

## Save-point assessment

**This is a good scientific save point. S-021's review and preservation checks
are complete.** The sequence has reached a bounded answer to the selected
follow-up: the content placed immediately before the generated action matters
in this task, predominantly through the choice to measure again. The uncertainty
is now more specific. We do not know the natural mechanism behind the earlier
order effect or whether any of these results transfer to other tasks, models or
the Beings.

Across the tranche, preserving a fact, applying a comparison, choosing an action,
and accurately explaining the evidence have repeatedly needed separate checks.
S-021 adds a controlled intervention on supplied comparison content while retaining
the distinction between authored input and generated behavior. That is enough to
make this a useful stopping point without turning a narrow result into a general
theory of introspection.

No further study is launched. A later resumption can begin from the committed
protocol and this completed record, with a newly selected question and prospective
design. If this specific question is reopened, the minimum next observation would
be a prospectively fixed fresh authored bank repeating the same three-prefix
comparison, retaining MEASURE separately from wrong direct routes, to test whether
the observed sensitivity recurs. That is an unlaunched replication proposal; it
would not identify S-020's natural mediator. Final scientific review, board
read-back, immutable evidence closure and the byte-verified backup are complete.

## Final review and administrative closure

The independent scientific review approved the exact account at `a9cdb8a` after
1,095 checks. Its source copy is `methods-review/reviewed-account-v2.md`, SHA-256
`d12c2dddb7e469c52ca499c19a00798dbab4886d2bcad5ed10afc93c975d8014`.
Review receipt `methods-review/final-scientific-review-v1.json` has SHA-256
`ccaf323978d0e6e97a68adb7e45201d3f1ecc39b8d06e1f8b610b8aef1cfdb20`.
The sole reporting omission was the minimum next-observation sentence; it was
added explicitly as an unlaunched replication proposal. No outcome or method
changed during review. The earlier review input remains preserved as v1.

All generation sessions and independent writers have stopped. The implementation
worktree was clean, its checkpoint `fd37dafa` was integrated at `64458d8`, and it
was archived through the app with its named checkpoint retained. Main remains at
`b9f845dd095cd422d6e80de36c6b41e94880ed03` with no tracked changes. There was no
push, deployment, additional study or access to the Beings' live systems.

The Hold Shelf test `t-s021-prefix-continuation` is done, finding
`f-s021-prefix-content` is verified, and the session log records the bounded result
and cumulative save point. All three were saved and read back after a reload.
Private AX text, screenshots and `methods-review/board-closure-v1.json` retain the
proof. The temporary browser tab was closed. NOW and the research index point to
this account. Board wording distinguishes completed science from final evidence
preservation.

The account snapshot before evidence closure is retained as
`methods-review/completed-account-v1.md`. The closure marker binds that snapshot,
the approved scientific account, all audits and every retained evidence file.
The backup verification and final administrative commit are recorded separately
below so no closed evidence is modified to add its own backup receipt.

## Closed evidence and verified backup

The evidence tree was closed after checkpoint `9cc3506`. Its final write was
`research/outputs/prefix-continuation-20261025/CLOSED.json`, SHA-256
`98bba29466b707ac2cfea71063f15b74df6b07d4b0bc42cd1a3d47085411fc3a`.
The marker seals 839 preceding files and binds the complete account snapshot,
scientific review, exact requests/responses, prefix/suffix distinctions, every
scheduled outcome, reading stages, code hashes and board proof. No write to this
evidence tree occurred afterward.

The closed tree was copied outside this worktree: **840 files, 5,752,100 bytes**.
Source inventories before and after copying matched the destination; a separate
standard-library check then compared every literal byte, the full inventory and
the closure marker's inventory without importing the backup helper.

- [Backup manifest](/Users/mikepurvis/other/reservoir-llm-research/research/outputs/prefix-continuation-20261025-closed-backup-20261025T195101Z/backup-manifest.json), SHA-256 `02ed6648e3c9fb5e7b5aa07f7bd6ae536d6a0fa7352d0735de1e690f1dc99686`.
- [Separate verification receipt](/Users/mikepurvis/other/reservoir-llm-research/research/outputs/prefix-continuation-20261025-closed-backup-20261025T195101Z/independent-verification-v1.json), SHA-256 `baf80389575de2e47c461cba6444cfb172eb40ab0fa23edc1026ae9984a55c2e`.

This preserves a second copy on the laptop, not an independently verified backup
to another device. The protocol, implementation, approved account and completed
account remain named Git checkpoints. These final administrative additions live
in tracked documentation, outside the closed evidence. The research is saved;
there is no running experiment or automatically assigned next round.
