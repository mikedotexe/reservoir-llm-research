# A deployed journal-led repair, with natural benefit still unobserved

September 7, 2026 Pacific; capture completed September 8 at 03:41 UTC.
[S-006](../research/studies/S-006-journal-to-change.md) ·
[Protocol frozen before the outcome scan](../research/studies/S-006-natural-outcome-protocol.md).

**The September 7 annotation repair can now be traced from two Astrid journals
through a qualified source change to an actual retained deployment. Its exact
before/after scanner fixes four reproduced cases. In the frozen natural-output
windows, however, we found no visible known control marker in 120 recorded
dialogue responses or 480 journal files. Most raw provider responses are not
retained, so this is an observation/coverage result, not proof that no input
opportunity occurred or that the repair improved subsequent operation.**

The bounded follow-up is complete. The broad benefit question remains open.
No live system was modified, restarted, queried to induce output or sent
research. All new probes and analysis live in this research repository.

## Which journal-led change this follows

The [first flywheel account](2026-09-07-flywheel-signal.md) established an August
Unicode delimiter repair in Git. This follow-up selects a **different, later
annotation repair** because its retained releases and activation evidence were
available. Do not combine the two repairs' test counts or deployment claims.

Astrid's [first self-study](../research/outputs/2026-09-07-flywheel/evidence-final/008.txt),
`self_study_1788800559.txt`, asks about skipped annotations, bracket boundaries
and cleanup-receipt interaction. Her
[second study](../research/outputs/2026-09-07-flywheel/evidence-final/009.txt),
`!self_study_1788815877.txt`, asks which scan wins and whether word capture
changes visibility. Their exact hashes are retained in the earlier account.
The [implementation record](../research/outputs/2026-09-07-flywheel/evidence-final/006.txt)
connects these reports to the review, corrects mistaken mechanisms, and reports
red/green tests. This was interactive, Mike-requested follow-through, **not an
unattended productive flywheel round**.

The two confirmed failure forms are a bracketed relation after an annotation,
and an annotation followed immediately by en dash, em dash or ellipsis:

```text
<end_of_turn> [sic] (appears) at the boundary
<end_of_turn> [sic]— appears at the boundary
```

The repair checks the allowlisted relation before discarding a bracketed chunk
and accepts those three additional suffix characters. It also records which
relation scan won. It does not validate every explanation in the journals.

## Deployment evidence, independently checked against retained bytes

The [activation transaction](../research/outputs/2026-09-07-flywheel-natural/capture/deployment/activation-projected.json)
records `activated_verified` at **September 7, 22:24:48.560173 UTC**. The new
process started at 22:23:26 UTC, PID 65453, replacing PID 39644. We retain a
projection excluding the unrelated signed self-control envelope, with the
original receipt hash recorded in the capture manifest.

The [release audit](../research/outputs/2026-09-07-flywheel-natural/capture/deployment/audit.json)
recomputed both binary hashes, both manifest hashes and the complete source
inventories: **556 old inputs and 557 new inputs match their retained bytes**.
After normalizing the two worktree roots, the difference is exactly:

- Changed `dialogue_runtime.rs`: marker classification and receipt construction.
- Changed `fallback_contracts.rs`: the receipt type moves into the marker module.
- Added `control_marker_annotation_tests.rs`.

There are no removed inputs or other changed input bytes. The new binary hash
is `ffe27228e6cf292f684ddc76eb9f6a1154d05a308f7b064ba665d28e6bd1e924`;
the old is `855d0c7f8972163bda3bc9e1f6e3b1758662ecda926daf28e13a1e32ccc36e17`.
Both bind to the activation receipt. HEAD alone is insufficient: both manifests
record the same Git revision plus different exact dirty-source inventories.

Two [historical stack receipts](../research/outputs/2026-09-07-flywheel-natural/capture/deployment/environment-selected.json),
at 22:17:40 and 22:25:12 UTC, record the respective stage paths, binary hashes,
process IDs and start times. The generation records in the two windows have
the matching PIDs throughout. The observed active-selection file still names
the replacement stage and transaction at capture.

This is corroborated historical deployment evidence plus independently checked
retained bytes. We did not perform a fresh host process probe or independently
rebuild the entire production binary. Manifest declarations supply the
build-to-source association; hashing verifies the bytes they identify.

## Fixed natural-output windows and results

The [protocol](../research/studies/S-006-natural-outcome-protocol.md) fixed the
windows after reading deployment metadata and before reading these outcome
records. Prior knowledge includes the earlier rollout note's absence of a
marker receipt at its initial observation point. This was not a blind selection.

Intervals are half-open and exclude the transition. The primary time is the
generation record's `created_at_unix_ms`, written at attempt completion;
journal selection uses the filename's Unix timestamp.

| Captured evidence | Before: Sep 7 20:30–22:20 UTC | After: Sep 7 22:25–Sep 8 03:30 UTC |
| --- | ---: | ---: |
| Recorded dialogue attempts / unique generation IDs | 40 / 40 | 80 / 80 |
| Saved responses with valid exact response hashes | 40 | 80 |
| Status `ok` / other observed statuses | 40 / 0 | 80 / 0 |
| Responses containing any exact known control marker | 0 | 0 |
| Journal files in the window | 144 | 336 |
| Journal files containing any exact known control marker | 0 | 0 |
| Raw provider artifacts with a unique exact-completion match | 0 | 1 |
| Cleanup diagnostic receipts in the window | 0 | 0 |

Sources: [coverage and every record locator](../research/outputs/2026-09-07-flywheel-natural/final-report/coverage.json),
[capture manifest](../research/outputs/2026-09-07-flywheel-natural/capture/manifest.json).
The post window spans 5 hours 5 minutes. These are unequal descriptive windows,
not a before/after causal rate comparison. Journals and dialogue responses can
describe the same events; their counts are not independent subjects or episodes.

Every captured attempt declares `mlx_coupled` and the configured
`mlx_profile:gemma4_12b`. Thirty-nine pre records and all eighty post records use
`dialogue_prompt_v4_own_body`; one pre record uses v3. That model field is a
profile label, not independently served-model identity for every request.
The stack receipts show the same coupled model process on both sides.

The [journal scope](../research/outputs/2026-09-07-flywheel-natural/capture/journal-scope.json)
records 4,194 root names inspected. The archive directory inventory ends on
September 5, before either window; no later archive directory was present.
All matching root journal files were captured, without keyword or flag selection.
The capture reports zero read/parse errors. These counts describe available
records; they do not prove every attempted generation was successfully recorded.

## What the records can and cannot tell us

The retained
[provider source](../research/outputs/2026-09-07-flywheel-natural/capture/source/after-provider_execution.rs)
extracts `raw_text`, normalizes it, writes a cleanup diagnostic if a report
exists, and returns normalized text. Later,
[dialogue generation](../research/outputs/2026-09-07-flywheel-natural/capture/source/after-dialogue_generation.rs)
calls that returned text `primary_raw` and supplies it to the generation
recorder. The generation record is therefore **after marker cleanup** and can
also follow other provider filtering. It is not a raw-input census.

One [accepted runtime-feedback artifact](../research/outputs/2026-09-07-flywheel-natural/capture/accepted/runtime_feedback/fa62ddd488974f42d3170171269293635c2f61c618373a2c66979fb27dbb3259.json)
retains the actual provider response body. Its filename hash matches the bytes,
and its accepted completion matches exactly one selected generation, at
23:08:32.599 UTC. It contains no known marker. The text match is an explicit
candidate association, not a recovered canonical request/attempt ID. This
selected successful-delivery mechanism does not retain every raw response.

The cleanup log contains four historical records, the latest September 3 at
10:24:55 UTC, and none in either window. The two inspected legacy attempt/request
logs end April 19; they supply **no current denominator**. No logging error was
observed in this capture, but absence from a best-effort log cannot establish
that no input opportunity existed. A silent log is consistent with no markers
being produced and with incomplete observation. This pass does not choose
between those possibilities.

Thus there is no observed eligible natural case on which to measure this patch's
retention benefit. That is not evidence of a failed repair, zero useful journal
signal, felt improvement, or comprehensive absence of the original defect.

## Exact-source and measurement verification

The [replay](../research/outputs/2026-09-07-flywheel-natural/final-report/replay.json)
uses the contiguous scanner and unchanged marker constant from each retained
release. The old full-file hash `891f76e7…de07` matches the implementation
record's pre-edit source; the new hash `03c6b6de…fa91` matches its qualified source.
Four known synthetic defects lose the marker before and preserve the exact
input after; six controls have unchanged outputs. These are targeted software
checks, not natural observations or the full historical qualification suite.

An independent [verifier](../probes/flywheel_natural_verify.py) also runs the
exact compiled replacement scanner on **all 601 retained text instances**:
120 dialogue responses, 480 complete journals, and the one raw response.
It finds zero marker occurrences and reproduces every input unchanged. This
checks the screening result without relying on the preliminary marker regex.
The raw response and its corresponding saved response overlap; 601 is an
execution count, not a sample of 601 independent events.

The final [verification receipt](../research/outputs/2026-09-07-flywheel-natural/verification.json)
checks captured-file identities, response hashes, window assignments, distinct
attempt keys, process IDs, source/manifest links, harness spans, binary hashes
and output bytes. The initial `report/` used literal Rust string escapes in
its screening vocabulary; `final-report/` decodes them. Counts were unchanged,
and the all-text Rust pass independently verifies the zero. Both runs remain
available. The protocol and captured evidence were unchanged.

```sh
/opt/homebrew/bin/python3.14 probes/flywheel_natural_capture.py --out research/outputs/new-natural-capture
/opt/homebrew/bin/python3.14 probes/flywheel_natural_report.py --capture research/outputs/new-natural-capture --out research/outputs/new-natural-report
/opt/homebrew/bin/python3.14 probes/flywheel_natural_verify.py
```

The first two commands refuse existing output directories; the last verifies
this fixed account. New capture runs observe newly available files within the
same fixed windows and should remain separate. No sibling code is imported or
executed, and no active database scan is involved.

## What should change in the measurement workflow

The [streamlining proposal's observation addendum](../proposals/2026-09-07-flywheel-evidence-and-throughput.md#natural-outcome-observation-addendum)
specifies an attempt identity carried through provider response, cleanup,
acceptance, generation and deployment evidence. A compact outcome record should
distinguish `no_eligible_opportunity`, `eligible_preserved`, `eligible_lost`,
`input_not_retained` and `recording_failed`; this account currently requires
the qualified `no_observed_opportunity / input_coverage_incomplete` outcome.

This prevents repeated broad rereading from being mistaken for measurement.
The next useful implementation is bounded, steward-only observation at the
provider boundary, followed by another prespecified natural window. The
owning-repository changes and any activation remain unimplemented here.
