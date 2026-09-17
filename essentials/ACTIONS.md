# Actions and comparisons

Build up one mechanism at a time in **Reservoir Scope → Essentials → Actions & comparisons**.
This is the default workspace in the portable 0.12.0 app. [Portable lab guide](../native/ReservoirScope/docs/PORTABLE-LAB.md).
The workspace keeps its own versioned records. Explore and the original four
stage recipes retain their existing behavior.

## The ladder

| Version | Addition | Expected comparison |
|---|---|---|
| A · Minimal reservoir | Leaky units with external input | Baseline; recurrence, bias and noise off. |
| B · Recurrence | Seeded connections return the previous state | State persistence changes. |
| C · Sensory observer | Separate input projection and covariance | Reservoir state stays identical to B. |
| D · Journal output | Generate and save a complete journal entry | Reservoir and field stay identical to C. |
| E · Reservoir return | Encode the journal into semantic input | The first possible state change is the step after writing. |
| F · Journal memory | Include the previous saved journal in the next prompt | Inspect exactly which words were supplied and what follows. |
| G · Action choice | Choose `WRITE_JOURNAL` or `WAIT` | Inspect the choice and its actual outcome. |
| H · Regulation | Enable reduced sensory-retention control | Compare fill and controller history, including unreachable targets. |

These are reduced experimental mechanisms. They do not execute actions in Minime
or Astrid. The language observation comes from the **separate sensory field**;
reservoir activations do not enter the A–H ladder prompt. Enabling recurrence by itself
therefore cannot change writing through this observation channel.

The common baseline uses 32 reservoir nodes, 32 sensory coordinates, the original
66 input coordinates, seed 20260909, leak 0.65, no bias or noise, and the same synthetic
12-step-on / 18-step-off forcing. Default runs last 300 steps at one-third simulated
second per step. Scheduled journal opportunities occur after steps 30 through 270.
Waiting for language does not advance simulated time.

Start with **Step → Write journal → Step** in E · Reservoir return. The first
step supplies an observation; writing saves the entry and prepares feedback;
the next step applies it. **Open example** loads the selected component’s 120-step
scripted example. **Runs & examples** also contains recorded model writing. Scrub across steps 30 and 31 to inspect the first return.
The inspector includes all 66 applied input coordinates, all 32 sensory
eigenvalues when available, the exact journal and its encoded feedback.

**Stop** between steps preserves a resumable session. Cancelling an outstanding
language action ends that session; the next Run or Step starts a fresh one.
Saved results remain available through Open. Native runs and their journals live
under `~/Library/Application Support/Reservoir Scope/Actions/<session>/`; Export writes a portable
record to the explicitly selected local location. The [headless recipes](actions/recipes/)
also expose the numerical settings, with runs bounded to 600 steps.

## Writing and its return paths

**Write journal** invokes an explicit action. Scheduled writing is also explicit;
the action-choice stage adds the bounded choice to write or wait. Waiting produces
no journal and leaves the previously applied semantic input held.

The inspector distinguishes an action request, completed language response,
successfully saved journal, later context exposure, and actual codec application.
Saving words does not itself change the reservoir. Returning them to the reservoir
uses the 48-coordinate handcrafted feature lane; embedding features remain unavailable.
Returning them to a language prompt supplies the previous complete saved text.

Failed or incomplete output stays visible as attempt evidence. It is not eligible
for feedback. A journal must be successfully saved before either return path can
use it. Local journal files belong to the research session; portable run exports
include the exact entry text and references needed for replay.

## Compare one addition

**Compare with previous** matches the selected version with its immediate predecessor.
Both views use one recorded-step cursor, synchronized cameras and fixed color and
height scales. The difference trace uses the actual coordinate vectors. It measures
state differences, not writing quality or understanding.

Two modes answer different questions:

- **Replay identical replies** holds the reply text and its encoded vector fixed
  from a retained reference trajectory. Changing only the return gate isolates the
  numerical effect of journal feedback. Freezing words alone is insufficient because
  the codec also uses the sensory observation. Controller isolation also holds the
  complete input vectors fixed.
- **Generate independently** gives each arm its own actual observation and memory.
  Different subsequent writing is part of the coupled result. Scripted defaults
  are repeatable fixtures; they do not establish adaptive writing. An explicitly
  configured separate local Ollama endpoint and model can supply real generations.

Fixed replies cannot tell us whether memory improves writing. For that question,
use independent generation, inspect the exact context and replies, and keep the
model settings matched. A zero temperature is not a promise of identical generation.

Record the question, expected difference, alternative explanations and stopping
point before interpreting a comparison. One paired run is an inspectable example;
its 300 steps are not 300 independent trials. Preserve waits, failed attempts and
targets that remain out of reach alongside successful output.

The [accepted design](stages/ACTIONS-AND-COMPARISONS.md) records the original reasoning.
The [research methods](../research/METHODS.md) explain the interpretation boundaries.

## Controlled observation comparison

**What can the journal observe?** uses two stage-D arms, matching all numerical
observations while adding the 32 indexed reservoir coordinates to only one prompt.
It requires independent generation, alternates request order, and preserves one-arm
failures. Its question and stopping rule belong to [S-009](../research/studies/S-009-portable-reservoir-journals.md),
separate from live observational studies. New records use `essentials-actions-v2`;
legacy v1 files retain their original prompt-verification path.

[Headless recipe](actions/recipes/D-observation-comparison.json) ·
[Release checks](../analyses/2026-09-16-portable-reservoir-lab.md).
