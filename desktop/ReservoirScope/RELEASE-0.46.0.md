# 0.46.0 · continuing questions and designed input probes

November 14, 2026. Local development checkpoint on `codex/inquiry-continuity`,
extending the 0.45.0 semantic recovery version.

New action-enabled sessions can retain a question across ordinary entries. An
explicit `INQUIRY` choice opens, continues, replaces or closes it. Later entries
receive an identified opening observation and bounded recent journal evidence,
so an expressed curiosity can have a subsequent opportunity for investigation.
Omission keeps the question open. This adds no extra model calls or outside
research. [Behavior, limits and syntax](CONTINUITY-INQUIRY.md).

`NEXT: PROBE` accepts a model-designed vector of 48 numerical input coordinates.
It enters the existing input channels for one step, independently of whether
the entry's text is withheld. It differs from `PULSE`, which changes recurrent
state directly. The exact accepted input and its immediate paired recurrent
response are retained. Bounds are explicit; invalid vectors are rejected without
padding or normalization. Separate sensory-field observations are not presented
as isolated probe effects.

The new invitation leaves subject, form and length open. It distinguishes
observed change from additional action effect, clarifies that `RELEASE` preserves
state and history, and gives send and withhold as independent choices. Eight
meaningful interventions and eight input-disposition transitions have separate
retained histories. Later `NONE` choices do not immediately displace an earlier
intervention.

This is the versioned `authored-v3` / `reservoir-journal-actions-v3` mechanism.
Enabling shaping selects **Continuing inquiry and reservoir actions** for a new
session; the earlier action contexts remain selectable and saved sessions keep
their original contract. Scheduled conversations remain passive, and their plain
prompt is still exactly the configured text. Encoding recovery reuses the saved
writing and applies its inquiry and probe once.

The desktop exposes the retained question, opening evidence, selected excerpts,
inquiry receipts, meaningful actions, input transitions and exact probe vectors.
See the [first-session guide](GETTING-STARTED.md#give-a-curiosity-a-later-opportunity).

## Qualification record

| Check | Observed result |
|---|---|
| Core | Broad suite: 345 passed. Final focused inquiry suite: 23 passed, including two later additions; 347 distinct passing cases in total. |
| Desktop host | Broad suite: 317 passed, three existing opt-in investigations ignored. Seven final focused cases passed after review corrections, including one additional memory-evidence case. |
| Frontend | 591 passed, one existing skipped test, across 69 files. TypeScript and production build passed. |
| Rust formatting and Clippy | Final workspace/all-targets checks passed, warnings denied. |
| Scripted core fixture | Six saved/read-back entries; inquiry open, continuation, omission, release and close; probe and checkpoint/segment roundtrip verified. |
| Native app | Built, ad-hoc signed, signature verified; failure, normal quit/relaunch, restore, retry, application and export exercised. |
| Native replay | New inquiry export and both completed 0.45.0 three-hour model exports passed exact offline verification. |

Review found that host memory evidence still labeled a full journal body as
supplied although V3 supplies a bounded prefix. The correction uses the core's
shared UTF-8-safe 2048-byte prefix, its own hash and truncation metadata, while
retaining the complete raw entry identity. Long multibyte ordinary and telemetry
memory, prior conversation text and legacy parity are covered. Display validation
also rejects inconsistent inquiry identities and history chronology. The final
targeted checks and native build include these corrections; the broad host suite
preceded them.

The native loopback fixture made **three writing requests and two embedding
requests**. Its first reply opened a question and withheld text while applying
`PROBE [0.5,0,…,0]` at step 3. The second reply's first encoding deliberately
returned HTTP 503. Quitting, relaunching and restoring retained the original
question, probe receipt and exact second reply. Retry used the identical encoding
request without another writing call; explicit Resume applied CONTINUE and text
at step 5. The third reply closed the inquiry and withheld text at step 7. The
three-attempt budget then held the session. Exactly one probe was applied, with
immediate recurrent difference L2 `0.6254034759038498`; this is fixture evidence,
not a model-selected investigation. The immutable revision-33 export passed
genesis, contiguous event/numerical replay and journal/application verification.

The native walkthrough used **Reservoir Scope Inquiry**, identifier
`research.reservoir.scope.inquiry`, with binary SHA-256
`346144d9cc99e9ae05ead62ef6a5ff3b9b31ea2dd129df3e19375f35323679e6`.
Source checks, logs, fixture requests, exports and verification receipts remain
in ignored `research/outputs/continuity-inquiry-20261114/`. The older Semantic
app and completed studies were preserved. The local bundle is not notarized or
qualified for distribution; the existing frontend chunk-size advisory remains.

A subsequent setup-only correction raises the new V3 local-model context preset
to at least 16,384 tokens. A separate 21,835-byte synthetic full-evidence stress
prompt required 11,127 reported input tokens on Gemma and 9,629 on GLM: neither
fit 8192, while both fit 16,384 with the ordinary output/template reserve.
These were two one-token transport checks, not journal-quality samples. Larger
custom sizes survive explicit V3 selection; smaller Advanced values remain
allowed; existing and restored sessions are not upgraded. The final app's
inquiry-first setup was inspected and showed 16,384, and the native fixture
export verified again with the final binary. Core prompts and host execution
were unchanged by this correction. The final bundle, built from code checkpoint
`ce511c1`, is also ad-hoc signed and signature-verified; its binary SHA-256 is
`4ef8b949feaab9add1a9a01d643518fa49c96e5d65e428e4a81d114ba9bbe1da`.

The separately declared [frozen-context wording diagnostics](../../research/studies/2026-11-14-continuity-prompt-diagnostics.md)
completed all 48 planned local calls without retries or reservoir applications.
Model digests remained unchanged and all provider-reported prompt counts fit the
declared headroom check. Two independent anonymous readings were fixed before
unblinding. Clearer comparison wording helped some responses, particularly the
paired Gemma NONE cases, but interpretation errors remained. Balanced input
examples did not establish reduced withholding, and nine of the 24 input-example
responses had rejected NEXT syntax. These are native parser classifications,
not executed actions. [Results, counterexamples and context stress check](../../research/studies/2026-11-14-continuity-prompt-results.md).

The diagnostics concern selected known contexts and isolated wording changes.
They do not establish the benefit of the full inquiry mechanism. Runtime tests
and scripted fixtures establish application and persistence behavior, not that
a model will conduct a good investigation or have an experience. The local
preview does not replace the frozen research instrument or sharing candidate.
