# S-006 · One bounded historical recovery before closeout

Frozen October 6, 2026, 16:59:38 UTC, before source contents are read. Mike chose
one bounded recovery of the missing S-006 records. This addendum does not restart
the study, change its selection, authorize another intervention or inspect S-007.
The original [consecutive-review protocol](S-006-consecutive-review-protocol.md)
and provider-only amendment remain unchanged.

The executable [recovery plan](../outputs/2026-10-06-bounded-followups-preparation/recovery-plan.json)
has SHA-256 `2608ae691ab774c128ec7e29a9044ac77803cd33a58a1a566d65dd81b952952e`.
Its qualification passed 49 fixture tests, including the 33 original collector
tests and 16 closeout tests. The plan binds exact collector and test identities.
The [preservation inventory](../outputs/2026-10-06-bounded-followups-preparation/preservation-before.json)
binds 45 original files, including protocols, collectors, packet manifests and
the S-007 ledger/pending record, before this work.

## Unchanged observation clocks

| Frame | UTC interval |
|---|---|
| Consecutive run starts | September 17, 20:35:39 inclusive to September 24, 20:35:39 exclusive |
| Each selected run's follow-up | Its start plus 48 hours, never beyond September 26, 20:35:39 |
| Provider dispatch starts | September 17, 20:43:05 inclusive to September 18, 20:43:05 exclusive |
| Provider outcome allowance ends | September 18, 20:45:05 exclusive |

Select the first ten chronological runs with actor `claude-heartbeat` and adapter
`subprocess`. Failures, cancellations, incomplete and no-input runs remain eligible.
Other actors remain separate. Do not replace a selected run because its packet is
missing. Preserve collection time separately from these historical event clocks.

## Exact source scope and bounds

All paths are under the already declared local `/Users/v/other/astrid` tree:

- Direct controller receipts in `capsules/spectral-bridge/workspace/diagnostics/steward_control_v1/runs`.
- Direct `docs/steward-notes/claude-heartbeat_<unix>_<name>` directories in the original interval;
  a `verification_receipt.json` must link a selected controller run before packet files are read.
- The seven originally allowed packet files, plus at most **40 combined** JSON/Markdown
  files in direct `claims/` and `summaries/` directories. Exact original introspection
  reports are read only when an admitted read manifest names their allowed path and hash.
- Original provider spool `capsules/spectral-bridge/workspace/provider_observations/20260908-live-01`:
  direct matching event files and exact hash-addressed raw references only.

Keep the original 20,000-name and ten-second directory caps, 8 MiB file cap,
256 KiB provider raw cap, 5,000 retained-dispatch cap and 150 seconds per collector.
The two collectors share a 256 MiB read budget. Refuse symlinks, path escapes,
unknown schemas, hash/identity mismatches and unstable reads. Source credentials
remain omitted from retained controller/JSON projections; original hashes remain.

One output directory and an exclusive start record prevent repeating this plan.
Unavailable or capped sources end with explicit gaps. No remote fallback, replacement
spool, larger limit, repeat outcome collection, source command, database access,
service operation, source write or message is permitted.

## Interpretation and finish

Late terminal receipts remain censored. Undated packet assertions, file modification
time, filename dates and present-day source state cannot establish an on-time outcome.
Complete enumeration of this local directory does not establish that no historical
files were removed or that the local copy covers the whole observation period.

Seal the recovery before interpretation. The separate offline closeout accepts explicit
hashed inputs and retains reviewer disposition, response, commit, activation and benefit
as distinct evidence stages. Any recovered episode requires evidence-coded review.
If the original cohort cannot be reconstructed, finish with **incomplete historical
evidence**, not a zero-run, zero-opportunity or benefit claim. Broad S-006 questions
remain open. S-007 and all existing schedules remain unchanged.
