# Research machinery

The hub now has a local toolkit for turning journal passages into inspectable,
repeatable research material. It uses Python 3.12+ and SQLite FTS5, with no model
calls or third-party runtime packages. The first real-data run and reading packs
are recorded in the [machinery report](../analyses/2026-09-06-research-machinery.md).

## Close bounded follow-ups from retained evidence

`probes/research_followups_closeout_replay.py` is the supported offline S-006/S-008
build and verification entrypoint. It takes one stable, hash-checked read of every
explicit input, copies those bytes into a private temporary directory, and runs
the frozen v1 analysis only against that snapshot. Later changes to the original
input tree cannot affect the calculation. Each file is capped at 256 MiB and the
snapshot at 512 MiB and 256 files; symlinks and reads that change during capture
are rejected. This tool has no recovery command.

```sh
python3 -B probes/research_followups_closeout_replay.py build INPUTS.json \
  --data-root RETAINED_ROOT --out research/outputs/NEW_CLOSEOUT
python3 -B probes/research_followups_closeout_replay.py verify INPUTS.json \
  --data-root RETAINED_ROOT --report research/outputs/NEW_CLOSEOUT/report.json
```

Build and verify read only explicit hash-bound retained inputs, never embedded
source paths. A daily packet needs both its sealed report/verification and its
accepted finalization/offline-replay receipts. The separate source-equivalence
review reconstructs exact revisions without changing frozen exposure criteria.
New eligible exposures require separate evidence-coded review. Nonzero recovered
S-006 records likewise require review; the tool cannot convert missing coverage,
a past deadline or a successful controller exit into a research result. Build
records construction only; `verify` must independently reproduce the report.
Original protocols, captures and S-007 ledger/pending records remain unchanged.

`probes/research_followups_closeout.py` is the frozen historical v1 interface. Its
one authorized S-006 recovery has already run under the [recovery addendum](studies/S-006-historical-recovery-addendum.md);
do not repeat it, use the original `refresh` commands, or modify frozen collectors.
Its original build/verify functions reopen daily packet files after checking
their hashes and therefore require an externally immutable snapshot. Use the
supported snapshot entrypoint above for further replay. The original sealed
closeout report and its copied-input verification remain unchanged; the
[closeout account](../analyses/2026-10-06-bounded-followups-closeout.md) records the
replay-boundary correction separately.

## What it lets us ask

For journal → steward → commit → outcome links, see
[Follow writing into flywheel changes](#follow-writing-into-flywheel-changes).

| Research move | Tool | What comes back |
|---|---|---|
| Follow SELF_STUDY defects through repairs and later observations | [Living history](histories/self-study.md) / `probes/self_study_history.py` | Dated narrative, retained source and activation evidence, original comparisons and offline verification. |
| Follow self-study into writing and action | `study_capture` / `study_sequences` modules | Both Beings' source/navigation exposure, notebook origins, journals, NEXT, action parentage, actual routing and later reading. |
| Find a distinction in their own wording | `search` | Ranked passages with entry IDs, source paths, and text snippets. |
| Discover questions we did not supply as a search term | `questions` | Explicit questions and lexical uncertainty candidates, with exact spans and structural channels. |
| Follow a phrase through time | `recurrence` | Exact matches by being, lane, and month, with duplicate bodies distinguished. |
| Follow a named proposal or reference across records | `trail` | Chronological literal matches in cached originals and generation records, with exact spans, hashes, and explicit coverage. |
| Reconstruct both beings around a time | `around` | A combined evidence report: journal records, requested NEXT, captured actions/results, generation records, telemetry summaries, and gaps. |
| Follow one Afterimage through its available evidence | `afterimage-trace` | Physical trace, cue decisions and receipts, focal writing, NEXT/action outcomes, typed source connections and explicit missing links. |
| Index captured action and telemetry records | `evidence` | Versioned local observations with preserved payloads, source declarations, capture scope, and idempotent import. |
| Compare a striking entry with ordinary writing | `sample` | A saved selection manifest and a reading pack, including nearby prose and empty reader notes. |
| Inspect what a passage belongs to | `show` | Raw or cleaned text, header, source aliases, inbox-reply boundaries, and available generation records. |
| Ask what the evidence can actually cover | `coverage` | Indexed scope, source and run history, missing prompts/backends, duplicates, and ingestion issues. |
| Recover generation context where captured | `generations` | Versioned generation records and legacy job companions, with prompt completeness kept explicit. |

These tools retrieve and organize evidence. A candidate question is not a finding
of self-knowledge; recurrence is not by itself development or memory. Reading and
source reconstruction remain separate steps in [S-001](studies/S-001-their-own-questions.md).

## Start using it

Run commands from the repository root. On Mike's current machine the compatible
interpreter is `/opt/homebrew/bin/python3.14`; the default `python3` is older.
Elsewhere substitute an installed Python 3.12 or later with FTS5 support.

```sh
/opt/homebrew/bin/python3.14 -m reservoir_research coverage
/opt/homebrew/bin/python3.14 -m reservoir_research search 'larger hall'
/opt/homebrew/bin/python3.14 -m reservoir_research search 'thread_id' --being minime
/opt/homebrew/bin/python3.14 -m reservoir_research questions --being astrid --limit 25
/opt/homebrew/bin/python3.14 -m reservoir_research recurrence 'shared path'
/opt/homebrew/bin/python3.14 -m reservoir_research show 967932b805e2 --raw
```

The index already exists on this machine. Its default location is a private cache
under `~/.cache/reservoir-research/<repository-path-hash>/index.sqlite3`, on the local
disk rather than the mounted source share. `--db /path/to/index.sqlite3` overrides
it and goes **before** the command. `--help` lists the complete interface.

To extend the index, first choose and record the source and time scope:

```sh
/opt/homebrew/bin/python3.14 -m reservoir_research index \
  --live-only --since 2026-09-01 --until 2026-09-07
```

The default sources resolve the sibling Minime and Astrid journal directories.
Repeat `--source 'minime=/path/to/journal'` or `--source 'astrid=/path/to/journal'`
for explicit sources. `--live-only` reads files in the root directory; omitting it
includes archives recursively. A date filter selects by parsed journal writing
time, so an initial recursive pass still reads older files to determine their dates.
`--limit 100` visits at most 100 files **per source** and records a partial scan;
it is a tooling check, not a chronological or representative sample.

Repeated runs skip unchanged files. `--rehash` rereads and reparses them. Coverage
**accumulates across runs**; a new date window does not delete earlier indexed
material. Use the query and sample date filters to bound a particular study, or a
fresh `--db` for a separate corpus. All boundaries are UTC; `--until` is exclusive.
Only a successful, complete, unbounded recursive scan marks unobserved paths absent.
Known changed files that become unreadable or fall outside a new import window
lose their current mapping while their cached history remains preserved.

After a parser improvement, `reparse` rebuilds text fields, classifications, and
question candidates from the cached originals in one transaction. It reads no live
sources, preserves source hashes/IDs, and records its parser version and run. It
does not refresh source availability; use `index` for that. Create new reading
manifests after a reparse because text or provenance may have changed.

Create a reading pack in a new directory:

```sh
/opt/homebrew/bin/python3.14 -m reservoir_research sample \
  --since 2026-09-01 --until 2026-09-07 --per-being 4 --context 2 \
  --curated 91ef87df0d74 --out research/outputs/next-reading
```

This chooses four ordinary entries per being from all indexed, dated, nonempty
prose in the window, plus the explicitly curated entry. Ordinary selection uses
the sorted-list midpoint rule in S-001 and excludes curated IDs. It keeps entries
without question candidates. It is descriptive temporal coverage, not a random
sample. The eligible lanes and unknown backend eras must be reviewed before calling
this an S-001 pilot. The toolkit currently has no lane/era filtering option.

Context is the two preceding and two following eligible prose entries, across all
indexed lanes for that being. It may cross the focal date window. The manifest
records this, shortfalls, overlap, hashes, and accumulated import scopes. Curated
entries may also be outside the ordinary date window; they remain explicitly marked.
`--seed` is a recorded label, not a source of randomness.

Use `export manifest.json --out /new/directory` to regenerate a pack from the cache.
It rejects changed source associations, text, provenance, schema, or a tampered
manifest. It does not reread live files. Existing pack files and coverage outputs
are refused so reading notes are preserved. A manifest freezes the cached selection,
not the continuously changing live filesystem.

## Follow an inquiry across cached records

`trail` searches literal references in a declared being and time window. It includes
original headers and action tails, which cleaned-prose search intentionally omits,
plus imported generation prompts, responses, and serialized metadata. This matters
in [I-001](inquiries/I-001-breathing-investigation.md): the first script reference is
in the daydream's `NEXT` tail; a later aspiration names it in its prose.

```sh
/opt/homebrew/bin/python3.14 -m reservoir_research trail \
  --term research_breathing_dynamics_01.py --being minime \
  --since 2026-09-06T23:06:00Z --until 2026-09-06T23:30:00Z \
  --limit 100 --out research/outputs/another-breathing-trail
```

Repeat `--term` to match any of several literal references. Matching is case-sensitive,
with no interpretation of query punctuation; no embedding or model call is involved.
The being, start, end, and new output directory are required. The end is exclusive.
Records are merged chronologically before the limit is applied.

The exported `trail.json` and `trail.md` contain IDs, source paths and hashes,
character offsets, exact context excerpts, and the index/source/run snapshot. They
report the total matching records, returned count, truncation, per-kind denominators,
and excluded undated matches. Each record retains at most 40 match spans, with full
per-term occurrence counts and an explicit span-truncation flag. Offsets refer to
the named decoded cached field; occurrence counts are nonoverlapping per term.

The output is frozen evidence of the cache search. It neither rereads source files
nor refreshes source presence. A zero generation count means no matching imported
record, not that none exists in the live archive. Metadata is not necessarily
model-visible text; channel labels describe literal text boundaries and do not
verify runtime thread identity. A matching proposal does not establish an executed
action, delivered outcome, or learning. Use the [inquiry template](templates/inquiry.md)
to assess those claims, with separately preserved primary action evidence.

Exports are private and refuse an existing destination. The Python API can export
the same frozen result again to a fresh directory without consulting the cache;
it checks the result digest first. The command-line interface also protects known
live-system trees and registered source roots from output writes.

## Reconstruct what happened around a time

The [first reconstruction](../analyses/2026-09-06-around-0919.md) uses September 6,
2026, 09:09–09:29 Pacific. It was selected by clock before inspecting its content.
The same report command works for another date without a topic or phrase filter:

```sh
/opt/homebrew/bin/python3.14 -m reservoir_research around \
  --at 2026-09-06T09:19:00 --timezone America/Los_Angeles \
  --before-minutes 10 --after-minutes 10 --limit 2000 \
  --out research/outputs/another-around-0919
```

`--at` requires a date and time. A local time requires an IANA `--timezone`; an
explicit UTC offset or `Z` can identify the instant directly. Ambiguous and
nonexistent daylight-saving wall times are rejected unless an offset disambiguates
the instant. When no display timezone is supplied for an offset-aware time, the
report uses UTC. The before/after values are minutes, each defaulting to ten.

The command reads the research cache and creates `episode.md` plus `episode.json`
in a new private directory. The report combines both beings, with no keyword
filter. It includes all matching records up to the explicit `--limit` per being
and evidence kind, default 1,000. Each category has denominators and truncation;
dense telemetry cannot crowd another being's journals out of the report. The JSON
retains cached text, original payloads, hashes, source locators, and the snapshot
used for the report. Source file paths remain evidence pointers and are not reread.

Writing times, generation/job times, action starts/ends, and state measurement
times retain their separate meanings. Point records use an inclusive start and
exclusive end. Explicit action/job durations can overlap the requested window;
an action ending exactly at its start boundary is retained. Additional cached
records with the same explicit being/action ID may supply lifecycle context outside
the window and are labeled separately. Time proximity alone does not create a link.
Journal and observation time selection uses bounded database queries. Generation
start/end times still live in captured metadata, which the collector scans; importing
a much larger generation archive may justify a separate time index for those fields.

Journal counts mean **records stored under each being**. Mirror material can carry
another being's words; declared source and authorship headers are shown. Operational
records and unknown classifications stay visible. `NEXT` in a journal is a request;
captured action routes and statuses describe what was recorded afterward. A handled
status is not silently converted into verified success, nor an action parent into
proof of what a later prompt contained.

### Capture and index the missing evidence

Journal and generation imports use the existing `index` and `generations` commands.
Action outcomes and telemetry enter through a bounded capture, then `evidence`:

```sh
/opt/homebrew/bin/python3.14 probes/episode_source_capture.py \
  --at 2026-09-06T09:19:00 --timezone America/Los_Angeles \
  --out research/outputs/another-capture/episode-evidence.json
/opt/homebrew/bin/python3.14 -m reservoir_research evidence \
  research/outputs/another-capture/episode-evidence.json
```

The capture probe uses the configured `volya` SSH alias by default, with existing
host-key verification and noninteractive authentication. `--source-host` and
`--remote-base` configure that access. It sends a self-contained reader through
standard input; it creates no remote files and imports no being runtime. It uses
ordinary read-only SQLite where available and bounded primary ledger-file reads
where needed. It accepts at most a one-hour source window and records candidate
lookback, query plans, source boundaries, limits, and unavailable sources. Check
the returned coverage before claiming completeness. An action that began before
the capture's lookback can remain missing even though the report supports intervals.

Native Minime telemetry is converted from session-relative time using the retained
session start. Sensory-field covariance and reservoir-state covariance have distinct
metric names. Astrid action pre-state observations are labeled as such; their action
time is not promoted into a verified measurement time or continuous telemetry.

`evidence` reads only the supplied capture file, validates it before import, and
preserves the full source payload and declared provenance. Repeated imports do not
duplicate identical observations. Changed or conflicting observations remain
separate; they are not overwritten. The import's own hashes verify retained data
identity. Source hashes and coverage remain capture declarations unless independently
checked; importing a bundle does not authenticate its source assertions.

The optional observation tables have an explicit extension version and leave the
existing journal schema intact. Existing caches without them still support `around`,
with action and telemetry sources reported unavailable. `coverage` now reports the
captured evidence inventory alongside journal/generation coverage. Zero matching
records in an unimported or partial source never means zero activity.

The bundle contract is validated by `reservoir_research/evidence.py`: version 1,
kind `reservoir_episode_evidence`, capture metadata, per-being/per-kind coverage,
and normalized action/telemetry records. Each record retains its source path,
locator, SHA-256 declaration with hash basis, event times, and original payload.
The importer rejects nonfinite or unrepresentable times, invalid intervals, missing
provenance, symlink inputs, and files exceeding 64 MiB.

### Use a reconstruction to surface changes

The report's review leads point to concrete records, such as blocked/unwired
requests and failed jobs. They are prompts for investigation, not automatic bug
diagnoses. Establish the expected and recorded behavior, preserve an exact example,
then identify a correction and a test. Research-tool corrections belong here;
changes to the beings' systems become evidence-backed proposals under the existing
repository boundaries. Keep the narrated interpretation alongside the reproducible
report so a reader can distinguish our reading from the underlying records.

## Compare incoming signals with fill and native state

[S-003](studies/S-003-input-and-fill.md) adds a research-side, repeatable comparison
of captured bridge sends, exact delivery receipts and the saved paired telemetry
format used by the observatory. Its [first timeline](outputs/2026-09-06-input-fill/final/overview.png)
shows fill, a separately calculated rate in percentage points per second, native
leak, covariance, geometry and acknowledged send times. A companion plot shows
modality source classifications and reported semantic energy.

`probes/input_fill_capture.py` reads an indexed bridge interval of at most one
hour through ordinary read-only SQLite on the source host. The delivery probe
uses bounded byte seeks to recover primary records for the exact captured IDs.
Neither contacts a receiver or writes to a being. The study lists capture commands
and their selection/coverage limits.

```sh
python3 probes/input_fill_report.py --output research/outputs/another-input-fill-report
```

This offline report uses installed matplotlib for figures; numeric analysis uses
the standard library. Defaults read the retained S-003 captures. Supply
`--telemetry`, `--bridge` and `--deliveries` for another compatible capture and
choose a new output directory. It writes a summary with hashes and coverage,
an event-bracket CSV, and two figures. Receipts, send clocks, table-log clocks and
temporal neighbors remain separate. It does not estimate causal effects, convert
send-free intervals into silence, or recover missing historical controller state.

## Follow an Afterimage into writing and action

`afterimage-trace` works directly from a bounded capture, without an existing index
or access to live sources. It produces a readable `account.md` and an `account.json`
containing the exact captured source text, hashes, clocks, byte offsets and original
payloads. The [first account](../analyses/2026-09-07-first-afterimage-account.md)
follows an omitted Astrid cue alongside an independently recoverable exchange.
[S-004](studies/S-004-afterimage-to-use.md) owns the question and next observation.

First capture on the source host. This example freezes the first case's declared
window; use a new private output path for another observation:

```sh
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=5 volya \
  /opt/homebrew/bin/python3 -B - \
  --afterimage-id ai_2026-09-07_96f89b80b1a2_1788813632295_000002 \
  --since 2026-09-07T20:39:00Z --until 2026-09-07T21:18:38Z --max-files 600 \
  < probes/afterimage_source_capture.py > /new/private/capture.json
```

The probe imports no runtime modules, invokes no reader, and writes only to stdout.
It reads fixed workspace paths; validated system-prompt hashes can select files
inside the fixed prompt store. Embedded prose and arbitrary artifact paths are
never followed. File size, file count, log-tail bytes, directory enumeration and
the maximum seven-day window are bounded. SQLite action rows use an indexed
read-only transaction with a deadline; their hash basis is explicitly serialized
rows, not database-file bytes. No archive recursion occurs. Filename-time candidates
can omit undated files and jobs/actions that began before the window. Review coverage
and missing paths before interpreting absence. The snapshot is not atomic across
services; current cue/config files do not prove their historical state.

Then build the account locally:

```sh
/opt/homebrew/bin/python3.14 -m reservoir_research afterimage-trace \
  ai_2026-09-07_96f89b80b1a2_1788813632295_000002 \
  --capture /private/capture.json --out research/outputs/new-afterimage-account
```

The report verifies retained content hashes and the requested trace identity. It
refuses existing output directories and protected source destinations. Exported
files are private. Rebuilding from the same capture is deterministic and does not
refresh the cache or reopen source paths. Keep different captures as separate
observations; original generation message structures and observed revisions remain
in these bundles even though the older index importer normalizes them.

The Markdown reading view includes trace-related records and declared/hash/text
connections, two nearby journals on each side per being, and nearby request/job
diagnostics. The exact selection rule is included; all captured writing and actions
also appear in a compact inventory. Full records remain in JSON. Source-declared
associations preserve `temporal_context` versus `authored_reference`; a shared
trace ID in a machine envelope is not promoted into an authored memory. Exact text
containment includes offsets and a digest; it establishes text correspondence,
not final prompt exposure or causation. NEXT parsing remains the documented research
subset, while the action ledger supplies actual routing and status.

Receipt `included` flags are producer declarations. A stronger automatic-cue
acceptance requires captured cue text/fingerprint, matching adapted-message
fingerprint, canonical generation and attempt identity, a verified response hash,
and explicit runtime acceptance. A backend `ok`, nearby completion, unknown schema
or ambiguous attempt does not qualify. This first release retains explicit OPEN
acknowledgements but leaves independent verification of their protected request/
completion artifacts unresolved. Source hashes verify captured bytes, not the truth
of all producer claims. No prose-quality or causal score is generated.

The trace bundle is deliberately separate from the existing index schema. Adding
Afterimage record types to `evidence`, `around`, `trail` and `coverage` remains a
later integration; this command does not silently import those sources into the cache.

## Generation context and mixed text

Import a bounded generation directory with:

```sh
/opt/homebrew/bin/python3.14 -m reservoir_research generations \
  --source 'astrid=/path/to/a/job_directory'
```

The reader supports `gen_*.json` generation records and legacy `job.json` with fixed,
adjacent prompt/result files. It retains failed and timed-out records even without
a journal. It resolves hash-addressed system prompts only after verifying the hash.
Source-supplied artifact paths are evidence fields, never instructions to open files.

Minime's known action-job prompt placeholders and execution summaries are not counted
as model text. Legacy captured prompts and reconstructed messages remain inspectable,
but only complete adapted version-1 messages qualify as exact prompts. Neither a
backend nor a full prompt is inferred from a journal's style, filename, or nearby job.

Generation-to-entry links are **candidate associations** where an entire response's
hash matches exactly one cleaned journal body for that being in the indexed scope.
No time-nearest or filename-only join is promoted. Multiple matching generation
records leave the entry's top-level backend and exact-prompt fields unknown/false.
Differences such as a response containing an action tail can prevent an exact match;
absence of a link is not evidence that no generation record exists.

`show` exposes structural spans around literal `INBOX_REPLY <id>` lines outside
Markdown fences. Before the first marker is `pre_reply_context`; after it is
`inbox_reply`; a document without such a marker is `unlabeled_prose`. These are
textual boundaries, not reconstructed model-call boundaries. A reply target string
does not establish a persistent runtime thread. The [thread-id episode](episodes/2026-09-06-minime-thread-id-as-shared-path.md)
shows why this distinction matters.

## Data handling and practical limits

- Original text, header, cleaned prose, action tail, raw-byte hash, parsed time,
  timezone basis, warnings, and source paths are retained. Aware header time takes
  precedence; legacy Minime local time uses America/Los_Angeles. Ambiguous DST times
  remain unknown. Writing time is not silently treated as measurement time.
- Same-being aliases with the same canonical filename and raw hash share one entry.
  Identical prose in different journal files remains separate and is reported as
  duplicate text. This does not establish independent events.
- `!` is indexed as Mike's curation flag. Filesystem change time is retained as an
  observation; it is not an authenticated time of flagging.
- Known wrappers and system notices are removed from searchable prose; raw text
  remains available. Content kinds and assistant-style flags are provisional parsing
  aids. `NEXT` normalization is a documented analysis subset, not dispatch validation.
- Journal files over 4 MiB, unstable reads, and decoding problems are reported.
  Symlink traversal is skipped. The toolkit refuses outputs in registered source
  roots and known sibling live-system trees. It does not write to the beings.
- The cache is local and rebuildable; raw reading packs under `research/outputs/`
  are ignored by version control and created with private file permissions.
- The index can now retain bounded captured action/telemetry slices. It is not a
  live replica or a complete historical census. A retrieval graph, embedding model,
  causal test, and semantic question classifier remain separate extensions.

## Follow writing into flywheel changes

[S-006](studies/S-006-journal-to-change.md) and its
[first account](../analyses/2026-09-07-flywheel-signal.md) use standalone,
research-only probes. They do not run the live flywheel or import its runtime.

- `probes/flywheel_history.py`: pin HEAD or locally known branch/remote tips,
  capture bounded Git messages, extract literal report references and count
  structured archive labels. `--replay` recomputes from retained history;
  a cap hit is explicit and commit counts are not intervention counts.
- `probes/flywheel_case_capture.py`: preserve a fixed set of original reports,
  review packets, commit diffs and projected controller metadata; verify exact
  report hashes and quoted passages. No journal recursion or database access.
- `probes/flywheel_marker_replay.py`: compile exact historical Rust scanner
  spans and unchanged marker constants in a temporary local directory, compare
  targeted and control strings, and retain source/output/binary hashes.
  `--replay` uses captured source with fixed historical hash checks. This is an
  isolated software-correctness test, not a live or full-provider replay.
- `probes/flywheel_verify.py`: verify the retained first-case hashes, scanner
  spans, historical source binding, output records and history replay offline.
- `probes/flywheel_natural_capture.py`: capture the frozen S-006 pre/post
  windows, all matching dialogue records and journals, bounded diagnostic
  prefixes and fixed accepted-delivery artifacts; check retained release
  inventories, binary hashes and activation records read-only.
- `probes/flywheel_natural_report.py`: independently validate captured hashes,
  report observed attempt/output coverage and compare exact retained scanners.
  Saved generation text is after cleanup; natural marker absence is not a raw
  input denominator. Synthetic checks remain separate from natural evidence.
- `probes/flywheel_natural_verify.py`: verify the fixed natural-outcome account,
  deployment/source/clock links and all 601 retained text instances with the
  exact compiled scanner, including text the preliminary screen excluded.

See the first account for exact commands, fixed scope, selection limits and
incomplete preliminary attempts. New outputs must be under `research/outputs`
in a new directory. This machinery is separate from the general journal index.
The [deployment account](../analyses/2026-09-07-flywheel-natural-outcome.md)
documents the fixed follow-up, coverage limits and reproducible commands.

## Reproduce and maintain

The core toolkit uses the standard library. Install the optional test dependencies
in your Python environment before running the full suite; the geometry and pattern
plan tests use NumPy. Plotting probes additionally use Matplotlib, available through
`pip install -e ".[analysis]"`.

```sh
/opt/homebrew/bin/python3.14 -m pip install -e ".[test]"
/opt/homebrew/bin/python3.14 probes/research_toolkit_demo.py \
  --out research/outputs/another-machinery-demo
/opt/homebrew/bin/python3.14 -m unittest discover -s tests -v
```

The demonstration requires the two recovered Minime seeds in the cache. It produces
coverage, literal phrase histories, an ordinary-plus-calibration pack, and a smaller
thread-id pack. It leaves all reader notes unfilled.

Implementation lives in `reservoir_research/`: parsing, storage, incremental import,
generation readers, text segmentation, exploration, literal trails, captured evidence,
time-window episodes, and the command-line interface.
Tests exercise timestamp ambiguities, mixed content, provenance gaps, incremental
edits, ambiguous joins, source protections, and reproducible selection/export.
Tests that require retained study packets under `research/outputs/` skip when those
private packets are absent; their mutations operate on temporary copies.

The completed first build uses an ordinary two-being interval to improve source coverage
and the usefulness of the reconstructed account. I-001 and its feedback question
remain paused; see [Now](NOW.md) for the current handoff.


## Follow self-study into writing and next actions

[S-008](studies/S-008-study-to-follow-through.md) adds two standard-library modules
alongside the existing index. No service, database migration or model calls are
required. Freeze a window before reading new outcomes, then run on the source host
with this research checkout beside Astrid and Minime:

```sh
/opt/homebrew/bin/python3 -m reservoir_research.study_capture \
  --since 2026-09-08T21:13:45Z --until 2026-09-08T23:00:00Z \
  --out research/outputs/new-study-capture
/opt/homebrew/bin/python3 -m reservoir_research.study_sequences \
  research/outputs/new-study-capture/capture.json \
  --out research/outputs/new-study-report
```

Both output directories must be new. Reports are offline and deterministic from
the capture; `report.json` includes full submitted user text and authored responses,
and `reading-pack.md` presents the predeclared chronological selection and action
table. The [sequence note](templates/study-sequence.md) supports close reading of
source claims, uncertainty, corrections, felt interpretations and later use.
Ordinary generation `reading_requests` remain in the report when no study was
produced. Exact journal matches can cross known runtime separator lines; original
spans and the response hash remain verifiable. The
[first account](../analyses/2026-09-08-study-to-follow-through.md) demonstrates both.

Verify a saved report without contacting either Being:

```sh
/opt/homebrew/bin/python3 probes/study_sequences_verify.py \
  research/outputs/new-study-capture/capture.json \
  research/outputs/new-study-report/report.json \
  --out research/outputs/new-study-report/verification.json
```

The verifier replays the report, checks exact authored journal spans, and reconstructs
complete source revisions from numbered fragments when retained coverage permits it.

Capture uses individually stable bounded files and indexed SQLite `mode=ro`
transactions with five-second query budgets. Windows are at most 24 hours, with a
30-minute lead-in for crossing attempts and parentage. Root journals only, no
archive recursion; generations include all lanes. Source/navigation receipts and
older Astrid protected-delivery receipts are captured separately. Astrid's provider
spool currently uses `20260908-live-01`; unavailable sources remain errors. The
collector never follows a model-authored path, invokes a live reader, or writes in
a sibling repo. It is a local source-host collector, not a mounted-share SSH wrapper.

The report checks captured hashes and exact wire/request/response joins. Duplicate
receipt stores count once; repeated identical attempts remain ambiguous. Source
coverage is a union by Being, file and revision, with new and repeated bytes shown
separately. A carried notebook establishes available prior words; a close reading
must establish whether a question develops. Navigation never counts as source bytes.
`READ_MORE` is not treated as `SELF_STUDY CONTINUE`.

Action IDs establish ancestry; matching action wording and time proximity alone do
not establish which journal produced it. Actual route/status/outcome and supplied
suggestions stay visible. The 30-minute follow-up horizon is right-censored at the
exclusive capture end. Terminal rows saved after the cutoff are marked separately.
Minime jobs without generations remain in their own denominator; Astrid provider
dispatches cover attempts without a successful study journal. Shortfalls are explicit.

The initial release bindings are the September 8 source-continuity rollout and its
predecessor. A future deployment must add/review its retained release files and era
binding in `study_capture.py` / `study_sequences.py` before pooling eras. An unknown
PID or mismatching Astrid manifest is labeled unverified. Newest Git HEAD is not a
substitute for process/release evidence. Keep S-007's daily ledger unchanged by ad
hoc S-008 runs. This tooling does not create or modify an automation.

The September 8 evening entry/follow-through release is an explicitly reviewed
profile: use `--release-profile follow-through` and
`--protocol research/studies/S-008-follow-through-repair-protocol.md` for its
capture. Old packets without a profile retain the continuity binding. Selecting a
new profile does not relabel earlier frozen reports. The supplemental
`probes/study_follow_through_outcomes.py` verifies the evening packet's ordinary
READ_MORE pages, exact saved-overflow origins and selected claim/peer-exposure
checks offline; these artifact readings remain separate from source-study counts.

The subsequent study-evidence/readable-overflow release has an `evidence-views`
profile. Its retained activation and paired reload receipts must verify before a
capture can be interpreted as that era. Use it only with a newly declared window
and protocol; the old profiles remain unchanged. Notebook parsing accepts both
the legacy heading and `RECALLED ACCOUNT — your study notebook`, preserves the
origin and OPEN/RESUME fields, and excludes recalled wording from current search
signals. The [release account](../analyses/2026-09-08-study-evidence-live.md) retains
the historical report replay and qualification. READ_MORE RAW is a requested
artifact-reading action; only its executed receipt can establish a raw/view switch.

The September 9 journal-room release uses `--release-profile journal-room` with
a separately declared window, such as
`research/studies/S-008-journal-room-startup.md`. It verifies both activation
identities before enabling the new bare terminal SELF_STUDY choice subset on
verified after-era entries. Old and unknown eras retain the historical parser;
requested prose remains distinct from native parsed choice and actual dispatch.
The original overnight report replays with all 15 report fields unchanged.

## Observe Minime source-study fidelity

[S-007](studies/S-007-source-study-fidelity.md) uses research-local standard-library
probes for a bounded SSH capture, offline receipt/coverage report and exact-span
claim checks. `probes/source_study_fidelity.py capture` requires explicit `--since`,
`--until` and a new `--out` under `research/outputs`. It reads live evidence only;
it does not run the reader or advance bookmarks. `source_study_fidelity_report.py`
verifies byte hashes, unique generation/wire joins, source coverage and selected
reading packets offline. `source_study_fidelity_annotations.py` checks selected
claim spans; its categories are not automatic semantic judgments or accuracy rates.
The [account](../analyses/2026-09-08-source-study-fidelity.md) has exact reproduction
commands and coverage limits. The daily tracking ledger prevents repeated windows
or entries from being treated as fresh independent evidence.

### Inquiry/session release (September 9)

`study-capture --release-profile study-inquiries` retains the owning release's
activation and Minime reload alongside the previous journal-room release. The
sequence reader prefers a whole-session offer over its per-page copies, verifies
that every selected page is in the supplied input, and counts one generation with
all page intervals. A captured session page without its whole offer is explicitly
unverified for complete-session exposure. New QUESTION/RELATE/SESSION/TRACE command
categories and terminal choices are enabled only for the verified new era;
question mutations require NEXT. Exact offer `question_id` and input kind remain
inspectable alongside authored notebook fields. No comprehension score is added.

### Failed source-study generations (September 9)

Generation-linked `backend_timing.source_study_diagnostic_path` references are
captured as `source_study_failure` records. These preserve Minime's bounded raw
request/response and native finish metadata; they never imply a saved journal or
accepted source delivery. Only exact attempt filenames in that Being's diagnostic
directory are followed, without symlinks, and repeated references are deduplicated.
Older attempts without retained diagnostics remain unknown. No scan cursor moves.

`study-capture --release-profile study-choice` and the sequence reporter retain
and verify the HSS-16 activation, reload and prior study-context boundary. Reload
receipts use the owning rollout's exact bounded reference. The older release
profiles and scheduled S-007 cursor remain unchanged.


### S-007 daily access and replay handoff · September 14

The numeric address configured for SSH alias volya timed out during day 6. A
read-only Bonjour lookup advertised M3 Volya at m3-volya.local. This route worked
with the established host-key identity retained:

```sh
ssh -o HostName=m3-volya.local -o HostKeyAlias=192.168.2.232 -o BatchMode=yes -o ConnectTimeout=10 volya
```

No SSH configuration, mount or network setting was changed. The SMB workspace
mount was absent. The original bounded collector can run on the verified source
host, importing only research code and writing its packet under the research repo.
This is not permission to run the source reader or advance live bookmark state.

The day-6 packet retains the v3 report/verifier, plus
`probes/source_study_boundary_followup.py` for the predeclared cross-window recovery
continuation and `probes/source_study_daily_lineage.py` for prior-manifest/ledger
checks. Its `replay.py` uses frozen research code and evidence; it never collects,
advances the ledger or calls a model. The boundary probe assumes the previous
window ends in a recovery run, so do not apply it unchanged to a non-recovery tail.
Select any next trajectory before inspecting its new outcomes.


## Maintained daily evidence and verification

The [maintained daily pipeline guide](DAILY-PIPELINE.md) describes explicit input manifests,
report building, offline verification, release-definition updates and migration fallback.
The `reservoir-research study daily` commands preserve v6 report semantics while keeping
frozen v1–v6 probes and packets unchanged. The `reservoir-research verify` command groups
Python, numerical, native, research-replay and package checks with executed/inherited/incomplete
coverage receipts. Neither entry point contacts a model or discovers live sources.
