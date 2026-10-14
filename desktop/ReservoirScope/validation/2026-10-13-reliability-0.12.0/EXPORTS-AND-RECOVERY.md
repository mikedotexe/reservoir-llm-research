# Immutable exports and explicit recovery — frozen 0.12.0

Both native exports passed offline genesis/event/numerical replay using a pinned copy of the actual frozen shipping executable, SHA-256 `f68a3752a628edf11ac6161a26e6979bb22dcf4c3ee1c63f10add2cea86ab40d`. The second export preserves every earlier segment and journal object and adds one accepted, saved and applied writing opportunity after explicit restoration and Resume. These are owned synthetic-provider results, not real-model quality or physical power-loss qualification.

## Export identities and replay

Session: `sustained-1791908510756-1`. Both exports are immutable native-dialog outputs under `target/qa/0.12-reliability/exports-multi-hour/`.

| Export | Generation / revision | Steps | Journals | Segments | Verified bytes |
| --- | --- | ---: | ---: | ---: | ---: |
| `sustained-1791908510756-1-1-8283` | 1 / 8283 | 7,100 | 236 | 1,180 | 106,035,294 |
| `sustained-1791908510756-1-2-8319` | 2 / 8319 | 7,127 | 237 | 1,186 | 106,526,564 |

The first manifest SHA-256 is `8c9579321471d37b7fb97c9a6974bc949bd51b2a1a00be7210fa73c8ef2273fa`; the second is `fc012b6c55582baa966c51d0b91eb8f1161253e29e0cd17f4ea1ad1053dcc021`. Their current checkpoint hashes differ as expected after continuation. That does not alter the retained segment or journal prefix.

| Offline invocation | UTC interval | Monotonic wall time | Peak RSS from `/usr/bin/time -l` |
| --- | --- | ---: | ---: |
| First frozen CLI replay | 18:43:52.867437–18:43:57.496229 | 4.628683125 s | 13,778,944 bytes |
| First export evidence and 13 corruption controls | 18:44:33.858795–18:45:08.241965 | 34.383190167 s | 126,861,312 bytes |
| Second frozen CLI replay | 18:49:58.094589–18:50:02.111011 | 4.016110625 s | 13,893,632 bytes |

These are separate post-capture verifier/checker workloads, not resource measurements of the GUI or minimized interval. Raw stdout, stderr/time output, exact commands and binary hashes are in [first CLI receipt](export-frozen-cli-01-receipt.json), [checker execution receipt](export-evidence-and-negatives-01-execution.json), and [second CLI receipt](export-frozen-cli-02-receipt.json). The CLI reports replay and save/application consistency; it does not authenticate provider execution or physical power-loss durability.

## Request, journal and memory evidence

The unchanged [existing checker](../2026-10-13-sustained-0.12.0/check_sustained_ui_exports.py), SHA-256 `5df124ea9d9443ebb52c7baa921026f9cc31a6265ab9308611645964c0576689`, matched all 236 original journals to exact owned-fixture requests, message bodies, prompts and response-text hashes. It also checked the recorded observation against numerical frames, saved journal identity, previous applied journal used as memory, and host dispatch/response/publication ordering. The first export contained 236 unique applications and 235 prior-journal memory confirmations.

All **13 corruption controls were rejected** on fresh scratch copies: altered text, configured model, prompt or transport duration; altered manifest clock, count or seed; missing/reordered segments; a non-genesis initial checkpoint; altered numerical state; reordered events; and a missing journal. Reanchored controls rebuilt their hash chain where specified, so rejection did not rely only on an unchanged outer hash. The original export and pinned verifier remained unchanged. See [full evidence and negative controls](export-evidence-and-negatives-01.json). These controls were not unnecessarily repeated for the second export.

The second check imported only the checker's read-only helpers, without calling its mutation workflow. [Recovery continuity evidence](export-recovery-continuity-02.json) records:

- All **1,180 previous segments and 236 previous journal objects** are byte-identical in the second export; its event stream starts with the exact earlier event prefix.
- The added numerical events are exactly steps **7,101 through 7,127**. There is one new language-start event, one received response, one saved journal and one memory confirmation.
- Request, turn and attempt **237** observed step **7,110**, saved journal `journal-7110-237-f2ed0fc25e2dd1cacf94bc306c8c556e95e0fbb8be8376b496e45654deb512e3`, and first applied it at **7,111**.
- Its retained prompt memory is the latest previously applied journal, from step **7,080**, attempt 236. Exact text, identity and prompt inclusion passed the existing checker.
- All **237 journal applications are unique**. The continuation adds exactly one matched fixture request; no earlier application is duplicated. Both original export inventories were unchanged across the checks.

The request log was copied to a fresh immutable prefix snapshot for each check. Later requests may append to that owned log for other qualification work. A snapshot or match count is not a claim that the whole fixture log is finished or that all later requests belong to this session.

The originally selected step-30 journal also survived exactly: its 6,065-byte object SHA-256 remains `1cabdd0a2f238f15c83ddfeb38b57f1def54caa459616488e1509fd8246baa70`, and its text SHA-256 remains `0d13d66fa338b79d8a2d7683a94a86e22cbe135318676038c0b9242f7ba7812b`. [Byte-continuity evidence](selected-journal-export-continuity-01.json) compares the export with [the pre-minimize selection receipt](selected-journal-before.json). File continuity alone does not prove an unchanged visible selection; the UI observations are separate.

## Actual quit, idle relaunch, restore and continuation

These actions were performed and recorded by the root agent. The offline verification agent read their receipts without controlling the app or accessing its live store.

| Receipt | Recorded result |
| --- | --- |
| [Normal quit](normal-quit-01.json), captured 18:43:04.564997Z | Actual Cmd-Q from the clean, paused, exported boundary exited directly; original PID 17307 was recorded absent. **No Checkpoint-and-quit review button was exercised.** The manifest remained at step 7,100 and the fixture POST count at 236. |
| [Idle relaunch](idle-relaunch-01.json), captured 18:43:55.845908Z | The same executable relaunched as PID 76635 with its recorded process-start identity. My reservoir showed the preparation form with no active session. No automatic restoration or new fixture POST was observed. |
| [Explicit paused restoration](restored-paused-01.json), captured 18:47:05.030292Z | Restore produced generation 2, revision 8284, paused at step 7,100. Elapsed time remained 7,721.255 seconds and the POST count remained 236. The old step-30 journal was reselected with its original text/hash and application at 31. |
| [Explicit Resume then Pause](resumed-paused-01.json), captured 18:47:58.829794Z | The session reached live/durable step 7,127, 237 journals and 7,748.510 elapsed seconds. The old journal remained selected with Follow latest off and one new entry. One new POST was recorded; the second immutable export independently confirms the continuation. |

The full accepted configuration is identical between exports: seed `20261013`, 30-step writing cadence, 1,000 ms requested pace, 10,000 steps, 400 attempts, **7,800 active seconds** and 268,435,456 storage bytes, with unchanged numerical and source settings. Restoration did not reset the elapsed budget. The continuation consumed **27.255 additional active seconds**, leaving **51.490 seconds** at the second paused export. It did not demonstrate behavior after budget exhaustion.

## Scope and remaining gates

This evidence establishes numerical/history continuity for this normal-quit, explicit-restore and short-continuation path in the frozen 0.12.0 package, with an owned synthetic HTTP provider. It preserves actual native-export and root UI observations separately from independent offline checks.

The separately initiated forced-process-interruption fixture is not covered by these two exports. Neither clean quit nor process termination proves physical power-loss safety. The unbuilt 0.12.1 publisher/quota/frontend changes, real-model behavior, longer-duration qualification, actual system sleep/wake, GPU/energy attribution and other operating systems require their own evidence. No source repair is credited to the frozen binary here.
