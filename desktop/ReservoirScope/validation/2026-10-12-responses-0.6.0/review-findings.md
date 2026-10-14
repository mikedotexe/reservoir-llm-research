# Response compatibility findings before packaging

The first independent 33-case run exposed two native integer-format differences.
The unsigned-limit decimal/exponent tokens were accepted by Rust but rejected by
Swift. `response-conformance-1.json` retains that failed run; its expected-accept
assumption for those two cases was also wrong. Rust now applies a representability
check before exact lexical integer conversion; no numeric tolerance was changed.
The 36-case second run passed, including accepted wide decimal values and rejected
unsigned-limit floating forms. Plain full-width unsigned integers remain intact.

A later independent source review found that Swift string equality is canonical:
NFC/NFD spellings of the same identity must not become a new session or command.
Using the binaries identified in `response-conformance-2.json`, the reviewer ran
three temporary input pairs through both unchanged Swift and Rust helpers:

- Canonically equivalent session ID plus changed source hash: Swift rejected;
  Rust accepted as a different identity.
- Canonically equivalent command ID plus changed boundary reason: Swift rejected;
  Rust missed the overlapping immutable boundary and accepted.
- Canonically equivalent reason text alone: Swift accepted the same boundary;
  Rust rejected it as changed text.

The temporary probe files were removed after the comparison. This account records
the observed probe, not a claimed raw-output capture. The repair normalizes text
only for equality and internal matching. Retained strings and original exported
bytes remain unchanged. The final independent oracle includes explicit regression
pairs for these cases and canonical identity within a bundle. Final focused tests
and conformance receipts establish the repaired source; earlier passes are not
silently extended across this change.
