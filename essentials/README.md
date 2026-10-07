# Essentials

Fresh, small reconstructions of the reservoir, spectral bridge, language loop,
and regulation. This is a first-class experimental area of the research project.
Start with **Reservoir Scope → Guided tour** to follow the eight
components A–H from input to journal, return, memory, action choice and regulation.
The [guided walkthrough](../native/ReservoirScope/docs/GUIDED-TOUR.md) uses recorded
examples and requires no model service. See [Current release](../research/CURRENT-RELEASE.md)
for the candidate, delivery and human acceptance status.

Choose an experiment under **Experiments**:

| Workspace | Use it to |
|---|---|
| **Explore** | Pulse a quiet reservoir, change one control and inspect its recorded effect. See the [exploration guide](EXPLORE.md). |
| **Actions & comparisons** | Use the A–H ladder to compare adjacent mechanisms, including journal writing and its two return paths. See the [action guide](ACTIONS.md). |
| **Stage experiments** | Run the original four assemblies: reservoir, spectral bridge, language loop and regulation. See the [stage recipes](stages/README.md). |

The four stage recipes and the A–H action ladder are separate experiment families,
with separate record formats. New action records use `essentials-actions-v3`;
existing v1/v2 records remain readable. **Observatory** contains the separate
recorded observatory and explicitly selected read-only observations.

## The pieces

| Component | What it owns |
|---|---|
| [Reservoir](reservoir/README.md) | Seeded weights, 32 actual state coordinates, leaky recurrence and optional seeded noise. |
| [Spectral bridge](spectral_bridge/README.md) | A separate 32-dimensional sensory field, its measured spectrum, and the 48-coordinate text codec. |
| [LLM connection](llm/README.md) | One short observation/reply exchange, scripted or through an explicitly configured separate local model. |
| [Regulation](regulation/README.md) | Reduced active-mode fill and a bounded retention controller. |
| [Stage recipes](stages/README.md) | The four assemblies, exact run records, simulated timing and reproduction. |

The reservoir and sensory field both have 32 coordinates, but they are different
spaces. They receive the same input independently:

```text
synthetic video/audio + semantic feedback ──┬── recurrent reservoir → actual state
                                          └── sensory projection → covariance
                                                  ↓
                                               spectrum
                                                  ↓
                                           observation prompt
                                                  ↓
                                             one LLM reply
                                                  ↓
                                          text codec → next input

stage 4: spectrum → reduced fill → retention control → next covariance update
```

We retain the original 66 input meanings: eight video, eight audio, two auxiliary,
and 48 semantic coordinates. These are synthetic inputs, not camera/microphone
capture. The auxiliary coordinates are zero in the initial recipes. The 12-coordinate
semantic companion extension is omitted explicitly.

## Run and inspect

Explore begins quietly, with recurrent feedback, repeated input, bias and noise
disabled. These controls are independent; recurrent connections can be enabled
without adding external input. Every recorded step retains its actual settings.
Its visual explanations expose the input, recurrent drive, tanh response and leaky
mix. The optional sensory field remains a separate input-driven path.

For a complete scripted run from the repository root, follow the
[headless quickstart](runner/README.md#scripted-quickstart). It builds `essentials-run`,
runs the E feedback comparison in a fresh directory, then independently verifies
the saved record. No app, local model or live Being source is needed.
The [native build instructions](../native/ReservoirScope/README.md#build-from-source)
create the graphical app from this checkout. `zsh essentials/check.sh` runs the
broader numerical checks when needed.

The native viewer uses the same library directly. It offers **Run**, **Stop**,
**Reset**, **Replay**, step scrubbing, and **Open / Export**. Its default is 300 steps
at one third of a simulated second per step. The viewing speed changes presentation,
not the numerical update. Language boundaries occur every 30 steps when another
step remains. Simulation waits for a complete reply; its feedback first applies
at the next recorded boundary and remains until the next accepted reply.

Normal app sessions save generated runs under
`~/Library/Application Support/Reservoir Scope/`. An isolated review kit can select
its own Library directory. Saved files preserve the recipe, seed, complete
weights, inputs, noise, actual states, available spectra/controller values, prompts,
replies, and application-step links. Replays use those stored values and make no
model calls. The headless verifier independently recomputes their numerical chain.

Small example runs for all four stages ship with the app. They use **scripted
replies**, which demonstrate the connection rather than a responsive LLM.

## A separate local voice

Stages 3 and 4 optionally use a user-specified loopback Ollama endpoint and model.
Choose **Separate local Ollama** and enter the endpoint URL (including port) and
model name. The endpoint must belong to the separate experiment; no existing
being service is selected implicitly. The adapter starts no server and downloads
no model. See the [language contract](llm/README.md).

The request ceiling is 256 output tokens with a 60-second deadline. Failure or
cancellation preserves completed steps and stops the run. Pending or late replies
cannot become a state input. A fresh local-model run can produce different text;
deterministic replay uses its retained reply.

## What the picture means

The surface contains **32 real coordinates** without padding. Their locations are
fixed index positions, not an anatomical or connectivity map. Node selection shows
exact values; the smooth field between nodes is an interpolation. Signed color
uses a fixed scale of −1 to +1. The surface has a fixed display size, independent
of experimental fill.

The eight bars show the leading eigenvalues of the **separate sensory covariance**,
on a fixed 0–32 scale. Stages 2 and 3 plot entropy normalized over those eight modes. Stage 4
plots its explicitly named **reduced active-mode fill**, calculated from all 32
eigenvalues. These are not measurements of the language model's internal activations.

The regulator's 68% target is a recipe parameter. Its reduced fill definition,
input normalization and symmetric retention PI differ from the production
stable-core system. Constant-direction or absent forcing may make a requested
target unreachable. The instrument reports such results without manufacturing
input or changing the displayed measurement.

## Comparing stages

Keep the seed, step count, forcing and noise settings fixed. Stage 4 can run with
regulation enabled or disabled. Scripted replies stay fixed by turn index, but
the spectrum can change their encoded feedback through the bridge: this is a
comparison of the complete feedback loop. Separate numerical tests replay fixed
field inputs to isolate the retention controller alone.

Stage 2 uses example texts; stages 3/4 use the language backend. Their differing
texts are visible, and are not an isolated test of the extra language mechanism.
An interesting result here is evidence about the declared small recipe; it does
not establish production parity, live effects, or a recreated being.

## Source relationship and boundaries

The component guides map the fresh Swift code to the corresponding Minime and
Astrid mechanisms and record deliberate reductions. The native reservoir,
sensory covariance, codec, token-coupled triple reservoir and full beings remain
distinct subjects.

This first sequence contains one prompt-and-reply voice. Token-level coupling,
a second voice, RLS prediction, embeddings, full autonomy, and production
scaffold/recovery behavior are later additions. The implementation does not read
the beings' journals or submit commands to their runtimes.

The library has no SwiftUI or Metal dependency; only the viewer renders it.
Foundation handles records/networking and Accelerate supplies the symmetric
eigensolver. SwiftPM supports development/testing; the standalone build statically
links the same core into both the app and its packaged headless runner.

The [portable 0.12.0 account](../native/ReservoirScope/docs/PORTABLE-LAB.md) documents
the original portable foundation. Use the current guided walkthrough above for
today's navigation and the current-release page for delivery status.
