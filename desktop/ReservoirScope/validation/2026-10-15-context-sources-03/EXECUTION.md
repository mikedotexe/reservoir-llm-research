# Parent-only execution handoff

**Prepared, not admitted or launched.** Wait for independent review and the parent’s
explicit release after the product build/tests and native UI work finish. This
document schedules nothing. Do not repeat a failed/partial admission or extend
this window’s bounds.

## Qualified preparation

- [preparation-checks-04.json](preparation-checks-04.json): 14 actual file-only
  transformation/provenance tests passed with source identities unchanged.
- [runtime-checks-03.json](runtime-checks-03.json): 97 actual synthetic
  supervisor/transport/renderer/reuse/admission tests passed with source unchanged.
  The nine new admission tests include 29% refusal and 30%/31% acceptance; all
  test host probes are mocked. Four added dependency-partition checks retain core
  validation and target/qa evidence, classify explicit product roots, and reject
  unknown/duplicate paths. Independent review caught the earlier freeze’s missed
  core-validation root before freeze or admission; it was corrected by scope,
  not by changing an asserted count.
- [runtime-checks-01.json](runtime-checks-01.json) preserves the initial test
  failure. Its mocked temporary freeze used `/var/...` instead of canonical
  `/private/var/...`. The entrypoint correctly refused that mismatched identity
  before probing; only the fixture was corrected.
- [input-generation-01.json](input-generation-01.json) binds the unchanged
  generator/plan and twelve exact reused prompt bytes. All 73 original export
  files and 492 retained prior validation files remain unchanged. The first
  passing preparation receipts remain historical; `-04` binds final test sources.

## After explicit release

Use this directory as the working directory, with `PYTHONDONTWRITEBYTECODE=1`.
First run only the prospective freeze, then the one admission:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 freeze_inputs.py
PYTHONDONTWRITEBYTECODE=1 python3 admit_once.py
```

Inspect the retained admission. If it is false, missing or partial, close this
window with twelve unstarted slots; do not continue to launch or invoke the probe.
If it passes, the already-authorized parent may launch the isolated supervisor
with these exact arguments (keep the supervisor owned and await its terminal result):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 owned_model.py launch \
  --seconds 1200 \
  --supervision-directory /Users/v/.codex/worktrees/tauri-checkpoint/reservoir-llm-research/desktop/ReservoirScope/target/qa/0.20-context-sources-gemma3-4b-run03 \
  --software-selection /Users/v/.codex/worktrees/tauri-checkpoint/reservoir-llm-research/desktop/ReservoirScope/validation/2026-10-15-runtime-0.40.5/software-selection.json \
  --expected-software-selection-sha256 b055ddd7c91e67c75fae0df183b234836ef11eb3a96574b9da458b06576196fa
```

Use only its new owned endpoint receipt. Do not contact a default service or
perform a separate readiness request. The following runner verifies ownership,
software, model, source hashes and the 1,140-second remaining lifetime, then owns
the single inventory request and at most twelve sequential generation requests:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 run_probe.py \
  --inputs /Users/v/.codex/worktrees/tauri-checkpoint/reservoir-llm-research/desktop/ReservoirScope/validation/2026-10-15-context-sources-03/frozen-inputs.json \
  --expected-inputs-sha256 2a74d74a0c6d94642ca15011c797b74e938d861884126a8c4a8dc0fe0ff266bf \
  --output-directory /Users/v/.codex/worktrees/tauri-checkpoint/reservoir-llm-research/desktop/ReservoirScope/target/qa/0.20-context-sources-results03
```

The first failed/incomplete response or insufficient remaining full-request
budget stops subsequent requests. Preserve all twelve slot outcomes, including
partial/unstarted ones. No retries or replacements. Stop only the exact owned
service through its `stop-request` mechanism and retain the supervisor’s result.
Then invoke `retain_and_analyze.py` with the actual terminal ledger and supervisor
SHA-256 values; do not invent those hashes in advance. The exact copied renderer
and reading protocol retain independent masked full-text readings before mapping
or source audits. A refusal produces no invented prose reading.

The new 30% policy is a provisional operating choice, not a guarantee of RAM
capacity or successful 0.40.5 execution. Earlier refusals are not reopened.
