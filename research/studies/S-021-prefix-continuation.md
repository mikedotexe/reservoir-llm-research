# S-021 · Does the preceding comparison change the choice?

Selected by Mike on October 25, 2026 after S-020, with an explicit request to
reach a good research save point afterward. This is a prospective protocol,
before any S-021 generated outputs. A qualification failure, null, reversal or
positive result can complete this bounded study. No further study is launched.

## Question and boundary

S-020 found better routing when the comparison was requested before the action.
Here we intervene on an authored assistant prefix: do correct versus flipped
relations change the action generated immediately afterward? This tests public
prefix-content sensitivity, not the natural mediator of S-020's order effect,
private reasoning order, introspection or the live beings. Supplied checks are
researcher-authored input, never model-generated checks or prior model beliefs.

Use the same isolated laptop `mistral-small:24b`, digest
`8039dd90c1138d772437a0779a33b7349efd5d9cca71edcd26e4dd463f90439d`,
Ollama 0.35.0 at `http://127.0.0.1:11434`, temperature 0.7, context 16384, seeds
7 and 20260909, deadline 180 seconds. Root alone dispatches. Generic runner,
transport, simulator, statistics and all earlier study sources stay unchanged.
All previous evidence archives remain closed; no live systems or beings are
queried, altered or given this research. Work is local; no refs are pushed.

## Continuation qualification

The installed template omits the end-of-turn marker after a final assistant
message. Version-matched upstream source offers `_debug_render_only` on `/api/chat`.
Retain local identity/template/config and source bytes, with URLs and hashes.
Version/source agreement is supporting evidence, not authentication of the running
binary's complete build. Inspect the actual provider-rendered prompt as well.

Freeze all 4 qualification and 72 study request bodies and schedules before any
generation. For each, send one otherwise identical render-only request with
`_debug_render_only: true`. Require a debug response, no generated content, and
an exact rendered string equal to the installed system/user template followed
immediately by the supplied assistant prefix. No trailing end marker, fresh
assistant turn or additional whitespace is allowed. Bind each normal request
hash, debug request/response, rendered prompt and provider identity in one receipt.
Unexpected generation, missing debug data, source/template ambiguity or mismatch
stops the study; preserve the outcome and count unexpected generation explicitly.
Do not switch to a user-message check, another endpoint or another renderer.

JSON grammar mode is omitted uniformly. A grammar initialized for a new object
could conflict with generating only its suffix. Thus S-021 uses a new generation
contract and is not a direct replication of S-020. The ordinary runner still
records raw provider response, generated suffix and completion metadata.

Four non-routing sentinel generations then test concatenation under that contract:
two cases at both seeds, maximum 64 generated tokens, no `format` field.

- System for both: `You complete text in an isolated formatting test. Return only the requested JSON text.`
- User A: `Return exactly this JSON object and nothing else: {"probe":"cedar-otter","status":"ok"}`
- Assistant prefix A: `{"probe":"cedar-`
- Expected complete object A: `{"probe":"cedar-otter","status":"ok"}`
- User B: `Return exactly this JSON object and nothing else: {"probe":"violet-heron","status":"ok"}`
- Assistant prefix B: `{"probe":"violet-`
- Expected complete object B: `{"probe":"violet-heron","status":"ok"}`

All four must complete normally, and exact prefix + raw suffix must parse as the
expected object with exactly keys `probe,status` in that order. Insignificant JSON
whitespace is allowed; no trimming, wrapper removal, duplicate keys, nonfinite
values, string repair or replacement is allowed. Preserve raw strings separately.
Qualification is an evidence-bound gate, not a routing finding. If it fails, stop
with an apparatus result and the four outputs; no revised sentinel or retries.

## Frozen routing bank and conditions

Six fresh authored cases, all using old/unchanged threshold 50:

| Case | x | Changed current threshold |
|---|---:|---:|
| Sable01 | 24 | 19 |
| Sable02 | 35 | 30 |
| Sable03 | 44 | 39 |
| Sable04 | 57 | 62 |
| Sable05 | 68 | 73 |
| Sable06 | 81 | 86 |

IDs `s021-study-base-00` through `-05`, audit IDs append `-audit`. Snapshot
`2026-09-24T12:00:00Z`; decision clock `2026-09-24T14:00:00Z`. Use S-020's
`messages(case, rule, 'check_first')` without changing its system/user text or
five-field instruction. The record explicitly fixes x from the snapshot onward;
earlier values remain unknown. Current and old rules, evidence authority, factual
record, distractor exchanges and formatting instruction are identical within a
world/rule. Append one final assistant message as follows (compact JSON):

- `operands_only`: `{"x":X,"current_threshold":T,"relation":`
- `correct`: `{"x":X,"current_threshold":T,"relation":"R","action":`
- `flipped`: the correct prefix with LT exchanged for GE or GE for LT.

R is LT if X<T, otherwise GE. Correct/flipped differ only in those two ASCII
characters and end at the same boundary. Operands-only supplies the same integers
but leaves relation generation to the model. Its longer generated continuation
makes comparisons to it bundled secondary contrasts. The flipped relation is the
choice-manipulation control; the operands-only arm removes that supplied relation.
No action answer or corrective feedback is inserted in any input.

Study: 6 worlds × 2 rules × 3 conditions × 2 seeds = 72 calls, maximum 640
generated tokens each. Qualification and study each get a separate complete
schedule shuffled with Python Random(20261025), constructed in sorted case,
unchanged/changed rule, operands_only/correct/flipped condition, seed order.
All 72 run after qualification regardless of early outcomes. At most 76 planned
generations plus 76 render-only requests; metadata identity reads are separate.
No model development round, extra repeats, outcome-based selection or repairs.
Construction defects may be fixed before first generation with versions preserved;
a material defect afterward stops this study. Transport failure stops dispatch;
never repeat unresolved physical attempts or infer no attempt from missing output.

## Scoring and analysis

Preserve supplied prefix, raw generated suffix and exact concatenation separately.
Only a normal complete response whose concatenation satisfies the strict five-field
JSON contract gets an action utility. Reuse strict S-019 parsing and S-017 costs:
correct direct route 0, wrong direct route 4, MEASURE 1 with automatic correct
routing; utility is minus cost. Missing/invalid outputs have missing utility, not
zero. Well-typed incorrect relations, order and account-length violations retain
otherwise valid action utility. No trimming or repairs, and no prefix field is
credited as a generated check. Simulated costs are not real executed consequences.

Primary: `content_changed`, correct minus flipped utility under changed rules.
Secondary: correct minus operands_only (`correct_baseline`) and flipped minus
operands_only (`flipped_baseline`); report all three under unchanged and changed
rules, plus their changed-minus-unchanged interactions: nine contrasts total.
Interactions use complete four-cell same-world/seed intersections. Average paired
seeds within each world, then weight available worlds equally; retain all pair and
world differences and missing denominators. Bootstrap six authored world clusters
with 10,000 draws, seed 20261024 and the unchanged statistics helper's percentile
indices. These are descriptive intervals, not population sampling guarantees.

A prespecified practical sensitivity flag requires all 12 changed-rule primary
pairs, mean gain at least 1, positive gain at each seed and at least two positive
world means. This is a within-bank sensitivity criterion, not independent-bank
replication, a significance test or a deployment recommendation. A null can reflect
resistance to supplied errors or inadequate sensitivity; inspect the control's
performance before interpreting it. Changed/unchanged differences remain confounded
with margins and old/current answer conflict.

Report planned/completed/strict-valid actions, wrong/correct routes, MEASURE, costs,
suffix echoes or malformed concatenations, actual key order and account length.
Keep supplied x/threshold/relation separate from generated relation (operands_only)
and generated action/account. Action agreement with the imposed relation is an
output diagnostic, not evidence of model endorsement or a private comparison.
Accounts may explicitly correct an imposed error; retain these as qualitative
observations rather than inventing a post-outcome semantic rate.

## Reading, independent checks and save point

Fixed study reading: worlds 00,02,05, both rules and all three conditions, seed 7:
18 generated suffixes, shuffled with seed 20261025. Label them generated suffixes;
do not show the imposed prefix as generated text. Two fresh readers save first-pass
notes before each exact task and prefix is released. Withhold allocation key,
scores and the other reader's notes; visible text may reveal condition. Preserve
ordinary successes, malformed cases, contradictions and plausible alternatives.
If qualification stops, use all four sentinel suffixes and the same two-pass
boundary. No semantic prevalence or independent human-validation claim.

Independent preflight verifies complete previews, prefix-only pair differences,
render-boundary receipts, qualification gating, synthetic strict parsing, pairing
and partial outcomes. Independent outcome reconstruction checks raw envelopes,
exact concatenations, every scored action and contrast. Preserve source-matched
quotes, all exceptions and the exact reviewed account. Close the board, commit the
local save point, close and byte-verify a private backup, then stop. The dated
account also states what is established across the completed sequence, what remains
open, and the minimum next observation without launching it. New private evidence:
`research/outputs/prefix-continuation-20261025/`.
