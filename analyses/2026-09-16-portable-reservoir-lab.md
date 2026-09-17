# September 16 · Portable Reservoir Scope lab

Reservoir Scope 0.12.0 build 16 implements Mike’s accepted portable research plan. The app starts in Essentials → Actions & comparisons → A, stores experiments under the current user’s Application Support directory, and includes both scripted examples and recorded local-model journals. Source identity is sealed in the package; the final package and validation receipts identify the delivered executable separately from the base Git commit.

The synthetic study is [S-009](../research/studies/S-009-portable-reservoir-journals.md). The existing S-007 daily ledger, cutoff, sampling rules and automation were not changed. No live Being process, model endpoint or data file was modified.

## Implemented behavior

- One local store for Explore, original stages, action comparisons, journals and verified imports. Failed record saves remain in memory with retry/export; quit waits for persistence or requires an explicit discard.
- Runs & examples, normal file-dialog import/export, cursor-aligned readable journals, previous/next component selection and Next journal. Recorded playback does not contact a model or follow historical paths.
- Nine verified scripted 120-step examples: A–H and the separate observation comparison. Interactive defaults remain 300 steps. A–C explicitly have no journal component.
- Six verified 120-step model recordings: D–H and the observation comparison. All 21 writing opportunities completed and saved journals. Four qualification attempts are also bundled, including the three failures.
- A separate stage-D comparison with identical input, state and sensory measurements. Only the designated prompt adds the 32 indexed, eight-decimal reservoir coordinates and recorded step. Both arms disable feedback, memory, action choice and regulation. Request order alternates; one-arm failures preserve the partner outcome.
- New `essentials-actions-v2` comparison-kind, observation-channel, request-order and prompt-version evidence. V1 keeps its original sensory-only prompt-verification path.
- Explicit local endpoint/model settings, bounded context and JSON output for new action generations, no service startup, pull, provider switch or scripted substitution on failure.

See the [portable lab guide](../native/ReservoirScope/docs/PORTABLE-LAB.md) for operation and the [headless recipe](../essentials/actions/recipes/D-observation-comparison.json).

## Model preparation and interpretation

The frozen preparation protocol precedes generation in
`research/outputs/2026-09-16-portable-lab/protocol.json`. The user’s installed
`phi3:mini` is 3.8B Q4_0, digest
`4f222292793889a9a40a020799cfd28d53f3e01af25d48e06c5e708610fc47e9`.
An isolated, explicitly owned Ollama 0.32.15 server ran on the viewer Mac at
127.0.0.1:63593. It was stopped after this finite preparation. No model was downloaded.

Four qualification attempts, each with one opportunity, are retained:

1. Provider-selected context expanded to 131,072 tokens; the bounded client request timed out during preparation. No journal was admitted.
2. Explicit 4,096-token context returned Markdown-fenced JSON. Strict response validation rejected it, preserving the raw output.
3. Explicit JSON output exhausted the 256-token output limit before completion. No feedback was admitted.
4. Prompt version 2 requested a short numerical journal. The response completed in 110 tokens and was saved.

The subsequent frozen batch used independent generation, 4,096-token context, JSON output, temperature 0, a 256-token output ceiling and prompt version 2. Each run used seed 20260909, 120 steps and opportunities at 30, 60 and 90. One run per recipe completed with no retries. The observation arm request ordinals were left [1,2,1], right [2,1,2].

Evidence:
`essentials/examples/portable/model-recordings.json` includes the model inventory,
runner identity, settings, record hashes and outcomes. The example JSON files retain
every prompt, raw response, journal, observation and application boundary. Complete
preparation recipes and logs are retained under the dated output directory.

A deliberately limited, post-hoc inspection of the first added-observation journal
shows why access and accuracy must remain separate. At step 30 it reports a maximum
sensory eigenvalue of 0.79487568, while its supplied prompt includes 5.57608588.
Its x[0] value, -0.00000085, does match the supplied rounded coordinate
(the full recorded value is approximately -8.52406115e-7). This is one selected
illustration, not an accuracy rate or treatment-effect estimate. No general fidelity
gain is established by these six demonstrations.

Reproduce the example from `example-model-observation.json` by reading
`right.actions[0]`, `right.journals[0]` and `right.frames[29]`. The relevant
measurement is `max(frame.spectral.eigenvalues[:8])`, with n=1 selected journal.
The next research step is a separately frozen claim-coding rubric and replicated
paired runs; different prose alone is not an improvement measure.

## Qualification

The current receipts are under `native/ReservoirScope/validation/0.12.0/`.
The final delivery account records exact app/runner hashes, signature verification,
source/resource identity and the copied-app offline results.

- Shared core: 56 tests pass, retaining recurrence, sensory separation, feedback timing, memory, waiting, regulation, cancellation, late-response and save-failure checks.
- Native lifecycle: 47 action checks, 28 exploration checks and 17 original-stage checks pass. These include next-journal stopping, future-journal and future-application exclusion, controlled observation access, save retry and termination persistence.
- Native paired layout: 25 checks pass at 1380×940 and 1100×820. A one-pixel backing-coordinate rounding difference is allowed between paired view widths; scales and camera remain shared.
- Actual HTTP transport: five owned-fixture cases pass, including partial output, length termination, HTTP failure and redirect rejection. Exact submitted messages, JSON mode, context and output limits are checked.
- Copied-app qualification denies networking and access to /Volumes, the original /Users/v/other checkout and the local editing mirror. All 19 bundled records verify; all eight action stages run for 120 steps, export and verify after original run/journal folders are moved away. Production native view models run all eight components, save journals, reopen them in new view-model instances and discover all experiment formats in the local browser.
- Presented-app review confirms initial stage A, the examples browser, saved local journals, paired recorded journals at step 30, normal dialog export, clean quit and reopening. Screenshots contain only the research app window.
- Cross-user replay is recorded separately on the build Mac under user v and the viewer Mac under mikepurvis. This checks transfer and path independence; it is not a claim that every macOS version has been tested.

The app is ad-hoc signed for trusted research Macs, targets macOS 14+ on Apple
silicon and bundles a standalone headless runner. Public distribution/notarization
are outside this release. The build used the research checkout on the Mac Mini
because the viewer Mac’s command-line compiler is license-blocked; the copied
product’s runtime tests deny access to that build checkout and networking.

Verification establishes internal numerical/prompt/receipt consistency. It does
not independently authenticate a historical provider event or establish a writing
quality effect. Scripted fixtures demonstrate mechanisms only.

## Delivered artifacts

Installed viewer: `/Users/mikepurvis/Applications/Reservoir Scope.app`.
Portable archive: `/Users/mikepurvis/Downloads/Reservoir-Scope-0.12.0-arm64.zip`
(76,495,068 bytes; SHA-256
`cd7d68391ecc1ad977faf4b7f98116c18d88dbad2a915dfdf1e81cc9e21ede3e`).
The archive contains the app, standalone runner, observation recipe, user guide,
study protocol, model recordings and qualification evidence.

The final archive was extracted into a fresh local directory. All 65 manifest-listed
files matched; the app and standalone runner signatures passed, all 33 packaged
resources and 19 examples matched the package identity, and the recorded observation
comparison verified with network and original source paths denied. The exact receipt
is [archive-verification.json](../research/outputs/2026-09-16-portable-lab/archive-verification.json).
Final copied-app/store qualification is [disconnected.json](../native/ReservoirScope/validation/0.12.0/disconnected.json);
[delivery.json](../native/ReservoirScope/validation/0.12.0/delivery.json) records executable
hashes and the final check counts. Source changes remain in the research checkout;
packaged source hashes identify the release beyond its base Git commit.

## Board updates pending

The Artifact board connector and an authenticated board browser were unavailable.
Retain this pending payload for the Hold Shelf:

- `c-portable-reservoir-lab`: change, done, being system. Implement the local portable app, A–H workflow, storage recovery and verifiable observation comparison. Evidence: this account, S-009, portable guide and release receipts.
- `t-portable-reservoir-lab-disconnected`: test, verified, being system. Copied app/CLI, network and original-path denial, local save/reopen/export, v1 compatibility and package identity. Evidence: 0.12.0 validation receipts.
- `q-journal-observation-access`: question, open, being system. Does adding indexed reservoir state change the factual claims a journal can support? Demonstrations are available; freeze a claim rubric and replicated study before estimating an effect.
- Log `2026-09-16-portable-reservoir-lab`: delivered the separate synthetic research app and preserved all model-preparation attempts. S-007 and live systems remain untouched.
