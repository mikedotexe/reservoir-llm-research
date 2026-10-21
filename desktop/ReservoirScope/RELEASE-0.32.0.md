# 0.32.0 — Model thinking toggle

**Unqualified local source candidate, October 21, 2026, on top of 0.31.0.** Needed to run
the S-010 arms on `gemma4:12b`, the beings' own model family: under Ollama that model
thinks before it replies, the thinking consumed the whole 1,024-token output budget, and
every attempt was retained as blocked ("Incomplete or token-limited response cannot become
journal feedback"). Both beings' runtimes send gemma4 `think: false`, read read-only on
volya the same day.

## What changed

- `LanguageConfiguration.thinking: Option<bool>`. Omitted, every request body is byte for
  byte as built. `false` adds `"think": false` to the chat request, asking for the reply
  only; `true` adds `"think": true`. `Sampling.thinking` carries it to the transport.
- The journal object records `thinking` beside `temperature` and `samplingSeed`; the
  immutable-journal and replay checks compare it like the temperature; the journal
  detail view shows it.
- Advanced settings: a "Model thinking" choice (as built, off, on) with its explanation.
  Version 0.32.0.

## Checks run on this source

| Check | Result |
|---|---|
| `cargo test --locked -p reservoir-core` | 246 tests pass |
| `cargo test --locked -p reservoir-scope-desktop` | 260 pass, 3 ignored, 0 fail; new test: the `think` field is sent only when configured and leaves the messages and options unchanged |
| `npm test` | 58 files, 503 tests pass (new `ModelThinking.test.tsx`) |
| `npm run build` | TypeScript and Vite pass |
| `cargo fmt --check`, `cargo clippy --workspace --all-targets` | clean |
| macOS package | not attempted; see the 0.28.0 record |

Results of the gemma4 arms belong to the study's dated account. No human acceptance,
platform qualification or writing result is claimed.
