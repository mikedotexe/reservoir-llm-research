# Reservoir Scope · current release

**0.14.0, build 19 — test candidate. Human newcomer acceptance is pending.**
This page is authoritative for the current version, installation, verification and
acceptance status. Earlier accounts describe their own releases, not this build.

## Open the lab

The trusted-Mac delivery is `Reservoir-Scope-0.14.0-arm64.zip`, containing the
self-contained app, matching `essentials-run`, guide, participant worksheet and
verification account. Its delivery receipt sits beside the archive and records its
final hash. Requires Apple silicon and macOS 14 or later. Copy the
app to Applications and open it. It is locally ad-hoc signed; public distribution
and notarization are outside this release. No model download or service startup
is required for the guided examples.

Begin with [the guided journey](../native/ReservoirScope/docs/GUIDED-TOUR.md).
Use **Runs & examples → Reviewed research cases** for the two real evidence
walkthroughs. [The participant worksheet](../native/ReservoirScope/docs/NEWCOMER-WORKSHEET.md)
keeps human acceptance separate from software checks.

Experiments and journals save under `~/Library/Application Support/Reservoir Scope/`.
Replay and case viewing work offline. Live Beings feeds and fresh local generation
are explicit choices; opening the app does not contact the Mac Mini or a model.
The endpoint/model **Check local model** button makes one bounded loopback inventory
request. Availability is advisory and does not promise a successful generation.

## What changed

- A single resource manifest stages the app and matching runner from declared inputs;
  building no longer copies generated resources into the source tree.
- Two reviewed cases connect supplied evidence, authored writing, supported or
  unresolved interpretations, and subsequent outcomes. Case exports reopen in the
  same read-only viewer without adding experiment runs.
- Maintained daily analysis has explicit hashed inputs and separate build, verify
  and exclusive-create output steps. Frozen historical packets remain unchanged.
- Private archive commands verify complete snapshots and restore without following
  their original provenance paths.

## Evidence and limits

The [0.14 verification account](../analyses/2026-09-17-reservoir-scope-014.md)
records checks actually run and any incomplete coverage. The packaged identity
binds exact compiled inputs, resources, toolchain and source commit; the external
receipt records final executable, archive and signature hashes. The local release
tag is `reservoir-scope-v0.14.0`. No remote publication is included.

The [short-output qualification](../analyses/2026-09-17-short-output-qualification.md)
stopped after its first paired input: the candidate completed but exceeded the
24-word bound and copied multiple measurements. Both responses are retained;
there is no prompt-v3 registration or new recording. Existing partial model runs
remain available. Different prose is not a writing-quality or improvement score.

Core, replay, storage and package verification are recorded separately. Presentation
coverage includes a prior exact-binary inspector pass, but the latest accessibility
attempt and full presented-app offline traversal are incomplete. The raw failed
aggregate is retained; this is not an all-checks-passed acceptance claim.
**No human newcomer acceptance result has been obtained.** Agent checks and rendered
screens are not a substitute. The live flywheel and durable-correction follow-ups
have separately frozen windows and can finish after the app candidate. See
[Now](NOW.md); missing or unavailable observations will remain explicit.

## Build and research tools

See [native build instructions](../native/ReservoirScope/README.md) and
[research tools](TOOLS.md). The maintained commands include:

```sh
reservoir-research study daily build INPUTS.json --data-root RETAINED_ROOT --out NEW_DIRECTORY
reservoir-research study daily verify INPUTS.json --data-root RETAINED_ROOT --report REPORT.json
reservoir-research archive snapshot SOURCE --out NEW_SNAPSHOT
reservoir-research archive verify SNAPSHOT
reservoir-research archive restore SNAPSHOT --out NEW_DIRECTORY
reservoir-research verify --group all-offline --app APP --daily-manifest INPUTS.json --daily-report REPORT.json --data-root RETAINED_ROOT --out NEW_DIRECTORY
```

Capture, evidence annotation and ledger advancement remain explicit operations.
Default verification makes no model requests. Unknown release identities or
contradictory evidence cannot receive a successful final verification.

Historical documentation: [project status](NOW-history-through-20260917.md),
[native release history](../native/ReservoirScope/README-history-through-0.13.1.md),
[earlier handoff](../native/ReservoirScope/HANDOFF-history-through-0.13.1.md).
