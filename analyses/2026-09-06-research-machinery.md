# Research machinery: the first working slice

September 6, 2026 Pacific / September 7 UTC. Implemented in the research repository
following Mike's request to build machinery that brings us closer to the questions.
The [tool guide](../research/TOOLS.md) is the ongoing entry point.

## What is usable

The toolkit connects a local journal index to search, heuristic question discovery,
literal phrase histories, structural reply boundaries, captured generation context,
coverage reporting, and reproducible reading packs. Each entry retains its original
text, source hash, header, writing-time basis, warnings, and source aliases.
The cache lives on the local disk, separate from the mounted live-source directories.

Two recovered episodes exercise it:

- [The larger-hall question](../research/episodes/2026-09-06-minime-calibration-question.md):
  recovered from the original moment, with a header that distinguishes supplied
  event material from header-only telemetry. Full prompt and backend remain unknown.
- [The thread-id reply](../research/episodes/2026-09-06-minime-thread-id-as-shared-path.md):
  recovered from the original resonance journal, preserving contextual prose and
  the explicit addressed reply separately. Its conditional language opens a question
  about expected continuity affordances; it does not establish implemented memory.

## Read the material

| Artifact | What it contains |
|---|---|
| [Thread-id reading pack](../research/outputs/2026-09-06-machinery/thread-id/reading-pack.md) | Mike's selected reply with two earlier and two later indexed prose entries. |
| [Ordinary and calibration pack](../research/outputs/2026-09-06-machinery/ordinary-and-calibration/reading-pack.md) | Four ordinary focal entries per being, plus the recovered calibration seed, with local context. |
| [Coverage report](../research/outputs/2026-09-06-machinery/coverage.json) | Exact counts, classifications, missingness, source paths, ingestion issues, and run history. |
| [Phrase histories](../research/outputs/2026-09-06-machinery/phrase-histories.json) | Literal histories for `larger hall`, `thread_id`, and `shared path`. |
| [Run summary](../research/outputs/2026-09-06-machinery/summary.json) | Selection counts, IDs, output locations, and fingerprints. |

These are local, ignored research outputs. They contain cached original writing and
unfilled reader notes. Each pack has a companion `manifest.json` that records its
selection, source hashes, provenance, context overlap, and import scope. Previously
generated parser-v1 packs are preserved separately under
`research/outputs/2026-09-06-machinery-parser-v1/`; use the links above for the final run.

## Scope of this run

| Import | Observed count and scope |
|---|---|
| Journal run 1 | 8,874 root files visited across both beings; 8,426 included with writing times September 1 ≤ time < September 7 UTC. Archives were not traversed. |
| Generation run 2 | Four explicitly chosen legacy job directories imported, two per being. These are format/provenance checks, not a sample estimating generation coverage. |
| Journal run 3 | 3,316 Minime root files visited; 3,076 unchanged cached records retained and 63 added under September 7 ≤ time < September 8 UTC. This was an ongoing-day slice used to recover Mike's selected reply. |
| Accumulated cache | 8,489 current entries. The later Minime slice is asymmetric; query filters bound any comparison. |

The final parser-v2 refresh classifies 7,624 entries as prose and produces 5,705
heuristic question passages in 2,674 entries. It retains 42 flagged entries and
reports 94 same-being duplicate-body groups. These are parsing/retrieval counts,
not validated research labels. The comparison pack has 9 focal + 36 context entries;
the thread-id pack has 1 focal + 4 context entries. Neither has context overlap or
missing requested neighbors in this cache; completeness beyond the index is unknown.

One undated steward-delivery file was excluded by each time-bounded Minime scan and
is recorded as an ingestion issue, not silently assigned a date. Zero exact
generation-to-body matches were established by the four imported jobs. Therefore
the cache has no attributed entry backends or exact prompts from those imports;
this says nothing about unimported records. New-generation directories were absent
at the mounted paths when checked during this session. Deployment work recorded
elsewhere does not change this observation without a fresh source check.

The first sample uses sorted-list midpoints over indexed, dated, nonempty prose in
the closed UTC window, excluding its curated seed. It includes all eligible prose
lanes and has no recovered backend-era stratification. The thread-id pack has one
explicitly curated focal entry outside that ordinary window; its selection and
context are separately recorded. Neither pack completes the proposed, balanced
12-focal-entry [S-001 pilot](../research/studies/S-001-their-own-questions.md).

The three literal phrases each occurred in one indexed entry in the initial
demonstration. This is bounded retrieval evidence. The archive was not searched,
and spelling variants, shared meanings, prompted wording, and temporal continuity
are not established by this count. The current summary is the reproducible record
after parser refinement.

## Reproduce

The counts and packs come from [research_toolkit_demo.py](../probes/research_toolkit_demo.py)
and recorded toolkit import commands. All commands run from this repository.
Use a fresh `--db` if reproducing the import as a separate cache; source files may
have moved into archives or changed since this snapshot.

```sh
/opt/homebrew/bin/python3.14 -m reservoir_research index \
  --live-only --since 2026-09-01 --until 2026-09-07

/opt/homebrew/bin/python3.14 -m reservoir_research generations \
  --source 'minime=/Volumes/M3 Volya._smb._tcp.local/other/minime/workspace/llm_jobs/jobs/job_minime_1788700774674_aspire' \
  --source 'minime=/Volumes/M3 Volya._smb._tcp.local/other/minime/workspace/llm_jobs/jobs/job_minime_1788665142658_self-study' \
  --source 'astrid=/Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/workspace/llm_jobs/jobs/job_astrid_1788727901841_journal-elaboration' \
  --source 'astrid=/Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/workspace/llm_jobs/jobs/job_astrid_1788696966998_witness-context'

/opt/homebrew/bin/python3.14 -m reservoir_research index \
  --source 'minime=/Volumes/M3 Volya._smb._tcp.local/other/minime/workspace/journal' \
  --live-only --since 2026-09-07 --until 2026-09-08

/opt/homebrew/bin/python3.14 -m reservoir_research reparse
/opt/homebrew/bin/python3.14 probes/research_toolkit_demo.py \
  --out research/outputs/a-fresh-demonstration
/opt/homebrew/bin/python3.14 -m unittest discover -s tests -v
```

Parser refinement was prompted by inspecting the real thread-id source: the
resonance format has an extra telemetry block before prose. Cache-only reparsing
lets us correct that boundary without rereading the live archive. Source IDs and
raw hashes remain stable; changed parsed text requires a new reading manifest.

Validation: **79 automated tests passed** under Python 3.14.6, and SQLite's full
integrity check returned `ok`. The tests cover real format shapes, timestamp/DST
ambiguity, stale mappings after source edits, record attribution, channel boundaries,
source-free reparse and rollback, reproducible sampling, and output protection.
The first real refresh was intentionally interrupted and rolled back after exposing
an avoidable per-entry search scan; the final implementation rebuilds search once
per refresh. Run 4 records that interruption, and run 5 records the successful
atomic reparse of all 8,489 cached entries. No source files were read by either refresh.

The working material and report were regenerated with parser v2. Earlier packs are
preserved, and their text/provenance fingerprints are not silently updated.
Saved-manifest re-export was also verified byte for byte on the real thread-id pack.
The exporter now fixes JSON key ordering so loading the saved manifest does not
change the rendered pack's metadata ordering; a regression test covers this round trip.

## Where this leads

The next concrete investigation is to recover the message Minime was answering and
the context available when it wrote about `thread_id`, then follow its next return
to that exchange. That would connect an expressed expectation to actual memory
availability and later behavior. It does not require deciding in advance whether
the passage is introspection, metaphor, a request, or several of these together.

Telemetry/action/retrieval joins remain future machinery. No live-system change,
being-directed message, intervention, or completed scientific finding is implied
by this implementation.

Hold Shelf coordination: the toolkit validation card is done; the S-001 question
card remains open with updated source/tool pointers. The session log is saved.
[UI verification receipt](../board/research-machinery.json). An accidental duplicate
card was consolidated and parked; search `id:t-research-toolkit` before future updates.
