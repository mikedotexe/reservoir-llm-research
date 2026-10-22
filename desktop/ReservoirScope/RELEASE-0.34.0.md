# 0.34.0 — No-tag and scrambled-tag controls

**Unqualified local source candidate, October 21, 2026, on top of 0.33.0.** Two controls
from the self-observation spec's falsification layer, for
[S-011](../../research/studies/S-011-self-observation-stack.md): the prompt-leakage
audit and the shuffled-state control, as frozen prompt versions.

## What changed

- `reservoir-journal-inert-no-tag-v1` and `reservoir-journal-inert-plain-contract-no-tag-v1`:
  the inert input with the "Optional context: step N · fill X%" line removed and nothing
  added, without and with the plain contract. A test asserts the prompt is the inert
  prompt minus that line.
- `reservoir-journal-inert-plain-contract-scrambled-tag-v1`: the inert input under the
  plain contract with a fill number in [40, 95) computed from the session seed and the
  step (`scrambled_fill`), unrelated to the field. The observation keeps the live fill;
  the retained prompt shows what the model saw. Deterministic per seed; tested.
- The frontend recognises the three versions. Version 0.34.0.

## Checks run on this source

| Check | Result |
|---|---|
| `cargo test --locked -p reservoir-core` | 250 tests pass, including `tests/sustained_inert_tags.rs` (2) |
| `cargo test --locked -p reservoir-scope-desktop` | 260 pass, 3 ignored, 0 fail |
| `npm test` | 58 files, 503 tests pass |
| `npm run build` | TypeScript and Vite pass |
| `cargo fmt --check`, `cargo clippy --workspace --all-targets` | clean |
| macOS package | not attempted; see the 0.28.0 record |

Results of the arms belong to the study's dated account. No human acceptance, platform
qualification or writing result is claimed.
