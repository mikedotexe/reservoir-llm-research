# 0.43.0 · authored reservoir actions

November 13, 2026. Local development checkpoint on
`codex/authored-reservoir-actions`, based on 0.42.0 scheduled conversations.

An optional **Let the model shape the reservoir** setting gives ordinary journal
turns four consequential choices: `PULSE`, `TUNE`, `NONE`, and `RELEASE`.
Pulses displace the recurrent state once. Tuning changes recurrent leak, recurrent
gain, or text-feedback scale until changed or released. The next ordinary prompt
receives effective controls and recent actual outcomes, independently of which
entry returns as memory. [Semantics and research scope](AUTHORED-ACTIONS.md) ·
[setup](GETTING-STARTED.md#let-the-model-shape-the-reservoir).

The final action line is parsed separately from journal prose. Raw replies remain
available as evidence; body text supplies feedback and memory. Quoted examples do
not authorize an action. Missing or malformed choices yield visible rejections.
The save/readback transaction prepares both feedback and action, and the next
successful numerical boundary applies the action exactly once. Recovery, retries,
exports and replay retain pending choices, controls and execution receipts.

Scheduled conversations stay passive. Plain requests remain exactly the editable
prompt. Telemetry-enabled requests include read-only controls and outcomes in an
action-enabled session, without an action menu. Historical sessions and absent-mode
serialization preserve their earlier mechanism. The capability is fixed at
creation; enabling it requires a new session.

## Validation

| Check | Result |
|---|---|
| Core suite after final parser/context hardening | 306 passed. |
| Full desktop host suite | 294 passed; 3 opt-in investigations ignored. |
| Focused desktop action tests after final hardening | 10 passed. |
| Focused desktop schedule tests after final hardening | 12 passed. |
| Frontend suite | 555 passed; 1 existing skipped test across 65 files. |
| TypeScript and production frontend | Passed; existing bundle-size advisory remains. |
| Rust Clippy | Workspace and all targets passed with warnings denied. |
| Rust formatting and diff whitespace | Passed. |
| Native macOS preview | Built, ad-hoc signed, and signature verified. |
| Independent code and documentation reviews | Completed; parser/context findings corrected. |

The full host suite preceded the final quoted-line parser and check-in context
refinement; focused action and schedule checks cover the resulting integration.
The final native build also repeated TypeScript and production frontend checks.

The native walkthrough used **Offline example writing**, two numerical steps per
entry and four writing attempts. It saved four journals and applied `PULSE` at
step 3, `TUNE leak 0.35` at step 5, `NONE` at step 7, and `RELEASE` at step 9.
The limit hold showed four recorded choices, three applied actions, zero rejected
choices, and restored controls (leak 0.65, recurrent gain 1, feedback scale 0.4).
The journal showed body text separately from the raw response and exact action.

Native export created an immutable revision-31 snapshot with four journals and
19 committed segments. Read-only verification passed exact genesis and contiguous
event/numerical replay, including journal/save/application consistency. After
normal quit and relaunch, native verification and restoration recovered the same
four choices and controls at step 9, paused, with no new writing or action.
This does not test physical power-loss durability or authenticate a model request.

The `authored_action_response` core example compares 13 scripted cases at two
seeds for 300 steps against matched `NONE` trajectories. All 26 comparisons
passed finite-state, unchanged pre-action trajectory, receipt agreement and
release checks. Pulses decayed quickly in these cases: recurrent L2 difference
after ten more steps was below 0.000467. Tuning produced sustained differences
while active; release restored controls at step 151 without resetting state.
Feedback scale 2 produced the largest observed difference (L2 3.705184) and up to
11 of 32 coordinates with absolute value at least 0.999. These descriptive bounds
are specific to this grid and forcing, not exhaustive parameter qualification.
The numerical example uses simulated in-memory save receipts, distinct from the
host/native persistence checks above.

Private logs, numerical trajectories, report, native export and verification
receipt are retained under `research/outputs/authored-actions-20261113/` in this
worktree (ignored). The canonical numerical report is
`numerical-response-final/report.json`; earlier runs remain as development records.
The preview has a separate application identity, `research.reservoir.scope.actions`,
and separate storage. Its build does not replace the running 0.42.0 check-in app.

## Research boundary

This is an implemented local action capability, not evidence that a model uses
it competently or experiences control. Validation so far uses scripted choices;
no extra model requests were introduced while the separate six-hour baseline was
running. A later comparison should distinguish the action menu's framing from
actual execution and feedback. No live-being intervention, public-sharing
qualification, publication, or change to the frozen 0.39.0 instrument is claimed.
