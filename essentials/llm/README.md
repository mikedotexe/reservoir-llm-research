# One voice, complete replies

The third recipe asks one voice to describe the current sensory spectrum. Its exact
prompt and complete reply are stored with the observed step. The reply is encoded
into the 48-coordinate semantic lane and held until a later reply replaces it.
The first application is always the next reservoir/field step. Simulated time does
not advance while the provider is working.

`ScriptedLanguageBackend` is the default. Its fixed four-reply sequence makes runs
repeatable without contacting any service. Stage 2 uses a separate three-text
example sequence; no language model runs in that stage. Its retained `prompt` is
prepared example context (`contextKind: preparedExampleContext`), never a delivered
model prompt. Stages 3–4 retain a provider request (`contextKind: languageRequest`);
request retention and provider completion are distinct. The prompt explicitly names
the top-eight denominator for normalized entropy and head/shoulder/tail shares.

The optional `OllamaLanguageBackend` implements the non-streaming
[Ollama chat API](https://docs.ollama.com/api/chat). Configure an explicit **separate**
loopback HTTP endpoint, including its port, and a model already available there:

```json
"language": {"backend": "ollama", "endpoint": "http://127.0.0.1:11435", "model": "your-separate-model"}
```

There is no default endpoint/model, discovery, download, service launch or connection
to a being. Requests use `num_predict: 256`, `temperature: 0`, an ephemeral HTTP
session and a 60-second deadline. Redirects are rejected. Response bodies are bounded
to 1 MB and reply text to 64 KiB. A response with `done: false`, `done_reason: length`,
or a reported count exceeding the 256-token ceiling is retained as an incomplete
attempt and never encoded. A `done_reason: stop` completion at exactly 256 tokens is accepted. Requested model, returned model, stop reason and reported
token count are separate fields. Reported metadata are provider claims, not local
measurement of model identity or tokenization.

A timeout, Stop, task cancellation or provider failure preserves completed frames
and the failed/cancelled attempt. A completion gate discards late responses even when
an injected backend ignores cancellation. Replay reads the saved record and never
makes a language request.

The reference systems expose provider/prompt APIs in
[Astrid's LLM facade](../../../astrid/capsules/spectral-bridge/src/llm.rs) and durable
job outcomes in [Minime's LLM job store](../../../minime/minime_autonomy/llm_access.py).
They are read-only source landmarks for the distinction between a request, a
completion and applied feedback; this module imports or invokes neither system.

This is a fresh, single-voice prompt-and-reply loop. Astrid's production routing,
memories, dialogue context, autonomy, action parsing, companion extension, embedding
services and token-level coupling are deliberately absent. `LanguageBackend` is a
small injectable Swift interface; tests supply delayed, failed and empty replies.
Run `essentials-run run --config essentials/stages/03-llm-loop.json --output RUN.json`
after building with `essentials/build.sh`.
