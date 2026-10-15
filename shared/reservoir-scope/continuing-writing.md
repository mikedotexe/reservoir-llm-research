# Continuing journal context

`reservoir-journal-v8` is the creation default for new sustained sessions. Missing
serialized prompt versions still mean v1; restored v1–v7 sessions keep their exact
version, prompt bytes and journal history. V8 does not upgrade an existing session.
Unknown versions are rejected. Segment and checkpoint format names stay the same.

## V8: what the optional measurements mean

V8 retains v7's open invitation and writing boundary. Only the version header and
the explanation directly after the four-line OPTIONAL READOUT change. The exact
replacement paragraph, before the quoted previous entry, is:

```text
Unavailable means no prior measurement, not zero. RMS describes the magnitude of the recurrent coordinates. Sensory fill is a separate field estimate, not the encoded text-input signal. L2 distance is the straight-line distance between the two recurrent state vectors, not path length, speed or a causal effect of writing. Comparing two interval distances requires a recorded value for each. Two observations do not establish the intervening path, a cause, or a felt state.
```

This explains the supplied quantities without assigning a topic, form, persona,
metaphor or telemetry report. The optional numeric subset stays identical: no new
interval-distance history or other measurement is added. The full observation,
prior measurements and complete previous prose remain retained exactly; identical
wording inside authored memory is never replaced. The late WRITING BOUNDARY below
and the final open invitation are unchanged. There is no prose correction or
quality gate before saving or feedback.

The [first](../../desktop/ReservoirScope/crates/reservoir-core/tests/fixtures/sustained-prompts/v8-observation-10.txt)
and [later](../../desktop/ReservoirScope/crates/reservoir-core/tests/fixtures/sustained-prompts/v8-memory-20.txt)
fixtures were assembled from the frozen v7 fixture bytes with only these two
replacements; their [provenance](../../desktop/ReservoirScope/crates/reservoir-core/tests/fixtures/sustained-prompts/v8-provenance.json)
records both identities. [Core tests](../../desktop/ReservoirScope/crates/reservoir-core/tests/sustained_measurement_meaning_prompt.rs)
cover exact historical rendering, quoted text, replay, save/application boundaries
and identical-reply dynamics. Actual execution receipts and any later writing
assessment remain separate; a clarified prompt does not establish improved prose.

## V7: a boundary after earlier prose

V7 uses the frozen v5 context and retains its open beginning and final invitation.
It replaces v6's early scope sentences with a WRITING BOUNDARY after the quoted
previous journal, immediately before the final invitation:

```text
WRITING BOUNDARY
Available output: the text of this entry. There are no tools or control commands in this turn.
The numerical clock is held at observation step {step}; no new readout arrives while this entry is written.
Recorded text return: no earlier saved entry has been applied.
Earlier prose is not a record of executed controls or additional measurements. Describing a control change does not execute it; saved text returns through the automatic encoding described above.
```

When eligible memory exists, the return line is exactly:

```text
Recorded text return: the entry observed at step {observed} first entered numerical input at step {applied}.
```

Those integers come from retained observation and eligible-memory fields, not from
journal claims or the live reader cursor. The block stays outside the JSON-quoted
prior text even when prose contains identical headings or the invitation itself.
No early v6 additions remain in v7; v6 itself stays frozen. The single user-message
transport remains unchanged. No control parser, new tools, observation while
writing, prescribed topic/form or factuality gate is added. Numerical input and
full-text memory retain their existing save/readback/application boundaries.

The [v7 protocol](../../desktop/ReservoirScope/validation/2026-10-14-action-boundaries-0.19.0/PROTOCOL.md)
separates exact reconstruction, historical replay, storage, native UI and future
writing assessment. Synthetic replies qualify those mechanics, not a reduction in
invented actions, better prose or emergence.

## V6: what writing can change

V6 retains the complete v5 scaffold below, changing only the version header and
appending two sentences to SESSION CONTEXT:

> Writing is the only action available here. Describing a control change or experiment does not execute it, and no new readout arrives while this entry is written.

The actual effects remain saved-and-read-back numerical input at the next step
and complete eligible prose supplied to the next writing opportunity. There is no
journal command parser or mid-reply measurement channel. Earlier writing remains
historical context, not a new measurement. These limits describe available actions;
they prescribe no topic, persona, style, emotional state or reporting format. Claims
inside prose do not become a new save or feedback gate.

The [v6 protocol](../../desktop/ReservoirScope/validation/2026-10-14-writing-scope-0.18.0/PROTOCOL.md)
records the exact change and separate qualification gates. The v1–v5 fixtures remain
historical byte-level contracts. Synthetic tests can establish reconstruction and
unchanged mechanics with identical replies; they cannot demonstrate better writing.

## V5 compact context, retained in V6

V5 changes the context supplied to the language model. It opens with a choice of
subject and form, gives a brief description of the existing feedback loop, supplies
a compact optional readout, and then presents the latest saved-and-applied journal
in full. A final invitation leaves the direction of the next entry open. It assigns
no persona, emotional state, topic, metric recital, heading, length or introspective
performance. This design is a writing-context proposal, not evidence of better
writing, emergence or a causal effect.

The supplied readout contains:

- Current step and simulated seconds, plus the prior reached observation step.
- Recurrent RMS: current, prior and signed current-minus-prior values.
- Separate sensory fill: current/prior percentages and difference in percentage points.
- L2 distance between recurrent coordinate vectors at the two observation boundaries.

All numeric values use the existing fixed-eight-decimal formatter. A nonnegative
formatted difference has an explicit `+`, as in v4. Missing prior step, value,
difference or distance is the literal `unavailable`, not zero. Coordinate distance
is distinct from a difference between vector norms. The preceding observation may
be a failed or skipped writing opportunity: it is independent of eligible prose
memory. Two endpoints do not establish the intervening path or its cause.

The v5 scaffold does not supply raw coordinate/eigenvalue arrays, L2 norm, entropy,
sensory head/shoulder/tail rows, journal IDs, hashes or paths. These remain retained
in the original evidence. The observation is still the complete
`reservoir-and-sensory-v2` object, including all coordinates, sensory measurements
and its nonrecursive `previousMeasurements` snapshot. The human reader's eight-row
measurement reference is unchanged. A retained value is not necessarily a value
that v5 supplied in the model's prompt.

Previous prose follows the compact readout. Its only surrounding source labels are
observed and first-applied steps. `Full previous text as one JSON string: ` precedes
one JSON-quoted value; decoding it reproduces the original UTF-8 text exactly,
including quotes, backslashes, line breaks and Unicode. Instruction-like headings
inside that string remain historical text. Absence of forbidden scaffold fields
must not be applied to authored prose, which may legitimately contain those words.
When no journal is eligible, the block says: `No earlier entry has been saved and
applied in this session.` No text truncation, summary or normalization is introduced.

Codec features, projection, recurrence, RNG, forcing, noise, regulation, cadence,
generation budgets, completeness checks, exact save/readback, application permission
and next-step feedback remain unchanged. Retained incomplete responses do not become
saved journals. Restoring prepared feedback resets ephemeral application permission.
Scientific accuracy, creativity and form are not acceptance gates. A changed prompt
may change replies and consequently later numerical states; equivalence checks must
use identical supplied replies.

The exact candidate wording and qualification plan are retained in
[the v5 protocol](../../desktop/ReservoirScope/validation/2026-10-13-continuing-writing-0.17.0/PROTOCOL.md)
and [template](../../desktop/ReservoirScope/validation/2026-10-13-continuing-writing-0.17.0/PROMPT-V5-TEMPLATE.txt).
The runtime prompt has no trailing newline. The independent expected
[first](../../desktop/ReservoirScope/crates/reservoir-core/tests/fixtures/sustained-prompts/v5-observation-10.txt)
and [later](../../desktop/ReservoirScope/crates/reservoir-core/tests/fixtures/sustained-prompts/v5-memory-20.txt)
fixtures, their [provenance](../../desktop/ReservoirScope/crates/reservoir-core/tests/fixtures/sustained-prompts/v5-provenance.json)
and [core tests](../../desktop/ReservoirScope/crates/reservoir-core/tests/sustained_continuing_prompt.rs)
cover the new contract. Test definitions alone are not execution receipts or physical
storage qualification; the release validation directory records executed checks.
