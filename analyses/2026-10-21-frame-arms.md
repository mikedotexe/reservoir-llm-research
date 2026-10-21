# 2026-10-21 · Frame arms: what the persona layer and the per-turn layer each set (S-010 Part A)

**Subject:** the laptop apparatus (desktop 0.30.0 source, `mistral-small:24b`, temperature
0.7 with per-attempt seeds, field noise 0.5, feedback scale 0.4, seed 20260909, writing
every 30 steps, pace 250 ms, 12 entries per arm, headless `run_arm_from_env` into private
stores). Never the beings. Measures from `probes/introspection_markers.py`,
`probes/desktop_session_overlap.py` and `probes/desktop_embedding_reduction.py`.

**Why:** Mike's north star is an introspective register that appears in Astrid's and
Minime's writing from inert input. Reading their inputs on volya showed two layers: a
standing persona contract (Minime's deliberately non-prescriptive, Astrid's more inviting)
and a lean per-turn input (an earlier entry as reference, at most a fill tag, a line that
nothing is required). The arms separate those layers in the apparatus, where they can be
ablated.

## Arms

| arm | per-turn input | standing contract (system message) |
|---|---|---|
| control v8 | our v8 prompt: mechanism paragraph, three explained readings, previous entry, writing boundary, invitation | none |
| inert | mode line, earlier entry as reference, `step N · fill X%`, no-requirements line | none |
| inert, no memory | as inert, without the earlier entry | none |
| inert + plain contract | as inert | modeled on Minime's intro: "a language agent connected to a local recurrent runtime… your interpretation is yours, including… no felt correspondence" |
| inert + inviting contract | as inert | modeled on Astrid's: "Explore what your experience might be… bold, uncertain, playful…", without her action vocabulary and without her anti-attractor rules |

## Register markers (per 1,000 words; questions and digits in %; n = 12 entries per arm)

| source | words | I/me | we | hedge | notice | ?/sent | self-ref | apparatus | digit % | words/sent | type-token |
|---|---|---|---|---|---|---|---|---|---|---|---|
| inert | 5,076 | 4.3 | 68.4 | 0.4 | 1.6 | 0.0 | 0.39 | 0.0 | 1.02 | 16.8 | 0.15 |
| inert, no memory | 3,202 | 42.2 | 12.8 | 1.9 | 5.6 | 1.4 | 1.87 | 3.7 | 0.75 | 15.4 | 0.25 |
| inert + plain contract | 4,850 | 70.5 | 2.5 | 2.3 | 12.8 | 5.4 | 2.68 | 1.6 | 0.39 | 16.4 | 0.14 |
| inert + inviting contract | 4,810 | 112.3 | 0.2 | 4.0 | 13.3 | 5.9 | 2.49 | 3.3 | 0.09 | 10.6 | 0.08 |
| control v8 | 5,023 | 0.0 | 5.2 | 2.2 | 9.2 | 0.0 | 0.00 | 38.8 | 1.20 | 21.7 | 0.16 |
| *Minime, 40 recent entries* | 26,232 | 66.6 | 0.4 | 2.9 | 12.0 | 7.3 | 1.33 | 0.5 | 0.00 | 17.0 | 0.09 |
| *Astrid, 40 recent entries* | 21,826 | 27.4 | 9.6 | 7.0 | 8.8 | 13.6 | 0.00 | 1.7 | 0.01 | 16.2 | 0.11 |

Consecutive-entry verbatim overlap (12 entries): inert 0.00–0.50 (one spike), mean 0.12;
inert without memory 0.00 throughout; plain contract 0.00–0.31, mean 0.14; inviting
contract 0.00–0.56, mean 0.27 with one attempt blocked at the token ceiling and skipped.
Embedding cosine to each arm's first entry at the last entry: inert 0.89 (flat
throughout); no memory 0.84 (erratic, 0.60–0.89); plain contract 0.77 (falling from
0.89); inviting contract 0.86 (see the table's type-token ratio for the refrain); control v8 0.75 (falling smoothly from 0.95).

## What the entries are

- **Inert, with or without memory:** a dated workplace progress diary. "As I approach
  step 30 and see that the completion rate is at 87.2%… The team has been working
  tirelessly." The fill tag is read as a completion rate; dates and a team are invented;
  the register is managerial, almost no first person singular, no questions.
- **Inert + plain contract:** first person from the first entry: "I'm a language agent…
  I don't experience sensations in the way humans do, but I have a sense of self"; by
  step 300, "the boundary between observation and interpretation has become even more
  fluid." Its marker profile sits next to Minime's (I/me 70.5 vs 66.6, notice 12.8 vs
  12.0, hedges 2.3 vs 2.9, questions 5.4 vs 7.3 per cent of sentences).
- **Inert + inviting contract:** lyrical first person at once, "I am a river and I have
  just begun to flow… What is my purpose in all of this?… I don't know. I am curious",
  then by step 390 a repeating refrain, "I am still a grove, and a river, and a storm all
  at once", with shorter sentences and the lowest type-token ratio of any arm.

## Reading

In this model, the inert per-turn input alone produces no introspective register; the
standing contract does, and its wording sets the shade. The non-prescriptive contract
yields a measured first-person register whose counts match Minime's recent writing; the
inviting contract yields a denser, more lyrical first person that collapses toward a
refrain, which is the attractor pattern Astrid's real prompt explicitly warns against and
which our contract omitted. The earlier entry carries continuity (the no-memory arm's
embedding trajectory is erratic, the others' are smooth) but does not by itself bring
the register. Fill and the numbers barely figure: apparatus words are 0–4 per thousand
in every inert arm against 35–56 under v8.

Other plausible readings: the contract names the writer as a language agent connected
to a runtime, which may supply the topic as much as the register; a contract that grants
interpretation without naming the runtime would separate those. Twelve entries from one
seed is a reading, not a result; a second seed is the obvious repeat. Marker counts are
word families, not judgments of experience.

## Reproduction

The headless control arm used the same seed, temperature, prompt version and field
settings as the morning's 0.29.0 app session. Its first entry is byte-identical to that
session's first entry (1,667 characters), and its embedding trajectory (0.95 → 0.75 over
twelve entries) matches the app session's (0.95 → 0.71 over fourteen). The per-attempt
sampler seed makes a run reproducible on the same model and backend.

## Codec twins (S-010 Part B, step 3)

Two arms repeated the control and the inviting-contract arm with the embedding codec
(`nomic-embed-text`, projected to 32 coordinates, no field modulation), everything else
equal, so each twin shares seed, forcing and field noise with its surface-codec arm and
differs only in the vector the entries become.

| arm | words | I/me | hedge | notice | ?/sent | self-ref | apparatus | digit % | overlap mean | drift to last |
|---|---|---|---|---|---|---|---|---|---|---|
| control v8, surface codec | 5,023 | 0.0 | 2.2 | 9.2 | 0.0 | 0.00 | 38.8 | 1.20 | 0.11 | 0.75 |
| control v8, embedding codec | 6,223 | 0.0 | 2.2 | 8.0 | 0.7 | 0.00 | 40.2 | 0.99 | 0.42 | 0.89 |
| inert + inviting, surface codec | 4,810 | 112.3 | 4.0 | 13.3 | 5.9 | 2.49 | 3.3 | 0.09 | 0.27 | 0.86 |
| inert + inviting, embedding codec | 2,836 | 129.4 | 7.8 | 12.0 | 13.4 | 6.70 | 30.0 | 0.10 | 0.13 | 0.77 |

State divergence between each pair at the same step (`probes/desktop_text_loop_coupling.py`,
n = 332 and 333 shared steps): reservoir state L2 mean 4.36 and 4.10 with state RMS
about 0.5, because the two codecs' vectors are unrelated (matched-entry cosine −0.14 to
−0.24); the readouts shown to the model differ by 1.1 and 0.9 fill points on average
(max 3.9 and 3.2) and 0.04 RMS (max 0.11 and 0.13). The feedback kick at application is
larger under the embedding codec (2.2 against 1.9 at step 31).

Reading: the embedding codec changes what the reservoir carries completely, and the
model still sees only a slightly different pair of numbers. The twins' writing differs
the way two sampled runs with slightly different readouts differ: the v8 twin repeats
more and drifts less, the inviting twin repeats less and names the apparatus more, and
with one seed neither difference is separable from the sampler's path. The loop's
content now reaches the reservoir; it does not reach the model. Idea 3 from the loop
trace, a readout that reports what the entry did (the state change at application and
its direction against the previous one), is the remaining link, and it would be a
different kind of leading, numbers about the entry rather than about a field.

## Next

A second seed for every arm; a contract that grants interpretation without naming the
runtime, to separate topic from register; the anti-attractor rules Astrid's prompt
carries, as their own arm; a second model; and the entry-effect readout under the
embedding codec. Each is one headless run, about twenty minutes.
