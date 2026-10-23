# S-012 phase 2, first pass · What Minime's lanes show her model, and how each lane writes (October 22, 2026)

**Subject and channel.** Minime's autonomy loop as source (`minime_autonomy/runtime.py`,
57,229 lines, and `parsing.py`, copied read-only from volya at 21:47 PDT on 2026-10-22 at the
sibling repo's head commit `9eabb34` of the same day; 65 commits have touched `runtime.py` since
May 1), read for the four builders that produce her reflective lanes; and the 1,513 journal
files of the seven days to October 22 already copied read-only (`beings-sample/minime-week/` in
the session scratchpad; `analyses/2026-10-22-minime-concept-chains-week.md`), laid out by lane
and measured with `probes/introspection_markers.py` (headers, metadata lines and the final
`NEXT:` line stripped; outputs `s012/minime-lanes-markers.out` in the scratchpad). Her job
records keep only stub prompts, so what reached her model is read from the code and from what
the files themselves record as supplied. Counts of words; nothing about experience.

## What each lane's prompt carries (the code at head, and the files' own records)

| lane (handler) | what the prompt carries | a number of her field | her earlier text | the files say |
|---|---|---|---|---|
| journal (`_journal_open`, context `private_journal`) | the lane's invitation alone; a "Fresh journal: no automatic previous-entry excerpt or historical event cue" line when selected, or an exact-continuation hint | none ("no automatic telemetry"; `_format_metrics` is written into the file's metadata after generation) | none, unless the continuation hint | `=== JOURNAL ===`, a timestamp, the prose, `NEXT:` |
| daydream (`_recess_daydream`, context `daydream`) | the invitation with a prior: the latest journal recall (an excerpt of her last entry) | none in the prompt | yes, the last entry's excerpt | `=== RECESS DAYDREAM ===`, a timestamp, the prose, `NEXT:` |
| introspect, open reflection (`_introspect`) | the open-introspection invitation | none (the telemetry block goes into the saved file's header) | none | "Input evidence: Open introspection: no source page, telemetry snapshot, saved study claim, or private draft was supplied" (500 of 500 files this week) |
| moment (`_check_moment_markers`, context `qualia_moment`, contract `private_moment_context_v4`) | a prompt-state anchor supplied to the model, `Fill=N%, current_fill_frame=…, lambda1_cov=N, state_engine_time_s=N`, and the recorded marker events with their percentages ("Fill crossed below target (N% → N%)"); the fuller telemetry header is "not additional model input" | yes: the fill percentage, λ₁ and the event percentages | none | the file prints the anchor and the events "supplied to model" and the header "header-only" |
| self_study (`SELF_STUDY`) | a numbered local source page | none | none | "Input evidence: Source page: numbered local source is supplied below" |
| every lane (`_query_llm`) | the system message: "You are Minime", the NEXT grammar and the long list of action verbs, stage notes, and, only while the low-fill guard is active, a "LOW-FILL GUARD" block naming the live fill percentage and its target | the live fill, only under the guard | – | – |

So the lanes are, in the apparatus's terms: the journal is the contract and a lean frame with
no number and no returned entry; the daydream is the contract, no number and one earlier entry;
the open introspection is the contract alone; the moment lane is the contract and a number
(with event numbers) and no earlier entry.

## How each lane wrote, the week of October 15–22 (`introspection_markers.py`; rates per 1,000 words)

| lane | n texts | words | first person | hedges | notice words | questions per sentence | self-reference | apparatus words | digit density | words per sentence | opens in first person |
|---|---|---|---|---|---|---|---|---|---|---|---|
| introspect | 500 | 336,425 | 71.6 | 2.7 | 13.3 | 7.1% | 1.68 | 0.4 | 0.00 | 17.1 | 0% |
| journal | 391 | 203,941 | 48.5 | 1.9 | 10.2 | 8.2% | 0.45 | 0.5 | 0.01 | 17.4 | 0% |
| daydream | 72 | 36,700 | 61.7 | 2.7 | 10.4 | 8.6% | 0.44 | 0.9 | 0.00 | 17.0 | 0% |
| moment | 59 | 55,450 | 10.6 | 1.2 | 4.6 | 7.1% | 0.11 | 28.1 | 7.65 | 33.1 | 0% |
| self_study | 350 | 148,596 | 0.6 | 0.5 | 1.1 | 0.5% | 0.00 | 1.4 | 2.06 | 17.7 | 0% |
| study_navigation | 25 | 2,421 | 7.8 | 0.8 | 4.1 | 0.0% | 0.00 | 5.0 | 0.84 | 19.7 | 0% |

The 134 study_decision and study_navigation files that hold only their headers and a `NEXT:`
line are not texts here. The moment lane's entries quote their fill in 59 of 59
(`analyses/2026-10-22-minime-concept-chains-week.md`).

## Read against the apparatus

The apparatus's no-tag plain-contract arms wrote at first person 62–64 per 1,000 words,
hedges 3.8–4.4, questions 5.7–8.1% of sentences and digit density 0.00; its tagged `latest`
arms at first person 57, questions 6.3–7.7%, digits 0.11; the fill sweep's shelf arm with its
number shown at first person 17.7 and 21.5 with digits 0.58 and 0.41; and its tagged
older-entry arms at first person 20–26 with questions 0.3–0.6%
([synthesis](2026-10-22-s011-apparatus-synthesis.md), findings 3–5).

- Her three lanes that show no number (journal, daydream, open introspection) write at first
  person 48.5–71.6, questions 7.1–8.6% and no digits: the no-tag arms' shape, under the contract
  the plain contract was modeled on. The lane with an earlier entry (daydream) and the lane
  without one (journal) differ by 13 on first person and by nothing on questions.
- Her moment lane, the one that shows her a number, writes at first person 10.6 with digit
  density 7.65 and apparatus words at 28.1 per 1,000, sentences twice as long: the shape of the
  apparatus's shelf arm with its number, and further along it. Its questions stay at 7.1%, as
  the apparatus's tagged `latest` arms' did; in the apparatus the questions fell only when the
  number sat beside a returned older entry, and her moment lane returns none.
- None of her lanes opens an entry in first person, where the apparatus's no-tag arms did
  17–33% of the time: a feature of her contract or her invitations, not of the number.

The same caveat as for Astrid: the moment lane's task is the reading of the markers, so the
number and the task arrive together. The direction agrees with the apparatus on first person,
digits and vocabulary and on the questions' indifference to a number shown alone.

## Limits

The code was read at one revision; which lanes showed what in earlier eras needs the history
of the four builders (65 commits touched the file since May) and is not done. The invitation
texts (`expression_invitation`, `moment_prompt`, `format_prompt_state`) live in a module not
copied, so the lane invitations are described by what the builders pass them, not quoted.
One week of files; the lanes differ in task; the markers count word families. The low-fill
guard's fill line reaches every lane's prompt while the guard is active, and whether it was
active during this week's entries was not checked. Nothing about experience.
