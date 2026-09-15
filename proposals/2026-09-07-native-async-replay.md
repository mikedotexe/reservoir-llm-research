# Preserve asynchronous native work with explicit data dependencies

September 7, 2026 (Pacific). Mike selected asynchronous replay as the next
prerequisite for implementing targeted substrate actions. This is S-002 support
work; S-005's selected reading stays unchanged. Research variants are built here;
the owning Minime repository receives the production implementation.

**Repair selection:** the corrected, identity-checked ablation passes all nine
constant-rho cases with tracked covariance alone, versus zero of nine for the
original source or a fused-pass fence alone. The final repair adds per-dispatch
rho capture and passes all 27 primary qualification cases on each of M1 Max and
M4 Pro, plus three measurement follow-ups per host. Full adaptive snapshots
agree exactly, and the pending-command bound remains two. The
[completed account](../analyses/2026-09-07-native-async-replay.md) retains the
controls, failure history and independent verification.

The first labeled ablation reused the original executable from a shared build
target. Its treatment comparisons are invalid and retained with that explicit
qualification. Corrected builds use separate targets, compiled variant identity
and source-to-executable checks before numerical execution. The
[corrected results](../research/outputs/2026-09-07-native-async/corrected/summary.json)
are the evidence for the selection above.

## Problem and intended behavior

The first native rehearsal reproduced state exactly in synchronous profiling
mode but failed complete adaptive checkpoint parity in asynchronous mode. An
action experiment needs the same checkpoint and inputs to continue consistently
before attributing a difference to the action. Small state agreement alone is
insufficient when covariance, eigenvalue estimates or effective leak differ.

Keep asynchronous non-introspection updates and the existing two-command bound.
Give each GPU update a fixed state/parameter payload, order commands that share
mutable covariance, and obtain exact CPU observations only at an identified
completion boundary. Shared memory removes copies; it does not remove data
dependencies.

The [source audit](../analyses/2026-09-07-native-async-source-audit.md) separates
three mechanisms. Their experiment evidence is retained under
[native async diagnosis](../research/outputs/2026-09-07-native-async/).

## Narrow implementation

Current source identities are retained in the experiment manifest; line numbers
refer to that captured version of `minime/minime/src/esn.rs` and `gpu.rs`.

1. **Track persistent covariance dependencies.** `gpu.rs:60–67` creates untracked
   resources. At `esn.rs:930`, allocate this estimator's covariance with
   `StorageModeShared | HazardTrackingModeTracked`, preserving its size and
   alignment. The buffer is directly bound to the existing `MTLCommandQueue`
   encoders. This covers background read/modify/write dependencies and the
   fused covariance-write/matvec-read boundary. Other resources do not need a
   blanket allocation-policy change for this repair.
2. **Capture rho with each dispatch.** `set_rho` at `esn.rs:1069` writes a shared
   scalar that submitted work still references. Bind a copied scalar with
   `set_bytes` at all rank-one encoder sites, or retain a per-submission parameter
   buffer through completion. A later setter then affects later submissions.
   Automatic GPU hazard tracking cannot order an unsynchronized CPU store.
3. **Use completed observations.** `snapshot_v2` drains pending covariance work
   before reading it. Use that boundary for exact rehearsal/capture. The raw
   `get_covariance(&self)` at `esn.rs:2421` has no such guarantee. Replace its
   future observer use with a fallible completed read or an explicitly versioned,
   completed staging copy. A bounded search of `minime/minime/src` found only
   the definition; this is not a finding of current live caller behavior.

Conceptual application:

```text
CPU: choose x_k and rho_k; encode immutable inputs; submit; continue CPU work
GPU: wait only for conflicting covariance work; apply C_k = f(C_previous, x_k, rho_k)
introspection: consume the completed C_k required by its named step
checkpoint: finish owned pending updates; serialize the completed state
```

The allocator repair uses the current Metal command-queue API. Apple's
[resource synchronization guidance](https://developer.apple.com/documentation/metal/resource-synchronization)
describes automatic conflict tracking for directly bound tracked resources;
its [fence guidance](https://developer.apple.com/documentation/metal/synchronizing-passes-with-a-fence)
describes explicit dependencies for separate passes. This proposal does not
assume that encoder boundaries alone synchronize untracked buffers. It also
does not assume Metal 4 command queues inherit this behavior.

## Acceptance and evidence

The frozen ablation independently varies covariance tracking and an explicit
fused-pass fence. All variants start from identical retained checkpoint bytes;
ordinary state, control-forced shadow state, effective leak, realized noise and
final numerical snapshots are compared. Profiling remains disabled, observation
does not force a per-step checkpoint, and all negative results are retained.
A measurement-on diagnostic confirms that the async branch and bounded pending
queue remain in use. Changing-rho tests are separate from the constant-rho
diagnosis and must compare the intended per-dispatch parameter schedule.

Before production integration, require exact within-host replay on the target
M4 as well as the development M1. Compare each host to its own continuation,
without asserting cross-hardware floating-point identity. The retained work is
correctness evidence; it is not an uncontended latency, energy or throughput
benchmark.

GPU error handling is a distinct integration requirement. Several synchronous
wait sites currently omit a command-error check. Propagate completion failure,
drain all owned pending work even after an error, and withhold an applied-step
or clean-checkpoint receipt after failed work. No GPU error is presumed to be
the cause of the reproduced numerical divergence. The pending state buffer is
already retained until command completion; do not rewrite that ownership without
evidence of a separate problem.

## Delivery and rollback

Keep the existing async scheduling, estimator equations and checkpoint schema.
Record the repaired implementation revision in rehearsal/application receipts;
the correction may change trajectories previously affected by missing ordering.
Do not equate this with a change in the beings' authored intent.

The next action implementation can present a concise explanation of which
settings each update used and a measured result through Mike's selected
being-facing workflow. This research task sends no material to the beings.

Retain the old source and failing outputs for diagnosis. Roll back a production
release by revision; do not silently restore the known-unqualified async path
while continuing to claim exact replay. If a release needs a temporary
synchronous fallback, label it explicitly and keep async qualification separate.
Numerical history already generated is not reversed by reverting source.

The [exact tested patch](patches/2026-09-07-native-async-replay.patch) applies to
`minime/src/esn.rs` and `minime/src/gpu.rs` relative to the owning repository.
The [apply/reverse receipt](../research/outputs/2026-09-07-native-async/patch-check-receipt.json)
verifies that it recreates the tested source and restores the captured original
source in fresh research-local copies. Source review, completed observation and
error/application reporting remain part of owning-repository integration; this
research pass does not deploy the patch.
