# Packaged macOS walkthrough — 0.8.0

Executed October 12, 2026 through native desktop control against the shipping
`target/release/bundle/macos/Reservoir Scope Tauri Preview.app`, on this Apple-silicon
Mac running macOS 27.0.1. This is an agent-observed walkthrough, not collaborator
acceptance. `package-before-ui.json` binds the exact package before launch;
`archive-check.json` checks that package stayed unchanged through this walkthrough.
No development server, test-driver service, model provider or live feed was started.

## Creation and source

The app launched with **0.8.0 · Memory and choice**. Experiments → Fresh experiments
showed an empty session and explicit Create, with Explore, original stages and the
A–H component ladder in the recipe picker. Selecting a recipe did not start a run.

Created H with fixed scripted reply tape, unsigned seed **18446744073709551615**,
11 steps, opportunities every 3 steps, leak 0.65, noise 0, initial retention 0.955,
input strength 1 and no constant bias. Creation remained ready at step 0. The accepted
source disclosure reported `essentials-action-tape-v1`, 10 precomputed packets and
its zero-semantic reference origin. It explicitly distinguished prepared context
from tape-generated replies and stated that the surface/camera is not supplied as
journal context. No paired arm or model request was claimed.

## Save, memory, WAIT and retention boundaries

1. Run stopped at the pending step-3 journal. Step/Run, Save to Library and portable
   export were disabled. The candidate prose, ID, text hash and intended relative
   path were visible, with feedback eligibility explicitly withheld.
2. Cmd-Q opened **Retain this experiment before quitting** with the same candidate.
   Quit after saving was disabled. Return to app preserved the candidate and step.
3. Save journal durably committed the first journal and advanced the durable
   checkpoint from 0 to 3, with the session paused. The next Run stopped at step 6
   with a second pending journal; its prompt disclosure was inspectable. The second
   save advanced the durable checkpoint to 6.
4. The next Run completed at step 11 with **3 retained turns · 2 journals**. The
   step-9 WAIT did not create a save pause or a third journal.
5. Inspect retained turn 2 displayed the exact step-3 journal as memory, its entry
   ID/hash, the distinct step-6 saved journal and **application step 7**. Fixed-tape
   provenance remained clear: that memory was prepared context, not a model request.
6. Inspect turn 3 displayed WAIT at step 9, no journal ID/hash, no application
   receipt, and the exact step-6 journal as memory. The view explicitly explained
   that prior returned input remains held. Exact portable inspection and independent
   numerical replay separately check the held input; the UI wording alone is not
   the numerical proof.
7. At step 3, H displayed fill 27.0496324%, retention used 0.975, next 0.985. At
   step 11 it displayed fill 68.07707379867752%, current retention 0.985 and next
   0.975. The expanded controller receipt showed error 0.0770737986775174,
   integral 0, requested 0.955 and applied output 0.975. These remain sensory-field
   controls, not direct recurrent-state regulation or evidence of writing benefit.

## Visible presentation

The actual window showed the signed 32-node contorted state surface alongside the
separate sensory fill sphere. State coordinate 0 at step 11 was
−0.4563735134238537; fill was 68.07707379867752%, with sphere/full radius
0.8796980446396875. The displayed surface fixed scale was −1 to +1. Both surfaces
became rendered when brought into view; the offscreen fill initially remained
unprepared, then drew its retained value after scrolling into view. The fill panel
reported one frame drawn without smoothing. The controller, WAIT and memory cards
were legible in the observed 1280×860 window.

This is a visual smoke observation. No GPU/power/frame-time measurement, comprehensive
picking/context-loss exercise, screen-reader traversal, minimum-OS or scaled-display
acceptance was executed for 0.8. Existing renderer implementation bounds do not
establish measured efficiency.

## Native export, Library, quit and recovery

Export retained record opened the native macOS Save panel. The initial compact panel
still showed the previous test directory, so it was expanded and Go to Folder was
used to select the explicit repository-local `target/qa/0.8-ui` destination before
saving. The resulting `fresh-h-tape-11.json` contains 626,321 bytes with SHA-256:

`a7623dd5b4f90a80ed4ba401b53dfb3fffaa0601f1315020d8674aeb20a6aa15`

`ui-h-conformance.json` records both unchanged Swift and current Rust accepting
that actual dialog export and rejecting seven targeted mutation instances.

Save to Library reported **Experiment saved to the local Library** and **Current
record saved to Library**. Cmd-Q then terminated the process, confirmed by a separate
process inventory before relaunch. Relaunch required no development server and
showed no active fresh session. Explicit recovery inspection listed earlier 0.7
entries as well as this session; no record was automatically resumed or rewritten.

The H checkpoint identified `session-1791843291799-83505-1`, generation 1/revision 19,
completed step 11/durable step 11, retained actionH/unsigned seed, the same portable
hash, and two committed journal-save attempts. Export portable snapshot through
step 11 used the native Save panel to create `fresh-h-tape-11-recovered.json` in the
same isolated test directory. It reported the same portable SHA-256. The separate
`recovery-export-equality.json` checks both actual files byte for byte and inspects
their retained memory, WAIT, application and controller fields.

## Limits

Other standalone recipes/modes, manual forced WRITE, corrupted/missing memory and
storage faults were exercised by the recorded automated core/backend suites and
36-record independent oracle corpus, not by this H-only UI walkthrough. No fresh
matched pair, external tape, local model or sustained loop is implemented by this
tranche. Windows/Linux packages, physical crash/power-loss recovery, Dock/logout/
shutdown paths, long-session soak tests and collaborator acceptance remain open.
