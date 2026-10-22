# 0.39.0 — The two-entry slot without a context line

**Unqualified local source candidate, October 22, 2026, on top of 0.38.0.** The 0.38.0 blind
reading placed the sample's invented-number, finished-state entries (884.3%, 100.0%, 98.8%
where the context line showed about 70%) entirely in the arms whose slot carried two entries
beside the live fill tag (S-011, `research/readings/2026-10-22-blind-policy-038.md`), and
the markers showed the latest entry's presence in that slot restores none of the questions,
hedges or first-person openings the older-entry slot removes. The direct test of whether the
number made that family is the same slot with no number: one prompt version, one change.

## What changed

- Prompt version `reservoir-journal-inert-plain-contract-two-no-tag-v1`: the plain contract's
  two-entry slot (the policy's chosen older entry under "First:", the latest applied entry
  under "Second:", marked only by order) inside the no-tag frame, so the prompt is
  `Mode: journal`, the two entries, and the closing line, with no "Optional context" line at
  all (no step, no fill). It needs one of the two older-entry policies, like the tagged
  two-entry version; the latest entry rides on the pending language and the journal object as
  `latestShown` under the same rules; when both slots would name the same entry it renders the
  no-tag plain contract's single slot, byte for byte. A test asserts the prompt is the tagged
  two-entry prompt minus its context line and equals the no-tag single-slot prompt with the
  slot replaced.
- The app is no longer labelled a preview (Mike, October 22: it is past that). The installed
  name, window title, menu and About text are `Reservoir Scope Tauri`; the identifier
  `research.reservoir.scope.tauri` and the storage it names are unchanged, so an installed
  copy keeps its data. The living guides and references drop the label; dated records,
  validation receipts, the 0.27.0 archive's own name and the tag
  `reservoir-scope-tauri-v0.27.0-private-preview` keep theirs; the install guide keeps its
  file name `PREVIEW-START.md` because dated records link to it.
- The frontend recognises the version; the two-entry policy gate covers both two-entry
  versions. Every other prompt version, object and fixture is byte for byte unchanged: the only
  shared-code edits are the dispatch arm of `prompt()` and the `returns_two_entries` match. A
  0.38.0 reader rejects a bundle naming the version. Version 0.39.0.

## Checks run on this source

| Check | Result |
|---|---|
| `cargo test --locked -p reservoir-core` | 275 tests pass (`tests/sustained_memory_choice.rs` now 17, `tests/sustained_inert_tags.rs` 3) |
| `cargo test --locked -p reservoir-scope-desktop` | 262 pass, 3 ignored, 0 fail |
| `npm test` | 60 files, 508 tests pass |
| `npm run build` | TypeScript and Vite pass |
| `cargo fmt --check`, `cargo clippy --workspace --all-targets` | clean |
| macOS package | not attempted; see the 0.28.0 record |

Results of the arms belong to S-011's dated account. No human acceptance, platform
qualification or writing result is claimed.
