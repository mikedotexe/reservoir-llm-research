# 0.17.0 · Native macOS synthetic workflow

This is agent-operated native-app evidence on the current host, separate from tests,
builds, collaborator acceptance and real-model writing. The package was launched by
its exact `.app` path after the old app exited. The visible header read **0.17.0**.
The [archive receipt](archive-check-01.json) binds executable SHA-256
`7d46719838495b7a9ba57eea69ac9c940bb81f2fdc47cd12b761d97bb472d081`
and archive `3628110243c963d5aeca943864b174ea9873b357dbbfd949ee497299d9d5190a`.
Local ad-hoc signature verification passed; no distribution identity or notarization
is claimed. [Before](qualification-before-ui-01.json) and [after](qualification-after-ui-01.json)
receipts retain exact source, resource, package and host identities.

## Explicit creation and complete writing boundaries

The [frozen plan](packaged-ui-plan-01.json) used only the owned synthetic endpoint
`http://127.0.0.1:60168` and fixed model label
`reservoir-fixture:input-evidence-0.16`. That historical label identifies the fixture,
not the app version. No model weights or real service were used. The
[setup/readiness view](ui-config-readiness-01.txt) retained the exact seed, context,
output/deadline and three-minute/32-MiB/five-attempt limits. The explicit readiness
check returned its synthetic identity. [Creation](ui-created-before-start-01.txt)
left step zero, zero journals and no generation POST before the separate
[Start click](ui-start-01.json). Native select-menu choice required Return to commit.

Session `sustained-1791941918315-1` used v5 and completed four fixed responses,
observed at steps 10/20/30/40 and first applied at 11/21/31/41. The fifth response
was incomplete and the clock held at step 50, with four saved journals and five
retained attempts. Retained running time is 51,757 ms; this is not a GPU/resource
measurement or real model generation duration. No Retry, Skip, Stop or budget
extension was used.

The [first-entry view](ui-first-journal-evidence-01.txt) stayed at writing step 10
while the live state advanced to 27. It showed unavailable prior measurements,
all eight retained rows, the v5 version and a clear explanation that the full table
was not supplied in the prompt. Follow latest returned to later saved writing and
its exact prior-text memory. [Completed evidence](ui-completed-evidence-01.txt)
retains the later entry. The [blocked-attempt panel](ui-held-attempt-01.txt) stated
that no accepted fifth journal/feedback existed and no request was active.

AX text truncates long values; it is not the full prompt-byte witness. The immutable
export, exact HTTP hashes, full JSON memory joins and production replay in
[the independent analysis](NATIVE-EXPORT-RESULTS.md) provide those checks.

## Export and clean offline recovery

The actual native folder chooser accepted the new owned export directory through
Go to Folder and Return. [Original publication](ui-original-export-01.txt) and
[its receipt](ui-original-export-receipt-01.txt) report step 50, four journals,
22 segments and 1,666,849 bytes. Both app replay and the pinned command-line
verifier passed, with all five request/prompt/response joins checked independently.

Only the owned fixture was stopped, using its stop file; the supervised command
exited zero. Its [retained terminal log](fixture-run-01/retention.json) records one
inventory GET, five generation POSTs and explicit shutdown. The immediate
[quit observation](ui-quit-01.json) still reported running; the subsequent
[observation](ui-quit-02.json) returned no running app. Relaunch began with idle
setup and performed no model check or generation.

Explicit catalog inspection verified the exact current session, then
**Restore paused for review** created generation 2/revision 77. The
[restored state](ui-restored-paused-01.txt) remained at step 50, four journals and
five attempts, with Resume disabled. [Version/memory evidence](ui-restored-evidence-01.txt)
kept v5. [Received responses](ui-recovered-response-list-01.txt) kept the incomplete
fifth separate from journals, including its optional provider metadata.

The [second native export](ui-recovered-export-01.txt) passed independently. The
[recovery account](RECOVERY-RESULTS.md) records all 27 scientific files byte-identical;
only manifest generation, revision and wrapper phase changed. No request was retried
or sent after fixture shutdown. This exercises clean relaunch, not a crash or power loss.

The app is left paused on the fourth fixed journal with Evidence and Recorded
measurements closed: [final reading screenshot](ui-final-reading-01.png) and
[retained UI state](ui-final-state-01.txt). The incomplete-attempt notice remains
available. No temporary provider is intentionally left running.

## Scope

Native controls, selection, dialogs and this save/restore workflow worked on the
current host. No real-model writing quality, provider attention, emergence, measured
GPU/energy, minimum macOS, Windows/Linux, minimized duration, sleep/power-loss or
broad accessibility acceptance follows from this check. Minime and Astrid were untouched.
