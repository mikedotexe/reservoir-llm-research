# Reservoir Scope Tauri Preview

**0.27.0 candidate 04 · Ready for a first invited tester · Human acceptance pending**
**0.31.0 source · two more S-010 contract arms ([record](RELEASE-0.31.0.md)), on 0.30.0 embedding text reduction and S-010 frame arms ([record](RELEASE-0.30.0.md)), 0.29.0 writing temperature ([record](RELEASE-0.29.0.md)) and 0.28.0 field noise and feedback scale ([record](RELEASE-0.28.0.md)); unqualified local candidates**

Reservoir Scope combines a personal reservoir and journal with offline experiments,
recordings and evidence readers. The native macOS app remains separate at
[native/ReservoirScope](../../native/ReservoirScope/README.md), with its existing
0.15.0 build 21 identity. This preview uses `research.reservoir.scope.tauri` and its
own storage. Opening a workspace starts no experiment, model connection or live feed.

[Current status and next work](STATUS.md) ·
[Capability/platform matrix](../../shared/reservoir-scope/PARITY.md) ·
[Accepted roadmap](../../TAURI-ROADMAP.md)

For the private Mac preview, begin with [Install and first reading](PREVIEW-START.md).
The [0.27 release record](RELEASE-0.27.0.md) identifies candidate 04 and its exact
archive. Source checks, fourteen standalone runtime checks, fresh setup and the
bounded writing path have retained evidence. The repaired package completed two
exports/imports and normal quit/reopen, preserving all 104 original payload files
and paused review without model work.

The exact quarantined transfer opened through macOS's app-specific exception and
completed standalone Prepare, Check and normal quit/reopen. Named activation setup,
reading and recovery screens passed at measured 900×700 and 720×600 content sizes,
including scoped keyboard and enlarged-text checks. Read the bundled historical
writing offline, then explicitly prepare the runtime for new writing.
The [newcomer task card](NEWCOMER-TASK-CARD.md) is still awaiting a human session.
An optional new synthetic arrival-navigation check was refused at memory admission;
that packaged behavior remains unobserved, with source-test coverage retained.
Minimum-OS, second-Mac, broad accessibility and endurance qualification remain open.

The optional [Activation experiment](ACTIVATION-EXPERIMENT.md) connects quiet Qwen3
prefills to a persistent 32-unit state and a fixed residual intervention during
journal writing. It has a separate session format, worker, calibration and reader.
The [computational contract](../../shared/reservoir-scope/activation-experiment.md)
defines the three conditions and bounded exploratory pilot. Actual qualification
for 0.26 is recorded in its [dated account](validation/2026-10-15-activation-0.26.0/README.md).
The [October 16 headroom work](validation/2026-10-16-activation-headroom/README.md)
qualified a bounded worker/CLI path; it does not qualify the new package. The
historical examples contain six trace journals and a separate unsteered prefix
with an unfinished response, not a completed three-condition comparison.
Historical Ollama sessions continue to use their recorded prompt contracts.

<a id="start-your-journal"></a>

## Build from source and start an Ollama journal

With the [build prerequisites](#build-prerequisites) installed, run from the repository root:

```sh
cd desktop/ReservoirScope
npm ci
npm run tauri -- dev
```

In **My reservoir**, choose **My local Ollama model**, enter your server address and
exact installed model name, and check availability. **Create my reservoir**, then
**Start**. Saved and verified writing becomes eligible for numerical input at the
next step; Pause can hold that boundary. Follow the journal as it arrives, alongside
current sensory fill.

[Build-to-first-journal walkthrough](GETTING-STARTED.md) covers prerequisites,
model selection, first-entry timing, fill interpretation, export and paused recovery.
Offline example writing remains available without a model. The [0.25 journal-first
tranche](validation/2026-10-15-journal-first-0.25.0/README.md) passes 431 frontend
tests, the production build and a distinct macOS package check. A native walkthrough
confirms setup, prominent prose/current fill, Earlier/Later and enlarged text; three
scripted journals save and apply at the next step before a natural step-91 hold.
Post-quit replay preserves all 19 files. Rust qualification is reused from exact
0.24 inputs with application-version metadata changes only; it was not rerun.

## Implementation status

The personal writing loop is implemented and has bounded real-model evidence:
twelve complete v8 journals were saved and applied at the next step, with eleven
exact prior-text memory joins, followed by native export and explicit paused recovery.
This demonstrates the recorded mechanics, not reliable prose claims or scientific
benefit. The wider Observatory, cross-platform delivery, current-build endurance,
measured GPU behavior and collaborator acceptance remain incomplete.

The [0.24 compact-reading tranche](validation/2026-10-15-compact-reading-0.24.0/README.md)
keeps selected journal positions stable across history windows and new arrivals.
Refresh and Older/Newer preserve an accepted entry anchor; stale or failed reads
retain the current prose. Earlier/Later work even when the selected entry is outside
the list window. Evidence can be focused and scrolled by keyboard; View adds zoom
and Actual Size. All 427 frontend tests in 46 files, 224 core and 203 desktop tests,
TypeScript/Vite, reference checks and both strict Clippy checks pass; two opt-in
desktop tests remain ignored. The distinct 46-file macOS package is archived and
ad hoc signed. The [native walkthrough](validation/2026-10-15-compact-reading-0.24.0/MACOS-UI.md)
confirms zoom/reset, Library details, skip-link focus and evidence-panel scrolling.
A scripted session creates 36 journals and naturally holds at live/saved step 361.
Pinning/refresh, Older/Newer, crossing the twenty-entry boundary, Earlier from an
outside-window selection, workspace return and explicit Follow latest all pass
while entries arrive. Normal quit leaves owned PID 9390 absent. Actual geometry
is 1830 × 1050 with 100%/125%/200% zoom; unsuccessful resize attempts leave
900 × 700 and 720 × 600 unqualified. The corrected
[post-quit replay](validation/2026-10-15-compact-reading-0.24.0/ui-session-check-02.json)
passes all 36 journals, preserving all 217 files unchanged with no recorded provider
dispatch. The earlier wrapper refusal is retained separately; no application rerun
occurred. Native export/recovery were not rerun. Production v8, numerical and
saved-record behavior are unchanged.

A [fresh native retry](validation/2026-10-15-compact-reading-0.24.0/MACOS-COMPACT-RETRY.md)
on the same package remained at 1280 × 860 outer geometry. Setup, Library details,
Observatory controls and journal reading worked at 200% zoom. A copied exhausted
36-journal session verified and restored paused with Resume disabled; the original
files stayed exact. Native resizing remains unresolved through automation, so the
900 × 700 and 720 × 600 **content-area** targets remain unqualified.

The prior [0.23 navigation tranche](validation/2026-10-15-navigation-0.23.0/README.md)
makes My reservoir the initial, direct destination alongside the five original
research destinations. Preparation history has one Observatory reader and a Library
shortcut. Accepted reports and disclosures survive return; subviews retain their
scroll, and Library results retain position for an unchanged query. Setup guidance
is shorter. All 417 frontend tests in 46 files, TypeScript/Vite, reference checks and
the distinct 46-file macOS package with local ad hoc signing pass. Rust qualification
is reused by exact comparison of 164 inputs with five version-only substitutions;
it was not rerun. Scoped native checks pass: preparation report/disclosure and
Library list position survive return; a pinned journal remains selected while a
second entry arrives, and Later entry selects it. The scripted session reaches its
61-step bound with two journals, followed by clean quit. Its 13-file stored bundle
passes the same-build verifier unchanged; native export/recovery were not rerun.
Production v8 and backend behavior are unchanged.

The prior [0.22.1 wording pass](validation/2026-10-15-research-language-0.22.1/README.md)
uses plain workspace titles, shorter controls and optional technical details. About
this preview holds build/platform information and diagnostic scenes. It passes all
413 existing frontend tests, TypeScript/Vite, reference checks and its distinct macOS
package build. Scoped native inspection covers revised screens and one short
scripted journal/save/application flow through step 31, then clean quit.
Production v8 and the backend are unchanged; prior Rust checks are
reused by exact source equality with version-only metadata changes. See the
[copy and navigation conventions](RESEARCH-LANGUAGE.md).

The prior [0.22 reference-field package](validation/2026-10-15-observatory-fields-0.22.0/README.md)
adds magnitude, deviation, reconstruction/residual and the complete state capture
spectrum to the linked trajectory. Its 224 core, 199 desktop and 413 frontend tests,
TypeScript and both strict Clippy checks pass; two opt-in desktop tests remain ignored.
Scoped native checks cover exact fields, spectrum provenance, preference retention
and graphics recovery. A short main-PID CPU/RSS capture excludes WebKit, GPU and
power; it is not whole-app or endurance qualification. The
[0.20 source/package/native account](validation/2026-10-14-reading-measurements-0.20.0/README.md)
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
slots remain unstarted, with no service or provider request. A separately identified [third window](validation/2026-10-15-context-sources-03/README.md)
uses the user-approved provisional 30% admission floor. It passed at 42% and completed
all twelve responses within bounds; the owned service stopped cleanly. The candidate
was not promoted: a local improvement coexisted with invented present measurements.
Prior refusals and original journals remain unchanged. The report separates full
readings, the review-order recovery and numerical evidence from writing style.

## Use the preview

| Workspace | Available workflow | Details |
| --- | --- | --- |
| My reservoir · initial destination | Explicitly create/start a bounded scripted or local-model session; watch recurrent state and separate sensory fill; read complete journals independently of the live cursor; export and restore paused | [Sustained sessions](SUSTAINED-SESSIONS.md) |
| Experiments → New experiment | Explore, stages 1–4, standalone A–H, matched B–H and D/D observation pairs, plus a separate fixed field-only controller study | [Fresh experiments](FRESH-EXPERIMENTS.md) |
| Experiments → Recording / Library | Verify recorded experiments, inspect exact prompt/save/application evidence, import immutable bytes, search/filter metadata, export originals and recover the index | [Library](LIBRARY.md), [guided evidence](GUIDED-EVIDENCE.md) |
| Observatory | Independent clocked fill and ordinal state recordings; linked trajectory, reference fields and full state capture spectrum; responses and the canonical Preparation history reader, also reached from Library; exact exports | [Recorded fields](RECORDED-STATE-FIELDS.md), [recorded fill](RECORDED-FILL-SPHERE.md), [responses](RESPONSE-EVIDENCE.md) |
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

Earlier/Later selects adjacent entries from the selected journal's saved position.
Older/Newer changes the history window without changing the selected prose; one
boundary entry overlaps adjacent windows. Refresh keeps that window anchored while
new entries arrive. Pause following pins the reading; Follow latest explicitly
opens the newest entry. Evidence and measurements begin closed, and evidence panels
support keyboard focus and scrolling. View offers 75–200% zoom and Actual Size;
this process-local presentation setting is not stored in a recording.

The app never strips model-authored telemetry or rewrites the journal. Retry and
skip remain explicit; recovery restores verified state paused and never resends a
request automatically.

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
sphere and state surface preserve their distinct quantities and exact-value fallback.
The [retained trajectory](RECORDED-TRAJECTORY.md) adds selectable PC-axis pairs linked
to the state row, with fixed full-capture scales and exact values. [Reference fields
and spectrum](RECORDED-STATE-FIELDS.md) distinguish per-row centered energy from
the static 128-mode sample-covariance spectrum and separate sensory history.
Field, mode and trajectory-axis choices survive workspace navigation within the
running app. Compact layouts, broader accessibility and platform visual acceptance
remain in the [parity matrix](../../shared/reservoir-scope/PARITY.md#capability-matrix).

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

Earlier published source checkpoints are 0.25 at `3cfbf1b` and 0.27 private preview
at `4a46c38`; candidate 04 is built from `c4a3ba1`. The
[0.27.1 completion polish](RELEASE-0.27.1.md) adds a separately qualified, calm
finish for fully saved sessions at their run limit. This save point also preserves
the [bounded journal-flow account](validation/2026-10-16-journal-flow-0.27.0/README.md)
and the superseded 0.25 check's preparation evidence. The standard 0.27.1 build does
not replace the private candidate 04 handoff; prompts and original receipts remain
unchanged. See [current status](STATUS.md) for the qualification boundaries.
The [earlier publication account](validation/2026-10-13-public-checkpoint/README.md)
remains historical. The full pre-edit README is preserved byte-for-byte in
[README-HISTORY-2026-10-15.md](README-HISTORY-2026-10-15.md).
