# Final readiness and local recovery — October 7

The product and integration review found the research routes, current claim
boundaries and build 21 app ready for named-branch publication. This pass closes
the remaining recovery gap and a test portability defect found by the restore.
Human acceptance, merging, a released 0.15 package and Being-side rollout remain
separate. Mike's build 20 review copy and S-007 day11's historical-witness blocker
are unchanged.

## Review and one concrete repair

Three independent reviews covered the research entry routes and preserved histories,
the new native app behavior, and outgoing Git content. The Git review inspected
84 outgoing paths and 138 blob versions through `a73b6dc`: no credentials or accidentally tracked
private captures, databases, app bundles or validation screenshots were found.
Historical material already on published main was distinguished from new content.
The native review found no further defects in cancellation, stale-result protection,
navigation pause behavior, synthetic origin or input rejection.

The first restored Python run exercised 405 tests and failed one retained framing
input test. The frozen verifier followed a historical absolute predecessor path;
the sandbox correctly denied it. The failure is preserved. Commit `a4eedd7` changes
only `tests/test_study_question_framing_review.py`: an exact twenty-input mapping
checks the unchanged declared hashes before invoking the original verifier. The
regression rejects incomplete, missing, changed and undeclared inputs, even when
a good original remains available. Frozen probes, protocols, manifests, generated
responses and research outcomes were not edited. The source suite passes 406 tests.

## Verified local recovery

The repository snapshot captures clean commit
`a73b6dc358ec1c338d7548c57275f455037d5c1f`: **30,707 entries, 24,112 files,
9,309,079,832 bytes**. Its manifest SHA-256 is
`33db5dac8ab3523aed119545b4b3c439e96ad5857d36a1ac2671083a1770715d`.
The separate build 21 archive contains **49 files, 269,881,904 bytes**, with manifest
SHA-256 `8c11a09d515ced8d8c8ff16799cafb6d44a7464065e6f02f61dd21d577351d44`.
Its executable remains
`5900a5b9cf11cc613e0511adda63d6d3d9897920ce786c831dc275e81a1ee259`.

These are private **same-volume copy-on-write recovery copies**. macOS `clonefile`
creates distinct inodes sharing physical blocks until changed. It does not provide
independent-device redundancy. The qualified transport passed nine existing archive
tests and four clone boundary tests; it has no overwrite or byte-copy fallback.
The original archive library's inventory, private-permission, path and full-content
checks remain unchanged. Standard exclusions remain `.build`, `.swiftpm`, `.venv`,
`__pycache__`, `.pytest_cache` and `.research`.

The initial snapshot refused ten absolute symlinks in the preserved first failed
guided-playback harness. The successful retry used a normalized archival view:
only those ten explicit aliases became equivalent internal relative links. Every
regular-file byte and every other inventory entry is unchanged; all targets are
manifest-listed regular files. Their original target strings and hashes are retained
in a separate relocation receipt. The original harness and first failure are preserved.
The disposable staging view was removed after archive and restore verification.

Archive and separate restore passed for both repository and app. Historical replay,
with networking and original paths denied, passed eleven daily/weekly windows,
three original bounded checkpoints and the closeout report. Day11 reproduced its
expected refusal; the 5,088-ID ledger and pending window did not advance. The existing
qualified scratch/path adapter was reused without modifying frozen research code.

A self-contained named-ref Git bundle carries the later test repair into a fresh
restore, preserving the first archive and restore. The repaired restore passes all
406 Python tests, the two-entry synthetic CLI walkthrough, package verification
and both 300-step scripted runner examples. All 180 packaged source inputs and
the exact app binary match. These checks deny networking, original paths and writes
into the restored source; complete before/after inventories remain unchanged. This
is a recovery check, not a repeated human UI session or a new all-native aggregate.

Final documentation recovery is performed after this account’s commit using a
separate named-ref bundle. Its standalone receipt records verification status,
exact commit and bundle hash; the snapshot does not contain its own verification.

## Locations and receipts

The private base is
`~/Library/Application Support/Reservoir Research/`:

- `Backups/2026-10-07-final-integration-v2/`: repository/app archives and named-ref bundles.
- `RestoreChecks/2026-10-07-final-integration-v2/`: unchanged baseline repository/app restores.
- `RestoreChecks/2026-10-07-final-integration-v3/`: restored source with the later committed changes.
- `RecoveryChecks/2026-10-07-final-integration-*`: external operation and replay receipts.

The [private receipt packet](../research/outputs/2026-10-07-final-review/packet-manifest.json)
binds the initial failures, archive operations, exact link relocation, historical
replay, later source/product checks and final Git boundary. These local evidence
links are not downloadable inputs from GitHub. Earlier October 6 and October 7
snapshots, release checkouts and candidates remain preserved.

## Publication boundary

Mike authorized publication after the final review. Push only the named
`codex/research-closeout` branch to the existing public repository; no force push,
merge, tag update or app-release publication belongs to this pass. The standalone
[publication receipt](../research/outputs/2026-10-07-final-review/publication.json)
records the actual remote readback and unchanged main/tag identities.

The [board manifest](../board/2026-10-07-final-readiness.json) covers one dated
readiness/recovery log. All 289 existing cards and 112 prior logs remain unchanged;
the repeated reconciliation proposed zero writes. Human review and day11 remain open for
their specific evidence; an independently located backup remains an unverified
future option under Mike's chosen local recovery scope.
