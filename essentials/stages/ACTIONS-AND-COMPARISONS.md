# Actions and comparisons: accepted design

**Original proposal, September 9, 2026; accepted for implementation September 10.**
The [implemented workspace guide](../ACTIONS.md) and
[implementation account](../../analyses/2026-09-10-essentials-actions.md) track the
result and validation. The proposal below is retained as the design record.
Add one mechanism at a time. The existing four stage recipes,
examples and `essentials-v1` verifier keep their
original meaning. New action sessions would use a separate versioned format.

## What exists already

[Explore](../EXPLORE.md) separates recurrence, external input and sensory observation.
The [numbered stages](README.md) assemble more mechanisms together: Stage 2 already
returns supplied example text through the codec; Stage 3 already returns completed
language replies. Neither provides journal storage, retrieval or an action dispatcher.

The current prompt observes the **separate sensory field**, which receives input,
not reservoir activations. Recurrence alone therefore cannot change writing through
this observation channel. Adding a reservoir-state summary would be a later,
separate comparison. The [language interface](../llm/Language.swift) already retains
requests and provider outcomes; it can support the proposed journal generator.

## A ladder with one change per comparison

Each row adds only the named feature.

| Version | Added feature | What to compare with the preceding version |
|---|---|---|
| A · Minimal reservoir | Leaky units receiving the declared external input; recurrence, bias and noise off | Starting baseline. Leak alone can retain previous state. |
| B · Recurrence | Enable the same seeded recurrent weights | State persistence and coordinate differences after input stops. |
| C · Sensory observer | Observe the separate projected covariance | Reservoir states should remain identical; new measurements become available. |
| D · Journal output | Execute a scheduled `WRITE_JOURNAL`, save its complete text, return nothing | New writing and storage receipts; reservoir and field should remain identical to C. |
| E · Reservoir return | Apply that same journal text through the declared codec on the next step | State and field changes caused by the semantic-input gate. |
| F · Journal memory | Supply the previous completed journal in the next journal prompt | Exact context exposure and subsequent writing; storage already existed in D. |
| G · Action choice | Replace forced `WRITE_JOURNAL` with a bounded choice of `WRITE_JOURNAL` or `WAIT` | Chosen action, actual execution, writing opportunities and outcomes. |
| H · Regulation | Enable the existing reduced retention controller | Controller effect under fixed inputs first, then the complete interacting loop. |

For H, compute reduced fill in both arms; switch only the controller.

Use 300 steps of one-third simulated second, with nine opportunities at steps
30–270. Fix seed `20260909`, leak `0.65`, bias off, noise zero, input strength one,
and the same 12-on/18-off external waveform. Retention stays `0.955` until H.
Record identical noise samples if noise is later tested. Semantic input is the
explicit difference in E; “same input” otherwise means the same external forcing.
Keep model, prompt ceiling, seed and display scale matched within a pair.

At D, the journal action is invoked by the schedule or a **Write journal** button;
this is not autonomous choice. G initially offers only writing or waiting. `WAIT`
creates no journal and leaves previously applied semantic input held as declared.
Both arms use the same opportunity clock and limits. New retrieval actions or
environmental tools would require additional comparisons.

## Writing, remembering and returning are different events

Keep a local journal store under each research session, separate from its frame
record and from bundled examples. An entry holds immutable text, its hash, producing
action/turn ID and source step. A portable export must include the referenced text.

An action inspector should show distinct receipts:

- **Requested:** the scheduled, human or model-selected action and exact raw choice.
- **Completed:** a valid complete generation or completed wait, with failure/cancellation separate.
- **Saved:** the journal write succeeded and has an entry ID; completion alone is insufficient.
- **Read into context:** exact saved text was loaded and included in a particular later request. This records exposure, not proof of understanding.
- **Codec applied:** the encoded vector actually entered a named step, beyond merely being prepared.

Failed or partial prose remains attempt evidence and produces no journal feedback.
A failed save remains visible. For this proposed journal path, only completed,
successfully saved entries are eligible for either return channel.

**Linguistic return** supplies words to a later model request. Start with the latest
whole entry, bounded by the journal output limit, without automatic summaries or
search. **Reservoir return** converts words into the existing 48-coordinate
handcrafted feature lane; its last 16 features remain unavailable. It does not store
recoverable journal text or demonstrate semantic understanding.

## Compare in the viewer

Propose **Compare with previous**: two synchronized surfaces, a shared cursor and
camera, fixed color/height scales, and an exact coordinate-difference trace. A banner
states the sole changed feature and all matched settings. A parallel action timeline
opens the two prompts, replies, journal receipts and application steps. Missing
measurements stay unavailable. Display external-input and semantic-input differences
separately; geometry and RMS are not measures of writing quality.

Offer two explicitly different run modes:

**Replay identical replies** isolates feedback mechanics. Prepare and retain a text
tape before comparison, including its origin and exact codec vectors from declared
reference observations. D and E receive identical text; only E injects those vectors.
Freeze vectors as well as words: current spectral shaping can otherwise change the
applied input. For H's controller isolation, both arms receive identical complete
input vectors. Replaying fixed replies cannot test whether memory improves writing.

**Generate independently** lets each arm's observations, memory and choices influence
its next request. Keep backend configuration matched and retain every actual prompt
and reply. These are interacting trajectories; reply differences are part of the
result. A temperature of zero does not guarantee identical generations.

Following [research methods](../../research/METHODS.md), record the question, expected
difference, alternative explanations and stopping point before running. Save failures
and waits alongside successes; report paired sessions and action opportunities, not
steps as independent subjects. Begin with one inspectable pair, then preselect more
seeds for any broader claim. This document runs no model and changes no live system.
