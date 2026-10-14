# Held-request process interruption and explicit recovery

The frozen 0.12.0 package recovered the committed three-step history after an exact owned app process was killed during a witnessed, held synthetic request. Restoration did not resend that request. Explicit Retry created a new attempt, four later journals were saved and applied, and the five-attempt budget remained exhausted across a further quit/relaunch/restore. This is a **process-interruption result**, not physical power-loss or real-model qualification.

## Recorded intervention and idle/restore boundary

[The plan](process-interruption-01-plan.json) created the separate session `sustained-1791917410760-3`: seed `20261014`, writing every 3 steps, requested pace 100 ms, maximum 20 steps, 5 attempts, 600 seconds and 32 MiB. The owned synthetic provider already had 237 POSTs from preceding work.

[The kill receipt](process-interruption-01-kill.json) binds app PID 76635, process start `1791916998.781710`, and the frozen executable path. At **18:51:26.264027Z**, root sent SIGKILL only to that process after witnessing fixture request **238** held for approximately 22.212 seconds, within the request deadline. The app was recorded absent before the held fixture was released at **18:51:26.264814Z**. The retained state was generation 3/revision 6, `awaitingLanguage`, live/durable step 3, no journals, one segment and 437 elapsed milliseconds.

The fixture then logged request 238's handler completion at epoch milliseconds **1791917486273** (18:51:26.273Z), including `socketWriteCompleted: true` and text hash `bc4d0e9f27e930873a4f7bec8a2c45439182b49922c799b1203e439add3847d7`. This records the handler's late outcome; it does **not** show acceptance by the dead client.

Root observed an idle relaunch with no active session, then explicitly inspected and restored the history. [The restored receipt](process-interruption-01-restored.json), captured **18:56:35.443649Z**, records generation 4/revision 7, paused step 3, zero journals, attempt 1/5 and fixture POST count still **238**. The UI showed a blocked opportunity, no active request, disabled Resume, and explicit Retry/Skip. The unchanged count across the witnessed request and paused restore supports no automatic resend in this observed interval.

The independent passive capture in [process-interruption-01-idle.json](process-interruption-01-idle.json) **missed the idle interval**. Its first read raced explicit recovery and found the old checkpoint already rotated out of the live store; it aborted rather than claiming unchanged state. The later successful capture at **18:57:49.455959Z** is explicitly labeled post-recovery: PID 78221, start `1791917494.208249`, frozen binary hash, generation 4/revision 40, step 13, four journals and POST count 242. The preserved pre-kill copy remained available and was independently checked below. The restored receipt's empty `providerResponse238` field is not evidence of no late response; the actual response row is retained in the passive and export-evidence receipts.

## Immutable native export and independent checks

Root exported `target/qa/0.12-reliability/exports-multi-hour/sustained-1791917410760-3-4-40` through the native dialog. It contains **13 steps, 4 journals, 21 segments and 1,500,534 verified bytes**, with manifest SHA-256 `a17be97faa91115680ae52dc7b2f062761bf4e454265d1a07f61cb4def14914b`.

[Pinned CLI verification](process-interruption-01-cli-receipt.json) passed using exact frozen executable bytes, SHA-256 `f68a3752a628edf11ac6161a26e6979bb22dcf4c3ee1c63f10add2cea86ab40d`. The offline invocation ran **18:59:31.137424–18:59:31.269318Z**, measured **0.131719333 seconds** wall time and **13,107,200 bytes** peak RSS through `/usr/bin/time -l`. These are separate verifier-process measurements, not GUI resource measurements. Raw [stdout](process-interruption-01-cli-stdout.json) and [stderr/time output](process-interruption-01-cli-stderr-time.txt) are retained.

[Independent export evidence](process-interruption-01-export-evidence.json) passed every check:

- The preserved pre-kill manifest, checkpoint and first segment match all three identities in the kill receipt. The first exported segment is byte-identical to that preserved segment.
- The export contains exactly one `interrupted` event, then one `retried` event naming previous attempt 1. It has **no accepted response, saved journal or application for attempt 1**, and no saved journal with the late response-238 text hash.
- All numerical steps 1–13 are retained exactly once. Accepted request bodies, exact prompts, observation frames, response text hashes, save receipts, host timing and memory satisfy the existing checker for all four successful attempts.
- Applications are unique, and memory is limited to the latest previously applied saved journal:

| Fixture request | Attempt | Observed step | First application | Retained memory |
| --- | ---: | ---: | ---: | --- |
| 238 | 1 | 3 | None | None; interrupted, no accepted journal |
| 239 | 2 | 3 | 4 | None |
| 240 | 3 | 6 | 7 | Journal from step 3, attempt 2 |
| 241 | 4 | 9 | 10 | Journal from step 6, attempt 3 |
| 242 | 5 | 12 | 13 | Journal from step 9, attempt 4 |

The check is reproducible with the retained [read-only checker](../../target/qa/0.12-reliability/process-interruption-01/check_export.py). It reuses the prior checker's accepted-journal logic unchanged. That older helper's rejected-request branch assumes a live `languageCancelled` event; process recovery instead records `interrupted`. Accordingly, request/response 238 are excluded only from that accepted-journal helper invocation and validated explicitly by the interruption checks. The complete original request log and records are unchanged; the receipt states this distinction.

No corruption controls were repeated. The original native export and preserved pre-kill copy were unchanged across this check. The fixture log was bound as an immutable prefix snapshot; later app-owned requests may append without being attributed to this session.

## Attempt limit survives another restore

The exported manifest records `budgetReached` at step 13 and **29.836 / 600 seconds**. Its checkpoint retains attempt cursor **5**, equal to the unchanged maximum of 5; the interrupted attempt consumed one opportunity. The configuration is exactly the same as the pre-kill configuration. Neither restore nor Retry replenished that budget.

After [normal quit](process-interruption-01-quit.json), root performed another idle relaunch, inspection and explicit Restore. [The exhausted-budget receipt](process-interruption-01-exhausted-restore.json), captured **18:59:07.797507Z**, binds PID 79294/start `1791917884.550580`, generation 5/revision 41, paused step 13, four journals, five of five attempts and unchanged elapsed 29.836 seconds. Resume was explicitly disabled and the fixture POST count stayed at 242. A paused phase label did not make the exhausted attempt budget runnable.

[Final stop](frozen-package-final-stop.json) records Cmd-Q, PID 79294 absent at **18:59:17.489858Z**, and unchanged frozen binary identity. The separate 0.12.1 build and its new-source qualification do not inherit this frozen package's result automatically.

## Evidence limits

Root's receipts establish the actual UI/process actions; the independent checks establish exported byte, numerical/event and fixture-log consistency. The passive reviewer did not operate the app, control processes, contact endpoints or alter the live store. Handler completion is distinct from client acceptance; the retained `interrupted` event expresses uncertainty about the outstanding request rather than inventing a received or cancelled response. This exercised one deliberate process interruption at one held writing boundary. It does not establish arbitrary crash-point coverage, sudden power-loss durability, system sleep/wake behavior, real-model quality or other operating systems.
