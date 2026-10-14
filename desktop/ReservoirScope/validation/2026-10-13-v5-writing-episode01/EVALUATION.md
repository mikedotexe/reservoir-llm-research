# Twelve-opportunity offline verification

This plan qualifies the retained mechanism and continuity of one bounded v5 writing
episode on the unchanged 0.17.0 package. It does not authorize a model call or
change a prompt, numerical rule, save gate or runtime setting. The
[protocol](PROTOCOL.md), [run plan](run-plan.json) and [separate reading rubric](RUBRIC.md)
own the selected configuration, execution boundaries and interpretation.

The [checker](check_real_model_export.py) is adapted from the qualified prior
twelve-opportunity episode checker. [The adaptation basis](checker-adaptation-basis-01.json)
binds the unchanged historical sources. This complete episode checker accepts v5
only and preserves twelve-slot accounting and exact optional provider input
evidence. It does not reuse the five fixed replies or token values of the synthetic
fixture. Its compact-scaffold checks derive from the separately qualified 0.17
synthetic checker; the real-model replies remain unconstrained prose.

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
- Current observations matched to numerical frames, with every v5 retained prior scalar
  snapshot matched to the preceding **reached observation**. That history is
  distinct from the latest **saved and applied journal** used as prose memory.
- Exact prior full text, hash, path and applied boundary, plus its earlier memory
  read confirmation and decoded single JSON-string occurrence near the end of the prompt. The hash and
  journal identity remain retained evidence and are not required in the v5 prompt.
  All twelve completed entries imply eleven such journal memory joins. The
  application supplies the most recent applied entry, not all twelve earlier
  journals or a claim of independent long-term memory inside the language model.
- Frozen seed, v5 version, owned endpoint, configured model, cadence, attempt/step,
  duration/storage and generation budgets. Host timestamps are reported only
  where retained; they are not treated as simulated seconds or physical durability.

## Compact supplied context versus retained evidence

V5 supplies the current/prior recurrent RMS and separate sensory fill, signed
changes for those two measurements, and nonnegative state-coordinate L2 distance.
The entire observation-v2 state, spectrum and prior scalar reference remain in the
export. The static checker requires the retained 32-coordinate state and
32-eigenvalue sensory spectrum and checks prior scalar snapshots against the
preceding reached observation. This does not mean all retained fields were sent
to the model.

The prompt scaffold excludes the other measurement rows, raw vectors, journal
IDs, hashes and paths. These checks stop before the quoted historical prose:
a prior entry may contain those words or apparent section markers without becoming
a new instruction or forbidden scaffold. The one LF-delimited JSON string must
decode to the full saved/applied text, including Unicode line separators,
combining marks, quotes, newlines and backslashes. The observed/applied provenance
lines and closing marker precede the exact final open invitation. First-entry
absence is explicit and not represented by invented zero measurements.

Exact full prompt wording and numeric rendering are checked by the pinned
production replay. The static helper supplements that authority with structural
exposure checks; it is not an independent formatter or a second numerical engine.
The reader may inspect additional retained measurements, but a prose claim about
an omitted measurement is not automatically a claim about a value supplied in
this prompt. A value may also have arrived through historical prose. Read those
sources separately using the [rubric](RUBRIC.md).

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
memory-read confirmation. V5-specific cases cover hash-free prompt memory, exact
final placement, old/unknown-version rejection, full retained dimensions, malformed
compact rows, provenance boundaries and inert adversarial historical prose. These are static-checker tests, not valid numerical
fixtures or evidence that a model ran. The executed count and source identities
are bound by [checker-tests-01.json](checker-tests-01.json).

After the parent hands off an immutable native export, supply explicit absolute
paths and the frozen 0.17 executable identity:

```sh
python3 -B check_real_model_export.py \
  --bundle /absolute/path/to/native-export \
  --executable /absolute/path/to/0.17-pinned/reservoir-scope-desktop \
  --expected-executable-sha256 7d46719838495b7a9ba57eea69ac9c940bb81f2fdc47cd12b761d97bb472d081 \
  --expected-model gemma3:4b \
  --expected-prompt-version reservoir-journal-v5 \
  --protocol /absolute/path/to/this/run-plan.json \
  --expected-endpoint http://127.0.0.1:EXPLICIT_OWNED_PORT \
  --output-directory /absolute/path/to/new-review-directory
```

The output directory must be new and outside the input bundle. The retained
`receipt.json`, CLI stdout/stderr and `quality-review-material.json` are append-only
evidence. An optional later recovered export receives its own receipt and exact
file comparison, without rewriting the original episode outcome. No checker
discovers live stores, contacts services, opens UI, or invokes an automatic retry.
