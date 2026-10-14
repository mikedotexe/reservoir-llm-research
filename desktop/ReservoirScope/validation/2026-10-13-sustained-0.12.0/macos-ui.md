# Packaged macOS walkthrough — 0.12.0

Executed through native desktop control on this Apple-silicon Mac, October 13, 2026.
The owned fake provider binds only an ephemeral loopback port, model
`reservoir-fixture:0.12`. It starts no actual model and contacts no Being service.

## Initial package

Binary SHA-256 `4ee2297882841777ba02ab609b3d300af165563ef624fc1a3b9325b88bfc5e50`.
`package-before-ui.json` and `initial-package-after-ui.json` agree exactly. Its archive
is retained independently; the later checkpoint-and-quit improvement has a separate
source snapshot, build log and package identity.

### Automatic journals and minimized operation

1. Opened Experiments → My reservoir. Configured the full-width seed
   `18446744073709551615`, six-step cadence, 1,000 ms pacing, 200-step / 30-attempt /
   600-second / 32 MiB bounds and the owned explicit model. Create showed step zero,
   no journals and no provider request log. Start was a separate action.
2. Both WebGL2 views rendered actual backend data: signed recurrent surface and
   separately labeled sensory fill. At step 9 both showed nine draws. No smoothing
   or reservoir-state/fill equivalence was inferred.
3. Journal at observed step 6 was saved and first applied at 7; the next entry at 12
   first applied at 13. Selected the step-6 journal while the live clock advanced.
   The reading selection stayed there and Follow latest accumulated a new-entry count.
4. Clicked the native minimize button. Read-only disk samples, taken without activating
   the window, moved from durable step 37 / six journals to step 91 / fifteen journals
   over 53.875 seconds. Afterward the UI showed step 100, the same step-6 reading
   selection and frozen offscreen graphics counters. This is a short minimized check;
   it does not measure GPU power or establish an hour-long minimized run.
5. The numerical owner eventually stopped at the attempt boundary: 30 saved journals,
   181 steps, 149 committed segments, 10,690,170 exported bytes, within its 32 MiB quota.
   A quit review and Return kept the app available. An initial desktop-control binding
   by application path became stale during minimize/restore; rebinding by bundle ID
   restored reliable control. Earlier ineffective pointer actions are not counted as
   successful Pause tests.
6. A native folder dialog exported a new immutable directory. The shipping executable's
   read-only `--verify-sustained` route passed genesis, all segments and journal/application
   checks for the exported 181-step bundle. Original and exported records remain intact.

### Pause, application and late cancellation

1. Stopped the first owner, then created seed 7, cadence 3, pace 1,000 ms, 1,000 steps,
   100 attempts, 600 seconds and 32 MiB with the same owned provider.
2. Held provider request 31 at observed step 3. Selected Pause, then explicitly released
   the response. It saved one journal, remained paused at 3, and displayed prepared
   feedback for 4 with no first application recorded. Both graphics counters stayed
   at three despite request/status updates. The held transport lasted 23,251 ms.
3. Resume advanced to 4 and showed first application at 4. At the next opportunity,
   step 6, held request 32. Cancel request and stop retained a blocked/cancelled attempt.
   Releasing its late success added no journal or feedback: step 6, one saved journal,
   two attempts remained. The native folder export passed whole-bundle verification.
4. Quit the stopped, retained session; process absence was checked without relaunching it.

The held-feedback inspection exposed a workflow improvement in code review: the initial
Checkpoint and quit path rejected even fully committed prepared feedback. The final
candidate allows that explicit decision while preserving paused recovery and requiring
Start before first application. Implicit quit still requests review. New focused tests
cover saved-prepared quit/restore/application once and failed-discard refusal.

## Final candidate

Binary SHA-256 `f68a3752a628edf11ac6161a26e6979bb22dcf4c3ee1c63f10add2cea86ab40d`.
The change is limited to explicit committed-preparation quit admission, its regression,
and two contract documents. Frontend, core and other desktop sources are unchanged;
`source-continuity.json` enumerates exact hashes. Final checks passed 20 sustained tests,
15 close-related tests and strict all-target Clippy before the shipping rebuild.

1. Relaunched and navigated to My reservoir. No prior owner was loaded automatically.
   Explicit catalog read and full verification selected the six-step cancelled session.
   Restore returned paused, with cancelled attempt 2 still blocked. There were still
   only 32 fixture requests after these actions: no retry or generation had started.
2. Explicitly skipped that cancelled opportunity, then Start continued at global 7.
   Held request 33 at observed step 9; Pause followed by releasing the reply saved a
   second journal and left its feedback prepared for 10. Both graphics counters
   stayed unchanged while the numerical boundary was held.
3. Cmd-Q showed the preparation, and Checkpoint and quit exited. Read-only capture
   `prepared-after-quit.json` shows local stopped metadata, global step 9, two journals,
   generation 3, and the core phase still Prepared. No skipped event was manufactured.
4. Relaunched, verified and restored the same session into generation 4. It stayed
   paused at 9 with saved feedback intended for 10. Explicit Start showed first
   application at 10. Pause then held at 11. Two journals and three attempts remained;
   no additional model request was made.
5. Exported generation 4/revision 39 through the native folder dialog. The final
   verifier passes. The independent evidence checker proves the original seven
   segments and prior journal are byte-identical; the captured Prepared checkpoint
   exactly joins the final ordered chain; steps 1–11 occur once; attempt 3 has one
   application at 10, with its vector held at 11. Attempt 2 remains cancelled/skipped
   and has no saved journal. See `final-ui-recovery-continuity.json`.
6. Quit the fully retained paused app and confirmed process absence. Stopped the owned
   fixture PID; preserved its final 33-request log. No real provider was contacted.

All three actual native-dialog bundles pass full verification, and all 39 deliberately
altered copied bundles are rejected. These include reanchored prompt/model/event/state
mutations, changed clock/count/seed, missing/reordered segments, a non-genesis start,
and missing or damaged journal evidence. Original exports remain unchanged. The fixture
handler's late response log is not proof that the cancelled client received that response.

`final-package-before-ui.json` and `final-archive-and-resource-check.json` bind the
unchanged shipping package. All 46 archived files match bytes/modes, and all 39 canonical
resources / 42 packaged resource files are verified. The final archive has a distinct
name and checksum; the initial archive remains historical. Broader human acceptance,
accessibility, real-model, physical sleep/crash, long-duration and other-platform gates
remain unexecuted.
