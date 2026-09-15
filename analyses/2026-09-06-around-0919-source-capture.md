# Source access for the 09:19 clock window

This note records the bounded source capture behind the [around-time reading](2026-09-06-around-0919.md). The selection was September 6, 2026, 09:19 America/Los_Angeles, with ten minutes on either side: **16:09–16:29 UTC**, epochs `[1788710940, 1788712140)`. No topic or question filter selected the window.

The reusable driver is [episode_source_capture.py](../probes/episode_source_capture.py). It sends a self-contained standard-library worker to the configured SSH host `volya` over stdin. It opens databases with ordinary `mode=ro` and streams selected primary logs on their source host. It does not import the beings' runtime, execute a requested action, create a remote script, use `immutable`/`nolock`, or copy a database.

Actual capture command, from this repository:

```sh
/opt/homebrew/bin/python3.14 probes/episode_source_capture.py \
  --at 2026-09-06T09:19:00 --timezone America/Los_Angeles \
  --before-minutes 10 --after-minutes 10 \
  --out research/outputs/2026-09-06-around-0919/source/episode-evidence.json
```

It uses `ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=yes volya`, with quoted remote arguments beginning `python3 -B - --worker`. Explicit `--since`/`--until`, `--source-host`, `--remote-base`, and bounded limits are supported. Ambiguous or nonexistent local clock times require an explicit UTC offset. Existing output paths are refused, and output cannot be inside the known sibling source trees.

## Preserved evidence

The current [episode-evidence.json](../research/outputs/2026-09-06-around-0919/source/episode-evidence.json) was captured at `2026-09-07T04:58:44.071954+00:00`. It contains **1,032 normalized records** and complete query/scan coverage metadata. Its SHA-256 is:

```text
9af075bc4e8418839e8c8c9a813e14c5995e6bad5ea9faa79d6f6c5fa81b257a
```

The exact [capturing driver](../research/outputs/2026-09-06-around-0919/source/episode_source_capture.py) is preserved beside it; SHA-256 `0dc76ee20bda9c03c8f67879b207244c1fe732ef1a4d45d599d7111182ecfc9c`. All 1,032 payload hashes were independently recomputed successfully, with no duplicate `(being, kind, source_record_id)` values. The toolkit's `read_bundle` validator accepted the bundle. Files containing primary material were created with mode `0600` under the private source directory.

The [initial bundle](../research/outputs/2026-09-06-around-0919/source/episode-evidence-initial.json) and [initial driver](../research/outputs/2026-09-06-around-0919/source/episode_source_capture-initial.py) are preserved but **superseded**. That capture used heuristic seeking in Astrid's logs, and its database availability check only opened a lazy SQLite connection. The current capture reads an actual schema row to check access and streams both selected files fully; use its coverage declarations.

## Actual source coverage

| Source | Retrieved/scanned | Selected | Scope |
|---|---:|---:|---|
| Minime `action_events` | 6 candidates | 4 actions | Indexed action-ID range with 600-second lookback |
| Minime `eigenvalue_timeline` | 507 rows | 507 observations | Indexed session-relative time range, session 5316 |
| Minime `esn_metrics` | 507 rows | 507 observations | Indexed session-relative time range, session 5316 |
| Astrid June 7 action-thread log | 36,485 rows | 7 actions | Complete unchanged captured file |
| Astrid May 8 action-thread log | 16,922 rows | 0 actions | Complete unchanged captured file |
| Astrid selected actions' `pre_state` | Above action rows | 7 observations | Partial snapshots associated with action start |

Minime source: `/Users/v/other/minime/minime_consciousness.db`. Mounted read-only access had failed; ordinary source-host access succeeded. A read transaction pins the selected SQLite snapshot. The action candidate query was:

```sql
SELECT * FROM action_events
WHERE action_id >= ? AND action_id < ? ORDER BY action_id LIMIT ?;
-- ['act_minime_1788710340000', 'act_minime_1788712140000', 1501]
```

The plan used the primary-key index. Event time comes from JSON `started_at`/`ended_at`; the SQL `timestamp` is a mirror-write time. Explicit recorded intervals overlapping the window are retained. Actions starting before 15:59 UTC, including earlier actions with an unknown completion, may be missed.

For telemetry, the driver read bounded session metadata (5,316 returned rows; limit 10,000), selecting session 5316 with `start_time=1788205897.115178`. The two table queries use their declared timestamp indexes with the relative range `[505042.8848218918, 506242.8848218918)` and `session_id=5316`, limited to 1,501 returned rows each. Wall time is the recorded session start plus the row timestamp. Exact SQL, parameters, plans, and session row are retained in the bundle. There was no row truncation. An indexed `SEARCH` plan is required for data queries, with a five-second progress-handler limit; the small session metadata query is the explicit scan exception. The bundle's SQL `rows_examined` counts retrieved candidate rows, not internal SQLite rows visited.

Astrid sources: `/Users/v/other/astrid/capsules/spectral-bridge/workspace/action_threads/threads/th_astrid_20260607_action-continuity/events.jsonl` and the corresponding `th_astrid_20260508_action-continuity/events.jsonl`. The worker scanned **505,596,712 bytes** locally on the source host, returning only selected records and coverage metadata. Both files had unchanged size and modification time across the read, zero parse errors, and complete byte-range hashes. No chronological ordering assumption was needed. Limits were 512 MiB total, 100,000 lines, 30 seconds across the log stream, and at most four thread directories. `complete_captured_file` describes each selected, unchanged file; it does not establish universal coverage of all actions or unselected threads. An actual ordinary read-only schema query on Astrid's `bridge.db` also succeeded during this capture, after earlier access failures; the action evidence remains the primary logs.

The telemetry channels retain separate names: `sensory_field_cov_lambda1` for the sensory-field covariance and `reservoir_state_cov_lambda1` for the native reservoir-state covariance. Astrid's retained action snapshots use `lambda1_ambiguous`, with unresolved metric ownership and a timestamp associated with action start rather than an independently verified measurement time. These observations do not establish what was present in a generation prompt, a particular triple-reservoir handle, or a causal relation between the beings.

## One declared preview result

The action `act_minime_1788711761487_experiment-advance` records `EXPERIMENT_ADVANCE exp_minime_20260906_legacy-self-experiment :: mode: preview`, `stage=read_only`, and `status=handled`, with explicit parent `act_minime_1788711413694_aspire`. Its generic outcome summary does not itself prove application or non-application. Two exact artifact paths declared by that event were therefore read separately over the same SSH channel, each under a 1 MiB cap. They are preserved unchanged; source size and modification time were stable during both reads:

- [Conveyor readout](../research/outputs/2026-09-06-around-0919/source/action_thread_conveyor_2026-09-06T09-22-42.882001.json), 40,654 bytes, SHA-256 `4657a3dded5fac074342f34be0d002e3382b142b538e71be2d9e97592942657f`. Top-level fields record `mode=preview`, **`applied=false`**, `preview_allowed=true`, `can_apply=true`, `apply_blocked_reason=null`, and `stage=needs_decision`. This supports the narrow reading that this recorded preview was not applied; `can_apply` is not evidence of application.
- [Action manifest](../research/outputs/2026-09-06-around-0919/source/2026-09-06T09-22-42.939916_thread_action.json), 61,972 bytes, SHA-256 `4ffbd97a5b48de75fbd4570d122fc51d72c5e8b88e19cb78914a9cd680e581b5`. Its `action_continuity.stage` is `read_only`.

[Companion provenance](../research/outputs/2026-09-06-around-0919/source/preview-artifacts-provenance.json) records exact source paths, byte hashes, size/mtime checks, and the access cap. The reads used `Path.stat()`, a symlink/size guard, `Path.read_bytes()`, and a second `stat()` in a self-contained `python3 -B -` worker; only the two explicitly named files were accessed. Companion artifact-writing times are not substituted for action times. These companions do not modify the already imported bundle. Background `live_control_changed=false` flags in metric snapshots concern those particular metric reviews and are not used as proof of this action's result or of the absence of other live activity.

## Verification

```sh
/opt/homebrew/bin/python3.14 -m unittest tests.test_episode_source_capture -v
```

Four focused tests pass: local/DST clock resolution, indexed-query truncation and scan refusal, full-log interval selection without chronological ordering, and byte/line-cap missingness. All use temporary fixtures and make no SSH calls or live source reads. Broader episode interpretation belongs to the companion reading, with provenance and coverage retained rather than filled in by proximity.
