# Optional provider prompt-count evidence

Introduced by the Tauri 0.16.0 candidate. This is retained transport evidence,
that does not affect numerical behavior, journal completeness or save eligibility.
Replay checks its retained consistency. It changes no journal prompt version or
numerical mechanism.

The [Ollama chat API](https://docs.ollama.com/api/chat) describes
`prompt_eval_count` as the number of tokens in the prompt. The application records
that provider assertion; it does not independently tokenize the prompt or certify
complete processing, attention, comprehension or factual accuracy.

## Response and portable representation

Sustained response events, pending candidates and saved journal records may carry
`providerPromptEvaluation` in their retained `LanguageResponse`:

```json
{"status":"reported","count":9007199254740993}
```

`count` is an unsigned 64-bit JSON integer. Zero is a reported count, not missing.
Missing or JSON null `prompt_eval_count` produces absent evidence. Absent evidence
is omitted when serializing a response, preserving historical response/checkpoint
serialization. Portable records retain integers; frontend IPC uses exact decimal
strings, including values above JavaScript's safe integer range.

Malformed optional counts are retained as a bounded diagnostic:

```json
{"status":"unusable","reason":"wrongType"}
```

Reasons are `wrongType`, `negative`, `nonInteger`, `outOfRange`, or
`duplicateField`. Parsing uses the original JSON token, not a floating-point
conversion. Positive fractional/exponent tokens are `nonInteger`; a negative
numeric token is `negative`. Repeated field names are ambiguous even if their
values agree. Invalid JSON or an invalid established response envelope still
fails the existing transport checks.

Usability of this optional count does not change the established complete-response,
model identity, byte, deadline, cancellation, durable-save or next-step application
requirements. A complete response with unusable metadata can save normally. An
incomplete response with a reported count cannot become eligible feedback.
The current finite-record families retain their existing field sets.

## Inspection and compatibility

The selected journal's closed **Evidence** section shows **Reported prompt tokens**
separately from **Requested context capacity**. Evidence stays attached to that
entry. An explicit recovery inspection returns at most the newest 50 received
response summaries, with total/truncation status; this includes incomplete attempts
without treating them as saved journals. Stop-reason previews are capped at 256
Unicode characters with explicit truncation status; the full values stay in the
bundle. Attempt/step identities and reported input
and output counts in that summary use decimal strings.

The field is additive within the sustained v1 family. The tested pinned 0.15 reader ignores
it: a passing old replay does **not** validate its schema or consistency with the
corresponding response event. The actual new five-response bundle is rejected by that older reader at its
checkpoint hash check. Compatibility therefore depends on retained checkpoint
state; neither blanket acceptance nor blanket rejection is promised. A 0.16-aware
verifier is required for the new evidence checks.
Original historical records remain unchanged. Verification establishes retained
internal consistency, not authentication of a provider's assertion.

The [0.16 qualification protocol](../../desktop/ReservoirScope/validation/2026-10-13-input-evidence-0.16.0/PROTOCOL.md)
separates synthetic transport, historical compatibility and actual packaged UI checks.
