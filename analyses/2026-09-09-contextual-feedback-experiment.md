# Contextual feedback: frozen Gemma 4 comparison

Status: completed with resource and interpretation limits. Provider controls and
completion reporting are committed and live. Contextual feedback remains offline.
The [implementation history](2026-09-09-activation-input-and-provider-knobs.md)
preserves the original audit, implementation and rollout boundaries.

This is an isolated Gemma 4 comparison using retained study/draft inputs and a
copied Astrid triple-reservoir state. These are not new live Being studies or a
Minime backend migration. The result does not establish an understanding advantage
from contextual feedback.

## Protocol and qualification

Evidence root: `research/outputs/2026-09-09-contextual-feedback-gpu-v1/`.
The immutable protocol fixes four cases, two free-generation seeds (91 and 193),
temperature 0.8, top_p 0.95, thinking off and an 8,192-token output ceiling. Free
generation has lookup, contextual and no-feedback arms: 24 planned trials. Fixed
49-token replay adds shuffled contextual order and a zero-state control: 32 planned
cells. Fixed prose is imposed and cannot establish improved understanding.

All arms share the 32-dimensional projection (seed 137), canonical reservoir weights,
fresh caches and copied initial states. Coupling is fixed at 0.1; wide coupling and
adaptive gain are disabled. These depart from the full live loop. The contextual
scale 0.0047853296183391816 was calibrated on separate rain/river material to match
lookup projected RMS magnitude 0.08979499653958431 and then frozen.

With wide coupling disabled, the reservoir returns three scalar modulations of
temperature, recent-token repetition penalty and low-probability tail scaling
(`mlx_reservoir.py::ReservoirLogitProcessor`). The contextual vector is not inserted
into the model's residual stream or prompt. A behavioral null constrains this
particular feedback route, not every possible use of contextual activations.

Capture observes the installed Gemma 4 final normalized hidden vector before
vocabulary projection, within the same forward call. Absolute token positions
account for generator lookahead and retain the existing two-distribution feedback
delay. The end-of-prompt vector is retained for observation and is not fed back.
Projected traces retain first/last 64 rows, with selected full-vector checkpoints.
Shuffled order applies only to imposed-token replay; it cannot establish what a
free continuation would have done under reordered future activations.

Same-device observation parity passed: capture-off/on tokens, raw vocabulary logits,
normalized log probabilities, cache offsets and forward ranges matched. Maximum
observed raw-logit difference was zero, within `rtol=1e-5`, `atol=1e-5`.
This qualifies observation fidelity on the retained replays, not behavioral benefit.
Dependency versions, model assets, source hashes and projection identity are in
`manifest.json`, `qualification.json` and `raw-logit-qualification.json`. Exact
manifested source copies are retained under `source-snapshot/`.

A supplementary `dependency-receipt.json` hashes installed distribution files for
MLX, MLX Metal, MLX-LM, NumPy, Transformers and Tokenizers. Its observation begins
after fixed replay started and before free-response files existed; it does not
retroactively broaden the earlier manifest. Final verification found those files
unchanged. Dependencies were not installed or modified for this work.
`numerical-receipt.json` verifies all 48 returned-trial projections and bit-identical
reconstruction of 19 canonical arrays under different global NumPy seeds; construction
preserves the global NumPy random state. This is a supplementary reconstruction,
not retroactive per-trial instrumentation.

## Execution and missingness

The default CPU attempt stopped during prequalification native matrix work after
more than eight minutes, before any evaluation. Its original protocol and interruption
record remain under `research/outputs/2026-09-09-contextual-feedback-v1/`. The GPU
protocol was frozen before evaluation outcomes, retaining selected cases and settings.
GPU admission uses the existing read-only idle-service check, not an atomic resource
reservation. Admission failures and resource bounds remain outcomes, with no
response-based reruns. One isolated model instance ran serially per invocation.

Two free cells (`worker`, seed 91, no feedback; `correct_control`, seed 193, lookup)
encountered the 1,800-second invocation bound without a returned result. The
supervisor retained explicit `invocation_resource_limit` cells and resumed remaining
cases without rerunning them. A shared invocation deadline can leave a late-starting
cell less time than its nominal per-trial allowance. This is protocol-related
censoring, not evidence of 8,192 tokens consumed, chosen silence or failed understanding.
A later study should admit a cell only with its full per-trial time allowance.

An unavailable contextual replay exposed a null-prerequisite orchestration defect.
The frozen runner and error log remain; the supervisor recorded those shuffled
cells as unavailable without generation. Future source commit `1000bf0` rejects
null/partial prerequisites cleanly. Completed experimental source and outcomes
were not rewritten to incorporate the repair.

Per-cell seconds measure generation and capture after admission; they exclude the
idle-window wait and initial model load, and include shared-host contention.
Supervisor logs retain invocation boundaries, handoff and admission refusals.
Retained-trace averages use first/last projected rows, not necessarily every token.

## Final denominators

All 56 cells are accounted for: 48 generation receipts and eight explicit unavailable
outcomes, with zero missing files. `integrity-final.json` verifies source/snapshot
identity and required evidence. No live state was written and no generated NEXT
instruction was executed.

| Fixed condition | Planned | Full 49-token replay | Admission unavailable | Prerequisite unavailable |
|---|---:|---:|---:|---:|
| Lookup | 8 | 7 | 1 | 0 |
| Contextual | 8 | 6 | 2 | 0 |
| None | 8 | 7 | 1 | 0 |
| Shuffled contextual | 8 | 6 | 0 | 2 |
| Total | 32 | 26 | 4 | 2 |

All completed teacher sequences match and end with `length` at the imposed allowance.
For each initial-state type, lookup final-state norms match across available cases;
contextual and shuffled feeds can produce different norms. No retained contextual
coordinate exceeded the saturation threshold. These are mechanical checks, not
understanding scores. Missing fixed cells are worker/zero lookup, contextual and
shuffled; private/persisted contextual and shuffled; private/zero none.

| Free condition | Planned | Returned stop | Nonempty prose | Empty channel boundary | Invocation limit |
|---|---:|---:|---:|---:|---:|
| Lookup | 8 | 7 | 6 | 1 | 1 |
| Contextual | 8 | 8 | 7 | 1 | 0 |
| None | 8 | 7 | 6 | 1 | 1 |
| Total | 24 | 22 | 19 | 3 | 2 |

There are five complete three-arm comparisons with prose out of eight planned
case/seed groups: worker/193, private/193, correct_control/91 and both draft seeds.
Source cases supply 13 nonempty accounts from 18 planned cells; drafts supply six
from six. No free response reaches the ceiling; nonempty responses use 376–1,132
tokens. Returned-response median generation/capture times are 110.1 seconds for
lookup, 117.5 for contextual and 135.0 for none. These unpaired, censored summaries
include short empty stops and contention; they do not establish a speed advantage.
Resource-limit cells have no token receipt and are not zero-token generations.

## Close reading

Review criteria in `claim-review-criteria.json` were saved before the first free
response. All 24 free cells have hash-verified annotations in `claim-annotations.json`;
quotes are checked against exact responses. `review-final.json` contains the ledger,
parsed choices, annotations and matched-case denominators. Reproduce it using
`probes/contextual_feedback_review.py`.

**Worker case.** Lookup at both seeds recognizes queueing but retains the misleading
synchronous/asynchronous contrast and omits the persistent worker. Contextual seed
91 claims the single path avoids a queue/new task, contradicted by source. Contextual
seed 193 makes a useful partial revision: it distinguishes submission from actual
execution and recognizes the dedicated queue worker. Its final note then says,
“Both eventually rely on the capsule's internal `mpsc` queue for execution.” The
multi-chain task shown invokes directly. No-feedback seed 193 makes the same useful
worker correction and saves an accurate note about the single path remaining
asynchronous through its queue; it does not add the shared-queue error. Both still
overgeneralize about identical result handling. The clearest target correction in
this matched group occurs without feedback; contextual feedback has no established
advantage.

A material source qualification emerged: the supplied dispatcher comment at lines
249–251 incorrectly promises per-capsule queue ordering for all events. The generated
overgeneralization echoes actual provided documentation while contradicting the
implementation. It is not wholly invented. Astrid `5e4365467e` corrects this comment
to distinguish queued single-interceptor events from directly invoked chains.
Runtime behavior is unchanged. The frozen experiment retains the original comment.

**Private case.** All seed-91 arms return the same four-token sequence
`[100,45518,107,101]` and no cleaned prose. The inherited policy stops at token 101,
`<channel|>`, absent from the model configuration's EOS set `[1,106,50]`. This is a
completion-policy issue, not chosen silence or token-budget exhaustion.
`token-termination-audit.json` retains exact tokens and source identities.
Production commit `e719cd7`, gracefully loaded as PID 43115, adds termination evidence
with boundary classification and stop-token identity. API `stop` still means the
configured server stop policy; it alone does not establish a complete answer.
Thinking and stop policy remain unchanged, as do all frozen inputs and outputs.

All three seed-193 Private accounts retain both target misconceptions: caller
acceptance is restricted to the multi-chain path, and a post-invocation failure
helper supplies independent admission validation for a local-provider fast path.
They cite individual predicates accurately while placing them incorrectly in the
call path. Each saves the misconception in `STUDY_NOTE`. This matched group provides
no evidence of correction from contextual feedback.

**Correct control.** All five nonempty accounts retain the correct host-first
filtering core, with unsupported elaboration. The frozen input has a correct current
note but also an older response placing authorization inside invocation: it is a
mixed-history retention control, not an uncontaminated correct explanation.
Guest-side stateful authorization and end-to-end guarantees exceed the shown snippets.
Questions about how a host mediates a Private route are valid questions, not evidence
of fabricated symbols. Host mediation may exist elsewhere; verdicts are scoped to
supplied evidence. Two seed-193 accounts also repeat the misleading ordering comment.
Annotations distinguish support from documentation from contradiction by implementation.
This is retention of a correct core, not five wholly accurate accounts.

**Private drafts.** All six continuations develop the prior distinction between
collecting code facts and connecting them into an account. They discuss dependencies,
untaken branches, failure paths and predictions under changed conditions. All choose
`WRITE FINISH`. Retained quotes show conceptual development in every arm, with no
demonstrated contextual advantage. Drafts have no fresh source; their metaphors and
hypothetical examples cannot demonstrate dispatcher understanding.

All 13 source accounts choose further reading: twelve `SELF_STUDY CONTINUE` and
one `SELF_STUDY OPEN 573` in correct-control seed 91 without feedback. These are
textual choices in isolated outputs, never executed actions. Repeated worker
contrasts and Private misconceptions persist despite the expanded ceiling.
Accurate-looking predicate quotations coexist with incorrect call-path explanations.
Length and reservoir movement are descriptive, not success criteria.

The small selected case set, two seeds, unblinded review, mixed-history control and
resource-related missingness preclude broad superiority claims. The experiment
qualifies the observation mechanism and provides actionable interface/source findings;
it does not establish improved understanding from contextual feedback.

## What this makes worth testing next

1. Test evidence presentation: place the same recalled bytes before fresh source,
   and compare revision and retained conclusions. The current prompts put substantial
   mistaken recall after fresh code, but this trial does not isolate an order effect.
   Freeze corrected documentation into a separate future protocol.
2. Qualify channel parsing and termination policy on separate fixtures and model
   replays before changing it. The production receipt diagnoses the empty boundary
   outcome; it does not repair the inherited behavior.
3. Give each admitted cell its full time allowance and stronger resource isolation
   before comparing latency. Preserve this study's failures rather than rerunning
   missing cells to improve the outcome.

No technical capture failure occurred. This negative/inconclusive behavioral result
completes the study. Contextual feedback remains offline regardless. Live activation,
wider projections, learned adapters, residual injection and Minime backend migration
require a subsequent reviewed plan.

## Board updates pending

Provider changes are live, observation parity passed, all 32 fixed and 24 free cells
are accounted for, and all 24 free cells are annotated. No contextual understanding
advantage is established. Record the source-comment correction and termination
diagnostic separately from behavioral benefit. Board mirroring remains pending;
`board/activation-input-pending.json` holds the local update.
