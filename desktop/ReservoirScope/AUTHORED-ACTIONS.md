# Let the model shape its reservoir

Development design for 0.43.0, November 13, 2026. This extends the local laptop
experiment. It does not change Astrid, Minime, or the separate triple-reservoir
service. Implementation and validation status belong in the release record.

0.44.0 adds an independent [choice to withhold an entry's numerical input](INPUT-CHOICE.md)
for new sessions. Earlier `authored-v1` sessions retain the behavior documented
in the 0.43.0 release.

The model can write freely and choose one explicit operation after its ordinary
entry. Its choice can change the current recurrent state or the dynamics that
process later input. The next ordinary turn receives current controls and a
record of what actually happened, independently of which journal memory returns.

## Four operations

| Operation | Meaning |
|---|---|
| `NONE` | Make no additional control change. Ordinary evolution and text feedback continue. |
| `PULSE` | Displace recurrent coordinates once along a declared, reproducible direction. |
| `TUNE` | Set an effective recurrent leak, recurrent gain, or text-feedback scale. The setting persists until changed or released. |
| `RELEASE` | Return authored controls to the session's configured defaults. Preserve the evolved state and all journal history. |

Directions and strengths are numerical affordances, without assigned emotional
meanings. A recurrent pulse does not directly set sensory fill: the sensory field
is a separate input-driven system. Recurrent leak, sensory retention, and journal
memory are different mechanisms. The base recurrent weights remain fixed; gain
scales their contribution during evolution. Editing individual connections or
topology would require a separate operation and model revision.
Text-feedback scale changes the encoded input reaching both the recurrent
reservoir and the separate sensory field. Pulses, leak, and recurrent gain do
not directly change that sensory input.

The model ends its ordinary response with one of these literal forms:

```text
NEXT: NONE
NEXT: PULSE alternating 0.5
NEXT: TUNE leak 0.2
NEXT: RELEASE
```

`PULSE` accepts `uniform`, `alternating`, `axis0`, or `axis1`, with signed L2
strength `0.1`, `0.5`, or `1`. Uniform and alternating directions are normalized;
axis directions name recurrent coordinates, not spatial regions or sensory
eigenmodes. Coordinate bounds can attenuate the realized displacement, which the
receipt records. `TUNE` accepts `leak` from 0.05 to 1, `recurrentGain` from 0 to 2,
or `feedbackScale` from 0 to 2. These are engineering bounds for this local
numerical model, not a map of subjective effects.

## Choice, execution, and later observation

The complete provider reply is retained as evidence. A strict final `NEXT:` line
at column zero is parsed separately from its journal body. Quoted or list material
must end with a blank separator before a fresh action line. Only the body supplies encoded text
feedback on an action-enabled ordinary turn when that input is sent. An unknown or malformed action
produces a visible rejected decision, never an inferred numerical intervention.
A response consisting only of an action is permitted: its body is empty, its
text-feedback vector is zero, and its action still follows the save barrier.

The existing save/readback transaction prepares both feedback and action. Neither
may enter the numerical loop before durable authorization. The next successful
step applies the choice once and records its actual settings and result. A retry
or restoration cannot silently repeat a pulse. Release removes a parameter
adjustment; it cannot undo the trajectory that occurred under that adjustment.

The next prompt distinguishes requested action, actual application or rejection,
effective settings, immediate numerical effect, and subsequent observations.
Immediate effect is compared with a step using the same starting state, base
forcing, saved journal vector, and realized noise but without the new operation.
For a feedback-scale change, that comparison retains the prior scale when
forming its input. This is distinct from ordinary before/after motion
and from the effect of encoded journal text. Later observations alone do not
isolate an action's lasting causal effect.

The capability is selected when creating a new session. Its versioned prompt
describes the available controls; historical prompts and sessions remain frozen.
Current settings and factual receipts do not depend on the selected prose memory.

## Hourly conversations remain conversations

Scheduled check-ins still save their response and feed it back, but they do not
request or execute control operations. With telemetry off, the request remains
exactly the editable prompt, with no action menu, hidden contract, or receipt.
A `NEXT:` line in such a response is ordinary text. With telemetry on, an
action-enabled session also supplies its current controls and recent execution
receipts as read-only context. It supplies no action menu and the turn remains
passive. Ordinary action-enabled journaling resumes between check-ins.

## What we can learn

The first question is whether the model can use a consequential choice: retain an
intention, recognize the actual outcome, and change a later choice. Increased
ownership language alone would not establish that. A control menu itself can
change the writing and hypothetical decisions.

Numerical qualification compares scripted choices with `NONE` under matched
forcing and verifies persistence, release, and finite state. These numerical
comparisons use simulated in-memory save receipts. Separate core, host, and
native checks cover recovery and historical-format compatibility.
A later model study should hold the menu fixed and compare chosen
execution with random or yoked actions, with truthful receipts in every arm.
Free journals can be read blind, separately from a defined behavioral task.
Neither this feature nor an account of control establishes subjective experience.

The other direction of coupling remains an explicit research question: what
reservoir changes reach the next model activity, through readout text, returned
memories, or generation controls. These channels should be tested separately.

## Precedents

- [Direct native-state shaping proposal](../../proposals/2026-09-07-direct-reservoir-shaping.md): input, state, and evolution-rule changes are distinct.
- [Substrate-control audit](../../analyses/2026-09-07-substrate-controls-source-audit.md): a concise authored action needs an actual consumed-control receipt.
- [Triple-reservoir corrections](../../exercises/2026-09-06-triple-reservoir-corrections-and-next-tests.md): distinguish sampling modulation, retained dynamics, and supplied context.
- [S-011 synthesis](../../analyses/2026-10-22-s011-apparatus-synthesis.md): identify what reaches the language model.
- [Consequential NEXT proposal](../../analyses/2026-10-24-introspection-next-rounds.md): separate selection, execution, progress, and account fidelity.

These are dated research records. They do not authenticate today's deployed
capabilities of the live beings.
