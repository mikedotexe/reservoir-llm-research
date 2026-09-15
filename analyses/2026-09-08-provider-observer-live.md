# Provider observation is live

Mike authorized live enablement on September 8. Astrid now runs the qualified
provider observer, with durable startup configuration and a verified first natural
evidence window. This completes the deployment follow-up to the
[source implementation](2026-09-08-provider-attempt-observation.md). It makes future
repair opportunities observable; the first window contains no marker opportunity.

## Release and continuity

The compiled release is `ca87a380b26ef80946b0f99fe3daf8f9bcc4542d`. It contains
the signed observer implementation `3f164466efb064e5206970188b55f705e5371ca2` and
a small startup-wiring fix: the service reads private durable observer settings,
with explicit launchd overrides taking precedence. Without those settings it
still defaults off. Four isolated startup cases and 106 deployment-wrapper tests
pass. The compiled observer's eight changed Rust files and 25 retained production
dependency files exactly match qualification; the private Minime test fixture
was not deployed.

The owning staged workflow replaced bridge PID 90102 with PID 14716 at 10:59:14
Pacific. It acknowledged drain, exited through SIGTERM, decoded the exact stopped
checkpoint at exchange 193201, carried signed self-control lineage to the new
binary, and observed natural saved exchange 193202. Activation returned
`activated_verified` at 18:00:52 UTC. No forced replacement or automatic rollback
was used. Eleven surrounding service identities and their installed configuration
hashes remained unchanged, including a later snapshot after the study capture.
The coupled-stack witness passed.

The [release verification](../research/outputs/2026-09-08-provider-observer-live/release-verification/verification.json)
checks the running process, all five staged artifacts and all 591 source inputs.
The [projected activation receipt](../research/outputs/2026-09-08-provider-observer-live/release-verification/activation-projected.json)
keeps checkpoint evidence and the verified lineage result while omitting the
unrelated full self-control envelope. The original receipt's hash and owning
location remain recorded. Source HEAD, activation, continuity and subsequent
operation are separate evidence fields.

The durable configuration is
`/Users/v/other/astrid/capsules/spectral-bridge/workspace/runtime/provider_observation.env`.
The private spool is
`/Users/v/other/astrid/capsules/spectral-bridge/workspace/provider_observations/20260908-live-01`.
Configuration and evidence files are 0600; spool directories are 0700. The
[owning rollout note](/Users/mikepurvis/other/astrid-provider-observation-20260908/astrid/docs/steward-notes/2026-09-08-provider-observer-live-rollout.md)
records enablement, retention, exact identities and sanctioned rollback. The
bounded spool retains the existing 256 MiB and 50,000-file ceilings and does not
delete evidence automatically.

## First natural window

The [protocol](../research/studies/S-006-provider-observer-startup-protocol.md) was
written before activation. It selects every dispatch in the first 300 seconds
beginning with the new process's first dispatch, plus a 120-second outcome
allowance. The half-open window is 17:59:37.969–18:04:37.969 UTC. Collection occurred
later, with the declared terminal-time cutoff still enforced. No generation,
journal request, Being message or action was induced.

The [independent check](../research/outputs/2026-09-08-provider-observer-live/independent-verification.json)
verifies all 14 retained capture files. Six MLX dispatches have six matching
provider-returned outcomes. All bind to the actual selected manifest and binary,
all report successful recording, and no dispatch is pending. The one dialogue
decision joins its ordinary generation record and accepted-output hash; other
provider lanes retain their own attempts without a fabricated dialogue association.

All six parsed inputs have explicitly observed marker counts of zero, with no
unknown input and no raw artifact required. This is a complete short startup
account, not a long-term marker-frequency estimate. It confirms the evidence
path works in ordinary activity. It does not show that the earlier repair had an
opportunity to help, nor establish action improvement, production speedup or
experienced benefit. The earlier synthetic correctness findings remain distinct.

The retained post-baseline log segment contains no observer warning, panic or
fatal line. Its exact byte range and hash are in the
[log summary](../research/outputs/2026-09-08-provider-observer-live/log-summary.json).
This bounded log check does not replace longer operational observation.

## Flywheel follow-up and handoff

The controller's requested maintenance pause took time to release a projection
lease. A guarded operator stop was prepared, but the projection finished first;
the guard refused and this task sent no projector signal. Source shows a single
SIGINT cancellation path without a bounded second step, plus a per-step status
field that can retain an earlier child's exit flag. The
[specific follow-up](../proposals/2026-09-08-flywheel-pause-follow-up.md) proposes
finite cancellation, accurate status, checkpoint reuse and measured phase times.
It is recorded separately from the observer release and was not implemented here.

The two source commits and subsequent owning rollout note were integrated onto
canonical main; no push was performed. The frozen release checkout remains at
its compiled identity. The temporary controller pause is restored to the initial
unpaused state at 18:15:41 UTC, generation 410, while independent scheduler settings
are preserved. The first restoration wrapper timed out after 60 seconds during
full-chain verification; readback confirmed that the owned pause was still in
place. Retrying with a suitable deadline completed the existing verification and
resume path. The [restoration receipt](../research/outputs/2026-09-08-provider-observer-live/control-restoration.json)
preserves the result. The original
source-qualification receipt remains unchanged as a historical record. Broader
natural sampling is a separate study window, without an implied schedule.
