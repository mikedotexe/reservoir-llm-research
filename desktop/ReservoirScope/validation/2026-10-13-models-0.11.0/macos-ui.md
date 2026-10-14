# Agent-operated macOS packaged walkthrough

These are observed UI actions in pristine Tauri application bundles, using native
accessibility control. They are not collaborator/steward acceptance or a GPU benchmark.
Host: macOS 27.0.1, Apple silicon. No developer server or embedded test-driver plugin.

## Initial candidate

Bound by `package-before-ui.json`; binary `ffd9e314234c8e5e49dca8595a221147d1b804cc36bcc98a8598e89e36026347`.

- Launch shows 0.11.0. Fresh starts idle. Local backend selection reveals empty
  endpoint/model fields, context 4096, output limit 256 and temperature zero.
- Owned provider observed zero requests before explicit Check. Explicit Check found
  `reservoir-fixture:0.11` at `http://127.0.0.1:56117`, retaining the fake digest.
- F standalone, seed 20260909, seven steps, cadence three: Create stays at zero.
  Run reaches step three and waits for a durable journal save; Step and export are
  disabled. The accepted response is not yet a committed journal.
- Save right journal durably moves the durable checkpoint from zero to three. Step
  four applies the saved semantic input. Turn inspection shows observed/applied 3/4,
  completed WRITE, actual request order, configured/returned model and saved receipt.
- Run reaches six; the second prompt contains the physically reread first journal.
  Save then Step reaches seven with two journals and the second application at seven.
- State and separate fill widgets report WebGL2 rendering; exact values and clocks
  remain labeled. This observation does not measure visual correctness, FPS or power.
- Save to Library succeeds. Native Save dialog creates `model-f-complete-7.json`.
- Reset creates a new generation. A held HTTP request stops clock at three. Pause
  leaves it awaitingLanguage. Cancel request and stop terminalizes it; a subsequent
  provider reply creates no journal, accepted reply or application.
- The cancelled record's reason incorrectly mentions an unresolved journal save.
  The record is exported as `model-f-cancelled-initial.json`, saved to Library, and
  the app quits cleanly. That wording issue triggers a small final rebuild.

Complete session: `session-1791872447091-18536-1`.
Initial cancelled session: `session-1791872614953-18536-2`.
The initial candidate archive and receipts remain separate.

## Final candidate

Bound by `final-package-before-ui.json`; binary `a7f81d7570401219430e1f2bb93c440bd54c283be5be2d1c82e4480ed6dcb6fd`.
Only the Stop reason and its assertion changed in runtime/test source; documentation
clarifications are separate. Existing successful workflow observations are attached
to the initial binary rather than relabeled as new executions.

- Relaunch starts idle, with blank model configuration. Creating the same explicit
  F test performs no request and does not require a prior readiness check.
- Run reaches a held request at step three. Stop retains cancelled status, zero
  journals, no accepted reply or application, and the corrected reason:
  “Explicit stop while the language request remained unresolved.”
- Releasing the fake provider after Stop does not change those outcomes.
- Native Save creates `model-f-cancelled-final.json`; Save to Library and Cmd-Q succeed.
- Relaunch starts no session. Explicit recovery lists the saved experiments, and
  inspection/export does not cause a provider request.
- The completed seven-step portable snapshot is exported as `model-f-recovered-7.json`.
  It is byte-identical to the original complete export, SHA-256
  `112ac08ad3f2c973b4bed7da6cb1bd4684224cf27ea9bfad331fd0e2ae2f1624`.
  Its local checkpoint phase is stopped following the earlier explicit Reset; the
  portable experiment outcome remains completed.

Final cancelled session: `session-1791872951987-20655-1`.
The final app is left idle with the completed recovery entry visible. The owned fake
provider has been stopped. Its log shows one explicit inventory GET and four generation
POSTs across both candidates, with no additional requests during relaunch/recovery.

## Limits

No real model, unmatched/matched provider comparison UI, readiness-cancel dialog,
unsupported-response recovery UI, operating-system minimize/sleep soak, hardware
performance benchmark, minimum macOS, other OS, or human acceptance was executed.
Relevant automated tests and independent supplied-response checks have separate receipts.
