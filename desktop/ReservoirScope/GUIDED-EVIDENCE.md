# Portable guided evidence evaluator

The 0.4 evaluator in `crates/reservoir-core/src/guided_evidence.rs` ports the native
`GuidedEvidenceEvaluator` A–H and observation-comparison rules. It produces
mechanical observations from a verified action-record prefix. It does not verify
records itself, judge journal quality, establish a provider call's authenticity,
or implement the separate sustained-input regulation-window evaluator.

## Integration contract

```rust
pub fn evaluate(
    record: &actions::ActionComparisonRecord,
    cursor_step: usize,
) -> LessonEvidence;
pub fn unopened() -> LessonEvidence;
```

The caller must accept the typed record through its numerical/structural verifier
before calling this API for user-facing evidence. The evaluator does not read raw
JSON, follow recorded paths, access live systems, or contact providers. Deliberate
invalid mutations are used only in the test harness to exercise evidence gaps.

`LessonEvidence` and `LessonEvidenceState` derive `Clone`; the state also derives
`Copy`. Serialized output is:

```json
{
  "state": "Not reached yet",
  "observation": "Open an example to inspect recorded evidence.",
  "evidenceSteps": []
}
```

The five state strings match the native display values exactly:

| Rust variant | Serialized/native display value |
| --- | --- |
| `NotYetObserved` | `Not reached yet` |
| `Observed` | `Observed` |
| `DifferentResult` | `Different outcome` |
| `Incomplete` | `Incomplete evidence` |
| `NotApplicable` | `No matched comparison` |

The cursor refers to the native **right-arm evidence prefix**, even when the
caller is displaying the left track. Evaluation selects the last retained right
frame at or before the cursor, then uses frame, action and journal prefixes ending
at that selected step. The API is stateless: rewinding produces the earlier
prefix's result. A zero cursor or empty prefix returns `unopened()`; a cursor
beyond the recording uses its final retained right frame. Evidence step numbers
refer to actual observed events, not requested frame indices.

The desktop can cache these small DTOs for the bounded accepted recording and
attach the corresponding result to each frame response. The existing frame
request identity and generation controls should govern surface, fill and evidence
together. The display should identify the right-prefix meaning rather than imply
that changing the displayed track changes which experiment received a mechanism.

## Preserved rules

| Subject | Evidence rule and limit |
| --- | --- |
| A · Input and state | Current external-input RMS distinguishes active/quiet; lower state RMS than the previous retained frame under quiet input establishes the reported decay observation. |
| B · Recurrence | Both prefixes must have matching step sequences. The first state RMS difference above `1e-12` identifies divergence; a single arm cannot isolate recurrence. |
| C · Sensory measurement | Requires the selected frame's sensory measurement; states are compared separately from the sensory spectrum. |
| D · Journal output | Requires a completed action with a saved receipt. A paired prefix can establish unchanged recorded states; a single arm is explicitly qualified. |
| E · Reservoir return | Requires the first saved semantic action, a reached application step and a frame with the matching semantic action ID. Saving at 30 cannot establish application at 31 before that cursor is reached. |
| F · Journal memory | Requires the earlier journal identity, earlier observation step, matching memory text and inclusion in the prompt. Prepared/scripted, prepared-but-unsubmitted and submitted-model contexts remain distinct. Inclusion establishes exposure, not improved writing. |
| G · Action choice | A completed WAIT must lack journal/save receipts. A retained all-WRITE model run remains a valid observation; an expected WAIT is not imposed on the result. |
| H · Regulation | Requires fill, retention used and a controller receipt. Reports next applied retention and native limit checks (`0.82`/`0.995`) without claiming target attainment. |
| Observation comparison | Requires both matched prefixes and reached opportunities in both arms. Reports retained statuses and state agreement; different wording is not an improvement score. |

Native observation text and ordering are preserved, including native incomplete
states for inconsistent receipts. An invalid numeric stage cannot occur in an
accepted record; a defensive fallback returns incomplete evidence for an
independently constructed unsupported stage. That fallback has no Swift enum
counterpart and is not an accepted-record parity claim.

## Checks executed

The focused Rust integration suite contains **14 passing tests**. It covers
canonical A–H boundaries, every cursor and rewind of selected scripted/model/
observation recordings against a physically truncated prefix, future frame/action/
journal mutation invariance, delayed application, recurrence tolerance, absent
arms, failed/cancelled saves, exact memory linkage, WAIT receipts and controller
bounds. One initial test wrongly assumed A's recording ended at its authored
checkpoint 30; it was corrected to use the actual final retained frame (120).
The implementation did not change for that test correction.

Run the suite from `desktop/ReservoirScope`:

```sh
cargo test --locked -p reservoir-core --test guided_evidence
```

The independent script `scripts/check_guided_conformance.py` compiles the unchanged
native `GuidedLessons.swift` and current EssentialsCore sources into a temporary
Swift harness. It builds the separate Rust test example
`crates/reservoir-core/examples/guided_evidence_oracle.rs`, then compares exact
state, observation and evidence steps for each requested cursor. It processes
records sequentially, avoids live systems and never writes canonical examples.
Original records must verify in both engines. Mutants bypass verification only
inside the harness; a matched incomplete result is not acceptance of that mutant.

The executed run passed **58 cases / 2,507 cursor results**: 22 original retained
records, 35 deliberate evidence mutations and the unopened state. All 22 originals
verified in Swift and Rust. Mutations include missing/misaligned arms, missing
sensory/control data, failed saves, future or unlinked applications, altered
memory, prepared model context, invalid WAIT receipts and failed observation arms.
The receipt was written with exclusive creation to
`target/qa/guided-evidence-conformance-01.json`; existing qualification receipts
were not changed.

To make a fresh local receipt on macOS, from `desktop/ReservoirScope`:

```sh
python3 scripts/check_guided_conformance.py --output target/qa/guided-evidence-conformance-new.json
```

This host required process-local `DEVELOPER_DIR` and `SDKROOT` pointing to its
installed Xcode SDK. No global developer-directory or host setting was changed.
The retained receipt includes native/Rust source hashes, Swift core source hashes,
input hashes, Swift version, per-case outcomes and explicit test limits. Native
compilation emitted the existing Accelerate CLAPACK deprecation warning.

## Remaining boundaries

This finite comparison supports evaluator conformance within the current action
verifier's accepted scope. It is not exhaustive floating-point, Unicode-version,
platform or desktop qualification. The action verifier now admits the separately
[qualified Unicode subset](crates/reservoir-core/CODEC-UNICODE.md); other text and
ambiguous JSON cases remain incomplete. The evaluator itself does not widen those
limits, and its text-equality behavior is not a general Unicode compatibility claim.

The 600-step sustained-input controller record has a separate verifier and native
`RegulationWindowEvidence` contract. Its evaluation window, partial counts and
mean absolute target errors are outside this module and these tests. Rendering,
record replacement, playback, source selection, accessibility, Windows/Linux and
packaged-app acceptance also require their own checks. Native code, immutable
receipts, live systems and model services were not modified.
