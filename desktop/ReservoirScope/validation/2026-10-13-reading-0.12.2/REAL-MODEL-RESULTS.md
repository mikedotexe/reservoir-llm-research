# 0.12.2 real Gemma journal result

The actual local-model loop worked in this bounded run: four complete Gemma replies were saved, read back, and applied at the next numerical step; the next three prompts contained the exact latest applied journal text. The exported history passed whole-bundle replay. The prose was readable but not reliably scientific: it mixed correct measurements with stale labels, one carried percentage, and unsupported interpretations. Successful journaling and trustworthy interpretation are separate results.

## Exact workload and evidence

The parent agent explicitly created and started `sustained-1791919382664-3` in the 0.12.2 native app. [The UI account](REAL-MODEL-UI.md) records readiness, separate Create/Start, reading, minimization, keyboard interaction, native export and normal quit. [Creation](real-model-created.json) binds executable SHA-256 `2fa824855d1172ebf707b4f1ce5f50d2c3eb74ab4aeeb437d41dc566f818db8d`, configured model `gemma3:4b`, and owned endpoint `http://127.0.0.1:63515`.

The session used seed 20261013, cadence 30, requested pace 1 second per free step, 121-step and four-attempt ceilings, a ten-minute maximum and 64 MiB storage. It reached its original limits at 121 live/durable steps, four journals, 19 segments and 158,846 milliseconds of retained active time. There were no failed, cancelled, interrupted or skipped attempts in this export. These are four dependent entries from one short episode, not four independent replications or a multi-hour real-model qualification.

The model ran in an explicitly owned Ollama 0.40.3 process using the [reviewed selection](../2026-10-13-reading-0.12.1/model-selection.json) and [staged-cache receipt](../2026-10-13-reading-0.12.1/owned-model-cache-stage-01.json). The staged Gemma manifest SHA-256 was `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a`; selection SHA-256 was `7de0ae35b3d231201679b2242484cb24a9122a8f9ce866b8554dfe6384a2d86a`. [The startup receipt](owned-model-server-start.json) binds the owned listener and process. The reduced reservoir, forcing and sensory field are synthetic experimental machinery; the language replies in this run came from the actual selected local model.

## Replay, saved text and feedback

The immutable native export is `target/qa/0.12.1-reading/exports/sustained-1791919382664-3-3-143` under `desktop/ReservoirScope`. The directory's older parent name is not its producer version. Its manifest SHA-256 is `215162126a8701c55f8ad039cbd081071f84a6d18903366c0e723f69d2780d1c`; checkpoint SHA-256 is `1a066c4fec045169e8cacd582ba5b4d78a664be0576860c82e079eaa597c1e3e`. The bundle contains 1,781,880 bytes.

The prepared [offline checker](../2026-10-13-reading-0.12.1/check_real_model_export.py) ran once against the explicit 0.12.2 executable, pinning a byte-identical copy in `real-model-export-01`. [The passing receipt](real-model-export-01/receipt.json), SHA-256 `7cc9bc59a8ff6c27f5ab740e586d80821b4a383206b59b1606fb07dfd19094c1`, retains the entire original inventory, exact executable identity, numerical replay and journal associations. The original export was unchanged after verification.

`--verify-sustained` passed at 19:35:01.858704–19:35:02.254032 UTC on October 13. Measured verifier wall duration was 0.394506042 seconds, with peak RSS 13,713,408 bytes. [Stdout](real-model-export-01/cli-stdout.json) and [stderr/timing](real-model-export-01/cli-stderr-time.txt) are preserved. These resource values describe the offline verifier only, not the GUI, model service, GPU or energy use.

| Writing observed at step | First applied at step | Prior journal supplied in full | Returned token count | Recorded transport duration |
|---:|---:|---:|---:|---:|
| 30 | 31 | None | 184 | 7.089 s |
| 60 | 61 | 30 | 150 | 10.942 s |
| 90 | 91 | 60 | 207 | 12.152 s |
| 120 | 121 | 90 | 233 | 5.206 s |

All four retained responses identify `gemma3:4b`, have `complete: true`, and end with stop reason `stop`. Each has one matching dispatch event, accepted response, exact text/hash save receipt and unique next-step application. Prompt observations match the retained recurrent state and separate sensory summary. Each later memory object contains the latest earlier saved-and-applied journal, including its full text, hash and first-application step; none is merely inferred from a journal count. There are exactly four starts, four received responses, four saves, three memory-confirmation events and 121 numerical steps.

This qualifies the mechanical path for these four entries. It does not establish that the model understood its memory or that words alone caused a later state change. The fixed textual-feature codec supplies feedback; it does not train model or reservoir weights. Forcing, recurrence, noise and regulation remain part of the evolution.

## Close reading of all four entries

[Exact prose, prompts and observations](real-model-export-01/quality-review-material.json) are retained without cleaning or rewriting, SHA-256 `da9b912349e4a1efb60a07dac88cf12d35ac99246a41e7f3997c9ffc3d8b78a7`. [The authored review](real-model-prose-review.json), SHA-256 `e228a8e1646d6f9e2f63f0456dfc1c1472228e596bed7eb72891bca5000b922c`, contains 24 anchored annotations and exact numerical values. [Its script](review_real_model_prose.py) checks that the quoted passages occur in the saved text and derives the measurement table; the qualitative assessments are an agent close reading, not an automatic score. A second agent independently read all four entries and confirmed the main contrary evidence.

| Step | What the entry gets right | What needs correction or qualification |
|---:|---|---|
| 30 | RMS 0.226, leading sensory eigenvalue 0.654, entropy 0.8084 and fill 94.31% match the prompt at stated precision. | “Good convergence” and stability are not established by the first observation, whose prior change is explicitly unavailable. The near-flat tail does not justify calling the entire spectrum uniform. Sensory fill is not a direct measure of recurrent processing. |
| 60 | Head share 86.8% matches the current top-eight sensory statistic. | A “focus on spatial information” has no supplied basis. “Relatively low RMS” overlooks the rise from about 0.226 to 0.800 and lacks a reference threshold. Eigenvectors were not supplied. |
| 90 | Leading eigenvalue 27.05, RMS 0.83 and fill 12.35% round correctly. | The heading says “Observation 61,” while the current step is 90. Head share 86.8% repeats prior memory; current share is 85.54%. The claim of consistent values across all 32 modes conflicts with a spectrum spanning approximately 27.0491 to 0.0155241. |
| 120 | Leading eigenvalue 27.09, whole-percent head share 86% and fill 17.32% round correctly. | The “Observation 61” heading repeats. RMS 0.83 is stale or inaccurate at two decimals: current 0.82242177 rounds to 0.82. Claims about a learning plateau or deliberate suppression have no supplied evidence; the prompt expressly says writing does not train weights. |

All four entries are readable and finish their sentences. Three retain an assistant-style preface, and the latter two add Markdown headings despite the plain-text request. Those are presentation limitations, not missing or truncated journals. The entries repeatedly propose watching eigenvectors even though only coordinates and eigenvalues are supplied. Similar RMS values do not establish stable dynamics: the later prompts also report nonzero state-change L2 values of about 2.247 and 1.930.

The wrong heading and prior percentage recur in available memory, which makes carried prose a plausible contributor. This run has no matched no-memory condition, so it cannot establish that causal explanation. Exact context inclusion is proven; comprehension, reliable correction and scientific benefit are not. The next improvement suggested by this reading is better grounding of current-step labels and quantitative comparisons, tested separately rather than rewriting these retained entries.

## Reading behavior, shutdown and remaining limits

The [native UI account](REAL-MODEL-UI.md) records the old step-30 journal staying selected as later entries arrived, Follow latest remaining off, and keyboard activation later selecting step 120. It also preserves unsuccessful pointer/AX activation attempts; those are not mouse-path passes. The conservative minimized interval was about 91 seconds and included time after the finite bound, so it is not another sustained advancement or GPU-utilization test. [Normal app quit](real-model-clean-quit.json) separately confirms exact PID absence and unchanged package identity.

The original owned-model supervisor reported `Operation not permitted` during cleanup. That failure receipt is preserved. [Supplemental read-only checks](owned-model-cleanup-supplement-01.json) subsequently found the exact owned server and supervisor absent and their original process group empty three times, without additional signals or endpoint calls. This establishes the scoped absence observations; it does not turn the original cleanup into an error-free pass or identify the failing syscall. Escaped descendants outside the original group were not inventoried.

The checker made no service, model, UI or live-store calls. Owned Ollama request-body logging was disabled: prompts, returned identity and timing here are app-retained evidence, supported by the separately bound owned runtime, not independent wire-level request receipts. No causal learning, autonomy, consciousness, weight training, physical power-loss durability, broader model quality, or long-run real-model reliability claim follows from this short successful mechanical loop.
