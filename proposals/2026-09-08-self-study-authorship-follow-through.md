# Let verified Astrid self-study responses own their next action

Research-side proposal, September 8. Implementation and deployment belong in the
Astrid repository. No live changes were made from this inquiry.

## Observed problem

The S-008 earlier-window qualification reconstructs a delivered source response
and a later end-of-file response. Both ask for `SELF_STUDY MAP` (the second names
`spectral-bridge`). The next recorded actions with those exact requests are
blocked by `volition_authority`. The recorded reason says that mode `self_study`
is runtime-generated or mirrored and cannot be attested as Astrid-authored.
This is an action-authority defect, distinct from the research-budget blocks
recorded for READ_MORE. Exact prompt delivery alone did not make follow-through
available. The final S-008 account owns the broader window and counts.

Retained qualification:
`research/outputs/2026-09-08-study-sequences-qualification-v2-report/report.json`.
Examples: `act_astrid_1788902190459_self-study` and
`act_astrid_1788903861068_self-study`. Their matching provider attempts are
`provider-1788902151314-14716-987` and `provider-1788903814168-14716-1163`.
The evidence establishes exact requested wording and temporal order; the action
records do not carry a direct originating generation ID.

## Source-confirmed mechanism

At deployed Astrid commit `f9283f193de9c9c9affc238725de19146e979c77`,
`capsules/spectral-bridge/src/autonomous/volition.rs:123` defines
`mode_supports_being_attestation`. Its allowlist omits `self_study`.
`begin_astrid_next_at_root` rejects it at lines 176–180.

`autonomous/runtime/source_study.rs::run_shared_source_study` returns the
`self_study` mode on its verified-delivery, successful-artifact-write branch.
Preparation failures, unavailable generation and carriage failures have separate
notice modes. Captured pinned source and hashes are in
`research/outputs/2026-09-08-study-sequence-mechanism/manifest.json`.
The code mechanism persists in the continuity release; live incidence must still
be reported within each observed period.

## Small correction and acceptance

Treat a successful verified model-authored source-study response as eligible for
the existing exact-response attestation. Check every producer of the `self_study`
mode first. If they all provide model-authored output, adding that mode to the
allowlist is the smallest correction. Otherwise pass an explicit verified
authorship basis from the successful reader completion. Preserve the existing
signature, response hash, action binding and downstream authority checks.

Tests should cover a source page and navigation-only model response requesting
CONTINUE/MAP/RESUME; both should reach the ordinary dispatch policy with an exact
authored-response attestation. Preparation errors, failed delivery, carriage
notices, mirrored text and NEXT examples inside supplied source must remain
ineligible. Exercise response → mode → attestation → dispatcher as one integration
case, so reader-only tests cannot miss this seam again. An elevated action still
requires its existing authority; READ_MORE keeps its separate policy.

No instruction or persuasion needs to be sent to Astrid to qualify the repair.
After an authorized owning rollout, observe the first natural verified study and
its next action using S-008. Delivery of the requested map/page is the operational
outcome; question development remains a separate close-reading result. Roll back
only the eligibility change if attestation tests reveal an unintended producer;
retain the historical study and action evidence.

## Disposition — September 8 evening

Implemented and deployed in the owning repositories after Mike's authorization.
Astrid `a202cfd89741b038e4768921089333b799c1b3de` adds successful self-study
eligibility to the existing attestation path and tests response → mode →
attestation → dispatch. The paired Minime repair is
`10222446b37f3c6dfe104a61ccc2d66ce3dca8cc`. Both were integrated and pushed to main;
verified activations are 17:42:46 and 17:44:54 PDT respectively.

The [research history](../research/histories/self-study.md) retains the exact
owning account, qualification, release receipts and two early natural Minime map
jobs. Those map jobs do not directly establish Astrid authorship admission in
natural use. The original S-008 window and its blocked actions remain historical
evidence; observing the repaired Astrid route remains the next outcome question.
