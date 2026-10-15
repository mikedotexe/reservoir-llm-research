# Offline recovery verification · v6 episode02

The recovered native export passed the frozen checker and the exact pinned
0.18.0 production verifier on its first execution. The original and recovered
exports each contain **46 files, 37 segments, 240 numerical steps and seven saved
journals**. All 45 non-manifest files are byte-identical, including the checkpoint,
every journal object and every event segment. Both exports still match their
respective first verification inventories. [Recovered verification](recovered-export-01/receipt.json)
· [Exact file comparison](recovery-comparison-01.json)

Only three manifest values changed:

| Field | Original | Recovered |
| --- | --- | --- |
| generation | `1` | `2` |
| revision | `281` | `282` |
| wrapper phase | `attemptBlocked` | `paused` |

All other manifest fields are equal, including configuration, elapsed active time
of 324,322 ms, cursor, counts and checkpoint hash. The retained core remains
`blocked`; changing the wrapper to paused does not accept or resume its incomplete
response. The unchanged checkpoint SHA-256 is
`a6b690a1141cafbee0d92dea4ccbb90630d4a3732b09403a1226d4518d691ac7`.

The twelve-slot outcome is unchanged: attempts 1–7 produced complete saved entries
at steps 30–210, first applied at steps 31–211. Attempt 8 reached step 240 and
returned `complete: false`, stop reason `length`, and 1,024 output tokens. Its full
text and reported input count remain retained, but it has no journal or application.
Slots 9–12 remain unstarted. This is a held partial episode, **not** twelve completed
entries or exhaustion of the configured 361-step, twelve-attempt or 900-second
limits. [Original verification and all twelve slots](real-model-export-01/receipt.json)

Both runs used executable SHA-256
`fe14eeb2f921a541644a900d3397d973d81a6f70de66347f485cc0851fecafb0`.
The offline verifier reported no model contact. The comparison is reproducible
with [compare_recovery_01.py](compare_recovery_01.py); it reads only the two
explicitly handed-off exports and their existing verification receipts and writes
an exclusive new result. Original exports and receipts remained unchanged.

The parent separately observed provider shutdown, clean quit, idle relaunch,
explicit inspection and paused Restore with Resume disabled. Those are native UI
and supervision observations; this note establishes the resulting retained bytes
and replay consistency. It does not establish crash or power-loss durability,
new generation, provider comprehension, or writing quality.
