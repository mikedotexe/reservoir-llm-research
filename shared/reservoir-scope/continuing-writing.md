# Continuing journal context

`reservoir-journal-v5` is the creation default for new sustained sessions. Missing
serialized prompt versions still mean v1; restored v1–v4 sessions keep their exact
version, prompt bytes and journal history. V5 does not upgrade an existing session.
Unknown versions are rejected. The segment and checkpoint format names stay the same.

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
