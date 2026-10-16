# macOS native walkthrough — 0.25.0

Executed October 15, 2026 Pacific (receipts use October 16 UTC), through the native
desktop automation tool against the exact app in [ui-launch-01.json](ui-launch-01.json).
Owned PID **26529**; exclusive Library `target/qa/0.25-journal-first-ui01/library`.
The [frozen UI plan](ui-plan-01.json) was saved before launch. Tool-returned native
accessibility trees and screenshots are the observation record; no synthetic DOM
or browser substitutes were used. Images remained in the tool transcript.

## Observations

1. **Initial setup:** My reservoir opens with Offline example writing selected.
   My local Ollama model is first in the Writing source menu. Selecting it reveals
   blank actual endpoint/model inputs with example placeholders and a disabled
   Check local model button. The setup explains Check → Create → Start and the
   included feedback loop. No inventory or generation request was sent.
2. **Bounded offline preparation:** returned to Offline example writing, set
   maximum steps 91, attempts 4, duration 3 minutes and storage 64 MiB. Cadence 30,
   requested pace 1000 ms, seed 20260909 and other defaults remained. Create yields
   Ready at step 0, zero journals, and Current sensory fill Unavailable. Start is a
   separate action. Inputs displayed leading zeroes during editing; the committed
   configuration was checked as the intended integers after quit.
3. **Running view:** step and fill update. At the first observed journal, entry 30
   appears as saved with feedback first applied at 31. The prose and Earlier/Later
   controls precede history. The wide layout puts current fill and the state
   surface beside the journal. Numerical details are closed initially; opening
   them exposes the 68% target and 64–72% deadband with the non-threshold explanation.
4. **Natural hold:** the run reaches live/saved step 91, three saved journals,
   1 minute 32 seconds elapsed, and 1.19 MiB / 64 MiB. Entry 90 is selected while
   following latest, and its feedback first-applied step is 91. The run-limit
   status and Writing and feedback review notice remain visible. No Resume or
   extension is attempted.
5. **Reading without moving the clock:** Earlier selects entry 60 and disables
   following, preserving live step 91. Its Recorded measurements identify writing
   step 60, show fill 17.991738% and prior step-30 fill 94.310404%; the current fill
   stays 15.00% at live step 91. Later returns to entry 90. Follow latest can then
   be re-enabled explicitly. This run did not test a pinned entry while another
   was arriving; earlier build evidence for that behavior remains separate.
6. **Text enlargement:** one View zoom-in shortcut gives 125%; the journal occupies
   the full reading column ahead of the visuals. Three further increments give
   200%; Earlier/Later controls wrap, and the full prose wraps visibly without
   horizontal clipping. Command-0 restores normal scale. Native outer geometry
   remains 1280 × 860; this is no claim of the 900 × 700 or 720 × 600 content targets.
7. **Close and replay:** normal Command-Q is sent after those checks. No app
   observation is requested afterward, avoiding an automation-induced relaunch.
   Exact PID 26529 is independently absent. The pinned same-build executable then
   runs only `--verify-sustained` against the recorded directory. All plan checks
   pass; all 19 files and store owner/enumeration remain unchanged.

## Retained scripted entries

These are deterministic example text, not fresh LLM output or a study of writing.

| Writing step | First applied step | Text |
|---|---|---|
| 30 | 31 | I notice a steady pattern and a quiet change. I remember the earlier signal and will watch what persists. |
| 60 | 61 | The broad field carries several shapes together. I wonder whether another rhythm will change the balance. |
| 90 | 91 | I feel curious about this new pattern. Let me hold the bright signal briefly and listen for what returns. |

Session: `sustained-1792113543525-1`. The [post-quit receipt](ui-session-check-01.json)
binds exact file, text and prompt hashes, configuration, verifier output and owned
process absence. It reports `verified_complete`, 91 committed steps, three journals,
14 event segments and 1,250,024 logical bytes. No provider was contacted.

No native export/restore, real-model quality, physical power-loss durability,
current-build endurance, GPU efficiency, screen-reader acceptance, smaller native
window, other operating system or collaborator acceptance claim follows from this
walkthrough. The QA app is closed and all evidence remains retained.
