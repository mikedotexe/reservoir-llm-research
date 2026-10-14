# Sustained quota repair — source-only qualification

The source repair prevents the reproduced sparse-journal quota dead end by holding ordinary work before it consumes terminal headroom. It also permits an inspected committed snapshot to be exported while the same active generation has a newer volatile revision. This is **not a rebuilt or shipped app**. The frozen 0.12 executable remains SHA-256 `f68a3752a628edf11ac6161a26e6979bb22dcf4c3ee1c63f10add2cea86ab40d`; the concurrent minimized reliability run measures that unchanged executable.

[Final checks and exact source/executable hashes](quota-repair-final-02-qualification.json), [natural-profile outcomes and file inventories](quota-repair-final-02-evidence.json), and [source continuity and patches](quota-repair-final-02-source-continuity.json) are retained separately from the [original failure investigation](NATURAL-QUOTA-01.md). Historical failure records and the successful publisher qualification were not overwritten.

## Admission and terminal handling

Ordinary publications size their actual segment, checkpoint, replacement manifest, and any conflicting uncommitted-link quarantine copy. Existing identical immutable objects require readback/sync but not another allocation. Admission counts existing files and the temporary replacement manifest; it does not spend space based on speculative future checkpoint cleanup. Counts refer to logical file lengths, not filesystem allocation blocks or available device capacity.

Ordinary run low water is **8.125 MiB** (`2 × 4 MiB object limit + 128 KiB manifest limit`). An actual candidate crossing that threshold is retained as `budgetReached`; numerical advancement, provider dispatch, next-step feedback application, Start, and retries then stop. Minimum 16 MiB sessions can therefore stop near half their logical budget. The default 256 MiB budget has the same fixed headroom. This policy does not promise full quota utilization.

A separate projection clones the actual core state, acknowledges the clone's buffered events, and serializes the bounded remaining terminal path. Ordinary writes reserve Stop/cancel → Skip → close; Stop reserves Skip → close; Skip reserves close; final close admits its actual peak only. Terminal segment slots and object slots are included. The projection never changes the live RNG, recurrence, events, journal or feedback. The core change is solely `#[derive(Clone)]`: removing that line reproduces the frozen 0.12 core source hash exactly.

The storage-hold marker survives bounded diagnostic truncation. Both the journal-admission hold and duration-exhaustion pending boundary now increment the durable revision. An ordinary persistence during Retry save may itself impose low water; Retry returns immediately in that case without publishing a journal. Provider settlement after Pause still uses ordinary admission.

## Old blocked instances and exact export

Recovery export accepts an inspected disk generation/revision even when the same active generation has newer unsaved state. It still checks the current disk identity under the state lock. The main live-revision export does not silently substitute an older snapshot. A different active generation or a changed committed revision remains stale.

Explicit discard can release an unsaved tail without rewriting the retained manifest only when the **current verified durable checkpoint is Ready**, agrees with the active committed checkpoint, and belongs to the same generation. It never selects an older Ready checkpoint. All committed bytes remain unchanged. The UI reports the live/durable boundary; the stopped decision in this exceptional path is process-local, not a fabricated durable stopped marker. Retained Language, Memory, Journal, Prepared or Blocked intent requires a durable Skip and cannot use this fallback.

## Measured natural profiles

These accelerated scripted tests generated real records in isolated temporary stores, with no padding, budget changes, providers or app-process actions. They are not elapsed-duration or power-loss tests.

| 16 MiB profile | Live / durable step at hold | Saved journals | Logical bytes at hold | Outcome |
| --- | ---: | ---: | ---: | --- |
| Every 3 steps | 75 / 75 | 24 | 8,284,793 | Stop, close, live export, inspected export and held restore pass |
| Every 1800 steps | 1740 / 1740 | 0 | 8,317,151 | Stop, close, live export, inspected export and held restore pass |

Both hold with zero uncommitted events. The sparse configuration intentionally reaches low water before its first observation at step 1800. This contrasts with the preserved original sparse failure at live step 3240 / durable step 3210, where Stop, discard and active export could not complete.

## Checks and limits

- Final natural profiles: **2 passed**.
- Full desktop all-target suite: **169 passed**, 2 opt-in natural tests separately executed.
- Full core all-target suites: **150 passed** across 29 test result groups.
- Strict workspace all-target Clippy: **passed**.
- Final checks ran **2026-10-13 17:32:34.913899–17:40:11.274699 UTC** with before/after source and package identities unchanged. Earlier pre-review natural execution began at 17:28:03 UTC; its successful result and a paused orchestration note are separate `final-01` receipts. Treat this whole compilation/test period as host load when interpreting the ongoing packaged-app sampler, not a quiet-energy comparison.

Focused tests cover exact near-cap terminal reserve consumption, final close with only actual replacement-manifest space, pure projection, diagnostic marker retention, both revision fixes, a newly held Retry save, same-generation durable-prefix export, Ready-tail discard, and retained-intent refusal. Two synthetic HTTP-shaped reply envelopes stay at or below the 1 MiB transport cap: a maximum accepted 65,536-byte heavily escaped reply and a rejected 170,000-byte reply. Each follows a saved/applied 65,536-byte heavily escaped memory and can be retained and explicitly stopped/skipped into a verified Ready chain.

A separate direct-core 1 MiB NUL reply expands beyond the 4 MiB segment limit. That deliberately unsupported HTTP-envelope-sized injection remains fail-closed: no journal is claimed, the retained Language checkpoint is preserved, and generic discard cannot pretend a Skip was durable. It is not evidence that this specific payload can arrive through the current 1 MiB entire-HTTP-body cap. Hard object limits, external I/O failures, malicious changes and arbitrary oversized future evidence remain distinct from the tested natural-quota repair; there is no claim of universal recovery from every possible corruption or response.

No native numerical formats, tolerances, provider behavior, dependency versions or live systems were changed. A rebuilt package and independent packaged UI/reliability qualification are still required before attributing these repairs to a shipping executable.
