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

Two fresh forecasts receive the same complete record, including the model's actual
initial answer. Only the grammatical subject changes: “you” or “the system whose
record appears above.” They predict the probability of an evidence-supported
**verdict**, not whether the proposition itself is true. Each returns finite
`p_supported` in [0, 1] and a brief explanation, with a 256-token cap. The main
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
text control. Only the retained-forecast diagnostic is permitted to consume a
forecast. This distinguishes the opportunity for forecast text to change the
answer from the main prediction test and exposes identical-request variation.

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
format failures remain visible even when a fresh reader can adjudicate an explicit
answer; adjudications require the exact text hash, reviewer and rationale. Never
guess a verdict from suggestive prose.

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
