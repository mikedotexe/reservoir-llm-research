# Make flywheel outcomes easier to trace and cheaper to verify

September 7, 2026. Research-side proposal, **not implemented in the flywheel**.
Motivated by [S-006](../research/studies/S-006-journal-to-change.md) and its
[source account](../analyses/2026-09-07-flywheel-signal.md). Mike explicitly
welcomes streamlining opportunities discovered during this inquiry.

## The observed friction

The existing system retains unusually useful evidence: report/source hashes,
claim dispositions, exact quotes, run IDs, tests and boundaries. But one episode
is distributed across commits, packet files, shared ledgers and runtime receipts.
Archival commits arrive later; source changes and test-only additions share the
`addressed_change` category; a quote-verification flag can coexist with wrong
being attribution; and some historical commit bodies lost formatting or quoted
identifiers during shell construction.

The retained September 7 codec controller receipt spans 179.95 minutes for one
processed report. The packet attributes about 67 minutes to preprojection and
reports an earlier mistaken deadline calculation. This supports profiling and
clear phase clocks, not a claim about typical run speed or a guaranteed saving.
`scripts/steward_control/executor.py:23` begins the controller before creating
the child; lines 30–31 create it and start its clock. The wrapper separately
sets a whole-cycle watchdog in `scripts/flywheel_loop_run.sh`.

## 1. Generate the archive from one typed episode record

Add a steward-only `episode.json` to each existing round packet. Keep claim and
evidence files as authoritative children. Suggested fields:

```json
{
  "schema": "flywheel_research_episode_v1",
  "episode_id": "immutable-local-id",
  "reports": [{"id": "...", "author_being": "astrid", "source_subject": "minime:regulator", "raw_sha256": "...", "authored_spans": []}],
  "review": {"run_id": "...", "actor": "...", "model": null, "mode": "unattended_or_interactive", "selection_receipt": "..."},
  "claims": [{"id": "...", "disposition": "...", "evidence_refs": []}],
  "changes": [{"id": "...", "kind": "characterization_test", "origin": "report_requested", "paths": [], "commits": []}],
  "activation": {"status": "not_applicable", "receipt": null},
  "outcomes": [{"kind": "software_correctness", "status": "unmeasured", "evidence": null}],
  "corrections": []
}
```

Null model identity is preferable to guessing it from an actor name. Permit
many reports per change and several changes per report. Change kinds include
characterization test, bug regression plus production fix, new affordance,
observation/tooling, documentation, proposal and no change. Origins distinguish
report-requested, reviewer-discovered and human-requested work. Keep declaration,
verification and unresolved contradiction separate.

Render the commit body, short ledger entry and research index from the same
record. Write commit bodies to a file, never interpolate them into a shell.
Verify quote spans against exact report bytes, classify citations outside the
authored spans, and retain a separate source-subject field. A correction appends
a superseding record and links the original; it does not rewrite historical Git.
First implementation lives beside the packet/archival tooling and feeds
`scripts/flywheel_loop_prompt.txt`; inspect the owning branch's archival writer
before naming its exact mutation hook. No absent handoff file is recreated from
guesswork. The new record is steward-only and never enters a being's prompt.

**Acceptance:** round-trip quotes containing backticks, dollar expressions,
Unicode, newlines and `Source:` metadata; reject a body marked verified when its
quote differs; preserve the `7ad16072c9ef` authorship contradiction; represent
`c99e2117e59a` and `c34cbd9cb6bf` as corrections; deduplicate rebased archives
without collapsing distinct changes. A test-only change cannot acquire a
production/deployment/benefit status merely from a successful round. Historical
imports retain unknown fields and do not manufacture past receipts.

## 2. Measure the time spent in each phase, then checkpoint verification

First add neutral timings to existing run/verification receipts: queue read,
source/witness verification, projection, child review, focused tests, full
integrity checks, persistence and postprojection. Record wall and monotonic
durations with separate preparation, child and outer-watchdog deadlines.
Show the actual remaining child allowance to the headless agent. This directly
addresses the misbudgeting described in the codec packet without changing any
time limit or scheduling policy.

Then prototype incremental verification **offline** on frozen event/source
copies. A checkpoint must bind the verified chain head/sequence, source registry,
parser/projection schema, configuration and exact source bytes. Verify the new
suffix and dependent projections against it. A replaced prefix, truncation,
schema/configuration change, stale source or unknown identity invalidates the
checkpoint and requires a full check. File mtime alone is not an integrity key.
Do not cache an authorization grant as if it were permanent.

**Acceptance:** compare cold full verification and warm incremental verification
over identical historical snapshots; require identical canonical queues,
dispositions, counters and evidence heads. Test old-prefix tampering, reordering,
missing suffixes, truncation, schema changes, duplicate events and concurrent
append boundaries. Report total phase times and cache-hit rates, including
invalidations, on the same machine and data. Keep periodic full audits. Adopt
only if the measured saving is useful and all parity/fault checks pass. No speed
target or reduction in verification coverage is assumed in advance.

## 3. Reuse already established claim evidence without erasing new reports

The current prompt already supports same-source family batching and individual
variant terms. Build on that mechanism. Index prior grounded claims by source
hash, exact scope, claim semantics, test identity and response kind. A later
report still gets its own full authored reading and disposition; reuse a proof
only when the actual invariant/source applies. Present prior answers to the
reviewing steward so it can identify the new delta, contradiction or missing
outcome quickly. Do not merely compare raw text or collapse a felt concern into
a code invariant.

For example, the September 7 codec review explicitly finds earlier tests for
several requests while its new attribution question earns a distinct check.
The change record should say both things. An “already covered” status must
point to the original proof and its scope, not add another supposedly new fix.

**Acceptance:** same-source duplicates, new variant terms, changed sources,
different authors reading the same subject, contradictions, and a technically
resolved claim with an unresolved experience must remain distinguishable.
Begin with reviewer presentation only; queue reordering and changes to how
beings are invited to study require a separate decision.

## 4. Attach a narrow outcome question to production changes

At implementation time, record the failure property and the smallest observable
post-change endpoint. For the Unicode repair, that endpoint is exact marker
preservation on eligible inputs. A later operational trace requires a verified
activation boundary, input-level exposure and all eligible attempts, not just
successes. For a test-only change, report added coverage and leave live benefit
not applicable or unmeasured. Retain regressions and costs as possible outcomes.

Use naturally occurring records where adequate. Do not prompt the beings to
confirm an improvement or treat a reassuring subsequent journal as a verdict.
Test results, live availability, uptake and subjective benefit remain separate.

### Natural-outcome observation addendum

**September 8 status:** Mike authorized this observation fix. Its isolated owning
[implementation and qualification](../analyses/2026-09-08-provider-attempt-observation.md)
are now available for review. It defaults off and has not been deployed. The
following specification preserves the original proposal; broader flywheel
changes remain separate.

The [completed deployment follow-up](../analyses/2026-09-07-flywheel-natural-outcome.md)
exposes a concrete measurement gap. The marker repair is present in the verified
retained deployment, but the 120 saved dialogue responses are after cleanup.
Only one selected accepted-delivery artifact supplies a raw provider response.
The frozen sample contains no visible known marker; absence cannot establish
the input opportunity count. The two legacy request/attempt logs inspected here
end in April and cannot provide a September denominator.

The smallest useful owning-repository extension is an additive provider-attempt
observation, connected to the episode record above. Preserve the existing
`response_text` semantics and explicitly label its stage; do not silently rename
historical cleaned text as raw. Use one attempt identity generated before
dispatch and propagated through these verified source hooks:

| Owning source hook | Proposed observation |
| --- | --- |
| `provider/provider_execution.rs`, immediately around `normalize_provider_output_v1(&raw_text)` (retained lines 243 and 426) | Attempt ID, observed provider/model, raw-response hash, cleanup result and sanitized hash before any later rejection; record response unavailable/parse failure separately. |
| `provider/dialogue_generation.rs`, `record_dialogue_attempt` calls (400 and 453) | Carry the same attempt ID into acceptance/rejection and the existing generation record. Preserve upstream failure evidence even when the provider returns `None`. |
| `provider/generation_record.rs`, `GenerationRecordV1` and `append_generation_record` (383) | Add response-stage and input-availability fields, release identity and persistence status. Deduplicate against an existing exact provider artifact when one is available. |
| `provider/dialogue_runtime.rs`, `sanitize_model_control_markers_with_report` (484) | Reuse the existing bounded occurrence accounting and hashes; connect them to the attempt instead of relying on label/time proximity. |

These line numbers refer to the [retained release source](../research/outputs/2026-09-07-flywheel-natural/capture/manifest.json),
not an instruction to patch an uninspected future checkout. This table sketches
the change; no producer code has been implemented in this research workflow.

For every dispatched attempt, record a small outcome envelope even when no
marker occurs: response received/unavailable/invalid, marker count, omitted
receipt count, response-record stage and persistence outcome. Retain raw text
only under an explicit bounded private evidence policy, preferably only for
marker-bearing responses, reusing the existing hash-addressed private-artifact
pattern and its size limits. A truncated/omitted raw artifact must remain
`input_not_retained`, not count as an ineligible input. Keep request/response
text out of the board, ordinary logs, prompts and the compact episode sidecar.
Default to hashes/counts in routine review; expose private text only for a
specific research trace. This observation must not change acceptance or prose.

Join the envelope to the selected release's manifest/binary identity and the
journal-led episode's fixed failure property. A reviewer can then report
`no_eligible_opportunity`, `eligible_preserved`, `eligible_lost`,
`input_not_retained`, `recording_failed` or `activation_unknown`. Classification
of a focal opportunity still requires the specified old/new scanner property;
a zero marker count establishes ineligibility only for a successfully captured
input. Store all windows and unknowns, not just the first successful example.

**Acceptance:** replay frozen identical provider responses through old and new
observation paths; require identical accepted text, rejection/fallback decisions
and action results. Include bare markers, affected references, no markers,
mixed preservation/removal, UTF-8 offsets, response parse failure, provider
timeout, output rejection, persistence failure, oversize input, duplicate retry
and both provider routes. Assert exact raw-to-cleaned hash/stage identity and
one attempt ID throughout; prove existing cleaned records are never relabelled
as pre-cleanup. Measure bytes and latency on the same fixtures. A recording
failure must remain visible through the established failure channel while
leaving generation behavior unchanged. Do not infer natural frequency from
these qualification fixtures.

Roll back by disabling the additive observer; preserve all collected evidence
and keep legacy generation records readable. Show the exact producer diff,
private-retention limits and measured qualification before any owning rollout.
No message to a being, induced generation, automatic schedule or live activation
is part of this proposal. Once observation is qualified and available, freeze
a new natural window before examining its outcomes.

## Order, review and rollback

Start with the typed episode record and deterministic renderer. It directly
supports the research inquiry, reduces duplicate prose and has no being-runtime
dependency. Phase timing follows; a checkpoint prototype comes only after those
timings locate the cost. These are proposals for the owning stewardship repo,
not permission to mutate its live workspace from this research session.

Before any owning-repo implementation, show Mike the exact field/rendering
changes and measured acceptance results. Nothing needs to be shown to a being
for a steward-only index. Any future proposal that changes study selection,
prompts, information access or runtime behavior must separately describe its
being-facing effect and follow the applicable workflow.

Rollback is to stop generating/consuming the additive episode sidecar and use
the existing packet/ledger flow. Leave generated evidence and corrections
intact. Verification optimization must have a full-verification fallback;
disable the cache if parity or integrity cannot be established. No database
migration, automatic scheduling, model change, deployment or live control change
is required for this first slice.
