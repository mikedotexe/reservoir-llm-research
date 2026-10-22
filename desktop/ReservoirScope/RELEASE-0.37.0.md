# 0.37.0 — Two more memory policies: state-residual and random-older

**Unqualified local source candidate, October 21, 2026, on top of 0.36.0.** The first gemma4
arm under `state-aligned` returned the latest entry on 39 of 39 turns: with entries that
differ, the latest entry's vector is still being fed at every step, the recurrent state
points along its push, and the cosine rule can only pick it. Two policies fix the question
rather than the finding.

## What changed

- `memoryPolicy` gains `state-residual`: the latest entry's effect direction is projected out
  of the observing state (`project_out`), and the entry whose effect points most along the
  residual is chosen among the entries older than the latest (ties to the most recent;
  one candidate returns the latest). And `random-older`: a seeded uniform draw among the
  older entries, the control. The recorded choice, its score (cosine with the residual),
  age, candidates and the readback match are as in 0.36.0.
- `latest`, `state-aligned` and `random` are unchanged, so every 0.36.0 bundle replays
  exactly; the degenerate behaviour of `state-aligned` with distinct entries is documented
  in the settings text. Version 0.37.0.

## Checks run on this source

| Check | Result |
|---|---|
| `cargo test --locked -p reservoir-core` | 263 tests pass (`tests/sustained_memory_choice.rs` now 6) |
| `cargo test --locked -p reservoir-scope-desktop` | 262 pass, 3 ignored, 0 fail |
| `npm test` | 60 files, 507 tests pass |
| `npm run build` | TypeScript and Vite pass |
| `cargo fmt --check`, `cargo clippy --workspace --all-targets` | clean |
| macOS package | not attempted; see the 0.28.0 record |

Results of the arms belong to S-011's dated account. No human acceptance, platform
qualification or writing result is claimed.
