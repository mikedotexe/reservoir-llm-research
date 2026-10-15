# Packaged v7 reanchored tampering

The pinned 0.19 production verifier accepted the original native synthetic export both before and after six negative-copy checks. All six copies were rejected for their intended semantic cause. The original’s 28 files, the pinned executable, and the qualified helper sources remained unchanged. The two positive reports are identical: 50 numerical steps, four journals, 22 segments, and 1,678,982 retained bytes.

Execution ran from 2026-10-14 17:09:08.869578 UTC to 17:09:09.619635 UTC. The [exact CLI receipt](reanchored-tamper-01.json) retains commands, output, binary identities, original inventory and every negative-copy inventory. [Continuity](tamper-execution-continuity-01.json) binds the copied receipt and helper qualification; [seven pure helper tests](tamper-helper-tests-02.json) preceded execution. The initial helper test receipt remains preserved separately and records a test-only macOS temporary-path alias assertion correction.

| Copied evidence changed | Reanchoring and observed rejection |
|---|---|
| Held observation clock | Saved journal hash, its envelope anchor, following predecessor hashes and manifest tail repaired; rejected as differing from replayed response/save evidence. |
| Prior entry’s recorded first application step | Same repairs on the later saved journal; rejected for the same replayed-evidence mismatch. |
| Authority sentence changed to claim described controls execute | Same repairs; rejected for the same replayed-evidence mismatch. |
| Writing-boundary block removed | Same repairs; rejected for the same replayed-evidence mismatch. |
| Writing-boundary block moved before prior prose | Same repairs; rejected for the same replayed-evidence mismatch. |
| Manifest prompt version changed from v7 to supported v6 | All existing byte anchors retained; rejected because the chain no longer begins at the exact genesis/previous committed continuation. |

For all five journal cases, the helper checked the raw UTF-8 span of every core segment payload and all checkpoint files byte for byte. It did not reconstruct or rehash Rust’s canonical numerical state in Python. Each changed journal had exactly one committed object anchor; all repaired outer anchors were consistent before invoking the verifier. This isolates saved-evidence consistency from simple stale-checksum rejection. Separate typed core tests cover rehashed checkpoint prompt changes.

Scratch copies remain under `target/qa/0.19-reanchored-tamper-01`; no original files were replaced. This offline check made no model, provider, UI, restore or live-store calls. It establishes neither model adherence to the wording nor writing quality, provider authenticity, or physical power-loss durability.
