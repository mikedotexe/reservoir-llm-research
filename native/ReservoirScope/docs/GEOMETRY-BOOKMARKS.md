# Geometry bookmarks

This offline viewer reads explicitly exported `question-geometry-v1` packets.
See [current candidate status](../../../research/CURRENT-RELEASE.md) for the
qualified app identity. The October 7 source changes add the synthetic example
described below; earlier app copies do not gain it automatically. A fresh build
has its own package identity and does not establish human acceptance or a Being
deployment. The published 0.14.0 tag remains separate.

Choose **Geometry bookmarks**. Select **Load synthetic example**
for a self-contained first look, or **Open packet** to choose an exported JSON
file. Then choose a capture, prediction, comparison or revision in the left
column. A capture shows all 128 coordinates on a fixed −1…1 scale. Scrub the
recorded frames and expand **Exact selected coordinates** to inspect values.
Recorder gaps and both engine and wall clocks remain visible. Authored accounts
are displayed in full; sidebar excerpts are navigation only.

The bundled example uses invented text, clocks and coordinates. Its visible
synthetic label distinguishes it from an opened packet; the Minime owner field
is a schema label, not attribution to a Being. Two three-frame captures contain
128 coordinates and an explicit recorder gap. The comparison's RMS distance is
0.1, exceeding the invented prediction bound of 0.05; the revision records that
outcome without claiming a mechanism or experience. Loading the example runs the
same validation as opening a file and makes no model or live-source request.

Switching to another workspace and returning preserves the opened packet,
selected record, frame and coordinate disclosure in this window. The view keeps
the imported bytes in memory, even if the original file subsequently disappears.
It does not restore packets automatically after the window closes. Cancelling or
rejecting a replacement preserves the current reading position and origin label.
Missing or invalid bundled example data likewise leaves the prior packet intact.
The visible persistence note applies to both examples and opened packets: neither
adds a saved copy to the Library. A later window starts empty.

Opening a packet checks exact body and history hashes, record-specific fields,
source labels, dimensions, bounds, clocks and references. Numerical comparisons
are recomputed from the two retained mean vectors. Extra fields are rejected,
including a snapshot or substitute account attached to another kind of record.
A rejected file displays an error and leaves the previously opened packet visible.
Nothing follows source paths, polls live workspaces, calls a model or writes back.

Mean-state RMS distance can hide opposite movements and depends on sampling and
gaps. A threshold match does not establish mechanism, experience or return to an
identical physical state. Boot and node-layout identity remain unverified. Record
ordering does not establish a prospective prediction or previously unseen data;
hashes check bytes, not the producer's identity or provider delivery.

## Offline qualification

From the repository root, use fresh output directories:

```sh
bash native/ReservoirScope/check-geometry-bookmarks.sh research/outputs/geometry-model-checks
bash native/ReservoirScope/check-geometry-bookmark-presentation.sh research/outputs/geometry-presentation-checks
```

The model wrapper verifies the deterministic fixture provenance before checking
valid and malformed imports. The presentation wrapper renders synthetic views at
two desktop widths and checks removal/return with the source file absent, cancelled
selection, failed replacement and successful replacement. It also checks synthetic
origin changes, missing/damaged example resources and a new window's empty state.
These run through the `native-model` and `native-presentation` verification groups.
The fixtures and generator remain part of staged source identity. The resource
manifest additionally installs the exact Minime fixture as
`synthetic-geometry-example.json`; it does not regenerate or modify the fixture.

The [fixture description](../Tests/Fixtures/geometry-bookmarks/README.md) explains
what the synthetic packets establish. The earlier external reader/adapter workflow
remains a separate, explicitly supplied interoperability check. It is not required
for these offline viewer checks and is not run automatically.

Presented app interactions and a newcomer session remain separate from importer
checks and rendered screenshots. See the [original inquiry](../../../research/inquiries/2026-09-21-geometry-bookmarks.md)
for the research boundary and the independently owned runtime rollout requirements.

The app uses standard system window resizing, with no exact-size menu preset.
Automated geometry images use 1100×820 and 1380×820 view sizes. They do not establish
that a drag successfully resized a presented full app; report its actual observed
bounds separately when performing the interactive walkthrough.
