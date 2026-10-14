# Owned model cleanup result — 0.14.0

The completed owned run's retained receipt records successful cleanup of its original process group: one accepted SIGTERM, no SIGKILL, group quiescence verified before the direct child was reaped, child exit code 0, and no supervision errors. This inspection only read completed files. It made no service requests, process queries, signals, app interactions, or credential-content reads.

All six original run files were copied into a new, exclusive [owned-run-01](owned-run-01/retention.json) directory. Each copy was read back and compared byte for byte; each source was reread unchanged. The receipt records original file identities, lengths, SHA-256 values, parsed access-log entries, cross-file identity checks, and limitations.

## Bound run

- Owned leader PID/PGID/SID: **33792**; direct supervisor PID: **33771**.
- Spawn: **2026-10-13 21:27:14.189803 UTC**. Supervision ended: **21:32:01.993271 UTC**, after **287.807358 seconds** on the monotonic clock, following the explicit stop request. The configured lifetime ceiling was 1,200 seconds.
- Owned endpoint: `http://127.0.0.1:51691`, obtained from the server's listener log, not rediscovered during this inspection.
- Ollama version from bound application metadata: **0.40.3**. Executable SHA-256: `76535100c7aaf5aa94fe749b1bf0cfe3a702fa0743c7421fed059b783f4969de`.
- Helper SHA-256: `9c5351878ff5ee634f8f6c3afa49f0e9c6e5108224073a7b8ebda14d0d35ae9f`, matching the prospective [helper freeze](helper-source-freeze-01.json) and [pre-Start binding](real-model-bound-before-start.json).
- The private selected-model cache, selection SHA-256 and stage-receipt SHA-256 agree across the launch, process, endpoint, result, and pre-Start receipts. This retention did not reread or copy model blobs.

The service's default context setting was 4,096. The separately bound application request configuration was context **8,192**, output ceiling **1,024** tokens, and request deadline **180 seconds**. The service default must not be substituted for the application's actual request configuration. Provider and export checks are documented separately in [EVALUATION.md](EVALUATION.md).

## Logged request counts

The complete retained **38,089-byte** [owned service log](owned-run-01/service.log) has five `[GIN]` access records; all five parse, and the supervisor reports **zero discarded log bytes**.

| UTC completion time | Method and path | Status | Logged duration |
| --- | --- | --- | --- |
| 21:27:29 | `GET /api/tags` | 200 | 3.404375 ms |
| 21:28:47 | `POST /api/chat` | 200 | 9.33210425 s |
| 21:29:32 | `POST /api/chat` | 200 | 14.890474083 s |
| 21:30:11 | `POST /api/chat` | 200 | 7.413168875 s |
| 21:31:07 | `POST /api/chat` | 200 | 25.1351155 s |

This establishes **one logged metadata request and four logged chat requests**, with no extra generation request in this retained owned log. Times are converted from the log's local UTC−07:00 time on this date; they are access-log completion times, not precise request-start timestamps. HTTP 200 alone does not establish response completeness, scientific validity, journal-save success, or writing quality. It does not exclude unlogged attempts or activity outside this owned service. Native export/replay and writing evaluation remain separate evidence.

## Cleanup evidence and the unreadable leader

At **21:32:01.887489 UTC**, the helper sent SIGTERM only after two scoped snapshots agreed on the stable start identities of leader **33792** and member **34134**, both in PGID/SID **33792** with the expected user identities. The syscall was accepted; the helper did not treat that fact alone as successful termination.

Subsequent observations at **21:32:01.992952** and **21:32:01.993062 UTC** listed only the leader. Its `proc_pidinfo` identity read returned **ESRCH (3)**, while `waitid(P_PID, WEXITED | WNOHANG | WNOWAIT)` proved that exact direct child had exited and remained unreaped. The [frozen helper](owned_model.py) permits this exception only for its own leader; an unreadable peer would not inherit the proof. The raw unavailable-identity observations remain in the [supervision result](owned-run-01/supervision-result.json).

The final record is therefore **quiescent before reap**, not a claim that the group enumeration was already empty. The leader's reserved PID remained available for ownership protection until the final verification, then the helper called its sole reaping wait and obtained exit code 0. The original group's other observed member was absent from the final snapshots. This is an actual exercise of the unreadable-leader exit-proof path. It is not a qualification of every transient membership retry or escalation path.

Scope remains the original owned process group. Escaped descendants were not inventoried. This review performed no fresh process-absence or endpoint probe and makes no claim about unrelated services. The complete helper audit contains four group-observation records and one signal record, with no signal escalation or recorded error.

## Continuity and retained identities

The helper's retained before/after metadata for the conventional private key, public key and `server.json` is identical; `server.json` remained absent. These are `lstat` identity/size/time/mode checks only. No key or configuration contents were read or hashed by this inspection, and metadata equality is not a content-equivalence proof.

| Artifact | SHA-256 |
| --- | --- |
| [Retention receipt](owned-run-01/retention.json) | `f1655aff08c5ab0df842a28d7106c6741ac5ca23c24bcf013dfbbeacb86869a9` |
| [Supervision result](owned-run-01/supervision-result.json) | `1c885879e9a5b54bb0831cc599073363b4acac38ed70fed893c7162d91f3fa62` |
| [Service log](owned-run-01/service.log) | `63c3da3b954e46739eea15e82f9c8a64ab5c35d6ea4b322f6fba72fefd73ba8d` |
| [Launch intent](owned-run-01/launch-intent.json) | `be7b9d1c7e890eb2b12df806e785f174b619bf472244b140b5bdf9bbd0d1bae9` |

The original 0.13 failed supervision result remains unchanged at SHA-256 `c13eb6fd8d15fabc42b23656a7eef703cd426f408221492bca9169d80b31955e`, matching its preexisting [cleanup supplement](../2026-10-13-grounding-0.13.0/owned-model-cleanup-supplement-01.json). This successful 0.14 run does not retroactively change the earlier failure or establish its exact transient kernel cause.
