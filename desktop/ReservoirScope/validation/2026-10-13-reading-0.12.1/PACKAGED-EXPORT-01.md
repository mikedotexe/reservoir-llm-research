# 0.12.1 native export: offline verification

The exact 0.12.1 native export passed numerical/event replay and independent joins against the owned synthetic fixture log. This is the package with the subsequently observed historical-alert presentation defect; none of these results claims that the later 0.12.2 fix was exercised.

The original export is `target/qa/0.12.1-reading/exports/sustained-1791918426303-1-2-56` under `desktop/ReservoirScope`. It retains 31 numerical steps, three journals and 16 segments (1,192,002 bytes). Its manifest SHA-256 is `1b6fe0ee3307f967b5e81b39dab3c5981922fa398869e02358506fef93d99f87`; checkpoint SHA-256 is `43c9761b890375aeb38cd5aaf05a6542df628685c7f043fc7dfeb55582168b76`.

## Exact package and verifier

Before the package path could be overwritten, the executable was copied to `target/qa/0.12.1-reading/export-verification-01/reservoir-scope-desktop-0.12.1-pinned`. [The pin receipt](packaged-export-01-pin.json) records 16,783,472 bytes and SHA-256 `e66533cfd3371d8cdf80ce9969fae702b957987fad2a1a12974945c33842f43c`.

The [CLI receipt](packaged-export-01-cli-receipt.json), [stdout](packaged-export-01-cli-stdout.json) and [timing output](packaged-export-01-cli-stderr-time.txt) retain the actual `/usr/bin/time -l <pinned executable> --verify-sustained <immutable export>` invocation. It passed at 19:12:06.365306–19:12:06.937034 UTC on October 13, with measured wall duration 0.57174675 seconds and verifier-process peak RSS 13,090,816 bytes. These resource figures describe this offline verifier process, not the GUI or provider.

The [package qualification](qualification.json) and [pre-UI identity](package-before-ui.json) bind the original package. [The source inventory](source-before-build-final.json) has SHA-256 `f0c0f31e08b6a40016ab64665a79127f14229de75651988c63be03a6e79af362`. The 0.12.1 archive SHA-256 is `90751609736ee70a0d3f88a218fd2ff4a15259a4d49e61b7d3ca3bde778cfb7d`.

## Failed attempt, successful writing and memory

The [independent evidence receipt](packaged-export-01-evidence.json), SHA-256 `ba43bbad14d523db4f510b1cc4a94718a50dc0a92c922118ca00f92b16b50512`, passed all 21 explicit checks at 19:17:46.281446–19:17:46.346229 UTC (0.064678291 seconds measured wall duration). It retains source identities, the complete original-export inventory, a fixture-log prefix snapshot and exact request/journal/application joins.

| Fixture request | Attempt | Observation | Outcome | First application | Prompt memory |
|---|---:|---:|---|---:|---|
| 243 | 1 | 10 | HTTP 503 failure; no accepted response, saved journal or application | None | None |
| 244 | 2 | 10 | Explicit retry; response saved exactly once | 11 | None |
| 245 | 3 | 20 | Response saved exactly once | 21 | Full text and hash of the step-10 journal |
| 246 | 4 | 30 | Response saved exactly once | 31 | Full text and hash of the step-20 journal |

The failed attempt and retry used the exact same held observation and prompt, with separate attempt identities. All four language-start events occur once. The export contains exactly three accepted responses, three unique save receipts, three unique next-step applications and two memory-confirmation events. All numerical steps 1–31 occur once. The final record preserves the configured 61-second duration and four-attempt maximum, `budgetReached`, and 39,592 milliseconds of retained active time; this is not a 61-second elapsed-run claim.

The historical fixture checker was reused unchanged for accepted journals. Its rejected-request branch assumes explicit cancellation, so request 243 was excluded from that helper's input and independently checked against the actual `languageFailed` and `retried` events. The fixture's failure mode does not emit its normal response row; that absence does not mean no HTTP response was sent. The app retains the HTTP 503 failure. No original record or log was edited, and no corruption-control copies were needed for this follow-up.

## UI scope and limits

[The actual packaged UI account](PACKAGED-UI.md) and [final UI receipt](packaged-synthetic-final-ui.json) retain the native create, failure/retry, close review, restore, explicit resume, selection and export observations. The old step-10 entry was selected after the finite bound; this short check does not independently demonstrate stable selection while new entries arrive. The separate multi-hour 0.12.0 evidence owns that earlier workload.

The 0.12.1 UI displayed a historical 503 diagnostic as an active alert in later prepared/budget-only states. This verified export preserves that diagnostic as history; its integrity pass does not validate the presentation. The distinct 0.12.2 package owns the correction and its later checks.

All verification here was offline: no UI, live store, service endpoint, model, or process controls were used. The original export inventory, pinned executable and captured request-log prefix remained unchanged. The provider was a synthetic fixture, not Gemma. Replay establishes internal numerical/event and saved-text consistency; it does not independently prove physical power-loss durability, model learning, prose quality, or long-run performance of 0.12.1.
