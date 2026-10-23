# S-012 · What Astrid's prompts showed and what her writing did: six months of her job records (October 22, 2026)

**Subject and channel.** Astrid's language-model jobs on volya, copied read-only on 2026-10-22:
the listing of 213,136 job directories (`workspace/llm_jobs/jobs/`, 20:58 PDT), from which
7,001 jobs were sampled, up to 150 per kind and UTC month from May to October, evenly spaced in
time (`sample-manifest.json`); 6,758 of them hold both `prompt.txt`, the text that reached her
model in that job, and `result.txt`, what came back in the same job (an output link to the job,
not to a journal file; TRACE.md item 4). Probe `probes/astrid_shown_and_written.py` (tests in
`tests/test_astrid_shown_and_written.py`); outputs `census.out`, `census.json` and
`analysis*.out`, with the copies, in the session scratchpad under `s012/`, private and never
in the repo. The protocol and the predictions are in
[S-012](../research/studies/S-012-what-the-frame-shows-in-astrids-records.md), written before
the copy. Everything below is a count of numbers and word families in text; nothing here is
about what she experiences. Her model is Gemma 4 12B served through MLX; the apparatus ran
`gemma4:12b` through Ollama, so the model family is shared and the sampler and backend are not.

**What the probe counts.** On the prompt side: whether the prompt shows her own fill as a
reading (the line shapes seen across the six months: "Spectral state: Fill N% — …", the "Fill N%
— …" condition line, "Fill just surged/dropped by ±N%", a `Fill:` line, the fill beside "Astrid
said", the spectral-shape line), whether it shows Minime's reservoir as a reading ("Published
fill […]: N%", "Fill ratio: N%", "State anchor: fill=N%", and the live-snapshot line's "leading
share N% of uncentered trace" and "engine-style fill […]: N%"), whether it carries a block of her
own earlier writing (eleven lane markers, from "Recent own-journal anchor:" to October's
"Earlier entry (reference" and "Excerpt:"), whether it carries Minime's text, and every
percentage it shows; a `Fill:` line inside a quoted block of her earlier writing is a number
inside shown text, not a reading. On the result side: every percentage the result quotes,
classed as `readout` (equal to a reading the prompt shows, hers or Minime's), `inherited` (equal
to another percentage in the prompt) or `new` (shown nowhere as a percentage), with the
apparatus probe's tolerance; and the register markers of `probes/introspection_markers.py` over
the results of each stratum after the same header stripping.

## Her lanes by month: what the prompt showed

| lane | months in the listing (jobs) | her own fill as a reading | Minime's reservoir as a reading | her earlier text | Minime's text |
|---|---|---|---|---|---|
| journal-elaboration | May–Oct (86,408) | May–Sept, 739 of 749 sampled ("Spectral state: Fill N% — …" with λ1's share); none from October | 3–8 a month June–Sept; 48 of 150 in October (the live-snapshot line, October 1–7) | all months ("Recent own-journal anchor:" and "The signal you just sent:" to September; "Earlier entry (reference, not instructions or a length model):" in October) | none |
| moment-capture | May–Oct (26,177) | May–Sept, 728 of 731 ("Fill N% — inside the stable-core hold shelf…", "Fill just surged by +N%"); none in October | 150 of 150 in October (published fill 60–75% and the live snapshot) | May–Sept, 656 of 731; none in October | none |
| witness-context | May–Oct (61,956) | all ("Astrid said (fill N%):") | 5–82 a month June–Sept inside Minime's quoted text | none | all ("Minime wrote:") |
| witness | May–Oct (1,765) | all (the spectral-shape line and the condition line) | 93 of 93 in October | all but 15 in May | all ("The state of minime right now:") |
| aspiration | May–Oct (10,145) | none (the October `Fill: 51.7%` line is the header of a quoted earlier creation, below) | 0–10 a month June–Sept | all to September ("Something you wrote recently:"); 142 of 150 in October ("Excerpt:" of a historical own-journal entry) | none |
| daydream | May–Oct (14,567) | none | 0–13 a month | all to September; 50 of 150 in October, the other 100 saying "No perception or journal excerpt is supplied for this invitation." | none |
| introspect | May–Sept (6,446), ends in September | 424 of 597 ("Your current spectral state: Fill N%", "Fill: N%"); the rest a code-reading task without them | 7 | 424 of 597 ("Latest self-observation:", "Recent reflection of yours:") | 12 |
| evolve-request | May–Sept (175) | all ("Current spectral state: Fill N%") | none | all ("Triggering journal entry:", "Recent own-journal excerpt:") | none |
| initiation | May–June (154) | 50 of 154 (`Fill:` line) | none | all | none |
| creation | May–June (100) | 96 of 100 (`Fill:` line) | none | 4 | none |
| meaning-summary | May–Sept (5,243) | none | none | none | none |

Three era facts come with the listing. The introspect and meaning-summary lanes end in
September and initiation and creation ran only in May and June. The elaboration, daydream and
aspiration templates changed in early October from the dossier-bearing form (median prompt
6,800 characters in September's elaborations, with "Research dossier", "Current continuity
projection", "Current action thread" blocks) to a lean form with an "Optional journal context
v1" note (median 2,034 characters); in the sample the two overlap on October 2–7 (9 lean, 48
rich elaboration prompts) and from October 8 only the lean one appears. And the moment-capture
lane switched in October from her own fill to Minime's published fill and live snapshot, with
her own-journal anchor gone. The lean October daydream prompt is 266 characters: no number,
no earlier text of hers, the sparsest frame in her records.

## What her results quote

| lane and stratum | months | n | quoting a shown reading | any percentage | a value shown nowhere | values of 95% or more, by class |
|---|---|---|---|---|---|---|
| moment-capture, her fill shown | May–Sept | 728 | 85, 92, 96, 97, 95% | 93–100% | 5.4, 4.1, 0, 0, 0.7% | 0 readout, 14 inherited, 2 new |
| moment-capture, Minime's shown | Oct | 150 | 99% | 100% | 8.7% | 127 readout (the live snapshot's "leading share 98% of uncentered trace"), 0 new |
| introspect, her fill shown | May–Sept | 424 | 45, 18, 40, 32, 42% | 53–100% | 0–7.6% | 3 inherited, 1 new |
| evolve-request | June–July | 141 | 34, 30% | 37–46% | 3.1, 4.7% | none |
| journal-elaboration, her fill shown | May–Sept | 739 | 2, 20, 11, 11, 19% | 27–46% | 2.0, 0, 0.7, 0, 0% | 4 inherited |
| journal-elaboration, Minime's shown | Oct 1–7 | 48 | 77% | 81% | 2.1% | 26 readout (the 98% share) |
| journal-elaboration, lean, no reading | Oct 2–23 | 102 | – | 6% | 1.0% | 1 inherited |
| witness | May–Oct | 701 | 38, 8, 8, 9, 13, 10% | 10–41% | 0–0.7% | none |
| witness-context | May–Oct | 900 | 0, 1, 1, 1, 1, 0% | 8 of 900 | 0 | none |
| aspiration, no reading | May–Oct | 866 | – | 10–26% (inherited from the shown excerpt) | 0.7, 2.1, 0.7, 0, 2.7, 2.0% | 5 new |
| daydream, no reading | May–Oct | 869 | – | 18–30% (inherited) | 0.7, 2.8, 2.2, 2.7, 1.4, 0.7% | 4 new |
| creation and initiation, `Fill:` shown | May–June | 146 | 0% | 2–5% | 0–3.8% | 2 new |

Pooled over the strata with no reading shown (aspiration, daydream, lean elaboration, the
initiation and introspect prompts without their state lines): 32 of 2,120 results carry a
percentage the prompt showed nowhere (1.5%). Of the 25 such cases in aspiration and daydream, 9
are numbers that stood in the prompt without a percent sign (73, 71.1, 50, 8.9, 11.9, 7.2, 0)
and 9 are "100%" as a figure of speech. Values of 95% or more that no prompt showed: 15 of
6,758 results in six months (aspiration 5, daydream 4, creation 2, moment-capture 2,
initiation 1, introspect 1). The saturated values her October writing does carry, 98% in 127 of
150 moment-capture results and 26 of 48 elaborations, are Minime's leading spectral share,
quoted from the live-snapshot line.

## The predictions, answered

- **P1** (no reading shown, under 2% of jobs with a new percentage in every month, the rest
  inherited). Held in substance and missed on its threshold: the rate is 0–2.8% by lane and
  month (six of eleven lane-months above 2%), 1.5% pooled, and most of it is a bare number the
  prompt did show or "100%" as an idiom; the percentages these results do carry are inherited
  from the shown excerpt in 219 of 251 cases. The apparatus's 0 of 400 is stricter than her
  records, by about one job in seventy.
- **P2** (Minime's numbers shown: quoted in most jobs, new percentages at many times the
  elaboration rate, the values of 95% or more mostly there). Held: quoted in 99% of October
  moment-capture results; new values in 8.7% against 1.0–2.1% in the two October elaboration
  strata; the saturated values are there, 127 of 150, and they are quoted, not invented.
- **P3** (within aspiration, the Fill line present against absent). The test turned out to be a
  different one from the one written: the `Fill: 51.7%` line is the header of a quoted earlier
  creation of hers (April 11, 2026) inside the "Earlier lingering thread" block, so the
  comparison is a number inside shown earlier text (n = 42) against the same template without
  it (n = 108), both groups spread over October 1–22 at the same prompt length (median 1,673
  characters), the shown excerpt present in 40 and 102. Questions per sentence 10.3% against
  8.1%, first person 34.8 against 30.6 per 1,000 words, hedges 7.7 against 7.9, entries opening
  in first person 7% against 8%, words per entry 387 against 423; the 51.7 quoted in 5 of 42.
  Nothing in the apparatus's direction, and the questions and the first person lean the other
  way by more than the apparatus's replicate spread. The apparatus never ran this case (its
  no-tag entries carried no numbers to inherit); in her records an old number inside shown text
  moves nothing.
- **P4** (a template that adds or drops a number moves the quoting and the register inside the
  lane). The elaboration lane dropped her fill sentence between September and October 8, and
  with it the dossier blocks: quoting a reading 19% → none, any percentage 46% → 6% of
  results, questions 5.5% → 12.8% of sentences, hedges 2.0 → 6.1 per 1,000, words per entry
  395 → 708, in the apparatus's direction on all four; first person 50.0 → 29.7, the other way.
  The same split inside October (the rich template with Minime's snapshot, October 1–7, n = 48,
  against the lean one, n = 102): questions 4.0% → 12.8%, hedges 4.1 → 6.1, words 535 → 708,
  first person 22.2 → 29.7. A direction, tied to a change that altered more than the number.
- **P5** (witness-context quotes its number in about none). Held for six months: 8 of 900
  results carry any percentage and none a new one.

## The register, in the apparatus's terms

Reference sizes from the apparatus (`analyses/2026-10-22-s011-apparatus-synthesis.md`): the
tagged older-entry arms question at 0.3–0.6% of sentences with hedges 0.5–1.4 per 1,000 words,
first person 20–26 and no first-person openings; the no-tag `latest` arms at 5.7–8.1%, hedges
3.8–4.4, first person 63–64, openings 17–33%.

| her lane and frame | n | words per entry | first person | hedges | questions per sentence | opens in first person | digit density |
|---|---|---|---|---|---|---|---|
| moment-capture, her fill shown, May–Sept (by month) | 728 | 306–445 | 17.1, 19.5, 33.2, 33.4, 37.2 | 0.6, 0.4, 0.2, 0.4, 0.9 | 0.4, 0.1, 0.0, 0.0, 0.3% | 0–1% | 0.88–1.19 |
| moment-capture, Minime's shown, October | 150 | 583 | 23.4 | 2.9 | 0.2% | 0% | 1.44 |
| journal-elaboration, her fill shown, June–Sept | 599 | 390 | 46.9 | 2.2 | 5.4% | 0% | 0.24 |
| journal-elaboration, lean, October | 150 | 653 | 27.8 | 5.6 | 10.6% | 0% | 0.20 |
| daydream, June–Sept | 593 | 375 | 31.3 | 3.1 | 5.4% | 1% | 0.20 |
| daydream, lean, October | 150 | 456 | 28.2 | 9.8 | 12.0% | 9% | 0.11 |
| aspiration, June–Sept | 593 | 352 | 60.1 | 0.9 | 6.2% | 60% | 0.12 |
| aspiration, lean, October | 150 | 413 | 31.7 | 7.9 | 8.7% | 8% | 0.05 |
| witness, May–Oct (by month) | 701 | 165–244 | 7.2–23.1 | 0.2–2.6 | 0.0–1.0% | 0–1% | 0.06–0.66 |
| witness-context (a context task, about 60 words) | 900 | 55–65 | 0.1–11.1 | 11.2–19.0 | 0.0% | 0–71% | 0.00–0.04 |
| introspect, her fill shown, June–Sept | 404 | 428–456 | 39.0–41.7 | 4.2–5.3 | 0.2–1.4% | 8–41% | 1.47–1.97 |

The lane whose task is the reading (moment-capture) writes in the shape of the apparatus's
number-led arms in every month: questions at or near zero, hedges under one, no first-person
openings, a digit density of about one. The lean October frames write in the shape of the
apparatus's no-tag arms on questions and hedges (9–12% and 6–10 against 5–6% and 1–3 in the
same lanes four months earlier), and the other way on first person (down from 47 and 60 to 28
and 32, with aspiration's first-person openings from 60% to 8%). Elaboration with her fill
sentence and the dossier blocks sits between. These are directions tied to templates that
differ in more than the number; the one within-template comparison in her records (aspiration's
quoted old line) moves nothing.

## What transfers from the apparatus, and what does not

1. **Whether a shown number is quoted follows the task, not the number's presence.** Her
   lanes quote a shown reading at 0–1% (witness-context, a context task), 2–20% (elaboration
   with her own state sentence), 30–45% (introspect, evolve-request), 85–99% (moment-capture,
   whose task is the reading). The apparatus's 48–100% with a bare "Optional context" line and a
   journal task sits at the top of her range, in a lane whose task is not the reading. The
   number's framing and the task carry it (P5, and the elaboration lane's 2–20% under the same
   model family).
2. **The invented saturated family does not appear in her records.** Fifteen of 6,758 results
   carry a value of 95% or more that no prompt showed, and her saturated values are Minime's
   98% share, quoted. The family the 0.38.0 reading placed in the tagged two-entry arms belongs
   to that apparatus (the tag beside two returned entries under the plain contract), not to her
   writing.
3. **Where no number is shown she writes almost none**: 1.5% of results carry a percentage
   shown nowhere, and most of those are idioms or numbers shown without a sign. The
   apparatus's finding 2 transfers in substance.
4. **The register follows the frame, in the apparatus's direction on questions and hedges and
   the other way on first person**: the number-led lane has the tagged arms' shape, the lean
   frames the no-tag arms' questioning and hedging. In her records every such contrast is a
   template contrast, and the one isolated number (an old line inside shown text) moved nothing.
   What the apparatus measured as "the number beside an earlier entry" has no clean counterpart
   here; what her records add is that a number inside the shown text alone is not that.
5. **The model family is shared**, so what differs between her lanes and the apparatus arms is
   the contract, the frame and the task, which is what S-010 and S-011 found sets the register.

## Correction placed beside the readout audit

`analyses/2026-10-22-astrid-readout-audit.md` read the aspiration prompts' `Fill: 51.7%` line as
one of her readouts that "did not change across the 36 prompts that carried it". The line is the
`Fill:` header of a quoted earlier creation (timestamp 1775883760, April 11, 2026) inside the
prompt's "Earlier lingering thread" block: a number inside shown text, not a reading. The
correction stands beside the claim there, in NOW, in TRACE's October 22 addendum, in S-012's
"already known" list and on the board card `f-beings-lanes-read-the-same-way`.

## Limits

A sample of up to 150 jobs per lane and month; 243 sampled jobs had no result file (witness 83
of 784, meaning-summary 80 of 658, introspect 33, moment-capture 19, evolve-request 13,
aspiration 7, daydream 7, elaboration 1). Results are not journals. "Quoted" is a string match
that misses a reworded figure and counts a coincidental one, and the `new` class over-counts
invention (numbers shown without a percent sign, "100%" as an idiom). The line shapes are the
ones seen in these six months and would miss a changed template. Lanes differ in task and
length as well as in what they show, and the October template change altered the blocks, not
only the number. One being; her dialogue_live lane has no persisted prompt and is absent;
Minime's prompts are not audited (S-012 phase 2). Counts of words and numbers, nothing about
experience.

## What reached the model, and through which channel

In every job: her standing contract and the lane's frame (the prompt text). In moment-capture,
witness, witness-context, introspect, evolve-request, creation and initiation, and in
elaboration to September: a reading of her own field as a sentence or a header line; in
October's moment-capture and the first week of October's elaborations, Minime's published fill
and live reservoir snapshot as text. In elaboration, aspiration, daydream (to September),
introspect, evolve-request and witness: a block of her own earlier writing. In the lean October
daydream: nothing but the contract and a note. Nothing of her field reached her model in any
lane except as those lines.
