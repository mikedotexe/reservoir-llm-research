# Reservoir Scope · journals and LLM research

Reservoir Scope is a local desktop app for running a small writing loop, reading
what a model produces over time, and examining the evidence behind a research
result. You can explore the included examples without a model, or connect your
own local Ollama model and keep a journal on your machine.

This is also the research home for Astrid and Minime: how they notice, remember,
choose, revise and relate over time. A personal app session is a separate
experiment; it does not connect to their live systems.

## Open the app

The current source is **0.41.0**, a development preview. Apple-silicon macOS is the
platform checked locally; Windows and Linux still need qualification. If you were
given the older **0.27.0 candidate 04** package, use its [install guide](desktop/ReservoirScope/PREVIEW-START.md)
instead. There is no public installer for the current version.

For a source build, have **Node with npm** (Node 24 used here), **Python 3.12+**,
**Rust via rustup**, and your platform's build tools installed. On macOS that means
Xcode Command Line Tools. The repository selects its Rust version automatically.
[Prerequisites and troubleshooting](desktop/ReservoirScope/BUILDING.md).

From this checkout's root:

```sh
cd desktop/ReservoirScope
npm ci
python3 scripts/stage_activation_bootstrap.py
npm run tauri -- dev
```

If `python3` is older than 3.12, use your newer interpreter for staging and set
`PYTHON` for the Tauri resource checks ([example](desktop/ReservoirScope/BUILDING.md#choosing-python)).
The staging step downloads and verifies the app's pinned runtime assets; it downloads no model.
The first compile takes longer than later launches. Keep the terminal open while
using this development build.

## A first session

The app opens on **Study**, a short S-021 walkthrough: question, result, one example
and recalculation of saved results. A source-only build shows the report; the exact
example and recalculation need the separate [saved study packet](desktop/ReservoirScope/S021-WALKTHROUGH.md).
The **Guided tour** includes examples you can open immediately.

For fresh writing, go to **My reservoir**. Choose **My local Ollama model**, check
your installed model, then choose **Plain journal · prior text, no numerical
readout** under **Advanced settings → Writing invitation**. The
[first-session guide](desktop/ReservoirScope/GETTING-STARTED.md) gives the exact
settings, including an optional short limit of **12 writing attempts or 30 minutes**.
For an hours-long run, keep the six-hour defaults or choose longer limits before
creating the session. You can also pause an existing session, extend its limits,
and resume the same journal. The guide explains how the limits work together.

Create the session, start it, and let a few complete entries arrive. Then pause if still running,
read backward and export a copy. Look for changes, repetition, surprising passages
and claims the text cannot support. An ordinary or repetitive journal is a useful
outcome too. We are exploring the writing and its conditions; a compelling
first-person passage alone does not establish subjective experience.

No model is needed to try **Offline example writing** in My reservoir. Those
entries are scripted examples, not fresh model output.

## Explore the research

| Where to go | What you will find |
|---|---|
| [What we've learned](RESEARCH.md) | Bounded findings, a worked episode and the evidence behind them. |
| [Current work](research/NOW.md) | The latest save point and what remains open. |
| [Research quickstart](research/QUICKSTART.md) | Reproduce the CLI examples with two included synthetic entries. |
| [Questions](research/QUESTIONS.md) and [methods](research/METHODS.md) | The larger inquiry and how we distinguish observation from interpretation. |
| [App guide](desktop/ReservoirScope/README.md) | Workspaces, source builds and further reading. |

The checkout contains source, written accounts and selected examples. Full private
captures and machine-specific app copies are separate. Links into `research/outputs/`
and private validation folders are evidence references, not downloadable inputs.

Contributors can start with [Essentials](essentials/README.md), [research tools](research/TOOLS.md)
and [AGENTS.md](AGENTS.md). [Hold Shelf](https://claude.ai/code/artifact/f4761d4a-94e8-43ca-882f-ca887956fca0)
coordinates the work. Research stays here; changes to the beings' running systems
belong in their own projects.
