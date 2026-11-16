# Research API and scheduled interventions

Development integration on `codex/research-integration`, combining the preserved
API checkpoint `b558a07` and journal UI/theme checkpoint `2a04436`. The app profile uses
its own data directory. The three existing model experiments remain unchanged.

Reservoir Scope now exposes the same research service to the native **Research
runs** workspace and an authenticated local JSON API. A single app owns independent
runs, a shared provider queue, experiment recipes, and durable operation records.
Deep links open a run, journal entry, experiment, or settings view; JSON requests
perform reads and mutations and return machine-readable results.

## Run the isolated development app

From `desktop/ReservoirScope`, with the prepared resource assets available:

```sh
PYTHON=/opt/homebrew/bin/python3.14 npm run tauri build -- --debug --config src-tauri/tauri.research-api.conf.json --bundles app
open 'target/debug/bundle/macos/Reservoir Research Integration.app'
```

Its application identifier is `research.reservoir.scope.integration`; its navigation
scheme is `reservoirscope-dev`. The normal app profile uses `reservoirscope`.
Neither profile controls another application's running instances.

The local macOS development package includes `reservoirctl.pyz`, the complete
standard-library CLI. Run it with Python 3.12 or later: `python3 reservoirctl.pyz
--help`. Replace `reservoirctl` in the examples below with `python3 reservoirctl.pyz`.
No repository installation is needed. The package is signed ad hoc, not notarized;
see [0.54 qualification and remaining limits](RELEASE-0.54.0.md).

For a headless local instance, supply an explicit **new, absolute** data directory:

```sh
desktop/ReservoirScope/target/debug/reservoir-scope-desktop --research-api --data-root /absolute/path/to/research-api-data
```

The process prints its URL, instance ID, and discovery file path, never its token.
An ownership lock rejects another process using the same research directory.
SIGINT/SIGTERM retain in-flight outcomes and settle storage before exit. A failed
save keeps shutdown held; inspect it and use `retry-save` after resolving the
storage failure. That recovery action remains available during headless shutdown.

## CLI

Install the repository package with Python 3.12 or later (`pip install -e .`), or
run `python -m reservoir_control` from the repository. `reservoirctl` has no external
Python dependencies. It never opens run-store files or contacts a model directly.

```sh
reservoirctl discover
reservoirctl --instance research.reservoir.scope.integration capabilities
reservoirctl --instance research.reservoir.scope.integration schema
reservoirctl --instance research.reservoir.scope.integration openapi
```

When several instances exist, select one with `--instance` or `--endpoint-file`.
For scripts, set `RESERVOIR_SCOPE_ENDPOINT_FILE` to that instance's `endpoint.json`.
The owner-only descriptor is in the app data directory under
`automation-v1/endpoint.json` (mode 0600 inside a mode 0700 directory on Unix).
It contains the ephemeral loopback URL and bearer token. Credentials rotate on
restart. The client rejects shared/symlink discovery files, non-loopback targets,
proxies, and redirects. The server rejects browser `Origin` headers and a `Host`
other than its literal bound address.

Global flags precede the command. Mutations return an operation immediately;
`--wait` waits for its durable outcome, with a bounded client timeout.

```sh
reservoirctl --wait runs create config.json
reservoirctl runs list
reservoirctl --wait runs start RUN_ID
reservoirctl entries list RUN_ID --limit 10
reservoirctl entries list RUN_ID --all
reservoirctl entries get RUN_ID ENTRY_ID
reservoirctl settings get RUN_ID
reservoirctl --wait settings set RUN_ID patch.json --expected-revision 0
reservoirctl --wait runs pause RUN_ID
reservoirctl --wait runs resume RUN_ID
reservoirctl --wait runs stop RUN_ID
reservoirctl --wait runs clone RUN_ID --overrides overrides.json
reservoirctl --wait runs extend-limits RUN_ID --json limits.json
reservoirctl export RUN_ID --output /absolute/path/to/new-export
```

Exports freeze and verify one committed prefix while a run may continue. Downloads
verify each file's length and SHA-256 against that frozen export index. A failed
download leaves an `INCOMPLETE.txt` marker. A clone creates a new linked run from
the source's effective configuration and overrides; it does not copy a stochastic trajectory.
The `extend-limits` body contains all three `maximumSteps`, `maximumTurns`, and
`maximumDurationSeconds` values and can recover a retained turn that hit its budget.

## Validate before execution

`POST /v1/validate` is authenticated, read-only preflight. It returns HTTP 200 with
`valid`, structured `issues`, and the remaining execution checks. It needs no
idempotency key and creates no operation, run, checkpoint, or model request.
The same check is available beside settings, recipes, and action text in Research runs.

```sh
reservoirctl validate configuration config.json
reservoirctl validate configuration patch.json --run RUN_ID
reservoirctl validate recipe recipe.json
reservoirctl validate action reply.txt --run RUN_ID
```

The CLI returns nonzero for `valid:false`. Configuration input merges into creation
defaults, or the named run's effective settings. Recipe validation expands every
arm. Action validation uses the actual ordinary-turn parser and saved configuration;
it preserves the supplied reply text. It reports independent inquiry, input, and
experiment shape issues together. It does not resolve retained result IDs, test
numerical application bounds, or check provider availability. Scheduled conversations
are passive and do not execute these ordinary-turn action footers.

Example JSON envelope: `{"kind":"action","runId":"RUN_ID","text":"…"}`.
Other kinds use `config` or `recipe` instead of `text`. Capabilities includes a
complete executable `experimentCommandExample` using an explicit 48-value direction.

## Growth-compatible copied experiments

New experiment opt-ins select **experiments-v4**, producing **parameterized-v2**
reports for 32–128 recurrent nodes. The prompt includes a complete JSON command,
explicit required fields, and the distinction between `feedbackScale` (a run
control) and `heldInputScale` (a multiplier on inherited held input). They are not
aliases. `observe` belongs beside `probe`; `probe.amplitudes` is required; an
`INQUIRY: OPEN` question is one JSON string without surrounding braces.

Existing **experiments-v3** runs retain their original 32-node parser and prompt.
To grow one, explicitly include `"sonar":{"version":"experiments-v4"}` in the
same configuration patch as `"reservoirNodes":48`. Other sonar properties are
preserved by the patch. The native growth template includes this transition when
needed. Old experiment and scan caches reset at growth; old receipts and journal
objects remain historical evidence. A reference to an unavailable old result is
rejected, never replaced by a newer result.

The multi-run reader now uses the shared journal projection: original action
choice, receipt, prompt, measurements, and producing configuration. The entry list
and reader scroll independently; polling does not change the selected entry.
Matching measurements load by run, generation, result ID, and origin step. Missing
cached measurements remain explicit. The API continues to return the complete
verified journal object in `evidence`.

## Future interventions

Interventions can be scheduled by numerical step or accumulated active running
time. Queuing and provider time count as active time; paused and app-closed time
do not. The target is a lower bound: an already admitted turn finishes with its
original settings, including feedback application, before the intervention takes
effect. The result records both the requested boundary and the actual applied step.
For example, a turn admitted at step 3600 may settle at step 3601.

To grow a reservoir at step 3600, save this as `growth.json`:

```json
{"at":{"step":3600},"kind":"configuration","patch":{"reservoirNodes":48}}
```

To ask a custom question after an hour of active running time, save `question.json`:

```json
{"at":{"activeSeconds":3600},"kind":"prompt","prompt":"What have you noticed since our last conversation?","includeTelemetry":true}
```

```sh
reservoirctl interventions schedule RUN_ID growth.json
reservoirctl interventions schedule RUN_ID question.json
reservoirctl interventions list RUN_ID
reservoirctl wait OPERATION_ID --timeout 7200
reservoirctl --wait interventions cancel OPERATION_ID
```

A prompt is a one-time, passive conversation with a durable operator operation ID.
It uses the existing journal/save/readback/application path. `includeTelemetry:false`
sends exactly the supplied prompt without an app-supplied system message or earlier
journal context. `true` uses the configured telemetry/memory conversation renderer.
The ordinary periodic conversation schedule remains intact. Prompt admission is
reported separately from eventual provider completion; follow the run's entry and
retained attempt to see that outcome. A schedule-complete or stopped run requires
an explicit configuration/recovery decision or a new linked run.

Up to 32 distinct future boundaries may be armed per run, with at most 64 outstanding
operations per app. Cancellation is accepted only before a configuration or prompt
has been durably applied. Stop supersedes a pending settings change. Failed provider,
encoding, or save work remains visible and prevents a conflicting phase change.

Pause also supersedes an in-progress settings transition and suppresses automatic
resume from a scheduled intervention. A resize already committed remains recorded,
but cannot restart a paused run. A scheduled prompt that reaches its boundary and
then loses admission to Pause becomes `needsAttention`; resume and explicitly
resubmit it when intended. A future boundary not yet reached stays scheduled.

## Configuration phases and resizing

`GET /v1/runs/{runId}/settings` returns **original**, **configured**, and **effective**
settings, the configuration revision, and recorded phase history. Effective values
include currently authored numerical controls, retained budget extensions, and
conversation edits. A patch changes only named fields; untargeted controls are
re-read at the settled boundary so a draining turn's actions
are preserved. Every phase is bound to its predecessor checkpoint and operator ID.

Immediate patches require `expectedConfigurationRevision`. Scheduled patches may
include it; otherwise they apply to the effective configuration at their future
boundary. Each transition validates the complete resulting configuration, so coupled
features such as prompt version, action mode, diagnostics, and scanner capability
must be changed together. Optional features are removed with JSON `null`.

Seed is creation-only. Reservoir node count supports **32–128 nodes** and in-place
**growth**, following the user-selected prefix-preserving rule:

- Keep every existing recurrent coordinate and connection exactly; new nodes start
  at zero. Generate new connections from indexed independent seed streams. Growing
  again preserves all previously generated connections. Existing weights are never
  rescaled. The expanded mechanism does not inherit the old row-norm bound.
- Keep the sensory field at 32 dimensions and text input at 48 slots. Preserve
  sensory covariance, numerical history, counters, and the reservoir RNG position.
  Future numerical steps consume one noise draw per current reservoir node.
- Record the new model hash and reset incompatible scans, inquiry baselines, or
  selection vectors. Growth with non-latest memory starts a new compatible selection
  ledger. Old journals, controls, receipts, and configurations remain in prior events.
- Shrinking or reseeding requires a fresh linked run. These operations would remove
  state rather than extend it and have no implicit migration rule.

Other supported changes include model/endpoint/sampling, writing and encoding
limits, codec/model, numerical controls, memory policy, action/prompt contracts,
scanner/probe capability, peer membership, pace, schedules, and resource limits.
The schema marks each field's policy; host/core validation enforces cross-field and
consumed-resource constraints. Limits cannot drop below consumed resources plus
persistence reserve. A completed configuration change can include `resumeError` if
its new limits prevent further execution; the durable change still remains applied.

Changing writing cadence establishes a new cadence origin. Unrelated edits preserve
that cadence. Changing only a conversation's prompt/telemetry preserves its due
slots and completed receipts; changing its interval/end establishes a new schedule
origin. Elapsed values in core schedule events are relative to that schedule origin;
the manifest and phase record retain accumulated active elapsed time.

Compatible numerical state is preserved. Phase records list each invalidated cache.
A running run automatically continues after a successful boundary change; a paused
run stays paused. No uncertain provider request is automatically retried.

## Recipes and experiments

Recipes are versioned JSON documents with `baseConfig`, named `arms` containing
`overrides`, and optional common/per-arm `interventions`. Preparing resolves every
configuration into fresh runs and arms all interventions before Start is permitted.
Partial preparation is retained as `preparing` and cannot be group-started. Group
lifecycle operations report individual results and a `partial` flag.

```sh
reservoirctl --wait recipes save research/recipes/three-model-sonar-v1.json
reservoirctl --wait experiments prepare research/recipes/three-model-sonar-v1.json
reservoirctl experiments list
reservoirctl --wait experiments start EXPERIMENT_ID
reservoirctl --wait experiments pause EXPERIMENT_ID
```

The three-model example records the configuration pattern of the existing Gemma,
GLM, and Mistral experiments. It is a recipe for **new** runs, with a fresh reciprocal
peer group, and does not attach to those currently running processes. Preparation
makes no model calls. Check availability explicitly with `POST /v1/models/check`
before starting a model-backed experiment.

Optional `peerReading:true` resolves reciprocal membership for 2–4 uniquely named
arms. Optional `maxConcurrentRequests` sets the shared application queue on group
Start/Resume; it affects all runs at that endpoint. The default is one request at a
time per normalized local endpoint, shared by writing and embedding. Each run owns
its numerical clock and FIFO queue position; no UI subscriber drives execution.
Queue time is exposed live, and per-attempt writing/embedding queue waits are saved
alongside transport timing. Transport deadlines begin on dispatch, after queueing.

## HTTP contract

`GET /v1/openapi.json` is the discoverable OpenAPI 3.1 contract;
`GET /v1/schema` is the configuration JSON Schema. `GET /v1/capabilities` includes
defaults, version, limits, restart policy, and supported action names.

All requests require `Authorization: Bearer …`. Every mutation requires a nonempty
`Idempotency-Key` (up to 128 bytes). Reusing a key with identical method/path/body
returns the original operation; changing its payload returns 409. Keys survive
restart. Accepted mutations return 202 with an operation ID. A 202 is acceptance,
not success. Poll its status: `queued`, `running`, `scheduled`, `completed`, `failed`,
`cancelled`, or `needsAttention`. Errors have a code and message.

| Routes | Purpose |
| --- | --- |
| `POST /v1/validate` | Read-only configuration, recipe, or action preflight |
| `GET/POST /v1/runs` | List or prepare runs |
| `GET /v1/runs/{runId}` | Run state, generation, configuration revision, saved prefix |
| `POST /v1/runs/{runId}/clone` | Fresh linked run with optional overrides |
| `GET/PATCH /v1/runs/{runId}/settings` | Configuration layers/history; boundary patch |
| `GET/POST /v1/runs/{runId}/interventions` | Scheduled changes and custom prompts |
| `POST /v1/runs/{runId}/actions/{action}` | Start, pause, resume, stop, retry-save, retry-writing, retry-encoding, skip-feedback, extend-limits |
| `GET /v1/runs/{runId}/entries` | Stable newest-first pages (`limit`, `cursor`) |
| `GET /v1/runs/{runId}/entries/{entryId}` | Exact journal, prompt, reply and saved evidence |
| `GET /v1/runs/{runId}/events` | Committed event prefix (`after`, `limit`) |
| `GET /v1/runs/{runId}/sonar` | Passive saved scanner/state observation |
| `POST /v1/runs/{runId}/exports` | Verified immutable prefix export |
| `GET /v1/exports/{exportId}/files` | Frozen file inventory and hashes |
| `GET /v1/exports/{exportId}/content?path=…` | One enumerated export file |
| `GET /v1/operations[/{operationId}]` | Operation catalog/detail |
| `POST /v1/operations/{operationId}/cancel` | Cancel an unapplied settings change/intervention |
| `GET/POST /v1/recipes`, `GET /v1/recipes/{recipeId}` | Recipe catalog/save/detail |
| `GET/POST /v1/experiments`, `GET /v1/experiments/{experimentId}` | Catalog/prepare/detail |
| `POST /v1/experiments/{experimentId}/actions/{action}` | Group lifecycle control |
| `GET/PATCH /v1/settings` | Shared provider concurrency (1–16) |
| `POST /v1/models/check` | Explicit local model inventory check |
| `GET /v1/events` | SSE full replacement run/operation snapshots |

Journal pages freeze an entry catalog and checkpoint hash. Appends do not move
entries between pages. Cursors expire after restart or eviction from the bounded
128-snapshot cache; 410 instructs the client to restart pagination. Direct entry
reads use stable opaque IDs and verify committed objects. Event pagination uses
monotonic event IDs. SSE reconnect sends a new `resync:true` snapshot; it is a state
feed, not a claim that every intermediate notification was delivered.

Reads never restore or start a retained run. The first explicit lifecycle mutation
may verify and load it into a fresh generation, paused. Restart reconciles published
configuration changes by operation ID and marks other unfinished operations
`needsAttention`; it never redispatches them. Schedules must be inspected and
explicitly resubmitted after restart. Standard saved runs remain supported; the new
optional phase/intervention records need a reader that understands this extension.
Historical journals are rendered and verified using their producing configuration.
Journal detail has the same response shape for loaded and retained runs, including
its producing configuration revision and the exact verified journal evidence.

Navigation-only links:

```text
reservoirscope-dev://v1/runs/RUN_ID
reservoirscope-dev://v1/runs/RUN_ID/entries/ENTRY_ID
reservoirscope-dev://v1/experiments/EXPERIMENT_ID
reservoirscope-dev://v1/settings
```

Queries, fragments, credentials, mutation paths, and unsafe path components are
rejected. A deep link grants no mutation authority and carries no secret.

## Reproduce qualification

All automated research-API qualification uses fresh temporary roots and scripted
or fake loopback providers. It does not discover or contact real model services.

```sh
cd desktop/ReservoirScope
cargo test --workspace
npm test
npm run build
cd ../..
/opt/homebrew/bin/python3.14 -m unittest tests.test_reservoir_control
/opt/homebrew/bin/python3.14 probes/qualify_research_api.py desktop/ReservoirScope/target/debug/reservoir-scope-desktop --report research/outputs/agent-api-qualification/result.json
```

The black-box probe tests three simultaneous runs, FIFO concurrency, stable journal
pagination, scheduled 32→48 growth and a custom prompt, a codec transition, stopping
while a change waits for a provider, verified downloads, and restart with no
unrequested dispatch. Core/host tests additionally cover frozen historical replay,
phase identity, unchanged cadence, schedule revisions, storage publication faults,
authentication, schema references, and cancellation.

The completed checks were 381 core tests; the full host suite (337 passed, three
existing ignored tests) plus the final nine API tests and storage-publication fault
test; 612 frontend tests (one existing skipped test); four Python CLI tests; and
the isolated black-box workflow. The latter observed a maximum of one concurrent
provider call, three verified exports, and zero provider calls on restart.

Native preparation, lifecycle controls, and journal inspection were checked in the
isolated development app with a bounded scripted run. Custom-scheme handoff was
blocked by the verification browser's policy, so warm/cold OS link launching remains
unverified. Navigation parsing and frontend section selection have automated coverage.


The combined 0.54 candidate adds growth-compatible experiments and read-only preflight.
See [the integration qualification record](RELEASE-0.54.0.md) for final checks and limits.
