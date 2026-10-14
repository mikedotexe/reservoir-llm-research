# Preview 0.4.0 — resumed macOS checks, October 12, 2026

This supplement records new agent-operated UI checks; it does not replace or extend the original October 11 receipts implicitly. Actual 0.4 binary SHA-256: `a905dbe673acf047fe7a26c2d03562d30569d1cbb6fd567ec0d953d72fee2400`. Host macOS 27.0.1 (26A434), arm64.

- Controller reader displayed the separate regulated study and its explicit absence of a retained noise vector.
- Native Save exported the accepted controller recording. The filename editing action produced `example-regulatio0.4-controller-export.json-controller.json`; the resulting bytes were compared, rather than assuming the intended filename. Exact 52,776,851-byte source match and independent unchanged-Swift verification passed; see `2026-10-12-export-supplement.json`.
- Native Open imported this exported record. Library reported successful verification/publication and increased its total from 23 to 24 entries.
- Reimporting the same file reported that the exact bytes already existed; no second managed entry appeared.
- Metadata search for controller showed the imported regulation record and its enabled Verify & open action. Activating it completed numerical verification and opened the managed 600-frame baseline controller track at step 1, with outcome, seed, no-reservoir-state distinction, evaluation window and original-byte export available.
- **Upgrade defect found:** the existing persisted index still classified the bundled controller as unknown/not included, with opening disabled. The 0.4 query only initialized an empty bundled catalog and did not refresh it after an application upgrade. This is a failed upgrade behavior, not a passed check. The 0.5 repair refreshes bundled metadata transactionally when package/resource identities change; qualification is recorded separately.

No live model or feed was connected. No collaborator or steward acceptance is implied.
