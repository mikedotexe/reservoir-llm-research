# Pointer baseline on unchanged 0.12.2

This note consolidates the parent agent's direct native UI observations on 2026-10-13. The author of this note reviewed source and receipts, but did not operate the app during these checks. It records a mixed baseline, not a confirmed JavaScript defect or a causal repair result.

The [baseline identity](pointer-baseline-identity.json) binds the app executable to SHA-256 `2fa824855d1172ebf707b4f1ce5f50d2c3eb74ab4aeeb437d41dc566f818db8d`, the unchanged 0.12.2 package. The [baseline process identity](pointer-baseline-process.json) and [quit observation](pointer-baseline-quit.json) identify this subsequent controlled session. The quit observation records process absence at 19:53:00.296586 UTC and an unchanged executable. No model service or new numerical run was used for these baseline checks.

## Earlier reported behavior

The [0.12.2 real-model UI account](../2026-10-13-reading-0.12.2/REAL-MODEL-UI.md) records the earlier difficulty after a short minimize interval. The retained session had reached 121 steps and four journals; an older step-30 journal remained selected with Follow latest off. Repeated accessibility and screenshot-grounded pointer attempts on Follow latest, Refresh this page, and export did not perform their expected actions. Some interactions scrolled the page. Keyboard navigation with Tab, Space, and Return subsequently worked without relaunching the app.

These observations establish an interaction problem in that particular session. They do not establish whether the cause was an app event handler, native focus or menu state, minimize/restore state, or the computer-use interaction path. A frozen renderer or backend was not demonstrated.

## Controlled checks before the new package

The parent then reported the following on the same unchanged 0.12.2 executable:

1. On fresh launch, ordinary pointer navigation to Experiments worked.
2. After restoring the retained v1 session, pointer selection of the step-30 journal worked, and Follow latest selected the step-120 journal.
3. A minimize followed by rebinding through the computer-use `getApp` API reproduced a pointer failure once; keyboard input still worked.
4. During an attempt to find an explicit restore action, the native Window menu remained open after Escape. Finder Open appeared to restore the app, but the native menu remained in the tool's UI state. Explicit accessibility cancellation of that menu was followed by a successful Follow latest pointer action.
5. In a further controlled repetition without opening that menu, selecting the step-30 journal worked; Cmd-M, `getApp`, and a Follow latest pointer action also worked on unchanged 0.12.2, without Finder reopen.

The native menu state explains a concrete obstruction in one investigated episode. It is not evidence that the same menu caused the earlier real-model-session failures. The successful final repetition means an intermittent source-level pointer defect was not confirmed by this baseline.

## Scope of the subsequent source change

[POINTER-SOURCE.md](POINTER-SOURCE.md) records the source audit and pinned Tao/Tauri references. The new macOS `RunEvent::Reopen` handler explicitly unminimizes, shows, and focuses the existing main window. It is desktop lifecycle hardening: it performs no automatic session resume, provider request, or numerical action. This baseline does not demonstrate that the handler repairs the historical pointer failures.

The next package must be checked with actual pointer interactions through repeated minimize/reopen, older-journal selection, Follow latest, and a native dialog. A successful check can qualify that tested workflow while leaving the historical cause undetermined. Keyboard success alone is not a substitute for the requested pointer check.
