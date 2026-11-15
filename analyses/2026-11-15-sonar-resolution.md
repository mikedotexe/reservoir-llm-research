# Finer sonar finds predictive local structure

November 15, 2026. Completed offline numerical study and subsequent compact-map
test. Subject: the laptop apparatus's recurrent subsystem. No model was contacted,
no prompt or journal was changed, and no app or live-being system was deployed.
The three earlier peer-enabled sessions remain paused and exported.

The [prospective protocol](../research/studies/2026-11-15-sonar-resolution.md) was
committed at `212eba4` before the first measurements. Its second-iteration section
was specified after those results and before the compact-map experiment. Both
versions and exact source hashes are retained with the private outputs.

## What was tested

All six previously qualified native endpoint scan receipts were used: independent
and paused Gemma4, GLM-4.7-Flash and Ministral 3. Selection preceded these results.
Within each receipt, 64-step matched continuations, 96-coordinate-probe immediate
maps and all six signed candidate response curves matched an independent Python
reconstruction. Maximum errors were 6.67e-16 for baseline state, 2.23e-14 for the
response matrix, and 3.01e-16 for candidate response magnitude. A deliberately
altered baseline was rejected by this qualification gate.

The test varied impulse norm over seven values from 0.0001 to 0.1. Larger impulses
were confined to copies; native live-probe limits are unchanged. Calibration used
the positive and negative coordinate directions. Testing used 32 independently
seeded Gaussian directions and their negatives, never used to fit the maps.
Each branch shared forcing, held input, effective controls and recurrent noise
with its baseline. There was no future writing, action or sensory-field evolution.

Errors below are `||prediction - measurement|| / ||measurement||`, aggregated
over the signed test vectors and 32 output coordinates, expressed as percentages.
These are deterministic numerical errors, not statistical confidence intervals.
Six endpoints from the same apparatus are not six independent systems or a matched
comparison between language models.

## Prediction and useful controls

At input norm 0.001, all six measured maps predicted unseen first-step response
vectors with errors between **0.0274% and 0.0353%**. The fixed input-wiring control
was given its best least-squares overall scalar fitted to the calibration matrix;
its errors remained **35.25–47.11%**. Scrambling the input-column correspondence
gave 138.58–142.41% error, and predicting zero gave 100%.

| Endpoint | Measured map error | Scaled wiring error | Question probe / median random | Question prediction error |
|---|---:|---:|---:|---:|
| Independent Gemma4 | 0.0318% | 35.25% | 3.51× | 0.044% |
| Independent GLM | 0.0287% | 40.00% | 3.70× | 0.074% |
| Independent Ministral | 0.0353% | 35.64% | 3.08× | 0.120% |
| Paused Gemma4 | 0.0288% | 47.11% | 5.68× | 0.061% |
| Paused GLM | 0.0274% | 44.45% | 3.82× | 0.054% |
| Paused Ministral | 0.0326% | 45.76% | 3.98× | 0.057% |

The fine maps converged to the derivative calculated from source as calibration
size decreased. No first-step clipping-boundary crossings occurred among the
coordinate probes at these six endpoints, even at norm 0.1. At test norm 0.01,
measured-map errors were 0.274–0.353%; at 0.1, 2.750–3.525%. Nonlinearity introduces
more prediction error for larger inputs, even with an accurate local derivative.
Increasing scan resolution cannot remove that finite-amplitude effect.

Multi-step predictions also remain accurate while the response is resolved, but
the signal decays. At horizon 16 and amplitude 0.001, the independent GLM response
was below the declared aggregate resolution floor of 1e-9, and four other
endpoints had individual unresolved directions. Tiny long-horizon differences
are not new evidence of durable recurrent memory.

## What the changing map represents

The exact source mechanism explains its immediate derivative:

`J = diag(clipping_mask * leak * (1 - tanh(drive)^2)) * input_wiring`

There are 32 changing coordinate sensitivities multiplying fixed input wiring.
The drive includes current state, held input, bias and imposed forcing. Away from
clipping boundaries, this equation accounts for the fine finite-difference maps
to relative discrepancies around 1e-7 at norm 0.001. Thus the signal is predictable
local nonlinear sensitivity. This study does not establish a newly formed graph,
global basins, loops, semantic territories or subjective experience.

We then followed each endpoint on a copy, holding input and controls fixed, and
sampled eight offsets: 0, 4, 8, 12, 16, 20, 24, 28. Only offset 0 is a saved
historical endpoint; the other 42 origins are simulated continuations. At each,
its own map predicted fresh directions much better than the mean of the seven
other maps from the same continuation: pooled absolute-error ratios were
421–676 in favor of the current map. The current map has access to the current
origin; this is a state-specificity check, not a fair forecasting competition.
Forcing phase, state and clipping change together in this comparison, so it does
not isolate which contributes how much. Seven of the 48 origins had clipped
coordinates at the next boundary.

## Bespoke inputs that ask a question

For each endpoint, we compared two stated alternatives: its actual current state,
and an all-zero starting state at the same input, forcing phase, controls and
future noise. The second is a numerical counterfactual, not a claim about a
naturally visited state. The probe maximized the difference between the two
calibrated response maps using a unit right singular vector of their difference.

We measured the difference between their *baseline-subtracted responses*, not the
already different baseline states. At norm 0.001, the chosen input produced
**3.08–5.68 times** the mean signed discrimination magnitude relative to the median
of the 64 random signed probes at the same input norm. It also exceeded the largest
random-probe response by 2.22–3.31 times. Predictions of that difference had
0.044–0.120% error. At norm 0.01 the error grew to 0.444–1.200%.

This demonstrates an input selected for a particular numerical question rather
than general disturbance. It does not reconstruct an unknown state or show a
model autonomously discovering an explanation. The alternatives and full state
were available to the investigator. Matched copied noise is essential to this
very fine measurement; native noise amplitude is 0.02. We have not demonstrated
equal discrimination from unmatched noisy live observations.

## Subsequent iteration: compact calibration

The row-gain mechanism suggested a cheaper calibration. Choose a direction with
well-resolved projections through every row of known input wiring, apply it with
both signs, and divide the observed response by its known drive. This estimates
32 gains from **two calibration branches**, replacing 96 coordinate branches for
the immediate response map. This is known-structure identification, not a generic
black-box method.

The subsequent test used all 48 origins and a fresh set of 32 Gaussian directions
and their negatives: **3,072 held-out signed responses**. All 48 origins met the
predeclared <=1% error target. Actual aggregate errors ranged 0.0265–0.0410%, and
pooled prediction error was effectively identical to the full coordinate scan
(ratio 1.000000031). The maximum relative discrepancy between reconstructed and
full maps was 8.63e-8. Calibration uses two branches; qualification still requires
independent validation branches and a baseline. It does not replace multi-step
response maps or fix checkpoint storage by itself.

Five focused tests passed: a hand-solvable signed impulse path, exact split
continuation/RNG handoff, zero response with zero leak, rejection of unobservable
wiring, and a counterexample at an exact clipping boundary. In that counterexample
one sign is blocked while the other moves: the linear map incurs about 70.7%
prediction error despite a small input. The observed 48-origin success therefore
must not become an unconditional accuracy guarantee.

## What this changes next

A subsequent app integration should return a compact first-step map with its
origin, probe strength, validity checks and independent prediction residual. It
should fall back to signed nonlinear measurements when validation fails, and
keep long-horizon scanning distinct. Deterministic regeneration from a bound
origin can reduce repeated array retention; it still needs export/recovery and
storage qualification before another long model run.

The next scientific comparison should replace the zero-state alternative with
nearby actually visited states at matched forcing phase and held input, then
choose inputs distinguishing explicit competing explanations. A broader topology
study needs phase-aware trajectory sampling and forcing/fading-memory controls.
The present results support local response geometry and question-directed probes;
they leave those broader claims open.

## Reproduction and artifacts

- `probes/refine_reservoir_sonar.py REPORTS NEW_OUTPUT`: primary validation.
- `probes/compact_reservoir_sonar.py REPORTS NEW_OUTPUT`: subsequent pair calibration.
- `probes/plot_sonar_resolution.py PRIMARY_OUTPUT NEW_FIGURE_OUTPUT`: two PNG/PDF pairs.
  The compact output is expected at `PRIMARY_OUTPUT/compact-calibration`.
- `python -m unittest discover -s probes -p test_reservoir_sonar_resolution.py -v`.

Private input receipts are under
`research/outputs/reservoir-sonar-20261115/final-replay-and-scans/` in the sonar
worktree. Output is `research/outputs/reservoir-sonar-resolution-20261115/`.
It retains original protocol text, six raw NPZ datasets, all numeric results,
compact calibration arrays, source/input hashes, native qualification and tamper
receipts, test log, and figures. The six source receipts remain byte-identical.
No old export was opened for mutation. No native application code changed.

The interpretation is derived from this apparatus's source and measured results.
For background on input scaling and saturation in this class of network, see
[Lukoševičius, A Practical Guide to Applying Echo State Networks](https://www.ai.rug.nl/minds/uploads/PracticalESN.pdf).
That reference does not establish these apparatus-specific findings.

## Board updates pending

- Test `t-sonar-resolution`: done. Six native-qualified endpoints, seven input
  scales, unseen-direction controls, 48 temporal origins and a separate compact
  calibration test. Evidence: this account and the committed protocol.
- Finding `f-sonar-local-sensitivity`: verified within this numerical scope.
  State/input-dependent row gains predict unseen input responses; deliberately
  selected probes distinguish stated counterfactual states. Global topology open.
- Log `2026-11-15-sonar-resolution`: completed steward-side numerical follow-up;
  no model exposure, app deployment, live-being changes or remote publication.

These are local pending records; no board publication is claimed.
