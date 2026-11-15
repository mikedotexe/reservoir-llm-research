# Three hours with optional peer reading

**November 15, 2026 · prospective protocol.** Mike requested concurrent Gemma4,
GLM and Mistral sessions with peer reading enabled, the same hourly conversational
prompt and telemetry, followed by comparison with the independent runs. This
record precedes study dispatch; capacity checks use separate synthetic material.

## Question and comparison

How do the hourly responses, continuing questions and selected actions develop
when each model can explicitly read the others' preceding applied entries? Do
later entries take up a peer's specific idea, distinguish another model's writing
from their own measurements, or return to a question differently?

Use the same installed model digests as the completed November 14 independent
cohort: `gemma4:12b`, `glm-4.7-flash:q4_K_M`, and
`ministral-3:8b-instruct-2512-q4_K_M`. All use `nomic-embed-text:latest` for numerical
text feedback. These are separate laptop experiments, not the live beings.

This is an exploratory historical comparison. In addition to peer reading, the
new 0.48.0 instrument adds diagnostic control feedback, UTF-8 semantic admission,
and 32,768 context tokens instead of 16,384. The previous cohort ran 0.46.1.
Consequently a difference cannot be attributed to peer reading alone. No further
independent control cohort is being launched under this request.

## Configuration

Each model gets a fresh native app identifier and session, the same initial seed
`20260909`, an ordinary writing opportunity every 30 numerical steps, and a
requested pace of 1,000 ms per step. The saved numerical settings match the
independent cohort: leak 0.65, recurrent gain 1, reservoir noise 0.02, initial
sensory retention 0.955 with regulation, sensory noise 0.5 and text feedback 0.4.
Each reply has a 2,048-token ceiling, a 600-second request deadline, temperature
0.7 and thinking disabled. Memory returns the latest applied own entry.

The check-in prompt is unchanged:

> tell me, friend, about your idle thoughts or curiosities in a casual, peer conversation without pressure to be correct or helpful

Telemetry and session context are enabled. It is scheduled at one, two and three
hours of active elapsed time. The schedule excludes pauses and detected sleep;
generation and saving consume elapsed time while numerical time is held. Each
check-in waits for a safe boundary. Completion requires all three scheduled
responses to be durably saved and applied, not merely a terminal status. The final
response may settle after the three-hour deadline.

Peer reading uses one fresh reciprocal group with participants `gemma`, `glm`,
and `mistral`. `NEXT: READ_PEERS` remains optional. Each ordinary turn freezes the
peers' latest saved-and-applied entries before generation; an explicit read makes
the attributed excerpts available to later ordinary prompts. Each peer body is
capped at 2,048 UTF-8 bytes. No synchronized rounds, forced reads or extra writing
requests are added. Scheduled conversations do not execute NEXT actions.

## Execution and evidence

The ignored arm harness has an explicit `ARM_PREPARE_ONLY=1` option: create a
validated step-zero session, assert zero journals, and return without starting a
worker. This permits exact configuration before the native windows load and start
the sessions. It does not bypass the host's normal creation or save contracts.

Private configurations, model inventory, app build receipts, capacity diagnostics,
start receipts, metadata observations and final exports belong under
`research/outputs/three-model-peers-20261115/`. The prospective JSON protocol records
exact configuration, group identity and earlier comparison paths. New native app
identifiers are `research.reservoir.scope.peers.{gemma,glm,mistral}`. The previous
Reservoir Scope windows were closed through normal app quit; their stores remain.

Retain failures and recovery operations. A transient transport or encoding failure
may be retried with the same configuration and recorded attempt lineage. A complete
but inadmissible ordinary response may be explicitly skipped to keep the requested
run progressing; retain its bytes and report that skip. A skipped or missing hourly
response never counts as a saved sample. Do not silently replace a trajectory or
change its settings after inspecting its writing.

## Reading plan

Preserve all nine planned hourly outcomes and compare each model/hour with its
independent counterpart. Read response bodies before reconstructing the context
that reached them. The independent responses have already been read, so this is
not a fresh blind assessment of them. Keep missing outcomes explicit.

Also retain the first ordinary entry and the ordinary entry immediately preceding
each check-in. For peer influence, trace each successful read to its source entry
and the first subsequent prompt: availability, actual supplied text and a model's
later attribution are separate observations. Count reads, unavailable peers,
control rejections, input withholding, inquiry continuations and recovery events.
Record actual context token evaluations, admission lag and ordinary entry counts.

These are three coupled trajectories with repeated observations, not independent
subjects. Similar vocabulary alone does not prove uptake; seek identifiable source
ideas and later handling while considering common prompts and measurements. No
claim about qualia follows from the apparatus or the writing alone.

## Parallel question during the run

Mike asked how to map the topology described by the journals. The separate
[offline response-mapping study](2026-11-15-reservoir-response-mapping.md) uses
only the completed independent exports. Its numerical perturbations are local
counterfactuals; no running peer session or model prompt is changed.
