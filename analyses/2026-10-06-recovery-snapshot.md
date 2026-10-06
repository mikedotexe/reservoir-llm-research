# Research closeout recovery snapshot — October 6

The private **same-volume recovery snapshot**, independent restore directory and
isolated research replay passed. The snapshot binds clean source commit
`d47a866192eafe0da803f62acd6e20f1a16dfffc` on `codex/research-closeout`.
It contains the completed source, research results and pre-snapshot reconciliation.
This later recovery account, replay-adapter revision and final board attestation
are outside that snapshot. Independently located backup availability remains
**unverified**; this result does not establish availability of Mike's older backup.

## Captured state and locations

The [archive operations receipt](../research/outputs/2026-10-06-closeout-recovery/archive-operations/operations-receipt.json)
records snapshot, separate verification and restore between **17:36:49 and
17:38:34 UTC**. The verified inventory has **29,984 entries, 23,492 files and
8,757,769,076 bytes**. Its manifest SHA-256 is
`2c6579284f93b22ea093dc273e62b52fb3021ba43a1a574eda95e1a63accdd9b`.

All three locations report device ID `16777234`:

| Role | Local path |
|---|---|
| Source | `/Users/v/other/reservoir-llm-research` |
| Snapshot | `/Users/v/Library/Application Support/Reservoir Research/Backups/2026-10-06-research-closeout` |
| Restore | `/Users/v/Library/Application Support/Reservoir Research/RestoreChecks/2026-10-06-research-closeout` |
| External replay receipts | `/Users/v/Library/Application Support/Reservoir Research/RecoveryChecks/2026-10-06-research-closeout-replay-v2` |

The existing archive implementation copied Git history and ignored private evidence
with private permissions, compared the source before/after copying and checked every
restored file against the manifest. Its established exclusions are `.build`,
`.swiftpm`, `.venv`, `__pycache__`, `.pytest_cache` and `.research`.
App bundles and release checkouts outside the source directory are outside this
snapshot. The unchanged 0.14 tag and retained delivery metadata are separately
preserved; present availability of the original historical binary/zip was not
newly verified. No old candidate, release checkout or recovery ref was replaced.

## Isolated replay and retained first failure

The [first attempt](../research/outputs/2026-10-06-closeout-recovery/replay-attempt-1/replay-receipt.json)
passed its access-denial controls and initial inventories, then stopped because
day1's frozen verifier creates `verify-control-` scratch inside its packet directory.
The sandbox correctly denied that write. This failed attempt and its log remain
unaltered; it is not a failed research finding or a successful replay.

The [qualified external adapter](../research/outputs/2026-10-06-recovery-preparation-v2/README.md)
passed nine isolated boundary fixtures. Its code SHA-256 is
`decb73ff0e5edd2ede75e64c3d7b4046a6cf0f62b247fef3c40fb01ca78a349f`.
It binds the original snapshot's driver and stages only its own revision into a
fresh external receipt directory. It does not edit the archive, restore, frozen
replay files, protocols, captures or expected outputs.

The successful run retains three explicit relocation accommodations:

- Day1–day9's exact `TemporaryDirectory(dir=packet, prefix='verify-control-')`
  calls use external private scratch. Undeclared packet paths or prefixes fail.
- Day11's declared negative-control files use its existing `EXDEV` copy fallback
  instead of linking restored evidence into its external scratch directory.
- The three historical bounded checkpoints use the unchanged analyzers with one
  exact original-day9-to-restored-day9 mapping. Only the recomputed provenance
  string is normalized before exact result comparison. This is a relocation
  adapter, not a claim that the old absolute-path verify CLI relocates unchanged.

The [sandbox controls](../research/outputs/2026-10-06-closeout-recovery/replay-v2/sandbox-controls.json)
confirmed permission denial for a network socket/connect attempt, a known original
research-file read and write-opening the existing restored ledger. The profile
denies network access, reads/writes under `/Users/v/other`, the research cache,
`/Volumes` and `/Users/mikepurvis`, and all writes into the archive and restore.
Missing files or connection refusal do not count as successful controls.

## Verified results

The [final replay receipt](../research/outputs/2026-10-06-closeout-recovery/replay-v2/replay-receipt.json)
passed between **17:45:29 and 17:47:30 UTC**, with SHA-256
`3b6d84ff04dfcb47a7487c741c6016cad9aa60e7105c6ec2904ad178011e02bc`.

| Replay | Result |
|---|---|
| Original day1–day9 and week1, plus verified day10 | All eleven passed using their retained code and evidence |
| Original bounded checkpoints | All three matched: one original and two provider-amended checkpoints |
| New closeout through stable hashed-input copies | Verified report SHA-256 `d1bacd71728b0cb08212cf26ecc4c9742abc88401d065c6978994db92ebaea71` |
| Day11 integrity and refusal | Expected `verification_blocked`; PID 81688's 263 unknown-era rows remain unresolved |
| S-007 ledger and pending window | Exact before/after hashes match; 5,088 IDs, no advance |
| Archive and restored inventories after replay | Both match the complete original manifest |

No collection, original-source reopening, new model request or research acceptance
occurred during replay. Coverage-qualified S-006/S-008 closure and the failed S-009
qualification keep the limits in their [bounded account](2026-10-06-bounded-followups-closeout.md).

Exclusive, hash-checked copies of the archive operations, full archive manifest,
first failed attempt and successful replay are retained under
`research/outputs/2026-10-06-closeout-recovery/`. Its [packet manifest](../research/outputs/2026-10-06-closeout-recovery/packet-manifest.json)
has SHA-256 `361097768f151dd46ebd3db08b2a668984b67220ec79ec0261a9041679bcbe64`.
These private links resolve in this checkout, not on GitHub.

The later [preservation receipt](../research/outputs/2026-10-06-closeout-final-preservation/preservation.json)
also verifies all 45 original protected files, four frozen v1 code identities,
three qualified wrapper identities and seven sealed packet inventories/content
hashes unchanged. Its SHA-256 is
`867e2162f24e873425891573afffd77675841550b8f4f4aa25dd2aac504bfb6b`.
The accompanying [0.14 retention check](../research/outputs/2026-10-06-closeout-final-preservation/release-014-retention-check.json)
distinguishes the unchanged tag's resource manifest and retained release identities
from the deliberately changed 0.15 working manifest and old binaries whose bytes were not rechecked.

The [integration account](2026-10-06-research-closeout-and-geometry-integration.md)
records the local commits and qualification limits. The [board account](2026-10-06-board-reconciliation.md)
records the later final attestation and repeat reconciliation. Those subsequent
records do not retroactively change the snapshot's captured commit or claim that
the snapshot contains its own verification.
