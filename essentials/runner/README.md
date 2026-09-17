Current release adds `regulation --config SPEC.json --output RUN.json` for the field-only controller fixture (`{}` selects its fixed protocol). `verify` supports action v1/v2/v3 and `essentials-regulation-v1`; new action runs use v3 with explicit forcing metadata.

# Headless runner

For the action ladder and paired comparisons:

```sh
essentials-run actions --config essentials/actions/recipes/E-feedback.json --output research/outputs/essentials/feedback.json
essentials-run verify research/outputs/essentials/feedback.json
```

`actions` uses the same shared action engine as the viewer. Its recipes cover A–H;
`F-memory-independent.json` selects independent generation. Scripted replies are
the default. To use a separate local model, explicitly set `language` to an Ollama
backend, loopback endpoint with a port, and model, as described in the
[language guide](../llm/README.md). No model is contacted by verification or replay.

Journals save beside the output in `<run name>.journals/`. The JSON export also
contains exact journal text, save receipts and context/application references, so
replay does not need that folder. Action runs are bounded to 600 steps and 128
opportunities per arm. New action records use `essentials-actions-v2`; v1 still verifies with its original prompts;
the older stage and exploration formats retain their meaning. The
[action guide](../ACTIONS.md) explains the comparison controls and their limits.

Build with `essentials/build.sh` from the research root, or use Swift Package Manager:

```sh
mkdir -p research/outputs/essentials
swift run --package-path essentials essentials-run run --config essentials/stages/03-llm-loop.json --output research/outputs/essentials/essentials-run.json
swift run --package-path essentials essentials-run verify research/outputs/essentials/essentials-run.json
```

`run` accepts exactly one recipe and a separate output path. Missing optional recipe
fields use the documented defaults. It writes a completed, stopped or failed run;
Ctrl-C stops at the next safe boundary and preserves the completed frames. Failed
language runs are written and return exit code 1; stopped runs return 130.

`verify` validates bounded structure, availability, seed-generated weights, synthetic
forcing, saved noise, every state update, sensory covariance and spectra, eigenvector
residuals, fill and controller history, exact prompts and text feedback. It does not
contact a model, including when verifying an Ollama run. Eigenvector sign and basis
choices within degenerate eigenspaces can differ between Accelerate builds, so the
verifier checks eigenvector equations and orthogonality rather than byte identity.

Run JSON contains the recipe version and complete parameters, weights, actual inputs,
state/noise vectors, available sensory measurements, turns and their application
steps, and final status. Optional fields mean unavailable; they are not zero-valued
measurements. Input JSON is limited to 1 MB, run files to 256 MB, original stage recipes to 3,000 steps,
and all numerical dimensions and finite values are checked before inspection.

The core is independent of SwiftUI and Metal. `EssentialsSession` runs the same recipe
for the viewer and this command. Writes use the explicit output path; do not choose
any being's directories. Choose a local output folder separately from source recipes/examples; no checkout is required for the packaged runner.

For the controlled stage-D observation study use
`actions/recipes/D-observation-comparison.json`. New short-journal recipes should
set `promptVersion: 2`; an omitted version preserves the original prompt contract.
Optional Ollama settings are `contextTokens: 4096` and `responseFormat: "json"`,
alongside the explicit loopback endpoint and installed model. The native action UI
uses these bounded settings. No provider is started, downloaded or substituted.
