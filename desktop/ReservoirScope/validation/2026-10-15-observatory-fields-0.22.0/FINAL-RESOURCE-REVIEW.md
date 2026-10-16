# Final resource evidence review: Observatory 0.22

Reviewed at **2026-10-15T22:10:55.414704+00:00** by the independent qualification agent. The review used existing files only: no tests, sampler, executable, UI, process, network, or resource probe was run. Only this report and [RESOURCE-RESULTS.md](RESOURCE-RESULTS.md) were written.

**Finding:** no concrete blocker to reporting the four closed windows as short, descriptive main-PID measurements. The prospective exact settled playback row witnesses are unavailable and are explicitly limited in the results. There is no general performance, GPU, leak, or endurance pass.

## Independent checks

- Recomputed each phase directly from all raw monotonic timestamps and cumulative CPU deltas, without calling the sampler's analyzer. The four declared durations, sample counts, interval counts, covered durations, duration-weighted CPU percentages, and RSS/thread/descriptor minimum/median/maximum values match [main-process-analysis-01.json](main-process-analysis-01.json) exactly.
- Checked the 121 sequential samples, strictly increasing sample timestamps, all 120 cumulative-counter differences and interval origins, nonnegative CPU deltas, every `identityVerified` flag, process/descriptor availability, and empty raw error lists. Every descriptor count is 13. No missing sample was converted to zero; the initial baseline alone has no prior CPU interval.
- Confirmed all named phases are closed and bounded by their actual adjacent markers. Only intervals wholly inside each phase were counted; no interval exceeds the 7.5-second eligibility limit. Settling is at least 15 seconds for each phase. All four declared windows and their eligible CPU coverage exceed 60 seconds.
- Recomputed header-to-footer duration as **600.014794792 seconds** and first-to-last sample span as **599.999199083 seconds**. The completed footer contains the correct 121-sample count, no error, and the same final executable SHA-256 as the header. No separate post-capture PID check is claimed: identity was checked at each sample, including the last, and the footer confirms executable bytes.
- Checked the analysis's raw/marker/analyzer identities, and the raw header's launch-receipt/sampler/qualified metric-source identities against the corresponding file bytes. All **12 inputs** in [measurement-freeze-01.json](measurement-freeze-01.json) still match their frozen SHA-256 values. This checks those evidence files and source bindings; it does not rerun the package or recursively requalify every package file.
- Read the [operator UI witnesses](resource-ui-witnesses-01.json) separately from process metrics. They support unchanged idle/restored row/draw witnesses and the declared untouched minimized interval. They do not provide synchronous settled playback row boundaries or localize the minimize/restore draw difference. The process analysis does not infer window state or GPU work.
- The reporting-only [UI correction](ui-functional-correction-01.json) preserves the original receipt and resolves the one-versus-two input-refresh count. It does not change the measurement, product, or package.

## Bound evidence

The following identities were checked before writing and rechecked after writing the reports:

| Evidence | Bytes | SHA-256 |
|---|---:|---|
| [main-process-samples-01.jsonl](main-process-samples-01.jsonl) | 58494 | `ed313736f1dd8c538d3d8c0361f4a3435b5fd33854e4dde4acbecf5a6e208c1b` |
| [resource-markers-01.jsonl](resource-markers-01.jsonl) | 2153 | `ffe0be393f82af2f639d7b0cc5c1022c7e76136c4e789e8c198057cc09c7f9e4` |
| [main-process-analysis-01.json](main-process-analysis-01.json) | 5371 | `1b6006b1b5e8d6fd099166b8ab61c56969ffb2782936b2451dd44238908ff6b4` |
| [measurement-freeze-01.json](measurement-freeze-01.json) | 3191 | `01fd5d558d948243109d8e232bec2a44a9a481e3095f5887f6870c785e4fbe47` |
| [resource-ui-witnesses-01.json](resource-ui-witnesses-01.json) | 2349 | `6427938846017322eaf36595d5ccd450db9024ef26fd5f5f0a45fc4c7154e7e8` |
| [ui-functional-correction-01.json](ui-functional-correction-01.json) | 555 | `dbcb1303d4f1ffec875a4f964093a87822feb64f6dfa5e644ef98d36819f5ecc` |
| [RESOURCE-PROTOCOL.md](RESOURCE-PROTOCOL.md) | 5883 | `f760bd963ec4b279dca735a54bfba64b32b9fde94ccac041ae4b333679410294` |
| [sample_owned_app.py](sample_owned_app.py) | 14685 | `bf1a6092a30f5a23334f663c56c875d2dd6d317eaed540778fb3fa766cb1d314` |

The launch/header executable SHA-256 is `788b636ec898f9863e146e7dfe67c380910ae38943b0b178f6e22b8e8d794051`, main PID 74000. The metric reader is the frozen `scripts/macos_reliability.py` implementation with SHA-256 `326fb72a668f1cac1f32585e0b61e791a56a959b1ac0ae32560fcebd0fba5215`; no new CPU-unit calibration or host measurement was performed in this review.

Remaining scope is unchanged: no separate WebKit/GPU attribution, total application footprint, energy/frame-pacing estimate, causal RSS interpretation, repeated comparison, other-platform evidence, or endurance result. Final app exit and whole package/source preservation are handled in the lead's separate closeout evidence.
