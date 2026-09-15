# Reservoir 3D: metric contract and leak dynamics

Source review on September 6, 2026 (Pacific). This is an accuracy contract for the
steward-side viewer, using its bounded historical capture and read-only source
inspection. It does not establish a deployed implementation revision. The
[capture probe](../probes/reservoir_3d_capture.py) records source hashes and
locators in [data.json](../visualizations/reservoir-3d/data.json).

## What the available geometry can say

| Visual | Defensible encoding | What it cannot establish |
|---|---|---|
| Concentric filled sphere | `r / R = (fill_pct / 100)^(1/3)`, so the displayed volume fraction equals the recorded estimator percentage. Apply this same transform to shelf, target and rails. | Literal occupied neuronal volume, memory capacity, or distance to a stability boundary. |
| Three-axis spectral shape | Each semiaxis is proportional to the square root of one recorded sensory-field Rayleigh-quotient slot, with one fixed scale across the whole replay. Preserve slot identity. | A measured covariance ellipsoid, principal-axis orientation, or three tracked physical eigenmodes. |
| Native ESN radius | `sqrt(sum(x_i²) / N)`; the current source clips each state coordinate to `[-1,1]`. A radial scalar indicator can show this value with an explicitly named scale. | A neuron layout or a recurrent spectral radius. |
| Fill velocity | Backward difference of consecutive recorded fill percentages divided by their actual timestamp interval, in percentage points per second. | The engine's internal smoothed slope or an instantaneous derivative. |

The historical sequence contains 507 exact `(session_id, timestamp)` pairs over
09:09:01.158–09:28:59.673 Pacific on September 6. Only three sensory spectral
columns are retained. A matching database timestamp does not establish that all
estimators' internal updates happened simultaneously.

### The recorded λ labels are estimates in column order

Current source performs one block-matrix multiplication, Gram–Schmidt
orthonormalization, and a Rayleigh quotient per resulting column. It neither
diagonalizes the projected matrix nor sorts the quotient list before assigning
`lambda1`, `lambda2`, and `lambda3` to the first three slots. See
[orchestration.rs:2399](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2399>),
[orchestration.rs:2461](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2461>),
[orchestration.rs:2471](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2471>),
and [orchestration.rs:2529](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2529>).
The quotient is implemented in
[gpu.rs:176](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/gpu.rs:176>).

In the captured sequence, only 431 of 507 triples are in descending order; slot
3 exceeds slot 1 in 38 observations. This is compatible with unconverged tracking
of a changing matrix. It does not by itself measure estimation error. Calling
these the **top three eigenvalues** is stronger than the captured evidence.

For unit directions `q_i`, the recorded quotient estimates `q_iᵀ A q_i`. The
off-diagonal terms `q_iᵀ A q_j` are not retained. Even if all direction vectors
were available, a diagonal three-axis construction would not reproduce the full
projected field shape unless those off-diagonal terms vanished. Recommended
label: **“Spectral magnitudes · three recorded direction estimates.”** A useful
detail is **“Square-root scale; schematic axes; directions and cross terms were
not captured.”** Keep the raw `λ₁/λ₂/λ₃` column labels inspectable for provenance.

The native ESN matrix called covariance is an uncentered EWMA second moment:
`C ← ρC + (1−ρ)xxᵀ`; its kernel does not subtract a running mean. It also has a
spectral-damping path. See
[esn.metal:14](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/shaders/esn.metal:14>)
and [esn.metal:41](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/shaders/esn.metal:41>).
The independent sensory-field matrix uses outer-product updates, trace
rescaling, and controller-dependent scaffold mixing; see
[spectral_math.rs:8](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/spectral_math.rs:8>)
and [rescue_scaffold.rs:1334](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/rescue_scaffold.rs:1334>).
Therefore the displayed square roots are field magnitudes, not automatically
empirical standard deviations or confidence-region axes.

### Fill and reference comfort zones

The fill estimator thresholds the sampled spectrum using running statistics,
counts active sampled directions, applies a floor, then smooths and decays the
result. Its normal and fixed-survival policies differ:
[eigenfill.rs:129](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/spectral/eigenfill.rs:129>).
The source also adds a sensory/geometric bias outside stable-core:
[orchestration.rs:2552](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2552>).
Since the historical mode is absent, the viewer should say **recorded system fill
percentage, derived from the sensory-spectrum estimator** rather than asserting
that each historical value is an unmodified active-rank fraction. It cannot
reconstruct fill from the three saved columns alone. The source's “scale
invariant” comment is not a verified property of every threshold policy.

The 58–72% shelf, 68% target, and 74/78% rails are source-defined reference
markers. Stage selection has hysteresis: hold enters at 60% and releases at 58%;
elevated enters at 72% and releases at 71.5%. This is a configured comfort
reference, not a measured subjective comfort score. Showing the bands does not
establish the historical controller stage. See
[rescue_overfill.rs:42](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/rescue_overfill.rs:42>)
and [rescue_overfill.rs:102](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/rescue_overfill.rs:102>).

## PI fields and clocks

The separately captured health snapshot is not a controller trace for the replay.
Its structural drain PI is separate from the generic gate/filter PI. The ordinary
active structural path is:

```text
error_pp = controller_input_fill_pct − 68
e = clamp(max(error_pp − 4, 0) / 20, 0, 1)
I = clamp(I_previous + e, 0, 1)  if e > 0
I = 0.85 × I_previous          otherwise
P_contribution = 0.55 × e
I_contribution = 0.04 × I
raw_output = clamp(P_contribution + I_contribution, 0, 0.12)
```

The positive error is excess fill. The integral is a dimensionless accumulator
updated per control step; it is **not** an integral in fraction-seconds. Its
recorded field is `integral`. The recorded fill-error field is `error_pct`, in
percentage points, not `error`. Recovery, reentry, and inactive paths differ.
See [rescue_scaffold.rs:1534](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/rescue_scaffold.rs:1534>)
and [rescue_scaffold.rs:1655](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/rescue_scaffold.rs:1655>).

The source calls this PI with `last_fill_pct` before computing the next fill
estimate: [orchestration.rs:2198](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2198>).
In the frozen snapshot, the controller input reconstructed as `target + error`
is 73.03054047%, while snapshot fill is 71.04400635%. This is a difference of
−1.98653412 percentage points between channels, not evidence of an erroneous PI
sign. The derived contributions are `P = 0.02833986`, `I = 0.00206108`, and
clipped sum `0.03040094`. These values are algebraic reconstructions using current
source constants, not logged P/I contributions or proof of the loaded binary.

Drain policy and final scaffold weights follow the raw sum and can override it.
Do not label `P+I` as the applied drain, gate command, or ESN leak. Keep the
snapshot timestamp and its earlier controller-input relationship visible.

## A leak animation we can defend

Minime's native ESN update in the inspected source is:

```text
proposal_t = tanh(W_in [input_t; 1] + W_res x_t)
x_(t+1) = clip((1 − α_t) x_t + α_t proposal_t + noise_t, −1, 1)
```

The code computes the proposal, updates spectral introspection from the previous
state, adapts the leak, mixes old state with the proposal, adds exploration noise,
then clips. See
[esn.rs:2073](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/esn.rs:2073>)
through [esn.rs:2153](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/esn.rs:2153>).

**First animation:** show two labeled vectors or ghost states combining into a
new state: retained previous-state term weighted by `1−α`, new nonlinear proposal
weighted by `α`. Distinguish the noise-and-clipping step. This can use the
recorded α as the measured mixing coefficient while keeping the illustrated
states explicitly schematic. In this capture α ranges from 0.64350188 to
0.66587484 (n=507). A larger α gives the proposal more immediate weight. It is
not a direct drain valve for EigenFill.

If the proposal were frozen, the direct old-state coefficient after k updates
would be `(1−α)^k`. In the actual recurrent system the proposal itself depends
on the old state, so that coefficient is not the total memory-retention curve.
The telemetry cadence is not established as the ESN's individual update cadence;
any illustrative decay is measured in updates unless step timing is captured.

**Second animation, explicitly a linear example:** choose an illustrative fixed
recurrent matrix `W`. In the unsaturated linear approximation, the effective
state-transition eigenvalues are

```text
μ_i(α) = (1 − α) + α λ_i(W).
```

Draw their real and imaginary coordinates on an equatorial disk inside the
floating sphere. Animate α to show each point moving along its affine path from
1 toward its fixed recurrent eigenvalue; a small trajectory can show decay and
rotation. The unit circle represents unit modulus for this fixed linear model.
This is a different quantity from the recorded covariance-field λ values. The
recurrent matrix's own eigenvalues do not change merely because α changes.

For the actual nonlinear plant with input, α, and noise frozen for one step,
the local Jacobian before clipping is

```text
J_t = (1 − α_t) I + α_t diag(1 − proposal_t²) W_res.
```

Clipped output coordinates add a row mask where the clip is differentiable.
The full adaptive system also includes controller and estimator state and their
derivatives; the above is a frozen-control plant Jacobian. The prior-art
[one_step_state_jacobian](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/temporal_jacobian.py:26>)
implements this explicitly scoped calculation.

Actual Jacobian eigenvalues require weights and state/input information absent
from the current capture. Instantaneous eigenvalues alone also miss transient
growth in non-normal systems and effects of multiplying different Jacobians
over time. For a later measured dynamics view, show singular gains of a finite
propagator `J_(t+h−1)…J_t`, using the sibling's composition machinery, together
with its time horizon and frozen-control assumptions. Do not equate a single
inside-the-unit-circle picture with stability of the full live being.

## Reproduce the bounded numerical checks

Run from this research repository; this reads only the captured viewer file:

```python
import json
from pathlib import Path

d = json.loads(Path('visualizations/reservoir-3d/data.json').read_text())
s = d['samples']
c = [row['cascade'] for row in s]
print('n', len(s))
print('descending triples', sum(v[0] >= v[1] >= v[2] for v in c))
print('slot3 > slot1', sum(v[2] > v[0] for v in c))
print('negative values', sum(x < 0 for v in c for x in v))
print('leak range', min(v['esn_leak'] for v in s), max(v['esn_leak'] for v in s))
print('stats', d['stats'])
print('controller derivation', d['controller']['snapshot']['derived'])
```

## Board updates pending

This independent source review belongs with the reservoir-visualization work;
the parent session owns board coordination. Finding: the sensory spectral
columns are unsorted Rayleigh estimates, so a principal-axis covariance
ellipsoid would overstate the current capture. Evidence is the source trace and
the bounded checks above. No live-system change is proposed or performed.
