# Bounded Swift Unicode codec qualification

The portable `codec::encode` now accepts a qualified Unicode subset in addition
to ASCII. It preserves the existing 48 coordinates, semantic gain, feedback
formula and numerical tolerances. This is a structural/lexical encoder, not an
embedding or an interpretation of a person's or being's experience.

The qualification is anchored to the unchanged
[`TextCodec.swift`](../../../../essentials/spectral_bridge/TextCodec.swift).
No native source, canonical experiment, live system or provider was changed or
contacted. Original recording and journal bytes are not normalized or rewritten.

## What is admitted

The retained [native oracle](tests/fixtures/unicode-codec-v1.json) contains
properties and scalar lowercase mappings for 44,206 scalars, plus 21 explicit
multi-scalar graphemes. Admission uses those tables with pinned
`unicode-normalization = 0.1.25` and `unicode-segmentation = 1.13.3`.

A grapheme must normalize to one scalar in the qualified tables, with all its
original scalars also covered, or canonically match an explicitly retained
multi-scalar cluster. Its lowercase result must also pass qualification. This
supports many Latin, Greek, Cyrillic, CJK, Hangul, Japanese, numeral and punctuation
inputs, canonical composed/decomposed accents, and selected Hebrew, Arabic,
Indic and emoji clusters. It does **not** imply complete language, script, emoji,
Unicode-version or arbitrary combining-sequence support. The exact scalar ranges
and clusters are machine-readable in the oracle; examples outside the boundary
include U+10FFFF, U+FB00, arbitrary extended combining sequences and the unlisted
complex cluster in `नमस्ते`. Other Indic examples such as `कि` and `क्ष` are admitted.

Unsupported inputs return `CoreError::Unsupported`, causing record verification
to remain **incomplete**. This is distinct from a numerically invalid recording.

## Native behavior preserved

- Counts, word lengths and character predicates operate on graphemes. Character
  frequency and unique-word equality use canonical normalization internally,
  matching Swift equality; the scalar-rhythm coordinate still uses the original
  Unicode scalars, so canonically equivalent spellings need not have identical
  complete feature vectors.
- Lowercase mappings come from the retained Swift implementation. For example,
  native `ΟΣ` becomes `οσ`; applying Rust's whole-string final-sigma behavior
  would change the native result. `İ` expands to `i` plus combining dot.
- Letter, number, uppercase, whitespace and punctuation predicates are native
  property tables. Numbers include more than ASCII digits, while symbols remain
  distinct from punctuation. Apostrophe-based word splitting preserves the
  native distinction between `'` and typographic apostrophes.
- Foundation trimming, line separators, bullet prefixes and quotation marks have
  separate behavior from Rust's default whitespace helpers. U+200B is trimmable
  by Foundation but is not a whitespace `Character`.
- Ellipsis matching excludes a final period carrying a combining mark. Paragraph
  matching retains the native raw LF substring behavior, including an LF inside
  CRLF. Both differences have retained native vectors.

The production property tables are generated constants in
[`codec_unicode_data.rs`](src/codec_unicode_data.rs). The desktop does not load
these test fixtures or call Swift/Foundation to encode text.

## Observed checks

The native corpus has a deterministic input seed and 1,147 vectors: curated cases,
seeded mixed strings and chunks covering the declared scalar alphabet. On the
retained Swift 6.2.4 host:

- **1,124 vectors admitted and matched**, each of 48 features within the existing
  `1e-12` oracle tolerance; reserved coordinates remained exactly zero.
- **23 vectors explicitly incomplete**, rather than falsely reported as matched.
  Whole chunks containing an unsupported cluster are incomplete; the 44,206
  scalar-property entries are not a claim that every scalar chunk passed the
  end-to-end codec.
- Every admitted vector also matched native empty-after-trimming behavior.
- The retained ASCII oracle still passed. Three focused Unicode tests and two
  action-envelope tests passed. The eight action-conformance tests also passed,
  including all 22 retained canonical action recordings and qualified whitespace
  failure receipts. `cargo clippy --locked --package reservoir-core
  --all-targets -- -D warnings` completed cleanly.

The [independent action receipt](validation/2026-10-11-unicode-actions-v2.json)
records 21 expected Swift/Rust comparisons. Sixteen terminal stage-4 Unicode
journal mutations passed both verifiers; two native-valid texts deliberately
remained incomplete in Rust; three corrupted feature/hash/text mutations failed
both. These are synthetic verifier probes derived from a public record, **not**
new model answers or research observations. Cached native codec/parser/verifier
sources were checked against the unchanged repository copies, and both executable
hashes are retained.

The earlier [v1 receipt](validation/2026-10-11-unicode-actions-v1.json) remains as
failed evidence: its harness initially expected the unsupported `नमस्ते` example
to pass. The v2 harness corrects that expectation and adds coverage; no runtime
qualification boundary was loosened to obtain the result.

A full core run initially found an unrelated obsolete CLI test that still expected
the newly supported regulation-controller family to be incomplete. That test's
integration correction and final full-suite results belong to the root validation
ledger, not this focused codec account.

## Action parser boundary

Standard JSON Unicode journal text now uses the qualified Foundation trim helper
instead of the old blanket ASCII gate. `WAIT` still requires an exactly empty
string, forced-journal stages still reject `WAIT`, and output byte limits are
unchanged. Tests cover Unicode journals, U+200B/NEL/NBSP, controls, forced choice,
and explicit incomplete input.

This does not resolve all Foundation/serde JSON differences. Duplicate known
keys, trailing commas, a leading BOM and ambiguous syntax remain incomplete under
the existing parser guard. General parser compatibility and every canonical
string-equality edge in surrounding record metadata are separate qualification
work; this tranche changes only the codec and the action text/trim admission gate.

## Reproduction

Run from `desktop/ReservoirScope`:

```sh
cargo test --locked --package reservoir-core --test unicode_codec_conformance -- --nocapture
cargo test --locked --package reservoir-core unicode_parser_tests
cargo test --locked --package reservoir-core retained_swift_ascii_codec_oracle_vectors_match
cargo clippy --locked --package reservoir-core --all-targets -- -D warnings
```

A macOS host with an explicitly selected, working Swift SDK can generate a **new**
oracle (the scripts refuse to overwrite outputs):

```sh
python3 crates/reservoir-core/tests/support/generate_unicode_codec_oracle.py --output /tmp/new-unicode-oracle.json
python3 crates/reservoir-core/tests/support/derive_unicode_codec_tables.py /tmp/new-unicode-oracle.json /tmp/new-codec-tables.rs
rustfmt --edition 2021 /tmp/new-codec-tables.rs
```

The generator compiles the unchanged native codec directly. A shape-only
`SpectralMeasurement` declaration satisfies the unused feedback API; it supplies
no encoder implementation. Floating reduction order in the native dictionary
can affect final bits, so comparison uses the existing numerical tolerance rather
than requiring byte-identical JSON from another Swift process or host.

For fresh independent record probes, build the current portable CLI and supply an
explicit native runner whose adjacent `sources/` directory can be checked:

```sh
cargo build --locked --package reservoir-core --bin reservoir-core
python3 crates/reservoir-core/tests/support/check_unicode_action_oracles.py --rust-runner target/debug/reservoir-core --swift-runner /absolute/build/bin/essentials-run --output /tmp/new-unicode-action-receipt.json
```

Windows/Linux execution, other Swift/Unicode versions, packaged desktop acceptance
and comprehensive Unicode/parser parity are not established by these receipts.
