# Owned episode 02 service and cleanup

The completed supervisor outputs are preserved byte-for-byte in [owned-run-01](owned-run-01/retention.json). All six source files were ordinary bounded files, copied into a new exclusive directory, read back, and compared again with their originals. No source file, helper or application was changed. This audit performed no process query, signal, UI action, model request or endpoint call.

## Identity and elapsed time

The selected Ollama 0.40.3 executable retained SHA-256 `76535100c7aaf5aa94fe749b1bf0cfe3a702fa0743c7421fed059b783f4969de`. The owned server was PID/PGID/SID **56024**, a direct child of supervisor **55992**, listening at the recorded owned endpoint `http://127.0.0.1:54465`.

Spawn was **22:53:21.150089 UTC**; supervision ended **22:58:47.063051 UTC**, after **325.916913 seconds** of recorded monotonic supervisor lifetime, below its 1,200-second cap. This includes readiness and idle time. It is not the application's retained running time, numerical elapsed time, or a request deadline. App session elapsed time is not derived here.

## Retained access log

The complete retained log has **39,934 bytes**, with **zero discarded bytes** reported by the supervisor. All five access-log lines parsed: one `GET /api/tags` and four `POST /api/chat`, all HTTP 200. No additional generation or other access request appears in this owned log. This is a scoped log count, not a capture of every network action or independent authentication of the provider.

| Recorded completion (UTC, second resolution) | Method and path | Status | Logged duration |
| --- | --- | --- | --- |
| 2026-10-13T22:53:32+00:00 | `GET /api/tags` | 200 | `2.134666ms` |
| 2026-10-13T22:54:44+00:00 | `POST /api/chat` | 200 | `12.22889775s` |
| 2026-10-13T22:56:47+00:00 | `POST /api/chat` | 200 | `1m33s` |
| 2026-10-13T22:57:41+00:00 | `POST /api/chat` | 200 | `23.054066333s` |
| 2026-10-13T22:58:28+00:00 | `POST /api/chat` | 200 | `16.132702667s` |

## Runner-reported context information

The runner logs an 8,192-token context slot. Tasks 0 / 213 / 599 / 996 respectively report prompt counts **1,637 / 2,199 / 2,370 / 2,374** and output-evaluation counts **210 / 382 / 393 / 441**. All four releases report `truncated = 0`. Their exact source lines are retained in the receipt. These are runner log self-reports, not the typed application's output-count fields or a retained `prompt_eval_count` response field. Task identities have not been equated to app attempt identities. The startup warning comparing an 8,192 context with the model's larger training context is distinct from input truncation.

This log adds descriptive context evidence; it does not establish exact full-input coverage, attention, comprehension, or a beneficial memory effect. Output counts and request completion also do not establish correct prose. Application response/save/memory/application evidence belongs to the independently checked native export.

## Completed scoped cleanup

The root operator wrote the explicit stop request after reporting the app's four saved/applied opportunities and 121-step budget. The supervisor records **one accepted SIGTERM to its verified owned process group**, no SIGKILL, no errors, and child exit code 0.

Before TERM, two stable owned members were reported: leader 56024 and child runner 56428, with matching group/session/user identities. The final two observation pairs no longer reported the runner. They reported only leader 56024 as unreadable with ESRCH while the supervisor still held that exact direct child unreaped and had non-reaping child-exit proof. The final record states original-group quiescence **before** the child was reaped. It does not claim that the group was already empty before reap. No foreign member, reused identity, unstable membership failure or escalation is reported in this run.

This supports successful cleanup of the original owned group within the helper's scope. It is not a fresh post-reap process-absence scan, and escaped descendants were not inventoried. Prior supervision failures remain historical evidence; this successful run does not reinterpret them.

The retained conventional key/configuration lstat metadata is identical before and after. Neither this audit nor the helper read or hashed credential contents. The result remains a metadata-continuity check, not proof of every possible external effect.
