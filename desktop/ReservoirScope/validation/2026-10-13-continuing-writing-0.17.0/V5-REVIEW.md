# Independent v5 source review

Reviewed 2026-10-14 UTC by the frontend/readback agent. No concrete production
blocker was found in the scoped review. This is a source and test-design review,
not an executed Rust qualification, packaged UI check, or model-writing result.
The parent owns those execution receipts. No services, models, live Beings or
application state were accessed for this review.

## What was checked

- **Contract and historical versions.** The explicit v5 enum dispatches to a new
  `prompt_v5`; omitted serialized versions still deserialize to v1. V1–v4 retain
  separate prompt branches. The new historical fixture test pins both retained
  fixtures for each of those versions. Desktop tests exercise saved prompts,
  exact journal export, paused restoration and explicit continuation for all five
  versions, and reject relabelled or removed manifest versions.
- **Approved wording and number meaning.** The implementation and first/later
  fixtures match [the template](PROMPT-V5-TEMPLATE.txt) and
  [protocol](PROTOCOL.md): open invitation, mechanism context, compact readout,
  full prior writing, final invitation. Step identities use integer formatting;
  simulated seconds and scalar values use the existing `fixed8` formatter. RMS
  differences are current minus prior; fill differences are percentage points.
  State-coordinate distance is the nonnegative norm of the vector difference,
  separate from a change in RMS or L2 norm. Missing prior values remain
  `unavailable`, including the first-entry block. Signed differences preserve
  the existing formatting policy rather than introducing a new rounding rule.
- **Memory and observation remain distinct.** The prompt serializes the entire
  eligible journal as one JSON string after the readout. Tests include newline,
  quote, backslash, Unicode and apparent section-marker content, checking exact
  decoded bytes. A failed/skipped intervening opportunity tests that the prior
  measurement boundary can differ from the latest applied journal boundary.
  Full coordinates, spectrum and prior scalar snapshot remain in the retained
  observation even though the v5 measurement scaffold omits them.
- **Unchanged mechanical gates.** The new core tests compare v4/v5 numerical
  continuations under identical supplied replies; distinguish saved readback
  from application authorization; retain incomplete text without saving or
  applying it; and reject prompt/version/prior-observation mutations after
  rehashing. Desktop tests additionally exercise physical journal reread and
  reject a fabricated prompt after rebuilding all outer journal/segment hashes.
- **Human evidence wording.** Selected journal identity supplies the prompt
  version to the reader. V5-only text explains that the full eight-row table and
  observation exceed the compact measurement subset. The exact prompt remains
  visible, so a number voluntarily repeated inside prior prose is not falsely
  represented as absent from all supplied context. Historical v4 wording stays
  separate. The frontend restore guard refuses an accepted summary whose prompt
  version differs from the inspected recovery configuration.

## Review bindings and limits

Paths below are relative to `desktop/ReservoirScope`; SHA-256 values identify the
reviewed bytes.

| Source | SHA-256 |
|---|---|
| `crates/reservoir-core/src/sustained.rs` | `073d324a17eab74e0d80d738213afb8d1b353102e2c7a5a23d0875077d3baa5b` |
| `crates/reservoir-core/tests/sustained_continuing_prompt.rs` | `a26ebaa41dd5d78d304fc3955050420cfb0f581ad8f29792da658ebc5180f06b` |
| `src-tauri/src/sustained_tests.rs` | `d902c77449fde262b23e81ce222550a6e72e2c7c25736234aa71afcc43609c51` |
| `validation/2026-10-13-continuing-writing-0.17.0/PROMPT-V5-TEMPLATE.txt` | `7107385f63cec5b27697a43bd4ba3d58f2f7f5c59b998e9ab8c929e76cd9b25f` |
| `src/MyReservoirJournals.tsx` | `363a88d5558490e7d1d6be331e1fe58e24c9fff1f4a6197919a6d7a88c5360ff` |
| `src/JournalMeasurements.tsx` | `af69686916449fbb640eb864701610a4a33a3171fa1934941098060909a4581e` |

The core owner reported two failures in the first Rust run from older tests that
still assumed v4 content in the fresh default. I read the subsequent test-only
corrections: `tests/sustained.rs` now distinguishes retained arrays/hash from the
compact prompt and decodes the v5 memory marker (SHA
`894b2d89ba7cbab93da7aa871acb3948beea387fbb3c6924693c32fd49b63433`);
`tests/sustained_generation_budget.rs` uses that marker for full-text readback
(SHA `e5523e244ca9940d7d01c6fd16a6f0c7cc471a5bf01ea142f06df7a78b970b4f`).
Production, template and new v5 fixture bytes did not change in that correction.
The parent's rerun determines their execution outcome; this review does not
convert inspected assertions into passed checks.

The separately executed frontend tests/build are recorded in
[frontend-checks-01.json](frontend-checks-01.json). Neither those checks nor this
review establish better continuity, factual accuracy, creative range, emergence,
or a causal explanation for earlier writing. Actual model prose requires its own
bounded episode and full reading; no such v5 result is claimed here.
