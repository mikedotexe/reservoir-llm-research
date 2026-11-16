# Parameterized reservoir experiments

Selected November 15, 2026. Implementation contract for a new, opt-in
`experiments-v3` scanner session. Existing v1/v2 sessions keep their contracts.
The current three model runs are evidence sources, not upgrade targets.

`NEXT: EXPERIMENT <one JSON object>` ties a question to numerical arguments.
The experiment uses the requesting turn's state **before this entry's SEND or
WITHHOLD**, or an explicitly referenced retained experiment origin. It runs only
copied recurrence. Every condition and waveform has its own no-probe baseline
with the same forcing and noise; future writing and sensory evolution are not
simulated. Question/name fields are inert provenance, never executable prose.

Bounded customization: one or two conditions; custom vectors, cached measured
directions, prior experiment directions and weighted mixtures; one to three
amplitudes in [0, 0.01]; either/both signs; impulse, pulse train or oscillation;
at most 64 numerical steps and eight returned time points. Conditions can vary
held input, leak, recurrent gain and starting state. References resolve to
immutable result identities, with explicit rejection when unavailable. The last
four results are retained in the model's experiment ledger; original persisted
checkpoints/events retain earlier evidence. Named follow-ups preserve a parent ID.

Returned evidence separates execution, excitation and contrast. It includes
baseline-subtracted response curves, selected recurrent coordinates, response
alignment, peak/return summaries, signed asymmetry and amplitude scaling error.
The latter compares measured responses with the smallest nonzero amplitude in
that sweep, not an assumed globally valid linear map. Identical conditions and
zero stimuli are explicit outcomes. No automatic assertion that a hypothesis
was proved. The model gets a compact result in the next ordinary prompt.

`NEXT: PROBE_EXPERIMENT <JSON>` can select a retained, measured impulse direction,
amplitude and sign for one real step. It requires the existing real-probe opt-in,
an amplitude/sign measured in that experiment, and a refreshed application-time
bound/forecast. The source must be an impulse experiment; pulse trains and
oscillations are copied experiments only in this version. An excessive dose is
rejected rather than silently scaled. A real probe changes recurrent and sensory
input. Only its immediate paired recurrent effect is observed; its future curve
remains a conditional copied prediction. Counterfactual settings never become
live TUNE operations implicitly.

Qualification before release: native numerical parity and matched baselines;
state-origin timing across SEND/WITHHOLD; deterministic reference resolution;
degenerate contrasts; waveform and amplitude behavior; bounded cost; parser and
version rejection; live authority and fresh forecast; checkpoint tampering,
retry/recovery and exact export replay; frontend validation/rendering; historical
bundle replay; a scripted native run. Later model competence is a separate test.

Companion explanation will distinguish sensory-field spectra, recurrent-state
trajectory covariance and intervention response. Spectral concentration alone
does not identify a global topology, semantic region or a language model's
private activations. Plotted recorded trajectories will be labeled by source,
time window and what was actually supplied to the model.

A minimal test after a successful `SCAN` can be authored as one final line:

```text
NEXT: EXPERIMENT {"name":"held-or-quiet","question":"Does held text change sensitivity along this direction?","conditions":[{"label":"held"},{"label":"quiet","heldInputScale":0}],"probe":{"direction":{"kind":"scan","id":"latest","direction":"strongest"},"amplitudes":[0.001,0.003]}}
```

A follow-up explicitly reuses the origin and direction while narrowing amplitude:

```text
NEXT: EXPERIMENT {"name":"between-strengths","followUpOf":"latest","origin":{"kind":"experiment","id":"latest"},"conditions":[{"label":"held"},{"label":"quiet","heldInputScale":0}],"probe":{"direction":{"kind":"experiment","id":"latest"},"amplitudes":[0.0015,0.002]}}
```

The final action line is at most 4096 UTF-8 bytes. Defaults are materialized in
saved requests, and each `latest` becomes its exact reference ID. The raw journal
retains the original authored request. No experimental controls or waveforms are
silently inherited from an earlier result. Result names are labels; references
use IDs. The ledger is limited to four results. Older prompt entries have request
and outcome summaries; the latest result includes response arrays. The native
panel retains full details for every result still in the ledger.
