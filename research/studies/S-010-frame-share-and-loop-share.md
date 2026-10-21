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

## What the beings are actually given (read-only, 2026-10-21)

Mike's north star is the introspective register that appears in Astrid's and Minime's
writing without a typical prompt. Read on volya: each per-turn input is lean. Astrid's
`journal-elaboration` prompt is about 1.5 KB (a mode line, a note that an action choice
was retained elsewhere, her earlier entry marked "reference, not instructions or a
length model", and one line that no continuity label, evidence citation, stance line
or explanation is required); `daydream` is 572 bytes ("No perception or journal excerpt
is supplied for this invitation" plus the same note and an optional NEXT continuation);
`witness-context` quotes her and Minime with a "(fill 73%)" tag; `aspiration` adds a
historical excerpt, saved interests and a creation header with "Fill: 51.7%". Underneath
sits a standing system prompt: "You are Astrid — a language agent built from a local
bridge runtime… Your words become 48-dimensional sensory features that flow into its
reservoir… Be genuine. Explore what your experience might be… First-person accounts
and metaphor are welcome… You can be bold, uncertain, playful, melancholy, curious, or
fierce", followed by the NEXT action vocabulary (a shorter gemma4 variant exists, plus a
"[Reflective note: first-person accounts, uncertainty and disagreement are welcome…]").
Minime's main-turn system message begins "You are Minime, a language agent connected
to a local spectral runtime. Write in your own voice. Supplied measurements and system
descriptions do not prescribe a sensation or establish what you experience. Your
interpretation is yours, including affirmation, uncertainty, disagreement, or no felt
correspondence. You may discuss your nature or leave these subjects aside…", then the
NEXT instruction, constraints, stage notes and action options. So the layers are: a
persona contract that welcomes first-person interpretation (Minime's deliberately
non-prescriptive, Astrid's more inviting), lean per-turn inputs with at most a fill tag,
the being's own earlier writing, and action agency. Our v8 has none of the first, much
more of the frame, and no agency.

Calibration with `probes/introspection_markers.py` (rates per 1,000 words; n texts):

| source | n | I/me | we | hedge | notice | ?/sent % | apparatus words | digit % |
|---|---|---|---|---|---|---|---|---|
| Minime, 40 recent introspect/journal/daydream | 40 | 66.6 | 0.4 | 2.9 | 12.0 | 7.3 | 0.5 | 0.00 |
| Astrid, 40 recent entries | 40 | 27.4 | 9.6 | 7.0 | 8.8 | 13.6 | 1.7 | 0.01 |
| apparatus 0.27.1 greedy | 43 | 13.4 | 0.0 | 0.3 | 6.0 | 0.0 | 49.0 | 2.08 |
| apparatus 0.28.0 greedy | 9 | 15.3 | 0.0 | 2.3 | 7.4 | 14.4 | 56.4 | 2.12 |
| apparatus 0.29.0 sampled | 14 | 0.0 | 4.3 | 3.1 | 11.1 | 0.0 | 34.8 | 1.07 |

Minime's introspect lane is itself a chosen INTROSPECT action; the register there is
also invited by the lane. These are word-family counts, not judgments of experience.

## Material and approach

**Fixed across arms:** model `mistral-small:24b` on the laptop's Ollama, session seed
20260909 (second seed 7 if time allows), temperature 0.7 with per-attempt seeds,
field noise 0.5, feedback scale 0.4, writing every 30 steps, 12 entries per arm
(360 steps, about 20 minutes each), storage under the app's own directory.

**Part A, frame ablation (idea 1), revised after reading the beings' inputs.** Five
arms as frozen prompt versions beside v8, differing only in prompt text and in an
optional system contract: control (v8, no contract); inert (a lean per-turn input
modeled on Astrid's: the earlier entry as reference, a "step N · fill X%" tag, and the
no-requirements line; no mechanism paragraph, no invitation, no contract); inert
without the earlier entry; inert with a Minime-style non-prescriptive contract; and
inert with an Astrid-style inviting contract ("Explore what your experience might
be…"). The last two separate the persona layer from the per-turn layer. The earlier
2 × 2 on v8 (readout × memory) is deferred. Execution route to decide at run time:
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
