# V7 episode 01 — admission refused; all twelve slots unstarted

Recorded 2026-10-14T18:01:23.735126+00:00. The one preserved admission at **2026-10-14T17:58:27.245973+00:00** refused this episode before service launch or a new model session. There is **no new writing or quality signal**.

| Admission condition | Frozen requirement | Recorded value | Outcome |
| --- | --- | --- | --- |
| Memory pressure level | 1 | 2 | Refused |
| Reported free memory | At least 35% | 31% | Refused |
| Available disk bytes | At least 8,589,934,592 | 529,490,833,408 | Passed |

These values come from [the saved admission receipt](host-admission-01.json), not a fresh probe. Its freeze hash matches [the prospective freeze](evaluation-freeze-01.json). The parent operator reports no new owned service, readiness request, session creation, Start, model request, response, journal or application after refusal. No retry or admission polling was performed for this accounting.

## Twelve-slot accounting

All twelve planned opportunities remain **unstarted**. The planned observation steps below are prospective positions, not observations that occurred. Request, response, journal and application are `null` for every slot; zero counts describe this unexecuted episode only.

| Slot | Planned observation step if reached | Actual status | Request | Response | Journal | Application |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 30 | Unstarted | null | null | null | null |
| 2 | 60 | Unstarted | null | null | null | null |
| 3 | 90 | Unstarted | null | null | null | null |
| 4 | 120 | Unstarted | null | null | null | null |
| 5 | 150 | Unstarted | null | null | null | null |
| 6 | 180 | Unstarted | null | null | null | null |
| 7 | 210 | Unstarted | null | null | null | null |
| 8 | 240 | Unstarted | null | null | null | null |
| 9 | 270 | Unstarted | null | null | null | null |
| 10 | 300 | Unstarted | null | null | null | null |
| 11 | 330 | Unstarted | null | null | null | null |
| 12 | 360 | Unstarted | null | null | null | null |

The [structured accounting](outcome-slots-01.json) also preserves the planned next-step positions and null actual identities. Actual totals: **0 requests, 0 responses, 0 saved journals and 0 feedback applications; 12 of 12 slots unstarted**.

## Evaluation status and limits

Mechanical replay and prose evaluation were **not executed**: this episode produced no session export or received text to assess. Host admission refusal is neither a failed model response nor a prose-quality finding. There is no `JOURNALS.md` to manufacture, and no unseen-text evaluation. Earlier v5/v6 writing and synthetic v7 qualification remain separate evidence; they do not fill these slots or establish a new v7 real-model result.

The frozen [evaluation plan](EVALUATION.md) and [reading rubric](RUBRIC.md) remain unchanged. Their planned questions about continuity, voluntary measurements and described versus executed actions remain unanswered by this episode.

## Receipt binding

| Preserved input | SHA-256 |
| --- | --- |
| [host-admission-01.json](host-admission-01.json) | `27868e1ef0a29139ff0f34b6e933b9e9ab0beb63eed328f07c7783ad66e93330` |
| [evaluation-freeze-01.json](evaluation-freeze-01.json) | `10148c5f6244f3fe404d26f6fd798a9a89220c1bc5e25ab512e3d4b3f69778a0` |
| [run-plan.json](run-plan.json) | `297a91d85e46ec7ffb942be491961ed478b281f86f1f7c884c9d605102928212` |
| [PROTOCOL.md](PROTOCOL.md) | `64a03130e67669a1af0d627f7e849d73ae8c6f61f7ba0ffe3fa0a0a013a4f5b0` |
| [RUBRIC.md](RUBRIC.md) | `98dfaf72a45af2d3f602407eb6b739357eab532c2d39e0b2868c85fa23c3aef6` |
| [EVALUATION.md](EVALUATION.md) | `91df1c746a900a50b6509ab233b94f41ad54158e7f235b111ed49da5db817704` |

This account reads only preserved local files. It does not remeasure the host, inspect a service, contact a model, or infer new runtime activity from prior episodes.
