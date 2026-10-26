# Building and checking Reservoir Scope

For the first-run experience, use [Your first journal session](GETTING-STARTED.md).
This page collects the setup and contributor details.

## Prerequisites

- **Node.js with npm:** package requirement is Node 20.19+; local checks use Node 24.
  CI currently pins 20.20.1. Use `npm ci` to install the lockfile's dependencies.
- **Python 3.12+:** used for build-time resource checks and bootstrap staging.
- **Rust through rustup:** [rust-toolchain.toml](rust-toolchain.toml) selects 1.94.1.
- **Platform tools:** Xcode Command Line Tools on macOS; MSVC C++ Build Tools and
  WebView2 on Windows; WebKitGTK/GTK development packages on Linux.
  Follow [Tauri's current prerequisite guide](https://v2.tauri.app/start/prerequisites/).

Apple-silicon macOS is the locally checked platform. The other build targets are
not claims of completed installation or first-user qualification.

### Choosing Python

Check `python3 --version`. If it is older than 3.12, use your newer interpreter for
staging and set `PYTHON` so the npm resource wrapper uses the same interpreter.
For example, on a Mac where Python 3.14 is installed at this path:

```sh
export PYTHON=/opt/homebrew/bin/python3.14
"$PYTHON" scripts/stage_activation_bootstrap.py
npm run tauri -- dev
```

Run these from `desktop/ReservoirScope` after `npm ci`. Substitute your actual
interpreter path. In PowerShell, set `$env:PYTHON` to that path and invoke it with
`& $env:PYTHON scripts/stage_activation_bootstrap.py`. On Windows, `python` may
already be the Python 3.12+ command.

## Open the native app

From the repository root:

```sh
cd desktop/ReservoirScope
npm ci
python3 scripts/stage_activation_bootstrap.py
npm run tauri -- dev
```

The staging helper downloads and hash-checks the pinned CPython and uv assets
listed in the activation setup manifest. Matching existing assets are reused.
The app bundle requires these resources even if you only plan to use Ollama.
Staging does not download a model or start the optional activation worker.

Tauri prepares the included reference resources, starts the frontend and compiles
the native shell. Keep the terminal open. `npm run dev` alone serves the frontend
without the native commands needed to create and save sessions.
[Tauri development reference](https://v2.tauri.app/develop/).

The optional activation runtime includes its own Python. Ordinary packaged Ollama
sessions do not require the user to install Python. Build-time Python and the
optional runtime are separate.

## Build a local package

After the setup steps above, run the command for the host you are building on:

```sh
# macOS Apple silicon
npm run tauri -- build --target aarch64-apple-darwin --bundles app -- --locked
# Windows x86-64
npm run tauri -- build --target x86_64-pc-windows-msvc --bundles nsis -- --locked
# Linux x86-64
npm run tauri -- build --target x86_64-unknown-linux-gnu --bundles deb -- --locked
```

Packages appear under `target/<target>/release/bundle/` in this app directory.
These are local builds. macOS uses ad-hoc signing, without notarization; Windows
public installer signing is not implemented. A successful build is not evidence
of clean-machine installation or collaborator acceptance.

## Contributor checks

From the repository root, with Python 3.12+:

```sh
python3 desktop/ReservoirScope/scripts/check_reference.py
python3 -m unittest discover -s desktop/ReservoirScope/scripts -p 'test_*.py'
cd desktop/ReservoirScope
npm test
npm run build
npm run prepare:resources
cargo test --locked --package reservoir-core
cargo test --locked --package reservoir-scope-desktop
```

Prepare resources before compiling either Rust package directly. Keep the two
Rust package test invocations separate so workspace feature unification does not
hide a missing dependency feature. Reference preparation copies checked canonical
inputs into generated `src-tauri/resources/`; it does not regenerate recordings
or edit native originals. [Reference provenance](../../shared/reservoir-scope/README.md).

Private captures are not needed for the included examples or My reservoir.
The S-021 exact example and recalculation have a separate
[packet-staging step](S021-WALKTHROUGH.md). Its real-data test skips explicitly
when that packet is absent; synthetic tests still run.

For package qualification and receipts, use [current status](STATUS.md),
[platform acceptance](../../shared/reservoir-scope/PARITY.md#platform-acceptance),
the [roadmap's checks](../../TAURI-ROADMAP.md#5-validation-release-practice-and-program-management)
and the [preserved receipt instructions](README-HISTORY-2026-10-15.md#capture-a-local-qualification-receipt).
