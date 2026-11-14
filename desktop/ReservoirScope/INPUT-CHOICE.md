# Choosing whether an entry enters numerical feedback

Development design for 0.44.0, November 13, 2026. This extends local authored
actions with a separate choice about the current entry's text input.

A journal can be worth keeping without immediately becoming numerical input.
The model can retain the entry in its journal and later text memory while
withholding its encoded signal from both the recurrent reservoir and the
separate sensory field. This choice is independent of its `NEXT` operation.

```text
I will leave this entry in the journal and let the other inputs continue.

WITHHOLD_RESERVOIR_INPUT=true
NEXT: NONE
```

The optional directive goes immediately before the final `NEXT:` line. Explicit
`false`, or omitting the directive, sends the body through the usual text-feedback
path. `true` sets that entry's held text vector to zero at the next authorized
application boundary. It replaces the prior held vector rather than continuing
to feed an older entry. A subsequent ordinary entry can send its text again.

The raw response remains exact evidence. Recognized control lines are separated
from the journal body. Saving, readback and durable application still happen;
only the numerical text-input route is withheld. With an embedding codec, the
withheld entry needs no embedding request. Its body remains eligible for return
as memory under the selected memory policy.

The distinction matters: returned prose can affect later writing or choices,
which can then influence the reservoir. Withholding the immediate numerical
input does not make the entry causally isolated from the rest of the loop.

## Independent choices and truthful results

| Input choice | NEXT choice | Result after the saved boundary |
|---|---|---|
| Send | `NONE` | Ordinary text input; effective controls stay in place. |
| Withhold | `NONE` | Zero held text input; effective controls stay in place. |
| Send | `PULSE` or `TUNE` | Text input plus the separately selected intervention. |
| Withhold | `PULSE` or `TUNE` | Zero held text input plus the selected intervention. |
| Either | `RELEASE` | Restore initial controls, preserving state; respect the independent input choice. |

Withholding does not stop recurrence, base forcing, noise, regulation, or an
enabled difference channel. It does not undo earlier input or reset memory.
`NONE` never means “withhold,” and `RELEASE` never means “erase.”

The input decision and action decision have separate receipts. A valid input
choice survives an invalid `NEXT` choice. A malformed fresh input directive is
reported as rejected, and numerical text input is withheld for that entry
rather than guessing permission to send it. Quoted, fenced and list examples
remain inert prose. Later ordinary prompts report the actual disposition.

Scheduled conversations keep their existing behavior: their answers become text
feedback and they execute no input directive or NEXT action. Telemetry-enabled
conversations can see recent receipts; plain conversations receive only the
editable prompt. The capability belongs to new `authored-v2` sessions. Saved
`authored-v1` sessions retain their original parser, prompts and numerical path.

## A question this makes possible

Mike noticed a developing culmination narrative in an earlier ordinary journal:
an event was anticipated, announced, declared complete, and then elaborated into
an aftermath. That user-selected passage motivates a question; it is not a
preselected sample or evidence that the new capability improves anything.

Can a model retain an intention, distinguish what it sent from what it kept as
writing, encounter an actual consequence, and revise its later account or choice?
Ownership language alone would not answer this. The first useful observation is
whether later prose accurately distinguishes an executed action, an unchanged
control, a rejected directive, and withheld text input.

A bounded future test could preserve the same available menu and compare chosen
execution with a matched random or yoked execution condition, always returning
truthful outcomes. A separate input-routing comparison would isolate the
withholding capability. The numerical input channel and the returned-prose
channel need separate controls. Any action task should be scored separately from
blind reading of free journals. This is a proposed inquiry, not a launched study
or a conclusion about subjective experience.
