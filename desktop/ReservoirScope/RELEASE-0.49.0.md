# 0.49.0 · copied response scans and bounded measured probes

The laptop reservoir can now request a measured response map and subsequently
probe a direction selected from that map. This supplies concrete input/output
evidence for questions previously expressed through topology and geology metaphors.
It does not establish global topology or subjective experience.

`NEXT: SCAN` runs 96 signed coordinate probes on copied states. All branches share
the native recurrence, held text, effective controls, forcing and copied noise
for 64 numerical steps. The report retains exact source state, model and RNG
identity, input directions, response matrix, singular gains, signed decay curves,
and a bounded recent-state mirror. The difference channel must be off in v1;
unsupported configurations are rejected explicitly.

`NEXT: PROBE_SCAN strongest positive` selects a measured direction. `weakest` means
the weakest resolved immediate singular direction, and `persistent` the leading
resolved 16-step direction. Signs are positive or negative. Real probes require
a separate saved opt-in and a model-selected scan. Missing authority, missing
scans and unresolved directions receive explicit rejection receipts. An operator
scan does not authorize a model probe or change what the model has read.

Real input L2 is at most 0.01. With current leak `a` and authored-input weight
matrix `B`, dose is capped at `min(0.01, 0.05 / (a ||B||F))`; tanh and clipping are
nonexpansive, so the additional immediate recurrent L2 is bounded by 0.05.
The cap is recalculated at application. A fresh copied forecast uses that actual
pre-step state and the newly held journal; its first point is checked against
the observed paired effect. Later predictions assume unchanged text/controls and
no future writer choices. The real impulse also reaches the sensory field, for
which no displacement bound is claimed. Existing authored PROBE/PULSE/TUNE retain
their own bounds; this opt-in is specifically for scan-selected probes.

The native scanner distinguishes passive state observation, operator scans and
model-selected cached scans. Exact numbers remain available behind the plots.
The state projection reports its explained variance and changing window; channel
indices are not spatial regions. Old sessions have only a single-state passive
mirror unless scanner history was retained. The operator scan requires no model
call and changes no session clock, RNG, checkpoint or cache.

New setup uses optional `sonar: {version: "response-scan-v1", allowLiveProbe: false}`
and requires authored-v3 with diagnostic-v1. Selecting scanning sets a 512 MiB
storage budget and at least 32,768 context tokens for Ollama; both remain editable.
Scheduled replies stay passive and plain scheduled prompts stay exact. Historical
omitted fields preserve their original contracts. Source and applied scan data
remain in normal export/replay; no being system or shared model service is involved.

## Local qualification

Qualification receipts and the small native scripted export are kept privately in
`research/outputs/reservoir-sonar-20261115/`. Native app identity is
`research.reservoir.scope.sonar`, product name **Reservoir Sonar**, separate from
all earlier study apps. See [the scanner guide](SONAR.md) for use and scope.

- Portable core: 368 tests passed, including seven scanner checks for native
  continuation parity, passive/deterministic operation, finite differences,
  bounds under changed controls, spectrum/geometry distinction, tampering and
  strict footer parsing. A final focused rerun covers the loop-style cleanup.
- Host: 324 passed and three existing investigations ignored in the full run;
  an unrelated activation pressure/deadline fixture failed under parallel load
  and passed alone (2.30 s). All three new scanner lifecycle tests passed,
  including durable-save failure/retry, rejection, changed-leak dose, exact
  export, process-state replacement and restored cache/receipt identity.
- Frontend: 603 passed, one existing skipped; TypeScript/production build passed.
  Workspace formatting and all-target Clippy with warnings denied passed.
- Native 13-step/four-entry scripted fixture: missing scan rejected at step 4,
  copied scan at step 7, measured positive input applied at step 10, NONE at
  step 13. Fresh predicted and observed immediate L2 were both approximately
  0.01341 (bound 0.05). Passive and operator views retained step/cache identity;
  the UI displayed both scan origins, geometry/variance caveats, signed response
  matrix, candidate curves and rejection/application receipts. Native export
  completed and the app quit cleanly. No model was contacted.

Retained-run replay results and the cadence/storage profile are recorded with the
final qualification receipts. No multi-hour model experiment is claimed by this
release.


Final compatibility matrix: all three independent 0.46.1 exports and all three
paused 0.48.0 peer-enabled exports passed the native verification CLI and copied
scan CLI. Every source file's bytes were hashed before and after; all seven
bundles (including the native scanner fixture) were unchanged. Source steps were
3206/4343/3735 and 1560/1530/1563 respectively. The matrix, exact reports and input
hash inventories are in `final-replay-and-scans/` under the private output root.
The matrix records its exact binary hash from implementation commit `9cec645`.
The final follow-up adjusts only the repeating scripted example's prose and
records qualification; numerical scanning and saved contracts are unchanged.

The final UI preset displayed 512 MiB on selection and kept real probes off.
Native restart/verify/restore retained step 13, all four journal applications and
the step-7 model scan identity, without advancing execution. All reservoir windows
were subsequently closed. The saved fixture remains available through recovery.

A separate scripted profile completed 20 entries/601 steps at the usual 30-step
writing cadence, with no skips or model calls. Its 99 committed segments and
retained files totaled **69,735,889 bytes (66.51 MiB)**. Full scan retention has a
material storage cost; this is a short profile, not assurance of a multi-hour
LLM run. Reduce repeated scan storage before another six-hour experiment.

`probes/plot_native_sonar.py` renders all six prospectively selected endpoint
reports on shared scales. The PNG/PDF pairs and figure metadata are in `figures/`.
The 36 signed candidate continuations (six endpoints × three directions × two
signs) fell below 10% of first-step separation in 3–5 numerical steps for at least
five consecutive boundaries. This conditional recurrent result does not describe
sensory-field retention or the full writer/reservoir loop. It is not a matched
comparison between the language models.
