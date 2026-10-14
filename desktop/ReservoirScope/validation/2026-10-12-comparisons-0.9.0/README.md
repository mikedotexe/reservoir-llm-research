# Matched comparisons — 0.9.0 qualification

This directory records executed engineering checks for the macOS candidate, separate
from cross-platform qualification and human acceptance. Native reference 0.15.0
build 21, canonical examples and verifier thresholds remain unchanged. No model
service or Being workspace is contacted.

## Retained initial mismatch

`fixture-conformance.json` is the first full independent run: 52 of 58 original
Rust records passed both engines; six quiet observation records failed Swift prompt
reconstruction while passing Rust. All 608 individual altered-record controls were
rejected by both. The failing corpus remains in `target/qa/0.9-comparison-fixtures`.
This receipt is not a successful compatibility claim. Later repair and execution
receipts are additive.

The diagnostic found the same decoded IEEE-754 bits (`3febdf19934efcbd`) in both
languages. Plain Swift formatting prints `0.87098387`, while the native prompt's
locale-aware `en_US_POSIX` formatting prints `0.87098388`. The retained observation
is unchanged; the discrepancy concerns exact prompt text, not numerical tolerance.
The diagnostic and native formatter vectors qualify this distinction separately
from the generated comparison corpus.

## Evidence boundaries

Core and independent replay checks establish numerical, prompt and file contracts
for the tested corpus. Backend tests separately cover physical journal publication,
readback, per-arm memory, retry, bounded partial-boundary checkpoints and reopening
with a new session state. They do not simulate physical power loss. Frontend tests
cover view state, arm identity, stale results and source labels. Actual packaged UI
and native-dialog exports are recorded separately in `macos-ui.md`.

The source/package/archive inventories bind the candidate. Signing status comes
from the receipt tool; no notarization, public distribution, minimum-macOS testing,
Windows/Linux execution, measured GPU efficiency or collaborator acceptance is
inferred. The 600-observation field-only controller creation workflow, model
connections and sustained journal loop remain following tranches.

## Final repaired candidate

The shared native-compatible prompt formatter passes 1,173 retained Swift vectors,
including 62 that distinguish ordinary binary printf. Final full checks passed 232
frontend, 128 core, 92 desktop and 9 Python tests; both strict Clippy invocations pass.
`fixture-conformance-fixed.json` passes all 58 regenerated originals in both engines
and rejects all 608 altered-record instances in both. `fixture-manifest-fixed.json`
binds the final corpus. Earlier failing evidence remains intact.

The actual package walkthrough and native-dialog exports pass the separate checks
described in `macos-ui.md`; recovered portable bytes are unchanged. See
`qualification.json`, `source-continuity.json`, `package-resource-check.json`, and
`archive-check.json` for identities and remaining unexecuted gates.
