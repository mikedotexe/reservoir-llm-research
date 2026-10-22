# 0.36.0 — State-chosen memory and the watchdog warm-up

**Unqualified local source candidate, October 21, 2026, on top of 0.35.0.** Part B of the
planning pass with Mike for [S-011](../../research/studies/S-011-self-observation-stack.md):
the recurrent state, not the clock, chooses which earlier entry a turn returns, closing the
loop through content in the reservoir-to-text direction without adding a word to what the
model is told. And the fix the first ladder twins asked for: a warm-up before the difference
channel's watchdog counts fill variance.

## What changed

- `memoryPolicy` on the specification: `latest` (default, as built), `state-aligned`,
  `random`. Under a choosing policy the continuation keeps `appliedEntries`, a bounded ledger
  (256, oldest dropped) of applied entries with their identity, path, application step and
  the 32-coordinate effect the entry had at its application (the 0.33.0 counterfactual, now
  computed whenever a policy or a prompt version needs it; only the effect prompt versions
  show it to the model). At each turn boundary `state-aligned` returns the entry whose effect
  has the largest cosine with the observing state (ties to the most recent; an entry with no
  direction loses; when none has one the latest is returned); `random` returns a seeded
  uniform draw (`SplitMix64(seed ^ MEMORY_CHOICE_SEED ^ step)`), the control.
- The pending read names the choice (`choice`: policy, entry id and hash, path, application
  step, age in entries, candidates, score) and carries no expected text; the worker rereads
  the chosen file and `confirm_memory` matches its id and hash before the prompt is built.
  The prompt is the one the version always built; `memoryChoice` rides on the pending
  language, the journal object and the journal detail, `chosenMemory` on the continuation.
  Under `latest` the pending read, prompt, journal, checkpoint and frame bytes are unchanged.
- `validate_state` recomputes the choice from the ledger and the state and rejects a pending
  read the state would not make, a ledger that does not end with the latest applied entry,
  and any ledger or choice under `latest`; restore across a choice is byte-identical.
- `differenceWatchdogWarmup` (default 0, as built, so 0.35.0 bundles replay exactly): steps
  before the watchdog's fill ring counts. The four gain-0 twins of the first ladder showed
  the start-up climb alone gives a trailing 90-step fill spread of 14.6–16.9 points at step
  90 against the default bound of 10; the validator holds the ring empty through the warm-up.
- Advanced settings gain "Earlier entry returned" and the warm-up field, with their
  explanations. Version 0.36.0. A 0.35.0 reader rejects a bundle that carries either field.

## Checks run on this source

| Check | Result |
|---|---|
| `cargo test --locked -p reservoir-core` | 262 tests pass, including `tests/sustained_memory_choice.rs` (5) |
| `cargo test --locked -p reservoir-scope-desktop` | 262 pass, 3 ignored, 0 fail |
| `npm test` | 60 files, 507 tests pass |
| `npm run build` | TypeScript and Vite pass |
| `cargo fmt --check`, `cargo clippy --workspace --all-targets` | clean |
| macOS package | not attempted; see the 0.28.0 record |

Results of the arms belong to S-011's dated account. No human acceptance, platform
qualification or writing result is claimed.
