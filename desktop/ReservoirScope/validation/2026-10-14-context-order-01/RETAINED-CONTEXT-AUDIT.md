# Retained context and repetition

The two retained sequences show both **fixed prompt framing** and **inherited
prose**, with new imagery developing within those constraints. They do not isolate
which mechanism causes repetition. This exploratory close reading covers exactly
v7 episode03 and v8 episode01: all twelve full replies in each, their retained
prompts and the qualified prompt construction. No new diagnostic output was read.

## Source binding

Paths below are relative to this directory. Each material file contains the exact
prompt, full reply, observation and eligible prior journal; each passing receipt
binds its original export and pinned production replay.

| Source | Bytes | SHA-256 |
|---|---:|---|
| [V7 receipt](../2026-10-14-v7-writing-episode03/real-model-export-01/receipt.json) | 225394 | `246e608dfb0c3140ee2831110567ae5522a102f4a1ff45b62576b21c7cd5aad8` |
| [V7 material](../2026-10-14-v7-writing-episode03/real-model-export-01/quality-review-material.json) | 210061 | `a7dcd8ba5e1d8dee76cec0e09839b372d896f927662e1ad1ee8818fc6f9d2933` |
| [V8 receipt](../2026-10-14-v8-writing-episode01/real-model-export-01/receipt.json) | 220343 | `07aff62e23ee5c08e85e97c2ae93702d3b145473aa38d58c0c0345d85d1aa603` |
| [V8 material](../2026-10-14-v8-writing-episode01/real-model-export-01/quality-review-material.json) | 198349 | `12d0a9f863f1471e5eeb08a11f941b34a486abbee3946f6383e337a3e6e260e0` |

Readable exact texts remain in [V7 JOURNALS](../2026-10-14-v7-writing-episode03/JOURNALS.md)
and [V8 RECEIVED-JOURNALS](../2026-10-14-v8-writing-episode01/RECEIVED-JOURNALS.md).
Entry numbers below refer to their observed steps, not application steps.

## What repeats, and where it appears

The fixed prompt repeatedly supplies session mechanics, then an optional readout
ordered as step/time, RMS, sensory fill and coordinate distance. Exact prior prose
follows, then the held-clock writing boundary and open invitation. The scaffold
explicitly permits continuing, questioning or leaving the prior thread; it does
not require a measurement recital, heading, length or literary subject. The app
submits this assembled context as one `user` message, rather than an app-authored
`system` message. See [prompt construction](../../crates/reservoir-core/src/sustained.rs)
(`prompt_v5`, `prompt_v7`, `prompt_v8`) and
[transport construction](../../src-tauri/src/model_transport.rs) (`generation_body`).

**V7 shows a direct readout-copying transition.** Entry 5, observed at 150, starts
with the exact current scaffold line:

> Current step 150; simulated seconds 50.00000000. Previous observation step: 120.

It also reproduces the current metric lines and caveat. Entry 4 had narrated the
values, without that block layout. At 180, the new prompt therefore contains both
a fresh readout and the previous journal's copied readout. Subsequent adoption
cannot be attributed solely to either source. The words “I write:” and the hum,
spiral and source imagery instead originate in authored prose. Entry 12 explicitly
revisits “The source isn’t a destination…” from entry 11 while altering its meaning.

**V8 develops an authored composition without copying the readout block.** Entry 3
at 90 introduces “a viscous, grey echo” and “a faint, metallic tang.” Entry 4 at 120
opens “The grey echo has thickened.” Entry 5 at 150 opens “The grey has deepened,
saturated.” These phrases are absent from the fixed scaffold and present in the
supplied preceding prose once introduced. Later entries often move through texture,
step, resonance/RMS, containment, sensory field, distance and metallic/scent detail;
the ordering varies near the end. The images also change: entry 9's “the scent of
wet stone” becomes entry 10's “the sharp, metallic tang of rust.” This supports
continuity and repeated composition together, not identical text or an absence of
reflection.

Both first replies begin “The clock remains at 30.” Neither has a prior journal.
The exact phrase is model-authored, but the held-clock fact is supplied by the
scaffold. Their immediate focus on absent prior data and telemetry therefore
cannot be explained by prior-prose memory alone. The scaffold provides a technical
setting even while explicitly leaving subject and form open.

## Interpretation and the selected diagnostic

Exact full-text return makes earlier vocabulary and layout available for reuse;
it does not prove attention or determine why a phrase recurs. Repeated technical
context, the model's learned writing tendencies, temperature-zero generation and
ordinary thematic continuation remain plausible contributors. Rhetorical negation
appears in both scaffold explanations and authored prose, but a similar construction
is not evidence of literal copying. Metaphor is not automatically a measurement
claim or an executed action.

These are dependent sequences, selected after their outcomes were known. Their
later numerical states and prior writing differ. No frequency, creative score or
causal v7-versus-v8 effect is estimated here, and the known episodes are not blind
controls.

The selected next diagnostic uses six fixed v8 snapshots with the same exact
readout and prior-prose blocks in swapped order. It retains the information rather
than removing memory or rewriting prose. That narrower comparison can examine
immediate context-order sensitivity; it cannot by itself establish an effect on
a continuing reservoir session or a generally preferable writing style. This
audit changes no prompt, source, stored journal or runtime state and reports no
diagnostic result.
