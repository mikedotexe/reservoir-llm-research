# Git tidy-up and research record status · October 6

October 6, 2026. Mike asked us to survey the work here, finish loose ends and leave
the repository clean for Git. The survey ran the evening of October 5 Pacific; the
changes were made the next morning. This is a maintenance and record account, not a
new observation of either Being. No journal, study cursor, ledger, sealed packet,
live handle, deployment or installed viewer was changed, and no retained file was
deleted. Nothing here was sent to either Being.

The last commit before this pass was `622ed38` (September 19). Its tracked tree was
clean. What remained was untracked output, a research record that stopped on
September 19, and board updates that had not been mirrored.

## What changed in Git

**Two ignore decisions** (`2323f2a`, [.gitignore](../.gitignore)). Both keep files
on disk and stop them appearing as untracked.

| Ignored | Files on disk | Aggregate SHA-256, before and after |
| --- | --- | --- |
| `essentials/examples/portable/*.journals/` | 36 in seven directories; three more directories are empty | `bf3da8479b52cc3ff02d6a692b52172ef23dd41327c9555666f48bb20ce368f9` |
| `native/ReservoirScope/validation/0.12.0/`, `0.13.0/`, `0.13.1/` | 130 (21, 105 and 4) | `29f2d9ed8168b39bd7c12c220f5a6da4db2fadbdb288e9286cdef8f4d5923e73` |

The journal sidecars are written beside an output file by `essentials-run actions
--output` (`essentials/runner/Main.swift:73`). The same text, identifiers and hashes
are embedded in the tracked run JSON, and
`native/ReservoirScope/Tests/PortableStoreChecks.swift:94-98` checks replay with the
sidecar files absent. All 36 contain scripted example replies, not writing by either
Being.

The validation outputs follow the exclusion already recorded in the
[0.14 delivery account](2026-09-17-reservoir-scope-014-delivery.md): "earlier
validation outputs remain outside the reviewed commits". One 0.13.0 accessibility
capture also includes host menu content unrelated to the app, which is a further
reason to keep that directory local. Of the 130 files, 128 had been visible to Git;
two build logs already matched an existing rule.

Git does not protect ignored files. The digests above are their only binding in this
record. Nine references in four tracked documents point into these directories and
resolve only in this checkout:

- [portable lab account](2026-09-16-portable-reservoir-lab.md), lines 59, 95, 96
- [guided lab account](2026-09-16-guided-reservoir-lab.md), lines 3, 5, 7
- [active observation retry](2026-09-16-active-observation-retry.md), lines 28, 30
- `native/ReservoirScope/HANDOFF-history-through-0.13.1.md`, line 7

Those dated accounts are left as written.

**Layout guidance** (`298e927`). The "Repo layout" block in [CLAUDE.md](../CLAUDE.md)
now lists `essentials/`, `native/`, `visualizations/`, `pyproject.toml` and the
`board/*.json` payloads, and describes `analyses/` as it is used.

**Author identity.** New commits in this repository use Mike's GitHub identity through
repository-local configuration. The 36 earlier commits keep their recorded authors.
History was not rewritten: the annotated tag `reservoir-scope-v0.14.0` still resolves
to `2b4babc9e463f5bbe447c5c480a85adaebbb2232`, the commit the 0.14.0 candidate was
built from.

No file covered by the package source identity changed. The Python suite passed on
this tree: 380 tests, none skipped. No Swift build or native check was run, since no
source changed. `git gc` was not run: 73 blobs and 96 trees are unreachable and a
default collection would prune them.

## S-007 after September 19

The [day 11 account](2026-09-19-source-study-fidelity-day11.md) left the September
18–19 window retained and verification-blocked: 263 responses use Minime PID 81688,
whose historical restart or deployment receipt had not been located. Four later
rechecks exist only under ignored `research/outputs/` and were not in the tracked
record until now.

| Recheck (UTC) | Result, verbatim | Packet manifest SHA-256 |
| --- | --- | --- |
| 2026-09-20 18:44:02 | `unchanged_blocker` | `b209d768a9ce2d62d41ccf1d8ae22ec86c2495c03265a1f97cbf4047ba557b09` |
| 2026-09-21 18:43:15 | `unchanged_blocker_new_later_release_evidence` | `90eac2db89b0d97e2494a1c07e9c8948943641a74589f9fbd62665dd15f9b790` |
| 2026-09-22 18:41:10 | `unchanged_blocker_new_later_release_account` | `a06cdb688a66184055fb7f060b0bf415998a24f410111de8fffd00badf7c14ea` |
| 2026-09-23 18:40:01 | `unchanged_blocker_unrelated_release_account` | `19a4e6cead27c5373d292fb670d571768e717f60a46b47a3022c2f308ce6787b` |

All four finalization records (n = 4) read `research_verification: blocked`,
`ledger_advanced: false` and `retained_artifact_integrity: passed`. All four result
records read `new_generations_collected: 0` and `seen_generation_count: 5088`. The
ledger hash `8a3066d0…0e8a1b` and pending-window hash `8a3a8e13…182401` are the same
in all four and match the files on disk today. The last completed cutoff remains
2026-09-18T18:34:00Z.

The September 21 recheck retained a later receipt. In its words, the receipts "record
a later transition from old PID81688 to new PID18648, with successful outcome recorded
at 2026-09-20T18:37:56.943517+00:00. They do not document the original transition into
PID81688." It also notes that the later receipt gives the old process start as
September 18 17:43:12 local, while the pending target keeps the startup witness at
September 19 00:43:15Z, and that these are "not silently substituted or treated as a
proven contradiction". The September 22 and 23 rechecks retained accounts of later or
separate releases and reached the same blocked result.

Since then:

- No recheck output is retained after September 23 (n = 0 entries newer than
  September 23 12:00 Pacific).
- No daily window after the one ending September 19 18:34 UTC has been captured.
  As of this account, sixteen further windows have elapsed, those ending September
  20 through October 5 at 18:34 UTC. Under the study's own rule these are coverage
  gaps to be stated and processed separately, not merged
  ([S-007](../research/studies/S-007-source-study-fidelity.md), "If the computer
  misses a run…").
- Whether the 11:34 Pacific heartbeat is still scheduled was not determined from
  this checkout.

The four recheck packets were written after the snapshots recorded on September 17,
and no later snapshot is recorded in this repository. They are ignored by Git. The
manifest hashes in the table are their binding here.

What would resume the study is unchanged: the original restart receipt for PID 81688,
verified in a new attempt directory against the sealed day 11 inputs. Whether to keep
waiting for it is Mike's decision. Nothing is closed here.

## S-006 and S-008 after their registered boundaries

The [bounded follow-up account](2026-09-17-bounded-followups-status.md) registered a
seven-day intake ending September 24, 2026, 20:35:39 UTC and a final follow-up ending
September 26, 20:35:39 UTC. Both have passed.

Three captures are retained, all from September 17: 20:34:39 UTC (before the 20:35:39
start), 20:42:28 and 20:43:20. The latest status, at 20:43:20, reads
`future_observation_complete: false`; S-006 `run_count: 0` with the provider window
`coverage_blocked`; S-008 `eligible_exposures: 0` and `no_eligible_exposure_yet` for
both cases. That is a reading taken under eight minutes after the start. The September 17
account already says it "is not a completed negative finding", and that remains true.

The separate follow-up heartbeat was "requested but not received" on September 17. No
tracked document records a later approval. No later capture is retained, and none was made
here: a refresh reads live sources, and it would now observe after the frozen windows
closed.

S-008 may draw only on "explicitly identified, sealed and successfully
replay-verified S-007 daily research packets". Inside the intake, day 10 is the only
verified packet; day 11 is blocked and later days were not captured. No retained
capture examines day 10 for eligible exposures. S-008 is therefore unexamined, not
empty.

Neither study is closed or judged here. Their protocols define the finish: for S-006,
"an auditable bounded cohort with honest dispositions and shortfalls"; for S-008, "a
complete bounded account of these two selected cases, including unchanged accounts or
no eligible exposure". Writing those accounts, or deciding not to, is open.

## Backup

[The handoff](../native/ReservoirScope/HANDOFF.md) says a final follow-up snapshot "is
due when both bounded natural studies close". Private snapshots live on Mike's Mac;
the backup directory is absent on this one. This checkout holds no record that the
snapshot was taken, and its state could not be checked from here.

## Open work left as found

- **Geometry bookmarks.** Branch `codex/geometry-bookmarks-20260921` is at `622ed38`.
  Its separate worktree holds eight uncommitted entries from September 21: one
  modified source file and seven new files, including an inquiry note that describes
  an "implemented offline candidate; human acceptance and paired being rollout
  pending". It was not reviewed, committed or published in this pass.
- **Reservoir Scope 0.14.0.** Human newcomer acceptance is still pending
  ([current release](../research/CURRENT-RELEASE.md)).
- **Release checkouts.** Two clean detached checkouts of `2b4babc` and `99fd6f6`
  remain registered under the local cache directory.
- **Version banners.** `essentials/README.md`, `essentials/ACTIONS.md` and
  `native/ReservoirScope/docs/PORTABLE-LAB.md` still describe 0.12.0 or 0.13.0 as
  current. The
  first two are covered by the package source identity, so they wait for the next
  release.
- **Letters.** `letters/DELIVERIES.md` logs three delivered filenames whose copies in
  `letters/` carry `2026-09-07-L…` names, and three rows still read pending from
  September 7.
- **Selected study.** `research/QUESTIONS.md` names S-001 as the selected inquiry,
  `RESEARCH.md` names the self-study follow-through study, and
  [NOW](../research/NOW.md) names none.

## Hold Shelf

The board was reachable on the evening of October 5 and again on October 6: 178 cards
and 44 log entries, with the newest card update at 2026-09-08T18:53:49Z and the newest
log dated September 8. Work recorded in this repository after September 8 is not on it.

The backlog held in this repository:

- 59 tracked files carry a `Board updates pending` heading, and ten further inline
  notes say the same (70 matching lines in 65 files; one is the convention itself in
  CLAUDE.md).
- 29 `board/*-pending.json` payloads. One records `published_verified`; the other 28
  describe themselves as unpublished in six different spellings.

Two things need reconciling before any of it is mirrored. Card
`c-study-page-scope-and-coverage` is `open` in `board/astrid-study-survey-pending.json`
and `done` in `board/study-source-context-pending.json`. And three differently named
newcomer-test cards are proposed: `t-reservoir-scope-newcomer-route`,
`t-reservoir-scope-newcomer`, and a third in an ignored payload. That reconciliation
was not attempted in this pass.

## Queries and counts

Run from the repository root.

```sh
# untracked before the ignore rules: exactly ten entries, nothing else dirty
git --no-optional-locks status --porcelain=v1

# evidence digests (36 files; 130 files)
find essentials/examples/portable -path '*.journals/*' -type f -print0 \
  | sort -z | xargs -0 shasum -a 256 | shasum -a 256
find native/ReservoirScope/validation/0.12.0 native/ReservoirScope/validation/0.13.0 \
  native/ReservoirScope/validation/0.13.1 -type f -print0 \
  | sort -z | xargs -0 shasum -a 256 | shasum -a 256

# the only tracked file matching an ignore rule, before and after
git ls-files -ci --exclude-standard    # native/ReservoirScope/validation/0.7.1/build.log

# S-007 rechecks, n = 4
python3 -I -c "
import json
for d in ('20','21','22','23'):
    b = f'research/outputs/2026-09-{d}-source-study-fidelity-day11-release-recheck'
    f = json.load(open(b + '-finalization.json')); r = json.load(open(b + '/result.json'))
    print(f['checked_at'], f['result'], f['research_verification'], f['ledger_advanced'],
          f['retained_artifact_integrity'], r['new_generations_collected'],
          r['seen_generation_count'], f['packet_manifest_sha256'])"
shasum -a 256 research/outputs/source-study-fidelity-tracking.json \
  research/outputs/source-study-fidelity-pending.json

# nothing newer than the last recheck, n = 0
find research/outputs -newermt '2026-09-23 12:00' | wc -l

# follow-up captures and any recorded heartbeat approval
ls research/outputs/2026-09-17-bounded-followups
git grep -n -i heartbeat -- research analyses

# board backlog, excluding this account
git grep -n -i -E '^#{1,6} +Board updates pending' -- . | wc -l          # 59
git grep -n -i 'Board updates pending' -- . \
  ':!analyses/2026-10-06-git-tidy-and-record-status.md' | wc -l      # 70
git ls-files 'board/*-pending.json' | wc -l                        # 29

# references into the ignored validation directories, n = 9 lines in 4 files
git grep -n -E 'validation/0\.1(2\.0|3\.0|3\.1)' -- . ':!.gitignore' \
  ':!analyses/2026-10-06-git-tidy-and-record-status.md'

# Python suite, writes nothing with -B: Ran 380 tests, OK
/opt/homebrew/bin/python3.14 -B -m unittest discover -s tests

# unreachable objects a default gc would prune
git fsck --unreachable --no-reflogs | awk '{print $2}' | sort | uniq -c    # 73 blob, 96 tree
```

Board counts come from listing the `cards` and `log` collections of the Hold Shelf
artifact on October 5 and 6.
