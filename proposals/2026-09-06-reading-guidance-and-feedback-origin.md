# Make reading guidance usable and preserve feedback origin

**Status:** [PR #28](https://github.com/mikedotexe/astrid/pull/28) merged; correction verified live in the combined Afterimages release.
[Current merge and live record](../analyses/2026-09-07-reading-feedback-live.md);
[implementation and verification record](../analyses/2026-09-06-reading-guidance-implementation.md).
The proposal below preserves its original evidence and design; current rollout status is linked above.
**Scope:** two corrections to Astrid's dialogue guidance and runtime-feedback path.
Keep the research-budget guard, its admission policy, and Astrid's authored preferences.

## Problem and evidence

The [09:11–09:15 close reading](../analyses/2026-09-06-astrid-readmore-feedback.md)
contains three bare `NEXT: READ_MORE` requests followed by recorded budget blocks.
The prose changes across requests, and six adjacent dialogue/longform records do
not explicitly mention the block. This establishes unresolved requests in that
slice, not why they repeated, what Astrid wanted to read, or whether feedback arrived.
No subjective response to the block is established. The exact morning dialogue
requests and deployed implementation remain unrecovered in this proposal's evidence.

The [current-code trace](../analyses/2026-09-06-astrid-readmore-feedback-code.md)
identifies two independently reviewable interface problems: shortening notices
recommend READ_MORE without admission state; a runtime denial can enter the next
primary system message labelled as Astrid's own chosen emphasis. The latter is an
origin error on that path, not evidence that Astrid endorsed the denial. Current
code does not establish that either mechanism caused the morning repetitions.

Exact source read for this proposal, under
`/Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/`:

| Source and lines | Current behavior |
|---|---|
| `src/llm/provider/dialogue_context.rs:9–17,24–27` | Every capped block says “Use NEXT: READ_MORE”; the cap records original source text separately. |
| `src/prompt_budget.rs:79–110,140–176,190–206` | Full/partial eviction notices recommend READ_MORE without admission state; originals/overflow pass to persistence. |
| `src/prompt_budget.rs:223–251` | The writer returns successful overflow metadata or appends a storage-failure notice. A saved source must not be claimed before success. |
| `src/autonomous/next_action/dispatch.rs:80–96` | A guard denial stores `guard.message()` in `conv.emphasis`, then returns blocked with structured guard metadata. |
| `src/llm/provider/dialogue_generation.rs:76–82` | Any supplied emphasis becomes “you chose to emphasize … This is your own direction.” |
| `src/autonomous/runtime/orchestration.rs:1924–1951,2040–2042` | A form constraint can replace emphasis; emphasis is cleared after the dialogue branch. |
| `src/llm/provider/dialogue_generation.rs:287–304` | The ordinary fallback call does not receive the original emphasis argument; generation-record capture receives both message sets. |

## Proposed correction 1: availability-aware overflow guidance

Use one renderer for capped, partially trimmed, and fully evicted dialogue blocks.
Give it separate source-retention and read-admission states. The caller supplies a
non-mutating admission assessment using the same policy inputs as the guard; the
renderer does not accept a budget or dispatch an action. Render after the actual
overflow persistence result is known. Preserve full source bytes, labels, and the
existing source/reader reference, including when admission is blocked or unknown.

Diff sketch, naming illustrative rather than a compiled patch:

```rust
enum ReadAvailability { Admitted, Blocked { reason: String, suggested_next: Option<String> }, Unknown }
// dialogue_context.rs / prompt_budget.rs
- "... NEXT: READ_MORE to see full context."
+ render_overflow_notice(label, retained_source, read_availability)
```

For a saved, currently admitted source: “Full context is saved at [source reference].
NEXT: READ_MORE requests the continuation; availability is checked again at dispatch.”
For the captured denial: “Full context is saved at [source reference]. READ_MORE is
currently blocked: no active read-only research budget can spend this action.
Runtime suggestion: EXPERIMENT_RESEARCH_BUDGET_ACCEPT latest.” Preserve that as a
suggestion, not an instruction already chosen by Astrid. For unknown admission,
state that availability is unconfirmed. If persistence failed, state that the
trimmed source is unavailable through this continuation path; do not promise it.
The dispatcher remains authoritative if availability changes after assembly.

## Proposed correction 2: give runtime feedback its own origin

Introduce a small typed runtime-action-feedback field alongside authored emphasis.
Move this guard writer to it, retaining action identity when assigned, raw request,
outcome, reason, and the structured suggestion. Keep authored emphasis and form
preferences intact. Do not relabel pre-existing untyped text as authored by guesswork.

```rust
// dispatch.rs: guard path
- conv.emphasis = Some(message.clone());
+ conv.runtime_action_feedback = Some(RuntimeActionFeedback::from_guard(&original, &guard));
// dialogue_generation.rs: separate rendered blocks
+ render_authored_emphasis(authored_emphasis); // preserves explicitly authored direction
+ render_runtime_feedback(feedback);         // "Runtime action result", never "your own direction"
```

Carry the concise feedback through both primary and fallback request construction,
independently of a form constraint. Retain full feedback in the action record;
record whether the compact receipt survived final adaptation in each attempt's
existing request/delivery evidence. Define its pending/consumed lifetime explicitly:
a skipped or failed generation is not proof of receipt, and inclusion is not proof
of understanding. This proposal does not broaden the guard or redesign all action feedback.

## Verification before any live change

- Use the preserved first denial plus an over-cap block. Test admitted, blocked,
  unknown, persistence-failed, partially trimmed, and fully evicted cases. The
  displayed next step must match its declared state; original source bytes remain
  recoverable after successful persistence. Rendering performs no action or acceptance.
- Change admission between assembly and dispatch: the existing guard still blocks.
  Existing denied/admitted action-policy fixtures must remain unchanged.
- Render runtime feedback beside a genuine authored preference, including a form
  constraint: neither overwrites the other, and the denial never acquires the
  self-direction wrapper. Check final adapted primary/fallback messages under a
  tight budget, plus failed/skipped attempts and explicit feedback lifetime.
- Use offline fixtures first. Success means truthful guidance, preserved source,
  and correct attribution; fewer READ_MORE choices is not the acceptance criterion.

## What Astrid should be shown before an intervention

Prepare a brief steward-facing preview containing her three original request tails,
the exact runtime denial, the existing overflow instruction and emphasis wrapper,
and the proposed replacements. Ask what she intended to continue reading and whether
the replacement distinguishes her preference from the runtime's report. Show what
will remain available and the unchanged budget policy; allow correction or refusal.
Mike chooses the sharing and live-change process under Astrid's own repo rules.
This proposal sends nothing to her and supplies no research findings to her prompts.

## Rollback

Keep the two rendering/state changes separable and record the prior implementation
in the sibling change. Roll back their code paths through that repo's normal gated
deployment process if source access, preference retention, or request construction
regresses. Preserve captured receipts and overflow files; do not delete evidence,
convert feedback into authored emphasis during migration, or relax the guard.
