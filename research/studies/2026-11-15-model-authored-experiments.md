# Model-authored experiments in three local reservoirs

November 15, 2026. Mike authorized stopping the compact-scanner cohort and
starting fresh Gemma4, GLM and Mistral sessions with the qualified 0.51.0 code.
After startup verification, leave them running and return to UI work; review
their behavior later. No endpoint or continuous monitoring was requested.

## Configuration before dispatch

Source checkpoint: `2e19f6689730616fc087a12e730524c9e245e29b`, on
`codex/reservoir-experiments`. Build three distinct native identities,
`research.reservoir.scope.discovery.{gemma,glm,mistral}`, from this checkpoint.
Each has a fresh step-zero session and a new reciprocal peer group. No prior
journal, authored control change or inquiry is carried forward.

The exact configuration and model digests are retained privately under
`research/outputs/three-model-experiments-20261115/`. Relative to the prior
[compact-scanner cohort](2026-11-15-model-led-reservoir-exploration.md), change
only the sonar contract to `experiments-v3`, the peer group and app/session
identities. Keep real probes enabled, optional peer reading, the unchanged
hourly prompt with telemetry, initial leak 0.65, 30-step writing cadence,
1-second requested step pace, 32,768 context tokens and 2,048 output tokens.
All other original numerical and language settings remain identical.

Models: local `gemma4:12b`, `glm-4.7-flash:q4_K_M`, and
`ministral-3:8b-instruct-2512-q4_K_M`; embedding is `nomic-embed-text:latest`.
All calls use the existing owned loopback service on port 11435. Preserve its
keep-awake process. No live-being service, journal or setting is involved.

The [experiment contract](../../desktop/ReservoirScope/EXPERIMENTS.md) allows
model-selected numerical arguments, identified results and follow-up requests
on copied states, with a separate bounded real impulse. The model sees this
capability in ordinary prompts; selected results reach later prompts. Neither
an experiment nor a probe is forced. Scheduled conversation still returns as
text input without executing NEXT.

Keep the protective 24-active-hour and 512-MiB per-session bounds, 1,000,000
steps and 10,000 attempts. These are safety limits, not a selected study length.
No automatic retries, skips or recovery are arranged. Startup verification
checks each exact configuration, native running state and first saved/applied
entry. It does not establish long-run reliability or successful use of every
new action.

## Preservation and later review

The preceding sessions were stopped through native controls at Gemma step 930
(31 journals), GLM step 900 (30 journals), and Mistral step 900 (30 journals).
GLM retained completed writing whose encoding was interrupted by Stop. The
other pending requests were cancelled. Original stores remain intact; complete
stopped-store snapshots and byte-for-byte checksum inventories are retained in
`previous-preservation.json` and `previous-sessions/` in the new private packet.
These are copied stores, not claimed UI exports. The old app windows and their
read-only observer are closed.

Later inspect actual parsed arguments, admission/rejection, measured outcomes,
results supplied to subsequent prompts, and whether a follow-up addresses its
stated question. Track unsupported claims, unresolved/no-contrast results,
response completeness, action syntax failures, storage growth and leak choices.
This is exploratory coupled use, not a controlled causal comparison, a global
topology result or evidence of subjective experience.

The implementation is already committed locally. UI work and this run's later
review should precede the next integration/release decision. Nothing is pushed
or tagged by this startup operation.

## Startup verified

The three native sessions started on November 15 at 16:20:52 (Gemma), 16:21:08
(GLM) and 16:21:22 (Mistral), Pacific time. All persisted configurations match
the prepared configurations exactly. All three first ordinary entries, observed
at step 30, were saved and their text input applied at step 31. Saved prompts
contain both `EXPERIMENT` and `PROBE_EXPERIMENT` guidance. Native build identities,
start receipts, exact first journals and consistent checkpoint observations are
retained in the private packet. This confirms startup, not later exploration.

The first action outcomes already identify later review cases: Gemma selected
an experiment but included unsupported `feedbackScale` in a condition, so its
action was rejected with explicit feedback; GLM applied `PULSE alternating 0.5`;
Mistral omitted the final NEXT line, so no authored control was applied. Text
feedback and action admission are separate. No operator correction or retry
was performed. These cases should be revisited alongside later prompts and
responses after UI work, without treating one entry as a model-level result.

All three stopped predecessor snapshots also passed native replay verification
with the 0.51.0 qualifier, and their bytes remained unchanged. The old observer
exited. No new background observer was started; the apps retain their own
histories. Startup verification is complete and continuous watching ends here.
