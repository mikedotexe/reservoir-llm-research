# Offline recovery and final identity audit

The separately exported recovered session passed the same pinned 0.16.0 r2
production verifier. The [audit receipt](recovery-audit-01.json) and
[reproducible script](check_recovery_01.py) retain the exact command, result,
every exported-file identity, manifest differences, frozen-file hashes and
executable hashes. The original full checker was not rerun.

Both exports contain 73 files. Exactly 72 are byte-identical: all 59 segments,
all 12 journal objects and the exact final checkpoint. Only `manifest.json`
changed, precisely:

| Field | Original | Recovered |
| --- | --- | --- |
| Generation | 3 | 4 |
| Revision | 423 | 424 |
| Wrapper phase | budgetReached | paused |

Configuration, numerical step 361, twelve journals, elapsed time, diagnostics,
all prompt/response/provider-count evidence, full-text memory and application
history are unchanged. The core checkpoint remains Ready. No new numerical
step, journal, application or provider attempt was added. Both exported inputs
and the original qualification receipt remained unchanged during this audit.
The original [mechanical result](MECHANICS-RESULTS.md) and exact
[twelve-text rendering](JOURNALS.md) therefore apply to the identical retained
history; no new prose result is manufactured by restoring.

All 22 files in the episode's prospective freeze still match their recorded byte
lengths and SHA-256 hashes. The packaged executable and its original pinned copy
both match
`73872388b56d2483054497aa8513e3659f79dfaf255699d6bca29041cafd258d`.
Their combined content-hash cost was 33,967,488 bytes. File identity metadata
remained unchanged through the verifier call. The 248,015,048-byte package
resource contents and 96,675,714-byte archive were not rehashed; their earlier
package proof is retained, not presented as a fresh full-content check here.

The parent separately observed clean Cmd-Q, idle relaunch and explicit paused
Restore with Resume disabled. This script did not observe those UI actions or
inspect processes, and makes no crash/power-loss durability, new model,
writing-quality or full-context-processing claim.
