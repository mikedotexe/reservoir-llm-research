# The threshold battery: fill without a number, and the two-entry slot without one (October 22, 2026)

**Subject and channel.** Ten gemma4:12b arms of the laptop apparatus (desktop 0.39.0, plain
contract, embedding codec, 40 entries each, seeds 20260909 and 7), read beside the 0.37.0
single-slot policy arms and the 0.38.0 two-entry arms at the same seeds. No context line was
sent in any of the ten: what reached the model at each turn was the text of one earlier entry
(leg A) or of two (leg B, the chosen older entry first and the latest second, marked only by
order), and nothing else. No step, no fill number. The reservoir's state reached the model only
as which older text came back, and under the embedding codec the field cannot reach that choice
(the audit below), so in leg A the two fills sent identical prompts by construction and the fill
pairs measure the provider, not the field. Configurations in `research/arms/configs/` (`thr-*`,
`bothnotag-*`, `calib-embed-*`, `gate-*`, `prime-notag-gemma4`); outputs in the session
scratchpad under `arms/logs/` (`analyze-v039.out`, `v039-choice.out`, `v039-identity.out`,
`v039-early-pair1.out`, `quoted-v039.out`, `concept-chains-v039.out`, `v039-fill.out`,
`calib-embed.out`, `v039-gate-choice.out`). Numbers first, texts unread; the blind sample is
read with Mike before its key (`research/readings/2026-10-22-blind-threshold-039.md`, pending
at the time of writing). One model, two seeds; a difference at one seed is a direction, two
seeds agreeing past the fork bar an effect (`research/METHODS.md`).

| arm | slot | policy | fill (median over the run) | seeds | compared with |
|---|---|---|---|---|---|
| `thr-lo-state-residual-gemma4[-seed7]` | one entry, no number | state-residual | retention 0.93 fixed: 64.6, 63.6 | 20260909, 7 | `thr-hi-*` at the same seed (the fill pair) |
| `thr-hi-state-residual-gemma4[-seed7]` | one entry, no number | state-residual | retention 0.97 fixed: 77.3, 76.3 | 20260909, 7 | `thr-lo-*` at the same seed |
| `thr-lo-random-older-gemma4[-seed7]` | one entry, no number | random-older | 0.93 fixed: 64.8, 64.2 | 20260909, 7 | `policy-random-older-gemma4[-seed7]` (tagged, the same picks: the number alone) |
| `bothnotag-state-residual-gemma4[-seed7]` | two entries, no number | state-residual | 0.955 regulated: 70.8, 70.2 | 20260909, 7 | `both-state-residual-gemma4[-seed7]` (tagged) |
| `bothnotag-random-older-gemma4[-seed7]` | two entries, no number | random-older | 0.955 regulated: 70.8, 70.6 | 20260909, 7 | `both-random-older-gemma4[-seed7]` (tagged, the same picks); `thr-lo-random-older-*` (the latest's presence, no number) |

Fill medians are over the whole run (1,201–1,204 frames per arm, `v039-fill.out`), start-up
climb included; the calibration's post-climb medians were 63.6 and 76.7 (S-011, 15:00).

## Why the battery, and what it could find

Mike's question of 13:20: with no fill shown, and the field held marginally below and
marginally above its target, does the writing differ. The by-construction answer for three of
the five policies was already in hand: under `latest`, `random` and `random-older` the no-tag
prompt does not depend on the field at all (October 21: 24 of 24 entries identical at fill 70%
and 44%; October 22: `random-older`'s pick sequence identical under the single and the
two-entry slot, because the draw is seed-and-step). So fill could reach the writing without a
number only through `state-residual`'s choice of the older entry, and leg A routes the question
there. Leg B follows the 0.38.0 key: the invented-number, finished-state family of that blind
sample was entirely the tagged two-entry arms, and the only thing the new prompt version removes
from those arms is the context line.

## Calibration, gate and channel audit, written before any model arm was read

Four 12-entry no-tag `latest` arms, embedding codec, fixed retention, seed 20260909
(`calib-embed-*`). After the start-up climb (steps 180–361) each series holds within about a
point of its median: retention 0.92 gives 61.4 (59.4–64.9), 0.93 gives 63.6 (61.5–67.1), 0.965
gives 74.8 (73.6–78.7), 0.97 gives 76.7 (74.9–80.5), against the regulated shelf's 70.4–71.0
(67.9–73.3 over 1,200 steps, two 0.38.0 arms). The plan's thresholds (a median at most 62 and
at least 78) assumed the whole-series spread of 7–9 points, which is the climb; with the
post-climb spread at 1–1.5 points the rule was restated before any battery arm ran: the
calibration point nearest the shelf on each side whose post-climb range is clear of the
regulated band, 0.93 below and 0.97 above.

The gate: `state-residual` on scripted texts at retention 0.93 and 0.97, 40 entries each,
surface codec (`gate-lo/hi-state-residual-scripted`): the same entry returned on 40 of 40
turns, the cosine scores equal to three decimals. The code says why
(`crates/reservoir-core/src/sustained.rs`, `advance`; `math.rs`, `ReservoirEngine::step`): the
recurrent state reads the forcing, the held text vector and its own seeded noise; the sensory
field reads the same input with its retention, and nothing of the field returns to the
reservoir. Under the surface codec `codec::feedback` scales four of 48 coordinates by the
field's head share, entropy and tail shares (the gate's states differed by at most 3e-3, no pick
changed); under the embedding codec the held vector is the projected embedding alone, so
retention cannot reach the state, the choice or the prompt. Stated at 15:05, before leg A was
read: the two fills under `state-residual` send identical prompts, each pair is an
identical-prompt replicate of 40 turns, and any parting is a fork.

## Leg A: the fill pairs (`probes/desktop_arm_identity.py`, 40 entries per arm)

Seed 7: the low-fill and high-fill `state-residual` arms are identical in every entry, 40 of
40, prompt and text, at run medians of 63.6 and 76.3. Seed 20260909: identical through entry 8,
parted at entry 9 on an identical prompt and an identical sampling seed (a fork), and because the
no-tag frame renders only the returned text, the two arms sent identical prompts again on three
later turns (17, 18 and 29, when both returned one of the eight shared entries) and wrote
identical texts on all three: 12 identical-prompt turns, 1 fork, 11 of 40 entries identical.
Across the two pairs, 52 identical-prompt turns and 1 fork. Prediction 1 as first written
(a parting on a differing pick within ten turns) did not happen and could not have; the amended
form (any parting is a fork) is what the pairs showed. The fill moved 13 points and nothing
reached the writing.

The seed-20260909 pair is two replicates from entry 9 on, which gives the first replicate spread
at 40 entries this apparatus has: first person 67.4 against 69.3 per 1,000 words, hedges 2.8
against 2.7, notice words 12.5 against 11.8, questions 7.6% against 6.7% of sentences,
self-reference to the writing 1.66 against 1.10, entries opening with "I" 0% against 22%,
bridges 1.23 against 0.95 per entry, words 18,690 against 19,056; the chooser 7 against 8
distinct entries of 39, the most-returned 14 against 8 times. The rate markers move by a point
or less between replicates; the openings count and the lock's depth move a lot.

**Prediction 2.** The fill-to-fill differences are zero at seed 7 and the replicate spread at
seed 20260909, inside the policy-to-policy difference at one fill (`state-residual` against
`random-older` at 0.93: first person 67.4 against 64.9 and 60.5 against 59.5, questions 7.6%
against 8.2% and 8.6% against 6.7%, openings 0% against 10% and 20% against 12%) and inside the
seed-to-seed difference (`state-residual` at 0.93: 67.4 against 60.5, hedges 2.8 against 5.1,
openings 0% against 20%). Held. The seed-7 lock reappeared as convergence but not at its tagged
depth: 12 distinct entries of 39 with one returned 14 times, against 3 and 36 under the tag
(`probes/desktop_memory_choice.py`); the prediction's bar (at most 10 distinct, one returned 12
or more times) is met on the second count and missed on the first.

## The number: quoted percentages (`probes/desktop_quoted_numbers.py`)

Not one of the 400 entries in the ten no-tag arms contains a percentage: 0 of 40 in each arm.
In the tagged arms at the same seeds, entries with any percentage number 19, 40, 40 and 37 of 40
(0.37.0 single slot) and 29, 38, 40 and 20 of 40 (0.38.0 two entries); entries quoting 95% or
more number 3, 0, 2 and 9 in the single slot and 11, 8, 25 and 12 with two entries, the largest
value 884.3%. **Prediction 3** held in its strongest form: the saturated-number family is the
tag's, entirely, and with no number shown the model writes no numbers at all.

## The number beside the older entry is what moved the register

The `random-older` pairs are the cleanest comparison in the battery: at each seed the tagged
0.37.0 arm and the no-tag leg A arm returned the same entries in the same order (21 and 24
distinct of 39, the most-returned 6 and 4 times, in both), and their prompts differ in the
context line alone. `probes/introspection_markers.py`, n = 40 texts per arm:

| arm | words | I/me | hedges | notice | questions per sentence | digit share | opens with "I" |
|---|---|---|---|---|---|---|---|
| `latest`, no tag, seed 20260909 (n = 12) | 5,443 | 63.9 | 4.4 | 9.4 | 8.1% | 0.00 | 33% |
| `latest`, no tag, seed 7 (n = 12) | 5,483 | 62.7 | 3.8 | 9.7 | 5.7% | 0.00 | 17% |
| `latest`, tagged, seed 20260909 (0.37.0) | 16,842 | 57.5 | 4.5 | 14.0 | 7.7% | 0.11 | 22% |
| `latest`, tagged, seed 7 (0.37.0) | 15,290 | 56.7 | 4.8 | 11.6 | 6.3% | 0.12 | 20% |
| `random-older`, tagged, seed 20260909 | 10,969 | 26.1 | 0.5 | 13.0 | 0.6% | 0.66 | 0% |
| `random-older`, no tag, seed 20260909 (`thr-lo`) | 18,001 | 64.9 | 3.8 | 11.4 | 8.2% | 0.00 | 10% |
| `random-older`, tagged, seed 7 | 10,380 | 19.6 | 1.4 | 8.2 | 0.3% | 0.67 | 0% |
| `random-older`, no tag, seed 7 (`thr-lo`) | 15,886 | 59.5 | 5.1 | 9.3 | 6.7% | 0.00 | 12% |
| `state-residual`, no tag, 0.93, seed 20260909 | 18,690 | 67.4 | 2.8 | 12.5 | 7.6% | 0.00 | 0% |
| `state-residual`, no tag, 0.97, seed 20260909 | 19,056 | 69.3 | 2.7 | 11.8 | 6.7% | 0.00 | 22% |
| `state-residual`, no tag, 0.93 and 0.97, seed 7 (identical) | 16,370 | 60.5 | 5.1 | 11.3 | 8.6% | 0.00 | 20% |
| two entries, `random-older`, tagged, seed 20260909 | 14,110 | 34.7 | 1.0 | 8.5 | 0.7% | 0.26 | 0% |
| two entries, `random-older`, no tag, seed 20260909 | 17,921 | 66.6 | 4.0 | 9.9 | 5.6% | 0.00 | 0% |
| two entries, `random-older`, tagged, seed 7 | 13,943 | 20.4 | 1.3 | 7.4 | 0.5% | 0.42 | 0% |
| two entries, `random-older`, no tag, seed 7 | 17,299 | 50.8 | 2.3 | 8.7 | 4.3% | 0.00 | 5% |
| two entries, `state-residual`, no tag, seed 20260909 | 19,342 | 68.0 | 1.1 | 4.4 | 2.1% | 0.00 | 0% |
| two entries, `state-residual`, no tag, seed 7 | 16,916 | 66.6 | 4.0 | 9.4 | 4.1% | 0.00 | 12% |

With the same older entries in the same order and the number removed, first person goes from
26.1 to 64.9 per 1,000 and from 19.6 to 59.5, hedges from 0.5 to 3.8 and 1.4 to 5.1, questions
from 0.6% to 8.2% and 0.3% to 6.7% of sentences, entries opening with "I" from 0% to 10% and
12%, and the entries are two thirds longer (18,001 against 10,969 words, 15,886 against 10,380).
Two seeds, the same direction, by amounts many times the replicate spread: an effect. The same
holds in the two-entry slot at identical picks (first person 34.7 to 66.6 and 20.4 to 50.8,
questions 0.7% to 5.6% and 0.5% to 4.3%).

So the no-tag older-entry arms write at the `latest` arms' rates: questions 6.7–8.6% of
sentences in leg A against 5.7–8.1% under `latest` with no tag and 6.3–7.7% with one; hedges
2.7–5.1 against 3.8–4.8; first person 59.5–69.3 against 56.7–63.9; openings with "I" 0–22%
against 17–33%. **This corrects the October 21 and 22 attribution.** The register effect read
across thirteen arms (fewer questions, hedges and first-person openings when an older entry
returns) was measured in tagged arms against tagged and untagged `latest` arms; it is the
older entry's presence beside a shown number, not the older entry's presence. The tag alone
did not do it (the tagged `latest` arms question at 6.3–7.7%) and the older entry alone does not
do it; the two together do. The 0.38.0 result that the latest entry's presence restores nothing
stands as measured, inside tagged arms, and now reads as: with a number shown beside any older
entry, the measurement register holds whether or not the latest is there. The corrections are
recorded beside the earlier claims in `analyses/2026-10-21-state-chosen-memory.md`,
`analyses/2026-10-22-two-entry-slot.md` and S-011.

## Leg B: two entries, no number

The writing still follows the second slot: the inferred source is the previous entry on 36%,
72%, 82% and 64% of turns in the four arms (`probes/concept_chains.py`; 51–85% with the tag,
5–15% in leg A's single slot). Both texts reached the model verbatim on 39 of 39 turns. Against
the single-slot no-tag `random-older` arm at the same seed and picks (the latest's presence
with no number): questions 5.6% against 8.2% and 4.3% against 6.7%, openings 0% against 10%
and 5% against 12%, bridges 1.80 against 1.25 and 1.12 against 0.55 per entry, first person
66.6 against 64.9 and 50.8 against 59.5. A direction at both seeds, small next to the tag's,
toward fewer questions and more bridges when the latest entry is also shown. **Prediction 4**
held on bridges (1.12–1.80 per entry in leg B against 0.25–1.38 in the tagged two-entry arms
and 0.58–1.00 under no-tag `latest`) and failed on the register: the two-entry no-tag arms do
not keep the tagged slot's 0.3–0.8% questions; they sit at 2.1–5.6%, between the tagged two-entry
arms and `latest`. The tagged two-entry arms' 39-entry chain on one term ("longer", 2–40 in
three of four) is absent; one no-tag two-entry arm carries a 39-entry chain on "watching". The
chooser under the two-entry frame with no number: 13 distinct of 39 (one returned 10 times,
median age 3 entries) at seed 20260909 and 6 distinct (one returned 16 times) at seed 7, against
9 and 8 distinct (21 and 12 times) with the tag. Whether the finished-state register persists
without its numbers is a question for the blind reading, not for these counts.

## The chooser without the number

Convergence persists under `state-residual` in every no-tag arm (one entry returned 8, 10, 14,
14 and 16 times against 4 and 6 for `random-older`), and its depth varies with the texts: the
seed-7 single-slot lock that returned one entry 36 times with the tag returned one 14 times
without it, and the two seed-20260909 replicates differ 14 against 8. The lock is the rule's,
as the window arms showed; how deep it goes is a property of the particular entries, not of
the seed or the fill.

## The provider

Forks: 1 in 52 identical-prompt turns across the fill pairs, in line with October 21's 2 of
117. First entries: the primer (one entry, the same first prompt, run before the ten) wrote the
335-token text that the October 21 no-tag arm and the first calibration arm wrote; of the five
seed-20260909 arms, the first two wrote the 397-token text the later calibration arms wrote and
the other three wrote the primer's; all five seed-7 arms wrote one 297-token text. The primer
did not make the seed-20260909 first entries uniform, and the calibration's reading (fresh load
against warm) does not fit the battery's order: arms three, seven and eight followed other arms
and wrote the fresh-load text. The laptop's Ollama log records no load or unload events, so the
mechanism is unknown; what is established is that for one prompt and seed this provider has two
deterministic first texts and the choice between them is set by state we do not control. For
comparisons at one seed this means the first entries must be checked (`desktop_arm_identity.py`
does) and arms whose first entries differ compared only on what they share: the leg A
`state-residual` against `random-older` comparison at seed 20260909 differs from entry 1 for this
reason, while at seed 7 it is identical through entry 4 and parts at 5 on the first differing
pick, as designed.

## The blind sample

The chain's draw (`--per 2`, first entries skipped) landed on entry 2 and entry 40 of each arm,
and entry 2 is shared by every arm at one seed whose prompts are still identical then (all five
at seed 7, two and three at seed 20260909), which the identity probe shows without reading a
text. That draw was set aside unread and the probe gained `--skip N`
(`tests/test_desktop_blind_sample.py`); the sample for the reading is entries 10 and 40 of nine
arms (the seed-7 high-fill arm left out as byte-identical to its low-fill twin), 18 entries, all
distinct by hash, seed 39, in `blind-policy-039/` in the session scratchpad. Read with Mike
before the key; record in `research/readings/2026-10-22-blind-threshold-039.md`. [Read the
same evening by Claude alone, at Mike's delegation, notes before the key: the finished-state
register survives without numbers, in three of the nine step-1200 entries (two from two-entry
arms, one from a single-slot arm), its clearest instance and its explicit refusal being the two
random-older two-entry arms at the two seeds; the picks came from both legs; the record has
the key.]

## Limits

One model, two seeds, 40 entries per arm. "Below" and "above" are post-climb bands 7 and 6
points from the shelf, and the chooser's sensitivity to retention is nil under this codec by
construction and at most 3e-3 in state under the surface codec at these two retentions; the
battery says nothing about a codec that fed the field back. The no-tag `latest` arms are 12
entries each, so the "latest arms' rates" above rest on 24 entries plus the two tagged 40-entry
arms. The provider's first-entry state is uncontrolled. Nothing here is evidence about the
beings' texts.

## What reached the model, and what the battery offers

With no number shown, nothing of the field reaches the writing in this apparatus: not through
the context line (removed), not through the state-chosen return (no path under the embedding
codec; 40 of 40 identical at seed 7 at two fills), and the October 21 controls had already shown
the same under `latest`. The field reaches the writing only as the number shown, and the number
did more than was credited: it carried the register effect of the older-entry slot, and in the
two-entry slot it bred the saturated numbers. What the older entry does on its own is now a
reading question: the no-tag older-entry arms write at the `latest` arms' rates on every marker
while following an older topic, and whether that reads as the shape Mike named ("what they're
perceiving and observing, and just 'being'") or as something else is what the 18-entry sample
is for.
