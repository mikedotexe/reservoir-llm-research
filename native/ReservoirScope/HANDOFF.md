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
| Continue a research question | [Question library](../../research/QUESTIONS.md), owning study and [Methods](../../research/METHODS.md) |
| Reconcile coordination | [Board records](../../board/README.md); older pending payloads are historical inputs, not independent publication requests |
| Understand earlier work | [Preserved handoff](HANDOFF-history-through-0.13.1.md), [research chronology](../../RESEARCH-history-through-20261007.md) |

## Preserve the boundaries

Inventory the working tree before changes, preserve other work, review diffs and
stage explicit paths. The current integration work is local on
`codex/research-closeout`; pushing and merging are outside this pass. Preserve the
published 0.14 tag, release checkouts, candidate apps and recovery refs.

Keep private captures under ignored `research/outputs/`. A clean checkout can run
the synthetic examples; it does not contain every historical replay input.
The maintained daily package verifies explicit retained evidence without capturing
or advancing ledgers. Frozen packet code remains authoritative for its original
accounts. S-007 day11 stays parked at its original historical witness; never widen
or recollect the frozen window to get around verification.

The lab’s scripted examples, model recordings and reviewed research cases have
different evidence roles. Playback inspects saved evidence; new experiments and
model requests start explicitly. Geometry imports retain validated bytes and reading
state in the window without following embedded source paths. Software checks and
board completion do not establish human acceptance or producer interoperability.

Mike’s isolated steward-review copy is already open. Keep that copy and its identity
stable while he records his answers; [Now](../../research/NOW.md) tracks the handoff.
Do not operate the acceptance tasks on his behalf. App navigation changes follow
in a separate tranche, using his difficulties as evidence.

The [October 7 local recovery account](../../analyses/2026-10-07-local-backup-and-steward-review.md)
records a same-volume snapshot, separate restore and isolated replay for its exact
captured commit. Later documentation and attestations are outside that snapshot.
Preserve it and the [October 6 snapshot](../../analyses/2026-10-06-recovery-snapshot.md).
Independent-device availability remains unverified; Mike selected local recovery.
Restore checks deny original source paths and networking.

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
