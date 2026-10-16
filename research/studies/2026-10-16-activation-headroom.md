# Making room for the isolated activation comparison

October 16, 2026. Selected by Mike after the second incomplete comparison.
Constraint confirmed: use this Mac and leave the live systems untouched.
Status: implementation and prospective qualification; no new writing collected.

## Question and current evidence

Can the isolated apparatus bound its unused allocator retention and complete
the missing conditions with one admitted model load, while preserving numerical
and text-context isolation between conditions?

The previous two attempts remain stopped. Both completed the trace condition;
the first then received a Rust admission refusal, and the second exhausted a
resource-preparation window without dispatching another condition. All six trace
journals and retained activations reproduced exactly. The controls remain absent.
This work does not resume either attempt or reinterpret missing writing as a
null result.

A new read-only host inventory found warning pressure before any experiment
worker was launched. The major process footprints belonged to the running
research systems and model services. They are outside this task's mutation
scope. The inactive desktop reader was not a comparable memory consumer.
Snapshots are private under `research/outputs/activation-headroom-20261016/`;
the [resource interpretation](../../desktop/ReservoirScope/validation/2026-10-16-activation-headroom/RESOURCE-INTERPRETATION.md)
explains why reported free percentage is not unused RAM.

No system-wide purge, process-name kill, service unload, live-model reconfiguration,
or pressure-threshold relaxation is selected. Removing memory that our process
does not own would not be an apparatus fix. There is no evidence of a lingering
activation worker or a persistent duplicate full model in its loading path.

## Changes to test

Set the dedicated worker's MLX free-buffer cache limit to 64 MiB before loading.
Clear unused buffers periodically during decoding, synchronize finished work,
and release request-local references at cleanup. Retain phase-specific active,
cached and peak-active MLX byte counters. These counters cover MLX's allocator;
the cache setting is neither a hard process-memory ceiling nor a reservation of
host RAM. No prefill chunking, vocabulary-head shortcut, changed precision,
steering arithmetic or sampling policy is selected.

Add a separate serial cohort CLI with one model initialization and three fresh
condition records. Only immutable weights and qualified calibration are shared.
Every condition starts with fresh numerical state and prose history; every model
operation uses a fresh KV cache, cleared steering and its declared seed. Bind each
session explicitly to the shared initialization evidence. Export and offline
verification must preserve that provenance. Individual cohort sessions cannot
silently restart an interrupted cohort.

Admission before the sole model load remains pressure exactly 1 and reported
free percentage at least 25. A prospective preparation window allows at most
600 seconds, polling with a ten-second delay and requiring three consecutive
healthy observations. The final admission is checked again immediately before
load. A refused load is never retried within the attempt.

The resident cohort is bounded to 900 seconds including initialization, with
each request capped by 180 seconds or the remaining cohort time. Before each
request and condition boundary, critical or unknown pressure stops the cohort.
Normal or warning pressure can continue the already admitted worker; this guard
does not permit a second model load under warning pressure. All failures and
completed earlier material remain retained.

## Qualification and frozen writing design

Synthetic checks cover preparation expiry, an admission race, timeouts, failure
after a completed condition, one initialization, state/history isolation,
borrowed-initialization evidence, cancellation and paused recovery. Qualify the
changed worker before new writing: retain the existing logit/cache/capture/norm
checks and add the cache-policy receipts and exact unsteered–steered–unsteered
order-isolation comparisons. Changing worker source changes its manifest, so
calibration must be freshly qualified and bound to the new identity. Preserve
the earlier calibration and qualification unchanged.

The qualification launcher gets one bounded preparation and one model execution,
with a 900-second total child timeout. A failed or inadmissible qualification
holds subsequent writing. Existing inference packages and previous attempts
remain frozen; the new CLI binary and sources get their own recorded identities.

If qualification passes, the separate
[cohort protocol](../../shared/reservoir-scope/activation-cohort-20261016.json)
runs **no steering, recurrent state, then decaying trace**. Missing conditions
come first; this changed order is declared before outputs are available. All
twelve observations, seed, numerical spacing, invitation, memory policy,
1% intervention norm and 1,024-token ceiling remain fixed. There are six journal
opportunities per condition. The new worker's manifest/calibration are shared
within this comparison; equality with an earlier worker is measured, not assumed.

Read complete sequences with allocation concealed from a fresh reader, freeze
that account, then disclose prompts, arm identity and mechanics separately.
First journals provide the matched text-context comparison. Later trajectories
also include the effect of preceding prose. There is no predicted direction of
literary quality, semantic benefit or recurrent advantage.

## Finish line

The intended result is a qualified bounded-memory worker and serial cohort path,
plus a complete three-condition comparison if current host admission allows it.
An exhausted preparation or first execution failure ends the new attempt without
retry or extension. If host pressure remains unsuitable despite lower own-process
cost, report that remaining boundary rather than claiming headroom is solved.
Title and previous-prose contrasts remain separate later inquiries.
