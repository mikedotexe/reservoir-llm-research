# Three local models with continuing inquiry — 14 November 2026

Status: three primary sessions running from approximately 14:25 PST, with recoveries retained. This is a separate laptop apparatus experiment, not a run of Astrid or Minime.

Mike selected three-hour runs with the same default conversational prompt every hour, telemetry enabled, and the new continuing inquiry and authored-vector probe controls. The comparison is Gemma4 12B, GLM-4.7-Flash Q4_K_M, and Mistral’s Ministral 3 8B Instruct Q4_K_M. The last is a compact local Mistral-family instruction model, chosen to leave room for simultaneous inference on this 64 GiB laptop; it is not a claim to be Mistral’s largest or newest flagship.

The initial prospective protocol and all private evidence are in `research/outputs/three-model-inquiry-20261114/` in the `codex/three-model-inquiry` worktree. Its protocol fixes a fresh seed of 20260909, authored-v3, semantic input through `nomic-embed-text:latest`, 16,384 context tokens, 1,024 output-token ceiling, temperature .7, thinking off, a 30-step ordinary cadence, and 1000 ms requested pace. Three separately compiled app identifiers isolate windows and storage. A separate loopback-only Ollama service uses the existing local model files.

## Question and prospective reading

What develops over these three trajectories, particularly when an entry can keep a question open, examine retained local evidence, choose a specific 48-coordinate probe, and later encounter the recorded result? The primary material is every hourly opportunity: nine responses if all complete, with failures and absences retained. Two independent readers see shuffled response-only samples before model and hour labels are disclosed. The secondary ordinary sample is the first ordinary entry and the one immediately before each check-in, deduplicated by ID. Neither sample is selected for striking prose.

After that first reading, recover the exact supplied context and inspect inquiry continuity, actual action and input application, response lengths, request outcomes, admission lag, steps, and entry counts. These are three dependent developing sequences. Equal elapsed duration does not equal numerical exposure or feedback count, and concurrent inference adds shared resource contention. The study describes differences; it does not identify a causal model effect or establish subjective experience. Yesterday’s V2/8K sessions differ in more than model identity and are historical context only.

## Qualification and completion

The existing 0.46 source qualified inquiry persistence, probe replay and explicit encoding recovery. A cold concurrent test with the largest synthetic retained-history prompt exceeded the app’s 180-second request limit for Gemma and Ministral; GLM completed in 167.6 seconds. Before any study writing, the protocol was amended to a uniform 600-second allowance, using the validated 0.46.1 increase of the selectable maximum (`ee7c65e87fc107e3d64d81b7b562f25150e8b014`). The default remains 180 seconds. The initial unstarted Gemma preparation at 180 seconds is retained and excluded from the study.

Start only after qualification under the final settings. At completion each arm must have all three hourly outcomes marked applied with saved journal IDs and application steps, followed by an immutable snapshot and successful native offline replay. A terminal label alone is insufficient. No automatic writer retries, skipped opportunities or selected replacement samples are planned. A bounded observer watches durable metadata without changing app state.

The private protocol, model digests, build receipts, preflight results and start manifests are the authoritative exact configuration record. Results and any deviations will be appended after completion.

The repeated cold concurrent capacity trial completed normally for all three writers:
Gemma 306.5 seconds (11,127 prompt / 228 output tokens), GLM 216.1 seconds
(9,629 / 331), and Ministral 260.4 seconds (11,700 / 898). All returned a complete
nonempty reply with a normal stop; all four models, including Nomic, remained loaded.
These are synthetic capacity diagnostics, excluded from the study sample. Shared
compute remains substantial and memory headroom is limited; a passed stress test is
not a guarantee against later failures. Exact receipts: `preflight-600/assessment.json`
and the per-arm response metadata.

All three signed native builds are 0.46.1. Core generation-budget tests (7), targeted
host/transport tests (5), and frontend/controller tests (40) passed, along with
TypeScript, production build and formatting checks. Fresh ready manifests match the
prospective protocol exactly apart from writer model, with zero elapsed time, steps
and journals. `ready-audit.json` retains the independent storage paths and hashes;
`protocol-before-start.json` freezes the final settings before any Start action.

## Output-budget amendment before the primary runs

The 1,024-token sessions started around 14:07 PST. GLM ordinary attempt 9 at step
270 returned `stopReason=length`, `tokenCount=1024`, `complete=false` after 104.438
seconds. The app held that attempt and excluded it from feedback. This was an
output ceiling, not the request deadline. The other two sessions were paused at
settled boundaries, retaining their last saved but unapplied replies. The three
pilot snapshots preserve 9 Gemma, 8 GLM and 10 Ministral journals; every scheduled
hourly opportunity is still pending. These are explicitly incomplete pilot
trajectories, not three-hour outcomes or replacement hourly samples.

Before restarting, all three fresh primary configurations were changed uniformly
to the existing maximum of 2,048 output tokens. Every other numerical, language,
prompt and schedule setting is unchanged. Primary exact settings, ready manifests
and subsequent outputs live under `primary-2048/`; `pilot-1024-exports/` retains
the complete pilot material with source/destination hashes. The model identities,
0.46.1 source and app binaries are unchanged. This amendment is based on the
recorded operational failure before any hourly sample existed, not on a prose
preference.

A diagnostic call using the blocked GLM prompt and derived attempt seed with the
larger allowance returned a complete 304-token reply. It was never applied to
any session. Because it is a different shorter response, it does not demonstrate
that the same truncated reply would have finished or that all later entries will
fit. It is retained separately, with the original incomplete attempt unchanged.

## Primary ordinary-attempt recovery

At 20 minutes 14.444 seconds of GLM active time, ordinary attempt 18 at step540
hit the 2,048-token ceiling (`complete=false`, `stopReason=length`) after181.406
seconds. No text from that attempt entered feedback. The failure and pre-recovery
checkpoint are retained. At approximately14:47 PST, the steward-side agent explicitly
skipped the failed ordinary attempt and resumed the same session without changing
its configuration or retrying that opportunity. This deviates from the initial
no-skip plan: the same operational handling will apply to any arm’s incomplete
ordinary entries. Every intervention remains in `primary-2048/recovery-ledger.jsonl`
and the native event stream. Scheduled hourly opportunities remain separate, with
no selected replacements. Paused recovery time does not count toward active time.
