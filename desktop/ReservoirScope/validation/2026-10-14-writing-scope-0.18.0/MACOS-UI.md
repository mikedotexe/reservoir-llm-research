# Native app observations · 0.18.0

Agent-operated native macOS checks on October 14, 2026. These are separate from
automated source tests and collaborator acceptance. The exact local app and
pinned verifier are bound by [the archive receipt](archive-check-01.json);
the prospective [plan](NATIVE-QUALIFICATION-PLAN.md) was frozen before launch.

The previously exported 0.17 session was paused at step 361. Native Quit closed
that app before the distinct worktree 0.18 app launched. The visible header read
0.18.0. Navigation and creation generated no text. The only readiness check used
the new fixture's explicit endpoint and exact synthetic model identity. See
[launch and configuration observation](native-launch-01.json).

Session `sustained-1791992604115-1` accepted v6 and the planned bounds: 51 steps,
five attempts, cadence 10, 1,000 ms pace, 180 active seconds and 32 MiB; output
1,024, context 8,192 and 180-second request deadline. Start was pressed once.
Four journals at 10/20/30/40 were saved and applied at 11/21/31/41. The incomplete
fifth reply held the clock at step 50, with four saved journals and five retained
attempts. The interface stated that no request was active, that the opportunity
had no accepted journal or feedback, and that it would not be retried automatically.
No Retry, Skip or further Start was used.

The reader displayed full prose independently of the current numerical state.
Step 10 remained selected as the live session advanced to 50; its RMS stayed
0.48830363802103116, fill 64.65940080013085, and prior readings remained unavailable.
Step 20 and step 40 showed their own prior observations and exact previous saved
prose. The first reported input count appeared as 9007199254740993, the absent
count as “Not retained,” and the fourth as 18446744073709551615. The Evidence view
identified v6. The eight-row measurement table explicitly said that the compact
prompt did not supply the full table. Accessibility output truncates long prompt
text; exact full-prompt placement and bytes are checked independently against the
export and fixture request hashes, not inferred from the truncated UI text.

Native export selected the new worktree's `target/qa/0.18-writing-scope/exports`
using Go to Folder, then Open. Return worked without user intervention. The app
reported a committed immutable bundle at revision 76, retained separately as
`sustained-1791992604115-1-1-76`. The owned synthetic provider then exited through
its stop file. No real model, model weights or Being service was involved.

Native Quit closed the app, confirmed by the app inventory. Relaunching the same
0.18 package opened no session automatically. Reading the recovery catalog and
Verify and inspect reported this exact session at step 50, four journals and 22
segments. Restore paused for review produced a paused session with Resume disabled;
the incomplete-attempt warning remained visible. No Start, retry, Skip or Stop was
used. Native export then produced `sustained-1791992604115-1-2-77` in the same
parent directory, without overwriting the first export.

Both exports passed the pinned verifier and fixed-fixture joins. All 27
non-manifest files were identical; only manifest generation, revision and wrapper
phase changed. The underlying blocked attempt, prompt version, clocks, journals
and feedback stayed intact. The stopped-provider files also remained unchanged.
See [original result](NATIVE-EXPORT-RESULTS.md), [recovered result](RECOVERY-RESULTS.md)
and [exact comparison](recovery-comparison-01.json).

The app is left paused for review with the recovery panel collapsed. This short
check does not qualify minimized duration, GPU efficiency, crash/power-loss,
Windows/Linux installation, or effects on actual model writing.
