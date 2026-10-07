# Continuing the research work

Start with root [AGENTS.md](../../AGENTS.md) and [CLAUDE.md](../../CLAUDE.md), then
[the findings hub](../../RESEARCH.md) and [Now](../../research/NOW.md).
The [current-release page](../../research/CURRENT-RELEASE.md) owns app identity,
qualification and acceptance status. Use links to those living pages instead of
copying their version numbers or board totals here.

## Choose the route

| Task | Start here |
|---|---|
| Learn or reproduce the reading tools | [Synthetic CLI quickstart](../../research/QUICKSTART.md), then [Tools](../../research/TOOLS.md) |
| Build the app or run numerical experiments | [Native build guide](README.md), [headless runner](../../essentials/runner/README.md) |
| Review the product | [Guided tour](docs/GUIDED-TOUR.md), [participant worksheet](docs/NEWCOMER-WORKSHEET.md), [geometry supplement](docs/GEOMETRY-ACCEPTANCE-WORKSHEET.md) |
| Inspect reviewed evidence | The direct Research cases workspace: choose a question, then use the [case’s embedded evidence links](docs/GUIDED-TOUR.md#reviewed-research-cases) |
| Continue a research question | [Question library](../../research/QUESTIONS.md), owning study and [Methods](../../research/METHODS.md) |
| Reconcile coordination | [Board records](../../board/README.md); older pending payloads are historical inputs, not independent publication requests |
| Understand earlier work | [Preserved handoff](HANDOFF-history-through-0.13.1.md), [research chronology](../../RESEARCH-history-through-20261007.md) |

## Preserve the boundaries

Inventory the working tree before changes, preserve other work, review diffs and
stage explicit paths. The integration was merged into `main` and published on
October 7 at `41438da`; [Now](../../research/NOW.md) owns the current integration
status. App release publication remains separate. Preserve the published 0.14 tag,
release checkouts, candidate apps and recovery refs.

Keep private captures under ignored `research/outputs/`. A clean checkout can run
the synthetic examples; it does not contain every historical replay input.
The maintained daily package verifies explicit retained evidence without capturing
or advancing ledgers. Frozen packet code remains authoritative for its original
accounts. S-007 day11 stays parked at its original historical witness; never widen
or recollect the frozen window to get around verification.

The lab’s scripted examples, model recordings and reviewed research cases have
different evidence roles. Playback inspects saved evidence; new experiments and
model requests start explicitly. The qualified tranches 3–4 candidate adds direct
Guided tour, Experiments, Research cases, Geometry bookmarks and Observatory routes;
separate Continue and playback controls; question-led case browsing; and an explicitly
synthetic geometry example. Cases open read-only into the current window, retaining
the selected case and verified embedded evidence across navigation. Geometry retains
its packet and reading state there too. Neither route follows historical source paths
or creates a library copy; Import experiment does keep a verified local copy.
Software checks and board completion do not establish human acceptance or producer
interoperability.

The separate **0.15.0 build 21** candidate passed the Python suite, focused native
checks, package verification and actual-app navigation/evidence walkthrough.
Use [Current release](../../research/CURRENT-RELEASE.md) for the exact identity and
check scope, and the [dated account](../../analyses/2026-10-07-lab-navigation-and-evidence.md)
for receipts and per-width UI coverage. These are scoped results, not a new
all-native or all-offline aggregate.

Mike’s isolated **build 20** steward-review copy was opened at task A. Answers and
acceptance remain pending. Keep that copy and its identity stable while he records
his answers; [Now](../../research/NOW.md) tracks the handoff. The build 21 work does
not replace that session. Do not operate the acceptance tasks on his behalf.

The later [readiness and recovery account](../../analyses/2026-10-07-final-readiness-and-recovery.md)
records verified same-volume repository and build 21 archives/restores at source
commit `a73b6dc`. Ten absolute aliases from failed check harnesses were normalized
only in the archival view, with their original targets retained. Historical replay
passed eleven daily/weekly windows, three bounded checkpoints and closeout; day11
kept its expected refusal and unchanged ledger. A restored Python run exposed a
host-dependent test. Its narrow repair passes all 406 tests in a new restored
checkout, together with the synthetic CLI, packaged app and scripted runner checks.
The test repair is recovered from a named-ref Git bundle. Use the standalone
receipts in the dated account for later documentation recovery and publication.
Networking and original paths are denied during restore checks.
Preserve the [earlier October 7 snapshot](../../analyses/2026-10-07-local-backup-and-steward-review.md)
and [October 6 snapshot](../../analyses/2026-10-06-recovery-snapshot.md).
Independent-device availability remains unverified; Mike selected local recovery.
Historical replay checks deny original source paths and networking.

Do not change the Beings, their services or their self-study schedule from this
research project. Implementation, deployment and demonstrated benefit stay distinct.

## Existing host access

The established canonical checkout is `/Users/v/other/reservoir-llm-research` on
`volya`; an SMB alias may be unavailable. When access to that host is needed, the
existing trusted-key route is:

```sh
ssh -o HostName=m3-volya.local -o HostKeyAlias=192.168.2.232 -o BatchMode=yes -o ConnectTimeout=10 volya
```

This is an access reference, not a prerequisite for the offline examples or
permission to change a live system. No host connection is needed for this tranche.
