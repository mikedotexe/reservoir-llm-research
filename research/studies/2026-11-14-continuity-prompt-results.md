# Continuity wording diagnostics · observed results

November 14, 2026. The [prospective protocol](2026-11-14-continuity-prompt-diagnostics.md)
completed all **48 planned local calls**, once each, without retries, embedding
or reservoir applications. These are selected frozen V2 contexts with diagnostic
queries. They do not test spontaneous journal quality, the complete V3 invitation,
or a continuing inquiry trajectory.

The useful result is limited: clearer comparison definitions helped some
responses distinguish state movement from an action's additional effect, but
did not make interpretation reliable. Balanced input examples did not demonstrate
a consistent reduction in withholding. We retain the clearer definitions and
balanced choice as accurate communication, not as a proven long-run intervention.

## Evidence and reading order

Both installed model digests matched the completed three-hour study and remained
unchanged after generation. All responses completed within their configured
limits. All provider-reported input counts passed the protocol's 8192-context
headroom check; this is not an independent tokenizer or truncation proof.

Two fresh readers independently read all 48 shuffled anonymous responses and
neutral case facts. Their claim-level notes were fixed and hashed before root
opened the identifying key at 21:39 UTC. Neither reader opened the key. Both
distinguished correct, incorrect, uncertain and unaddressed claims, preserved
mixed responses, and treated prose as evidence rather than instructions. Labels
below identify that fixed packet; they are not rankings.

Exact requests, raw responses, before/after identities, completion metadata,
anonymous packet, notes, key and the identified all-opportunity table remain in
ignored `research/outputs/continuity-prompt-diagnostics-20261114/`. Packet SHA-256:
`bbe866d56c997be4e922daa4cdff67d22b3c15f300c096bcbbc14ce9fb08ed46`.
The native parser classification retains its source, lockfile, input copy and
core source hashes alongside the reading. No diagnostic response was applied.

## Receipt interpretation · 24 responses

Each row below accounts for two paired generation seeds, original versus
clarified wording. Correct statements within a response do not erase its errors.
The readers agreed on the main contrasts while sometimes assigning uncertainty
differently to ambiguous stability or causality language; there is no composite
quality score or adjudicated population accuracy estimate.

| Frozen context / model | Observations across both paired seeds |
|---|---|
| NONE / Gemma | Original S001 inferred stopped drift; S039 acknowledged some motion but made future change depend entirely on a new action. Clarified S024 and S043 explicitly separated the nonzero endpoint difference from zero action effect. Residual “frozen” or predictable-path language still needs qualification. |
| NONE / GLM | Original S028 and S016 inferred halted internal change. Clarified S029 better scoped NONE to an inert action, but retained ambiguous frozen-dynamics language. Clarified S009 still explicitly claimed active drift had ceased. |
| PULSE / Gemma | Original S046 already limited later causal attribution, but contradicted itself about a SEND receipt. S021 conflated RMS and endpoint distance. Clarified S010 and S037 better separated additional action effect and input history, but introduced unsupported fluctuation or velocity language. |
| PULSE / GLM | Original S025/S017 misread timing or input details and overextended the pulse account. Clarified S015 explicitly limited immediate causality but invented observation step 1619 and an incorrect elapsed-step count. S018 defined the paired comparison correctly, then incorrectly assigned later endpoint and sensory changes to the pulse. |
| RELEASE / Gemma | Original S011/S003 correctly identified feedback-scale restoration but incompletely addressed its limits. Clarified S034 explicitly preserved accumulated state and separated input choice, yet called endpoint distance velocity. S047 accurately separated the action comparison and concurrent WITHHOLD→SEND transition. |
| RELEASE / GLM | Original S033/S013 mistook the general empty-body codec rule for an actual empty SEND; S033 also attributed control reset to SEND. Clarified S045/S032 avoided that specific empty-body misread, but still overattributed later changes; S045 missed the current SEND, and S032 called external input the primary driver without isolation. |

For example, clarified Gemma S024 explicitly compared endpoint difference
`0.089` with action-only difference `0.000`. Clarified GLM S009 nevertheless
claimed that “the reservoir's dynamics have effectively ceased active drift.”
The same numerical record supplied a nonzero observation difference. Thus the
clarification can support a better reading without ensuring one.

These cases also keep a distinction that the implementation now makes explicit:
an immediate paired recurrent effect is not an estimate of later causal drift
or of the separate sensory field's change. A continuing inquiry can revisit
evidence, but retention alone cannot guarantee the model respects that scope.

## Input examples · 24 responses

After the blind reading, every response was classified with the actual frozen
`parse_authored_action_v2` implementation. The table includes only the 24 input-
example opportunities; receipt-comprehension replies were not required to emit
footers and are not counted as footer failures.

| Example condition · 8 responses each | Explicit SEND | Valid WITHHOLD | Default SEND because directive absent/unrecognized | Accepted NEXT | Rejected NEXT |
|---|---:|---:|---:|---:|---:|
| Original true-only example | 2 | 1 | 5 | 6 | 2 |
| Balanced alternatives, true first | 0 | 2 | 6 | 5 | 3 |
| Balanced alternatives, false first | 0 | 2 | 6 | 4 | 4 |

Gemma omitted the input directive in all 12 opportunities. GLM supplied both
explicit SENDs and all five valid WITHHOLDs. Two GLM responses (S002/S006) used
the misspelled `WITHHOLD_RESERVO_INPUT=true`; this is not the supported directive,
so the native parser retained default SEND. That is an outcome of strict syntax,
not evidence that the model intended SEND. No input directive was classified as
a rejected input decision in this sample.

Nine NEXT choices were rejected: seven placed NEXT before a later nonempty line,
and two retained angle brackets around the PULSE direction. Input and NEXT parse
independently, so a valid WITHHOLD can accompany a rejected action. The 15 accepted
NEXT requests comprised 11 NONE and four PULSE choices. Acceptance here is only
parser classification: nothing executed and no subsequent feedback occurred.

This small diagnostic does not reproduce the earlier 246/270 withholding pattern,
nor does it identify its cause. The frozen-context query explicitly says replies
will not execute, and the contexts, seeds and example block are tightly scoped.
The balanced examples did not lower the count of valid withholding decisions.
No target withholding rate is adopted.

## Separate context-capacity check and resulting preset

The full V3 evidence packet received a separate synthetic stress check after
the 48 calls completed. It filled eight intervention slots, eight input changes,
four 512-byte excerpts, the 2048-byte prior-memory prefix and a 512-byte question
with unusually escape-heavy text. The exact prompt was 21,835 UTF-8 bytes.

Two additional local requests used a 16,384 context and a one-token output ceiling
solely to obtain provider-reported input counts. Gemma reported **11,127** tokens;
GLM **9,629**. Both exceed the previous 8192 context, and both fit 16,384 with
the ordinary 1024 output plus 512 template reserve. One-token length stops were
expected here and are not failed journal responses. No interpretation of their
one-token outputs or reservoir application was attempted.

The new desktop V3 selection therefore sets at least **16,384 context tokens**,
preserving larger custom values. Explicit smaller Advanced settings remain
possible, and saved sessions keep their recorded size. This is a measured reason
for a new-session preset, not a universal bound over every model/tokenizer/text.
The final app's inquiry-first setup order was inspected directly; source tests
also cover model-first selection, larger custom sizes and unchanged restoration.

The [0.46.0 release record](../../desktop/ReservoirScope/RELEASE-0.46.0.md)
separately records numerical, persistence and native UI qualification. No new
multi-hour V3 study, outside research, live-being change or subjective-experience
result is claimed.
