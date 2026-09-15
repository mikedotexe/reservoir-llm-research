# Hands-on Essentials in Reservoir Scope

Mike asked for native controls that start the reconstructed reservoir, change its
parameters, supply repeated input, and make the effects visible. Reservoir Scope
0.9.0 build 12 adds **Essentials → Explore** beside the four existing stage
experiments. The [user guide](../essentials/EXPLORE.md) gives a first experiment.

## Implemented behavior

The explorer begins at zero with bias, noise, recurrence and external forcing off.
Start advances a paced clock; Step advances once; Send pulse supplies one synthetic
video/audio input. Recurrent feedback sends the previous state through the seeded
connections. Repeat external input supplies twelve steps of forcing followed by
eighteen quiet steps. These controls expose two separate mechanisms; leak alone
also preserves a share of the preceding state. No trained readout is introduced.

Leak, feedback strength, input strength, noise, bias and optional sensory projection
can change while running. Each observation retains the actual settings it used.
One numerical step remains one third of a simulated second. Viewing pace changes
the wall-clock rate, with no catch-up burst after delayed drawing. Sessions pause
at 1,800 steps. Reset preserves the old recording and starts from the chosen seed
with the current controls.

The 32-coordinate surface has fixed size and a fixed signed activation palette.
Its drawing map identifies coordinates rather than wiring. Input, recurrent drive
and state RMS share a fixed 0–1 history scale. The node inspector exposes exact
input, recurrent and bias contributions, tanh, the leak mix, added noise and
clipped state. Pre-tanh contributions use a shared −6 to +6 scale. Optional sensory
measurements come from a separate projection of the same input; its eight displayed
modes use a fixed 0–32 scale. Explore estimates no fill.

The left controls describe the next step. The inspector describes the recorded
cursor, even after controls change. Scrubbing pauses execution; continuing resumes
the latest numerical state. Replay, Open and Export preserve stored observations.
Mode and subject changes stop the experimental clock. The four-stage LLM and
regulation loop remains available under Stage experiments.

## Implementation and retained evidence

The shared implementation is
[ReservoirExploration.swift](../essentials/reservoir/ReservoirExploration.swift).
[ExplorationViewModel.swift](../native/ReservoirScope/Sources/ReservoirScope/ExplorationViewModel.swift)
owns pacing, import, replay and serialized background saves.
[ExplorationExperience.swift](../native/ReservoirScope/Sources/ReservoirScope/ExplorationExperience.swift)
owns the controls and visual explanation. Exploration records use
`essentials-exploration-v1`; the headless verifier accepts both that format and
the existing `essentials-v1` stage records. Files remain under
`research/outputs/essentials/`, separately from source and bundled examples.

- [Core checks](../native/ReservoirScope/validation/0.9.0/core-tests.json): 32 tests,
  including ten exploration tests, nine mechanism tests and thirteen runtime tests.
  These include exact contribution arithmetic, quiet start, recurrence switching,
  applied controls, seeded continuation, spectral reset, tamper rejection and
  preservation of valid imported spectral orientation.
- [Lifecycle checks](../native/ReservoirScope/validation/0.9.0/exploration-lifecycle.log):
  28 cases cover paced ticks, pulses, pause, replay, load cancellation, saved-file
  handling, save ordering, the step cap and leaving the view.
- [Runtime receipt](../native/ReservoirScope/validation/0.9.0/exploration-runtime.json):
  a 50-step exploration and a legacy 300-step run verify; modified state and an
  unknown format are rejected.
- [Native hosting checks](../native/ReservoirScope/validation/0.9.0/exploration-layout/receipt.json):
  15 checks exercise the production view timer, compact layout, actual node count,
  controls at the cursor, pause and leave. This measures layout/event-loop behavior,
  not presented frame rate.
- [Current build receipt](../native/ReservoirScope/build-receipt.json) links final
  packaged identity, example verification and direct native inspection.

The final presented-window check opened the original 15-step native recording,
replayed it, continued it to 33 steps, switched modes, and exported it through the
native save dialog. The packaged verifier reproduces both that export and its
autosave; their JSON is identical, and the original fifteen frames are retained
exactly. The node-0 value displayed at step 33 agrees with the exported vector.
[Native inspection details](../native/ReservoirScope/validation/0.9.0/runtime-qa.json)
separate preliminary control checks from final-package inspection. Direct visual
inspection caught a wrapped workspace label and an inactive-window button-contrast
problem; both were corrected before final identity qualification.

The final native hosting run used the packaged core archive and the exact view
source: 39 frames, 48.7 ms maximum layout time and 68.1 ms maximum event-loop gap.
All four packaged stage examples also reproduce, totaling 1,200 steps and 27
recorded text turns; the separate scripted exploration fixture has 50 steps.
The reproducible entry points are the two exploration check scripts listed in
[HANDOFF](../native/ReservoirScope/HANDOFF.md), the retained core-test command, and
the packaged runner's `verify` command for each path in the record receipts.

The original four canonical stage examples, reduced controller tests, transport
qualification and 128-node rendering comparisons retain their
[0.8.0 account](2026-09-09-essentials-implementation.md) and
[archived build receipt](../native/ReservoirScope/build-receipt-0.8.0.json).
Unchanged source comparisons distinguish that retained evidence from new checks.

## Scope and limits

This is a synthetic experimental reconstruction. It supplies no commands, prompts,
files or changes to either being. No real model calls, live ingestion, new hardware
comparison, energy measurement or presented-frame-rate qualification occurred.
The source changes remain in the shared research checkout and are not committed.

## Board updates pending

The Artifact board connector is unavailable in this session; the prior board
access attempt did not provide an authenticated editing surface. The prepared
[card and session log](../board/essentials-exploration-pending.json) remain pending.
The implementation and local evidence are complete independently of publication.
