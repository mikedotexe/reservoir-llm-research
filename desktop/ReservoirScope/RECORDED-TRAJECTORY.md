# Retained state trajectory

The Observatory's **128-node replay** pairs the signed activation surface with a
selectable two-dimensional view of the retained PCA coordinates. Choose PC1/PC2,
PC1/PC3 or PC2/PC3, then click a retained point or use the row controls. Both views
inspect the same accepted row. A manual selection pauses playback; a failed or stale
read cannot replace the last accepted row.

The three coordinates come from the bundled `state-geometry.json`, bound by the
backend to the original Float32 activation bytes. They use a frozen basis fitted
retrospectively to the full 1,024-row capture. The interface does not refit that
basis, infer online availability or introduce new measurements.

## Reading the view

- Axes use one symmetric range derived from all three retained coordinates over
  the entire capture. The range stays fixed across row selection and projection
  changes. Equal axis units preserve the selected projection's coordinate scale.
- Each point selects an actual retained ordinal. Lines connect successive retained
  rows to show order; they do not interpolate states or establish a continuous path.
  Overlapping projected points may represent different 128-coordinate states; use
  the row controls to inspect them individually.
- The selected marker and exact PC values belong to the same row as the surface and
  coordinate table. Exact reconstruction metrics remain available in a disclosure.
- Playback rate is a viewing choice. Per-row timestamps, measured cadence and paired
  fill measurements are unavailable. The clocked fill history is a separate capture.
- A projection is not the complete phase space. Apparent crossings do not establish
  recurrence, causation, speed or physical motion.

The trajectory requires complete, ordered, finite source coverage. A partial or
malformed timeline does not produce an apparently complete plot. Exact selected
frames remain available if timeline retrieval fails.

## Rendering and accessibility

The trajectory uses SVG and memoized projection geometry; it creates no extra WebGL
context or continuous animation timer. The existing surface retains its bounded
pixels, event-driven scheduler and exact-value fallback. These implementation choices
do not establish measured GPU or power savings.

Pointer picking has keyboard and row-control alternatives. Exact coordinates are
available without a graphics context. Hiding 3D leaves the trajectory usable; it
requires no WebGL. Screen-reader and broader platform acceptance remain separate
from source tests and scoped native checks.

The original 0.21 trajectory tranche did not add reference-field or spectrum
inspection. The subsequent [recorded state fields and spectrum](RECORDED-STATE-FIELDS.md)
guide describes the 0.22 field controls and full-capture spectrum, including the
distinction between per-row energy and capture-wide variance. Live feeds and
synchronization with the separate fill history remain outside these views.
