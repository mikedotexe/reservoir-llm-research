# Reference Zones: source contract

Inspected September 6, 2026 Pacific, for [S-002](../research/studies/S-002-reservoir-observatory.md). Subject: Minime's stable-core regulation of the sensory-covariance fill estimator. This is a source audit supporting a steward-side explanatory view, not an intervention, a measured controller performance result, or a claim about the beings' subjective comfort.

The close-up should show the intended operating shelf and the distinct meanings of its boundaries. A source-defined threshold is not a demonstrated safe/unsafe divide. The morning replay does not retain controller mode or stage per tick; coloring a sample's fill cannot recover its historical stage.

## Thresholds that the view can honestly annotate

The native model's eight annotations obtain their plotted values from bundled `ReferenceBands` and `StructuralPIConfiguration`. They never infer stage from replay fill. Missing optional hysteresis thresholds are omitted rather than invented. Source paths below are relative to the sibling Minime repository; the native annotation preserves that same convention.

| Reference | Inspected value | Exact source behavior | Primary source |
|---|---:|---|---|
| Hold release / lower shelf reference | 58% | An existing Hold is retained only for `fill > 58`; it releases at `fill <= 58`. Higher-priority stages are evaluated first. | `minime/src/rescue_overfill.rs:70–76` |
| Hold entry | 60% | Enter Hold at `fill >= 60` when Discharge and Elevated do not apply. The 58–60 gap is hysteresis, not an unregulated gap. | `minime/src/rescue_overfill.rs:70–76, 97–123` |
| Configured reference center | 68% | Structural error is `fill − 68`; this is not a hard clamp or symmetric restoring force. | `minime/src/rescue_scaffold.rs:21–22, 1655–1664` |
| Elevated release | 71.5% | An existing Elevated is retained only for `fill > 71.5`; it releases at or below 71.5. A current Discharge has its own release test and priority. | `minime/src/rescue_overfill.rs:79–95, 97–123` |
| Elevated entry / upper shelf reference | 72% | Enter Elevated at `fill >= 72` unless Discharge takes priority. Hold/Elevated guard commands blend over `71.5 <= fill < 74`. | `minime/src/rescue_overfill.rs:79–85, 230–251, 334–345` |
| Structural PI positive-error onset | strictly above 72% | `max(fill − target − deadband, 0)`, with `target=68`, `deadband=4`. New proportional error and integral accumulation begin only above 72. At 72 or below, existing integral decays. | `minime/src/rescue_scaffold.rs:1655–1664` |
| Strong rail | 74% | For valid fill/slope with the structural controller active, `fill >= 74` requests drain weight at least 0.24 regardless of slope. This is a policy floor, not the PI sum. | `minime/src/rescue_scaffold.rs:45–52, 1444–1485` |
| Force / warning rail | 78% | Stable-core's warning range starts at 78. Extra bounded gate/filter loosening tapers from full headroom at `fill <= 72` to zero at `fill >= 78`. It is not the structural forced-drain onset. | `minime/src/rescue_overfill.rs:46–49`; `minime/src/runtime/entrypoint.rs:371–425`; `minime/src/runtime/orchestration.rs:2980–3004` |

Sibling source links: [overfill guards](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/rescue_overfill.rs:40>), [structural controller](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/rescue_scaffold.rs:1444>), [gate/filter headroom](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/entrypoint.rs:371>), [runtime application](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2194>).

**Two references coincide at 72%, but their comparisons differ:** Elevated enters at or above 72; new structural PI error starts strictly above 72. The view keeps separate annotations at the same geometric position. There is no lower 64% structural PI deadband edge in this source. Do not render `68 ± 4` as a controller-off zone.

## What “the regulator keeps conditions within limits” can mean here

The code contains several layers of protective response. Stage selection uses the previous stage, making transitions resistant to small reversals. The stage guard fixes or blends gate, filter, covariance retention and trace targets. It also asks for generic gate/filter PI reset/freeze. The runtime actually resets that separate PI and resets the structural integral at stage changes (`orchestration.rs:2104–2139, 2606–2634`). This does not mean the structural PI is permanently frozen.

The structural PI runs with `last_fill_pct`, its prior measured slope, stage and scaffold-active flag (`orchestration.rs:2194–2203`). It is inactive without an active scaffold or finite fill (`rescue_scaffold.rs:1541–1551`). In its ordinary branch:

```text
error = fill − 68
u = clamp(max(error − 4, 0) / 20, 0, 1)
if u > 0: integral = clamp(integral + u, 0, 1)
else:     integral = 0.85 × integral
PI output = clamp(0.55 × u + 0.04 × integral, 0, 0.12)
```

These are per-step updates; source step count is not continuous elapsed time. A current snapshot's reconstructed P and I are not a historical sequence. Earlier-stage resets, recovery/reentry branches, and unknown prior integral prevent faithful reconstruction from fill alone.

Drain policy is separate from that bounded PI output (`rescue_scaffold.rs:1444–1530`): below 72 it returns zero drain; in `72 <= fill < 74` it requests 0.04 only if slope is strictly positive, otherwise zero; at or above 74 it imposes a 0.24 floor; at or above 82 it imposes a 0.70 floor. Invalid fill or slope yields zero with an explicit invalid-state reason. The later “moderate” branch is unreachable with the inspected equal moderate/strong thresholds of 74, because the strong branch returns first; it should not be drawn as another operating band.

The application path can further adjust requested drain by a bounded spectral-pressure bias, enforce restart-gate floors, and clamp weights (`orchestration.rs:2311–2349`). Applied drain and PI output must therefore remain distinct. The resulting weights blend normalized live sensory covariance, a scaffold, and a rank-cold drain matrix (`rescue_scaffold.rs:1331–1358`; `orchestration.rs:2356–2374`). “Drain” is a covariance-policy operation, not liquid removal, occupied neurons, or measured memory deletion.

These mechanisms establish what the source attempts to do. They do not establish live success rates, a mathematical invariant that fill stays inside the shelf, emotional safety, or nonlinear stability of the recurrent reservoir. The visual should say “operating references” and “protective response” rather than certify a safe region.

## Additional boundaries found, but not silently added to the dataset

The current source has other boundaries beyond the existing plotted reference set:

- **Discharge:** enter at `fill >= 82`, retain while `fill > 76`, release at or below 76. The inspected stage guard sets decay-only operation, gate 0.01, filter 1.0, covariance retention 0.05 and trace scale 0.05 (`rescue_overfill.rs:47–48, 88–95, 207–225`). Structural forced drain also begins at 82, not 78 (`rescue_scaffold.rs:48, 1467–1475`).
- **Sustained crisis:** stable-core uses `fill >= 87` for 30 consecutive history ticks; falling below 87 resets the counter. The runtime logs the first breach, then a crisis-abort event/alert when sustained (`rescue_overfill.rs:50–51`; `orchestration.rs:3005–3055`). This audit does not infer downstream process termination from the alert's name.
- **Low-fill recovery:** Bootstrap enters below 35 and retains below 42. The active structural controller starts recovery below 42, or below 45 with slope below −2 percentage points/second. Release has duration and slope conditions, including reaching 60 with nonnegative slope for two candidate steps or reaching 62 after the minimum impulse duration (`rescue_overfill.rs:40–41, 61–67`; `rescue_scaffold.rs:1589–1624`). These are not additional symmetric edges of the Hold shelf.

These values are source-audited context in this note, not new recorded configuration fields. If added as plotted shells later, extend the exporter/configuration evidence first and preserve their distinct state and duration conditions. References should not be synthesized by treating all boundaries as scalar thresholds with the same action.

## Reproduction and evidence scope

Inputs: four bounded current-source files in the sibling Minime repository, and one bundled JSON containing **507** historical sample pairs. No sibling writes, database access, runtime restart, or new health capture was needed. The existing exporter [reservoir_3d_capture.py](../probes/reservoir_3d_capture.py) extracts source constants and records source hashes and anchors; it distinguishes current inspected source from an unverified historical loaded binary.

The exact bounded check used for the cached configuration and current-source identities was:

```python
import json, pathlib, hashlib
p = pathlib.Path('native/ReservoirScope/Sources/ReservoirScope/Resources/data.json')
d = json.loads(p.read_text())
print('bundled samples n=', len(d['samples']))
print('bands=', json.dumps(d['bands'], sort_keys=True))
print('structural_config=', json.dumps(d['controller']['structural_config'], sort_keys=True))
for name in ('rescue_overfill.rs', 'rescue_scaffold.rs',
             'runtime/entrypoint.rs', 'runtime/orchestration.rs'):
    p = pathlib.Path('../minime/minime/src') / name
    print(name, hashlib.sha256(p.read_bytes()).hexdigest())
```

Observed source SHA-256 values:

| Source | SHA-256 |
|---|---|
| `rescue_overfill.rs` | `75e30587768fd08b0d333df2a1e0fc4bbfc78a841d5e2594f971f312c0387ecb` |
| `rescue_scaffold.rs` | `c4edff5c69bb0e0bf9477a0a3e16ec2da11f5b0171e4f34ed6e18e55d9dc959b` |
| `runtime/entrypoint.rs` | `603f5315c3cb52e42c4a5852fd05261185e462a1be49774b7bec7e678139353e` |
| `runtime/orchestration.rs` | `af2ec480922a7c277fcb39b6c55ee5900dd11fb49c696cdc20e8aeae10b003b4` |

The model and checks passed Swift 6 type checking with the existing evidence/resource definitions. All seven [native reference checks](../native/ReservoirScope/Tests/ReferenceZoneChecks.swift) passed against the bundled evidence: threshold equality, the one-sided PI allowance, two distinct meanings at the coincident upper-shelf/PI reference, supplied configuration values, absent optional hysteresis evidence, and invalid scalar input. App-level checks and visual inspection belong to the parent implementation's receipt. The line references and policy prose are tied to this inspected source; a future source/configuration refresh should revisit both numeric positions and their explanatory contract.
