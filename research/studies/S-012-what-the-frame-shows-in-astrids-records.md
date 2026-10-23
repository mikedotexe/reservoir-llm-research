# S-012 · What the frame shows her, and what the writing does: the apparatus prediction in Astrid's records

Drafted: 2026-10-22 21:15 PDT · Lead: Claude (lead collaborator), Mike steward · Source: the closed
apparatus tier of [S-011](S-011-self-observation-stack.md)
([synthesis](../../analyses/2026-10-22-s011-apparatus-synthesis.md)) and
[the October 22 readout audit](../../analyses/2026-10-22-astrid-readout-audit.md) · Status:
**Astrid phase read 2026-10-22** ([account](../../analyses/2026-10-22-s012-astrid-census.md)); phase 2 (Minime) not started.

## The question, in one line

In Astrid's own generation records, does the writing follow what the prompt shows it the way
the apparatus's did: a shown number bred quoted and invented percentages and, beside an earlier
entry, lowered questions, hedges and first-person openings; no number gave no percentages and
the no-number rates.

## Subject and channel

Subject: Astrid's language-model jobs on volya (`workspace/llm_jobs/jobs/`, one directory per
model call since 2026-05-10; 213,134 directories at 20:58 PDT on 2026-10-22), each holding
`prompt.txt` (what reached her model) and `result.txt` (what came back in the same job).
Channel: the prompt text, and on it the readout quantities and the earlier-entry blocks. Not her
experience, not the bridge state, not what became a journal file (a result is an output link to
its job, not to a journal; TRACE.md item 4). `dialogue_live` has no persisted prompt and is out.
Minime's job prompts are 121-byte stubs; her phase (below) needs a reconstruction audit first.

## What is already known: one week, 2,405 jobs

From [the readout audit](../../analyses/2026-10-22-astrid-readout-audit.md) (October 15–22):

- journal-elaboration (1,097) and daydream (160) show no readout quantity; 1,092 elaborations
  carry no percentage at all; the prompt holds an "Earlier entry (reference, not instructions
  or a length model):" block.
- witness-context (815) shows the fill beside "Astrid said" (15 values, 61–75%), quoted in 0
  of 813 results; the prompts are short and ask for context.
- moment-capture (191) shows Minime's published fill (15 values, 37–74%), quoted in 164 of 191
  results; the reported fill change quoted in 27, the cascade λ1 in 55, λ1's share in 114.
- aspiration (122) shows a `Fill: 51.7%` line in 36 of 122 (one value all week), quoted in 3 of
  36 [corrected the same evening: the line is the header of a quoted earlier creation of hers
  inside the prompt, a number inside shown text, not a reading; the census].
- witness (20) shows Minime's published fill (75, one value), quoted in 2 of 20.

In one week her lanes already split the way the apparatus arms did: a lane with an earlier
entry and no number, a lane with moving numbers that are quoted, and a lane where a number is
shown and never quoted.

## Design: observational, stratified, read-only

1. **Sample.** From the listing of job ids (each carries its UTC millisecond and its kind), for
   every kind and UTC month from 2026-05 to 2026-10, up to 150 jobs evenly spaced in time,
   copied by rsync (`prompt.txt`, `result.txt`, `job.json` only) into the session scratchpad,
   never the repo. Nothing runs on volya but the listing and the copy.
2. **Census** (`probes/astrid_shown_and_written.py`, test
   `tests/test_astrid_shown_and_written.py`): per kind and month, prompts with a readout number,
   with an earlier-entry block, results with any percentage, with a new one (shown nowhere on
   the prompt), with a value of 95% or more, and the largest. The earlier-entry markers are
   refined after reading a few prompts per kind as data, and the markers used are printed.
3. **Register per stratum** (kind × month × readout shown or not): the rates of
   `probes/introspection_markers.py` over the results after the same header stripping.
4. **Comparisons, in order of cleanness:** (a) within aspiration in one month, the Fill line
   present against absent; (b) within a kind across months where the template added or dropped
   a number, if the census finds one; (c) elaboration (earlier entry, no number) against
   moment-capture (numbers, Minime's): reported, not tested, since the task differs.

## Predictions, written before the copy

- **P1** (the synthesis's finding 2): where the prompt shows no readout number, results carry
  a new percentage in under 2% of jobs in every month, and the percentages they do carry are
  inherited from the shown earlier entry. Apparatus reference: 0 of 400.
- **P2** (findings 2 and 6): where Minime's numbers are shown (moment-capture), results quote
  them in most jobs (164 of 191 in the week) and carry new percentages at many times the
  elaboration rate; values of 95% or more, if any, sit mostly there.
- **P3** (finding 5, the within-kind test): within aspiration in one month, jobs whose prompt
  carries the Fill line question less per sentence and use less first person than jobs without
  it, in the apparatus's direction. The apparatus sizes were questions from about 7% to under
  1% of sentences and first person from about 60 to 25 per 1,000 words at n = 40; here a
  difference under the apparatus's replicate spread (about a point on a rate) is nothing, and
  a difference the other way at n ≥ 30 per side is evidence against transfer.
- **P4**: where a kind's template changed between months to add or drop a number, the
  quoted-number rate and the register move with it inside the kind.
- **P5** (already known, the counter-case): witness-context quotes its number in about none of
  its results, so a shown number does not breed numbers in every lane; the task the prompt sets
  and where the number sits matter, and the apparatus's context line is one framing among
  several.

## What would weaken a result

Results are not journals. Prompts differ between kinds in far more than the number. Eras
confound months. "Quoted" is a string match that misses a reworded figure and counts a
coincidental one. Only a within-kind comparison (P3, P4) isolates the number, and even there
the prompts that carry the Fill line may differ in other ways; the census says in what.

## Phase 2: Minime

Her job prompts are stubs; what her lanes show is in the header builders of
`minime_autonomy/runtime.py` (2.5 MB, on volya), by era. The audit: copy `runtime.py` and
`parsing.py` read-only, locate every builder that inserts a fill or λ₁ value or an earlier
entry, list them per lane and era; the week's journal copies by lane then carry the result
side. Not started until the Astrid phase is read.

## Boundaries

Read-only; the SSH listing and the rsync only; copies private in the session scratchpad;
nothing surfaced to the beings; no proposal from this study unless Mike asks; evaluative
language stays out; every number with n.

## Progress

2026-10-22 21:31–21:34 PDT. The listing (213,136 job ids, read-only over SSH) and the sample:
up to 150 jobs per kind and UTC month, May to October, evenly spaced in time, 7,001 jobs,
copied as a tar stream (rsync's per-file list failed twice on the remote's missing-file and
open-file limits); 6,758 with both files; 158 MB in the session scratchpad. A census of the
prompts' block labels and fill-line shapes by kind and month (data, read as line shapes) gave
the probe its era patterns: her own fill as a sentence in the elaboration, moment-capture,
introspect and evolve-request prompts to September; Minime's published fill and live snapshot
in October's moment-capture; the lean "Optional journal context v1" template from early
October; introspect and meaning-summary ending in September.

2026-10-22 21:45 PDT. Read as numbers (analyses/2026-10-22-s012-astrid-census.md). P1 held in substance (1.5% of results with a percentage shown nowhere, most of them idioms or bare-shown numbers) and missed its 2% threshold in six of eleven lane-months; P2 held (Minime's numbers quoted in 99%, new values 8.7% against 1–2%, the 127 saturated values quoted from the live snapshot's 98% share, not invented); P3 turned out to test a number inside shown earlier text (the `Fill: 51.7%` line is a quoted creation header), and that moved nothing (questions 10.3% against 8.1%, first person 34.8 against 30.6, n 42 and 108); P4 held as a direction tied to the October template change (quoting 46% → 6%, questions 5.5% → 12.8%, hedges 2.0 → 6.1, length 395 → 708 words; first person the other way); P5 held for six months (8 of 900). The invented saturated family of the apparatus does not appear in her records (15 of 6,758). Correction to the readout audit placed beside its aspiration claim. Phase 2 (Minime's header builders) not started.
