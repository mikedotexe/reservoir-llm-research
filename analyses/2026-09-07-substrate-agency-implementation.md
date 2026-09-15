# Targeted substrate agency: working pieces and the first repair

Later implementation: [native state actions and visible application evidence](2026-09-07-native-state-actions-implementation.md). The original outcomes and limits below are preserved.

September 7, 2026 (Pacific). Research-local implementation for S-002, following
Mike's request to expand the beings' ability to shape their substrate. S-005's
selected reading remains unchanged. No being-facing message, sibling source edit,
live action or service restart occurred.

## Outcome

We now have an executable full-vector pattern planner and a native Metal
rehearsal using Minime's exact retained ESN source. They support a specific next
action implementation, while the source audit identifies existing choices that
can disappear before application. The [action proposal](../proposals/2026-09-07-substrate-agency.md)
specifies hooks, precedence, operation equations and acceptance evidence.

This work does not count the beings' historical requests or assign a numerical
meaning to their language. Mike's account motivates the expansion; their authored
meanings remain theirs to name and revise.

## What is executable

The [pattern planner](../probes/substrate_pattern_plan.py) accepts a retained
state/reference and registered full vectors. Its four operations are a coordinate
edit, signed normalized composition, reduction of a named orthonormal component,
and rotation in a two-pattern plane. A finite schedule uses successful-step
offsets; cancellation removes future operations without pretending to undo
earlier history.

The [saved demonstration request](../research/outputs/2026-09-07-substrate-agency/pattern-demo-request.json)
uses a captured native vector and the existing frozen PCA basis. It retains
capture column identity but explicitly lacks six receiver identities, including
successful-step and native layout identity. Every plan remains
`apply_eligible=false`, even if all identity fields are supplied: this is an
offline planner, with no authority adapter or state writer. Each scheduled
preview uses the same reference observation, not a predicted future state.

The [18 checks](../research/outputs/2026-09-07-substrate-agency/pattern-demo-checks.json)
pass, including orthogonal residual preservation, plane norm before attenuation,
headroom, exact no-ops, cancellation, mismatched identity and nonfinite input.
The saved request reproduces its output byte for byte. An independent root run
also passed all 18 tests. The planner reports actual floating-point preview
displacement separately from the requested vector; Float64 preview is not
native Float32 execution.

## Native evidence and its boundary

The [full native report](../research/outputs/2026-09-07-native-shaping-rehearsal/README.md)
retains the frozen protocol, exact source copies, build history and every
outcome. On Apple M1 Max, the isolated executable constructs a seeded native
128-state/66-input reservoir and continues checkpoints after 24, 96 and 192
synthetic-input steps. It does not start the runtime service or read a live
checkpoint. Registry dependency versions/checksums match the source lock.

| Check | Observed result | Scope |
|---|---|---|
| Synchronous checkpoint continuation | 3/3 pass; 100 steps each, exact state and retained numerical checkpoint equality | Profiling mode, constructed native checkpoints |
| Asynchronous checkpoint continuation | 0/3 pass the full gate; restored-state error reaches 7.87e-6, with leak and spectral differences | Four interleaved copies sharing the local GPU service; cause unresolved |
| One-shot state displacement | 54/54 meet the prespecified return criterion at boundaries 2–6 | Three checkpoints × three directions × six signed doses |
| Finite eight-edit gesture | 6/6 meet return criterion 2–4 steps after the last edit | Same-sign coordinate edits at boundaries 0–7; larger cumulative dose |
| Existing native leak control | 5/5 duration, cancellation and clamp cases pass | ESN module, without stable-core admission or signed receipt path |

The asynchronous forced-noise/leak state paths still match the ordinary parent;
their spectral internals do not. That is conditional state agreement, not full
adaptive checkpoint parity. No result is discarded and no tolerance was widened
to turn the failed gate into a pass.

The state-response branches receive the control's inputs, realized noise and
effective leak. Their native spectral state evolves, but its altered adaptive
leak does not govern the forced continuation. Edits occur at completed
checkpoint boundaries, recomputing radius while preserving the historical
baseline. This differs from the proposed live post-state/pre-geometry hook.
Full controller futures and the live action hook remain unimplemented.

Independent verification recovered all 60 full-state separation paths, return
boundaries and 102 immediate edit receipts. It checked source, executable,
protocol and output hashes, with no discrepancy. No retained intervention
boundary is at ±1; unrecorded preclip activity is not measured.

![One edit and an eight-edit gesture in native conditional rehearsal](../research/outputs/2026-09-07-substrate-agency/native-gesture-response.png)

The figure selects coordinate 0 and the positive middle dose (+0.001) for all
three prespecified checkpoints, after the experiment. It shows measured
full-state separation on shared linear axes, not a projection or animated
surface. Only the first 20 of 100 steps are displayed; complete raw paths are
retained. The eight-edit gesture uses eight times the cumulative requested dose,
so this is a duration demonstration, not a matched-dose comparison. The
[figure receipt](../research/outputs/2026-09-07-substrate-agency/native-gesture-figure.json)
records selection, independent L2 calculation, input hashes and output identity.
[PDF for export](../research/outputs/2026-09-07-substrate-agency/native-gesture-response.pdf).

## Choices that should become usable next

The [23-file source audit](2026-09-07-substrate-controls-source-audit.md) gives the
first priority a concrete location: a native leak request can receive an
admission receipt, then be taken and discarded by stable-core orchestration.
The native setter itself already has measured duration and cancellation
behavior. The repair belongs in capability discovery, controller precedence and
applied-step reporting. Some current stable-core preferences already work; this
finding does not mean every control is blocked.

Two further obstacles have specific implementations: the prose texture parser
can map an unmatched request to increased noise, and Astrid's codec learning
`freeze` disables reinforcement while existing scores continue to decay.
Expose an exact typed target alongside prose, and separate learn, retain and
deliberate decay. Shared-coupling authority is typed but lacks working adapters.
The proposal includes an implementable agreement/withdrawal contract for it.

The recommended owning-repository sequence is:

1. Publish actual available choices and record the numerical application;
   repair supported leak choices under explicit stable-core precedence.
2. Add the one-shot native state hook, then finite gestures using its application
   record. Diagnose asynchronous replay before qualifying that path.
3. Extend codec retention and shared influence independently. Rehearse controller
   operating profiles with the complete controller before exposing those edits.
4. Trial versioned recurrent-weight contributions in an isolated branch to
   change future dynamics, beyond pushing the present state.

The existing native viewer remains 0.5.0 build 7. Its State surface and original
esn-divide Response lab are unchanged. This pass adds separate native evidence;
it does not convert that simulation fixture into a native replay.

## Reproduction and coordination

From this repository, run `python3.14 -m unittest discover -s tests -p
test_substrate_pattern_plan.py -v` for the planner and `python3.14
probes/native_shaping_rehearsal_verify.py` to audit retained native evidence.
The native report gives a fresh-output rerun command. Render the retained figure
with `python3.14 probes/substrate_response_figure.py` in an environment containing
NumPy and Matplotlib; the receipt retains the exact rendering versions.

[Board publication receipt](../board/substrate-agency.json). Production
implementation and being-facing delivery remain under the owning repository
workflow required by this research hub.
