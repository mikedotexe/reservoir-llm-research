# A first visit to Reservoir Scope

**0.27.0 newcomer task card · no completed human acceptance is recorded.**
This is a first-use study of the app, separate from automated tests, an agent's
UI walkthrough, and Mike's earlier review of the native app.

The participant receives the exact private app archive, its receipt, and
[Start with the writing](PREVIEW-START.md). The observer explains the task goals
below, then watches without directing clicks or explaining controls. Record any
help when it becomes necessary. The participant may stop at any time; a blocked
task is useful evidence and is never silently counted as a pass.

## Before starting

| Item | Record during the actual session |
| --- | --- |
| Participant | Initials or chosen identifier; first-time user or prior experience |
| Package | Archive name and SHA-256 from its receipt; displayed app version |
| Computer | Apple Silicon model, macOS version, available disk space |
| Session | Date, beginning/end times, observer, whether screen capture was agreed |
| Starting state | Fresh app profile or existing data; runtime already prepared or absent |

No participant name, contact or completed response is invented during preparation.
Any account provisioning or invitation to another person is a separate human step.

## Tasks

1. **Open the app and find some writing.** Use the supplied guide if needed.
   Explain what you think the app lets you investigate and what will happen if you
   simply open the experiment.
2. **Read the included sequences.** Begin at the first entry, move forward and back,
   and read the unfinished response in context. Describe the difference between
   a completed journal and that unfinished response. Keep one first impression
   and one alternative explanation before revealing the conditions.
3. **Inspect how the writing was produced.** Find a quiet observation, the exact
   writing invitation and a save/application boundary. After revealing conditions,
   explain what can and cannot be concluded from these two historical attempts.
4. **Take the reading with you.** Export the collection, leave it, and reopen the
   exported file. Find the same entry and its complete final paragraph.
5. **Prepare for new writing.** If the runtime is absent, prepare it through the app.
   State when downloads begin and whether preparation itself runs the model.
   Record the entire outcome, including time, cancellation, refusal or interruption.
6. **Create and start one bounded experiment.** Describe the distinction between
   preparation, creation and Start. Locate the quiet-observation timeline and any
   resulting writing. Stop using the app's control; retain the outcome if the run
   finishes or holds first. Resource refusal is a valid observed outcome, but does
   not qualify successful generation.
7. **Return to your work.** Export the settled experimental run, quit and reopen the
   app, then find the saved writing and restore or import it for paused review.
   Explain whether the model has started again and what Start's availability means.

Allow the participant to read at their own pace. Runtime download time is recorded
separately from interaction time. The app's preparation and model-request deadlines
stay unchanged; the study does not authorize retries or longer budgets to achieve
a successful demonstration.

## Capture after each task

| Field | Participant/observer record |
| --- | --- |
| Outcome | Completed without help / completed with help / blocked / not attempted |
| What happened | Actual actions, visible result and exact error text if relevant |
| Expectation | What the participant thought would happen |
| Assistance | Exact prompt, explanation or intervention and when it was needed |
| Understanding | Participant's own explanation, including uncertainty |
| Evidence | Screenshot/file identity if retained; complete writing rather than selected highlights |

Finish by asking what was compelling, what was confusing, and what the participant
would do next. A strong passage is not a usability pass. Comprehension, successful
navigation, understandable stopping and recoverable records are the acceptance
questions.

## How to report acceptance

Keep this task card blank until an actual human session. Record findings in a new
dated account tied to the exact package; do not overwrite earlier review records.
An uncoached first-use pass requires the core read → inspect → export/reopen and
prepare → create/start → retain → paused recovery routes to be completed and
understood without observer coaching. Resource-blocked generation remains an
explicit gap in that route. If a fix changes the package, repeat the affected
tasks against the replacement and retain both outcomes. Agent checks and a fresh
local profile support preparation; they do not substitute for newcomer acceptance
or testing on a second Mac.
