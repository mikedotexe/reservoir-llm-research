# Owned model supervision for the writing-room rehearsal

This is a new validation helper, copied from the frozen 0.13 helper. It changes no app source, model bytes, shared model configuration, or historical receipt. Tests use synthetic files and mocked process operations. Actual 0.14 launch, cleanup, runtime memory, and writing quality remain unexecuted by this helper author.

## Fixed selection and isolated launch

The immutable [selection receipt](../2026-10-13-reading-0.12.1/model-selection.json), SHA-256 `7de0ae35b3d231201679b2242484cb24a9122a8f9ce866b8554dfe6384a2d86a`, remains the authority for the selected `gemma3:4b` manifest and its five referenced objects. The manifest SHA-256 is `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a`.

Launch revalidates the existing independent private copy under `target/qa/0.12.1-real-gemma3-4b/models`; it does not copy another 3.3 GB or read shared model blobs. Exact size/hash validation covers all six private files, the original stage receipt, and the selected application metadata. Missing or changed input aborts; there is no pull, model substitution, or fallback endpoint.

The selected executable remains `/Applications/Ollama.app/Contents/Resources/ollama`, version 0.40.3 from the application plist, SHA-256 `76535100c7aaf5aa94fe749b1bf0cfe3a702fa0743c7421fed059b783f4969de`. Conventional private/public key and `server.json` checks use `lstat` metadata only, before and after supervision. Their contents are never read or hashed.

The child receives the same explicit environment as the pinned selection: ephemeral `127.0.0.1:0`, the private models directory, cloud disabled, one parallel request, one loaded model, one queued request, pruning disabled, and no history. Inherited `OLLAMA_*` and proxy overrides are removed; `HOME` is preserved. The per-request context sent by the app is separate from the service's default context setting. The actual listener port is read from this owned process's log, never discovered by probing a service.

From `desktop/ReservoirScope`, the parent's proposed launch is:

```sh
python3 validation/2026-10-13-writing-room-0.14.0/owned_model.py launch \
  --seconds 1200 \
  --supervision-directory /Users/v/other/reservoir-llm-research/desktop/ReservoirScope/target/qa/0.14-real-gemma3-4b-run01
```

The output directory must be new, absolute, ordinary, and beneath this desktop project's `target/qa`. The helper creates it exclusively. Existing paths, links, traversal, and changed cache/software identities are refused. `stage` remains a separate command and is not needed for this already staged selection. `launch` defaults to 900 seconds and accepts at most 1,200 seconds; it starts one process session/group and never relaunches it.

The service lifetime proposal is 1,200 seconds. A 900-second app duration, 121 numerical steps at one-second pace, cadence 30, and four attempt slots are compatible with the proposed larger request limits of 1,024 output tokens and 180 seconds per request. Four worst-case request deadlines alone account for 720 seconds; numerical pacing, saving, setup, and UI work also take time. The first app budget reached holds the session, and an already-dispatched request may settle under its own deadline. These bounds do not guarantee four successful journals. The parent must bind the actual accepted app configuration and endpoint in the run receipt; the helper does not enforce the app's token or numerical budgets.

## Scoped cleanup repair

The [0.13 cleanup supplement](../2026-10-13-grounding-0.13.0/owned-model-cleanup-supplement-01.json) preserves a successful group SIGTERM followed by a failed post-signal stability check. Subsequent scoped observations found the server, supervisor, and original group absent. The exact transient observations were not recorded, so this revision does not assert a retrospective cause beyond that evidence.

The new observer checks only the known process group, at most 128 members per observation. Two observations must agree on process start identities and membership; volatile scheduler status and reparenting do not count as PID replacement. UID, real UID, saved UID, group, session, and known start identity remain mandatory. Foreign identity, reused PID, permission failure, or unknown status fails closed before another signal. Known member identities remain pinned across the cleanup sequence.

Transient ESRCH or membership changes receive bounded rereads, with at most two seconds per observation call and a ten-second TERM grace. Each failed observation retains available raw members, the operation, error, timestamp, and outcome. Evidence is capped at 512 observations and 8 MiB; exhausting that cap fails closed rather than dropping evidence silently. A group that remains unknown at the deadline is neither escalated nor claimed clean.

An unreadable member is never assumed gone. The sole exception is the direct owned leader: `waitid(P_PID, WEXITED | WNOHANG | WNOWAIT)` can prove that exact still-unreaped child exited even when `proc_pidinfo` returns ESRCH. That proof is labeled separately from BSD metadata and never extends to another unreadable group member. The child remains unreaped until the whole original group is proved quiescent. Any SIGKILL after the TERM grace requires a fresh known-group proof; final proof and reaping are separately bounded. Cleanup can extend beyond the selected service-running lifetime by its bounded observation/grace/reap windows.

The source basis remains the public macOS SDK `proc_bsdinfo` ABI and [Apple's XNU signal implementation](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_sig.c). The API review was performed on 2026-10-13; the particular 0.13 transient is not inferred from that source. No broad process inventory, signal-zero liveness probe, `pkill`, default-service stop, or signal to an unverified group is used. Descendants that escape the original group are outside this helper's inspection claim.

## Qualification

The focused command is:

```sh
python3 -m unittest discover \
  -s validation/2026-10-13-writing-room-0.14.0 \
  -p test_owned_model.py -v
```

[owned-helper-tests-01.json](owned-helper-tests-01.json) and its log bind 27 passing mocked tests. They cover repeated post-TERM transient reads, status-only changes, foreign/reused identities, unknown peers, explicit direct-child exit proof, deadline exhaustion, audit exhaustion, keeping the leader unreaped through final group cleanup, metadata-only credentials, exclusive private copies, unchanged `HOME`, loopback listener parsing, and EOF handling. These are mechanism tests, not a completed real cleanup qualification. Peer review and any subsequent actual run must be retained separately; the 0.13 helper and receipts remain immutable.
