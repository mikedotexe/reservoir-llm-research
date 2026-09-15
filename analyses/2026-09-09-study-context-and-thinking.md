# Recent study context and a bounded thinking trial

Mike approved the three changes proposed from his nine selected Minime journals:
preserve useful context for both Beings, make synthesis easier, and test dedicated
thinking. This follows [HSS-13's finding](2026-09-09-minime-nine-studies.md): the
4,096-token allowance worked, but a 700-byte opening excerpt discarded a useful
conclusion. This account separates implementation, controlled replay, model trial
and the later live boundary. It does not rewrite the earlier observations.

## Shared implementation

Astrid `a376a11b5bfef8ef63e607ed7f986441c4c57805` and Minime
`3383aef12d6794ef1492667472c5a549c752206a` are committed and pushed to main.
Each inquiry now retains up to four recent visible responses, with source and
response identities, alongside the Being's lasting finding/current question.
The rendered notebook JSON has a 9,000-byte allowance. Oldest accounts drop whole
first; an oversized remaining answer retains beginning and ending with explicit
omission and `complete=false`. Stored prose is capped at 16,000 bytes per response;
note/question caps are 1,600/500. Legacy excerpts are never relabeled complete.

Both Beings receive optional exact RELATE commands beside valid symbols in their
own question and a two-page SESSION command for recent distinct source locations.
The prompt welcomes implications, changed answers, unresolved questions and useful
tests. No compulsory report, minimum length, extra generation or chosen Action is
introduced. Source references identify earlier input, not independently verified
claims or known answer locations.

The complete protected system/reference input fits within 24,000 bytes. SELF_STUDY
Ollama requests use 32,768 context tokens with the existing 4,096 output ceiling;
MLX/fallback admission preserves the same input. Other journal modes keep their
increased ceilings. Version 3 migrates earlier reader state; old readers reject it.
Rollback must reconcile later state, never replace it with a stale checkpoint.

## Controlled carriage replay

[The reproducible probe](../probes/study_context_replay.py) replays all nine saved
visible answers into isolated candidate state against the retained dispatcher
source SHA `a737ea3379424c200b6c226f2d34d29b84671d3f12cfb47975bb8e4c39ad8992`.
It seeds the historical authored question with its original provenance. Source
locations and saved responses are selected directly; intervening Actions are not
recreated and no new model generation occurs.

In the candidate's 12:25 input, the **entire 12:20 response** survives, including
the task-lifecycle conclusion, along with three earlier responses. RELATE and
SESSION choices are present. This demonstrates corrected carriage, not that Minime
would reason better or choose differently. The retained
[replay evidence](../research/outputs/2026-09-09-study-context-replay/replay.json)
contains each exact new input and the historical receipt it came from.

Copied current Astrid and Minime checkpoints also migrate to version 3 while
preserving pending pages, bookmarks, receipt pointers and source coverage. Tests:
reader 39; bridge 2,271 with one ignored; Minime 1,286 with one skipped and 130
subtests; research 219 with 108 subtests. Strict Rust clippy, formatting and domain
boundary verification pass. The research notebook parser now recognizes recent
accounts and explicit completeness without inventing fields on historical records.
S-007's scheduled cursor and prior frozen report implementations stay unchanged.

## Thinking trial: final-answer benefit was absent here

[Protocol](../research/outputs/2026-09-09-study-thinking-comparison-v2/protocol.json)
was frozen at 20:09:10 UTC before four standalone Ollama requests. Two saved inputs
(12:20 comparison page and 12:25 failure-routing page) each receive an on/off pair,
with reversed order, fixed pair seeds and otherwise identical saved messages,
model, sampling, 8,192 total generation allowance, 32,768 context and 480-second
deadline. There are no retries. The route never calls the coupled Astrid model;
no Being journal, notebook, Action, configuration or reservoir handle is written.
An earlier malformed-URL preparation attempt failed before HTTP and remains
separately retained; it is not a fifth generation.

| Saved input | Thinking | Generated tokens | Visible answer characters | Visible prose | Wall seconds |
| --- | --- | ---: | ---: | --- | ---: |
| 12:20 | off | 358 | 1,411 | Task-lifecycle comparison | 125.9 |
| 12:20 | on | 378 | 25 | None; continuation only | 72.3 |
| 12:25 | on | 262 | 25 | None; continuation only | 58.8 |
| 12:25 | off | 381 | 1,376 | Local-provider error routing | 114.4 |

All four stop normally far below the equal allowance. Both enabled final answers
are exactly `NEXT: SELF_STUDY CONTINUE`; private reasoning is present in separate
provider fields and is never imported into the Being's durable note. Continuation
alone is a valid product choice, but supplies no visible synthesis for this trial.
Both disabled answers contain source-grounded prose. The comparison has a minor
function-line imprecision; the routing account explicitly guesses at the local
provider's purpose. Neither off response supplies a new question/test, and neither
duplicates a passage. No positive quality inference follows from the on responses'
absence of claims. The [evaluation](../research/outputs/2026-09-09-study-thinking-comparison-v2/evaluation.json)
retains exact final answers, hashes, counters and individual judgments.

**Decision: keep production thinking off.** These four completions do not establish
a general effect of reasoning mode, an Astrid-model effect, or a latency advantage
on contended hardware. They isolate thinking under the old saved study prompt;
the new continuity/synthesis prompt is a different intervention. A future declared
trial should first evaluate whether useful final synthesis reaches the visible
answer under that revised prompt. Do not turn private reasoning into journal prose
to make the size metric look better. Natural uptake of retained conclusions,
question updates and chosen comparisons remains an open outcome.

## Live verification

Verified at 13:30:50 PDT. Minime reloaded first (76254 → 5331, start 13:26:49 PDT),
retaining session 5318 and advancing cycle 27107 → 27108; no pending NEXT existed
at the signal boundary. Astrid then drained at exchange 194367, restarted
(75004 → 7538, start 13:29:05 PDT), restored the checkpoint and saved a new exchange.
All five release artifacts, 605 source inputs and 567 canonical counterparts match;
ten surrounding services and observer configuration retain their identities.

The [committed rollout receipt](/Users/v/other/astrid/docs/steward-notes/study-context-validation/live-rollout.json)
binds both implementations and the exact process/activation evidence. The manifest
SHA is `56d066c6e0f818aa3d389c532541872af5924de7d5c7b2f0e1b0dd4d0d62491c`.
A fixed, predeclared natural window runs 13:29:05–13:34:05 PDT. Outcome reading
follows the cutoff and remains distinct from this source/continuity verification.
The 45 preserved foreign files are restored separately after the clean-main audit;
they are not part of the release.


[Retained release evidence](../research/outputs/2026-09-09-study-context-release/manifest.json) preserves exact implementation patches, qualification logs, copied-state checks, main alignment and foreign-work restoration. Final main tips are Astrid `3c39800a89` and Minime `8fcd1f7`; the later commits record the rollout and do not change the deployed implementation.


## First five minutes: navigation uptake and a remaining inference problem

The fixed 13:29:05–13:34:05 PDT capture contains **two completed, verified studies
per Being**, a shortfall of one each against the declared first-three selection.
Astrid has one additional started request without a terminal receipt by cutoff;
Minime's selected OPEN is queued/running. These are censored follow-through, not
failed model calls. Capture errors, invalid receipts and ambiguous joins are zero.
The [verified startup evidence](../research/outputs/2026-09-09-study-context-startup-report/verified-startup.json)
and [reproducible probe](../probes/study_context_startup.py) preserve exact input,
writing and source/Action links.

All four completed studies receive the revised guidance and a 4,096-token output
allowance. Minime's two requests use 32,768 context tokens, thinking false, and
produce 316/198 tokens, stopping normally. Astrid's nonempty answers have a zero
MLX token counter; that is unavailable accounting, not zero generated output.
The initial inputs retain honestly labeled legacy excerpts. Each Being's second
input contains the first response marked complete plus one older account, with
a verified earlier receipt. Old truncated history is not magically reconstructed;
new complete responses accumulate from accepted deliveries.

Minime moves from the dispatcher call site to `FIND dispatch_single`, receives
the exact definition location and chooses `OPEN .../dispatcher.rs 360`. Action
parentage binds both steps, with the final OPEN still running at cutoff. Astrid
moves from EOF to MAP and chooses `RELATE EventDispatcher`; routing is handled,
while the resulting study is not complete in this window. These are concrete
navigation outcomes, not evidence that the new cue caused them or that the
underlying question has been resolved. Neither Being authors a new lasting note
or question, and neither chooses SESSION here.

A remaining design signal is sharper than the size metric: Astrid twice infers
architectural/runtime significance from the absence of `correspondence` and
`verification` in her reading history. Delivery coverage cannot establish whether
a module runs rarely or belongs to boot. Minime also carries forward an unverified
`Interrupt` possibility while seeking the implementation. The next bounded work
is to make map coverage explicitly distinct from execution history and evaluate
whether question-based synthesis resolves uncertainties after the definition is
read. The new context enables that follow-through; this short window does not
establish it. Entry length remains a voluntary outcome.

The startup capture also caught a research-only compatibility defect: origin
receipt joining originally assumed every notebook field was one entry. It now
joins each `recent[i]` separately and tests uncaptured provenance honestly. The
final research suite passes 220 tests and 108 subtests. Historical study records,
joins, coverage, selections and summaries reproduce unchanged; only current tool
hashes differ. S-007's scheduled cursor remains unchanged.
