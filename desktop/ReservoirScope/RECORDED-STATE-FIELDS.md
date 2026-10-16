# Recorded state fields and spectrum

In **Observatory → 128-node replay**, choose a surface field to inspect another
view of the same recorded row. The raw signed activation stays visible beside
the selected field value. The coordinate table preserves exact values; the
surface uses fixed display ranges so changing rows does not rescale them.

This guide describes the 0.22 implementation contract. It does not establish
package, native UI, resource-use or cross-platform qualification.

## Field choices

Let `x` be the recorded 128-coordinate state, `μ` the capture mean, and `c = x − μ`.
For retained component `vᵢ`, its score is `sᵢ = vᵢ · c`. For selected modes `S`,
the reconstruction is `r = Σᵢ∈S sᵢvᵢ`.

| Field | Exact value | Fixed display range |
|---|---|---|
| Signed activation | `x` | −1 to +1 |
| Activation magnitude | `abs(x)` coordinate by coordinate | 0 to 1 |
| Deviation from capture mean | `c = x − μ` | −2 to +2 |
| Selected-mode reconstruction | `r`, without adding the mean | −2 to +2 |
| Residual after selected modes | `c − r` | −2 to +2 |

Reconstruction and residual offer four choices: PC1, PC2, PC3, or all three
captured modes. These are the only retained basis vectors. An omitted component
is not automatically noise, a prediction error or a causal effect. No field is
a physical map of neuron positions or connectivity.

Rust derives these vectors from the original little-endian Float32 activations,
promoted exactly to Float64, and the retained mean and basis. Its centering,
ordered dot products, sorted unique mode selection and reconstruction follow
the native [`StateSurfaceMath.field`](../../native/ReservoirScope/Sources/ReservoirScope/StateSurface.swift)
arithmetic. The frontend selects backend vectors; it does not refit PCA or
reconstruct fields independently. Out-of-range counts describe drawing limits:
color and relief saturate, while exact coordinates remain unclipped.

## Three different quantities

**The state capture spectrum** is the full set of 128 centered sample-covariance
eigenvalues retained for all 1,024 rows. Its denominator is `rows − 1` (1,023).
It is fixed across replay, with a zero-based linear display scale. The first
three modes have retained basis vectors; the remaining 125 have eigenvalues
and variance fractions only. The closed exact table includes all values,
retained/omitted fractions, fit scope and geometry source identity.

**A selected row's squared deviation** is `Σ cⱼ²`. The row disclosure also gives
`Σ rⱼ²` and `Σ (cⱼ − rⱼ)²`; the displayed reconstructed percentage divides the
first by `Σ cⱼ²`, and is unavailable when that denominator is zero. This row
fraction differs from the first three modes' share of variance across the whole
capture. Recomputed scores and energies are labeled separately from the
historical geometry file's retained PC coordinates and RMS metrics.

**Sensory history** is a separate recording. Its three stored Rayleigh direction
estimates and fill statistic are neither this 128-mode state spectrum nor a
paired measurement for a selected state row. The state spectrum is also not
live covariance, recurrent-weight eigenvalues, or evidence of a stability or
capacity boundary.

## Navigation, provenance and rendering

The surface, exact coordinates and [retained trajectory](RECORDED-TRAJECTORY.md)
share one selected ordinal row. Choosing a field or mode changes its view;
it does not advance a simulation. Field, reconstruction-mode and trajectory-axis
choices remain selected when switching Observatory tracks or leaving and
returning within the current app session. This is not persistence across an app
restart. Manual row selection pauses playback; stale reads cannot replace the
last accepted row.

The backend checks packaged resource hashes, dimensions and reference metadata.
The reference was fitted retrospectively to the complete capture, not online at
each row. Capture time does not supply per-row timestamps, measured speed or
paired fill. Historical source paths are provenance labels, never live inputs.

The field controls reuse the existing state surface. Spectrum and trajectory
use SVG, adding no WebGL context or continuous rendering timer. Exact-value
mode keeps their charts and tables available without 3D. These implementation
choices alone do not demonstrate GPU or energy savings.
