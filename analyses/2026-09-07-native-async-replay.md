# Repair asynchronous native adaptive replay

Later implementation: [native state actions and visible application evidence](2026-09-07-native-state-actions-implementation.md). The original outcomes and limits below are preserved.

September 7, 2026 (Pacific). Mike selected the asynchronous replay failure as the
next prerequisite for targeted substrate actions. This investigation belongs to
S-002; the selected S-005 reading remains unchanged.

**Completed:** the final asynchronous repair passes all 27 primary qualification
cases on Apple M1 Max and all 27 on Apple M4 Pro, plus three measurement cases
per host. Independent evidence and executable-identity audits pass on both.
The [exact tested patch](../proposals/patches/2026-09-07-native-async-replay.patch)
is ready for owning-repository integration; no live system was changed.

## What the diagnosis establishes

The corrected experiment isolates a missing dependency on the native spectral
covariance buffer. Consecutive background GPU jobs read and modify the same
buffer, whose allocation explicitly disables automatic hazard tracking. Making
that covariance buffer tracked restores exact asynchronous continuation in the
bounded constant-rho comparison. The state equations, input stream, adaptive
rules and two-command pending limit are unchanged.

The [source audit](2026-09-07-native-async-source-audit.md) traces the conflicting
accesses and distinguishes them from mutable-parameter and observation hazards.
The [implementation proposal](../proposals/2026-09-07-native-async-replay.md)
specifies the narrow source changes and production integration requirements.
All executed source variants are research-local copies. No sibling source,
running being, controller setting or being-facing material was changed.

## Corrected ablation

The [frozen corrected protocol](../research/outputs/2026-09-07-native-async/corrected/protocol.json)
uses the same three retained native checkpoint files at boundaries 24, 96 and
192, three interleaved variant repeats, and 100 continuation steps. These are
newly constructed research checkpoints from a 128-state/66-input native ESN.
Each case compares ordinary continuation, restored ordinary continuation and
two state paths supplied with the ordinary parent's realized noise and effective
leak. It also compares complete final numerical snapshots with only the declared
profiling diagnostics and parent-versus-shadow RNG exception removed.

| Candidate on M1 Max | Exact primary cases | What changed |
|---|---:|---|
| Original native source | 0/9 | No repair |
| Tracked covariance | 9/9 | Persistent covariance dependency tracking |
| Fence inside fused introspection only | 0/9 | Rank-one write to first matvec dependency only |
| Tracked covariance plus fused fence | 9/9 | Both |

The [results](../research/outputs/2026-09-07-native-async/corrected/summary.json)
support selecting tracked covariance without the redundant extra fused fence.
The fused-only variant leaves consecutive background updates unqualified. This
does not mean a fully explicit GPU dependency scheme could never work; that
alternative is unnecessary for the tested minimal repair.

Profiling remains disabled. No per-step snapshot or new CPU wait is inserted.
The queue retains its two-command bound. Four separate measurement-on diagnostic
cases record 376 async submissions each; the two tracked variants pass and the
other two fail. Pending depth is a retained command count, not a measurement of
simultaneous physical GPU execution. No throughput or energy claim is made.

The [independent audit](../research/outputs/2026-09-07-native-async/corrected/verification.json)
checks all 40 cases, including those four measurement cases. It recomputes
Float32 bit identity, first state/scalar differences, realized noise, effective
leak and complete numerical snapshot comparisons. It verifies checkpoint,
source, patch, runner, dependency, compiled-variant and executable identities.
There are 20 passing and 20 failing cases across this intentionally mixed
comparison; the failed controls remain evidence.

## A build mistake that must stay visible

The initial labeled ablation and a following chain diagnostic reused the same
original executable from a shared Cargo target. They were numerically audited,
but their labels did not identify different executed treatments. They cannot
support conclusions about repair efficacy. The immediate-drain diagnostic's
unexpected pending depth exposed the problem, and repeated executable hashes
confirmed it.

Those runs are retained with [invalidity](../research/outputs/2026-09-07-native-async/INVALIDITY.json)
and [verification qualification](../research/outputs/2026-09-07-native-async/verification-treatment-qualification.json)
records. Earlier statements that the repairs failed are withdrawn. Corrected
execution uses a separate build target per variant, compiled variant/source
identity, distinct executable hashes and an identity check before numerical
execution. The independent verifier now treats missing treatment identity as a
failure, even when a numerical report is internally consistent.

## Changing parameters and fresh checkpoint qualification

Constant rho cannot qualify a setter that rewrites a scalar while old GPU jobs
still reference it. The selected further repair captures rho as part of each
command's immutable payload. Its comparison runs each complete asynchronous
trajectory before the complete synchronous reference; interleaving a waited
reference at every step could mask the race by draining the shared GPU queue.
Fresh asynchronous warmup, capture, serialization and restored continuation are
also required, so the qualification is not limited to old retained checkpoints.

The [local qualification protocol](../research/outputs/2026-09-07-native-async/qualification/protocol.json)
was frozen before execution. Its [interpretation addendum](../research/outputs/2026-09-07-native-async/qualification/protocol-interpretation-addendum.json)
clarifies inherited generic metadata: the explicit fresh-construction and
changing-rho sections define this stage. The source/executable identity gates
precede all numerical runs.

| M1 Max primary qualification | Original | Tracked covariance | Tracked covariance + captured rho |
|---|---:|---:|---:|
| Fresh asynchronous warmup, checkpoint and 100-step continuation | 2/9 | 9/9 | 9/9 |
| Fixed-rho whole async trajectories versus synchronous reference | 0/9 | 9/9 | 9/9 |
| Alternating-rho whole async trajectories versus synchronous reference | 0/9 | 0/9 | 9/9 |

Each denominator is three starts × three repeats. Fixed rho is the retained
checkpoint value; alternating rho is 0.82 and 0.999 at successive updates.
Two complete asynchronous trajectories precede the complete synchronous
reference in each parameter case. State, noise, effective leak and complete
final numerical checkpoints must agree exactly, excluding only declared mode
and diagnostic fields. This is free native adaptive continuation, rather than
forcing a successful answer by replaying the reference's leak. The fresh
checkpoint cases additionally retain the conditional shadow comparisons.

The [local results](../research/outputs/2026-09-07-native-async/qualification/summary.json)
therefore distinguish the two repairs. Covariance tracking fixes constant-rho
continuation; immutable scalar arguments are additionally required by the tested
changing-rho schedule. All 27 primary cases for the final candidate pass. Separate
measurement cases retain async submission and the two-command bound.

## Target M4 qualification and handoff

The M4 Pro Mac mini at `volya` ran the same three-variant, three-repeat
qualification. The [replication protocol](../research/outputs/2026-09-07-native-async/m4-validation/protocol.json)
preserves the source, harness, checkpoint files and schedule, recording only
declared host-path, registration-time and parent-protocol differences. It ran
under Rust 1.94.1 on macOS 26.6.2; the M1 build used Rust 1.91.0. Equality is
required within each host's comparison, not between different chip/toolchain
combinations.

| Final candidate, primary cases | M1 Max | M4 Pro |
|---|---:|---:|
| Fresh asynchronous checkpoint continuation | 9/9 | 9/9 |
| Fixed rho, whole async trajectories versus synchronous reference | 9/9 | 9/9 |
| Alternating rho, whole async trajectories versus synchronous reference | 9/9 | 9/9 |

Each host also passes the three measurement follow-ups. The fresh checkpoint
measurement case records 376 async submissions and pending depth two. The
tracked-only control fails all nine alternating-rho primary cases on each host.
Original-source failures are timing/hardware dependent: its fresh cases pass
2/9 on M1 and 7/9 on M4; its rho cases pass 0/18 on M1 and 7/18 on M4. These are
experimental case counts, not a live failure rate. A pass in one original-source
run does not remove the source hazard or qualify that variant.

The [M1 verification](../research/outputs/2026-09-07-native-async/qualification/verification.json)
and [M4 verification](../research/outputs/2026-09-07-native-async/m4-validation/verification.json)
each audit 30 fresh-checkpoint and 60 rho comparisons, including controls and
measurement follow-ups. Both confirm the reports from retained numerical data
and validate the source-to-executable mapping. Their pass/fail totals include
deliberately unrepaired controls; the final candidate passes every comparison.

The exported patch targets `minime/src/esn.rs` and `minime/src/gpu.rs` relative
to the owning Minime repository. It changes covariance allocation and three
rho argument bindings, plus synchronization comments. Applying it to fresh
retained source reproduces the tested source hashes exactly; reversing it
restores the original hashes. The [round-trip receipt](../research/outputs/2026-09-07-native-async/patch-check-receipt.json)
records both checks. Patch SHA-256:
`e53583177da5aa120ee87d561e8403225eec8e987f3b966f450177c41926394e`.

The [evidence guide](../research/outputs/2026-09-07-native-async/README.md) gives
the frozen runner, source, reproduction steps and all invalid/valid stages.
The remaining implementation slice is to integrate this tested repair through
Minime's workflow, add completed-step application records and implement the
native state-action hook and finite gestures. Completed observation, GPU-error
reporting and stable-core action precedence belong in that integration contract.
Complete controller replay, active readout training and live deployment remain
separate. The native viewer and its earlier simulation fixture are unchanged.

[Board publication receipt](../board/native-async-replay.json).
