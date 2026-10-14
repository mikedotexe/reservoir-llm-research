# Sustained persistence and publisher review

This is an engineering source review plus an isolated regression, not an observation of Astrid or Minime and not a multi-hour endurance result. Sources are the repository's sustained engine, owned-store backend and lifecycle adapter. No Being source/store or model endpoint was accessed. The independent long run uses the unchanged final 0.12 executable SHA-256 `f68a3752a628edf11ac6161a26e6979bb22dcf4c3ee1c63f10add2cea86ab40d`.

## Confirmed false-interruption defect and pending source repair

The packaged watchdog samples wall time, then calls `emit()`. Its synchronous publisher acquires the session mutex and invokes the subscriber. Export owns that mutex during verification and copy. A healthy, awake 5.5-second mutex hold therefore delays the next watchdog sample past the five-second threshold and incorrectly marks the run interrupted. `watchdog-lock-before.log` retains the failed regression. This establishes one reproducible software path; it does not establish its incidence in the long run.

The unbuilt source patch moves delivery to one per-state publisher thread and a capacity-one signal queue. Worker/watchdog emission is nonblocking; the publisher reads the latest snapshot under the state mutex and invokes the subscriber after releasing the mutex. A slow observer cannot accumulate old frames or create a thread per update. The publisher uses a weak state reference while waiting; its channel closes when the final state owner disappears. A failed subscriber is removed only if it is still the same subscription.

Readback also found that the worker did not explicitly publish after clearing `worker_active`. The patch sends a settled update after watchdog cleanup. A new process-local `snapshotSequence` decimal u64 orders every update, including empty initial snapshots and same-revision capability changes, without changing a saved manifest's revision. Its first value is one; checked increment fails closed at theoretical exhaustion and cannot wrap. Frontend ordering is qualified separately by its owner.

`watchdog-source-binding.json`, the `*-before.rs.txt`/`*-after.rs.txt` copies and `watchdog-*-final.patch` bind this change. The before copies were reconstructed by reversing the patch and matched byte-for-byte by SHA-256 to `../2026-10-13-sustained-0.12.0/source-before-final-build.json`; historical receipts were not rewritten. `publisher-final-01-qualification.json` records source/package identities, exact commands, environment and overlap timestamps for the full desktop tests and strict Clippy. These compile/test intervals are background load and must not be interpreted as quiet-host energy measurement windows.

The five-second watchdog condition and the real AppKit sleep/wake adapter are unchanged. Actual sleep, scheduling starvation and forward wall-clock adjustments still have conservative interruption semantics. The patch does not claim to distinguish those causes. The baseline package still contains the confirmed blocking publisher until a separately identified future build is made.

## Growth and lock costs to measure

| Source location | Mechanism and implication |
| --- | --- |
| `src-tauri/src/sustained_store.rs:422,597,715`; `sustained.rs:620` | Every successful persistence performs an owned-directory byte scan for admission, then another for displayed usage. Journal admission adds a scan at store line539. Each scan grows with retained objects; cumulative steady-run persistence cost can grow faster than linearly across a long session. No measured performance failure is inferred from this source path alone. |
| `sustained_store.rs:820,900,960` | Verification replays every segment, then reparses segments for journal indexing. Extra-file classification compares each physical journal name against every committed journal, giving an O(J²) membership pass at large J. Hash/replay guarantees remain useful, but late recovery/export latency deserves explicit measurement. |
| `sustained.rs:1166,1220`; `sustained_store.rs:662,666`; `sustained_commands.rs:230` | Restore verifies before calling a journal-index operation that verifies again. A normal UI export performs a pre-dialog verification, then three more verification passes through the runtime/store/copy path. Runtime export holds the state mutex for the latter operations. This can delay controls and stepping; test it as a separate workload rather than folding it into steady-run resource statistics. |
| `sustained.rs:620`; `sustained_store.rs:960` | Core event buffers are bounded; the backend journal catalog still grows with retained journals and scans for unsupplied hashes at commits. It is bounded by the configured maximum of 10,000 attempts, not constant memory. The package needs measured RSS/file-descriptor/CPU trends over actual duration. |
| `sustained_store.rs:417–424,539` | Journal admission reserves 4 MiB, but general persistence checks only the next object sizes despite its “margin” comment. Near a self-filled quota, another terminal/skip checkpoint may also be refused. Existing injected quota tests do not establish recovery from every naturally saturated-store state. Preserve this risk and use a separate owned low-quota case before claiming quota-exhaustion usability. |

Default budgets are 10,800 steps, 360 attempts, 21,600 running seconds, 256 MiB and 1,000 ms pacing. The time budget is a ceiling, not a promised duration: a different step, attempt or storage budget may stop first. Hard limits are 1,000,000 steps, 10,000 attempts, 24 hours, 512 MiB and pacing 100–10,000 ms. The accepted config in the actual run plan, rather than these defaults, determines that run's scope.

## Recovery boundaries

Whole-bundle replay begins from exact genesis and a contiguous hash-linked prefix. Physical journal bytes are checked against reconstructed journal evidence. Uncommitted files are diagnosed and never silently promoted; a later explicit history change may quarantine a conflicting uncommitted slot. Current and previous standalone checkpoints are retained while segment endpoints preserve earlier states.

Restore never automatically dispatches a provider. A retained language opportunity becomes an interrupted/blocked decision even when the checkpoint predates dispatch, since that checkpoint cannot prove no later network attempt occurred. Saved Prepared feedback remains ineligible to advance until explicit Start; restored authorization is not inferred from old process memory. Unsaved numerical progress may roll back to the last durable checkpoint: do not describe all visible pre-crash steps as recovered.

The previous 0.12 clean-quit Prepared test is useful but does not qualify abrupt process termination. The separate prospective [process-interruption case](PROCESS-INTERRUPTION-PROTOCOL.md) names the required trigger and evidence. Root owns actual UI/process actions; this review did not perform them.

## Source-only qualification result

The final Rust source passed all 161 desktop tests in 149.87 seconds and `cargo clippy --locked -p reservoir-scope-desktop --all-targets -- -D warnings`. The test command was `cargo test --locked -p reservoir-scope-desktop`. Both used the pinned workspace toolchain and the per-process Xcode/SDK environment retained in the receipt. Six added tests cover awake mutex delay, slow subscribers, subscriber replacement, bounded coalescing plus last-owner release, deterministic terminal publication with same-revision Stop ordering, and exact snapshot sequencing above JavaScript integer precision. An existing late-response/subscription test now waits for actual delivery instead of allowing an empty received list. The source and frozen packaged executable hashes were unchanged throughout this qualification.

The test/Clippy interval was 2026-10-13T16:31:50.400328+00:00 through 2026-10-13T16:34:35.556782+00:00. This is a source-only result; the existing package has not been rebuilt with this repair.
