# Reservoir response scanning

Implementation contract selected November 15, 2026. Implemented in local 0.49.0;
qualification and limits are recorded in [the release note](RELEASE-0.49.0.md).

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

The implementation uses the native numerical core, not the preliminary
Python reconstruction. The latter supplies independently checked numerical
expectations and examples, not live execution authority.

## Scope and interface

New sessions opt into versioned scanning. Live probes require a separate saved
opt-in. Earlier sessions omit these fields and keep their original prompts,
parsing, state hashes and replay behavior.

- `NEXT: SCAN` requests a scan of the copied post-application recurrent state.
  The scan itself adds no numerical input or control change; the ordinary entry's
  existing text-input choice still applies. Its cached result appears in later
  ordinary prompts and the app.
- `NEXT: PROBE_SCAN strongest positive` (or `negative`) selects a cached measured
  direction. Other direction names are `weakest` and `persistent`.
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

The subsequent [offline resolution study](../../analyses/2026-11-15-sonar-resolution.md)
qualifies smaller probes, unseen-direction prediction and a two-branch method for
recovering the immediate map with known wiring. It also demonstrates a direction
selected to distinguish two specified starting states. Those are research tools,
not additional native actions or a change to this version's stored contract.

## Use the local instrument

In My reservoir, enable reservoir shaping with continuing inquiry and specific
correction feedback. Select **Allow the model to scan copies of its reservoir**.
Real probes have a separate checkbox, off by default. Create the session and start
explicitly. Offline example writing exercises rejection → scan → measured probe
→ NONE; it is a deterministic fixture, not an LLM interpretation.

Open **Reservoir response scanner** to observe a committed state or scan a copy.
These operator views never enter model prompts. Scans freeze the currently applied
held input even if a newer reply is saved and awaiting application. Model-selected scans enter later
ordinary prompts as bounded summaries; full arrays remain available in the app
and exports. Observations identify their source step and need explicit refresh.

For an immutable exported bundle, the native executable also accepts:

```sh
reservoir-scope-desktop --scan-sustained /absolute/path/to/export > scan.json
```

This verifies the entire source first and outputs a source-bound JSON report. It
neither restores nor writes the source. `probes/qualify_reservoir_sonar.py` records
native replay/scan results plus before/after hashes for explicitly supplied exports.

To build a separately identified app from this directory:

```sh
npm run tauri -- build --debug --bundles app --config src-tauri/tauri.sonar.conf.json -- --locked
```

Scan histories and full cached reports increase checkpoint storage and replay
cost. The app retains its existing quota/headroom hold. The time limit is not a
promise that storage will last that long. A new long-run study needs a measured
budget at its chosen writing cadence; the native qualification is deliberately
short. Future compact storage must retain reproducible scan provenance.

The operator JSON `checkpointSha256` is the core checkpoint's embedded continuation
digest. The CLI envelope's `source.checkpointSha256` is the exported checkpoint
file digest; these bind different serialized objects and should not be compared
as if they were the same checksum.
