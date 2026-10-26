# Your first journal session

The aim is simple: open Reservoir Scope, let a local model write a short sequence,
then read it with some curiosity. You do not need to understand the reservoir's
math to begin. Plan for **up to 30 minutes of running time**, after installation
and model setup, plus a few minutes to read.

These instructions describe **0.41.0 source**. If you received the older 0.27.0
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
