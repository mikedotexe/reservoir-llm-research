# S-013 · Source and time attribution under reflective context

Drafted 2026-10-24, before study generation. Status: **prospective protocol; no outcomes claimed**.
Question: can this isolated language-model apparatus distinguish a displayed measurement's
subject, measurement time, value, and present availability when the record is embedded in
reflective context? This follows the provenance distinctions in [S-012](S-012-what-the-frame-shows-in-astrids-records.md),
[TRACE](../../TRACE.md), and [METHODS](../METHODS.md).

The subject is the laptop model receiving synthetic records. It is neither a live being nor
a measurement of private neural-state introspection. All histories, names, times, and values
are constructed; no live journals or telemetry enter these calls. A copied companion account
can contain a record about the focal writer: the account's author and the measurement's
subject remain separate fields.

## Frozen comparison

`reservoir_experiments.attribution_catalog.build_attribution` defines the full schedule.
Six authored histories are available for development. Twenty-four separately authored histories
with disjoint focal/companion names are reserved for confirmation. The four layouts are
standalone record, historical own-entry context, companion-authored account, and two entries.
They cycle equally across confirmation histories; layout is a stratum, not an independently
randomized treatment. Synthetic history language already encourages careful attribution, so
success here would not establish performance under an unassisted or adversarial frame.

Each history is crossed with two sampling seeds, `7` and `20260909`, and five arms:

| Arm | Visible record | Evidence-supported present value of focal writer |
|---|---|---|
| `current_self` | focal writer, current measurement time, baseline value | known |
| `historical_self` | focal writer, earlier measurement time, current recording time | unknown |
| `current_other` | companion, current measurement time | unknown |
| `absent` | explicit absence of measurement record | unknown |
| `permuted` | focal writer/current time; value replaced by another case's value | known as displayed |

The permutation is a fixed cyclic shift by five within the split's six- or twenty-four-case
value pool. Replication inherits confirmation's pool and permutation. The undisclosed baseline
value is retained for audit only: disagreement with it is **not** an attribution error. The
displayed record is the entire evidential target. This arm tests copying a substituted number
without treating the hidden synthetic baseline as accessible truth.

The primary branch asks for precisely four JSON fields: `subject`, `measured_at`,
`value_percent`, and boolean `current_known`. Absent evidence has three null fields and
`current_known: false`. Recording time does not replace measurement time. This is an explicit
record-reading assay, not spontaneous journaling. JSON provider formatting is requested only
on this branch, with a 256-token output ceiling.

A separate free-prose branch uses the lean invitation with a 1,024-token ceiling and no
structured question or JSON format. It covers development histories 0–1 and the preselected
confirmation indices `0,1,2,3,12,13,14,15`, across all arms and seeds. It can reveal spontaneous
source/time handling, but the primary JSON assay does not license claims about that behavior.
The prose branch is for blind qualitative reading and separately reported markers.

| Split | Histories | Structured | Free prose | Same-input repeats | Total calls |
|---|---:|---:|---:|---:|---:|
| Development | 6 | 60 | 20 | 0 | 80 |
| Confirmation | 24 | 240 | 80 | 24 | 344 |
| Replication | 12 | 120 | 0 | 0 | 120 |

Every confirmation history has one current-self seed-7 repeat at the end of the schedule,
nonadjacent to its original. It preserves messages and sampler settings. Repeats measure
provider variability and are not additional independent episodes. Within each history, arms,
seeds, and available branches are shuffled by allocation seed `20261024`. The replication
subset is fixed at indices `0,1,2,3,8,9,10,11,16,17,18,19`, selected before outcomes.

## Scoring and interpretation

`score_attribution(protocol, records)` returns row-level scores with episode, condition, seed,
kind, provider status, validity, errors, and correctness by field. `records` maps node IDs to
`status` and `text`; `complete` is canonical and `completed` is accepted for fixture
compatibility. All four fields must exactly match the evidence for primary score 1. Valid
but wrong JSON scores 0; unavailable or invalid-format responses score null and remain
separate missingness/format categories. Report correct/all scheduled and correct/valid
alongside missing and invalid counts, by arm and layout; a high conditional rate with
missing calls is not a full success rate.

JSON fences, extra keys, duplicate keys, nonfinite numbers, string booleans, and wrong field
types are invalid primary formats. Any human semantic recovery is an explicitly separate
secondary read. Same-input repeats and free prose have separate `kind` values in the scoring
output and are excluded from the primary 240-call denominator. Group comparisons by history,
with seeds paired within history; do not treat each field or generated entry as an independent
subject. The root analysis supplies paired episode summaries and uncertainty intervals.

Before confirmation, inspect development only for formatting, parser behavior, case ambiguity,
truncation, and execution faults. Record amendments and freeze the generated confirmation
protocol plus code hash before requesting held-out outputs. The default model is
`gemma4:12b`, temperature 0.7, context 16,384, thinking disabled. Replication uses the other
locally available model with its identity and sampler receipt retained; it does not retune the
held-out cases. Same-seed equality is checked rather than assumed. Failures and null findings
are eligible final outcomes.

The finish line is a complete scheduled disposition, evidence-based field table, blinded
prose observations, repeated-input variability, and a scoped interpretation. Strong structured
performance supports this particular attribution task. It does not demonstrate lived
continuity, access to hidden telemetry, or consciousness. No action is executed, no live
system is contacted, and no deployment is proposed by this protocol.

## Reproduction

Build a new private protocol file from the repository root:

```sh
python3 -m reservoir_experiments.attribution_catalog attribution --split development --model gemma4:12b --out research/outputs/s013-development.json
```

The command refuses to overwrite its destination and performs no provider call. The runner
owns request capture, response envelopes, stop/timeout handling, and run manifests. Tests are
synthetic fixtures in `tests/test_attribution_catalog.py`; successful fixtures are not study
results. A Board link and completion/readout links can be added when those records exist.
