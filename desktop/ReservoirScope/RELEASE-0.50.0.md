# 0.50.0 · validated compact scans and model-selected questions

The first scanner measured every input coordinate at every sampled horizon and
retained a large report. New compact-scanner sessions now calibrate first-step
response using known wiring and two signed inputs, check it against 32 fresh signed
inputs, and retain measured coordinate responses if validation fails. The model
can choose a numerical comparison and later apply its measured question vector.

The versioned contract is `compact-scan-v2`. Old `response-scan-v1` serialization,
prompts, parsing and replay remain frozen. New optional cache/receipt fields are
omitted for historical sessions. The application version is 0.50.0 throughout
the package, lockfiles and native bundle configuration.

## Resulting behavior

- `NEXT: SCAN` uses input norm 0.001 for two calibration branches. Sixteen fresh
  directions, each measured with both signs, must pass both pooled and maximum
  prediction error <=1%. Unresolved response or calibration is explicit. Failure
  records all 96 signed coordinate responses and labels the resulting central
  summary as an unvalidated predictor. Candidate curves remain actual paired
  copied measurements. Successful cached reports retain coefficients and
  validation receipts instead of dense coordinate/horizon arrays.
- `NEXT: SCAN_QUESTION state|input|recurrence` compares current response with zero
  starting state, no held input, or zero recurrent gain, respectively. Other
  conditions and future noise are shared. The numerical tool chooses a direction
  from the difference of the two local maps, then measures both signs and compares
  against equal-energy random inputs. The explicit alternatives, source IDs,
  error and measured contrast return in subsequent ordinary prompts. Unresolved
  contrasts retain no usable direction. The action itself adds no numerical input.
- `NEXT: PROBE_SCAN question positive|negative` uses the most recent resolved
  model-selected question. It requires the separate saved real-probe permission.
  Application refreshes actual/counterfactual predictions with current input and
  controls; input L2 <=0.01 and additional immediate recurrent L2 <=0.05 remain
  enforced. Only the actual paired effect is observed live. The alternative and
  future trajectory remain copied predictions. The impulse also reaches the
  sensory field, whose displacement has no corresponding 0.05 guarantee.
- New passive history retains 32 recent states. Operator scans/questions remain
  outside model caches and prompts. Hourly replies remain passive. Existing
  save/readback/application authority and explicit retry/recovery remain required.
- The native panel shows validation results, signed fallback, copied alternatives,
  prediction-versus-measurement tables and actual probe receipts. Setup still
  defaults real probes off. The existing 512 MiB quota is retained.

[Use and interpretation](SONAR-V2.md). This is local apparatus work; it is not a
new multi-hour model experiment or a deployment to the live beings.

## Qualification

Private receipts, exports and the preserved native app are in
`research/outputs/reservoir-sonar-native-v2-20261115/`. This is an Apple-silicon
debug bundle with ad-hoc signing, not a notarized distribution. App identity
remains `research.reservoir.scope.sonar` (**Reservoir Sonar**).

- Portable core: **374 passed**, including six new compact/question tests and
  all seven v1 scanner tests. The new tests cover native response agreement,
  deterministic passive scans, independent validation directions, deliberately
  forced clipping fallback, unresolved questions, strict versioned parsing,
  tampering, changed-control dosing and separate real-probe authority.
- Host: **328 passed, three existing ignored**, with no failures in the full
  suite. Three new tests cover missing/unresolved questions, disabled authority,
  save failure/retry, operator isolation, exact export and restored evidence.
- Frontend: **608 passed, one existing skipped**, across 73 files. Five new
  checks cover compact validation/fallback, question alternatives, unresolved
  evidence, source-bound views and versioned receipt rendering.
- TypeScript/production build, native build, workspace formatting and all-target
  Clippy with warnings denied passed.

The native scripted fixture completed **28 steps and nine entries**, exercising
one missing-question rejection, one compact scan, all three question comparisons,
three real question-direction probes and NONE. The scan's 32 fresh signed checks
passed with pooled error **0.02681%** and worst error **0.04089%**. The recorded
immediate probe effects were 0.010262760923218907 (state),
0.007439068993630213 (input) and 0.008953508750262526 (recurrence); each exactly
matched its fresh first-step forecast and stayed below the 0.05 recurrent bound.
The input norm was approximately 0.00426428 in each case. These are scripted
mechanism checks, not evidence of autonomous model use or a global topology.

Native UI inspection confirmed the signed curves, matrix, comparison table,
validation error and actual-versus-counterfactual receipts. An operator state
comparison at step 28 left the model's step-22 recurrence question and step-7
scan unchanged. Export, quit, restart, full verification and paused restoration
retained all nine entries and both cache IDs at step 28. No numerical advancement
or model request occurred during recovery. All reservoir windows were closed.
The exported fixture and separate storage profile also passed the verification
and scan CLIs; before/after source hashes were identical. Arithmetic and prompt
visibility are summarized by `probes/audit_compact_sonar_fixture.py`; complete
native replay is handled separately by `probes/qualify_reservoir_sonar.py`.

A **20-entry, 601-step** scripted profile at the usual 30-step cadence retained
**30,078,839 bytes (28.69 MiB)**, versus **69,735,889 bytes (66.51 MiB)** for v1's
earlier profile. Numeric settings and cadence match, but the v2 script includes
question actions and uses a different cycle. This is a descriptive workload
comparison, not matched experimental arms or a six-hour storage qualification.
History was bounded at 32 samples. Repeated checkpoints and full prompts still
have a material storage cost, and fallback reports are larger than compact ones.

All **seven historical bundles** passed both native verification and copied
scanning: the 0.49.0 native fixture, three independent 0.46.1 exports and three
paused peer-enabled 0.48.0 exports. Every source file retained its before/after
hash. The independent runs replayed through steps 3206/4343/3735; paused peer
runs through 1560/1530/1563. This verifies compatibility, without resuming those
runs or turning the interrupted peer experiment into a completed comparison.
Together with the two new fixtures, all **nine bundles** passed both CLI routes.
The final matrices and exact reports are in `historical-replay/` and `v2-replay/`.

Implementation save point: `537685c` on `codex/reservoir-sonar`. The tested binary
SHA-256 is `6b5e7de0d4c132058aec9ef9d57ad2472aceaf0b0360ab34a16689acffe49956`.
The preserved `app/Reservoir Sonar.app` matches the built bundle file for file;
its signature verification passed. Build receipt, test logs, native UI record,
fixture audits and file hashes accompany the private evidence. Work is local;
no new multi-hour model experiment or live-being deployment was started.
