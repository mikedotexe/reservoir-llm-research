# First bounded local-model rehearsal: cached Gemma 3 4B

Recommend **the existing cached `gemma3:4b`**, pinned by the local manifest SHA-256 below, for a short plain-prose journal rehearsal. This is a selection and prospective launch handoff. No model has been copied, downloaded, launched or queried by this task. No Being process, workspace or service was accessed. The exact metadata, every referenced layer digest, environment and proposed app configuration are retained in [model-selection.json](model-selection.json).

Gemma 3 offers a modest instruction-tuned 4B candidate for text generation. Its current Ollama listing is approximately 3.4 GB. That registry listing currently identifies `68ceab7e468a`; **it differs from the cached manifest**. Preserve the local bytes; do not silently pull or update the tag. Runtime prose quality, latency and memory remain unmeasured. [Google model card](https://ai.google.dev/gemma/docs/core/model_card_3), [Ollama model listing](https://ollama.com/library/gemma3:4b).

## Observed local identities

- Command path: `/usr/local/bin/ollama`, resolving to `/Applications/Ollama.app/Contents/Resources/ollama`.
- Installed app metadata: `CFBundleShortVersionString` and `CFBundleVersion` both `0.40.3`. `/Applications/Ollama.app/Contents/Info.plist` is 1,377 bytes, SHA-256 `20b38700aaa5fff48b94832e05d812b658fd93fcdd1bf6b0be61dec57820d15a`. The executable was neither run nor hashed; runtime version confirmation is unexecuted.
- Selected manifest: `/Users/v/.ollama/models/manifests/registry.ollama.ai/library/gemma3/4b`, 856 bytes, SHA-256 `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a`.
- Its five referenced objects declare 3,338,801,804 bytes; with the manifest the private selected copy would be **3,338,802,660 bytes (3.110 GiB)**, below the proposed 3.5 GiB copy limit. Their existence and contents have **not** been checked. Before launch, validate every exact size and SHA-256 in the JSON, then verify the private copy. Abort on a missing or mismatching object; no fallback download.
- Conventional private/public key files exist as ordinary, nonsymlink files, respectively mode `0600`, 387 bytes and mode `0644`, 81 bytes; both owner UID 501. `/Users/v/.ollama/server.json` is absent. Only existence/type/permission metadata was inspected; no key or config contents were read or included.

## Conditional startup audit

The official **v0.40.3** direct `serve` path initializes keys only when the conventional private key is absent. With that existing file still present, the reviewed path does not regenerate the private/public keys. Configuration loading reads `server.json`; the reviewed loader does not create it. Recheck these preconditions immediately before launch and retain private before/after identity evidence. This source audit is not runtime proof that global files are unchanged. [Startup source](https://github.com/ollama/ollama/blob/v0.40.3/cmd/cmd.go), [environment/config source](https://github.com/ollama/ollama/blob/v0.40.3/envconfig/config.go).

`OLLAMA_NO_CLOUD=1` prevents the reviewed recommendation refresh/persistence path, although an existing conventional recommendation cache may be read. Disable request-body file logging explicitly. Startup model-directory maintenance can still occur with `OLLAMA_NOPRUNE=1`; therefore use private copies or independent filesystem clones of only the selected cache, **without shared-cache symlinks or hard links**. No claim of an OS filesystem or network sandbox is made. [Recommendation cache](https://github.com/ollama/ollama/blob/v0.40.3/server/model_recommendations.go), [request logging](https://github.com/ollama/ollama/blob/v0.40.3/server/inference_request_log.go), [server startup](https://github.com/ollama/ollama/blob/v0.40.3/server/routes.go).

## Owned launch recipe — not executed

Wait until the root task completes the frozen minimized reliability run and begins this rehearsal; never before `2026-10-13T18:39:18.845510Z`. Use a new run directory such as `desktop/ReservoirScope/target/qa/0.12.1-real-gemma3-4b`, with the manifest at `models/manifests/registry.ollama.ai/library/gemma3/4b` and its five verified objects at `models/blobs/sha256-…`.

Launch the exact executable directly with argv `['/Applications/Ollama.app/Contents/Resources/ollama', 'serve']`. Set the following **child-only** environment, after removing inherited Ollama/proxy overrides. Preserve `HOME` unchanged. Do not use the GUI launcher, `launchctl`, or `ollama run`, `pull`, `list` or `stop` against any existing service.

```text
OLLAMA_HOST=127.0.0.1:0
OLLAMA_MODELS=<absolute-owned-run-directory>/models
OLLAMA_NO_CLOUD=1
OLLAMA_NOPRUNE=1
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_MAX_QUEUE=1
OLLAMA_CONTEXT_LENGTH=4096
OLLAMA_KEEP_ALIVE=2m
OLLAMA_LOAD_TIMEOUT=60s
OLLAMA_DEBUG=0
OLLAMA_DEBUG_LOG_REQUESTS=false
OLLAMA_NOHISTORY=1
```

Port zero is accepted by the reviewed host parser. Read the actual nonzero loopback listener address from this owned process's log; only then set the app endpoint. Do not probe port 11434 or discover other services. Model paths, concurrency, context and keep-alive are explicit controls. [Configuration source](https://github.com/ollama/ollama/blob/v0.40.3/envconfig/config.go), [listener logging](https://github.com/ollama/ollama/blob/v0.40.3/server/routes.go), [official configuration FAQ](https://docs.ollama.com/faq).

Launch in a new process session/group, for example `Popen(start_new_session=True)`, and record PID, start identity, executable hash and PGID. The GGUF path starts an owned, bundled `llama-server` child on loopback with offline mode; the reviewed Darwin spawn attributes do not assign a different process group. Supervise the service for about **15 minutes maximum**. On cleanup, signal only the still-verified owned PID/group, wait and reap; any escalation remains confined to that group. Never use broad `pkill`/`killall` or stop a default service. [Runner creation](https://github.com/ollama/ollama/blob/v0.40.3/llm/llama_server.go), [Darwin attributes](https://github.com/ollama/ollama/blob/v0.40.3/llm/llm_darwin.go), [bundled helper lookup](https://github.com/ollama/ollama/blob/v0.40.3/llm/llama_binary.go).

## First app run and limits

Propose seed `20261013`, 1,000 ms pacing, journal cadence 30, maximum 121 steps, **four prepared attempts**, 600 seconds and 64 MiB retained app storage. With successful replies this permits journals at 30/60/90/120 and their following application boundaries through 121. Use the existing numerical defaults: leak 0.65, noise 0.02, retention 0.955 and regulation enabled. Keep response format unset for prose. A failed, incomplete or rejected response is an outcome to retain; do not substitute a provider, manufacture success or automatically retry.

Use the real app's existing request: `gemma3:4b`, `stream:false`, `num_ctx:4096`, `num_predict:256`, temperature zero, no explicit generation seed. The app retains its 5-second inventory and 60-second generation deadlines, 1 MiB response cap, and disabled redirects/proxies/automatic retries. Temperature zero is not a guarantee of bit-identical output across software or hardware. An already dispatched request may settle within its request deadline after the duration budget is reached; it does not authorize a new request or application past a reached budget. [Generate API](https://docs.ollama.com/api/generate), [generation options](https://docs.ollama.com/modelfile), [current app transport](../../src-tauri/src/model_transport.rs).

The parent describes a 64 GiB Apple-silicon host. One model, one parallel request and a 4,096-token context limit resource demand, but there is **no measured peak-RAM, quality, throughput or energy result yet**, and no process memory cap. A proposed 8 GiB free-disk cushion covers the 3.110 GiB private copy plus possible owned auxiliary files; it is not an enforced Ollama disk quota. Apple Metal support is documented, not a measurement of this rehearsal. [GPU support](https://docs.ollama.com/gpu).

Afterward, retain actual request/save/application outcomes and owned process/resource identities; verify conventional key/config identities unchanged and reap the owned process group. Keep this real-model evidence separate from the preceding synthetic reliability run.
