# Prospective 0.12.2 real-model export check

**Unexecuted preparation.** The intended real-model rehearsal moved from 0.12.1 to the distinct 0.12.2 presentation-fix package before any real-model result was claimed. Wait for the exact native export, package executable SHA-256, configured model and owned loopback endpoint from the parent task. This document neither starts a service nor qualifies a result.

Reuse the unchanged [offline checker](../2026-10-13-reading-0.12.1/check_real_model_export.py), SHA-256 `b09e46d46eb7e7fe7aa9ba3c519881af72d90867a3d8d91c016f93b2802fb525`. Its required `--expected-executable-sha256`, `--expected-model` and `--expected-endpoint` arguments bind the actual selected package and configuration; the script has no hardcoded app-version dependency. Supply the actual 0.12.2 executable, not the pinned 0.12.1 synthetic verifier. Use a fresh output directory for the 0.12.2 result.

The original [prospective method](../2026-10-13-reading-0.12.1/REAL-MODEL-EXPORT-CHECK.md) remains unchanged as the earlier preparation record (SHA-256 `4dbe8ba1f0b525c351853799d2e9b5c24efc2c7e862aa3531a955fd5d7c9a8d4`). Its 0.12.1 placeholders are superseded only for package selection by this note. The owned-model helper, staged-model identities and reviewed model selection remain in their existing 0.12.1 validation directory; they describe isolated model assets/runtime preparation, not an app package result.

Independent read-only core review found no concrete checker blocker. It checked unique save/application identities, next-step semantics, latest earlier applied full-text memory, and truthful zero-journal handling. The reviewer did not execute the checker or contact a service. Source review is not a runtime pass.

Retain the actual 0.12.2 CLI result, exact package and bundle identities, journal/save/application/memory evidence, real returned stop reason/completeness, and a separate qualitative reading of the prose. Owned Ollama request-body logging is disabled; app-retained prompts and timing must not be described as independent wire-level provider receipts. Integrity, successful feedback, readable prose and accurate claims remain separate conclusions.
