# 0.45.0 · recover semantic encoding without rewriting

November 14, 2026. Local development checkpoint on
`codex/semantic-feedback-recovery`, extending the 0.44.0 semantic/action trial.

A complete model response is now retained in the saved session before its
embedding request begins. If encoding fails or is interrupted, **Completed
writing awaiting encoding** shows the exact retained reply and **Retry encoding**
encodes that same writing. It does not call the writer again, select new memory,
change the original generation timing, or consume another writing attempt.
Verified restoration after quitting the app preserves this recovery path.

A successful retry saves the journal and leaves its application paused. Explicit
Resume applies the text input and any NEXT choice once at the ordinary saved
application boundary. Withheld text and action-only empty bodies still bypass
embedding. Scheduled conversations use the same recovery path while retaining
their passive action semantics. An entry can also be explicitly skipped.

Retention and request-dispatch saves precede network work. Save failures stop
dispatch and expose the existing save-recovery path. Encoding retries have
distinct request identities, so a late response from a stopped or older request
cannot settle a newer retry. Recovery and export retain the full raw response;
the received-response inventory uses a bounded, UTF-8-safe preview.

New sessions reject the unsupported scripted-writer/embedding combination;
historical configuration validation and legacy event replay remain available.
The existing semantic option keeps its 32-coordinate production projection and
opt-in setup. This change does not alter the input width, initial leak, or
ordinary default codec. [Setup and recovery](GETTING-STARTED.md#use-semantic-text-input).

## Validation

| Check | Result |
|---|---|
| Core suite | 324 passed; no failures or ignored tests. |
| Desktop host cases | 311 passed; 3 existing opt-in investigations ignored, accounting for all 314 cases. |
| Frontend suite | 577 passed; 1 existing skipped test across 67 files. |
| TypeScript and production frontend | Passed; existing chunk-size advisory remains. |
| Rust formatting and Clippy | Workspace/all-targets checks passed, with warnings denied. |
| Native preview | Built, ad-hoc signed, signature verified, and exercised through failure, restart, retry, application, and export. |
| Saved-session compatibility | New native export and both previous 0.44.0 input-choice and semantic/action exports passed exact offline verification. |

The host checks preserve 122 completed serial passes and run the remaining
192 cases as four isolated test processes. One older embedding test initially
expected a writing failure and writer retry. Its assertions were updated for
retained writing, encoding-only retry, unchanged attempt identity, and the
paused application boundary; that case then passed separately. The original
failure and all subsequent results are retained. Six focused runtime checks
also cover retention/dispatch save failures at three fault stages, stop with a
late result, restoration at the writing budget, and a final scheduled check-in.

Native qualification used an owned loopback fixture, not a model: one writing
request and two embedding requests (deliberate HTTP 503, then success). The
reply survived two app restarts unchanged. Retry encoding made no new writing
request; Resume applied its single `TUNE leak 0.75` choice at step 2, moving
leak from 0.65 to 0.75. Export produced an immutable revision-19 bundle with
one journal and one applied action. The native walkthrough found missing retry
command registration in the permission boundary; registration and capability
were corrected, rebuilt, and the same retained session completed successfully.

The separately named app is **Reservoir Scope Semantic**, bundle identity
`research.reservoir.scope.semantic`. Private logs, fixture requests, export,
verification receipts, and inspection scripts are retained under
`research/outputs/embedding-recovery-20261114/`; core and frontend suite evidence
also remains in their separate implementation worktrees.

These checks establish local recovery behavior, including normal quit/restart;
they do not test physical power-loss durability or establish long-run model
behavior. The prior four-entry semantic/action trial remains the model evidence.
No new six-hour semantic study was started. No live-being system, frozen research
instrument, sharing candidate, or published ref was changed.
