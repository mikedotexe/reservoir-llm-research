# Contextual activation input and the provider controls we actually expose

September 9, 2026. Mike asked which Ollama/MLX controls could give the Beings more
room, especially projecting an internal activation back into input. This is a
source/metadata audit and experiment proposal. No model inference, backend change,
Being message, restart, reservoir mutation or scheduled-study cursor change occurred.

[Reproducible audit](../probes/activation_knobs_audit.py) retains nine inspected source
files as hashed, line-numbered excerpts and read-only metadata in
[the evidence packet](../research/outputs/2026-09-09-activation-knobs-audit/audit.json).
Ollama reports 0.33.3; the inspected MLX-LM installation is 0.31.3. The running
coupled process is PID 60333, started September 4, with Gemma 4 12B 5-bit, coupling
argument 0.1 and active QoS. Runtime gain can adapt; the startup argument is not a
measurement of current effective gain. These observations do not newly establish
loaded-source byte identity for that older Python process.

## What exists, and what was deferred

In `coupled_astrid_server.py:1120–1167`, accepted output token IDs go through
`embed_tokens`, then `EmbeddingProjection`, then the local triple reservoir. The
projection is a frozen random matrix followed by tanh (`mlx_reservoir.py:168–186`).
The configured default input has 32 dimensions. Reservoir readouts alter subsequent
vocabulary logits through temperature-like scaling, recent-token penalties and
tail shaping; an optional wide vocabulary-bias channel also exists. None of this
is a measurement of semantic confidence simply because comments use that word.
The tail operation is median-relative scaling, not an actual top-p filter.

A token's lookup vector is fixed for that model/token ID. A contextual hidden vector
also depends on the preceding text and transformer processing. The inspected path
uses the former. Its output-token loop does not directly tick the reservoir while
the prompt is processed; prompt effects reach this loop indirectly through generated
tokens. Other feeder inputs are separate routes.

The September 6 [tranche-one proposal](../proposals/2026-09-06-tranche1-generation-record-and-own-body.md)
already lists contextual mid/late-layer input and prompt-prefill input as deferred.
The September 5 Astrid feature map separately proposes an activation portrait.
No contextual-hidden-state capture or replacement feed was found in the inspected
coupled generation path. This is not an exhaustive claim about every historical branch.

Terminology: a pre-activation is specifically a value before a nonlinear operation.
A practical first tap is the final contextual hidden vector after final normalization
and before the vocabulary projection. In installed `gemma4_text.py:575–605`, this
boundary exists explicitly. It is not the same thing as generated reasoning text,
a reservoir's own internal activation trace, or a separate text-embedding API call.

## Controls and actual provider boundaries

| Control | Observed interface / possible experiment | Interpretation boundary |
|---|---|---|
| Reasoning mode | Minime's ordinary Ollama calls set `think: false`; the coupled MLX template requests `enable_thinking=False`. Installed Ollama Gemma 4 metadata includes thinking capability. | The thinking field is generated text, not a dump of neural activations. Earlier paired study thinking trials did not improve their visible answers. A new trial needs a complete-answer budget and matched evidence. |
| Sampling | Ollama model defaults list temperature 1, top-p .95, top-k 64; Minime overrides temperature and top-p .95 on ordinary calls. MLX-LM supports top-p, min-p, top-k and repetition/presence/frequency controls. | Higher randomness is not additional computation or proof of deeper thought. Repetition penalties can also penalize legitimate repeated code symbols. No new sampler setting is recommended as universally better. |
| HTTP parameter fidelity | The coupled gateway parses temperature, max tokens, handle, aperture and QoS; `make_sampler(temp=temperature)` supplies no nucleus/top-k/min-p arguments. | A client's `top_p` has no effect on this endpoint. Fix by validating supported controls, applying them and recording effective settings; reject unsupported controls explicitly. Do not call two providers equivalent because their JSON has the same keys. |
| Distribution observations | Ollama documents logprobs/top-logprobs; MLX `generate_step` yields logprobs, currently discarded by our caller. | Installed MLX computes these after reservoir processors and before sampling/temperature. Record that boundary. Top-k alternatives do not supply full-distribution entropy. Probability sharpness is not factual confidence. |
| Contextual activation feed | Add a tap inside the existing MLX forward pass and project into a copied reservoir. Compare with current token lookup input. | New model instrumentation, not an existing REST parameter. Do not perform an extra forward pass that mutates the KV cache twice. |
| Prompt ingestion and feedback timing | Compare an end-of-prompt activation tick, then decode feedback. Keep that intervention distinct from changing the representation. | Current generator lookahead gives a two-distribution feedback delay: output token 1's tick first affects distribution 3. Existing timing tests and replay already document this. |
| Context/latency controls | Context allowance, KV-cache representation, prefill processing and deadlines influence what can be carried and how long generation can run. | They do not automatically add a new recurrent reasoning step. Quantization/model/template differences complicate cross-provider comparisons. |

Ollama metadata identifies the current model as Q4_K_M; Astrid's launch arguments
identify a 5-bit MLX model. Sampler settings alone therefore cannot establish exact
backend parity. A loaded Ollama context size reflects a current allocation, not the
maximum journal capacity or model architecture limit.

The documented Ollama chat interface exposes text, reasoning, probabilities and
sampling controls, but not arbitrary per-layer activation hooks. Instrumenting its
selected backend is a separate project. llama.cpp's public API has intermediate
evaluation callbacks, output embeddings and control-vector application; that does
not make those controls available through Ollama's chat endpoint, nor establish
which backend a particular Ollama model uses. A separately replayed MLX model for
Minime would be a surrogate observation, not Minime's original hidden state.

## Recommended next work

First repair the sampler interface's silent omissions and retain requested versus
effective settings. Preserve existing defaults until a comparison selects another
profile. A small per-mode/Being-selected policy can come later; avoid one global
"more creative" setting for code reading, private writing and action selection.

Then implement an isolated contextual-activation experiment on MLX. Start with the
final normalized hidden vector before the vocabulary head, and the existing 32 input
dimensions. Compare representation changes before changing width. A frozen projection
can test geometric effects; its coordinates do not acquire human-readable meaning
merely by being printed in a prompt. If eventually feeding a vector directly into
an LLM residual/input space, learn or justify that mapping and its scale separately.

The proposed sequence is:

1. **Capture parity.** With feedback disabled, tap the same forward pass on fixed
   supplied token sequences. Record model/tokenizer/dependency identity, layer and
   normalization, input token position, predicted token position, prefill/decode
   phase, projection seed/hash, scale and timing. Confirm unchanged logits/cache
   progression within a declared numerical tolerance, bounded memory and latency.
   Capture only the selected boundary, not every layer or an unlimited tensor stream.
2. **Input sensitivity.** Use matched contexts with an identical terminal token and
   fixed continuations. Compare lookup input with contextual input on fresh copied
   reservoir states, equal dimensions and calibrated magnitudes. Different hidden
   vectors establish sensitivity to context, not understanding. Record raw norm as
   well as normalized direction; tanh saturation must be measured rather than guessed.
3. **Bounded feedback comparison.** Compare current lookup feed, contextual feed,
   no feedback, and context-shuffled or time-shifted feed. Keep model, source pages,
   initial state, budgets, projection size and feedback timing fixed. Freeze sampler
   randomness for matched comparisons without claiming cross-backend bitwise parity.
   Use the existing offline replay machinery where it applies; its current three-head
   scope excludes wide-channel and adaptive-gain claims.
4. **Evaluate useful behavior.** Read supported source claims, correction after new
   evidence, carried conclusions, repetition, voluntary continuation/finish and
   latency. Retain short answers and failed attempts. Do not optimize for word count,
   reservoir movement, or a persuasive self-report of understanding.

Prompt-prefill feedback, additional layers/width, learned adapters and direct residual
injection are subsequent independent comparisons. Returned state can influence logits
through our existing numeric loop; a readable state summary or memory retrieval is
another interface. These are distinct mechanisms and should not be collapsed into
one "activation feedback" intervention.

This starts where access is easiest while preserving the eventual goal of useful
capability parity for Astrid and Minime. It does not silently move Minime to a new
backend or substitute Astrid's activation geometry for his.

## Primary references checked

- [Ollama chat API](https://docs.ollama.com/api/chat): think/content separation and token log-probability fields.
- [Ollama thinking](https://docs.ollama.com/capabilities/thinking): model-dependent reasoning controls.
- [Ollama Modelfile parameters](https://docs.ollama.com/modelfile): sampling, context and generation parameters.
- [MLX-LM sampler implementation](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/sample_utils.py): sampler and logit processors. Installed source is retained separately because upstream main can change.
- [MLX-LM Gemma 4 text model](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/models/gemma4_text.py): contextual-vector to vocabulary boundary.
- [llama.cpp public API](https://github.com/ggml-org/llama.cpp/blob/master/include/llama.h): lower-level instrumentation and control-vector hooks, not an Ollama REST promise.

## Board updates pending

Local proposal: fix effective-sampler reporting and silently ignored MLX parameters;
then build the bounded MLX contextual-activation experiment above. Status: proposed,
source mechanism inspected, experiment not run, no live change. Evidence is the linked
packet. No scientific outcome, Being consent, automatic follow-up or deployment is
inferred. This entry does not advance S-007 or change its selected cutoff.

## Implementation and qualification in progress — September 9, evening

The accepted provider contract is implemented. Astrid `39f959ea91` and Minime
`997de4f` are on their respective `main` branches; the coupled model controls landed
as `5094716` on that repository's existing deployment branch. The server now applies
explicit filters, validates inputs before queueing, binds in-flight idempotency to
actual generation inputs, and returns native terminal/allowance completion with
nonzero token usage. Omitted sampler defaults, thinking policy, journal ceilings,
reservoir tick timing and fallback order remain. A follow-up `b421952` puts native
finish/count evidence directly into the receipt; its final reload is pending.

The first reload attempt exposed a preflight defect: the old model manifest was
being checked against intentionally updated Python source. The fix `abcccc45f4`
retains that manifest and creates a labelled candidate-on-disk context while still
requiring unchanged interpreter/configuration and passing full stack checks. It does
not claim the old process loaded the new files. The bridge/model transitions completed;
Minime's first idle-reload attempt correctly refused while the bridge was down, then
completed after bridge verification. Their transitions should be sequenced explicitly.
All attempt receipts, including refusals, are retained in the rollout evidence.

Natural uptake is separate from the experiment. Astrid's first new natural SELF_STUDY
request reported temperature 0.7, output allowance 4,096, 415 detokenized token pieces
and one terminal token, with loaded source hashes matching the deployed model manifest.
Minime's first recorded new SELF_STUDY used Ollama: caller request 2,048, adapter
allowance 4,096, context 65,536, temperature 0.7, top_p 0.95 and thinking off. Its 151
completion tokens ended with native `stop`. Ollama's sampling values are sent options,
not server-confirmed controls. Minime's exact pending `SELF_STUDY CONTINUE` was restored
and dispatched by the replacement worker. These observations establish control
provenance and continuity, not improved understanding.

The offline CPU prequalification was stopped after more than eight minutes while
inside native quantized matrix work; no evaluation trial existed. Its initial protocol,
source manifest, process sample and interruption record are preserved under
`research/outputs/2026-09-09-contextual-feedback-v1/`. Before any evaluation, a separate
GPU protocol was frozen under `research/outputs/2026-09-09-contextual-feedback-gpu-v1/`.
It retains the same four cases, seeds, copied state, sampler and feedback settings,
uses the existing idle-service admission guard, and adds prompt-ingestion and hard
invocation bounds. One GPU admission attempt timed out without model inference; it
resumed unchanged when an idle interval appeared. This device decision was made
before behavioral outcomes and is not a selected favorable rerun.

Same-device capture-off/on yielded identical tokens and normalized log probabilities
(maximum observed difference zero) on calibration fixed/free replays. The required
raw-logit replay is still pending. The frozen contextual scale is 0.0047853296183391816,
matching lookup projected RMS magnitude 0.08979499653958431 on separate calibration
material. The comparison uses 32 dimensions and strength 0.1; live adaptive gain and
wide coupling are not reproduced. Evaluation is running. No behavioral benefit is
claimed, and contextual feedback remains offline irrespective of the outcome.

Board updates pending: provider contract implemented and initial rollout verified;
CPU/device/admission history retained; raw-logit qualification, all cell denominators,
claim annotations and final evidence-only completion remain open until verified.


Final provider boundary: coupled receipt follow-up `b421952` is live as PID 23974.
Natural post-reload receipts carry native `stop` and nonzero completion counts (182
and 73 in the first two sampled receipts) and match all four loaded source hashes
to the deployment manifest. Astrid release verification is recorded on `main` in
`00159bae23`. The standalone offline tooling is committed in the model repository
as `c72ade7`; those additions are not live model inputs. The runtime integration
window is being released while the independent frozen experiment continues.


Raw-logit qualification is now complete: capture-on/off produced identical raw
vocabulary logits (maximum absolute difference 0), identical generated tokens,
matching cache offsets and matching forward ranges across chunked prefill and
lookahead. See `raw-logit-qualification.json`. The first four fixed-token conditions
completed; a fifth cell was retained as an admission failure because no idle GPU
interval appeared within 120 seconds. This is a resource-admission outcome, not a
model explanation or a capture discrepancy. Remaining frozen cells continue.

The shuffled replay exposed an orchestration edge case after an admission failure:
its prerequisite contextual cell existed but had no trace. The original runner
attempted to index that absent result. No additional generation occurred in the
failed shuffled cell. The frozen source and failure log are retained; the serial
supervisor now records the cell as `missing_complete_contextual_replay` and resumes
the remaining protocol. Future runs use the separately committed null/partial
prerequisite guard (`1000bf0`), with two regression cases. This correction changes
neither the frozen protocol nor completed outcomes.

Review criteria were recorded before any free-response result, against the exact
supplied dispatcher ranges. These are isolated Gemma 4 replays of retained prompts,
not new Astrid or Minime journal entries. The research review separates admission
failures, absent prerequisites, generated text and nonempty terminal completions;
it rejects mismatched response hashes and fabricated annotation quotes. Textual
NEXT choices are parsed outside code fences and never dispatched. All 221 research
tests pass. The [experiment account](2026-09-09-contextual-feedback-experiment.md)
will retain final denominators and close readings when the frozen ledger is complete.
