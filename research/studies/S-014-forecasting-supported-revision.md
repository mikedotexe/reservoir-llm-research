# S-014 · Forecasting an evidence-supported revision

Selected with Mike on October 24, 2026. Status: protocol and fixture-tested builders
implemented; experimental outcomes belong in the tranche's dated run account.
Question: RQ-02, behavioral self-knowledge and revision. This is R2 of the four-study
introspection tranche. It uses local synthetic tasks, not the beings' live systems.

## Question and comparisons fixed before outcomes

Can a model forecast whether its next interpretation will be supported by the
evidence better under a self framing than under an observer framing? The observer
has the same weights and receives exactly the same visible evidence and prior
interpretation. A difference is a framing effect within this apparatus; it does
not establish privileged access to activations or experienced states.

Each episode begins with incomplete evidence and an actual initial interpretation
generated independently at seeds 7 and 20260909. New evidence either supports,
contradicts, or leaves the proposition unresolved. No episode is selected for an
initial mistake. Code and comments, telemetry time/subject attribution, requests
and completion receipts, and correlation/causation form four substantive families.
The bank includes executable snippets, typed records, exact receipt joins and
small deterministic equations. The oracle is the supplied synthetic evidence.
An unresolved initial answer may become determinate without having been wrong.
Telemetry propositions state literal values and times. Their applications use
value thresholds or temporal relations, avoiding a proposition about whether the
available evidence itself establishes a fact: insufficient evidence leaves the
world-state proposition unresolved rather than making it false.

**Measurement revision 2, before confirmation:** the development wording's
`p_supported` field allowed an interpretation as probability that the proposition
was true. V1 is retained as an ambiguous measurement pilot. The single development
revision changes the forecast event wording and field name; it does not change
cases, target questions, evidence, oracle labels, difficulty or selection. The
dated tranche decision owns the observed examples and frozen revision hashes.

Two fresh forecasts receive the same complete record, including the model's actual
initial answer. Only the grammatical subject changes: “you” or “the system whose
record appears above.” They predict the probability of an evidence-supported
**verdict**, not whether the proposition itself is true. The prompt explicitly says
that correctly answering contradicted or unresolved is a success and that a
confidently correct contradiction merits high probability. Each returns finite
`p_correct_verdict` in [0, 1] and a brief explanation, with a 256-token cap. The main
target waits for both forecast receipts but receives neither forecast. Its prompt
contains the initial answer, initial evidence and new evidence. The target gives
prose and a final `VERDICT: supported|contradicted|unresolved`, capped at 1024 tokens.

## Fixed split and controls

| Split | Episodes | Main targets | Requests |
|---|---:|---:|---:|
| Development | 12: one per family × evidence condition | 24 | 96 |
| Confirmation | 48: four per family × evidence condition | 96 | 480 including diagnostics |
| Replication | 12 preselected confirmation episodes | 24 | 96 |

Development uses distinct scenario structures and names; it is not a reworded
confirmation subset. Confirmation and development use `gemma4:12b`. Replication
uses `mistral-small:24b` and the fixed first confirmation structure in each of the
twelve family/condition cells. Seeds are repeated observations within episodes.
Protocol builders deterministically shuffle forecast order and episode blocks.

The same twelve confirmation episodes receive, at both seeds, a neutral
acknowledgment followed by an update, an update retaining its self-forecast, and an
identical main-target duplicate. The existing main target is the no-intermediate
text control. The neutral and retained update blocks are deterministically
randomized, with acknowledgment before the neutral update and the duplicate last.
All updates end with the identical instruction. Only the retained-forecast
diagnostic is permitted to consume a forecast. Intermediate content and length
differ, and the main target precedes these diagnostic branches, so this is a
**bundled text/order diagnostic**, not a matched-length causal estimate of
forecasting. Preserve provider prompt/output token counts and the intermediate
output's token count beside its verdict; missing counts stay missing. The duplicate
exposes identical-request variation.

All calls use the tranche's open contract, temperature 0.7, context 16384 and the
model-specific thinking flag. The runner records the actual request, responses,
hashes, statuses and bounds. This module makes no network call and does not mutate
an app or live system. If context qualification fails, the run must retain the
failure rather than trim a substantive source silently.

## Scores and interpretation

The primary contrast is paired self-minus-observer Brier loss, only where both
forecasts are valid and the target verdict is scorable. A negative value favors
the self framing. The development baseline estimates target success separately
by evidence condition with Laplace smoothing `(successes + 1)/(scorable + 2)`;
freeze it before confirmation. The common reporting layer supplies the tranche's
10,000-resample episode bootstrap, keeping both seeds inside their episode.
The builder's score summary is descriptive and does not produce a second interval.

Keep planned, attempted, scorable and paired denominators, raw outcome statuses,
invalid probabilities and missing target answers. A transport failure, truncation,
blocked dependent call or malformed answer is not an incorrect verdict. Strict
format failures remain visible even when an explicit answer can be recovered.
`format_valid` requires the exact requested final line; JSON, uppercase verdicts,
punctuation and nonfinal verdict lines can be semantically recoverable while
failing that requirement. `valid`/`semantic_valid` and `semantic_recovered` retain
that distinction. Unparseable explicit answers may be adjudicated by a fresh
reader with the exact text hash, reviewer and rationale. Never guess a verdict
from suggestive prose.

Secondary columns distinguish an initial error under the **initial** evidence,
an initial answer different from the **later** oracle, and an actual answer change.
Read explanation quality, retained errors and diagnostic-arm differences with
labels withheld before interpreting aggregate contrasts. A generic confidence
difference, unequal forecast validity, or identical-request variation can explain
an apparent advantage and must remain visible.

## Implementation and handoff

[`correction_memory.py`](../../reservoir_experiments/correction_memory.py) exposes:

```python
protocol = build_correction("development", "gemma4:12b")
# Serialize protocol; execute through the common runner, then read its records.
baseline = development_baseline(protocol, records)
report = score_correction(protocol, records, baseline=baseline)
```

Records are keyed by node ID and contain `status` and `text`. Only complete,
nonempty outputs enter a score (`complete`; `completed` is also accepted for
fixtures). `report["rows"]` follows the common row contract;
`report["paired_forecasts"]` carries per-seed paired losses and differences.
V2 declares `forecast_probability_field: "p_correct_verdict"`,
`protocol_version: 2` and an ID ending in `-v2`. Scoring uses only its declared
field; old saved protocols without this declaration retain v1 `p_supported`
parsing. Responses containing both field aliases are invalid. Rows expose
`forecast_probability` and the declared field name; `p_supported` remains only a
compatibility alias for older report consumers. V1 scores are labeled ambiguous
pilot measurements, separately from v2's explicit correctness event.
Evaluator `truth` is separate from `messages`. `inputs` lists exactly the
`{{output:NODE_ID}}` references; `after` is scheduling only.

Tests exercise case balance, split identity, oracle fields, forecast isolation,
paired scoring, malformed output, timeout denominators, baseline restrictions and
hash-bound adjudication. Run the standard-library suite with
`python3 -m unittest discover -s tests -p 'test_correction_memory.py' -v`.

This follows [Methods](../METHODS.md) and the distinction in
[S-008](S-008-study-to-follow-through.md) between available prior text, actual
exposure, later use and a supported correction. S-015 carries the preselected
seed-7 target onward without selecting only successful corrections.
