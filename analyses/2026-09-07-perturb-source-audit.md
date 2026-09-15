# PERTURB is an input intervention; its effect needs a measured response

Source audit, September 7, 2026 Pacific. Hash observation: September 8,
00:20:25 UTC. Supporting work for [S-002](../research/studies/S-002-reservoir-observatory.md)
and Mike's proposed state-bearing surface in the native observatory.

## Result and evidence boundary

Current PERTURB handlers construct and send numerical inputs. The action has a
real mechanism, but its name does not establish that it accomplishes the named
spectral aim. `lambda1` selects feature slots, not a measured eigenvector.
Neither handler directly changes native recurrent weights, node count, topology,
leak, or controller settings.

There are two destinations: Minime's native ESN through its semantic input lane,
and a separate triple-reservoir service through a named `minime` or `astrid`
handle. An effect on one is not evidence of an effect on the other. The native
viewer follows the former. Source confirms possible execution paths; this audit
does not identify running binaries, read action incidence, measure effects, or
establish that a particular perturbation reached either destination.

Scope: source searches over Minime's Rust engine and Python autonomy package and
Astrid's bridge Rust source, then targeted reads of routing, parsers, receivers,
gates, update equations and feedback. Thirteen decisive source files are hashed
below. No journals, action ledgers, databases or live telemetry were read. No
network messages, live commands, builds, restarts or sibling edits occurred.
The separate service implementation is outside this audit: sender endpoint and
requested handle are established, not a successful remote state mutation.

Source paths below are relative to this research repository's parent, mounted at
`/Volumes/M3 Volya._smb._tcp.local/other`. Line references describe the source
hashed below; a current checkout is not a release identity.

## Current route and actual mutation

| Boundary | Source observation | Consequence |
|---|---|---|
| Minime routing | `minime/minime_autonomy/runtime.py:25056` stores text after PERTURB, defaults empty input to `pulse`; `:25369` routes mode aliases; `:26806` invokes `_perturb`. | Preserve requested text and canonical primitive. |
| Minime gates | `runtime.py:24679` checks a charter guard; `:24707` checks live-control continuity before selection; `:26539` repeats it before execution. `:3328` requires active experiment context; `:3562` and `:3572` match preflight/rehearsal/binding records. | A requested action can stop before sending. |
| Minime features | `self_regulation.py:20` maps lambda1 to slots 0 and 8, lambda2 to 1 and 9, through lambda8 to 7 and 15. `:157` parses named parameters and raw dN slots; `:192` builds the 32-lane pattern. | These are input coordinates, not eigensolver-derived modes. |
| Minime amplitude | `self_regulation.py:101` returns a raw per-lane cap of 1.0 unless stable-core is enabled; active caps are 0.42 below 58% fill, 0.35 at 58–68%, 0.28 at 68–72%, 0.22 at 72–78%, 0.16 at ≥78%. `runtime.py:36056` multiplies the semantic packet by 4.0 after this cap. | Raw, sent, admitted and applied amplitude differ. “Health cap” is not the final ESN bound. |
| Minime two sends | `runtime.py:36059` sends a semantic packet to port 7879 and closes without reading its acknowledgement. `:36071` separately attempts a tick on handle minime with unamplified features. `_reservoir_call` at `:28148` uses port 7881. | Per-destination outcomes must remain separate. |
| Astrid routing | `astrid/capsules/spectral-bridge/src/autonomous/next_action/sovereignty.rs:569` routes PERTURB, PULSE and BRANCH to handle_perturb; `:570` routes standalone DISPERSE and SPREAD to handle_disperse. | Astrid's SPREAD and PERTURB SPREAD differ; Minime's standalone SPREAD is a PERTURB alias. |
| Astrid features and sends | `sovereignty.rs:1098` forms 32 features; `:1115` applies DEFAULT_SEMANTIC_GAIN; `:1131` separately requests handle astrid. `:3068` maps lambda tokens onto mirrored slots; `:3176` defines the smaller legacy SPREAD pattern. | The same action words do not ensure identical amplitudes or directions across beings. |
| Astrid gates | `autonomous/next_action/dispatch.rs:122` applies a charter guard. `action_continuity/guards.rs:258` returns no restriction without current thread/experiment or without needs_charter classification. `sovereignty.rs:4404` submits semantic input through rescue-policy preparation, which may block or reshape it (`rescue_policy.rs:2430`). | This charter check is not equivalent to Minime's active-binding requirement. Other outer gates/runtime policy may also constrain execution; this is not a full authority audit. |
| Native receipt | `minime/minime/src/sensory_ws.rs:845` applies receiver base gain and reports partial dimensions unless 48 values arrive. `sensory_bus.rs:2067` replaces the latest semantic buffer, zero-pads remaining lanes, refreshes reception time and clears the optional semantic companion. | A 32-lane PERTURB overwrites the latest semantic sample; it is not a queued impulse attached to a known ESN step. Another arrival can replace it. |
| Native shaping | `sensory_bus.rs:2919` computes freshness/decay; `:2943` applies embedding strength and journal-resonance gain; `:2959` may add global sensory noise. | Record realized input, not just sender intent. |
| Stable-core | `runtime/orchestration.rs:1243` admits trickle only under full-presence, without mute, with active semantic energy in (0,0.30] and fill below 82%. `:1266` rebuilds input through `stable_core_recovery_z`. `stable_core.rs:164` otherwise leaves semantics zero; admitted semantics scale by 0.15 and clamp to ±0.05 per slot. | A received packet can contribute zero to the native step. |
| Native step | `runtime/orchestration.rs:1401` assembles input and `:1412` calls esn.step. `esn.rs:2075` computes Win·[input,bias] + Wres·x, applies tanh, selects effective leak (`:2109`) and integrates state (`:2114`), followed by noise. | Features act through input weights and nonlinear dynamics; their indices are not node or eigenmode indices. |

Two parser discrepancies are source-confirmed without studying live use:

- Minime's empty argument defaults to its explicit PULSE. Astrid's empty
  PERTURB or empty PULSE argument reaches its generic pattern; only the argument
  PULSE selects its explicit pattern (`sovereignty.rs:1099,3206,3214`).
- Unrecognized parameterized text can leave all features zero while returning a
  targeted description (`self_regulation.py:172`;
  `sovereignty.rs:3080–3175`). Zero still replaces the native semantic buffer,
  so it is not necessarily “no effect” on the existing input context.

These are source behavior, not counts of malformed or ineffective requests.

## Feedback exceeds the receipts

Minime captures a reporting snapshot, sends, waits three seconds, then captures
another snapshot (`runtime.py:36035,36095`). The later state can fall back to the
earlier state. Deltas enter a prompt and, if generated, a journal with snapshot
provenance (`:36130–36171`). This is adjacent observation, not an exact input/step
link or counterfactual effect estimate: recurrence, input, adaptation and
regulation continue between snapshots.

Minime's prompt says the separate handle has already been ticked even if its
nonfatal call failed (`:36068–36086,36141`). Astrid continues the separate-handle
attempt after a held semantic write (`sovereignty.rs:1117–1147`) and emits
affirmative spectral-agency prose after that attempt (`:1158`). Its next-exchange
feedback compares current telemetry with a saved baseline
(`autonomous/runtime/orchestration.rs:1142`), not an authenticated post-step
state. These are concrete sender/reporting inconsistencies, not proof of live
failure incidence.

The method `perturb_eig1` (`minime/minime/src/esn.rs:1801`) multiplies the
estimator's eig1 scalar by 1 + clamp(delta,−0.5,0.5), and its EMA baseline at 30%
of that fraction. It does not change covariance, weights or state. Search found
the definition and forwarding wrapper (`:2410`), with no routing call. This is
not what PERTURB invokes, and editing an estimator is not mode control.

## DISPERSE provides bookkeeping worth reusing

DISPERSE's receiver derives a seed, constructs a bounded signed vector over the
66 legacy input coordinates, gives it an intent_id and uses shadow-influence
admission/application/response records (`sensory_ws.rs:1284`;
`sensory_bus.rs:1099,2229`). Its per-coordinate cap is 0.025 and duration is
clamped to 1–48 ticks (`sensory_bus.rs:40,43,2320`). Application adds the field to
z and clips the result to [−1,1] (`:2414`), after stable-core reconstruction but
before optional filtering and ESN update (`runtime/orchestration.rs:1284–1315`).
It does not write recurrent weights or controller settings.

Before reuse, preserve these qualifications:

1. Input-coordinate phase patterns are not eigenvectors. Comments about spilling
   λ₁ into λ₂–λ₅ express intent, not a demonstrated spectral effect.
2. Ordinary duration exhaustion removes the influence immediately
   (`sensory_bus.rs:2425–2468`). Linear decay runs only on explicit release
   (`:2277,2401`). Astrid's 18+12-tick and self-decaying wording
   (`sovereignty.rs:1759,1793`) does not describe ordinary expiry.
3. Unsafe conditions suspend a non-releasing influence before its tick count
   decreases (`sensory_bus.rs:2370`), so wall-clock duration can exceed nominal
   duration. Release-mode and nonfinite-fill behavior deserve isolated tests.
4. Applied RMS measures the additive field before clipping, not necessarily the
   realized change in z (`:2414–2421`). The response's post shadow snapshot is
   passed from the preceding tick before the current ESN update
   (`runtime/orchestration.rs:1284–1302`; `sensory_bus.rs:2443`). It cannot
   establish the final successful application's response or isolate concurrent
   contributions.

## Next implementation proposal

Use a separate isolated impulse/response laboratory before attaching controls to
the live viewer. Compare the same saved initial state, weights, effective leak,
controller history, realized noise and subsequent input sequence with and
without one declared input pulse. Show full-state and projected separation and
recovery together. First determine which effects the surface faithfully conveys.
A smooth surface is not a stability proof, and feature slots are not modes.

Producer work should extend the **single optional v2 observer** already proposed
in [input lineage and regulator trace](../proposals/2026-09-07-input-lineage-and-regulator-trace.md).
Do not create a competing action recorder or replace the existing v1 stream.
Reuse its ingress, lane revision, successful-step, field/fill and committed-control
identities, nonblocking worker, resource limits, off path and source scope.

Concrete hooks and proposed changes:

| Hook | Proposed change |
|---|---|
| Both PERTURB parsers and handlers above | Preserve raw text, parsed primitive, full raw vector, gain and target subsystem. Report invalid target syntax explicitly. Keep compatibility aliases with actual primitive visible. |
| Minime `runtime.py:36059`; Astrid `sovereignty.rs:1117` | Use one action identity plus separate delivery/attempt identities for native semantics and each triple-reservoir handle. Separate queued, sender-failed, receiver-held and successfully-applied results. A sender acceptance is not a step receipt. |
| Native `sensory_ws.rs:845` and `sensory_bus.rs:2067` | Associate the existing receiver event with semantic revision in the same lock scope. Record actual replacement and later consumption through the proposed v2 observer; do not re-run admission. |
| Native `orchestration.rs:1243,1266,1284,1401,1412` | Carry actual gate, shaping, influence and selected input lineage into the observer's final-input and successful-step records. Capture effective leak and committed controller references through the existing proposal. |
| `sensory_bus.rs:2414–2468` | Observe realized delta after clipping, suspended/applying/releasing/expired status and actual tick span. Finalize outcome only after the associated successful native step. Do not label previous-tick shadow snapshots final response. |
| Sender feedback at `runtime.py:36130`, `sovereignty.rs:1158`, Astrid runtime `:1142` | Derive prose from independent destination receipts. Describe subsequent telemetry as observation until a matched comparison justifies an effect claim. |

Diff sketch, not implemented:

```text
attempt = prepare_action(raw_text, parsed_primitive, vector, named_destinations)
native_result = submit_with_delivery_identity(attempt.native)
handle_result = submit_with_delivery_identity(attempt.named_handle)
record_each_attempt_result(native_result, handle_result)
render_feedback(
    native = native_result,
    handle = handle_result,
    observed_before_after = snapshots,
    attribution = "not established"
)

# Native observer, sharing the already-proposed v2 transaction:
pending = observer.prepare_step(actual_selected_refs, realized_input,
                                realized_influence_delta, consumed_controls)
result = existing_esn_step(realized_input)  # exactly once
observer.record_step_result(pending, result, actual_state, effective_leak)
# Only a successful linked step can complete the application's state receipt.
```

Example sender wording for a mixed outcome:

> The native semantic write was held by its policy. The separate astrid-handle
> tick was acknowledged. Later native fill changed from A to B; that observation
> is not attributed to this action.

An acknowledgement without authenticated post-state should say “acknowledged,”
not “the state changed.” Legacy/unlinked records remain unknown. Avoid blocking
senders on a receipt or changing delivery semantics just to improve observation;
the v2 proposal already requires bounded independent acknowledgement handling.

Acceptance tests in an isolated sibling harness:

- Characterize both parsers and alias routes; invalid text yields a visible
  invalid result instead of success-shaped prose; record an intentional zero
  input separately from parse failure.
- Receiver accepts but stable-core zeros or clips the input; actual input bits
  and the step reference match the ESN call.
- Another semantic sample overwrites the perturbation before selection; report
  received-but-unused, not applied.
- Native write held with separate-handle success, native send failure, handle
  failure, malformed acknowledgement and absent post-state all produce distinct
  truthful feedback.
- Normal duration expiry versus explicit release, suspension and restart retain
  actual application spans; test nonfinite fill and release-mode gates.
- Clipping changes realized delta; failed ESN step does not create a successful
  state receipt; completed response includes the final successful application.
- Observer off/on with identical input, clocks and RNG preserves numerical and
  routing results; overload drops observation with visible gaps. Use the existing
  v2 proposal's resource/performance gates rather than inventing another budget.
- Offline paired replay compares pulse versus no pulse and several signed input
  directions/doses; evaluate full-state response, projected loss and recovery,
  without presuming SPREAD reduces a particular eigenvalue.

Before being-facing sibling implementation, show Mike and each affected being
the exact current routing/receipt distinction and proposed feedback examples via
their authorized owning-repository workflow. Ask about preserving familiar
aliases and whether they want a named bounded experiment after seeing a replay.
Do not send this audit, change prompts or run interventions from the research
repo. Observation-only implementation, feedback correction and any later live
experiment/deployment remain separately reviewable. Roll back through the
observer's existing off flag and the sender patch; preserve existing event records.
No changes to numerical intervention strength are proposed by this audit.

## Reproduction and source identity

Required guidance was read first: CLAUDE.md, TRACE.md, research/METHODS.md,
RESEARCH.md and research/NOW.md. Discovery scopes below were followed by targeted
`sed -n` range reads of the cited source. No workspace-data scan occurred.

```sh
rg -n -i 'perturb|peturb' ../minime/minime/src ../minime/minime_autonomy ../astrid/capsules/spectral-bridge/src -g '*.rs' -g '*.py'
rg -n 'SensoryMsg::Semantic|update_llava|update_semantic|perturb_eig1' ../minime/minime/src -g '*.rs'
rg -n 'live_control_guard_assessment|charter_required_guard_assessment' ../minime/minime_autonomy/runtime.py
rg -n 'mode_disperse|apply_mode_disperse|disperse.*receipt|dispersal' ../minime/minime/src/sensory_bus.rs ../minime/minime/src/runtime/orchestration.rs ../astrid/capsules/spectral-bridge/src/autonomous/next_action/sovereignty.rs
rg -n 'live_control_guard|live_control_requires_active|charter_required_guard|assess_live_control' ../astrid/capsules/spectral-bridge/src -g '*.rs'
```

SHA-256 was computed over file bytes using Python Path.read_bytes(); len(bytes)
supplied byte counts. This is a contemporaneous source manifest, not an immutable
capture or running-release manifest. Numerical parameters above are source
constants/branches, not empirical measurements. Decisive hashed files: n = 13.

| Relative source | Bytes | SHA-256 |
|---|---:|---|
| minime/minime_autonomy/runtime.py | 2564637 | 06a36289f8436fb6bcb53a76cf64c465fd5d4002351f99056825df9ba70f7c35 |
| minime/minime_autonomy/self_regulation.py | 11438 | e4578ec72b9740b92c22bf2018447f6c7d448ea50b5ee53b6da0a9e50f69a0e1 |
| minime/minime/src/sensory_ws.rs | 51991 | 5f2f5aa6e3415231341b4fb4d2dbf95a3024691cf12c3bd73081f669e3d4c6c6 |
| minime/minime/src/sensory_bus.rs | 168439 | 3fc6bd2a16bd78c5caa496f2a6dccbc67928da4fbded123998f59a82bcd4aa3a |
| minime/minime/src/stable_core.rs | 30316 | 53af3ff961e5e0d4e65095ab4e8a8bda3e6f5592d8020405acdca031dae0cbe6 |
| minime/minime/src/runtime/orchestration.rs | 321337 | 020595234e2820c0a8d08b62cac00f64d367837d7c4c11f9573c279a8367799a |
| minime/minime/src/esn.rs | 124286 | 98e8fe727e9908e8939d5317d23e954425748edb45b2a737e5624a42166dfe92 |
| astrid/capsules/spectral-bridge/src/autonomous/next_action/sovereignty.rs | 164198 | 919b5990dd57f435fd44115622bdfad2e2c7c74623c581f8921346af955a1297 |
| astrid/capsules/spectral-bridge/src/autonomous/next_action/dispatch.rs | 25869 | eeb58d23e0ed9b3ae33c75e7b1297354b36d2cb73b4b1eab4c9bcf5923a6b88d |
| astrid/capsules/spectral-bridge/src/action_continuity/guards.rs | 36711 | 887e9b2214be8ed29b3840466a22704735feb17cef72d73ea90bac39d31cf70c |
| astrid/capsules/spectral-bridge/src/autonomous/runtime/orchestration.rs | 306166 | fda7b52d3d1b3e4b56b5331fd27ea182f12ea99e11af30a21f67aa5b3c22712b |
| astrid/capsules/spectral-bridge/src/rescue_policy.rs | 100308 | 155bc25ce396a90b6cb54571855d2e829b08fa2e3c5e1de112accd11392a5367 |
| astrid/capsules/spectral-bridge/src/autonomous/reservoir.rs | 25261 | 9a8bd8865f91c5b20dfa68e37225d360c6609359c9a0ba3cc8db034e4190b07f |

The parent observatory session owns board publication and the combined visual
design proposal. Live incidence, deployment identity and measured spectral
effectiveness remain unresolved.

