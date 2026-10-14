# Next bounded work: provider-reported context evidence

Read-only proposal, prepared October 13, 2026. No implementation, test execution, model request, admission check or process action accompanies this note. It does not change episode 02, its frozen criteria or the existing package.

The useful offline next step is to retain bounded provider usage metadata with explicit missingness. Call this **provider-reported context evidence**, not verified full-context processing. A model-authored answer, an exact retained prompt, or a returned token count alone cannot establish that every supplied character was processed or used.

## Present contract and gap

The [transport](../../src-tauri/src/model_transport.rs) constructs one nonstreaming chat request with the exact prepared prompt, explicit model, temperature zero, output ceiling and optional `num_ctx`. Sustained requests forward the retained output/deadline policy; finite requests keep their separate defaults. The decoder retains text, returned model, completion, stop reason and output count through the shared [LanguageResponse](../../crates/reservoir-core/src/session.rs). It currently drops prompt-evaluation counts and provider timings. The [journal object](../../src-tauri/src/sustained_store.rs) records the core pending object and separate host attempt timing. The existing [export inspector](../2026-10-13-measurements-0.15.0/check_real_model_export.py) therefore reports `providerPromptEvalCount: null` and `fullPromptProcessingVerified: false`.

Current official [chat documentation](https://docs.ollama.com/api/chat) describes `prompt_eval_count` as prompt tokens and `prompt_eval_cached_count` as tokens read from cache. The [usage reference](https://docs.ollama.com/api/usage) describes provider timings in nanoseconds. These are provider-reported fields; the cited current documentation is not proof that every field exists or has identical semantics in the selected installed 0.40.3 runtime. Missing cached-count support must remain unavailable. No local endpoint was queried for this review.

## Proposed first slice

1. Add a bounded transport-side usage envelope for sustained responses, separate from numerical acceptance. Retain optional prompt count, cached count and provider durations, plus exact request/prompt identity and the returned model identity. Preserve host monotonic duration separately; it is not the provider's clock. Bind the envelope to session, generation and actual attempt ID, including failed or incomplete received attempts where metadata exists.
2. Prefer a backend-only result wrapper around the existing core `LanguageResponse`; do not casually add serialized fields to that shared historical object. Existing core checkpoints, events and old journal hashes must stay byte-compatible. Any new exported evidence field needs an explicit compatibility rule: omitted old values remain absent, current readers validate the new bounded schema, and old readers may fail closed rather than silently reinterpret it. Adding optional fields to `JournalObject` still changes new object bytes and requires store/checker updates; a sidecar needs an equally explicit manifest binding. Select one format deliberately before coding.
3. Display **Reported prompt tokens** beside **Requested context capacity**, with unavailable/invalid metadata distinguished from zero. Label cached counts as reported, and do not subtract or add them to other counts without runtime-specific semantics. Exact prompt UTF-8 bytes/characters and decoded memory remain useful identities, not tokenizer counts. Do not introduce an automatic fit badge or prevent a valid response from saving solely because optional telemetry is absent.
4. Qualify the parser, persistence and IPC entirely offline first, using supplied envelopes and an owned synthetic HTTP fixture. This can close the evidence-retention gap even if real-model admission is refused; it cannot close the actual-provider coverage question.

## Focused qualification before any future real request

- Legacy v1–v4 exports and typed hashes remain unchanged with absent telemetry; no finite transport budget or numerical/save gate changes.
- Missing, zero, positive, malformed, negative and over-bound counts remain distinct. Unknown optional metadata yields an explicit diagnostic/unavailable value, not invented zero or a full-context claim. Define integer width and serialize any wide exact integer as a decimal string at IPC.
- Actual request serialization preserves the exact model/prompt/options and existing response byte cap, deadline, redirect/proxy restrictions and cancellation. One attempt's usage must not be attached to a later retry or replacement.
- Incomplete responses, compatibility-blocked responses, Stop, late response and recovery retain their existing outcome semantics. Usage never makes failed text eligible for a journal or feedback. No automatic resend, larger context request or model substitution follows from a low count.
- Immutable export/replay, store quotas, failed-write retry and old-reader behavior have focused positive and negative fixtures. Review tools explicitly separate provider metadata from independently verified numerical history.

A later separately authorized real check could compare exact runtime/template/tokenizer input accounting with the retained provider report, under its own unchanged admission and request budget. It would need to distinguish template tokens, cache reuse, truncation and output reservation. Until that runtime-specific reference exists, the defensible claim is only that reported usage is retained correctly. Full processing, attention, comprehension and causally useful memory remain different questions.

This proposal is independent of whether episode 02 runs. A refused episode remains refused and is not replaced by this engineering work.
