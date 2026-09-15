# Reservoir Scope handoff

The feature baseline is **0.11.0 build 15**, adding the Essentials action ladder,
local journals and paired comparisons. [The packaged build receipt](build-receipt.json)
preserves the September 10 qualification and its exact source hashes. The
September 15 source stabilization makes two expressions explicit for Swift 6.2.4:
the recurrent row-sum calculation and the action comparison plot coordinates.
It preserves their arithmetic and recorded-fixture behavior.
Source staging also removes obsolete Swift files and resources from reused
build caches; `check-source-staging.sh` verifies this with temporary fixtures.

[The source-check receipt](validation/stabilization-20260915/source-checks.json)
records the separate offline build, tests and fixture verification. These sources
were not installed or launched as an app; the historical package receipt is not
a claim of current executable identity. The initial viewer snapshot remains
`dc93adb85861bda82ee941a4abf2c67e6644fa33`.

## Shared checkout

These paths expose the same files and Git history:

- On `volya`: `/Users/v/other/reservoir-llm-research`
- Through the Mac's mounted share:
  `/Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research`

The original handoff's SSH inspection confirmed matching source hashes on both
paths. Recheck available paths, current remotes, branch and changes before starting:

```sh
git status --short --branch
git remote -v
git log -2 --oneline
```

The initial snapshot tracked the viewer and selected supporting files. Research
tracking has since expanded. Preserve other agents' work, stage explicit paths,
and coordinate before switching branches in this shared checkout. The
[version-control account](docs/VERSION-CONTROL.md) explains the initial scope.
Read the workspace's root AGENTS.md and CLAUDE.md for the broader research rules.

The generated `Sources/ReservoirScope/Resources/essentials-workspace.txt` is a
local build hint and is ignored. `build-app.sh` regenerates it for the chosen
checkout. A SwiftPM build without a valid hint can inspect examples, but research
saves require a package configured for the current workspace. Required example
JSON and their bundled copies remain tracked. Large raw renderer buffers,
preliminary captures and build logs stay local; retained qualification receipts,
source snapshots and final image fixtures remain reviewable.

## What is ready

**0.11.0 build 15** adds **Actions & comparisons** alongside Explore and Stage
experiments. Its core is `essentials/actions/`; its native lifecycle and view are
`ActionComparisonViewModel.swift` and `ActionComparisonExperience.swift`. The
[action guide](../../essentials/ACTIONS.md) covers the eight versions, Run/Step/
Write journal, fixed reply/vector tape, independent generation and exact receipts.
New `essentials-actions-v1` records include portable journal text. Local journals
and generated sessions save under `research/outputs/essentials/actions/`.
The [implementation account](../../analyses/2026-09-10-essentials-actions.md) and
[current receipt](build-receipt.json) retain qualification and limits.

**0.10.1 build 14** halves the zero-contour blend strength, keeping its location,
width and the state mapping unchanged. The renderer's 43 checks pass again,
including seven exact legacy image matches. The saved completed Stage 1 run was
reopened in the final app and its first frame inspected. The
[actions and comparisons ladder](../../essentials/stages/ACTIONS-AND-COMPARISONS.md)
was proposed with that release and implemented separately in 0.11.0.

Reservoir Scope **0.10.0 build 13** defaults Essentials to **Topography**, with
signed height, fixed contour intervals and a display-only Height slider. The
original Surface view remains available. [The mapping guide](docs/STATE-TOPOGRAPHY.md)
and [implementation account](../../analyses/2026-09-09-state-topography.md) explain
why this is the topography of a projected scalar field rather than network wiring.
The numerical core and recording formats are unchanged; the baseline renderer
retains its earlier behavior.

Reservoir Scope **0.9.0 build 12** opens **Essentials → Explore** with Start/Pause,
Step, Send pulse, editable next-step settings, independent recurrent feedback and
repeated external input, optional sensory observation, and exact recorded history.
The [exploration guide](../../essentials/EXPLORE.md) explains the controls and
the [exploration account](../../analyses/2026-09-09-essentials-exploration.md)
retains checks and presentation limits. Explore has a separate replayable record
format; its quiet defaults do not alter the existing stage recipes.

The preceding **0.8.0 build 11** added **Minime & Astrid / Essentials** at the top.
The [Essentials guide](../../essentials/README.md) covers four executable stages,
the headless runner, local-model configuration, exact records and replay.
The [implementation account](../../analyses/2026-09-09-essentials-implementation.md)
and [current build receipt](build-receipt.json) retain validation and its limits.
The shared core lives under `essentials/`; workspace, execution and inspection
live in `ScopeWorkspace.swift`, `EssentialsViewModel.swift` and
`EssentialsExperience.swift`. Hands-on execution and its view live in
`ExplorationViewModel.swift` and `ExplorationExperience.swift`; the numerical
implementation is `essentials/reservoir/ReservoirExploration.swift`.
New runs save under `research/outputs/essentials/`.

The previous viewer features remain available:

Reservoir Scope **0.7.1 build 10** has fading measured high/low marks in
Reference zones. Each pair collects 30 source seconds and fades over 60; a new
pair forms at half-life when a new observation arrives. The speed buttons offer
1×, 5×, 10×, 20× and 40×, with 20× selected by default. Reduce Motion retains
turnover using static forming/retiring contrast.

The [completed account](../../analyses/2026-09-07-fading-watermarks.md) and
[animation guide](docs/ANIMATION-DATA.md#observed-high-and-low-water-marks)
explain recorded replay, accepted health clocks, batch-scoped activation data,
gaps and rewind. Aging changes visibility, not measured fill positions; eased
surface fill never supplies a watermark measurement.

Useful entry points in `Sources/ReservoirScope/`:

- `FillWatermarkMemory.swift`: measured intervals and source-time aging.
- `ReferenceWatermarksView.swift`: forming/fading arcs and readable labels.
- `ReservoirScopeApp.swift`: source selection, replay clock and view wiring.

## Build and check

From the research repository root on a Mac with Swift tools and Metal:

```sh
native/ReservoirScope/build-app.sh
essentials/check.sh
native/ReservoirScope/check-source-staging.sh
native/ReservoirScope/check-dynamic-state-surface.sh
native/ReservoirScope/check-topographic-surface.sh
native/ReservoirScope/check-topographic-renderer.sh
native/ReservoirScope/check-essentials-ui.sh
native/ReservoirScope/check-essentials-layout.sh
native/ReservoirScope/check-essentials-run-layout.sh
native/ReservoirScope/check-exploration-ui.sh
native/ReservoirScope/check-exploration-layout.sh
native/ReservoirScope/check-actions-ui.sh
native/ReservoirScope/check-action-comparison-layout.sh
native/ReservoirScope/check-action-inspector-layout.sh
native/ReservoirScope/check-shared-state-camera.sh
native/ReservoirScope/check-fill-watermark-memory.sh
native/ReservoirScope/check-evidence.sh
native/ReservoirScope/check-watermark-view.sh
python3 probes/reference_watermark_memory.py
python3 native/ReservoirScope/verify-app-identity.py
```

The build prints the completed app path in the local cache. The historical
[0.7.1 build receipt](build-receipt-0.7.1.json) records **179 targeted checks** (52 model,
42 evidence/source/replay and 85 view checks), 28 final offscreen images, and
packaged source/resource identity. The separate
[native inspection receipt](validation/0.7.1/runtime-qa.json) records the
recorded-data comparisons and UI inspection limits. No new M4 performance or
fresh live-ingestion qualification is implied.

The app's baseline remains a steward-side, read-only research viewer. Essentials
controls change only the local reconstruction. The separate native
state-action implementation and any being-runtime integration retain their own
owning-repository workflow; this main commit does not merge or deploy them.
