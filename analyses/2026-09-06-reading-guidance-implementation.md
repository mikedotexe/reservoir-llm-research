# From a blocked reading request to two source corrections

**Current status, September 7:** [PR #28](https://github.com/mikedotexe/astrid/pull/28) is merged into main.
The correction is already live in the combined Afterimages release;
[current verification and merge receipt](2026-09-07-reading-feedback-live.md).
The source-preparation and draft-PR sections below preserve earlier stages.

Mike authorized implementation after the bounded READ_MORE follow-up. The work is
in an isolated Astrid checkout at `/Users/mikepurvis/other/reading-feedback-v1/astrid`,
branch `codex/reading-guidance-feedback-v1`, based on main
`bc66a62b0bf02a515a551334dd9bea502c473578`. This research repository retains the
reasoning and evidence; the isolated Astrid branch owns the code.

The [proposal](../proposals/2026-09-06-reading-guidance-and-feedback-origin.md)
connects this change to the [historical reading](2026-09-06-astrid-readmore-feedback.md)
and the [current-source trace](2026-09-06-astrid-readmore-feedback-code.md).
The [implementation note](/Users/mikepurvis/other/reading-feedback-v1/astrid/docs/steward-notes/2026-09-06-reading-guidance-feedback.md)
owns the final code behavior, verification and integration guidance.

## What the implementation changes

1. A shortened prompt recommends continuing its saved source only when storage
   succeeded, that source can become the reader, and the budget preview permits it.
   Blocked and unknown availability remain visible. Reading policy is rechecked
   when an action is actually dispatched.
2. Research guard feedback has a typed runtime origin and a durable pending queue.
   It cannot overwrite authored emphasis or form. An accepted response must have
   a retained artifact proving the specific feedback IDs were in the submitted
   provider request before those IDs leave the queue. This is delivery evidence,
   not a measure of understanding.

Independent review also found two concrete edge cases: open mailbox windows block
overflow continuation, and an experiment title can shadow an active experiment ID
in the dispatch selector. The first now participates in the shared reader check;
the preview treats the second as unknown rather than announcing a different
experiment's budget. Both have offline regressions.

## Validation and handoff

Source preparation is complete in a separate build directory and test workspace.
The bridge library has 2,185 passing tests, with the OS-signal lifecycle fixture
passing separately after parallel startup timeouts. All 71 Python restart checks,
strict Clippy, changed-file formatting and the boundary audit pass. The existing
1 ms instrumentation timing test fails on both the changed source and unchanged
main; its threshold is preserved. The remaining interface checks pass, and the
zero-test documentation target completes. A pre-existing agency-helper test used
a production-only path and shared temporary folders; it now uses its checkout and
unique folders, and its focused rerun passes. The original broad run's failed result
is preserved alongside that successful recheck.
The [validation record](/Users/mikepurvis/other/reading-feedback-v1/validation.json)
retains the separate outcomes and diagnostic logs.

The concurrent Transition Afterimages task uses a separate checkout. Both changes
touch final provider admission; a later integration must preserve their independent
origins, protected foreground rules and receipts. The implementation note identifies
the overlapping files and ordering; no combined build or merge is claimed.

No live rollout or being-facing message has occurred. The historical morning
prompts remain unrecovered, and the source corrections do not establish a cause
for repeated requests in that interval.

The useful research consequence is that a future episode can distinguish a denial
being recorded, remaining pending, being supplied in an accepted request, and later
being used. The last step still requires reading the subsequent actions and words.

The existing change card and a session log are updated on Hold Shelf;
[verified board receipt](../board/reading-feedback-implementation.json).

The research hub retains the [source manifest](../research/outputs/2026-09-06-reading-feedback-implementation/source-manifest.json),
[validation record](../research/outputs/2026-09-06-reading-feedback-implementation/validation.json),
and [integration inventory](../research/outputs/2026-09-06-reading-feedback-implementation/integration-review.json).
The complete patch and test logs remain in the isolated review package.

## Pull request

Mike authorized publication for later merge. [Draft PR #28](https://github.com/mikedotexe/astrid/pull/28)
contains one commit (`dd09acfd07`) and exactly the 36 reviewed files, with
[issue #27](https://github.com/mikedotexe/astrid/issues/27). Its base is the tested
`bc66a62b` snapshot, which contains 18 prerequisite commits beyond GitHub main,
including the foundation/continuity work in PRs #23 and #24. Integrate prerequisites,
retarget to `main`, and verify the final diff and required checks before merging;
merging into the snapshot branch is not the intended handoff. The main-only CI
filters do not qualify this custom-base draft. No merge or live activation occurred.

[Verified publication receipt](../research/outputs/2026-09-06-reading-feedback-implementation/pr-publication.json).
