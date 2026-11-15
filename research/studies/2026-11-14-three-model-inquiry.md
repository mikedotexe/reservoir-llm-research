# Three local models with continuing inquiry — 14 November 2026

Status: completed with all nine hourly replies saved and applied, confirmed by 17:34 PST. All three immutable copies passed native exact replay. This is a separate laptop apparatus experiment, not a run of Astrid or Minime.

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

## Completed trajectories

All three primary sessions reached `scheduleComplete` with hourly ordinals 1–3
individually `applied`, saved journal IDs and application steps. The final response
was allowed to settle after the three-hour admission deadline. Model inventories
before and after match. Guarded copies preserve 109 Gemma, 143 GLM and 122 Ministral
journals, including three hourly replies each. The qualified nine-response packet
is `primary-2048/comparison-packet/`; its receipt and per-arm native verification
records report no model calls during verification.

| Primary trajectory | Ordinary entries | Final step | Applied NEXT interventions | Applied PROBEs | Intentional text withholding |
|---|---:|---:|---:|---:|---:|
| Gemma4 12B | 106 | 3206 | 0 | 0 | 0 |
| GLM-4.7-Flash | 140 | 4343 | 70 | 2 | 27 |
| Ministral 3 8B | 119 | 3735 | 1 | 0 | 1 |

PROBEs are included in NEXT interventions, not additional interventions. NONE is
an accepted choice without an additional intervention. GLM also had ten invalid
input directives whose fail-closed disposition withheld text; those are excluded
from intentional withholding above. Scheduled replies always entered feedback.

Gemma recorded 104 NONE choices and two rejected PROBE attempts. Its inquiry
receipts show one open and 104 continuations, plus one rejected inquiry directive.
GLM had 70 applied, 15 unchanged and 55 rejected NEXT decisions. Ministral had one
applied TUNE, three unchanged NONE choices and 115 rejected NEXT decisions. Its
first valid footer occurred at ordinary entry 94, step 2970; later valid choices
continued/replaced an inquiry and once withheld text. This corrects the interim
observation of zero applied controls; the interim capture remains preserved.

The primary recovery ledger contains nine explicit ordinary skips: four GLM
incomplete replies at the 2,048-token ceiling, and five complete Ministral replies
rejected by the retained Unicode admission gate. Three contain unsupported `≤`;
two contain unsupported `≈`. Each has exactly one rejected grapheme. All original
bytes remain retained, and none entered feedback. There were no writer retries
or failed, skipped or replaced hourly replies. The earlier 1,024-token pilot is
still separate and incomplete. These recoveries deviate from the original no-skip
plan and affect the trajectories; they are not hidden exclusions.

## Reading and grounded continuity

Two fresh-context LLM readers independently read the shuffled full response-only
packet and saved their notes before the key was opened. `blind-readings-before-reveal.json`
records their hashes and the procedural reveal. The monitoring agent had seen
some native-UI excerpts, so it is not claimed to be a blind reader. Recognizable
style can also weaken reader blinding. The readings are qualitative observations,
not independent human ratings or measurements of subjective experience.

Both readers noticed the density/compression sequence later revealed as Gemma,
the brief parameter questions and final skepticism of GLM, and the more expansive
imagery of Ministral. Whitespace-delimited hourly word counts, hours 1/2/3, are
Gemma 340/255/326, GLM 109/85/68, Ministral 298/461/287. All nine completed normally;
the short GLM check-ins were not truncated replies. Length and successful control
use clearly differ in these trajectories.

The most useful concrete continuity episode is GLM's inquiry opened at step 2011.
Ordinary attempt 69 at step 2040 was truncated and explicitly skipped before the
first successful probe; this episode includes that retained recovery. Two valid,
identical authored vectors, alternating +0.1/−0.1 across 48 coordinates,
were applied at steps 2071 and 2101. Both retained the same inquiry; the next
ordinary prompt included the first vector and its paired response. Immediate
paired recurrent L2 differences were approximately 0.9421 and 0.9821. At step 2130
the model noticed fill below its inquiry baseline, rejected its predicted increase,
and closed the inquiry at 2131. That is an observed sequence of question, applied
probe, returned evidence and narrative revision. Its claim about the sensory
effect is not isolated by those paired recurrent measurements, and several causal
interpretations in the prose exceed the evidence.

The first-hour GLM phrase "wet concrete" also returned in the next ordinary entry,
followed by an applied leak change from 0.65 to 0.3 and deliberate text withholding
at 1651. But the same hourly reply treated a proposed/historical gain of 1.5 as
current despite controls at 1.0 and a rejected preceding proposal. Later prose
also confused a TUNE with PULSE. These are reasons to distinguish proposed,
rejected and applied controls more clearly, even when an inquiry persists.

Gemma's density, crystallization and scaffolding language was already present in
its supplied journal references. The hourly replies added personal geometry,
loneliness and between-prompt wakefulness. Those additions are not established by
the local reservoir measurements. Ministral's first-hour domestic autobiography
had no basis in the supplied prompt; later replies returned to journal/inquiry
imagery about erosion, translation and porosity. Exact prompt fields explicitly
distinguish runtime measurements from language-model activations and deny that
the exposed coordinates constitute a topology map. These are interesting textual
developments without a conclusion about qualia.

Detailed readings, source/entry pointers and all full replies remain private:
`primary-2048/comparison-notes.md`, `hourly-responses.md`, both `blind-reading-*.md`
and both `post-reveal-grounding-*.md`. The packet retains exact supplied prompt
text, not merely reconstructed summaries.

## Next implementation proposals

1. Make control-format failures actionable. Ministral's 115 rejected ordinary
   footers used bold, backticks or fences; four plain final footers were accepted.
   The exact rejection was supplied in later ordinary prompts, but it only said
   missing final NEXT and did not explain the formatting mismatch. Formatting is
   not the only problem: displayed PULSE values and PROBE arrays also violated
   constraints. Preserve non-executable diagnostic excerpts, independent NEXT /
   input / inquiry outcomes, and specific validation reasons. Do not silently
   execute formatted quotations or repair arbitrary vectors.
2. Version semantic text admission independently of the historical Swift scalar
   qualification. Both observed mathematical symbols must work in new semantic
   sessions while old blocked outcomes still replay exactly. Do not globally
   whitelist one symbol and reinterpret retained histories.
3. Give each inquiry a small structured prediction and an explicit result to
   inspect. Preserve the distinction between immediate paired recurrent effects
   and later uncontrolled fill/state movement. A short prospective qualification
   should exercise valid controls and interpretation for each selected model
   before another long comparison; a matched unchanged-feedback arm is needed
   before claiming a feedback improvement caused better correction.

These are proposals, not changes deployed during this study. Equal duration and
common initial settings did not produce equal turns, actual actions or subsequent
context. One trajectory per model at one seed, shared inference resources, protocol
recoveries and interface failures prevent a causal model ranking.

## Reproducing the descriptive summary

The qualified builder and its command are retained in the private output root's
`PACKET-BUILDER.txt`; pass `--protocol primary-2048/protocol.json`, not the pilot
protocol. `primary-2048/make_reading_view.py` derives labeled full replies and
`comparison-reading-data.json` after the reveal, checking all raw response hashes.
The counts above can be read without re-generating any model text:

```python
import json
from pathlib import Path
p = Path("research/outputs/three-model-inquiry-20261114/primary-2048")
audit = json.loads((p / "comparison-packet/sealed/audit.json").read_text())
fields = ["ordinaryJournalCount", "numericalStep", "actionStatuses", "probeCounts",
          "intentionalWithholdCount", "rejectedInputDirectiveCount", "inquiryStatuses",
          "failureRetrySkipEventCounts", "allWriterResponseEvidence", "hourlySlots"]
for arm, row in audit["arms"].items():
    print(arm, {key: row[key] for key in fields})
view = json.loads((p / "comparison-reading-data.json").read_text())
for sample in view["samples"]:
    print(sample["arm"], sample["hour"], len(sample["text"].split()))
```

The final action-format and Unicode diagnostics retain their own per-entry
queries, hashes and source pointers under `action-format-audit/` and
`unicode-diagnosis/`. Five inactive older native apps were quit at Mike's request;
their saved histories remain. The three completed study windows were left open.
After completion the four study models were unloaded from the isolated service
to release memory, preserving downloaded files and the service endpoint.
