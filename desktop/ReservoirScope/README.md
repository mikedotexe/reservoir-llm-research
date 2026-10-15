# Reservoir Scope Tauri Preview

**0.20.0 · `reservoir-journal-v8` · Local preview**

Reservoir Scope combines a personal reservoir and journal with offline experiments,
recordings and evidence readers. The native macOS app remains separate at
[native/ReservoirScope](../../native/ReservoirScope/README.md), with its existing
0.15.0 build 21 identity. This preview uses `research.reservoir.scope.tauri` and its
own storage. Opening a workspace starts no experiment, model connection or live feed.

[Current status and next work](STATUS.md) ·
[Capability/platform matrix](../../shared/reservoir-scope/PARITY.md) ·
[Accepted roadmap](../../TAURI-ROADMAP.md)

## Implementation status

The personal writing loop is implemented and has bounded real-model evidence:
twelve complete v8 journals were saved and applied at the next step, with eleven
exact prior-text memory joins, followed by native export and explicit paused recovery.
This demonstrates the recorded mechanics, not reliable prose claims or scientific
benefit. The wider Observatory, cross-platform delivery, current-build endurance,
measured GPU behavior and collaborator acceptance remain incomplete.

The [0.20 source/package/native account](validation/2026-10-14-reading-measurements-0.20.0/README.md)
and [separate real v8 episode](validation/2026-10-14-v8-writing-episode01/README.md)
identify executed checks and limits. Historical evidence belongs to its exact build.
The two-hour synthetic run belongs to 0.12.0. Windows/Ubuntu's initial CI failure and
unqualified test-only correction are retained separately; they are not successful
platform acceptance.

Production v8 remains unchanged. The first standalone source-role diagnostic
[refused the changed runtime before launch](validation/2026-10-15-context-sources-01/README.md).
Separate 0.40.5 source/identity review and synthetic helper checks now pass, but the
[new comparison window](validation/2026-10-15-context-sources-02/README.md) refused
its one memory admission at 31% free against the unchanged 35% minimum. All twelve
slots remain unstarted, with no service or provider request. Actual 0.40.5 execution
and candidate writing effects remain unassessed; no automatic retry is queued.

## Use the preview

| Workspace | Available workflow | Details |
| --- | --- | --- |
| Experiments → My reservoir | Explicitly create/start a bounded scripted or local-model session; watch recurrent state and separate sensory fill; read complete journals independently of the live cursor; export and restore paused | [Sustained sessions](SUSTAINED-SESSIONS.md) |
| Experiments → Fresh experiments | Explore, stages 1–4, standalone A–H, matched B–H and D/D observation pairs, plus a separate fixed field-only controller study | [Fresh experiments](FRESH-EXPERIMENTS.md) |
| Experiments → Recording reader / Library | Verify recorded experiments, inspect exact prompt/save/application evidence, import immutable bytes, search/filter metadata, export originals and recover the index | [Library](LIBRARY.md), [guided evidence](GUIDED-EVIDENCE.md) |
| Observatory | Independent clocked fill and ordinal state recordings; response evidence, preparation histories and exact exports | [Recorded fill](RECORDED-FILL-SPHERE.md), [responses](RESPONSE-EVIDENCE.md) |
| Guided tour / Research cases / Geometry | Authored A–H questions and limits, reviewed evidence, checked catalog derivatives and 128-coordinate geometry packets | [Cases](crates/reservoir-core/CASES.md), [geometry](GEOMETRY.md) |

### My reservoir and sustained journals

Choose the source explicitly. Scripted replies are synthetic; a local model requires
an endpoint and exact model. Readiness is an explicit availability check, not proof
of context capacity or prose quality. Create prepares local state; Start permits the
bounded run. Pace, step/attempt/duration/storage limits remain visible, and the first
reached bound holds the run. Storage reserves room for safe saving and stopping.
There is currently no budget-extension control.

Saved-and-checked writing contributes numerical input at its recorded next-step
application boundary. Only actually applied writing becomes later full-text memory.
Saving, applying, skipping and failure are distinct. A description of a control
change in prose does not execute it. The full retained observation and exact prompt
remain in closed Evidence; the v8 prompt supplies a compact measurement subset.

Earlier/Later selects adjacent entries; Pause following pins the reading while new
journals arrive. Evidence and measurements begin closed. The app never strips
model-authored telemetry or rewrites the journal. Retry and skip remain explicit;
recovery restores verified state paused and never resends a request automatically.

### Fresh experiments and journal saves

Finite experiments retain their own controlled recipes and save gates. A WRITE
candidate waits for explicit durable save; publication and readback precede eligible
feedback. Pending pairs retain per-arm identity and partial outcomes. Fixed tapes,
local responses, WAIT/WRITE and controller evidence stay distinguishable. The separate
600-step controller study contains sensory fields, not a reservoir or language loop.

### Explicit local-model connections

See [local-model configuration and boundaries](LOCAL-MODELS.md). No service is launched
or contacted by opening a workspace. Optional provider-reported input counts are
retained evidence, not proof that the model processed or understood the entire prompt.
Selected read-only feeds are a separate future workflow.

### First offline Observatory recordings

Fill history has 507 clocked samples; state replay has 1,024 ordinal rows × 128
coordinates. They are independent recordings, not synchronized signals. The fill
sphere and signed surface preserve their distinct quantities and exact-value fallback.
Remaining trajectory/topography/spectrum workflows and visual acceptance are tracked
in the [parity matrix](../../shared/reservoir-scope/PARITY.md#capability-matrix).

### Recorded visual and writing experience

Playback navigates retained frames; selection exposes exact values and available
turn evidence. Invalid replacement and stale responses preserve the accepted reading.
Rendering uses bounded pixels, event-driven updates and hidden suspension. Those are
implemented bounds, not measured GPU, battery or all-platform performance claims.

### Guide, Library, cases and geometry

Reviewed interpretations, source identities, clocks and missing values remain explicit.
Opening is temporary reading. Experiment import or Save to Library creates a managed
copy; cases and geometry do not silently enter the Library. Historical source paths
are inert text. No native Library or live Being workspace is automatically scanned.

## Build prerequisites

Use Node **20.20.1**, npm, Python **3.12 or newer**, and Rust **1.94.1** (pinned by
[rust-toolchain.toml](rust-toolchain.toml)). Platform prerequisites come from the
[Tauri v2 guide](https://v2.tauri.app/start/prerequisites/):

| Target | Development requirements | Configured bundle |
| --- | --- | --- |
| macOS 14+, Apple silicon | Xcode Command Line Tools or Xcode, working macOS SDK | `.app` |
| Windows, x86-64 | MSVC C++ Build Tools with Desktop development with C++, WebView2 runtime | NSIS setup executable |
| Ubuntu 24.04, x86-64 | WebKitGTK 4.1 and GTK development dependencies | `.deb` |

The OS rows identify initial qualification targets, not completed support claims.
Windows and Linux packaged qualification has **not been executed locally**. This
repository's workflow is configured to build those targets; a checked-in workflow
is not evidence that its jobs passed. A build result alone does not establish usable
graphics, working native dialogs, accessibility or package installation.

On Ubuntu, install the build dependencies documented by Tauri:

```sh
sudo apt-get update
sudo apt-get install -y libwebkit2gtk-4.1-dev build-essential curl wget file libxdo-dev libssl-dev librsvg2-dev libayatana-appindicator3-dev
```

On macOS, ensure `xcrun --show-sdk-path` resolves to an existing SDK. If multiple Xcode
installations are present, select a valid SDK for the build process; do not alter the
native application's identity or installation to build this preview.

## Run and build

From the repository root, verify the immutable native reference first:

```sh
python3 desktop/ReservoirScope/scripts/check_reference.py
python3 -m unittest discover -s desktop/ReservoirScope/scripts -p 'test_*.py'
```

On Windows, use `python` instead of `python3` if that is the installed Python 3.12+
command. The npm resource-preparation wrapper selects the platform's Python command.
All other commands below work in a standard terminal without zsh-specific scripts.

Then enter the desktop directory:

```sh
cd desktop/ReservoirScope
npm ci
npm test
npm run build
npm run prepare:resources
cargo test --locked --package reservoir-core
cargo test --locked --package reservoir-scope-desktop
npm run tauri -- dev
```

`npm run tauri -- dev` runs the native Tauri shell. `npm run dev` alone only serves
frontend assets; it does not provide the Rust commands or establish desktop parity.
Both Tauri development and package builds verify and stage reference resources before
starting. Staging copies only checked canonical inputs into generated
`src-tauri/resources/`; it never regenerates recordings or edits native originals.
Prepare resources before compiling either Rust package's tests directly: the core
case tests also embed a staged resource at compile time. Test the two
Rust packages in separate invocations: workspace feature unification must not hide
a dependency feature missing from either package.
See [the shared reference](../../shared/reservoir-scope/README.md) for source and hash
provenance.

Build a local package using the command for your host:

```sh
# macOS Apple silicon
npm run tauri -- build --target aarch64-apple-darwin --bundles app -- --locked
# Windows x86-64
npm run tauri -- build --target x86_64-pc-windows-msvc --bundles nsis -- --locked
# Ubuntu x86-64
npm run tauri -- build --target x86_64-unknown-linux-gnu --bundles deb -- --locked
```

Packages land under this directory's `target/<target>/release/bundle/`. These are
local/CI previews, not signed public releases. macOS builds use ad-hoc signing; they
are not notarized. Windows installer signing and public-distribution acceptance are
not implemented. No command publishes a release or touches the beings' live systems.

## What to verify in the packaged app

Record the exact package, OS, architecture and display/runtime identities. Exercise
create/run/pause/read/export/recover; native dialogs and invalid replacements;
keyboard/focus/screen-reader behavior; resize, scaling, hidden rendering and graphics
recovery; clean quit/relaunch, interruption and denied/full storage. Keep model
readiness and actual requests explicit. A browser fixture is not a native WebView
check, and passing tests are not collaborator acceptance.

Use the accepted [qualification gates](../../TAURI-ROADMAP.md#5-validation-release-practice-and-program-management)
and dated [validation accounts](validation/). The longer historical checklist is
preserved in the [prior README](README-HISTORY-2026-10-15.md#what-to-verify-in-the-packaged-app).

## CI and evidence boundaries

The [workflow](../../.github/workflows/tauri.yml) configures macOS, Windows and Ubuntu
checks and native bundles. Artifact/build success and clean-host installation,
graphics, accessibility and human acceptance are separate gates. See the
[current platform rows](../../shared/reservoir-scope/PARITY.md#platform-acceptance).
No command here publishes a release or authorizes access to a Being's live system.

## Capture a local qualification receipt

After source edits and a build finish, use
[scripts/qualification_receipt.py](scripts/qualification_receipt.py) with an explicit
package and a new output path. The [preserved invocation and field guidance](README-HISTORY-2026-10-15.md#capture-a-local-qualification-receipt)
explain source/package identity, caller-supplied checks and limitations. Capture does
not rebuild, confer test success, or establish public signing/notarization.

This documentation consolidation changes no product source, prompt, package or old
receipt. Newer local work is pending a source checkpoint; the
[earlier publication account](validation/2026-10-13-public-checkpoint/README.md) remains
historical. The full pre-edit README is preserved byte-for-byte in
[README-HISTORY-2026-10-15.md](README-HISTORY-2026-10-15.md).
