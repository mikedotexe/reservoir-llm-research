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

## Model arms, seed 20260909 (interim: seed 7 and the 0.37.0 arms pending)

| arm | returned the latest | median age (entries / steps) | distinct returned of 39 | most-returned | I/me per 1,000 | hedges | notice | questions per sentence | self-reference | first-person openings |
|---|---|---|---|---|---|---|---|---|---|---|
| latest | 100% | 0 / 29 | 39 | 1× | 57.5 | 4.5 | 14.0 | 7.7% | 0.24 | 22% |
| state-aligned | 100% | 0 / 29 | 39 | 1× | 57.5 | 4.5 | 14.0 | 7.7% | 0.24 | 22% |
| random | 8% | 9 / 299 | 17 | 7× | 54.2 | 2.0 | 10.4 | 2.9% | 1.79 | 0% |

n = 40 entries per arm, 16,842 words in the first two and 15,054 in the third. With a
random older entry returned, the writing hedges less, asks fewer questions, opens in the
first person less, and refers to the writing itself seven times as often ("By writing
about the act of writing, I am creating a feedback loop where the subject and the object
are identical"; 27 self-reference matches against 4). One seed; the second is running.

## Pending

Seed 7 of the three 0.36.0 policies, then the four 0.37.0 arms (state-residual and
random-older, both seeds) with the `latest` arms as their baseline; the overlap and
embedding-drift readouts; a blind sample for Mike (`probes/desktop_blind_sample.py`).
