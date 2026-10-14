# Actual sustained UI exports — offline qualification

The two explicit UI exports passed the final production whole-bundle verifier, and all 26 corrupted copies were rejected. Original file inventories and the pinned verifier remained unchanged. No model or provider was contacted by this check.

| Export | Numerical steps | Saved journals | Segments | Result |
|---|---:|---:|---:|---|
| `sustained-1791904148347-1-1-333` | 181 | 30 | 149 | Passed |
| `sustained-1791904526118-2-2-19` | 6 | 1 | 7 | Passed |

The final executable was copied before use and checked before and after every invocation: SHA-256 `f68a3752a628edf11ac6161a26e6979bb22dcf4c3ee1c63f10add2cea86ab40d`. Each original passed `--verify-sustained`, which checks exact seeded genesis, contiguous event/numerical replay and journal/save/application consistency. This new format has no claim of Swift-format verification.

All 31 saved journals matched a unique owned fixture request by exact retained prompt and response-text SHA-256. Request bodies matched the selected model, one user message, `stream: false`, context 4096, token cap 256, temperature 0 and no action-JSON format. Compact request-body serialization also matched the fixture's recorded raw body hash. Retained recurrent state and sensory observations matched their recorded frames. Each noninitial journal's memory was the exact preceding saved-and-applied journal, including text, identity, hash, path and application boundary. The first export preserves seed `18446744073709551615` exactly and contains all 30 next-step applications.

Fixture request 31 was held for 23,248 ms between fixture receipt and handler completion; the app retained a 23,251 ms transport duration. Its journal was observed at step 3, durably saved into a prepared checkpoint, then applied at step 4. The UI's Pause interaction is reported separately; this bundle itself establishes the saved/prepared/application ordering, not an authenticated wall-clock Pause event.

Fixture request 32 corresponds to attempt 2 at step 6. The final bundle retains `languageStarted` followed by `languageCancelled` with the explicit-Stop reason, and contains zero accepted responses, saves or applications for that attempt. The fixture later recorded a complete response with text SHA-256 `a96176c333312a7d11b4abe4cc42a1469e7630e0871fafebb5d5a5325e0dd464`; that response is absent from every retained journal. The fixture log proves handler completion, not delivery to a cancelled client. No exact cancellation wall time is present in the portable event.

Thirteen controls were applied to each fresh copied bundle: altered journal text; altered configured-model metadata with recomputed byte anchors; altered prompt with recomputed anchors; negative transport duration with recomputed anchors; manifest clock, journal-count and seed changes; removed or reordered segments; a valid non-genesis checkpoint substituted as genesis with recomputed anchors; changed recurrent frame state with recomputed anchors; reversed language-event order with recomputed anchors; and a removed journal. All were rejected. These checks do not make SHA-256 an author signature or authenticate a provider's execution.

Evidence: [full receipt](actual-ui-export-qualification.json), [source binding](actual-ui-export-source-binding.json), [command output](actual-ui-export-qualification.log), and [reusable checker](check_sustained_ui_exports.py). The checker snapshots the append-only fixture request log, so later requests can be qualified without changing this receipt. Temporary mutated copies and the pinned binary are under `target/qa/0.12-proof/initial-exports`.
