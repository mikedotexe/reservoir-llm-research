# Spectral motion and a route from curiosity to experiment

November 15, 2026. Selected by Mike's request to understand the recurrent
“topology” language while implementing numerical arguments for copied tests.
This is a scoped Gemma4 case and an instrument change, not a frequency estimate
or a finding about Astrid or Minime. Their live systems were not accessed.

## Material and channel

Source: local Gemma4 `gemma4:12b` scanner session
`sustained-1794783602602-1`, version 0.50.0. The selected journal is
`journal-150-5-38919ac1a91e9eb4f98cbe58a3118f1ba11499a28e04f6f1fee2f866fb81f5ed.json`.
Selection was exploratory: this entry explicitly relates sensory fill, a prior
clipped pulse, and a “packed” state. It is not representative sampling.
The private packet at
`research/outputs/parameterized-experiments-20261115/spectral-explainer/`
retains the full journal/prompt, first 300 advanced frames, captured manifest and
checkpoint, chain-link hashes and derived data. The complete captured chain
contained 151 links. SHA/sequence checks passed; this particular capture was not
independently replayed by the native engine. No source writes or provider calls.

The entry says the 1.77095888 endpoint difference “confirms a state of high
structural inertia” and infers that high fill preserves “volume” while clipping
caps “height.” It then proposes a perpendicular pulse to test channel independence.
These are model-authored interpretations, not measurement definitions.

The actual current-observation prompt at step 150 supplied:

- recurrent RMS 0.55436905;
- **separate sensory fill** 71.28076279%;
- recurrent endpoint distance from step 120, 1.77095888;
- an explicit warning that endpoint distance is not an isolated action effect,
  speed or proof of stasis.

The broader prompt also carried recurrent coordinates, previous writing and
available action/scan evidence. It did not contain either of the plotted full
spectral time series or the fixed PCA projection. Words such as “spectral” in
recalled prose must not be counted as delivery of numerical spectra. The new
analyst visualization is not inserted into any model prompt.

The clipping interpretation has a numerical anchor in the PULSE operation.
The attribution of a later endpoint distance to retained pulse energy does not:
that interval also includes forcing, held input, recurrence and noise. Sensory
fill belongs to a separate input-driven field. In `math.rs`, that field normalizes
its projected input and repeatedly normalizes its retained second-moment matrix's
trace. Its spectral mass is therefore not a conserved physical energy or a direct
measurement of recurrent-state volume. The new experiments make a matched
no-probe comparison available for investigating these ideas.

## A first visual map

Reproduction: `probes/visualize_reservoir_spectra.py SESSION NEW_OUTPUT` with NumPy.
All 300 recurrent state vectors are retained. The fixed two-axis projection is
fitted to all 300 states and accounts for 49.53688494% of overall variance. This
is a retrospective analyst view, including states later than the selected journal.
A moving 32-state window supplies a separate centered sample covariance at each
of 269 boundaries, steps 32–300. Native sensory eigenvalues are plotted separately.
The covariance trace/variance identity and invariance of eigenvalues under an
orthogonal rotation pass numerical checks.

At step 150, the last 32 recurrent states (119–150) put **95.43487158%** of their
variance in their leading three directions. This is measurable local concentration
of motion. It does not identify semantic regions, holes, global connectivity,
attractor dimension or phenomenological experience. The corresponding top-three
share of the separate sensory spectrum is **45.31625514%**. They have different
inputs, estimators and windows; their percentages are not interchangeable.

Useful image: each recurrent state is a point in 32 dimensions; successive points
form a path. Covariance describes the spread of a selected cloud of points.
Its eigenvalues give squared spread along principal axes; the eigenvectors tell
which directions those axes point. Eigenvalues alone omit axis orientation and
path order. A projection can hide motion or create apparent crossings. A probe
asks a different question: how does this point's subsequent path change after a
specific input, relative to its own unchanged comparison?

The inline visualization uses a step slider, a fixed projection and a spectrum
selector. The first eight modes appear individually, and modes 9–32 are explicitly
combined. Spectral bars are normalized shares; raw numerators and totals remain
in tooltips. Twelve chart configurations across both selectors and the slider's
endpoints/default were validated. Source data and calculation checks are retained;
that check does not establish browser rendering.

## Implementation and what remains to learn

The 0.51.0 opt-in instrument is specified in
[EXPERIMENTS.md](../desktop/ReservoirScope/EXPERIMENTS.md). A model can set an
explicit vector, measured direction or weighted mixture; choose impulse/train/
oscillation timing; vary held input, leak, recurrence or saved state; request
selected response times/coordinates; and name a follow-up. Every condition has
its own matched-forcing/noise baseline. Aliases resolve to exact IDs in saved
arguments. A real impulse is a separately authorized action with a current-origin
bound and forecast, never implicit application of copied controls.

This implements observation → experiment → identified evidence → another test.
It does **not** establish that a model can reliably exploit the route. The next
behavioral test should be short and should assess evidence use before adding
more tools: can each model distinguish no excitation/no contrast from a finding,
correct a pulse-persistence attribution, and choose a follow-up that separates
its own alternatives? Preserve the exact prompt/result/action chain. Compare a
matched arm without returned results and a scrambled-result arm, with repeats,
before attributing improved reasoning to numerical feedback. No such model study
was run during this implementation.

The separate three-model 0.50.0 cohort keeps its original settings and processes.
Qualification evidence and limitations are in
[the 0.51.0 release record](../desktop/ReservoirScope/RELEASE-0.51.0.md).

## Board updates pending

The Hold Shelf ArtifactData tools were unavailable. Pending finding: a selected
Gemma “packed topology” passage combines separate sensory fill with recurrent
endpoint/action evidence; no full spectral time plot was supplied. Pending change:
parameterized copied experiments with immutable follow-up references. Pending
question: does returned experimental evidence change the model's next inquiry?
These are recorded locally; no board publication is claimed.
