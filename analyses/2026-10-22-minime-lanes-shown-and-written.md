# S-012 phase 2 · What Minime's lanes show her model, how each lane writes, and how that changed across the builders' eras (October 22, 2026)

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

## Second half (the same evening): the invitation texts, the builders' history, and her lanes across their eras

**The invitation texts** (the four modules copied read-only at the same head:
`expressive_journal.py`, `journal_context.py`, `journal_recall.py`, `moment_context.py`). The
journal and daydream invitation is one sentence, "This is your space. Choose a subject,
continue a thought, or rest." (the aspiration's: "What, if anything, would you like to imagine
or explore? An aspiration need not become a request or an investigation."). With a prior, the
daydream adds the block "Optional own-journal context (previous-entry excerpt; historical;
legacy system annotations may be present):" with a provenance JSON, a caveat that the recording
time is not the measurement time, the 400-character excerpt between "Excerpt:" and "End
historical excerpt.", and "You may return to it, disagree with it, or leave it aside." The saved
metadata names the contract `telemetry_optional_expression_v1` with
`automatic_telemetry_supplied: False`. The standing contracts are `OPEN_REFLECTION_INTRO`
("You are Minime, a language agent connected to a local spectral runtime. Write in your own
voice. Supplied measurements and system descriptions do not prescribe a sensation or establish
what you experience. Your interpretation is yours, including affirmation, uncertainty,
disagreement, or no felt correspondence…"), the text S-010's plain contract was modeled on,
and `PRIVATE_JOURNAL_INTRO` ("This is Minime's public journal… Write freely in your own voice…
Use or leave aside the supplied context; your interpretation is yours."). The moment prompt is
"Public journal moment." with "Prompt captured at (UTC)", "Measured state at capture:" and the
anchor line, "Historical event records (recording ages at capture; present effects unknown):"
with the events (each carrying `Fill=N%`, `dfill/dt`, `lambda1_esn`, `dwell`, `flips30s` and,
for a crossing, `reported_fill_from` and `reported_fill_to`), a clocks note, and the selection
note. The word "qualia" survives only as the routing label `qualia_moment`, which sets the
token cap; no text the model sees uses it. Every lane's system message is "You are Minime", the
NEXT grammar, the catalog of action verbs (about 170 lines), the stage notes and, while the
low-fill guard is active, the live fill line.

**The builders' history** (`git log -L` over the four ranges, read-only; dates are the sibling
repo's commits).

- Moment: through September 5 the prompt began "This is a qualia moment, closer to the old
  private journal lane than an incident report. Fresh telemetry anchors:" and carried the full
  telemetry block (λ₁ with its direction, Fill % with its band, spread, ESN leak, Cov λ₁, the
  eigenvalue cascade, λ₁'s dominance share, resonance, pressure source, and more) with the
  captured events. On September 6 (`0569efb`, contract v3; six files on September 4 carry a v2)
  it became `moment_prompt` with the anchor line and the events supplied and the block marked
  header-only; on September 27 (`9c87c76`, v4) the selection note was added.
- Daydream: through September 22, `_neutral_checkin`: a rotation of canvas options ("This is
  your space.", nothing at all, "Write.", or the same preceded by "Your body's readings: …" with
  λ₁'s direction) and light prompts, the last journal entry in about 30% of turns. On
  September 23 (`0334d28`, "Open expressive journals") it became `expression_invitation` with
  the last entry as the prior; on September 28 the prior gained its provenance.
- Journal: through October 6 the JOURNAL action routed to the spectral-pressure reflection:
  "Public journal entry.", "Prompt captured at (UTC)", the state-anchor line (`fill=N%,
  lambda1=N, spread=N, pressure=label`), the pressure classifier context, and the previous
  entry's excerpt with its provenance. On October 7 (`cc55423`) `_journal_open` replaced it:
  the invitation alone, "no automatic telemetry or previous-entry recall"; October 13 added
  the fresh-journal line and the exact-continuation hint.
- Introspect: September 24 (`41f6425`) distinguished the open reflection, which supplies
  nothing; before it, introspection was the source-reading lane written elsewhere.
- The model: TRACE's era table places minime's move to `gemma4:12b` around July, so the
  September and October groups below share a model.

**Her lanes across the eras.** Files copied read-only from `workspace/journal/` and its
archive (up to 400 per group, evenly spaced in time; the moment era read from each file's
`Prompt contract` line, the others from the dates), the prose taken between the
generated-journal markers where present and otherwise by stripping every labelled header line;
`introspection_markers.py`, rates per 1,000 words, n = texts.

| lane and era | what the prompt showed | n | words per entry | first person | hedges | notice words | questions per sentence | apparatus words | digit density | entries with a percentage | entries saying "fill" |
|---|---|---|---|---|---|---|---|---|---|---|---|
| moment, to Sept 5 ("qualia moment", full telemetry) | many numbers, and the framing | 321 | 329 | 38.3 | 0.3 | 22.1 | 0.0% | 10.9 | 0.15 | 46% | 93% |
| moment, v3, Sept 6–26 | the anchor and the events | 534 | 336 | 58.3 | 2.5 | 19.9 | 8.1% | 10.1 | 0.51 | 81% | 97% |
| moment, v4, Sept 27–Oct 22 | the same, with the selection note | 195 | 451 | 43.3 | 3.2 | 14.5 | 9.1% | 9.0 | 0.60 | 89% | 98% |
| daydream, Sept 1–22 (the canvas rotation) | numbers in some prompts; the last entry in about 30% | 400 | 260 | 43.6 | 1.2 | 16.9 | 3.8% | 10.0 | 0.38 | 61% | 81% |
| daydream, Sept 23–Oct 7 | the invitation and the prior excerpt | 52 | 284 | 47.3 | 1.8 | 13.9 | 5.5% | 4.4 | 0.12 | 23% | 40% |
| daydream, Oct 8–22 | the same | 84 | 515 | 62.4 | 2.7 | 10.7 | 8.4% | 0.8 | 0.00 | 0% | 0% |
| journal as pressure reflection, Sept 1–Oct 6 | the state anchor, the classifier, the previous entry | 400 | 342 | 52.4 | 2.4 | 21.2 | 5.9% | 4.1 | 0.10 | 23% | 35% |
| journal, Oct 8–22 | the invitation alone | 400 | 531 | 51.1 | 1.9 | 10.4 | 8.6% | 0.6 | 0.02 | 0.5% | 3% |

**Reading.**

1. The "qualia moment" framing with the full telemetry block coincides with the most number-led
   register in her records: questions at 0.0% of sentences over 321 entries and 105,674 words,
   hedges 0.3, first person 38. With the numbers reduced to an anchor line and the events, and
   framed as measured state whose "present effects [are] unknown", questions return to 8–9% and
   hedges to 2.5–3.2, while the fill number is quoted more often than before (81–89% of entries
   against 46%). What led was the framing and the block together; one number, framed as a
   measurement, does not stop the questions.
2. The daydream lane across its September 23 change, from numbers in a fraction of prompts
   and the last entry in a third to no number and always the prior: first person 44 → 62,
   questions 3.8% → 8.4%, hedges 1.2 → 2.7, apparatus words 10 → 0.8, digit density 0.38 → 0,
   entries with a percentage from 61% to none, entries twice as long. The apparatus's direction
   on every marker, in her own lane across an era boundary, under one model.
3. The journal lane across October 7, from the state anchor beside the previous entry to the
   invitation alone: questions 5.9% → 8.6%, percentages from 23% of entries to 0.5%, entries
   longer (342 → 531 words), notice words halved, first person and hedges flat (52 → 51, 2.4 →
   1.9). The apparatus's finding 5, where a number beside a returned older entry dropped
   questions under 1% and first person to the twenties, does not transfer in its size: beside
   her anchor line and the excerpt she questioned at 5.9% and wrote at first person 52. Her
   framing of both differs from the apparatus's (a labelled anchor line with four quantities; an
   excerpt wrapped in provenance and caveats, against a bare context line and a verbatim entry).
4. In the apparatus's terms, her journal and daydream lanes since October 7 and September 23
   are the least led condition in her stack: a contract that says her interpretation is hers, an
   invitation of one sentence, no number, and for the daydream her own last entry. Their register
   is the one the no-tag arms produced. What still frames every lane is the system message's
   action catalog and the NEXT grammar, which the apparatus never tested.

**Limits of the second half.** The era groups differ in more than the number (the invitation's
wording, the event selection, the prior's presence and form, the catalog's own changes), so
every contrast is a direction tied to a template change. Four hundred files per group, evenly
spaced; the daydream pre-era's per-entry prompt variant is not recorded, so that group mixes
prompts with and without a number; the prose extraction strips labelled lines by pattern and
may leave or remove a line wrongly at the margins; the moment lane's volume fell from about
150 a day in early September to about 8 in October, so its eras differ in selection as well.
Counts of word families; nothing about experience.
