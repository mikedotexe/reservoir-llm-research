# Mapping the laptop reservoir's geometry and response

**November 15, 2026 · exploratory offline study, specified before numerical analysis.**
Mike noticed repeated topology/geology language and asked how we could map the
reservoir ourselves. This work uses the completed November 14 independent laptop
exports. The November 15 peer-reading runs continue without changed prompts,
actions, parameters or timing. No live being or model service is involved.

## What can be mapped

The current source records two distinct numerical systems:

- A 32-coordinate recurrent state, driven by 66 inputs: 18 forcing slots and 48
  textual/probe slots. The current semantic codec fills 32 of those latter slots;
  an authored probe can use all 48. The weighted graph is fixed apart from the
  scalar recurrent-gain control. Persistent tuning changes the dynamics, not the
  individual edges.
- A separate 32-dimensional sensory projection of the inputs, with a normalized,
  exponentially retained outer-product matrix. Its spectrum, fill and retention
  are not the covariance spectrum or memory constant of the recurrent state.
  There is no direct numerical sensory-field-to-reservoir feedback in these runs.
  Both quantities can reach the writer as prompt text.

Source: `desktop/ReservoirScope/crates/reservoir-core/src/math.rs` (`ReservoirModel`,
`ReservoirEngine`, `SensoryField`, `forcing`) and `sustained.rs::advance`. Saved
frames contain every state, input, recurrent noise draw and applied control receipt.

Three different claims need different evidence: graph connectivity, geometry of
visited states, and response to intervention. A 2D projection is a view of sampled
states, not proof of basins, loops, semantic territories or subjective experience.
Repeated journal metaphors motivate questions; they do not identify those structures.

## A useful source-derived expectation

The recurrence is `x' = clamp((1-a)x + a*tanh(W_in[u,1] + g*W*x) + noise)`.
Seeded `W` has maximum absolute row sum 0.9. For two states with identical input,
noise and controls, tanh and clipping are nonexpansive, giving an infinity-norm
separation bound of `1-a + 0.9*a*abs(g)` per step. At the initial leak 0.65 and
gain 1 this is 0.935. This is a mathematical bound, not an observed decay rate.
Identical later additive pulses and their clipping cannot increase that bound.

Consequently the initial recurrent subsystem forgets differing initial states
under the same drive. Persistent distinctions can still be maintained by changed
input, controls, journal memory and the larger language loop. Gain tuning can
invalidate this sufficient contraction bound; it does not by itself prove chaos
or multiple attractors. Saturation can simultaneously reduce response to new
inputs and speed loss of a state perturbation.

## First bounded analysis

Use all saved numerical frames from the three completed independent sessions.
Reconstruct the seeded weights from the checked source. Before interpreting a
counterfactual, require one-step replay of every observed transition within
1e-12 maximum coordinate error, including held inputs, noise, tuning and pulses.
This Python numerical reconstruction is separate from the native exact replay.

1. Map actual trajectories in a shared centered PCA basis; report retained
   variance. Compute recurrence distances in the full 32-dimensional space,
   excluding trivial temporal neighbors from any recurrence summary. Compare
   forcing phase and entry applications before interpreting apparent loops.
2. Measure local saturation and the singular values of the input-response map,
   separating all 48 probe coordinates from the 32 semantic-input coordinates.
3. Select six state boundaries per session at fixed fractions 0.10, 0.25, 0.40,
   0.55, 0.70, 0.85 of its recorded numerical duration. At each, compare unmodified
   continuation with signed state perturbations in coordinate 0, a fixed seeded
   random direction, and the direction of greatest 16-step linear response.
   Use signed L2 amplitudes 0.0001 and 0.1, a 64-step horizon, and identical
   subsequent recorded input, noise and actions on every branch. Record clipping,
   separation, and time below 10% of the actual initial displacement for five
   consecutive boundaries. No return within the horizon is an explicit outcome.
4. At the same anchors, test signed 0.01 single-coordinate input impulses across
   all 48 authored-probe slots. Compare responses after 1, 2, 4, 8, 16 and 30
   steps; retain the response matrices and their singular values. Check agreement
   of central finite differences with the analytic derivative where unclipped.

Counterfactuals keep the later recorded writer choices fixed. They measure the
conditional numerical subsystem, not what the closed language loop would choose
after a changed observation. The unmodified path is the paired control; opposite
signs and a fixed random direction constrain directional interpretation.

Private output: `research/outputs/reservoir-response-mapping-20261115/`. Preserve
the source manifests, source/probe hashes, selected steps, numerical checks and
results. No model calls or extra live-run measurements are required.

## What follows only if useful

An adaptive probe could select a bounded input vector that best distinguishes two
explicit numerical hypotheses, predict the response, and compare the next receipt
with that prediction. This is a more grounded meaning of "exploring the terrain"
than assigning a topic name to a projection axis. The model could request a probe
goal; numerical tooling would provide the vector, norm and predicted alternatives.
This is a proposal, not an implemented or deployed action.

Persistent homology is a later way to ask whether loops/components survive changes
in distance threshold and sampling. It needs forcing-only, linear fading-memory
and suitably matched surrogate controls; a shuffled point order leaves ordinary
point-cloud topology unchanged and is not a sufficient topology control. Full
state is already logged, so delay reconstruction is not needed merely to recover
missing state coordinates.

Relevant primary work: [Wainrib and Galtier on input-conditioned stability](https://arxiv.org/abs/1402.1619),
[Perea and Harer on persistence and periodicity](https://arxiv.org/abs/1307.6188),
and [Dambre et al. on information-processing capacity](https://pmc.ncbi.nlm.nih.gov/articles/PMC3400147/).
These motivate methods; they do not establish a result for this apparatus.

## First results, November 15

The bounded offline analysis is complete. No model was called and no running
session was changed. The Python recurrence reproduced all 11,284 saved transitions
with maximum absolute coordinate error below 1.1e-15. Its matrices are generated
from the source seed and checked against the actual transitions, not inferred
from journal language.

| November 14 trajectory | Frames | State perturbations | Return below 10%, five consecutive boundaries |
|---|---:|---:|---|
| Gemma4 | 3,206 | 72 | all; 3–4 numerical steps |
| GLM-4.7-Flash | 4,343 | 72 | all; 2–4 numerical steps |
| Ministral 3 | 3,735 | 72 | all; 3–4 numerical steps |

These are 216 conditional continuations from 18 selected state boundaries, not
216 independent subjects. Numerical steps are not LLM turns or elapsed hours.
The ordinary writer cadence in these runs was 30 numerical steps; the recurrent
system does not advance while it waits for a writer/embedding response.

The input impulse test used 1,728 signed numerical continuations: 18 anchors ×
48 directions × two signs. Immediate leading response gains ranged from 3.01 to
4.12 in state-L2 per input-L2 units; the leading finite-difference gains at 16
steps were at most 4.8e-5. This indicates directions that can move the system now
while the impulse's distinct trace rapidly disappears under the fixed future
drive. It does not identify a semantic direction or establish all-state
controllability. At long horizons some differences reach floating-point precision;
their tiny nonzero values are not evidence of durable memory.

The shared two-axis PCA view retains 39.1% of pooled state variance. It visibly
separates some of the visited regions, but leaves most variation off the page.
The full-state distance maps contain repeated structure. At the same phase of
the imposed 30-step forcing gate, median distances are lower in all three sampled
maps than at other phases. This is descriptive and also confounded with the
30-step entry cadence; it does not attribute the pattern to forcing alone.

The existing source and this experiment support distinguishing three forms of
persistence: a displaced recurrent state; a held embedding reapplied at every
step; and text returned through journal/inquiry memory. The first decays quickly
in these samples. The latter two can keep an idea's influence present after its
original state displacement has disappeared. Long-lived narrative structure
therefore need not imply a long-lived unforced recurrent basin.

### Numerical qualification and correction

Every selected 64-step unmodified continuation reproduced its saved trajectory
within the declared 1e-12 gate. All 54 signed state-derivative comparisons encounter
clipping somewhere in the 64-step horizon, so none qualifies under the original
strict "unclipped window" criterion. We do not claim that criterion passed.

A subsequent one-step derivative audit exposed a comparison error: requested
directions at a state boundary were compared with analytic derivatives even when
the initial signed perturbation had been clipped. The comparison now uses the
actual central displacement. The maximum one-step relative discrepancy is below
5.8e-7 across 54 checks. Earlier diagnostic outputs are retained alongside the
correction. The 216 state trajectories and 1,728 input trajectories, their selected
anchors and all primary numerical results are unchanged
before and after this derivative-audit correction. Long-horizon relative errors
can still be large when the predicted response is close to numerical zero.

### Reproduction and retained artifacts

The measured numbers come from `probes/map_sustained_response.py` and
`probes/plot_sustained_response.py`, using the three immutable exports named by
the November 14 primary protocol. Source hashes, input manifest hashes, selected
steps, all numerical outcomes and NumPy version are in private `results.json`;
arrays are in the per-session NPZ files. Plotting uses an isolated local environment.
The three PNG/PDF pairs are `state-map`, `recurrence-map` and `response-map`;
`figure-metadata.json` retains the shared PCA spectrum and sampling indices.

The next useful study would compare pulse and held-input effects across leak and
input-update cadence, with matched drive/noise and a simple linear fading-memory
baseline, before changing the live experiment's settings. A second stage can
test which bounded bespoke input best separates two predicted responses, and
whether returning that evidence lets the writer revise a concrete claim.

## Follow-up: an identity mirror and a light probe

Mike next asked whether a crafted input, perhaps an identity matrix, could reflect
the internal space without altering it. An identity **readout**, `y = I*x`, copies
the recurrent state. An identity **input basis**, `epsilon*I_48`, means separate
small probes along the 48 input coordinates; the measured output columns estimate
the local input-response matrix. The latter is what the offline impulse analysis
above does. It is an intervention on each copy, not a neutral live input.

For the known numerical model, a passive mirror can expose state, recent motion,
principal directions and local input-response derivatives directly from a saved
checkpoint. Tag the held input, forcing phase and effective controls: the 32
recurrent coordinates alone are not the complete state of the coupled apparatus.
The sensory matrix, controller and journal/inquiry memory carry additional history.

Reinjecting `x` is a new feedback law, not the identity readout. Replacing the held
input with zero also changes the experiment. Isotropic input noise (covariance
proportional to identity) has no preferred input direction, but the input weights
and nonlinear activation can make its effect on state strongly directional.
Equal positive/negative perturbations need not cancel a nonlinear trajectory.

A recurrent-input nullspace can provide a control that leaves the recurrent
drive unchanged, but that does not imply the separate nonlinear sensory field or
subsequent LLM loop is unchanged. A direction invisible to the recurrent state
also cannot reveal its response through that state. Treat any such control as
channel-specific, not a universal harmless input.

Recommended future interaction: passive observation, then an explicitly labeled
experiment on a copy, then an optional bounded real intervention. Bound a real
probe by predicted **state displacement** as well as input norm, and compare its
actual outcome with the prediction. A small requested input is not automatically
a small effect. Supplying the mirror in a prompt changes what the writer can see
and may change its later writing/input; that informational feedback is separate
from the passive numerical readout. No mirror action has been implemented here.

This distinction connects to [Lall, Marsden and Glavaški's empirical input-output
analysis of nonlinear systems](https://www.cds.caltech.edu/~marsden/bib/2002/06-LaMaGl2002/).
