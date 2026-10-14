# Independent v5 integration review

No concrete blocker found in the reviewed prompt exposure, version routing and persistence interfaces. This is source review, not a new execution result. Core/frontend owners retain their own test evidence; this reviewer changed only desktop `sustained_tests.rs` and new validation artifacts.

The new version selects a compact prompt projection while retaining observation v2 and its prior scalar snapshot. Four observation-generation/validation branches now admit both v4 and v5; serialized missing version still selects v1. Restored configuration and journal DTO version remain bound to the manifest and replayed genesis. The frontend rejects an unsupported or mismatched returned version before accepting a restore/detail, and distinguishes full human-readable measurements from the smaller model readout.

The prompt separates RMS/fill signed changes from nonnegative coordinate distance; fill changes are percentage points. Prior reached measurements and prior saved/applied text are different references. Full historical prose is JSON quoted, remains recoverable, and is followed by the open invitation. Scaffold exposure checks deliberately exclude that authored string, since it may itself contain hashes, metric names or apparent instructions. No persona, emotional state or required writing form is assigned. Compact context is a design change whose literary effect remains unmeasured.

Desktop test edits retain explicit v1, v2, v3 and v4 save/export/paused-restore cases alongside v5; omitted-version exact wire roundtrip and manifest-relabel rejection remain. Additional v5 tests cover physically reread full memory, full retained observations/eight-row reader evidence and a fabricated prompt that must fail replay despite repaired outer byte hashes. These Rust tests have not been executed by this reviewer; root owns the coordinated `CARGO_INCREMENTAL=0` run.

The new [synthetic harness freeze](synthetic-harness-freeze-01.json) binds the exact unchanged provider/test copies and new checker source. Its 7 provider and 15 checker pure-helper tests passed without a server or production CLI. The core agent independently reviewed the checker and found no blocker. Native UI, exact HTTP prompt/response joins on new output, export replay and paused recovery remain prospective under [the qualification plan](NATIVE-QUALIFICATION-PLAN.md). No model, Being service, UI, process control or endpoint was touched by this review.

## Reviewed source identities

| File | SHA-256 |
|---|---|
| `desktop/ReservoirScope/crates/reservoir-core/src/sustained.rs` | `073d324a17eab74e0d80d738213afb8d1b353102e2c7a5a23d0875077d3baa5b` |
| `desktop/ReservoirScope/src-tauri/src/sustained.rs` | `5399ac3d9faf9fcd291dcc6dd176f80c7cd712bc489e6969bfcf621a084223c8` |
| `desktop/ReservoirScope/src-tauri/src/sustained_store.rs` | `cc3a18469733b975eb0aafc03d41270619e88f6b64eefbcb7a40a91df09b2ef4` |
| `desktop/ReservoirScope/src/myReservoirTypes.ts` | `f46503721a7b4250ad24281eadb585a62678212e502ef134820a30c787fe9d93` |
| `desktop/ReservoirScope/src/myReservoirController.ts` | `23a6fdfdcaa82d435bfda6c5da8b99473184ee6ffaacaa6f2d6532810b843bdf` |
| `desktop/ReservoirScope/src/MyReservoirConfig.tsx` | `4b53c30724b2b895f0e5ad5edcac0493a7f3fd0c7650d302e2db423d5c2df9d4` |
| `desktop/ReservoirScope/src/MyReservoirJournals.tsx` | `363a88d5558490e7d1d6be331e1fe58e24c9fff1f4a6197919a6d7a88c5360ff` |
| `desktop/ReservoirScope/src/JournalMeasurements.tsx` | `af69686916449fbb640eb864701610a4a33a3171fa1934941098060909a4581e` |
