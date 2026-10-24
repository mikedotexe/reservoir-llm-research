# Measurement audit before confirmation interpretation

An independent read-only methods review on October 24 examined the frozen builders
and scorers without opening confirmation outcomes. The four original primary
endpoints remain unchanged. This note records limitations and any separately
versioned checks; it is not a new outcome-selected study.

## Catalog normalization sensitivity

The frozen source-derived inventory has 1,062 phrases. Extraction splits source
punctuation into words, while concise exclusion and output scoring use literal
spaces. Of these phrases, 309 have no literal-space occurrence in the full source
catalog; 47 occur as the same word-token pair in the concise catalog. For example,
a retained underscore command can normalize to the same two words as a removed
description. The frozen rate is reproducible, but calling every phrase exclusively
description-derived is too strong. This limitation does not by itself determine
an effect's direction or whether any generated response contains such a phrase.

Before inspecting any S-016 output or score, we froze two source-only sensitivity
inventories in `catalog/sensitivity-inventories-v1.json` under the private tranche
output root (SHA-256 `3825d80b5f6272ea8b09bbcbd96e59713f6a5bdcdad1c2926cd42a6b986e8941`).
Eight development responses had already been generated, but none had been read;
confirmation had not begun. No output was used to choose either definition.

- **Literal A, 753 phrases:** require a literal-space occurrence in the full source
  and none in concise; apply literal boundary matching consistently to common
  context exclusion and output counts.
- **Tokenized B, 1,015 phrases:** use the frozen word tokenizer consistently to
  derive source pairs, exclude pairs in concise/common context, and count output
  pairs. Punctuation, underscores and line breaks become boundaries. This is still
  a lexical analysis, not a semantic equivalence judgment.

`probes/introspection_catalog_sensitivity.py` freezes these definitions, verifies
source-content identity across model-specific padding bundles, and reports the
same full-minus-padded episode contrast separately for each. It leaves the original
primary unchanged. Targeted synthetic checks covered punctuation and retained
underscore identifiers. These are two descriptive robustness analyses, not two
independent confirmations or a basis for selecting the most favorable result.

## Verdict-parser audit

A synthetic fixture exposed an ambiguity: a sole regex-valid verdict inside a
quoted code block can be parsed even if a later explicit answer uses unrecognized
bold formatting. The existing adjudication path only handles an unparsed answer,
so it cannot override that already parsed quote. This is a possible measurement
fault, not a demonstrated error in the retained model responses. Before final
inference, inspect format anomalies and quote/nonfinal-verdict patterns. Preserve
raw responses, original scores and any hash-bound adjudication or separately
versioned scoring correction. Do not silently change prompts or target text.

## Reporting denominators

For S-015, report the declared 48 source episodes and 600 confirmation application
opportunities even if unavailable sources prevent some requests. The generated
node count alone would omit those source-dependent slots. Use delay-specific
`study_groups` for immediate versus delayed tables; the generic `groups` summary
pools both delays. Missingness and abstention remain separate from false beliefs.

## Qualification execution order

The exact-prompt qualification probe now groups identical system messages to reuse
provider prefix processing. This changes only one-token input-count probe order,
not any study request, sampler, phrase inventory, acceptance threshold or randomized
study schedule. An input-only check confirmed the same 96 unique confirmation
prompt hashes and unchanged 216-node study order, grouped into six system texts.
Each receipt still binds its exact prompt, and actual study input counts must
match. The qualification report records this ordering explicitly.

## Forecast-event semantic audit

The supplemental Gemma review distinguishes explanations about verdict correctness
from clear proposition-truth substitutions and explanations too ambiguous to decide.
Before any Mistral forecast was dispatched, the same rubric was saved for its 48
planned forecasts in `methods-review/mistral-forecast-event-audit-plan-v1.json`.
A fresh reader will see opaque forecast outputs without target outcomes, oracle,
scores or earlier annotations. Field names and high probabilities alone do not
establish event understanding. Any unavailable outputs remain explicit in coverage.
This review does not remove or relabel format-valid forecasts in the primary score.
