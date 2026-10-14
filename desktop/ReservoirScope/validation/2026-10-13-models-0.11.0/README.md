# 0.11.0 — explicit local models and bounded generation

Executed October 12, 2026 locally / October 13 UTC, on this Apple-silicon Mac.
This receipt covers finite local-model transport and its session/save gates. It does
not qualify a real model, long-running sessions, Windows/Linux, or scientific benefit.

## Delivered

Blank-by-default loopback endpoint/model configuration, exact inventory readiness,
finite generation in stages 3/4 and independent D–H/pairs, cancellation, retained
failure outcomes, and bounded rejected-response recovery. Commands run through the
Rust backend; the WebView has no direct model-network capability. Requests neither
start a server nor download a model. The app preserves the actual journal publication
and readback gate before next-step feedback.

## Automated and independent evidence

| Check | Executed result | Evidence |
| --- | --- | --- |
| Frozen reference | 180 native sources, 43 resources, one fixture verified | `reference-integrity.log` |
| React/frontend | 264 tests; TypeScript and production build pass | `frontend-full-shipping.txt`, `frontend-build-shipping.txt` |
| Rust core | 140 tests; strict all-target Clippy passes | `core-tests.log`, `core-clippy.log`, `core-checks.json` |
| Rust desktop | 125 tests; strict all-target Clippy passes | `desktop-tests.log`, `desktop-clippy.log` |
| Final Stop-message correction | 10 relevant tests rerun; strict Clippy passes | `desktop-model-cancellation-final.log`, `desktop-clippy-final.log` |
| Python tooling | 13 tests pass | `python-tests.log` |
| Supplied-response records | 63 originals pass Swift and Rust; 567 corruptions rejected by both; six allowed raw-diagnostic controls accepted by both | `fixture-conformance-final.json` |
| Actual dialog exports | Four exported files pass both verifiers; 26 corruption checks rejected; recovered complete record byte-identical | `initial-ui-export-conformance.json`, `final-ui-export-conformance.json`, `recovery-export-conformance.json` |
| Packaged archive/resources | All 46 archive files match package bytes/modes; 39 canonical and 42 packaged resource files verified | `archive-and-resource-check.json` |

There are **542 distinct tests** in the full automated suites above; the final ten
are a focused rerun after the small Stop-message correction, not ten additional tests.
Core, frontend and transport code are unchanged after their complete passing suites.
The final backend change selects the accurate cancellation reason; its relevant
model lifecycle tests were rerun. Full-suite and focused-source identities remain
separate. No numerical tolerances or native verifiers were changed.

The first conformance checker incorrectly expected cancelled stage `rawReply`
diagnostics to be rejected. Both implementations permit that inert field without
feedback. Its original failed expectation is retained in `fixture-conformance.json`;
the final checker tests prohibited accepted `reply` and separately tests allowed raw
diagnostics. All original generated records passed on the first run too.

## Actual application checks

The [packaged walkthrough](macos-ui.md) distinguishes the initial and final binaries.
The initial package demonstrated explicit readiness, an F run with two physical
journal saves, observed/applied boundaries 3→4 and 6→7, reread memory in the second
request, Library saving, native exports, held-clock Pause and cancellation. It exposed
an inaccurate cancellation reason. The package and original cancellation are preserved.

The final binary demonstrated the repaired cancellation reason, rejection of a late
response, zero new journals, native export, clean quit/relaunch, idle recovery and
byte-identical export of the earlier completed record. These checks used one owned
fake provider on an ephemeral loopback port, with one GET and four POST requests total.
The provider was stopped after testing. `owned-provider-export-evidence.json` binds
exact prompts, response/save evidence and export hashes; the request log is retained.

A local checkpoint later labels the completed session stopped because the test
explicitly Reset it. Its portable experiment remains completed and its bytes unchanged.
Inspection of recovery starts neither the old numerical session nor a provider request.

## Candidate identity

Final app binary SHA-256:
`a7f81d7570401219430e1f2bb93c440bd54c283be5be2d1c82e4480ed6dcb6fd`

Final archive: `ReservoirScopeTauriPreview-0.11.0-macos-arm64.tar.gz` (101,794,614 bytes).
SHA-256: `4582e01213a0bef9ac4f9b4071d6a5e3be38a60f92233284715b8e75240b6eb1`.

[Qualification receipt](qualification.json) records actual toolchains, signing and
identities. `source-before-build.json` binds the initial build; `source-before-final-build.json`
binds the repair. `final-package-before-ui.json` and the archive/resource check prove
that UI testing did not alter shipping files. Documentation-only follow-ups are
identified separately in `source-continuity.json`. The initial archive remains a
separate historical candidate and is not the final delivery.

## Unqualified gates

Real-model interoperability/capacity, public signing/notarization, minimum macOS 14,
Windows/Linux execution, collaborator acceptance, full accessibility, measured
latency/FPS/GPU/power/memory, sleep/minimize soak, physical crash/disk-full behavior,
and sustained sessions remain unqualified. Unsupported codec/parser inputs remain
explicitly incomplete or blocked; no feedback is fabricated. No live Being service,
workspace, producer or research schedule was accessed or changed.

Next: versioned sustained personal sessions while open or minimized, bounded storage,
automatic durable journal saves, and journal reading independent of the live cursor.
