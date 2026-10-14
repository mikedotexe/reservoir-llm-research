# Journal-quality evaluation preparation

The prospective [protocol](PROTOCOL.md), [run plan](run-plan.json) and [rubric](RUBRIC.md) are ready before new v2 outputs. The bounded actual rehearsal is four requests with the previously selected Gemma manifest and unchanged finite session limits. It includes no additional frozen-prompt comparison, automatic retry or replacement samples. Later trajectories can differ because feedback text differs, so the resulting comparison is descriptive, not a causal prompt-improvement claim.

## Source and checks

The new offline [harness](../../scripts/journal_quality.py) produces source-bound transcription candidates, current-step labels, rounding/unit checks, coverage gaps, lexical carryover candidates, style observations and inference-reading cues. It never awards scientific correctness. It requires a passing immutable-export receipt whose material hash and retained prompt version match the inputs. Text is never executed or used as instructions.

[Twenty-two focused tests passed](quality-tests-03.log), with [closed execution interval and source hashes](quality-tests-03.json). These cover current versus prior labels/numbers, precision and coarse-percent rounding, units, scalar-percent mistakes, ordinal eigenvalue ambiguity, missing values, negated/qualified statements, unsupported claims without cue words, safe statements with cue words, inert instructions, extraction bounds, invalid source values, receipt mismatch, version mismatch and output preservation. [Synthetic fixtures](synthetic-fixtures.json) are authored examples, not model responses.

The first run, [quality-tests-01](quality-tests-01.json), failed one fixture whose `is86.8%` typo fell outside the deliberately limited grammar; the log is preserved. The second run passed 20 tests. Independent peer review then found two substantive unit/identity gaps: an unexpected percent sign on a scalar could be marked consistent, and a bare/ordinal eigenvalue could be compared to the leading mode. Both now route to review, with two new passing regressions in the final 22-test run. Earlier logs and the first v1 report remain historical.

No runtime Rust, UI, bundle, dist or app source was changed by this work. No service launch, model request or UI operation was performed. Tests invoked only the offline Python evaluator.

## Immutable v1 reference

The original four-entry [review material](../2026-10-13-reading-0.12.2/real-model-export-01/quality-review-material.json), [replay receipt](../2026-10-13-reading-0.12.2/real-model-export-01/receipt.json) and [manual close reading](../2026-10-13-reading-0.12.2/real-model-prose-review.json) remain unchanged. Their exact hashes are bound in the protocol/freeze receipt. V1 is known development/reference material, not a held-out test.

The final harness [v1-reference-report-02](v1-reference-report-02.json) recognizes 13 metric claims across four journals: ten consistent at the written precision, two mismatches and one requiring scope review. It recognizes two incorrect current observation headings; another step reference requires scope review. The numeric mismatches are the already reviewed step-90 head share and step-120 RMS. “86%” at step 120 is correctly accepted as coarse rounding. No missing required-metric count is imposed retroactively on v1.

The scope-reviewed step-90 fill value is numerically correct in the independent manual review, but its clause contains future/conditional language. This is a known conservative limitation, not a newly discovered false statement. Other unsupported interpretations cannot be established or dismissed by metric regexes. The manual reviewer still reads all four texts and all substantive claims.

## Applying the frozen contract to v2

After the parent supplies the exact v2 export and package identity, first run the separately pinned whole-bundle integrity checker. Then apply this frozen quality harness to its hash-bound material with `--prompt-version reservoir-journal-v2` and a new output filename. Retain the actual config `promptVersion`; do not infer it from good-looking prose.

Review all retained attempts, including any incomplete outcome, and manually assess every successful entry using the same dimensions. V2 asks for `Step N.`, current RMS and separate sensory fill, approximately 60–100 words, and one cautious next-observation sentence/question. Missing these is coverage/style evidence, not automatic falsehood. Correct numbers can coexist with unsupported conclusions; clean style can coexist with incorrect science. Record both improvements and remaining errors with exact excerpts and current evidence.

No actual v2 journal result is asserted by this preparation record. The [freeze receipt](evaluation-freeze-01.json) binds the final checker, tests, protocol, reference inputs and reports before new outputs.
