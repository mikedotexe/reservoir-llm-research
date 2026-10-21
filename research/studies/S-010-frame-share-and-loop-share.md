# S-010 · Frame share and loop share in My reservoir writing

Started: 2026-10-21 · Lead: Claude (lead collaborator), Mike steward · Question family:
apparatus; relates to RQ-04 (what self-description does) and RQ-03 (continuity) ·
Board card: unlinked (board not reachable from this session)

## Question and scope

In the desktop preview's writing loop (laptop apparatus, `mistral-small:24b`, never the
beings), how much of what the model writes is set by the prompt frame, the mechanism
paragraph, the readout labels and the returned previous entry, and how much by the
numerical loop, text → reduced vector → reservoir and field → readouts → text?
Mike's concern: do research, do not lead the model, allow emergent writing. Mike's
intuition: the loop plays an important role. The [loop trace](../../analyses/2026-10-21-text-loop-trace.md)
found the loop as built closed only through surface statistics and a constant-direction
kick, with the content channel being the returned text, and 22 of 23 entries quoting
the readout. Mike selected two ideas from it: a content-carrying reduction (idea 2)
and a frame ablation (idea 1). This is a bounded causal comparison within the
apparatus plus descriptive measures of the writing.

## Material and approach

**Fixed across arms:** model `mistral-small:24b` on the laptop's Ollama, session seed
20260909 (second seed 7 if time allows), temperature 0.7 with per-attempt seeds,
field noise 0.5, feedback scale 0.4, writing every 30 steps, 12 entries per arm
(360 steps, about 20 minutes each), storage under the app's own directory.

**Part A, frame ablation (idea 1).** Five arms as new frozen prompt versions beside v8:
control (v8); no readout; no returned entry; neither; and neutral labels (readout kept
but values named A, B, C and a context paragraph without the words reservoir, sensory
or field). Arms differ only in prompt text. Execution route to decide at run time:
a research-only prompt-version selector under Advanced settings, or a headless runner
in the desktop crate that uses the real transport and a private store; neither touches
the frozen native reference or any live system.

**Part B, content-carrying reduction (idea 2).** Offline first: embed every retained
entry from the three October 21 sessions with a small local embedding model (none is
installed; `nomic-embed-text`, about 274 MB, needs Mike's go to pull), project to 32
coordinates with a fixed SplitMix64-seeded Gaussian matrix, and compare consecutive
and matched-entry cosines with the surface codec's 0.975–0.9999. If the embedding
separates a recital from a tale and shows the traveler drift as a trajectory, add an
apparatus option: a codec choice on sustained sessions (surface, embedding) with a v3
mechanism identity recording the embedding model, its digest, the projection seed and
the raw embedding hash. Then run the control arm under both codecs and compare
reservoir-state divergence, readouts and writing. Idea 3 from the trace, a readout
of what the entry did (one-step state change at application and its cosine against
the previous application), is an optional extension if the loop stays invisible.

**Measures per arm, from journal files via probes:** consecutive-entry verbatim
overlap; readout quoting rate; rate of apparatus vocabulary (reservoir, sensory,
field, RMS, fill, L2); first-person and question rates; novelty (new sentences);
motif persistence (a noun absent from the prompt that appears in three or more
consecutive entries); embedding drift from the first entry when Part B's model exists;
reservoir-state divergence between arms sharing seed and noise.

**Alternatives to keep in view:** the model's generic metaphors would appear under any
frame (test: neutral-labels arm); sampling alone explains the drift (control arm at
temperature 0 exists: the 0.28.0 session); n = 1 per arm is a reading, not a result
(second seed); our measures are ours (report them as counts with denominators).

## Finish line

A dated account with the arm table (entries per arm, every measure with n), the
offline embedding comparison, and a plain statement of what the frame sets and what
the loop sets, with what would weaken it. Outside reach: anything about Astrid or
Minime; human reading quality; other models. No live-system proposal is expected.

## Progress and results

2026-10-21: selected by Mike after the loop trace; protocol written; nothing run.
Retained inputs: sessions `sustained-1792603675762-1` (0.27.1 source, greedy, 43
entries), `sustained-1792607625263-1` (0.28.0, greedy, 9 entries), and
`sustained-1792609937721-1` (0.29.0, temperature 0.7, 14+ entries, still running at
the time of writing) under `~/Library/Application Support/research.reservoir.scope.tauri/sustained-v1/`.

## What changed / next

Next: Mike's go on the embedding pull, then Part B offline, then Part A arms. Results
go to a dated account in `analyses/`; apparatus changes go on a branch, pass the
crate and frontend suites, and merge to main; nothing is pushed.
