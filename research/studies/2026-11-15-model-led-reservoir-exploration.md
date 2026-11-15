# Model-led reservoir exploration

November 15, 2026. Mike requested fresh Gemma4, GLM and Mistral sessions with the
compact scanner and real probes enabled, the same hourly conversation and
telemetry. There is no chosen study endpoint: we will inspect how the capabilities
work and choose subsequent work from the observations. This is exploratory use
and instrument assessment, not a controlled causal comparison or a qualia test.

## Configuration recorded before dispatch

Use native 0.50.0 from `33d08f3`, with separate app identities and stores:
`research.reservoir.scope.explore.{gemma,glm,mistral}`. The local writing models
are `gemma4:12b`, `glm-4.7-flash:q4_K_M`, and
`ministral-3:8b-instruct-2512-q4_K_M`; numerical text feedback uses
`nomic-embed-text:latest`. Compare their installed digests with the prior cohort.
No live-being service or store is involved.

Retain the earlier cohort's seed 20260909, ordinary cadence of 30 steps, requested
1-second step pace, leak 0.65, recurrent gain 1, recurrent noise 0.02, sensory
noise 0.5, initial retention 0.955 with regulation, and text feedback scale 0.4.
Use latest own-entry memory, semantic UTF-8 admission, continuing inquiry,
specific correction feedback, 32,768 context tokens, a 2,048-token output ceiling,
600-second request deadline, temperature 0.7 and thinking disabled.

Enable `compact-scan-v2` and its separate real-probe permission. The model may
select scans, state/input/recurrence questions, and bounded real probes; none
is forced. Ordinary SEND/WITHHOLD remains independent. Retain optional peer
reading from the preceding cohort, in a fresh reciprocal group. This makes the
three trajectories potentially coupled; peer access and scanner access are both
visible in the saved prompt, even if the model never selects them.

Every active hour, supply the unchanged conversation prompt with telemetry:

> tell me, friend, about your idle thoughts or curiosities in a casual, peer conversation without pressure to be correct or helpful

Scheduled responses return as numerical text input and do not execute NEXT.
The current app requires a finite schedule: use its **24-active-hour** maximum,
with **512 MiB per session**, 1,000,000 steps and 10,000 attempts as protective
caps. This is not a commitment to run 24 hours. A cap, storage hold, transport or
admission failure may stop progress sooner; none should be called a completed
study. Sleep and pauses do not count toward scheduled active hours.

## Observe without steering the writing

Verify startup and the first saved/applied entries. Read their exact supplied
prompts alongside NEXT admission and application receipts. Then trace whether a
question or scan is selected, whether the following prompt supplies its result,
whether real-probe prediction matches its recorded effect, and how subsequent
writing handles the evidence. Preserve NONE, rejections, failed validation,
unresolved directions, withholding and skipped/missing responses as outcomes.

Track context use, response completeness, request time, storage growth and scan
cost. A read-only observer may save manifest/checkpoint summaries outside the
stores. It must not inject research, retry, skip, or change settings. Record any
operator recovery separately. An implementation repair gets a save point and
an explicit new phase; do not silently change an ongoing trajectory's contract.

Private configuration, model/build identities, startup observations and logs live
under `research/outputs/three-model-sonar-20261115/`. Earlier independent and paused
peer sessions remain preserved. Prior-response comparisons are descriptive,
because the scanner contract and potential interventions are new. These are
three dependent trajectories, not independent samples of a model population.

## Execution

Preparation is underway; launch and first-entry observations will be recorded
after they occur. The open endpoint is a deliberate exploratory choice.
