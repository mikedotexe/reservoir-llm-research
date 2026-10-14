# Preview 0.6.0 — packaged macOS checks

Status: shipping 0.6.0 arm64 app built; new packaged UI checks blocked by locked desktop.

The existing 0.5.1 preview was visible at the start of this tranche. Before the new
build, desktop control reported that the Mac was locked and automatic unlock could
not unlock it. An unlock was requested. The prior read-only preview process was
terminated by exact executable identity for build hygiene; this is not a successful
UI quit/lifecycle check. No new response/preparation UI acceptance is inferred from
source review, React tests or successful compilation.

After the shipping 0.6.0 build completed, `cua.getApp` was attempted against the
exact new app path. Desktop control again returned “The Mac is locked and automatic
unlock could not unlock it.” The pending unlock request has not been answered.
No 0.6.0 screen, native dialog, rendering interaction or UI launch success is claimed.

## Candidate walkthrough

- Launch the shipping app, confirm 0.6.0, and open Observatory → Action responses.
- Load bundled native receipts: eight applied boundaries and ten total events.
  Inspect ordinary/applied/difference values, source identity and the fixed whole-bundle
  scale. Admission/completion show no applied state. Compare states, move the shared
  camera, select a coordinate, use exact fallback and test context recovery.
- Export original native receipts through Save, cancel another Save, then reopen
  exported bytes through Open. Compare exported SHA and bytes with canonical input.
  Reject an invalid replacement without losing the accepted frame or selection.
- Load the distinct esn-divide simulation: 65 samples, original boundaries 200–264,
  fixed delta ±0.001, declared return sample 2 with eight-boundary dwell. No measured
  fill/time/native-PCA interpretation. Inspect sample 0 and sample 64, playback,
  pause, navigation/return and exact paired coordinates.
- Open Preparation history: original unavailable, correction not executed, separate
  retry failed with historical verification passed. Inspect 60 steps, four requests,
  two left journals and one right journal. Open its hash-bound retry recording and
  confirm the current experiment verifier runs independently.
- Export all three reports through native Save; compare each file byte for byte and
  SHA for SHA with its own original. Verify cancelled export retains selection.
- In the Library, expand the preparation disclosure and open an earlier attempt.
- Confirm the previous fill/state recordings remain distinct and readable.
- Check compact/scaled layout, keyboard access, close/relaunch and single instance.

Automated file-boundary checks do not substitute for native-dialog checks. Measured
GPU frame times, power, memory, minimum macOS, Windows, Linux, full accessibility and
human collaborator acceptance remain separately unqualified unless explicitly
recorded in a later artifact-bound account.
