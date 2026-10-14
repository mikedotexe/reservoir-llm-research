# V5 review addendum: final test-only correction

2026-10-14 UTC. The original [V5-REVIEW.md](V5-REVIEW.md) is preserved unchanged
(SHA-256 `382ca970d3f950176063089088d6f9f1362cbe39532de6d38caf02abefa3523c`).

After the second retained Rust run, the core owner corrected a test that forbade
the generic substring `journal-`: it also matched the required
`reservoir-journal-v5` version header. The forbidden item now names the old
provenance label `Prior journal ID:`. The separate adversarial-memory test still
checks that the actual journal entry ID and hash are absent from the measurement
scaffold. Reading those assertions confirms that the correction removes the
false match without discarding the intended provenance-exposure checks.

The final `crates/reservoir-core/tests/sustained_continuing_prompt.rs` SHA-256 is
`ff9e1c93cb0dcc0c52ec849dab4c4f73ab39b9966dd10adb81c126a2cebd5a58`.
The production `crates/reservoir-core/src/sustained.rs` still has SHA-256
`073d324a17eab74e0d80d738213afb8d1b353102e2c7a5a23d0875077d3baa5b`.
The owner reports no template or fixture changes. The earlier default-based
test corrections remain documented in the original review.

I read the parent's [focused-core-01.log](focused-core-01.log), SHA-256
`abb36a47023358aa8ec50bf87838122ad996ac2c9ed3dd4c92784d2d653eafaa`:
the four targets report **33 passed, 0 failed** (9 continuing-prompt, 5 generation
budget, 12 historical/current prompt, and 7 provider-evidence tests). The earlier
message saying 40 was a count error, corrected against the log. I did not execute
these tests or start another suite. The parent's full third run was still in
progress when this addendum was prepared; its own receipt records the outcome.

No new production issue was found in this narrow readback. This addendum makes
no packaged-UI or model-writing claim and changes no earlier receipt.
