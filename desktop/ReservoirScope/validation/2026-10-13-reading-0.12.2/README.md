# 0.12.2 reading and native recovery qualification

The distinct macOS arm64 0.12.2 package passes build, ad-hoc signing, archive and
resource checks. Its actual native regression confirms that a resolved provider
failure remains historical instead of appearing as a current alert, and that
Checkpoint and quit preserves saved feedback for explicit restoration and one
later application. A separate bounded Gemma run completed four saved-and-applied
journals and passed immutable-export verification. Its prose exposed a grounding
problem; native pointer operation and the model supervisor's cleanup error retain
explicit limitations below.

This account is written after package capture. It does not change the runtime,
resource files or packaged executable, and it does not overwrite earlier receipts.

## Exact candidate and scope

| Identity | Value |
| --- | --- |
| Version / architecture | 0.12.2 / macOS arm64 |
| Executable SHA-256 | `2fa824855d1172ebf707b4f1ce5f50d2c3eb74ab4aeeb437d41dc566f818db8d` |
| Source inventory | 279 files; `3abb97c9d10202767399018e1c974ea0129c068f758d8870a3aabb6ad199a238` |
| Package inventory | 46 files; `3c319f06101af673c6fc04ccdc0d280c6cc6944284d589c21df7d298d3f2dde3` |
| Archive | `ReservoirScopeTauriPreview-0.12.2-macos-arm64.tar.gz`, 102,491,660 bytes |
| Archive SHA-256 | `4d4223ca7edd684a8bab2a7cda6de06bdc58c3cee5eebf69b3656159b295492b` |

[Package qualification](qualification.json), [pre-UI capture](package-before-ui.json),
[source inventory](source-before-build-final.json) and
[source/test continuity](source-test-continuity-01.json) bind the candidate.
[Archive verification](archive-check.json) compares every member and all 46 regular
files with the app; [resource verification](package-resource-check.json) compares
39 canonical inputs and 42 packaged resource files, including the staged index and
frozen reference manifest/scenes. The ad-hoc signature verifies locally. This is
not notarization, a distribution identity or human acceptance.

The package preserves the calmer setup/reading changes and the already-qualified
publisher/order and storage-admission repairs. It adds a narrow presentation fix
and version metadata. The [prior-release preservation](prior-release-preservation-01.json)
keeps the earlier candidate identifiable. Frozen 0.12.0 remains the producer of the
[two-hour measurement and recovery evidence](../2026-10-13-reliability-0.12.0/RESOURCE-RESULTS.md);
no duration or energy claim transfers to this newer build.

## Defect, correction and source checks

Actual 0.12.1 use exposed a historical HTTP 503 as a current error after a successful
retry had saved Prepared feedback, and again when the run reached its budget.
The old message was valid retained history. The alert predicate incorrectly treated
every required decision as an active failure. Its
[three-journal native export](../2026-10-13-reading-0.12.1/PACKAGED-EXPORT-01.md)
still verifies; the presentation defect remains recorded separately.

`MyReservoirBoundary` now distinguishes active failure from attention. Current
storageBlocked, attemptBlocked, interrupted, retry-save, retry-provider and blocked
language states retain visible alerts and remedies. Saved Prepared and budget-only
states retain their decision panel without promoting an old diagnostic. The main
Session diagnostics disclosure preserves the original message. Top-level and close
review command errors are unchanged.

The [current focused receipt](boundary-source-checks-02.json) records **26 passing
tests in three files**, including three new cases, and successful TypeScript
validation. It covers failure→successful Prepared in main and close review with
history retained, budget-only attention and paused retry-save visibility. A first
synthetic test fixture used impossible journal/attempt counts and was corrected;
its [failed receipt](boundary-source-checks-01.json) remains intact.

The earlier full frontend pass was **323 tests across 36 files**. It was not rerun
for this narrow delta; 323 and 26 are not additive. The **169 desktop tests**,
**150 core tests** and strict workspace/all-target Clippy are reused for unchanged
Rust sources, as recorded in source continuity. Two natural quota profiles passed
separately from the two ignored long tests in the ordinary desktop suite. The
[fresh package build](package-build-01-receipt.json) also ran the production
TypeScript/frontend build. No numerical contract, historical verifier, native
reference source or tolerance changed.

## Actual native regression

The [native account](NATIVE-REGRESSION.md) and
[20-check evidence receipt](native-regression-export-evidence.json) retain the exact
sequence and distinguish UI observations from independent offline verification:

1. Owned synthetic request 247 returned HTTP 503, visibly exposing the failure.
2. Explicit retry 248 reused the held observation and prompt. Cmd-Q opened close
   review while the request was held. Releasing it saved a journal at step 1,
   prepared for step 2, without the old 503 as a current alert.
3. The actual **Checkpoint and quit** button retained the saved Prepared boundary
   and exited; the [quit receipt](native-regression-checkpoint-quit.json) records
   absence of the identified app process.
4. Idle relaunch, Inspect and explicit Restore recovered Prepared step 1→2.
   Explicit Resume applied it once at step 2, reached the original step/attempt
   limits and made no extra synthetic request. The historical error stayed in
   Session diagnostics, not the current alert.
5. The native dialog export passed the pinned 0.12.2 production verifier and all
   20 evidence checks: **two numerical steps, one journal, six segments**, 418,856
   bytes. Failed attempt 1 produced no accepted response, journal or application;
   attempt 2 saved once and applied once. The pre-quit fifth segment remains exact.

The export path contains an older `0.12.1-reading` directory name; the pinned
producer and package receipts identify it as 0.12.2. The historical diagnostic,
export bytes, fixture-log prefix and verifier identity were preserved. One saved
journal cannot demonstrate subsequent full-text memory. These are synthetic-provider
failure/recovery checks, not the real-model result or a new resource-duration run.

## Real-model rehearsal — mechanics passed, writing quality limited

The selected cached **gemma3:4b** was copied into a private owned model directory
with manifest/blob hashes checked in the
[staging receipt](../2026-10-13-reading-0.12.1/owned-model-stage-01.json).
The [owned service receipt](owned-model-server-start.json) records startup at
19:15:31 UTC on October 13, endpoint `http://127.0.0.1:63515`, and a 900-second service
limit ending about 19:30:31 UTC. Startup alone is not model execution evidence.

The actual app readiness check matched the pinned digest. The
[creation receipt](real-model-created.json) binds session
`sustained-1791919382664-3` to this package, seed 20261013, cadence 30, one-second
pace, **121 steps / four attempts / 600 seconds / 64 MiB**, and explicit Create
separate from Start. The run reached its original bounds at **121 retained steps,
four journals and 19 segments**, with 158,846 milliseconds of session running time
and no retained failure event. The [actual native walkthrough](REAL-MODEL-UI.md)
records the interaction; the [independent results](REAL-MODEL-RESULTS.md) distinguish
mechanical integrity from prose interpretation.

The [pinned export check](real-model-export-01/receipt.json) passes whole-chain replay
and exact journal/response/save/application/memory checks. The original native export
is unchanged: 1,781,880 bytes, manifest
`215162126a8701c55f8ad039cbd081071f84a6d18903366c0e723f69d2780d1c`.
Observations **30, 60, 90 and 120** saved once and first applied at **31, 61, 91 and
121**. The first prompt has no invented memory; the later three contain the exact
latest saved-and-applied journal. All four retained responses report `complete=true`,
`stopReason=stop` and returned model `gemma3:4b`; token counts are 184, 150, 207 and
233. These are actual app-retained provider outcomes, not an independent signed
provider execution receipt. The offline checker contacted no model.

The step-30 journal stayed independently selected while three new entries arrived.
Keyboard Follow latest selected the step-120 entry, with full inert prose and
Evidence closed. A conservative **91.029388792-second minimized interval** includes
the time after the run reached its bound; it is not 91 seconds of continuous
advancement or another endurance test. Several AX/screenshot pointer attempts after
restoration only scrolled or produced no observable action. Keyboard activation
worked for Evidence, Follow latest and native export without relaunch. The pointer
path remains for human/native review; these attempts neither pass that gate nor
establish a frozen JavaScript/backend defect.

The text is readable and reports some current metrics correctly, but it is not yet
dependable scientific narration. Entries observed at 90 and 120 label themselves
“Observation 61”; at 90, head share 86.8% repeats the prior entry instead of the
current 85.54%. Claims about uniformity across all 32 eigenvalues conflict with the
retained spectrum's large leading modes and small tail. Stability/convergence,
spatial meaning, eigenvector changes and learning claims exceed the supplied
observations; the prompt explicitly states that writing does not train weights.
The exact prose, prompts and numbers remain preserved in
[review material](real-model-export-01/quality-review-material.json). No entry is
rewritten, and successful mechanical feedback is not a quality score or causal
benefit claim.

Native Cmd-Q exited after export and reading; the
[quit receipt](real-model-clean-quit.json) confirms exact app PID absence, unchanged
executable and the retained 121-step/four-journal budget boundary. The model
supervisor reported an OS permission error during shutdown. Its original failure
is retained; [three later read-only checks](owned-model-cleanup-supplement-01.json)
found the exact server/supervisor absent and their original process group empty,
without signals or service calls. The failing syscall remains unidentified, and
escaped descendants outside that group were not inventoried. This is qualified
absence evidence, not a clean automatic-supervisor pass. The synthetic provider's
[separate stop receipt](owned-synthetic-provider-stop.json) confirms its owned
248-request process ended. No Being system was contacted or altered.

## Next bounded tranche

Version the personal-session prompt contract before changing its wording. Separate
the current observation's identity and measurements from quoted historical prose;
ask for grounded observations with explicit uncertainty, and make absent evidence
for convergence, eigenvectors, spatial meaning or training unambiguous. Preserve
v1 export replay and original journals. Use retained prompts/responses first for
an auditable evaluation of current-step accuracy, metric transcription, memory
contamination and unsupported interpretation; then qualify any later explicitly
authorized model comparison separately. This account starts no additional model
request. Native pointer behavior and the owned supervisor cleanup error remain
separate follow-ups.

## Remaining boundaries

This release is a manually qualified Mac preview with bounded checks. Human
collaborator acceptance, minimum macOS support, Windows/Linux, broader accessibility,
24-hour operation, real host sleep/wake, physical power loss, broader interruption
points, GPU/energy and total-app resource attribution remain open. The frozen 0.12.0
measurement's final settled thread/descriptor gate remains incomplete. A successful
saved journal would establish a recorded mechanism, not model training, improved
writing, causal attribution to words alone or behavior of a live Being.
