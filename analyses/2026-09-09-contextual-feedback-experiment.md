# Contextual feedback: frozen Gemma 4 comparison

Status: running. Provider controls and truthful completion reporting are separately
committed and verified live; contextual feedback remains offline. The
[implementation history](2026-09-09-activation-input-and-provider-knobs.md) preserves
the initial source audit, accepted design, rollout refusals and completed transitions.

This comparison concerns an isolated Gemma 4 model with retained study/draft inputs
and a copied Astrid triple-reservoir state. It is not a new set of live Being studies,
not a Minime backend migration, and not a test of the entire live system.

## Protocol and qualification

Evidence root: `research/outputs/2026-09-09-contextual-feedback-gpu-v1/`.
The immutable protocol fixes four cases, two free-generation seeds (91 and 193),
temperature 0.8, top_p 0.95, thinking off and an 8,192-token output ceiling. Free
generation has lookup, contextual and no-feedback arms: 24 planned trials. Fixed
49-token replay adds shuffled contextual order and a zero-state control: 32 planned
cells. Fixed prose is imposed and cannot establish improved understanding.

All arms share the 32-dimensional projection (seed 137), canonical reservoir weights,
fresh caches and copied initial states. Coupling is fixed at 0.1; wide coupling and
adaptive gain are disabled. These are explicit departures from the full live loop.
The contextual scale 0.0047853296183391816 was calibrated on separate rain/river
material to match lookup projected RMS magnitude 0.08979499653958431 and then frozen.

Capture observes the installed Gemma 4 final normalized hidden vector before
vocabulary projection, within the same forward call. Absolute token positions
account for generator lookahead and retain the existing two-distribution feedback
delay. The end-of-prompt vector is retained for observation and is not fed back.
Projected traces retain first/last 64 rows, with selected full-vector checkpoints.

Same-device observation parity passed: capture-off/on tokens, raw vocabulary logits,
normalized log probabilities, cache offsets and forward ranges matched. Maximum
observed raw-logit difference was zero, within the required `rtol=1e-5`, `atol=1e-5`.
This qualifies observation fidelity on the retained replays; it is not a behavioral
benefit. Dependency versions, model assets, source hashes and projection identity
are in `manifest.json`, `qualification.json` and `raw-logit-qualification.json`.

The default CPU attempt was stopped during prequalification native matrix work after
more than eight minutes, before any evaluation. Its original protocol and interruption
record remain under `research/outputs/2026-09-09-contextual-feedback-v1/`. The GPU
protocol was frozen before evaluation outcomes, retaining the selected cases and
settings. GPU admission uses the existing read-only idle-service check; this is not
an atomic resource reservation. Latency includes shared-host contention. Admission
failures and resource bounds remain outcomes, with no response-based reruns.

## Outcome review

Review criteria in `claim-review-criteria.json` were saved before the first free
response. The unblinded qualitative audit will distinguish source-supported,
contradicted and unsupported assertions, correction of earlier mistakes, retention
of the correct control account, repetition and voluntary continuation/finish.
Draft continuations have no fresh dispatcher source; prior prose remains fallible
context. Neither length nor reservoir movement is a success criterion.

Final denominators, missingness, trial annotations and paired comparisons are pending
completion of the frozen ledger. No behavioral conclusion is available yet.

## Board updates pending

Provider changes are live; capture observation parity passed; the offline comparison
is in progress. Do not mark a behavioral finding verified or activate contextual
feedback on the basis of this technical qualification. Board mirroring remains pending.
