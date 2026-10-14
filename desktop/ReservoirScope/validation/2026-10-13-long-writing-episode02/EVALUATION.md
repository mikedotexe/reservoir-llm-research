# Twelve-opportunity offline verification

This plan qualifies the retained mechanism and continuity of one bounded writing
episode on the unchanged 0.16.0 r2 package. It does not authorize a model call or
change a prompt, numerical rule, save gate or runtime setting. The
[protocol](PROTOCOL.md), [run plan](run-plan.json) and [separate reading rubric](RUBRIC.md)
own the selected configuration, execution boundaries and interpretation.

The [checker](check_real_model_export.py) is a new copy of the prior 0.15 real-model
checker. Historical checkers and receipts remain unchanged. It adds the exact
optional provider input evidence qualified in 0.16 and a twelve-slot outcome;
it does not reuse the five fixed replies or token values of the synthetic fixture.
This complete episode checker accepts v4 only. Small inherited memory-helper
tests for older versions do not claim whole-episode qualification of those versions.

## Distinct results

The top-level `status` reports integrity, including exact pinned production replay.
`evidence.continuity.outcome` independently reports `complete`, `partial` or
`unstarted`. A valid incomplete response, saved entry awaiting application, or
early stop can pass integrity while the twelve-entry outcome remains partial.
No missing opportunity is replaced or inferred successful.

Exactly twelve slot rows are emitted, for observation steps 30, 60, …, 360 and
first possible application steps 31, 61, …, 361. Each row identifies whether its
observation was reached, dispatch was recorded, a response arrived, the response
was complete, a journal was saved, feedback was applied, and the slot remained
unstarted. An undispatched slot can be reached/prepared; this is different from an
observation that was never reached. A missing response has `complete: null`, not a
fabricated failure response. Failure/cancellation/interruption events remain visible.

Full twelve-entry continuity requires all twelve unique complete received
responses, saves and next-step applications, with the retained numerical prefix
ending at step 361. Retry, Skip and budget-extension events are outside this frozen
episode. Any such event is reported as a protocol violation, not silently omitted.
Twelve related entries constitute one episode, not twelve independent subjects.

## Evidence checked

- Exact supplied package SHA-256, executable identity before/after pinning,
  production CLI exit/result and immutable exported-file inventory. The checker
  calls only the offline `--verify-sustained` path, with `modelsContacted: false`.
- Contiguous segment and event identities from genesis, byte-hash predecessors,
  typed checkpoint continuity, anchored journal bytes and final manifest anchors.
  Production replay supplies the numerical and complete prompt reconstruction
  check; the static checker is not a second independent eigensolver.
- Each dispatched attempt, received response, pending journal, saved journal,
  readback receipt and first application joined by its retained identity. Save
  follows response; application follows save at the next numerical step, once.
  Incomplete received text remains inspectable and cannot count as a journal.
- Current observations matched to numerical frames, with every v4 prior scalar
  snapshot matched to the preceding **reached observation**. That history is
  distinct from the latest **saved and applied journal** used as prose memory.
- Exact prior full text, hash, path and applied boundary, plus its earlier memory
  read confirmation and decoded single JSON-string occurrence in the prompt.
  All twelve completed entries imply eleven such journal memory joins. The
  application supplies the most recent applied entry, not all twelve earlier
  journals or a claim of independent long-term memory inside the language model.
- Frozen seed, v4 version, owned endpoint, configured model, cadence, attempt/step,
  duration/storage and generation budgets. Host timestamps are reported only
  where retained; they are not treated as simulated seconds or physical durability.

## Optional provider input evidence

Each received response, including an unsaved incomplete response, retains one of:
absent, `reported` with an exact unsigned-64-bit count, or `unusable` with one of
the five bounded reasons. Review summary counts use decimal strings; raw retained
responses in review material preserve their original JSON numeric type. The
checker never routes an integer through floating point, guesses zero for absence,
or coerces a malformed retained typed object into a usable count.

The count must agree across the received event, pending candidate and journal.
This is internal consistency, not provider authentication. Requested context,
input count, output count, UTF-8 bytes, Unicode characters and prior-text bytes
remain separately named. No ratio or threshold is used to certify input coverage,
attention, comprehension, continuity quality or accurate prose. Optional missing
or unusable evidence does not make otherwise complete writing a failure.

All saved prose and every received response are retained for review, without
text truncation; a received response remains bounded by the existing 1 MiB
transport-evidence limit. Prompt, observation, memory, textual features and reduced
feedback vectors remain available. Human/agent prose reading is separate and
must not turn expressive metaphor into a literal measurement by default.

## Qualification and execution

The [focused tests](test_real_model_export.py) use temporary hand-built structural
bundles, including a twelve-entry chain, early cutoff, unstarted history and a
twelfth saved entry awaiting application. Re-anchored mismatches exercise prior
measurements, exact memory, response metadata, duplicate attempts and missing
memory-read confirmation. These are static-checker tests, not valid numerical
fixtures or evidence that a model ran. The executed count and source identities
are bound by [checker-tests-01.json](checker-tests-01.json).

After the parent hands off an immutable native export, supply explicit absolute
paths and the frozen r2 executable identity:

```sh
python3 -B check_real_model_export.py \
  --bundle /absolute/path/to/native-export \
  --executable /absolute/path/to/0.16-r2-pinned/reservoir-scope-desktop \
  --expected-executable-sha256 73872388b56d2483054497aa8513e3659f79dfaf255699d6bca29041cafd258d \
  --expected-model gemma3:4b \
  --expected-prompt-version reservoir-journal-v4 \
  --protocol /absolute/path/to/this/run-plan.json \
  --expected-endpoint http://127.0.0.1:EXPLICIT_OWNED_PORT \
  --output-directory /absolute/path/to/new-review-directory
```

The output directory must be new and outside the input bundle. The retained
`receipt.json`, CLI stdout/stderr and `quality-review-material.json` are append-only
evidence. An optional later recovered export receives its own receipt and exact
file comparison, without rewriting the original episode outcome. No checker
discovers live stores, contacts services, opens UI, or invokes an automatic retry.
