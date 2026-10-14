# Owned model helper: review before use

`owned_model.py` is a standalone Python standard-library helper pinned to the SHA-256 of [model-selection.json](model-selection.json). Importing it does nothing. Staging and launching are separate explicit commands. Neither command has been executed as part of writing this helper; synthetic qualification is recorded separately when available.

Wait until the root task completes the frozen reliability run before staging or launch. Commands below are intended to run from `desktop/ReservoirScope`. They target only the exact proposed run directory in the selection receipt; an existing directory causes staging to fail without overwriting or deleting it.

```sh
python3 validation/2026-10-13-reading-0.12.1/owned_model.py stage
python3 validation/2026-10-13-reading-0.12.1/owned_model.py launch --seconds 900
```

Staging validates the pinned manifest and all five referenced blobs before copying any blob. It checks ordinary files and nonsymlink ancestors, exact sizes and SHA-256, checks source identity across reads, copies independent bytes using exclusive destination creation, fsyncs each copy and verifies its digest. It requires the proposed 8 GiB free-space cushion. No model inventory scan, pull, version command or endpoint call occurs. A failed stage leaves a diagnostic and any partial owned files for inspection; it cannot be mistaken for a complete stage or reused automatically.

The staging receipt binds the selected executable hash and installed Info.plist, and the metadata of conventional private/public keys and `server.json`. **Conventional credential/config checks are lstat-only:** device, inode, size, timestamps, permissions and owner. They do not read or hash file contents. Unchanged metadata is useful continuity evidence, not cryptographic proof of unchanged contents. Neither helper command writes those conventional files.

Launch revalidates the completed stage, model copies, software and conventional metadata. It removes inherited `OLLAMA_*` and proxy overrides, installs only the selection's child overrides and preserves `HOME`. It executes only the exact selected `serve` argv, with a new session/process group. The supervisor retains its direct child unreaped while deciding group cleanup, preventing PID reuse between identity checking and signalling. It requires Python's `waitid(...WNOWAIT)` support and fails before launch if unavailable. No process listing or default-service discovery occurs.

`endpoint.json` is published exclusively when the owned service log reports a valid nonzero `127.0.0.1` listener. This is log evidence, not a readiness probe. Root may then configure the app with that endpoint and run its explicit readiness check. The service log is capped at 16 MiB while excess output is drained and counted. One trailing incomplete log line may not be retained as listener evidence.

To end early, send SIGINT/SIGTERM to the **supervisor PID** recorded during launch, or create the ordinary file `<owned-run-directory>/stop-request`. The helper checks its 900-second maximum using a monotonic clock, sends SIGTERM only to its verified owned group, and keeps the leader unreaped through a grace period of up to 10 seconds. If that original group remains, it sends group-scoped SIGKILL before reaping the leader, even if the leader exited first; a final wait is bounded to 5 seconds. It writes `supervision-result.json`, including conventional before/after metadata and errors. The direct-child exit result does not independently prove the absence of a descendant that escaped the original group; the reviewed Ollama runner path is expected to inherit that group. There is no daemon, automatic restart or whole-machine process cleanup.

The helper is an isolation and identity aid, not an OS sandbox, model-quality test, peak-RAM limiter or disk quota for Ollama's auxiliary files. Record any unexpected conventional metadata change, startup failure, request timeout/validation failure or missing owned runner cleanup as an outcome. Do not replace the provider or silently retry. The bounded app recipe and separate package/resource evidence remain in the selection handoff.

Synthetic tests use tiny temporary files and mocked process operations only:

```sh
python3 -m unittest discover -s validation/2026-10-13-reading-0.12.1 -p test_owned_model.py -v
```

They do not establish real-service startup, child-runner cleanup, memory consumption or model output quality. Per the ongoing resource protocol, do not run them before `2026-10-13T18:36:06Z`.
