# Retained response reader contracts

`response.rs` reads two distinct native application contracts. It does not run a
new simulation or replay a live engine. The desktop ownership and UI contract are
described in `desktop/ReservoirScope/RESPONSE-EVIDENCE.md`.

## Native immediate boundaries

`NativeResponse::decode` accepts `research.native_action_response.v1`, with the
native loader's exact subject, scope and clock declarations. The wrapper must
contain exactly its eight allowed keys, including explicit null `fill` and
`reference_basis`. Receipt and identity fields reject unknown additions. Files
are nonempty and at most 8 MiB; each holds 1–1024 receipts with 128-coordinate
directions. Source hash and identifier bounds follow the native contract.

All eleven retained statuses remain distinct. `applied` and `no_op` create
inspectable state frames. `headroom_rejected` participates in boundary validation
and replacement immutability but remains an event with zero change, not an applied
frame. Admission, terminal and failed events cannot carry before/after/delta
geometry. A valid bundle may contain events and no applied frames.

At a boundary, `before` is the ordinary result of that **same** successful step,
not an independently evolved counterfactual. The native Float32 subtraction
`after - before` must match every retained delta bit, including the sign of zero.
The full-vector L2 is checked at native tolerance
`1e-12 * max(1, expectedL2)`. Maximum absolute delta must match the Float32 maximum
exactly. No-op/rejected changes are zero; headroom rejection additionally requires
zero attenuation, L2 and maximum change, and no clipping flag. Bounds, noise,
effective leak, pulse identity and required measurements follow the source loader.

All boundary identities agree within a bundle, successful-step IDs increase
strictly, and boundary IDs cannot repeat. A replacement with the same native
identity must retain its source hashes, preserve every overlapping boundary
receipt and not move the last successful step backwards. A new native identity
starts an independent batch. Missing intermediate successful steps are not
invented. The reader makes no recovery-time, future-effect or stability claim.

## Float and integer decoding

Native float arrays and controls are parsed directly from raw numeric tokens into
Float32, rejecting unrepresentable nonfinite values even on event metadata. The
backend promotes those Float32 values exactly into Float64 before JSON IPC;
serializing a short Float32 decimal directly would lose that exact displayed
value in JavaScript. Original JSON bytes are stored separately and never rebuilt
from those display values.

The native `JSONDecoder` accepts some integral decimal/exponent tokens for integer
fields. Response-local `RawValue` deserializers preserve those original tokens and
produce the integer lexically, so an identity never acquires Float64 rounding.
For decimal/exponent tokens only, a separate Float64 representability gate matches
the observed native type boundary before exact conversion:

- Plain `18446744073709551615` is accepted as UInt64.max.
- `9007199254740993.0`, `9007199254740993e0`, `9223372036854775808.0` and
  `18446744073709549568.0` retain their exact integer values.
- Near the upper endpoint, `18446744073709551615.0` and
  `18446744073709551615e0` are rejected by the native typed decoder and this reader,
  although the corresponding integer token is representable.
- Fractional, negative unsigned and overflowing values fail. Successful steps,
  supplied rehearsal clocks and boundary waits cross IPC only as decimal strings.

The initial independent receipt recorded the endpoint mismatch; its successor
records the corrected comparison. Neither historical qualification file is
rewritten. These are tested native-decoder cases, not a claim of universal JSON
implementation equivalence.

Native Swift strings compare by canonical Unicode equivalence. Response-local
identity, receipt-text, frame-key and source-hash-key comparisons follow that
rule; an NFC/NFD spelling change cannot become a new session or bypass immutable
overlap checks. A reason changed only to an equivalent Unicode spelling remains
equal. Original text and bytes are not normalized for display or export.
Canonically duplicate source-hash keys within one object are explicitly rejected
as ambiguous rather than selecting among conflicting aliases; this is a bounded
reader restriction. The independent comparison adds canonical identity, command,
reason and within-bundle identity cases after retaining the initial review
finding and earlier binary identities.

## Retained simulated-parent pair

`SimulationResponse::decode` requires the exact retained SHA-256
`fe97623dcccb4b089ce4e0a1b5cc99ec902793efed8fbfcf1041ce8c865e9100` and at most 1 MiB.
It accepts only the native `research.state_response_preview.v1` fixture contract:
65 paired 128-coordinate frames, sample indexes 0–64 and original boundaries
200–264. Provenance strings cannot be relabeled as live/native measurements.
Wrapper and frame fields are exact, with null fill and reference basis.

Each retained difference is checked against intervention minus control at `1e-14`;
full-vector L2 uses `1e-12`. Boundary zero must already contain the declared
coordinate-zero displacement. Peak/initial separation is checked at `1e-10`.
The return claim is recomputed from the path: first starting sample after zero
with eight consecutive separations at or below ten percent of initial separation.
The declared displacement scale stays fixed at ±0.001; no per-frame normalization
or fresh simulation occurs. The simulation's coordinate order is not established
compatible with the native node identity, and its boundaries supply no measured
seconds. Clipping and the unestablished unclipped derivative validation remain
explicit limits.

`decode_with_hash` permits a supplied expected identity for independent synthetic
mutation tests. The desktop path always uses `decode` with the compiled retained
identity and opens external files only as native rehearsal receipts.

## Ownership, tests and oracle

The backend retains at most four immutable handles and 32 MiB of original bytes.
It validates a candidate and any requested native replacement before insertion;
a failed read or replacement leaves prior handles and bytes untouched. Scalar
summary timelines/events are bounded by 1024 receipts; detailed coordinate arrays
are fetched only for the selected frame or event. Original-byte export snapshots
remain valid through handle closure and use the shared atomic export helper.
There is no file polling, automatic following, Library import or provider call.

Focused checks: eight core tests and seven backend tests passed. They cover native
Float32 differences and signed zero, native statuses/headroom boundaries, malformed
provenance/schema/vectors, numeric bounds and wide integer tokens, immutable
replacement, full simulation summaries, exact Float32 promotion, invalid candidate
retention, handle limits, event-only evidence and byte-identical exports.

The root-owned independent harness compiles unchanged native
`NativeActionResponse.swift` and the data-only portion of
`StateResponseExperience.swift`. The Rust `response_oracle` example accepts:

```text
response_oracle native FILE [PREVIOUS_FILE]
response_oracle simulation FILE [EXPECTED_SHA256]
```

It emits compact identities, scalar summaries and numeric digests. Each digest
encodes optional arrays with a presence byte, little-endian UInt64 length and all
Float64 bit patterns; optional scalars use a presence byte and one Float64 pattern.
Native Float32 numbers are promoted exactly. The independent suite compares
canonical values and semantic rejection/replacement cases; it does not certify
fresh simulations, live systems, Windows/Linux execution or full desktop parity.

Focused commands from the project root, with the configured per-process SDK
environment (`DEVELOPER_DIR` and `SDKROOT`) on this host:

```sh
cargo test --manifest-path desktop/ReservoirScope/Cargo.toml --locked -p reservoir-core --test response
cargo test --manifest-path desktop/ReservoirScope/Cargo.toml --locked -p reservoir-scope-desktop response::tests
cargo build --manifest-path desktop/ReservoirScope/Cargo.toml --locked -p reservoir-core --example response_oracle
```
