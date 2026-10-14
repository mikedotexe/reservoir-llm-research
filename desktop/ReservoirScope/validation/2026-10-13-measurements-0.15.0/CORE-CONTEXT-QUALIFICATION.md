# V4 measured context: source qualification

The frozen Rust source passed **174 core tests**, **182 desktop tests**, and strict
all-target Clippy with warnings denied. Two existing opt-in natural-quota probes were
ignored; they are not claimed as rerun here. The [receipt](rust-checks-01.json) binds
99 source/fixture identities, unchanged before and after the checks. Load interval:
2026-10-13T22:27:24.938796Z through 2026-10-13T22:32:25.664047Z. Receipt SHA-256:
`e732f8e90fa84c3a4c54ff3fedc21e9b120db56bfb4e416883311fded27affce`.

No application or actual model was launched for this qualification. The existing
transport regression used an owned ephemeral loopback fixture, including a delayed
61-second reply. The fixture generator used supplied prose and a new private output
directory. These are implementation checks, not a new writing-quality result.

## Retained contract

- New sessions select `reservoir-journal-v4` with observation
  `reservoir-and-sensory-v2`. The open invitation remains: no required topic,
  measurement, heading, length or form. V1–v3 prompt bytes, golden fixtures and
  historical typed serialization remain unchanged; absent prompt version still means v1.
- A fixed-size optional `previousMeasurements` snapshot is captured from the previous
  reached numerical observation before that reference is replaced. It is independent
  of the latest saved/applied prose memory. The first observation has unavailable
  prior scalars, never fabricated zeros. V4 rejects a previous step without its scalar
  snapshot; old contracts omit that new field and preserve exact bytes/hashes.
- Eight rows expose RMS, L2 norm, largest sensory covariance eigenvalue, reduced fill,
  top-eight head/shoulder/tail shares, and normalized entropy. Differences are
  current minus previous; percentage rows use percentage-point differences. State
  coordinate L2 distance remains separate from the difference in L2 norms.
- The same core helper supplies the prompt and the additive inert journal
  `measurementReference` DTO. Old journal references can retain a previous step while
  prior scalar values remain unavailable. The view stays bound to the entry's writing
  step across restore and subsequent numerical application. A missing optional
  reference does not hide prose or raw evidence.
- Full current vectors/spectrum and exact JSON-quoted prior journal text remain
  supplied. No quality grading, prose rewriting or new save/feedback gate was added.
  Numeric endpoints do not establish a trajectory, oscillation, stability or cause.

## Checks that bear on the change

[Seven new core tests](../../crates/reservoir-core/tests/sustained_measurement_reference.rs)
cover unavailable first references; frozen initial/memory prompts and explicit retry;
exact signed differences; failed/skipped step 6 remaining the numerical prior at step
9 while memory still refers to saved step 3; malformed boundary/version/prompt
rejection; full replay rejection of self-consistent rehashed prior-value tampering;
honest missing historical scalar data; and byte-identical numerical frames between
v3 and v4 under identical supplied responses.

[The new desktop case](../../src-tauri/src/sustained_tests.rs) compares all eight rows
with the core helper for both v3 and v4, verifies them through physical saved journal
history and paused recovery, and checks that advancing to step 7 does not change an
entry written at step 6. Existing historical prompt/budget, long-text save/memory,
recovery, quota and transport tests also ran in the full suites.

A checkpoint validates bounded shape and local identity, not independent truth of a
past scalar assertion. The checked chain from genesis supplies that provenance:
replay reconstructs the prior snapshot from preceding state. This distinction remains
the same as the existing anchored-segment verification contract.

The new [first prompt fixture](../../crates/reservoir-core/tests/fixtures/sustained-prompts/v4-observation-10.txt)
is 4,445 UTF-8 bytes, SHA-256
`26bae96991e12bb591ba517c46345aeac167abbbdaf79858c514a35b8986f75f`.
The [memory fixture](../../crates/reservoir-core/tests/fixtures/sustained-prompts/v4-memory-20.txt)
is 4,829 bytes, SHA-256
`d51753e1eddd68fd193ba46da49e6f909aaebdef328471ddf79e3b134b10c2c0`.
[Provenance](../../crates/reservoir-core/tests/fixtures/sustained-prompts/v4-provenance.json)
records the supplied-prose generator. These lengths are not tokenizer counts or
proof of full provider processing. More explicit data does not establish that future
writing will be accurate or that creative continuity will improve.

Exact commands, SDK environment, log hashes and source identities are in the receipt.
Logs: [core](core-tests-01.log), [desktop](desktop-tests-01.log),
[Clippy](strict-clippy-01.log). The [exclusive runner](run_rust_checks.py) preserves
these outputs rather than replacing earlier qualification evidence.
