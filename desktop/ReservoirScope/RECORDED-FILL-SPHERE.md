# Recorded fill sphere

`RecordedFillSphere` displays an explicit retained percentage as a concentric
sphere using the native app's volume mapping:

```text
radius / full radius = cbrt(fillPercent / 100)
```

The unchanged native references are
[`ReservoirScene.swift`](../../native/ReservoirScope/Sources/ReservoirScope/ReservoirScene.swift)
(`fillRadius`, `makeFill`, `ReferenceLens.radius`) and
[`ReferenceZones.swift`](../../native/ReservoirScope/Sources/ReservoirScope/ReferenceZones.swift).
A cutaway exposes the radial reference circles. At 12.5% the radius is one half;
a 68% sphere does not have a radius of 0.68. This is a scalar volume illustration,
not a reconstructed activation geometry or a physical fluid simulation.

## Input and interpretation

```tsx
<RecordedFillSphere
  sample={{
    fillPercent: retainedFill,
    provenance: retainedSourceLabel,
    sourceTimeLabel: retainedTimeOrPositionLabel, // optional, displayed verbatim
  }}
  references={retainedReferenceConfiguration} // optional; no defaults
  active={workspaceIsActive}
  tableOnly={exactValuesOnly}
/>
```

A sample may be `null`. `FillReferences` contains `shelfMinPercent`,
`targetPercent`, `shelfMaxPercent`, `strongRailPercent`, `warningRailPercent` and
`provenance`. The containing workspace is responsible for backend-verified
identity, selection and source association. This component performs no file,
network, history or live-system reads.

All values must be finite and in 0–100%. The reference configuration must preserve
that declared threshold ordering. Missing or invalid fill produces a distinct
no-data view; it is never silently clamped or displayed as zero. Actual zero is a
valid retained measurement. Missing/invalid reference metadata produces no rings.
The native 58/68/72/74/78 references appear only if those values are supplied.
No historical controller stage, mode, safety or subjective comfort is inferred.

The DOM always retains the exact JavaScript numeric value, provenance, supplied
time/position label, computed radius, reference table and interpretation limits.
It constructs no timestamp. The large percentage is explicitly rounded to two
decimals; the exact percentage remains selectable below. Normal JavaScript
binary64 decoding remains the enclosing IPC contract, not a new decimal-text
preservation guarantee. Missing time is labeled “Not supplied.”

The image shows the latest supplied measurement immediately, with no smoothing,
interpolation, automatic playback, watermarks or manufactured intermediate values.
Changing provenance alone does not trigger a graphics redraw.

## Rendering and resource bounds

The renderer owns one fresh WebGL2 canvas/context. Three.js uses a static 64×32
sphere, 96-segment cut face, and a shared 192-segment reference-circle geometry.
Fill changes update scales; reference changes update scales/colors/visibility.
There are no textures, shadow maps, postprocessing passes or render targets.
The component has a large responsive canvas but shares the existing surface
raster policy: DPR at most 2, at most 1,000,000 physical pixels, and each dimension
bounded by both 4096 and the context's `MAX_RENDERBUFFER_SIZE`.

The pixel cap is **per canvas**, not a total application memory/VRAM budget.
Antialiasing and implementation-owned buffers can consume additional memory.
`powerPreference: 'low-power'` is a request; this work does not establish which
GPU a system WebView selects, energy consumption or contention with a local model.
Hardware acceleration is not disabled.

The shared scheduler coalesces input, resize and recovery into one pending frame.
It schedules no idle follow-up frame. Hidden documents, offscreen canvases and
lost contexts suspend drawing, retaining only the latest pending update.
IntersectionObserver edge contact uses `isIntersecting` so threshold-zero entry
cannot leave the scene permanently suppressed. Inactive workspaces, no-data and
explicit `tableOnly` mode dispose the owned context rather than drawing a hidden
sphere. Element/window/DPR changes resize only when actual dimensions change.

Context loss hides the image while leaving exact evidence available. Restoration
reapplies the clear color, checks the extension again, rebuilds size state and
requests one latest frame. Explicit recovery controls are available only when the
WebView exposes the context-loss extension. Cleanup cancels pending frames,
removes listeners, disconnects observers, disposes every geometry/material and
renderer, and requests release of the owned context when the extension allows it.
React StrictMode remounts use new canvases.

## Focused checks and limits

Run from `desktop/ReservoirScope`:

```sh
npm test -- src/fillSphereMath.test.ts src/fillSpherePolicy.test.ts src/RecordedFillSphere.test.tsx
npm run build
```

The 13 focused tests cover volume recovery across 401 percentages, native
reference values, invalid/no-data boundaries, custom reference metadata,
coalescing/latest-state behavior, active/document/viewport/context suspension,
post-disposal suppression, raster bounds, exact accessible values, source text
escaping, and inactive/table-only views. These are CPU/policy/static-render tests;
they do not demonstrate GPU pixels, restoration, memory reclamation or native
WebView accessibility behavior.

Actual packaged rendering, context loss/restoration, high-DPI changes,
minimize/restore/sleep/wake, cross-workspace memory behavior, screen-reader use,
battery/energy, sustained-session GPU measurements and Windows/Linux qualification
must be recorded separately by the packaging/UI qualification owner. No new GPU,
power, performance or live scientific measurements are claimed here.
