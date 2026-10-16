# Packaged macOS observations

These are agent-operated native-app checks on Apple silicon, not human acceptance
or cross-platform qualification. The separate native Swift app and live Being
processes were not controlled. No activation model was started through the UI.

## Package history and corrections

1. The first package exposed a missing Tauri command permission when Check setup
   was clicked. `package-ui-attempt-01.json` preserves the failure. Commit
   `d5d09b1` registers all ten activation commands and their capability entries;
   its focused regression and strict Clippy logs are retained.
2. The next package, binary `354a7f129daec07d128fec88e48662659f499916cb6fadcc3746a6db31a7f648`,
   passed the synthetic reader/export/recovery walkthrough. Opening the optional
   mode did no work. Check setup resolved the owned Python/model and bundled
   worker. Create produced a ready session with zero observations and journals;
   Start remained a separate action. The synthetic six-entry import reached step
   121, Earlier/Later and Follow latest preserved the correct entry boundaries,
   labels stayed concealed until explicit reveal, and a reading note retained
   its exact excerpt, alternative explanation and event link. Native export
   preserved all 186 original immutable files. Restoring the prepared session
   produced paused step 0 with no events. `package-ui-attempt-02.json` records
   hashes, annotation text and session identities. Its writing is explicitly
   synthetic and supplies no model-behavior evidence.
3. The inference package at `27f05ac`, binary
   `e2d332c0dcc84b657016338db73dccb19dbb97f8a295a19a6fc26da6ce60cb0e`,
   incorporates the owned-stdin deadline/cancellation repair and qualification
   reporter repair. All 14 bundled worker files, fixtures and worker documents
   match source. The real frozen pilot ran through this binary's CLI. This
   exact app is retained privately as `pilot-package-27f05ac.app`.

## Real sequence walkthrough

The third package opened My reservoir without launching inference. Opening
Activation and checking setup succeeded using its bundled worker. A new export
bundle was constructed from the completed pilot session's exact UTF-8 files,
leaving the source directory unchanged, and selected in the native Import dialog.

The UI reported Complete, step 121, 12/12 quiet observations and 6/6 journals.
Start and Stop were disabled. Reading A initially concealed the condition.
Earlier selected entry 5 at observed step 100 / applied step 101; Later returned
to entry 6 at 120 / 121. Follow latest turned off on Earlier and could be restored.
Opening Evidence alone left labels hidden; explicit Reveal displayed Decaying
trace and the expected model, calibration and journal hashes.

The timeline displayed 48 ordered events, including quiet processing, receipt,
save/readback, and next-step application. This revealed a reader gap: the quiet
observation's actual text was only in technical evidence. A subsequent UI-only
repair exposes that text alongside its processing/application boundary. The
experimental worker, calibration, schedule and retained pilot were unchanged.

Native Export saved `activation-1792120199861083000.activation.json` locally.
All 188 original immutable files matched byte for byte; the 190-file export adds
the import identity/manifest and updated latest pointer. Independent CLI replay
of the imported directory passed, with six journals, 48 events and 121 steps.
`package-ui-attempt-03.json` retains the export hash and verifier output.

The full prose remains in the saved journal and export; accessibility snapshots
may abbreviate long individual text elements. No successful UI action is used
as evidence that an additional model request ran.

## Final reader package

Commit `d63884b` changes only frontend observation presentation. Its package binary
is `be00fac6fecaf03a8ee554dfc451d9ebad8126f071fac9f689159e581bcdde3a`;
39 focused frontend checks and TypeScript pass in `frontend-timeline-final.log`.
After relaunch, Refresh saved runs and Restore reopened the real completed
sequence at step 121 with Start disabled and labels concealed. The timeline now
shows all twelve exact quiet inputs, including the first rain/window/thread
observation requested at step 9 and received/applied at step 10 without sampling.
Earlier reached entry 1 with its step 20 / 21 boundary. Visual inspection showed
the complete-prose reader with legible text and navigation.

A contextual note on “The reservoir hums.” retains the sequence interpretation,
the title/rain/memory alternatives, and preceding events 2, 4 and 5. Saving the
note explicitly reported that it remains separate from model feedback.
Native export to a new `pilot-01-reading-A-annotated.activation.json` preserved
all 188 original immutable files and included the note. Offline verification
still passed at six journals, 48 events, 121 steps. The 192-file export hash,
note and verifier receipt are in `package-ui-attempt-04.json`. All 14 bundled
worker files remain byte-identical to the qualified worker; no Python bytecode
is packaged. The original pilot package and original source evidence remain
separate and unchanged.

## Boundaries

The inference path is exercised through the packaged binary's CLI; the native
walkthrough covers setup and retained evidence. Cancellation, duplicate/late
results, blocked stdin, worker loss and paused recovery are covered by focused
automated tests. The app is ad-hoc signed, with no notarization claim. This does
not constitute a full accessibility audit, human acceptance, or Windows/Linux
package and UI qualification.
