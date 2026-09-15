# Closing the provider-input observation gap

**Later September 8 update:** Mike authorized the
[verified live rollout](2026-09-08-provider-observer-live.md). The account below
preserves the completed source-qualification stage and its original boundaries;
the linked rollout supplies the later activation and natural-window evidence.

Mike authorized implementation of the next S-006 fix on September 8. The
[natural-outcome follow-up](2026-09-07-flywheel-natural-outcome.md) established a
deployed marker-preservation repair, but ordinary generation records were already
cleaned. Its raw opportunity denominator remained unavailable. The approved
[observation addendum](../proposals/2026-09-07-flywheel-evidence-and-throughput.md#natural-outcome-observation-addendum)
is now implemented in an isolated owning Astrid checkout:
`/Users/mikepurvis/other/astrid-provider-observation-20260908/astrid`, branch
`codex/provider-attempt-observation`, signed commit
`3f164466efb064e5206970188b55f705e5371ca2`, based on exact source
`2bfaad02e4e5b1e455a32aa2ed82353404ab4b33`.

The canonical sibling and live services were not edited, restarted or contacted
for generation. No research material or message was sent to either being.
Observation defaults off; source readiness and live availability remain separate.

## The change

A unique identity begins immediately before each provider dispatch. An immutable
dispatch receipt precedes the request; the outcome records fully read HTTP-body
and parsed-content hashes, cleanup and provider-output hashes, bounded marker
counts and receipts, observed versus unavailable input, and provider rejection
or failure. Each physical Ollama fallback call remains visible. Graceful
cancellation records an abandoned outcome; abrupt process loss may leave a
dispatch without a terminal receipt, which remains unknown.

The protected Ollama incomplete-response branch previously returned before the
normal cleanup hook. It is covered explicitly. Missing messages and malformed
responses do not acquire a zero-marker count. Marker-bearing raw input is retained
exactly in a private hash-addressed artifact when its limits permit; duplicates
share the artifact while retaining distinct attempt identities.

Dialogue receipts and legacy generation records share generation identity and
logical attempt index with every underlying provider call, including failed ones.
The existing `response_text` values retain their semantics and now carry explicit
stage labels. A separate decision receipt records accepted-output hash or
non-acceptance. No new action executor, acceptance rule or fallback policy is added.
Affected transport error logs no longer expose response excerpts.

The observer uses the existing startup-verified manifest/executable binding,
recorded before and after each attempt. It never substitutes current Git HEAD
or an unverified mutable manifest for activation evidence. Legacy launches
without that binding remain `activation_unknown`. Configured and actually reported
model identities remain distinct; a missing identity stays unknown.

## Privacy, cost and failure limits

The owning [implementation contract](/Users/mikepurvis/other/astrid-provider-observation-20260908/astrid/docs/provider-attempt-observation.md)
specifies opt-in configuration, rollback, exact stage/hash scopes and private
retention. Raw artifacts are limited to 256 KiB each, 64 MiB of raw data, 256 MiB
total spool bytes and 50,000 artifact files. Files are 0600 in 0700 directories.
An exclusive writer lock, bounded initial inventory, exact deduplication checks
and atomic publication protect the retained evidence. Nothing is automatically
deleted. Archiving and a new private spool belong to the owning workflow.

When raw evidence is omitted, its reason is explicit. Total-store failure is
visible through ordinary warnings and available generation links, rather than
through an imagined successful write into the failed store. A completed file is
a write receipt, not an unlimited durability guarantee. Synchronous recording
adds disk latency; this cost must accompany any usefulness claim.

## Qualification

Qualification uses frozen synthetic HTTP responses and private workspaces.
The exact unchanged source has only a test-worker addition. Its actual provider
results are compared with observer-disabled, enabled and recording-failure arms
of the new source. Each worker is a fresh process with explicit loopback mock
routes; a filesystem/network sandbox blocks live workspace writes and live
service ports. No model generation is induced.

The final library run passes 2,232 tests, with the default-path and OS-lifecycle
checks each passing separately (2,234 functional library checks total). The
public-interface contract passes its two positive cases and expected private-module
compile rejection. Strict Clippy across library, binaries and tests, and the domain
boundary audit pass. The existing 1 ms instrumentation timing test fails on the
initial changed-source run (3.043614 ms p95) and unchanged baseline (1.971239 ms);
it is excluded from the final functional run, with its threshold unchanged.
Those timings do not estimate an observer effect.

All 38 provider scenarios agree across four arms in output, dialogue acceptance
and fallback count. Each arm makes 54 physical calls. The enabled arm retains
146 dispatch/outcome/decision envelopes and 17 raw artifact files, with 21 accepted
and 17 non-accepted dialogue cases. An independent offline probe checks identity,
marker byte spans, raw/cleanup/normalized hashes, permissions and every join.
These are deliberately selected synthetic cases, not estimated natural rates.

The enabled fixture spools contain 245,395 bytes. Across 34 non-timeout,
non-manifest-binding pairs, median enabled-minus-disabled worker duration is
41.0718955 ms, maximum 171.066416 ms. The runs include heterogeneous inputs and
local qualification workload, not a controlled production benchmark. Recording
cost is explicit; no throughput improvement is claimed from this observer.

The signed commit contains exactly 11 reviewed files, and the exported patch
applies to the exact baseline and reverses byte-for-byte. Final evidence is in the
[completion receipt](../research/outputs/2026-09-08-provider-observation/completion.json),
[independent verification](../research/outputs/2026-09-08-provider-observation/final-independent.json),
[source manifest](../research/outputs/2026-09-08-provider-observation/source-manifest.json),
and [review patch](../proposals/patches/2026-09-08-provider-attempt-observation.patch).
The [owning review package](/Users/mikepurvis/other/astrid-provider-observation-20260908/README.md)
retains executable fixtures, baseline source, logs and reproduction guidance.
Development results remain separate from final ones. Nothing was published or
activated; the canonical live source remains outside this change.

## Research consequence and next boundary

This is a human-authorized measurement improvement motivated by a journal-led
repair study. It is not another authored journal request, an unattended flywheel
round or evidence that the beings experienced an improvement. The earlier case
and its correction history remain intact.

After a separately verified rollout enables the observer, freeze a fresh natural
window before examining its outcomes. Include all dispatches and unknowns. Join
the exact release and retained input to the focal repair's old/new property;
marker-bearing inputs are not automatically eligible examples. Operational
benefit and subsequent uncoached experience still require their own evidence.

The current baseline already contains related steward throughput work: anchored
indexed status reads and machine-verified headless completion receipts are
documented in its changelog. This implementation does not duplicate or benchmark
those changes. Typed episode rendering, phase measurements and the other broader
flywheel proposals retain their separate scope.

The implementation card and session log are saved and read back on Hold Shelf;
[board receipt](../board/provider-attempt-observation.json).
