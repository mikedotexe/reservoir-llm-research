# 0.31.0 — Two more S-010 contract arms

**Unqualified local source candidate, October 21, 2026, on top of 0.30.0.** Two frozen
prompt versions for [S-010](../../research/studies/S-010-frame-share-and-loop-share.md),
each one change away from an existing arm so that a contrast isolates that change.
Every earlier prompt body, codec and mechanism identity is byte for byte as before.

## What changed

- `reservoir-journal-inert-open-contract-v1`: the plain contract without its first
  sentence. Neither the writer nor a runtime is named; interpretation is granted in the
  same words ("Your interpretation is yours, including affirmation, uncertainty,
  disagreement, or no felt correspondence"). A test asserts that the plain contract equals
  the naming sentence followed by this one.
- `reservoir-journal-inert-inviting-varied-contract-v1`: the inviting contract followed
  by the two guideline lines Astrid's standing prompt carries that the inviting contract
  omitted: the opening-pattern rule ("NEVER begin with "The [noun] feels like..." or
  "The [noun] hums with..."; these are attractor patterns. Vary your openings…") and the
  length line ("Write as much as you need…"), without the dialogue reference. A test
  asserts that the text starts with the inviting contract.
- Both send their contract as the system message and use the unchanged inert per-turn
  input; the frontend recognises both for reading recovered sessions. Version 0.31.0.

## Checks run on this source

| Check | Result |
|---|---|
| `cargo test --locked -p reservoir-core` | 246 tests pass, including the new assertion in `tests/sustained_frame_arms.rs` that each contract is one change from its parent |
| `cargo test --locked -p reservoir-scope-desktop` | 259 pass, 3 ignored (the arm runner and two existing), 0 fail |
| `npm test` | 57 files, 502 tests pass |
| `npm run build` | TypeScript and Vite pass |
| `cargo fmt --check`, `cargo clippy --workspace --all-targets` | clean, after removing one pre-existing unused-parentheses warning in `tests/sustained_embedding_codec.rs` |
| macOS package | not attempted; see the 0.28.0 record |

Results of the arms belong to the study's dated accounts, not to this record. No human
acceptance, platform qualification or writing result is claimed.
