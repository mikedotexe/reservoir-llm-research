# Prospective qualification · action boundaries 0.19.0

This is the prospective native procedure. Helper tests and preservation/preparation receipts are separate executed evidence; no new package, production replay, provider or native UI result is implied. The lead owns execution after final sources and this procedure are frozen. All prior 0.18 receipts, archives, pins and exports remain untouched. [Tool inventory and copy identities](qualification-tools-01.json).

## Scope and required evidence

1. **Source contract.** Fresh sessions select the approved v7 prompt; absent historical version stays v1 and explicit v1–v6 remain unchanged. Full retained observation v2, exact prior saved/applied prose, numerical clocks and save/application gates remain authoritative. The exact v7 action-boundary wording and placement must come from the approved core fixtures, not a checker-invented paraphrase. The approved [v7 protocol](PROTOCOL.md) places the exact boundary after `END PREVIOUS JOURNAL`, before the unchanged final invitation, with current and actual prior observed/applied clocks. The early SESSION CONTEXT stays v5-derived without v6 additions.
2. **Meaningful source checks.** Preserve old fixture bytes and test new first/later prompts. Check missing/mutated/duplicated/misplaced action scope, hostile-looking headings inside quoted prior prose, LF-delimited exact JSON memory including U+2028/U+2029 and Unicode normalization distinctions, and unsupported future versions. Reanchored typed checkpoint/segment negatives must use core serialization so a rejection is not merely caused by stale hashes or Python/Rust float formatting differences. Backend save/export/recovery and frontend old-selection/readout/prompt-version behavior need final source-bound receipts. No old passing Rust result covers changed core code merely because the file names match.
3. **Protect and package.** Verify the old 0.18 app, immutable archive and pinned CLI before replacing the app path. Old expected executable is `fe14eeb2f921a541644a900d3397d973d81a6f70de66347f485cc0851fecafb0`; archive is `1a59336a35715cd3e5f532c7d5b933fc2e3216ec0241c839aca7d35abe758561`. The [preservation receipt](prior-package-preserved-01.json) freshly verifies these identities and an exclusive complete copy at `target/qa/0.18-preserved/Reservoir Scope Tauri Preview.app`; retain this copy unchanged after build. Build 0.19 only after final frontend/Rust input hashes match. Pin the new executable, create a new archive exclusively, compare every archived member with the app, and capture package/resources/signature/source identity before UI. Retain old archive/pin equality after build. Use the pinned Xcode SDK 26.2, locked dependencies, `CARGO_INCREMENTAL=0` and coordinated compiler/disk use.
4. **Historical acceptance.** The prepared twelve-case selection keeps all eight previously replayed exports and adds v6 synthetic original/recovery plus real held-partial original/recovery. It covers actual v1, v3, v4, v5 and v6 exports. There is no selected historical v2 export; generated v2 test coverage must be labeled separately. The previous completed twelve-entry v4 and v5 exports stay in the denominator. Each exact old bundle and basis receipt must match before any CLI call and again after all calls. Use only `--verify-sustained`, never Restore/Resume/Start on old material.
5. **Reanchored tampering.** In new exclusive scratch copies, change the v7 scope in a saved journal prompt and recompute the journal file SHA, envelope journal anchors, segment predecessor byte anchors and final manifest anchor. The new verifier must still reject mismatch with replay-derived journal evidence. Separately require core tests that mutate pending v7 context and recompute typed checkpoint/segment hashes; the context must remain derivable from the declared specification. Test manifest version substitution against unchanged v7 history. Keep originals unchanged, retain each mutation description and reanchoring scope, and distinguish semantic-replay rejection from a simple file-hash failure. The separate [packaged tamper helper](check_reanchored_tamper.py) repairs only byte-envelope anchors while leaving core payload/checkpoint bytes intact. Its own pure tests and source-bound receipt are separate; execute it only after the new pin and positive v7 export pass. Source-level typed-state reanchoring remains covered by the core tests.
6. **Actual synthetic wire path.** Reuse the provider and five fixed replies byte-exact. New fixture model label stays `reservoir-fixture:input-evidence-0.16`; it is a deliberately unchanged test identity, not a real model. New exclusive output: `target/qa/0.19-action-boundaries-provider-01`. At most five POST requests, no retry/wrap, stop file or 900-second ceiling. Freeze the exact provider, v7 checker, tests, fixtures and UI plan before launch. An endpoint may come only from the new owned `endpoint.json`.
7. **Native UI and immutable exports.** Configure v7, seed 20261013, cadence 10, 51 steps, five attempts, 180 active seconds, 32 MiB, 1,000 ms pace, noise .02, leak .65, retention .955 and regulation enabled. Use the explicit fixture endpoint, context 8192, output 1024, deadline 180 seconds and temperature zero. Creation must not generate; one explicit readiness check precedes one Start. Expect entries at 10/20/30/40, applied once at 11/21/31/41, then the fifth incomplete response held at 50 without a journal or new feedback. Inspect first/later prompt boundary placement, full prior text and separate recorded-measurement disclosure. Keep an older selected entry tied to its writing step while the live state changes. Preserve provider count metadata (wide, absent, malformed, u64 maximum, incomplete) without turning it into a save gate.
8. **Recovery.** Native-export the held prefix, then run the new pinned production CLI and exact wire/memory/save/application checker. Stop only the owned fixture through its stop file; retain its terminal files/log count. Cleanly quit/relaunch, explicitly inspect/Restore paused, do not Resume/Retry/Skip/Start, and export again. Require byte-identical non-manifest files; allow only the actually observed generation/revision increments and wrapper phase transition, while core held state stays unchanged. Report any additional differences rather than granting a broader exception.

## Prepared commands

Run these from `desktop/ReservoirScope` only after the lead authorizes the corresponding stage. Placeholder arguments below require actual retained paths/hashes; they are not inferred service settings.

```sh
# Before replacing the current app; no app or service invocation.
python3 -B validation/2026-10-14-action-boundaries-0.19.0/protect_prior_package.py

# Bind the twelve explicit old exports; no production executable invocation.
python3 -B validation/2026-10-14-action-boundaries-0.19.0/prepare_historical_replay_01.py

# After final checks and GUI shutdown; build/archive/pin, no native launch.
python3 -B validation/2026-10-14-action-boundaries-0.19.0/build_package.py \
  --rust-receipt validation/2026-10-14-action-boundaries-0.19.0/rust-checks-01.json \
  --frontend-receipt validation/2026-10-14-action-boundaries-0.19.0/frontend-checks-01.json

# After the new exact pin exists; headless old-record verification only.
python3 -B validation/2026-10-14-action-boundaries-0.19.0/replay_historical.py \
  --cli target/qa/0.19-pinned/reservoir-scope-desktop \
  --expected-cli-sha256 QUALIFIED_019_EXECUTABLE_SHA256 \
  --output validation/2026-10-14-action-boundaries-0.19.0/historical-replay-01.json

# Parent-operated only after prospective freeze; synthetic loopback server.
python3 -B validation/2026-10-14-action-boundaries-0.19.0/owned_provider.py \
  target/qa/0.19-action-boundaries-provider-01 --lifetime-seconds 900
```

The parent owns build execution. The build wrapper expects the established Rust receipt fields `passed`, `sourceUnchanged`, `sourceAfter`, and frontend fields `status`, `sourceChangesDuringChecks`, `sourceInputsSha256`. If the actual final receipt schema differs, adapt this new wrapper explicitly before execution; do not relax source equality or reuse the 0.18 comment exemption. Each output name is exclusive. A failed run requires a new named attempt and retention of its original result.

The v7 checker retains the previous CLI API:

```sh
python3 -B validation/2026-10-14-action-boundaries-0.19.0/check_fixture_export.py EXPORTED_BUNDLE \
  --fixture target/qa/0.19-action-boundaries-provider-01 \
  --cli target/qa/0.19-pinned/reservoir-scope-desktop \
  --expected-cli-sha256 QUALIFIED_019_EXECUTABLE_SHA256 \
  --output validation/2026-10-14-action-boundaries-0.19.0/original-export-evidence-01.json
```

The adapted checker requires the exact approved v7 suffix outside the JSON-quoted memory, one successful readiness GET, five completed response writes, five exact attempts, four once-only applications, and a final blocked core. Skip, cancellation, retry, interruption or budget extension fails protocol acceptance even if a broader prefix could replay. Pure-helper outcomes are recorded separately in `synthetic-harness-tests-01.json`. A failed or interrupted qualification preserves its first receipt.

## Interpretation limits

This tranche can establish software behavior, exact supplied HTTP bytes, replay consistency, save/application gating and clean-quit recovery for the inspected package. It does not establish improved model writing, policy understanding, full context processing, a causal prompt effect, real-model execution, long-duration/GPU/energy behavior, power-loss recovery or Windows/Linux qualification. Historical failures and held responses remain part of the record. No Being system, endpoint, prompt or workspace is involved.
