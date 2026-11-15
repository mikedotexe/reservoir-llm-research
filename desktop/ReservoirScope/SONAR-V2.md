# Compact native scanning and model-selected questions

Implementation scope selected November 15, 2026. New sessions use
`compact-scan-v2`; historical `response-scan-v1` contracts and bytes remain intact.

In **My reservoir**, enable continuing inquiry and specific correction feedback,
then **Allow the model to scan copies of its reservoir**. Real probes require the
separate **Also allow real probes along measured scan directions** checkbox,
which starts off. Both capabilities are fixed at session creation. Restoring an
older session does not silently upgrade its protocol.

The **Reservoir response scanner** panel offers a passive observation, a copied
scan and a question selector. Operator-only results never enter model prompts or
authorize its next real probe. The model chooses through its own final NEXT line:

```text
I want to test how the current state changes responsiveness to a small input.
WITHHOLD_RESERVOIR_INPUT=true
NEXT: SCAN_QUESTION state
```

On a later ordinary turn it can choose `NEXT: PROBE_SCAN question positive`,
choose another question, or take no action. Text withholding remains independent.
The saved comparison returns with the explicit alternatives, prediction error,
measured signed contrast, random control and any unresolved/fallback outcome.

`NEXT: SCAN` calibrates 32 coordinate sensitivities with two signed input probes
of norm 0.001 through known wiring. Sixteen separate deterministic unit directions,
each tested with both signs, validate prediction. Both aggregate and worst resolved
relative error must be at most 1%; unresolved signal and poorly conditioned
calibration are explicit outcomes. Failed validation falls back to 96 actual signed
coordinate measurements. A fallback is never relabeled as a validated linear map.
Long candidate curves remain paired measurements. Only compact coefficients and
validation receipts are retained on success; the fallback retains signed vectors.

`NEXT: SCAN_QUESTION state|input|recurrence` asks which input best distinguishes
current response from a stated counterfactual: zero starting state; no held text
vector; or recurrent gain zero. Everything else, including future noise, is shared.
The numerical tool chooses a vector from the difference of the two response maps,
then measures both signs and records prediction versus measured contrast, with
random equal-energy comparisons. This action only experiments on copies. It
returns the stated alternatives and evidence to subsequent ordinary writing.

`NEXT: PROBE_SCAN question positive|negative` selects the most recent resolved
model-selected question direction. It uses the existing separate real-probe
permission and bounds. Application refreshes the forecast and counterfactual at
the actual origin, with current held input and controls. Only the actual paired
immediate displacement is an observed live consequence; the alternative remains
a copied numerical counterfactual. Operator scans never populate model caches.

V2 keeps the last 32 recurrent states for passive views. Saved scan/question
reports bind their origin, model, seed, copied RNG, held input, controls, method
and source history hash. Save/readback/application, retry, withholding, ordinary
versus hourly prompts and exact export/replay retain their existing boundaries.

Qualification includes native algorithm parity, calibration success and forced
clipping fallback, fresh-direction independence, unresolved contrasts, parser
admission by version, bounded actual probes, save/retry/restart and replay,
frontend validation/rendering, historical v1 export replay, native UI and a
measured storage comparison. This is a local application addition, not a new
long model study or a deployment to Astrid or Minime.

## Reading the evidence

The compact map predicts first-step sensitivity. Strongest/weakest candidate
curves are separately measured over 64 copied steps. V2 does not offer v1's
16-step `persistent` selection. A stale cached vector is not a current prediction;
every real application refreshes its copied forecast with the newly applied
held text and effective controls.

A failed compact map retains all positive/negative coordinate responses, including
asymmetry at clipping boundaries. Its central difference is only a directional
summary. Question vectors selected from such a summary are tested directly;
their comparison is labeled unvalidated when its linear prediction fails.
An unresolved contrast cannot authorize a question-direction probe.

The row gains assume this instrument's known fixed input wiring. Calibration
and validation use distinct deterministic generators; copies share recurrent
noise. This is not a black-box identification or a guarantee under unmatched
live noise, other amplitudes or future states. Global topology remains open.

The CLI `--scan-sustained DIRECTORY` still verifies the entire export first.
For v2 it returns a compact report and a reconstructed matrix; for older sessions
it retains the original v1 JSON shape. Exact export/replay regenerates applied
scans/questions under their saved version. Neither CLI route calls a model.
