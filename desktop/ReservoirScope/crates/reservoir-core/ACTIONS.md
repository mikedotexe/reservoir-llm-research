# Historical action-record verification

The Rust core reads and verifies retained `essentials-actions-v1`,
`essentials-actions-v2`, and `essentials-actions-v3` records. This is an offline
verifier of the historical Swift contract, not a new action-session runner. It
does not contact a language provider, save journals, follow a journal path, or
establish that a recorded provider or storage event actually occurred.

The implementation is [src/actions.rs](src/actions.rs). Its public entry point is
`ActionComparisonRecord::verify()`, with `validate_structure()`, `checked_steps()`
and `checked_turns()` available separately. The shared import/verification
dispatcher calls this implementation for the three formats.

## What is checked

- A–H numerical replay: the seed, original model weights, bias and recurrence
  settings, noise sequence, external forcing, held semantic input, previous and
  next reservoir states, sensory projection/covariance/spectrum, reduced fill,
  and H's next-step retention controller. Numerical tolerance follows the native
  verifier: `2e-7 * max(1, abs(expected))`.
- Both component arms and the separate observation comparison: arm identities,
  matching boundaries, declared observation channels, alternating request order,
  matched observation dynamics and G/H fixed-tape full-input constraints.
- The fixed reply tape, regenerated from its declared seed and zero-semantic
  sensory reference. Every nonfinal packet's text, choice, spectrum, raw codec
  features and shaped semantic vector are checked.
- Prompt versions 1 and 2, reconstructed from the retained observations after
  their numerical checks. Manual opportunities force `WRITE_JOURNAL`; scheduled
  G/H opportunities can choose `WAIT`. Memory exposure must be the most recent
  successfully saved journal in F–H. Prompt reconstruction retains the native
  eight-decimal formatting and exact journal text.
- The action-to-journal chain: raw response byte count and completion metadata,
  parsed action, content hash, journal identity, save receipt, exact relative
  path, portable journal copy, codec features and prepared feedback. A saved
  journal first applies at the next recorded step in E–H; feedback is held until
  a later successful journal. `WAIT` does not clear or replace it.
- Failure and cancellation boundaries. Unsuccessful responses cannot produce
  journal or feedback effects. A failed save retains its completed response and
  save failure, but has no prepared or applied feedback. In component
  comparisons a failed left action/save prevents the paired right request.
  Cancelled actions cannot retain a late provider outcome or resume as a matched
  comparison.

The decoder preserves the native historical absent-or-null specification
defaults. In particular, an absent prompt version means version 1 even though
the modern Swift constructor defaults to version 2. Missing or null whole
`language` configuration defaults to scripted; a present incomplete language
object is rejected. Existing shared loopback endpoint validation is reused for
retained Ollama configuration; verification never opens an endpoint.

## Bounded compatibility

The text codec and action-text whitespace classification now accept the bounded
Unicode contract documented in [CODEC-UNICODE.md](CODEC-UNICODE.md). The retained
native corpus has 1,124 matched vectors and 23 explicitly incomplete vectors;
selected canonical accents, scripts and emoji clusters are supported. Scalars or
graphemes outside that contract still return `Unsupported`, including text in
failed-save or response-validation receipts. Numerical tolerances are unchanged.

Response JSON parsing is also conservative. Local Foundation `JSONDecoder`
checks showed that it accepts trailing commas and a UTF-8 BOM and uses the first
duplicate known field; serde does not share these behaviors. Duplicate known
fields and ambiguous object-syntax errors therefore return `Unsupported`.
They must not turn a Swift-valid response into a falsely verified historical
response-validation failure. Some actually malformed response objects will
also remain incomplete until a compatible parser is independently qualified.
Standard JSON envelopes with qualified text and clear rejection cases such as the retained fenced
Markdown response are covered. Explicit provider completion/output-limit
failures are checked before response syntax.

Independent-generation records verify the retained response and its subsequent
effects; they do not prove a provider generated that response. A save receipt
and matching portable journal establish internal consistency, not the existence
of an external file. The verifier performs no filesystem reads from receipt
paths. This work does not demonstrate language-memory benefit or any claim
about the live beings, and it makes no new provider, deployment or action-runner
claim.

## Retained canonical coverage

[tests/actions_conformance.rs](tests/actions_conformance.rs) explicitly names
all 22 tracked canonical inputs beneath `essentials/examples/`:

| Group | Exact input names | Count |
| --- | --- | ---: |
| Historical v1 | `essentials-actions-feedback.json` | 1 |
| A–H fixed replay | `portable/example-component-1.json` through `example-component-8.json` | 8 |
| D–H independent generation | `portable/example-model-4.json` through `example-model-8.json` | 5 |
| Observation | `portable/example-model-observation.json`, `example-model-observation-active.json`, `example-observation-scripted.json`, `example-observation-active-scripted.json` | 4 |
| Preparation/failure evidence | `portable/example-preparation-1.json` through `example-preparation-4.json` | 4 |

These cover v1 legacy fields, v2 components/observation, v3 continuous
observation, A–H, scripted and retained model responses, journal memory, WAIT,
and recorded provider/response failures. Tests also mutate numerical and
evidence fields, exercise incomplete Unicode/parser cases, and derive bounded
manual/cancelled/failed-save records from canonical numerical evidence. Those
derived cases are verifier tests, not independent Swift session exports.

Native reference implementation:
[ActionTypes.swift](../../../../essentials/actions/ActionTypes.swift),
[ActionVerification.swift](../../../../essentials/actions/ActionVerification.swift),
[ActionMechanisms.swift](../../../../essentials/actions/ActionMechanisms.swift),
[ActionComparisonSession.swift](../../../../essentials/actions/ActionComparisonSession.swift),
and [ActionForcing.swift](../../../../essentials/actions/ActionForcing.swift).

Run from `desktop/ReservoirScope`:

```sh
cargo test --locked --package reservoir-core --test actions_conformance -- --nocapture
cargo clippy --locked --package reservoir-core --all-targets -- -D warnings
```

Qualification of fresh Swift-generated action sessions, broader seeds/noise and
failure injection, Unicode outside the bounded codec contract, general Foundation
JSON parser compatibility, and cross-platform numerical execution remains
outstanding. The independent Unicode action oracle covers terminal stage-4
journal mutations and explicit negative controls; it is not a fresh action run. Existing native source and retained input bytes
are unchanged.
