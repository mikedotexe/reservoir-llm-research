# Activation preparation protocol v1

This installer is separate from inference and the activation session format.
Importing its modules performs no work. The application starts it only after an
explicit Prepare or Resume action; opening the app never starts a download.
The experiment's separate Check action uses the worker's metadata-only inspection.

## Resource and installation layout

The application bundles `activation_setup/` as source and an adjacent
`activation_setup_bundle/` with `setup-manifest.json`, three hash-bound lock and
inventory files, notices, and private staged `assets/`. Bootstrap archives and
executables are ignored in source control. `scripts/freeze_activation_setup.py`
recreates that resource bundle from fixed upstream releases, the unchanged
34-package version lock, and independently checked local pinned model files.
The freeze tool never loads a model. Existing different frozen bytes are refused.

The selected bootstrap is CPython 3.12.13 build 20260510 and uv 0.10.8 for native
Apple Silicon. Activation's configured minimum is macOS 26. This requirement does
not qualify every supported operating-system release; exact observed package/host
qualification is recorded separately. Python's installation-only archive and the
release-tagged upstream library notices are included, along with uv's two licenses.

Rust validates the archive hash, safely extracts it into the final path, owns
bootstrap recovery, and starts the interpreter below. The driver never copies a
development virtual environment or uses Homebrew. `runtimeId` is an immutable
installation identity; changing Python or dependency artifacts requires a new ID.

```
<setupRoot>/runtime/<runtimeId>/python/bin/python3.12 -I -B \
  <resourceDir>/activation_setup/__main__.py \
  --setup-root <setupRoot> \
  --resources <resourceDir>/activation_setup_bundle \
  --parent-pid <application PID> --mode prepare
```

The environment is created at `<setupRoot>/runtime/<runtimeId>/venv`, and model
files at `<setupRoot>/models/<pinned revision>`. Neither configured environment is
renamed. The interpreter in the final receipt is `venv/bin/python`. `--mode inspect`
checks an existing receipt, exact package versions and all model hashes without
installing, downloading or writing; it invokes a metadata-only child interpreter.
The application's lightweight status read does not invoke this driver at all.
Package-manager configuration, cache, data and credential locations are app-owned.
`NETRC=/dev/null` prevents uv's always-enabled netrc lookup from reading the user's
credentials; keyring use is disabled and the actual HOME value is preserved.
It checks receipt identity, declared paths, the interpreter and model provenance
presence; it does not hash model weights or verify installed package versions.
A missing or changed weight can therefore leave lightweight status at Ready until
the explicit full Check setup reports the failure. Ready alone is not that full check.

## Process and progress contract

Rust owns one setup process group and its 30-minute deadline. uv inherits that group;
the driver does not create another group. The driver also watches its parent's PID
and reaps its direct uv/metadata child after parent disappearance. SIGINT/SIGTERM
mark cancellation; subprocess escalation terminates then kills after five seconds.
Network reads use 30-second timeouts and bounded chunks. No inference operation or
service is started. No global process-name termination is used.
Rust launches setup children with the owned setup root as their working directory;
the Python supervisor explicitly uses that same root for uv and metadata probes.
Setup therefore does not depend on the app's launch directory, which may be removed
or unavailable after relocation or source isolation.

Stdout contains JSON-lines with schema `activation-setup-progress-v1`. Phases are
`environment`, `model`, `verification`, `ready`, `failed`, and `cancelled`. Running
events may carry `message`, or model `file`, `downloadedBytes`, `totalBytes` for that
file. Success is `phase: ready`, `status: complete`, `receiptPath`, and a nested
`receipt`. Failure/cancellation carry `diagnostic` and exit with 1/130 respectively.
Subprocess output is captured and never mixed into this protocol.

## Ownership, retry and completion

An advisory `setup.lock` excludes simultaneous setup drivers. The driver preserves
Rust's bootstrap files. It owns `.environment-owner` beside its environment and
`model-owners/<revision>.json`, written before model-directory creation. Within the
model directory `.setup-owner` identifies its partial downloads. The marker has no
JSON suffix so it is not confused with model/tokenizer assets by the inference
worker. Unexpected files, links and ownership mismatches are refused.
Rust writes `bootstrap-owners/<runtimeId>.json` before creating the runtime directory,
so an interruption before its inner `bootstrap-owner.json` write remains resumable.
A matching legacy inner marker can establish the sibling marker without changing
an existing environment; arbitrary existing directories are never adopted.

An explicitly repeated Prepare can rebuild a matching owned incomplete venv,
resume a verified HTTP byte range, or restart an owned partial when the server
ignores Range. A completed bad-hash download is retained outside the model under
`model-download-failures/`; the next explicit Prepare can fetch a fresh copy. There
are no automatic retry loops. Incomplete transfers retain their partial bytes.

uv receives exact hash-pinned wheels, an explicit interpreter, wheel-only policy,
disabled Python downloads/config discovery, and an owned cache. Inherited Python,
pip, uv, provider-token and proxy settings are not forwarded. Model HTTPS uses the
installed pinned certifi trust roots and the frozen Hugging Face revision/asset
hashes. Network access belongs to preparation only, with no change to the app's
loopback-only provider HTTP client or inference worker's offline settings.

`ready.json` is atomically published after package metadata and every expected model
file are checked. It has schema `activation-setup-ready-v1`, `runtimeId`,
`manifestSha256`, `pythonPath`, `modelPath`, `modelProvenanceSha256`, `lockSha256`,
`completedAtUtc`, and runtime metadata. Publication is the completion boundary:
cancellation afterward cannot relabel a verified completed installation as partial.
The receipt is setup evidence, not real-model qualification or permission to infer.

An existing `ready.json` also prevents preparation from modifying the completed
installation. Repeated preparation only inspects it. If lightweight status detects
invalid readiness, it reports Failed with Resume disabled, and Prepare/Resume refuse
to start. If this driver's full inspection finds damage that lightweight status
cannot detect, its diagnostic likewise explains that the prepared files and receipt
are preserved. The inference worker's explicit Check setup can report a missing or
changed weight while the separate lightweight preparation status remains Ready;
that failure does not enable Resume or modify the prepared installation.
This is not an interrupted preparation. This preview has no repair or upgrade route
for an existing prepared installation; keep its files intact and contact the preview
maintainer with the diagnostic. Neither checks nor attempted preparation remove the
receipt, overwrite assets, or turn this case into an automatic retry.

## Focused checks

```
python3 -B -m unittest discover -s activation_setup/tests -v
```

These tests use synthetic files, fake transfers and a briefly owned sleeping Python
child to check parent-loss reaping. They do not download packages, load MLX, start
a model or exercise packaged macOS UI. A fresh standalone-runtime setup and its
real-model qualification remain distinct integration checks.
