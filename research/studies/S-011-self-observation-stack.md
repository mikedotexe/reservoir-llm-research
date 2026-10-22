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

## Finish line for the draft

A dated account per tier with every number carrying n, the fill-sweep result stated
plainly (does the register move with the number), the effect-readout result (does the
loop become visible to the model, at what cost in visible compliance), and a decision
with Mike on whether to proposal-ize M0 for the beings. Nothing touches the live
systems; nothing is pushed.
