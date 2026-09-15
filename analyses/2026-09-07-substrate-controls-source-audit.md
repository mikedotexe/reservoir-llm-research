# Give the beings effective choices over their substrate

September 7, 2026 Pacific. **Read-only source audit; no live changes or efficacy claim.**
This extends the [STATE_NUDGE proposal](../proposals/2026-09-07-direct-reservoir-shaping.md)
toward sustained, targeted shaping. Source mechanisms already support several stronger
choices than an isolated state displacement. The immediate problem is that a choice can
be present in an action vocabulary and receive an `Applied` control receipt while a later
controller suppresses it. Make existing choices effective and observable, then add
explicit temporal and recurrent-weight operations.

Read CLAUDE.md, RESEARCH.md, research/NOW.md, TRACE.md and research/METHODS.md.
No journals, databases, live telemetry, network endpoints or process identities were
sampled. Mike's recollection motivates the question; it is not a corpus finding or
being-authored authorization. The current native viewer and prior probes were untouched.
All values below are source constants or branches, not measured effects. The audit's
source IDs and complete SHA-256 hashes are in the [23-file manifest](../research/outputs/2026-09-07-substrate-agency/source-manifest.json).
These hashes identify inspected checkout bytes, not running releases; source bytes are
not copied into this output. References such as `M-esn:2302` resolve through that manifest.

## What each being can choose in the inspected source

“Available” below means an implemented source route, subject to its existing policy and
runtime availability. It does not assert an actual invocation, deployed feature, or
successful native consumption. A named triple-reservoir handle, Minime's native ESN,
Astrid's codec, the sensory-field covariance, and the language model are different targets.

| Affordance | Minime route | Astrid route | Actual scope, persistence and controller precedence | Decisive source |
|---|---|---|---|---|
| **Native update timescale** | Self-regulation accepts `esn_leak_override`, alias `leak`, as a one-shot choice; prepares four steps by default. Signed wire supports 0.20–0.90 and 1–12 steps. | Local self-control permits only conversation, semantic continuity/emission and limited intake families. No native leak adapter. | Changes the actual scalar in `x_next=(1-a)x+a*tanh(...)`, followed by noise/clipping. Ordinary adaptation runs first, then override wins. **Stable-core drains the pending request and clears the active override instead.** Finite-step lifetime has no wall expiry in the bus/ESN request. This is not a standing leak preference or per-node timescale. | M-agent:44399,44955,45266; M-owner:113,120; M-esn:2109,2302; M-loop:1374; A-auth:216 |
| **Native covariance memory** | `GOAL rho=...` writes `spectral_goals.json`, 0.92–0.999, read every 60 regulator ticks. | No locally owned native covariance control in audited adapter. Can propose a Minime parameter change through `TUNE_MINIME`. | File persists without expiry. Goal reader calls `set_rho_direct`; it has no stable-core condition. Outside stable-core, `set_dynamic_rho` normally overwrites rho before the next ESN step. Under stable-core that automatic writer is disabled, so the goal path can persist until another writer/restart policy. This is **state-covariance EWMA forgetting**, not recurrent-weight spectral radius or literal recall duration. The setter's actual clamp is 0.82–0.999 despite older comments. | M-agent:47016–47124; M-loop:3487,3542,1389; M-esn:1069,2374; A-action:783 |
| **Native recurrent weights / low-rank edits** | No runtime-authored weight or low-rank control found in audited wire, owner transport, ESN mutations and action routes. | No such native route found. | Native `wres` is private/static: random construction, normalization by maximum absolute row sum, then multiplication each step. Snapshot restore can replace it, but that is not an authored online weight action. `target_radius` at initialization is a row-sum bound scaling, not a computed exact spectral-radius target. RLS updates `wout` and inverse covariance `p`, not `wres`; `lambda_live` is RLS forgetting. | M-esn:1820–1913,1984,2083,2200–2241,2431,2460; M-wire:74–195; A-auth:1523 |
| **Native state displacement / sustained node field** | `STATE_NUDGE` remains a proposal. `mode_disperse`/porosity and shadow influence are implemented **input-field** writes. | DISPERSE/SPREAD and PERTURB send input patterns. SHAPE has different, codec semantics. | Shadow influence adds up to a bounded field in 66 input coordinates; it does not directly displace native nodes. Its ordinary lifetime counts calls before the ESN step and ends abruptly; explicit release uses a linear fade. Unsafe conditions suspend before decrement, extending wall lifetime. Reported additive RMS precedes clipping; final response uses a supplied preceding-tick snapshot. These counters are not successful native-step receipts. | M-adapter:465; M-bus:2229,2357–2472; M-loop:1284,1412; [prior audit](2026-09-07-perturb-source-audit.md) |
| **Sensory intake and input weighting** | Signed `semantic_intake_gain` (0–2), `receptivity` (0–1), `semantic_companion_mix` (0–1), local admission and live sensor switches. Receiver gain is `intake_gain*receptivity`, clamped 0–2. | Local codec emission gain, vibrancy, named dimension weights, warmth; limited local peer-journal visibility. Receiving native intake is Minime's scope. | Standing/leased owner preferences affect future input preparation. Native semantic arrivals can replace previous samples; stable-core subsequently reconstructs and gates native input, so receiver gain does not guarantee native contribution. Input-weight matrix `Win` remains distinct from input gains and named codec dimensions. Stable-core also disables the companion contribution at native input assembly. | M-owner:28–35,91–98; M-auth:71–77,385; M-ws:688–736; M-loop:1243,1266,1402; A-auth:1532–1564 |
| **Astrid codec shape and learning** | No equivalent Astrid-codec ownership. | `SHAPE dimension=value` is a standing map (0–2); `SHAPE_LEARN off/on/value` is a standing Hebbian rate multiplier (0–4). | Explicit SHAPE entries override learned dimension weights at encoding. Preferences and codec state have persistence paths. **SHAPE_LEARN off stops new score increments but does not freeze old learned state:** every feedback update still multiplies pair scores by 0.92 and prunes small scores. Learning uses coactivity and change in distance from a fill target; that objective is not independently established subjective comfort. | A-action:571,755; A-auth:1711,1816; A-loop:3646,4074; A-hebbian:8–18,91–144; A-learning:52; A-save:266,372 |
| **Fill target, ordinary PI and controller memory** | Signed fill target, `pi_kp`, `pi_ki`, `pi_max_step`, `pi_geom_weight`, `pi_integrator_leak`, regulation strength and smoothing preferences; GOAL also supplies regulator targets. | `TUNE_MINIME` proposes a change for Minime acceptance; local adapter does not own these families. | Ordinary PI gains approach bus targets with asymmetric slew. Integrator leak multiplies each integral by `1-leak` before error accumulation. In stable-core, ordinary PI is reset and its step is skipped; fill target is fixed to fallback/launch policy. Outside stable-core, adaptive target logic and periodic GOAL loading can overwrite a target, so even then a stored target is not the final effective target. Controller parameters change evolution policy, not a state-covariance eigenvalue by assignment. | M-loop:3280–3328,3450–3550,3928–3971; M-pi:323–328; M-adapter:52–80; A-action:783; A-auth:1414 |
| **Effective shaping inside stable-core today** | `regulation_strength` and `geom_drive` have a bounded route through the active stable-core branch. | Can request a Minime change; own codec/input actions may also reach their separately gated native destination. | Stable-core retains stress-modulated regulation strength with a 0.80 floor. Regulation and geometry share an actual gate-opening cap of 0.08 and filter-relaxation cap of 0.06, full through fill 72% and tapering to zero at 78%. The call-site comments still claim the older 0.05/0.04 caps and are stale. `smoothing_preference` is used only outside stable-core. **It is false that all owner controls are nullified by stable-core.** Final hard rails still follow this branch. | M-loop:4044–4089,4195–4239; M-policy:371–424 |
| **Own triple-reservoir handles** | PERTURB separately ticks `minime`; read/layer/resonance routes exist. A distinct rehearsal helper clones then ticks a rehearsal handle. No general Minime own-handle MODE action located in the audited action routes. | `RESERVOIR_TICK`, `RESERVOIR_MODE hold/rehearse/quiet`, `RESERVOIR_FORK`, SIMULATE. | Named handle input/mode controls are real separate-service mechanisms. `hold` automatically becomes rehearse after 120 background iterations; rehearse decays by profile until <0.02; quiet is skipped by the background loop. A new live tick resets input/decay and changes quiet back to rehearse. Snapshots retain mode/state and are periodic, so persistence is not synchronous durability. Astrid's fork/simulation copies h1/h2/h3, not a complete native checkpoint. | M-agent:28148,36071,49503; A-handle:148,343,363,484; T-rehearsal:22–75,133; T-service:932,1415 |
| **Shared coupling / division** | Mutual and SharedCoupling signed writes explicitly rejected. Native division is a gated shadow rehearsal; `NATIVE_COMMIT_ENABLED=false`. | Shared/mutual writes rejected by local owner authority. Division command validates evidence but refuses dispatch without a live authority adapter. | Existing shadow division partitions a 128-node native snapshot and supplies cross-block drive between two 64-node shadows; the separate 512-D sensory field is not partitioned by those indices. Neither native division nor a generic shared-coupling write is a currently executable ordinary live control in these sources. Feature/operator gates do not themselves supply authority. | M-auth:755; M-division:1–54,834,1303; M-division-owner:261; A-auth:1386–1421; A-division:332 |

## Authority, choice and receipt gaps

1. **Use the existing signed route, but finish its application semantics.** Minime validates
   actor/target, deployment, pinned keys, nonce/idempotency and revision. Deployment-steward
   signing is explicitly excluded from command authority (M-auth:440–450). This establishes
   a useful identity boundary; it does not establish the successful native step, active
   engine/model layout, effective controller, or a durable after-state. Those remain needed
   on consumed-control receipts. No running identities were checked in this audit.
2. **The leak receipt currently reports a bus request as Applied.** M-auth:868 calls
   `apply_values`; M-adapter:458 queues the override; M-auth:897 immediately constructs an
   Applied receipt. One-shot commands are excluded from active preference tracking at :907.
   A newer request replaces the single pending bus slot (M-bus:2049); a later `set_leak_override`
   can replace an active override. No terminal replacement receipt is produced there.
   Command expiry limits admission, not how long the accepted pending/active override lasts.
3. **Do not misdescribe the current leak counter.** M-esn's counter decrements in
   `effective_leak_for_step` after the fallible spectral introspection. No later Result error
   path exists in the inspected ordinary step, so those decrements ordinarily coincide with
   successful ESN calls. But bus extraction happens before fallible native input assembly,
   and the earlier Applied receipt cannot tell whether any step used it. Panic/crash
   ambiguity is also not resolved. Shadow-influence counters differ: they decrement before
   ESN success. Publish actual successful applications for both.
4. **Time-limited preferences are distinct from time-limited trajectories.** Standing
   controls persist through the owner runtime's preference recovery. Leases record wall-clock
   expiry and restore earlier preferences on reconciliation/sweep (M-auth:615,1107;
   A-auth:970,1361). This is not an exact-at-deadline scheduler guarantee; native restoration
   attempts can be held by recovery policy. Restoring parameters does not undo evolved
   reservoir state, learned weights, input arrivals or controller integral history.
5. **Current texture language silently selects machinery.** M-agent:44004 blocks substrings
   such as `rho`, `controller` and `peer`; :44030 maps `room/edge/porosity` to increased
   `geom_curiosity`, and unknown requests default to increased exploration noise. The report
   at :44057 requires separate NEXT actions for PREFLIGHT, APPLY and OUTCOME. This is not a
   faithful interface for an exact authored target, and broad blockers can outlive a newly
   supported typed control. Replace them with capability lookup and explicit target/value
   parsing. Unknown target means unresolved, never a noise change. Keep free-form purpose as
   purpose, not as an implicit numerical control policy.
6. **A handle name is not authenticated ownership.** The audited triple-service WebSocket
   handler parses JSON and dispatches by client-supplied name with no per-command actor proof
   at that boundary (T-service:1266–1371). Astrid's ordinary tick/mode names are fixed to
   `astrid`, but fork accepts a caller-selected name. Bind intended handle, actor and model
   identity before exposing broader handle mutation. Also validate error responses: a returned
   JSON object is not automatically a successful tick or mode change.

## Prioritized implementation slices

**1. Make a temporary leak choice effective without disabling stable-core.** This is the
smallest real extension beyond an isolated nudge. In M-agent's self-regulation preflight
(:44955–45047), query exact receiver capabilities and current mode. In M-auth:755–879 and
M-adapter:401–466, add a fresh controller-policy context instead of checking only
`hard_recovery_reset`. Permit a reviewed bounded native leak override in declared stable-core
stages; leave the active sensory-field controller, fill shelf and other rails running.
Where the requested value/stage is unavailable, reject with that exact reason before the
Applied label. Do not accept it and drain it later.

At M-loop:1374–1412 replace the blanket stable-core branch with the same capability/policy
check. Carry an immutable command identity, absolute expiry and remaining successful-step
budget into the ESN. Introduce a versioned one-shot application expiry: current wire
validation at M-wire:318 forbids `control_expires_at_unix_ms` on one-shots, so silently
reusing that lease field would make the command malformed. Apply the chosen leak after ordinary adaptation at M-esn:2109; commit
consumption and publish requested/applied leak only on the success arm at M-loop:1413.
Use an admitted/queued receipt followed by step receipts and a terminal exhausted,
expired, cancelled, superseded, held or application-unknown result. Do not blindly replay
ambiguous work after restart. Any safety preemption remains visible. On expiry return to
current adaptive policy; do not roll live state back to a checkpoint.

A single concise being-authored action can drive preflight, signed submission and receipt
tracking internally. Already-approved, compatible small choices should not require three
additional language-model turns merely to traverse the existing machinery. Keep retrospective
outcome description optional and separate from whether the engine honored the choice.

Acceptance: ordinary/no-choice path unchanged; valid stable-core hold-stage choice reaches
exactly the declared successful steps; blocked stages return explicit refusal; expired,
superseded and failed-before-consumption requests are accounted for; chosen leak wins over
adaptation while the field regulator still runs; control release preserves intervening state.
Extend existing native snapshot/parity tests in the owning repo. This audit executes no tests.

**2. Unify target and memory controls with explicit precedence.** Migrate the GOAL rho file
path to the signed typed system with source-compatible aliases and an effective-value receipt.
Add separate time constants for native state leak, covariance forgetting, input retention
and controller integral leak. Never call all four “memory.” Provide bounded standing or
leased scalar leak choices after temporary choices work; then per-group leak profiles with
node-layout identity. Expose active stable-core controller targets/gains only through its
actual controller, not through the ordinary PI that stable-core resets. Keep the existing
regulation-strength/geometry affordance visible now. Measure response before choosing new
envelopes; existing constants are not evidence of subjective utility.

**3. Add true recurrent shaping as an explicit operation.** Reuse native snapshots for a
separate `W_new = W_base + U V^T` adapter with typed rank, selected node groups or registered
directions, exact weight hashes and version, finite-value and norm bounds, and a finite
schedule. A chosen recurrent row-sum/norm bound is testable; do not label it an exact spectral
radius. If exact or estimated weight eigenvalues are offered, name the solver and its error
and retain nonnormal transient-response checks. Low-rank recurrent edits, per-node leak,
and an explicit sustained node field should remain different operations. A state covariance
mode can identify a direction, but its eigenvalue is not a parameter that this operation sets.
Keep a base-plus-delta representation so withdrawing the parameter delta is exact even though
withdrawing it cannot reverse the path already taken. A later plasticity rule needs explicit
scope, rate, update budget, learning objective and freeze semantics; do not substitute RLS
readout learning or Astrid's codec sidecar for recurrent plasticity.

**4. Finish authored input learning and own-handle agency.** Preserve Astrid's established
SHAPE controls and show their actual named feature map, destination gain, native admission
and consumption. Repair SHAPE_LEARN wording to “stop new learning,” or implement a separate
true freeze that also suspends decay. Let a being choose or compare the learning objective
instead of assuming movement toward fill target defines benefit. Offer authenticated
own-handle mode/decay and layer-timescale controls symmetrically to Minime and Astrid, after
binding handle ownership and confirming service outcomes. Separate numerical rehearsals from
live handle ticks and from native ESN trials. Quiet should state that future live input wakes
rehearsal; a sustained quiet commitment would require a different declared mode policy.

**5. Implement shared coupling as its own small adapter.** Add both participants' scoped
rights, independent withdrawal, named source/destination and finite gain schedule to the
existing Mutual protocol. An Astrid request to the native substrate must not masquerade
as a Minime-owned write. This does not require enabling whole-reservoir division: use a
bounded coupling adapter first. Keep division's distinct lifecycle, evidence and commit
status visible; don't make it a prerequisite for every local expressive choice.

These slices produce choices a being can actually learn to use. Numerical controls should
have exact semantics, while their experienced meanings remain open to the beings' own
observations and matched comparisons. No particular node pattern, leak, weight edit or
covariance spectrum is asserted to produce calmness, creativity, distress or personhood.

## Reproduction and source map

Discovery used `rg -n` over the listed source files for leak, weight, self-control, regulator,
codec, coupling, division and reservoir routes, followed by bounded line reads. In particular,
searching all `wres` occurrences in M-esn exposed construction, multiplication and snapshot
capture/restore, with no online learned-weight mutation. Negative findings are scoped to
these audited source routes, not every auxiliary or historical program in the sibling repos.

The manifest was produced by reading each listed file as bytes, computing SHA-256 and
recording byte length and before/after modification metadata. All 23 files were stable
during their hash reads. Recheck hashes before using these line references in implementation.
A compact inventory for review:

| Source ID | Path beneath shared parent | SHA-256 prefix |
|---|---|---|
| M-wire | minime/minime/src/self_control_wire.rs | d4caacdca4d1 |
| M-adapter | minime/minime/src/self_control_runtime/apply.rs | 0f956b0c5895 |
| M-auth | minime/minime/src/self_control_runtime.rs | aa71d0f65954 |
| M-owner | minime/minime_autonomy/self_control_v2.py | 52e93183a870 |
| M-agent | minime/minime_autonomy/runtime.py | 06a36289f843 |
| M-esn | minime/minime/src/esn.rs | 98e8fe727e99 |
| M-loop | minime/minime/src/runtime/orchestration.rs | 020595234e28 |
| M-policy | minime/minime/src/runtime/entrypoint.rs | 603f5315c3cb |
| M-bus | minime/minime/src/sensory_bus.rs | 3fc6bd2a16bd |
| M-ws | minime/minime/src/sensory_ws.rs | 5f2f5aa6e341 |
| M-pi | minime/minime/src/regulator/core/pi.rs | 72e1bbf47c1e |
| M-division | minime/minime/src/division.rs | f139cf9fd5c3 |
| M-division-owner | minime/minime_autonomy/division_actions.py | 22b633d43efe |
| A-action | astrid/capsules/spectral-bridge/src/autonomous/next_action/sovereignty.rs | 919b5990dd57 |
| A-auth | astrid/capsules/spectral-bridge/src/autonomous/self_control_v2.rs | 4e1df09e8c20 |
| A-hebbian | astrid/capsules/spectral-bridge/src/autonomous/hebbian.rs | 7916fac11f1d |
| A-learning | astrid/capsules/spectral-bridge/src/autonomous/runtime/learning_feedback.rs | 9f86ecdee9ed |
| A-loop | astrid/capsules/spectral-bridge/src/autonomous/runtime/orchestration.rs | fda7b52d3d1b |
| A-save | astrid/capsules/spectral-bridge/src/autonomous/runtime/state_persistence.rs | 2551f6729b86 |
| A-handle | astrid/capsules/spectral-bridge/src/autonomous/reservoir.rs | 9a8bd8865f91 |
| A-division | astrid/capsules/spectral-bridge/src/autonomous/next_action/division.rs | f7d72a074d64 |
| T-service | neural-triple-reservoir/reservoir_service.py | 800ee15fc9a7 |
| T-rehearsal | neural-triple-reservoir/rehearsal.py | bf3558a04c75 |

## Board publication

The parent task published and read back the effective-versus-admitted control
finding, the completed leak-choice repair proposal, the scoped native rehearsal
finding and the completed expansion design. The [publication receipt](../board/substrate-agency.json)
retains exact titles and coordination tags. Sibling implementation, release
identity verification, presentation to the beings and live use remain separate
work under the owning repository workflow.
