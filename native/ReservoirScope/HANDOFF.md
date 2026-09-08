# Reservoir Scope handoff

The verified viewer snapshot is already on **main** in commit
`dc93adb85861bda82ee941a4abf2c67e6644fa33`. There is no pending viewer feature
branch to merge. This handoff is a documentation follow-up to that snapshot.

## Shared checkout

These paths expose the same files and Git history:

- On `volya`: `/Users/v/other/reservoir-llm-research`
- Through the Mac's mounted share:
  `/Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research`

SSH inspection confirmed the same main commit and native source hashes on both
paths. No Git remote is configured; agents using this shared folder do not need
a push or pull. Check the current branch and changes before starting:

```sh
git status --short --branch
git log -2 --oneline
```

Only the viewer and its selected supporting files are tracked. Other agents'
research notes and work remain untracked. Preserve them, stage explicit paths,
and coordinate before switching branches in this shared checkout. The
[version-control account](docs/VERSION-CONTROL.md) explains the initial scope.
Read the workspace's root AGENTS.md and CLAUDE.md for the broader research rules.

## What is ready

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
native/ReservoirScope/check-fill-watermark-memory.sh
native/ReservoirScope/check-evidence.sh
native/ReservoirScope/check-watermark-view.sh
python3 probes/reference_watermark_memory.py
python3 native/ReservoirScope/verify-app-identity.py
```

The build prints the completed app path in the local cache. The retained
[build receipt](build-receipt.json) records **179 targeted checks** (52 model,
42 evidence/source/replay and 85 view checks), 28 final offscreen images, and
packaged source/resource identity. The separate
[native inspection receipt](validation/0.7.1/runtime-qa.json) records the
recorded-data comparisons and UI inspection limits. No new M4 performance or
fresh live-ingestion qualification is implied.

The app remains a steward-side, read-only research viewer. The separate native
state-action implementation and any being-runtime integration retain their own
owning-repository workflow; this main commit does not merge or deploy them.
