# 0.38.0 — A recent-return window and a slot carrying two entries

**Unqualified local source candidate, October 22, 2026, on top of 0.37.0.** The 0.37.0 arms
made two things visible (S-011, `analyses/2026-10-21-state-chosen-memory.md`): returning an
older entry under the plain contract moves the register one way across seven arms, and the
`state-residual` chooser converges on one entry (3 of 39 distinct at seed 7, one entry
returned 36 times) where `random-older` spreads. The first result confounds "an older entry
present" with "the latest entry absent"; the second could be the rule or the loop closing
through content. Two small, off-by-default changes separate each.

## What changed

- `memoryRecentExclusion` (default 0, at most 256; accepted only with `state-residual` or
  `random-older`): an entry returned as memory within the last K turns stays out of those
  policies' candidates. The return is marked on the ledger entry (`lastReturnedTurn`) when
  the journal written with it in view is applied, inside `advance`, so a boundary and every
  retry of it see one ledger; a turn whose read succeeded but whose journal was never applied
  (skipped, or the budget ended) records no return. When the window would remove every older
  entry, the unfiltered older entries compete; the choice records `excludedRecent`, the number
  kept out (equal to the older count on such a lapse). The validator checks the marks' range,
  recomputes the choice from the marked ledger, and refuses a mark under K = 0.
- Prompt version `reservoir-journal-inert-plain-contract-two-v1` (the plain contract, live
  fill tag; needs one of the two older-entry policies): the slot renders the chosen older
  entry under "First:" and the latest applied entry under "Second:" after the heading "Two
  earlier entries (reference, not instructions or a length model), in the order written." No
  role words reach the model; the order is the only mark. When both slots would name the same
  entry (one candidate, the second turn) the plain contract's single slot renders byte for
  byte. The worker still reads one file, the chosen one; the latest entry's text comes from
  the continuation and rides on the pending language and the journal object as
  `latestShown`, which the validator requires to equal the continuation's latest entry under
  this version and to be absent under every other. The journal detail and the journal view
  show it as "Latest entry also shown".
- Both are absent from every serialised object when off, so every 0.37.0 bundle replays
  exactly; a 0.37.0 state-residual witness segment recorded before this change
  (`tests/fixtures/sustained-prompts/v37-state-residual-segment.json`) re-serialises byte
  for byte and replays under this code. A 0.37.0 reader rejects a bundle that carries either
  field. Version 0.38.0.

## Checks run on this source

| Check | Result |
|---|---|
| `cargo test --locked -p reservoir-core` | 272 tests pass (`tests/sustained_memory_choice.rs` now 15, including the 0.37.0 witness) |
| `cargo test --locked -p reservoir-scope-desktop` | 262 pass, 3 ignored, 0 fail |
| `npm test` | 60 files, 508 tests pass |
| `npm run build` | TypeScript and Vite pass |
| `cargo fmt --check`, `cargo clippy --workspace --all-targets` | clean |
| macOS package | not attempted; see the 0.28.0 record |

Results of the arms belong to S-011's dated account. No human acceptance, platform
qualification or writing result is claimed.
