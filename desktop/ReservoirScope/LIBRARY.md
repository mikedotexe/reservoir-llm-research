# Tauri Library (0.7.0)

The Library is a local collection of explicitly imported numerical recordings,
explicitly saved fresh experiments and a read-only catalog of bundled examples. Its SQLite database is a rebuildable metadata
projection. A metadata row is not numerical verification, a saved journal receipt is
not proof of storage in another application, and a recorded model route is not
provider authentication. Opening a recording runs the existing Rust verifier against
its complete bounded byte snapshot before handing a new handle to the reader.

## Boundaries and supported imports

The native macOS app keeps its own store. Tauri uses its own app-data directory and
`library-v1` subdirectory. It does not scan the native app, sibling repositories,
live databases, journal directories, remembered external paths, or paths inside a
record. Import uses an explicit native file selection. Merely opening an external
recording, reviewed case, or geometry packet does not add it to the Library.

Managed import positively allows only the numerical families supported by this
release: a stage `recipeVersion: essentials-v1` with no overriding `format`,
`essentials-exploration-v1`, `essentials-actions-v1/v2/v3`, and the separate
`essentials-regulation-v1` controller study. Unknown versions,
invalid JSON, case catalogs, and geometry packets cannot enter through import—even
when the core verifier can pass a different integrity scope for that format. A
full numerical verification failure publishes nothing. Imports retain the existing
256 MiB per-record bound; that bound is not a cap on Library size.

The 22-entry authored `examples-index.json` controls catalog order: guided,
model, comparison, preparation; then each authored order and stable catalog ID.
All 22 entries are bundled in 0.5, including the separate controller study,
quiet/active observation comparisons and four preparation recordings. Controller
entries use the `regulation` family and `numerical` source filters; they have no
language provider. Resources are loaded through the build's filename allowlist and SHA-256 manifest.
Entries authored in the catalog but absent from this build are shown as **not
included in this build**, with no verifier or resource coverage claimed. Other
missing or hash-mismatched resources have distinct unreadable diagnostics. Catalog
open verifies the immutable source again and never creates a managed copy.

## Publication and identity

The application writes these files beneath its marked store:

```
owner.json
records/<sha256>.json
metadata/<sha256>.json
index.sqlite3
index.sqlite3-wal / index.sqlite3-shm  (when SQLite uses them)
index-backup-*.sqlite3               (after explicit rebuild)
```

`records/` contains exact original bytes: whitespace, unknown fields, large integers,
and historical encodings are not reserialized. The SHA-256 of those bytes is the
managed identity. An identical import retains the first copy, name and local save
time and reports a duplicate. Different bytes with the same embedded ID retain two
entries. No operation replaces a recording by its embedded identity.

Publication writes a same-directory temporary file, flushes it, verifies a bounded
readback, publishes without overwriting an existing destination, and verifies the
final bytes. Unix also flushes the publication directory. Only then are local
metadata and the SQLite projection updated. A damaged conflicting file at an
existing content address is never overwritten. If an index update fails after
publication, the result says the original record survived and provides its opaque
identity; rebuild can recover its metadata. Local metadata failure also preserves
the recording and is visible as a diagnostic. Tests exercise these failure
boundaries, not sudden-power-loss durability on every filesystem.

The local sidecar stores the original filename, SHA identity, and local import/save
time. That time is bookkeeping, not an authenticated historical event time. Missing
or damaged sidecars leave the record available for explicit verification and show an
unknown local date. The app rejects unmarked nonempty roots, wrong owner markers,
symlink roots/directories/files and non-regular index files. SQLite opens with
NOFOLLOW after canonicalizing the validated owned directory (necessary for macOS's
system `/var` alias). Neither sidecar paths nor frontend strings authorize filesystem
navigation. Reader requests use an opaque SHA or catalog ID.

## Metadata search and coverage

Search matches a Unicode-lowercased literal substring of title, filename, family,
format, stage, configured backend/model, decimal seed, Library identity and retained
embedded identity. `%`, `_`, quotes and SQL syntax are ordinary search text. Seed
values remain decimal strings in IPC, including `18446744073709551615`.

Filters cover origin, family, recorded generation route, recorded outcome, recently
opened, and entries needing attention. The route is separate from configured backend:

- **Fixed replay** is the declared action-comparison mode, including its historical
  default. An unused Ollama configuration does not turn a tape into a model reply.
- **Model/scripted** on independent comparisons requires a retained started request
  and the corresponding configured route. On stage records it follows consistent
  retained turn backend labels.
- **Unknown** includes records with no turn/request evidence, exploration, and
  unsupported or ambiguous headers. These remain visible.

Header projection follows the verifier’s exact family dispatch. Ignored fields from
a different family remain in the original bytes and cannot promote metadata or
prevent opening an otherwise valid imported record.

These tags describe retained metadata. Opening checks its mechanical consistency;
it does not authenticate an external service or establish that a failed request
produced a journal. The reader retains detailed request, tape and provider receipts.
Search does not index journal bodies, execute text, or follow historical links.

Bundled entries precede managed entries in authored order. Managed entries sort by
local import time descending, then opaque ID. Recents sort by local successful-open
time and ID. Recents persist only for Library/bundled opens, and preserve their times
through a healthy rebuild. Corrupt-index recovery explicitly reports when prior
recents could not be recovered. It never restores external temporary viewers.

Each query returns a total, offset, page limit and `hasMore`; IPC permits up to 100
rows per page and the UI pages by 50. The viewport renders only visible rows plus
overscan. There is no 500-result or 5,000-file stop. The scanner enumerates the flat
owned `records` directory completely, retains diagnostics for unexpected entries,
and inspects own sidecars for missing records. It does not recurse through arbitrary
paths. Distinct non-UTF-8 unexpected filenames keep distinct diagnostic identities.

Coverage is always visible: not scanned, running, complete, interrupted, or failed.
Scan counts cover managed directory entries and resulting managed rows; catalog
attention rows are separately visible through the normal query/filter. A scan's
metadata transaction gives readers the previous committed projection until completion
or cancellation. Cancellation commits the partial work and says coverage is
incomplete. A restart seeing a persisted running marker reports an interrupted scan.
Previously indexed missing files stay visible on refresh; a rebuild can recover a
missing-file row from its surviving sidecar. If both original and sidecar are gone,
a completely rebuilt index cannot reconstruct that deleted identity.

Import and scan mutations are serialized. Metadata query and reader handles stay
independent. A failed query retains previous frontend results with its diagnostic,
never an invented empty-success state. A failed scan retains incomplete coverage.
Rebuild archives only the owned disposable database files, preserves scientific
files, and reconstructs the metadata index. A non-regular index requires attention
and is not moved or followed. Archived damaged indexes remain available for
inspection; this release does not silently purge them.

## Qualification and limits

Implementation is in `src-tauri/src/library.rs`, its storage tests in
`src-tauri/src/library_tests.rs`, and the frontend in `src/LibraryView.tsx`,
`libraryApi.ts`, `libraryTypes.ts`, `libraryViewModel.ts`, and `library.css`.
`libraryViewModel.test.ts` checks pagination/virtual window math, evidence labels,
explicit desktop-only IPC, and initial incomplete presentation. Its IPC mock is a
unit-test fixture only; browser preview has no fake storage backend.

Run from `desktop/ReservoirScope`:

```sh
cargo test --locked -p reservoir-scope-desktop library::tests -- --nocapture
cargo clippy --locked -p reservoir-scope-desktop --all-targets -- -D warnings
npm test
npm run build
```

On the qualification Mac, Rust commands use these per-process SDK selectors:

```sh
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk \
cargo test --locked -p reservoir-scope-desktop library::tests -- --nocapture
```

Storage fixtures are temporary synthetic recordings or tracked bundled examples;
there are no provider requests or live-store reads. Coverage includes a 5,001-file
scan with pagination over every row, cancellation/restart, corrupt-index rebuild,
index-publication failure, exact-byte/embedded-ID distinctions, UInt64 seed retention,
missing/damaged/unsupported/unreadable records, symlink refusal, initialization races,
persistent recents, and wrong-scope rejection with otherwise verifier-passing case
and geometry packets. A retained canonical H record with an unused Ollama config
must remain fixed replay. Cross-family ignored fields also retain their bytes without
becoming backend/stage/outcome metadata. Non-UTF-8 identity tests exercise the
scanner’s byte-derived identity helper; APFS rejects creating those filenames, so
this is not a macOS filesystem roundtrip claim. These tests do not establish Windows/Linux package or
filesystem qualification, full accessibility, live generation, or sustained-session
crash recovery; separate release evidence owns those claims.

SQLite uses the pinned Rust package
[rusqlite 0.40.2](https://docs.rs/crate/rusqlite/0.40.2) with its bundled SQLite
build. Its [OpenFlags API](https://docs.rs/rusqlite/0.40.2/rusqlite/struct.OpenFlags.html)
documents NOFOLLOW. SQLite is metadata infrastructure here, never a replacement
format for the portable recordings.

## Bundled catalog upgrade repair (0.5)

The first query compares the stored catalog identity with the metadata schema, package
version and compiled resource-index hash. If it changed, a transaction replaces only
bundled rows and updates the identity marker. It preserves managed bytes, managed
entries and the separate recents table. Interrupted catalog publication rolls back;
an upgrade failure is visible rather than silently retaining a newly successful marker.
The query and scan paths share the index gate.

This repairs the 0.4 behavior where a populated older index could keep new examples
marked not included. A regression covers the controller metadata, retired entries,
managed bytes and recents. Packaged upgrade observations are recorded separately.


## Fresh created records (0.7)

Save to Library uses the same verified immutable publication boundary as import. New
local sidecars retain `origin: created`; existing import sidecars without the field
keep their historical managed meaning. Created here has its own filter, and refresh
or index rebuild preserves that origin. Duplicate bytes preserve the first entry's
provenance, filename and local date. Local bookkeeping never alters portable bytes.

A missing/damaged sidecar cannot prove where a file originated. Such files retain the
legacy managed grouping, show origin unavailable and an unknown date, and keep a
visible metadata diagnostic. The grouped filter is labeled Imported / other managed.
A reader opened from that group is labeled Managed Library, without claiming that
missing creation provenance was recovered.

Finite-session checkpoints and actual journal files live separately under
`sessions-v1`; they are not Library imports. The fresh session's checkpoint step,
Library save and journal eligibility are separate statuses. See
[the fresh session/save contract](FRESH-EXPERIMENTS.md).
