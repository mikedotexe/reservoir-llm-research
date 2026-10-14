# Historical export replay and test correction

The exact new pinned 0.17.0 verifier, SHA-256 `7d46719838495b7a9ba57eea69ac9c940bb81f2fdc47cd12b761d97bb472d081`, accepted all six preserved exports through its offline `--verify-sustained` route. Every invocation returned `modelsContacted: false`. Every input file matched its earlier retained inventory before execution and remained identical afterward; the executable also remained identical. See the complete [replay receipt](historical-replay-01.json), [case selection](historical-replay-cases-01.json) and [runner](replay_historical.py).

| Preserved case | Prompt | Step | Saved journals | Exact files |
|---|---|---:|---:|---:|
| Original completed reading episode | v1 | 121 | 4 | 25 |
| Completed writing-room episode | v3 | 121 | 4 | 25 |
| Held incomplete open-writing attempt | v3 | 30 | 0 | 4 |
| Completed four-entry episode 02 | v4 | 121 | 4 | 25 |
| Completed twelve-entry episode 02 | v4 | 361 | 12 | 73 |
| Its paused recovery export | v4 | 361 | 12 | 73 |

No historical v2 export was found in the bounded owned-QA manifest inventory. V2 remains covered by the separately executed temporary desktop save/export/paused-restore tests; this is not a historical v2 native-export result. No export was regenerated, relabeled or resumed, and no UI or service call was made. These results qualify compatibility with these exact artifacts, not provider authenticity, writing quality or new physical-crash durability.

The earlier [synthetic harness freeze](synthetic-harness-freeze-01.json) included desktop test source SHA `d902c77449fde262b23e81ce222550a6e72e2c7c25736234aa71afcc43609c51`. During root's full run03, the long-output worker test failed because its default had correctly changed to v5 while its extraction assertion still searched for the old v4 prior-text marker. [Run03](rust-checks-03.json) and its failed log remain preserved. After that runner exited, only this test was corrected: the default is now explicitly asserted as `ContinuingJournalV5`, and extraction uses `Full previous text as one JSON string: `. No production source or prompt changed for that repair.

Final desktop test source SHA is `f0dc83f427de668a17a4bb84c568728fb7f45af434280ce04f2567a4facc172b`. Root's [run04](rust-checks-04.json) records **192 desktop tests passed, two ignored**, strict core/desktop Clippy passed, and unchanged source during that run. It reuses the **190 passing core tests** from run03 with all core inputs verified identical. The original harness freeze is historical evidence, not rewritten to hide the later test-only correction; helper/checker source identity remains unchanged.
