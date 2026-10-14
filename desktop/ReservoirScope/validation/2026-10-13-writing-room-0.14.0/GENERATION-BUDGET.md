# Sustained generation budget qualification

Source-only qualification completed on October 13, 2026. No application, actual model,
or existing service was launched by this check. HTTP tests used temporary owned
loopback listeners; their responses are supplied fixtures.

The [bound receipt](rust-checks-01.json) records **167 core tests passed**, **181 desktop
tests passed**, and strict all-target Clippy with warnings denied. Two existing opt-in
natural-quota investigations were ignored; this run does not repeat their previous
qualification. All 95 captured source/fixture identities were unchanged between
the checks. The load interval was 2026-10-13T21:18:21.529781Z through 2026-10-13T21:23:17.904912Z.
Receipt SHA-256: `d9d4b836e616dc414a6c4e9ddb7f929b5b008e2563192dac21a2cb4db8caa554`.

## Contract and evidence

- New sustained sessions retain `outputTokens=1024` and `requestDeadlineSeconds=180`.
  Bounds are 256–2048 tokens and 60–180 seconds. An explicit context capacity must
  exceed the output budget; this does not prove prompt fit or full provider processing.
- Omitted historical fields still mean 256/60 and remain omitted on serialization.
  The frozen pre-change v3 segment decodes, reserializes byte-identically, preserves
  its SHA-256 and checkpoint hashes, and replays. Existing v1/v2/v3 prompt fixtures
  pass without changes. The prompt text contains no new output length directive.
- Core replay binds pending request budgets to its immutable specification. Rehashed
  pending/specification mutations fail validation; consistent final-state mutations
  still fail event replay. Desktop manifest-only mutations fail whole-bundle verification.
- An actual worker forwarded 1024/180 and context 8192 to its owned supplied provider.
  Two complete 900-token, multi-paragraph responses were physically saved and read back;
  observations 3/6 applied at 4/7, and the second prompt decoded the exact full first
  journal as memory. Export and paused recovery retained settings and text exactly.
- The production sustained HTTP entry point posted exact `num_predict=1024` and
  `num_ctx=8192` without an added JSON format. A deliberately delayed owned response
  returned successfully after 61 seconds, beyond the former 60-second ceiling. Separate
  stalled-header/body cases verified the same total-deadline mechanism at short test
  durations. This is not a 180-second timeout soak or a provider speed measurement.
- A healthy provider wait longer than the five-second wall-gap threshold did not
  trigger the independent watchdog; Pause accepted and saved its completed response
  while holding application until explicit continuation.
- Incomplete, length-cutoff, negative-count and over-selected-budget responses remain
  blocked. Reported counts are retained without clamping, including 2049 above the
  maximum selectable 2048. Cancellation, response-size limits, strict loopback scope,
  no redirects, and no automatic retry remain covered. Finite stage/action requests
  still use 256 tokens and 60 seconds.

## Reproduce

The exact commands and per-process SDK environment are in the receipt. The
[runner](run_rust_checks.py) uses exclusive receipt/log names; it will not overwrite
this evidence. Logs: [core](core-tests-01.log), [desktop](desktop-tests-01.log),
[Clippy](strict-clippy-01.log).

Implementation: [core contract](../../crates/reservoir-core/src/sustained.rs),
[transport](../../src-tauri/src/model_transport.rs),
[desktop orchestration](../../src-tauri/src/sustained.rs).
Focused evidence: [core budget tests](../../crates/reservoir-core/tests/sustained_generation_budget.rs),
[transport tests](../../src-tauri/src/model_transport_tests.rs),
[desktop lifecycle tests](../../src-tauri/src/sustained_tests.rs),
[legacy fixture provenance](../../crates/reservoir-core/tests/fixtures/sustained-prompts/v3-legacy-budget-provenance.json).

This establishes bounded implementation behavior under these tests. Completed real
journal continuity, prose quality, provider context processing and packaged interaction
remain separate prospective checks; no outcome is inferred from a larger configured
ceiling.
