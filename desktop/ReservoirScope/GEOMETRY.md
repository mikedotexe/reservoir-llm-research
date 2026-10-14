# Geometry bookmarks in the Tauri preview

The Geometry workspace reads explicit local `question-geometry-v1` packets and a
separately labeled bundled synthetic example. It does not follow a historical
source path, poll a recorder, contact a model, write to a source workspace, or add
the opened packet to the Library. The accepted original bytes and reading
position remain in this window's memory until replacement or app exit.

Use **Load synthetic example** for the invented five-record workflow, or **Open
packet…** for a local export. A cancelled dialog, missing resource or invalid
replacement preserves the accepted packet, origin, selected record/frame,
coordinate and exact-table disclosure. A successful replacement resets those
positions and records the explicit operation's origin, even if its bytes match
the previous packet. Returning from another workspace retains the reading.
**Export original bytes…** writes the accepted byte snapshot without rebuilding
the JSON; the returned size and SHA-256 must match that snapshot.

## Validation and presentation

The Rust [core validator](crates/reservoir-core/src/geometry.rs) ports the
unchanged native
[GeometryBookmark.swift](../../native/ReservoirScope/Sources/ReservoirScope/GeometryBookmark.swift)
contract:

- The outer packet is nonempty and at most 4 MiB. Its exact nested body text must
  match its SHA-256. The format, owner and question identity are checked.
- A history contains at most 64 records. Every chain identity includes the
  previous ID, request-ID hash, request SHA-256 and exact record-body hash.
  Duplicate request IDs use canonical Unicode equivalence, matching Swift's
  string set. Source/request hash syntax includes Swift's fullwidth hex forms;
  computed body/chain hashes must still match the actual lowercase digest.
- Captures, predictions, comparisons and revisions have kind-specific fields.
  Extraneous fields are rejected, including unexpected null fields. References
  must resolve to the appropriate earlier records; a comparison's observation
  capture must follow its prediction record.
- At most four captures are retained. Each contains 1–61 frames with exactly
  128 finite values in `[-1, 1]`, a 1–60 second requested interval, the declared
  native-activation scope, the required source label and explicit unverified
  boot/node-layout identity. Engine clocks increase by at least 1000 ms; wall
  clocks increase. Duration cannot exceed the requested interval; capture time
  must be between the last wall clock and 12 seconds later.
- Recorder gaps above 1000 ms remain explicit. They are not interpolated.
  Comparisons require at least two frames per interval and strictly later
  observation engine/wall clocks. Mean-state RMS is independently recomputed
  from unweighted 128-coordinate means, with the native `1e-12` absolute
  tolerance and exact threshold decision.
- Capture notes, prediction expectations and revision text must be nonblank and
  at most 2000 UTF-8 bytes. Foundation's whitespace set, including U+200B, is
  matched explicitly. Authored text remains text; a comparison is not given an
  invented authored account.

The [backend](src-tauri/src/geometry.rs) validates before replacing its accepted
snapshot, serializes geometry file operations, rejects stale export handles and
converts `u64` clocks to decimal strings for IPC. The frontend never round-trips
clock identity through JavaScript numbers. UTC calendar display is omitted when
the retained clock exceeds the supported calendar range; exact milliseconds
remain visible.

The [workspace](src/GeometryWorkspace.tsx) shows a fixed `−1…+1` coordinate map,
ordinal retained-frame rows, explicit gaps, exact frame clocks, state RMS and an
accessible table of all 128 selected-frame coordinates. This map is not PCA,
an inferred eigenbasis, a connectivity map or anatomy. Reference buttons move
between the frozen records. File/body/source/request hashes are labeled
separately, and packet-authored limits are exposed verbatim as data.

## Evidence and limits

The bundled alias `synthetic-geometry-example.json` resolves through the existing
canonical resource catalog to
[minime-synthetic-geometry.json](../../native/ReservoirScope/Tests/Fixtures/geometry-bookmarks/minime-synthetic-geometry.json).
Its original SHA-256 is
`25ecc19605ee1bed307735f52668b817a854af98239018e74072c17ffbe92abc`.
The companion Astrid fixture is also tested. Both are generated fixtures with
invented coordinates, text and clocks. Owner/source fields demonstrate the
schema; they do not establish a Being's observation or producer interoperability.
See the retained [fixture provenance](../../native/ReservoirScope/Tests/Fixtures/geometry-bookmarks/README.md).

Hashes and replayed arithmetic establish internal consistency. They do not
authenticate a producer, establish boot/node layout, prove the result was
previously unseen, or test causality, mechanism or experience. Record order is
not proof of prospective prediction: a source interval may predate its stored
prediction. Sampling gaps affect the means, and opposite movements can cancel.

The qualified wire representation is the canonical snake_case JSON used by the
retained fixtures. Foundation's permissive JSON syntax and alternate decoder
key spellings are not claimed as portable compatibility; Rust can reject such
noncanonical packets. No original fixture, native source or frozen reference
manifest is rewritten.

## Checks executed for this source tranche

From `desktop/ReservoirScope`:

```sh
cargo test --locked --package reservoir-core --test geometry_conformance
cargo test --locked --package reservoir-scope-desktop geometry::tests
npm test -- src/geometryController.test.ts src/geometryView.test.tsx
```

Observed locally: **5 core tests**, **2 backend tests**, and **10 frontend tests**
passed. Core tests use both canonical fixtures and reseal semantic mutations,
including their dependent references, to test more than outer-hash rejection.
They cover changed vectors, bounds, owner/source identity, request collisions,
clock/restart/overlap conditions, reference ordering, RMS/threshold changes,
authored limits, excess fields, empty history and exact `u64::MAX` clocks.
Backend tests exercise accepted-state preservation, stale handles, operation
serialization and exact-byte export. Frontend tests exercise cancellation and
replacement state, response/export identity, accessible exact values, escaped
authored text, origin labels and hidden-view continuity.

The unchanged native checker was also run from the repository root:

```sh
bash native/ReservoirScope/check-geometry-bookmarks.sh
```

It verified the retained fixture generator hashes and passed **96 native
checks**. This host required the existing per-process Xcode SDK selection for
the Swift/backend invocations:

```sh
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk
```

These are source, backend and static-render/state checks. Packaged native dialog
interaction, keyboard/screen-reader behavior, viewport inspection, resource and
memory profiling, Windows/Linux execution and human acceptance remain separate
qualification gates. The tests do not establish live-producer interoperability.
Earlier package receipts retain their original meaning and are not refreshed by
this source change.
