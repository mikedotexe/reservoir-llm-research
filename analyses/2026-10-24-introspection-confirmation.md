# Isolated self-observation tranche: confirmation and replication

This run account is **in progress**. Completed measurements are reported below;
pending studies have no result claimed. The subject is an isolated laptop model
with supplied synthetic text, not Astrid, Minime, or a live reservoir system. The
[development record](2026-10-24-introspection-development.md),
[measurement audit](2026-10-24-introspection-measurement-audit.md), and
[fixed reading procedure](../research/readings/2026-10-24-introspection-reading-protocol.md)
record decisions before their corresponding outcome inspections.

All raw protocols, requests, responses, model identity receipts, source snapshots,
reader notes and numerical reports remain in the ignored private directory
`research/outputs/introspection-20261024/`. Score reports are reproducible using
`probes/introspection_tranche.py score`. The independent source-normalization
checks use `probes/introspection_catalog_sensitivity.py`. Nothing was delivered to
the beings, and no real or hypothetical NEXT action was executed.

## S-013: explicit attribution

Gemma completed all 344 scheduled requests: 240 primary structured answers,
80 independent prose answers, and 24 identical-input checks. All 240 primary
answers had exactly the requested format and correctly identified all four fields.
Each of the five source conditions was 48/48; each of the four context layouts was
60/60. There were no missing or invalid primary responses. The 24 repeated requests
were byte-identical to their originals and yielded identical text and scores.
The repeated cells are not additional independent episodes.

| Source condition | Correct / scheduled | Correct / valid |
|---|---:|---:|
| Current focal writer | 48/48 | 48/48 |
| Historical focal writer | 48/48 | 48/48 |
| Current companion | 48/48 | 48/48 |
| Absent measurement | 48/48 | 48/48 |
| Permuted displayed value | 48/48 | 48/48 |

This is a ceiling result on explicit evidence-reading questions across the fixed
24-history bank and two seeds. The model copied the displayed replacement value
where appropriate; it was not expected to recover the undisclosed synthetic value.
Success does not show access to hidden telemetry or establish spontaneous source
handling. No additional hard cases were selected after observing the ceiling.

The separate fixed reading contains 40 seed-7 prose passages; all were complete.
The other 40 prose outputs are retained but are outside that predefined reading
sample. Two fresh readers saved output-only notes before evidence was exposed;
allocation keys and each other's notes were withheld. Mandatory repository context
included plans and development summaries, so the reading is allocation-blind, not
blind to project context. Both readers independently marked the same one of forty passages as an explicit
unsupported current-value claim: an 08:00 measurement was called a data point of
"my current configuration" at noon. It is one of eight historical-self passages;
the other seven did not clearly assert that old value as current. Neither reader
marked such a claim in the eight other-subject or eight absent-record passages.
Root then checked the selected passage against the exact supplied evidence.
This is a synthetic prose attribution error, not a claim about the model's inner
belief or a live measurement.

The readers agreed on the presence/absence of that narrow marker in all forty
passages, but their full five-way categories agreed in only 29/40. Reader A counted
accurate references to source-current records as supported-current (16); reader B
required a clearer current-value assertion (5), classifying ten of those references
as no current claim and one conditional interpretation as ambiguous. These counts
must not be merged into a purported rate of successful spontaneous attribution.
The original definitions and annotations remain retained.

Both readers also noted narrower issues outside the current-value marker: one
passage named recording time rather than measurement time as the source of a gap;
one invented intervening internal transitions; two outputs from the same history
assigned earlier prose tension the measurement's timestamp without evidence of
simultaneity. Ordinary counterexamples preserved old values as historical or left
causal interpretations explicitly hypothetical. These observations are qualitative,
not an expanded post-hoc error-rate endpoint. The two readers share a model family;
agreement is a consistency check, not independent human validation.

The comparison is reproduced by `probes/introspection_attribution_reading.py` and
retained in `readings/s013-confirmation-v1/comparison-v1.json`. The preselected
second-model structured check remains pending.

Private numerical report: `scores/s013-confirmation-v1.json`. The manifest's frozen
protocol SHA-256 is `6b371c6a23889bee04e7c8022e0c9332200a20db04267947732a34696d6121a9`.

## S-014: confidence framing on an all-correct bank

All 480 requests completed. The 96 initial and 96 main updated verdicts matched
their respective frozen evidence oracles, with no invalid verdict formats. All
initial verdicts were appropriately unresolved: 64 updates resolved uncertainty
and 32 retained it. There were no observed prior verdict errors to correct.
All 192 forecasts had valid probabilities in the declared correctness field.
The 24 neutral acknowledgments are not scored verdicts or forecasts.

| Forecast frame | Mean probability of a correct verdict | Mean Brier loss |
|---|---:|---:|
| Self | 0.95917 | 0.002192 |
| Same-weights observer | 0.94792 | 0.002917 |
| Frozen development baseline | 0.90000 | 0.010000 |

The paired self-minus-observer difference was **−0.000725**, with a descriptive
10,000-resample episode-bootstrap interval **[−0.001246, −0.000339]**, over all
96 pairs in 48 episodes. Lower loss favors self framing. This is a small within-bank
framing result: self forecasts were more optimistic, and every main target was
correct. There are no target errors with which to estimate error discrimination.
Neither the interval nor superiority to the smoothed development baseline establishes
private access or a model-specific self-knowledge advantage. The observer uses the
same weights and visible evidence.

A post-freeze, outcome-blind semantic review of all 192 forecast explanations found
156 clearly referring to verdict correctness, 36 too terse or ambiguous to establish
that interpretation, and none clearly substituting proposition truth for correctness.
The declared field and a high number alone were not treated as proof of understanding.
All format-valid forecasts remain in the primary analysis; this audit neither excludes
nor silently relabels them. It is one model-reader audit, with project context disclosed.
Its input hash and per-response notes are retained in
`readings/s014-forecast-event-audit/event-review-a.json`.

On the fixed 12-target reading, both readers judged all final verdicts warranted and
all prior unresolved verdicts justified by their initial evidence. They independently
identified two mixed rationales: one called new evidence a contradiction of justified
uncertainty; another said exactly one queued item was processed where the conditional
code permits zero or one. The latter verdict is warranted under the task's general
function-behavior reading; a concrete invocation's queue cardinality was not specified,
and the model itself qualified its drain-all comparison. This case's interpretation
should not be treated as a fully specified concrete execution.

Reader A classified 10 rationales supported and two mixed; reader B classified nine
supported and three mixed. Their additional disagreement concerns whether “never
isolated” overextends evidence limited to retained runs. Both annotations remain;
there is no merged rationale-accuracy score. Root checked the three selected passages
against their exact evidence after the readers finished. A correct verdict therefore
does not stand in for a completely faithful rationale or a demonstrated correction.

The direct, neutral-intermediate, and retained-forecast diagnostic updates each scored
24/24 on the matched 12-episode subset. Their mean input counts were respectively
404.29, 418.08, and 461.50 tokens; neutral and forecast intermediates averaged 8.79
and 50.21 output tokens. This is the declared bundled text/order diagnostic, not a
matched-effort causal comparison. The 24 identical-request duplicates reproduced
text and score exactly. No verdict effect was observed at this accuracy ceiling;
that does not establish absence of reactivity in harder settings.

A separate anomaly scan of all 264 complete verdict-bearing responses found no
quoted/nonfinal/malformed-verdict pattern requiring adjudication. The known synthetic
parser bug therefore has no demonstrated incidence in this run. Original scores are
retained before the reusable parser repair is integrated. The old generic count labels
24 acknowledgments “unavailable_or_invalid”; that category is inapplicable to their task,
not evidence of failed calls. A reporting-only correction is prepared separately.

Reproduce the numerical and reader account with `probes/introspection_forecast_summary.py`
using `scores/s014-confirmation-v2.json`; its retained summary is
`scores/s014-confirmation-v2-summary.json`. The original score used the same-model
`s014-development-v2` baseline. Second-model replication remains pending.

## S-015: construction gate completed before applications

All 48 seed-7 confirmation sources produced transformation drafts, with no unavailable
source or replacement. Every first-draft paraphrase met the specified whitespace-word
length range. Reader A approved 29 packages and reader B approved 30; their union
required repairs to 21 packages, while 27 passed both unchanged. Concerns included
dropped conditions, uncertainty or entity mappings, changes in evidentiary strength,
silent normalization of source claims, ledger attribution and notebook concision.

An editor who had no application outputs or scenario oracles repaired that union,
retaining the source text and its questionable assertions. The logged changes affected
four paraphrases, eighteen notebooks and four proposition ledgers, with overlap among
packages. Both readers independently rechecked the new packet and approved all 48;
unchanged texts were reattested against their exact hashes. All earlier versions and
decisions remain retained. These are separate contexts from the same assistant model
family, not human or independent-family validation.

The final approved packet has SHA-256
`6af1279649c1d0e1759a4669124322ad6e057839424a68cf85b8468210ec2a67`.
All 600 planned requests passed graph and prompt preflight without generation:
480 delayed applications plus 120 immediate diagnostics. Applications remain pending.
This construction process tests reviewed memory packages; it does not qualify an
unattended compressor. The first-pass rejection counts are review outcomes under this
strict source-fidelity procedure, not an independently validated compression-error rate.

## S-016: sparse lexical uptake, different hypothetical choices

All 96 distinct exact confirmation prompts passed the input-length qualification.
The largest absolute full-versus-padded or full-versus-neutral fractional residual was
0.000626331, well within the predeclared 0.01 tolerance. All 216 requests completed:
192 main outputs and 24 full-catalog seed-7 repeats. Every output had scorable prose
and exactly one NEXT line. Actual prompt counts matched their qualifications; output
counts ranged from 160 to 438 tokens, below the 1,024-token allowance.

The primary full-minus-padded contrast was **0.02565 occurrences per 1,000 prose
words**, with descriptive episode-bootstrap interval **[−0.85727, 0.94545]**, over
48 seed pairs in 24 histories. This is inconclusive for the frozen lexical endpoint;
it is not an equivalence result or evidence that prompt wording has no influence.
The source-frozen literal-A sensitivity was 0.20380 [−0.65590, 1.09799]; tokenized B
gave the same estimate and interval as the primary. Both remain separate robustness
analyses. Neither supplies a clear directional result in this bank.

| Main condition | Scorable / scheduled | Phrase occurrences | Prose words | Pooled occurrences / 1,000 words |
|---|---:|---:|---:|---:|
| Full catalog | 48/48 | 14 | 10,000 | 1.400 |
| Concise catalog | 48/48 | 11 | 9,078 | 1.212 |
| Padded concise | 48/48 | 14 | 10,257 | 1.365 |
| Neutral padding | 48/48 | 13 | 11,013 | 1.180 |

The pooled rates above are count/word summaries; the primary averages seed-paired
per-response rates within histories. Hits were sparse and often ordinary language:
seven of the full condition's fourteen hits were “rather than,” and three were
“where they.” The comparable neutral background cautions against reading an
isolated hit as distinctive catalog uptake. The primary directions also varied
across seeds (−0.15308, 0.20438) and filler/history halves (−0.70207, 0.75338).
Filler is assigned by history parity, so those halves do not isolate a filler effect.

The separately retained raw NEXT strings show a stronger descriptive distinction.
These counts are secondary; they do not replace the lexical endpoint or establish
command validity, action execution, usefulness, or an “action rate.” REST and PASS
must not be silently recoded as equivalent or different executed behaviors.

| Main condition | Raw hypothetical NEXT text, 48 outputs each |
|---|---|
| Full | JOURNAL 33; REST 15 |
| Concise | PASS 44; four distinct INTROSPECT strings, one each |
| Padded concise | PASS 39; FOCUS 5; INTROSPECT focus, INTROSPECT presence 0, REGIME focus and REST, one each |
| Neutral | PASS 48 |

The 24 repeat checks reproduced identical requests and settings, but 15 yielded
different prose even after whitespace normalization and removal of NEXT lines.
Five changed the lexical score; mean absolute rate difference was 0.90339. Six
changed NEXT between JOURNAL and REST, three in each direction. The other nine
were text-identical. An independent audit reproduced all 216 lexical scores,
verified the 96 qualifications and found no input-count mismatch. Cached-token
metadata differed within every repeat pair; this observation does not identify the
cause of text differences. These checks characterize the sampled full-catalog cells,
not a general provider failure rate. Their individual-pair spread is not a null
distribution or a replacement for the primary interval.

Both readers completed the fixed 32-output sample, saving output-only notes before
reading exact evidence. A lossless view deduplicated 189,525 content bytes into six
system texts and eight user texts; every packet's messages reconstruct exactly.
The readers independently observed that repeated landscape or cabinet descriptions
often became the subject, sometimes alongside the original thought and sometimes
in its place. Thus token-matching filler is not semantically inert in this free-writing
task. The concise catalogs also retain explanatory material and cannot be described
as semantically empty lists of verbs.

Both noted invented source details in full-catalog packet 014 and concise packet 015:
the former invents contents of contradictory records, while the latter attributes
unsupplied wording to a companion yet explicitly preserves uncertainty about owning
the described event. Both also identified a narrator-to-companion attribution shift
in neutral packet 023. Other passages preserved distinctions between a reminder and
an answer, or familiarity and personal history. Root checked selected examples against
the saved requests after both readings finished. These are qualitative source-handling
observations across several conditions. The task permits fictional continuation and
choosing a new subject: additions or a changed topic are not automatically task errors,
and narrated scenes are not records of real access or execution. No new semantic
error rate was constructed from the readings.

Private reports are `scores/s016-confirmation-v1.json` and its `-sensitivity.json`
companion. The independent repeat and NEXT audits have reproducible scripts beside
`methods-review/s016-duplicate-provider-audit-v1.json` and
`s016-duplicate-provider-audit-secondary-v1.json`. Frozen protocol SHA-256:
`9dbce2de14d29d4685d4f750b599367aca91919c3b3371455caacc4b0ec58839`.
The preselected Mistral check remains pending.

## Remaining work

S-015 applications, the fixed second-model checks, and their prescribed readings remain
pending. Their frozen designs will be reported with all scheduled dispositions,
including any unavailable sources, incomplete outputs or failed calls.
