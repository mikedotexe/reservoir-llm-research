# Longer writing · admission refused

The planned twelve-opportunity real-model episode **did not run**. The single
[admission receipt](host-admission-01.json), captured at
**2026-10-14 00:25:07.910524 UTC** (October 13 locally), refused admission under the
unchanged [prospective plan](run-plan.json).

| Admission measure | Observed | Required | Result |
| --- | --- | --- | --- |
| Memory pressure level | 1 | 1 | Met |
| Reported free memory | 32% | At least 35% | Not met |
| Free disk bytes | 5,587,763,200 | At least 8,589,934,592 (8 GiB) | Not met |

All three admission commands exited successfully; both the memory and disk
thresholds failed. The protocol forbids another sample or retry for this episode.
No additional probe was made for this account.

## Actual outcome

The parent operator reports prepared UI only and the prior completed synthetic
session stopped. No owned model service was launched, no readiness request was
sent, and no new model session was created or started. This review inspected
retained files only; it did not independently inspect processes or endpoints.

**0 generation requests, 0 received responses, 0 saved journals and 0 feedback
applications out of 12 planned opportunities.** All twelve slots—planned at steps
30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330 and 360—remain unstarted because
admission was refused. There is no new session, native export or recovery result.
The [outcome ledger](real-model-outcome-01.json) records each slot explicitly.

No actual-export checker, production verifier or prose-quality harness was run
for this episode. No full-text reading or `JOURNALS.md` was produced because no new
response exists. The previously executed 27 synthetic checker tests remain
[source qualification](checker-tests-01.json), not real writing or continuity
results.

## Evidence and limits

The admission receipt binds the [prospective freeze](evaluation-freeze-01.json),
SHA-256 `ea2ec0b090b1164651c720e4e99353296ca83c87e8f5799ebfc3fd4e7dd61c00`.
The outcome ledger records exact hashes for the admission, protocol, plan,
[rubric](RUBRIC.md), evaluation contract and admission source.

An initial readback detected a post-freeze amendment to the independent review
note. Its owner preserved that amendment separately and restored the exact frozen
original; [REVIEW-CONTINUITY.md](REVIEW-CONTINUITY.md) records the chronology.
All 20 frozen inputs now match in this account's independent readback. This current
match does not erase the documentation race. The prospective protocol, plan,
checker, helper and actual admission receipt were unchanged.

This is an operational refusal with **no new journal-quality signal**. It neither
confirms nor refutes longer writing continuity, factual grounding or input-token
evidence from a real provider. Prior four-entry writing and synthetic transport
results do not fill the twelve unstarted slots. No retry, replacement run, polling
or budget extension belongs to this episode.
