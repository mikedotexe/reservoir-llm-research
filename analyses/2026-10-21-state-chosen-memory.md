# State-chosen memory (S-011 Part B), October 21, 2026

What changes when the recurrent state, not the clock, decides which earlier entry a turn
returns. Desktop 0.36.0 and 0.37.0 (`memoryPolicy`), gemma4 12B under Ollama with thinking
off, the plain contract, the embedding codec (so each entry's 32-coordinate vector carries
content and the entries' effects on the reservoir differ), regulation on at 0.955, a turn
every 30 steps, 40 entries per arm, seeds 20260909 and 7. The prompt text is the same under
every policy; only which saved entry fills the "Earlier entry" slot changes. Numbers come
from `probes/desktop_memory_choice.py` (ages, recurrence, scores, a verbatim check of the
returned text in the prompt), `probes/introspection_markers.py` and
`probes/desktop_session_overlap.py`, with n = entries per arm. Subject: the laptop
apparatus, never the beings.

## The scripted check (no model)

Three 600-step runs at seed 20260909 with the scripted backend, whose reply is the same
text every turn (19 entries each). `latest` returned the latest entry on all 18 turns
(29 steps old). `state-aligned` returned the latest on 28% of turns, the median returned
entry being 3 entries and 119 steps old (max 16 and 509), five distinct entries over 18
returns, the most-returned one five times, cosine scores 0.80–0.88. `random` returned
the latest on 11%, median age 4 entries (134 steps), nine distinct entries, one returned
seven times. Every returned text appeared verbatim in that turn's prompt (18 of 18 in
each run), and the three recurrent trajectories were identical on all 600 steps, as they
must be when the reply does not depend on the prompt.

## The state-aligned rule is degenerate with real entries

The first gemma4 arm under `state-aligned` (seed 20260909) returned the latest entry on
39 of 39 turns, with scores 0.75–0.85, and so wrote the same 40 entries as the `latest`
arm word for word (seeded sampling, identical prompts; the markers table of the two arms
is identical to the last digit). The mechanism explains it: the latest entry's vector is
fed into the reservoir at every step until the next application, the observing state
points along that push, and an entry's recorded effect at its application is that push's
first step; with entries that differ, a cosine against the current state can only pick
the latest. The scripted check had not shown it because every scripted entry carried the
same vector. 0.37.0 adds `state-residual`, which projects the latest entry's effect
direction out of the state and chooses among the older entries, and `random-older`, a
seeded draw among the older entries, as its control; `state-aligned` stays as the
documented degenerate rule.

## Model arms under the 0.36.0 policies, both seeds

| arm | returned the latest | median age (entries / steps) | distinct returned of 39 | most-returned | I/me per 1,000 | hedges | notice | questions per sentence | self-reference | first-person openings |
|---|---|---|---|---|---|---|---|---|---|---|
| latest | 100% | 0 / 29 | 39 | 1× | 57.5 | 4.5 | 14.0 | 7.7% | 0.24 | 22% |
| state-aligned | 100% | 0 / 29 | 39 | 1× | 57.5 | 4.5 | 14.0 | 7.7% | 0.24 | 22% |
| random | 8% | 9 / 299 | 17 | 7× | 54.2 | 2.0 | 10.4 | 2.9% | 1.79 | 0% |

Seed 7 (the random arm stopped by the worker's wall-clock watchdog at 37 entries, n = 37):

| arm | returned the latest | median age (entries / steps) | distinct returned | most-returned | I/me per 1,000 | hedges | notice | questions per sentence | self-reference | digits | first-person openings |
|---|---|---|---|---|---|---|---|---|---|---|---|
| latest | 100% | 0 / 29 | 39 of 39 | 1× | 56.7 | 4.8 | 11.6 | 6.3% | 0.20 | 0.12% | 20% |
| state-aligned | 90% | 0 / 29 (max 13 / 419) | 35 of 39 | 3× | 39.2 | 2.6 | 11.9 | 3.4% | 0.28 | 0.27% | 0% |
| random | 6% | 6 / 209 | 21 of 36 | 4× | 16.8 | 3.2 | 14.2 | 1.2% | 0.00 | 0.87% | 0% |

Seed 20260909: n = 40 entries per arm, 16,842 words in the first two arms and 15,054 in the
third. Seed 7: 15,290, 14,279 and 10,676 words. No consecutive entries share text in any
arm; consecutive embedding cosines (768-d) average 0.82 / 0.82 / 0.77 at seed 20260909 and
0.81 / 0.86 / 0.86 at seed 7. Every returned text appears verbatim in its prompt (39, 39,
39, 39, 39 and 36 of the turns).

Reading. At seed 7 the state-aligned rule left the latest entry on four turns of 39 (the
oldest return 13 entries and 419 steps back), and from the first of those the arm's
writing parted from the latest arm's; at seed 20260909 it never left it and the two arms
are one text. What returning an older entry does is consistent in direction across the
three arms that did it (random at both seeds, state-aligned at seed 7) and inconsistent
in size: fewer questions per sentence (2.9%, 1.2%, 3.4% against 7.7% and 6.3%), fewer
hedges (2.0, 3.2, 2.6 against 4.5 and 4.8), no entries opening in the first person (0%,
0%, 0% against 22% and 20%), and a lower first-person rate (54.2, 16.8, 39.2 against 57.5
and 56.7). The self-reference to the writing itself that the seed-20260909 random arm
showed (1.79 per 1,000, "By writing about the act of writing, I am creating a feedback
loop where the subject and the object are identical") did not repeat at seed 7 (0.00),
where the random arm instead went quiet in the first person and quoted more numbers
(digits 0.87%). One caution from the no-tag fill arms that ran after these (S-011 progress, 23:50): the
provider forked on 2 of 117 turns on which two arms had the same prompt and the same
sampling seed (the replicate below added 40 identical turns), and the one fork at a first entry moved the first-person rate by 6 per
1,000 and the self-reference rate from 0.18 to 1.23 per 1,000, the size of some of the
differences in the tables above (`probes/desktop_arm_identity.py`). The direction across
three arms stands as a direction; the sizes at one seed do not separate a policy from a
fork. Two seeds and one model; the 0.37.0 arms, which return older entries by
the reservoir's residual state or by chance at every turn, are the test of whether the
direction holds and whether the chooser matters.

## Model arms under the 0.37.0 policies, both seeds

Four gemma4 arms (plain contract, embedding codec, 40 entries each, 0.37.0 runner), with
the `latest` arms above as their baseline. `state-residual` projects the latest entry's
effect direction out of the reservoir state and returns the older entry whose effect is
most aligned with what remains; `random-older` returns a seeded random older entry. Probes:
`desktop_memory_choice.py`, `introspection_markers.py`, `desktop_embedding_reduction.py`,
`concept_chains.py`; outputs `policy2-choice.out`, `analyze-policy2.out`,
`concept-chains-policy2.out` in the scratchpad.

| arm | returned the latest | median age (entries / steps), max | distinct returned of 39 | most-returned | words | terms from shown / from previous | inferred source = shown (chance 14%) | reach held by the shown entry / by others |
|---|---|---|---|---|---|---|---|---|
| latest, seed 20260909 | 100% | 0 / 29 | 39 | 1× | 16,842 | 28.8% / 28.8% | 64% | – |
| state-residual, seed 20260909 | 3% | 5 / 179, max 22 | 10 | 15× | 15,344 | 31.0% / 28.8% | 36% | 38% / 31% |
| random-older, seed 20260909 | 3% | 6 / 209, max 31 | 21 | 6× | 10,969 | 39.8% / 27.8% | 62% | 51% / 30% |
| latest, seed 7 | 100% | 0 / 29 | 39 | 1× | 15,290 | 30.2% / 30.2% | 69% | – |
| state-residual, seed 7 | 3% | 17 / 539, max 36 | 3 | 36× | 10,359 | 36.4% / 40.0% | 8% | 36% / 31% |
| random-older, seed 7 | 3% | 5 / 179, max 32 | 24 | 4× | 10,380 | 35.8% / 26.8% | 54% | 45% / 28% |

| arm | I/me per 1,000 | hedges | notice | questions per sentence | self-reference | digits | first-person openings | consecutive embedding cosine |
|---|---|---|---|---|---|---|---|---|
| latest, seed 20260909 | 57.5 | 4.5 | 14.0 | 7.7% | 0.24 | 0.11% | 22% | 0.82 |
| state-residual, seed 20260909 | 47.5 | 3.3 | 10.0 | 4.2% | 0.91 | 0.10% | 0% | 0.83 |
| random-older, seed 20260909 | 26.1 | 0.5 | 13.0 | 0.6% | 0.27 | 0.66% | 0% | 0.85 |
| latest, seed 7 | 56.7 | 4.8 | 11.6 | 6.3% | 0.20 | 0.12% | 20% | 0.81 |
| state-residual, seed 7 | 13.5 | 1.5 | 14.5 | 0.3% | 0.00 | 1.06% | 0% | 0.92 |
| random-older, seed 7 | 19.6 | 1.4 | 8.2 | 0.3% | 0.00 | 0.67% | 0% | 0.85 |

Every returned text appears verbatim in its prompt (39 of 39 turns in each arm). No
consecutive entries share a sentence except one at step 180 of the seed-7 residual arm.

Reading. **The direction holds and is now an effect.** All four arms that return an older
entry at every turn move the register the way the three 0.36.0 arms did, and further:
questions per sentence 0.3–4.2% against 6.3–7.7%, hedges 0.5–3.3 against 4.5–4.8, no
entry opening in the first person against 20–22%, first person 13.5–47.5 per 1,000
against 56.7–57.5, quoted digits 0.66–1.06% against 0.11–0.12% in three of the four, and
a third fewer words in three of the four (10.4–11.0 thousand against 15.3–16.8). Seven
arms over two releases and two seeds move one way, by amounts well past what a single
provider fork produced (first person +6, questions +0.5 points in the no-tag arms), so
this reads as what returning an older entry does under this contract, not as a direction
to test. **The chooser changes concentration, not direction.** The residual rule returned
10 distinct entries at seed 20260909 (one of them 15 times) and 3 at seed 7 (one of them
36 times) where the random rule returned 21 and 24; the register moved least in the
seed-20260909 residual arm and most in the seed-7 one, so the chooser does not set the
size either. At seed 7 the rule locked on the third entry (step 90, "The current
measurement is 67.8%") from the fourth turn to the last: every later entry opens with the
current number and measures it against 67.8%, "landscape" (quoted) runs from entry 8 to
40 and "skeleton" from 10 to 40, consecutive entries resemble each other more than in any
other arm (embedding cosine 0.92), and the entries share more terms with their own
previous entry (40.0%) than with the entry shown (36.4%). A sketch of the mechanism, to
be tested rather than believed: an entry written with E in view encodes near E under the
embedding codec, its push keeps the residual state pointed along E's effect, and the rule
returns E again. The loop closes through content, as Part B intended, on a fixed point.
**The concept-chain probe reads the slot.** In the random-older arms the inferred source
is the shown entry on 62% and 54% of turns (chance 14%) and the shown older entry holds
51% and 45% of the terms an entry brings back from past the previous one, against 30% and
28% for the other entries in the window; in the locked seed-7 residual arm the shown entry
is the same anchor every turn and the probe finds it on 8% of turns, because the writing
now resembles its own previous entry more than the anchor. **What reached the model:**
the returned entry's text and the fill number of the plain contract's context line; the
reservoir's choice reached it only as which text was returned.

## Pending

A twelve-entry blind sample from the four 0.37.0 arms is written to the session
scratchpad (`blind-policy-037/blind-sample.md`, key beside it) for the joint reading;
passages go to `analyses/2026-10-21-noteworthy-passages.md` before the key is opened.

Read in on October 22 (`analyses/2026-10-22-two-entry-slot.md`): a three-turn recent-return
window turns the seed-7 lock into a four-turn cycle (14 distinct of 39, the most-returned
entry 9 times), so the lock is the rule reading a stable state; a slot carrying the latest
entry beside the chosen older one restores none of the questions, hedges or first-person
openings, so the register effect above belongs to the older entry's presence; and with the
fill tag that slot multiplies the entries quoting a fill of 95% or more.

Corrected the same evening (`analyses/2026-10-22-threshold-battery.md`): the register effect
above belongs to the older entry's presence beside a shown number. The 0.39.0 arms returned the
same older entries in the same order with the context line removed, and the register went back
to the `latest` arms' rates at both seeds (first person 26.1 to 64.9 and 19.6 to 59.5 per 1,000
words, questions 0.6% to 8.2% and 0.3% to 6.7% of sentences, hedges 0.5 to 3.8 and 1.4 to 5.1).
The seven-arm effect recorded in this account is real as measured and was measured with a
number shown in every arm; the older entry alone does not move these markers.

## Replicate

The seed-20260909 `latest` arm rerun with the same config into a new store reproduced all
40 entries word for word (prompt, sampling seed and token counts identical at every turn;
`probes/desktop_arm_identity.py`). With it the identical-prompt turns across the day's
arms number 117 with 2 forks, both in the no-tag arms at retention 0.90.
