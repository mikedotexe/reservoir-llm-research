# Hold Shelf reconciliation — October 6

Status: **published and verified: 286 cards, 108 logs, overall closeout done;
repeat reconciliation requires zero writes**.
Mike selected the full local mirror backlog for reconciliation. The root session
owns the authenticated board and publication receipts. This account distinguishes
historical work, present card status, and the later act of mirroring it.

The reviewed [manifest](../board/2026-10-06-reconciliation.json) records every source
hash, pending section, canonical operation, alias and existing live match. Its
generation 8 contains 114 source rows: 29 pending JSON payloads, the ignored guided
release payload, 60 pending sections and ten inline notices, plus 14 dated
completion, qualification, recovery and coordination sources. The section total is
the original 59 plus the integrated geometry inquiry. Repeated notices map to the
same canonical records rather than creating another task.

The historical plan comprised 104 new cards, 61 new historical log entries,
six existing-card updates and 13 no-ops. Generation 3
changed one already-created card to an explicit correction update, with its former
desired fields retained in the revision event. Generation 4 prepared the two
completed bounded follow-up extensions and their October 6 log. Generation 5 made
reviewed local geometry integration publishable while holding overall closeout for
the actual snapshot/restore result. Generation 6 records that pre-snapshot boundary.
Generation 7 prepared the later final update and dated log only after isolated
replay passed. Generation 8 binds their actual publication and readback. Manifest action
counts describe intended operations, not a running count of outstanding writes.
The initial DOM inventory retains 178 cards and 45 logs; the root session separately
saved and read back its active closeout card.

The historical publication was reloaded and independently checked against
generation 3: **283 cards, 106 logs; all 184 ready operations verified; zero required
DOM writes**. All original 178 cards and 45 logs remain, including unchanged fields
on unrelated cards. The [after-reload inventory](../research/outputs/2026-10-06-board-reconciliation/historical-after-reload.json),
[operation receipts](../research/outputs/2026-10-06-board-reconciliation/historical-publication-attempts.json),
[explicit correction](../research/outputs/2026-10-06-board-reconciliation/historical-publication-correction.json)
and [independent DOM check](../research/outputs/2026-10-06-board-reconciliation/historical-dom-check.json)
are retained privately. The check binds manifest SHA-256
`2e40d6a1af404b698bb727e768232a1a9c7da9fd33f96c5bf60122edc4c4d53d`
and readback SHA-256
`17b702185c5d1b360431220a7bdfd4ab8ff425cd49b43297291dfd72f4c79411`.
This result covers visible fields; editor-only source verification is recorded
separately and is not inferred from the DOM.

The later [read-only editor pass](../research/outputs/2026-10-06-board-reconciliation/historical-and-bounded-editor-readbacks.json)
was independently compared to generation 4: **112 changed cards match all eight
editor fields exactly, including source; zero required editor writes**. The
[editor check](../research/outputs/2026-10-06-board-reconciliation/historical-and-bounded-editor-check.json)
retains one historical source-witness limitation: the reading/letter/return card's
first saved editor value and publisher preservation note exist, but its separate
pre-update source value was not retained. No previous source value is invented.
Other original-card updates have their pre-update editor source witnesses; the
new cards match their explicit intended source. Thirteen no-op records were not
edited. The two bounded cards and log have their own
[publication receipt](../research/outputs/2026-10-06-board-reconciliation/bounded-publication.json).

The final pre-snapshot [reloaded inventory](../research/outputs/2026-10-06-board-reconciliation/pre-snapshot-after-reload.json)
contains **286 cards and 107 logs**. The [DOM comparison](../research/outputs/2026-10-06-board-reconciliation/pre-snapshot-dom-check.json)
verifies all **188 ready operations**, and the [exact editor comparison](../research/outputs/2026-10-06-board-reconciliation/pre-snapshot-editor-check.json)
verifies **113 changed cards** against the [read-only editor pass](../research/outputs/2026-10-06-board-reconciliation/pre-snapshot-editor-readbacks.json).
Both checks require **zero writes**. The geometry card's
[publication receipt](../research/outputs/2026-10-06-board-reconciliation/geometry-publication.json)
is retained, and its separate [actual-app UI receipt](../research/outputs/2026-10-06-geometry-ui/ui-receipt.json)
records passed import, cancellation, rejection, selection, scrubbing and view-return
checks at the two measured content sizes. The [final companion receipt](../research/outputs/2026-10-06-geometry-ui/final-ui-receipt.json)
identifies the corrected compact and wide proof images. Human acceptance remains separate.

The [compact backlog mirror](../board/2026-10-06-reconciled-backlog.json) records all
190 canonical records' actual observed states and binds the complete private
inventory and editor readback. It shows the overall closeout card as **done**.
The pre-snapshot mirror and prepared generation 7 remain retained privately;
the snapshot itself contains generation 6 and the then-active card's mirror.
Unrelated original board records remain in the private complete inventory. The
[board overview](../board/README.md) points future work to the reconciled state so
historical pending filenames do not trigger duplicate publication.

## Final recovery attestation and repeat reconciliation

The [final publication receipt](../research/outputs/2026-10-06-board-reconciliation/final-closeout-publication.json)
records the existing closeout-card update and one new dated recovery/integration
log, completed at **17:52:52 UTC**. Its original evidence pointers, including
`research/NOW.md`, and actual editor source were preserved. No second closeout card
was created. The [reloaded full inventory](../research/outputs/2026-10-06-board-reconciliation/final-after-reload.json)
contains **286 cards and 108 logs**. The independent [DOM check](../research/outputs/2026-10-06-board-reconciliation/final-dom-check.json)
passes all **190 operations** and preserves every original card and log. The
[editor check](../research/outputs/2026-10-06-board-reconciliation/final-editor-check.json)
passes **114 changed cards** with exact editable fields and sources. Its
[readback file](../research/outputs/2026-10-06-board-reconciliation/final-editor-readbacks.json)
combines the prior 113 editor observations with the new final card observation;
it does not imply that all editors were reopened after the last save. Both repeat
checks require **zero writes**. The [final board screenshot](../research/outputs/2026-10-06-board-reconciliation/final-board-proof.jpg)
is a supplementary visual record of the saved done card.

The [recovery account](2026-10-06-recovery-snapshot.md) owns the exact snapshot,
restore and replay results: clean commit `d47a866192eafe0da803f62acd6e20f1a16dfffc`,
23,492 files and 8,757,769,076 bytes, eleven historical daily/weekly replays, three
bounded checkpoints and the safe closeout. Day11's expected refusal and unchanged
5,088-ID ledger remain explicit. The first denied scratch-write attempt and the
qualified external relocation adapter are retained; the frozen code and archive
and restore inventories were not changed. The final card and log also retain the
native aggregate's one watermark failure and the unchanged strict rerun's pass.
Neither outcome is rewritten as an all-checks-passed aggregate.

## Decisions that prevent false closure or duplicated work

- `c-study-page-scope-and-coverage` takes the later supported **done** state from
  the September 15 source-context account. Its earlier open proposal remains
  historical evidence; natural understanding benefit remains unestablished.
- The three newcomer aliases resolve to `t-reservoir-scope-newcomer`. It remains
  **open**. Neither agent checks nor prepared worksheets count as a participant
  session, and this repository closeout does not perform acceptance.
- `anemone-pending.json` is already published and verified: its nine cards and log
  match existing records and require no write. The resolved Afterimage assessment
  likewise stays with its existing completed card and log.
- The original `t-source-study-fidelity` remains **done**. Day11's missing historical
  host-release witness is recorded separately as **parked**, with the frozen window,
  first-three selection and 5,088-ID ledger preserved.
- The input-delivery-ledger proposal joins the already completed observatory
  telemetry/input-lineage proposal; it does not create another open copy or infer
  producer implementation. Existing prompt/backend instrumentation completions and
  the observatory completion also remain intact.
- The September 16 product-review proposals link to their later guided/replay
  implementation. Proposal, isolated qualification, historical rollout, natural
  exposure, comprehension and human acceptance remain different claims.
- Completed negative model qualifications stay complete. The manifest does not
  request new generations, promote prompt changes, or execute proposed choices.
- The initial active-input fixture's unavailable model preparation is qualified
  by the later September 16 partial retry. The already-published card receives one
  explicit correction update, not a duplicate. Neither scripted transport nor the
  failed 60-step model recording is a completed controlled model comparison.
- The S-006 and S-008 cards use **done** for the explicitly titled frozen
  extensions and administrative closeout. Both bodies retain incomplete historical
  coverage and open broader research questions. Neither is an empirical negative
  result or a claim of operational benefit, durable correction or full observation.

Pending files sometimes contain earlier fields such as `in_progress`, “awaiting
receipt,” or “experiment not run” alongside later completed accounts. The manifest
uses the supported terminal account rather than blindly replaying field order.
Historical event logs retain their dates; publication timestamps belong in the
new receipts. Original pending payloads and dated accounts are preserved unchanged.

## Publication and verification contract

The board's DOM exposes title, tags, evidence, status, lane, being, body and displayed
date. It does **not** expose database IDs, creation timestamps or the source field.
Every `database_id` in the manifest is therefore null. Existing records are matched
by a unique `id:` tag or exact title; logs use dated titles. Before each update the
publisher must inspect the editor, preserve its actual source and unrelated fields,
and stop to reconcile any drift from the retained initial observation. A null
`desired.source` on an update means preserve the editor value, not clear it.

No records are deleted. The six historical existing-card updates retain the original body and
append the relevant historical qualification, union evidence/tags, and preserve
completion status. Logs are append-only; existing logs are not replaced. Each save
must be reloaded and read back, including editor-only fields, with operation identity,
desired/readback hashes and actual publication time retained privately under
`research/outputs/2026-10-06-board-reconciliation/`.

The [one-off preparation/check script](../probes/board_reconciliation_20261006.py)
reads only retained metadata and repository accounts and never contacts the board,
models or live sources. It validates unique desired identities, complete source
dispositions, explicit source handling, and absence of ambiguous initial matches.
Earlier prepared manifests are retained privately before replacement. Preparation
refuses to overwrite the post-snapshot generation; the readback/editor checks and
mirror command remain available.

The snapshot used two phases. The source/research/reconciliation commit retained
overall completion as held. The local archive and isolated restore bind that exact
commit. The later verified outcome released the final done update and log. This
recovery/board attestation is a later Git record, outside the snapshot; the archive
is not claimed to include its own subsequent verification or board attestation.

After root publication, the read-only check is:

```sh
python3 -B probes/board_reconciliation_20261006.py --check-readback \
  research/outputs/2026-10-06-board-reconciliation/final-after-reload.json

python3 -B probes/board_reconciliation_20261006.py --check-editors \
  research/outputs/2026-10-06-board-reconciliation/final-editor-readbacks.json
```

It requires one visible-field match per ready operation and preservation of
all original 178 cards and 45 log entries, including unchanged unrelated card
fields. Rendered body whitespace is normalized because the DOM collapses it;
exact editor text remains in the operation receipts. Zero required DOM writes is the repeat-pass
criterion. Hidden source-field equality still requires the publisher's editor
receipts; a DOM-only pass cannot establish it. Unknown save outcomes must be read
back before retrying a create.

## Boundaries

Preparation changes no live Being, research ledger, schedule, frozen packet or
release tag. The 0.14 candidate and its pending acceptance remain unchanged. The
bounded research closure and geometry integration use their retained October 6
accounts. The snapshot, separate restore and isolated replay passed within their
documented scope. The local snapshot is a same-volume recovery copy; independently
located backup and Mike's old backup availability remain unverified.
