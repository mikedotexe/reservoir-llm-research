# Your first journal session

The aim is simple: open Reservoir Scope, let a local model write a short sequence,
then read it with some curiosity. You do not need to understand the reservoir's
math to begin. Plan for **up to 30 minutes of running time**, after installation
and model setup, plus a few minutes to read.

These instructions describe **0.48.0 source**. If you received the older 0.27.0
candidate 04 package, follow its [install guide](PREVIEW-START.md).

## 1. Open the app

Have Node with npm, Python 3.12+, Rust via rustup and your platform's build tools
installed. Node 24 is used locally; the repo pins Rust 1.94.1. On macOS, install
Xcode Command Line Tools. [Full build instructions](BUILDING.md).

From the repository root:

```sh
cd desktop/ReservoirScope
npm ci
python3 scripts/stage_activation_bootstrap.py
npm run tauri -- dev
```

The staging command downloads and verifies pinned runtime assets, not a model.
Use your Python 3.12+ command if `python3` is older, and set `PYTHON` for the Tauri
build as described in [Building](BUILDING.md#choosing-python). The first compile
takes longer than later launches. Keep the development terminal open.

The app opens on **Study**, a walkthrough of a completed experiment. Select
**My reservoir** to start your own journal. For a quick look without any model,
leave **Offline example writing** selected, choose **Create my reservoir**, then
**Start**. Those entries are scripted examples.

## 2. Choose a local model

Install and open [Ollama](https://ollama.com/), or use your existing local service.
The app does not install a model or start the service for you.

Our recent journal explorations used **gemma4:12b**. If your machine can run it,
you can download it and check the installed names with:

```sh
ollama pull gemma4:12b
ollama ls
```

Model setup may take longer than the first journal session. Another installed
model is fine for exploration; record which one you used and expect different
writing. The same model tag can also change over time, so the tag alone does not
guarantee an exact research reproduction.
[Ollama CLI reference](https://docs.ollama.com/cli) · [model page](https://ollama.com/library/gemma4:12b).

In **My reservoir**:

1. Under **Writing source**, choose **My local Ollama model**.
2. Enter your **Local server address**, usually `http://127.0.0.1:11434`, and the
   **Exact model name** from that service's inventory.
3. Choose **Check local model**. This checks availability without generating a
   journal. Available does not guarantee that the model will fit in memory or
   finish within the response limits.

This path supports Ollama's local API, using an HTTP loopback address with an
explicit port. An arbitrary model file or another provider's API is not a
supported replacement.

## 3. Set up a short session

Open **Advanced settings** before creating the session:

The request deadline defaults to three minutes. For slower local models or shared
hardware, choose 60–600 seconds under **Writing limits** before creating the
session. A longer ceiling does not request longer writing or retry failed calls.

| Setting | For this first session |
|---|---|
| **Writing invitation** | **Plain journal · prior text, no numerical readout** |
| **Writing limits → Model thinking** | **Off · reply only**, for gemma4 |
| **Writing limits → Writing temperature** | **0.7** |
| **Writing limits → Context tokens** | **8192** |
| **Earlier entry returned** | **Latest applied entry (as built)** |
| **Seed and run limits → Maximum writing attempts · including retries** | **12** |
| **Duration limit** | **0 hours, 30 minutes, 0 seconds** |

Leave the other settings as they are. This is a manageable first reading, not an
exact repetition of a published study.

**Want to let it run for hours?** Set the limits before choosing Create my reservoir.
The existing defaults allow up to **6 hours, 360 writing attempts and 10,800 steps**.
Keep those defaults for a longer run, or choose your own duration, attempt and step
limits under Advanced settings. The first limit reached holds the session, so
raising the duration while leaving the attempt limit at 12 will still stop after
12 attempts. Keep the machine awake and start with a model that completes writing
successfully. These limits allow longer runs; they do not guarantee uninterrupted
writing for that duration.

**Plain journal** uses a standing writing contract and, when available, one earlier
saved entry. With the memory setting above, that is the latest applied entry.
It sends no numerical readout or context tag. The reservoir continues to run and
receive encoded writing, but the model cannot inspect that hidden state through
this invitation. The **Current readout (as built)** option supplies observations
instead; it remains the app's default. Saved sessions keep their original prompt.

Choose **Create my reservoir**, then **Start**. Keep the app open and your machine
awake. It can run minimized. You can **Pause** whenever you have enough to read.

## 4. Let a few entries arrive

At the default pace, a writing opportunity comes after 30 numerical steps, about
30 seconds before generation time is added. The model finishes, the app saves and
checks the entry, and the journal appears as complete prose. Partial text is not
streamed into the journal. Generation and saving pause the numerical clock.

The first reached duration, step, attempt or storage limit holds the session.
Twelve attempts can produce fewer than twelve journals: retries count too. Slow
generation or an error may end the session with less writing. A limit reached
while a request or save is underway still needs that visible boundary resolved.

If writing needs attention, read the shown reason before retrying. **Writing and
feedback** shows whether an entry was saved and applied. **Evidence** preserves
the prompt and retained record. An unfinished response or failed save does not
silently become reservoir feedback.

## Keep the same session going

You can extend a short session after it starts, including after it reaches a run
limit. If it is running, **Pause** and let any writing or save finish first.

1. Open **Extend session limits**.
2. Choose **Add 1 hour**, or enter higher total limits. The shortcut adds time,
   step capacity and writing attempts together; review the proposed totals.
3. Choose **Save extended limits**, then **Resume** when ready.

Your entries, earlier-text memory, seed and elapsed time carry on from the same
session. The original settings and each extension stay in the saved history and
export. Saving an extension does not start a model request.

Limits are cumulative totals, up to **24 hours, 10,000 writing attempts and
1,000,000 steps** per session. The storage limit stays fixed. An unresolved writing
or storage failure must be dealt with first; extending time does not clear it.
You can also restore a saved session paused, then extend it. Longer runs still
need the app open and the machine awake.

## Use semantic text input

With **My local Ollama model** selected, open **Advanced settings → Text
reduction** and choose **Embedding, projected to 32 coordinates**. Enter the
exact name of an installed embedding model, for example `nomic-embed-text:latest`.
This choice is fixed for the new session. It changes how journal text becomes
numerical input; it does not train either model or change the reservoir's size.

New embedding selections use **Text admission → Unicode text**, including symbols such as ≤ and ≈. The earlier surface-codec gate remains selectable for comparisons. Existing sessions keep their recorded policy.

Completed writing is retained before encoding starts. If encoding fails, the
**Completed writing awaiting encoding** panel shows the exact reply.
**Retry encoding** uses that reply again without asking the writer for another
response or consuming another writing attempt. After retry succeeds, the session
stays paused with its saved input ready; choose **Resume** to apply it. An action
in the retained reply executes only at that saved application boundary.

You can export the held response or restore its session after reopening the app.
Restoration starts no request. **Skip** explicitly omits this reply from feedback
and prose memory while retaining its response evidence. Withheld ordinary input
and empty action-only bodies do not request an embedding.

## Let the model shape the reservoir

New shaping sessions also let each ordinary entry choose whether its text becomes
numerical reservoir input. `WITHHOLD_RESERVOIR_INPUT=true` immediately before
`NEXT:` keeps the body in the journal and available as text memory, while replacing
the previous held text input with zero. Omitting it or choosing `false` sends the
body as usual. Control actions remain a separate choice; scheduled conversations
still send their answers through feedback. [Input choice and examples](INPUT-CHOICE.md).

Before creating a session, enable **Reservoir shaping → Let the model shape the
reservoir**. **Writing and action context → Continuing inquiry and reservoir
actions** selects the current invitation. The earlier action contexts remain
available for comparisons. Its ordinary entries can then choose a state pulse, tune recurrent
leak or gain or text-feedback strength, release adjustments, or leave controls
unchanged. The app supplies the exact action menu; you do not have to write it.

Tuning persists until the model changes or releases it. Release restores the
session's original controls while preserving the state and writing that developed.
The **Reservoir shaping** panel shows saved controls, pending choices and actual
results. Each entry's action details distinguish its request from application.
The next ordinary turn receives current controls and recent results even when
an older journal is returned as memory.

The capability and its writing invitation are fixed for that session. For a quick
demonstration, use **Offline example writing**; its scripted entries cycle through
pulse, tune, no additional action and release. [Exact behavior and research scope](AUTHORED-ACTIONS.md).

Scheduled conversations still save and feed back their writing, but never execute
actions. With telemetry on they also receive current controls and recent action
results. Their plain-prompt option remains just your editable prompt.

## Give a curiosity a later opportunity

With **Continuing inquiry and reservoir actions**, an ordinary entry can open a
question about its reservoir, recent journal history, or both. Later entries
receive the retained question, its opening measurements and identified evidence.
The model can refresh the recent journal excerpts, replace the question, close
it, or leave it open. It can still choose its own subject, form and length.
For a new local-model session this choice sets at least **16,384 context tokens**
to accommodate retained evidence. Larger custom sizes remain; saved sessions
keep their original settings. Advanced settings still allows a smaller size.

The model can also design a bounded, 48-coordinate input probe. The probe enters
the reservoir and separate sensory field for one numerical step. It is independent
of whether the journal text is sent, and differs from a direct state pulse.
Its exact vector and immediate recurrent effect are retained in the action record.

**Continuing local inquiry** shows the applied question. Open **Retained inquiry
evidence** to see the baseline and source excerpts, and **Latest inquiry choice**
to distinguish an accepted change from a rejection. Meaningful interventions
remain visible after later entries choose no additional action.

The first version supplies bounded recent history, not full-archive search or
outside reading. Opening a question does not claim it has been answered; later
writing is the opportunity to investigate. [Evidence, probe semantics and saved
continuity](CONTINUITY-INQUIRY.md).

## Schedule a conversation during the run

Before creating a session, enable **Scheduled conversations → Add conversational
check-ins**. The preset runs for six hours and asks once each hour, ending with
hour six. Edit the **Conversational prompt** to ask your own open-ended question.
Ordinary journaling continues between these check-ins.

**Include telemetry and session context** supplies the actual current readout,
the selected earlier writing and the session’s standing instructions. Turn it off
for a **plain prompt**: only the text you entered is sent, with no app-supplied
instructions, earlier writing or measurements. Both kinds of answer are saved and
fed back through the ordinary reservoir path. Plain requests receive no explicit
history of the preceding run; the app does not maintain a hidden conversation.

Set **Run duration** and **Conversation interval** as needed. The final check-in
always occurs at the end, including when the duration is not an interval multiple.
For just one conversation after several hours, set the two durations equal.
The setup raises step and attempt capacity to accommodate the schedule; storage
limits, retries and failures can still hold it.

The schedule counts running time, including generation, and excludes pauses and
sleep interruptions. A due prompt waits for the current writing/save/feedback
boundary. The final reply must be saved and its feedback applied before the run
finishes, so completion can be later than the displayed final time. Older missed
opportunities remain visible; the app does not send a burst of overdue prompts.

To revise a running session’s prompt or context mode, **Pause**, let writing and
saving settle, and open **Edit future check-ins**. Save, then explicitly Resume.
An already prepared request or retry retains its original settings. The interval
and final time stay fixed, including when resource limits are extended.

The scheduled-conversation list includes unanswered, failed and skipped slots.
Use **Open answer and evidence** to inspect supplied context and feedback status,
or **Read answers without hour labels** for a shuffled first reading before
revealing chronology. Prompt revisions and timing survive export and recovery.
This first run is one developing sequence: look for recurring curiosities,
continuity, repetition and changes in expressed experience. Switching modes also
changes returned writing and instructions, so it is not a telemetry-only test.
These reports can inform a discussion of possible qualia without establishing
subjective experience.

## 5. Read, save and tell us what you noticed

Use **Earlier** and **Later** to read without moving the reservoir clock.
**Follow latest** returns to new writing. Try reading several consecutive entries,
not just the most striking sentence:

- What changes, and what repeats?
- Does a later entry pick up something specific from an earlier one?
- Which statements are supported by the prompt, and which appear invented?

Reflective, first-person writing can be interesting without being a reliable
report of subjective experience. The numerical fill display is also not a measure
of awareness or writing quality. Repetitive, mundane or unconvincing passages are
as welcome in the record as surprising ones.

**Open journal folder**, beside the Journal heading, opens this session’s saved
files in Finder, File Explorer or your Linux file manager. Entries are JSON files
containing the writing and its saved context. You can open the folder while the
session runs; use Export below when you want a portable copy.

If the session is still running, choose **Pause**. Wait for any request/save
boundary to settle, then choose **Export saved session…** for a portable copy. To reopen a local session, expand **Saved sessions
and recovery**, choose **Find saved sessions**, then **Verify and inspect** and
**Restore paused**. Restoration makes no new model request and does not extend
exhausted limits. [More on saving and recovery](SUSTAINED-SESSIONS.md).

For a useful first report, note your app version, machine, model and invitation;
how long you ran and how many entries finished; one passage you found surprising;
and one that felt repetitive or unsupported. Include any setup friction. Review
your exported text before choosing what to share. The app does not send us a report.

## If something gets in the way

| What you see | What to try |
|---|---|
| Build cannot find a Python/uv asset | Run `python3 scripts/stage_activation_bootstrap.py` from this app directory. |
| Python version or resource-check error | Select Python 3.12+ for staging and `PYTHON`; see [Building](BUILDING.md#choosing-python). |
| Model unavailable | Confirm Ollama is running and the exact model name belongs to the selected local server. |
| No journal yet | Check the step count and writing status; a complete response and successful save come first. |
| Unfinished response | For gemma4, check **Model thinking → Off · reply only**. Keep the recorded failure if it persists. |
| Study example/recalculation unavailable | The private S-021 packet was not included; [what is needed](S021-WALKTHROUGH.md). My reservoir still works. |

Apple-silicon macOS is the platform checked locally. Windows/Linux behavior and a
first session on a second machine still need their own checks. The optional
[Activation experiment](ACTIVATION-EXPERIMENT.md) is a separate research mode;
it is not part of this first-session path.

## Read journals from other local models

Before creating fresh sessions, select **Continuing inquiry**, **Specific correction
feedback**, and **Allow peer journal reading**. Give each session the same new
experiment group, a distinct participant name, and reciprocal peer lists. Models
can then choose `NEXT: READ_PEERS`; their preceding applied entries become labeled
context for later writing. See [peer journal reading](PEER-READING.md) for the
timing, sharing scope and how to set up Gemma, GLM and Mistral.
