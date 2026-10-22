# The difference-signal ladder (S-011 M5), October 21, 2026

What feeding the apparatus reservoir a gain-limited signal of its own motion did, measured
against a gain-0 twin at the same seed. Desktop 0.35.0, scripted backend (no model), surface
codec, field noise 0.5, feedback scale 0.4, a turn every 30 steps, 600 steps per run at a
100 ms pace, the inert effect prompt so frames carry the entry effect. Numbers come from
`probes/desktop_difference_channel.py` (fill statistics, 90-step spectrum, retention
actuation, state rank, entry effect, the channel's own contribution and a recomputation of
it from the recorded states) with n = frames per run. Subject: the laptop apparatus, never
the beings.

## Step 0: the dead band and the watchdog bound, from four gain-0 twins

Seeds 20260909 and 7, each regulated (initial retention 0.955) and fixed (retention 0.95),
600 steps each (`--calibrate`, `logs/ladder-calibration.out` in the scratchpad).

| twin | d_f RMS | per-coordinate RMS | share of coordinate-steps beyond 0.02 | implied δ = 2×RMS | max trailing-90 fill std (window end) | after step 180 |
|---|---|---|---|---|---|---|
| reg, seed 20260909 | 0.0504 | 0.016–0.088 | 39.8% | 0.1009 | 14.95 (step 90) | 1.34 |
| fixed, seed 20260909 | 0.0504 | 0.016–0.088 | 39.7% | 0.1009 | 16.86 (step 90) | 0.97 |
| reg, seed 7 | 0.0550 | 0.020–0.110 | 38.7% | 0.1100 | 14.64 (step 90) | 1.44 |
| fixed, seed 7 | 0.0550 | 0.020–0.110 | 38.7% | 0.1099 | 16.73 (step 90) | 2.30 |
| pooled (2,400 steps) | 0.0528 | | 39.2% | 0.1055 | | |

No twin left 15–98% fill for more than one step or saturated more than five nodes. Two
decisions followed. The spec's rule (δ = twice the gain-0 floor) gives 0.105, five times
the shipped default, so the main ladder runs at δ = 0.105 and a companion block at the
shipped 0.02. The watchdog's default bound of 10 points sits under the start-up climb's
spread, so it would have dropped the gain at step 90 on every regulated rung for a reason
that has nothing to do with the channel; the ladder runs at a bound of 34, twice the largest
start-up value, and 0.36.0 adds a warm-up field. The regulated and fixed twins at a seed
give the same motion floor to three decimals: retention acts on the field, not on the
recurrent state.

## Block 1: regulated, seed 20260909, δ = 0.105, bound 34

Gains ±0.01, ±0.02, ±0.05, ±0.10, ±0.20 against the twin (600 frames each). The twin: fill
min/median/max 10.0/71.5/93.4, std 6.33, max trailing-90 std 14.95 (start-up), retention
actuation on 93% of steps (mean |Δ| 0.0022), state effective rank 9.54 and participation
ratio 2.34 over 64-step windows, entry-effect shift median 1.589 (n=19) and alignment median
+0.917 (n=18).

| gain | contribution RMS | dead-band-silent steps | clip hits | drops | recompute max abs Δ | Δ fill std | Δ trailing-90 std | Δ actuation | Δ erank | Δ PR | Δ shift median |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ±0.01 | 0.0001 | 64% | 0 | none | 4e-19 | 0.00 | 0.00 | 0 pts | 0.00 | 0.00 | 0.000 |
| ±0.02 | 0.0003 | 64% | 0 | none | 9e-19 | 0.00 | 0.00 | 0 pts | 0.00 | 0.00 | 0.000 |
| ±0.05 | 0.0007 | 64% | 0 | none | 2e-18 | 0.00 | 0.00 | 0 pts | 0.00 | 0.00 | 0.000 |
| ±0.10 | 0.0014 | 64% | 0 | none | 3e-18 | 0.00 | 0.00 | 0 pts | 0.00 | 0.00 | 0.000 |
| +0.20 | 0.0029 | 64% | 0 | none | 7e-18 | 0.00 | 0.00 | 0 pts | +0.01 | 0.00 | 0.000 |
| −0.20 | 0.0029 | 64% | 0 | none | 7e-18 | 0.00 | 0.00 | 0 pts | +0.02 | 0.00 | 0.000 |

Reading. The contribution scales linearly with the gain, as built, and the recomputation
from the recorded states matches the engine to floating-point precision, so the channel
does exactly what the spec describes. At the spec's dead band it is silent on 64% of steps
and its root-mean-square contribution reaches 0.003 per slot at the top rung, against
feedback slots of order 0.1 and sinusoidal forcing of order 1: within 600 steps nothing
about fill, its spectrum, the controller's actuation, the state's rank or the entries'
measured effect moved by more than the second decimal. The watchdog never fired; the top
rung ends with the gain in force. Whether a larger gain at the shipped dead band does
anything is block 4's question.

## Block 2: fixed retention 0.95, seed 20260909, δ = 0.105, bound 34

The twin without regulation: fill min/median/max 10.0/72.4/97.2, std 7.14, max trailing-90
std 16.86 (start-up), no actuation, state effective rank 9.54 and participation ratio 2.34,
entry-effect shift median 1.589 (n=19), alignment +0.917 (n=18). The same ten gains, 600
frames each:

| gain | contribution RMS | silent steps | clip hits | drops | recompute max abs Δ | Δ fill std | Δ trailing-90 std | Δ erank | Δ PR | Δ shift median |
|---|---|---|---|---|---|---|---|---|---|---|
| ±0.01 | 0.0001 | 64% | 0 | none | 4e-19 | 0.00 | 0.00 | 0.00 | 0.00 | 0.000 |
| ±0.02 | 0.0003 | 64% | 0 | none | 9e-19 | 0.00 | 0.00 | 0.00 | 0.00 | 0.000 |
| ±0.05 | 0.0007 | 64% | 0 | none | 3e-18 | 0.00 | 0.00 | 0.00 | 0.00 | 0.000 |
| ±0.10 | 0.0014 | 64% | 0 | none | 3e-18 | 0.00 | 0.00 | 0.00 / +0.01 | 0.00 | 0.000 |
| ±0.20 | 0.0029 | 64% | 0 | none | 1e-17 | 0.00 | 0.00 | +0.02 | 0.00 | 0.000 |

The channel's contribution is the same to four decimals as in block 1 at every gain: the
recurrent state never reads the field, so regulation changes nothing the channel sees, and
the field's own response to the channel (fill std, its spectrum) is below the second
decimal with or without the controller.

## Block 3a: regulated, seed 7, δ = 0.105, bound 34

The twin: fill min/median/max 10.0/70.3/93.4, std 5.99, max trailing-90 std 14.64,
actuation on 94% of steps (mean |Δ| 0.0010), state effective rank 8.88 and participation
ratio 2.00, entry-effect shift median 1.836 (n=19), alignment +0.931 (n=18). The same ten
gains, 600 frames each:

| gain | contribution RMS | silent steps | clip hits | drops | recompute max abs Δ | Δ fill std | Δ trailing-90 std | Δ actuation | Δ erank | Δ PR | Δ shift median |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ±0.01 | 0.0002 | 62% | 0 | none | 7e-19 | 0.00 | 0.00 | 0 pts | 0.00 | 0.00 | 0.000 |
| ±0.02 | 0.0003 | 62% | 0 | none | 1e-18 | 0.00 | 0.00 | 0 pts | 0.00 | 0.00 | 0.000 |
| ±0.05 | 0.0008 | 62% | 0 | none | 3e-18 | 0.00 | 0.00 | 0 pts | +0.01 / 0.00 | 0.00 | 0.000 |
| ±0.10 | 0.0016 | 62% | 0 | none | 5e-18 | 0.00 | 0.00 | 0 pts | +0.02 / 0.00 | 0.00 | 0.000 |
| +0.20 | 0.0031 | 62% | 0 | none | 1e-17 | +0.01 | +0.01 | 0 pts | +0.05 | 0.00 | 0.000 |
| −0.20 | 0.0031 | 62% | 0 | none | 1e-17 | 0.00 | 0.00 | +1 pt | +0.02 | +0.01 | 0.000 |

The second seed repeats the first: the only deltas that reach the second decimal are at
the top rung (fill std +0.01, state effective rank +0.05 at +0.20).

## Block 3b: fixed retention 0.95, seed 7, δ = 0.105, bound 34

The twin: fill min/median/max 10.0/69.8/97.0, std 7.54, max trailing-90 std 16.73, no
actuation, state effective rank 8.88 and participation ratio 2.00, entry-effect shift
median 1.834 (n=19), alignment +0.931 (n=18). The same ten gains, 600 frames each: the
contribution RMS is 0.0002, 0.0003, 0.0008, 0.0016 and 0.0031 at |g| = 0.01, 0.02, 0.05,
0.10 and 0.20, silent on 62% of steps, no clip hits, no drops, recomputation within 2e-17;
every delta against the twin is 0.00 except the state effective rank at +0.05 (+0.01 at
|g| 0.05, +0.02 at |g| 0.10, +0.05 at +0.20, +0.02 at −0.20) and the participation ratio
at +0.01 at −0.20, as in block 3a.

The main ladder: 44 runs, none interrupted. Its four gain-0 twins reproduce the four
calibration twins run earlier by the same binary frame for frame (600 of 600 frames
identical in each pair).

## Block 4: the shipped dead band 0.02, regulated, both seeds, bound 34

The same ten gains against the same regulated twins (600 frames each; none of the twenty
runs interrupted). With the dead band under the motion floor the channel is silent on only
19% (seed 20260909) and 22% (seed 7) of steps, and its contribution is about 2.7 times
block 1's at every gain:

| gain | contribution RMS, seed 20260909 / 7 | clip hits | drops | recompute max abs Δ | Δ fill std | Δ erank (s1 / s7) | Δ PR (s1 / s7) | Δ shift median |
|---|---|---|---|---|---|---|---|---|
| ±0.01 | 0.0004 / 0.0004 | 0 | none | 2e-18 | 0.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.000 |
| ±0.02 | 0.0008 / 0.0009 | 0 | none | 3e-18 | 0.00 | 0.00 / +0.01, 0.00 | 0.00 / 0.00 | 0.000 |
| ±0.05 | 0.0020 / 0.0022 | 0 | none | 7e-18 | 0.00 | −0.01, +0.01 / +0.03, 0.00 | 0.00 / 0.00 | 0.000 |
| ±0.10 | 0.0039 / 0.0043–0.0044 | 0 | none | 2e-17 | 0.00 | −0.01, +0.03 / +0.05, +0.02 | 0.00 / 0.00, +0.01 | 0.000 |
| ±0.20 | 0.0079 / 0.0086–0.0088 | 0 | none | 3e-17 | 0.00 / ±0.01 | +0.03, +0.08 / +0.08, +0.06 | +0.01, 0.00 / −0.02, +0.02 | 0.000 |

Actuation and the fill spectrum are unchanged at every rung. The state's effective rank
rises by up to 0.08 (of 9.5) at the top rung; nothing else leaves the second decimal.

## Block 5: the shipped dead band 0.02 at gains ±0.5 and ±1.0, regulated, both seeds

The top of the range the specification allows (600 frames each, none interrupted; the
whole ladder is 72 runs, none interrupted). The twins as in blocks 1 and 3a.

| seed | gain | contribution RMS | silent steps | clip hits | drops | recompute | fill std | max trailing-90 std | actuation | state erank | PR | shift median |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20260909 | twin | | | | | | 6.33 | 14.95 | 93% | 9.54 | 2.34 | 1.589 |
| 20260909 | +0.50 | 0.0197 | 19% | 0 | none | 6e-17 | 6.33 | 14.93 | 93% | 9.78 | 2.41 | 1.588 |
| 20260909 | −0.50 | 0.0197 | 19% | 0 | none | 7e-17 | 6.35 | 14.97 | 93% | 9.88 | 2.37 | 1.589 |
| 20260909 | +1.00 | 0.0396 | 19% | 45 | none | 8e-17 | 6.30 | 14.92 | 93% | 10.12 | 2.46 | 1.588 |
| 20260909 | −1.00 | 0.0395 | 18% | 78 | none | 1e-16 | 6.31 | 14.91 | 93% | 10.31 | 2.46 | 1.589 |
| 7 | twin | | | | | | 5.99 | 14.64 | 94% | 8.88 | 2.00 | 1.836 |
| 7 | +0.50 | 0.0214 | 22% | 0 | none | 7e-17 | 5.99 | 14.63 | 94% | 9.17 | 1.95 | 1.836 |
| 7 | −0.50 | 0.0227 | 22% | 0 | none | 8e-17 | 6.00 | 14.66 | 95% | 9.10 | 2.04 | 1.836 |
| 7 | +1.00 | 0.0420 | 22% | 107 | none | 1e-16 | 5.98 | 14.62 | 94% | 9.62 | 1.99 | 1.836 |
| 7 | −1.00 | 0.0461 | 22% | 237 | none | 1e-16 | 6.01 | 14.66 | 95% | 9.35 | 2.03 | 1.836 |

## Reading

Across 72 runs the channel did exactly what it says: its contribution scales with the
gain, the dead band sets how often it speaks (62–64% silent at the spec's δ, 18–22% at the
shipped one), the clip engages only at |g| = 1 (45–237 of 600 steps), the recomputation
from the recorded states matches the engine to 1e-16, the watchdog never fired with the
bound set above the start-up climb, and the entry-effect counterfactual, which keeps the
channel on both sides, reports the same shift to three decimals at every rung. What it did
to the dynamics is one thing: at |g| ≥ 0.5 with the shipped dead band the recurrent state's
effective rank rises, by +0.24 to +0.34 at |g| = 0.5 and +0.47 to +0.77 at |g| = 1 (from
9.5 to 10.1–10.3 at seed 20260909, from 8.9 to 9.4–9.6 at seed 7; both signs of the
projection raise it). The field saw none of it: fill's median, spread, trailing spread and
90-step spectrum, and the controller's actuation, are the twin's to the second decimal at
every gain, because a contribution of 0.04 RMS per slot (the ceiling, under the clip) is
small beside the scaled held vector and the forcing the field also reads. So in this
apparatus the difference signal is a small rank-raiser for the reservoir, not a fill
driver, and the gains that do anything are the ones the spec's dead-band rule would have
silenced. A model arm would tell whether a reservoir with half a unit more rank writes
differently; the entry-effect alignment this sweep leaves untouched (0.92–0.93) says the
entries' pushes stay as alike as before, so the first expectation is no. The spec's
own rule, δ at twice the floor, is the conservative one; whether the register follows the
numerics at all is the S-010 question, which these runs do not touch.
