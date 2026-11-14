# 0.42.0 · scheduled conversations

November 13, 2026. Local development checkpoint on `codex/scheduled-conversations`.

**My reservoir** can now ask an editable conversational question at intervals
while ordinary journaling continues. The preset asks at hours 1 through 6.
Every complete answer follows the existing save, readback, encoding and feedback
path. The final answer is applied before completion, even at the duration limit.
[Setup and reading](GETTING-STARTED.md#schedule-a-conversation-during-the-run).

The context toggle includes actual telemetry, selected earlier writing and the
standing contract, or sends only the editable prompt. Paused edits affect future
unprepared check-ins and preserve every revision; retries retain their original
wording. A six-slot outcome list keeps unanswered, failed, skipped and missed
opportunities visible. Shuffled reading hides chronological/context displays until
revealed. Exact prompt and feedback evidence remain available for each answer.

The schedule uses accumulated running time, not numerical steps. Generation time
counts, pauses and detected sleep interruptions do not. Safe writing boundaries
can delay dispatch. Missed opportunities are recorded rather than backfilled in
a burst. Step and attempt capacity is provisioned at setup; storage holds and
provider failures still require explicit handling. Timing remains fixed after
creation. A completed schedule stays complete after restoration.

Implementation uses explicit core admission/settings events and frozen turn
metadata, carried through retries, saves, feedback, checkpoint replay and export.
Historical prompt templates and absent-schedule serialization remain unchanged.
The existing difference channel accepts observations between ordinary turn steps.

## Validation

| Check | Result |
|---|---|
| Full Rust workspace | 572 passed, 3 opt-in research investigations ignored (289 core, 283 desktop). |
| Focused scheduled desktop tests | 12 passed, including the additional final-commit failure/retry regression. Its later durable-display refinement also passed separately. |
| Frontend suite | 544 passed, 1 existing skipped test across 64 files. |
| TypeScript and production frontend | Passed; existing bundle-size advisory remains. |
| Rust formatting and Clippy | Passed for the workspace and all targets, with warnings denied. |
| macOS native preview | Built and ad-hoc signed with a separate application identity. |
| Independent implementation review | Completed; identified clock, recovery, capacity and reading issues corrected. |

The native walkthrough used **Offline example writing**, a 45-second duration
and 15-second interval. It completed three scheduled replies plus one ordinary
journal. The first check-in used only the original prompt. At 26.094 seconds of
running time the paused edit saved revision 1, enabling telemetry and changing the
prompt; the later two check-ins retained that revision. All three answers were
applied. The final application was step 43, with completion at 46.365 seconds.
These timings describe this scripted walkthrough, not model performance.

The shuffled view hid chronology and the ordinary journal/measurement displays.
Native export succeeded. After normal quit and relaunch, verification recovered
all four journals, all three applied check-ins and both settings revisions;
restoration kept the schedule complete with Resume disabled. Recovery wording
was then corrected and covered by focused frontend tests before the final rebuild.

Checks used `cargo test --workspace`, focused `sustained::tests::check_ins` tests,
`cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets -- -D warnings`,
`npm test` and `npm run build`. The six-hour schedule is exercised with controlled
elapsed time; an actual six-hour endurance/model run has not been performed.
The private test logs, native export and file-hash receipt are retained under
`research/outputs/scheduled-conversations-20261113/` in this worktree (ignored).

## Research boundary

This is a local application feature and an exploratory reading capability. No
six-hour model study, controlled telemetry comparison, qualification for public
sharing, live-being intervention or publication is claimed. Prompt-only replies
receive no explicit run history. Switching the toggle changes memory and
instructions as well as telemetry. Changes in expressed experience can be read
and discussed while subjective experience remains unresolved.
