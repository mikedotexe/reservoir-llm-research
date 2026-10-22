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
provider forked on 2 of 77 turns on which two arms had the same prompt and the same
sampling seed, and the one fork at a first entry moved the first-person rate by 6 per
1,000 and the self-reference rate from 0.18 to 1.23 per 1,000, the size of some of the
differences in the tables above (`probes/desktop_arm_identity.py`). The direction across
three arms stands as a direction; the sizes at one seed do not separate a policy from a
fork. Two seeds and one model; the 0.37.0 arms, which return older entries by
the reservoir's residual state or by chance at every turn, are the test of whether the
direction holds and whether the chooser matters.

## Pending

The four 0.37.0 arms (state-residual and random-older, both seeds) with the `latest` arms
as their baseline; a blind sample for Mike (`probes/desktop_blind_sample.py`).
A replicate of the seed-20260909 `latest` arm (same config, new store) to measure the
provider's fork rate under the embedding codec over 40 turns, queued after the 0.37.0 arms.
