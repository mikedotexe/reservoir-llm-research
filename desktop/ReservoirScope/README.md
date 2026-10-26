# Reservoir Scope

A desktop app for reading model writing, running a personal reservoir journal,
and exploring reproducible research examples. Opening it starts no model request.
You choose when a new session begins.

**Current source: 0.41.0 development preview.** The current app has been checked
locally on Apple-silicon macOS. A second-machine first session is still needed.
Windows and Linux remain qualification targets.

## Start your journal

Follow [Your first journal session](GETTING-STARTED.md) to open the app, choose a
local model, let it write for a short bounded session, then read and export.
The short first-session limits are optional; you can keep the six-hour defaults
or set your own duration, step and attempt limits before creating a session.
You can also pause, open **Extend session limits**, add time and resume the same journal.
It includes a **Plain journal** invitation that returns prior writing without a
numerical readout. The existing **Current readout** invitation remains the default.

Already have the [build prerequisites](BUILDING.md#prerequisites)? From the
repository root:

```sh
cd desktop/ReservoirScope
npm ci
python3 scripts/stage_activation_bootstrap.py
npm run tauri -- dev
```

Use Python 3.12+ for both staging and the build's resource checks. Staging downloads
the pinned runtime assets required by the app bundle, but no model. The first
compile may take a while. Keep the terminal running during development.

The app opens on **Study**. Select **My reservoir** for your journal, or **Guided
tour** to explore without a model. Offline example writing is also available in
My reservoir; its entries are scripted and labelled as such.

## What is in the app?

| Workspace | Start here when you want to… |
|---|---|
| **Study** | Understand S-021 through its question, result, a paired example and saved-result recalculation. |
| **My reservoir** | Create a local journal, follow entries, export or restore; optionally explore activation. |
| **Guided tour** | Get oriented with included examples. |
| **Experiments** | Open recordings and compare or prepare experiments. |
| **Research cases** | Follow reviewed cases into their evidence. |
| **Geometry bookmarks** | Inspect saved views of the numerical state. |
| **Observatory** | Explore recordings and preparation history. |

The S-021 exact example and recalculation require a separate private data packet;
a fresh source checkout still shows the report and explains what is unavailable.
[Walkthrough and reproduction](S021-WALKTHROUGH.md). The other included examples
need no private captures.

## What to expect

Journal responses arrive as complete, saved entries. You can read Earlier/Later,
return to Follow latest, or pause and export. Model speed varies; the duration and
attempt settings are ceilings, not a promise of a certain number of journals.

The invitation matters. **Current readout** supplies numerical observations;
**Plain journal** supplies a standing writing contract and, when available, a
selected earlier entry. In plain mode the reservoir still runs, but its readout
is not sent to the model. Both are useful conditions to examine. Neither turns
the model's descriptions into a verified account of an inner experience.

The app uses its own local storage and supports a local Ollama service for ordinary
journals. No API key is needed for that path. The separate
[Activation experiment](ACTIVATION-EXPERIMENT.md) has its own runtime and setup;
you do not need it for a first Ollama journal.

## Build prerequisites

See [Building and checking the app](BUILDING.md) for Node, Python, Rust and platform
requirements, including how to select a newer Python.

## Run and build

Use the four commands above for development. [Building and checking](BUILDING.md#build-a-local-package)
also explains standalone app bundles and contributor checks. `npm run dev` alone
opens only the browser frontend; use the Tauri command for the full app.

## Research and release records

- [Research overview](../../RESEARCH.md) and [current work](../../research/NOW.md).
- [Current app status](STATUS.md) and [0.41.0 change record](RELEASE-0.41.0.md).
- [Current candidates](../../research/CURRENT-RELEASE.md): the older **0.27.0 candidate 04**
  is the private sharing candidate; **0.39.0** remains the frozen S-011 instrument.
- [Install guide for 0.27.0 candidate 04](PREVIEW-START.md), if you received that package.
- [Sustained sessions](SUSTAINED-SESSIONS.md) for exact save and recovery behavior.
- [Platform acceptance](../../shared/reservoir-scope/PARITY.md#platform-acceptance)
  and [roadmap](../../TAURI-ROADMAP.md) for the remaining qualification work.

The [previous README](README-HISTORY-2026-10-25.md) preserves the full release
history and earlier validation accounts. This preview does not replace those
packages or the separate [native macOS app](../../native/ReservoirScope/README.md).
