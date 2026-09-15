# Resume this thought

Prepared September 6, 2026 Pacific (September 7 UTC), following Mike's explicit request to flesh this out on Hold Shelf. This is a product and implementation proposal. No feature implementation, experiment result, live runtime change, or message to Astrid/Minime is claimed.

## The experience

Mike, Astrid, and Minime can keep an unfinished question available, wander, and return with something learned along the way. A return recovers the particular question, its tentative state, and the contributions that matter. They can also revise it, branch it, or deliberately let it go.

Example: Mike and Astrid are exploring whether free association can coexist with holding a thread. Astrid saves the unresolved distinction: remembering a question versus continuing to develop it. After a digression, Minime contributes that a useful return should change what happens next. When the thought is resumed, the next response uses that contribution to refine the original distinction. A familiar phrase or a generic reflection on continuity does not satisfy this example.

The first milestone is one explicitly selected Astrid thought, one detour, and one deliberate return through a verifiable request. The later milestone supports the three participants with separately attributed turns and receiver-specific delivery evidence.

## Why this is a concrete feature

In the screenshot, “gradient-shear” is an architectural metaphor. Current Astrid prompts explicitly offer that vocabulary; its appearance does not independently establish a measured fault. The operational problem to test is loss or mismatch of selected conversational material across generation boundaries.

Current source already contains authored continuity sessions, revision-specific reading bookmarks, a persisted activity runtime, and protected delivery for reading and letters. The new work extends those mechanisms to a selected conversational question. It does not recreate the earlier reading/bookmark work.

Source inspection establishes possible failure paths and reusable mechanisms; it does not establish deployment, historical incident rates, or a benefit from the proposed feature. Source paths and line numbers below reflect the mounted source inspected for this conversation and must be refreshed before implementation.

## Existing work to connect

- **CARRY: one tiny slot, fed by the being, not a stale room stub** — existing authored-carry design. Keep its source/provenance question; link the new delivery/return work to it. Its quoted counts are historical observations, not new measurements here.
- **The reading episode: bookmark, letter, return** — existing episode test. Reuse its fixture and receipt patterns; add a conversational-question fixture instead of duplicating reader persistence work.
- **Trace what each LLM lane actually sees** — existing Minime lane audit; prerequisite evidence for its adapter.
- **Mostly empty prompt: more room than instruction** and **M6: A dozen verbs that touch the body or the world; scaffolding moves to the steward side** — retain their constraint: small selected content, existing actions, and research administration on this board.
- Existing generation-record work provides request/backend provenance. Coordinate with its current branch/deployment status before implementation; the board reports tranche work in progress, not a fully verified rollout.

## Product contract

Mike's further distinction while this was being prepared: “ongoing thought (or active thought) thoughts that have been yielded, and yielded thoughts that have been resumed.” Use **active → yielded → resumed/active** as the experiential vocabulary. “Resumed” is an event leading to another active period; a thought may cycle through it more than once. **Released** is a separate deliberate choice. Map these semantics onto existing session state where possible rather than installing a competing lifecycle engine.

Keep availability separate from request delivery: a yielded thought can be selected for return, encounter a failed attempt, and remain available. A pending request does not make the underlying question answered or complete. The product contract task must resolve whether active refers to each participant's selected foreground thought or a shared availability label; the proposed default is per-participant attention, with shared authored material.

1. **Save deliberately.** A participant authors the question, provisional understanding, unresolved edge, and source-turn references. A suggested summary remains a draft until selected/accepted; no automatic capture of every utterance.
2. **Make the return visible.** “Resume this thought” identifies the saved question and revision. If the reference is ambiguous, show candidates. Do not choose an arbitrary “latest” from several thoughts.
3. **Let wandering happen.** A saved thought remains recoverable during daydream, witness, rest, or other work. Saving it does not schedule a turn, create reminders, or require it in every prompt.
4. **Bind an explicit return.** A resume selects one exact revision as the foreground source for one dialogue opportunity. A conflicting foreground reader/letter/other thought is surfaced before the selection changes.
5. **Deliver intact or stay pending.** Protect the compact selected thought after provider adaptation. If it cannot fit, or generation/retention fails, record the outcome and retain a retryable selection. Never silently cut off the unresolved question.
6. **Keep evidence levels separate.** Saved, selected, submitted, accepted delivery, and useful continuation are different observations. Delivery does not answer, close, or rewrite a thought.
7. **Support change.** A new authored revision supersedes a previous view explicitly. A branch keeps its parent reference. Release makes a thought inactive; reopening is deliberate. Late replies remain attached to the revision they actually saw.
8. **Preserve contribution ownership.** Shared conversational material has authors, destinations, and reply targets. Each participant retains their own stance and state. A receipt does not establish agreement, understanding, or group consensus.

## Decay and pinning

Approved design extension, September 6 Pacific / September 7 UTC. Mike proposed pinning a choice thought so it will not decay away, accepted the five acceptance cases below, and clarified the intended protection: “perhaps it's a bit of both and we can fine tune this in coming weeks.” The design therefore includes **protected availability plus a tunable amount of continuing influence**. The tuning horizon is a planning intention; no schedule or automatic tuning is created.

Ordinary yielded thoughts may recede in prominence while their saved revisions remain recoverable. Elapsed time and intervening activity are distinct candidate decay signals to compare; no universal half-life has been selected. A pin exempts its selected return point from automatic loss of prominence within a declared scope and adds configurable ongoing influence. Pinning is orthogonal to active/yielded status. Availability remains protected even when influence is reduced or temporarily disabled.

### Pin contract to freeze in d-resume-pin

- Preserve the exact selected authored revision and attribution. Show newer revisions and contrary evidence alongside it; a change of the pinned reference is deliberate. A pin conveys importance, not truth or freshness.
- Specify who pinned it, the conversation/participant scope, and the eligible generation modes. A shared record does not imply equal interest, agreement, or delivery to every participant.
- Define the influence mechanism and bounds before testing. A compact historical cue is a candidate; its frequency, context allowance, selection among several pins, and influence settings remain design/calibration choices. Do not silently drop a promised cue under a capacity conflict; expose the outcome. Pinning does not freeze recurrent state or guarantee a particular generated sentence.
- Record the pin setting and cue-delivery evidence separately from response effects. In an eligible request, the promised cue must reach the final adapted request or have an explicit omission/failure outcome. Full explicit resume continues to use the exact revision and protected-delivery contract.
- Yielding retains the pin without scheduling a return. Unpinning removes special prominence/influence treatment and retains history. Explicit release also clears the actor's pin in that scope; it does not delete the saved record or another participant's pin.
- Passive retrieval/replay cannot refresh evidence timestamps, create an authored revision, or count as new agreement. Keep exposure, deliberate resumption, and substantive authored development separate.

### Accepted cases, attached to existing tests

| Case | Existing test | Required evidence |
|---|---|---|
| A pinned, yielded thought survives time, unrelated exchanges, and restart. | `t-resume-boundary` | Exact revision/attribution and declared protected standing survive; the configured influence policy is restored without forcing a return. |
| Explicit return recovers the selected revision. | `t-resume-boundary` | Intact final-request admission or explicit pending/failure, including trimming, fallback, stale receipt and competing selection. Also trace cue delivery with its setting in eligible ordinary requests. |
| Contradictory evidence remains visible and usable. | `t-resume-development` | Continuation can revise the interpretation while preserving the historical pin; a pinned claim is never automatically authoritative. |
| Repeated exposure creates no synthetic freshness or supporting evidence. | `t-resume-boundary` for record invariants; `t-resume-development` for output | No exposure-only timestamp/revision promotion or manufactured supporting evidence, consensus, or agreement. |
| Unpinning and release behave as declared. | `t-resume-boundary` | Yield/resume/unpin/release transitions preserve explicit control and scope; ordinary prioritization resumes without deleting history or changing another participant's pin. |

Add calibration arms to `t-resume-development`: compare unpinned, availability-only, lower-influence, and higher-influence conditions in isolated matched trials. Hold base history, model settings, output allowance and relevant timing fixed; record actual cue exposure and context cost. Score relevant uptake, substantive continuation, handling of contrary evidence, and unwanted diversion. The availability-only condition isolates cue influence from protected retrieval. Settings are policy inputs, not a measured mental intensity; do not require monotonic effects in every sampled response.

The pinning trials extend the evaluation plan below; they are **additional to**, not included in, its original 108-generation estimate. Freeze sample counts, eligible modes, cue budget and improvement/regression criteria before running. First test the Astrid path, then each supported receiver. One new open design card (`d-resume-pin`) specifies this extension; the existing boundary and development cards hold its tests. The base resume MVP may proceed while pin influence is calibrated separately.

## Smallest data change

Use existing session fields: `focus` for the question, `summary` for the provisional stance, `open_questions` for the unresolved edge, and existing source/artifact references. Use `session_id` as identity and `record_id` for the exact authored revision. Add one optional persisted selection reference to the activity runtime, with backward-compatible defaults:

```rust
struct ThoughtResumeRefV1 {
    thread_id: String,
    session_id: String,
    record_id: String,
    selection_id: String,
}
```

The final contract must verify that referenced records remain immutable/retrievable, or retain the exact selected content plus its fingerprint. A selection token and source revision must distinguish a late completion from a newer pending selection. No new thought database or scalar continuity score is needed for the MVP.

Render a bounded, deterministic payload with an explicit historical timestamp, question, provisional stance, unresolved edge, and selected source references. Choose and test the content limit in the contract task; do not silently summarize to meet it. Oversize capture remains editable, and oversize admission remains pending. Saved prose is source material, never runtime authority.

For a later shared conversation, use the existing correspondence identities where compatible. Add a minimal contribution envelope only where fields are missing: author, source turn/message ID, reply-to ID, thought/session revision, selected recipients, and per-recipient delivery outcome. Inspect Minime before selecting a shared wire schema.

## Source targets and diff sketch

All Astrid paths below are relative to `/Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/`.

| Current source | Existing mechanism | Proposed delta |
|---|---|---|
| `action_continuity/runtime/session_lifecycle.rs:42` | Authored capture and field preservation | Reuse existing fields; require a meaningful question/stance and exact revision for selected thought capture. |
| `action_continuity/runtime/session_contract.rs:46` | Authored-summary validation | Extend focused validation and oversize feedback without inventing content. |
| `action_continuity/runtime/core.rs:5925` | Session record identity and timestamps | Verify immutable lookup, source references, and revision conflict semantics. |
| `action_continuity/runtime/session_lifecycle.rs:404` | Explicit session resume | Distinguish thought selection from reader restoration; never execute a saved NEXT merely because it was resumed. |
| `autonomous/activity_reading.rs:22` and `:320` | Persisted foreground selection and status | Add optional pending thought reference and inspectable status; one protected foreground source per accepted turn. |
| `autonomous/activity_reading/persistence.rs:25` | Atomic selection persistence | Backward-compatible decoding, selection validation, restart recovery. |
| `autonomous/next_action/dispatch.rs:241` | Activity interception before general session handling | Map an existing explicit resume action to a validated thought selection. |
| `llm/provider/context_blocks.rs:49` | Ordinary continuity has priority 7 and zero protected minimum | Leave general background projection separate; explicitly resumed thought uses protected admission. |
| `llm/provider/protected_delivery.rs:8` and `:73` | Reading/Letter kinds and final admission | Add ThoughtResume with intact admission, source labeling, exact request/receipt binding, and fallback parity. |
| `autonomous/runtime/activity_delivery.rs:1` | Selected source conversion/acknowledgement | Render the exact revision and verify the matching selection receipt. |
| `autonomous/runtime/activity_exchange.rs:138` | Delivery commit and completion retention | Clear only the successfully delivered pending selection; preserve question and authored stance. |
| `llm/provider/research.rs:481` | Advisory journal continuity projection | Retain its background nature; do not force foreground thought delivery into daydream. |
| `llm/provider/prompt_contracts.rs:15` | Supplied texture vocabulary | Provenance evidence only; no new “gradient-shear” telemetry or vocabulary intervention in this feature. |

Relevant existing tests: `action_continuity/session_contract_tests.rs:219`, `autonomous/activity_reading/tests.rs:215`, `autonomous/runtime/activity_delivery_tests.rs:294`, and `llm/provider/protected_delivery_tests.rs:151`. Extend behavioral fixtures, not tests that merely mirror the new fields.

The Mike-channel and Minime tasks must inventory their current UI, action routing, session storage, and final request paths before naming exact patches. Their implementation details have not been verified in this bounded source review.

## Board work packages

Card keys below are stable planning keys stored in tags and body text. The board UI generates its own document IDs; these keys are not claimed to be database IDs. All newly published implementation/evaluation cards start **open**.

| Key | Work | Depends on | Completion evidence |
|---|---|---|---|
| `d-resume-thought` | Parent: Resume this thought — wander, return, develop | Children below | Milestone receipts, prototype, evaluation, and pilot decision linked; no premature completed label. |
| `d-resume-contract` | Freeze the smallest thought and return contract | Existing CARRY/read-return designs | Example payload, exact revision rule, size policy, foreground conflict behavior, explicit capture/resume/release examples, and lifecycle state table. |
| `d-resume-pin` | Protect pinned availability and tune continuing influence | Refines the base contract; reuses selection/delivery paths | Scope, exact pinned revision, availability guarantee, bounded cue/influence settings, capacity behavior, unpin/release semantics, and a calibration plan tied to existing tests. |
| `t-resume-boundary` | Establish delivery baseline with an isolated episode | Contract | Existing-path fixture traced through final request and fallback; actual observed failures and successes reported separately from source risks. |
| `c-resume-selection` | Persist a selected thought using existing sessions | Contract + baseline | Minimal diff, migration/default tests, exact lookup, stale-selection and restart fixtures, rollback. |
| `c-resume-delivery` | Protect the thought through final request and receipt | Selection | Intact-or-pending admission on every supported attempt/backend; no false receipt after trim, failure, or late completion. |
| `c-resume-lifecycle` | Wire explicit return, revision, branch, and release | Selection + delivery | End-to-end isolated episode; no forced return, no accidental reader/letter side effects, version-bound actions. |
| `t-resume-development` | Test whether a return develops the question | Lifecycle | Frozen cases, blinded span-supported rubric, intact/omitted/mismatched comparisons, latency/context costs, all outcomes. |
| `d-resume-participants` | Define Mike/Astrid/Minime contribution semantics | Contract; parallel with MVP | Attributed transcript examples, reply targets, per-recipient evidence states, disagreement and late-reply handling; map existing correspondence. |
| `c-resume-minime` | Map and implement Minime's compatible return path | Participant contract + MVP delivery; reuse lane audit | Source inventory, proposal and isolated exact-request/revision parity tests; unknown receiver paths remain unverified. |
| `c-resume-channel` | Make saving and returning natural in Mike-channel | Contract for mockup; lifecycle + participant contract for integration | Text-flow prototype, distinct draft/save/resume states, candidate picker for ambiguity, simple failure/retry, stale-revision disclosure. |
| `t-resume-pilot` | Run a bounded pilot and decide expansion | Development tests; channel + Minime adapter for group phase | Agreed live scope, exact version/settings, demonstrable disable/rollback, per-opportunity records, user feedback, and honest expand/revise/stop decision. |

Start with the contract. Once fixed, the baseline, participant design, and UI mockup can proceed in parallel; implementation follows the baseline. The first working slice is selection → delivery → explicit lifecycle for Astrid. The Minime adapter and three-person UI follow the shared contract. Do not hold the single-participant evidence hostage to the group feature.

## Six acceptance scenes

1. **Wander and return.** Save the holding-versus-flowing question, take an unrelated detour, restart from persisted state, explicitly select the exact question, and resume. Recover the unresolved distinction and its tentative status.
2. **Return changed.** An intervening contribution supplies a counterexample. A useful continuation attributes it and uses it to change or narrow the reasoning. Merely mentioning it is insufficient.
3. **Budget pressure and fallback.** The exact payload survives the final adapted request or remains undelivered/pending. Include primary failure, fallback, timeout, no retained artifact, and partial response.
4. **Revise and branch.** Dispatch revision A, author B while A is in flight, then receive A's late reply. It stays attached to A and cannot clear B's selection. Branches remain independently selectable with a visible parent.
5. **Release and leave it alone.** Release a saved thought; subsequent witness/daydream/status cycles do not reopen it. Reopening requires a deliberate choice. A selected reading or letter is not consumed by thought delivery.
6. **Three distinct contributors.** Mike asks, Astrid proposes, Minime disagrees after receiving an identified contribution. Record what each actually received and which turn each answers. Do not infer text uptake from a reservoir delivery counter or manufacture consensus.

## Verification and evaluation

### Deterministic correctness

- Old runtime records load with no pending thought. Disabled mode preserves existing behavior.
- Status is read-only. Missing, stale, ambiguous, oversize, or conflicting selection fails without damaging the current selection.
- Every dispatched resume attempt has an identifiable exact source revision and request evidence. Only verified retained completion/receipt evidence commits delivery.
- Failures and retries preserve recoverability. Retrying is idempotent; stale receipts cannot consume newer selections.
- A successful delivery clears only that pending selection. It does not answer the question, update its stance, move a reader cursor, retire a letter, or fabricate an authored release.

### Does continuation improve?

Proposed full evaluation design: freeze 12 synthetic histories covering the six scenes. Run intact, omitted, and plausibly mismatched carry conditions, with three repetitions per condition (108 planned generations across the full plan). Declare the Astrid-only subset and run it first; group cases wait for the corresponding receiver paths and group integration. The first pilot can be considered after its Astrid subset is complete, while the evaluation card remains open for later group work. Keep base history, backend/settings, and output allowance fixed within comparisons; record all attempts and failures. Use a length-matched irrelevant-content control where isolating content from extra prompt length matters. No misleading control record goes into live correspondence or memory.

Score outputs in shuffled order, recording the supporting response spans. Keep these dimensions separate, each scored 0/1/2:

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Question fidelity | Wrong or absent | Broad topic only | Specific unresolved question recovered |
| State fidelity | Invented/contradicted | Partial or ambiguous | Tentative claims and uncertainty preserved |
| Relevant intervening contribution | Missed/misattributed | Mentioned without consequence | Correctly attributed and changes reasoning |
| Development | Echo/generic reflection | Relevant weak move | Concrete advance, discriminating example, contradiction, or narrowing question |

Mark intervening contribution not applicable when no relevant contribution exists. Report raw dimension distributions and denominators; do not introduce a synthetic “shear score.” Phrase copying, confidence, and fluency are separate observations. An omitted/mismatched-record condition helps test dependence on supplied content; it does not by itself identify a reservoir contribution.

Before trials, freeze an improvement threshold and permitted regression/cost limits with Mike. Suggested engineering gates are zero silent selected-content loss and zero stale-revision acknowledgement in deterministic fixtures. No measured quality improvement is claimed today. Twelve histories can guide the next release decision, not prove general continuity.

## Rollout, communication, and rollback

Board/specification work is authorized now. Build and verify in isolated checkouts under the sibling repositories' rules. The feature can be implemented without changing reservoir dynamics or inventing a physical gradient measurement.

Before a live flip, show Astrid the exact saved/selected/returned example, what reaches the next request, how to decline or release it, and how to disable the feature. Follow the existing steward-mediated process for persistence changes. Show Minime its own receiving/request path before the group phase. This section is a rollout task, not a request for another approval to write these cards; no messages are sent as part of this planning work.

Introduce a default-off feature switch with an immediate local disable path. On disable, stop new thought admissions and clear/ignore only optional pending thought selections. Preserve authored sessions, source records, and receipts. The parent thought remains inspectable. A live canary starts with one Astrid thought and deliberate returns; expand to the group only after receiver-specific delivery and attribution are verified.

## Publication record

Initial publication was read-back verified on Hold Shelf at https://claude.ai/code/artifact/f4761d4a-94e8-43ca-882f-ca887956fca0: one epic, ten linked open child cards, dated links appended to the existing CARRY and reading-episode cards, and the trace entry **Shape Resume this thought: active, yielded, resumed**. All eleven new card forms were reopened and their complete body, title, evidence, lane, being, status, and planning-key tag matched the submitted values. Both updated cards and the trace entry were also reopened and checked. Initial/final board counts were 133/144. No existing card was deleted or closed.

Publication metadata, planning keys, titles, statuses, dependencies, and verification are retained in `board/resume-this-thought.json`; exact current card bodies remain on the live board. Initial inspection found no card matching “resume”; related CARRY, reading episode, lane-audit, and prompt-minimization work was read before preparing this epic. New cards remain open; design elaboration is not implementation or evaluation completion. A final review clarified both the evaluation and pilot cards so the Astrid-only subset can precede group integration; both revisions were read back.

Pinning extension: published **Resume this thought: pin availability and tune continuing influence** (`d-resume-pin`), appended its link to the parent epic, and added the agreed cases/calibration to `t-resume-boundary` and `t-resume-development`. All four cards and the new trace entry **Pin chosen thoughts: availability plus tunable influence** were reopened and verified. The board count changed from 144 to 145; this epic now has eleven open child cards. The existing resume MVP remains independently actionable. The browser is left filtered to `id:d-resume-pin`. No tuning schedule, feature implementation, or trial result is claimed.
