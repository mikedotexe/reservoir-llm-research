# 0.16.0 · Provider prompt-count evidence

This tranche retains optional provider-reported prompt input counts without changing
the open writing invitation, numerical mechanisms or durable feedback rules. The
new value appears inside a selected journal's closed **Evidence** section, beside
the separate requested context capacity. Received-response inspection also retains
metadata from incomplete attempts, explicitly separate from saved journals.

The [contract](../../../../shared/reservoir-scope/provider-prompt-evidence.md)
defines omission, malformed values, exact integer representation and the limits of
the evidence. A provider count is not proof of complete context processing or
accurate writing. No real model is contacted in this tranche.

## Executed source evidence

- [Frontend](frontend-checks-05.json): 359 tests across 39 files and TypeScript/Vite
  production build passed. The source inventory is captured after these checks;
  the successful package build compared it with its exact inputs. Existing large-chunk
  warning remains; this check measures no GPU performance.
- [Focused core](core-focused-01.json): 31 tests passed, including seven new
  response-evidence tests and unchanged historical prompt/budget/reference checks.
- [Focused backend](backend-prompt-evidence-tests-02.json): eight tests passed,
  covering exact raw integer parsing, malformed/duplicate optional metadata,
  unchanged completion gates, synthetic HTTP, save/export/recovery, incomplete
  attempts, bounded inspection and re-anchored mutation failures.
- [Old-reader probe](old-reader-probe-01.json): pinned 0.15 ignores the additive
  journal-only field and passes two deliberately inconsistent/malformed copies. Those passes
  do not qualify the new evidence. Original historical exports stay unchanged.
- [Full Rust suite](rust-checks-01.json): 181 core and 190 desktop tests passed;
  two existing opt-in tests remain ignored. Strict all-target Clippy passed for
  both crates. The recorded Rust source inventory was unchanged through execution.
- [Independent review](PEER-REVIEW.md): no remaining blocker; the new recovery
  output-count precision edge was corrected before the full checks.

## Package and native workflow

The [prospective protocol](PROTOCOL.md) and [frozen plan](prospective-freeze-01.json)
define five synthetic replies, exact run limits and cleanup. The
[old package preservation receipt](prior-package-preservation-01.json) keeps the
0.15 archive and pinned verifier distinct. The first built candidate's native launch exposed a stale hardcoded **0.15** header.
[That finding](candidate01-ui-finding.json), its original archive and pinned executable
remain preserved. The header now reads the package version directly, with an
[independent review](header-peer-review-01.json) and repeated frontend checks. A
separately identified **0.16.0-r2** archive passed [source-bound build](package-build-02.json),
[archive readback](archive-check-02.json), local ad-hoc signature verification and
[actual native checks](MACOS-UI.md). [Four historical bundles](reader-compatibility-02.json)
passed unchanged and both altered-metadata cases were rejected by its exact binary.

The five-response native run saved and applied four journals at the expected next
steps, then held the incomplete fifth reply. Wide, absent and unusable counts stayed
attached to their entries. [Independent export analysis](NATIVE-EXPORT-RESULTS.md)
confirmed all five request/prompt/response joins and exact prior-text memory. After
clean quit and provider shutdown, explicit offline paused recovery preserved all
27 non-manifest files; [recovered replay](recovered-export-evidence-01.json) and
[byte comparison](recovered-export-equality-01.json) passed. No retry, skip or budget
extension was used.

The [actual old/new-reader comparison](actual-bundle-reader-comparison-01.json)
is distinct from the journal-only negative probes: pinned 0.15 rejected this new
bundle at its checkpoint hash, while r2 passed. Old-reader behavior depends on the
retained state and cannot qualify the new optional evidence.

The app remains paused with a synthetic journal readable and technical disclosures
closed. The owned fixture stopped explicitly; its [retained files](fixture-run-01/retention.json)
record one inventory request and five generation requests. No real LLM was run.

## Limits and next work

This change supplies inspectable bookkeeping. It does not fix the voluntary
measurement errors observed in the [preceding v4 writing episode](../2026-10-13-v4-writing-episode02/REAL-MODEL-RESULTS.md),
assess emergence, or certify provider attention. It adds no mandatory subject,
metric citation, response form or prose-quality acceptance gate.

Longer real-model continuity, all-platform packaged acceptance, physical crash/sleep,
broader accessibility and measured GPU/energy behavior remain separate work. The
next natural tranche is a prospectively bounded longer writing episode using this
evidence, with saved journals, prior-text continuity and resource measurements
reviewed separately.
