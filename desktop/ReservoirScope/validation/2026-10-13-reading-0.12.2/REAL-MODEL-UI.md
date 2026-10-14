# Actual 0.12.2 real-model journal walkthrough

The packaged application completed one explicitly started, four-request Gemma run,
saved four journals, and applied each at the following numerical step. It exported
the completed history through the native folder dialog and quit normally. This
account records the parent agent's actual UI observations; independent replay and
prose interpretation are recorded separately in [the results](REAL-MODEL-RESULTS.md).

## Exact session and boundaries

[Creation](real-model-created.json) binds session `sustained-1791919382664-3`,
generation 3, app PID 84707 and executable SHA-256
`2fa824855d1172ebf707b4f1ce5f50d2c3eb74ab4aeeb437d41dc566f818db8d`.
The exact selected source was `gemma3:4b` at the owned loopback endpoint
`http://127.0.0.1:63515`. The native readiness check matched the staged manifest
digest. Create left the session at step zero; Start was a separate explicit action.

The accepted bounds were seed 20261013, writing every 30 steps, requested pace
1 second per free step, 121 steps, four attempts, ten minutes and 64 MiB storage.
The original limits were never extended. The final budget boundary retained
121 live and durable steps, four journals, 19 segments and 158846 milliseconds of
session running time. The UI showed 2 minutes 38 seconds and 1.70 MiB / 64 MiB.

## Reading and minimization

After writing had begun, the first journal at step 30 was explicitly selected.
As subsequent journals arrived, the reading position stayed there and Follow latest
stayed off. Before minimization the UI showed live step 100, durable step 91,
three saved journals and two new entries relative to that selection.

[The minimization marker](real-model-minimized.json) and
[pre-restore receipt](real-model-before-restore.json) establish a conservative
91.029388792-second minimized interval. The run reached its original budget during
that interval. This duration includes completed/stopped time, so it is not a claim
of 91 seconds of continuous advancement or another multi-hour qualification.
Restoration showed step 121, four journals, the original step-30 selection and
Follow latest off with three new entries. Surface and fill draw counters both
remained 60; both renderers were already offscreen while reading before minimization.
This observation is not a measurement of GPU utilization, power or total WebKit cost.

The first journal's full prose was visually inspected with Evidence closed. Opening
Evidence with the keyboard showed the exact prompt, saved hash, model identity,
completed response, timing and first application at step 31. Later, keyboard
navigation to Follow latest and Space refreshed all four list entries and selected
step 120 with first application at 121. A screenshot inspection confirmed the final
prose presentation and its inert Markdown characters. Screenshots were inspected
inline through the native tool; this account does not assert retained image files.

### Input qualification limitation

Several AX button and screenshot-coordinate click attempts after restoration only
scrolled or produced no observable action. They did not establish a working mouse
activation path. Keyboard Tab/Shift-Tab, Space and Return successfully operated
Evidence, Export and Follow latest without relaunching the app. No frozen React or
backend defect was established by this episode. Preserve the unresolved click-path
observation for human/native pointer review; do not relabel these attempts as passes.

## Native export and shutdown

Keyboard activation opened the native parent-folder dialog. Selecting its owned
`target/qa/0.12.1-reading/exports` parent produced the actual success message and
historical export receipt at revision 143. The immutable directory is:

`target/qa/0.12.1-reading/exports/sustained-1791919382664-3-3-143`

The older parent-directory name is not the producer version. The receipt displayed
121 verified steps, four journals, 19 segments and 1781880 bytes. Its manifest hash
is `215162126a8701c55f8ad039cbd081071f84a6d18903366c0e723f69d2780d1c`;
checkpoint hash is `1a066c4fec045169e8cacd582ba5b4d78a664be0576860c82e079eaa597c1e3e`.

Native Cmd-Q then exited the app. [The independent absence receipt](real-model-clean-quit.json)
confirms PID 84707 absent, unchanged executable hash and the retained budget boundary
at 121 steps/four journals. No real-model request was retried or sent after completion.

The owned model supervisor reported an OS permission error during shutdown. Its
original failure receipt remains intact. [Supplemental read-only checks](owned-model-cleanup-supplement-01.json)
found the exact server and supervisor absent and the original process group empty
three times, without additional signals or service calls. The precise failing syscall
remains unknown; this is not a clean automatic-supervisor pass. The owned synthetic
provider's [separate stop receipt](owned-synthetic-provider-stop.json) also records
confirmed absence. No Being service or workspace was involved.
