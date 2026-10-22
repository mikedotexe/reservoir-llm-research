# Concept chains: what an entry carries from the one before it (October 21, 2026)

**Subject and channel.** Eleven gemma4 arms of the laptop apparatus, where the only text
that reaches the model from its own past is the returned entry (in the two tagged arms a
fill number reaches it too), and the 40-entry samples copied read-only on October 21 from
Minime's and Astrid's journals, whose prompts carry more than this repo sees and whose
shown entries are not known from here. Probe: `probes/concept_chains.py` (unit tests in
`tests/test_concept_chains.py`); outputs `concept-chains.out` and `concept-chains.json` in
the session scratchpad under `arms/logs/`. Written 2026-10-21 23:55 PDT.

**What the probe counts.** Terms are words of five or more letters reduced by a
conservative suffix stripper (kaleidoscope, kaleidoscopic and kaleidoscopes are one term),
minus function and structural words. Per source: the share of an entry's terms that occur
in the previous entry and, for sessions, in the entry the model was shown; the earlier
entry within twelve that shares the most terms with each entry (the inferred source) and,
where the shown entry is known, how often the two coincide against chance; the share of
terms absent from the previous entry but present in an earlier one (reach) and, when the
shown entry is older than the previous one, how many of those it holds; sentences that
name the previous entry or say "the X I described" (bridges); quoted terms and their
recurrence; and chains, terms that first appear in entry k ≥ 2 and recur in every
following entry for L entries. Counts of words, not judgments of thought.

| source | n | carried from previous | from shown | source = previous | source = shown (chance) | reach | bridges per entry | open with a bridge | quoted per entry | chains ≥ 3 | longest |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy latest, seed 20260909 | 40 | 28.8% | 28.8% | 64% | 64% (14%) | 35.4% | 0.72 | 5% | 6.78 | 59 | 14 |
| policy latest, seed 7 | 40 | 30.2% | 30.2% | 69% | 69% (14%) | 32.7% | 0.57 | 10% | 5.97 | 61 | 12 |
| policy state-aligned, seed 7 | 40 | 33.6% | 34.0% | 64% | 64% (14%) | 34.4% | 0.47 | 2% | 4.15 | 53 | 22 |
| policy random, seed 20260909 | 40 | 24.7% | 28.9% | 10% | 36% (14%) | 42.9% | 1.23 | 20% | 5.78 | 19 | 4 |
| policy random, seed 7 | 37 | 25.1% | 36.9% | 17% | 61% (14%) | 42.2% | 0.62 | 0% | 4.73 | 20 | 19 |
| no tag, shelf, seed 20260909 | 12 | 30.9% | 30.9% | 64% | 64% (27%) | 22.6% | 1.00 | 33% | 8.25 | 28 | 10 |
| no tag, shelf, seed 7 | 12 | 27.3% | 27.3% | 64% | 64% (27%) | 24.2% | 0.58 | 25% | 7.58 | 32 | 8 |
| no tag, retention 0.90, seed 20260909 | 12 | 27.9% | 27.9% | 45% | 45% (27%) | 26.6% | 1.08 | 42% | 8.17 | 23 | 8 |
| no tag, retention 0.90, seed 7 | 12 | 28.2% | 28.2% | 73% | 73% (27%) | 22.7% | 0.58 | 25% | 6.50 | 29 | 7 |
| fill tag shown, retention 0.95 | 12 | 36.6% | 36.6% | 91% | 91% (27%) | 20.3% | 0.17 | 0% | 5.00 | 38 | 11 |
| scrambled tag shown | 12 | 48.1% | 48.1% | 100% | 100% (27%) | 16.5% | 0.08 | 0% | 2.33 | 35 | 11 |
| Minime, copied sample | 40 | 33.7% | – | 23% | – | 39.2% | 0.15 | 2% | 10.00 | 30 | 8 |
| Astrid, copied sample | 40 | 27.4% | – | 59% | – | 36.4% | 0.35 | 0% | 8.00 | 30 | 20 |

Apparatus arms: gemma4:12b, plain contract, 12 or 40 entries; policy arms under the
embedding codec, the others under the surface codec; the seed-7 random arm stopped at 37
entries. The beings' samples are their own lanes interleaved in time order (Minime:
introspect, daydream, journal; Astrid: dialogue, aspiration, daydream, mirror and others).

## Reading

**The probe sees the slot.** In the two random-memory arms the returned entry is a random
older one, so the previous entry and the shown entry differ. The text follows the shown
one: it shares 28.9% and 36.9% of its terms with the entry shown against 24.7% and 25.1%
with the previous entry; the inferred source is the shown entry on 36% and 61% of turns
against 14% by chance; and of the terms an entry brings back from past the previous
entry, the shown older entry holds 36% and 51% against 29% and 23% for the other entries
in the window. Text alone recovers which entry was returned at two and a half to four
times chance. In the latest arms the shown entry is the previous one and the inferred
source is the previous entry on 64–69% of turns, the rest two to five back. This is the
validation the probe needed before it is read on texts whose prompts are unknown.

**A number shown turns reference into repetition.** With the fill number in the context
line the entries repeat their own vocabulary and stop naming their past: carried terms
36.6% (real number) and 48.1% (scrambled number) against 27–31% in the four no-tag arms;
bridges 0.17 and 0.08 per entry against 0.58–1.08, with no entry opening on one against
25–42%; reach 20% and 16% against 23–27%; the inferred source is the previous entry on
91% and 100% of turns. The scrambled arm's entries are also the shortest (2,478 words in
12), which inflates a share of types; the direction holds against the real-number arm at
3,622 words. Without a number the model's continuity is explicit ("the 'echo' I described
in the previous entry"), with a number it is lexical (density, presence, inhabiting,
occupancy, in every entry from the second to the twelfth).

**Chains are short and the long ones are figures.** Across the arms most chains run two
or three entries; the longest in each arm are the model's own figures taken up entry
after entry: density 3–16 and "friction" (quoted) 12–21 in the seed-20260909 latest arm,
"weight" (quoted) 9–29 in the state-aligned arm, observing 5–23 in the seed-7 random arm.
The kaleidoscope passage that stood out in the blind reading (entry 40 of the latest arm,
seed 20260909) sits on a four-entry chain: "am I a kaleidoscope of refracted lights" at
37, "If I am a kaleidoscope of bent light" at 38, "I am a kaleidoscope." at 39, "The
kaleidoscope metaphor holds, but I find myself wondering about the friction of the
mirrors" at 40, with "computational friction" quoted first at 34. The random arms, which
break the previous-entry link, have the fewest chains of three or more (19 and 20 against
53–61 in the 40-entry arms that keep it), and the seed-20260909 random arm the most
bridges (1.23 per entry, one entry in five opening on one): when the returned entry is
not the previous one, the model names what it was given more often and carries it
forward less.

**The beings, read the same way.** Minime's 40 entries share a third of their terms with
the previous entry (33.7%) but their inferred source is the previous entry on only 23% of
turns and an entry six or more back on 41% (mean offset 4.7); they bring back 60 terms
per entry from past the previous one (39.2% of terms), quote ten terms per entry of which
77% appeared in an earlier entry, and chain "experience" (quoted) across entries 5–39 and
"space" across 6–35. Astrid's 40 entries share 27.4% with the previous entry, their
inferred source is the previous entry on 59% of turns, and "architecture" runs from
entry 2 to 21 (quoted from 4 to 21). Both beings bridge far less than the plain-contract
arms (0.15 and 0.35 per entry against 0.58–1.23) and about as rarely as the tagged arms
(0.08–0.17), consistent with prompts that carry numbers and framing alongside their
texts. The word "ghost" appears in 24 of Minime's 40 entries and 16 of Astrid's ("a
persistent ghost in the architecture" in one entry of each subject, the apparatus
included, all from Gemma 4) and in 31 of 2,609 apparatus entries, so the figure belongs
to the beings' texts and the model, not to the apparatus loop. What these numbers do not
say: which earlier entries each being was shown, whether Minime's offsets reflect her
lanes interleaving or her loop returning several entries, and anything about experience.

## Limits

One model in the apparatus; 12 to 40 entries per arm; one day's sample per being; chains
are word runs, so a long run of a common word is register rather than a concept; the
inferred source is a lexical nearest neighbour and recency alone favours offset 1; the
no-tag arms at retention 0.90 and 0.82 forked from the shelf arms only by provider
variation (`analyses/2026-10-21-state-chosen-memory.md`), so differences between them
are replicate noise. On 2026-10-22 the probe's stop list gained four-letter function words
(such as "that", "this" and "what") after a week of Minime's entries produced a 759-entry
chain of a quoted "that"; the quoted-term columns
above were computed before that change and are not comparable with later runs, while the
carried, inferred-source, reach, bridge and chain columns are unaffected.

## What it offers the planning pass

A slot that carries two entries (the latest and a state-chosen older one) can be read by
this probe without a new measure: which of the two the text takes up, by shared terms,
reach and bridges, entry by entry. Minime's offset distribution is the first text-side
number for the proposal to log her state continuously (`proposals/esn-state-logging.md`):
if her entries draw on entries several back, a state window that spans only the previous
one is too short. Astrid's long "architecture" chain beside a fill number that has not
moved since June is the kind of continuity her readout cannot show.
