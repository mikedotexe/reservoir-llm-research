# 0.30.0 — Embedding text reduction and S-010 frame arms

**Unqualified local source candidate, October 21, 2026, on top of 0.29.0.** Built for
[S-010](../../research/studies/S-010-frame-share-and-loop-share.md): a reduction that
carries content, and lean prompt arms that separate the persona layer from the per-turn
layer. Surface-codec sessions and every earlier mechanism identity are unchanged.

## What changed

- `SustainedCodec` on the specification: `surface` (omitted, as built) or `embedding
  { model, projectionSeed }`. Under the embedding codec the Tauri worker embeds each
  accepted reply through the loopback server's `/api/embed`, the core projects it with
  `codec::project_embedding` (unit-normalise, fixed SplitMix64 Gaussian matrix, scale to
  the surface codec's median RMS 0.74, clamp ±5, 32 of 48 slots) and applies no field
  modulation. The pending journal, the saved journal object and the language-received
  event carry the projected vector with a `FeedbackProvenance` (kind, model, digest,
  dimensions, embedding sha256, projection seed). Continuation validation and segment
  replay check the provenance against the session codec and reuse the stored vector.
  Mechanism identity `essentials32-splitmix64-embedding32-scaled-feedback-field-noise-v3`.
  An embedding failure is retained on the attempt like a provider failure and is retryable.
- Four frozen prompt versions: `reservoir-journal-inert-v1`, `…-inert-no-memory-v1`,
  `…-inert-plain-contract-v1`, `…-inert-inviting-contract-v1`. The inert input is a mode
  line, the earlier entry as reference, a "step N · fill X%" tag and a no-requirements
  line, under 400 bytes; the contract versions add a frozen standing contract sent as the
  system message (`Sampling.system`). Historical bodies are unchanged.
- `run_arm_from_env`, an ignored test in the desktop crate, runs one session headless in
  a private store with the real transport and stops it at a journal count or a bound.
- Advanced settings: text reduction choice with the embedding model name; journal
  evidence shows the reduction and provenance; the frame-arm versions are recognised for
  reading recovered sessions. Version 0.30.0.

## Checks run on this source

| Check | Result |
|---|---|
| `cargo test --locked -p reservoir-core` | 245 tests pass, including `tests/sustained_embedding_codec.rs` (3) and `tests/sustained_frame_arms.rs` (2) |
| `cargo test --locked -p reservoir-scope-desktop` | 259 pass, 3 ignored (the arm runner and two existing), 0 fail; new tests cover the embedding request body and reply decoding, the system message, and an embedding-codec session with a fake embedder whose first embedding fails and is retried |
| `npm test` | 57 files, 502 tests pass (two new files) |
| `npm run build` | TypeScript and Vite pass |
| `cargo fmt --check`, `cargo clippy` | clean |
| macOS package | not attempted; see the 0.28.0 record |

Results of the arms belong to the study's [dated account](../../analyses/2026-10-21-frame-arms.md),
not to this record; the headless control arm reproduced the morning app session's first
entry byte for byte, which is the sampler-seed design working as intended. No human
acceptance, platform qualification or writing result is claimed.
