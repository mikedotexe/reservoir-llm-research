# Spectral bridge essentials

## Standalone use

From the repository root on macOS, build the shared package with
`ESSENTIALS_BUILD_DIR=/tmp/essentials-standalone essentials/build.sh`. Save this
public `EssentialsCore` example as `/tmp/bridge-example.swift`; it runs the field
and codec without constructing a reservoir or calling a language model:

```swift
import EssentialsCore

var field = try SensoryField(seed: 42)
var input = [Double](repeating: 0, count: 66)
input[0] = 0.5 // Synthetic video-coordinate input.
let observed = try field.step(input: input, retention: 0.955)
let encoded = TextCodec.encode("I wonder which pattern will persist.")
let feedback = TextCodec.applySpectralFeedback(encoded, measurement: observed)
input.replaceSubrange(18..<66, with: feedback)
let next = try field.step(input: input, retention: 0.955)
print(observed.displayEigenvalues, next.displayEigenvalues)
```

Compile and run the independent example:

```sh
swiftc -I /tmp/essentials-standalone/lib -L /tmp/essentials-standalone/lib -lEssentialsCore -framework Accelerate /tmp/bridge-example.swift -o /tmp/bridge-example
/tmp/bridge-example
```

Create the research output directory first with `mkdir -p research/outputs/essentials`.

For the assembled reservoir-plus-bridge recipe:
`/tmp/essentials-standalone/bin/essentials-run run --config essentials/stages/02-spectral-bridge.json --output research/outputs/essentials/bridge-run.json`.

## Equations and source relationship

The same 66D input drives a **separate** 32D sensory field. Channel scales are
0.75 video, 0.72 audio, 1.12 aux and 0.42 semantic, followed by gain 0.58 and tanh.
A seeded fixed matrix projects these values with `1/sqrt(66)` scaling. Nonzero
projected vectors are normalized to RMS 1: an explicit reduced-model convention
that makes covariance retention interpretable under trace normalization.

The field starts at identity and applies `A_next = q A + (1-q) z zᵀ`. Nonzero
updates scale toward trace 32, with a maximum rescale factor of 2. Silent input
has zero projected vector and decays existing covariance without restoring its
energy. This is an uncentered second-moment matrix. LAPACK's symmetric eigensolver
returns all 32 eigenvalues and modes; their signs are fixed for display while a
degenerate eigenspace has no unique basis. Eight leading modes define the displayed
entropy and head/shoulder/tail shares. Fill uses all 32, separately.

Text becomes a deterministic 48D vector: 32 handcrafted character, lexical,
sentence and marker features at gain 2, followed by 16 exact zeros. Embedding
coordinates 32–39 and narrative arc 40–43 are unavailable; 44–47 are reserved.
Lexical warmth/tension markers describe words, not measured emotions. The small
feature inventory is a new source-inspired implementation, not production codec
parity. A spectral feedback pass damps concentration and adds shoulder/tail texture
to named text coordinates before they enter input coordinates 18–65.

Source mapping: Minime `runtime/orchestration.rs` channel scaling/projection and
`runtime/spectral_math.rs` rank-one covariance; Astrid
`capsules/spectral-bridge/src/codec/{core,encoding,cascade,feedback}.rs` and
`codec_gain.rs`. Inspected Minime commit
`c9c2a70fb8dbb3fd51725839fce853cc8d576db5`, Astrid commit
`d7a8bbcff9baaf34a6c05fcda6c2c9ab9f0d7e89`, September 9, 2026.

The actual sensory field is nominally 512D and distinct from native ESN state.
Production codec implementation includes time-seeded noise despite an old
deterministic header. This reconstruction has no hidden randomness, embeddings,
rolling text history, personalized weights, recovery scaffolds or live sockets.
No source gain, native RMS, or text marker is substituted for production fill.
