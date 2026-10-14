# Prospective room-for-writing rehearsal — 0.14.0

This protocol is written before any 0.14.0 model output. The question is whether the newly bounded output/time/context settings permit complete open writing and an observable saved-journal continuity chain in one short native episode. The `reservoir-journal-v3` prompt stays unchanged. No heading, metric, topic, word count or literary form is prescribed; the reviewer does not control saving or feedback.

## Fixed run and admission

Use the same privately staged `gemma3:4b` model manifest as the prior episode, SHA-256 `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a`, and a newly qualified owned process/listener. The [run plan](run-plan.json) binds **1024 maximum output tokens, 180-second request deadline, requested context 8192, temperature 0**. These are limits, not a desired response length or proof that a complete response will fit. Sustained `outputTokens` and `requestDeadlineSeconds` must be explicitly retained with those values; historical omission means 256/60 and cannot substitute for this run.

Create one session with seed 20261013, cadence 30, pace 1000 ms, maximum 121 steps, four attempts, 900 seconds, 64 MiB, leak 0.65, noise 0.02, initial retention 0.955 and regulation enabled. The first reached bound governs. If all opportunities are reached and saved, observations occur at steps 30/60/90/120 and feedback first applies at 31/61/91/121. This is a target to observe, not assumed completion.

Before Start, record the exact package executable hash/version, new explicit loopback endpoint, staged model/runtime identities and retained configuration. Do not contact a default endpoint. Readiness is an explicit metadata check, not a writing attempt. The parent performs one passive pre-Start host-memory admission check using the established owned-run method: pressure level 1 and free percentage at least 35. If it does not qualify, do not Start; retain the reason rather than poll for a favorable reading.

The owned service receives a 1200-second lifetime from launch. Require at least 960 seconds remaining immediately before Start, preserving a 60-second margin beyond the session's 900-second ceiling. Otherwise leave the rehearsal unexecuted. Prepare the app before launch where possible. Four 180-second requests plus approximately 121 paced seconds leave some room within 900 seconds, but scheduling, saving and other overhead can still end the run earlier. This arithmetic is not a completion guarantee. No lifetime extension or replacement service is part of this plan.

There are **no retries, skips, sample replacements, additional prompts or budget extensions**. Any incomplete, timed-out, rejected, memory-failed or unstarted opportunity remains an outcome. A concrete runtime/resource problem can end the run early; retain its exact reason. An incomplete reply must not be silently promoted to a journal or counted as continuity. No reviewer annotation triggers a rewrite or new generation.

## Mechanical evidence

Retain the exact native exported bundle, configuration, package identity and UI execution record. Run the pinned packaged whole-chain verifier offline before secondary interpretation. Whole-chain replay is the authority for numerical state, full prompt construction and typed event consistency; it does not independently authenticate provider execution or power-loss durability.

Use this directory's [versioned checker](check_real_model_export.py) with explicit expected package hash/model/endpoint, `--expected-prompt-version reservoir-journal-v3`, and mandatory `--protocol` pointing to this plan. It rejects older output/context/deadline settings or changed session budgets, unexpected retries/skips, and attempt/step overruns. Complete responses above the old 256-token limit are eligible when their retained count fits the actual new budget. The earlier 0.13 checker and records remain immutable.

For each response, retain its actual completeness/stop reason/output token count and any failure, independently of saving. For each saved journal, check exact UTF-8 text/hash, save/readback receipt, source/dispatch/response/save order and actual application at the next step. For later journals, require the memory object to equal the latest earlier saved-and-applied journal and require exact JSON-decoded full text in the retained prompt, with matching journal/hash/path/application boundary. Saved-but-not-applied or skipped text is not eligible memory under this mechanism.

Account for all four planned opportunities: started, received, complete, saved, applied, failed or unstarted are different columns. Keep bounded unsaved response evidence, including explicit prefix truncation if relevant, rather than hiding a cutoff behind zero saved journals. Originals remain unchanged. If native export cannot be obtained, any passive committed-file copy must be separately authorized and clearly labeled a deviation; it does not qualify the native export flow.

## Context availability and continuity

Configured context 8192 is **requested capacity**. The exact retained prompt and decoded memory establish what the app prepared and dispatched according to its records. They do not prove tokenization, absence of provider truncation, complete processing, comprehension or a causal influence on the next entry. Prompt UTF-8 byte and Unicode character counts are retained descriptively; they must not be converted into a token-fit claim.

The current typed response retains output token count but no `prompt_eval_count`. The checker therefore reports provider prompt-evaluation count as unavailable, not zero. If a separately retained provider artifact later exposes usage, label it provider-reported, preserve its source/meaning, and do not treat a count alone as exact content coverage. No new provider logging or introspective call is authorized here.

Read every received response, including incomplete responses, separately from the mechanical table. Describe chosen topics/form, continuation, revision, departure, questions, repetition and treatment of earlier writing. Exact prior text availability is one fact; a later passage appropriately using or challenging it is another. Do not require an entry to echo its predecessor, claim that lexical overlap proves comprehension, or infer hidden memory when no journal was supplied.

The first pre-feedback v3 prompt can be compared with the retained 0.13 first prompt as a scoped implementation check because seed/numerical settings/prompt version are unchanged. Later observations may diverge as writing changes feedback. Even identical first prompt text would not isolate output budget from deadline, requested context or runtime conditions.

## Reading and finish line

Apply the unchanged frozen `open-writing-review-2` [quality harness](../../scripts/journal_quality.py) to hash-bound saved-journal material, then use the [manual rubric](RUBRIC.md) on all responses. The harness is a partial extraction aid with no automatic scientific or creative-quality verdict. Absence of metrics, a step heading or a preferred length is not a defect. Determine whether a passage asserts a literal fact before comparing it with evidence; imaginative or subjective prose is not automatically a scientific claim.

Report completion/save/application/memory observations and the writing separately. The prior 0.13 first response stopped at 256 tokens; it is preserved as historical context, not discarded because this run might finish. This tranche changes several resource settings together and has only one episode with dependent successive entries. It cannot establish a causal budget or prompt benefit, a general success rate, emergence, consciousness, model learning or long-duration reliability.

Before any output, freeze the plan, protocol, copied checker/tests, unchanged quality-harness identity, v3 prompt-vector identities and prior reference receipts. The parent owns service/UI execution and cleanup. The evaluator makes no app, model, provider or live-Being calls. A faithful, reviewable partial or unsuccessful outcome can complete this inquiry without authorizing further requests.
