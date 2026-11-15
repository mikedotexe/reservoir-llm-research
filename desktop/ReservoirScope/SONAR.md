# Reservoir response scanning

Implementation contract selected November 15, 2026. Status: in development.

The scanner asks how a known small input changes this recurrent reservoir from a
specific saved state. "Sonar" is the interface metaphor; the measured object is
a conditional response map, not established global topology or language-model
activations. Development is isolated on `codex/reservoir-sonar`. Earlier runs and
their saved contracts remain unchanged.

## Observe, scan a copy, optionally intervene

1. A passive mirror reports the recurrent state, recent state variation, held
   input, forcing phase and effective controls. Reading it does not write to the
   numerical session. A view of the separate sensory field stays separately labeled.
2. A scan runs positive/negative small input impulses on copied numerical states,
   paired with an untouched continuation. Every branch shares future base forcing
   and copied recurrent noise. Held text and controls stay fixed; no future LLM
   writing, action or model call is simulated. Results identify the origin, horizon,
   assumptions, input basis, amplitude, direction and decay.
3. Optional real probes use a measured scan direction, with explicit bounds on
   both input norm and the one-step additional recurrent displacement. A real
   probe also reaches the sensory field; it is not a passive measurement.

The first implementation will use the native numerical core, not the preliminary
Python reconstruction. The latter supplies independently checked numerical
expectations and examples, not live execution authority.

## Scope and proposed interface

New sessions opt into versioned scanning. Live probes require a separate saved
opt-in. Earlier sessions omit these fields and keep their original prompts,
parsing, state hashes and replay behavior.

- `NEXT: SCAN` requests a scan of the copied post-application recurrent state.
  The scan itself adds no numerical input or control change; the ordinary entry's
  existing text-input choice still applies. Its cached result appears in later
  ordinary prompts and the app.
- `NEXT: PROBE_SCAN strongest positive` (or `negative`) selects a cached measured
  direction. Other proposed direction names are `weakest` and `persistent`.
  The receipt must retain the source scan and the actual application boundary;
  a cached direction is not a current response prediction. A missing scan or
  absent live-probe authority must produce explicit rejection, never a guessed
  vector. A global Lipschitz bound can cap the immediate recurrent displacement
  even when the direction came from an older state.
- The operator can inspect/scan a saved checkpoint without requesting a model
  response or changing which scan the model has read. Operator observations and
  model-selected observations must remain distinct.

The initial numerical scope is the 32-node recurrence with the difference channel
off. Unsupported configurations must be reported explicitly. Scans must not
silently omit an active numerical feedback channel. Identity basis probes cover
the 48 authored-input slots; the normal semantic codec uses only 32 of those slots.

## Qualification before claiming completion

- Passive observation and scans leave source checkpoints, clocks and RNG state
  unchanged; equal checkpoints and settings produce equal scan receipts.
- Unmodified continuations agree with the actual core under matched held input,
  forcing, noise and controls. Signed finite differences agree with local
  derivatives where applicable, with clipping and numerical floors disclosed.
- Scan arrays are finite and bounded, representative directions are reproducible,
  and changed controls/state alter the appropriate results. Equal spectra alone
  must not be described as equal state geometry.
- Real probes require saved opt-in and a prior scan; their saved receipts separate
  request, application, predicted bound and actual paired response. Existing
  save/readback authorization remains mandatory; retries and skips cannot duplicate
  or accidentally apply a probe.
- Export/restart/exact replay retain scan provenance without calling any model.
  Earlier independent and paused peer exports continue to replay unchanged.
- Native UI demonstrates the passive report, a copied scan, a bounded applied
  probe and a rejected request. Frontend, core and host checks pass.

The first product is a small, trustworthy response scanner. Further iterations
can add waveforms, frequency scans, adaptive question-driven vectors and robust
topological analysis after the simple instrument is qualified.
