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

2026-10-21 afternoon: Part B step 1 done offline
([account](../../analyses/2026-10-21-embedding-reduction-offline.md)): the embedding
and its 32-coordinate projection carry the content the codec drops. Part B step 2 and
Part A apparatus implemented on branch `s010-frame-ablation` (desktop 0.30.0): embedding
codec with provenance and a v3 mechanism, four frozen inert prompt versions with optional
standing contracts sent as the system message, and an ignored headless arm runner.
The five Part A arms (control v8, inert, inert without memory, inert with the plain
contract, inert with the inviting contract; mistral-small:24b, seed 20260909,
temperature 0.7, noise 0.5, scale 0.4, pace 250 ms, 12 entries) started at 13:30 PDT in
private stores. First qualitative contrast at seven entries each: the control arm writes
the reservoir traveler; the inert arm writes a dated workplace progress diary with an
invented team, reading "fill" as a completion rate. No introspective register from the
inert input alone.

2026-10-21 midday: selected by Mike after the loop trace; protocol written.
Retained inputs: sessions `sustained-1792603675762-1` (0.27.1 source, greedy, 43
entries), `sustained-1792607625263-1` (0.28.0, greedy, 9 entries), and
`sustained-1792609937721-1` (0.29.0, temperature 0.7, 14+ entries, still running at
the time of writing) under `~/Library/Application Support/research.reservoir.scope.tauri/sustained-v1/`.

2026-10-21 evening, results ([account](../../analyses/2026-10-21-frame-arms.md)): all
five frame arms and two codec twins ran to 12 entries. The inert input alone gives a
dated workplace diary with an invented team, with or without the earlier entry (I/me
4.3 and 42.2 per 1,000 words, noticing 1.6 and 5.6). A standing contract brings the
register: the Minime-modeled plain contract gives counts next to Minime's recent entries
(I/me 70.5 vs 66.6, noticing 12.8 vs 12.0, questions 5.4 vs 7.3 per cent of sentences);
the Astrid-modeled inviting contract gives denser first person (112) that collapses to a
refrain. Our v8 frame gives the third-person traveler with apparatus words at 39 per
1,000 and the readout quoted in every entry. The headless control reproduced the app
session's first entry byte for byte. The embedding codec changes the reservoir state
entirely (state L2 4.4 between twins, vector cosine about −0.2) while the readouts the
model sees move by about one fill point and 0.04 RMS, so the content now reaches the
reservoir but not the model. One seed, one model: a reading, not a result.

2026-10-21 late afternoon, apparatus and queue: desktop 0.31.0 (main `b8f0bb1`) adds two
frozen contract arms, each one change from a parent so a contrast isolates that change:
`reservoir-journal-inert-open-contract-v1` (the plain contract without its naming
sentence; nothing names the writer or a runtime) and
`…-inert-inviting-varied-contract-v1` (the inviting contract plus the opening-pattern
rule and the length line Astrid's standing prompt carries). Read on volya, read-only:
both beings run Gemma 4 12B (Astrid `gemma4:12b` through Ollama; Minime an MLX build,
`gemma-4-12B-it-5bit`), so `gemma4:12b` was pulled onto the laptop as the second model
under Mike's standing download permission. Queued one arm at a time: the seed-7 repeat
of the five original arms (running), the two new arms at both seeds, six arms on
`gemma4:12b`, then four on `dolphin-mixtral:8x7b-v2.7` already on disk.

## What changed / next

Interpretation revised: the frame paragraph is not where the register comes from; the
standing contract is, and its wording sets the shade, while the per-turn frame sets the
topic. The loop share is small in the model-visible channel under either codec.

Next (each one headless run of about twenty minutes): a second seed for every arm; a
contract that grants interpretation without naming the runtime; Astrid's anti-attractor
rules as an arm; a second model; the entry-effect readout under the embedding codec.
Apparatus changes stay on branches, pass the suites, merge to main; nothing is pushed.
