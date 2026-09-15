# Essentials

Fresh, small reconstructions of the reservoir, spectral bridge, language loop,
and regulation. This is a first-class experimental area of the research project.
Each piece can be understood separately, then assembled into four runnable stages.

Open **Reservoir Scope → Essentials → Explore** for Start/Pause, single steps,
pulses, repeated input and live parameter controls. The [exploration guide](EXPLORE.md)
explains each control and its recorded effects. Choose **Stage experiments** to
run the four assemblies, inspect exact coordinates, and replay their history.
The **Minime & Astrid** side retains the existing
recorded and optional read-only observations.

The [Actions & comparisons workspace](ACTIONS.md) adds an eight-version ladder,
explicit journal writing, semantic return, journal memory and bounded action choice.
Compare adjacent versions with fixed reply/vector replay or independent generation.
The [original design](stages/ACTIONS-AND-COMPARISONS.md) preserves the reasoning;
action records use a separate format from the original four stage recipes.

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

On macOS 14 or later with Swift tools:

```sh
essentials/build.sh
essentials/check.sh
native/ReservoirScope/build-app.sh
```

The Essentials build prints the headless runner's full path. Use it with a numbered
JSON specification from the stage directory. Create `research/outputs/essentials/`
first when using the runner; the app creates it automatically:

```text
essentials-run run --config SPEC.json --output research/outputs/essentials/RUN.json
essentials-run verify research/outputs/essentials/RUN.json
```

The native viewer uses the same library directly. It offers **Run**, **Stop**,
**Reset**, **Replay**, step scrubbing, and **Open / Export**. Its default is 300 steps
at one third of a simulated second per step. The viewing speed changes presentation,
not the numerical update. Language boundaries occur every 30 steps when another
step remains. Simulation waits for a complete reply; its feedback first applies
at the next recorded boundary and remains until the next accepted reply.

The app saves generated runs under this repository's
`research/outputs/essentials/`. Saved files preserve the recipe, seed, complete
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
