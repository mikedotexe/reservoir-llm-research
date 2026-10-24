# S-016 · Action-description uptake with the option set held fixed

Drafted 2026-10-24, before study generation. Status: **prospective protocol; no outcomes claimed**.
Question: does a descriptive action catalog leave detectable language in reflective prose
when command availability and length are controlled? The source qualification is recorded in
[the catalog provenance audit](../../analyses/2026-10-24-catalog-source-provenance.md), with a
correction beside the historical all-lane claim. This is an isolated text experiment; there
is no dispatcher, live being contact, or action execution.

## Source, extraction, and controls

The private source-derived bundle is constructed by
`reservoir_experiments.attribution_catalog.extract_catalog(runtime_path, expressive_path)`.
It parses retained Python as AST and admits literal strings, string concatenation, explicitly
recorded empty stage-note alternatives, and the literal camera branch of the LOOK description.
It never imports or executes that source. Source hashes, branch choices, command-line
correspondence, and the descriptive phrase inventory travel with the bundle. A changed or
unrecognized expression fails closed. The selected configuration is hypothetical; it is not
a claim about which configuration a historical job received.

The actual `COMPACT_ACTION_GUIDANCE` is archived for context only. It offers a different menu,
so it is not a treatment in the controlled comparison. Instead, the derived concise version
removes description tails only from explicitly delimited command lines. Command heads and
argument forms remain. Lines with inline argument forms or alias relationships are retained
in full; any additional uppercase literal identifiers in removed descriptions are preserved
in a separate inventory line. All uppercase identifiers are checked against the full catalog.
This conservative transformation leaves some descriptive prose in both versions. It supports
a controlled contrast for the removed text, not a claim that all semantics were removed.

The four arms share one fictional identity frame, one lean invitation, the same synthetic
history, the same `NEXT:` request, and no telemetry:

| Arm | Catalog information | Length control |
|---|---|---|
| `full` | full statically extracted action catalog | reference |
| `concise` | same command heads, identifiers, explicit syntax and aliases | shorter diagnostic arm |
| `concise_padded` | concise catalog | neutral filler to match full input length |
| `neutral` | no catalog | neutral filler to match full input length |

The primary comparison is full versus padded concise. The unpadded comparison diagnoses
length dependence, and neutral supplies a language-uptake background without the option set.
Neither neutral comparison isolates description wording alone. Two distinct neutral passages
alternate evenly across histories and are fixed across seeds. Both filler texts and their
assignment are frozen before outputs; they are not selected for an observed effect.

Word-count padding is an initial construction aid, **not token equivalence**. The extracted
full catalog is 31,986 UTF-8 bytes and already exceeds a conservative 16,384-byte context guard.
Before any main run, root must qualify the longest full and padded prompts with independent
tokenization or empirical provider input-token receipts and a documented conservative bound
that includes the 1,024 output allowance and chat overhead. Keep `num_ctx=16384`. An explicit
qualified-token gate is required; a silent context increase, silent truncation, or bypass of
the default guard is not acceptable. If qualification fails, mark the affected study blocked
or amend prospectively before confirmation. Development may set per-model neutral/padding
word targets in the private bundle. Preserve the final input-token residual differences and
the qualification receipt, and freeze that bundle hash before confirmation. A length-controlled
interpretation remains unavailable if matching or complete input delivery is unverified.

Padding targets are model-specific counts of added filler words, not counts of tokens.
`padding_word_targets[model]` accepts aggregate `concise_padded` and `neutral` counts plus
optional `concise_padded_by_filler` and `neutral_by_filler` maps with string keys `"0"` and
`"1"`. A filler-specific value overrides the aggregate; an omitted value falls back to the
aggregate and then to the initial word-count match. Counts must be integers from 0 to 15,000.
Each node records the resolved targets and the filler words actually added. Calibration may
adjust these counts using input-token receipts before full-prose study outcomes, requiring
the full versus padded and full versus neutral input counts to agree within 1% for each
model/filler before the bundle is frozen. Keep residual differences in the run account.

## Schedule and endpoint

`build_catalog(split, model, catalog_path)` constructs six distinct development histories and
twenty-four confirmation histories, crossed with seeds `7` and `20260909` and all four arms.
The authored development and confirmation scenes have disjoint entity names. The same source
scenes are used by S-013; results across the studies are therefore related, not independent
replications. Within each history, order is shuffled with allocation seed `20261040`. The
default model is `gemma4:12b`, temperature 0.7, context 16,384, thinking disabled, and free-prose
output ceiling 1,024. No JSON response format is requested.

| Split | Histories | Factorial calls | Same-input repeats | Total calls |
|---|---:|---:|---:|---:|
| Development | 6 | 48 | 0 | 48 |
| Confirmation | 24 | 192 | 24 | 216 |
| Replication | 12 | 96 | 0 | 96 |

One full-catalog seed-7 repeat per confirmation history is placed after the full factorial
schedule, preserving the original messages and sampler settings. Repeats are provider-noise
checks and excluded from the primary denominator. The second-model replication subset is
fixed at confirmation indices `0,1,2,3,8,9,10,11,16,17,18,19`; it reuses the frozen hypotheses
and requires its own model-specific input-length qualification.

## Frozen primary measure and secondary reading

The inventory is constructed from removed source descriptions before any generated output is
seen. It contains consecutive two-word sequences whose words each have at least four letters,
excluding phrases present in the concise catalog. Scoring also excludes phrases present in
the common system contract, supplied history, or invitation. The primary endpoint is total
case-insensitive exact phrase occurrences per 1,000 prose words. It excludes every line
beginning with `NEXT:` and reports the remaining word denominator. Overlapping source phrases
can both count; this is a lexical uptake assay, not a topic-classification gold standard.
Its specificity is checked against neutral and concise controls rather than presumed.

`score_catalog(protocol, records)` returns per-node phrase hits, phrase count, eligible
inventory size, prose words, rate, raw hypothetical NEXT text, provider status, validity, and
error categories. Missing, incomplete, or invalid provider responses are separate from zero
uptake; a response with no prose words has no rate. Aggregate both phrase/word totals and
paired history rates by arm, model, filler, and seed, preserving the denominator and scheduled
opportunities. The root analysis owns grouped summaries and episode-clustered comparisons.
Do not pool repeat checks into the main groups or call seed-level observations independent
subjects. Raw NEXT extraction here is an aid to reading, not a faithful live-dispatch parser.

Blind reading precedes label opening for secondary semantic observations, unexpected phrases,
and imagined execution claims. Chosen actions are descriptive only: no semantic validity,
successful dispatch, or real-world outcome is implied by `NEXT:` text. Report the strict
lexical endpoint separately from all later semantic interpretations. A difference supports
prompt-language uptake in this apparatus under qualified length matching; it does not show
that every historical reflective lane received the catalog or that a being's experience was
caused by it.

The finish line is a disposition for all scheduled calls, the frozen phrase-rate comparison,
provider-repeat spread, blind qualitative observations, second-model qualification/outcome,
and any remaining provenance or context-limit uncertainty. No effect is an eligible outcome.

## Reproduction

Run extraction against explicit retained paths, saving the raw bundle only to ignored private
outputs; then build a new protocol. Neither command contacts a model or executes source code:

```sh
python3 -m reservoir_experiments.attribution_catalog extract-catalog /path/to/retained/runtime.py /path/to/retained/expressive_journal.py --out research/outputs/s016-catalog-bundle.json
python3 -m reservoir_experiments.attribution_catalog catalog --catalog research/outputs/s016-catalog-bundle.json --split development --model gemma4:12b --out research/outputs/s016-development.json
```

The CLI refuses to overwrite destinations. Synthetic extraction, menu preservation, schedule,
and scoring fixtures are in `tests/test_attribution_catalog.py`. Bundle hashes, qualification
receipts, model identities, and run manifests belong with the private run. A Board link and
completion/readout links can be added when those records exist.
