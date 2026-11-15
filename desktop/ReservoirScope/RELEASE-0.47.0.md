# 0.47.0 · control explanations and Unicode admission

The three-model inquiry comparison exposed two apparatus problems: rejected
formatted controls returned a generic missing-NEXT message, and complete semantic
replies containing ≤ or ≈ could be held by the unrelated surface-codec Unicode
gate before reaching the embedding model.

New explicit selections now address both problems:

- **Continuing inquiry → Specific correction feedback** saves
  `controlFeedback: "diagnostic-v1"`. Later ordinary prompts and desktop receipts
  explain NEXT, input and inquiry independently. Formatting and argument errors
  retain the actual rejection and offer correction guidance. PROBE diagnostics
  distinguish JSON, dimension, coordinate, norm and byte-limit problems.
- **Embedding → Unicode text** saves `textAdmission: "utf8-v1"`. Any valid UTF-8
  text containing a non-whitespace scalar passes the semantic admission gate,
  subject to the existing size and completion checks. A fixed Unicode White_Space
  set defines empty input. Raw response bytes and hashes are preserved through
  encoding, save/readback, restoration, memory and replay.

Diagnostics retain a candidate count and one bounded prefix from the last
control-looking line per channel: at most 256 UTF-8 bytes, with its line number
and truncation flag. Explanations are bounded to 1,024 bytes each. Previous
candidate text is JSON-quoted as inert evidence in prompts and escaped as text
in the UI. It is never passed back into the action parser. The plain-format
guidance includes an exact 48-coordinate zero PROBE example and allowed pulse
strengths. NONE remains an available choice.

These are independently versioned policies layered over the V3 invitation and
semantic codec. They do not alter the action grammar, repair rejected vectors or
normalize journal text. Historical omission retains the old behavior and omits
the new fields from serialization. Existing sessions are not migrated. Both
earlier choices remain selectable for new comparisons. Surface statistics retain
their historical Unicode qualification. Plain scheduled prompts remain exact;
scheduled replies remain passive and feed their complete text back.

Completed writing still waits for durable save and readback before application.
Embedding retries reuse the same response without another writing request.
Invalid fresh input directives still withhold numerical text independently of
NEXT and inquiry; malformed formatted text is not promoted to authority.

## Verification

- Core: 355 tests passed, including eight focused tests for the new policies.
- Desktop host: 319 tests passed; three existing opt-in investigations remained
  ignored. Unicode, encoding failure/restart/retry, once-only action application
  and immutable export were exercised with deterministic providers.
- Frontend: 596 tests passed; one existing test remained skipped. TypeScript and
  the production build passed. Escaped candidate display, UTF-8 excerpt bounds,
  policy validation and immutable session settings were checked.
- Rust formatting and workspace/all-target Clippy with warnings denied passed.
- A separate local macOS **Reservoir Scope Feedback** 0.47.0 app was built with
  identifier `research.reservoir.scope.feedback`. Native setup selected specific
  feedback and defaulted a fresh embedding selection to Unicode. A three-turn
  scripted surface session reached step 4, displayed independent control feedback,
  and passed exact replay. No model was contacted for qualification.
- All three completed 0.46.1 study exports passed exact genesis/event/numerical
  replay with the new binary: Gemma 109 journals, GLM 143, Ministral 122. Their
  manifests remained byte-identical. GLM's historical incomplete-response outcome
  and Ministral's historical Unicode-admission outcome were reproduced rather
  than reinterpreted under the new policies.

Private qualification logs, build configuration, executable hash and replay
receipts are retained under
`research/outputs/control-feedback-unicode-20261115/qualification.json` and
`legacy-replay-receipt.json`. The previous study apps and stores were untouched.
This is a local build and source checkpoint; no ref was pushed.

Runtime correctness does not establish that a model will use the feedback well.
No new long model run or claim of improved investigation quality accompanies
these implementation changes.
