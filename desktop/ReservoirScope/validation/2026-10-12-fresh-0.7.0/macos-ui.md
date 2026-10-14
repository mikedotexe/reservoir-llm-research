# 0.7.0 fresh experiments — packaged macOS checks

Agent-operated desktop observations on macOS 27.0.1 arm64. This is bounded package
inspection, not collaborator acceptance, minimum-OS qualification or a soak test.
All interaction used the packaged application and native dialogs, without a dev
server, test-driver plugin, live feed or model service. Final candidate checks are
recorded below separately from the earlier attempts.

## Attempt 1: fresh Explore and a discovered quit defect

The initial package identity is retained in `failed-quit-package-attempt1.json`;
the rejected archive remains in target/qa. This attempt is not the shipping candidate.

- Entering Fresh created no session. Explicit Explore creation accepted decimal seed
  18446744073709551615 and a 600-step bound at step zero, with no invented values.
- Quiet step 1 had coordinate 0 = 0. A step-2 pulse yielded
  -0.022641762179305136. Enabling recurrence and repeat input for the next boundary
  yielded 0.04203198240461357 at step 3. Inspecting step 2 retained its earlier controls.
- The signed state surface was visible with exact selection. Explore correctly kept
  reduced fill unavailable. Run continued across navigation to Observatory. A minimize
  action and return were exercised; a read-only disk observation found a completed
  600-step checkpoint before another UI action. The tool can raise windows during
  observation, so this is not a measured minimized-duration or long-session claim.
- Returning to Fresh showed completion and a new renderer with one drawn frame.
  Save to Library succeeded. Created-here filtering found the record; Verify & open
  passed and disclosed the full-width seed and all 600 frames.
- Native Save produced `target/qa/0.7-ui/fresh-explore-600.json`, 27,936,652 bytes,
  SHA-256 406567496e680a49110b345fcee5663357fc1fb65da2d95ef13536d1e0660ca8.
  `ui-explore-conformance.json` records independent unchanged-Swift/Rust verification
  and rejection of the changed-weight negative control.
- A fresh E run with the same seed and 32-step bound paused for a journal at 30.
  Its coordinate 0 was 0.0000042900968348533035; reduced sensory fill was
  94.31040364192096%. Advance/export/Library save were blocked while writing was pending.
- Cmd-Q unexpectedly exited, confirmed by pgrep before observing the app again.
  No journal save was attempted. `quit-unexpected-exit-attempt1.json` records this
  failed gate. It led to the native menu and AppKit termination integration repairs.

## Attempt 2: recovered evidence and quit-path repair

`package-attempt2.json` retains this superseded package identity. It was superseded
by a further lock-based clean-exit barrier found during independent code review.

- Relaunch showed no active session. Recovery found the first E session at observed
  step 30, durable portable step 0, phase awaitingJournalSave, with zero save attempts.
- Its exact pending text, prompt, ID/hash and provenance path were retained. The UI
  said that inspection cannot resume/apply it or grant a committed save receipt.
- Native Save exported `target/qa/0.7-ui/recovered-pending-e-attempt1.json`, 2,248 bytes,
  SHA-256 6799e9c5f526b25ff13fc3090fcb5a41a792ef4ffc661a7673867881a7ef3b37.
  This checkpoint metadata is separate from its portable numerical snapshot.
- A new E session paused at 30. Cmd-Q opened the retention review with the same
  candidate, disabled record save/export and available journal save/explicit stop.
  Return to app preserved the candidate. Journal save then advanced durable step
  to 30 with one committed turn and journal, without advancing numerical time.
- The session was explicitly stopped and saved to Library. Cmd-Q exited; pgrep
  confirmed absence before another UI observation. A Dock-control attempt timed out,
  so this receipt does not claim direct Dock, logout or shutdown testing.

## Attempt 3: final lifecycle behavior and numerical journal boundaries

`package-attempt3.json` retains this package identity. It was superseded solely by
the committed-journal reader text repair: show the actual entry text, retaining raw
provider JSON in its separate disclosure. No numerical mechanism changed.

- Launch and entry to Fresh created no session. Explicit E creation accepted seed
  18446744073709551615, bound 32 and scheduled opportunity 30.
- The run paused at 30 with the same candidate/hash, coordinate and sensory fill
  observed above. A screenshot showed the prominent signed surface and separate
  fill card, with full seed and unavailable run controls visible.
- Cmd-Q opened retention review and kept the process/window alive. Return preserved
  the candidate. Cmd-W independently opened retention review and kept it intact.
- Save journal durably worked from the close panel: durable step became 30 without
  advancing the experiment. Return and Inspect retained turn showed Journal saved
  yes, observed/applied 30 / Not recorded, source scripted and the retained path.
- Step once changed the receipt to 30 / 31. Coordinate 0 became -0.2737858027770281;
  fill became 94.7096045511734%. The candidate did not apply before the next step.
- An explicit manual opportunity at 31 created a second pending candidate, blocked
  advancement, and saved with durable step 31. Step once completed at 32 with two
  turns/two journals; coordinate 0 = -0.4511989074539819 and fill 95.06816680786395%.
- Native Save exported `target/qa/0.7-ui/fresh-e32-two-journals-attempt3.json`,
  1,547,544 bytes, SHA-256 b9382bce3544c21c81c1fac72a6ec3fccb4be4d2bb1be1df4097097acf88cca1.
  `ui-journal-attempt3-conformance.json` records independent unchanged-Swift/Rust
  verification and both verifiers rejecting the changed-weight negative control.
- Library publication succeeded. Cmd-Q exited, confirmed by pgrep before any further
  app observation (`saved-quit-attempt3.json`).

## Final candidate (attempt 4)

The final package is bound by `qualification.json`, `source-at-build-attempt4.json`
and `archive-check.json`. `source-continuity.json` identifies changes between attempts.

- Launch and entry to Fresh again created no session. Explicit E creation with the
  full-width seed and 32-step bound ran to the scheduled candidate at 30.
- Cmd-Q opened the retention panel with the candidate intact, disabled portable
  save/export and no pending write. Save journal durably advanced durable step to
  30 without advancing numerical time. Return to app preserved the session.
- Inspect retained turn showed saved=yes and observed/applied=30 / Not recorded.
  The primary text was the committed prose beginning “I notice a steady pattern…”.
  Expanding Raw reply separately showed the exact original WRITE_JOURNAL JSON.
- Step once updated the receipt to 30 / 31, coordinate 0 to -0.2737858027770281,
  and fill to 94.7096045511734%. The next step completed at 32, with one journal;
  coordinate 0 was -0.3573273130265751 and fill 95.06816680786395%.
- Native Save produced `target/qa/0.7-ui/fresh-e32-final.json`, 1,544,710 bytes,
  SHA-256 24ee96a703c77a3397761272704a540bab0986688eb58f3a6f00981733ec39ba.
  `ui-journal-final-conformance.json` records unchanged-Swift/Rust passes and both
  rejecting the deliberately changed seeded weight. Save to Library succeeded.
- Cmd-Q exited; `saved-quit-final.json` records pgrep absence before further app
  observation. Relaunch and Fresh entry showed no active or resumed experiment.
- Recovery showed the final session completed at observed/durable 32 / 32, seed
  intact, one committed save attempt, no diagnostic and the matching portable hash.
  Native Save exported `fresh-e32-recovered-final.json`. Direct byte comparison
  proves it is identical to the earlier independently verified export
  (`recovery-export-equality.json`). The app was left showing this recovery receipt.

The final archive contains 46 regular files, compared byte-for-byte with the package.
It is a locally ad-hoc-signed preview, not a notarized distribution. Agent observations,
automated checks and future collaborator acceptance remain distinct.

## Remaining gates

Windows/Linux, macOS 14, clean-machine installation, complete keyboard/screen-reader
acceptance, direct Dock/logout/system-shutdown paths, physical power loss, OS sleep,
long-session soak, GPU timing/power and collaborator acceptance remain separate gates.
This tranche has no model transport or sustained LLM loop. Forced process termination
has checkpoint recovery only. Checkpoint inspection never automatically resumes a run.
