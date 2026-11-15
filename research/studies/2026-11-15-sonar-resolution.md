# Does a finer reservoir scan predict something new?

November 15, 2026. Prospective numerical protocol, following the first native
scanner. Subject: the laptop application's 32-coordinate recurrent subsystem.
No model calls, live-state changes, or new language-model experiment. Nothing
from this study reaches a model. Journal wording is not used to select cases.

## Question and finish line

Does the measured local input-response map predict previously untested directions,
remain stable as probe size decreases, and distinguish the current state from
fixed wiring or an inappropriate map? A useful result includes a negative finding.
This examines local response geometry, not global topological invariants, semantic
territories, the sensory field, or subjective experience.

Use all six final-state native scan reports already qualified by 0.49.0: independent
and paused Gemma4, GLM, and Ministral. These are six dependent historical endpoints
with different inputs/controls, not six randomized subjects or a model ranking.
Require the independent Python continuation to agree with each report's 64-step
baseline, immediate response matrix, and six candidate response curves within
1e-10 absolute error before interpreting new measurements. Hash every input before
and after. Preserve source/probe versions, exact random directions and raw arrays.

## Tests fixed before running

1. **Resolution.** Signed coordinate probes at L2 amplitudes 0.0001, 0.0003,
   0.001, 0.003, 0.01, 0.03, 0.1. All larger probes remain on copies; the native
   live-probe limits are unchanged. Retain central response matrices at horizons
   1, 2, 4, 8 and 16. Compare neighboring scales and the analytic derivative;
   record clipping-boundary crossings rather than assume differentiability.
2. **Unseen directions.** Generate 32 normalized Gaussian directions in 48D,
   fixed PCG64 seed 20261116, and their negatives. They are never used to estimate
   the coordinate maps. At every amplitude, predict their full response vectors
   using the 0.001 map. Report aggregate relative L2 error (sum of squared errors
   divided by sum of squared measured responses, then square root), alongside
   per-direction errors and absolute signal norms. Ratios below a 1e-9 measured
   signal norm are unresolved, not evidence of precision. At 0.001, a practical
   target is <=5% error at horizon 1 in every endpoint; report all failures.
3. **Controls.** Compare the same predictions with zero response, a fixed seeded
   permutation of input columns, and the known input wiring scaled by its
   least-squares scalar fitted only to the calibration map. This last control is
   intentionally advantaged: it knows the best overall local sensitivity but not
   coordinate-specific gating. It applies only at horizon 1.
4. **Map changes.** From each endpoint follow its frozen-input/control/noise
   continuation and sample offsets 0, 4, 8, 12, 16, 20, 24, 28. Only offset 0 is a
   saved historical endpoint; the others are simulated states. At 0.001 estimate
   each map and test the same held-out directions, comparing its own map against
   the mean of the other seven maps from that endpoint. Record forcing phase,
   active/clipped coordinates, and effective singular-spectrum dimension.
   Seek a >=2-fold reduction in pooled prediction error versus that mean, without
   treating these nearby states as independent observations.
5. **A bespoke question.** Compare the true starting state with a zero-state
   counterfactual at identical input, controls, phase and future noise. Choose the
   unit input maximizing the difference between their 0.001 response maps (top
   right singular vector of their difference). Test both signs at 0.001 and 0.01.
   Compare measured *differences of baseline-subtracted responses* with predicted
   differences and with the 32 random directions at equal energy. This tests a
   question-directed vector, not the claim that zero is a plausible natural state.
   Report prediction error and gain over the median random direction; <=5% and
   >=2-fold at 0.001 in every endpoint are practical targets, not significance tests.

Analytic immediate response has the form `J = diag(m*a*(1-tanh(z)^2)) B`, where
`B` is fixed authored-input wiring and `m` indicates an unclipped output. Report
how much of each finite response matrix this state/input-dependent row gating
explains. At a clipping boundary the derivative need not exist; finite signed
responses, one-sided disagreement, and scale convergence take precedence.

## Deliverables

A reproducible read-only probe, qualified against native receipts; compact numeric
results and raw arrays; scientific figures; and a dated interpretation separating
measured signal, alternatives, and the next instrument change. No app release or
long run is implied. The existing full-report checkpoint storage issue remains.

## Coordination

Work continues in the clean, previously owned `codex/reservoir-sonar` worktree.
No live-being service, other checkout, or old export is modified. Board publication
is not part of this local numerical run; record pending board payloads at closeout.
