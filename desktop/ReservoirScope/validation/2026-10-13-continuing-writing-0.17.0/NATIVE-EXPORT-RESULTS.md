# Native synthetic export: continuing-writing v5

The original 0.17.0 native export passed the pinned production verifier and the independent fixture joins. It retains step 50, four saved journals, 22 segments and 28 files. The fifth response is incomplete and has neither a journal nor an application. This is a synthetic wire-context and persistence qualification, with no real-model writing-quality result.

The [original export receipt](original-export-evidence-01.json) binds the unchanged bundle `target/qa/0.17-continuing-writing/exports/sustained-1791941918315-1-1-76`, session `sustained-1791941918315-1`, generation `1`, revision `76`. Its wrapper phase is `attemptBlocked`; the retained core phase is `blocked`. The manifest SHA-256 is `c69b66b82fa74d42a1fbe27bf2f4feb2aff81f202bc1bf1697fdcc0a42f2d360`. Total bundle size is 1,666,849 bytes.

The exact [0.17 package pin](../../target/qa/0.17-pinned/reservoir-scope-desktop), SHA-256 `7d46719838495b7a9ba57eea69ac9c940bb81f2fdc47cd12b761d97bb472d081`, replayed genesis, contiguous numerical/events, journal saves and applications with exit 0. The executable and original export remained unchanged. [The checker](check_fixture_export.py) additionally matched the exported prompts and responses to the fixture's exact HTTP request, prompt and response hashes.

| Attempt | Writing step | Optional provider input-count evidence | Saved | First application |
|---|---:|---|---|---:|
| 1 | 10 | Reported `9007199254740993` | Yes | 11 |
| 2 | 20 | Absent | Yes | 21 |
| 3 | 30 | Unusable: `wrongType` for string `"2450"` | Yes | 31 |
| 4 | 40 | Reported `18446744073709551615` | Yes | 41 |
| 5 | 50 | Reported `321`; incomplete, stop reason `length` | No | None |

The optional count never overrides completeness or save eligibility. Four exact full-memory reads link each later attempt—including the unsaved fifth—to the preceding saved and applied journal. Each saved journal applies once; the fourth journal remains the held feedback through step 50.

All five prompts use `reservoir-journal-v5`. The checker verifies the compact scaffold separately from the quoted historical text, including the current/prior RMS and sensory fill rows, their signed deltas, and the nonnegative state-coordinate distance. The full `reservoir-and-sensory-v2` observations remain retained, including state, sensory spectrum and measurement reference data. Exact numerical prompt formatting is qualified by production replay; the independent checker adds structural exposure and exact historical-text checks. The first prompt has no earlier journal. The four later prompts retain the entire preceding journal as one JSON string.

## Closed fixture retention

The [retention receipt](fixture-run-01/retention.json) binds eight byte-exact copies (7,552 bytes total) in `fixture-run-01`. All source files remained unchanged during copying. The retained [endpoint identity](fixture-run-01/endpoint.json) identifies only the owned synthetic fixture at `http://127.0.0.1:60168`, PID 6744, using unchanged helper SHA-256 `a4ea70f115fe569455cf8d9ae34e70eb3a79d63d187fc431ec8cae9a0ddd7fdb`. The fixture name still contains `0.16` because this tranche reuses its exact qualified replies and helper; it does not label the app version.

The closed [request log](fixture-run-01/requests.jsonl) records exactly one successful `GET /api/tags`, five accepted `POST /api/chat`, five HTTP 200 response writes, and no rejected POST or extra request. Its prefix inspected by the original export checker is unchanged; the sole later append is the terminal lifecycle row. The [stop request](fixture-run-01/stop-request) is timestamped 2026-10-14 01:40:53.862506 UTC. The fixture recorded `explicit-stop-file` at 01:40:53.967787 UTC after 172.724753 monotonic seconds, within its 900-second lifetime. Root reported the owned tool exited 0. This retention audit made no independent process-absence query, signal, service request or UI action.

Socket-write completion alone is not evidence of app acceptance; the export joins provide that separate evidence. Synthetic provider counts do not establish actual tokenization, complete context use, model understanding or scientific accuracy. This run adds no GPU, endurance, crash, power-loss, cross-platform or real-model quality qualification. Clean-quit recovery and the second export are separate evidence from this original export.

Original export receipt SHA-256: `c1e727fd9950eca13b3c3c6c5f171052c5dbad1b64bc9d07f885fbe91955c8bf`.

Fixture retention receipt SHA-256: `87ec18d6cba5e5911c7a52f57b24256b2e2368cf731be9ae9890c8705e05263c`.
