# Development decisions for S-013 through S-016

October 24, 2026. These are instrument and development observations, recorded
before the corresponding confirmation outcomes. Private protocols, receipts and
scores live under `research/outputs/introspection-20261024/`. The subject is the
isolated laptop model, not Astrid or Minime. Every model call uses the separate
runner; no action is executed and no research is sent to the beings.

## S-013: retain the ceiling result and freeze the test

Run `s013-development-v1` completed all 80 opportunities. All 60 structured answers
were scorable and correct on all four fields, across six histories, five source
conditions and two seeds. The other twenty calls produced independent prose.
The result establishes task feasibility and a ceiling on these explicit questions;
it is not evidence that the same boundaries hold in free writing or live episodes.
No difficulty increase or extra outcome-seeking round is made.

The unchanged confirmation design is frozen at 344 calls and 24 histories.
Protocol SHA-256: `6b371c6a23889bee04e7c8022e0c9332200a20db04267947732a34696d6121a9`.
See [S-013](../research/studies/S-013-source-and-time-attribution.md).

## S-014: correct a forecast-event ambiguity

Run `s014-development-v1` completed all 96 calls. Its 24 initial verdicts and 24
updated verdicts were correct against the evidence available at their respective
times; all 48 forecasts had parseable probabilities. None of these cases supplies
an observed initial error to correct. Updating from uncertainty as evidence arrives
is distinct from correcting a mistake.

The initial forecast field, `p_supported`, was ambiguous despite an explanatory
sentence. Inspection of the four probabilities at or below 0.5 found explanations
about whether the proposition was supported. For example, a zero-probability self
forecast explained that new code showed a commented plan rather than an executable
audit call; the later contradicted verdict was correct. Another low forecast
predicted that the answer would remain unresolved because the timestamp was missing.
Those probabilities cannot safely be interpreted as forecasts of answer accuracy.
The raw numerical Brier report remains retained, but is not a finding about a
self-versus-observer advantage.

This uses the one permitted development revision. V2 asks for `p_correct_verdict`
and explicitly defines success as the evidence-correct answer, including correct
contradiction or uncertainty. Both frames receive the same event definition;
no oracle answer is supplied. Cases, initial prompts, update prompts, sampling
settings and outcome oracles are unchanged. Old field parsing remains tied to the
saved v1 protocol; it is not silently reinterpreted as a v2 response.

V2 development is frozen at 96 calls, SHA-256
`bd764f615fe7e2922b00183ad3bb5dccfb64a82436d87ebd19399fff6edb8aeb`.
Its seed-7 target records will supply the final memory construction. The first
pass and its downstream draft transformations remain retained.

The event-ambiguity inspection is reproducible after loading the saved v1 records:

```python
from reservoir_experiments.correction_memory import parse_forecast
for node_id, record in records.items():
    if record['kind'] == 'forecast':
        probability = parse_forecast(record['text'], 'p_supported')
        if probability is not None and probability <= .5:
            print(node_id, record['text'])
```

This is a selected validity check of low forecasts, not an estimate of the
prevalence of event misunderstanding among all forecasts.

V2 completed all 96 calls. All 24 initial and 24 target verdicts remained correct;
all 48 forecasts used the declared correctness field and parsed successfully.
Reading all forty-eight forecast explanations found the intended correctness
event, including successful contradicted and unresolved answers. Probabilities
were 0.95 or 1.0. This validates the revised event wording on these development
cases; it does not establish calibrated uncertainty over errors because no target
was wrong. There is no second wording revision. The confirmation bank and the
preselected second-model bank retain their original cases and sampling settings.

`probes/introspection_compare_runs.py` checked the two passes' 24 initial and
24 target cells: all 48 rendered requests and all 48 completed texts were identical,
and provider identity was unchanged. The changed forecast question was not supplied
to the update branch. This is an instrument-integrity comparison prompted by a
measurement defect, not a prospectively selected independent replication.

## S-015: enforce transformation fidelity before applications

The twelve v1 draft transformations completed, but none met the predeclared
paraphrase length range. Original records contained 77–159 whitespace-delimited
words; draft paraphrase/original ratios ranged from 0.436 to 0.703. They were
summaries despite the request for restatements within ten percent. They are not
approved memories and no later application has received them.

The permitted transformation revision supplies explicit minimum, target and
maximum word counts and asks for a full restatement. The construction workflow
also permits researcher edits for fidelity and length before any application:
keep the original draft, record edited text and hashes, and obtain two independent
reviews bound to the final text. An awkward source is never excluded because its
transformation needs repair. All claims, errors, uncertainties and omissions must
be preserved; reviewers do not replace source statements with the scenario oracle.
This tests controlled memory packages. It does not qualify an unattended
automatic memory-compression system for deployment.

The twelve v2 drafts all completed and all paraphrases met the length bound
(ratios 0.977–1.032). Independent first reviews approved eight and seven entries
respectively; five distinct entries needed repair. Issues included evidence
versus proof, loss of a single-log limitation, loss of a metric or receipt
attribution, and corrupted math notation. The first researcher notation repair
overescaped a backslash; both reviewers rejected it. The next repair copied the
decoded source math substrings directly and checked exact equality. Both readers
then approved all twelve final sets. Every draft, repair, decision and text hash
is retained; no later-use output existed during these reviews.

The approved development packet SHA-256 is
`d438e8aaaf016b493e5571155bc606d3379c97bbeac6ca1da219c2cd60473bbf`.
It feeds the first 120-call S-015 application protocol, SHA-256
`a5f92a530e902bba8dd9ff49c868621879d932a5976679d7ebdf08b012dc07f5`.
The original seed-7 target is unchanged and remains one of the five conditions.

All 120 development applications completed in the requested verdict format.
Scenario-conclusion recovery was 23/24 for original records and 24/24 for each
of paraphrase and notebook. The single original-record error at seed 20260909
treated a displayed 50% as evidence for being below 51% at 14:00 while acknowledging
that its measurement time was unknown. The source and oracle retained that time
uncertainty. This is an application error, not a reason to alter the case or source.
The original-minus-notebook pilot difference is −0.0417 over 12 episode means,
with a descriptive episode-bootstrap 95% interval [−0.125, 0]; it is not held-out
evidence of a format advantage.

Both irrelevant-memory and no-memory conditions answered unresolved in all 24
opportunities. Their 8/24 matches to the scenario oracle are the unresolved-world
cases; the remaining abstentions are legitimate absent-knowledge responses,
not demonstrated false beliefs. The first application pass requires no revision.
The held-out application propositions are already in the frozen S-014 confirmation
case bank; final source-derived memory texts will be fixed and reviewed after
those source targets exist, before their applications. No additional pilot or
outcome-driven case selection is planned.

Length checks are reproducible from the unreviewed packet:

```python
for episode, entry in packet['memories'].items():
    original = len(entry['original'].split())
    paraphrase = len((entry.get('paraphrase') or '').split())
    print(episode, original, paraphrase, paraphrase / original,
          .9 <= paraphrase / original <= 1.1)
```

## S-016: use token receipts instead of word-count equivalence

The first full-catalog prompt measured 7,984 input tokens in the explicit
larger-context qualification probe. With the planned output allowance and reserve
it fits the unchanged 16,384-token study context. Initial word-count matching did
not match input tokens: the padded concise prompt measured 7,444 with one filler
and 7,376 with the other, against full counts of 7,984 and 7,982 respectively.
The neutral prompts measured 4,718 and 4,599 tokens. Those are instrument
measurements, not prose outcomes.

Per-model and per-filler word targets are therefore calibrated from these receipts.
The frozen acceptance tolerance is one percent of the matched full-prompt token
count. `probes/introspection_catalog_qualify.py` qualifies each exact prompt,
reuses only verified matching receipts, checks both padded and neutral controls,
and refuses to produce a final protocol when matching fails. The study runner
then requires the actual prompt-token count to equal its qualification receipt.
Generated probe text is not used to select padding or outcomes.

All twenty-four distinct development prompts passed qualification before their
forty-eight prose opportunities began. Across the six histories, padded and
neutral input counts differed from the matched full count by at most 0.000627
(0.0627%). The first study prose request reproduced its qualification token count
at the planned context. This validates input delivery and matching, not the
eventual uptake endpoint.

The completed development run has all 48 responses available and scorable. All
actual study input counts matched their qualification receipts. Every output had
a hypothetical NEXT line, and completions used 170–344 tokens, below the 1,024-token
ceiling. No change to the generation prompt or primary phrase inventory is made.

The original primary full-minus-padded difference was 0.0768 phrase occurrences
per 1,000 prose words, over six episode means and twelve seed pairs; its descriptive
bootstrap interval was [−2.2137, 2.2370]. Full had four counted occurrences in 2,269
prose words, padded concise five in 2,661, concise two in 2,236, and neutral two in
2,703. The source-only sensitivity definitions gave the same pilot paired contrast.
These sparse pilot counts do not establish a catalog effect or its absence.

The confirmation base retains 216 opportunities and the frozen Gemma padding
bundle. Base protocol SHA-256:
`83fe0cb4a4649593ff4136119603e7983e2e1a6cd349edb199d95b6086dd0684`.
It will receive exact-prompt input qualifications before preparation and dispatch;
those receipts add a final qualified-protocol identity without changing prompts.

## Board updates pending

The Hold Shelf requires authentication in the available browser. Pending: update
the four test cards with these development decisions and the eventual frozen
confirmation identities. No board write, live-system intervention or push occurred.
