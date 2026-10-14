# 0.14.0 — bounded room for open writing

This candidate gives sustained sessions explicit output and request-time budgets. New defaults are 1,024 output tokens and 180 seconds; new local-model setup requests 8,192 context tokens. Advanced settings allow 256–2,048 output tokens and 60–180 seconds. These are resource ceilings, not requested prose lengths. The v3 prompt is unchanged.

Historical records with omitted budget fields retain 256 tokens and 60 seconds, including exact typed serialization and segment hashes. Explicit budgets are immutable and bound to configuration, genesis, pending requests, whole-chain replay and the actual transport. Finite stage/action generation keeps its previous bounds. Context must exceed the output budget when explicit; that check does not establish token fit or full provider processing.

The prospective [protocol](PROTOCOL.md), [run plan](run-plan.json) and [evaluation freeze](evaluation-freeze-01.json) define one owned Gemma3:4b rehearsal with four opportunities and no retry, skip, replacement, or extension. Read the resulting execution and reading receipts separately from source tests. The prior 0.13 cutoff remains intact.

## Executed result

The native Gemma3:4b rehearsal completed **four journals**, all provider-complete `stop` outcomes: **329, 367, 323 and 358 output tokens**. All saved/read back and applied at **31, 61, 91 and 121**; all three subsequent prompts retained the exact latest eligible prior text. The run ended at its original 121-step/four-attempt bound, with 19 segments and 181,254 milliseconds of retained running time. No retry, skip, replacement or extension occurred.

[Read the exact journals](JOURNALS.md) and the [mechanical/reading account](REAL-MODEL-RESULTS.md). The first prompt/observation match 0.13 exactly and its prior cutoff is a prefix of the completed first journal. The later prose develops connected imagery while making some stale or incorrect literal measurement claims. Saving/continuity pass; general factual accuracy is not established. The review does not judge metaphor as measurement or prescribe the topic.

The [native walkthrough](MACOS-UI.md) passed setup, short minimized continuation, independent older-entry selection, export and clean relaunch/paused recovery. Resume remained disabled at the exhausted budget. All 24 non-manifest files stayed identical across the two 25-file exports; only phase/generation/revision changed. [Recovery receipt](native-recovery-01.json).

The [revised owned supervisor](CLEANUP-RESULTS.md) stopped its exact group with one TERM, no KILL and verified quiescence before reap. Its retained log has four generation POSTs and one metadata GET, all HTTP 200. The Beings were untouched; previous failed supervisor outcomes remain retained.

## Source checks

- Frontend: 332 tests and TypeScript/Vite production build passed, source unchanged. [Receipt](frontend-checks-02.json). The earlier copy-assertion failure is retained in check 01.
- Rust: 167 core and 181 desktop tests passed; two existing optional natural-quota tests were unrun. Strict all-target Clippy passed. The production sustained HTTP path accepted a response after 61 seconds. [Receipt](rust-checks-01.json), [contract note](GENERATION-BUDGET.md).
- Evaluation checker: 22 synthetic tests passed. [Receipt](checker-tests-02.json).
- Owned helper: 27 mocked tests passed. [Receipt](owned-helper-tests-01.json). [Supervision scope](OWNED-SUPERVISION.md).
- Independent read-only Rust review found no blocker in budget propagation, legacy hashing, context validation, completeness or finite-route separation. [Review](RUST-REVIEW.md). Package and actual-run receipts are recorded separately.

## Package and legacy compatibility

- [Source-bound build](package-build-01.json), [pre-UI qualification](qualification-before-ui.json), [archive check](archive-check.json), and [post-documentation continuity](source-continuity-final.json).
- Local macOS arm64 preview archive: `target/release/bundle/macos/ReservoirScopeTauriPreview-0.14.0-macos-arm64.tar.gz`, SHA-256 `032d9353d97688128e450468fb90c454f46d3b3f4fe1d9dcae814b37c15f8348`.
- Executable SHA-256 `87eb89c76200603b1cb68f34e5b5deddc54dbfa5042530ab0c9787ca56606fa4`. Local ad-hoc codesign verification passed; no notarization claim.
- Exact 46-file package and all archive file bytes checked; 42 resources staged after frozen-reference verification. The previous 0.13 archive remains unchanged.
- Pinned 0.14 CLI replay passed the old [held v3 bundle](legacy-v3-held-0.13.0-on-0.14-01.receipt.json) and [completed v1 bundle](legacy-v1-completed-0.12.2-on-0.14-01.receipt.json), with no model contact or source-record changes.

## Next bounded work

Investigate stale measurement references while retaining open-ended writing, then separately qualify longer runs with these budgets. Avoid automatic rewrites or a required status-report format. Provider/context coverage and model diversity need their own receipts.

## Scope

This is a macOS engineering qualification of a short, bounded writing episode, not a model success-rate estimate, isolated causal comparison, creative-quality score, emergence claim or new long-duration measurement. Windows/Linux, GPU energy measurements and broader collaborator acceptance remain open. The Beings' processes, prompts, workspaces and services are outside this work.
