# Essentials actions and matched comparisons

Mike accepted the [action ladder](../essentials/stages/ACTIONS-AND-COMPARISONS.md)
and requested implementation on September 10. This work adds research-local
journal actions and paired comparisons to the native Essentials workspace.
It does not add actions to either live Being.

## Question and declared checks

Can the viewer make each newly added mechanism observable while preserving enough
evidence to reconstruct its effects? The first comparison is journal output versus
returning the same writing and encoded vector to the reservoir.

Before inspecting the new paired fixtures, the expected differences are:

- B versus A: recurrent connections can change later reservoir state under the
  same external forcing.
- C versus B: observing the separate sensory field leaves reservoir state identical.
- D versus C: generating and saving writing leaves reservoir and field identical.
- E versus D: a journal observed after step 30 first enters state at step 31.
  Fixed comparisons retain identical text and codec vectors.
- F versus E with fixed replies: memory exposure changes the prompt record, while
  state stays identical. This does not test an improvement in writing.
- G versus F: a chosen wait creates no journal and holds prior semantic input.
- H versus G with fixed replies: complete input vectors stay identical; retention
  and sensory covariance can change. The controller need not reach its target.

Alternative explanations include different external forcing, codec shaping from
different observations, language-provider variability, unequal prompt memory and
different viewing scales. Records and paired controls must expose or hold these
conditions fixed. The initial fixture set uses one shared seed, eight adjacent
comparisons and bounded action opportunities; simulation steps are not independent
subjects and no general writing-quality claim follows from their state differences.

The release checks cover mechanism/replay verification, unsuccessful actions,
incomplete output, save failure, timeout/cancellation/late-response rejection,
malformed imports, native lifecycle, synchronized rendering and standalone packaging.
The real headless CLI is also exercised by
[action_cli_smoke.py](../essentials/tests/action_cli_smoke.py).

## Interpretation

The present journal prompt observes the separate input-driven sensory field.
Reservoir activations do not supply that observation. Recurrence alone cannot
change journal writing through this channel. A future reservoir-state observation
would be an additional explicit mechanism.

Journal output, storage, exposure in later language context and application through
the codec remain distinct events. The 48-coordinate handcrafted codec is a reduced
feature map; it is not a recoverable copy of the journal or evidence of understanding.
The topographic surface uses actual state with a fixed coordinate map and scale.
Its geometry does not depict network connectivity or writing quality.

## Validation status

Reservoir Scope **0.11.0 build 15** is built and opened locally. The
[build receipt](../native/ReservoirScope/build-receipt.json) binds the final
packaged sources and resources to the following retained checks.

| Evidence | Result |
|---|---|
| Shared core tests | 51 passed, including 19 action/comparison checks and the existing 32 tests. |
| Native session lifecycle | 40 checks passed; three additional impossible action histories rejected. |
| Packaged headless runner | Eight 91-step ladder recipes passed; 12 malformed exports rejected. |
| Isolated HTTP adapter fixtures | Five cases passed: complete replies with memory, partial output, length limit, HTTP error and redirect. |
| Saved-format compatibility | New 300-step action example, four original 300-step stage examples and a 50-step Explore recording verified. |
| Native layout and shared camera | 25 layout and nine camera checks passed. |
| Presented inspector | Seven disclosures expanded through accessibility, with scrolling and a subsequent journal-application step; five compound checks passed. |
| Renderer | 43 checks passed, including seven exact legacy pixel matches. |
| Final packaged app | Manual Step → Write journal → Step, expanded journal/prompt/vector details, example loading, shared scrubbing and Replay/Pause inspected successfully. |

The fixed recipe runs produced the declared numerical distinctions: C/B and D/C
had identical reservoir states; E/D first differed at step 31; F/E remained
identical with fixed replies; G/F first differed at step 91 after the scripted
wait; H/G retained identical inputs and states while sensory retention could differ.
These are deterministic implementation checks, not observations of adaptive writing.

In the final app, the bundled D/E example matched through step 30. At step 31,
node 0 was −0.103797 without journal return and −0.647102 with return; state
difference RMS was 0.536437 and external-input difference RMS was zero. The app
is left paused at that comparison. The separately saved manual two-step session
also verifies with the packaged runner.

An earlier native inspection found a SwiftUI layout loop while opening journal
details. The bounded inspector now uses an eager stack. The dedicated presented
regression and the final packaged-app interaction both pass; the original process
sample is retained in the validation directory. Successful offscreen checks alone
did not establish the interactive behavior.

No real model was contacted, and no live-being runtime was changed. The native
hosting timings are bounded responsiveness checks, not presented FPS, energy or
cross-host performance measurements. Saved receipts reconstruct a run's declared
history; they do not independently authenticate past network requests or prove a
journal file still exists at its original location.

## Board updates pending

The Artifact connector is unavailable, and the earlier board access attempt did
not provide an authenticated editing surface. The
[local card and session log](../board/essentials-actions-pending.json) are prepared.
Board publication remains pending.
