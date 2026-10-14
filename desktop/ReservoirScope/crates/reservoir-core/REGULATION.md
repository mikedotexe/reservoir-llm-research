# Controller teaching record

`regulation.rs` verifies `essentials-regulation-v1`, executes its fixed finite recipe
one paired step at a time, and exposes typed, cursor-bound window evidence. This is the separate field-only controller example
from `essentials/regulation/RegulationExample.swift`, not stage H, a live controller,
a reservoir run, a journal feedback loop, or a sustained-session checkpoint format.

The declared fixture is fixed: `uniform66-seed42-field98-v1`, field seed 98, input
seed 42, 600 steps at `dt = 1/3`, initial retention 0.955, target reduced fill 68%,
and evaluation steps 301–600. Specification fields omitted or set to JSON null use
the native defaults. Alternate seeds, clocks, targets and evaluation windows fail
validation. Study notes may vary; each must contain 1–4096 UTF-8 bytes. Native
validation permits whitespace-only nonempty notes, which this port also permits.

Each step consumes 66 signed SplitMix64 samples. Both fields receive that full
synthetic vector and the same seed-derived projection. There are no journal-return
coordinates and no reservoir state. The baseline field keeps retention 0.955. The
regulated field uses the controller's current retention, observes its own spectrum
and reduced fill, and records a new output that takes effect on the **next** step.
Reduced fill uses all 32 sensory eigenvalues; the displayed entropy/shares summarize
the leading eight. These are distinct quantities.

## Fresh finite execution

`RegulationSession::new(specification)` validates the same fixed specification as the
record verifier and initializes current fields, reduced-fill estimators, controller
and input RNG. Creation does not precompute observations. The core API is:

| Method | Contract |
| --- | --- |
| `specification()` | Borrow the accepted fixed recipe and study notes |
| `frames()` | Borrow only paired observations already committed by `advance()` |
| `projection_weights()` | Borrow the static row-major 32×66 seed-derived projection |
| `advance()` | Compute and commit exactly one pair, or return an error without changing accepted state |
| `window_evidence(cursor_step)` | Derive evidence from the requested retained prefix; future cursors cannot reveal uncomputed frames |
| `is_complete()` | True only after 600 paired observations |
| `completed_record()` | Clone an explicit original-format snapshot only at completion; every prefix returns an error |

Each advance copies only the current fixed-size numerical state, computes both
fields on that candidate, then publishes the pair and updated state together. If
the regulated-field computation fails after the baseline computation, neither field,
the RNG, fills, controller, nor frame history changes. Reading, pausing between
calls, and changing the viewer cursor do not consume a step. Advancing after step
600 fails without altering the completed session. The existing batch
`RegulationExampleRecord::generate` now uses this same incremental mechanism.

The core owns no pacing, filesystem, pause/stop lifecycle or recovery checkpoint.
A desktop caller must enforce its own terminal stop policy. It may retain separate
partial-progress metadata, but this API never fabricates a partial
`essentials-regulation-v1` record, whole-window summary, successful save, or resumable
checkpoint. A stopped prefix cannot be exported in that portable format. At step
600 the complete snapshot is eligible for the caller's actual save/readback flow;
creating the in-memory record is not evidence that it was saved.

The 32 retained `spectral.fieldVector` values are the common input after lane-scaled
tanh activation, seeded projection, division by `sqrt(66)` and RMS normalization
(or zeros when too small). They are distinct from the 2112 static projection
weights, covariance eigenvalues and any recurrent reservoir state. Both arms have
the same projected field vector for a given input; their covariance history,
retention and derived spectrum/fill may differ.

## Verification

A valid record retains all 600 paired observations. A stopped, truncated or otherwise
partial recording is not accepted under this format. The verifier checks dimensions,
finite values, contiguous steps, baseline/regulated controller presence, seeded
projection, deterministic common inputs, both spectra/covariances, reduced fill,
retention used, controller error/integral/requested/applied retention, and the fixed
whole-window summary. `checked_steps()` returns 1200 after successful verification,
counting both arms; there are no language turns.

The tolerance split follows the Swift source exactly:

- Projection weights compare exactly against their seeded values.
- Clock, common input, fill, retention, controller fields and summary scalars use
  `abs(actual - expected) <= 1e-8 * max(1, abs(expected))`.
- Spectral values, covariance, projected field, summary and basis validation use
  the native action verifier's `2e-7` relative/absolute floor. Basis checks use unit
  norms, covariance residuals and pairwise orthogonality, accepting sign/gauge
  differences rather than comparing LAPACK and nalgebra basis bytes.
- Spectrum shape requires 32 nonnegative descending values with the native `1e-8`
  ordering allowance; vectors and covariances must have their exact dimensions.

The whole-window summary is recomputed from the retained frames after their
verification, matching Swift. Verification replays one expected step at a time,
which avoids allocating a second complete 600-frame record. It does not trust a
stored aggregate in place of checking the trajectory. An aggregate improvement in
this fixed synthetic fixture is not a claim about other inputs, target attainment,
causality in a live being, or subjective experience.

## Typed reader contract and prefix evidence

Public serde camelCase types are `RegulationExampleSpecification`,
`RegulationArmFrame`, `RegulationExampleFrame`, `RegulationExampleSummary`,
`RegulationExampleRecord`, and `RegulationWindowEvidence`. All derive Clone.

The record has `format`, `specification`, `projectionWeights`, `frames`, and `summary`.
Each frame contains `step`, `time`, shared `input`, and `baseline`/`regulated` arms.
Each arm has `spectral`, `fillPercent`, `retentionUsed`, and optional `control`.
The baseline has no control; the regulated arm requires it.

Call `verify()` before exposing a record in the reader. Then call
`record.window_evidence(cursor_step)` or
`RegulationWindowEvidence::evaluate(&record, cursor_step)` for each cursor change:

| Cursor | Evidence |
| --- | --- |
| 0–300 | None: evaluation has not begun |
| 301 | One paired observation; partial |
| 450 | 150 paired observations, 301–450; partial |
| 599 | 299 paired observations; partial |
| 600 or later | 300 paired observations, 301–600; complete |
| Rewind | Recompute the newly visible prefix, including returning None before 301 |

Evidence contains `count`, `firstStep`, `lastStep`, `isComplete`,
`baselineMeanAbsoluteError`, and `regulatedMeanAbsoluteError`. It reads only visible
frames in the declared window; it never consults or caches the retained whole-window
summary. The helper itself is a projection of an already verified record, not a
second validator. The retained complete `summary` must not be sent to an early-cursor
viewer. Per-frame fields and window aggregates should remain labeled as sensory
field measurements, with the absence of reservoir state explicit.

Filesystem bounds, exact original-byte snapshots and opaque-handle lifecycle remain
owned by the existing core dispatcher and desktop backend. The module never follows
paths in unknown fields or contacts a provider. Core execution tests do not by
themselves qualify a desktop run/stop/save workflow.

## Checks and independent Swift oracle

`tests/regulation.rs` contains nine tests covering the retained Swift fixture,
exact inputs/projection, defaults/nulls/UTF-8 bounds, complete-record requirements,
next-step application, strict controller tolerances, corrupt spectra/bases, valid
basis sign flips, whole-window mutations, and prefix/rewind boundaries. The fixture
is the existing 52,776,851-byte
`essentials/examples/portable/example-regulation-controller.json`; it is not copied
or rewritten by the port.

Fresh-session coverage adds three tests in `tests/session_regulation.rs` and one
internal failure-injection test. They check completion-only export, exact seeded
projection and all 66 input coordinates, next-step retention, retained-prefix and
rewind behavior at 300/301/599/600, deterministic stepping across read/pause chunks,
rejection of alternate recipe values, independent snapshot ownership, and rollback
after failure in the second field. Focused commands are:

```sh
cargo test --locked -p reservoir-core --lib regulation::session_tests -- --nocapture
cargo test --locked -p reservoir-core --test session_regulation -- --nocapture
```

`examples/regulation_session_fixtures.rs` writes one freshly stepped complete record
and a separate manifest inspecting prefixes at 0, 1, 300, 301, 450, 599 and 600. It
requires a new output directory and uses new-file creation plus exact readback to
avoid overwriting an earlier fixture. The manifest reports generation and inspection,
not an independent verification or desktop storage result:

```sh
cargo run --locked -p reservoir-core --example regulation_session_fixtures -- NEW_OUTPUT_DIRECTORY
```

The 0.10 fresh-session qualification is retained separately under
`validation/2026-10-12-controller-0.10.0/`; the older controller receipts below remain
historical results for their recorded source identities.

Run from `desktop/ReservoirScope`:

```sh
cargo test --locked -p reservoir-core --test regulation -- --nocapture
cargo clippy --locked -p reservoir-core --all-targets -- -D warnings
cargo build --locked --release -p reservoir-core --bin reservoir-core --example emit_regulation_record
```

The independent check builds the unchanged Swift Essentials source into an isolated
`target/regulation-swift-oracle` directory. It compiles the actual native
`GuidedLessons.swift` alongside a small serializer wrapper; it does not replace the
native prefix-window algorithm with a restatement. On the qualification Mac these
commands used per-process `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer`
and `SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk`:

```sh
# From the repository root:
ESSENTIALS_BUILD_DIR="$PWD/desktop/ReservoirScope/target/regulation-swift-oracle" essentials/build.sh
swiftc -parse-as-library -swift-version 5 -O -target arm64-apple-macosx14.0 \
  -I desktop/ReservoirScope/target/regulation-swift-oracle/lib \
  -L desktop/ReservoirScope/target/regulation-swift-oracle/lib \
  -lEssentialsCore -framework Accelerate \
  native/ReservoirScope/Sources/ReservoirScope/GuidedLessons.swift \
  desktop/ReservoirScope/crates/reservoir-core/tests/support/regulation_window_oracle.swift \
  -o desktop/ReservoirScope/target/regulation-swift-oracle/bin/regulation-window-oracle

# From desktop/ReservoirScope:
python3 crates/reservoir-core/tests/support/check_regulation_oracles.py \
  --swift-runner target/regulation-swift-oracle/bin/essentials-run \
  --swift-window-oracle target/regulation-swift-oracle/bin/regulation-window-oracle \
  --rust-runner target/release/reservoir-core \
  --rust-helper target/release/examples/emit_regulation_record \
  --receipt validation/2026-10-12-regulation-oracles-final.json
```

Qualification completed with nine Rust controller tests, clean core clippy across
all targets, and 18 passing independent oracle cases. The first receipt is retained;
`validation/2026-10-12-regulation-oracles-final.json` records the rerun against the
frozen final dispatcher source.
The Swift build emitted only its existing deprecated `dsyev_` warnings.

The script compares the retained Swift record and a fresh Rust-generated record in
both verifiers; checks positive defaults/nulls, inert Windows paths and tolerance
boundaries; rejects seeded/input/clock/control/basis/summary/window mutations; and
compares native versus Rust prefix evidence through forward and backward cursor
sequences. The receipt records source, fixture and executable hashes and exact
commands. Missing executables or timeouts are incomplete, not passed. Old 0.2/0.3
receipts are unchanged. This is local macOS numerical qualification, not independent
Windows/Linux packaged-app, accessibility, sustained-session or live-model evidence.
