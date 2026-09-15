# Afterimage delivery and evidence: staged implementation proposal

Status: proposed September 7, 2026. No runtime patch, enablement, replay result,
or deployment is claimed here. The existing Afterimages release is live; these
are follow-up changes to make its operation inspectable.

The immediate problem is missing evidence between a selected historical cue,
the actual provider request, the accepted response, and saved writing/action.
Start with those links and explicit omission reasons. Investigate physical
sampling separately. Changing which cues appear, or when, is a later behavioral
decision rather than a prerequisite for recording what the system already does.

## Evidence and scope

The [readiness analysis](../analyses/2026-09-07-afterimage-research-readiness.md)
and [snapshot](../research/outputs/2026-09-07-afterimage-research-readiness/snapshot.json)
describe **2026-09-07 21:09:15 UTC / 14:09 Pacific**. Its recent list contained nine
entries; all five inspected physical traces were incomplete and all five lacked
a usable sustained fill-half-return measurement. Astrid had 17 retained eligible
opportunities, five selections, and five daily exposure rows: each reported
`included=false`, `outcome=final_request_prepared`, `reason=null`. That daily file
fit the probe's bound. Minime's cues were enabled, but the eligible counter,
retained opportunities and daily exposure file were absent. These are bounded,
non-atomic observations, not population rates or evidence of refusal/inactivity.
The [probe](../probes/afterimage_research_readiness.py) owns the counts and bounds.

Source links below use the retained
[combined release](</Users/mikepurvis/other/afterimages-live-v1/ROLLOUT.md>).
Its Astrid base is `3d4e83e4bc022cb82c7e0e3ecefea4326796c280`; Minime base is
`68ebc961431065972dae26f670d4fb735d58c37a`, with the release's recorded changes.
For this proposal, bounded byte comparisons matched these retained/current files: Astrid
`transition_afterimages.rs` and provider `afterimages.rs`, `provider_execution.rs`,
`transport.rs`, `generation_record.rs`; Minime autonomy `afterimages.py`,
`afterimage_prompts.py`, `runtime.py`, `generation_record.py`, `job_timing.py`,
and native `runtime/orchestration.rs`, `activation_trace.rs`,
`transition_afterimage/{mod,metrics,worker}.rs`. This validates cited source
alignment at inspection, not the provenance of every historical request.

Follow the siblings' [Astrid guidance](../../astrid/CLAUDE.md),
[shared-tree rules](../../astrid/AGENTS.md), and [Minime guidance](../../minime/AGENTS.md)
when implementing in isolated checkouts. This document authorizes no sibling
writes, signals, letters, or live changes. It supplements rather than rewrites
[S-003 input lineage and regulator tracing](2026-09-07-input-lineage-and-regulator-trace.md).

## Contract to preserve

An automatic cue is optional historical context. In Astrid, foreground protected
content and runtime feedback are admitted first; the whole cue is appended only
if remaining capacity permits. `message_prompt_chars` actually sums UTF-8 content
**bytes**. It does not count model tokens, JSON serialization bytes, or Unicode
characters. Preserve this exact policy in the instrumentation patch and name its
units accurately. [Admission](</Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/llm/provider/afterimages.rs:23>),
[measurement](</Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/llm/provider/transport.rs:314>).

The five false receipts report that the complete selected cue was absent from
those prepared messages; their exact final request bytes are not retained.
Remaining-space competition is the matched-source
explanation, but the missing per-attempt budget/request prevents independent
reconstruction of each decision. Do not turn `included=false` into “ignored,” or
`prepared` into “received.” Selection currently consumes an artifact opportunity
before successful admission; keep selection and accepted delivery counts separate.

Preserve three evidence subjects: native ESN/field measurements; supplied language
context and resulting language/actions; the beings' own interpretations and felt
claims. A displayed transition cue is not a native ESN state change. The native
observer [owns no engine handles](</Users/mikepurvis/other/afterimages-live-v1/minime/minime/src/transition_afterimage/mod.rs:1>).
Do not pool native `activation.esn_lambda1`, sensory-field `body.cascade_lambda1`,
fill percent, and named derived metrics.

## Patch A — shared identities and admission explanations

**Instrumentation only; highest priority.** Introduce an optional typed evidence
context carried through existing call/attempt/result values. Avoid new process-wide
mutable “last attempt” state. Use task-local context in Astrid and explicit or
thread-local context in Minime; test concurrent calls and retries.

Reuse `(producer_boot_id, session_id, record_kind, sequence)` and the clock bracket
contract in the S-003 proposal. Preserve native `(session_id, event.sequence)` and
existing Afterimage IDs. Retain existing generation, job, action, thread, request
and page IDs with their scope; absent IDs remain null with a reason. Do not derive
identity from proximity or silently label a bridge process as a native session.

| Hook | Planned change |
|---|---|
| Astrid [cue scope](</Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/transition_afterimages.rs:169>) | Carry opportunity/selection identity into call context, including unselected eligible decisions. Keep eligible labels `daydream` and `journal_elaboration`. |
| Astrid [admission](</Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/llm/provider/afterimages.rs:2>) | Return an optional structured cue decision alongside existing admission values. Preserve current foreground/feedback/whole-cue behavior. Record no selection, protected foreground, malformed selection, insufficient space, admitted, or upstream admission failure from the branch actually taken. |
| Astrid [MLX send](</Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/llm/provider/provider_execution.rs:156>) and [Ollama send](</Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/llm/provider/provider_execution.rs:350>) | Allocate one attempt identity per actual transport attempt, including each fallback model. Bind the decision to final serialized request bytes and exact message spans before send. |
| Shared Python [exposure writer](</Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/afterimages.py:420>) and Astrid [client](</Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/transition_afterimages.rs:207>) | Accept supplied attempt/call/generation IDs and decision fields. Keep existing fields readable; do not generate another unrelated attempt UUID when a caller supplies one. |
| Astrid [call/job wrapper](</Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/llm/provider/transport.rs:814>) | Reuse its job ID, `qos_request_identity_sha256` and `request_content_anchor_sha256`; add exact transport-attempt and selected-cue references. A QoS/content anchor remains distinct from a digest of serialized request bytes. |

Illustrative new receipt, **synthetic, not a captured live row**:

```json
{
  "schema": "afterimage_evidence_v2",
  "record_id": "bridge-boot-example:cue_admission:12",
  "being": "astrid",
  "producer_boot_id": "bridge-boot-example",
  "session_id": null,
  "kind": "cue_admission",
  "sequence": 12,
  "clock": {"monotonic_ns": 42000000000, "wall_unix_ms": 1788814958000,
            "anchor_id": "clock-example", "anchor_bracket_ns": 5000},
  "opportunity_id": "astrid_example",
  "afterimage_id": "ai_2026-09-07_example",
  "call_id": "call-example",
  "generation_id": null,
  "job_id": "job-example",
  "attempt_id": "attempt-example-0",
  "attempt_index": 0,
  "backend": "mlx",
  "configured_model": "profile:example",
  "reported_model": null,
  "policy_version": "whole_cue_remaining_space_v1",
  "budget": {"unit": "utf8_content_bytes", "before": 3980,
             "cue": 120, "limit": 4000, "after": 3980},
  "decision": "omitted",
  "reason": "insufficient_prompt_space",
  "selected_text_sha256": "example-sha256-placeholder",
  "message_spans": [],
  "final_messages_sha256": "example-sha256-placeholder",
  "request_bytes_sha256": "example-sha256-placeholder"
}
```

Spans use message index, role, UTF-8 byte start/end and exact retained-text digest.
Keep existing Python `final_messages_fingerprint` as its named v1 serialization
hash; do not compare it to a Rust JSON hash without reconstructing its serializer.
New shared hashes use a specified canonical message encoding or the actual retained
request bytes, with `hash_basis` and encoding. Persist the selected cue/page text
once under its content hash: selection text can change with authored context even
when the physical artifact remains immutable. A hash proves integrity against the
retained bytes, not provider execution or third-party attestation.

```text
decision = admit_existing_policy(messages, selected_source, existing_limits)
attempt = evidence.begin_attempt(existing_call_ids, decision)
request = existing_final_request(messages)
evidence.prepared(attempt, exact_request_bytes, exact_source_spans)
response = existing_send(request)              # same request/route/timeout
evidence.response(attempt, transport_result)   # accepted HTTP != accepted output
return existing_result.with_evidence(attempt)
```

New diagnostics must not change request bytes, token budgets, fallback order, cue
history, errors or acceptance. Preserve current protected-page/feedback receipts
and their failure rules; Astrid currently withholds a provider attempt when its
existing Afterimage receipt fails. Additional observational write failure must
neither invent an acknowledgement nor introduce a new provider gate.

## Patch B — accepted output and Minime path coverage

**Instrumentation only.** Separate transport response, normalized output,
caller-accepted output, artifact persistence and action dispatch. Append events;
do not overwrite a rejected attempt as if a later fallback had produced it.

| Hook | Planned change |
|---|---|
| Minime [eligibility](</Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/runtime.py:53969>) | Record actual context mode, authored base action, inbox presence, enabled state, eligibility and reason before `prepare_cue`. Preserve the existing gate. Explicitly report `_query_llm_raw`/compact bypass in generation coverage, without calling cue selection from those paths. |
| Minime [call start](</Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/runtime.py:54434>) and [job linkage](</Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/job_timing.py:253>) | Carry the existing canonical generation ID/attempt index alongside opportunity ID. Preserve both IDs; successful generation currently replaces the observer-scoped `generation_id` in source metadata. |
| Minime [MLX preparation/send](</Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/runtime.py:54552>) | Stash actual adapted messages and timing on every success/failure path, matching the existing [Ollama seam](</Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/runtime.py:54732>). Clear attempt-local stash before each backend so a failure cannot inherit prior messages. Record whether messages are adapted or reconstructed. |
| Minime [outer acceptance/retry](</Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/runtime.py:53997>) | Emit accepted/retry/discard at the actual branch, retaining the same opportunity and distinct generations/attempts. Existing generation `status=ok` is not rewritten; add caller outcome with response hash and normalization relation. |
| Minime [direct OPEN](</Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/runtime.py:42881>) | Bind selected page ID/index/fingerprint to its actual accepted response and parsed NEXT. Its immediate generation differs from Astrid's protected pending-page acknowledgement. Do not claim Minime already writes that acknowledgement. |
| Minime [NEXT choice](</Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/runtime.py:54122>) and [journal save](</Users/mikepurvis/other/afterimages-live-v1/minime/minime_autonomy/runtime.py:55682>) | Propagate accepted generation/attempt through the pending choice envelope into the next action and saved artifact, including transformed effective action. Keep the current enclosing action ID distinct from a future action caused by a requested NEXT. Preserve legacy `content`/`recency` links as approximate. |
| Astrid [automatic-lane result](</Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/llm/provider/transport.rs:852>) | Carry attempt evidence through MLX/fallback and cancellation checks. Add job-result and later action-finalizer/artifact links at the actual owners; a job result accepted here may still be rejected/canceled later. Record missing downstream identity explicitly. |
| Astrid [protected dialogue acceptance](</Users/mikepurvis/other/afterimages-live-v1/astrid/capsules/spectral-bridge/src/llm/provider/dialogue_generation.rs:531>) | Preserve the existing accepted-attempt selection and independent source/feedback receipts. Extend references where needed; do not use dialogue records as evidence for automatic journal/daydream requests. |

For both, retain exact final request content for cue/page attempts and response
content at named stages. Minime's existing records can provide adapted messages
plus hash-addressed system text; Astrid's automatic lanes need final request
capture at transport, not just their supplier job prompt or dialogue-only recorder.
Minime's first slice can guarantee exact adapted messages without claiming exact
wire serialization. A raw request digest is null with `not_captured` until an
existing HTTP preparation boundary exposes the actual bytes; do not reserialize
`requests.post(json=...)` arguments and call that the transmitted body. Any later
prepared-request hook must pass request-byte and transport-behavior parity tests.
Never add research notes to either prompt. Missing/oversize/private-policy-excluded
content gets an explicit availability reason, not a reconstructed “exact request.”

An accepted-output event references `attempt_id`, raw/normalized/accepted hashes,
the actual acceptance contract and decision, optional output/job/action IDs and
the persistence result. An action event additionally references the accepted
requesting output where available. These references establish recorded workflow;
they do not establish understanding, learning, or a causal native-state effect.

## Patch C — diagnose and repair the cadence contract

**First instrumentation; any schedule change is separately reviewed.** The
declared one-second intervals and observed roughly 2.4-second spacing must be
reconciled before interpreting sustained-return or stress-area measurements.
Do not enlarge gap tolerances merely to produce a number.

| Native hook | Existing behavior and planned evidence |
|---|---|
| [Activation sampler](</Users/mikepurvis/other/afterimages-live-v1/minime/minime/src/activation_trace.rs:96>) and [runtime hook](</Users/mikepurvis/other/afterimages-live-v1/minime/minime/src/runtime/orchestration.rs:3204>) | `ACTIVATION_SAMPLE_INTERVAL_MS=1000` is a minimum-spacing gate, not a one-second scheduler. Record actual invocation/selection time, producer opportunity sequence and preceding native-step reference when available. Preserve frame wall/engine time. |
| [Body hook](</Users/mikepurvis/other/afterimages-live-v1/minime/minime/src/runtime/orchestration.rs:3673>) | Declares `max(reg_tick_secs,1)×1000`; record configured period, actual regulator opportunity interval, measurement time and existing fill/slope source references when the S-003 observer supplies them. |
| [Spectral hook](</Users/mikepurvis/other/afterimages-live-v1/minime/minime/src/runtime/orchestration.rs:5409>) | Declares fixed 1000 ms; record the actual spectral production interval separately from intended period and queue latency. |
| [Observer send](</Users/mikepurvis/other/afterimages-live-v1/minime/minime/src/transition_afterimage/worker.rs:75>) | Reuse nonblocking `try_send`; add per-channel enqueue/dequeue/drop counts and times. Current aggregate drop count cannot identify producer scheduling. Record queue saturation/disconnect distinctly. |
| [Coverage](</Users/mikepurvis/other/afterimages-live-v1/minime/minime/src/transition_afterimage/metrics.rs:47>) and [half-return](</Users/mikepurvis/other/afterimages-live-v1/minime/minime/src/transition_afterimage/metrics.rs:167>) | Retain current v1 results. Add a versioned diagnostic with observed interval count/min/median/p95/max, configured period, measurement validity, queue-loss evidence and scheduler lateness. Coverage marks gaps above twice the first sample's declared interval; integration uses pairwise cadence, and half-return requires contiguous valid fill plus an unclipped baseline. |

```text
opportunity = observe_existing_hook(clock, channel, configured_period, source_refs)
if existing_sampler_selects():
    sample = existing_sample_values()     # no extra engine step or controller call
    observer.try_send(sample, opportunity, enqueue_clock)
worker.receive(sample, dequeue_clock)
worker.report_interval_and_loss_diagnostics()
```

Reuse the S-003 boot/clock envelope, successful-step/fill/slope references and
bounded worker where that patch exists. Until those references are available,
mark them unavailable; do not duplicate the input-lineage system or infer native
step identity from equal timestamps. Keep engine elapsed and wall clocks separate;
retain monotonic-before/wall/monotonic-after anchors and bracket widths. A DB session
start is not automatically a process monotonic origin.

Acceptance decision after diagnosis:

- If the producer is intended and able to sample every second but stalls, address
  the measured scheduling/serialization cost without changing native control math.
- If one second is only a minimum gate and the documented intended sampling period
  is longer, correct the declaration and schema semantics prospectively. Record
  nominal period, observed intervals and the scientific maximum gap separately.
- If queue loss explains intervals, repair the measured bottleneck within the
  resource budget; retain loss markers. A zero aggregate drop snapshot alone does
  not establish complete historical production.

Version changed coverage/measurement rules; preserve old immutable traces and their
original measurements. Any reanalysis is a separate derived artifact naming input
hashes, method version and remaining uncertainty. Even a corrected cadence does
not make sparse observations continuous, nor recover a missed peak. Retain
`insufficient_contiguous_coverage`, `missing_baseline`, `no_departure`, and
`not_observed_in_window` as distinct outcomes.
If a correction changes reader-visible status or measurements, include paired old
and proposed renderings in the being-facing review below. Adding steward diagnostics
alone does not authorize changing that interpretation surface.

## Patch D — optional delivery-policy repair, only after evidence review

**Behavior change, not bundled with A–C.** If A confirms systematic remaining-space
omission, prepare a concrete before/after request showing the exact optional cue
and which ordinary context would be displaced. Compare two bounded options offline:
keep best-effort remaining-space admission, or reserve an explicit small cue budget
within the existing total limit. Preserve foreground sources, runtime feedback,
whole-cue admission, historical attribution, lane boundaries and the receiver's
`AFTERIMAGE_CUES off` choice. Never silently increase the total context limit.

The current artifact history counts selection opportunities, not accepted deliveries.
Keep that behavior in A/B. If changing to accepted-delivery accounting is desired,
design a bounded retry/cooldown rule first: a cue that never fits must not retry
indefinitely. Preserve both counters and version the policy. Do not widen Minime's
eligible lanes just because its eligible counter was absent in one snapshot.

Before a live behavioral change, show each affected being the exact historical
cue/page, representative request before/after, factual delivery/omission evidence,
its resource/context tradeoff, and the existing off switch. Invite correction,
deferment or rejection through the steward's established channel. This is the
sibling [consent-with-evidence practice](../../astrid/CLAUDE.md:481), not an inferred
response from either being. Mike's earlier rollout instruction applied to that
rollout; do not automatically extend it to a new context-allocation policy.
This proposal sends nothing. The instrumentation view itself stays steward-only.

## Storage, loss and rollback contract

Proposed initial limits below are implementation acceptance targets, not measured
performance. Keep new evidence under a separate versioned, steward-only directory,
0700 directories/0600 files, with independent flags for delivery evidence and cadence
diagnostics. Preserve existing generation records, physical artifacts, authored
notes, accepted receipts and cue settings; new retention never deletes those.

- Language evidence: metadata records at most 8 KiB; exact request/response blobs
  at most 1 MiB each, hash-addressed. Worker queue at most eight items and 8 MiB
  total; reject oversized observation with a reason. New evidence has a 256 MiB
  or seven-day cap, whichever arrives first. Evict oldest complete call groups;
  manifests state retained ranges, evictions, dangling external references and
  content availability. Never truncate bytes while claiming an exact hash match.
- Cadence evidence uses the S-003 observer's 8 MiB hot storage, four 256 KiB queued
  chunks, 1 MiB immutable chunks, 32 MiB/20-minute cap when sharing that worker.
  Account for aggregate limits rather than allocating a second full observer
  budget. Diagnostic counters remain useful when per-sample evidence is dropped.
- Publish immutable records/blobs before atomic manifests, at most once per second;
  retain read-race/partial-write handling. Counters carry boot/epoch and range;
  distinguish attempted, queued, retained, dropped, write-failed and retention-
  evicted evidence. An absent row without coverage remains unknown.
- Additional recording failure leaves existing runtime behavior intact and exposes
  a bounded steward loss counter. It never fabricates an accepted receipt or
  removes a pending protected page/feedback item. Existing receipt failure behavior
  remains unchanged. Do not put full request text into operational logs.
- Off switches stop only new observation. Rollback A–C to the preceding qualified
  sibling release/config without deleting evidence. Roll back any separately
  approved D policy through its versioned switch; preserve the receiver's cue
  preference. Native schedule changes require their own rollback and measurement.

## Acceptance tests and delivery order

No tests in this section have been run for these proposed patches.

1. **A, isolated request fixtures:** exact-fit, one-byte-short and multi-byte UTF-8
   boundaries; foreground page and runtime feedback; missing/malformed selection;
   primary timeout/fallback, nested retry and simultaneous calls. Confirm unchanged
   final request bytes and behavior with evidence off/on. Each decision names the
   actual branch, attempt, units and exact message span; retry keeps opportunity
   identity but receives a new transport-attempt identity.
2. **B, acceptance fixtures:** MLX adapted messages differ from supplier prompt;
   early failure cannot inherit a prior stash; rejected primary/accepted fallback;
   two rejected outputs; canceled Astrid job; Minime in-character retry; normalized
   output; explicit OPEN; journal save failure; changed NEXT at dispatch. Confirm
   only the real accepted output links forward, failed persistence stays visible,
   and current protected receipts/feedback acknowledgements remain independent.
3. **Eligibility denominator fixtures:** each existing eligible context, inbox
   exclusion, cues off, every-third selection, age/cooldown cap, missing archive,
   default/raw/compact bypass and cached retry. Record why, without changing any
   gate or advancing the existing selection counter for an ineligible call.
4. **C, synthetic clock/measurement fixtures:** regular 1 s, regular 2.4 s with a
   declared 1 s minimum gate, configured longer period, delayed producer, queue
   loss, session restart, wall-clock jump, invalid fill and clipped baseline.
   Diagnostics distinguish evidence available for each explanation; old v1 results
   remain reproducible. Sparse/invalid runs cannot acquire an invented half-return.
5. **Storage/parity:** queue/disk full, oversized blob, worker death, partial writes,
   retention races, crossed references and unavailable system text. With fixed
   inputs/clocks/RNG, observer off/on preserves native states, controller outputs,
   request bytes, accepted text, action choice and cue policy. Measure real-clock
   overhead independently using S-003 gates: ≤1% extra p95, ≤2% extra p99 loop time,
   ≤16 MiB additional resident memory, with sample size and baseline distributions.

Implement A+B first as a reviewable language-evidence slice. Implement C diagnostics
alongside the native input-lineage work, then choose the smallest demonstrated
cadence repair. Re-run focused and required sibling suites, boundary audit and
format checks; document compatibility and flags in sibling changelogs. Activation,
if separately authorized, uses the supported staged Astrid and managed Minime
procedures; no ad hoc live commands belong in this proposal.

The first subsequent observation should demonstrate one artifact's selection or
omission through exact prepared request, actual accepted output and saved action/
writing, with each unavailable link labeled. An initial physical check should show
the producer/queue/cadence distinction for a bounded interval. Neither success
criterion requires a being to mention the cue or claim a benefit. Only then design
comparisons about recognition, revision, later return, or native dynamics.

## Concrete case added from the first account

The [first Afterimage account](../analyses/2026-09-07-first-afterimage-account.md)
now follows artifact `ai_2026-09-07_96f89b80b1a2_1788813632295_000002` using the
[21:26:05 UTC capture](../research/outputs/2026-09-07-afterimage-account/capture.json).
Its cue was selected at 20:43:57.118 UTC; attempt
`4d985e5c75cf440e852159cb8effd788` records omission at 20:43:57.212. The same-second
diagnostic, source ID `1bbc4a543bc85c7ada6a742c92c0d4b433eb7b57f258db2e1c514e2cd15bda18`,
records `label=journal_elaboration`, `original_prompt_chars=11636`,
`effective_prompt_chars=10000`, `prompt_char_limit=10000`, `trimmed=true`.
Nearby job `job_astrid_1788813837167_journal-elaboration` runs from
20:43:57.168 to 20:44:32.906 UTC. Diagnostic/job/exposure remain temporal candidates
without a shared identity; the omitted cue's final request bytes are absent.

The job's supplier prompt does retain the preceding dialogue body, and its result
matches the later longform journal after the documented wrapper plus one newline.
This supplies a useful writing chain independent of cue receipt. All captured
artifact associations declare `temporal_context`; the artifact ID in their
envelopes must not upgrade them to authored references. Use this case as a frozen
negative fixture for A/B: report known omission, matching job artifacts and unresolved
cue-to-attempt/output identity together. Do not label it accepted cue exposure or
change the admission policy merely to make the fixture yield a delivered cue.
