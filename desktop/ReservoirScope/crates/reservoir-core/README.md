# Reservoir Core: offline conformance

This crate supplies an offline Rust implementation of the four `essentials-v1`
stage mechanisms, exploration, A–H actions and the separate controller verifier, plus reviewed-case
and geometry packet validators. It is part of the
Tauri app's portable core, not a claim of complete M1 or desktop parity.

The verifier checks seeded weights, forcing, realized noise, every reservoir
state, separate sensory covariance/spectrum, stored eigenvector equations,
reduced fill and controller timing, retained prompts, text feedback and terminal
turn/run state. It uses the existing stage tolerance
`2e-7 * max(1, abs(expected))`. A pure Rust `nalgebra` eigensolver replaces
Accelerate; stored eigenvectors retain their orientation and are checked for
residuals and orthogonality rather than equality to a newly selected basis.

## Current boundaries

- `essentials-v1` stage records with qualified completed replies are supported,
  including retained model, stopped and failed records. Verification contacts
  no model and follows no embedded paths.
- The text codec admits a bounded corpus of Swift-qualified Unicode scalars and
  grapheme clusters. Unqualified text remains **incomplete**, with original UTF-8
  intact. The retained oracle includes accents, non-Latin scripts, selected emoji,
  whitespace and punctuation; it is not a claim of universal Unicode compatibility.
  See [the exact Unicode scope and retained oracles](CODEC-UNICODE.md).
- [Exploration](EXPLORATION.md) verifies every recorded control, forcing/noise,
  state contribution, sensory reset and optional spectrum. Its engine supports
  bounded offline continuation; it has independent Swift-generated oracle fixtures.
- [Actions v1/v2/v3](ACTIONS.md) verify A–H, matched tapes, observations, journal
  identity/save boundaries, prompts, full-text memory and next-step input. Retained
  model outcomes are checked offline. Ambiguous provider-response syntax and
  unsupported Unicode remain incomplete rather than receiving a false certificate.
- [Reviewed cases](CASES.md) validate embedded hashes, quotations and references;
  [geometry packets](../../GEOMETRY.md) validate chains, frozen vectors, clocks and RMS
  comparisons. Reports name these scopes separately from numerical experiment replay.
- The separate `essentials-regulation-v1` teaching record verifies the fixed 600-step
  two-field study, exact seeded projections, input, controls and summary. Native
  `1e-8` controller tolerances and `2e-7` spectral checks remain unchanged. Its
  evaluation exposes only the reached part of steps 301–600. Unsupported families
  still return **incomplete**. See [controller contracts and independent checks](REGULATION.md).
- `run` generates only scripted stage recipes. Provider requests, action
  journals, asynchronous session ownership and cancellation are later work.
  An Ollama recipe is refused without substituting a scripted backend.
- API fields used to control or display a seed must cross the frontend boundary
  as decimal strings. Canonical JSON retains historical integer encoding;
  Rust parses seeds directly as `u64`, including `u64::MAX`.

## Run from the desktop workspace

```sh
python3 scripts/stage_resources.py
cargo test --locked -p reservoir-core
cargo run -p reservoir-core -- verify ../../essentials/examples/essentials-stage-4.json --json
cargo run -p reservoir-core -- run --config ../../essentials/stages/03-llm-loop.json --output /path/to/new-run.json
```

Stage resources before compiling the tests: reviewed-case tests embed the generated
case catalog at compile time. The staging script verifies and copies canonical
repository inputs; it needs no private capture or model service. On Windows, use
`python` if that is the installed Python 3 command.

Verification JSON uses `status: passed | failed | incomplete`, a named `scope`,
the source-byte SHA-256, checked-step/turn counts and diagnostics. Exit codes are
0, 1 and 2 respectively. Malformed or inconsistent supported records fail;
unsupported capabilities are incomplete. The `modelsContacted` field is always
false. Existing output files are never replaced by `run`.

`inspect_bytes` retains original bytes alongside the decoded inspection view and
report. Copy these original bytes for import/export; serializing a decoded
record is not a byte-preserving copy. Unknown fields and original text are not
rewritten. A decoded record may accompany failed/incomplete validation, so
callers must preserve the report's status rather than infer verification from
the presence of decoded data.

## Qualification

The tests independently replay all four tracked 300-step Swift stage records,
exercise mutation rejection for 16 links in the numerical/evidence chain, check
u64 seeds and record bytes, cover failed/stopped/provider records without
network calls, and check exact ASCII codec vectors emitted by unchanged Swift
`TextCodec`. The static vectors are in `tests/fixtures`; their generator is
`tests/support/emit_codec_vectors.swift` and needs an explicitly built
EssentialsCore only when refreshing the oracle.

On a Mac with an already built Swift runner, the optional independent check is:

```sh
cargo build -p reservoir-core
python3 crates/reservoir-core/tests/support/check_swift_roundtrip.py \
  --rust-runner target/debug/reservoir-core \
  --swift-runner /absolute/path/to/essentials-run
```

It generates four 61-step noisy Rust records with seed `u64::MAX`, then verifies
each using Swift. It runs only explicit local binaries, emits a machine-readable
receipt and deletes its own temporary runs. The baseline execution passed on
the development Mac; Windows/Linux execution and packaging remain separate
qualification gates. This historical stage result does not establish Unicode, whole-app or live-system
parity. Later exploration/action qualification is documented in the linked guides.

The retained [development Mac roundtrip receipt](validation/2026-10-11-swift-stage-roundtrip.json)
binds each generated record and both explicit executables by SHA-256. Its Swift
oracle was built from this checkout with:

```sh
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk \
zsh essentials/build.sh
```

The source build printed
`/Users/v/.cache/reservoir-research/Essentials-build/bin/essentials-run`;
that exact runner was passed to the optional check. These are recorded host paths,
not required paths for other installations. No global Xcode selection was changed.
