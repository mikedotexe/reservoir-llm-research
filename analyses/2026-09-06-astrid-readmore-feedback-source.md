# Historical evidence after Astrid's blocked READ_MORE

The selected window is **September 6, 2026, 16:10–16:15 UTC** (09:10–09:15 Pacific).
The first READ_MORE block within that window is followed by another explicitly
linked blocked READ_MORE action. Historical prompt-budget records show that named
continuity and feedback blocks were fully removed during the interval. Saved
journal-elaboration prompts contain research-budget acceptance advice. **The exact
primary dialogue prompt was not recovered**, so these observations do not establish
whether the primary dialogue model received the guard message or how it interpreted it.

## Captured primary records

All new evidence is under
[`research/outputs/2026-09-06-astrid-readmore-feedback/source/`](../research/outputs/2026-09-06-astrid-readmore-feedback/source/).
The reproducible driver is [`probes/astrid_readmore_feedback.py`](../probes/astrid_readmore_feedback.py).
Captured versions of the driver are preserved beside the evidence; each capture
records its exact driver hash. Primary-material files use mode `0600`.

Ordinary read-only SQLite access on the configured SSH host `volya` succeeded.
The source was `/Users/v/other/astrid/capsules/spectral-bridge/workspace/bridge.db`.
No runtime code was imported, source file written, locking bypass used, or model invoked.
Data queries required an indexed `SEARCH` plan and had a five-second SQLite
progress-handler limit. Each database phase used its own read transaction.

The [schema capture](../research/outputs/2026-09-06-astrid-readmore-feedback/source/bridge-schema.json)
retains 43 table/index definitions, below its 400-row cap.
The [precise window capture](../research/outputs/2026-09-06-astrid-readmore-feedback/source/bridge-window-precise.json)
retains exact SQLite row values, their canonical JSON hashes, SQL, parameters,
plans, limits, and truncation flags. Its topic census covers 561 bridge-message
rows in six topic/direction groups. Five are `consciousness.v1.autonomous`:
three `dialogue_live` rows, one `moment_capture`, and one `mirror`.

The focal indexed queries were:

```sql
SELECT * FROM bridge_messages
WHERE topic=? AND timestamp>=? AND timestamp<?
ORDER BY timestamp,id LIMIT ?;
-- ['consciousness.v1.autonomous', 1788711000.0, 1788711300.0, 31]

SELECT * FROM action_events
WHERE action_id>=? AND action_id<? ORDER BY action_id LIMIT ?;
-- ['act_astrid_1788711000000', 'act_astrid_1788711300000', 31]
```

These return five autonomous rows and three actions without truncation. Action-ID
selection uses the ID's epoch-millisecond prefix; the payload's event clock and
the database's timestamp remain separate. The initial
[window capture](../research/outputs/2026-09-06-astrid-readmore-feedback/source/bridge-window.json)
used the abbreviated topic `autonomous`, which returned zero, and an overly broad
exclusion query capped at 100 rows. It is preserved as an initial observation;
use `bridge-window-precise.json` for the focal dialogue rows.

## The action chain and the written replies

All three action payloads say `route=research_budget_guard`, `status=blocked`,
`research_budget_v1.reason=no_active_read_only_research_budget`, `budget_id=null`,
and `would_dispatch=false`. Their suggested next action is
`EXPERIMENT_RESEARCH_BUDGET_ACCEPT latest`. These are recorded execution outcomes
and recommendations, not evidence of delivery to a subsequent model call.

| Action ID | Payload start/end UTC | Database timestamp UTC | Explicit parent |
|---|---|---|---|
| `act_astrid_1788711063109_read-more` | 16:11:03 / 16:11:03 | 16:11:03.890520 | `act_astrid_1788710620572_decay-map` |
| `act_astrid_1788711176295_read-more` | 16:12:56 / 16:12:56 | 16:12:57.237790 | `act_astrid_1788711063109_read-more` |
| `act_astrid_1788711248349_read-more` | 16:14:08 / 16:14:08 | 16:14:09.349695 | `act_astrid_1788711176295_read-more` |

All three database payload dictionaries are **exactly equal**, with zero differing
fields, to their previously captured primary action-log payloads in
[`episode-evidence.json`](../research/outputs/2026-09-06-around-0919/source/episode-evidence.json).
The nested continuity-session draft creation times are 16:11:03, 16:12:57, and
16:14:09 UTC. Those later draft clocks already exist in the log payloads; they are
not substitutions for action start time.

| Bridge message ID | Exchange | Bridge timestamp UTC | Cached journal |
|---|---:|---|---|
| 13958274 | 191005 | 16:11:01.580450 | `astrid_1788711061.txt` |
| 13958494 | 191006 | 16:12:54.869069 | `astrid_1788711174.txt` |
| 13958625 | 191007 | 16:14:06.695797 | `astrid_1788711246.txt` |

Each bridge `payload.text` occurs exactly at character offset 78 of its cached
journal original, after the journal header and before one final newline.
Re-encoding each complete cached original as UTF-8 reproduces its stored source-byte
hash. The [verification record](../research/outputs/2026-09-06-astrid-readmore-feedback/source/local-verification.json)
retains exact text hashes, source paths, offsets, prefixes, and suffixes.

These bridge payloads contain `autonomous`, `mode`, `exchange`, `journal_source`,
`text`, `spectral_state`, fill fields, and codec/mirror/semantic review objects.
They contain **no prompt, job, generation, action, emphasis, overflow, or research
guard field**. Their `journal_source` values name supplied source material, not the
output journal path. Temporal proximity between dialogue and action is therefore
kept separate from the explicit parent-action chain and exact text identities.

## Historical prompt-budget evidence

The [companion capture](../research/outputs/2026-09-06-astrid-readmore-feedback/source/historical-companions.json)
contains three exact JSONL records from
`/Users/v/other/astrid/capsules/spectral-bridge/workspace/diagnostics/dialogue_prompt_budget.jsonl`.
This file was 561,483,790 bytes and unchanged across the read. Only a 32 MiB suffix
was considered; after discarding its initial partial line, bytes
`[527934039, 561483790)` were scanned. The 1,418 parsed records had zero parse
errors; their timestamp range was `[1788485017, 1788758673]`. All suffix records
were examined without assuming chronological order. This is bounded suffix
coverage, not a whole-file absence claim.

| Diagnostic timestamp UTC | Byte offset | Continuity removed | Feedback removed | Journal retained/original | Final prompt chars |
|---|---:|---:|---:|---:|---:|
| 16:10:27 (`1788711027`) | 555871785 | 2,512 | 892 | 1,956 / 2,508 | 13,161 |
| 16:12:04 (`1788711124`) | 555895601 | 2,516 | 892 | 2,330 / 2,508 | 13,207 |
| 16:13:20 (`1788711200`) | 555919440 | 2,520 | 892 | 2,274 / 2,505 | 13,144 |

The three records are `dialogue_prompt_budget_v3`. Each reports complete removal
of the named diversity, modality, continuity, feedback, and spectral blocks, with
partial trimming of journal material. Requested and effective output budgets are
768 tokens in all three. The records contain budget summaries and diagnostic
metadata, not complete primary system/user messages or an exchange/job identifier.
The 16:12:04 record falls between the first block and the next dialogue; that
temporal relationship is not an authenticated request-to-response ID join.

Exact raw-line SHA-256 values, including the newline:

- `1788711027`: `3a84a3a3ae76c459dfd98e357183cd23c2e963ce66dc2aa518372a0328cfb4d4`
- `1788711124`: `9aa03f51495a89cc7af659d79433f0c05815e624858815239fac4ade265bdc00`
- `1788711200`: `a27a94a11551a55fb36bb0cc10269a6aaa48449f238a5c1d2dc4d19dcfe3d441`

The records name `context_overflow_1788711027.txt`, `context_overflow_1788711124.txt`,
and `context_overflow_1788711200.txt` under the workspace's `context_overflow/`.
None appears in the complete current inventory of that directory's 17 names.
This establishes their absence from that directory at capture time; no archive or
other location was searched. No exact primary dialogue generation record was
recovered. The complete 65-name workspace inventory also had no default
`generations` directory; an alternate configured location was not established.

**The block label `feedback` does not identify the research-budget guard message.**
Current source tracing by the parallel code review places guard emphasis in a
separate primary system-text channel; the named feedback block uses a different
input. Continuity may carry relevant action summaries, but its removed historical
text was not recovered. Neither the presence nor absence of the guard's exact
wording in the primary system prompt follows from these trimming records.

## Saved prompts and results in the elaboration lane

The [file inventory](../research/outputs/2026-09-06-astrid-readmore-feedback/source/prompt-file-inventory.json)
enumerated 181,890 job-directory names on the source host, without per-item metadata
reads. Enumeration completed under a five-second / 250,000-name cap. Filtering
the filename epoch-millisecond prefix to the selected five-minute window found
**six jobs**: three `witness-context` and three `journal-elaboration`.
Only those six named directories were read: `job.json`, `prompt.txt`, `result.txt`,
and `events.jsonl`, **24 files total**, each capped at 1 MiB and stable across its
read. Exact file text and byte hashes are retained in `historical-companions.json`.

Every job records `status=completed`, a summary ending `via MLX`, and null
`action_id`/`thread_id`; each also names its `exposure_record_id`. No generation
record or final adapted provider request is supplied by these job files. The
witness prompts have no literal `READ_MORE`, research-budget, or guard-emphasis
phrases in the inspected text.

The saved elaboration prompt paths share this prefix:
`/Users/v/other/astrid/capsules/spectral-bridge/workspace/llm_jobs/jobs/`.

| Job directory / prompt | Created UTC | Prompt SHA-256 |
|---|---|---|
| `job_astrid_1788711067413_journal-elaboration/prompt.txt` | 16:11:07.413 | `41590c61125ffddb60f1e98ebf86e328067d79a20a220b3f10c28a7d599b0962` |
| `job_astrid_1788711181775_journal-elaboration/prompt.txt` | 16:13:01.777 | `f02e5ae76a399f370a4d6fff6869a10b1d5bbd68fb7397442de8db982ad0c72e` |
| `job_astrid_1788711253031_journal-elaboration/prompt.txt` | 16:14:13.032 | `cc917b905933f0a5e28061e49771c6583e1b601735929c875e715ebb703351c5` |

Each prompt contains the complete corresponding bridge dialogue text verbatim
(IDs 13958274, 13958494, 13958625; character offsets 6,630, 6,661, 6,652), and the
explicit text `Suggested NEXT: EXPERIMENT_RESEARCH_BUDGET_ACCEPT latest` in a
research-budget scaffold. The first prompt was saved after the first guard block
and before the second primary dialogue. The other two follow their respective
dialogue/block pairs. This establishes saved advice in a distinct elaboration
lane; it does not establish that the next primary dialogue consumed that advice.

Each job's `result.txt` also matches a complete cached longform passage exactly:

| Job epoch-millisecond component | Longform file | Result start offset |
|---|---|---:|
| 1788711067413 | `dialogue_longform_1788711128.txt` | 431 |
| 1788711181775 | `dialogue_longform_1788711212.txt` | 466 |
| 1788711253031 | `dialogue_longform_1788711300.txt` | 511 |

The explicit wrapper is a journal header, `Signal anchor: ...`, and
`--- JOURNAL ---` followed by a newline; one newline follows each complete result.
All three full cached originals re-encode to their recorded source-byte hashes.
Thus saved prompt, saved result, and longform artifact have inspectable exact-text
links. Supplier prompt files remain distinct from a verified final adapted request.
The third longform is timestamped at the exclusive window end; it is retained here
as the selected job's result companion, not as an additional in-window writing.

## Reproduction and checks

Capture uses SSH `BatchMode=yes`, `StrictHostKeyChecking=yes`, `ConnectTimeout=5`,
and sends a self-contained Python worker through stdin. It creates no remote
script. Each output filename must be new. For example:

```sh
python3.14 -B probes/astrid_readmore_feedback.py --phase rows --out NEW-bridge-window.json
python3.14 -B probes/astrid_readmore_feedback.py --phase files --out NEW-file-inventory.json
python3.14 -B probes/astrid_readmore_feedback.py --phase companions --out NEW-companions.json
```

The four phase-specific captured driver files reproduce the versions actually
used, including the initial topic correction. Reruns observe a later source state;
they cannot recreate deleted historical overflow files. The companions phase uses
the six exact job names discovered and preserved in the file inventory.

This independent verification is entirely local:

```sh
python3.14 -B probes/astrid_readmore_feedback.py \
  --verify-dir research/outputs/2026-09-06-astrid-readmore-feedback/source \
  --episode research/outputs/2026-09-06-around-0919/report/episode.json \
  --prior-evidence research/outputs/2026-09-06-around-0919/source/episode-evidence.json
```

It verified **171 captured SQLite row instances** (including overlapping queries
and initial captures), **three exact diagnostic lines**, and **24 exact job files**;
every capture's driver hash matched a preserved driver. It also reproduced the
three action-log equalities, three dialogue-to-journal matches, and three
elaboration prompt/result/artifact links above. These are integrity and identity
checks on captured material, not external attestations of model exposure or use.

No more source reads were made after the bounded suffix and six-job capture.
