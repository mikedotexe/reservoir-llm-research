# Native paused recovery

The recovered export passed the same exact pinned 0.18.0 production verifier and fixed-fixture joins as the original. Both contain 28 files, 22 segments, four journals and a durable cursor of step 50. Version 6, all five received responses, the exact action-scope prompts, full prior-text memory and four applications remain verified. The incomplete fifth response remains ineligible. [Recovered verification](recovered-export-evidence-01.json)

The independent file comparison found **27 non-manifest files byte-for-byte identical**. Only these three manifest values changed:

| Field | Original | Recovered |
| --- | --- | --- |
| generation | `1` | `2` |
| revision | `76` | `77` |
| phase | `attemptBlocked` | `paused` |

Every other manifest field is equal. The original still matches its first verification inventory; both exports remained unchanged during comparison. Their retained core phase is `blocked` in both cases: the paused wrapper does not accept, retry or apply the incomplete reply. All eight stopped-provider files and their retained copies also remain byte-exact after recovery. [File comparison and provider continuity](recovery-comparison-01.json)

The parent performing the native UI qualification reported clean quit with the app no longer running, relaunch with no automatically opened session, catalog verification, explicit paused Restore and disabled Resume. No Start, retry, Stop or skip was used during that recovery sequence. Those are UI observations; the offline comparison establishes the resulting retained bytes and numerical/event consistency. The actual UI account is maintained separately by the parent.

This is a clean-quit/relaunch recovery check. It does not establish crash or power-loss durability, a new provider call, writing quality, GPU behavior, minimized endurance or platform parity.
