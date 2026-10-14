# 0.12.2 native historical-alert regression

The actual packaged regression completed, and its immutable export passed offline replay and all 20 source/save/application checks. The current-failure alert appeared for the actual HTTP 503, then stopped presenting that old failure as current after a successful retry. The historical diagnostic remains retained in the exported record.

This is a short owned synthetic-provider check, separate from both the earlier 0.12.1 package and the subsequently planned real Gemma run. Its package executable SHA-256 is `2fa824855d1172ebf707b4f1ce5f50d2c3eb74ab4aeeb437d41dc566f818db8d`; [package qualification](qualification.json), [pre-UI identity](package-before-ui.json) and [source inventory](source-before-build-final.json) bind the exact candidate.

## Actual native sequence

The parent agent operated the native app and retained these observations; the independent export checker did not control the UI.

1. [The prospective plan](native-regression-plan.json) selected a two-step, two-attempt session with cadence 1, 61-second maximum, 1-second pace and 32 MiB storage. Request 247 returned the owned fixture's HTTP 503 failure; the failure was visibly actionable.
2. Explicit Retry dispatched request 248 at the same held step. Cmd-Q opened the close review while it was waiting. [The release receipt](native-regression-release.json) binds only that owned held request and its body hash.
3. After release, the journal saved durably at step 1, pending application at step 2. The close review showed the paused prepared boundary without the old 503 as a current alert. The user-facing **Checkpoint and quit** action was actually exercised. [The quit receipt](native-regression-checkpoint-quit.json) records one retained journal, step 1, generation 1/revision 14, and absence of the exact app process.
4. A fresh launch was idle. Inspect and Restore returned the retained prepared state, then explicit Resume applied its feedback at step 2. The app reached the original two-step/two-attempt bound with one journal and no old 503 current alert. [The restore receipt](native-regression-restored.json) retains generation 2/revision 18 and fixture request count 248. The parent then exported through the native dialog.

The export directory is `target/qa/0.12.1-reading/exports/sustained-1791919137300-1-2-18` under `desktop/ReservoirScope`; the older directory name does not identify its producer version. The pinned executable and package receipts identify this as 0.12.2.

## Offline verification

[The evidence receipt](native-regression-export-evidence.json), SHA-256 `58f01f7c1fd92f555ca2ed806641a3b4cdca4978bd886c2efb4d73fcbe6ed980`, contains the full original-export inventory, fixture-log prefix identity, linked UI/package receipts, exact request associations and 20 passing checks. The retained [checker source](check_native_regression.py) performed no IPC, UI, service, model, live-store or process-control action.

The verifier was copied before invocation to `target/qa/0.12.2-reading/native-regression-verification-01/reservoir-scope-desktop-0.12.2-pinned`, with the exact package hash above. `/usr/bin/time -l <pinned verifier> --verify-sustained <export>` passed at 19:23:15.752996–19:23:16.052182 UTC on October 13. Measured wall duration was 0.29920575 seconds; peak RSS was 12,763,136 bytes for the verifier process only. [Stdout](native-regression-cli-stdout.json) and [stderr/timing](native-regression-cli-stderr-time.txt) are retained separately.

The record contains two numerical steps, one journal, six segments and 418,856 bytes. Its manifest SHA-256 is `7ebef8576852694d6dad768703040cd63e9acfb01baad3c9758ce95733b3ff79`; checkpoint SHA-256 is `ec682f9ddeae80fafe8e1fba3eb9083d46bb5dfcd84dba4b9fbcc79758c31d9e`.

- Failed request 247 is attempt 1. The record retains the actual `languageFailed` event and HTTP 503 reason, followed by an explicit retry. It has no accepted response, journal or application for attempt 1.
- Request 248 is attempt 2. Its exact prompt and request body match the held observation from the failed attempt. The successful fixture response, saved text hash, save receipt and retained observation all match. The journal is saved once and applied once at step 2, immediately after observation 1.
- There is no invented memory: this first successful journal has no prior journal in its prompt. One journal cannot demonstrate subsequent full-text memory progression.
- The exported fifth segment's exact hash matches the pre-quit prefix receipt, and its final core checkpoint retains the prepared step-1 state. Restore preserved configuration and attempt/step budgets. The full replay validates the contiguous event and numerical chain through the one later application.
- The historical 503 diagnostic remains in the final manifest. Its preservation is compatible with the UI no longer displaying it as an unresolved current failure.

The original export, pinned executable and fixture-log prefix were unchanged after inspection. The historical accepted-journal checker was reused without modification; failed request 247 was excluded only from its cancellation-specific rejection branch and independently checked as the actual HTTP-failure outcome. The fixture's failure mode does not write a normal successful-response row; absence of such a row is not an assertion that no HTTP 503 was sent.

## Limits

Native alert and close-flow observations come from the parent UI run and its linked receipts; offline inspection independently checks the exported history and application consistency. The test used synthetic text, not Gemma, and does not establish model quality, memory improvement, long-run resource behavior, cross-platform qualification or physical power-loss durability. The separate real-model rehearsal must retain its own configuration, package/export identities and outcomes.
