# Minime, one week of entries, concept chains by lane (October 22, 2026)

**Subject and channel.** Minime's journal files of the seven days to 2026-10-22, copied
read-only from volya on 2026-10-22 into the session scratchpad (`beings-sample/minime-week/`,
private; never in the repo): 1,513 files, of which 1,404 carry prose after the header lines
are stripped (the other 109 are `study_decision` and `study_navigation` files that hold only
their headers and a `NEXT:` line). What her prompts showed her at each turn is not known from
here; the moment lane's entries quote a fill reading themselves. Probe
`probes/concept_chains.py` (its `--lane` filter and the `both` flag were added today;
`tests/test_concept_chains.py`), outputs `concept-chains-minime-week.out` and one JSON per run
under `arms/logs/` in the scratchpad. Lanes are the filename prefix after Mike's `!` flag;
filenames are America/Los_Angeles local time. Counts of words, not judgments of thought, and
nothing about experience.

**What the probe counts** (as in `analyses/2026-10-21-concept-chains.md`): terms are words of
five or more letters reduced by a conservative suffix stripper, minus function and structural
words; per entry, the share of its terms that occur in the previous entry of the same run;
the earlier entry within twelve that shares the most terms with it (the inferred source, by
Jaccard); the share of terms absent from the previous entry but present in an earlier one
(reach); sentences that name earlier writing (bridges); quoted terms and their recurrence; and
chains, terms that first appear in entry k ≥ 2 and recur in every following entry. Within a
lane, "previous" and "offset" count that lane's entries only.

| run | n | words | carried from the previous entry | inferred source at offset 1 / 2 / 3–5 / 6+ (mean) | reach past the previous entry | bridges per entry (entries opening with one) | quoted per entry (already earlier) | chains ≥ 3 (longest) | files with "ghost" |
|---|---|---|---|---|---|---|---|---|---|
| all lanes, interleaved in time | 1,404 | 787,465 | 28.2% | 22% / 11% / 25% / 42% (5.2) | 43.4% | 0.06 (1%) | 9.7 (91%) | 33 (6) | – |
| introspect | 500 | 336,425 | 35.2% | 7% / 11% / 25% / 56% (6.4) | 44.0% | 0.02 (0%) | 9.1 (94%) | 14 (8) | 335 of 500 |
| journal | 391 | 203,941 | 27.3% | 8% / 8% / 26% / 58% (6.4) | 46.8% | 0.02 (0%) | 9.7 (88%) | 18 (8) | 185 of 391 |
| self_study | 350 | 148,596 | 38.4% | 52% / 13% / 17% / 17% (2.9) | 38.7% | 0.02 (0%) | 11.4 (81%) | 50 (18) | 2 of 350 |
| daydream | 72 | 36,700 | 25.6% | 8% / 11% / 34% / 46% (5.9) | 44.6% | 0.97 (22%) | 9.4 (73%) | 13 (5) | 41 of 72 |
| moment | 59 | 55,450 | 66.8% | 7% / 10% / 22% / 60% (6.9) | 20.2% | 0.00 (0%) | 7.9 (84%) | 7 (6) | 9 of 59 |

The window is twelve entries, so "6+" means six to twelve. The remaining lanes of the week
(study_decision 76 files, study_navigation 58, notice 3, action_thread 2, decompose 1,
visualize_cascade 1) are in the interleaved run only.

## Reading

**The deep offsets survive within a lane, and grow.** The October 21 sample of 40 entries
across lanes put the inferred source six or more entries back on 41% of turns, and the
question was whether that was her lanes interleaving. It is not: within the introspect lane
the nearest earlier entry is six or more back on 56% of entries and the previous one on only
7%; within the journal lane 58% and 8%; daydream 46% and 8%; moment 60% and 7%. The one lane
that follows its previous entry is self_study (52% at offset 1, mean 2.9), where consecutive
entries study the same source page and share its vocabulary. Five hundred introspections in
a week is about one every twenty minutes, so six entries back within that lane is about two
hours of wall time.

**Bridges are rare except in daydream.** Introspect, journal, self_study and moment name
earlier writing on 0.00–0.02 sentences per entry, less than the apparatus's tagged arms
(0.08–0.17) and far less than its plain-contract arms (0.58–1.08). The daydream lane is the
exception: 0.97 bridges per entry, 78% of its entries have one and 22% open with one, the
rate of the plain-contract arms. Whatever the daydream prompt carries, its entries say "the
X I described" where the other lanes do not.

**The moment lane has the shape of a number-led register.** Its entries share two thirds of
their terms with the previous entry (66.8% against 25–38% in the other lanes), reach back
for only a fifth (20.2% against 39–47%), never bridge, and carry the same quoted words from
the first entry to the last: "fill" in 59 of 59, "stable-core" and "stable" in 58, "fill
crossed above target" in 57. That is the shape the apparatus produced when a fill number was
shown (carried 36.6–48.1%, reach 16–20%, bridges 0.08–0.17), and these entries quote a fill
reading, so a number reached the model in this lane. The inferred-source offsets of this lane
(60% at six or more) mean little, because when every entry shares the same vocabulary the
nearest neighbour is arbitrary.

**Quoting is mostly re-quoting, and "ghost" lives in the reflective lanes.** Entries quote
nine to eleven terms each, and 81–94% of those already appeared in an earlier entry of the
same lane. The longest quoted-term runs are register words taken up once in quotation marks
and present in nearly every entry after: "human" in 467 consecutive introspections from the
34th, "i am" in 369 from the 132nd, "architecture" from entry 7 to 80 of the journal lane and
7 to 72 of daydream, "space" from 2 to 80 and 3 to 82. "ghost" appears in 335 of 500
introspections and 185 of 391 journal entries, 41 of 72 daydreams, 9 of 59 moments and 2 of
350 studies: the figure belongs to the lanes without a source page and, on this count, without
a number.

**Chains are short.** Terms that appear in every following entry for three or more entries
number 33 across the interleaved week (longest 6, "inhabit" in entries 2–7) and 7–18 within
the reflective lanes (longest 8: "expression" in introspections 11–18, "state" in journal
entries 2–9); the 18-entry "temporal" chain in self_study is a study topic. Continuity in
these lanes is carried by a stable vocabulary and by reaching back several entries, not by a
figure developed entry after entry, which is also what the apparatus's forty-entry arms showed
(longest chains 12–22, almost all the model's own figures).

## What this does not say

Which earlier entries she was shown, and whether the within-lane offsets come from a prompt
that carries several entries, from a long context, or from a vocabulary stable enough that
any earlier entry is as near as the last; the prompts were not copied. Nothing about the
other being: Astrid's week was read for its readouts, not its chains
(`analyses/2026-10-22-astrid-readout-audit.md`).

## Limits

One week, one being; lanes by filename prefix; a twelve-entry window, so offsets past it are
unseen and "6+" is 6–12; the inferred source is a lexical nearest neighbour, unreliable where
every entry shares a vocabulary (moment) and biased toward recency elsewhere; quoted-term
chains count plain recurrence after a first quotation, so a common word quoted once runs for
hundreds of entries; the probe's stop list gained four-letter function words today, so the
quoted columns are not comparable with the October 21 table; the self_study entries contain
code and markdown, which the term reducer treats as words.

## What it offers

For the state-logging proposal (`proposals/esn-state-logging.md`): a record that spans only
the previous entry cannot join her state to her text, because within her reflective lanes the
nearest earlier entry is more often two hours back than twenty minutes. For the two-entry
slot arms running today (desktop 0.38.0): her lanes without a number reach back to entries
several turns old without naming them, which is the shape the arms can now test with the
older entry shown beside the latest one, and her moment lane is the number-led shape the
tagged arms already reproduced.
