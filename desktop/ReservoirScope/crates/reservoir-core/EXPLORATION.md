# Bounded exploration conformance

`exploration.rs` supports `essentials-exploration-v1`: the independent, finite Swift
exploration mechanism in `essentials/reservoir/ReservoirExploration.swift`. It does
not call models, read live inputs, or implement sustained sessions. Passing this
family does not establish complete M1 or packaged desktop parity.

The public serde types are `ExplorationRecord`, `ExplorationFrame`, and
`ExplorationControls`. `record.verify()` checks the entire chain; on success the
report counts are `record.frames.len()` steps and zero turns. `validate_structure()`
alone is not numerical verification. Seeds remain `u64`; original imported bytes
remain authoritative for export, including unknown fields and valid alternative
eigenvector bases. The optional spectral measurement is a **separate sensory
field**. Exploration records contain no fill measurement, journal, or model turn.

The bounded `ExplorationEngine` supports `new(seed)`, `Default`, `advance(controls,
pulse)`, `frames()`, `record()`, and `from_record(&record)`. Verified resumption
preserves retained historical frames and resumes from retained last state/covariance
with the replayed RNG position. No command exposes a sustained background runtime.

## Compatibility rules

- Fixed 32 reservoir nodes, 66 inputs, 32 sensory coordinates and 1/3-second steps;
  zero through 1,800 retained steps are valid. Source weights and projection must
  equal their seeded values exactly, including below numerical replay tolerance.
- Rust constructor defaults match Swift's quiet constructor: leak 0.65,
  recurrence off/strength 1, repeated input off/strength 1, noise 0, bias off,
  sensory field off, retention 0.955. **All nine control fields are required in
  JSON.** Swift's synthesized Codable does not apply constructor defaults to
  missing or null imported controls. An omitted or null optional `spectral` is valid
  only when the recorded sensory control is off.
- Pulses use the first fixed forcing sample; otherwise repeated forcing uses that
  step's clock, including its 12-on/18-off pattern. Input scaling applies before
  recurrence. Auxiliary and text input coordinates remain zero.
- Controls alter only the current calculation, preserving source weights. Recorded
  input/recurrent/bias drives are raw pre-tanh contributions, not state increments.
  Proposal follows the recurrence's accumulation order; the next state adds leak
  and explicit noise, then clips to `[-1,1]`.
- Every successful step consumes 32 noise samples, even at zero amplitude. Failed
  controls/calculations never advance state or RNG. Sensory off discards field
  state; the next on step starts from identity covariance.
- Replay uses Swift's `2e-7 * max(1, abs(expected))` tolerance for frames and
  spectra. Eigenvector residuals, norms and orthogonality are checked instead of
  equality to one solver's signs/basis. Negative eigenvalues fail even inside the
  tolerance. As in Swift resumption, final retained covariance must also satisfy
  the field constructor's stricter `1e-10` symmetry guard.
- Unknown exploration versions are incomplete; supported but malformed or
  non-reproducing records fail. This format has no text-codec qualification limit.
  Unknown text metadata is preserved as original bytes, never interpreted as a
  journal or an instruction.

## Oracle corpus and qualification

`tests/fixtures/exploration/` contains five new records produced and verified by
the current Swift source, not by the Rust implementation: quiet/default controls,
pulse/repeated forcing, control transitions, sensory restarts, and empty/full-UInt64
seed cases. The five records contain 64 steps. Both seeds above JavaScript's exact
integer range and `UInt64.max` are represented. No pre-existing tracked exploration
record corpus was found; these are a focused conformance corpus, not user data.

The 14 Rust tests cover that corpus, all control mechanisms, exact imported bytes,
37 independent numerical/control mutations, required fields, valid degenerate bases,
noise continuity, retained-state resumption, final covariance symmetry and limits.
The separate retained receipt at
`validation/2026-10-11-exploration-oracles.json` records independent checks by both
implementations: five Swift records, six Rust records (including continuation from
a Swift import), and nine rejected mutations. Those 20 cases passed on the recorded
macOS host. The receipt records executable/source hashes and every verifier command;
temporary generated records were removed. It is not Windows/Linux or UI evidence.

The Swift oracle was rebuilt from this repository into
`/tmp/reservoir-core-exploration-oracle`. The source build emitted the existing
Accelerate `dsyev_` deprecation warnings; it completed successfully. Exact commands
used from the repository root:

```sh
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk ESSENTIALS_BUILD_DIR=/tmp/reservoir-core-exploration-oracle essentials/build.sh
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk swiftc -swift-version 5 -O -target arm64-apple-macosx14.0 -I /tmp/reservoir-core-exploration-oracle/lib -L /tmp/reservoir-core-exploration-oracle/lib -lEssentialsCore -framework Accelerate desktop/ReservoirScope/crates/reservoir-core/tests/support/emit_exploration_vectors.swift -o /tmp/reservoir-core-exploration-oracle/bin/emit-exploration-vectors
/tmp/reservoir-core-exploration-oracle/bin/emit-exploration-vectors desktop/ReservoirScope/crates/reservoir-core/tests/fixtures/exploration
```

From `desktop/ReservoirScope`:

```sh
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk cargo test --locked -p reservoir-core --test exploration
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk cargo clippy --locked -p reservoir-core --all-targets -- -D warnings
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk cargo build --locked -p reservoir-core --bin reservoir-core --example emit_exploration_records
```

From the repository root:

```sh
python3 desktop/ReservoirScope/crates/reservoir-core/tests/support/check_exploration_oracles.py --rust-runner desktop/ReservoirScope/target/debug/reservoir-core --rust-emitter desktop/ReservoirScope/target/debug/examples/emit_exploration_records --swift-runner /tmp/reservoir-core-exploration-oracle/bin/essentials-run > desktop/ReservoirScope/crates/reservoir-core/validation/2026-10-11-exploration-oracles.json
```

These per-process SDK values address this host's stale default Xcode lookup; they
are not application requirements. Oracle regeneration is a deliberate operation,
not part of ordinary tests, so an implementation cannot silently rewrite its own
reference fixtures to obtain a passing test.
