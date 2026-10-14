# Reservoir Scope Tauri Preview

This is the parallel cross-platform desktop foundation for Reservoir Scope. The native
macOS application remains in [native/ReservoirScope](../../native/ReservoirScope/README.md)
with its existing **0.15.0 build 21** identity. This preview has its own application
identifier, `research.reservoir.scope.tauri`, and version `0.17.0`; it can coexist with
the native application. See the full [Tauri roadmap](../../TAURI-ROADMAP.md).

This preview provides an offline A–H guided journey, a searchable experiment
Library, reviewed research cases and geometry bookmarks. Stages, exploration and
action and controller teaching recordings are numerically verified in Rust when opened. Imported experiments
are published as immutable original bytes; the Library's SQLite index stays separate.
Cases and geometry remain temporary views. Navigation starts no experiment, model
request, live connection or migration from the native application.

## Implementation status

| Roadmap area | Current implementation | Qualification still required |
| --- | --- | --- |
| M0 reference | Frozen source/resource manifest; verified staging and packaged hashes | Deliberate review before baseline changes |
| M0 desktop | Separate identity, single instance, native dialogs, bounded file access, atomic export | Windows/Linux execution; broader lifecycle/accessibility acceptance |
| Rendering | Event-driven 32/128-coordinate surfaces, picking, exact tables, context recovery; reusable buffers during recorded playback | Actual WebView checks and measured GPU, power and memory behavior across targets |
| M1 compatibility | Stage, exploration, action v1/v2/v3 and controller replay; bounded Unicode codec; case/geometry validation; independent Swift oracles | Unqualified Unicode/parser cases, remaining conformance edges |
| M2 offline research | A–H mechanical evidence; controller evaluation; all 22 authored examples; cases/geometry; exact original exports and checked selected-case derivatives; bundled catalog refresh on upgrade | All-target packaged/human acceptance |
| M3 Observatory | Independent clocked fill history and ordinal 128-node state replay, native radial-volume fill sphere, exact values, bounded timelines and playback; native response receipts, separate retained simulation, preparation history and exact exports | Remaining trajectory/spectrum and visual qualification; full M3 parity is not claimed |
| M4 fresh experiments | Finite Explore, original stages 1–4, standalone A–H and paired B–H with independent scripts/shared tapes; separate active/quiet observation pairs; arm-owned save/memory, partial-boundary checkpoints, WAIT/WRITE, H control, Library and recovery; fixed two-field controller creation | All-target save/lifecycle qualification |
| M5 model connections | Explicit loopback readiness and bounded finite model generation; cancellation and retained outcomes; no automatic service connection | Broader real-service and all-target qualification; selected feeds |
| M5b personal loop | My reservoir; versioned open journal invitations with historical replay, current/prior measurement reference, recurrent/sensory observations, automatic durable journals, bounded storage, explicit recovery and independent reading; explicit output/deadline limits; twelve completed v5 model journals with exact next-step feedback, eleven prior-text memory joins, native export and paused recovery; earlier evidence remains build-specific | Factual grounding and action-scope clarification, provider context coverage, broader pointer/accessibility review, longer-duration and all-target acceptance |
| M6 delivery | Identified manual preview builds and separate qualification receipts | Full platform matrix, collaborator tasks and native backport review |

Version **0.17.0** introduces `reservoir-journal-v5`: a shorter optional numerical
readout followed by the full previous saved-and-applied entry and an open invitation.
Full observations and the eight-row measurement reference stay in Evidence. Existing
sessions retain their exact v1–v4 contracts; the codec, numerical mechanisms and
save/readback/application gates are unchanged. The [contract](../../shared/reservoir-scope/continuing-writing.md)
and [qualification account](validation/2026-10-13-continuing-writing-0.17.0/README.md)
separate this context change from its subsequent
[twelve-entry real-model episode](validation/2026-10-13-v5-writing-episode01/README.md).
That episode passed delivery, exact memory, export and paused recovery checks.
Full reading finds developing prose alongside invented actions and measurements;
mechanical completion does not establish factual grounding or literary improvement.

Version **0.16.0** adds optional provider-reported prompt-token evidence inside each
journal's closed **Evidence** section, separate from requested context capacity.
Missing and malformed optional counts do not prevent an otherwise valid journal
from saving; incomplete replies remain ineligible. Wide counts retain exact integer
values. Recovery inspection includes a bounded list of received responses, including
incomplete attempts. The open writing invitation, numerical mechanism and feedback
rules are unchanged. The [contract](../../shared/reservoir-scope/provider-prompt-evidence.md)
and [qualification account](validation/2026-10-13-input-evidence-0.16.0/README.md)
separate implementation, synthetic checks and packaged behavior. The tested 0.15
reader ignores journal-only additions and rejects the actual new bundle at its
checkpoint hash check; its earlier replay checks cannot validate the new evidence.
The r2 native five-response check saved/applied four journals and held the incomplete
fifth reply. Export, clean relaunch and explicit offline paused recovery passed,
with every scientific file byte-identical. The first candidate’s stale version label
was fixed by deriving it from package.json; both candidate identities are retained.
A reported count does not prove complete context processing or accurate prose.

Version **0.15.0** adds a versioned current/prior measurement reference while leaving
the writing topic, form and length open. The model receives exact prior numerical
summaries separately from prior prose, and readers can open **Recorded measurements**
beneath each journal. Historical sessions keep their exact contracts. This is
better supplied evidence, not a guarantee that a model will use it accurately.
The [0.15.0 qualification account](validation/2026-10-13-measurements-0.15.0/README.md)
retains the source/native scripted checks and the first refused model admission.
A separately selected [v4 episode](validation/2026-10-13-v4-writing-episode02/README.md)
then completed four Gemma journals on the unchanged package. Saved feedback, exact
prior-text memory, native export and paused exhausted-budget recovery passed.
The writing carries its imagery forward, but incorrect numerical and temporal
claims remain alongside accurate references. Read the [actual journals](validation/2026-10-13-v4-writing-episode02/JOURNALS.md)
and [review](validation/2026-10-13-v4-writing-episode02/REAL-MODEL-RESULTS.md).
Mechanical verification does not certify prose accuracy or emergence.

Version **0.14.0** gives new sustained sessions an explicit 1,024-token output ceiling
and a three-minute request deadline, with 8,192 context tokens selected for new
local-model setup. Advanced settings expose bounded alternatives; old sessions keep
256 tokens and one minute. These limits do not prescribe a length or change the
v3 invitation. The [0.14.0 qualification](validation/2026-10-13-writing-room-0.14.0/README.md)
separates source checks, packaged behavior and the bounded real-model outcome. Four
entries completed, saved and applied, with exact previous-journal text in the three
later prompts. Native export and exhausted-budget recovery passed; the revised
owned service stopped cleanly. The writing develops recurring imagery but still
makes some incorrect measurement claims. Read the [journals](validation/2026-10-13-writing-room-0.14.0/JOURNALS.md)
and [review](validation/2026-10-13-writing-room-0.14.0/REAL-MODEL-RESULTS.md) separately
from mechanical verification.

The [0.13.0 account](validation/2026-10-13-grounding-0.13.0/README.md) records
open-ended writing, exact prompt versions and factual-claim checks that do not grade
metaphor as measurement. A bounded model rehearsal stopped at its first token-limited
response, correctly retaining zero saved journals and no feedback. Visible native
pointer controls passed two minimize/reopen checks. After resolving a folder-sheet
automation blocker, native export and clean relaunch/paused recovery also passed
for this held attempt, without a new model request. The
[0.12.2 account](validation/2026-10-13-reading-0.12.2/README.md) retains its four saved
and applied model journals, including the earlier grounding errors. The
[frozen 0.12.0 resource account](validation/2026-10-13-reliability-0.12.0/RESOURCE-RESULTS.md)
owns the actual two-hour minimized measurements; they do not transfer to this build.
The [original sustained-session account](validation/2026-10-13-sustained-0.12.0/README.md),
[0.11 model-connection account](validation/2026-10-13-models-0.11.0/README.md) and prior
candidates retain their own receipts. Longer runs, Windows/Linux and measured
GPU efficiency remain open qualification gates.

See the [parity ledger](../../shared/reservoir-scope/PARITY.md) and
[core guide](crates/reservoir-core/README.md). Numerical verification runs whenever
an example or external recording is opened; bundled hashes alone never grant it.
Verification, recorded outcome and source are separate. A faithfully retained failed
experiment can pass verification. Unsupported text or families return incomplete.

### My reservoir and sustained journals

Choose **Experiments → My reservoir** for the new personal session. Create prepares
local state; Start runs it within the displayed pace, step, attempt, time and storage
bounds. A scripted demonstration works offline, or configure your exact loopback
model. Writing is saved automatically and read back before its vector can be applied
at the next numerical step. The v5 prompt includes a short optional readout of RMS, separate sensory fill and
coordinate distance, then the full latest eligible journal. Full measurements remain
in Evidence. New sessions invite open-ended
writing: the model chooses its topic and form, without a required metric summary or
answer to a human question. This creates room for continuity and exploration; it does
not by itself demonstrate emergent behavior. Older sessions retain their exact prompt
version on recovery.

Read old entries while the state view continues. Leaving the workspace or minimizing
suspends unnecessary graphics while the Rust worker owns the run. Sleep and relaunch
require explicit review/resume. The new portable directory bundle preserves complete
continuation and ordered immutable evidence; it does not masquerade as a finite Swift
record. Read the [sustained-session contract](SUSTAINED-SESSIONS.md) for the numerical,
storage and lifecycle boundaries.

Setup leads with the source, pace, writing cadence and human-readable limits;
additional numerical controls are in Advanced settings. Saved prose leads the
journal reader. Open Recorded measurements for that entry’s current/prior reference,
or Evidence for the exact prompt, response, hashes and application
record. Follow latest returns to new writing without changing the running clock.

### Fresh experiments and journal saves

Choose **Experiments → Fresh experiments** to create a seeded, finite run. Explore
starts quiet and provides explicit pulses, per-step controls and history inspection.
The original four stages retain their existing meanings. The state surface and
separate sensory fill view show backend observations; neither invents unavailable
measurements. Changing controls affects the next numerical boundary.

Standalone A–H experiments expose input, recurrence, sensory observation, journals,
feedback, memory, choice and retention regulation as separate mechanisms. Choose
independent scripted replies, an explicitly configured local model for D–H, or a fixed
scripted tape before creating the session.
At each WRITE opportunity, the clock waits for **Save journal durably**. Rust publishes
the exact candidate and reads it back before committing its saved receipt. E–H then
apply the encoded semantic input on the next step: observing/saving at 30 first applies
at 31. D saves writing without returning it to state.

F–H reread the latest saved journal from the owned session store before forming the
next prompt. Missing, modified or linked files produce a retained failure before a new
request starts. G/H can WAIT, creating no new journal and leaving the previous feedback
held. Manual opportunities force WRITE. H shows current retention separately from the
controller's next-step retention. Fixed tapes preserve their precomputed text/vectors
rather than encoding them anew against the running field. Exact memory, prompts,
replies and application boundaries remain inspectable. The scripted mode demonstrates teaching mechanisms. Local-model mode records actual
requests and responses; neither establishes adaptive learning or writing benefit.

Components B–H can now run beside their preceding component with one aligned clock.
The state surfaces share camera controls and fixed scales; selecting an arm selects
its exact values, sensory fill, journal memory and outcomes. Each arm saves in its
own namespace. A failed component action retains an unstarted cancellation for the
later partner. While one journal is saved and the other is pending, recovery keeps
the completed receipt and pending candidate separate from the previous complete
portable snapshot.

The separate **Observation comparison · D / D** uses the same trajectory in both arms,
with recurrent coordinates added only to the right prompt. Active and quiet input
presets are explicit. Actual request order alternates; ordinary partner failures
remain independent. Both arms use the selected script or local model and keep feedback/memory disabled.
This exposes the observation contract without claiming an improvement in writing.

The separate **Controller study · two sensory fields** creates the fixed 600-step
baseline/regulated comparison. Both fields share the same seeded 66-dimensional
input; two fixed-scale fill spheres show their separate covariance evolution. Exact
inputs, 32 projected coordinates, spectra, controller output and next retention stay
inspectable. Read a selected prefix's fill/retention trends and shared 32 × 66 projection
weights explicitly. The evaluation includes only reached steps 301–600 and disappears
when rewound before that window. This study contains no reservoir state or journals.

Only all 600 observations form a portable controller record. Step, run, pause and
stop retain current progress for inspection; an incomplete run can export checkpoint
metadata, clearly labeled as progress without recoverable field observations. It
cannot be saved to the Library or exported as a partial native controller experiment.
The completed verified record supports Library saving and exact-byte recovery.
Fresh action turns also display their actual request order when retained; no ordinal
is invented for fixed tapes or unstarted requests.

A failed write retains the same candidate for retry. **Stop and retain failed save**
creates a terminal failed record, retaining the reply without inventing feedback
eligibility. Export cannot bypass a pending journal save. **Save to Library** publishes
a verified immutable snapshot, labeled **Created here** separately from imports.
Current step, durable checkpoint step and Library save status remain distinct.

Finite runs use a Rust worker and survive workspace navigation; hidden visualizations
release graphics resources. The application reviews unsaved evidence before close or
quit. Completed recovery files can be inspected and explicitly exported after relaunch;
no experiment automatically resumes. Internal checkpoints retain the current and
previous portable snapshot, avoiding an ever-growing copy of every prefix.
See [the fresh session and save contract](FRESH-EXPERIMENTS.md) and
[incremental core guide](crates/reservoir-core/SESSIONS.md).

### Explicit local-model connections

In an eligible fresh recipe, select **Explicit local Ollama model**, enter an HTTP
loopback endpoint and the exact model name, then explicitly check it. Both fields
start blank. The app starts no service and downloads no model. Readiness checks
identity/availability; it does not establish capacity or a successful generation.

Original stages 3/4 and independent D–H (including matched and observation pairs)
can request a response when Step, Run or a manual opportunity reaches its boundary.
The numerical clock waits. Requests have a 60-second deadline, one-MiB response
bound, 256 output-token limit, temperature zero and a 4,096-token context default.
Actions request JSON; original stages request prose. No redirects, proxies,
automatic retries or provider substitution are accepted.

Pause stops numerical scheduling while an in-flight request settles. Stop cancels
it and rejects late results. This finite preview holds numerical time after a response; a required paired peer
may still dispatch at that boundary. It asks for **Save journal durably** on WRITE;
the sustained automatic journal loop is
next. Failed and unqualified responses cannot become feedback. Recovery preserves
bounded diagnostics without resending requests. See [local-model contracts](LOCAL-MODELS.md).

### First offline Observatory recordings

Choose **Observatory → Open bundled recordings** to check the identities and structure
of two independent recordings. Fill history retains 507 clocked samples, exact fill,
backward fill differences, reference configuration and three sensory Rayleigh direction
estimates. The fill sphere uses the native radius `cbrt(fill / 100)`; its reference zones
do not establish historical controller modes. The estimates are not certified leading
eigenvalues or a complete spectrum, and remain distinct from ESN-state covariance λ1.

The separate binary state replay contains 1,024 rows × 128 coordinates in stored order.
It has no per-row timestamps or paired fill. A fixed coordinate-index atlas exposes the
signed surface and exact selected node; the coordinate history has a fixed −1 to +1
scale. Retained projection/RMS metrics are identified as capture summaries. Neither
recording is synchronized with the other. Original source paths remain inert metadata.

Playback holds the prior retained sample on the elapsed clock; manual scrubbing uses
nearest selection. Ordinal state playback has an explicitly chosen rows/second speed.
Pause, hiding and workspace navigation stop playback and reject late playback reads.
Timelines use bounded Rust pages and do not publish incomplete coverage as a complete
chart. Missing values and session boundaries break plotted lines. Large recorded
intervals remain spaced; no new gap-detection threshold is invented.

The fill renderer reuses geometry/materials and shares bounded, event-driven scheduling
with the surface policy. Graphics recovery and exact-values mode remain available.
There is no idle animation, smoothing or measured GPU/power savings claim. Desktop
foundation reference scenes are available through an explicit diagnostics disclosure.
See [fill rendering](RECORDED-FILL-SPHERE.md), [response and preparation contracts](RESPONSE-EVIDENCE.md), and the parity ledger for remaining M3 work.

### Recorded visual and writing experience

Open **Experiments → Recording reader**, choose Stage 4 or a recorded component, then use the frame
slider, stored playback and turn inspector. The signed surface shows retained
reservoir coordinates. Separate charts show recorded sensory covariance and reduced
fill; unavailable fields stay unavailable. Exact vectors and original prompts remain
accessible. Recorded observation and application steps expose the writing/return
boundary. Action journals retain their saved/failed receipt meaning. Exporting a file
never manufactures a journal-save receipt or makes text eligible for feedback.

Playback navigates stored frames at up to two per second, waiting for each read; this
is independent of recorded simulated time. Tracks keep separate cursors. Opening an
invalid replacement or receiving a stale asynchronous response cannot replace the
accepted reading. Valid empty records still expose identity, outcome, verification
and export. The original bytes remain in Rust, including unknown fields; only typed,
verified fields enter display views. Historical paths are text, never followed.

Each surface has a 1,000,000-pixel budget, DPR at most 2 and a bounded dimension.
Drawing is event driven and suspended while hidden, offscreen or context-lost.
Recorded frame changes reuse the context, mesh, material, interpolation atlas and
buffers. These are implemented workload bounds, not measured GPU or battery savings.

The reader keeps at most four temporary handles and 256 MiB of original bytes across
handles. Verification/file dialogs are serialized; scalar timelines contain at most
600 original points with explicit stride, missing data and final-frame retention.
Full selected frames and individual text turns are fetched on demand. Decoded data
and verification workspace use additional memory; long-session memory qualification
remains ahead. Opening does not import a file into a persistent Library.

### Guide, Library, cases and geometry

The **Guided tour** retains the authored A–H questions, checkpoints, expected
observations and interpretation limits. Continue seeks the next checkpoint and
pauses, then advances to the next lesson. Recorded-model examples D–H are explicitly
labeled; selecting them makes no provider request. Future turn text and application
steps remain hidden until the guide cursor reaches them. Rust evaluates the verified
right-arm prefix and its available matched arm, preserving the native evidence states
and conclusions. Same-step RMS measurements remain separate. The independent Swift
oracle covers 2,507 cursor results; see [mechanical evidence](GUIDED-EVIDENCE.md).

The separate controller study replays two sensory fields under shared input. Its
target-error evaluation appears only from step 301, counts the reached prefix through
600 and disappears when rewound before the window. It has no recurrent-state surface
or language turns. The guide's H lesson remains distinct from this 600-step study.

**Experiments → Library** searches metadata and filters origin, family, source and
outcome. It keeps bundled authored order, accurately labeled local save/import timestamps and
persistent recents. Explicitly created experiments have their own origin filter. Results are paginated and virtualized. Refresh reports scan coverage and
visible diagnostics, without the native 500-record/5,000-entry caps. Import verifies
and atomically publishes exact bytes; identical bytes identify the existing entry,
while different bytes with the same embedded ID stay distinct. A failed index update
leaves published records intact. Rebuild recovers metadata from this app's owned
files. Upgrades transactionally refresh bundled metadata when the package/resource identity changes; managed bytes and recents remain intact. No automatic scanning of the native Library occurs. See [Library details](LIBRARY.md).

**Research cases** explicitly loads the bundled reviewed catalog or opens an external
one. Embedded hashes, unique quotations and internal references are validated before
replacement. Authorship, source ownership, recalled accounts and not-observed outcomes
stay distinct. Evidence buttons expand the exact inert text. Export retains the whole
original catalog byte for byte. Export selected case creates a checked one-case derivative, preserving every embedded material and source reference; its resulting hash differs from the whole catalog. See [case contracts](crates/reservoir-core/CASES.md).

**Geometry bookmarks** explicitly opens the synthetic example or a selected packet.
It checks body/chain hashes, references, 128-coordinate vectors, clocks and recorded
RMS comparisons; it preserves exact unsigned clocks as strings at IPC. These checks
establish packet consistency, not boot/layout identity, novelty or a causal claim.
See [geometry contracts and remaining qualification](GEOMETRY.md).

The selected sustained-loop lifecycle is **keep running while the app is open
or minimized**. The Rust worker implements versioned continuation and observations,
automatic durable journals, run/storage budgets and explicit paused recovery.
Sleep/interruption handling is implemented; actual sleep, physical power-loss and
multi-hour real-model qualification remain open. The two-hour minimized synthetic
measurement belongs to its frozen 0.12.0 build, not every subsequent package.

The immutable initial M0 receipts describe the earlier foundation build. New check
records and candidate receipts are retained separately under [validation](validation/).
No source build, unit test or older UI observation confers new packaged acceptance.
The [0.17.0 qualification](validation/2026-10-13-continuing-writing-0.17.0/README.md)
and [real-model episode](validation/2026-10-13-v5-writing-episode01/README.md)
record the current package's separate checks and remaining limits. Earlier receipts,
including [0.11.0](validation/2026-10-13-models-0.11.0/), remain historical evidence
for their exact builds.
The [unlocked macOS walkthrough](validation/2026-10-12-responses-0.6.0/unlocked-ui-supplement.md)
checks paired responses, graphics recovery, retained preparation failures, current
retry verification, five native-dialog exports and quit/relaunch in the unchanged
0.6.0 app. Exported bytes match their sources, and the two response exports pass
independent Swift/Rust readers. This does not qualify other OS targets or measured
GPU efficiency.

## Build prerequisites

Use Node **20.20.1**, npm, Python **3.12 or newer**, and Rust **1.94.1** (pinned by
[rust-toolchain.toml](rust-toolchain.toml)). Platform prerequisites come from the
[Tauri v2 guide](https://v2.tauri.app/start/prerequisites/):

| Target | Development requirements | M0 CI bundle |
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

Run these steps against the actual packaged app after a successful build. Record the
package hash, OS version, architecture, WebView/runtime version and GPU/display setup
with the results. Keep a failed or unexecuted item explicit.

1. Install/open the package without starting a frontend dev server or model service.
   Confirm the Tauri Preview identity and the unchanged native app can coexist.
2. In Observatory, use Show desktop diagnostics and reference scenes to open both 32- and 128-coordinate references. Confirm the displayed source
   identity and limits, values table length and exact selection value. The historical
   128-coordinate row must not acquire a per-row timestamp or paired fill claim.
3. Use pointer and keyboard camera controls; select a coordinate from the table and
   by picking the geometry. Resize, change display scale, minimize/restore and move
   between displays. Confirm selection remains tied to the same coordinate.
4. Check idle rendering stops; measure redraw latency during interaction rather than
   treating successful WebGL2 context creation as proof of hardware acceleration.
   Exercise the graphics-context loss/recovery control where the runtime exposes it.
   Verify the exact-values table stays usable after graphics loss and in table-only
   mode. On Linux include the supported Wayland/X11 and GPU combinations in the result.
5. In Experiments → Recording reader, verify bundled Stage 4 and component H. Inspect observed step 30
   and applied step 31, switch tracks, pause playback, leave/return, and export original
   bytes. Open the export in the independent Swift verifier. Reject a changed record
   while preserving the accepted selection. Also exercise the separate foundation
   native open/save proof workflow: cancel each dialog, open a valid
   bounded file, reject oversize/non-regular input, export the scene fixture to a selected path,
   reopen it, and confirm the reported result matches the chosen file. Check Unicode
   filenames, spaces, read-only destinations and denied permissions. Do not use live
   data or private packets for this M0 qualification. The foundation file proof reports byte identity only; the Experiments Open
   command performs numerical verification. Neither silently imports into a Library.
6. Traverse controls with the keyboard, inspect visible focus, and test the coordinate
   table/status messages with the platform screen reader. Confirm reduced motion and
   display scaling keep all values and actions accessible.
7. Quit and restart the packaged app, verify it needs no network, and inspect that
   release builds expose neither test driver servers nor broad filesystem/shell APIs.

[Tauri's current testing guide](https://v2.tauri.app/develop/tests/webdriver/) supports
macOS, Windows and Linux through WebdriverIO's embedded test driver. Direct
`tauri-driver` still supports only Windows/Linux. M0 does not include WDIO; future
instrumented test builds must exclude those plugins from shipping packages and still
receive pristine-package acceptance. A Chrome frontend test is not a WKWebView,
WebView2 or WebKitGTK test.

[Tauri's Linux graphics notes](https://v2.tauri.app/develop/debug/linux-graphics/)
document that a successful WebGL2 context can still use software rendering or a slow
presentation path. Renderer strings are not a reliable substitute for measurement.
The table fallback is therefore part of acceptance, not merely an error page.

## CI and evidence boundaries

[The workflow](../../.github/workflows/tauri.yml) uses `macos-14`, `windows-2022`, and
`ubuntu-24.04`, installs pinned toolchains, checks references and staging behavior,
runs frontend/core checks, and builds one native bundle per platform. It uploads
ordinary short-lived CI artifacts labeled **unqualified**, with no release publication,
external deployment, or distribution signing.

The workflow asserts native architecture before compiling. GitHub's
[current runner table](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
identifies `macos-14` as arm64; that is an explicit checked assumption, not a silent
promise attached to a mutable runner alias. This Ubuntu 24.04 build does not establish
compatibility with older Linux distributions or their glibc/WebKitGTK versions.

Local test and build outcomes belong in the roadmap's execution ledger only after
execution. Windows/Linux acceptance, cross-platform visual comparison, hardware
performance and release signing remain unqualified until recorded evidence exists.

## Capture a local qualification receipt

After the build and source edits have finished, capture a receipt without rebuilding
or launching the app. From the repository root:

```sh
python3 desktop/ReservoirScope/scripts/qualification_receipt.py \
  --app 'desktop/ReservoirScope/target/release/bundle/macos/Reservoir Scope Tauri Preview.app' \
  --checks-file desktop/ReservoirScope/validation/2026-10-11-offline-0.3.0/checks.json \
  --output desktop/ReservoirScope/validation/new-candidate/qualification.json
```

Adjust `--app` for an explicit-target build (`target/aarch64-apple-darwin/release/...`).
The script records implementation source hashes, native baseline/resource identities,
lockfiles, host/toolchain outputs, packaged file and binary hashes, and actual local
`codesign` verification. It rejects changing inputs and refuses to replace an existing
receipt. Validation outputs are excluded from implementation hashes, so the receipt
does not hash itself. These identities capture source and package together; they do
not independently prove that the package was built from that source.

Generated `src-tauri/permissions/autogenerated/` TOMLs are also excluded: the small
retained outputs are regenerated by `build.rs`, whose hash is captured along with
the capability definitions. Supply `--archive /path/to/package.tar.gz` to record
the checksum of a completed package archive alongside the app identity. The tool
does not create an archive or establish its correspondence to the app merely by
hashing it.

No test pass, package build result, visual acceptance or cross-platform qualification
is inferred. Unexecuted checks remain explicit. Supply an optional `--checks-file`
containing a JSON array of observed results; every non-unexecuted entry needs `id`,
`status`, `command` and `evidence`. Results are labeled **caller-supplied**, distinct
from signing/toolchain commands actually executed by the capture tool. Supported IDs
are listed in the script's `CHECKS` constant. Use repeated `--note` arguments for
limits, partial UI observations or pointers to retained logs. A successful local
codesign check is not notarization or release approval.
