# Numbered recipes

The [Actions & comparisons workspace](../ACTIONS.md) implements separate pairs
that change one mechanism at a time, including journal output and feedback. The
[accepted design](ACTIONS-AND-COMPARISONS.md) records its reasoning. The action
format does not alter these executable recipes.

Each recipe composes the same small Swift mechanisms. All use seed `20260909`, 32
reservoir nodes, 32 separate sensory dimensions, 66 input coordinates, leak `0.65`,
initial covariance retention `0.955`, 300 finite steps, `1/3` simulated second per step,
no noise by default, and one text turn every 30 steps when another step remains.
The recurrent maximum absolute row-sum bound is `0.9`.

| Recipe | Added capability | Absent measurements |
|---|---|---|
| `01-reservoir.json` | Leaky recurrence and synthetic sensory forcing | Spectrum, fill, control, text |
| `02-spectral-bridge.json` | Separate projected covariance and supplied example text | Fill, control, model requests |
| `03-llm-loop.json` | Spectral prompt → complete reply → semantic feedback | Fill and control |
| `04-regulation.json` | Reduced fill and next-step retention PI | Production scaffold control |
| `04-regulation-disabled.json` | Matched controller-off comparison | Controller measurements |

Synthetic forcing is present for the first 12 steps of each 30-step cycle, then zero
for 18 steps. Video coordinates 0–7 and audio coordinates 8–15 vary smoothly and
independently; auxiliary coordinates 16–17 are zero. This allows Stage 1 to show
persistence after the external input ends. No camera, microphone or live-being data
are read. Noise, when requested, has its own seeded stream and is saved per step.

Stages 2–4 observe after steps 30, 60, …, 270. Each complete text passes through the
handcrafted codec and its declared spectral feedback shaping, then occupies semantic
coordinates 18–65 starting at the following step. It remains constant until replaced.
Both raw features and the applied semantic vector are saved, with the exact text and
first application step. The retained `prompt` is prepared example context in Stage 2,
marked `contextKind: preparedExampleContext`; it is never sent to a backend. Stages 3–4
mark the retained provider request `contextKind: languageRequest`. A retained request
alone does not establish successful delivery or completion; its outcome is separate. Unavailable embedding and reserved features remain zero.
The final step does not trigger a reply that could never be applied.

The field receives the same input as the reservoir, through a separate seeded
projection. Its spectrum is not a spectrum of reservoir activations. Prompt entropy is normalized
over the leading eight modes, and head/shoulder/tail shares use their sum as the
denominator, not the full 32-dimensional covariance trace. Stage 4 derives
**reduced active-mode fill** from all 32 field eigenvalues. It displays that experimental
percentage separately from the fixed-size 3D state geometry.

The controller-on/off recipes have identical forcing, noise and fixed scripted reply
texts. Their sensory-dependent codec shaping can produce different applied semantic
vectors, so this is a comparison of the complete feedback loop, not a same-input
causal isolation of retention. The numerical mechanism tests also compare retention
using exactly the same field inputs. Low/unreachable target cases are preserved;
there is no assertion that the PI must achieve 68% for every forcing sequence.

`RunSpecification` exposes step count (1–3000), step duration (0.001–10 seconds), turn
interval, seed, leak (0–1), noise amplitude (0–0.2), initial retention (0.82–0.995),
regulation enablement and language configuration. Dimensions, update order, projection
normalization, codec layout and controller coefficients are fixed by `essentials-v1`.
Run/replay records retain that recipe identity. Changing its numerical meaning requires
a new recipe version and corresponding verifier.
