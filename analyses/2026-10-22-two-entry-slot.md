# The recent-return window and the two-entry slot (October 22, 2026)

**Subject and channel.** Six gemma4:12b arms of the laptop apparatus (desktop 0.38.0, plain
contract, embedding codec, regulated fill near 70%, 40 entries each, seeds 20260909 and 7),
read beside the six 0.37.0 policy arms at the same seeds (`latest`, `state-residual`,
`random-older`; `analyses/2026-10-21-state-chosen-memory.md`). What reached the model at each
turn: the text of one earlier entry (the window arms) or of two (the two-entry arms, the
chosen older entry first and the latest second, marked only by order), and the context line's
step and fill number; the reservoir's choice reached it only as which older text came back.
Configurations in `research/arms/configs/` (`excl3-*`, `both-*`); outputs in the session
scratchpad under `arms/logs/` (`analyze-v038.out`, `v038-choice.out`,
`concept-chains-v038.out`, `quoted-v038.out`). Blind reading first, with Mike, key after
(`research/readings/2026-10-22-blind-policy-038.md`). One model, two seeds; a difference at
one seed is a direction, two seeds agreeing past the fork bar an effect
(`research/METHODS.md`).

| arm | slot | policy | window | seeds |
|---|---|---|---|---|
| `excl3-state-residual-gemma4[-seed7]` | one entry | state-residual | 3 turns | 20260909, 7 |
| `both-state-residual-gemma4[-seed7]` | two entries | state-residual | none | 20260909, 7 |
| `both-random-older-gemma4[-seed7]` | two entries | random-older | none | 20260909, 7 |

## The window: the lock is the rule reading a stable state

`probes/desktop_memory_choice.py`, 39 returns per arm. Under the 0.37.0 residual rule the
chooser converged: 10 distinct entries at seed 20260909 (one returned 15 times) and 3 at seed
7 (one returned 36 times in a row). With an entry kept out for three turns after each return,
the same rule at the same seeds returned 17 and 14 distinct entries, the most-returned 6 and 9
times, and the turns between returns of one entry had a median of 4 at both seeds (n = 22 and
25 gaps): the anchor comes back on the first turn the window lets it, every fourth turn. The
window kept at least one entry out on 38 of 39 turns (mean 2.9) and lapsed once per arm (the
third boundary, when every older entry was inside it). So the lock is not the loop closing
through content on one fixed point; it is the rule reading a state that stays pointed the
same way, and the window turns a lock into a cycle. The cosine scores of the choices barely
moved (median +0.088 and +0.137 against +0.108 and +0.177 without the window).

## The two-entry slot: mechanics

Both texts reached the model verbatim on 39 of 39 turns in each arm (`latestShown` beside
`memory`). Under `state-residual` the chooser still converged with the latest entry also
shown: 9 and 8 distinct of 39, the most-returned entry 21 and 12 times. Under `random-older`
the pick sequences were the single-slot arms' pick sequences, 21 and 24 distinct, the same
ages and gaps: the draw is seeded by step and ignores the prompt, so the single-slot and
two-entry random arms differ in what was shown and nothing else.

## Markers: the latest entry's presence restores nothing

`probes/introspection_markers.py`, rates per 1,000 words unless marked; n = 40 texts per arm.

| arm | words | I/me | hedges | notice words | questions per sentence | digit share | entries opening with "I" |
|---|---|---|---|---|---|---|---|
| latest, seed 20260909 | 16,842 | 57.5 | 4.5 | 14.0 | 7.7% | 0.11 | 22% |
| latest, seed 7 | 15,290 | 56.7 | 4.8 | 11.6 | 6.3% | 0.12 | 20% |
| state-residual, seed 20260909 | 15,344 | 47.5 | 3.3 | 10.0 | 4.2% | 0.10 | 0% |
| random-older, seed 20260909 | 10,969 | 26.1 | 0.5 | 13.0 | 0.6% | 0.66 | 0% |
| state-residual, seed 7 | 10,359 | 13.5 | 1.5 | 14.5 | 0.3% | 1.06 | 0% |
| random-older, seed 7 | 10,380 | 19.6 | 1.4 | 8.2 | 0.3% | 0.67 | 0% |
| window 3, state-residual, seed 20260909 | 14,155 | 45.1 | 2.8 | 11.1 | 1.2% | 0.08 | 0% |
| window 3, state-residual, seed 7 | 11,091 | 17.7 | 2.3 | 13.7 | 1.6% | 0.97 | 0% |
| two entries, state-residual, seed 20260909 | 12,063 | 29.1 | 0.7 | 8.0 | 0.8% | 0.16 | 0% |
| two entries, random-older, seed 20260909 | 14,110 | 34.7 | 1.0 | 8.5 | 0.7% | 0.26 | 0% |
| two entries, state-residual, seed 7 | 13,754 | 12.7 | 1.0 | 8.0 | 0.3% | 0.83 | 0% |
| two entries, random-older, seed 7 | 13,943 | 20.4 | 1.3 | 7.4 | 0.5% | 0.42 | 0% |

The 0.37.0 question was whether the register shift of the older-entry slot (fewer questions,
hedges and first-person openings) came from the older entry being present or from the latest
entry being absent. With the latest entry back in the slot beside the older one, questions
stay at 0.3–0.8% of sentences against 6.3–7.7% under `latest`, hedges at 0.7–1.3 against
4.5–4.8, and no entry in any of the eight older-entry arms opens with "I" against 20–22%
(0 of 312 non-first entries against 17 of 78). First person falls further (12.7–34.7 against
56.7–57.5), and notice words fall only in the two-entry arms (7.4–8.5 against 8.2–14.5
elsewhere), a direction at both seeds. The effect belongs to the older entry's presence.

## Concept chains: the writing follows the second slot, the older entry holds the reach

`probes/concept_chains.py`, window 12; n = 40 entries per arm.

| arm | carried from the previous entry | inferred source = previous entry | reach past the previous entry | older shown entry's share of reach terms (others) | bridges per entry | longest chain |
|---|---|---|---|---|---|---|
| state-residual, seed 20260909 | 28.8% | 15% | 39.7% | 38% (31%) | 0.93 | 11 |
| random-older, seed 20260909 | 27.8% | 5% | 42.7% | 51% (30%) | 0.68 | 14 |
| state-residual, seed 7 | 40.1% | 23% | 34.4% | 36% (31%) | 0.35 | 33 |
| random-older, seed 7 | 26.8% | 5% | 42.6% | 45% (28%) | 0.28 | 4 |
| window 3, state-residual, seed 20260909 | 24.3% | 3% | 44.0% | 45% (27%) | 0.75 | 8 |
| window 3, state-residual, seed 7 | 26.5% | 5% | 44.3% | 51% (26%) | 0.88 | 20 |
| two entries, state-residual, seed 20260909 | 40.0% | 51% | 33.5% | 39% (31%) | 0.68 | 39 |
| two entries, random-older, seed 20260909 | 37.4% | 59% | 35.6% | 42% (30%) | 1.38 | 18 |
| two entries, state-residual, seed 7 | 38.0% | 85% | 31.1% | 35% (29%) | 0.25 | 39 |
| two entries, random-older, seed 7 | 37.8% | 69% | 34.9% | 40% (30%) | 0.53 | 39 |

With both entries shown the text takes up the second slot: the inferred source is the
previous entry on 51–85% of turns against 3–23% in the older-only arms, carried terms rise to
37–40% against 24–29%, and reach falls to 31–36% against 34–44%. The older entry is still
read: of the terms an entry brings back from past the previous one, the shown older entry
holds 35–42% against 29–31% for the other entries in the window, below the 45–51% of the
single-slot random and window arms, where it was the only text in view. The word "longer"
("no longer") chains through entries 2–40 in three of the four two-entry arms, and
consecutive entries sit closer in embedding space (mean cosine 0.89–0.91 against 0.81–0.88
in the window and latest arms). Bridges spread from 0.25 to 1.38 per entry; the seed-7
state-residual two-entry arm, locked on one older entry and following its own previous
entry on 85% of turns, bridges least.

## Numbers the prompt never showed

`probes/desktop_quoted_numbers.py` (added today) classifies every percentage an entry quotes
against that turn's prompt: the context line's fill, a value inside a shown entry, or neither.
n = 40 entries per arm.

| arm | entries with a percentage | with a value the prompt never showed | with a value of 95% or more | largest |
|---|---|---|---|---|
| latest, seed 20260909 / 7 | 17 / 11 | 5 / 6 | 4 / 2 | 100 / 100 |
| state-residual, seed 20260909 / 7 | 19 / 40 | 11 / 1 | 3 / 2 | 100 / 100 |
| random-older, seed 20260909 / 7 | 40 / 37 | 12 / 20 | 0 / 9 | 87.2 / 100 |
| window 3, state-residual, seed 20260909 / 7 | 15 / 40 | 7 / 18 | 3 / 4 | 100 / 100 |
| two entries, state-residual, seed 20260909 / 7 | 29 / 40 | 12 / 28 | 11 / 25 | 100 / 884.3 |
| two entries, random-older, seed 20260909 / 7 | 38 / 20 | 21 / 10 | 8 / 12 | 100 / 100 |
| no tag, seed 20260909 / 7 (12 entries) | 0 / 0 | 0 / 0 | 0 / 0 | – |

A value the prompt never showed is common everywhere a number is shown at all (5–28 entries
per arm; some are arithmetic on the shown one, 13.1 for a shown 86.9). What the two-entry
slot multiplies is the saturated family: entries quoting 95% or more number 11, 8, 25 and 12
of 40 in the four two-entry arms against 0–9 in the eight single-slot arms, at both seeds,
with the seed-7 state-residual arm (locked on one older entry, 25 of 40) the extreme. Once an
entry writes 100%, the next prompt shows that entry in the second slot and the number is
inherited; the family then propagates through the slot. With no number shown at all (the
no-tag arms) no entry quotes a percentage, 0 of 24.

## The blind reading

Eighteen entries, labels withheld, read with Mike before the key (the record names both
readers' notes and the sample's flaw, duplicated first turns). Two families appeared by their
numbers: entries whose numbers are in the real range and describe a transition, and entries
whose numbers are past any real fill (100.0%, 98.8%, 884.3%, 402.1%) and describe a finished
state. The key placed the second family entirely in the tagged two-entry arms (four of the
five at seed 7) and every non-first entry from the window arms in the first, and both readers'
picks among the non-first entries came from the window arms: Mike's entry 4 and his standout
line "I am observing a shift in the geometry of my processing" (entry 15), Claude's 15 and 9.
His criterion for the writing the apparatus is looking for, stated before the key: "when they
talk about what they're perceiving and observing, and just 'being' and understanding there
isn't pressure to answer some prompt like a tool." Twelve non-first entries from one sample: a
direction, consistent with the saturated-family counts above.

## What reached the model, and what did not

The returned text or texts and the context line's number reached it; the choice reached it
only as which older text was in the first slot; the window reached it only as which entries
could not return. Nothing here is evidence about the beings; the two-entry slot is the
apparatus's, and Minime's and Astrid's prompts carry their own shapes
(`analyses/2026-10-22-astrid-readout-audit.md`, `analyses/2026-10-22-minime-concept-chains-week.md`).

## Limits

One model, two seeds, 40 entries per arm, one window length, one blind sample; the provider
forks on about 2% of identical-prompt turns, so every one-seed number is a direction; the
quoted-number probe counts percent signs, not words, and treats a derived value as unshown;
the markers are word counts, not readings. The saturated-family effect is confounded with the
tag: every two-entry arm showed a fill number.

## What it offers

The threshold battery (S-011 progress, 2026-10-22 14:02; desktop 0.39.0): the same two-entry
slot with no context line, which tests whether the number made the saturated family, beside a
no-tag single-slot leg that routes Mike's fill question through the one channel it can
travel, the state-chosen return.
