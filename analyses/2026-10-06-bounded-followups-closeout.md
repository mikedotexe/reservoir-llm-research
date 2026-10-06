# Bounded research follow-ups: closeout with incomplete coverage

October 6, 2026. Mike chose to finish the research loose ends, including one bounded
historical recovery of the missing S-006 records. That attempt is complete. It did
not recover the planned cohort. The two bounded extensions are now closed with
their coverage failures recorded; the broader S-006 and S-008 questions remain open.
S-009's September 17 short-output qualification was already complete and negative.

This work changes the research record and adds a separate closeout tool. It does
not change a Being, service, source repository, study schedule or S-007 ledger.
No new model call, message, induced study or daily-window capture occurred.

## S-006: one recovery, no eligible retained historical records

The [recovery addendum](../research/studies/S-006-historical-recovery-addendum.md)
was frozen at **16:59:38 UTC**, qualified against 49 fixture tests and peer-reviewed
before the single source-read attempt. It preserved the original seven-day run
intake, 48-hour follow-up and separate amended provider window. The original
collectors, protocols and evidence were not edited. The stricter wrapper enforces
40 combined claim/summary files per packet and a shared 256 MiB read budget.

The attempt finished at **17:01:41 UTC** (10:01 Pacific):

| Original observation surface | Retained recovery result |
|---|---|
| Controller run directory | Complete direct inventory of 681 names. The latest matching filename is September 17, 17:51:51.811449 UTC, before the registered 20:35:39 start. No eligible candidate receipt or episode packet was read. |
| Original provider spool | Enumeration stopped at the original 20,000-name cap. No complete inventory, dispatch, outcome or raw body was read. |
| Source-content reads | Zero bytes; the attempt read directory names and metadata only. No retry or remote fallback followed. |

The available local directory does not establish complete historical coverage of
September 17–24. Its absence of matching names cannot establish that no eligible
run occurred, and the incomplete provider inventory cannot establish zero natural
opportunities. The actual eligible-run count remains unknown; operational benefit
remains unmeasured. No episode or provider attempt is available to adjudicate.

**Disposition: closed with incomplete historical evidence.** This finishes the
bounded recovery and administrative closeout, not an empirical negative result.
It does not change the completed September 7 provenance/outcome passes or the
September 8 observer startup observation.

Private records: [recovery capture](../research/outputs/2026-10-06-bounded-followups-recovery/capture.json),
[completion receipt](../research/outputs/2026-10-06-bounded-followups-recovery/completion.json)
and [sealed inventory](../research/outputs/2026-10-06-bounded-followups-recovery/packet-manifest.json).
The capture SHA-256 is `f478f602130366418552147d48e2cd227b8227b7db5b6008d2f5341e7d749b24`.

## S-008: finish the available slice without changing selection

The [durable-correction extension](../research/studies/S-008-durable-correction-protocol.md)
keeps its two historical anchors and their different storage states. The only
accepted S-007 daily packet available inside intake is day10. Its sealed report,
successful research finalization and completed isolated replay are independently
hash-bound inputs. Day11 remains verification-blocked; subsequent daily packets
are absent. No source recovery or newly admitted daily packet is part of S-008.

Filtering day10 to the original T0 retains **294 generations**, including **281
observed notebook versions**. The original eligibility analysis returns no direct
eligible exposure for either case. It flags **14 changed-revision candidates** for
the prose-only worker claim; the saved-note comment case has none.

A [separate source-equivalence review](../research/outputs/2026-10-06-bounded-followups-source-review/source-review.json)
resolves those candidates without reading or coding their authored responses:

- The retained source pages reconstruct the old dispatcher revision `a737ea33…8992`
  (57,458 bytes) and new revision `24d8975b…5719` (60,505 bytes). Both complete
  reconstructed hashes match their recorded revisions.
- The complete 4,517-byte original anchor, `13598..18115`, occurs exactly once and
  byte-identically in the new revision at `13717..18234`.
- No candidate's delivered page contains that complete translated interval. It
  crosses the successive pages `12347..16620` and `16620..20929`. Combining separate
  exposures or shrinking the anchor would change the frozen selection rule.
- All 14 candidates are therefore ineligible under the unchanged rule. Neither case
  has a selected exposure in the supplied verified packet.

**Disposition: retained-slice assessment complete; planned-window coverage
incomplete.** The verified slice runs from September 17, 20:35:39 UTC to September
18, 18:34 UTC. Coverage after that is blocked or uncaptured through the September
26, 20:35:39 final deadline. Local correction, saved correction and later accurate
use remain unresolved. Zero eligible exposure in this slice is not evidence that
no natural correction happened during the full period.

The two bounded cases are no longer waiting for an unattended collection that was
never established. Further observation would require a separately declared study;
neither the sample nor these expired windows are extended here.

## S-009 and S-007 keep their distinct dispositions

[S-009](../research/studies/S-009-portable-reservoir-journals.md) now links its
[completed September 17 qualification](2026-09-17-short-output-qualification.md).
Two requests were made. The candidate failed the declared short-output bounds,
leaving five cells unattempted; no prompt v3 or replacement recording followed.
No new retry accompanies this documentation update. A writing-quality effect
remains unestablished.

S-007 day11 remains verification-blocked by the missing original host-release
receipt for PID 81688. No receipt hunt or repeated polling was added. Its frozen
window, first-three sample, 5,088-ID ledger and pending record are unchanged.
Later daily dates remain coverage gaps; this closeout does not fill them.

## Verification and retained identities

The frozen `probes/research_followups_closeout.py` separates one historical
`recover` from the original offline `build` and `verify`. The build labels its result as
constructed and awaiting verification. Nonzero recovered records require an
evidence-coded review; unknown schemas, altered hashes and newly eligible
exposures cannot silently become completed results. The tool follows no embedded
provenance paths during build or verification.

The 16 new fixture tests cover original windows, first-ten selection including
failures, actor exclusions, censoring, combined packet limits, unsafe paths,
one-attempt enforcement, exact source equivalence, separate-page selection,
missing coverage, accepted daily verification and relocated offline replay. They
pass alongside the 33 frozen collector tests: **49 passed**. No native source
changed in this research portion.

The built report then replayed byte-identically from copied explicit inputs and
code under an operating-system sandbox denying network access and all reads of
the original research, Astrid and Minime trees. The three original follow-up
checkpoints also replayed successfully, separately. A before/after receipt confirms
**45 original files unchanged**, including the frozen protocols/collectors,
historical daily packet manifests and S-007 ledger/pending record.

A subsequent boundary review found that the original v1 analysis reopens daily
packet files after it has cached their declared hashes. A synthetic fixture
changed and internally resealed those files between the two reads; v1 accepted
the changed report. The actual sealed closeout is unaffected: its independent
replay used static copied inputs, and the additional verification below reproduced
the same report bytes. The finding does mean that v1 build/verify is not the
supported interface for replay against a changing input tree. Its code and
historical identity remain frozen.

The supported entrypoint is now `probes/research_followups_closeout_replay.py`,
with only `build` and `verify`. It reads each declared input once through a stable
file descriptor, checks size, inode/metadata stability and its declared hash,
then copies those bytes into a private snapshot. Frozen v1 analysis sees only
that snapshot. Seven additional tests cover mutation during the initial read,
changed initial hashes, changed or removed originals after the snapshot, input
path and byte limits, changed reports, and independent verification. The full
Python suite passes **404 tests**.

The new wrapper built the same report, independently verified it, and replayed
it from relocated inputs and code with network access and the original research,
Astrid and Minime trees denied by the operating-system sandbox. A new preservation
receipt confirms the same **45 original files unchanged**, the frozen v1 code
identity unchanged, and seven old/new sealed packets intact. Historical recovery
was not repeated. The [boundary review](../research/outputs/2026-10-06-bounded-followups-snapshot-verification/boundary-review.json),
[qualification](../research/outputs/2026-10-06-bounded-followups-snapshot-verification/qualification.json),
[isolated snapshot replay](../research/outputs/2026-10-06-bounded-followups-snapshot-verification/offline-replay.json)
and [new preservation receipt](../research/outputs/2026-10-06-bounded-followups-snapshot-verification/preservation-after.json)
are sealed separately from the original closeout.

| Retained identity | SHA-256 |
|---|---|
| Explicit closeout input manifest | `78ff2f483cf9b40cac8f17e172188decb96b3ce829a63b890f1438fcfcd69c41` |
| Final closeout report | `d1bacd71728b0cb08212cf26ecc4c9742abc88401d065c6978994db92ebaea71` |
| Closeout packet manifest | `d6bcc1179e2b93aa49a2a0805d6bfd613d1f62fa7317fc8c988dcbde64a95649` |
| Snapshot verification packet manifest | `55bd149aeca76e61be5a4a4ed9135b79b31f02f780dff1d616cc1fefaf6a1857` |

Private evidence: [explicit inputs](../research/outputs/2026-10-06-bounded-followups-closeout-inputs/inputs.json),
[report](../research/outputs/2026-10-06-bounded-followups-closeout/report.json),
[isolated verification](../research/outputs/2026-10-06-bounded-followups-closeout-verification/offline-replay.json),
[original checkpoint replay](../research/outputs/2026-10-06-bounded-followups-closeout-verification/original-checkpoint-replay.json)
and [preservation receipt](../research/outputs/2026-10-06-bounded-followups-closeout-verification/preservation-after.json).
These links resolve in the private checkout, not on GitHub. Git commits and the
follow-up private backup are recorded in the separate integration account.
