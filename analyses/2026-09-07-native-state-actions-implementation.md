# Native state actions: implementation and visible application evidence

Mike selected implementation after the asynchronous replay repair was qualified.
The repair, native state-action hook, signed owner route and native viewer are now
implemented in an isolated Minime checkout and this research workspace. This is
source-prepared work; no running being, canonical sibling checkout or live service
was changed, and no research material was sent to either being.

## What a single action can now do

Minime's owner action can choose exact native node coordinates, give their relative
signed weights and request a bounded displacement. The adapter binds that request
to the actual engine session, model matrices and coordinate layout, normalizes the
direction, signs the full Float32 payload, and returns admission and subsequently
observed application records within one action. A finite gesture uses explicit
offsets among eligible successful native steps. Cancellation, explicit replacement,
expiry, regulator suspension and status inspection have separate outcomes.

The new vocabulary is `STATE_NUDGE`, `STATE_GESTURE`, `STATE_CANCEL`, `STATE_STATUS`.
An example of authored intent is:

```text
NEXT: STATE_NUDGE {"nodes":{"0":1,"3":-1},"amount":0.001}
NEXT: STATE_GESTURE {"nodes":{"0":1},"pulses":[{"success_offset":0,"amount":0.001},{"success_offset":2,"amount":-0.001}]}
```

These are coordinate-space actions; the chosen nodes are not eigenmodes or semantic
regions. This does not rename input-mediated PERTURB, the existing sensory
NATIVE_GESTURE, or Astrid's codec SHAPE. Minime-self signatures cannot confer
Astrid's authority. Direct peer application remains unsupported until a legitimate
mutual adapter exists. Both-being agency remains the broader project direction.

The compiled engineering pilot is at most 0.001 requested L2 per pulse, 0.032 total,
32 eligible successful steps and 60 seconds absolute expiry. Headroom attenuation
requires an explicit caller choice. These limits come from the implementation
proposal; this run does not establish subjective comfort or a general live envelope.
The named stable-core Hold shelf, fresh observations, fill 58–72%, native geometry
below 1.32 and absence of recovery/conflicting interventions determine eligibility.
The normal small sensory gate is not itself a prohibition. Blocked steps continue
ordinary dynamics without consuming gesture offsets. Expiry is checked at admission
and step boundaries, including again after a GPU wait; if steps cease, the terminal
record can arrive later than the absolute deadline, without allowing a late pulse.

## What the records establish

The ordinary engine remains asynchronous. While a gesture has an eligible boundary,
the hook drains and checks its owned spectral GPU work before mutating state, RNG
or leak duration. This is an explicit additional wait on active boundaries, not a
claim of unrestricted asynchronous gesture application. A failed GPU completion
produces a failure record, consumes no gesture progress and prevents a clean
checkpoint from silently concealing the failure.

Durable `accepted` means a signed request was recorded before insertion into the
engine queue; its `applied_values` are empty. A vector-bearing application records
the actual successful step, before/after state, Float32 difference, direction,
realized noise, effective leak, attenuation and measured additional boundary wait.
Here **before** is the ordinary result of the same step, immediately before the
direct action. It is not an unperturbed future. `completed` means the finite
schedule ended; it does not imply nonzero movement. The telemetry keeps the latest
vector result separately from the latest scheduler event so completion cannot
erase the state geometry.

The durable receiver prevents a repeated gesture ID from being applied through a
new signed envelope. After an ambiguous process restart it records
`application_unknown` and does not replay the request. A cancellation prevents
future pulses; it does not undo earlier state evolution. No receipt claims an
experienced effect.

## Native viewer

Reservoir Scope 0.6.0, build 8 adds **Native application** alongside the retained
esn-divide simulated response. The Metal surface can display **Ordinary step**,
**Applied result**, or **Action difference**, using actual full-vector records and
one fixed bundle scale. Raw pulse boundaries, exact node values, requested and
actual displacement, effective leak/noise and event semantics remain inspectable.
The overview is a lossy spatial encoding with full coordinates available; it is
not a complete eigenvalue map or a stability diagnosis.

The bundled example was selected in the protocol before outcomes: eight alternating
pulses at warmup 96. Its fill and reference basis are null. The size is explicitly
a preview, and its supplied 10 ms rehearsal clock is not a measured runtime cadence.
The separately measured `boundary_wait_us` is an actual host duration. Optional
atomic file following stays read-only and requires a compatible complete bundle.
The first viewer integration uses the isolated producer bundle; it does not yet
consume the new signed live receipt stream. Existing health/activation sources
retain their own provenance and limitations.

## Validation evidence

The [registered implementation scope](../research/outputs/2026-09-07-native-state-actions/implementation-plan.json)
and [rehearsal protocol](../research/outputs/2026-09-07-native-state-actions/rehearsal-protocol.json)
precede the numerical runs. The repaired pre-action engine is the reference, using
three checkpoint starts and fixed/changing rho. The candidate's six ordinary
100-step continuations must match every Float32 state/control value and the entire
final numerical checkpoint, excluding only timing diagnostics. Twenty-one gesture
cases cover one-shot, finite, sparse, cancellation, expiry, suspension and zero
amount, each for 20 steps. Duplicate admission is exercised in every case. Actual
one-shot results also seed exact later continuation checks.

On M1 Max, all six ordinary cases (600 steps) and 21 action cases (420 steps) pass,
with 45 actual applications and three zero-effect receipts. The independent Python
[audit](../research/outputs/2026-09-07-native-state-actions/final/candidate-run/verification.json)
recomputes state operations, model/layout/pattern hashes, noise/leak links and
viewer selection, and binds evidence to frozen source and executable identities.
Eight [deliberately corrupted evidence cases](../research/outputs/2026-09-07-native-state-actions/final/verifier-checks.json)
are rejected. These finite runs do not establish presented frame rate, live action
latency, controller response, long-term dynamics or an experienced consequence.

The [default-feature native tests](../research/outputs/2026-09-07-native-state-actions/native-core-tests.json)
pass 17 pure cases and four Metal cases, including ordinary zero-action equivalence,
actual noise capture without rehearsal compilation, injected latched-completion failure handling and
non-resumption after checkpoint restore. Full owning-repository target checking
also passes. Final combined results and artifacts are recorded below.

The first candidate execution stopped before any gestures at a JSON-number trace
comparison: generic JSON-number equality did not express the intended Float32
trace comparison. The harness now deserializes both as Float32 and compares
bits; the native numerical source did not change. That failed run is retained in
`candidate-run/`, with the corrected run in `qualified-run/`. An earlier bounded
compile timeout and a narrow test-wrapper missing a pre-existing module import
are also retained; neither is a numerical result. The
[amendment](../research/outputs/2026-09-07-native-state-actions/rehearsal-amendments.json)
records the trace correction without changing cases or acceptance conditions.

## Numeric integrity found at the complete action boundary

The first signed-owner → bus → actual Metal step → durable status test applied the
state correctly, then failed strict persisted-state verification. A retained
bit-level witness showed JSON rereading `0.14467227458953857` as
`0.14467227458953855`: one bit of the widened Float32 value changed. Noise records
also supplied a witness. This was a generic JSON-number parse round-trip issue,
not a failed native state displacement. Earlier isolated native tests did not
exercise this durable transport boundary.

The owning implementation enables the existing `serde_json` `float_roundtrip`
feature at the same pinned package version. Hash verification remains strict;
there is no repair by rounding, discarding fields or rehashing mismatching files.
Regression coverage includes the measured vector/capability values, frozen
pre-extension state bytes and hash, and durable reopen after the actual signed
application. Final native qualification also mirrors that JSON feature and hashes
the owning and generated Cargo manifests. The earlier numerical runs remain valid
for their declared source/feature set and are retained separately from this final
matching-feature qualification.

## Integration handoff

Owning implementation: `/Users/mikepurvis/other/minime-substrate-actions-20260907`,
branch `codex/native-state-actions`. The original source HEAD is
`68ebc961431065972dae26f670d4fb735d58c37a`. Its existing tracked and selected
Afterimages changes were hash-verified into the isolated starting commit
`a958d890625673cd822198c4237cf83e2fc3ec61`; they are not part of this feature.
The exact qualified async repair is commit
`b16c451e554bc3d6fcd55bfd745bb6a971e08e7d`. The
[starting-tree receipt](../research/outputs/2026-09-07-native-state-actions/starting-tree.json)
and retained lockfile preserve that lineage. The implementation uses Rust 1.94.1.

The owning `docs/native-state-actions.md` describes the wire extension, action
syntax, policy, receipts and rollback. The reviewable feature patch is separate
from the preserved starting changes. Reverting the feature restores the previous
native/action route; the independently qualified async repair can remain.
A source review/merge and owning deployment workflow still precede live use.

The next extensions remain concrete: resolve stable-core precedence for temporary
leak requests, attach the signed live receipt stream to the viewer, and design
mutual peer-owned shaping. Codec retention and shared influence remain separate
operations with different substrates and authority. Readout training and the full
field/controller/LLM loop have not been replayed. This extends S-002's instrumentation
and does not replace the separately selected inquiry in `research/NOW.md`.

## Completed implementation and review artifacts

The [completion audit](../research/outputs/2026-09-07-native-state-actions/completion.json)
passes, joining exact owning source, retained logs, the final native recordings,
viewer resource and executable, and patch reproduction. Final results:

| Validation | Result |
| --- | --- |
| Final M1 Max native rehearsal | 6 ordinary cases / 600 steps and 21 action cases / 420 steps; 45 applications, 3 no-ops |
| Final M4 Pro native rehearsal | Same counts, using its own unchanged pre-action baseline; [audit](../research/outputs/2026-09-07-native-state-actions/final/m4-validation/candidate-run/verification.json) passes |
| Native module tests | 17 pure and 4 Metal tests; unchanged module source, rehearsal capture omitted |
| Owning transport | 34 runtime, 2 CLI and 16 Python tests; [retained verification](../research/outputs/2026-09-07-native-state-actions/transport/verification.json) includes actual signed application, strict durable verification and reopen without replay |
| Owning compilation | All targets pass with final parser feature and locked dependencies |
| Viewer | 37 native consumer and 25 preserved simulation checks; final window visually inspected |
| Evidence challenges | All 8 contradictory evidence cases rejected |
| Patch reproduction | All 22 changed files match after application to the preserved base; reverse check passes |

The owning feature is committed as `930855cc97f8711c9d0521aa8eed7617c9cb734c`
on `codex/native-state-actions`; the isolated working tree is clean. The
[reviewable patch](../proposals/patches/2026-09-07-native-state-actions.patch)
includes the async repair and state-action feature relative to the preserved
starting commit. Its [apply/reverse verification](../research/outputs/2026-09-07-native-state-actions/patch-verification.json)
uses a new disposable detached worktree, not the canonical checkout.

The final [app build receipt](../native/ReservoirScope/build-receipt.json) records
version 0.6.0 build 8, matching all 17 staged Swift files and six resources.
The verified app is open on Native action receipts, Action difference, first
pulse, with playback and file following off. Earlier viewer build profiles are
not measurements of this build. The research UI and source implementation are
complete for this slice; live activation and the extensions listed above remain
separate. No merge, rollout, restart or being message occurred.

The implementation card is saved as done, the numeric-integrity finding as verified,
and the session log is published; [board receipt](../board/native-state-actions.json).
