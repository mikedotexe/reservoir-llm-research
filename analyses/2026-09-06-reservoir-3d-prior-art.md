# Reservoir 3D visualization: local prior art

Observed September 6, 2026 (Pacific), read-only in sibling `../esn-divide`. This is a source review and visualization recommendation, not a live-system result or deployment proposal. Sibling HEAD was `2cb226ef48ac5a40935ead9e4e0230c92d884f5c`; its working tree contained modifications and untracked analysis files. Citations describe the observed working tree, not necessarily that commit. No sibling files or live systems were changed.

## Finding

There is substantial reusable cartography: frozen reference PCA, shared versus local phase portraits, temporal Jacobian modes, time scrubbing, and explicit freshness/control evidence. I did not find an existing rendered 3D sphere. The PCA helper already accepts three components, but the inspected renderers select two and draw ordinary 2D plots or SVG. This absence claim is restricted to the source search below; it does not cover external artifacts or earlier revisions.

| Prior art | What to reuse |
|---|---|
| [FrozenPcaBasis, division_evidence.py:24](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/division_evidence.py:24>) | Fits a centered SVD basis, defaults to three components, and records `fit_source=pre_split_parent_only` and `frozen=true` at lines 48–55. A stable basis prevents camera-like coordinate changes from masquerading as reservoir motion. Its `explained_variance` values are raw component variances (line 32), not fractions; compute a denominator before presenting percentages. |
| [Split phase-space construction, split_phase_space_visualization.py:151](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/split_phase_space_visualization.py:151>) | Fits on pre-split states; transforms later parent/reconstructed/daughter states in that common basis (174–191), while keeping separately fitted local daughter views (193–196). The helper explicitly constructs two components (32–65). |
| [Barbell maps, barbell_phase_space_visualization.py:87](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/barbell_phase_space_visualization.py:87>) | Whole-system and left/bridge/right local projections are distinct. Here the bases are fitted on the captured run, not a preceding reference window. The renderer plots PC1 versus PC2 (499–506). Good precedent for a whole-system map with inspectable subsystem views. |
| [Temporal Jacobian, temporal_jacobian.py:26](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/temporal_jacobian.py:26>) | Computes an analytic state Jacobian with controller settings frozen for the tick; composes across time at 119–128. It decomposes the window-mean propagator into singular gains and state directions (454–498). This provides a future map of dynamical sensitivity, beyond activation variance. |
| [Interactive analysis, division_analysis_visualization.py:245](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/division_analysis_visualization.py:245>) | Shows frozen PCA alongside a frozen temporal causal-mode plane. Time scrubbing ties trajectories, fill, events, influence and mode gains together (493–520). The current trajectory serialization retains only x/y (27–30). These analysis files are untracked in the observed sibling tree. |
| [Flight recorder, division_evidence.py:132](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/division_evidence.py:132>) | Keeps phase-space coordinates, sensory-field metrics, freshness, actuator saturation and reservoir health in separate fields. Preserve this separation in the new visual. |

The temporal analysis explicitly excludes adaptive-controller derivatives and labels semantic probes as decoded associations (temporal_jacobian.py:967–980). It cannot establish the full closed-loop PI response or assign semantic meaning to a visual region by itself.

## What radius can mean

These quantities must have separate names in the visual:

- **Recurrent spectral radius:** a property of the recurrent weight matrix. The sibling initializes weights using a maximum absolute row-sum bound (`core.py:245–250`); its configuration target is not a measurement of the exact resulting spectral radius.
- **Reservoir covariance λ₁:** the top Rayleigh-quotient estimate of the running state second-moment matrix (`core.py:92–113`). The implementation calls it covariance but does not subtract a mean in this update. It is different from the weight matrix's spectral radius.
- **Geometric radius:** RMS activation, `sqrt(mean(x²))`; `geom_rel` divides it by an evolving baseline (`core.py:358–378`). This already gives a scalar distance from the zero state, though it is not a spectral distance.
- **Projected radius:** the norm of a point in a frozen PCA map measures retained activation displacement from its reference mean. It is a projection, and discarded dimensions remain invisible.
- **EigenFill:** the separate sensory-field estimator. Its running threshold counts active modes and smooths/leaks their fraction (`sensory_field.py:79–115`). The source explicitly distinguishes reservoir-node space from the 512D sensory field (`sensory_field.py:3–11`). It is neither a Euclidean volume nor the proportion of firing reservoir neurons.

Sources: [core.py:92](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/core.py:92>), [core.py:245](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/core.py:245>), [core.py:358](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/core.py:358>), [sensory_field.py:3](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/sensory_field.py:3>), [sensory_field.py:79](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/sensory_field.py:79>).

No canonical scalar named “spectral distance” was found in this inspected source. A sphere can honestly encode a named normalized spectral quantity, but its radial mapping and reference boundary need an explicit definition. Do not make one radius simultaneously mean spectral distance, geometric activation norm, and fill.

## Recommended first implementation

Build the requested floating sphere as a **telemetry instrument**, with fill animated inside it, a time cursor, controller shelf/target/rails, and distinct scalar spectral and geometric indicators. Label any decorative particles as schematic; scalar eigenvalues cannot reconstruct neuron positions or activation trajectories.

For a concentric filling sphere, use `inner_radius / outer_radius = (fill / 100)^(1/3)` so displayed volume matches the percentage. For a horizontal liquid surface, solve the spherical-cap volume instead; linear height is not linear volume. Both are deliberate visual encodings of an estimator, not physical claims about occupied space. Keep target and comfort markers in the same volume mapping. A separate radius selector can explore geometric ratio or a specifically defined spectral ratio without silently changing the meaning of fill.

Show PI memory and action distinctly: instantaneous error/P contribution, accumulated error/I contribution, total command, admission gate, filter blend, actuator saturation, and geometric brake. The sibling code demonstrates conditional integration and decay under saturation, integrator leakage, bounded actuator increments, and hysteresis ([regulator.py:161](</Volumes/M3 Volya._smb._tcp.local/other/esn-divide/src/esn_divide/regulator.py:161>) through 238). Use captured controller values when available; mark unavailable fields unknown. Do not reconstruct historical I terms from fill alone or substitute these harness defaults for current Minime configuration.

Next, when a bounded capture of actual reservoir vectors becomes available, add a second **state-map view** using three frozen PCA components, report the retained variance, and attach the fill/controller instrument to the same timestamps. A temporal sensitivity layer can later follow the sibling Jacobian approach, with its fixed-control scope visible. This makes the first sphere useful immediately while keeping a clear path to measured internals.

## Reproducible source search

Run read-only from `../esn-divide`:

```sh
git rev-parse HEAD
git status --short
rg --files src tests
rg -n -i 'cartograph|three[.-]?js|scatter3d|plotly|3d|spectral.distance|radial|sphere|embedding' --glob '!*.lock' --glob '!*.svg' --glob '!*.json' --glob '!*.html' --glob '!*.csv' .
rg -n -i 'spectral distance|cartograph|3d|three\.js|webgl|sphere|projection="3d"|mplot3d|scatter3d' --hidden -g '!.git/**' -g '!.venv/**' -g '!*.svg' -g '!*.json' -g '!*.lock' -g '!*.csv' .
```

The final search returned only `phase3d_silent` experiment labels and CSS color substrings. The positive findings above came from inspecting the visualization, evidence, core, sensory-field and controller modules, not merely from the absence of a keyword.

## Same-session extension: actual reservoir-state geometry recovered

Following Mike's request to make this an ambitious and accurate view of internals, we located an existing low-cadence Minime capacity dump. A bounded, read-only capture at **2026-09-07 05:11:52 UTC / September 6 22:11:52 Pacific** contains **1,024 successful ESN steps × 128 reservoir nodes**. The [export](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/visualizations/reservoir-3d/state-geometry.json>) retains hashes, original metadata, paths to exact raw snapshots, all 128 centered covariance eigenvalues, the first three signed eigenvectors, all projected scores, and per-row projection residuals. This supersedes the earlier uncertainty about whether actual state vectors are presently available.

The [probe](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/probes/reservoir_3d_state_geometry.py>) fits one centered sample covariance over the captured window, with denominator `n−1 = 1023`, and freezes that basis for playback. The first three components account for **8.9384%, 3.5301%, and 1.8839%**, totaling **14.3524%** of that window's temporal variance; **85.6476% lies outside the displayed subspace**. The covariance participation ratio is **60.7574**, a description of this window's variation, not a measured computational or memory capacity. Per-row residual distance must remain visible in the 3D view.

The sphere's proposed state-map reference radius is the maximum full 128D distance from this window's mean: **3.19193 activation units**. Projected points divide by that one constant. This is an empirical enclosing envelope for the capture, not a recurrent spectral radius, stability limit, or fill boundary. The centered window spectrum is also different from Minime's live uncentered EWMA covariance spectrum.

The producer appends successful ESN states to a ring and removes the oldest row when full, establishing oldest-to-newest order ([orchestration.rs:1432](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:1432>)). It writes binary states, secondary covariance and metadata with separate atomic renames ([orchestration.rs:5793](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:5793>)). Identical state/metadata bytes and file statistics across bracketing reads, plus state-write time not newer than metadata, passed on the first attempt. Since metadata lacks a state hash or common generation identifier, a transactional pair cannot be proven. This limitation is retained in the export.

Metadata `t_ms=552009907` is elapsed processing-loop time at the dump check; it supplies no session identifier or row timestamps. Rows arise from admitted batches and successful steps; the current source's 331 ms loop sleep is not a measured row interval ([orchestration.rs:1048](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:1048>), [orchestration.rs:1257](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:1257>)). No alignment to the morning fill sample or contemporaneous leak/PI telemetry is asserted.

Reproduction from retained inputs, without any live access:

```sh
/opt/homebrew/bin/python3.14 probes/reservoir_3d_state_geometry.py --replay visualizations/reservoir-3d/state-geometry.json
/opt/homebrew/bin/python3.14 -m unittest discover -s tests -p 'test_reservoir_3d_state_geometry.py' -v
```

Replay reproduced the same result. Four tests cover an analytically known spectrum and variance normalization, rotation invariance, reconstruction residuals, invalid/non-finite inputs, and exact snapshot hashes. On the measured capture, component orthogonality error was below `1.6e-15`, the squared-distance decomposition error below `7.8e-15`, and all 128 covariance eigenvalues were positive before any roundoff clipping. Source-state SHA-256: `09ea4db8212809085aa2e07a040975f3095d7ef79d06eb8ba7404cc2424e282f`.
