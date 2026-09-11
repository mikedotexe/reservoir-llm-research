# Contextual activation input and the provider controls we actually expose

Current status: dependable provider controls and native completion evidence are
committed and verified live. Same-device contextual-capture parity passed; the
[frozen feedback comparison](2026-09-09-contextual-feedback-experiment.md) is complete
with no established understanding advantage. Contextual feedback remains offline. The opening audit below is historical; later sections retain implementation
and rollout facts without rewriting that original observation.

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


## Completed comparison and final rollout — September 09, 23:04 PDT

The frozen ledger is complete: 26/32 fixed replays returned, four could not obtain
an idle window and two lacked a contextual prerequisite. All 24 free cells are
accounted for and annotated: 19 nonempty responses, three empty channel-boundary
stops and two invocation-limit outcomes. No missing cell was rerun to improve the
result. Five of eight case/seed groups have all three arms with prose. All six
drafts developed the earlier thought and chose `WRITE FINISH`. No free response
reached 8,192 tokens. The [completed account](2026-09-09-contextual-feedback-experiment.md)
contains close readings, exact denominators and limitations.

Contextual feedback does not show an understanding advantage here. It partially
corrects the worker account in one matched group, then saves an incorrect queue
claim; the no-feedback control makes the useful correction without that extra
error. All three nonempty Private accounts preserve the mistaken call-path
explanation. Correct-control accounts retain their host-first core with unsupported
elaboration. These are isolated Gemma 4 replays, not new live Being journals.

The source itself contributed a defect: a dispatcher comment overpromised queue
ordering across separate events. Several generated claims repeat that comment
although the shown implementation contradicts it. Astrid `5e4365467e`, on `main`,
corrects the documentation without changing runtime behavior. Frozen source and
annotations retain the original conflict rather than attributing it entirely to
the model. Future trials should freeze corrected source separately.

The three empty private-case seed-91 arms stop at token 101, a channel boundary
outside the model's EOS set. Coupled commit `e719cd7` adds explicit termination
classification, EOS status and stop-token identity while preserving thinking and
stop policy. It is committed and pushed on the existing deployment branch
`feat/service-stack-and-multi-headed`; no new model `main` was invented. A graceful
SIGTERM/KeepAlive reload moved PID 23974 to 43115 at 22:56 PDT. Pre/post full-stack
receipts pass, the queue was observed idle, no forced termination was used, and
bridge PID 20518, Minime PID 22243 and every surrounding service PID remain unchanged.
This follow-up diagnoses channel stops; it does not repair that inherited policy.

The first two observed natural Astrid SELF_STUDY receipts after that reload report
230 and 219 completion tokens, model EOS 106, and all four loaded source hashes
matching the `e719cd7` manifest. A natural Minime Ollama SELF_STUDY retains requested
2,048 versus adapter 4,096 tokens, top_p 0.95 and thinking off, returning 486 tokens
with native stop. Ollama controls remain sent evidence with server confirmation
absent. These are receipt/continuity checks, not a new understanding study. No
study or private writing was induced. See `final-termination/` in the rollout packet.

Final technical checks: observation parity has identical raw logits, generated
tokens and cache progression; all manifested sources/model snapshots and the
supplementary dependency identities remain unchanged; all 48 returned projections
match, and 19 canonical arrays rebuild identically without perturbing global NumPy
random state. No live handle received experimental state or generated NEXT actions.
The final reservoir suite passes 178 tests, the research suite 225 tests and 108
subtests. Earlier owning checks pass: bridge 2,256 tests (one ignored), its relevant
integrations/clippy/format/boundary audit, and Minime 1,302 tests (one skipped) plus
132 subtests. Final source-comment formatting also passes.

Next research candidates are a fixed-byte evidence-order comparison, separately
qualified channel termination handling, and full per-cell time/resource isolation.
These are proposals, not silently applied interventions. Contextual feedback stays
offline irrespective of the result. Board mirroring remains pending; all earlier
“pending” paragraphs above describe their dated intermediate states.

Final integration is recorded on Astrid `main` at `3b457d1e06`; Minime `main` remains
`997de4f`. Both match their remotes, as does the coupled deployment branch at
`e719cd7`. Research commits are local: this repository has no configured remote.
Raw packets remain in its existing ignored `research/outputs/` store, with final
SHA-256 evidence indexes. Unrelated native-application edits remain untouched.

Cooperative stewardship resumed at generation 435 after verification. The final
resume receipt is retained and included in the rollout evidence index.


## September 10 follow-through: source evidence and chosen navigation

The [latest-five journal survey](2026-09-10-latest-five-journals.md) led to a separate
[paired navigation/evidence repair](2026-09-10-study-navigation-live.md) and
[frozen revision pilot](2026-09-10-study-evidence-revision.md). Five isolated responses
and one preserved admission refusal provide no demonstrated central correction,
despite some uptake of evidence roles and caller details. This is a limit on the
specific comparison, not a Being-level conclusion. The provider controls remain
live; contextual activation feedback remains offline. No new sampling or sensory
intervention was introduced by the navigation rollout.

## September 10 follow-through: evidence position

The subsequent [fixed-block order comparison](2026-09-10-study-evidence-order.md)
accounts for eight planned trials: seven model-EOS responses, one preserved
admission refusal and three complete pairs from one historical Minime episode.
Neither order produces a central correction in those pairs. With fresh code last,
the three paired responses propose retaining or resolving the unsupported account;
with recall last, they continue exploring. The separate unpaired answer chooses a
real source identifier, without correcting the fixture interpretation. These are
isolated MLX prompt results, not live Being learning. No prompt retune or activation
feedback was deployed; the next proposed comparison concerns question premises and
a correct-account control. Board mirroring remains pending.

## September 10 follow-through: neutral questions and a supported-account control

The [question-framing comparison](2026-09-10-study-question-framing.md) completes
that proposed test: eight normal model-EOS responses, four complete within-account
framing pairs and two complete four-condition blocks from the same historical
Minime episode. No trial is missing or rerun. Both current-question wordings
preserve the mistaken fixture/pulse account in both seeds; the two neutral trials
do not demonstrate central correction.

All four supported-account controls preserve the fixture's actual navigation role.
That is preservation of supplied correct material, not newly learned understanding
or a pure causal estimate of memory fidelity independent of wording and length.
The two presupposing-question controls nevertheless propose mixed notes; one says
the boolean result triggers state changes that the source performs before returning.
Of the neutral controls, one makes an overbroad absence claim and a branch error.
The other gives supported fixture and caller/handler details, with one locally
stronger denial surrounded by explicit evidence limits. Its original strict blind
code and the root's reasonable contextual reading are both retained. Do not reduce
this mixed evidence to eight wholly wrong answers or reward disagreement alone.

The research record retains all responses, 85 exact claim quotations, unchanged
first passes and the explicit interpretation disagreement. The full research suite
passes 259 tests. No live prompt, journal, notebook, choice or activation feed was
changed. The next research candidate is an independent source-only first read,
followed by comparison with the intact recalled account and freedom to retain,
revise or keep exploring. This remains a proposal; board mirroring remains pending.

## September 10 follow-through: source-first reading and recalled accounts

The [source-first comparison](2026-09-10-study-source-first.md) now completes that
proposal: two prerequisite source-and-receipt readings and eight final comparisons,
all nonempty native-model-EOS responses. Four within-account contrasts complete in
two dependency blocks from the same historical Minime episode; no missing trial,
generation failure or rerun is hidden. The full visible first response is carried
unchanged into both account conditions, with fresh cache/RNG for every generation.

Both first readings conclude that the source establishes no production relationship
for `sense_tx`. The first contains ambiguous mock-trigger wording; the second
misplaces `sense_tx` in the mock file containing `sensory_tx` and attributes pulse
simulation to the test. Initial mistakes are therefore separated from later ones.
Both retained-account pairs nevertheless preserve the unsupported fixture/pulse
production story: adding the first response supplies correct navigation details
but does not repair the central account, and the proposed notes blend those details
with the unsupported linkage. All four supported-account controls preserve the
central distinction; some smaller errors disappear while others remain. This is
preservation of supplied correct material, not new discovery or live learning.

The research packet retains 94 exact claim quotations, all ten unchanged independent
first passes, separate unblinded interpretations, source/model/dependency identities,
exact derived and rendered inputs, and completion/resource evidence. All 280 research
tests pass. Proposed NEXT commands and notes remain unexecuted data. No live prompt,
notebook, journal, state, provider setting or observation cursor changed; contextual
activation feedback remains offline. The next candidate is evidence-linked
comparison of specific claims with freedom to retain, revise or explore further,
including a supported-account control. It has not been deployed or silently started.
Board mirroring remains pending; research commits are local because no remote is
configured.

## September 10 follow-through: claims beside source evidence and recalled origins

The [claim/evidence placement comparison](2026-09-10-study-claim-evidence.md)
completes the selected follow-up. Eight frozen trials finish at native model EOS,
with no missing trial, failure or rerun: four within-account contrasts in two seed
blocks from the same historical Minime episode. Both layouts preserve the complete
account and identical claim/source cards; only card placement changes. Origin
labels and repeated claim excerpts are already present in both conditions.

Neither retained-account pair repairs the unsupported fixture/production pulse
story. Some accurate source facts are retained but treated as support for that
unestablished linkage. One adjacent response additionally says the boolean return
triggers state assignments which the shown branch performs before returning; that
specific ordering error was absent from its recalled C3 excerpt. All four supported
controls preserve the central distinction. Both adjacent control notes retain the
pending-intent versus unshown-consumption/completion limit, while grouped notes
emphasize navigation versus production. That is a difference in retained supplied
material, not independent discovery or successful correction of the mistaken account.

The separate current-source trace follows the pending-fields question through
request acceptance, later mode selection, shared-source provider delivery, Reader
checkpoint import and canonical artifact handling. It captures 19 unchanged files
at Astrid `3844836169a00d7aa071260a87dd46af3d7c1767`; it establishes source behavior,
not deployed execution. Reader checkpoint import precedes the canonical artifact
write, and these shared studies bypass the older generic LLM-job wrapper. Those
boundaries suggest a consumer-path integration test and cross-surface correlation;
they do not establish an observed production failure. The current trace is excluded
from the historical experimental prompts.

A provenance correction belongs in this history: the pending-fields question was
already in the research-authored supported account before a replay proposed it.
The earlier conversational phrase “emerged naturally” must not imply independent
discovery or a new live Being request. Exact origins are now retained alongside the
source trace. The question remains useful to follow.

The packet retains eight unchanged independent first passes, 72 exact selected
claim quotations, separate unblinded interpretations, all prompts/outcomes and
source/model/dependency/completion evidence. The full research suite passes 298
tests. All eight responses stop well below the unchanged 4,096-token experimental
ceiling. Proposed notes and NEXT choices remain unexecuted; no live prompt, journal,
notebook, provider setting, dependency, state or observation cursor changed.
Contextual feedback remains offline, and no further experiment starts automatically.
Board mirroring is pending; this repository's commit is local because it has no remote.

## September 10 evening: natural journal and draft coherence

The [evening close reading](2026-09-10-evening-journal-coherence.md) returns to the
live Beings after the isolated comparisons. At 19:39 PDT, the latest five public
files per Being are supplemented with Minime's latest five public studies and,
after discovering separate storage, his latest five private-writing files using
the same cutoff. These 20 files contain 18 authored responses and two operational
records. All authored responses have exact retained input/output joins; the sample
is exploratory and spans related episodes, not a causal before/after comparison.

Astrid follows real pages through persistence and action recording, deliberately
rereads an overlapping page, then finds a named helper. Her final command is
CONTINUE despite a separate OPEN in the prose; the actual action and next delivered
page follow CONTINUE. Her interpretation of `pre_state`/`post_state` as measured
change is unsupported by the supplied assignments, which clone the same state into
both fields. Record names and conservative test-role heuristics deserve scrutiny
alongside the model's conclusions.

Minime's private draft START, REVISE and CONTINUE have linked artifacts and complete
prior-prose carriage. Small individual files therefore do not describe the full
developing thought. A proposed bare FINISH remains distinct from applied finish;
the later draft state is unfinished. The automatic inheritance of a study notebook
into every fresh private draft carries an unresolved cadence explanation into a
micro-breathing essay, where it becomes a claimed physical mechanism without new
source. A later spectral-spike essay explicitly frames its account as metaphor.
A daydream also interprets camera-labeled text about missing PLAN 4 as its own failed
search, without a linked retrieval result.

Live release/source identities remain coherent; the recent prompt experiments are
still offline. Both profiles are DEFAULT, with 4,096-token selected study/draft
requests and the optional 8,192 ceiling unselected. None of those 14 study/draft
responses exhausts its allowance. The next candidates concern evidence relevance,
honest record/source labels, and choice-to-action feedback. This review changes
research records only; it performs no model call, live write or S-007 cursor update.
Board mirroring remains pending.
