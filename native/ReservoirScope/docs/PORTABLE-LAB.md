See [Current release](../../../research/CURRENT-RELEASE.md) for the current candidate and [guided walkthrough](GUIDED-TOUR.md). Version **0.13.0** later added that guided route, playback fixes and separate active-state/controller examples. The account below documents the 0.12.0 portable foundation; its original interface and record-version descriptions are historical.

# Reservoir Scope 0.12.0 · portable research lab

Copy **Reservoir Scope.app** to a trusted Apple silicon Mac running macOS 14 or
later. Open it without the repository, Mac Mini, Ollama, or a network connection.
The first screen is **Essentials → Actions & comparisons → A**.

## From state to journal

Select any component A–H, or use Previous/Next. Run starts a fresh experiment
when changing configuration; Compare with previous starts a matched pair.
Step advances one numerical boundary. Next journal advances to the next writing
opportunity and pauses after its outcome; in a recording it moves the cursor.
Replay only reads recorded data. Interactive runs keep the 300-step default.

A–C have no journal component. D adds writing, E returns saved writing to the
reservoir on the next step, F supplies the previous journal in the next prompt,
G permits WAIT, and H adds sensory-retention regulation. The journal pane and
inspector share the recorded cursor. A pending or failed attempt is not a saved
journal. Saved output is not feedback until its recorded application boundary.

**Runs & examples** contains eight scripted 120-step component examples, a scripted
observation comparison, five recorded model runs for D–H, and a recorded model
observation comparison. Their scheduled opportunities are at steps 30, 60 and 90.
Four shorter model-qualification attempts are included separately, including the
three failures. Open example selects the scripted example for the current component.
The observatory's recorded Minime/Astrid evidence is also bundled. Live feeds are
separately selected read-only files; they are not prerequisites for these experiments.

## Local records and transfer

Explore, Stage experiments, Actions, journals and imports use one local store:

```
~/Library/Application Support/Reservoir Scope/
```

Import verifies a copied snapshot through a normal file dialog. Export writes a
portable JSON file anywhere explicitly selected in the save dialog. Journals,
prompts, raw replies, observations and application boundaries travel inside the
record. Historical paths are provenance; replay does not follow them. A separate
journal directory is not required to verify or replay an export.

Failed record writes remain in memory, with Retry save and Export available.
Quit waits for writes; if evidence remains unsaved, the app offers a return to
the experiment or an explicit discard. A failed journal save closes its feedback
gate and remains a failed opportunity, even if the enclosing record is exported.

The `RESERVOIR_SCOPE_LIBRARY` environment variable selects an isolated absolute
store directory for qualification. Ordinary launches use Application Support.

## Fresh local writing

The default experience needs no running model. For optional new writing, select
Independent and Use a local model, then explicitly enter an existing HTTP loopback
endpoint with a port and an installed model name. These settings are saved locally.
The app neither downloads a model nor starts a service. Connection, validation and
completion failures stay visible; no other provider or scripted text is substituted.
Opening a model recording enables the local-model option for future runs without
overwriting your saved endpoint/model; generation stays disabled until configured.

New action requests explicitly use JSON output, temperature 0, a 4,096-token context,
and a 256-token output limit. Prompt version 2 asks for at most 40 journal words.
The word request is an instruction, not an independently enforced quality measure.
Original stage experiments retain prose output. Older records preserve their original
prompt and provider settings. A temperature of zero does not guarantee reproducibility.

The bundled model is `phi3:mini`, digest
`4f222292793889a9a40a020799cfd28d53f3e01af25d48e06c5e708610fc47e9`.
Its exact inventory, runner hash, settings, qualification outcomes and recording hashes
are in `Contents/Resources/model-recordings.json`. All six finite recording runs
completed, retaining 21 journals. The package contains recorded outputs, not model weights.

## What can the journal observe?

This separate S-009 comparison keeps stage D in both arms. Both receive recurrence,
the same seeded input/state trajectory and the same sensory measurements. Feedback,
journal memory, action choice and regulation are off. The control receives sensory
measurements; the other arm receives the same prompt plus coordinates `x[0]` through
`x[31]` and the current recorded step. Numbers use eight decimal places and a fixed
POSIX locale. No renderer colors, surfaces or descriptions of experience are submitted.

Requests are independent. Order alternates left/right, then right/left, and is saved
on each started request. Both outcomes are retained when one fails. The question,
expected difference, alternatives and stopping rule are saved before generation.
New records use `essentials-actions-v2`, including comparison kind, observation
channels, request order and prompt version. V1 keeps its original sensory-only prompt
verification. Verification rejects changed coordinates, step identities, channels
or request-order metadata. It establishes consistency of recorded evidence, not
independent authentication of a provider call or an improvement in writing.

Scripted responses qualify mechanics only. Different model prose is an observation.
This synthetic study is separate from the live Beings and S-007 fidelity tracking.

## Headless runner and verification

The app contains the same core and a standalone runner at
`Contents/MacOS/essentials-run`. Copying that executable to another trusted research
Mac is sufficient for run/verify; it links system libraries only.

```sh
"Reservoir Scope.app/Contents/MacOS/essentials-run" actions --config recipe.json --output run.json
"Reservoir Scope.app/Contents/MacOS/essentials-run" verify run.json
python3 "Reservoir Scope.app/Contents/Resources/verify-package.py" verify --app "Reservoir Scope.app"
```

The first two commands require no Python. The last optional packaging check verifies
the resource hashes and ad-hoc signature without the source checkout. Source hashes
and the build's base commit are recorded in `release-identity.json`; the base commit
alone does not describe uncommitted source changes. Public distribution and notarization
are outside this release.
