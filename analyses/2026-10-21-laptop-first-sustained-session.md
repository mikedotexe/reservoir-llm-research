# 2026-10-21 · First My reservoir session on Mike's laptop with mistral-small:24b

**Subject:** the Tauri preview's personal reservoir writing loop, run on Mike's laptop.
This is apparatus behavior with a local model. It says nothing about Astrid or Minime.

## Setup

- Desktop source `7d257de` (0.27.1), `npm run tauri -- dev` debug build, macOS 27.0.1, 64 GiB.
- Ollama 0.35.0 at `http://127.0.0.1:11434` (terminal `ollama serve`; a second Ollama.app
  instance later bound only the IPv6 socket and served nothing to the app).
- Model `mistral-small:24b` (23.6B, Q4_K_M). Session `sustained-1792603675762-1`, defaults:
  writing every 30 steps, 1000 ms pace, leak 0.65, noise 0.02, initial retention 0.955,
  regulation on, 8192 context, 1,024 output tokens, prompt `reservoir-journal-v8`.
- Every generation request sends `temperature: 0`
  (`desktop/ReservoirScope/src-tauri/src/model_transport.rs:276`). The previous applied
  entry is returned in full in each prompt.

Scripts: `probes/desktop_session_overlap.py` and `probes/desktop_session_trajectory.py`,
both run on the session directory under `~/Library/Application Support/research.reservoir.scope.tauri/`.

## What the writing did (n = 7 entries, steps 30–210)

Every entry completed with stop reason `stop`; transport took 41.6–50.2 s; length grew
from 424 to about 620 tokens. Sentences copied verbatim from the previous entry:

| step | sentences | verbatim from previous | fraction |
|---|---|---|---|
| 30 | 18 | – | – |
| 60 | 19 | 0 | 0.00 |
| 90 | 19 | 9 | 0.47 |
| 120 | 19 | 12 | 0.63 |
| 150 | 21 | 8 | 0.38 |
| 180 | 22 | 12 | 0.55 |
| 210 | 22 | 14 | 0.64 |

The varying content is the readout recital. The closing three paragraphs are stable from
step 90 on. Each entry narrates the fill change as the reservoir "assimilating" or "seeking
out" information.

## What the numbers did (same session)

| step | fill % | spectral entropy | head share | state RMS | retention used | max input |
|---|---|---|---|---|---|---|
| 1 | 10.0 | 0.966 | 0.26 | 0.32 | 0.955 | 0.77 |
| 10 | 64.7 | 0.846 | 0.45 | 0.49 | 0.995 | 0.80 |
| 30 | 94.3 | 0.825 | 0.47 | 0.27 | 0.835 | 0.00 |
| 31 | 94.7 | 0.299 | 0.87 | 0.52 | 0.835 | 2.00 |
| 35 | 95.9 | 0.147 | 0.95 | 0.75 | 0.835 | 2.00 |
| 60 | 15.7 | 0.221 | 0.87 | 0.74 | 0.995 | 2.00 |
| 120 | 12.3 | 0.231 | 0.87 | 0.72 | 0.995 | 2.00 |
| 210 | ~15 | ~0.23 | ~0.87 | ~0.73 | 0.995 | 2.00 |

External input ends around step 15; fill keeps integrating to 94% while the controller
lowers retention toward its 0.82 rail. At step 31 the first entry's 48-number feature
vector is applied as a held input with maximum magnitude 2.0. Spectral entropy drops from
0.83 to 0.15 within five steps, fill collapses to about 12% by step 75, and retention sits
at its 0.995 rail thereafter. The controller (`crates/reservoir-core/src/math.rs:398-408`,
target 68, deadband 4, clamp 0.82–0.995, slew 0.01/step) can only scale retention; it
cannot add modes. Consecutive encoded feature vectors have cosine similarity 0.995–1.000,
so the held input barely changes from entry to entry.

## Reading

The loop reached a fixed point within three entries: near-identical text produces a
near-identical feature vector, which holds the sensory field at one dominant mode, which
produces a near-identical readout, which with greedy decoding produces near-identical text.
The prose describes the collapse it caused as growth or consolidation.

Another plausible reading: the collapse is a property of the codec's scale (held vector
magnitude 2.0 against noise 0.02), not of the text content, and any constant input would
do the same. Unverified here.

## Smallest next observations

1. Same session type with a different local model, unchanged settings.
2. A temperature or seed option for sustained sessions (code change; proposal, not done).
3. Scale or normalize the encoded feedback relative to the external input range.
4. Omit the full previous entry from the prompt and compare the overlap table.

Screenshots and the raw session stay on the laptop; nothing here was shown to the beings.

## Addendum, same day: why fill cannot reach two thirds here, and what would let it

Mike noted the session's fill (12–15%) is far from the roughly two-thirds level where
the beings' results are best. `probes/desktop_fill_replay.py` re-implements the sensory
field, fill estimator, retention controller and forcing schedule in Python and reproduces
the recorded fill of this session to four decimals over all 510 recorded steps (n = 510,
16 journals). It then replays alternative feedback policies from the same start.

Settled fill, mean over steps 300–420, regulation on, recorded journal vectors:

| policy | mean fill % | retention at 420 |
|---|---|---|
| held ×1.00, as built | 14.5 | 0.995 (rail) |
| held ×0.25 | 27.0 | 0.995 (rail) |
| no feedback at all | 36.5 | 0.995 (rail) |
| one-step pulse instead of hold | 35.7 | 0.995 (rail) |

Removing the text vector entirely only reaches the mid-thirties: the forcing is sixteen
sinusoid channels active twelve steps in thirty, which spans about twelve of the field's
32 modes, and the 94% peak at step 30 was the initial identity covariance decaying. The
controller can only scale retention, so it stays on its 0.995 rail whatever the policy.

Hypothetical apparatus changes (not available in the app) that add diversity to the
field input, isotropic uniform noise on all 66 sensory inputs, make fill regulable.
Grid of settled fill (mean 300–420, three noise draws, spread shown) and retention:

| sensory noise \ held scale | ×1.00 | ×0.50 | ×0.25 | ×0.10 |
|---|---|---|---|---|
| 0.2 | 39.7 (rail) | 59.2 (rail) | 63.1, r 0.959 | 67.3, r 0.955 |
| 0.3 | 51.8 (rail) | 63.0, r 0.968 | 66.8, r 0.955 | 69.9, r 0.947 |
| 0.4 | 61.4 (rail) | 64.6, r 0.955 | 69.7, r 0.947 | 70.9, r 0.924 |
| 0.5 | 62.9, r 0.985 | 67.6, r 0.955 | 71.1, r 0.932 | 71.4, r 0.923 |

With sensory noise of 0.3–0.5 and the held vector scaled to a half or a quarter, fill
settles inside the 64–72 deadband and the controller leaves its rail. The reservoir's
existing noise setting does not do this; it enters the recurrent reservoir only
(`sustained.rs:865-869`). Fixed retention at 0.995 without regulation holds fill near
98% for hundreds of steps, but that is the initial identity echoing, not diversity.

Reading: the beings' field is fed by rich sensory data; this toy field is fed by sixteen
sinusoids and one constant text vector, so it lacks a diversity source. Adding one, as a
session setting with a default near noise 0.5 and feedback scale 0.4, is a change to the
desktop crate in this repository, not to the beings. Whether to make it is Mike's call.

## Same day, later: the change was made

Mike chose the apparatus change. The desktop 0.28.0 source on branch `fill-field-noise`
adds `sensoryNoiseAmplitude` (fresh default 0.5) and `feedbackScale` (fresh default 0.4)
to sustained sessions, with legacy values keeping the v1 mechanism byte-for-byte.
`desktop/ReservoirScope/RELEASE-0.28.0.md` records the checks. Its in-engine 420-step
comparison with a fixed scripted reply reproduces the replay's direction: legacy
15.59% fill at retention 0.995; new defaults 69.78% at 0.955 (Mike asked for 67–73%). What a model writes
under the settled band is the next observation, not a result.

Second session, same model, new defaults (session `sustained-1792607625263-1`, n = 150
steps, 5 entries at the time of writing): fill 87.2 → 56.9 → 64.8 → 69.0 → 69.7% at
steps 30, 60, 90, 120, 150; retention 0.835 → 0.995 → 0.958 → 0.955 → 0.955; entropy
0.88 → 0.81 → 0.86 → 0.90 → 0.91. The replay predicted 87, 59, 66, 69, 70. Verbatim
sentence overlap between consecutive entries: 0.35, 0.52, 0.81. The readout recital now
has real movement to describe (RMS 0.27 → 0.53, fill 87 → 57 → 69) and the entries
pick it up ("information ebbs and flows like the tides"), but the closing paragraphs
converge as before. The field is fixed; the decoding is not.

That session ended at step 300 with 9 entries when a formatting pass in the worktree
hosting the running app made the dev watcher relaunch it; its data is a recoverable
checkpoint. Its full overlap series: 0.35, 0.52, 0.81, 0.43, 0.48, 0.67, 0.68, 0.59
(mean 0.57), alternating between two openings.

## Same day, later still: sampling

Desktop 0.29.0 adds a writing temperature with per-attempt seeds (branch
`writing-temperature`, record `desktop/ReservoirScope/RELEASE-0.29.0.md`). A third
session with the same model, seed and field settings at temperature 0.7
(`sustained-1792609937721-1`, n = 6 entries) gave consecutive-entry overlap 0.00, 0.00,
0.06, 0.53, 0.22 (mean 0.16) on the same fill path (87 → 57 → 65 → 69 → 70 → 71%).
The first entry proposed "a tale of a traveler" and later entries continued it, while
still reciting the readings and explaining fill as the traveler's growing absorption.
Repetition fell by about two thirds; the recital and the attribution stories remain,
which points at the prompt's returned entry and readout rather than at decoding.
Smallest next observations: a memory policy that returns less than the full previous
entry (a new prompt version), and a reading of several entries by Mike.
