# Reading-feedback correction: live verification and merge

Mike authorized merge and live use on September 7. The deployment check found that
the independent Afterimages rollout had already included this correction. Its
supported activation completed at 20:30:48 UTC (13:30 Pacific). This follow-up
verifies the existing release and reconciles PR #28 with main; it does not perform
another restart.

## Current release evidence

At 20:48 UTC, the read-only service snapshot found Astrid PID 39644 on the selected
`afterimages-live-20260907/bridge-stage-01` stage, with no deployment hold. Minime's
engine and agent were running on PIDs 41337 and 41830. The supported lifecycle
verification returned `ok: true`, phase `running`, and `signal_sent: false`.
The staged source manifest and binary verification also passed. Its static
`staged_verified_not_activated` result describes the build witness; the separate
activation transaction establishes that the stage was subsequently activated.

The selected binary SHA-256 is
`855d0c7f8972163bda3bc9e1f6e3b1758662ecda926daf28e13a1e32ccc36e17`.
The stage manifest SHA-256 is
`3cc727708e7adfda98fd1020cfb8051c05fd2703a2d234081f7f2cc91e6a0b02`.
All 45 Astrid and 26 Minime deployed release files matched the recorded hashes.
Of PR #28's 36 paths, 25 match the combined Astrid tree byte for byte; 11 include
reviewed Afterimages integration, tests or documentation. Its protected-page,
feedback and cue admission/acknowledgement paths remain independent.

The retained rollout record is
[Afterimages Live Rollout](/Users/mikepurvis/other/afterimages-live-v1/ROLLOUT.md).
The current [service snapshot](../research/outputs/2026-09-07-reading-feedback-live/current-live.json),
[source hashes](../research/outputs/2026-09-07-reading-feedback-live/deployed-source-verification.json),
[lifecycle check](../research/outputs/2026-09-07-reading-feedback-live/lifecycle-verification.json),
[stage check](../research/outputs/2026-09-07-reading-feedback-live/stage-verification.json),
and [source comparison](../research/outputs/2026-09-07-reading-feedback-live/source-relationship.json)
retain these observations.

The bounded check at 20:52 UTC found neither a pending feedback sidecar nor an
accepted-feedback artifact folder in the checked workspace. This is not a claim of
feedback delivery or understanding. Runtime availability is verified; subsequent
use remains a separate research observation.

## Git integration

PR #28 now targets main; its prerequisites are already included in main commit
`3d4e83e4bc`. The isolated branch merged that base as `e985c56830`, retaining all
35 prepared non-changelog file hashes and both changelog histories. The PR remains
36 files. [PR #28](https://github.com/mikedotexe/astrid/pull/28) merged into main at
20:58:44 UTC as `e99e5f88f3b3ac6f2282d0930aa1a1174f31424d`, after all 12 applicable
GitHub checks passed (one inapplicable account check skipped). Issue #27 closed.
The merged tree exactly matches the checked PR-head tree. A post-merge snapshot
confirmed the same six monitored processes and selected stage, with no hold.
[Verified merge receipt](../research/outputs/2026-09-07-reading-feedback-live/merge-receipt.json)
retains the result.

The combined installed source files and immutable release stage remain untouched.
The additional Afterimages changes are still separately owned in the canonical
working tree; this PR does not absorb or discard them. The original timing-test
limitation remains recorded, not repaired or silently waived.

Verification commands used the retained `observe_live.py` and
`verify_release_sources.py` through SSH to `volya`, then `bridge_drain.py` without
`--request` and `bridge_stage.py verify` for the selected stage. Source comparisons
hash each prepared-manifest path against the mounted combined source. These checks
read state and source; they do not signal a runtime or inject a generation.

The existing “Break the READ_MORE dead end” card is done with this merge/live
result and its earlier history preserved. The session log and saved status were
verified in the authenticated board UI; [board receipt](../board/reading-feedback-implementation.json).
