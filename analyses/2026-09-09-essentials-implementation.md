# Essentials: four visible reconstructions

September 9, 2026, Pacific. Mike requested a first-class project directory for
fresh essential implementations, connected to the native 3D viewer. He selected
working stages through one prompt/reply LLM voice, an optional separate local
model, original input-coordinate meanings, and a fourth reduced regulation stage.

## Implemented result

[Essentials](../essentials/README.md) contains a shared Swift library and standalone
runner, assembled into reservoir, spectral bridge, LLM loop and regulation recipes.
The initial reservoir has 32 nodes, the sensory field separately has 32 coordinates,
and the input retains the original 66-coordinate layout. All state/forcing is
synthetic. The handcrafted text codec preserves its 48-coordinate transport;
embedding and narrative-embedding features are explicitly unavailable.

Reservoir Scope 0.8.0 build 11 adds the **Minime & Astrid / Essentials** subject switch.
Each stage can run, stop, reset, replay, scrub, open, and export its complete record.
Node inspection reads exact coordinates. Dynamic Metal/CPU mapping supports actual
node counts without padding; the existing 128-node map stays compatible.
All generated run writes default to this research project's output directory.

The library drives both UI and CLI, whose interface is:

```text
essentials-run run --config SPEC.json --output RUN.json
essentials-run verify RUN.json
```

Stage 2 stores prepared example context, not a model delivery. Stages 3/4 store
language requests and separate completion/application evidence. Prompts name the
top-eight denominator of entropy and head/shoulder/tail shares. Stage 4 fill uses
all 32 eigenvalues under its separately defined active-mode estimator.

## Verification

| Check | Evidence and scope |
|---|---|
| Numerical and runtime | [22 passing Swift tests](../essentials/tests/runtime-validation.log): nine mechanism tests and thirteen runtime tests. |
| Canonical examples | [Source-bound receipt](../essentials/examples/runtime-verification.json): four independently reopened and numerically verified runs, 1,200 steps and 27 turns. |
| Packaged HTTP transport | [Five passing cases](../native/ReservoirScope/validation/0.8.0/http-smoke.json): actual request contract, complete feedback, retained partial/length replies, errors and redirect rejection, using temporary loopback fixtures only. |
| Dynamic geometry | 55 new checks for 1/2/8/32/128 coordinates, including CPU/GPU agreement, volume, selection and round-trip node-count switches. Maximum GPU field error 2.98e-7. |
| Existing geometry | 30 math and 22 GPU checks pass. Before/after 128-node flat, relief and cutaway images are pixel-identical. |
| Existing consumers | 42 evidence/source/replay, 19 state-data, 25 response-simulation and 36 native-action checks pass. |
| Viewer lifecycle | 17 checks exercise actual view-model code: stop, late replies, late file reads, stage/subject/reset races, retained outcomes, and fractional replay timing. |
| Native layout and Run/Stop | [Source-matched hosting checks](../native/ReservoirScope/validation/0.8.0/essentials-run-layout/receipt.json): all 300 canonical frames completed with 336 event-loop heartbeats; timed Stop retained 90 exact frames. |
| Build routes | Standalone static-library/app build and SwiftPM local-package viewer build both pass. |

Native logs and identity are under
[validation/0.8.0](../native/ReservoirScope/validation/0.8.0/). Dynamic/offscreen
checks can be reproduced with `check-dynamic-state-surface.sh`; lifecycle checks
with `check-essentials-ui.sh`. The [build receipt](../native/ReservoirScope/build-receipt.json)
identifies the final executable, shared core source, packaged runner and resources.
Native UI inspection covers the real app's stage selection, 32-coordinate surface,
spectral bars, exact node and reply inspection, replay/scrubbing and subject switch.

Native inspection exposed excessive intrinsic window sizing during changing
measurements. Essentials now takes the available window dimensions directly and
loads inspector sections lazily. The [bounded layout comparison](../native/ReservoirScope/validation/0.8.0/essentials-layout/comparison.json)
records the before/after change. The final Run/Stop harness uses the actual view model
and native event loop: maximum callback gaps were 328 ms during completion and
299 ms during Stop; the Stop boundary completed within 200 ms. These are unpresented
hosting checks, not displayed frame-rate or general input-latency measurements.
Native accessibility automation timed out during active runs, but later inspection
and saved-record verification confirmed completion. The completed view and replay
remained inspectable. This tooling limit is retained in the runtime receipt.

The [controlled numerical qualification](../essentials/examples/regulation-qualification.json)
uses 600 identical seeded input vectors for both covariance paths. Over steps
301–600 (n=300), mean absolute target error is 11.925 percentage points for fixed
retention and 4.160 with the reduced PI. The regulated range is 68.683–74.235%;
this is not strict convergence. Constant-direction and zero-field tests retain
unreachable targets instead of inventing missing rank.

The native app's default Stage 4 run (n=1, 300 steps, nine scripted turns)
[independently verifies](../native/ReservoirScope/validation/0.8.0/native-generated-run.json)
and is byte-identical to the canonical example. It finishes at 24.756% reduced
fill with retention at its 0.995 ceiling. The default forcing therefore does not
attain the target within this run. This whole-loop example is distinct from the
600-step fixed-input qualification above; the displayed result is retained as measured.

## Interpretation and limits

This reconstructs declared mechanisms, not the whole beings or production parity.
The native state, sensory covariance, text codec, separate triple reservoir and
language model remain distinct subjects. Unit-RMS field normalization, silent-input
covariance decay, top-eight summaries, full-32-mode fill and symmetric retention PI
are explicit experimental choices.

Controller-on/off app recipes keep forcing, noise and scripted reply texts fixed.
Their spectral feedback can change semantic vectors, so that comparison includes
the complete loop. The separate numerical qualification fixes every input to
isolate covariance retention.

Optional Ollama support is implemented with explicit separate endpoint/model
configuration, bounded requests, returned-model/stop metadata and cancellation.
The default and bundled runs use scripted replies. No actual model or being
endpoint was used for this implementation. The retained HTTP smoke test uses a
new ephemeral loopback fixture only. Existing compiler warnings identify the
legacy Accelerate LAPACK interface; they do not represent failed numerical checks.
No presented-window frame-rate, energy or cross-host performance claim is made.

No sibling repository, live database, being process, prompt, journal or study
cursor was changed. This is research instrumentation; deployment into a being
remains a separate owning-repository decision.

## Board updates pending

Local implementation and validation are complete. Live Hold Shelf publication
was not performed in this session. [Prepared update](../board/essentials-pending.json):
record the completed Essentials instrument and link this account, component guides
and verification receipts. Existing unrelated cards and studies remain untouched.
