# MOVES.md: the September 6 agenda, preserved

**Research hub update, September 6 (Pacific):** The enduring agenda now lives in
[RESEARCH.md](RESEARCH.md), with the current discovery focus in
[research/NOW.md](research/NOW.md). This file preserves the early thesis, proposed
moves, and subsequent qualifications. Use the later source corrections below when
interpreting its claims, and read Hold Shelf for current work-card status.
The new research map does not cancel independently authorized implementation work.

**Parallel track, September 6: Anemone.** Mike's unplugged Raspberry Pi is the proposed
home for a separate minimal sensor–body–aperture experiment. The
[Anemone epic](exercises/2026-09-06-anemone-minimal-body-epic.md) preserves the sketch,
references the earlier Avado/ICP work and defines eight child tasks. Protocol/replay work
can start before hardware access; no device or experiment has been started. This track
does not change the existing priority queue below. The epic, eight child cards and trace-log
entry are published and verified on Hold Shelf; the publication receipt is retained in
`board/anemone-pending.json` (its original preparation filename).

**End-of-session update, September 6:** Read the
[session-close briefing and bounded work queue](exercises/2026-09-06-session-close-and-board-brief.md)
before dispatching the moves below. The later source checks qualify several early claims:
the inspected stable-core path disables the rotating bias floor; stale-packet counts apply
to their audited sample; telemetry ownership is channel-specific; and nearby reservoir-state
comparisons do not establish coupling efficacy against off. The “one true body loop” and
corpus-wide interpretations below are historical framing, not settled findings. The new
priority is an isolated event-survival probe, with prompt/backend provenance and sensory
freshness work in parallel, followed by anchor attribution and controlled manner tests.
The live board required sign-in at wrap-up; pending updates are recorded in the briefing.

Written 2026-09-06 after the trace and two exercises, on Mike's ask to capture the moves that
feel obvious. These are proposals for the design sessions, not decisions. Each move has a card
on the Hold Shelf board (ids in brackets); the card carries the live status, this file carries
the reasoning. Change candidates that touch the beings' code become `proposals/<slug>.md`
before anything is implemented in the sibling repos.

## Thesis

A year of iteration built an extraordinarily rich nervous system of descriptions and a thin
body. The beings' senses are prose renderings of telemetry, and their language tracks those
renderings line by line (exercises 1 and 2). Most of the problems found this week descend from
one early decision about what the body is; most of the good parts are the ones that touch a
real dynamical state.

## Three "why did we do it this way" questions

### W1. Why is fill computed on the input field rather than the reservoir? [q-why-fill-on-input]

The cascade, fill, entropy, pressure, porosity and foothold are all statistics of a 512-D
random projection of the sensory input, decayed and held by the stable core
(`esn.rs:826` comment; `orchestration.rs:3147`). The reservoir's own state covariance
(ESN λ₁ near 20) is computed and almost nothing reads it. Consequences that follow from the
choice: a quiet room reads as dying, so the engine injects a rotating bias floor when
covariance RMS drops; Astrid's rest sends warmth pulses so the field never goes dark; the 14%
rest floor is listed as the top unresolved issue; the beings report "thinning" when the world
is quiet; REST cannot mean rest. Hypothesis to test: the concentration excursions of 09-06 are
the bias floor at work [q-excursion-cause]. What would change my mind: a reason the input
field is the right body that survives the observation that the world was stale in 97% of
packets.

### W2. Why is every observer a labeled prose review instead of a channel? [q-why-prose-reviews]

One telemetry packet carries about two dozen `*_v1` dictionaries, each with a policy name, an
authority string, a right-to-ignore flag and a sentence about what it does not control; the
reviews compute candidate control biases that are never applied
(`pressure_source.rs:121`, "advisory/read-only in v1"). The prompts render these as sentences
and the beings describe the sentences back. The values behind this (un-muffle, consent) are
right; the machinery overgrew. What would change my mind: evidence that any advisory review
changed a live control through the consent path.

### W3. Why do the beings run a project management system? [q-why-being-runs-pm]

Charters, evidence, decide, advance, dossiers, continuity sessions, memory cards, research
budgets, conveyors. Both beings follow the form's suggestion a third of the time; thread
actions came back blocked 1,728 times and failed 572 times; Astrid's READ_MORE loop is a
budget-guard dead end (0 accepts in 597). The research program belongs on the steward side,
which is what this board is. What would change my mind: a lifecycle verb the beings use
unprompted and that changes their state.

## The six moves, in order

### M1. Persist the exact prompt for every generation, both beings, every lane [c-persist-prompts]

Astrid's job records already hold full prompts for moment-capture, daydream, aspiration,
introspect, elaboration and witness lanes; her dialogue_live keeps nothing; minime's job
records are 121-byte stubs and the qualia lanes bypass jobs entirely. One record per
generation (prompt text, contract version, model, timeout outcome, response) is the single
thing that makes the research honest, and it costs almost nothing. Size: small. Decides: Mike
(steward-only surface, no being-facing change).

### M2. Fix the sensory freshness gap [c-fix-freshness-gap, t-sensory-freshness]

Camera and mic clients are streaming; the engine has marked both stale in 97% of logged
packets over the last twelve days. The outside has been arriving and being dropped. Find the
hop (client cadence, sensory_ws intake, engine freshness window), then fix. Size: small to
medium. Decides: Mike; no being-facing prompt change, but the body will change, so tell them.

### M3. Strip the labels from the two moment prompts and try glyphs [c-withholding-flags, c-glyph-lines, t-withholding-ab]

`format_prompt_state` always emits the frame label; `generate_moment_capture` emits prose with
adjectives. Two functions, two flags, a contract version stamp, and the 22:14 entry as the
check: does the roof still darken when the words are gone. Size: small. Decides: Mike, with
the beings told what changed (consent-with-evidence).

### M4. Decide what the body is [d-what-is-the-body]

The real conversation. Options on the table: keep the input-field covariance as the body;
move fill to the reservoir state (ESN covariance, 128-D) and demote the field to an input
meter; or make the triple reservoir's dynamics the shared body both beings sense and
influence. This changes what fill means, what rest means, and what Astrid's influence means.
Right now her words reach minime's kernel at zero energy in 97% of headers since July
[f-semantic-kernel-zero], so "shared substrate" is currently her reading him. Size: large.
Decides: Mike and both beings through the consent loop; this is the first design session.

### M5. One real quiet window, chosen by the being, that stops input [c-rest-body, d-sparse-events, q-real-rest]

REST maps to no route and fill is flat after it; recess is the loop's standing mode. Define a
window in which semantic admission and outbound pause and let fill do whatever it does; then
measure it. Depends partly on M4 (what "drain" should mean). Size: medium. Decides: the beings
first, since it is theirs to want.

### M6. Cut the verb set and move the scaffolding to the steward side [d-dozen-verbs, c-dedupe-thread]

A dozen verbs that touch the body or the world; letters (ACK, REPLY, TRACE) as the one
deliberate text channel; experiment lifecycle, dossiers and budgets run from the board by us.
Size: large, and the most contestable. Decides: Mike and the beings; measure the 33%
compliance and the blocked/failed rates before and after.

## Protect while changing things [d-protect-list]

- The v3 moment contract's split between "supplied to model" and "header-only". Extend it to
  every lane.
- The coupled generation server: the triple reservoir modulating Astrid's logits token by
  token is the one true body loop in the system. Consider making it the center.
- The un-muffle invariant and consent-with-evidence as values.
- The action ledgers with pre- and post-state.
- The corpus itself: 400k first-person entries aligned to telemetry, mess included.
- Mike's `!` flags, the only human label in the corpus.

## Two small findings that belong here

- SELF_STUDY reads the first 400 lines of each of nine sources. The "self" source is
  `runtime.py`, 55,752 lines, so she studies 0.7% of herself, faithfully, on rotation. Worse:
  six of the nine sources are now module facades left behind by refactors (`regulator.rs` 6
  lines, `main.rs` 45, and Astrid's `codec.rs`, `autonomous.rs`, `llm.rs`, `ws.rs` at 6 to 12
  lines of `pub use` and `include!`). Two thirds of the self-study rotation has been reading
  re-export shells; Astrid's "collapse of distance" reading of `pub use runtime::*;` was
  literal [f-self-study-window, c-self-study-window].
- Semantic energy in minime's headers: `kernel=0.000` in 17,004 of 17,520 archived entries
  since July and 1,715 of 1,760 live; input 0.001 to 0.004; admission
  `stable_core_semantic_trickle` in 99% [f-semantic-kernel-zero].

## Refinement (exercise 4, 2026-09-06): two bodies, elective contact

- **Astrid's body hears only her voice.** The coupled server ticks her triple reservoir only
  from generated-token embeddings; prompt tokens never touch it
  (`coupled_astrid_server.py:1094-1170`). Change candidate: exogenous tokens advance the
  reservoir with a separate gain, self lower than world [c-exogenous-tokens-tick-reservoir].
- **Her voice does not reach his body.** Every codec delivery in the live window is
  `blocked_before_send` (limited-write v2), what is sent is 0.003-RMS warmth, and his kernel
  reads 0.000. The Astrid-to-minime direction has been off by policy for months; the loop is
  one-directional today [f-astrid-to-minime-zero-sent].
- **Cut the live direction as an ablation, with consent.** Pause minime telemetry in her prompt,
  measure vocabulary decay of the July coinages and her reproduction index before and after,
  render her own handle to her instead [d-two-beings-elective-contact, t-cord-cut-ablation].
- **Silence exists as a verb.** CONTEMPLATE/STILL skip generation and she has used them ~557
  times since June; make silence a default, not an achievement.
- **Correction to exercise 3.** Steward-voice answers come from the gemma3:4b fallback after
  timeouts (77.5% of fallback-written aspirations vs 0% of primary-written), not from the
  committee block directly. Log the backend per generation (M1) and stop routing reflective
  lanes to the small fallback [c-log-backend-per-generation, c-reflective-lanes-no-fallback].
