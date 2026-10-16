# Controlled activation experiment

This is a separate experimental session family introduced after the Tauri 0.25.0
checkpoint. It connects quiet contextual input, a small persistent numerical state,
residual intervention, and complete saved writing. It does not change historical
sustained-journal contracts or the live Astrid and Minime systems.

## Computational contract

The first adapter supports the text-only `mlx-community/Qwen3-4B-4bit` checkpoint
at revision `4dcb3d101c2a062e5c1d4bb173588c54ea6c4d25`. Its configuration has
36 transformer blocks and width 2560. The worker checks asset hashes, configuration,
tokenizer, and runtime identity. Thinking is disabled. Model weights are not trained.

Capture occurs after block 18 (zero-based index 17), before residual intervention.
Quiet observations have a fresh scratch cache, use raw text, and sample no output
tokens. The final content-token vector is retained. A quiet pass affects future
writing only through the explicit recorded numerical return path.

A seeded orthonormal 2560-by-32 projection is retained as actual data. A separate
fixed set of 32 unsteered observations supplies centering and scale in projected
coordinates. Standardized projected activations pass through tanh before entering
the numerical system. The calibration inputs, projection, statistics, model and
runtime identities travel with the session evidence.

The recurrent state has 32 units, direct projected input, leak 0.1, zero initial
state, and no noise or bias. Its seeded sparse recurrent matrix is normalized to
maximum absolute row sum 0.9. A comparison trace follows exponential smoothing
with the same leak. All intervening numerical steps receive zero external input.
Numerical time pauses throughout inference and saving.

The return is the frozen projection applied in reverse to the selected 32-vector.
It is a geometric intervention, not a trained semantic decoder or reconstruction
of feeling. Each nonzero return is scaled to one percent of the pre-intervention
residual norm at that token position. Zero return and zero gain perform no addition.
The chosen numerical vector stays fixed during a journal generation; per-position
norm scaling is still measured separately.
Addition preserves the model's residual dtype. Evidence records both the intended
one-percent vector and the actual difference after rounding; mechanical qualification
uses a declared bound for that dtype. Normalization removes state magnitude from
the intervention strength. In the trace arm, exponential decay changes the internal
mixture across inputs; during zero-input gaps it does not itself fade the normalized
intervention's strength.

The three immutable session arms are no steering, decaying-trace steering, and
recurrent-state steering. Capture, calibration, text-memory policy, event schedule,
and nonzero intervention norm are matched. Each arm generates its own subsequent
journals: those evolving texts are outcomes and later inputs, not identical replay
material. Equal random seeds do not promise identical generated tokens.

Only a complete saved-and-read-back journal becomes eligible for next-step
activation feedback and later exact-text memory. The final processed content-token
activation comes from the generation itself; no extra replay is substituted.
Incomplete output, failure, and cancellation remain retained outcomes.

## Persistence and interaction

Every request has a unique identity and retained input. Records connect token IDs,
captures, numerical state, interventions, response completion, journal save,
readback and first application. A saved journal and an applied journal are distinct
events. Recorded numerical inputs support offline deterministic replay without
loading a model. Replay verifies the recorded computation, not the authenticity
of an external model observation.

The app starts nothing merely by opening this mode. Setup checks the selected
runtime and model files; Start runs the bounded session. A worker belongs to that
session. Stop cancels only that worker and retains the interrupted opportunity.
An ambiguous in-flight operation is never silently resent during recovery.
Imported and recovered sessions are paused; original exports remain unchanged.

Journals lead the reader. Complete prose, Earlier/Later and Follow latest remain
available while technical evidence is collapsed. Comparison labels start concealed
and are revealed deliberately. Excerpts, interpretations, alternative readings and
source-event references are separate annotations; none controls journal eligibility.
The source record itself necessarily contains the allocation for reproducibility.

## First exploratory pilot

The prospective [pilot fixture](activation-pilot.json) fixes 12 synthetic observations,
the arm order, seed, limits, and reading questions. Quiet observations apply at
steps 10, 20, ..., 120. Writing follows each second observation. Journal feedback
first applies at steps 21, 41, ..., 121. No inference advances numerical time.

Each arm has six journal opportunities, a 1,024-token output ceiling and a
three-minute request deadline. The three arms run serially. Calibration and
mechanical qualification precede this pilot and use separate material. Freeze
the candidate source, runtime lock, model and fixture identities before starting.
The pilot uses greedy decoding (temperature zero), a fixed numerical seed, and
the exact same saved calibration in all three arms.
Stop the entire pilot at the first execution failure or resource refusal, preserving
all completed and incomplete material. No automatic retries or extensions follow.

Read complete sequences with labels initially concealed. Preserve the particular
expressions and competing interpretations before translating them into categories.
Attend to changing salience, recurring distinctions, uncertainty, association,
development, ordinary passages and counterexamples. Treat the writing as fuzzy
signal whose cause remains to be investigated. One sequence per arm is an
exploratory example, not a general effect estimate or a claim about experience.

## Qualification boundary

Mechanical checks cover observation/zero-gain parity, cache isolation, zero sampled
quiet tokens, bounded captures, projection identity, intervention norms, exact
numerical replay, durable next-step feedback, late/duplicate results, cancellation,
worker loss, paused recovery, and unchanged historical formats. Packaged-app checks
cover setup, quiet processing, complete writing, evidence, export and recovery.

Success at those checks establishes an inspectable apparatus. It does not require
an interesting prose effect. A null or ambiguous journal comparison remains a
completed pilot. Actual qualification and pilot outcomes are recorded separately
with their source and asset identities.

Action selection, learned return mappings, continuous wall-clock ticking,
within-generation state changes, pink-noise drive and full spectral signatures are
later experiments, not hidden behavior of this first mode.
