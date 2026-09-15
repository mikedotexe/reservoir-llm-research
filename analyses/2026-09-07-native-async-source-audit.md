# Native asynchronous ESN: source audit, 2026-09-07

The retained source contains a concrete missing GPU dependency on the spectral covariance buffer. It also contains two separate CPU/GPU synchronization hazards relevant to future asynchronous control: rewriting a scalar used by pending work, and reading covariance without waiting. These are source findings, not evidence that either API is currently exercised by a live being. This audit ran no GPU work and changed no implementation or live system.

Identity is the retained rehearsal source, captured at `2026-09-08T01:30:52.633669+00:00`, not a deployed binary. SHA-256 values below were recomputed and matched [the capture manifest](../research/outputs/2026-09-07-native-shaping-rehearsal/source-manifest.json). Paths and line numbers in this note are relative to `research/outputs/2026-09-07-native-shaping-rehearsal/`.

| Retained file | SHA-256 |
| --- | --- |
| `source/src/esn.rs` | `98e8fe727e9908e8939d5317d23e954425748edb45b2a737e5624a42166dfe92` |
| `source/src/gpu.rs` | `779d11a222efd0bd45d3ab15830c66a0a796292a770c12710a04644d84a0b0ff` |
| `source/src/buffer_pool.rs` | `9f4dd10331e59fa5cb5de1cb5b46325fee6ded2caa2cb5107afa92217e288b5d` |
| `source/shaders/esn.metal` | `28b83c256e36fdb9a5077e1da4cb73c050e1d3496f830404fae61e7bbc812735` |
| `source/shaders/spectral.metal` | `0a5e9a98a25293e7f5658f9347282435caf5ad84f208fd24b746c5ce3258b031` |
| `retained-harness.rs` | `5d97ae09a30835524675e0dd253026abd3f391c0214c93a2baa817daabce5cf2` |

1. **Covariance GPU conflicts are not explicitly ordered.** `gpu.rs:61–67` allocates shared buffers with `HazardTrackingModeUntracked`; `esn.rs:930` uses that allocator for covariance. Background rank-one updates permit two pending commands (`esn.rs:1330–1371`). Their input vectors are distinct, but each command binds the same covariance at `1356`. The shader reads the old element and writes its update (`shaders/esn.metal:14–37`), so consecutive updates require a dependency. No fence or event establishes it. The fused introspection path drains earlier commands at `1578–1580`, then places a covariance write and read in separate encoders of one command buffer (`1592–1603`), also without a fence. Its comment at `1597–1598` assumes an automatic barrier despite the untracked allocation.

   Apple specifies automatic GPU dependency tracking for tracked resources directly bound to encoders submitted through `MTLCommandQueue`; a pass boundary alone does not supply that guarantee for this explicitly untracked covariance. A fence can order conflicting passes, including passes in different command buffers on the same queue. [Resource synchronization](https://developer.apple.com/documentation/metal/resource-synchronization), [Synchronizing passes with a fence](https://developer.apple.com/documentation/metal/synchronizing-passes-with-a-fence).

   Minimal candidate: allocate **covariance alone** with tracked hazards, retaining asynchronous submissions and the pending limit of two. An alternative is an explicit per-estimator dependency covering every conflicting covariance pass. A fence only inside the fused command buffer leaves background-to-background conflicts unresolved. The actual estimator loads `shaders/esn.metal` (`esn.rs:899–911`); `spectral.metal` is not the rank-one kernel used here. Causal attribution belongs to the separate experiment, not this source audit.

2. **Changing rho can change the scalar observed by already submitted work.** `set_rho` (`esn.rs:1069–1072`) immediately writes shared `rho_buf`; pending rank-one commands bind that buffer at `1358`. There is no wait before the CPU overwrite. GPU hazard tracking does not make a later CPU store wait for earlier GPU readers. Minimal asynchronous repair: retain rho as CPU policy and copy the intended scalar into command-owned arguments at encoding time, using `set_bytes` or an immutable per-submission buffer whose lifetime extends through completion. Apply the convention to all rank-one encoding paths. Acceptance should check that each update uses its submission's rho while multiple commands remain allowed in flight. The old parity harness does not vary rho, so this is not an explanation of that failure. Apple's guidance explicitly requires CPU writes to finish before committing commands that reference a buffer, and uses separate resource instances to permit overlap. [Synchronizing CPU and GPU work](https://developer.apple.com/documentation/metal/synchronizing-cpu-and-gpu-work).

3. **The public covariance getter has no completed-boundary qualification.** `ESN::get_covariance(&self)` (`esn.rs:2419–2425`) copies shared covariance through a raw CPU read (`gpu.rs:124–125`) without draining pending writes. It can therefore return data without a coherent native-step boundary. Root's bounded search for `get_covariance(` in `../minime/minime/src`, restricted to Rust files, found only the definition: no in-tree caller was identified, and live use is not diagnosed. Minimal exact-read repair: a fallible mutable getter that drains this estimator before copying, or the existing snapshot path. A frequent observer should instead receive a completion-stamped cached/staging copy or explicit unavailability. It should not borrow the active GPU buffer. `SpectralSR::snapshot_v2` already waits at `991–996`; the old harness uses that path, so the raw getter is not its snapshot failure.

4. **The input pool's completion ownership is present; premature reuse was not found.** `buffer_pool.rs:23–33` removes an acquired buffer from the free list. The submitting estimator owns that buffer with its command (`esn.rs:1368–1371`) until reaping sees `Completed`/`Error` (`1164–1188`) or the oldest-command wait completes (`1191–1205`). Only then is it returned to the pool. New estimator copies allocate separate covariance and scratch buffers (`929–936`). There is no evidence here of two pending submissions sharing the same pooled input. There is no explicit estimator `Drop`, but ordinary command buffers are used, not an unretained-reference command-buffer API; missing `Drop` alone is not evidence of a GPU use-after-free. The raw `Gpu` pointer (`810`, with unsafe `Send`/`Sync` at `895–896`) still imposes an ownership contract: the GPU owner must outlive the estimator. The retained harness satisfies this; an owning API should encode that requirement with a lifetime or shared owner when refactored.

5. **Completion and failure need consistent reporting.** Background waits check command error status (`1194–1199`), but synchronous rank-one (`1415–1425`), matvec (`1482–1501`), fused rank-one/matvec (`1605–1621`), and damping (`1135–1136`) do not. The drain loop exits on its first error (`1207–1213`), potentially leaving later owned commands pending. Minimal implementation acceptance: checked completion before reading results or issuing a successful application receipt; fallible damping; explicit shutdown/drain that finishes all owned commands while preserving an error; and no clean checkpoint claim after failed work. `maybe_introspect_batched` increments its tick before reaping can fail (`1716–1723`), so requested/submitted ticks cannot be treated as successfully completed GPU updates. This failure-path issue is separate from numerical parity: no observed GPU command error is asserted here.

The checkpoint contains covariance, eigenvector, rho, eigenvalue history, estimator schedule/count, adaptive settings, native weights/state, geometry baseline, RLS state, live/base leak and lambda, noise/RNG state, and leak override (`esn.rs:821–860`, capture/restore `991–1053`). Transient scratch buffers are overwritten before use. This bounded audit found no omitted recurrence-affecting field that explains an asynchronous-only failure. The old harness compares ordinary, restored, forced-control shadow, and shadow duplicate paths (`retained-harness.rs:54–128`); its forced shadow is a conditional-control comparison, not free adaptive equivalence.

Keep the covariance-ordering ablation isolated from these additional repairs. Its protocol and execution evidence are retained separately under [the native asynchronous experiment](../research/outputs/2026-09-07-native-async/); results were pending when this source audit was written. Passing that experiment can establish bounded replay behavior for the tested candidate. It does not by itself validate dynamic rho, the unused getter, error handling, live orchestration, or deployment.

## Final tested patch review and qualification, 2026-09-07

**No blocker found in the narrow final repair.** The
[exported patch](../proposals/patches/2026-09-07-native-async-replay.patch) has SHA-256
`e53583177da5aa120ee87d561e8403225eec8e987f3b966f450177c41926394e`.
The reviewed tested files under
`research/outputs/2026-09-07-native-async/qualification/variants/cov_tracked_rho_inline/src/`
have recomputed hashes:

- `esn.rs`: `b4c7d43582f11818408cfd2a6ecfd866a02a3c2c8dfcc5e832da50f5e0486a03`.
- `gpu.rs`: `5dbdff8d3f17f7289ba97ad76aacd260f37c9d3f03ba80d7bcead6f298d33ba9`.

These match the [patch round-trip receipt](../research/outputs/2026-09-07-native-async/patch-check-receipt.json):
application recreates the tested bytes and reversal restores the original bytes
in research-local copies. Final-source line numbers below refer to these hashes.

The tracked allocation at `esn.rs:930–935` is the same covariance object directly
bound by damping (`1131`), background rank-one (`1360`), synchronous rank-one
(`1410`), fused rank-one encoding (`1438`), fused matvec encoding (`1453`) and
standalone matvec (`1479`). It therefore covers all GPU covariance access sites
identified in this module. Initial/restore writes happen before new work; exact
snapshot reads retain their drain. The raw getter remains unsynchronized and
outside the qualified observation path. The patch adds no CPU wait or explicit
fence, changes no shader/equation, and retains `MAX_PENDING_RANK1 = 2` (`1335`).
`gpu.rs` changes comments only, avoiding an allocator-policy change for unrelated
resources.

All three rank-one rho bindings use `set_bytes` (`1363`, `1413`, `1441`), capturing
the selected scalar in command arguments. No remaining GPU binding reads
`rho_buf` in the reviewed module. Its retained allocation and setter writes are
redundant bookkeeping, not an in-flight shared-parameter hazard after this
patch. The change preserves the intended per-dispatch rho semantics without
serializing setters. It does not repair the separate unchecked completion,
error-drain, raw-getter or GPU-owner lifetime contracts described above.

The [corrected ablation](../research/outputs/2026-09-07-native-async/corrected/summary.json)
passes 9/9 constant-rho primary cases with tracked covariance and 9/9 with
tracked covariance plus a fused fence; original and fused-fence-only variants
each pass 0/9. This supports selecting covariance tracking without the extra
fence. The earlier apparent negative ablation reused the original executable
through a shared Cargo target; its treatment labels were invalid. The
[invalidity record](../research/outputs/2026-09-07-native-async/INVALIDITY.json)
preserves that correction. Its numerical outputs are not evidence against the
repair.

Final qualification passes **27/27 primary cases on each of M1 Max and M4 Pro**:
fresh checkpoint 9/9, fixed rho 9/9 and alternating rho 9/9, plus three passing
measurement follow-ups per host. Tracked-only alternating-rho controls pass
0/9 on each host. In the reviewed harness, each whole async trajectory finishes
before the synchronous reference starts (`src/main.rs:182–201`); it calls ordinary
`step`, allowing native adaptive leak to evolve rather than forcing reference
leak. Fresh checkpoint cases separately retain the conditional-shadow checks.
Only declared diagnostic/mode fields are excluded from final numerical snapshot
comparisons; rho comparisons retain RNG. The fresh measurement records 376 async
submissions and pending depth two (rho measurements: 188 submissions each).
Pending depth is not physical GPU concurrency or a throughput benchmark.

Both [M1 verification](../research/outputs/2026-09-07-native-async/qualification/verification.json)
and [M4 verification](../research/outputs/2026-09-07-native-async/m4-validation/verification.json)
report passing evidence audits and qualified variant comparisons, each covering
30 checkpoint and 60 rho cases including controls and measurements. This final
review checked their status and source/patch identities; it did not rerun GPU
work or replace those independent numerical audits. The
[main analysis](2026-09-07-native-async-replay.md) provides the complete scope and
history. Finite within-host native replay is qualified; full controller
integration, active readout training, state-action application and deployment
remain separate.
