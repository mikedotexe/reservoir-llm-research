# Try the activation experiment

This optional mode processes short observations without generating an answer,
feeds their contextual activations into a small recurrent system, and lets that
state influence later journal writing. It uses its own session format and a
dedicated local Qwen3 model. The ordinary Ollama journal loop remains available.

## Prepare the local runtime

The first adapter requires Apple silicon and Python 3.12. From this directory:

```sh
uv venv --python python3.12 .venv-activation
uv pip sync --python .venv-activation/bin/python activation-requirements.lock
.venv-activation/bin/python scripts/prepare_activation_model.py
```

The preparation script downloads the fixed Qwen3 4B 4-bit revision and writes an
asset-hash receipt under `.activation-models/qwen3-4b`. It loads no model and runs
no experiment. The environment and assets remain outside Git. The complete
dependency lock and preparation source are versioned.

## Create and read a session

Open **My reservoir → Activation experiment**. Select the absolute paths to the
prepared Python interpreter, worker `activation_worker/__main__.py`, and model
directory. The packaged app includes its own worker source; a source checkout can
use the worker beside this guide. Check the runtime and assets, then create the
session and choose Start explicitly. Opening the mode starts no model work.

Each session selects one immutable condition: no steering, a decaying trace, or
a recurrent reservoir. Use the same observation list and seed when comparing
conditions. Sessions run serially. A numerical step is controlled experimental
time: it does not advance while the model processes an observation or writes.

The default sequence has twelve quiet observations and six writing opportunities.
Quiet observations apply at steps 10 through 120, ten steps apart. Complete writing
is saved and read back before its activation enters the next step. A response that
ends at its output ceiling remains an incomplete attempt and cannot enter feedback.

Read whole entries with Earlier/Later or Follow latest. Select saved sessions in
the comparison reader to begin with concealed condition labels; reveal the
allocation deliberately in Evidence after recording your initial reading. Exact
technical evidence remains available. Excerpt annotations can retain an
interpretation, another plausible reading, and the source events that matter.

Stop retains completed evidence and cancels the owned model operation. Recovery
and import begin paused. An operation interrupted after dispatch is retained as
uncertain rather than automatically resent. Export a settled session for offline
verification and later reading.

## What the comparison can tell us

The intervention is a fixed geometric return into one transformer layer, with a
one-percent target residual norm. It is not a learned meaning decoder. Numerical
replay verifies the recorded state updates; it does not certify prose accuracy or
an interpretation of experience.

The prospective [first pilot](../../shared/reservoir-scope/activation-pilot.json)
freezes the observations, condition order, limits and reading questions. Read
complete sequences, including ordinary passages and counterexamples. What becomes
salient, which distinctions recur, and how uncertainty is carried are useful leads.
A striking passage is a reason to investigate its context; one sequence per
condition is not a general effect estimate.

For a qualified runtime, `scripts/run_activation_pilot.py` runs the frozen
three-condition comparison through the same Rust supervisor as the app. Supply
`--binary`, `--model`, `--qualification` (the successful mechanical-qualification
directory), and a new `--output` directory. It copies the exact qualified calibration,
checks worker/runtime identity, retains each attempt, and stops all further conditions
at the first failure. Its prose-only reading packets conceal condition labels.
The script requires the prepared activation Python environment.

See the [computational contract](../../shared/reservoir-scope/activation-experiment.md)
for capture, projection, timing and persistence details. This first mode has
scheduled writing opportunities. Choosing whether to write, learned readouts,
continuous wall-clock operation and additional sensory textures are later work.
