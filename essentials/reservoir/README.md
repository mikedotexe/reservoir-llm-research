# Reservoir essentials

A fresh Swift leaky recurrent network, inspired by Minime's native ESN. This
component is independent of the running beings and has no model or network access.

## Standalone use

From the repository root on macOS, build the shared package with
`ESSENTIALS_BUILD_DIR=/tmp/essentials-standalone essentials/build.sh`. The following
code imports its public `EssentialsCore` module and runs only the reservoir.
Save it as `/tmp/reservoir-example.swift`:

```swift
import EssentialsCore

let model = try ReservoirModel(seed: 42)
var reservoir = try ReservoirEngine(model: model, leak: 0.65)
var input = [Double](repeating: 0, count: model.inputCount)
input[8] = 0.5 // One synthetic audio-coordinate impulse.
let stimulated = try reservoir.step(input: input) // Default: zero noise.
let following = try reservoir.step(input: [Double](repeating: 0, count: 66))
print(stimulated, following) // Two actual 32-coordinate states.
```

Compile and run the independent example:

```sh
swiftc -I /tmp/essentials-standalone/lib -L /tmp/essentials-standalone/lib -lEssentialsCore -framework Accelerate /tmp/reservoir-example.swift -o /tmp/reservoir-example
/tmp/reservoir-example
```

Create the research output directory first with `mkdir -p research/outputs/essentials`.

For the retained stage recipe, use the same build's runner:
`/tmp/essentials-standalone/bin/essentials-run run --config essentials/stages/01-reservoir.json --output research/outputs/essentials/reservoir-run.json`.

## Hands-on exploration

`ExplorationEngine` is a separate stepping interface for changing one mechanism at
a time. It starts with zero state, no input, no recurrence, no bias, no noise, and
no sensory measurement. Starting it alone does not create an impulse. The existing
numbered stage recipes and their records keep their original behavior.

```swift
import EssentialsCore

var exploration = try ExplorationEngine(seed: 42)
var controls = ExplorationControls()
let quiet = try exploration.advance(controls: controls)
let impulse = try exploration.advance(controls: controls, pulse: true)
controls.recurrenceEnabled = true
controls.recurrenceStrength = 0.5
let recurrent = try exploration.advance(controls: controls)
controls.repeatInput = true
controls.sensoryEnabled = true
let observed = try exploration.advance(controls: controls)
print(quiet.state, impulse.inputDrive, recurrent.recurrentDrive)
print(observed.spectral?.displayEigenvalues ?? [])
```

Use the same standalone compilation instructions above. Each call advances exactly
one third of a simulated second. Repeated input uses the existing synthetic
12-step-on/18-step-off video/audio waveform at that step's clock. A pulse instead
uses the fixed first waveform sample once. Input strength scales the actual input;
all auxiliary and semantic inputs remain zero. Recurrence strength scales the
original recurrent weights from zero to their 0.9 maximum row-sum bound. Bias has
its own switch, and 32 seeded noise samples are consumed at every step even when
noise amplitude is zero. Controls are recorded where they actually take effect.

Each frame exposes `inputDrive`, `recurrentDrive` and `biasDrive` in raw pre-tanh
units. `proposal` is their tanh response before leak and noise. The resulting state
is `clip((1-leak)*previousState + leak*proposal + noise, -1, 1)`. Input drive can
exceed one; recurrent drive is bounded by 0.9 and bias by 0.5. These values should
not share a silently clipped display scale. The optional sensory field remains
separate from the recurrent state; each off-to-on change starts a fresh field.

`exploration.record` uses the tag `essentials-exploration-v1`. It retains source
weights, projection, every applied control and input, all contributions, resulting
states, explicit noise, and optional sensory measurements. `record.write(to:)`
verifies then atomically saves JSON. `ExplorationRecord.read(from:)` bounds the
file to 256 MB and checks its structure; call `verify()` for numerical verification,
or construct `try ExplorationEngine(record: record)` to verify and resume. Import
preserves the recorded frames, including valid alternative eigenvector signs.
Verification recomputes all steps and checks covariance/eigenvector residuals.
Runs stop at 1,800 retained steps and require an explicit reset to begin again.

## Native recurrence relationship

`x_next = clip((1-a)x + a tanh(Win [u,1] + Wres x) + noise, -1, 1)`.
All nodes use the same previous state. Default size is 32, input count 66, leak
0.65, input weight scale 0.5, recurrent density 0.1 and maximum absolute row-sum
bound 0.9. This bound is not a measured eigenvalue or spectral radius.

Input meanings are video 0–7, audio 8–15, aux 16–17, semantic 18–65. Aux weights
receive a 1.2 factor and semantic weights 1.6; the bias has neither. SplitMix64
makes initialization reproducible. Noise is supplied explicitly to each step;
empty noise means zero. The runtime records any requested nonzero noise.

Source mapping: sibling `minime/minime/src/esn.rs`, `ESN::new` and
`ESN::step_controlled`; construction in `runtime/orchestration.rs`. Source inspected
at Minime commit `c9c2a70fb8dbb3fd51725839fce853cc8d576db5` on September 9, 2026.
Fresh implementation and Double arithmetic do not promise native numerical parity.
The live source has 128 nodes and a 12D companion extending 66 inputs to 78.

Omitted: native adaptive leak, spectral self-reference, RLS prediction, filters,
prime scheduling, companion input, stable-core recovery, action routing and all
autonomy. The measured sensory field in the next component is a separate state,
not a projection or replacement of this native recurrent vector.
