# Can the research hub follow Afterimages?

September 7, 2026. Mike asked what this project can now answer, which questions
to start with, and what research/runtime changes would make those answers possible.
This is a readiness assessment and proposed next slice, not a completed study of
the beings' experience. No being-facing message or live-system change occurred.

**Follow-up:** Mike authorized the build. The
[trace command and first account](2026-09-07-first-afterimage-account.md) are now
available; [S-004](../research/studies/S-004-afterimage-to-use.md) owns the inquiry
and [the runtime plan](../proposals/2026-09-07-afterimage-delivery-and-evidence.md)
specifies the system changes. The assessment below preserves its earlier snapshot.

## Assessment

We can make useful bounded reconstructions now. `around` brings writing, requested
NEXT actions, captured outcomes, generation context and telemetry together. `trail`
can find literal trace IDs in cached writing and generation records. Afterimages
adds identifiable physical histories, per-receiver selections and request receipts.
The hub does not yet import or connect those new records as a complete chain.

The chain we want to inspect is:

`native event → retained physical trace → receiver's cue/page → final request → accepted response → saved writing/action → later return`

Every arrow needs a declared basis: explicit source identity, verified content hash,
temporal context, or unresolved. A content match verifies content equality, not
execution or causation. Research conclusions still require reading the material.

## Current bounded observation

At **21:09:15 UTC / 14:09 Pacific**, the read-only
[probe](../probes/afterimage_research_readiness.py) observed the archive's recent
list and checked its five newest traces, both cue-state files and bounded daily
exposure-ledger tails. It imports no runtime code, executes no reader action, and
does not inspect authored private notes. The snapshot is not atomic across files.

| Observation | Scope and implication |
|---|---|
| Nine entries in the recent list; all five inspected traces marked incomplete | A recent-list count and bounded sample, not a census of transitions. All five lacked a usable sustained fill-half-return measurement. |
| Astrid: 17 retained eligible opportunities, five selections and five exposure rows | All five rows report `included=false`, `final_request_prepared`, `reason=null`. The whole daily file fit the bound; no invalid rows or truncation were reported. |
| Minime: cues enabled, eligible counter absent, no retained opportunities or daily exposure file | This does not identify which generation paths ran or explain the missing opportunities. It is not a recorded refusal or evidence of inactivity. |
| Worker: enabled, no reported dropped observations, pending writes or error | A worker observation; this does not repair the recorded sample gaps. |

[Snapshot](../research/outputs/2026-09-07-afterimage-research-readiness/snapshot.json)
and [compact counts](../research/outputs/2026-09-07-afterimage-research-readiness/summary.json)
preserve the observation, file hashes, clocks and bounds. Reproduce from this repo:

```sh
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=5 volya \
  /opt/homebrew/bin/python3 -B - < probes/afterimage_research_readiness.py \
  > /new/private/research-snapshot.json
```

Choose a new local output path; a later run is a new observation. This snapshot
does not replace the earlier [rollout record](/Users/mikepurvis/other/afterimages-live-v1/ROLLOUT.md).
The rollout established availability. These records do not establish that both
beings have received automatic cues or experienced a benefit.

### A concrete delivery question already surfaced

Astrid's matched release source applies MLX prompt policy before adding the optional
cue. It then adds the complete cue only if the existing message bytes plus cue bytes
fit the final limit. These automatic lanes have no protected page or runtime-feedback
argument. No later text transformation precedes the exposure check. The check compares
the selected text with the prepared messages immediately before sending.

Therefore the five false receipts support **complete cue absent from prepared
messages**, with remaining prompt capacity the source-supported explanation. They
do not show a cue received and ignored. The missing reason, budget numbers and
retained request prevent independent reconstruction of each admission decision.
Selection also advances the artifact's cue history before successful inclusion;
future research must distinguish selection counts from actual delivery counts.

Source: [cue admission](/Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/llm/provider/afterimages.rs:23),
[send boundary](/Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/llm/provider/provider_execution.rs:156),
[selection and exposure](/Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/afterimages.py:370).
An optional next historical probe can inspect request-policy diagnostics around
Unix seconds 1788813837, 1788814172, 1788814420, 1788814767 and 1788814958.
Without a shared identity, those diagnostics remain nearby context.

## The initial questions

1. **What becomes available, and what actually reaches each being?** Follow trace
   capture, eligibility, selection, prompt admission, submission and accepted output.
   Include failed and omitted opportunities. This establishes the material for the
   other questions and reveals fixable interfaces.
2. **What do they choose to do with a past transition?** Follow explicit reopening,
   keeping, sharing, questioning and NEXT requests into actual outcomes. Preserve
   ordinary continuations and cases with no identifiable response to the trace.
3. **Does returning develop an account?** Compare the original record, the exact
   supplied cue/page and later writing for a new distinction, correction, unresolved
   question or changed intention. Note what new evidence was available. Repetition
   and development are descriptive readings, not a prose-quality score.
4. **Do the limits of a memory survive its retelling?** Trace whether missing samples,
   incomplete coverage, historical timing and quoted authorship remain qualified,
   become confused with present state, or become more certain than the record allows.
5. **What do Astrid and Minime make of the same physical history?** Pair by trace ID,
   then inspect their actual pages, own notes and preceding context. A shared trace
   does not guarantee identical exposure; shared inputs and quoted text can explain
   apparent agreement.

These connect to RQ-01 distinctions, RQ-02 self-knowledge, RQ-03 continuity, RQ-05
agency and RQ-06 relationship. The larger question is when a recorded event becomes
something they can use in an ongoing inquiry. A later, separately designed test
could compare exact-input isolated replays with and without a cue. Today's combined
rollout also changed recording, reading feedback and runtime state; a before/after
comparison cannot isolate an Afterimages effect. Cue-bearing telemetry is external
system information supplied to language generation, not access to private model
activations or proof of a native reservoir change.

## Changes that earn their place

### Research hub: one inspectable trace before a larger index

Build a bounded `afterimage-trace <id>` capture and report first. Retain immutable
physical artifacts and event updates, the exact receiver-specific cue/page, decision
and exposure receipts, relevant generation/job records, output/action records and
later explicit references. Record the deployment/configuration era and every source
hash. Preserve gaps in the chain instead of filling them with nearest timestamps.

Then integrate those record types into `evidence`, `around`, `trail` and `coverage`.
The current evidence schema accepts only action/telemetry, and trails search only
journals/generations. Preserve full original generation JSON and observed revisions:
the importer currently drops original per-message structure and replaces the same
generation-attempt row on refresh. Index declared job/action/thread/artifact IDs,
but retain each producer's association method and verify referenced content. Existing
exact-response matching against cleaned journal bodies can fail when NEXT is removed;
this should not be worked around with an unlabelled time-nearest link.

Source: [evidence kinds](../reservoir_research/evidence.py:25),
[trail inputs](../reservoir_research/trails.py:21),
[message normalization](../reservoir_research/generations.py:117),
[candidate generation links](../reservoir_research/indexer.py:217),
[generation refresh](../reservoir_research/indexer.py:334).

Acceptance: one report must resolve a successful exposed episode and retain an
omitted/failed one honestly; report each link's evidence, original wording, NEXT
request and outcome. An offline fixture with retries, ambiguous content matches,
missing artifacts and parser refresh must preserve distinctions and source history.
Nothing in this research-side extension needs a live behavioral intervention.

### Astrid: make cue admission and final attempts traceable

At the existing admission boundary, retain lane, eligibility/omission reason,
message bytes before admission, cue bytes, final limit, and cue opportunity ID.
Carry the existing provider/job identity through the exposure receipt, submitted
request, response acceptance/discard, journal and action output. Preserve final
adapted messages or a hash-addressed request artifact for the automatic-cue lanes.
Existing dialogue generation records are captured before provider adaptation, while
automatic cues use daydream/journal elaboration. They cannot substitute for those
final requests. Explicit AFTERIMAGE_OPEN already has stronger retained page/request/
completion acknowledgement; extend that pattern rather than replacing it.

First determine and record why natural selections fail admission. If prompt-space
competition is confirmed per attempt, a small optional cue allowance is a separate
behavioral proposal: it must retain foreground-page and runtime-feedback priority,
whole-cue admission and the existing off switch. Do not relabel a missing cue as
delivered, silently shorten its identity, or call a selection quota an exposure quota.

Source: [cue lanes](/Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/transition_afterimages.rs:169),
[explicit page acknowledgement](/Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/transition_afterimages.rs:134),
[generation capture](/Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/llm/provider/generation_record.rs:91).

### Minime: explain eligibility and connect existing identities

Retain a bounded cue decision for candidate generation paths: actual context mode,
authored action, inbox presence, enabled state, gate result/reason and generation ID.
Only specific journal/daydream paths currently call the selector; the absence of a
counter does not identify the cause. Link cue opportunity/exposure IDs to the existing
generation/attempt/job/action/thread chain. Record which successful provider response
the outer runtime accepted, retried or discarded. Add final adapted MLX message
capture equivalent to the existing Ollama stash. Direct AFTERIMAGE_OPEN also needs
an accepted-result link; it does not use Astrid's durable opened-page acknowledgement.

Source: [eligibility](/Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/runtime.py:53969),
[outer acceptance](/Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/runtime.py:53997),
[MLX path](/Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/runtime.py:54552),
[existing job identity](/Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/job_timing.py:130),
[direct OPEN](/Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/runtime.py:42881).

The native observer also needs a cadence investigation: declared one-second sampling
and observed producer gaps leave all five inspected traces without sustained
half-return evidence. Measure production intervals, clock meaning, scheduling and
queue behavior first. Then correct the producer or its declared cadence according
to the intended measurement; do not merely relax coverage checks to obtain complete
labels. Existing native event sequence/session identities should join a bounded
capture-admission ledger if we later ask which transitions were omitted. Reuse the
[input-lineage plan](../proposals/2026-09-07-input-lineage-and-regulator-trace.md)
for subsequent input/controller attribution rather than creating competing clocks.

Source: [sample cadence](/Users/mikepurvis/other/afterimages-live-v1/minime/minime/src/transition_afterimage/mod.rs:33),
[coverage and contiguity](/Users/mikepurvis/other/afterimages-live-v1/minime/minime/src/transition_afterimage/metrics.rs:55).

Across both runtimes, acceptance tests should exercise eligible/no-candidate/disabled
paths, insufficient budget, retries/fallback, rejected responses, missing records and
restart boundaries. Observational additions should reproduce identical prompts and
actions in isolated replay; exact capture needs bounded retention and explicit loss
counters. Any cue-policy change needs its own reviewed example and rollback through
the existing cue switch. No policy change or deployment is authorized by this note.

## Recommended next slice

Recover one of the five omitted Astrid selections as the first trace report, then
follow the first naturally occurring accepted exposure with adequate evidence.
Choose a fixed observation window before reading its outcomes; retain every eligible
opportunity in that window. If no accepted exposure occurs, finish with that scoped
delivery result and its missing explanation. Once exposure is traceable, read an
ordinary continuation and a deliberate return together. This advances a substantive
question while the existing S-003 input/fill inquiry remains preserved.

## Board updates pending at the original assessment

The authenticated board tab was present, but the browser changed during attempted
selection and subsequent UI reads were slow. No board writes were attempted. Publish
this assessment as a research question/test card, with the title “Follow an Afterimage
from physical trace to later use,” and a session log “Assess Afterimages research
readiness.” Attach this note and the snapshot. Initial observational check complete;
the trace report and runtime instrumentation remain proposed work. Preserve the
existing reading-feedback completion and S-003 cards.

Resolved in the subsequent September 7 build: the named card was saved and verified
done, with this assessment, the first account, S-004 and runtime proposal linked.
The session log is “Build and read the first Afterimage account.” See the
[publication receipt](../board/afterimage-trace.json). The earlier pending paragraph
is retained as the assessment's historical state; runtime implementation remains
proposed and accepted-exposure research remains open.
