# 2026-10-21 · Offline test of a content-carrying reduction (S-010 Part B, step 1)

**Subject:** the laptop apparatus' text→vector link. `probes/desktop_embedding_reduction.py`
embeds every retained entry of the three October 21 sessions with `nomic-embed-text`
(768 dims, laptop Ollama, loopback only, pulled with Mike's permission), projects each
embedding to 32 coordinates with a fixed SplitMix64-seeded Gaussian matrix, and compares
three representations of the same entries. Nothing here touches the beings.

| session | entries (n) | consecutive cosine, codec / embedding / projection | cosine to first entry, last entry, embedding / projection |
|---|---|---|---|
| 0.27.1 greedy | 43 | 0.9996 / 0.991 / 0.990 | 0.94 / 0.95 (flat 0.92–0.94 throughout) |
| 0.28.0 greedy | 9 | 0.9995 / 0.986 / 0.980 | 0.94 / 0.94 (flat) |
| 0.29.0 sampled | 14 | 0.9968 / 0.966 / 0.972 | 0.71 / 0.78 (falling from 0.95 / 0.98 at entry 2) |

Matched steps of the two sessions that share seed and noise (greedy vs sampled, n = 9
pairs): surface codec 0.975–0.988; embedding 0.82–0.89; projection 0.86–0.90. A tale
sentence against a recital sentence: embedding 0.52, projection 0.64, codec about 0.98
in the earlier trace.

Reading: the embedding, and its 32-coordinate projection, carry the content the codec
drops. The sampled session's drift into the traveler's cavern appears as a monotone
trajectory away from its first entry; the greedy sessions do not drift. Consecutive
entries remain similar under every representation, which is continuity, not a flaw.
The projection loses a little separation but keeps the trajectory and the arm split.

Other plausible reading: the drift could be length or register (longer, more
narrative entries) rather than topic; the matched-step split could be the recital's
digits. The frame-ablation arms will show whether the drift needs the frame.

Decision for Part B, step 2: add a codec choice to sustained sessions, surface (as
built) or embedding (projected, same 48-slot layout with 32 used), with a v3
mechanism identity that records the embedding model and digest, the projection seed
and the raw embedding hash. Replay of the numerical loop stays exact from the stored
held vector; the text→vector step becomes model-bound evidence, as the text already is.
