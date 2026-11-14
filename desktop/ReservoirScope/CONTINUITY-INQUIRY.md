# Returning to a question

The continuity invitation lets an ordinary journal entry open a question about
its local reservoir, recent journal history, or both. The question remains open
across subsequent entries and restoration. Later writing receives identified
evidence and can continue, replace, or close the inquiry. A sentence such as
“I want to investigate this” remains prose unless the model chooses the explicit
inquiry footer.

This is a local research capability. It does not browse the web, execute generated
code, inspect another session, or contact Astrid or Minime. It uses the ordinary
writing opportunities already scheduled for this session.

## The writing and the evidence

The journal invitation leaves the subject, form and length open. The model can
write briefly, develop a thought, ask a question, revisit an earlier idea, or
leave a thread aside. An inquiry is optional and does not require a report on
every entry. Text-input choice, control choice and inquiry choice are independent.

The runtime distinguishes two measurements:

- **Observed state difference** compares coordinates at two observation steps.
  It is not a path length, speed, or isolated effect of a particular action.
- **Additional effect of an action** compares two calculations at the action's
  application step, with the new action present or omitted and the other inputs
  held the same. A zero result for `NONE` does not mean the reservoir stopped.

`RELEASE` restores the session's initial control settings. It retains the current
state and the writing already recorded. Withholding clears the held journal-input
vector, while base forcing, noise and separately chosen actions continue.

Meaningful interventions have a separate bounded history, so subsequent `NONE`
choices do not immediately displace them. Input-disposition changes also remain
separate from control changes.

## Opening and returning to an inquiry

The model can place one inquiry line before its input-choice and final `NEXT`
lines:

```text
INQUIRY: OPEN both "What changes after this input, compared with the opening state?"
```

The supported sources are `journal`, `dynamics`, and `both`. Opening captures the
observation and controls from the requesting turn, before its new action applies,
and identifies earlier applied journal excerpts. The requesting response is not
silently included as prior evidence for itself.

```text
INQUIRY: CONTINUE
```

Continuing refreshes the available recent journal evidence while retaining the
original question and opening baseline. Omitting the inquiry line keeps the
question open. Another `OPEN` explicitly replaces it; `INQUIRY: CLOSE` closes it.
These changes become effective at the same saved application boundary as the
entry's input and control choices, with a recorded receipt.

The first version retains eight recent applied journal excerpts and returns up
to four selected preceding excerpts for an inquiry. Excerpts have entry IDs,
observation/application steps, full-body hashes and explicit truncation markers.
This is bounded recent-history access, not search of the complete journal archive.
The original full writing remains in its saved journal.

A dynamics inquiry returns its opening and current measurements and recurrent
coordinates. Other inputs and actions may have occurred between them. The
comparison describes what changed over that interval; it does not assign all
change to the opening action. The latest retained probe's immediate paired
response supplies a separately defined comparison.

## A model-designed input probe

`PULSE` changes recurrent state directly. `PROBE` instead sends an explicit vector
through the input channels for one application step:

```text
NEXT: PROBE <JSON array of exactly 48 numbers>
```

Each value must be finite and between −1 and 1, with total vector L2 norm at most
2. Invalid vectors are rejected without guessed padding or normalization. An
all-zero vector is valid as an explicit control.

The 48 values address the journal-input channel slots, corresponding to indices
18–65 of the engine's 66-coordinate input. The configured text codecs ordinarily
populate the first 32 of those slots. These are numerical input indices, not
named physical places or emotions. A bespoke vector can use any of the 48 slots.

The probe is added after the ordinary text and difference-channel contributions,
independently of the text feedback scale. It reaches the recurrent reservoir and
the separate sensory field, then disappears from the next reconstructed input.
It does not become a held input. A withheld journal can therefore accompany a
probe, and the record distinguishes those choices.

The receipt preserves the exact accepted vector and the immediate paired
recurrent response. A later sensory-fill reading is an actual observation,
not an isolated estimate of the probe's sensory effect. Probes at different
evolving states are not equivalent to a scan from one shared baseline.

## Conversations, saving and compatibility

Scheduled conversations remain passive for that reply. They cannot execute
control, input-choice or inquiry directives; their complete responses still
enter numerical feedback. Ordinary journal turns retain those capabilities.
Plain scheduled prompts remain the exact configured prompt without added context.

Completed responses are retained before semantic encoding. An encoding retry
reuses the same response; it does not generate a new inquiry or apply its probe
again. Restoration begins paused, and the saved application is authorized once.
Quoted earlier footers remain historical evidence rather than fresh commands.

The new mode is `authored-v3` with `reservoir-journal-actions-v3`. Earlier action
modes and saved prompt contracts retain their existing behavior. The app exposes
the older choices for comparison; enabling the new mode is not a migration of an
old session.

Runtime correctness and model investigation quality are separate questions.
The [release record](RELEASE-0.46.0.md) identifies the checks actually executed.
