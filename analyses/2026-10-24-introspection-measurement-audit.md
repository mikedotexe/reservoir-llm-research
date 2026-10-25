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

## Observed formats and versioned closeout

After the two Mistral S-014 target readings, the anomaly scan found nine complete
outputs whose explicit terminal verdict was inline and unavailable to the original
parser: four initial answers and five targets. A fresh reader received only opaque
outputs and exact text hashes, with no oracle or correctness score, and recovered
all nine stated labels. This uses the declared explicit-answer adjudication route.
No strict-format failure was waived. All 48 verdict-bearing outputs failed the
exact requested syntax, while all 48 JSON forecasts were valid.

The original automatic report retains 19 scorable targets, 16 correct, and a paired
contrast of −0.010417 [−0.027083, 0]. The separately bound reviewed report has 24
scorable targets, 21 correct, and −0.008646 [−0.026875, 0.003750]. The difference
reflects recovered measurement availability, not changed outputs or a correctness
adjudication. The summary probe also received a reporting-only fix: missing verdicts
now have an explicit string category, so a mixture of null and string dictionary
keys does not prevent JSON serialization. The original score hash remained unchanged.

The private `methods-review/scoring-closeout-plan-v1.json` records the final versioning
procedure after these observations and before Mistral memory outcomes. All eight
original reports and their matched comparison will precede integration of the
prepared parser/provenance fixes. New reports will retain strict format, source
labels and missingness separately; an unchanged-selection comparison will bind the
new scorer identities. This revised measurement binding will be labeled as such,
not described as a new outcome-blind selection freeze. No S-015 source verdict,
including an unavailable parsed label, will be silently reparsed in its frozen oracle.

## Transformation draft preservation

One Mistral transformation reached its 1,024-token cap. Its complete source answer
remained available, so the predeclared repair-and-review construction procedure
retained the episode without retrying the model call. The raw incomplete response
is in its original result receipt. The old review exporter correctly leaves its
usable transformation fields unavailable, but also omits the raw text from the
packet's draft field. A separate hash-bound addendum preserves that exact unfinished
text and stop reason beside the unchanged original packet.

A localized exporter repair is validated separately for final integration: preserve
raw failed/incomplete text and hashes directly, while keeping such text ineligible
as usable transformation fields, even if it happens to be valid JSON. Legacy packets
and logged source-only repairs remain readable. Array-valued memory fields are still
rejected until a logged repair; schema acceptance is not semantic fidelity. Neither
this fix nor the construction edits turn an incomplete call into a completed one.

## Transfer-diagnostic information access

A post-outcome source audit qualifies S-015's legacy “verdict-transfer baseline”
name. The calculation receives the authored `copy`/`invert` relation from evaluator
metadata; that field is absent from model messages. Some mappings rely on scenario
facts, not just grammatical polarity. A rejected equality, for example, does not
determine which side of a new threshold the value lies on. Gemma's 48/48 calculation
therefore characterizes transfer given the correct source labels and known relation;
it is not evidence that a verdict-only predictor using the actual visible input
achieved 48/48, or that retained rationales were unnecessary.

The numerical diagnostic and existing score-field names remain unchanged. The
confirmation account and future proposal now identify its privileged relation
access. A future operational comparator must infer consequences from permitted
visible text and retain warranted unresolved answers. The exact source-path audit
is `methods-review/memory-transfer-baseline-access-audit-v1.md` in the private store.

## Mistral catalog qualification labels

An input-only audit during Mistral collection found that the catalog bundle retains
the earlier Gemma `padding_qualification` field. It describes Gemma's calibration,
not the qualification of Mistral prompts. Mistral has a separate saved calibration
history, frozen before its prose generation, and 48 exact-prompt qualifications in
the final protocol's `context_qualifications` and `token_matching` records. All
matched inputs pass the 1% tolerance; the maximum absolute fractional residual is
0.000248047. The frozen protocol is unchanged. Actual generation input counts still
require their separate output-receipt audit.

The private `methods-review/s016-mistral-input-qualification-label-audit-v1.json`
binds both fields to the protocol and bundle hashes. Future bundle construction
should label calibration provenance by model to avoid treating an inherited
summary as the active qualification receipt.

## Legacy reading-note bindings

The first S-013 reading-note schemas lack six direct input or preserved-first-pass
hash fields used by later readings. Its retained comparison binds all four note
files and the export receipt; those bytes still match. Reader B's second pass also
binds the original output and evidence documents directly. The original notes are
unchanged. The closeout inventory records the absent links as explicit legacy
exceptions, rather than adding retroactive attestations. The reading procedure and
reported ordering remain documented; a later inventory cannot establish missing
historical before-evidence hash bindings. The private qualification is
`methods-review/s013-legacy-reader-binding-qualification-v1.json`.

## Catalog prose and NEXT extraction

The Mistral catalog audit found four titlecase `Next:` lines, one in each condition,
outside the frozen uppercase extractor. All 96 outputs are lexically scorable and
have one line under a case-insensitive diagnostic. Frozen word counts retain the
four titlecase lines. The two affected primary-condition responses have zero
phrase hits, so omitting their lines would leave their zero scores and the primary
contrast unchanged. The generic `catalog/valid` format counter falls back to prose
scorability and must not be read as a command-format or action-validity check.

The independent audit utility initially failed to serialize a Counter containing
both null and string NEXT keys. Its partial v1 output is preserved. A separately
named v2 utility uses value/count rows, preserving null distinctly, and serializes
before opening its output. Its full receipt/lexical audit passes. This utility
repair changes no generated response, frozen score or model-call disposition.

## Final scoring and closeout

The prospective closeout plan above was executed. All eight original scores and
their matched comparison were retained before integration. The final reviewed-v2
scores bind the scoring modules and annotations by hash. The exhaustive revision
diff verifies unchanged row identities, oracles, strict formats, dispositions and
frozen S-015 source labels; it records all field and summary differences.

Mistral S-015's original parser left 39 of 120 explicit verdicts unclassified.
A fresh output-only reader recovered all 39, with exact quotes and response hashes;
none required a correctness judgment. Semantic availability becomes 120/120,
while strict-format compliance remains 3/120. Three frozen source labels remain
null; the derived source-correctness field changes from false to null on their
thirty application rows. This is a missingness correction, not repaired source
content or a newly detected source error. The original report remains retained.

The private revision-diff utility initially passed single-change fixtures but
failed on actual repeated field names: `Counter.update` was given delta values
instead of field names. The exact original utility is retained. The one-line
repair and multirow regression cases passed, with 47 combined helper checks.
The actual eight-pair exhaustive comparison then succeeded. No model output,
score, primary endpoint or source oracle changed because of that utility repair.

Actual manifest assembly exposed a second helper issue: hashes of evidence
subsections were mistaken for whole-document hashes. The preserved assembler was
revised to distinguish whole-file bindings from component hash claims; twenty
scope and assembly checks passed, followed by successful actual assembly and
integrity verification. Component claims remain inside unchanged, hash-bound
reader notes but do not satisfy whole-file obligations and are not independently
reconstructed by this helper. Separate study audits perform their stated exact
prompt checks. No reader note was edited to make the inventory pass.

The [completed account](2026-10-24-introspection-confirmation.md) reports the final
versions, strict-format and available-pair denominators, qualitative limitations,
implementation tests and evidence-preservation record.
