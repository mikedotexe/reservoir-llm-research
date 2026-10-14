# Final source review — open writing and version compatibility

**No must-fix defect found in this scoped read-only review.** Source identities were captured at 2026-10-13T20:34:39.246445+00:00. This reviews the final 0.13.0 source paths for the user's open-ended writing intent, historical compatibility and the incomplete-response boundary. It is not a new model, UI, service, build or test run.

## Findings

- **The new invitation leaves the writing open.** [Core prompt v3](../../crates/reservoir-core/src/sustained.rs), line 1117, offers choice of attention, topic, form and continuity. It requires no metric, step heading, word count or literary form. Voluntary factual claims are distinguished from inference and expressive metaphor; creative and subjective prose is allowed. The prompt explains the actual reduced-feedback/full-text-memory paths and separates the external reservoir from language-model activations or training. The [transport](../../src-tauri/src/model_transport.rs), line 271, sends this prepared prompt directly; it adds no former v2 writing assignment.
- **Version selection preserves historical meaning.** [Core](../../crates/reservoir-core/src/sustained.rs), lines 18, 53, 91 and 1024, selects v3 for fresh defaults, retains exact v1/v2 prompt functions, interprets an absent serialized version as v1, omits legacy serialization, and rejects unknown enum values. [Backend configuration](../../src-tauri/src/sustained.rs), lines 50 and 106, carries the retained choice into the core. [Whole-bundle replay](../../src-tauri/src/sustained_store.rs), line 997, derives genesis from that exact configuration; relabelling cannot reinterpret an existing chain.
- **Memory and ownership remain explicit.** V3 JSON-quotes the complete prior text and places current numerical evidence in a separate block. [Prompt reconstruction](../../crates/reservoir-core/src/sustained.rs), line 1299, binds exact observation, memory and version. The [frontend controller](../../src/myReservoirController.ts), lines 64 and 145, rejects same-generation version changes and mismatched journal detail. [Reading](../../src/MyReservoirJournals.tsx), line 12, preserves whitespace and renders prose inertly rather than executing HTML/Markdown.
- **A cutoff cannot become feedback.** [Transport decoding](../../src-tauri/src/model_transport.rs), line 283, marks length-limited or otherwise incomplete output incomplete. [Core settlement](../../crates/reservoir-core/src/sustained.rs), lines 793 and 1204, retains the response event and blocks the attempt rather than creating an eligible journal. [Backend boundary handling](../../src-tauri/src/sustained.rs), line 970, holds execution; [UI status](../../src/MyReservoir.tsx), line 26, describes the absent accepted journal/feedback and lack of automatic retry. Save/readback and next-step application remain separate gates.

## Evidence and limitations

The existing [core receipt](core-source-checks-02.json) records **162 passing tests and strict all-target Clippy**, with unchanged captured files. Its SHA-256 is `e25d47d2776031726baa22801afcf73972f142e504ad37c132116246b91b77c1`. Current core runtime, prompt tests and SUSTAINED documentation still matched that receipt when checked for this audit. [Prompt tests](../../crates/reservoir-core/tests/sustained_prompts.rs), lines 103, 130, 397 and 507, cover legacy/default/unknown versions, frozen v2 bytes, free-form metric-free text, quoted memory/retry and serialized save/application gates. [Desktop tests](../../src-tauri/src/sustained_tests.rs), line 1146, cover v1/current save, exact export, paused restore and application; v2 exact-prompt and restore coverage is in the core tests. No tests were rerun for this review.

The unchanged **256-token output cap** is a practical resource constraint, not a requested literary length. Parent-reported first-attempt cutoff at step 30 with no journal/application does not establish successful real v3 journaling, a completed feedback/memory loop, writing quality, agency or emergence. The actual prose was not inspected during this source audit. Native pointer/export behavior and the separately authorized passive-copy response review require their own evidence; this source verdict does not qualify those paths.

## Reviewed source identities

| Source | SHA-256 |
|---|---|
| [Core prompt, version and feedback gates](../../crates/reservoir-core/src/sustained.rs) | `56ace3c535e7a66ee41cb7be8af4eccd9a62645d601c0d1c669e879cb1fd3682` |
| [Backend configuration and lifecycle](../../src-tauri/src/sustained.rs) | `d156c4f54ac9b9c346577550c3950c5bd00d5b02e9a5b4136b5ce80c15abeb84` |
| [Whole-bundle verification](../../src-tauri/src/sustained_store.rs) | `4dcf74443ce77c7e9e94cd2536002cdb3e6f410edec3f2e260794afbb40c37b6` |
| [Local-model request and response parsing](../../src-tauri/src/model_transport.rs) | `304edd5854eb2c639174c115b5789d4645355c778bcf08051f8e88a5a0bf2db0` |
| [Frontend version types and defaults](../../src/myReservoirTypes.ts) | `140cd00a07fc96be0a2f4b8de2b70ad312fd77aae8e2a5ebd8627917ffbd50ba` |
| [Frontend snapshot and journal ownership](../../src/myReservoirController.ts) | `68abbbbf3cb012773875e3ca61b961fcafeab1d329eca6161921a724268c5687` |
| [Boundary status and controls](../../src/MyReservoir.tsx) | `4fa30ecf4076f56bfdc742704c86c7567d16e189548419f37de6dc50933242d9` |
| [Inert full-text journal rendering](../../src/MyReservoirJournals.tsx) | `bb8d1353ece984956c1ad396c01cf56e6f559107e566e95a27ba33a388801e0b` |
