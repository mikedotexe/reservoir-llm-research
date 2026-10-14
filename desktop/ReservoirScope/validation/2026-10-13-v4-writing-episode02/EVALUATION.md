# Evaluation execution contract

This episode reuses existing qualified source bytes. No evaluator tests or model calls are rerun during preparation. The prior qualification is 43 review tests and 23 integrity tests, identified in `evaluator-reuse-01.json`; it is not new execution evidence. The prospective `evaluation-freeze-01.json` binds this plan/rubric, exact source bytes, prompt fixtures and helper/package continuity.

Only after an immutable export is supplied, invoke the existing checker from the project root with the actual export and new owned endpoint:

```sh
python3 desktop/ReservoirScope/validation/2026-10-13-measurements-0.15.0/check_real_model_export.py \
  --bundle "$EPISODE_EXPORT" \
  --executable desktop/ReservoirScope/target/qa/0.15-pinned/reservoir-scope-desktop \
  --expected-executable-sha256 18949732cf48c926003ffcf7b5b216bccc32ea071d0bff8a411e841eaba123d5 \
  --expected-model gemma3:4b \
  --expected-endpoint "$EPISODE_ENDPOINT" \
  --expected-prompt-version reservoir-journal-v4 \
  --protocol desktop/ReservoirScope/validation/2026-10-13-v4-writing-episode02/run-plan.json \
  --output-directory desktop/ReservoirScope/validation/2026-10-13-v4-writing-episode02/real-model-export-01
```

`EPISODE_EXPORT` and `EPISODE_ENDPOINT` are explicit handoff values, never discovered by contacting a default endpoint. Verify all frozen hashes before execution. The checker requires a new output directory, pins the verifier, records `/usr/bin/time -l` output for offline whole-chain replay, preserves source inventory, and produces `receipt.json` plus `quality-review-material.json`. Its pinned executable is locally ignored. Timing and peak RSS describe this offline verifier, not model generation or app resource usage.

After the integrity receipt passes:

```sh
python3 desktop/ReservoirScope/scripts/journal_quality.py \
  --material desktop/ReservoirScope/validation/2026-10-13-v4-writing-episode02/real-model-export-01/quality-review-material.json \
  --integrity-receipt desktop/ReservoirScope/validation/2026-10-13-v4-writing-episode02/real-model-export-01/receipt.json \
  --protocol desktop/ReservoirScope/validation/2026-10-13-v4-writing-episode02/run-plan.json \
  --prompt-version reservoir-journal-v4 \
  --output desktop/ReservoirScope/validation/2026-10-13-v4-writing-episode02/real-model-quality-review-01.json
```

Retain command, UTC start/end, exit code, stdout/stderr and source/output identities in new execution receipts. Read every response in full, including received text not saved as a journal; report those categories separately. The candidate inventory is not the review result. Record full-reading references and exact prose spans separately, with an exact-text journal rendering only if journals exist.

If admission fails, neither command is run. Write `real-model-outcome-01.json` and `REAL-MODEL-RESULTS.md` identifying the refusal, zero execution and all four unstarted opportunities. Prior results, prospective files and reused tools stay immutable.
