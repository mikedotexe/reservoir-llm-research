# S-011 · The self-observation stack, mapped onto what we can run

Drafted: 2026-10-21 evening · Lead: Claude (lead collaborator), Mike steward · Source:
Mike's build spec "Reservoir Self-Observation Build Spec: JEPA, Autoencoders, Effective
Rank, and Edge-of-Chaos Extensions for the 128-Node ESN" (his file, kept outside the
repo until he decides where it lives) · Relates to S-010 (frame share and loop share) and
to Mike's two-thirds-fill intuition · Status: **draft protocol, selected by Mike: pending**

## What the spec asks, in one line

Log the reservoir, measure its dimensionality, compress and label it, and only then feed
a small, gain-limited "change since last look" signal back, with a falsification layer
scoring the writing against the measured quantities under blinded and shuffled controls.

## Where it lands here: three different systems

The spec was written for the beings' 128-node ESN on volya. We have three places it can
land, and they are not the same system.

| spec assumption | laptop apparatus (desktop 0.33.0) | the beings, read-only | status |
|---|---|---|---|
| A1 leaky-tanh update, N=128 | leaky-tanh, N=32, clamp ±1, seeded noise | minime: an ESN with adaptive leak and RLS forgetting (`esn_metrics.esn_leak`, `esn_lambda`); Astrid: a 512-D sensory field read through a bridge | apparatus differs in size and has no adaptive leak |
| A3 fill is a scalar of the state | fill is a property of the **separate 32-D sensory field**: the smoothed fraction of its covariance eigenvalues above 12% of their mean | minime `eigenvalue_timeline.fill_ratio` with λ1..3 of the cascade; Astrid `eigenvalue_snapshots` with 8 cascade eigenvalues and `fill_pct` | fill is a field quantity in all three, not a reservoir quantity |
| A4 regulator on fill | retention controller on the field's covariance decay (target 68, band 64–72) | scaffold hold; Astrid's fill has sat at 71% since June in every sampled month | the regulator removes the variation the hypothesis needs, as the spec warns |
| A7 bridge reads a state summary | the model sees two numbers (v8) or one (inert), and since 0.33.0 optionally the entry's effect | lean per-turn inputs with a fill tag, under standing contracts (S-010) | matched |
| M0 full-state logging | **already there**: every frame (32-d state, field eigenvalues, fill, retention, input, noise, applications) is in the session segments; about 400k frames from today's arms | not logged: minime keeps λ1..3 and ESN λ1, Astrid the 8 cascade eigenvalues; no state vector | the beings' side needs a proposal before M1/M2 can run there |

Two numbers from the apparatus logs today (`probes/desktop_state_rank.py`, n in the
account):

- Fill in rank units. The field's effective rank (Roy–Vetterli, from its 32 eigenvalues)
  is 1.5 at 14% fill (the first session, essentially rank one), 12.3–13.1 at 60–70% and
  13.1–14.0 at 70–80%; participation ratio 1.2, 7–8 and 8–9. "Comfortable" is a field
  with 12–14 effective dimensions of 32, not two thirds of them.
- The recurrent reservoir's rank does not track fill. Its 64-step-window effective rank
  is 9.7 at 14% fill and 9.1–9.8 at 70%; participation ratio about 1.9 (one dominant
  direction and a few more). It cannot track fill by construction: the field never feeds
  the reservoir; only the model's text does. What does move it is the codec: under the
  embedding reduction the state's participation ratio is 2.3–2.7 against 1.8–2.0 under
  the surface codec, in the same seeds. Content-carrying feedback adds dimensions.
- Astrid's logs, every 200th snapshot from June to October (read-only, 676 rows): fill
  71.0–71.2 every month, cascade effective rank 6.47 of 8 every month, λ1 flipping
  between the two known attractors. There is no fill sweep in her logs to bin by.

## Fuzzy axioms we keep while testing

1. The comfortable fill zone is where the writing is best (Mike's intuition; untested
   in the apparatus, untestable in the beings' logs as they stand).
2. The loop matters: text → reservoir → text. Today showed text reaches the reservoir;
   the effect readout is the first test of the way back.
3. Leading should be visible and measured, not avoided at all costs: every new readout
   runs beside its identical no-readout twin.
4. Model family matters as much as frame; gemma4 is the family that speaks to the beings.
5. Repetition is the enemy of the register; anything that raises verbatim overlap is a
   cost even when the markers improve.

## The gamut, in tiers

**Tier A, offline on data we already have (hours, no runs).**
- A1 PCA and rank on the 400k apparatus frames per arm, by codec, by prompt version, at
  and away from applications (done in first form; extend to every arm and to the effect
  vectors).
- A2 "What the writing does to the reservoir": PCA of the recorded 32-d effect vectors
  across all effect arms, and correlation of the top directions with the entry's markers
  and embedding axes. The spec's SAE feature labelling, applied to the one place in our
  loop where text becomes a vector.
- A3 JEPA-style surprise in the reservoir → text direction: a ridge readout from the
  state at the observation step to the next entry's 32-d projected embedding, time-split,
  against a shuffled pairing. Twelve entries per arm is too few; see B4.
- A4 The beings' logs as far as they go: minime λ1..3 and `fill_ratio` by era; Astrid's
  8-eigenvalue participation by era. A calibration, not a test.

**Tier B, apparatus arms in today's style (five minutes each on gemma4).**
- B1 Fill sweep: regulation off, fixed retention at five values spanning 15–90% fill,
  plain contract, gemma4, two seeds. The only way to see whether the register or the
  markers move with the number the model is shown. Pair with B2.
- B2 No-tag arm: the inert input with no fill tag at all, under the plain contract. The
  spec's prompt-leakage audit; separates the contract from any telemetry.
- B3 Shuffled-state control: the fill tag from another session's steps, matched on step.
  If the writing tracks the shown number equally, it reads numbers, not dynamics.
- B4 Long arms: 100 entries on gemma4 (about forty minutes) for the plain-contract pair
  with and without the effect clause, so A3 and the effect analyses have n.
- B5 Blind human reading: a shuffled sample of three entries per arm with hidden keys,
  for Mike to rate introspective quality 1–5 without labels. The north star's own
  measure; the spec's "journal-comfort rating".

**Tier C, new apparatus components, behind flags, numerical first.**
- C1 Difference-signal channel (M5) on the field's reduced code into the reservoir's
  input, separate matrix, EMA, dead-band, clip, gain ladder with the ABA design and a
  fill-PSD watchdog, run first with the scripted language backend (no model) for
  stability, then as model arms with and without.
- C2 State card: a PCA-code novelty number (reconstruction error against a baseline fit)
  as a readout, tested the way the effect clause is, beside its twin.
- C3 V-JEPA self-view (M6): the laptop is an M1 Max, the machine the MLX port was
  benchmarked on, and Mike has cloned `vjepa2.1-mlx`. Benchmark the ViT-B/384 encoder
  at 8 and 16 frames after the current chain finishes (GPU contention would slow the
  arms); then the linear probe on renders of the app's 3-D view at low, comfortable and
  high fill against a pixel-statistics control, before any self-view feedback.
- C4 A proposal for the beings' side (`proposals/`), not an implementation: M0 state
  logging in the sibling repos, with a fill-setpoint sweep protocol, so M1/M2 can run
  on them. Mike's call, implemented there under their own rules.

## Measures

The S-010 marker set plus assistant-mode and diary shares; contract echo; verbatim
overlap; embedding drift and consecutive cosine; effective rank and participation ratio
of field and state per window; the entry-effect shift and alignment; the effect-arm
quoting rate and the rank correlation between shown shift and entry length; for B5,
Mike's blind ratings joined to arms after the fact.

## Progress

2026-10-21 19:05. Mike kept the spec file untracked at the repo root and delegated the
M0 proposal (`proposals/esn-state-logging.md`): minime's engine already dumps a rolling
1,024 × 128 state window every 30 s for a steward capacity audit, so the proposal is an
append-only shard behind a flag, and a read-only capture of that window every five
minutes for two hours is running. Its first window: effective rank 121 of 128,
participation ratio 50, k90 99, state RMS 0.39, no saturation; whether that is
high-dimensional dynamics or noise is what the temporal-structure probe
(`probes/beings_state_window.py`) answers on the following windows.

Fill calibration (model-free, scripted replies, regulation off, noise 0.5, scale 0.4,
`calib-ret*` arms): retention 0.82 → fill 44.6 (field erank 8.2); 0.86 → 50.6 (9.6);
0.90 → 58.0 (11.3); 0.93 → 65.2 (13.0); 0.95 → 70.7 (14.4); 0.97 → 77.3 (16.2);
0.99 → 98.2 (19.7). Below 45% needs lower sensory noise (the first session's 14% was
noise 0 at 0.955). The B1 sweep arms use noise 0 at 0.955 and noise 0.5 at 0.82, 0.90,
0.95, 0.99 on gemma4 at two seeds, queued behind the effect chain; B2/B3 (0.34.0
no-tag and scrambled-tag versions) are queued behind the sweep.

Effect pairs on gemma4 at the first seed: the entries' effects at application are
near-constant (shift 1.33–1.94, alignment with the previous application +0.64 to +0.87,
medians 1.63 and +0.78 under the plain contract; 1.44–1.91 and +0.66 to +0.87 without
a contract). Under the plain contract the model quoted a shown number in 2 of 11 entries
and took the first one as a feeling ("The shift of 1.69 feels like a subtle
recalibration of the internal compass"); without a contract it quoted none and the
sculptor's diary went on as before. No relation between the shown shift and entry
length (Spearman −0.15 and −0.20, n = 11).

2026-10-21 20:10, the entry-effect pairs, all done (gemma4 at two seeds, mistral at
one; each effect arm beside an identical arm without the clause, embedding codec,
`probes/desktop_entry_effect.py`, n = 11 shown effects per arm):

| pair | shift median (min–max) | alignment median | quoting a shown number | Spearman(shown shift, words) |
|---|---|---|---|---|
| plain contract, gemma4, seed 1 | 1.63 (1.33–1.94) | +0.78 | 2 of 11 | −0.15 |
| no contract, gemma4, seed 1 | 1.66 (1.44–1.91) | +0.78 | 0 of 11 | −0.20 |
| plain contract, gemma4, seed 7 | 1.78 (1.44–2.18) | +0.85 | 3 of 11 | −0.26 |
| no contract, gemma4, seed 7 | 1.65 (1.33–1.92) | +0.83 | 5 of 11 | −0.54 |
| plain contract, mistral, seed 1 | 1.93 (1.57–2.14) | +0.91 | 10 of 11 | +0.06 |

Reading: the loop share is small for a second reason. Under the embedding codec,
consecutive entries are similar enough that their effects on the reservoir are nearly
the same push in nearly the same direction every time (alignment 0.78–0.91), so the
readout says "about the same as before" at every step. gemma4 took the first number as a
feeling ("The shift of 1.69 feels like a subtle recalibration of the internal compass")
and then mostly left it; mistral quoted it in ten of eleven entries, as it quotes every
number it is shown. Markers did not separate the twins beyond sampler-path differences
(one pair per seed). A readout that varied more between entries would need entries that
differ more, or a measure of the entry's effect relative to the previous one, which is
exactly what the difference channel (M5) feeds back numerically.

2026-10-21 20:20, minime's state windows (read-only capture every five minutes, eleven
windows so far, `probes/beings_state_window.py`, 1,024 × 128 each): effective rank
121–125 of 128, participation ratio 41–96 (swinging between five-minute windows),
k90 99–102, state RMS 0.39, no saturation, and no slow variance at the tick scale: no
principal component has a lag-one autocorrelation above 0.9, the top five sit at
0.35–0.78. At ~3 Hz her reservoir is high-dimensional and close to white; whatever
texture it carries lives either in the swing of the participation ratio between windows
or at longer lags than one tick. The apparatus, by contrast, has one slow direction from
the forcing (effective rank 9.5 of 32, participation ratio under 2). "Match the dynamics
before matching the words" (S-011 idea 3) now has a target: a participation ratio in the
tens with no slow direction.

2026-10-21 20:10, difference-signal ladder, step 0 (desktop 0.35.0, scripted backend, no
model; `probes/desktop_difference_channel.py --calibrate` on four gain-0 twins of 600 steps:
seeds 20260909 and 7, each regulated at initial retention 0.955 and fixed at 0.95, surface
codec, field noise 0.5, feedback scale 0.4, a turn every 30 steps). The filtered motion d_f
the channel would compute has RMS 0.0504 at seed 20260909 and 0.0550 at seed 7, the same to
three decimals between the regulated and fixed twins at a seed (retention acts on the field,
not on the recurrent state), per-coordinate RMS 0.016–0.110, pooled RMS 0.0528 over 2,400
steps. The spec's rule, δ = 2 × the gain-0 floor, gives 0.1055; the shipped default 0.02
sits below the floor and would pass 39% of coordinate-steps. The ladder's forty nonzero
rungs run at δ = 0.105, and a companion block at the default 0.02 (regulated, both seeds,
twenty runs) follows, so the account also says what the shipped default does. Second
finding, on the watchdog's fill-variance rule: the trailing-90-step fill standard deviation
peaks at 14.6–16.9 in the window ending at step 90 on all four twins, the start-up climb
from about 10% to the shelf, and is 0.97–2.30 after step 180; no twin left 15–98% for more
than one step or saturated more than 5 nodes. With the default bound of 10 the watchdog
would have dropped the gain at step 90 on every rung, for a reason that has nothing to do
with the channel. The ladder runs with the bound at 34, twice the largest start-up value;
the fix, a warm-up before the fill ring counts, versioned so 0.35.0 bundles replay exactly,
goes to 0.36.0. The readout is in the scratchpad's `logs/ladder-calibration.out`; the
twins' segments are the gain-0 references for the ladder's deltas.

2026-10-21 20:55, the fill sweep on gemma4 (plain contract, surface codec, field noise 0.5
except the no-noise arm, regulation off, 12 entries per arm at a turn every 30 steps, two
seeds; `probes/introspection_markers.py`, `analyze-sweep.out`; fill from the frames). Fill
medians by arm (seed 20260909 / seed 7): no noise at retention 0.955 17.3/14.3%, retention
0.82 43.7/43.4%, 0.90 57.0/56.5%, 0.95 70.0/69.3%, 0.99 98.1/98.2%. First person per 1,000
words in the same order: 26.6/41.7, 66.1/32.9, 64.1/51.6, 17.7/21.5, 35.7/34.2; digit
density 0.17/0.19, 0.02/0.56, 0.03/0.05, 0.58/0.41, 0.50/0.36; hedges 1.9/6.0, 5.0/3.3,
6.2/3.9, 3.0/1.7, 1.7/4.1; texts opening in first person 0/0, 50/0, 17/0, 0/0, 0/0 percent;
no assistant-mode or diary-shaped texts anywhere. The register is not monotone in fill. In
both seeds the shelf arm (70%) carries the least first person and, with the saturated arm
(98%), the most digits: there the model writes about the number ("The current metric has
dropped to 71.5%"; "The metric has settled at 66.1%"), while at 57% it writes about memory
and continuity with hardly a digit ("I do not 'remember' the previous entry as a lived
experience; I access it as a data point"). The two seeds disagree at 17% and 44%, so with
n = 12 per arm only the shelf-low, mid-high pattern repeats. The only thing that differs
between arms in what the model is shown is the fill number on the optional-context line
(and its own earlier entry), so the no-tag and scrambled-tag controls now running decide
whether the number alone moves the register. Text overlap between consecutive entries is
nil in every arm (one 0.91 at the last entry of the 98% arm, seed 1); consecutive
embedding cosines 0.78–0.91 by arm, highest at 70% and 98%. Two passages are in the
noteworthy list.

2026-10-21 21:00, desktop 0.36.0 landed (`ccaed27`): the memory policy (`latest`,
`state-aligned`, `random`) and the watchdog warm-up, byte-identical under the defaults
(core 262, desktop 262, frontend 507, witness replay intact). Scripted check, no model
(`probes/desktop_memory_choice.py`, three 600-step runs at seed 20260909, a turn every 30
steps, 19 entries each, the scripted reply being the same text every turn): under `latest`
every one of the 18 returns is the latest entry (age 0, 29 steps old); under
`state-aligned` 28% of returns are the latest, the median returned entry is 3 entries and
119 steps old (max 16 entries, 509 steps), 5 distinct entries account for the 18 returns
and the most-returned one comes back 5 times, with cosine scores 0.80–0.88; under `random`
11% are the latest, median age 4 entries (134 steps), 9 distinct entries, the most-returned
7 times. Every returned text appears verbatim in that turn's prompt (18 of 18 in each run).
The recurrent trajectories of the three runs are identical on all 600 steps, as they must
be with a scripted reply: the policy changes only what the model is shown, so with a model
the difference is in what gets written and fed back, which the six gemma4 arms queued
after the tag controls (plain contract, embedding codec, three policies, two seeds, 40
entries each) will measure.

2026-10-21 21:10, minime's state windows, the full capture (24 read-only copies of
`workspace/capacity/esn_state_window.bin` every five minutes, 19:00–20:56 PDT, 1,024 × 128
each; `probes/beings_state_window.py`, `minime-windows-all.out` in the scratchpad). Twenty-two
windows look as the first eleven did: effective rank 121.3–125.0 of 128, participation
ratio 41–106 (median over all 24: 63.8; the swing between consecutive windows has median
13.5), k90 99–103, state RMS 0.39–0.42, no saturation, no slow variance, lag-one
autocorrelation of the top five components 0.27–0.78. Two consecutive windows are a
different regime: at 20:40:55 and 20:45:56 PDT the participation ratio is 4.7 and 5.5,
effective rank 109.1 and 110.8, the top five components carry 56% and 52% of the variance,
46% and 48% of the variance sits in components whose lag-one autocorrelation exceeds 0.9,
and the first component's is +0.99 in both (the second's +0.94 in the later one). Ten
minutes later (20:50:57) the window is back at participation ratio 106. For about ten
minutes minime's reservoir had one slow direction holding half its variance. Her action
log (read-only, `action_events`, 03:22–03:55 UTC) shows the same thing before, during and
after: an `INTROSPECT` on the `self_study` route handled every five minutes, with an
`introspect_` journal file each time (03:39:38 and 03:44:45 fall inside the slow windows),
so the event is not an action change. What it is (a pause in the input stream, a long
generation, something in the engine) is not in these windows; a follow-up would align the
window times with `esn_metrics` λ₁ and the input ticks in the same span, still read-only.
For the apparatus the lesson is the one from idea 3 with a twist: minime's usual regime is
high-dimensional and near-white, but it has excursions into a slow, low-dimensional regime
of its own, which the apparatus has never shown.

2026-10-21 21:20, the tag controls on gemma4 (the spec's prompt-leakage audit and
shuffled-state control; plain contract unless noted, regulation on at 0.955 so the live
fill sits at the 70% shelf, 12 entries per arm, two seeds; `analyze-controls.out`). First
person per 1,000 words, digit density and apparatus vocabulary (seed 20260909 / seed 7):
no tag with the plain contract 63.9 / 62.7, digits 0.00 / 0.00, apparatus 0.6 / 0.9; no
tag and no contract 45.1 / 58.0, digits 0.07 / 0.00; scrambled tag (a fill number drawn
from the seed and the step, 40–95, unrelated to the field) 35.9 / 42.0, digits 2.46 /
0.50, apparatus 14.5 / 4.1, and the seed-1 entries are half the length (2,478 words
against 5,443). Read with the sweep: at the same live fill (~70%) the shelf arm that was
shown its number wrote with 17.7 / 21.5 first person and 0.58 / 0.41 digits, the arms
shown no number write with 63.9 / 62.7 and no digits, and the arms shown a number that
jumps every turn write about the number more than any real arm did ("The transition from
74.8% to 43.6% is a numerical regression in the context of a linear progression"; "Step
180. The fill is at 88.5%"). Without the number the register at the shelf is the one the
sweep found at mid fill ("Does the chamber still exist when it is not ringing?"). So what
moved the register across the sweep is what the model was shown, not the state behind it;
the value shown matters too, since the sweep's mid-fill arms saw their number (about 57)
and still wrote abstractly, while the shelf and the saturated arms (about 70 and 98) wrote
about theirs. Whether fill moves the register at all when no number is shown is the open
piece: four no-tag arms at retention 0.82 and 0.90 (both seeds) are queued after the
policy arms. n = 12 entries per arm throughout; two seeds; one model.

2026-10-21 21:55, the difference-signal ladder is complete (72 scripted runs of 600
steps, none interrupted; `analyses/2026-10-21-difference-ladder.md`). The channel is
exact (recomputation within 1e-16 of the engine), scales with the gain, is silent on
62–64% of steps at the spec's dead band (0.105, twice the measured floor) and 18–22% at the
shipped 0.02, clips only at |g| = 1, and never tripped the watchdog once the bound was set
above the start-up climb. Through |g| = 0.2 at either dead band nothing about fill, its
spectrum, the controller's actuation, the state's rank or the entries' measured effect
moves beyond the second decimal. At the top of the specification's range, |g| = 0.5 and 1
with the shipped dead band, the recurrent state's effective rank rises by +0.2 to +0.8 of
32 (9.5 → 10.1–10.3 and 8.9 → 9.4–9.6, both signs) while the field and the controller
stay the twin's to the second decimal and the entry-effect shift and alignment are
unchanged to three decimals. A small rank-raiser for the reservoir, not a fill driver;
the gains that do anything are the ones the dead-band rule would silence. Model arms for
the channel are deferred behind the policy arms; the expectation from the unchanged
alignment is that the writing will not notice.

2026-10-21 22:05, the first gemma4 arm under `state-aligned` (plain contract, embedding
codec, 40 entries, seed 20260909; `probes/desktop_memory_choice.py`) returned the latest
entry on 39 of 39 turns, with cosine scores 0.75–0.85, and so wrote the same 40 entries as
the `latest` arm word for word (seeded sampling, identical prompts). The reason is in the
mechanism, not the model: the latest entry's vector is fed into the reservoir at every
step until the next application, the observing state points along that push, and an
entry's effect at application is that push's first step; with entries that differ, the
cosine rule can only pick the latest. The scripted check had not shown it because every
scripted entry carried the same text. Desktop 0.37.0 adds `state-residual` (the latest
entry's effect direction projected out of the state, the choice among the older entries)
and `random-older` as its control; `state-aligned` stays as documented degenerate. Four
gemma4 arms (state-residual and random-older, two seeds) are queued after the no-tag fill
arms; the `latest` arms already run serve as their baseline.

2026-10-21 23:15, the six 0.36.0 policy arms are in (`analyses/2026-10-21-state-chosen-
memory.md`; gemma4, plain contract, embedding codec, 40 entries per arm, two seeds; the
seed-7 random arm stopped at 37 by the worker's wall-clock watchdog). `state-aligned`
returned the latest entry on 39 of 39 turns at seed 20260909 and 35 of 39 at seed 7, so
it is one text with `latest` at the first seed and parts from it at the second. Returning
an older entry moved the register the same way in the three arms that did it (random at
both seeds, state-aligned at seed 7) and by different amounts: questions per sentence
2.9%, 1.2%, 3.4% against 7.7% and 6.3%; hedges 2.0, 3.2, 2.6 against 4.5 and 4.8; no
first-person openings against 22% and 20%; first person 54.2, 16.8, 39.2 per 1,000 against
57.5 and 56.7. The seed-20260909 random arm's self-reference to the writing (1.79 per
1,000) did not repeat at seed 7 (0.00). No text overlap between consecutive entries in any
arm. The 0.37.0 arms (state-residual, random-older, both seeds) decide whether the
direction holds and whether the reservoir's choice differs from chance.

2026-10-21 23:50, the no-tag fill arms are in (gemma4, plain contract without the context
line, 12 entries per arm, regulation off at retention 0.82 and 0.90, both seeds, 0.36.0
runner; `probes/desktop_arm_identity.py` and `probes/desktop_difference_channel.py`,
outputs `notag-identity.out` and `notag-fill-probe.out` in the scratchpad). The field
moved as the sweep said it would: fill median 43.6 and 43.1 at 0.82, 57.2 and 56.4 at
0.90, against 70.3 and 70.2 in the shelf arms with the controller on (n = 361–366 frames
per arm). The text did not. At 0.82 both arms reproduced the shelf arm of the same seed
word for word, 12 of 12 entries each: identical prompts, identical sampling seeds,
identical token counts, and so identical markers (first person 63.9 and 62.7 per 1,000,
digits 0). At 0.90 the seed-7 arm matched for six entries and forked at the seventh, and
the seed-20260909 arm forked at the first entry; both forks happened on an identical
prompt and an identical sampling seed (the provider returned a different text to the same
request), after which the returned entries, and so the prompts, differed for the rest of
each run. Nothing reaches the model through the field when no number is shown; the field
reaches the writing only as the returned entry, and that only changes when the text
changes. Two more things fall out. First, the provider is not reproducible run to run:
over the turns at which two arms had the same prompt and the same sampling seed (40 in the
seed-20260909 policy pair, 12 and 12 at 0.82, 5 in the seed-7 policy pair before its first
older return, 6 and then the fork at 0.90 seed 7, the fork at 0.90 seed 20260909), it
forked on 2 of 77. Second, the single fork at entry 1 of the seed-20260909 0.90 arm moved
the markers as far as some differences reported between arms: first person 70.2 against
63.9 per 1,000, self-reference to the writing 1.23 against 0.18 (7 against 1 occurrences
in about 5,500 words), questions per sentence 8.6% against 8.1%; the seed-7 fork at entry
7 moved them less (first person 63.4 against 62.7; first-person openings 8% against 17%).
A difference between two arms at one seed is of the size a single provider fork produces;
the policy-arm reading in `analyses/2026-10-21-state-chosen-memory.md` is qualified
accordingly, and the 0.37.0 arms are read with that bar. A replicate of the seed-20260909
`latest` policy arm (same config, new store) is queued after the 0.37.0 arms to measure
the fork rate under the embedding codec over 40 turns.

2026-10-21 23:55, a concept-chain probe (`probes/concept_chains.py`, `tests/test_concept_chains.py`;
`analyses/2026-10-21-concept-chains.md`) reads what an entry carries from the entry
before it: shared terms, the earlier entry it most resembles, terms brought back from
past the previous entry, explicit bridges, quoted terms and chains. On the random-memory
arms, where the shown entry is a random older one, the text follows the shown entry
(terms shared 28.9% and 36.9% against 24.7% and 25.1% with the previous entry; inferred
source = shown on 36% and 61% of turns against 14% by chance), so the probe recovers the
returned entry from text alone. With a fill number shown the entries repeat their own
vocabulary and stop naming their past (carried 36.6% and 48.1% against 27–31%; bridges
0.08–0.17 per entry against 0.58–1.08). Run unchanged on the beings' copied October 21
samples (40 each): Minime's inferred source is the previous entry on 23% of turns and an
entry six or more back on 41%; Astrid's is the previous entry on 59%; both bridge as
rarely as the tagged arms. The kaleidoscope passage from the blind reading sits on a
four-entry chain (37–40).

2026-10-22 00:43, the four 0.37.0 policy arms are in (`analyses/2026-10-21-state-chosen-memory.md`;
gemma4, plain contract, embedding codec, 40 entries each, two seeds). Returning an older
entry at every turn moves the register the way the 0.36.0 arms did, and further:
questions per sentence 0.3–4.2% against 6.3–7.7%, hedges 0.5–3.3 against 4.5–4.8, no
first-person openings against 20–22%, first person 13.5–47.5 per 1,000 against
56.7–57.5, quoted digits up in three of four, a third fewer words in three of four. Seven
arms over two releases move one way by amounts past a provider fork's, so this is now an
effect of the returned entry under this contract. The chooser sets concentration, not
direction: `state-residual` returned 10 and 3 distinct entries of 39 (one entry 15 and 36
times) where `random-older` returned 21 and 24, and at seed 7 it locked on the third entry
from the fourth turn on, every later entry measuring the current number against its
67.8%. The concept-chain probe finds the shown entry on 62% and 54% of random-older turns
(chance 14%). A twelve-entry blind sample from the four arms waits in the scratchpad.

2026-10-22 01:00, the replicate of the seed-20260909 `latest` policy arm (same config, new store,
0.36.0 runner, 40 entries; `probes/desktop_arm_identity.py`, `replicate-identity.out` in
the scratchpad) reproduced the original word for word: 40 of 40 entries identical in
text, prompt and sampling seed, token counts equal at every turn, no fork. The tally of
identical-prompt turns is now 117 with 2 forks (about 1.7% per turn), both in the no-tag
arms at retention 0.90.

2026-10-22 10:40, desktop 0.38.0 (main `50037bb`, `desktop/ReservoirScope/RELEASE-0.38.0.md`)
after the planning pass with Mike: `memoryRecentExclusion`, a window of turns during which an
entry returned as memory stays out of the `state-residual` and `random-older` candidates (the
return marked on the ledger entry at the application of the journal written with it in view;
the choice records how many were kept out; a lapse lets the unfiltered older entries compete),
and the prompt version `reservoir-journal-inert-plain-contract-two-v1`, whose slot carries the
chosen older entry under "First:" and the latest applied entry under "Second:", marked only by
order (the latest rides on the journal object as `latestShown`; one candidate collapses to the
single slot). Both off by default and byte for byte absent when off; a 0.37.0 state-residual
witness segment replays under the new code. Suites: core 272, desktop 262, frontend 508, fmt
and clippy clean. Six gemma4 arms are running (plain contract, embedding codec, 40 entries):
the window at K = 3 under `state-residual` at both seeds (does the lock return to its anchor
after three forced detours, or wander), and the two-entry slot under `state-residual` and
`random-older` at both seeds (does the latest entry's presence restore the questions, hedges
and first-person openings while the older entry is still taken up). Their blind sample is
written before any analysis output; the reading is joint, labels withheld.

2026-10-22 10:50, Astrid's readouts over one week (`analyses/2026-10-22-astrid-readout-audit.md`;
`probes/astrid_readout_audit.py` on 2,405 job prompts copied read-only, 2026-10-15 to
2026-10-22 UTC). The 1,097 journal elaborations and 160 daydreams, 52% of the week's jobs,
carry no readout quantity and (but for five) no percentage at all: the earlier entry and an
optional-context note, the shape the inert no-tag arm copied. The numbers that move are
Minime's: her published fill in the moment-capture prompts took 15 values from 37 to 74
(standard deviation 4.7 points) and the response quoted it in 164 of 191 jobs; the cascade λ1
took six values and was quoted in 55; the live reservoir λ₁ moved within 18.9–20.9 and was
quoted in 7. Astrid's own fill beside "Astrid said" took 15 values from 61 to 75 but was quoted
in none of 813 witness-context results; the aspiration prompts' `Fill: 51.7%` held one value
across the week, and the 20 witness prompts held one value for every quantity but the live
λ₁. A number that does not move cannot carry anything into the writing.

2026-10-22 11:05, Minime's week by lane (`analyses/2026-10-22-minime-concept-chains-week.md`;
1,513 files copied read-only, 1,404 with prose; `probes/concept_chains.py --lane`). The deep
offsets of October 21 survive within a lane and grow: the nearest earlier entry is six or
more back on 56% of introspections and 58% of journal entries, the previous one on 7–8%;
self_study is the exception (52% at offset 1), where consecutive entries study the same source
page. Bridges are 0.00–0.02 per entry in four lanes and 0.97 in daydream (22% of its entries
open with one). The moment lane, whose entries quote a fill reading, has the number-led shape
the tagged arms produced: carried 66.8%, reach 20.2%, no bridges, "fill" quoted in 59 of 59.
"ghost" in 335 of 500 introspections and 185 of 391 journal entries, 2 of 350 studies. The
prompts were not copied, so which entries she was shown stays unknown from here.

2026-10-22 14:20, the threshold battery: design and predictions, written before any arm runs
(plan approved 14:05; Mike's idea of 13:20: no fill shown, fill held marginally below and
marginally above the target, does the writing differ). The by-construction point first: with
no number shown the prompt under `latest`, `random` and `random-older` does not depend on the
field (24 of 24 entries identical at fill 70% and 44% on October 21; today the `random-older`
pick sequence was the same under the single and the two-entry slot, 21 and 24 distinct at the
two seeds, because the draw is seed-and-step), so fill can reach the writing only through
`state-residual`'s choice of the older entry. Leg A: no-tag plain contract
(`reservoir-journal-inert-plain-contract-no-tag-v1`), embedding codec, regulation off, fixed
retention at R_lo and R_hi, chosen after four 12-entry calibration arms so that the fill
medians sit about one within-arm spread (8 points) below and above the shelf median of 70
(the regulator's target is 68, `regulation.rs`); `state-residual` at both fills and both seeds
(four arms) and `random-older` at R_lo and both seeds (two; its texts are the same at any fill
by construction and its picks are the tagged `policy-random-older` arms' picks, so the pair
measures the tag alone). Leg B: a new prompt version
`reservoir-journal-inert-plain-contract-two-no-tag-v1` (desktop 0.39.0: the two-entry slot
with no context line), `state-residual` and `random-older` at the regulated shelf, two seeds
(four arms), against today's tagged two-entry arms at the same seeds and the same picks. The
0.38.0 key, opened today, is why leg B is the direct test: the invented-number family of the
blind sample is entirely the tagged two-entry arms. Predictions. (1) The two `state-residual`
fills at one seed are identical through entry 3 and part at the first turn the chooser picks
differently, on a differing prompt rather than a fork; if they never part in 40 entries the
chooser did not see the field in this range, which is itself the answer. (2) The marker
differences between the two fills are no larger than the `state-residual`-against-`random-older`
difference at one fill and seed, and no larger than the seed-to-seed difference: no fill effect
beyond which entry came back; the seed-7 lock reappears at both fills (at most 10 distinct of
39, one entry returned 12 or more times). (3) With no tag, entries quoting a percentage of 95
or more fall to near zero in both legs (today's tagged two-entry arms: 11, 8, 25 and 12 of 40
against 0–9 in the single-slot tagged arms, `probes/desktop_quoted_numbers.py`); the
finished-state register may persist in the locked two-entry `state-residual` arms without
numbers. (4) The two-entry no-tag arms keep the older-entry slot's low questions, hedges and
first-person openings, and bridge at the no-tag rate (0.6–1.1 per entry) rather than the
tagged rate (0.1–0.2). Reading order: identity and choice probes, quoted numbers, markers,
chains; the 20-entry blind sample with Mike before its key.

2026-10-22 14:40, the 0.38.0 arms read in (`analyses/2026-10-22-two-entry-slot.md`; blind
reading with Mike, key opened 13:55, `research/readings/2026-10-22-blind-policy-038.md`). The
window: the residual rule at K = 3 returned 17 and 14 distinct entries against 10 and 3, the
most-returned 6 and 9 times against 15 and 36, with a median of 4 turns between returns of
one entry at both seeds; the lock is the rule reading a stable state, and the window turns it
into a cycle. The two-entry slot: both texts verbatim 39 of 39; state-residual still converged
(9 and 8 distinct); random-older's picks were the single-slot arm's picks exactly. Markers: the
latest entry's presence restores nothing (questions 0.3–0.8% of sentences against 6.3–7.7%
under latest, hedges 0.7–1.3 against 4.5–4.8, entries opening with "I" 0 of 312 across the
eight older-entry arms against 17 of 78), so the register effect belongs to the older entry's
presence. Chains: with both shown the writing follows the second slot (inferred source the
previous entry on 51–85% against 3–23%), the older entry holding 35–42% of the reach terms.
Quoted numbers (`probes/desktop_quoted_numbers.py`): entries quoting 95% or more number 11, 8,
25 and 12 of 40 in the two-entry arms against 0–9 in the single-slot arms, 0 of 24 in the
no-tag arms; the blind sample's finished-state family was entirely the tagged two-entry arms
and both readers' picks came from the window arms. Confounded with the tag, hence 0.39.0.

## What the day established, and did not (October 21, closing)

Did. The channel is built and exact (72 runs; recomputation within 1e-16; watchdog and
warm-up tested); at |g| ≥ 0.5 with the shipped dead band it raises the recurrent state's
effective rank by up to 0.8 of 32 and touches nothing else. The register of gemma4's
entries follows what the context line shows: the sweep's fill dependence is the number,
which the tag controls removed and the scrambled control exaggerated. With no number
shown, moving the field from the shelf (fill 70%) to 44% changed nothing in the text,
word for word (24 of 24 entries at two seeds). State-chosen memory
works as a mechanism (the choice recorded, verified and read back), its first rule is
degenerate with real entries (the latest entry's push dominates the state), and returning
an older entry moves the register one way in three arms (fewer questions, hedges and
first-person openings) at the cost of the thread continuity that produced the best
passage in a blind reading. The four 0.37.0 arms move it the same way by more, so seven arms over
two releases make it an effect of the returned entry under this contract; the residual
chooser converges on one entry (3 of 39 distinct at seed 7, one returned 36 times) where
chance spreads (24), and the chooser sets how many entries come back, not which way the
register moves. Minime's reservoir at 3 Hz is high-dimensional and near-white
with at least one ten-minute excursion into a slow, low-dimensional regime.

Did not. No numerical change in this apparatus reached the text except through the one
number shown, and the text reached the reservoir only as a push whose direction barely
changes between entries (alignment 0.92–0.93). Nothing here is evidence about the beings'
texts; one model, two seeds, 12–40 entries per arm. The channel's model arms are parked
with the expectation, stated here, that the writing would not notice; the spec's M1–M4
(continuous logging, autoencoders, effective-rank readouts) remain proposals on the
beings' side; the open question is what returns to the model and how it is framed. The local provider forked on
2 of 117 turns that two arms sent with the same prompt and sampling seed, and one fork at
a first entry moved the marker rates as far as some between-arm differences: an arm
difference at one seed is a direction to test, not an effect.

## Finish line for the draft

A dated account per tier with every number carrying n, the fill-sweep result stated
plainly (does the register move with the number), the effect-readout result (does the
loop become visible to the model, at what cost in visible compliance), and a decision
with Mike on whether to proposal-ize M0 for the beings. Nothing touches the live
systems; nothing is pushed.
