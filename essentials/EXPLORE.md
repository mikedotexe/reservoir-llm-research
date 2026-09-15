# Build and explore the reservoir

Reservoir Scope → **Essentials → Explore** opens a quiet, 32-coordinate reservoir
that you can operate a step at a time or let run at a chosen pace. The existing
four assemblies remain under **Stage experiments**.

## First experiment

1. **Send pulse** applies one synthetic video/audio input and records one step.
2. **Start reservoir** lets time advance. Watch the state persist and decay while
   external input is absent.
3. Enable **Recurrent feedback**, then send another pulse. The previous state now
   also drives the next step through the seeded recurrent weights.
4. Enable **Repeat external input** to supply the original synthetic forcing:
   12 steps on, 18 steps off. Compare the input and state traces during the quiet gap.
5. Change one parameter, pause, and scrub the resulting history.

Recurrent connections and repeated external stimulation are different mechanisms.
With recurrent feedback off, leak can still preserve part of each unit's previous
state. This explorer exposes the reservoir dynamics; it has no trained readout.

## Controls and timing

**Start / Pause** controls a paced clock. **Step** advances exactly once while paused.
**Send pulse** advances once while paused, or queues one pulse for the next running
step. A pulse overrides that step's repeated stimulus; it is not added twice.
Starting a quiet reservoir does not secretly inject input.

Leak, feedback strength, input strength, noise, constant bias, repeated input and
the optional sensory field can change while running. Each change applies at the
next actual step and is stored with that observation. Feedback strength scales
the same seeded recurrent weights; full strength retains the 0.9 maximum absolute
row-sum bound. This control is not a measured spectral radius.

One step always represents one third of a simulated second. The viewing pace is
1, 3, 10 or 20 steps per wall-clock second; delayed drawing does not generate a burst
of missed steps. Paused time adds no simulated time. At 1,800 steps, recording
pauses and retains the session.

**Reset** starts from zero with the specified seed and keeps the current settings.
The previous nonempty session is saved. The seed field is used by Reset, rather
than changing weights in the middle of a trace.

## Reading the picture

The view shows the actual 32 state coordinates on a fixed drawing map, with
activation color fixed at −1 to +1. **Topography** turns their interpolated field
into cyan peaks and purple valleys, with contours every 0.2 and a brighter zero
boundary. **Height** adjusts display exaggeration; it changes no reservoir values.
The neutral radius stays fixed, and landscape volume does not represent fill.
Select **Surface** for the original fixed-size color surface. Locations identify
coordinates rather than neural connectivity. The [topography guide](../native/ReservoirScope/docs/STATE-TOPOGRAPHY.md)
explains the shared color/height field and its limits.

Select a node to inspect its complete update:

    input drive + recurrent drive + bias → tanh proposal
    previous state × (1 − leak) + proposal × leak + noise → clipping → next state

The three pre-tanh contribution bars share a fixed −6 to +6 scale. The input drive
can exceed the activation range; it is not clipped to the state palette. Numeric
values show the later leak and noise contributions separately.

The history plots external-input RMS, recurrent-drive RMS, and state RMS on a
fixed 0–1 scale. The input RMS spans 66 coordinates; the other two span 32.
The inspector's **Applied at the cursor** section reads saved settings. The left
controls set the next new step. Continuing after scrubbing resumes the latest
computed state; it does not fork the old cursor state.

**Observe sensory field** sends the same input through the separate 32-dimensional
projection. Switching it on starts a fresh covariance; switching it off makes the
measurement unavailable. Its eight leading eigenvalues use a fixed 0–32 scale.
This explorer estimates no fill and runs no language model or regulator.

## Saved explorations

Sessions save under **research/outputs/essentials/**, separately from source and
bundled stage examples. Pause, manual steps, periodic running checkpoints and
leaving Explore preserve the recording. A failed save is visible; the unsaved
snapshot stays in memory.

Open and Export support the versioned **essentials-exploration-v1** format. Records
retain the seed and weights, each applied control setting, pulses, inputs, noise,
previous and resulting state, all update contributions, and available sensory
measurements. Import independently verifies the numerical history and can resume
from its latest state. Replay uses recorded observations.

The shared headless runner verifies either an exploration or a numbered stage run:

    essentials-run verify research/outputs/essentials/EXPLORATION.json

Exploration records are separate from **essentials-v1** stage recipes. Their quiet,
unbiased defaults and optional recurrent connections are explicit experimental
choices. The four existing stage examples preserve their original behavior.
All of these controls operate within the research project.
