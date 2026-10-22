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

## Blocks 4–5

Block 4, the companion at δ = 0.02 (regulated, both seeds, the same ten gains), and block
5 at δ = 0.02 with gains ±0.5 and ±1.0 (regulated, both seeds): pending as this account is
written; their rows follow below when the runs land.
