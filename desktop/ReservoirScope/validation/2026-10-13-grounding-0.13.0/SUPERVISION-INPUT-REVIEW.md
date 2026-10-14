# Owned supervisor revision and input-path audit

This is a source review and mock-test record from 2026-10-13. It does not qualify another model launch or establish a product pointer defect. The original 0.12.1 helper and 0.12.2 package, model results, cleanup error and absence supplement remain unchanged.

## Owned cleanup

The historical supervisor reported EPERM inside cleanup after an explicit stop. Subsequent scoped checks found its exact server/supervisor PIDs absent and original process group empty. That establishes later absence, not the precise syscall that failed.

Apple's public XNU `killpg1` implementation excludes zombie members during group iteration, then can return EPERM when no signalable member is found. Our old helper deliberately kept its exited leader unreaped while polling `killpg(..., 0)`. A zombie-only group is therefore a source-supported explanation for the observed error, but the old receipt lacks the syscall detail needed to prove it. [Apple XNU kern_sig.c](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sig.c#L1580-L1624), inspected 2026-10-13. Apple's archived [killpg manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/killpg.2.html) separately documents permission and missing-group errors; neither should be ignored unconditionally.

The new [helper](owned_model.py) uses a maximum128member `PROC_PGRP_ONLY` libproc query. Before any signal it requires two matching snapshots and verifies each PID's start identity, effective/real/saved UID, process group, live-process session and recognized process status. Zombie entries explicitly use a null session identifier; they cannot act, and still require exact group/UID/status and unreaped-leader exit proof. A missing/unstable/unknown/foreign member refuses authorization. It never inventories global process command lines or credentials. The waitable direct child remains unreaped throughout group operations, preventing its PGID from being reused during cleanup.

Liveness uses the scoped read-only inventory, not signal0. A zombie-only or empty group is quiescent only with an unreaped leader-exit proof. If an actual signal races with exit and raises EPERM or ESRCH, a fresh stable inventory must establish quiescence before cleanup continues; otherwise the error remains a failure. The receipt retains operation, signal, errno, before/error snapshots, delivery distinction and final pre-reap group. The helper reaps only after quiescence; a surviving same-group runner receives bounded escalation before that point. Escaped descendants outside the owned session/group remain outside this claim.

[19 mock tests](owned-helper-tests-02.json) passed: immutable private copying, credential metadata-only checks, env isolation, exact listener parsing, foreign owners/status/session refusal, stable membership, explicit zombie session unavailability versus refusal of unknown live sessions, no signal0, EPERM race handling, survivor escalation-before-reap, timeout without a false success, exclusive new output directories and EOF unregistration. These are synthetic tests, not a real service cleanup qualification. Peer review is required before use; a later actual run must retain its own result.

## Explicit new supervision output

The revised helper retains the exact previous selection JSON digest and verifies all selected private cache files, installed executable/version metadata, original staging receipt and conventional key/config metadata before launch. It reuses independently copied model bytes; it does not copy3GiB again, pull, upgrade, discover default services, or change HOME. Each launch requires a new absolute supervision directory below this desktop's `target/qa`. Existing directories and partial attempts are refused and retained. New logs/stop request/identity/receipts and child cwd go there; `OLLAMA_MODELS` continues to the revalidated private cache.

Example authorized-once recipe, not executed by this review:

```sh
python3 validation/2026-10-13-grounding-0.13.0/owned_model.py launch \
  --seconds 900 \
  --supervision-directory /Users/v/other/reservoir-llm-research/desktop/ReservoirScope/target/qa/0.13-real-gemma3-4b-run01
```

Run from `desktop/ReservoirScope`. The original `stage` subcommand remains exclusive and will refuse the already-existing pinned staging directory. The new helper does not auto-create a new selection or silently mutate the old receipt. The actual loopback port comes from the new owned listener log; no client request is made by this helper. Stop uses the new output directory's ordinary `stop-request` file. Root owns launch, app UI and actual cleanup qualification.

## Pointer source review

See [POINTER-SOURCE.md](POINTER-SOURCE.md) for the separate source audit, explicit macOS reopen handling and bounded native qualification procedure. No causal pointer-fix claim is made by this helper review.
