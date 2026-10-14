# Deterministic aids and manual review

[`journal_quality.py`](../../scripts/journal_quality.py) is an offline report generator. Exit zero means the analysis artifact was written. It never returns a scientific-quality pass and never contacts the application or a provider. The [prospective protocol](PROTOCOL.md) owns the study boundary.

## Inputs and source binding

Supply the exact `quality-review-material.json` and `receipt.json` produced by the separately pinned whole-export checker, the retained prompt version, this run's `run-plan.json`, and a fresh output filename. The harness refuses a material hash that differs from its receipt, an unsuccessful/changed-original receipt, a supplied version that differs from retained config, nonordinary/oversized JSON input or an existing output. Missing config `promptVersion` means legacy v1. The receipt is local provenance, not a cryptographic authentication of provider execution.

```text
python3 scripts/journal_quality.py
  --material <bound-quality-review-material.json>
  --integrity-receipt <passing-export-receipt.json>
  --prompt-version reservoir-journal-v2
  --protocol validation/2026-10-13-grounding-0.13.0/run-plan.json
  --output <new-quality-report.json>
```

This is an argument illustration, not a request to start a model. The report retains all input and checker hashes, attempt/failure counts, recognition coverage and empty manual-review fields. Entries absent because an attempt failed are not manufactured or scored as good prose.

## What the deterministic part recognizes

The implementation recognizes a deliberately small English grammar: metric labels followed by a number, optionally with `is`, `of`, `at`, `=`, `:`, a few simple qualifiers or parentheses. Recognized labels cover recurrent RMS, L2 and changeL2, sensory fill, leading eigenvalue, head share and entropy. Percent-valued measurements require an explicit `%`; an unexpected percent sign on a scalar is also routed to unit review. It does not silently treat `RMS 0.43%` as scalar 0.43. Bare or ordinal eigenvalue claims need identity review; only an explicit leading/top/dominant-mode label can be compared mechanically to the first eigenvalue. It records each span, current expected value, written precision, comparison and scope caveat. Rounding tolerance is half the last displayed unit plus `1e-8` for eight-decimal prompt rendering. Exponents beyond ±16 require manual precision review.

`Step`, `current/global step` and `Observation` numeric labels are extracted separately. Exact v2 opening means literal `Step N.` at the start with the actual current step. A correct later label does not erase a contradictory one. V2 requires recognized current RMS and sensory fill for coverage; v1 has no retroactive mandatory metric or opening rule. A recognized label with an unknown unit is not a verified measurement even if its numeric part is in range.

Each local sentence/semicolon/newline clause is screened for explicit prior-memory, historical, negated, hypothetical or future scope. Such a clause is left for manual review instead of automatically compared as a present fact. This is a heuristic, not discourse understanding. It can miss paraphrases, complex quotation, unusual units or descriptions such as “eighty-six percent,” and can conservatively defer a valid present claim. Raw source remains available for full reading.

An incorrect current numeric candidate or step label that also appears in the supplied prior journal is marked as a lexical carryover candidate. Matching a prior number is not proof of causation or comprehension. The tool does not silently substitute a prior value for the current one. It does not assess an explicit historical claim without a reviewer locating the appropriate historical evidence.

Inference cues identify passages about convergence/stability, uniformity, eigenvectors/spatial meaning, learning/intent or causality. They always mean **review this passage**. “These values do not prove learning” and “this proves learning” both contain a cue; one can be responsible qualification and the other unsupported. An unsupported sentence with none of these words still needs review. Cue absence never grants scientific acceptance.

Extraction is bounded to 32 matches per kind and 512 characters per displayed clause; truncation is reported, with original spans retained. At most eight matching prior spans are expanded per candidate. Inputs are bounded to 16 journal entries, 64 KiB each journal/memory text and 16 MiB JSON. These are short-episode inspection bounds, not supported runtime capacity claims.

## Required whole-text review

For every entry, read the complete saved text, exact current prompt, typed observation and actually supplied prior memory. Complete each rubric field using `supported_within_scope`, `contradicted`, `not_established`, `unresolved`, or an explicit mixture with anchored subclaims. An omission is not automatically a false fact, and a future question is not an assertion of an achieved outcome. Record substantive claims the regex did not recognize.

- Check current identity and every stated numeric value, including rounded values and temporal comparisons.
- Keep recurrent state, sensory covariance, its eigenvalues, top-eight summaries and reduced fill distinct. A flat tail is not a uniform whole spectrum; eigenvalues are not eigenvectors or spatial semantics.
- Distinguish similar norm from unchanged coordinates or convergence. Inspect supplied changeL2 and the availability of earlier numerical evidence.
- Distinguish a cautious hypothesis from unsupported causal, training, learning, intent or sensory-meaning claims. Neither style compliance nor the absence of banned words answers this question.
- Record memory carryover/correction with exact text and value provenance. Do not attribute its cause without a comparison.
- Record directness, completeness, unnecessary prefaces/headings, repetition and word count separately from truthfulness. Preserve the original text.

Report a profile and concrete examples, not a composite score. All four v1 entries remain a known development set. All future v2 outcomes must be retained under the frozen protocol; later trajectories differ because feedback differs, so the resulting profile is a bounded descriptive comparison.
