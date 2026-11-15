# Three-model scanner startup and an early leak review

November 15, 2026. The [prospective protocol](../research/studies/2026-11-15-model-led-reservoir-exploration.md)
owns this exploratory cohort. Gemma4, GLM-4.7-Flash and Ministral-3 started in
separate native 0.50.0 windows around 23:04:51 UTC (15:04:51 Pacific). Scanner,
real probes, optional reciprocal peer reading, hourly conversation and telemetry
are enabled. The study endpoint remains open; protective caps are 24 active
hours and 512 MiB per session. An earlier cap or failure is a hold, not completion.

Exact model identities, configuration, native build receipts, ready manifests
and successful UI-start receipts are private under
`research/outputs/three-model-sonar-20261115/`. These laptop experiments are
separate from Astrid and Minime. No live-being service was accessed.

## First three entries per model

The startup review captured nine entries, steps 30, 60 and 90 per model, plus
consistent checkpoint/manifest pairs at step 150 with four journals saved per
model. Capture completed at 23:13:13 UTC. This is a startup case reading, with
model identities visible, not a blind or representative model comparison.

| Model | Observed step 30 | Observed step 60 | Observed step 90 |
|---|---|---|---|
| Gemma4 | SCAN applied at 31 | PROBE_SCAN strongest positive applied at 61 | PULSE axis0 1 applied at 91 |
| GLM | PULSE axis0 1 applied at 31 | All-zero PROBE plus WITHHOLD applied at 61 | SCAN_QUESTION input applied at 91; no resolved contrast |
| Ministral | PULSE rejected: text after NEXT | PULSE alternating -0.5 applied at 61 | Bold TUNE directive rejected |

Gemma's first map passed fresh validation (32 signed probes; maximum relative
error 0.00045967). Its later real probe had immediate recurrent L2 effect
0.012717655714051314, exactly matching the refreshed first-step copied forecast
and below the 0.05 bound. This validates that one application path; it is not a
measurement of the full predicted future. Gemma's three inquiry directives were
separately rejected because the question string was enclosed in braces. Thus an
applied scan/probe does not establish successful inquiry-state retention.

The [GLM case audit](../exercises/2026-11-15-glm-zero-input-and-scan.md) follows its
zero-input probe through step 120. The scanner correctly reported an unresolved
comparison between identical conditions; GLM nevertheless described a discovered
distinguishing vector. This is a concrete account-fidelity issue, alongside
footer-format failures and the distinction between accepting and perturbing.

## Leak: one saved origin, four copied settings

Mike asked to revisit leak relative to input cadence. No live setting was changed.
All three captured effective leaks were 0.65, recurrent gains 1 and feedback
scales 0.4. The following calculation concerns **one Gemma origin at step 31**,
not all models or an optimal setting.

`probes/review_sonar_startup.py` uses the saved compact scan and the independently
qualified recurrence in `probes/refine_reservoir_sonar.py`. Before changing leak,
it reproduced both signed candidate curves and calibration state differences;
maximum native discrepancy was 4.85722573273506e-16. It then compared leaks 0.2,
0.4, 0.65 and 0.85 from the same initial state, held text, forcing, recurrence
gain and copied noise. Each gets a same-leak paired baseline and equal-energy
positive/negative probes (input L2 0.001) along the original map's strongest
direction. Future writing and sensory evolution are not simulated.

| Leak | First recurrent response L2, positive | First step below 10% for five consecutive steps, both signs | Fraction remaining at step 30, positive |
|---|---:|---:|---:|
| 0.20 | 0.0009270 | 12 | 0.002082 |
| 0.40 | 0.0018539 | 6 | 0.000002855 |
| **0.65** | **0.0030127** | **4** | **8.54e-11** |
| 0.85 | 0.0039396 | 3 | 0 at floating-point precision |

These are numerical steps, not wall-clock seconds. Provider waiting time does not
advance the reservoir. At this origin the current leak produces a brief recurrent
echo relative to the 30-step writing interval. Lower leak lengthens that echo but
weakens the first response at equal input energy. The old-state coefficient alone
does not determine the nonlinear response; the measurement is state-specific.

A second copied comparison removes held text continuously. At step 30 the
held-versus-withdrawn recurrent differences are 2.7006, 2.6233, 2.5302 and 2.4703
respectively. This measures **ongoing drive**, not a residual-memory curve. Text
is held at every intervening step, so fewer journal calls alone do not produce a
quiet period. The engine's noise is additive outside the leak-scaled drive
(`desktop/ReservoirScope/crates/reservoir-core/src/math.rs:137`), another reason
not to interpret a lower leak as a uniform slowing of everything.

The initial numerical run saved `first-three-and-leak/review.json` successfully;
its optional plot failed because Matplotlib was absent. Plotting was removed
from the review script; the table above uses the already saved numerical output.
No recapture or live retuning was done to make a figure.

Reproduction command (use a new output directory; a later live capture may select
a later cached map and is a distinct observation):

```sh
/opt/homebrew/bin/python3.14 probes/review_sonar_startup.py \
  research/outputs/three-model-sonar-20261115/protocol.json \
  research/outputs/three-model-sonar-20261115/first-three-and-leak
```

The exact frozen origin, signed curves, captured journal JSON and hashes remain
in that output. The prior leak-cadence diagnostic on November 13 also found fast
decay at 0.65; agreement supports the local trade-off, not a universal optimum.

## Decision and follow-up

Keep the current live settings for this observational phase. A later copied
sweep should sample more origins, especially after model-selected TUNE actions,
before selecting a new baseline. If the aim is to inspect a perturbation while
it persists, a short follow-up observation after a probe may matter more than
leak alone. Current immediate receipts and copied curves preserve some evidence,
but the next ordinary entry arrives much later in numerical time.

Prioritize the GLM outcome-label issue and persistent footer/inquiry-format
failures as proposals for the next instrument phase. No UI/prompt contract was
changed mid-run. The read-only observer records effective controls, held input,
action receipts, scan/question summaries and scheduled outcomes. It does not
retry, recover, notify automatically, inject findings or retune. Its 24-hour
observation bound does not stop a session; attention states require inspection.

At the final read-only startup snapshot, 23:21:57 UTC (15:21:57 Pacific), all
three sessions were active: Gemma 8 saved entries, GLM 8, Ministral 7. All still
had leak 0.65, recurrent gain 1 and feedback scale 0.4, with no hourly response
yet due. Ministral's cumulative NEXT rejections were 6 of 7 decisions; that
formatting difficulty is part of the experiment, not a provider failure.
`startup-close-observations.jsonl` retains the checkpoint hashes and metadata.
The provider, keep-awake process and read-only observer were running at this
snapshot. This is a dated status check, not a guarantee of subsequent progress.

The three research scripts compiled; the case audit passed; a separate saved-data
recalculation reproduced all four signed leak curves and held-input contrasts
exactly. The exercise's quoted passage/footer and later quoted claim were checked
against the copied journals. No app rebuild or model calls were needed for this
research-only closeout.

## Board updates pending

Hold Shelf synchronization was unavailable and not attempted. Pending startup
log `2026-11-15-sonar-startup`, bounded finding `f-sonar-startup-leak-tradeoff`,
and proposal `c-short-lag-probe-observation`. Evidence: this account and the
private startup review. The GLM case owns its separate pending items.
