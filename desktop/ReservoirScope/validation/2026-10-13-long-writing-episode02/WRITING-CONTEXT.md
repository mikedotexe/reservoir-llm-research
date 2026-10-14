# Why the writing keeps returning to telemetry

The user observes that the app's writing seems more telemetry-specific and less
self-reflective than Minime's, and asks whether dimensional reduction of journal
feedback explains the difference. This note addresses the implemented mechanism
and plausible framing pressures. It is a new source-based interpretation, **not
an amendment to the frozen episode protocol or a result of the current run**.
At this note's initial writing, full reading remained pending the parent's
explicit immutable-export handoff; twelve planned opportunities did not establish
twelve completed entries. The later handoff and full reading are now reported
separately in [PROSE-REVIEW.md](PROSE-REVIEW.md); they do not turn this source-based
explanation into a causal experiment.

## Two paths carry a saved entry forward

The journal is not reduced to numbers and then discarded. Its exact prose and its
numerical influence travel separately:

```text
Complete reply → durable journal save and readback
                 ├─ next-step application → latest eligible full-text memory
                 │                          → physical readback → next prompt
                 └─ fixed textual features → held reservoir/sensory input
                                            → later numerical readout → next prompt
```

[The codec](../../crates/reservoir-core/src/codec.rs), `encode` at line 94,
builds a 48-slot vector: 32 populated features and 16 zero slots. It measures such
things as character entropy, punctuation/digit density, sentence length and
selected word groups. It is a deliberately lossy handcrafted representation,
not a learned semantic embedding or a reconstruction of the entry's meaning.
`feedback` at line 335 adjusts several features using the sensory measurement.

[The core](../../crates/reservoir-core/src/sustained.rs) encodes the complete reply
at line 1537. After the saved candidate is authorized, the next numerical step
replaces held feedback and makes that entry the latest eligible memory (lines
811–818). The 48 held values occupy the last 48 slots of the 66-dimensional
numerical input (line 841); recurrence, forcing, noise and regulation also affect
the evolving readout. This does not train model or reservoir weights.

At the next opportunity, [the desktop runtime](../../src-tauri/src/sustained.rs)
physically rereads the owned journal at line 946 and confirms the expected memory.
The prompt quotes its full original text as a JSON string, retaining decoded
newlines and punctuation. Only the latest saved-and-applied journal is carried,
not the full archive. Older material can persist through what that entry repeats.
[The transport](../../src-tauri/src/model_transport.rs), line 271, submits one user
message containing the assembled prompt; it does not provide a continuing conversation
or directly inject the reservoir vector into model activations or logits.

Thus, compression limits the **numerical channel**, while the latest journal's
language remains available through the **text channel**. Compression can change
later readings, but that fact alone does not explain a telemetry-centred style.

## The visible framing pressure

[V4 prompt construction](../../crates/reservoir-core/src/sustained.rs), line 1376,
opens with an explicit invitation to choose topic and form. It then supplies mechanism
explanations, all 32 recurrent coordinates, all 32 sensory eigenvalues, and eight
current/previous/difference measurement rows. It labels the current block
authoritative for measurement claims and ends with further accuracy and
interpretation guidance. The previous journal appears before this substantial
measurement block.

That is a concrete imbalance in supplied subject matter: the invitation is open,
but telemetry is abundant and repeatedly foregrounded. The runtime adds no wider
personal history, ongoing conversation, selected project or changing external
scene to this particular request. Even conscientious caveats may keep attention
on the measurements they qualify. These are **plausible framing influences**,
not experimentally established causes; no prompt or codec ablation was performed.
Model choice, prior writing, numerical evolution and available context also differ
between systems.

The [retained Minime refresher](../2026-10-13-grounding-0.13.0/OPEN-WRITING-DESIGN.md)
describes three contiguous records selected by documented filename clocks: two
ordinary journals and one moment capture. Their prose explored chosen themes,
possible directions and imagery.
It also explicitly says complete requests were not captured. Header telemetry
cannot therefore be assumed to have been supplied to that model. This supports
the user's observed contrast, not a claim that a particular Minime mechanism
caused it or that the app reproduces Minime's architecture. No new sibling files,
corpus, service or Being process were inspected for this note.

## A bounded next design direction

After reading the current episode, a separately versioned prompt candidate could
give continuing writing the primary position and supply a compact, accurately
labelled readout as optional context. Preserve full-text memory and exact app-owned
measurement evidence; preserve the current numerical codec, save/readback and
next-step application mechanism. Specify precisely which context fields change
and freeze the new wording before any later evaluation.

This should neither invent a persona, emotions or life history nor assign generic
“be self-reflective” writing. The aim is room to choose and continue a subject,
including choosing the measurements, rather than a prescribed introspective
performance. Any later comparison should read full prose and factual claims
separately; changed words also change feedback and future states, so a small
sequence does not isolate a causal prompt effect. No current prompt, protocol,
evaluator or runtime was changed for this proposal.

## Source identity at this reading

These hashes identify the source read, not a new deployment or model execution.

| Source | SHA-256 |
| --- | --- |
| `crates/reservoir-core/src/codec.rs` | `6192482229710de6bf8a6377480ec891f940cf9ecd02da2f493b6e108db264ee` |
| `crates/reservoir-core/src/sustained.rs` | `2c5b190812504d097623a309f451bb4c6d550c165193834362ba77258e2167b7` |
| `src-tauri/src/model_transport.rs` | `23af2733a02092fd22521b0e8fc10eee2901b83a632adc2d137b7bf4a4112e28` |
| `src-tauri/src/sustained.rs` | `5399ac3d9faf9fcd291dcc6dd176f80c7cd712bc489e6969bfcf621a084223c8` |
| Prior `OPEN-WRITING-DESIGN.md` | `9bad4b24231b6bd9f0125c24e07b609ea087b14df879020804fa355ab6edebf9` |
