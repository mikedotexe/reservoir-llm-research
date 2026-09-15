# HSS-16: help with wrong turns, preserve choices, qualify a claim-check invitation

September 9, 2026, Pacific. Mike authorized HSS-15's three recommendations and
emphasized that the Beings choose, may make mistakes or need several attempts,
and should have ample freedom to navigate and figure things out. The changes
support that freedom. There is no correctness gate, compulsory review, writing
quota, automatic note revision, forced question closure or retry based on prose.

## Why this follows HSS-15

[The previous natural follow-up](2026-09-09-study-context-followup.md) found a
source-grounded correction by Astrid, persistence of a mistaken explanation by
Minime despite improved context carriage, and eight Astrid recovery-map turns
after a missing-parent path. FIND could already locate the actual file. Two
Minime attempts exhausted 4,096 generated tokens without saved responses, but
their native finish and raw final bodies were not retained. These are three
different observations: navigation friction, claim revision and missing evidence.
None establishes a need to require first-try correctness or longer writing.

The frozen HSS-15 capture SHA-256 is
`82b369c73e86687bbcd9276b2ac74d4e46f91afdde4b5541230c3c7b44e6646e`.
The [implementation proposal](../proposals/2026-09-09-study-claim-check-and-recovery.md)
preceded this intervention. Older accounts, frozen outputs and S-007's daily
cursor remain unchanged.

## Implemented assistance

Astrid and Minime share the same reader. After an unavailable OPEN, RESUME or
SESSION path, it now offers up to three exact existing catalog candidates.
They stay in the requested repository, match the basename (including existing
underscore/hyphen spelling normalization), favor the requested subtree and use
stable ranking. An empty directory MAP can offer actual directory paths.

For example, the omitted `action_continuity` parent in
`astrid/capsules/spectral-bridge/src/runtime/command_dispatch.rs` now has a route
back to the real catalog entry. A candidate is clearly labelled and is not
opened automatically. Repeated errors preserve pending source and the delivered
bookmark. The Being can choose a suggestion, FIND, retry, read elsewhere or leave.
Source exclusions, exact resolution and inquiry state remain unchanged.

Minime now retains native finish/done information, raw/cleaned visible lengths,
thinking-content length, native generated-token count when supplied, and a
diagnostic link on failed attempts. Both Ollama and OpenAI-compatible adapters
are covered. Raw request and response are each bounded to a 64 KiB UTF-8 prefix,
with original hashes, original and retained lengths, and explicit truncation.
Files are atomically published with mode 0600 under a mode-0700 diagnostic folder.
Transport, HTTP, malformed response, cleanup, empty final, length termination,
incomplete response and delivery rejection can be distinguished.

These artifacts are provider-attempt evidence, not journals or accepted source
receipts. Diagnostic storage failure does not change completion policy. The
existing generation-record opt-out also disables retention. Astrid already has
provider-event metadata and selective raw-content observation, but does **not**
have identical arbitrary failed-wire retention; this change addresses Minime's
specific missing-output evidence gap. Shared navigation parity is separate from
host-specific diagnostic implementation.

The research collector now follows generation-linked diagnostic paths as
`source_study_failure`, deduplicates them, and refuses external or symlinked
references. Older failures remain unknown; this does not recover lost bodies.

## Six-call claim-check qualification

The [protocol](../research/outputs/2026-09-09-study-claim-check/protocol.json)
was frozen at 23:37:38 UTC, before model calls. It uses two mistaken saved Minime
accounts and Astrid's corrected host-filter account as a positive control.
Each pair receives identical actual caller/branch source, saved notebook,
model, sampling settings and seed. Only the candidate arm adds an optional
invitation to examine a counterexample and revise a note if useful. It also
explicitly allows further exploration, rereading, leaving the question open or
moving on. The middle pair reverses order. Six calls, no retries.

All calls use uncoupled local Ollama `gemma4:12b`, thinking off, output ceiling
4,096 and context 32,768; settings come from a saved Minime request. This is a
qualification of an assistance prompt using saved material, **not** the full
live Minime, Astrid's coupled model, or a natural longitudinal learning trial.
The relevant source is supplied to both arms, so the trial cannot estimate the
benefit of source selection itself. Shared hardware contention makes latency
descriptive. No output was inserted into a Being's notebook, mailbox or prompts.

Frozen dispatcher SHA-256:
`a737ea3379424c200b6c226f2d34d29b84671d3f12cfb47975bb8e4c39ad8992`.
Worker evidence: lines 245–302 and 360–449. Authorization/control evidence:
225–284, 530–601 and 413–520. The code shows a persistent per-capsule worker
for the single-match path, a task per multi-interceptor chain, a common caller
filter before the branch, and post-invocation error-reporting checks. The topic
predicate for reporting failures is not admission authorization.

| Saved case | Existing prompt | With optional invitation |
|---|---|---|
| Worker vs immediate execution | Repeats immediate-execution claim; later mentions worker but saves wrong contrast | Repeats immediate execution and avoids-spawn claim |
| Private filter vs supposed topic-isolated bypass | Repeats bypass; treats failure reporting as protection and invents topic-only dispatch | Repeats mutually exclusive topic zones and bypass |
| Correct host-filter control | Preserves core pre-dispatch filter; overstates a proven host-mediated service path | Preserves core filter; also overstates mediation/privilege and introduces `wasm__capsule` typo |

All six returned nonempty finals with native `stop`: 543–860 generated tokens,
2,285–3,352 visible characters and 137.36–249.35 seconds wall time. These requests
had ample unused output capacity. Body length is not a measure of thinking or
understanding, and this result gives no reason to impose longer output.

The invitation did not produce a correction in either erroneous-account pair.
The correct core survived both control responses, alongside unsupported
elaboration. Under the declared promotion rule, **the production prompt stays
unchanged**. This is not evidence that a Being must get an answer right on the
first try, cannot later revise it, or should lose navigation choices. It is
evidence that this particular additional invitation did not help in these cases.
There is one sample per arm, no population rate or pooled quality score.

Every raw request/response, native finish, token count and latency is retained
in the [trial directory](../research/outputs/2026-09-09-study-claim-check/).
[Manual evaluation](../research/outputs/2026-09-09-study-claim-check/evaluation.json)
is separate from the
[wire/pair/quote verification](../research/outputs/2026-09-09-study-claim-check/verified.json).
Reproduce verification without model calls:

```sh
python3 probes/study_claim_check_verify.py
```

## Qualification and implementation identities

Astrid source commit `7d85683d80`; Minime source `7c78a99` plus diagnostic-scope
documentation correction `c9c2a70`. Both are fast-forwarded and pushed to `main`.
Source and tests were isolated from five tracked foreign changes and five
heartbeat evidence directories; the original 57-file snapshot is retained at
`/Users/v/other/worktrees/study-choice-20260909/foreign/manifest.json`.

Checks: shared reader 42 passing tests; full spectral-bridge suite 2,271 passing,
one ignored; reader clippy with warnings denied and formatting checks passed.
Minime full suite: 1,296 passed, one skipped, 131 subtests passed. Research:
219 tests passed. Tests include repeated wrong paths, ambiguous catalog choices,
continued browsing, pending-delivery preservation, failed session recovery,
provider failures/cleanup, private bounded storage and diagnostic-write failure.
No bridge Rust file changed; this is shared-reader code and Minime integration.

Operational verification scripts are retained alongside the [release evidence](../research/outputs/2026-09-09-study-choice-release/). Test logs are the named suite outputs; source and release counts come from the retained verifier.

Logs and release evidence live under
`/Users/v/other/worktrees/study-choice-20260909/`. Activation and process facts
are recorded below once verified; source commits alone do not establish live use.

## Next observations, with room for choice

Observe a natural failed path receiving candidates and what the Being chooses
afterward. A retry, ignored suggestion, changed question or departure can all be
useful follow-through; recovery is not defined as choosing our first candidate.
Inspect the first naturally failing Minime attempt using native finish and wire
evidence before changing capacity. Do not induce failures for an outcome sample.

For understanding, preserve sequences in which a saved claim meets relevant
caller/branch evidence over multiple choices. If another intervention is tried,
a small **optional execution example** may be more useful than adding more
advice: show how one concrete message passes the common filter and reaches a
branch, then let the Being question or explore it. That remains a proposal,
with separate correct controls and source provenance; it is not implemented or
fed to either Being by this study. The current test does not isolate recall
anchoring from other causes, so keep that mechanism a hypothesis.

## Verified live rollout and bounded startup evidence

Verified at **September 9, 17:09:42 PDT**. Astrid main is `d7a8bbcff9`
(source `7d85683d80` plus rollout documentation); Minime main is `c9c2a70`.
Both remote main tips were verified after push. The selected stage is
`/Users/v/other/worktrees/study-choice-20260909/bridge-stage-01`;
manifest SHA-256
`52142a80c2990009dedf9b29d268449ccc30e961950481d2c3a121aa96f764f8`.

Bridge PID 7538 → **53226**, started 17:04:28 PDT, passed exact stopped-checkpoint
and state-lineage verification and saved a new exchange (194488 → 194489).
Minime PID 5331 → **52380**, process start 17:02:51 PDT, completed its quiet-boundary
reload without forced termination. The same session's pending
`SELF_STUDY CONTINUE` was restored and dispatched. Both select the same immutable
reader helper, SHA-256
`ab434f4954a64d54e0a1ec6b22df0af2ac3371a24b54957e644647755278bc3f`.
All 607 staged source inputs verify; 569 Astrid inputs match committed main,
with 38 external inputs. Ten other live services, launch settings and observer
overrides stayed unchanged.

[Release evidence](../research/outputs/2026-09-09-study-choice-release/live-verification.json)
and the owning [rollout receipt](/Users/v/other/astrid/docs/steward-notes/study-choice-validation/live-rollout.json)
retain executable, source, process and restart identities. Foreign source and
reader/dispatcher tests were restored byte-for-byte; both shared documents retain
all foreign lines alongside our additions. All 52 foreign untracked files are
unchanged. The five foreign tracked changes remain uncommitted and separately
owned. They were not included in this live stage or either main commit.

Minime's first completed study after reloading, at 17:04:35 PDT, is generation
`1788998595467-17fd6124` from PID 52380. It records native `stop`, 826 generated
tokens, raw/cleaned lengths both 3,184 and a linked 4,188-byte journal. Its next
choice remains `SELF_STUDY CONTINUE`. This is diagnostics and continuity evidence,
not new path-recovery exposure: the generation started before bridge activation.
No naturally failed new-process attempt was selected for this startup check;
failed-wire retention is qualified by adapter tests, not yet a live failure case.

The [selected-helper replay](../research/outputs/2026-09-09-study-choice-recovery/recovery.json)
repeats the original bad path twice and verifies both turns offer the exact
catalog path without opening it. An explicit OPEN succeeds. It uses isolated
research state, not the Being's notebook, and makes no model call. This establishes
the tool behavior; natural recovery uptake and subsequent understanding remain
future observations. The research toolkit now supports the verified `study-choice`
release profile, including generation-linked diagnostics and the previous
study-context release. Its final 219-test suite passes.

Stewardship resumed through its controller at 17:14:07 PDT, generation 426,
after the evidence audit completed. No lease or integration ownership is retained.

## Board updates pending

No compatible board connector is available in this task. The prior board authentication issue remains unresolved; no new authenticated UI write was performed.
Local payload: `board/study-choice-pending.json`, HSS-16 implementation, trial
finding and session log. No board publication is claimed.
