# Direct lab navigation and offline evidence first use

October 7, 2026 · product-review tranches 3–4 · research-local implementation

Mike asked us to proceed with the remaining product priorities. This pass makes
existing work easier to find and inspect. It selects no new discovery study,
collects no new Being evidence and changes no interpretation in the two retained
reviewed cases. The earlier [documentation and quickstart tranches](2026-10-07-product-navigation-tranches.md)
remain their own dated account.

## The product change

Five direct destinations replace nested navigation: Guided tour, Experiments,
Research cases, Geometry bookmarks and Observatory. New experiments do not start
when a destination is selected. Leaving their workspace pauses ongoing work.

Continue is the prominent guided action. Optional saved-record controls live in
an initially collapsed Playback controls disclosure; collapsing it pauses playback.
Open recording inspects a file, while Runs & examples → Import experiment verifies
and saves a Library copy. Existing experiment controls remain available.

Research cases lead with the existing question, then the reviewed account and its
embedded evidence. The window owns verified cases and selection across navigation.
Opening a replacement runs off the main UI thread; cancellation, rejection and
superseded completion preserve the prior valid cases. Bundled and opened identifiers
have separate namespaces. A later window requires reopening the file.

Geometry offers Load synthetic example using the exact retained Minime fixture.
The visible label says its text and coordinates are invented. The schema owner is
not an attribution to a Being. Loading uses the existing validator and establishes
synthetic origin only after success. Failed or missing resources preserve the prior
packet, selection, frame and origin. Neither case nor geometry opening saves a
Library copy or follows historical source paths.

The geometry fixture SHA-256 remains
`25ecc19605ee1bed307735f52668b817a854af98239018e74072c17ffbe92abc`;
the reviewed-case catalog SHA-256 remains
`3998951c6eaa4f414ff7ce0cef643f19078001e47c980be521255175743d0652`.
No fixture, reviewed claim, dated study, frozen protocol or research ledger was
rewritten to support this product change.

## Review and verification

The implementation received independent source review. Review caught a synchronous
case-load regression and corrected it with cancellable background verification.
It also corrected misleading start-button wording and preserved the prepared
experiment’s readiness status when leaving the guide.

The Python suite passed 405 tests. Focused checks passed 26 case-workspace assertions,
96 geometry import assertions, 13 synthetic-origin assertions and 14 mounted geometry
lifecycle assertions. Twelve geometry views cover the empty view and five records
at 1100×820 and 1380×820. The guided mounted/model harness passed 16 checks at both
widths with zero experiment starts and record writes; it does not press actual app
buttons. Its initial failed development attempts are retained separately.

Source staging passed 16 checks after an explicit local SDK selection. The first
SDK lookup failure remains recorded. Per-command DEVELOPER_DIR and SDKROOT selected
Xcode’s macOS 26.2 SDK without changing global settings. Disk availability fluctuated
during qualification; existing candidates, snapshots and evidence were preserved.

The fresh build and package verification passed with 180 source inputs, 44 resource
entries, 22 recorded examples and two reviewed cases. Additional checks passed:
67 action lifecycle, 37 guided-lesson, 47 readiness/research-case and 13 synthetic
package-identity checks. Readiness uses mocked transport. This is scoped
qualification, not a new all-native or all-offline aggregate. The guided mounted
harness used the retained earlier core; all 16 compiled core sources and toolchain
settings match the fresh build, while archive bytes differ. Its receipt states that
boundary rather than claiming a fresh execution against the new archive.

The actual app walkthrough used a separate ProductChecks copy with isolated
preferences and Library. The Mac was briefly locked; Mike unlocked it before
interaction resumed. A clipboard timeout in a file dialog was resolved by setting
the visible path field; no product validation failure was suppressed.

| Content size | Actual app coverage |
|---|---|
| 1100×820 | All five direct destinations; Continue to 12, Step to 13, Play then collapse-to-pause; E’s journal saved at 30 and return first applied at 31; Try an experiment prepared without starting. Case selection, embedded evidence, cancel, invalid replacement, verified opening and selection retained across navigation. All five geometry records, frame scrubbing, coordinate disclosure, cancel/rejection retention, successful packet replacement and bundled-origin labeling. |
| 1380×820 | Guided, case and geometry visual checks; case selection and geometry cursor retained across navigation; geometry scrubbing, cancel, rejection and successful packet opening. Library import cancel, case rejection with the correct route, one verified saved experiment and direct case navigation; Open recording; all three experiment destinations remained paused or at their initial state. |

Screenshots are 1100×852 and 1380×852 including the 32-pixel title bar. Independent
review found no blocking clipping, overlap or readability defect in the wider case
and guided views. The mounted geometry renders cover all five records at both
widths; the actual wide walkthrough does not repeat every compact record selection.

Sandbox controls confirmed networking and original repository/cache reads were
denied (EPERM). After the walkthrough the private Library contained exactly one
file: the explicitly imported recording, byte-identical to its input. Case and
geometry opening and direct recording viewing added no further saved files.
The new and old review executable hashes remained unchanged.

Private logs and receipts are under
`research/outputs/2026-10-07-lab-navigation/`, with separate focused geometry,
case-workspace and guided-playback directories. `candidate-identity.json`,
`package-verification/verification.json`, `qa-boundary-receipt.json`,
`ui-observations-final.json` and `screenshots.json` bind the final package and UI
observations. Source-staging and compiler checks use the explicit SDK settings above;
the root package group's host SDK metadata lookup reports unavailable, while its
sealed package verification passes and the package retains its build toolchain.

## Candidate and coordination

The source implementation is in local commits `faebed3` (synthetic geometry) and
`8e84742` (navigation, cases and guided controls). The candidate’s exact source commit
is `8e8474217f2ab9328f5a12c242af5b9893732ed6`; its executable SHA-256 is
`5900a5b9cf11cc613e0511adda63d6d3d9897920ce786c831dc275e81a1ee259`.
It remains at:

```text
/Users/v/.cache/reservoir-research/product-navigation-20261007/current/Reservoir Scope.app
```

The separate test copy is under
`~/Library/Application Support/Reservoir Research/ProductChecks/2026-10-07-build21/`.
It is software QA, not a participant session; its blank human worksheet stays blank.

The [reconciliation manifest](../board/2026-10-07-lab-navigation.json) covers one
completed work card and one dated log. Existing cards and logs, including human
review and the parked day11 blocker, are preserved. Before and exact editor/full
readbacks remain private; the repeat reconciliation proposes zero writes. Final
verification receipts bind these observations and source hashes. No push or merge
was performed.

## Preserved boundaries

The new source belongs to Unreleased 0.15.0 build 21. Build 20, Mike’s isolated
unfinished review copy and the published 0.14 tag remain separate and unchanged.
Agent software checks are not human acceptance. No fresh model request, producer
activation, sibling-system edit or Being-side rollout was performed.

S-007 day11 stays parked at its missing historical release witness; its window and
5,088-ID ledger remain unchanged. The S-006 and S-008 bounded closeouts and S-009
negative qualification remain complete with their recorded limits.

The [October 7 local recovery snapshot](2026-10-07-local-backup-and-steward-review.md)
covers its recorded earlier commit. This new source, candidate and attestation
postdate it; that snapshot’s recovery result does not cover them. Preserve both
same-volume recovery copies. Independent-device backup remains unverified.
