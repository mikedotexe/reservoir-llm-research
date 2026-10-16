# Frozen Observatory evidence readers

This module reads the native application's existing frozen evidence shapes. It
checks structure, finite values, bounds and retained hash bindings. It does not
re-run the historical engine, prove causal effects, inspect a live system or add
these captures to the experiment verifier's numerical-replay scope.

The desktop adapter is `src-tauri/src/observatory.rs`; its renderer contract is
`src/observatoryTypes.ts`. Both tracks remain independent. A shared inspection
workspace does not establish a cross-track timestamp or event join.

## Retained inputs and exact meaning

| Track | Frozen resources | Retained coverage | Inspection clock |
| --- | --- | --- | --- |
| History | `data.json` | 507 observations, 0 through 1198.51497746 elapsed seconds | Original `t_s`; playback holds the last recorded observation |
| Native ESN states | `state-replay.json`, `state-replay.bin`, `state-geometry.json` | 1024 rows × 128 Float32 coordinates | Ordinal row 0–1023, oldest to newest |

All four desktop resources are read through `resources::catalog_bytes`. Expected
hashes and byte lengths come from the resource index compiled into the executable.
The adapter never follows source paths embedded in a capture. Its reads are
limited to these four allowlisted filenames; corruption in one track is reported
without disabling the independent valid track.

History retains fill percentages, three sensory-covariance **direction estimates
in their recorded slot order**, and optional metrics. Those three estimates are
not a certified sorted eigenspectrum, tracked eigenmodes or three authenticated
spatial directions. The remaining five directions and all their vectors are
absent. The separately retained `esn_cov_lambda1` concerns native ESN state
covariance. It is distinct from the sensory estimates and from recurrent-weight
spectral radius. `esn_lambda` is the recorded RLS forgetting coefficient.

`fill_rate_pct_per_s` is an already retained backward finite difference between
consecutive recorded fills. It is **not** the engine's smoothed `dfill_dt`; this
reader does not recalculate or substitute it. Missing measurements and identifiers
stay null. Native signed integer session/source identities cross JavaScript IPC as
exact decimal strings.

The five reference bands (58, 68, 72, 74 and 78 percent), optional hysteresis
thresholds (60 and 71.5), status and explanation are retained configuration. They
do not establish historical per-tick controller stages or subjective comfort.
The separate controller snapshot inside `data.json` is not projected onto the
historical timeline.

Historical UTC strings preserve the original session-start conversion. Per
`TRACE.md` §5, the monotonic and database wall-clock starts were sampled separately:
an unrecorded baseline offset and subsequent clock/logging uncertainty remain.
The elapsed timeline is useful; precise alignment with another record is not
established. The history contains no explicit timed-gap annotations. The reader
exposes each exact elapsed interval and breaks at session changes. It does not
invent a gap threshold or interpret no break as complete coverage. Missing
individual metrics remain gaps for their own plot. This matches the native
history's elapsed-clock/hold-last policy rather than transferring the unrelated
GeometryBookmark packet format's gap rules into this capture.

Retained activations are decoded from row-major little-endian Float32 bytes and
promoted exactly to Float64. Their values are bounded to −1…1. There are no per-row
timestamps, measured cadence, paired fill, authenticated node-layout, boot/session
or successful-step identifiers. A selected coordinate trace uses ordinal rows.
Any playback rows/second setting and any drawn node arrangement are presentation
choices, not measured cadence or neuron positions.

The geometry rows are retained derived values bound to the exact original state
bytes by the replay manifest and frozen geometry source hash. The PCA fit is
retrospective over the full captured window. This reader neither refits the basis
nor claims that it was available at each historical row. The source's bracketed
read consistency limitation remains disclosed; no transactional dump-generation
pairing is inferred.

### Reference fields and the full-capture spectrum (0.22)

For each retained state row, Rust computes magnitude `abs(x)`, deviation `x − mean`,
and ordered Float64 dot-product scores against the three retained frozen
components. For a selected set of components, reconstruction is the sum of
`score × component`; the reference mean is **not** added back. Residual is deviation
minus that selected contribution. Their energies are sums of squared coordinates,
not sensory fill, prediction error or a causal attribution. Reversing a component
and its score leaves its reconstructed contribution unchanged.

Signed activation uses the fixed display range −1…1, magnitude 0…1, and deviation,
reconstruction and residual −2…2. Out-of-range counts describe those drawing
limits; the exact returned values are never clipped or rescaled. The IPC frame
contains the four selections PC1, PC2, PC3 and all three (zero-based mode indexes
in the contract). The pure core helper supports all eight subsets, including none.
It does not infer spatial adjacency, a clock, fill or live reference compatibility.

These recomputed `scores` and energies remain distinct from the existing `pc`,
RMS and distance fields retained in the geometry JSON. Both are tied to the exact
activation bytes and frozen reference, but one is a current reader calculation
and the other is saved metadata.

The state track summary exposes all 128 retained eigenvalues and their variance
fractions once, with the retained/omitted fractions, total sample variance,
`rows − 1` covariance denominator, frozen fit scope and geometry SHA-256. This is
the centered sample covariance fitted retrospectively to all 1,024 saved rows.
It is constant across the replay and separate from the three sensory-direction
estimates in history. Only three component vectors were retained; the other 125
eigenvalues do not provide corresponding reconstruction vectors.

## Validation and supported bounds

- Historical and geometry JSON: nonempty, at most 2 MiB each. Replay manifest:
  nonempty, at most 16 KiB. Binary: at most 524,288 bytes.
- Historical schema `reservoir_3d_evidence`, version 1; nonempty observations;
  strictly increasing finite elapsed seconds; valid calendar/RFC3339-shaped UTC
  timestamps; finite fill in 0–100%; exactly three finite spectral slots;
  optional numeric values finite when present. Spectral slots are never sorted.
- Ordered finite reference bands in 0–100%; optional band values finite in the
  same range. Unneeded snapshot/configuration fields are not promoted to samples.
- State schemas `reservoir.state_replay.v1` and `reservoir.state_geometry.v1`;
  exactly 128 dimensions, 2–1024 rows; exact row-major `<f4` layout and fixed
  `state-replay.bin` basename; exact byte count and hashes.
- State manifest requires oldest-to-newest order, no per-row timestamps or paired
  fill, and null/absent node-layout identity. Geometry timing must agree. Capture
  observation labels must match across the manifest and geometry.
- Geometry row indexes are contiguous; retained PCA dimensions agree; all exposed
  coordinates, norms and numeric basis values are finite. Distances are
  nonnegative. This validates the retained shape; it is not a reconstruction of
  the numerical fit.
- Reference components must be orthonormal within the native field routine's
  absolute 1e-5 bound. State spectrum values must be nonnegative and descending;
  variance shares, total variance, retained/omitted fractions and sample
  denominator must agree within absolute 1e-10 (total variance additionally scales
  that bound by `max(total, 1)`). These checks do not refit the covariance matrix.

The bounded reader rejects unsupported shapes explicitly. It does not silently
truncate larger captures or treat unfamiliar clock metadata as known. Optional
historical definitions and geometry missing-field lists preserve native missing
or null compatibility. The module is not wired into `reservoir-core verify` as a
simulation record family.

## Backend ownership and IPC

`ObservatoryState` holds at most four opaque sessions, each containing only the
validated snapshots loaded at open time. Opens are serialized by a guard and run
in a blocking worker. Closing a handle is idempotent. Later reads of a closed or
unknown handle fail. In-flight bounded reads retain their own immutable snapshot;
renderer generation/request guards prevent late responses from becoming current.

- `open_observatory(requestId)` returns a handle, available track metadata and
  per-track diagnostics. Even total failure is inspectable through diagnostics.
- `get_observatory_timeline(requestId, observatoryId, trackId, start, limit,
  nodeIndex?)` returns 1–256 requested rows, explicit total/next-page coverage,
  no downsampling and no hidden total limit. A start at total returns an empty
  final page; an out-of-range start is rejected. Optional node index 0–127 adds
  one coordinate to each state point; history rejects node requests.
- `get_observatory_frame(requestId, observatoryId, trackId, index)` returns one
  history observation or exactly 128 retained activations with its geometry.
  State frames also carry bounded magnitude/deviation arrays and four selected
  reconstruction/residual pairs; static basis matrices and the full capture are
  not repeated per frame. It never attaches history fill or UTC to a state row.
- `seek_observatory(requestId, observatoryId, trackId, position, mode)` supports
  `floor` (hold-last) and `nearest` (earlier observation wins a midpoint).
  Positions clamp to endpoints; nonfinite positions and unknown modes fail.
  History position means elapsed seconds; state position means ordinal row.
- `close_observatory(observatoryId)` releases the backend snapshot.

Only bounded pages, small metadata and one selected activation vector cross IPC;
the full 1024×128 matrix stays backend-owned. There is no import, export, model
request or live-data route in this interface.

## Checks and independent native oracle

Focused tests cover all retained coordinates, exact float decoding, finite/range
and shape errors, rebound corruption, binary length and hash mismatch, schema
versions, ordering, missingness, exact integer identifiers, session breaks,
seek endpoints/midpoints, complete paginated coverage, unavailable independent
tracks, handle limits and idempotent close. Seven core tests and six adapter tests
passed in the initial focused runs.

Commands from the repository root (this host's SDK variables only apply to each
command; no global SDK setting is changed):

```sh
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk cargo test --manifest-path desktop/ReservoirScope/Cargo.toml -p reservoir-core --locked --test observatory
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk cargo test --manifest-path desktop/ReservoirScope/Cargo.toml -p reservoir-scope-desktop --locked observatory::tests
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk cargo clippy --manifest-path desktop/ReservoirScope/Cargo.toml --locked -p reservoir-core -p reservoir-scope-desktop --all-targets -- -D warnings
```

The independent oracle compiles the **unchanged** native
`native/ReservoirScope/Sources/ReservoirScope/Evidence.swift` with a small output
wrapper. A `Bundle.module` stand-in supplies only the generated SwiftPM accessor;
the actual native loader receives explicit local resource URLs. No native decode
or validation function is replaced. The Rust example emits the same compact
comparison representation.

```sh
mkdir -p desktop/ReservoirScope/target/observatory-oracle
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk xcrun swiftc -parse-as-library native/ReservoirScope/Sources/ReservoirScope/Evidence.swift desktop/ReservoirScope/crates/reservoir-core/tests/support/observatory_oracle.swift -o desktop/ReservoirScope/target/observatory-oracle/native-observatory-oracle
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk cargo build --manifest-path desktop/ReservoirScope/Cargo.toml --locked -p reservoir-core --example observatory_oracle
python3 desktop/ReservoirScope/crates/reservoir-core/tests/support/check_observatory_oracles.py --swift-oracle desktop/ReservoirScope/target/observatory-oracle/native-observatory-oracle --rust-oracle desktop/ReservoirScope/target/debug/examples/observatory_oracle --receipt desktop/ReservoirScope/validation/2026-10-12-observatory-oracles.json
```

The script refuses to replace an existing receipt; use a distinct filename for a
new source revision or rerun. Numeric digests encode presence markers plus every
Float64 bit pattern in little-endian order. They cover all history numeric values,
all 131,072 activations, every exposed geometry value and the retained bands.
Historical UTC/session/source identities are compared separately and exactly.
Six mutation cases require both actual readers to reject with exit status 1,
including a nonfinite activation whose raw and geometry hashes are rebound so
that the value check itself is exercised. The receipt retains source, resource
and executable identities. This is reader conformance, not full M3 qualification,
Windows/Linux execution evidence or evidence about a current live being.

The 0.22 field oracle separately compiles unchanged `StateSurface.swift` with
`validation/2026-10-15-observatory-fields-0.22.0/StateFieldsOracle.swift`. Its saved
core fixture contains three synthetic cases and captured rows 0, 1, 511 and 1023,
each evaluated with all eight mode subsets (56 selections). Core tests compare
every vector, score, energy and out-of-range count against that independent native
output within 1e-12; invariants cover reconstruction/residual addition, sign
invariance, empty selections, exact unclipped values and invalid references.
`native-field-oracle-01.json` retains source, inputs, binary and fixture identities.
The first focused Rust attempt is preserved as a compile failure from two iterator
reference mismatches; the corrected focused attempt has its own receipt.
