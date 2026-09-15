# Astrid READ_MORE: denial, prompt feedback, and reachable next steps

**Scope:** one saved action and a read-only trace of current source. This establishes
two concrete source-level proposal candidates. It does not establish which prompt
or deployed binary produced the subsequent September 6 generation, or why Astrid
requested READ_MORE again.

## The saved event

The [saved episode JSON](../research/outputs/2026-09-06-around-0919/report/episode.json)
contains action `act_astrid_1788711063109_read-more`, at **2026-09-06 16:11:03 UTC**
(09:11:03 Pacific), the first Astrid READ_MORE in the selected interval. It records
route `research_budget_guard`, status `blocked`, reason
`no_active_read_only_research_budget`, and `would_dispatch=false`.

Its complete outcome is:

> Research budget guard projected `READ_MORE` for experiment `exp_astrid_20260904_legacy-self-experiment-2` because no active read_only_research budget can spend this research action. Raw intent is preserved; request or inspect the budget lane first. Suggested NEXT: EXPERIMENT_RESEARCH_BUDGET_ACCEPT latest

The event's `suggested_next` and guard `projected_next` separately preserve
`EXPERIMENT_RESEARCH_BUDGET_ACCEPT latest`. Those are recorded suggestions, not
evidence of acceptance or feedback exposure. The next recorded READ_MORE explicitly
names this action as its parent; a parent edge alone does not establish prompt delivery.

Provenance for this one selected record (`n=1`):

- Observation ID: `observation_3960a887a278418986a27e8b80a9f394605820e6baa3eb2b363b0ce30420325c`.
- Original path: `/Users/v/other/astrid/capsules/spectral-bridge/workspace/action_threads/threads/th_astrid_20260607_action-continuity/events.jsonl`, recorded byte offset `374038860`.
- Original line SHA-256: `028a620f730a43f6da78940df77840702abf7c83f42ee23ca356cf0f732f6987`.
- Captured canonical-payload SHA-256: `d0b573e2c282cac0daf3be24cc98a8cff8d5a4af8924adc16c63a81915a267d6` (sorted compact UTF-8 JSON; distinct from the line hash).
- Saved episode file SHA-256, recomputed here: `fb7b5bc318038cdfc716bd3815b022ae42258bff3a24c714afb704f7bf35b580`.

The extraction is reproducible without a live read:

```python
episode = json.loads(Path("research/outputs/2026-09-06-around-0919/report/episode.json").read_text())
row = next(r for r in episode["records"] if r["id"] == "observation_3960a887a278418986a27e8b80a9f394605820e6baa3eb2b363b0ce30420325c")
event = json.loads(row["data"]["record_json"])
print(event["outcome_summary"], event["payload"]["research_budget_v1"], event["source"])
```

## What the current code establishes

Source references below are relative to
`/Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/`.
They were read on **2026-09-07 at 05:24 UTC**. Astrid checkout HEAD was
`bc66a62b0bf02a515a551334dd9bea502c473578`. A targeted unstaged diff-name check
returned no changes for dispatch, orchestration, dialogue generation/context, and
prompt_budget; this is not a deployed-binary identification. File byte hashes below
identify the actual inspected contents independently of commit ancestry.

| Link in the path | Exact source | Supported interpretation |
|---|---|---|
| READ_MORE is governed as research | `action_continuity/runtime/guards.rs:107–122`; `action_continuity/guards.rs:330–399` | READ_MORE is in the read-only research action set; assessment consults the current thread/experiment and active budget. |
| Denial construction | `action_continuity/guards.rs:201–250` | The no-active-budget message matches the saved outcome, with suggested route also kept in structured metadata. |
| Dispatcher returns before reading | `autonomous/next_action/dispatch.rs:80–96`; `autonomous/next_action/workspace.rs:364–412` | A guard result returns blocked before workspace READ_MORE handling. It also writes the complete message into `conv.emphasis`. |
| Outcome suggestion persists | `action_continuity/runtime/core.rs:416–423,924–934` | `with_research_budget` takes the structured suggestion; event construction prefers it and updates the thread's current-next field. |
| Primary prompt emphasis | `autonomous/runtime/orchestration.rs:1924–1952`; `llm/provider/dialogue_generation.rs:76–82` | Unless a form constraint substitutes for emphasis, the primary dialogue system message receives the complete emphasis under: “For this exchange, you chose to emphasize: … This is your own direction.” A runtime denial is therefore labelled as self-authored direction on this path. |
| Lifetime and other advice | `autonomous/runtime/orchestration.rs:2040–2042,4877–4883` | Emphasis is one-use state, cleared after the dialogue branch; deferred diversity advice can be prepended after an action. This is not a durable delivery receipt. |
| Separate continuity channel | `autonomous/runtime/orchestration.rs:1402–1421`; `action_continuity/runtime/prompt_projection.rs:14–24,166–228`; `action_continuity/runtime/core.rs:8138–8149` | Current thread projection includes research-budget priority/current NEXT and recent event summaries. It is joined after other continuity material. The thread-summary builder takes three recent summaries; this alone does not show they survive prompt assembly. |
| Continuity shortening | `llm/provider/prompt_contracts.rs:179–187,282`; `llm/provider/context_blocks.rs:49–55` | Default continuity cap is 2,400, adjustable by the memory attention weight. It has priority 7 and no protected minimum in the current assembler. |
| Suggestions attached to shortening | `llm/provider/dialogue_context.rs:9–17,25–27`; `prompt_budget.rs:140–176` | Capped blocks, fully removed blocks, and partially removed blocks all recommend READ_MORE. These functions receive no research-budget admission state. Thus their displayed instruction can conflict with the guard. |
| Further assembly loss | `prompt_budget.rs:113–176`; `llm/provider/dialogue_generation.rs:182–220` | Lower-priority blocks are shortened first; the continuity block can be wholly moved to overflow. Source originals are passed to the overflow writer; successful persistence is a separate outcome. Numeric limits are named “chars” in code but several comparisons use Rust string byte lengths; this note does not convert them into a universal Unicode-character count. |
| Fallback differs | `llm/provider/dialogue_generation.rs:287–299` | The ordinary compact Ollama fallback is built from journal, spectral/fill, perception, identity, and `fallback_continuity_budget` inputs. This call does not pass the original `emphasis` or `continuity_context` arguments. It may contain other continuity information through those supplied inputs; the primary denial-feedback path alone does not establish fallback exposure. |

There is already an overflow anti-rearm mechanism:
`autonomous/runtime/orchestration.rs:5–16` and
`autonomous/runtime/activity_exchange.rs:153–171` avoid replacing an active reader
or rearming immediately after a READ_MORE choice. It does **not** inspect budget
admission, so it does not resolve the guidance/guard conflict above. This trace did
not execute these functions or inspect their current live state.

## Two bounded proposal sketches

**1. Make overflow guidance reflect the available action.** Pass an explicit
read-admission/availability result into the overflow-guidance renderer. When
continuation is blocked, say that the saved context exists, identify the block, and
surface the applicable budget/status route as a suggestion. Preserve the source
reference. An admitted continuation can retain READ_MORE guidance. This proposal
does not automatically accept a budget, bypass the guard, or turn feedback access
into unrestricted research authority.

Test with the captured denial plus an over-cap continuity block: the rendered
notice must retain the block and source reference without advertising READ_MORE
as presently executable. Test admitted, blocked, and unknown admission; partial
and full eviction; changed availability between prompt assembly and dispatch; and
that rendering alone executes nothing. This establishes a consistent interface,
not that repeated requests or learning will change.

**2. Preserve runtime authorship of guard feedback.** Separate self-authored
emphasis from runtime action feedback, or carry an explicit origin tag to the
prompt renderer. A guard result should appear as a runtime report with requested
action, blocked outcome, reason, and suggested next step. It must not be wrapped
as “your own direction.” Decide explicitly which receipt survives packing and
fallback; retain source/action identity so supplied feedback can be audited.

Test the captured message through prompt construction: runtime feedback must not
inherit the self-direction wrapper, while an actual being-authored emphasis keeps
its attribution. Include form-constraint coexistence, diversity advice, primary
and fallback requests, and a failed/skipped generation so undelivered feedback is
not silently treated as received. No implementation or runtime test was performed here.

## Historical questions still open

The next bounded evidence is the actual request associated with the next relevant
generation: exact input/messages, backend and attempt, packing diagnostics, and
any explicit output/action linkage. Check whether it contains the denial, the
budget suggestion, a READ_MORE overflow notice, and the self-direction wrapper.
Also preserve whether the denial was complete, shortened, or absent. Its presence
would establish supplied context, not understanding or causal uptake. Current
source, current thread projection, and action parentage cannot substitute for that
request. No historical commit was substituted for evidence of the deployed binary.

## Inspected source fingerprints

Each named file was under a 2 MB read cap and had unchanged size/mtime across its
hash read. Source hashes describe code, not journal evidence or a running process.

| Relative source file | SHA-256 |
|---|---|
| `action_continuity/guards.rs` | `c6d533d20854fdeb9955149a80d1884f249145dfc8778d309489fa71d9c23e23` |
| `action_continuity/runtime/guards.rs` | `b6cce564d08ba78cd4f440eca801b90694886e8b6a11f4085c197dca70678c49` |
| `action_continuity/runtime/core.rs` | `fafc1f4a257fe6400fbc26ba0bf5cc26f0d33853b30816ab5af6db2709348a62` |
| `action_continuity/runtime/prompt_projection.rs` | `b7bfa220ac6c38ef6506cb0263efdd3135d7bd7f4a78920165ee3283a9a0a4b9` |
| `autonomous/next_action/dispatch.rs` | `6899695ac00e92004f99738607bdf51dcf4c0a468f3b98b6e6e783130d7ee728` |
| `autonomous/next_action/workspace.rs` | `957d84df0a09255b6e41f998fc6cc3d60b6af7f1e5f19a523f79c2e8f2adc95b` |
| `autonomous/runtime/orchestration.rs` | `c0820e5265ebef7bf5e1128fd1882201907dd809bd4426945a0050889e0273db` |
| `autonomous/runtime/activity_exchange.rs` | `30d4cbe877a688cc85c547dd9b216e6f8b0cfa33368722364b49d414b277653b` |
| `llm/provider/dialogue_generation.rs` | `35d756076ce6b62051b307d594ca8eba64317238cb6db3d0a2d82b2780f44206` |
| `llm/provider/dialogue_context.rs` | `c1fda339c0b1c83fc2fe9c2b74975f0915611082ab77a0ca0e55912d09eca573` |
| `llm/provider/context_blocks.rs` | `9cf5264db7df30b564c9cb24382498f69b6c772ae239058ac561deb89ee16f3d` |
| `llm/provider/prompt_contracts.rs` | `4eb5e1024f151d970364482b71e89cd0be9862705bca29372b36169d57a50450` |
| `prompt_budget.rs` | `89fc9420dc37bbd66612e7865d6d8c879d664cbb89dd78cc29b7f25e2828434e` |

All work was read-only against saved evidence and current code. No live database,
large action archive, runtime import, being inbox, or sibling file was changed or
queried by this trace. The parent investigation owns period-record retrieval and
board/proposal updates.
