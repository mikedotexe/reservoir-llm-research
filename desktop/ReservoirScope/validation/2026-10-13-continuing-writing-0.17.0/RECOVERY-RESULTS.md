# Native clean-quit recovery: continuing-writing v5

The original and recovered native exports each passed the exact pinned 0.17.0 production verifier and independent fixture joins. Their 27 non-manifest files are byte-identical. Both retain step 50, four journals, 22 segments, the same five received responses and the same blocked core checkpoint. Recovery did not create, apply or discard another journal.

The [equality receipt](recovered-export-equality-01.json) compares all 28 files in each export, validates their inventories against the separately retained [original](original-export-evidence-01.json) and [recovered](recovered-export-evidence-01.json) replay receipts, and checks both inputs again afterward. Both exports and the pinned executable remained unchanged.

| Manifest field | Original export | Recovered export |
|---|---|---|
| `generation` | `1` | `2` |
| `revision` | `76` | `77` |
| `phase` | `attemptBlocked` | `paused` |

These are the only changed manifest fields. The entire checkpoint, all four journal objects and all 22 segments are identical, including exact v5 prompts, complete prior-memory text, provider input-count evidence, save receipts and once-only application evidence. The first four replies remain saved/applied at steps 11, 21, 31 and 41; the fifth remains incomplete and unsaved at step 50. The wrapper's paused state does not change the retained core's blocked state or make the incomplete response eligible.

The immutable bundle paths are:

- Original: `target/qa/0.17-continuing-writing/exports/sustained-1791941918315-1-1-76` (1,666,849 bytes).
- Recovered: `target/qa/0.17-continuing-writing/exports/sustained-1791941918315-1-2-77` (1,666,841 bytes).

Root reports the native sequence as a confirmed clean quit, idle relaunch, explicit Restore into paused generation 2, disabled Resume, and a second native export. Root used no Skip, Stop, Retry or Start after restoration. Those observations belong to the separate native UI account; this comparison itself reads only immutable files and existing replay receipts. The fixture had already stopped, as recorded in [its retained lifecycle evidence](fixture-run-01/retention.json).

This qualifies this clean-quit, explicit-restore path and exact evidence preservation. It does not qualify crash or power-loss recovery, a new model request, continued numerical execution, minimization/GPU behavior or writing quality.

Equality receipt SHA-256: `96bb9bfe4fb4cb6a51553a3d01d3bf8e05d4011ea636eaec19b4c8a330ca4838`.

Recovered replay receipt SHA-256: `fa6a721ea42b3ef867b49846d66d72f5185cc53a211c6c1e45df968a1fd52e49`.
