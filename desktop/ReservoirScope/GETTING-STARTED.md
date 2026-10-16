# Start your reservoir journal

Build the desktop app, select an installed local model, and watch its saved writing
return as input to a reservoir. Journal prose leads the running view; current
sensory fill and the reservoir surface remain available alongside it.

This preview currently connects to **Ollama's local API**. An arbitrary model file
or a different provider's server is not a supported endpoint. The offline example
lets you try the same save-and-feedback workflow without a model.

## 1. Build and open the app

Install Node **20.20.1** with npm, Python **3.12+**, and Rust through rustup. The
repository selects Rust **1.94.1** through its toolchain file. Install the system
build tools for your host: Xcode Command Line Tools on macOS, MSVC C++ Build Tools
and WebView2 on Windows, or the WebKitGTK/GTK development packages on Ubuntu.
[Tauri's prerequisite guide](https://v2.tauri.app/start/prerequisites/) and our
[host-specific build instructions](README.md#build-prerequisites) give the details.

From this repository's root:

```sh
cd desktop/ReservoirScope
npm ci
npm run tauri -- dev
```

The last command prepares the included resources, compiles the Rust application
and opens **Reservoir Scope Tauri Preview**. The first compile takes longer than
later launches. Keep its terminal running during development; quitting the app ends
its session. `npm run dev` alone serves only the frontend and cannot run a reservoir.

You do not need the private research captures, Python research index, or another
Reservoir Scope installation. Python is used for build-time resource checks; it is
not a bundled runtime. The preview has its own writable storage.

The currently inspected desktop platform is Apple-silicon macOS. Windows and Ubuntu
builds and packaged behavior still need qualification; prerequisites alone are not
a support claim. To run without a development terminal, build the
[package for your host](README.md#run-and-build).

## 2. Choose your installed model

Start your own Ollama service if it is not already running. To see the installed
model names, run:

```sh
ollama list
```

Use the exact name, including its tag, from the service you intend to use. For
example, enter `gemma3:4b` only if that name is installed there. A typical local
server address is `http://127.0.0.1:11434`; use your service's actual port.
For a custom service address, query that service's model list rather than assuming
the CLI's default inventory is the same. [Ollama CLI](https://docs.ollama.com/cli)
and [model inventory API](https://docs.ollama.com/api/tags).

In **My reservoir**:

1. Choose **My local Ollama model** under Writing source.
2. Enter the local server address and exact model name.
3. Select **Check local model**. This checks the selected service's inventory;
   it generates no journal. A successful check does not guarantee sufficient memory
   or a complete response.
4. Select **Create my reservoir**, then **Start** when ready.

The app starts no service, installs no model and makes no automatic connection when
you open it. Supported server addresses use HTTP and an explicit loopback port.
They contain no credentials, API path or query. Other providers are a future feature.

To try the interface first, leave **Offline example writing** selected and choose
Create, then Start. Those entries are a deterministic script, clearly identified
as example writing; they are not fresh LLM output.

## 3. Watch the writing loop

Feedback is included in My reservoir; there is no additional enable switch:

**Reservoir observation → model writing → durable save and readback → encoded input
at the next numerical step → later observation and eligible prior prose.**

The model's topic and form remain open. Encoding is deterministic numerical input,
not model training. A sentence describing an action does not execute a control.

By default, a writing opportunity occurs every 30 numerical steps at a requested
pace of one step per second. Generation and saving hold numerical time, so an entry
is not promised every 30 wall-clock seconds. The first complete journal appears
after the first writing opportunity finishes and its save is checked. Responses
arrive as complete entries; the app does not stream partial prose into the journal.

The journal initially follows the newest saved entry. Earlier/Later lets you read
without moving the reservoir clock. Selecting an older entry pins it; **Follow
latest** returns to incoming writing. Current fill stays tied to the current
observation, while a selected entry's Recorded measurements describe that entry.

If writing or saving needs attention, the app retains the outcome and shows the
available retry, skip or recovery action. An incomplete response or failed save
cannot silently become reservoir feedback. Check **Writing and feedback** for the
boundary; Evidence preserves the exact prompt and retained record.

The session can continue while the app is open or minimized. Its first duration,
step, attempt or storage limit holds it. The initial limits are 6 hours, 10,800
steps, 360 writing attempts and 256 MiB; these are ceilings, not a six-hour runtime
guarantee. Advanced settings changes the next session's limits. There is no current
budget-extension control, and quitting or computer sleep is not background execution.

## 4. Read fill alongside the journal

**Sensory fill (%)** is a smoothed estimate of active modes in a separate sensory
covariance field. It is not memory usage or the proportion of occupied reservoir
nodes. The state surface shows a different quantity: signed reservoir coordinates.

With sensory regulation enabled, this implementation uses a **68% target** and a
**64–72% deadband**. Those are controller settings, not a demonstrated special state
at 67–70%, a writing-quality score, or a guarantee that a run will reach the target.
The personal field and historical Minime recordings have different mechanisms and
reference policies. Their percentages must not be treated as interchangeable.

The percentage is fill level. A *fill rate* would be change per unit of time; the
personal readout does not claim to measure that rate. The selected entry's optional
measurements help inspect what was actually observed when its prompt was prepared.
The implementation is in [ReducedFill and RetentionController](crates/reservoir-core/src/math.rs)
and the [sustained numerical step](crates/reservoir-core/src/sustained.rs).

## Save a copy and return later

Use Pause, then **Export saved session…** for a portable snapshot. Saved sessions
and recovery can find a local session, verify its retained history and **Restore
paused**. Restoration starts no request and never silently extends exhausted limits.

If the app is waiting for a request or save, review the visible boundary first.
Quitting offers the existing checkpoint/return/discard flow when work is unresolved.
See [sustained-session behavior](SUSTAINED-SESSIONS.md) for exact recovery boundaries.

Build/test records and the remaining platform, endurance, graphics and collaborator
checks live in [Current status](STATUS.md). They are separate from this first-use
walkthrough; your chosen model and machine still need their own practical check.
