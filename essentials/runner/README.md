# Headless runner

`essentials-run` runs synthetic numerical experiments and verifies saved records
using the same core as Reservoir Scope. The separate `reservoir-research` command
organizes retained research evidence and archives; see [research tools](../../research/TOOLS.md).

## Scripted quickstart

On an Apple silicon Mac running macOS 14 or later, install the Xcode command-line
tools or Xcode so `swiftc` and the macOS SDK are available. Run this block in a
terminal from the repository root. No Python installation or model service is
needed for these commands.

```sh
task_runner="$(zsh essentials/build.sh)"
mkdir -p research/outputs/essentials
task_run_dir="$(mktemp -d "$PWD/research/outputs/essentials/quickstart.XXXXXX")"
"$task_runner" actions --config essentials/actions/recipes/E-feedback.json --output "$task_run_dir/feedback.json"
"$task_runner" verify "$task_run_dir/feedback.json"
```

The build prints the runner's absolute path and keeps compiler outputs in the local
cache. The recipe explicitly selects scripted replies and a matched D/E comparison:
300 steps per arm, with the journal-to-reservoir return added in E. Expect
`Completed: 300 action steps per arm` followed by
`Verified 300 action steps per arm`. Verification runs in a separate process and
recomputes the retained numerical chain. These commands neither read Being sources
nor contact a model. A successful verification establishes record consistency,
not a writing-quality improvement.

If you already have a copied Reservoir Scope app, its
`Contents/MacOS/essentials-run` is a standalone runner. Set `task_runner` to that
executable's full path instead of the build line; use the same recipe and fresh
output commands. The source quickstart above does not require an existing app or
another machine's cache.

## Recipes and records

`actions` uses the same shared action engine as the viewer. Its recipes cover A–H;
`F-memory-independent.json` selects independent generation. Scripted replies are
the default. To use a separate local model, explicitly set `language` to an Ollama
backend, loopback endpoint with a port, and model, as described in the
[language guide](../llm/README.md). No model is contacted by verification or replay.

Journals save beside the output in `<run name>.journals/`. The JSON export also
contains exact journal text, save receipts and context/application references, so
replay does not need that folder. Action runs are bounded to 600 steps and 128
opportunities per arm. New action records use `essentials-actions-v3`, including
explicit forcing metadata; v1/v2 still verify with their original prompt and
forcing interpretation. The older stage and exploration formats retain their meaning. The
[action guide](../ACTIONS.md) explains the comparison controls and their limits.

The `run` subcommand uses the original four stage recipes. After the quickstart,
you can use the same runner in another fresh directory:

```sh
task_stage_dir="$(mktemp -d "$PWD/research/outputs/essentials/stage.XXXXXX")"
"$task_runner" run --config essentials/stages/03-llm-loop.json --output "$task_stage_dir/run.json"
"$task_runner" verify "$task_stage_dir/run.json"
```

`run` accepts exactly one recipe and a separate output path. Missing optional recipe
fields use the documented defaults. It writes a completed, stopped or failed run;
Ctrl-C stops at the next safe boundary and preserves the completed frames. Failed
language runs are written and return exit code 1; stopped runs return 130.

`regulation --config SPEC.json --output RUN.json` runs the separate field-only
controller fixture (`{}` selects its frozen protocol). Its record format is
`essentials-regulation-v1`, also supported by `verify`.

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
