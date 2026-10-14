# 0.15.0: measured context with open-ended writing

Implemented and locally qualified: new sessions use `reservoir-journal-v4` and
`reservoir-and-sensory-v2`, supplying current/prior measurements separately from
historical prose. The reader adds a closed **Recorded measurements** table beneath
each entry. Topic, form, length and metric use remain open. No editorial score,
rewriting or extra save/feedback gate was added. [Design](DESIGN.md) and the
[session contract](../../SUSTAINED-SESSIONS.md) describe the boundaries.

**New real-model accuracy evidence is still pending.** The one frozen rehearsal
was not started: the passive admission reported 32% free versus a required 35%.
No model service, readiness call or generation was started, and all four planned
opportunities remain unexecuted. [Real-model outcome](REAL-MODEL-RESULTS.md) preserves
that refusal. The earlier [v3 journals and errors](../2026-10-13-writing-room-0.14.0/REAL-MODEL-RESULTS.md)
remain unchanged. Better supplied data does not guarantee accurate claims.

## Executed software checks

| Layer | Executed result | Evidence |
|---|---|---|
| Frontend | 341 tests; TypeScript and production Vite build passed | [Receipt](frontend-checks-02.json) |
| Rust | 174 core and 182 desktop tests passed; strict all-target Clippy clean; two prior opt-in quota tests unrun | [Receipt](rust-checks-01.json), [core note](CORE-CONTEXT-QUALIFICATION.md) |
| Source review | Independent Rust/frontend and evaluator review; concrete evaluator ambiguities repaired before freeze | [App review](PEER-REVIEW.md), [review-tool review](EVALUATOR-PEER-REVIEW.md) |
| Review tools | 43 lexical/scope tests and 23 integrity-checker tests passed | [Evaluation freeze](evaluation-freeze-01.json) |
| Historical packages | Completed v3 0.14, held v3 0.13 and completed v1 0.12.2 exports pass new pinned replay with original bytes unchanged | [Legacy receipt](legacy-replays-01.json) |
| Native offline workflow | Four scripted entries saved/applied; entry-owned tables, independent reading, original export, clean relaunch and explicit paused recovery checked | [UI walkthrough](MACOS-UI.md), [scripted result](SCRIPTED-RESULTS.md) |
| Recovery integrity | Same 24 non-manifest files; only generation/revision/phase changed; pinned whole-chain replay passed | [Recovery receipt](native-scripted-recovery-01.json) |

Failed intermediate frontend and review-tool runs remain beside their corrected
passing receipts. The frontend failure was a case-insensitive module-name collision;
the validator now has a distinct filename. The review helper now inventories
unmatched numeric mentions and marks ambiguous scope/identity for reading. The old
four v3 entries are a known regression corpus, not new model evidence. No automatic
quality verdict is supplied. [Protocol](PROTOCOL.md) and [rubric](RUBRIC.md) remain frozen.

## Identified package

- Archive: `ReservoirScopeTauriPreview-0.15.0-macos-arm64.tar.gz`.
- Archive SHA-256: `b02018a34fb1d80a4801b9c070354071985dae977546cbee87aa7379cc31909c`.
- Executable SHA-256: `18949732cf48c926003ffcf7b5b216bccc32ea071d0bff8a411e841eaba123d5`.
- [Build](package-build-01.json), [archive identity](archive-check.json),
  [initial package receipt](qualification-before-ui.json),
  [final package receipt](qualification-final-02.json) and
  [documentation continuity](source-continuity-final-02.json).

Source was unchanged through the build. The package has 46 files and the local ad-hoc
signature verifies; this is not notarization or public release acceptance. Prior
0.14 archive and native 0.15.0 build 21 remain separate and preserved. Final
post-build documentation identity is recorded separately.

Next: execute a newly identified bounded v4 model episode when its prospective host
admission passes, then read every response for literal measurement claims and freely
chosen continuity. Do not retry this refused episode, relax its threshold or call
scripted prose an accuracy result. Longer model runs, provider context coverage,
Windows/Linux, measured GPU/power, physical sleep/power-loss and broad human
acceptance remain unqualified. The old 0.12.0 two-hour evidence does not transfer here.
