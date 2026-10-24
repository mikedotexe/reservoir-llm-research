# Catalog source provenance and qualification of the all-lane claim

2026-10-24. Source audit only; no model outputs, live queries, or deployment claims.
This accompanies [S-016](../research/studies/S-016-action-catalog-framing.md) and corrects a
specific statement in [the October 22 Minime lane analysis](2026-10-22-minime-lanes-shown-and-written.md).

The retained `runtime.py` routes `private_journal`, `qualia_moment`, and `daydream` through
`_is_private_qualia_context`. At the catalog switch it combines those contexts with
`aspiration` as `open_expression_context`. In that branch the source selects
`COMPACT_ACTION_GUIDANCE` and omits `_low_fill_prompt_guidance()`. Other contexts use the
full catalog branch subject to its own stage choices. The shared NEXT grammar occurs before
the switch. Thus the retained code does **not** support an unqualified statement that the
long action catalog or active low-fill block reaches every lane.

The October 22 account identifies its copied source as sibling revision `9eabb34` and reports
57,229 lines. This retained runtime has 57,229 lines and sits in that session's S-012 source
directory, but this audit found no independently retained hash receipt binding these bytes to
that Git revision. Historical commit binding remains **unverified**. The source establishes
branch behavior for these bytes. It does not establish which bytes were deployed or what a
particular past model job received; those require delivery evidence. The historical journal
counts and lane marker estimates are not recomputed by this correction.

## Exact retained artifacts

The source directory is a private local capture, not a tracked research input:

```text
/private/tmp/claude-501/-Users-mikepurvis-other-reservoir-llm-research/5632654e-389b-4bc4-80a2-f71c14da3669/scratchpad/s012/minime-src/
```

| File | SHA-256 | Relevant source locations |
|---|---|---|
| `runtime.py` | `7a5281c677699ca61c3653e68ad28ff4def3df1792119dd10c02f1bb47c80799` | context set line 21321; open-expression selection lines 54964–54966; low-fill exclusion line 55004; catalog switch lines 55005–55206 |
| `expressive_journal.py` | `f4811dc218202b1421d95fae033f2642ea21aab38ebd9394354929927e486c9d` | `COMPACT_ACTION_GUIDANCE` at line 15 |

The compact constant offers a short set of examples and discovery affordances; it is not the
same option set with descriptions removed. It is retained in the private extracted bundle as
`compact_context_only`, excluded from S-016's four-arm treatment set.

## Reproducible, non-executing extraction

`reservoir_experiments/attribution_catalog.py` reads the two explicit files as Python AST.
It selects the full alternative of the one compact/full switch, concatenates only literal
strings, and records each static decision. All six stage-condition alternatives select their
empty branch: self-journal only, local-reflective only, Astrid-contact only, read-only research,
bounded actions, and experiments. The LOOK helper contributes its final literal camera
description. This is a declared hypothetical catalog configuration; no camera or source
method is invoked. Unexpected calls or expression shapes fail extraction.

The full result has 31,986 UTF-8 bytes and 3,926 whitespace-delimited words. The concise
transformation retains command heads, explicit inline argument forms, alias relationships,
undelimited framing/rules, and every uppercase literal identifier. It removes 136 description
tails, yielding 16,516 bytes and 1,725 words. Its source-only phrase inventory has 1,062
two-word candidates before per-case exclusion of common context. The actual compact constant
has 868 bytes and 112 words. These are source-construction measurements, **not experimental
outcomes**. All raw catalog text and correspondence rows stay in ignored private outputs.

The long catalog exceeds the runner's conservative byte-based guard at context 16,384.
S-016 therefore requires separately recorded token/context qualification and model-specific
padding before confirmation. There is no implication here that the full prompt already fits
or that a model received it intact. The protocol specifies the gate and interpretation limit.

The apparatus can test how a source-derived catalog affects synthetic writing. It cannot
retroactively establish the frequency, cause, or effect of actual past catalog exposure.
