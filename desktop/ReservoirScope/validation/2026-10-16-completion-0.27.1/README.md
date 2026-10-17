# Settled-limit presentation and source save point

**October 16, 2026, Pacific · 0.27.1 · scoped checks complete**

The user selected a small completion-message polish, qualification, then a commit
and push of this save point. The previous
[four-journal 0.27 workflow](../2026-10-16-journal-flow-0.27.0/README.md) remains an
independent completed real-model check. No model request or Being access occurred
in this patch tranche.

## Change and review

My reservoir treats `budgetReached` as settled only when it has no pending writing,
save or application, no retry/skip action, no active worker, and equal live and
durable numerical steps. Such a session retains **Run limit reached**, adds
**Saved entries remain available to read and export**, uses normal status styling
and leaves Writing and feedback collapsed without a review-needed suffix.

Every unresolved dimension still gets attention. The existing provider/save/storage
and interruption alerts and remedies are unchanged. Historical diagnostics stay in
Session messages. A storage-headroom hold can also be settled; the neutral limit
label deliberately avoids claiming that every originally planned entry completed.

An independent source review found no blocker. The change touches one presentation
component, its focused tests, and five version/lock files with six 0.27.0→0.27.1
substitutions. It changes no public API, numerical mechanism, prompt or persistence
contract. New tests cover the observable warning/open-state distinction rather than
changing or interpreting journal content.

## Executed qualification

| Check | Evidence | Scope |
| --- | --- | --- |
| Frontend | [Source checks](source-checks-01.json), [test log](frontend-01.log) | 497 tests in 53 files pass, including eight unresolved-limit cases and existing failure/recovery cases |
| Production frontend | [Build log](frontend-build-01.log) | TypeScript and Vite pass; the existing large-chunk warning remains |
| Frozen reference | [Reference log](reference-01.log) | 180 sources, 43 resources and one fixture verified |
| Backend reuse | [Identity binding](backend-reuse-01.json) | 357 tracked core/backend/activation inputs match `4a46c38`, except three exact application-version substitutions; prior qualification reused, not rerun |
| macOS package | [Build receipt](package-build-01.json), [log](package-build-01.log) | Standard Apple-silicon app builds successfully; all 516 tracked tested inputs remain unchanged |
| Artifact | [Package identity](package-identity-01.json) | Pinned copy and archive have 137 exact files; local ad-hoc signature verifies; no notarization claim |
| Actual app | [Plan](ui-plan-01.json), [launch](ui-launch-01.json), [observations](native-ui-01.json) | One scripted entry at 30, first applied at 31; natural limit with calm status and collapsed feedback disclosure |
| Read-only replay | [Replay receipt](replay-01.json) | New seven-file scripted bundle and earlier 25-file four-journal real-model bundle verify with all bytes unchanged |

The package executable SHA-256 is
`9c019150078771cd4c7a5ad40c56a06864d5970a8bd50929db77ce30d88f0e66`.
The archive and pinned app stay outside Git; their exact paths and checksums are
in the identity receipt. The package was built from the tested source snapshot
with parent `4a46c386c7e424f9502b20fc55182ecc757f436a`; the subsequent source
checkpoint carries those same implementation files and the evidence.
The final [preservation check](preservation-01.json) confirms all 516 tested inputs,
137 pinned package files, the archive, both replay bundles and the prior 34-file
journal-flow account remain unchanged before publication.

## Actual-app observation

An exclusive Library under `target/qa/0.27.1-completion-ui01` was empty at launch.
The ordinary offline writing source remained selected. Native controls set the
frozen bounds: seed 20260909, every 30 steps, 100-ms requested pace, maximum 31
steps/one attempt, 60 seconds and 16 MiB. Create prepared step zero; Start was
separate. No local model service was started.

At the observed 1280×860 outer window and default zoom, session
`sustained-1792217539631-1` reached live/saved step 31 with one saved scripted entry,
first applied at 31. The manifest records 3,753 ms of elapsed time. The normal green
status showed the new guidance. Writing and feedback stayed collapsed with no
review-needed suffix; Resume/Pause were disabled and export was enabled. The
journal stayed readable beside the current fill display. Export execution and
unresolved-state native walkthroughs were not repeated; source tests cover the
warning conditions in this patch.

Native Command-Q exited owned PID 15206 normally. No later computer-use call
reopened it. The same exact binary then verified both bundles without model contact.
The scripted response has `requestStarted: false`; its recorded application is
30→31. The earlier real-model journals were neither regenerated nor altered.
An exact copy of the owned app-run evidence is retained in ignored
`research/outputs/2026-10-16-completion-0.27.1/app-run`.

## Package and acceptance limits

This is the **standard** configuration build. Its 137-file inventory differs from
the 138-file private candidate 04 by the optional
`examples/activation-preview-v1.json`: the unchanged private-preview overlay adds
that historical collection, while the standard configuration does not. The
standard app still offers the collection-opening control; clearer availability is
an inherited packaging/UI follow-up, not repaired in this small patch. No private
preview replacement or full feature parity is claimed for this archive.

The retained 0.27.0 private candidate and its receipts remain intact. The new patch
does not inherit transferred-opening, fresh standalone preparation, compact-screen,
export/recovery, real-model endurance or collaborator acceptance from that package.
No Windows/Linux, GPU/power or sleep/wake qualification was performed.

## Preservation and publication scope

[Publication preparation](publication-preparation-01.json) reviews the preceding
34-file journal-flow account and copies the 14 earlier 0.25 preparation files into
this worktree. The twelve non-Markdown files remain byte-exact; only the two copied
closeout links are made relative, with exact original Markdown preserved under
`pre-portability/`. Original worktree files remain intact. The old four checkpoint-
wording corrections are reconciled in the current living documents.

This checkpoint includes the small UI patch, its scoped qualification, the completed
0.27 journal-flow evidence and preserved 0.25 preparation. Private raw bundles,
models, runtimes and app archives remain ignored. Publish only the named
`codex/activation-loop` branch; do not move the existing private-preview tag or
change the 0.25 branch. Source publication is separate from delivering a new app
to a collaborator. The next release gate remains an uncoached newcomer session.

The staged whitespace check reports only trailing blank lines in the exact captured
frontend-test and package-build logs. Those outputs are preserved; checking with
only that warning disabled passes.
