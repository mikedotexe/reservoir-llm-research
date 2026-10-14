# Preview 0.5.0 — packaged UI qualification status

Date: October 12, 2026. This is an agent execution account, not collaborator or
steward acceptance. The candidate is bound by `qualification.json` and
`archive-check.json` in this directory.

## Attempt and limitation

The app build completed. Opening its exact `.app` path through the native desktop
control tool was blocked: “The Mac is locked and automatic unlock could not unlock
it.” An unlock was requested. A second launch attempt after archive/resource verification returned the same locked-Mac result. No 0.5 UI interaction, rendering, native dialog,
upgrade, pause/navigation or context-recovery success is claimed from that attempt.

## Completed independent checks

- 127 frontend, 83 Rust core, 46 Rust desktop and 9 Python tests passed (265 total).
- Strict Clippy and the shipping TypeScript/Vite/Tauri build passed.
- 37 staged resource files exactly match the packaged files; the 34 canonical
  resource entries match their bound hashes and sizes.
- Independent unchanged Swift and Rust Observatory readers produced the same
  outputs from actual package resources as from the qualified staged resources.
- The archive contains the exact 41 regular app files, including their modes.

These checks establish their named scopes, not actual WebView or UI behavior.
The resumed 0.4 controller export/import/duplicate/reopen observations and discovered
upgrade defect are recorded in that build's separate October 12 supplements.

## Remaining checks for this exact candidate

1. Launch pristine package; enter Observatory without automatic playback or connection.
2. Explicitly open both recordings. Check first fill 67.31251478%, missing first rate,
   three distinct retained direction values, independent state row 0 / node 0
   0.35750484466552734 and ordinal-only clocks.
3. Scrub, play/pause, navigate away/return and confirm no stale advancement. Inspect
   node selection, exact values and fixed scales.
4. Observe idle frame counts, resize/orbit, context loss/recovery and exact-values
   fallback. Measure interaction and GPU/power/memory separately on qualification
   hardware; an idle draw count alone is not a power measurement.
5. Open Library using the pre-upgrade index without Refresh. Verify bundled controller
   becomes available and managed imports/recents remain intact.
6. Export selected reviewed case with the native Save dialog, cancel another export,
   reopen the derivative and verify with unchanged native Swift.
7. Check quit/relaunch, scale/accessibility and clean-machine installation.

Windows 11 x64, Ubuntu 24.04 x64 and minimum macOS 14 remain unexecuted. No prior build's
UI observations confer acceptance on this candidate.
