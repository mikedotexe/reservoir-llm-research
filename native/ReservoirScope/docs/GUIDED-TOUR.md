# Reservoir Scope · guided research walkthrough

[Current release and verification status](../../../research/CURRENT-RELEASE.md).

Open **Guided tour**. The first visit begins at A with a verified
scripted example. Continue is the main action: it jumps to a useful recorded moment and pauses. You can
visit any component directly. Your lesson, writing source and cursor are remembered
locally. Nothing plays or generates automatically on reopening.

## What to look for

| Component | Evidence to inspect |
|---|---|
| A · Minimal reservoir | Input arrives; state responds, then decays during the quiet interval. |
| B · Recurrence | Identical initial conditions; a difference beginning at step 2. |
| C · Sensory observer | Separate field and spectrum; the paired reservoir states remain identical. |
| D · Journal output | Prepared or submitted prompt, response, and saved journal at step 30. |
| E · Reservoir return | Journal saved at 30; return first applied at 31. |
| F · Journal memory | The journal from 30 appears in the prompt at 60. Fixed writing can remain identical. |
| G · Action choice | The scripted example chooses WAIT at 90. Inspect the choice, absence of a new journal, and retained previous return. |
| H · Regulation | Inspect measured fill and retention. The controller reaches a limit in this example; reaching its target is not promised. |

**Expected** describes the selected example. **Observed** is calculated only from
evidence through the current cursor. The explanation states what that observation
can establish. A missing control arm, failed save, or incomplete reply is not a
successful comparison. Scheduled future checkpoints may be shown, but future
journals and outcomes are not revealed early.

At D–H choose **Scripted example** or **Recorded model run**. Scripted text is
predictable and tests the mechanism. A prepared scripted prompt was not submitted
to a model. The existing model recordings are single-arm observations; they show
what was actually written and which actions occurred. They do not establish an
improvement over a control. The recorded model chooses WRITE at all three G/H
opportunities, which is a valid result.

The information-flow diagram shows input feeding the reservoir and sensory field
in parallel. Ordinary journal prompts receive sensory measurements, not the
reservoir picture or its coordinates. Journal return affects a later input;
journal memory supplies saved text to a later prompt. Only the separate controlled
observation study adds reservoir coordinates to its prompt.

## Replay and experiments

**Playback controls** expands the optional Play/Pause, Step, Next journal, Replay,
scrubber and pace controls. Collapsing it pauses playback. These controls inspect recorded evidence.
WAIT and failed writing attempts are opportunities too. Reaching the end of a
recording does not start another run. Viewing bundled examples does not create
copies in your saved library.

**Try an experiment** and **Compare with previous** prepare a stopped configuration.
Start it explicitly. New interactive runs default to 300 steps. While inspecting
an active experiment's earlier history, Step advances through existing frames;
at the latest boundary it computes one more step. Resume returns to that latest
boundary. Fresh local generation requires an explicitly selected local endpoint
and model. Start your installed local model service before fresh generation;
the app does not start it automatically. Use **Check local model** beside the settings to make one cancellable inventory request. Found shows the exact checked identity and time; changing settings clears the result. This is availability only, not a promise that generation will finish. Launch, replay and settings edits make no request. A connection-refused error means no
service accepted the request at that address. Replay never calls a model.

**Experiments** also contains Explore and the original stage recipes. **Observatory** is a direct destination for the separate recorded observations. These reduced synthetic
examples are not recordings of the Beings or the language model's private neural
activations.

## Separate examples

**What can the journal observe? · active input** keeps the sensory input active
at steps 30, 60 and 90. Both stage-D arms have identical state and sensory
measurements; only one prompt receives the current 32 indexed coordinates. The
original quiet-input examples remain available. Numerical qualification requires
maximum absolute state of at least 0.25 at each writing opportunity; this is an
input-contrast check, not a score for the resulting writing.

The associated model preparation permits one attempt, at most six requests, with
alternating arm order. Both outcomes at a failed opportunity are retained before
stopping. Model unavailability and partial failures remain in preparation history;
there are no automatic retries or model substitutions.

The September 16 user-authorized retry is available as a **Recorded model run**
under the active-input comparison. It contains 60 recorded steps of a planned 120:
both arms saved journals at 30; at 60 the added-state arm reached the 256-token
limit while copying coordinates, and the sensory-only arm saved its journal.
The partial response is preserved and labeled as having no saved journal. The
run stopped before 90. Preparation history keeps the original unavailable
attempt, prompt correction, and this separate retry report. Three saved journals
and one incomplete response are evidence to inspect, not an improvement score.

From H, open **Controller mechanism example** to inspect a separate known case
with reduced target error. This case contains only the sensory field and its
retention controller, with matched seeded 66-coordinate input. There is no
reservoir, writing, return, memory or action choice. It has 600 steps and evaluates
mean absolute distance from the 68% target over 301–600. Earlier cursors show only
the available part of that window. Reduced error in this fixture does not promise
that every input can reach the target.

## Saving and verification

Runs & examples groups guided examples, recorded model writing, separate
comparisons, saved runs and expandable preparation history. Existing examples
and failures are retained. **Import experiment…** verifies and keeps a copy in the
local Library. **Open recording…** in the action viewer inspects a file without
adding a Library copy. Export uses a normal file dialog. The shared
store remains `~/Library/Application Support/Reservoir Scope/`.

Exported records contain the observations, prompts, outcomes and boundaries needed
for replay. Historical source paths are never followed. Failed saves keep the
record available for retry or export; an unsuccessful journal save does not enable
feedback. Nothing connects automatically to the Mac Mini.

New action records use `essentials-actions-v3`, including an explicit input
profile. Existing v1/v2 records keep their original prompt and forcing interpretation.
The separate controller example uses `essentials-regulation-v1`. The bundled
headless runner supports:

```
essentials-run actions --config recipe.json --output run.json
essentials-run regulation --config recipe.json --output controller.json
essentials-run verify run.json
```

A controller recipe of `{}` selects the frozen teaching fixture. The copied app
and runner work without the repository or network access. The release is ad-hoc
signed for trusted Apple silicon research Macs running macOS 14 or later.

## Fifteen-minute newcomer check

Ask a first-time researcher to use a disconnected copy without coaching. Ask them
to find an actual model journal and its prompt, explain step 30 versus 31, point
to memory at 60, identify WAIT, explain what regulation changed, and export/reopen
the evidence. Record elapsed time, the evidence they point to, misunderstandings
and any help needed. This human observation is separate from automated or agent
presentation checks; do not describe it as passed until someone has completed it.

## Reviewed research cases

Open **Research cases** directly. Choose a question to follow supplied
evidence, authored writing, supported or unresolved interpretation, and subsequent
outcome. Exact excerpts, identities, dates and hashes remain inspectable. Export
a case and reopen it with **Open case…**. Opened cases and the selected case stay
available across navigation in this window, without creating a saved experiment.
Reopen the file in a later window. Historical source paths are labels, never replay dependencies.

The annotation repair distinguishes journal signal, reviewed defect, synthetic
repair and verified deployment from an unobserved natural benefit. The day-9 reading
case separates correct definition location, a byte/line extent error, notebook
carriage and verified subsequent navigation. Neither is a general writing score.

The [participant worksheet](NEWCOMER-WORKSHEET.md) records actual newcomer acceptance.


## Geometry first use

Open **Geometry bookmarks → Load synthetic example** to inspect invented captures,
a prediction, a comparison and a revision without another file. The visible synthetic
label distinguishes this fixture from Being evidence. **Open packet** verifies an
explicit export; cancelling or rejecting a replacement keeps the previous packet,
selection and frame. Both routes retain data only in this window. See the
[geometry guide](GEOMETRY-BOOKMARKS.md) for the measurement and provenance limits.
