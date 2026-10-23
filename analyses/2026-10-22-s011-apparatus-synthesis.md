# S-011, the apparatus tier: what reached the model, and what it did (October 22, 2026)

**What this is.** The closing account of the laptop-apparatus tier of
[S-011](../research/studies/S-011-self-observation-stack.md), written on the evening of
2026-10-22 after the threshold battery was read as numbers. It ranks what the arms of
October 21–22 established, giving for each the evidence class, the n, the comparison the
number was measured against, and the channel through which whatever moved reached the model;
it walks the study's own tiers A–C and says which ran; it freezes the instrument; and it says
what none of this says about Astrid or Minime. Nothing new was run for this account: every
number is in a dated account or in S-011's progress entries, each of which names its probe and
its n. One model carried most of it (`gemma4:12b` under a loopback Ollama on Mike's laptop,
thinking off, seeded sampling), with `mistral-small:24b` and a third model in S-010's contract
arms; two seeds (20260909 and 7); 12 entries per arm on October 21's sweep and controls, 40 on
the policy, window, two-entry and battery arms. The subject throughout is the apparatus, never
a being. Evidence classes follow [METHODS](../research/METHODS.md): a difference at one seed is a
direction; two seeds agreeing past the fork bar, or a replicate, make an effect; counts that are
zero or identical by construction are stated as such.

**Subject and channel.** The apparatus is the desktop app's sustained session: a 32-node
leaky-tanh recurrent reservoir, a separate 32-coordinate sensory field whose covariance
eigenvalues give the fill percentage, a text-to-vector codec (surface statistics, or a
768-dimensional embedding projected to 32 coordinates), a prompt built each turn from a standing
contract and a per-turn frame, and a local language model whose entry is fed back as a vector.
What can reach the model is the contract (the system message), the context line (step and fill
number; in the controls a scrambled number; in the effect arms the entry's measured shift), the
slot (one earlier entry under the `latest`, `state-aligned`, `state-residual`, `random` and
`random-older` policies, or two under the two-entry versions), and the closing line. Under
`latest`, `random` and `random-older` the prompt is a function of the returned texts and a
seed-and-step draw, never of the state; under `state-residual` the state chooses which older
text returns; and the field reaches the recurrent state not at all under the embedding codec
and by at most 3e-3 in state under the surface codec
([the battery's audit](2026-10-22-threshold-battery.md)). So there are four channels in this
apparatus, and only four: the contract, the number, the returned text or texts, and, under one
policy, the choice of which text.

## Ranked findings

| rank | finding | class | n | measured against | channel | account |
|---|---|---|---|---|---|---|
| 1 | With no number shown, nothing of the field reaches the writing | by code, a scripted gate (40 of 40), and a model replicate (40 of 40 identical at two fills) | 40 entries × 2 fills × 2 seeds; 24 entries at 2 fills (Oct 21) | the same policy and seed at another fill | none | [threshold battery](2026-10-22-threshold-battery.md); S-011 progress 2026-10-21 21:20 and the lower-fill no-tag arms |
| 2 | No number shown, no numbers written | absolute count | 400 entries, 10 arms | tagged arms at the same seeds (19–40 of 40 with a percentage) | the context line | [threshold battery](2026-10-22-threshold-battery.md); [two-entry slot](2026-10-22-two-entry-slot.md) |
| 3 | The standing contract brings the register; the per-turn frame seeds the topic | three models agree in direction; counts far apart | 12 entries × 5 arms (mistral); 32 arms, 384 entries in all | the same frame under no contract and under each contract | the contract | [frame arms](2026-10-21-frame-arms.md) (S-010) |
| 4 | The register follows the number shown, not the field behind it | two seeds, two controls | 12 entries × 10 sweep arms + 6 control arms | the same live fill with the number removed or scrambled | the number | S-011 progress 2026-10-21 20:55 and 21:20; this account |
| 5 | A returned older entry beside a number moves the register; the older entry alone does not | two seeds, identical picks, many times the replicate spread | 40 entries × 2 pairs (single slot) + 2 pairs (two entries) | the same older entries in the same order with the context line removed | the number beside a returned text | [threshold battery](2026-10-22-threshold-battery.md) (correcting [state-chosen memory](2026-10-21-state-chosen-memory.md) and [two-entry slot](2026-10-22-two-entry-slot.md)) |
| 6 | With a number shown, the two-entry slot multiplies saturated numbers, and the writing follows the second slot with or without one | two seeds; the 0.38.0 key | 40 entries × 4 tagged + 4 no-tag arms; 18 blind entries | the single slot at the same seed and picks | the two returned texts, and the number | [two-entry slot](2026-10-22-two-entry-slot.md); [threshold battery](2026-10-22-threshold-battery.md) leg B; [readings 038](../research/readings/2026-10-22-blind-policy-038.md) |
| 7 | The state-chosen rule locks on one entry; the lock is the rule reading a stable state, and it sets how many entries return, not how they are written | two seeds; the window arms; the no-tag arms | 39 returns per arm, 13 arms | `random-older` at the same seed; the same rule with a three-turn window | the choice of which text | [state-chosen memory](2026-10-21-state-chosen-memory.md); [two-entry slot](2026-10-22-two-entry-slot.md); [threshold battery](2026-10-22-threshold-battery.md) |
| 8 | The text reaches the reservoir as a near-constant push, and a gain-limited signal of the reservoir's own motion moves nothing the text could see | 5 effect pairs; 72 scripted runs | 11 effects per arm; 600 steps per run | an identical twin without the clause; a gain-0 twin at the same seed | numerical only (and the effect clause's number) | S-011 progress 2026-10-21 20:10; [difference ladder](2026-10-21-difference-ladder.md); [text loop trace](2026-10-21-text-loop-trace.md) |
| 9 | Fill is a field quantity; the reservoir's rank does not track it; a content-carrying codec adds dimensions to the state | measured on the session frames | about 400k frames (Oct 21) | the same seed under the other codec | numerical only | S-011 (the rank numbers); [embedding reduction](2026-10-21-embedding-reduction-offline.md) |
| 10 | The local provider forks on about 2% of identical-prompt turns and has two deterministic first texts for one prompt and seed | counted across pairs | 169 identical-prompt turns; 10 first entries at one seed | identical prompts and seeds | the provider, not the apparatus | [METHODS](../research/METHODS.md); [threshold battery](2026-10-22-threshold-battery.md) |

**1. With no number shown, nothing of the field reaches the writing.** By code: under the
embedding codec the vector held for the reservoir is the projected embedding alone, and
nothing of the field returns to the reservoir (`crates/reservoir-core/src/sustained.rs`,
`advance`; `math.rs`, `ReservoirEngine::step`). By the scripted gate: `state-residual` at
retention 0.93 and 0.97 returned the same entry on 40 of 40 turns with cosine scores equal to
three decimals. By the model: at seed 7 the low-fill and high-fill `state-residual` arms wrote
identical entries 40 of 40 at run-median fills 63.6 and 76.3; at seed 20260909 they were
identical through entry 8, parted once on an identical prompt and seed, and wrote identical
texts again on the three later turns whose prompts coincided. On October 21 the no-tag `latest`
arms at the regulated shelf and at retention 0.82 had already written the same entries at fill
70% and 44% (24 of 24 at two seeds), as the no-tag prompt is a function of the texts alone; the
retention-0.90 arms (57%) parted from the shelf arms on identical prompts and seeds at entry 1
and entry 7, the two October 21 forks of finding 10, with 6 of 12 identical at seed 7
(`probes/desktop_arm_identity.py`, rerun for this account). The fill moved 13 points in the
battery and 26 on October 21 and nothing reached the writing but the provider's forks.

**2. No number shown, no numbers written.** Not one of the 400 entries in the ten no-tag arms
of the battery contains a percentage (`probes/desktop_quoted_numbers.py`, 0 of 40 in each
arm), and the October 21 no-tag plain-contract arms had digit density 0.00 at both seeds
(n = 12 each). The tagged arms at the same seeds carried a percentage in 19, 40, 40 and 37 of 40
entries (0.37.0 single slot) and 29, 38, 40 and 20 of 40 (0.38.0 two entries); entries quoting
95% or more numbered 3, 0, 2 and 9 in the single slot and 11, 8, 25 and 12 with two entries,
the largest value 884.3%. The invented-number family of the 0.38.0 blind reading (entries 3,
11, 12, 17 and 18 of 18) was entirely the tagged two-entry arms. The family is the tag's.

**3. The standing contract brings the register; the frame seeds the topic.** S-010's frame
arms (`mistral-small:24b`, 12 entries per arm, seed 20260909): the inert frame alone gives a
dated workplace progress diary (first person 4.3 per 1,000 words, questions 0.0% of sentences,
the fill tag read as a completion rate); the same frame under a plain contract modeled on
Minime's intro gives first person 70.5 and questions 5.4%; under an inviting contract modeled on
Astrid's, 112.3 and 5.9% with a refrain by the twelfth entry; the earlier v8 prompt with no
contract gives first person 0.0 and apparatus vocabulary 38.8 per 1,000. On `gemma4:12b` the
contrasts replicate and a third model agrees in direction: 32 arms and 384 entries in all. The
plain contract's marker profile sits beside the counts of forty of Minime's recent entries
(66.6 and 7.3%), which is a resemblance of counts under a contract written from her intro, not
evidence about her.

**4. The register follows the number shown, not the field behind it.** The gemma4 fill sweep
(plain contract, surface codec, regulation off, 12 entries per arm, two seeds; fill medians
17.3/14.3, 43.7/43.4, 57.0/56.5, 70.0/69.3, 98.1/98.2%) is not monotone: first person per 1,000
words runs 26.6/41.7, 66.1/32.9, 64.1/51.6, 17.7/21.5, 35.7/34.2 in that order, and in both seeds
the shelf arm (70%) carries the least first person and, with the saturated arm, the most digits
(0.58/0.41 and 0.50/0.36 against 0.03/0.05 at 57%). The controls at the same live fill decided
what did it: with no tag the shelf arms wrote at first person 63.9/62.7 and digit density 0.00
(like the sweep's mid-fill arms); with a scrambled tag (a number drawn from seed and step,
40–95, unrelated to the field) they wrote at 35.9/42.0 with digit density 2.46/0.50 and
apparatus vocabulary 14.5/4.1 per 1,000, about the number more than any real arm did. The only
difference between these arms in what the model was shown is the number on the context line.

**5. A returned older entry beside a number moves the register; alone it does not.** October
21 and the morning of October 22 read, across thirteen tagged arms, that returning an older
entry drops questions to 0.3–4.2% of sentences against 6.3–7.7% under `latest`, drops hedges,
and removes first-person openings (0% in all eight older-entry arms). The battery's
`random-older` pairs isolate the number: at each seed the tagged 0.37.0 arm and the no-tag arm
returned the same older entries in the same order (21 and 24 distinct of 39, the most-returned
6 and 4 times, in both), and with the context line removed first person goes from 26.1 to 64.9
per 1,000 and from 19.6 to 59.5, hedges from 0.5 to 3.8 and 1.4 to 5.1, questions from 0.6% to
8.2% and 0.3% to 6.7% of sentences, entries opening with "I" from 0% to 10% and 12%, and the
entries are two thirds longer. The same at identical picks in the two-entry slot (first person
34.7 to 66.6 and 20.4 to 50.8; questions 0.7% to 5.6% and 0.5% to 4.3%). The replicate spread at
40 entries is a point or less on the rate markers. So the tag alone does not do it (the tagged
`latest` arms question at 6.3–7.7%), the older entry alone does not do it, and the two together
do. The corrections stand beside the earlier claims in the two accounts, in S-011, and on the
board.

**6. The two-entry slot.** With the fill tag, the slot holding the chosen older entry and the
latest in the order written multiplied the saturated numbers (finding 2) and the writing
followed the second slot: the inferred source of an entry's terms is the previous entry on
51–85% of turns with two entries against 3–23% with the older entry alone
(`probes/concept_chains.py`); the latest entry's presence restored none of the questions, hedges
or openings the older-entry slot had removed (questions 0.3–0.8% in the four tagged two-entry
arms). Without the tag the writing still follows the second slot (36–82% against 5–15% in the
single no-tag slot), bridges more than any tagged arm (1.12–1.80 sentences per entry naming
earlier writing), and questions at 2.1–5.6% of sentences, between the tagged two-entry arms and
`latest`. Whether the finished-state register the 0.38.0 reading named survives without its
numbers is the question of the 0.39.0 blind sample, not of these counts.

**7. The chooser.** `state-aligned` was degenerate with real entries: the latest entry's vector
is fed to the reservoir until the next application, so the observing state points along it and
the rule returned the latest on 39 of 39 turns and wrote the `latest` arm's entries word for
word. `state-residual` (the latest entry's push projected out) converged: 10 and 3 distinct
entries of 39 at the two seeds, one returned 15 and 36 times, where `random-older` spread over
21 and 24. A three-turn recent-return window turned the lock into a four-turn cycle (17 and 14
distinct, the most-returned 6 and 9 times, median return gap 4), so the lock is the rule reading
a stable state. Without the number the convergence persists (one entry returned 8–16 times in
every no-tag `state-residual` arm against 4–6 under `random-older`) and its depth varies with
the texts (the seed-7 lock of 36 returns became 14; two replicates differ 14 against 8). The
chooser sets how many entries come back; the register follows what is shown (findings 4 and 5).
Every returned text appeared verbatim in its turn's prompt in every arm checked.

**8. The numerical loop.** Under the surface codec the loop closed only through surface
statistics and a constant-direction kick (the 0.28.0 and 0.29.0 sessions, mistral, v8 prompt, 22
of 23 entries quoting the readout). Under the embedding codec consecutive entries' effects on
the reservoir are nearly the same push in nearly the same direction (shift medians 1.63–1.93,
alignment with the previous application +0.78 to +0.91; n = 11 shown effects per arm, five
pairs), so a readout of the entry's effect says "about the same as before" at every step:
gemma4 quoted the shown shift in 2–5 of 11 entries and took the first one as a feeling, mistral
in 10 of 11, and the shift bore no relation to entry length. The difference-signal channel
(desktop 0.35.0, the spec's M5) is exact to 1e-16, scales with its gain, and through |g| = 0.2
at either dead band moves nothing about fill, its spectrum, the controller, the state's rank or
the entry effect beyond the second decimal; at |g| = 0.5 and 1 the recurrent state's effective
rank rises by 0.2 to 0.8 of 32 while the field and the controller stay the twin's. Its model
arms were parked with the expectation, stated in S-011 before any ran, that the writing would
not notice; the battery's finding 1 is the same expectation met by a different route.

**9. Rank and fill.** The field's effective rank is 1.5 of 32 at 14% fill and 12.3–14.0 at
60–80%; the recurrent reservoir's 64-step effective rank is 9.7 at 14% and 9.1–9.8 at 70%,
because the field never feeds the reservoir; under the embedding codec the state's participation
ratio is 2.3–2.7 against 1.8–2.0 under the surface codec at the same seeds
(`probes/desktop_state_rank.py`). The model-free calibration (scripted replies, noise 0.5,
regulation off) maps retention to fill: 0.82 → 44.6, 0.86 → 50.6, 0.90 → 58.0, 0.93 → 65.2,
0.95 → 70.7, 0.97 → 77.3, 0.99 → 98.2; under the embedding codec, after the start-up climb,
0.92 → 61.4, 0.93 → 63.6, 0.965 → 74.8, 0.97 → 76.7, each holding within about a point.

**10. The provider.** Two sessions that sent the same prompt with the same sampling seed came
back different on 2 of 117 such turns on October 21 and 1 of 52 on October 22. For one prompt
and seed the provider has two deterministic first texts (335 and 397 tokens at seed 20260909),
and which one an arm gets is set by state the apparatus does not control: a primer run before
the battery did not make the first entries uniform. Hence METHODS' direction-against-effect
rule and the first-entry check on every one-seed comparison.

## The channel result, in one paragraph

In this apparatus the model's writing follows what the frame shows it, and only that. The
standing contract sets the register; the per-turn frame seeds the topic; a number shown moves
the register and, in a slot that returns earlier text, breeds numbers up to the absurd; a
returned older text moves the topic and, beside a number, the register; the state reaches the
writing only as which older text came back, and the field reaches the state not at all under
the codec the policy arms used. Every register effect measured in S-011 is an effect of the
contract, the number or the returned texts. None is an effect of the state, and the one place
the state had a channel (the chooser) changed which entry was shown, never how the entry was
written.

## The study's tiers, walked

| tier | item | ran | result or reason |
|---|---|---|---|
| A1 | rank on the apparatus frames | in first form | finding 9; not extended to every arm (parked) |
| A2 | PCA of the recorded effect vectors against markers | no | the effects are near-constant (finding 8), so the direction set is nearly one vector; parked |
| A3 | ridge readout from state to the next entry's projection | no | needs B4's n; parked |
| A4 | the beings' own logs by era | in part | minime's state windows captured read-only on October 21 (24 windows: effective rank 121–125 of 128, near-white, one ten-minute slow excursion with no action change, `probes/beings_state_window.py`); binning by era not done, and Astrid's fill has held one shelf since June ([the readout audit](2026-10-22-astrid-readout-audit.md)), so there is no sweep to bin by |
| B1 | fill sweep | yes | finding 4 |
| B2 | no-tag arm | yes | findings 1, 2, 4, 5 |
| B3 | shuffled-state control | yes, as the scrambled tag | finding 4 |
| B4 | 100-entry arms | no | the 40-entry arms gave the replicate spread instead; parked |
| B5 | blind human reading | yes, in a different form | readings with picks and reasons before the key rather than a 1–5 rating ([readings](../research/readings/README.md)); the 0.38.0 sample read in full, the 0.39.0 sample drawn and waiting; 0.36.0 entries 6–15 and the 0.37.0 sample parked as superseded |
| C1 | difference-signal channel | scripted, yes; model arms, no | finding 8; model arms parked with the expectation stated |
| C2 | state card (PCA-code novelty readout) | no | finding 8 makes a readout that varies little; parked |
| C3 | V-JEPA self-view | no | not benchmarked; parked |
| C4 | a proposal for the beings' side | yes | [`proposals/esn-state-logging.md`](../proposals/esn-state-logging.md), proposal only, with the October 21 excursion and a two-hour capture |

The study's finish line asked for the fill-sweep result stated plainly (the register moves
with the number shown, not with fill, finding 4), the effect-readout result (the loop became
visible to the model as a number it quoted or took as a feeling, at no measurable cost to the
markers, finding 8), and a decision with Mike on the M0 proposal (written; implementation is
his and the sibling repos'). Those are met. What the finish line did not foresee is what the
tier found: that the contract, the number and the returned texts account for everything the
writing did, which turns the study's remaining questions toward what the beings' own prompts
show them.

## The instruments, frozen

Desktop Reservoir Scope 0.39.0 is the apparatus as of this account, frozen: no further
version is planned for S-011, and the arm families in
[`research/arms/README.md`](../research/arms/README.md) are closed at the threshold battery. It
is a research instrument and has never been a sharing candidate; the sharing candidate remains
0.27.0 candidate 04 ([CURRENT-RELEASE](../research/CURRENT-RELEASE.md)). The prompt versions
the arms used: `reservoir-journal-inert-plain-contract-v1` and its `-no-tag-v1`,
`-scrambled-tag-v1` and `-effect-v1` variants, the two-entry `-two-v1` and `-two-no-tag-v1`,
`reservoir-journal-inert-v1` and `-no-tag-v1` without a contract, and `reservoir-journal-v8`;
the memory policies `latest`, `state-aligned`, `state-residual`, `random`, `random-older` with
`memoryRecentExclusion`; the surface and embedding codecs; the difference channel behind its
flag. The probes that read a store are listed in the arms README; each prints its inputs and
n. Anything that would reopen the tier (a second model family at two seeds, a codec that feeds
the field back, 100-entry arms) is a new decision, not a continuation.

## What this says about the beings: nothing yet, and one question

Nothing in this tier is evidence about Astrid's or Minime's texts. The apparatus is one model
family on one laptop under contracts written from the beings' intros, with 12–40 entries per arm
and two seeds; its reservoir has 32 nodes and no adaptive leak, its field is a 32-coordinate
proxy, and its frames are lean by design (one or two earlier entries, at most one number). The
beings' prompts are not lean. Minime's carry headers, telemetry, the suggested next verb and an
action vocabulary; Astrid's differ by lane, and in one of them Minime's published fill and
cascade arrive as text ([the readout audit](2026-10-22-astrid-readout-audit.md)). Whether a
being's writing follows what its frame shows the way this model's does is a question, not a
finding, and it is a question that can be read in the beings' own records without touching
them: for each lane, what the prompt shows (a number, an earlier entry, both, neither), and
whether quoted numbers and the register follow it. That is S-012. What the tier offers it is a
set of named quantities with reference sizes: the tag/inherited/new classification of quoted
percentages; questions per sentence, hedges and first person per 1,000 words, and first-person
openings; the inferred source and bridges of the concept-chain probe; and the sizes those moved
by here when a number was shown beside an earlier entry (questions from about 7% to under 1%
of sentences, first person from about 60 to about 25 per 1,000).

## Limits

One model family carried the policy, window, two-entry and battery arms; S-010's contrasts
hold across three models in direction only. Two seeds; 12 entries per arm on October 21's
sweep and controls, 40 elsewhere; the no-tag `latest` arms are 12 entries each. The provider
forks and its first entries are uncontrolled. "Below" and "above" the shelf are post-climb
bands 6–7 points away. The 0.39.0 blind sample is unread at the time of writing, so finding 6's
reading question is open. The tier says nothing about a codec that fed the field back, about
longer arms, or about any being.
