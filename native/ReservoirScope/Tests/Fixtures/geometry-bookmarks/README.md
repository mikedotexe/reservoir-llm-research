# Synthetic geometry bookmark fixtures

These are generated viewer fixtures for `question-geometry-v1`. They do not come
from Astrid, Minime, a live recorder, the shared Rust reader, or the Minime adapter.
The `owner` and `source` fields are required schema labels. The generator never
opens those source paths. Success with these fixtures establishes local importer
and presentation behavior; it does not establish producer interoperability,
provider delivery, a prospective prediction, mechanism, or experience.

Each owner file contains capture A, prediction, capture B, comparison, and revision.
Each capture has three frames of 128 bounded coordinates and a visible two-second
recorder gap. Coordinates vary by node and stay fixed within an interval. Every
coordinate in B is 0.1 above A; the mean-state RMS distance is 0.1, so the prediction
bound of 0.05 is not met. Fixed clock values are invented and have no observation
date significance. Simple rational coordinates avoid platform-dependent sine
calculations. Authored text matches the synthetic workflow's wording.

`provenance.json` records the generator SHA-256, both fixture SHA-256 values, byte
counts, and the complete fixed numerical recipe. The hashes bind bytes, not origin.
The `source_sha256` and `request_sha256` values bind synthetic in-memory objects
constructed by `capture()` and `append()` in `generate.py`; no corresponding source
file is opened and no request is executed. The source references in the provenance
explain the fixture design, without claiming to authenticate a producer revision.

From the research repository root, verify the retained files without writing:

```sh
python3 -B native/ReservoirScope/Tests/Fixtures/geometry-bookmarks/generate.py --check
```

To regenerate exactly, use a new directory (the generator refuses an existing one):

```sh
python3 -B native/ReservoirScope/Tests/Fixtures/geometry-bookmarks/generate.py --out /tmp/geometry-fixtures-reproduction
cmp native/ReservoirScope/Tests/Fixtures/geometry-bookmarks/astrid-synthetic-geometry.json /tmp/geometry-fixtures-reproduction/astrid-synthetic-geometry.json
cmp native/ReservoirScope/Tests/Fixtures/geometry-bookmarks/minime-synthetic-geometry.json /tmp/geometry-fixtures-reproduction/minime-synthetic-geometry.json
cmp native/ReservoirScope/Tests/Fixtures/geometry-bookmarks/provenance.json /tmp/geometry-fixtures-reproduction/provenance.json
```

The importer checks take the Astrid and Minime fixture paths in that order. The
presentation checks take either fixture path, followed by a new output directory.
Use `native/ReservoirScope/Tests/geometry_bookmark_workflow.py` only as a separate
interoperability check with explicit candidate helper and adapter paths. These
retained fixtures neither require nor replace that cross-repository qualification.
