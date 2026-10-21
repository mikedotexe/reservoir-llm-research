# 0.29.0 — Writing temperature with recorded per-attempt seeds

**Unqualified local source candidate, October 21, 2026, on top of 0.28.0.** Sustained
sessions can sample instead of decoding greedily. Historical sessions, finite
experiments and the request bodies they send are unchanged.

## Why

With fill settled in its band under 0.28.0, the first session's entries still converged:
verbatim sentence overlap between consecutive entries rose 0.35 → 0.52 → 0.81 within
four entries. The transport sent `temperature: 0` on every request, and the prompt
returns the previous entry in full, so greedy decoding reproduced it.

## What changed

- `LanguageConfiguration` gains an optional `temperature` (0–2). Omitted values
  serialize as before and mean greedy decoding, so historical configurations, pending
  records and checkpoints keep their exact bytes and hashes.
- The transport takes a `Sampling { temperature, seed }` per request. Temperature zero
  sends the historical body; above zero it sends the temperature and a seed.
- The seed is `sampling_seed(session_seed, attempt_id)`: one SplitMix64 output of a
  state unique per session seed and attempt, top bit cleared. Distinct per attempt,
  reproducible from the session seed, never stored in checkpoints.
- Each journal object records `temperature` and `samplingSeed` (decimal string); the
  store's conflict and replay checks compare them, and the pending-language record
  carries the temperature under the existing continuation guard.
- Fresh Ollama selections propose 0.7; the control sits under Advanced settings →
  Writing limits, with validation and the journal evidence showing the sampling used.
- Version 0.29.0.

## Checks run on this source

| Check | Result |
|---|---|
| `cargo test --locked -p reservoir-core` | 240 tests pass, including the new `tests/writing_temperature.rs` (3 tests: omitted-temperature serialization and bounds, seed determinism and distinctness, pending-record guard) |
| `cargo test --locked -p reservoir-scope-desktop` | 256 pass, 2 ignored, 0 fail; two new tests cover the request body under greedy and sampled settings and the provider receiving per-attempt seeds only for temperature sessions, with the journal objects recording them |
| `npm test` | 55 files, 500 tests pass (one new file; one existing expectation now includes the proposed temperature) |
| `npm run build` | TypeScript and Vite pass |
| `cargo fmt --check`, `cargo clippy` (both crates) | clean |
| macOS package | not attempted; the 0.28.0 record explains the host's thin-LTO proc-macro failure, unchanged here |

No human acceptance, platform qualification or writing result is claimed. Whether
sampling keeps the entries from converging is the next observation, not a result.
