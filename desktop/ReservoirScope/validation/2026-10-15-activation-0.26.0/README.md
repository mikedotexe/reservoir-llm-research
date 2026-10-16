# Activation experiment 0.26.0 qualification

This account separates source implementation, mechanical qualification, and the
first exploratory reading. It concerns the isolated Reservoir Scope apparatus;
no live Being service, workspace, database or prompt is changed.

## Published starting point

The completed 0.25.0 worktree was committed as
`3cfbf1b7fba9ceacba2c5ad84bd9636c04496909` with message
“Checkpoint Reservoir Scope Tauri 0.25.0”. The branch
`codex/tauri-0.17-checkpoint` and annotated tag
`reservoir-scope-tauri-v0.25.0-checkpoint` were pushed explicitly and their remote
object identities verified. The tag object is
`676817e24c3af8b126f7687d81c6c95291f02c8a`; it identifies a source checkpoint with
scoped macOS qualification. Three preceding unpublished apparatus commits are
included. Ignored packages, assets, caches and research outputs remain local.

Implementation continues on `codex/activation-loop` in a separate managed worktree.
The [contract](../../../../shared/reservoir-scope/activation-experiment.md) and
[frozen pilot](../../../../shared/reservoir-scope/activation-pilot.json) define the
experiment before any pilot writing is inspected.

## Recorded checks

- Frontend: 452 tests in 48 files pass in `frontend-tests-final.log`. The separate
  `frontend-final.log` records 33 focused tests plus TypeScript and Vite build;
  the subsequent timeline repair passes 39 focused tests and TypeScript in
  `frontend-timeline-final.log`. The final package build passes TypeScript/Vite;
  the existing large-bundle advisory remains.
- Python worker: 32 unit/protocol/math tests pass in `worker-tests-final.log` without
  loading a model. Explicit Float64 summation avoids host Accelerate warnings
  encountered with NumPy matrix multiplication during initial setup; no warning
  suppression or tolerance adjustment is used.
- Frozen native reference remains 180 source files and 43 resources, with one
  fixture, as recorded in `frozen-reference.json`.
- Script checks cover failed-qualification refusal, stopping the whole pilot on
  a failed second arm, retaining the first reading, qualification inventories,
  and frozen-reference mutations. Logs are retained separately.

- Rust: the full workspace passed 439 tests, with two existing opt-in tests ignored
  (`rust-tests.log`). Subsequent changes passed the command-permission regression
  and nine supervisor tests, including blocked stdin cancellation/deadline checks.
  Strict workspace Clippy passed after those changes. These are affected checks,
  not a claim that the earlier full suite was rerun on every later commit.
- [Packaged macOS observations](MACOS-UI.md) cover setup without inference,
  synthetic and real journal reading, exact export, and recovery. The model pilot
  uses the same Rust supervisor through its CLI; no UI Start inference is claimed.

## Real-model mechanical qualification

The isolated Qwen3 model and all 34 Python package versions are pinned. Attempt 01
completed its numerical probes but failed while serializing a NumPy boolean into
the final JSON receipt. Its original artifacts and failure remain retained.
Commit `27f05ac` repairs only this reporting conversion. Attempt 02 used the same
fixed probes and tolerances, recomputed calibration for the new worker identity,
and passed all ten checks. Both admission and outcome records are in this folder.
This repair occurred before the pilot; it was not a retry of pilot writing.

Across three zero-intervention paths and four forward stages, all 12 logit
comparisons were bitwise equal, with identical offsets in all 36 layer caches.
Quiet passes sampled zero tokens and did not change a subsequent unsteered probe.
Recomputing calibration from its 32 retained observations reproduced the saved
projection, center and scale exactly. Same-pass final content-token capture and
steering cleanup passed. At 11 bf16 probe positions, the requested 1% change
measured 0.999427924038423%–1.0121040451652004% of the original residual norm.
Requested geometry and realized finite-precision addition are recorded separately.

The manifest hash is
`82b39f39ce5ec7722be9c967149a18a1ac8ed1cc8f2691e1485e101f7e542513`;
calibration hash is
`0c1fc7c3e2868813643d629e1200c5188ee5007fa1c1ccef1e614b52c32dbe9c`.
All qualification captures, cache observations, token IDs and raw reports remain
under ignored `research/outputs/activation-0.26.0-20261015/`.

## Frozen pilot outcome

The single authorized pilot attempt stopped at its first resource refusal.

| Scheduled condition | Observed result |
| --- | --- |
| Decaying trace (Reading A) | Completed 12 quiet observations, six journals, 121 numerical steps; offline verification passed. |
| No steering | Refused before model load: macOS memory pressure level 2, 32% free; admission requires level 1 and at least 25% free. Zero observations or journals. |
| Recurrent state | Not started, following the frozen stopping rule. |

No retry, extension, output-limit change or resource-threshold relaxation was
made. The three-arm comparison is **incomplete because collection stopped**;
this is not a null or ambiguous comparative writing result. Reading A remains a
complete chronological sequence for exploratory reading. Its allocation was
concealed from a fresh reader until the initial six-entry account was saved.

The inference package was built from `27f05ac` and has binary SHA-256
`e2d332c0dcc84b657016338db73dccb19dbb97f8a295a19a6fc26da6ce60cb0e`.
Its 14 bundled worker/fixture/document files match the source byte for byte.
That package is preserved locally as `pilot-package-27f05ac.app`; subsequent
reader improvements do not replace its frozen experimental identity.

See [the reading account](PILOT-READING.md) for complete-sequence observations,
alternatives and limits, and `mechanical-pilot-summary.json` for the reproducible
artifact analysis. The probe is `probes/2026-10-15-activation-pilot.py`.

## Scope and limits

This is a working isolated experiment, with a mechanically qualified local model
adapter and a retained partial pilot. It does not establish that recurrent
steering improves writing, that the projection reconstructs meaning, or that
journal language reports subjective experience. Normalizing every nonzero return
to the same norm removes state-magnitude information. Trace and recurrent arms
also differ in their update functions; later journals would additionally carry
earlier effects through exact-text memory. These are interpretive constraints,
not defects to hide by rerunning until a preferred result appears.

macOS qualification is local and scoped. The app is ad-hoc signed, not notarized.
Human acceptance, Windows/Linux package/UI qualification, and live Being rollout
remain unclaimed. Earlier Ollama session contracts keep their existing meaning.

`qualification-receipt-final.json` binds the final reader source inventory, package,
local archive, signing observation and supplied check records. It records the
final reader package rather than replacing the separately preserved inference
package identity above. Raw command logs retain original output, including the
repaired Clippy failure and a corrected worker-test discovery invocation.
The earlier `qualification-receipt.json` remains as captured. A final whitespace
check removed one extra blank line from a type-only frontend file. Rebuilding
TypeScript/Vite produced byte-identical HTML, executable JavaScript and CSS;
the source map changed (`frontend-whitespace-equivalence.json`). The retained
package therefore includes the pre-whitespace source map. Its executable frontend,
Rust and worker are unchanged. The final receipt updates source identity without
implying a package rebuild, another model request or another pilot run.
