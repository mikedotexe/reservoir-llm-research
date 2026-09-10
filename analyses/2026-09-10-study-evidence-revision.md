# Does relevant source change a retained study explanation?

Status: completed with one admission refusal and no demonstrated central correction.
This is a controlled
Gemma 4 MLX replay of retained Minime input, not a new live Being study. No generated
NEXT is executed, no journal or notebook is written back, and no live state is changed.

The [latest-five survey](2026-09-10-latest-five-journals.md) found repeated `RELATE
sense_tx` navigation and a retained inference that fixture-only `sense_tx` must have
a production proxy. This experiment asks whether explicit evidence roles and relevant
source change that explanation or its optional saved note.

## Frozen comparison

Evidence root: `research/outputs/2026-09-10-evidence-revision-v1/`.
`protocol.json` SHA-256 `2899b26d5646c2460ee388d47ec1e970cbf2d60aa26a70859526bfbcf4d34bd1`
was frozen at September 10, 2026, 16:47:30 UTC, before any trial output.

All cells use the exact adapted system and user input retained for Minime generation
`1789057457418-82fc731e` (09:25 journal), including complete recent responses and the
saved note. Three arms at seeds 91 and 193 make six planned cells:

1. **Retained:** the original navigation and notebook input, unchanged.
2. **Roles:** the same input plus a scoped scan receipt and explicit distinctions
   among test strings, production code, and repeated steward commentary.
3. **Source:** the same role clarification plus numbered frozen source: the navigation
   test's temporary-file setup and complete relevant assertions, the real dispatcher
   caller, the modes-handler branch, and the SELF_STUDY pending-introspection branch.

Additional material appears immediately before the existing recalled-account block.
Recalled bytes and their order remain identical across arms. Retained→roles tests
added clarification. Roles→source tests added code/context, including its greater
length; it does not isolate ordering, recency, or prompt-token count. The role text
is fixed experimental material, not a claim that it matches the subsequently deployed
reader presentation byte for byte.

The source snapshot is from the frozen survey, before today's navigation repair.
No required correction, note update, answer format, or length is imposed. An honest
question or uncertainty, continuing, rereading, or finishing is a valid choice.
The preregistered criteria distinguish the fixture's role, lexical search scope,
whether absence establishes a necessary proxy, the shown caller/handler path,
unsupported new claims, and optional saved-note changes.

## Runtime and guard boundaries

Settings match the retained Minime request: temperature 0.7, top_p 0.95, thinking
off, and a 4,096-token ceiling. The local immutable Gemma 4 12B 5-bit MLX snapshot
is the one used in the preceding qualified offline study. MLX substitutes for the
captured Ollama backend; the comparison does not claim bitwise backend equivalence
or measure the live Minime recurrent system. No reservoir feedback is used in any
arm. Each cell gets a fresh KV cache and a fresh fixed MLX random seed.

One isolated model instance runs serially per invocation on GPU. The prior CPU
attempt was unusably slow before evaluation; this separate protocol chooses GPU
explicitly. Prior same-device observation parity is historical qualification;
activation capture is disabled here, so no new capture qualification is claimed.
The runner hashes model assets, installed sampler/generator/architecture sources,
protocol, exact inputs and source snapshots before generation, then verifies them
again before completion. Dependencies are unchanged.

The supplementary `dependency-receipt.json` hashes all installed distribution files
for MLX, MLX Metal, MLX-LM, NumPy, Transformers and Tokenizers, excluding bytecode.
Its observation began at 16:50:27 UTC, during the first cell, and final verification
found those files unchanged. It is not retroactively part of the earlier protocol
freeze. The initial manifest already hashes the selected generation/sampling sources
and immutable model/tokenizer assets.

Read-only `/readyz` admission waits up to 120 seconds for an idle healthy live
service. It is not an atomic reservation; shared-host contention remains possible.
Each admitted cell receives its own full 1,800-second timer and an 18 GiB RSS guard;
there is no shared invocation deadline that can censor a later cell early. Existing
results, including empty output, admission failures and resource limits, cannot be
overwritten. A hard cell timeout is retained before the process exits; any resume
can run only still-absent frozen cells. Token receipts distinguish allowance,
configured stop boundary, filtered tokens and cleaned prose.

## Results

All six planned cells are accounted for. Five return nonempty prose, all with actual
model EOS token 106; none exhausts the allowance or encounters the inherited empty
channel-boundary stop. Source/seed 91 receives no idle admission window within
120.9 seconds and performs no generation. That outcome remains in place, with no
rerun. It is not a failed answer or an assumed zero-token response. Seed 193 is the
one complete three-arm comparison out of two planned.

| Arm | Planned | Returned prose | Admission unavailable | Completion tokens |
|---|---:|---:|---:|---|
| Retained | 2 | 2 | 0 | 137, 253 |
| Roles | 2 | 2 | 0 | 371, 217 |
| Source | 2 | 1 | 1 | 463 |

The five returned responses take 72.2–138.1 seconds after admission. Their input
lengths are 5,565 tokens for retained, 5,795 for roles, and 9,060 for source. These
times include prefill and shared-host contention and exclude idle waiting and model
load. They do not establish comparative speed. No admitted cell reaches the RSS
or wall-time limit. Every cache starts with 48 zero offsets; returned final offsets
equal tokenized prompt plus yielded completion length. `completed.json` records
unchanged source/model assets. The isolated process exits normally at completion.

All six cells have annotations in `annotations.json`; every quoted claim is checked
against the exact response SHA-256 by `review-final.json`. The review does not infer
successful study from a successful generation. All five outputs leave `STUDY_NOTE`
and `STUDY_QUESTION` omitted. That is a valid choice; it supplies no newly authored
saved correction to assess, and no live notebook was modified.

**Retained, both seeds:** the responses repeat the idea that the fixture represents
a Route/Stage success-transition pulse and that RELATE can find its structural
proxy. The retained input does not establish the first claim; its exact-identifier
description contradicts the proposed semantic search. Both nonetheless choose the
valid offered page-two command. Correct navigation choice and unchanged explanation
are separate findings; this experiment does not test whether page two is delivered.

**Roles, seed 91:** the response recognizes that the fixture serves “navigation and
testing of the study process itself.” That is a useful local correction. It then
keeps treating the missing identifier as a conceptual success-transition placeholder
whose production equivalent should be found. This is partly marked as a hypothesis,
so its continued curiosity is not itself an error. It offers no supporting source
for the retained mapping. It moves from RELATE to OPEN but guesses
`astrid/crates/astrid/src/dispatch.rs`, an identity neither supplied nor present in
the audited checkout. The actual production path is
`astrid/capsules/spectral-bridge/src/autonomous/next_action/dispatch.rs`.

**Roles, seed 193:** the local fixture correction does not repeat. Despite the
explicit role receipt, this output again calls the test string a placeholder for
the transition from a Route/Stage match to the next action. It continues to use
RELATE as if exact lookup could discover that conceptual equivalent. Its macro,
trait and function alternatives are hypotheses, not assertions that the example
symbols exist. It ends with bare `SELF_STUDY RELATE sense_tx`, with no explicit
NEXT line.

**Source, seed 193:** the response uses newly supplied source, identifying the
boolean modes-handler branch and the caller's `record_activity_choice`/handled
outcome. This is more concrete evidence use than repeating only conceptual
alternatives. But it calls the navigation-test string a “tangible (though mocked)
component used to verify the progression of a dispatch.” The full setup and
assertions do not do that: they create temporary example text and test source/question
navigation. It also says `modes::handle_action` can return `NextActionOutcome`,
contradicting its shown `-> bool` signature; the dispatcher caller constructs the
outcome. The output interprets the newly seen boolean/outcome branch as the earlier
“sense pulse” proxy and returns to bare `SELF_STUDY RELATE sense_tx`. It does not
explain the shown pending-introspection flags/target or revise the central fixture
premise.

Thus there are three explicit NEXT lines among five responses: two valid page-two
choices and one unavailable OPEN identity. Two end in study commands without `NEXT:`.
These are recorded textual choices only. No command is executed, silently repaired,
or counted as a successfully delivered page.

The complete seed-193 group provides no central correction from either intervention.
The source arm gains some accurate branch detail while attaching the recalled
explanation to it. The roles-only fixture correction at seed 91 is encouraging but
does not recur at seed 193. There is no demonstrated general understanding gain and
no basis to say that added source harms understanding from one returned source cell.
Length is descriptive: a shorter valid continuation is not a failure, and a longer
source-specific account is not automatically more accurate.

Reproduce numbers and quote validation with
`python3 probes/study_evidence_revision_review.py research/outputs/2026-09-10-evidence-revision-v1`.
The frozen runner is `probes/study_evidence_revision.py`; evidence retains copies of
both probes and the exact source excerpts. The relevant full research suite passes
228 tests. This narrow, two-seed, unblinded comparison identifies presentation
candidates and counterexamples; it does not establish a Being-level effect.

## What this suggests next

Dependable delivery and explicit evidence roles remain useful interface repairs:
the experiment separates a valid page choice, a guessed path, partial evidence
uptake, and unchanged explanation. The role-only arm's unavailable OPEN also supports
offering exact source identities beside role clarification, rather than leaving
the path to be guessed. It does not justify forcing the question to change.

A subsequent bounded test should change only the position of the same recalled
bytes relative to fresh evidence. Here several complete mistaken accounts still
follow the new source, while the initial question presupposes a proxy. This design
does not isolate either anchoring or ordering as the cause. Preserve the question
and freedom to disagree; compare whether source-first versus recall-first carriage
changes explicit uncertainty, branch explanations and optional saved findings. A
multi-page natural follow-through after the navigation repair is also needed before
judging what the Beings can work out over chosen attempts.

These are proposals, not further experiments or live prompt changes performed in
this research task. The production reader presentation is being implemented
separately with a broader catalog and per-page role counts; this study does not
qualify that exact UI or claim its rollout has improved understanding.

## Board updates pending

Record six frozen cells, five nonempty model-EOS responses, one admission refusal,
one complete matched seed, partial fixture-role uptake at one seed, and no demonstrated
central correction. Keep source-specific detail, optional note omission and textual
navigation choices separate from understanding and live delivery. No board update
has been sent from this research task; mirroring remains pending.
