# Episode 02 · independent pre-run review

Status: accepted for the separately frozen, single-admission procedure. No concrete blocker found in the reviewed scope. This is preparation review, not admission or a model-run result.

Reviewed the [new protocol](PROTOCOL.md), [run plan](run-plan.json), cleanup and admission scripts, exact reused supervisor/checker sources, and the [cleanup receipt](cleanup-result.json). Shared operating guidance and live-system boundaries remain applicable. This reviewer performed file reads and identity comparisons only; no deletion, process control, service call, model request, app/UI action or test rerun.

The plan differs from the first refused episode only in episode/revision identity, exclusive supervision directory, user authorization description and prior-refusal provenance. Numerical settings, v4 invitation, model, response policy and all budgets are unchanged. Twelve possible observations are at steps 30–360, with saved feedback first applied at 31–361. The first of 361 steps, twelve attempts, 900 active seconds or 64 MiB governs; an already dispatched request may settle within its original 180-second deadline. Unstarted, failed, incomplete and saved-but-unapplied outcomes stay in the twelve-slot denominator. No retry, skip, substitution or extension is admitted.

The unchanged supervisor retains its 1,200-second ceiling. The required 1,140 seconds remaining before Start covers the 900-second active cap, one 180-second in-flight settlement and 60 seconds of margin. Only the new owned listener and `target/qa/0.16-long-writing-gemma3-4b-run02` supervision directory may be used. Launch revalidates the existing private selected-model copy and pinned software; no new staging copy, pull or default/shared endpoint is required. Process-group cleanup remains scoped to proven owned identities. The prior qualified helper tests are reused by exact source identity, not claimed as newly executed.

The admission script exclusively creates its receipt before probing, verifies frozen input hashes first, and requires all probes to succeed plus pressure level 1, free memory at least 35% and free disk at least 8 GiB. A refusal or partial receipt prevents a second invocation. Preparation readings do not constitute this admission. No active pressure watcher is added; one admission is not a guarantee of sufficient resources throughout the run.

## Cleanup scope and evidence

`reclaim_incremental.py` has one fixed removal target derived from its repository location: `desktop/ReservoirScope/target/debug/incremental`. It checks ordinary directory ancestors, holds the existing debug Cargo lock exclusively, and rejects nonregular, nonowned or unexpected-extension cache members before removal. It does not invoke Cargo clean or traverse a deletion target in `target/qa` or `target/release/bundle`. Its protection inventory hashes regular files and records symlink destinations without following those links. These guards assume the owned checkout is not being maliciously replaced concurrently; they are not a general adversarial filesystem guarantee.

The root-executed cleanup receipt reports 23,896 cache files removed, 8,116,832,165 logical bytes, and 29,589 protected identities unchanged across historical validation, `target/qa` and `target/release/bundle`. It records free disk increasing from 7,036,129,280 to 12,715,892,736 bytes. This is an observed filesystem delta, not an attribution of every reclaimed byte to the cache or a new admission. The receipt reports no stopped apps/services and no model requests; this reviewer did not independently inspect processes.

A scoped reference search across desktop validation, core validation/support, desktop scripts, shared documents, the roadmap and desktop README found no historical `target/debug/incremental` references. The only current matches were this episode's cleanup script/intent/result. Direct executables, examples, resources, all QA material, packages, archives and pins were outside the removal target. The earlier preparation memory recovery must not be attributed to this disk cleanup.

## Reused qualification and interpretation

Supervisor and helper-test bytes match the previous episode exactly. Checker, checker-test, rubric and evaluation bytes also match. The new [checker reuse receipt](checker-tests-01.json) explicitly carries the earlier 27-test qualification and records no new execution. New protocol/config identity was reviewed separately; a copied receipt is not a new runtime test.

The unchanged checker distinguishes typed provider input-count evidence, complete text, durable saves and applications. Counts remain provider assertions, not proof of full context use or writing accuracy. Current/prior observed measurements and latest saved-and-applied prose memory are separate references. Whole-response reading remains manual. Twelve linked opportunities are one dependent episode, and prior known four-entry writing is not a randomized control.

The parent still owns package identity, freeze, the one fresh admission, readiness/configuration binding, native Start, exports, paused recovery and actual owned-process cleanup. None is inferred from this review. Preserve the first refused episode and its documented review-file amendment unchanged.

## Reviewed identities

| File | SHA-256 |
|---|---|
| [PROTOCOL.md](PROTOCOL.md) | `bb47f7523371d759d6952b36a4cb960420f118c5174fb5efafb5215a42c3164a` |
| [run-plan.json](run-plan.json) | `8f1c0620a959df21fbdd119d84ee5a0b8d859dd184ebb4dc264e83e2f1ef78ba` |
| [reclaim_incremental.py](reclaim_incremental.py) | `59c0ac9a1c0c192c66d25fb09a9d099b6699edcefcf7bf38ba9f15ddfe401067` |
| [admit_once.py](admit_once.py) | `c416da52242be798f315e9a5384065373d694c5da6ce0e242aad796977053045` |
| [owned_model.py](owned_model.py) | `9c5351878ff5ee634f8f6c3afa49f0e9c6e5108224073a7b8ebda14d0d35ae9f` |
| [test_owned_model.py](test_owned_model.py) | `145d75ad5d1d8a090bb3c1a9830a59d1127d3424354b8b59db208d0006da9b87` |
| [check_real_model_export.py](check_real_model_export.py) | `ba4d03747ea29dde79fd93bb9b15488800eae0b865d5224902c6561b0b60b443` |
| [test_real_model_export.py](test_real_model_export.py) | `f9d2e14f816f56b5c57129ee9a27feff8076d665050e8d5b1ab4267de528ea02` |
| [checker-tests-01.json](checker-tests-01.json) | `2f58a382dc9bed9cdfd162da59c9eebb2db5fba5e9a95bad3cae40404446e59a` |
| [cleanup-result.json](cleanup-result.json) | `381197e236db9cb2b959517fef38003fedaa6c807f172073d478f08feb109edf` |

Written once at 2026-10-14T00:48:08.485345+00:00. This review will not be amended after the FINAL handoff; any later correction must be a separate artifact.
