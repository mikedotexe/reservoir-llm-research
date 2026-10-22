# 0.33.0 — Entry-effect readout

**Unqualified local source candidate, October 21, 2026, on top of 0.32.0.** The last idea
from the [loop trace](../../analyses/2026-10-21-text-loop-trace.md), built at Mike's
request: numbers about what each entry did to the reservoir, shown to the model. It is
the first change to what the model is told about its own writing, and a different kind
of leading from a frame or a contract; the arms that use it are compared against
identical arms without the clause.

## What changed

- `SustainedEntryEffect { appliedStep, journalId, shift, alignment? }`. At an
  application step of a version that reports it, the core computes the step a second
  time from the same prior state, forcing and noise draws with no held feedback; `shift`
  is the L2 norm of the difference, `alignment` the cosine of that difference vector
  against the previous application's (absent for the first). The application frame
  carries it, the continuation keeps the last effect and its vector, and the next
  observation carries it.
- Two frozen prompt versions, `reservoir-journal-inert-effect-v1` and
  `reservoir-journal-inert-plain-contract-effect-v1`: the inert input with one clause
  appended to the optional-context line from the second entry on, "previous entry's
  effect: shift 0.42 · alignment with the one before +0.18". Nothing explains the
  numbers. The second sends the plain contract as the system message.
- Every earlier version's frames, observations, checkpoints and prompts are byte for
  byte unchanged (tested); the frontend recognises the two versions for reading
  recovered sessions and shows the effect inside the versioned observation.
  Version 0.33.0.

## Checks run on this source

| Check | Result |
|---|---|
| `cargo test --locked -p reservoir-core` | 248 tests pass, including `tests/sustained_entry_effect.rs` (2): the shift equals the counterfactual recomputed from the recorded frame, alignment appears from the second application, and earlier versions' frames, observations, checkpoints and prompts carry nothing new |
| `cargo test --locked -p reservoir-scope-desktop` | 260 pass, 3 ignored, 0 fail |
| `npm test` | 58 files, 503 tests pass |
| `npm run build` | TypeScript and Vite pass |
| `cargo fmt --check`, `cargo clippy --workspace --all-targets` | clean |
| macOS package | not attempted; see the 0.28.0 record |

Results of the arms belong to the study's dated account. No human acceptance, platform
qualification or writing result is claimed.
