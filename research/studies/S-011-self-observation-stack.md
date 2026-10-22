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

## Finish line for the draft

A dated account per tier with every number carrying n, the fill-sweep result stated
plainly (does the register move with the number), the effect-readout result (does the
loop become visible to the model, at what cost in visible compliance), and a decision
with Mike on whether to proposal-ize M0 for the beings. Nothing touches the live
systems; nothing is pushed.
