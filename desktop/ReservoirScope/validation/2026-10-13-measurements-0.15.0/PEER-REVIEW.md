# Independent source review — 0.15 measurement reference

Reviewed 2026-10-13T22:27:11.055967+00:00. These hashes identify the source read for this review, not a replacement for final package/build receipts.

## Rust review by tauri_platform_validation

No concrete blocker found in the v4 prior-observation/reference changes in `crates/reservoir-core/src/sustained.rs` or their journal-detail projection in `src-tauri/src/sustained.rs`.

The bounded, nonrecursive prior scalar snapshot comes from the last reached numerical observation before memory/provider work, independently of prior journal prose. Failed or skipped writing therefore does not silently remove the reached observation; retry keeps its existing observation boundary. V4 validation binds prior step, simulated time and scalar bounds to the retained observation; v1–v3 reject a new prior payload, and omitted optional data preserves their serialized shape. Whole-chain replay regenerates observations and compares the exact final checkpoint; checkpoint structural validation alone is not claimed to authenticate prior history. The same helper supplies eight current/prior/delta rows to prompt and reader, with percent differences in percentage points. State-coordinate change L2 remains distinct from change in L2 norm. Optional reader projection failure returns unavailable without changing journal/store verification.

No Rust edits, duplicate tests, app, service or process actions were performed for this review. Core test execution belongs to its separate owner/receipts.

## Reciprocal frontend review by portable_core_assessment

The core owner independently read the new `JournalMeasurements.tsx` and `journalMeasurementReference.ts` source, without editing or running frontend tests. Their reported conclusion was no blocker: all eight labels/units match Rust; deltas come from the backend; prior observation, prior prose and live state remain separate. Historical prior-step metadata without scalar values stays unavailable, and the first observation never manufactures zero. Eight-significant-digit display is disclosed separately from prompt formatting; missing or malformed reference data leaves original prose and Evidence readable.

The frontend author separately ran the full suite and production TypeScript/Vite build: **341 tests in 37 files passed**, then build passed. [frontend-checks-02.json](frontend-checks-02.json) binds unchanged before/after source maps and logs. The first failed run is preserved; its new module case-folding collision was fixed by giving the validator a distinct filename before the passing run. This peer review adds no native UI or GPU execution claim.

## Reviewed source identities

| Source | SHA-256 |
| --- | --- |
| [crates/reservoir-core/src/sustained.rs](../../crates/reservoir-core/src/sustained.rs) | `2c5b190812504d097623a309f451bb4c6d550c165193834362ba77258e2167b7` |
| [src-tauri/src/sustained.rs](../../src-tauri/src/sustained.rs) | `caba4c9be5ec1865d8bd8e0e4cbe3947d0edbd8330d46bc8e1cc57c23cb047c5` |
| [src/JournalMeasurements.tsx](../../src/JournalMeasurements.tsx) | `c30647c4ccf246aa427c58f23a97c262592f2d1399c28a59f2256d35164b2b94` |
| [src/journalMeasurementReference.ts](../../src/journalMeasurementReference.ts) | `93df93715c6ac22f4d35137fb3b238efcb8f8a1160e975a48a1e852e56ac0d0a` |
| [src/MyReservoirJournals.tsx](../../src/MyReservoirJournals.tsx) | `cefca0ac4d20a782aef86b320d9b42a525a0bbbe528e65c6d240bc0939b41219` |
| [src/myReservoirTypes.ts](../../src/myReservoirTypes.ts) | `e4f288284fe528b29b0e42f02296626d07611546e58d1dd8432b0ae07f7f910e` |
| [src/myReservoirController.ts](../../src/myReservoirController.ts) | `f470bfee266744bdb84a3569929a62818ca82cbe7267f8ff02da4802a59b1dcd` |
| [src/MyReservoirConfig.tsx](../../src/MyReservoirConfig.tsx) | `261b32c159a89465b3af60a48630ae9feef2bc9cb69fe086a462ceba84c1505e` |
| [src/JournalMeasurements.test.tsx](../../src/JournalMeasurements.test.tsx) | `fc9d433f2c829aa95c73f876f169d7c72fe100dc9b1850b6969955781ff63e39` |

No automatic scientific, factual or creative-quality verdict is added by the table. Packaged old-record replay, native reader interaction and any new real-model run remain separately qualified by their own subsequent receipts.
