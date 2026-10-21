# 2026-10-21 · Tracing the text feedback loop of My reservoir

**Subject:** the desktop preview's writing loop on Mike's laptop, 0.28.0 and 0.29.0 source,
`mistral-small:24b`. Apparatus behaviour; nothing here is about Astrid or Minime.
**Question (Mike):** are we doing research or leading the model, and what role does the
loop text → reduced vector → reservoir → readout → text actually play?

Evidence: `probes/desktop_text_loop_coupling.py` on the greedy 0.28.0 session
(`sustained-1792607625263-1`, 9 entries, 300 steps) and the sampled 0.29.0 session
(`sustained-1792609937721-1`, 14 entries, 420 steps), which share seed, forcing and
field noise and differ only in the text that fed back; the codec source
`crates/reservoir-core/src/codec.rs`; the prompt builders in `sustained.rs`.

## The four links, as built

1. **Prompt → model (v8).** The model is shown: an open invitation, a paragraph
   describing the mechanism in our words, three readings (recurrent RMS, sensory fill,
   state L2 since the last observation, each with previous value and change), the full
   previous entry, and a writing boundary. Earlier versions v1–v4 showed all 32
   coordinates and all 32 eigenvalues; v5 narrowed this to the three scalars and added
   the previous entry with "no measurement recital is required".
2. **Text → 48 coordinates (`codec::encode`).** Thirty-two surface statistics, each
   squashed by tanh: character entropy, punctuation per word, uppercase and digit
   density, mean word length, adjacent code-point movement, whitespace, type–token
   ratio, words per sentence and their spread, questions, exclamations, ellipses,
   list lines, quotes, paragraphs, log length, an overall norm, and eleven keyword-list
   rates (hedges, certainty, negation, first and second person, action verbs,
   conjunctions, warmth, tension, curiosity, reflection, time, magnitude). No topic,
   no meaning, no order. Then `codec::feedback` adds a lift to four coordinates
   (sentence spread, curiosity, reflection, overall) when the field spectrum is spread
   and damps them when it is concentrated.
3. **Vector → reservoir and field.** The vector is held constant as input until the
   next entry replaces it (feedback scale 0.4 since 0.28.0). Reservoir input weights
   boost those columns by 1.6; the field activation scales them by 0.42.
4. **Reservoir and field → prompt.** RMS of the 32 coordinates, fill (fraction of
   active field modes, smoothed), and the L2 between observation states 30 steps apart.

## What the two sessions measure (n = 270 shared steps after the first feedback)

| quantity | greedy vs sampled, same step |
|---|---|
| reservoir state L2 between sessions | mean 0.547, max 0.821 (state RMS ≈ 0.5) |
| RMS shown to the model | mean difference 0.022, max 0.055 |
| fill shown to the model | mean difference 0.28 points, max 1.1 |
| one-step state change at a feedback application | 1.1–1.9, against a median step of 0.127 |

So different writing does move the reservoir's state direction appreciably, and each
new entry arrives as a kick ten times a normal step, but the two scalars the model is
shown are nearly blind to it: RMS reports magnitude and fill is set by forcing and
field noise. The kick itself points almost the same way every time: consecutive entry
vectors have cosine 0.989–0.9999 within a session, and a readout recital and a traveler
tale written at the same step have cosine 0.975–0.988 across sessions. The reduction
cannot tell them apart.

The field-driven lift in `codec::feedback` was +0.13 to +0.21 on the four coordinates
in every sampled entry (n = 8), while the text's own curiosity and reflection values
were 0.00–0.05. On those coordinates the reservoir mostly hears the field's spread.

Every entry in both sessions quoted the exact fill and RMS values it was shown
(22 of 23), until the sampled session's step-420 entry, which quoted neither and was
story alone: by then the traveler proposed at step 30 had led the writing into a
luminescent cavern, a hidden chamber and a subterranean lake. That continuity ran
through the returned previous entry, not through the reservoir.

## Where the leading is

- The frame. The context paragraph names a reservoir and a sensory field and explains
  our mechanism; the readout is called optional, and 22 of 23 entries recited it. The
  subject of the writing was given before any emergence could choose it.
- The returned entry. Under greedy decoding it produced verbatim repetition; under
  sampling it carried the model's own motif forward. It is the strongest channel.
- The codec's field lift and the keyword lists: a designed opinion about which words
  matter and a field-driven offset the model never sees.
- Our defaults: temperature 0.7, noise 0.5, scale 0.4, and the readout labels.

## Ideas that fell out, each one observation

1. **Frame ablation, 2 × 2.** Readout shown or not × previous entry returned or not,
   same model, seed, temperature and field. Measures how much of the writing is the
   frame. A fifth arm with neutral labels (values A, B, C instead of reservoir words)
   tests whether the labels pick the topic. New frozen prompt versions; no live change.
2. **A reduction that carries content.** Replace or augment the surface codec with an
   embedding from a local model (none installed; `nomic-embed-text` is a small pull)
   projected to 32 coordinates by a fixed seeded random matrix. Deterministic, not
   trained on our text. Test offline first on the 23 retained entries: does the
   traveler drift appear as a trajectory, and would L2 then respond to it?
3. **A readout that reports what the entry did.** The one-step state change at the
   application, and the cosine of that change against the previous application: two
   numbers that would differ between a recital and a tale. Numbers, not narrative, so
   no more leading than today; whether the model does anything with them is the point.
4. **Memory policy.** Return the model's own first lines instead of the full previous
   entry, or nothing after the first entry. Separates continuity from copying.
5. **Timing agency.** Let the model choose WAIT or WRITE, already noted as a later tranche.

None of these is selected; they are the smallest observations that would tell the
frame's share from the loop's share. The loop as built is closed only through style
statistics and a constant-direction kick; its content channel is the returned text.
