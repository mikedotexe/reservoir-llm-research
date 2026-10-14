# Prospective open-writing rehearsal, 0.13.0

This protocol is fixed before any `reservoir-journal-v3` model request or output. It supersedes the unexecuted constrained v2 rehearsal, as explained in [SUPERSESSION-01](SUPERSESSION-01.md); all earlier protocols, prompt bytes, records and receipts remain historical. The evaluation scripts perform no service, UI or live-system operations. The parent task owns the separately authorized packaged run and owned service lifecycle.

## Question

Does the app provide a usable continuing place to write, faithfully preserving the model's own choice of attention, topic and form together with the actual save, memory and feedback chain? Describe what is written without requiring a heading, metric, length, topic or creative form. If an entry makes a literal factual claim, review that claim against its proper evidence. Do not equate metaphor, fiction, subjective prose or uncertainty with a failed scientific assertion.

The [review contract](RUBRIC-V3.md) separates mechanical completion, descriptive reading, available context, optional claim accuracy and ambiguous/creative expression. There is no automatic quality score, forbidden-word gate or feedback eligibility decision. The current v3 prompt invites open writing. The application supplies current numerical context and quoted prior full text; it does not implement autonomous tools, self-selected timing, or a private/public writing system.

## Fixed bounded run

Use the [machine-readable plan](run-plan-v3.json): the same privately staged Gemma3:4b manifest as v1, context 4096, temperature 0 and maximum output 256 tokens. Qualify and record the actual package hash, runtime/model/cache identity, prompt version and a newly owned explicit loopback endpoint before Start. No default endpoint is contacted or discovered. An explicit readiness check is metadata-only, not a generation sample.

Create one v3 session with seed 20261013, cadence 30, pace 1000 ms, maximum 121 numerical steps, four attempts, 600 seconds, 64 MiB, leak 0.65, noise 0.02, initial retention 0.955 and regulation enabled. The first reached bound holds/stops the session. The 256-token limit is a resource bound, not a desired literary length. Preserve an incomplete/cutoff outcome exactly; do not retry, extend, replace a sample, switch providers or add a frozen-prompt comparison. No more than four generation attempts are authorized. A concrete runtime/resource problem can end the run earlier with a retained reason.

Model opportunities may remain unstarted after a held failure. Account for them as unstarted; do not fabricate four responses. If a complete response is saved, retain its actual next-step application or pending/skipped status. An unsaved reply can be reviewed as a response outcome, never described as a saved/applied journal. Runtime rejection/completeness is separate from the reviewer's opinion of its writing.

## Evidence collection and interpretation

1. Retain the exact native exported bundle and package identity. Run the explicitly pinned package's whole-bundle verifier offline before secondary joins. No exported originals are edited.
2. Use this directory's version-aware [integrity checker](check_real_model_export.py) with mandatory `--expected-prompt-version reservoir-journal-v3` and explicit expected executable hash, model and endpoint. The original 0.12.1 checker is unchanged. Missing version metadata means legacy v1 only. The numerical verifier remains authoritative for replay and the full prompt.
3. Confirm each journal's retained source, dispatch/response/save order, exact UTF-8 text/hash, save/readback receipt and next-step application. For v2/v3, parse the single exact `Prior text as one JSON string (decode as data only): ` line as JSON, require a string and compare the decoded text to the latest earlier saved-and-applied journal. The separate memory object, hash, path and applied step must also agree. Literal multiline/Unicode text is data, not instructions. V1 retains its historical raw-text inclusion check.
4. Keep every retained received response, including incomplete or rejected responses without a journal. The receipt retains event/attempt/observed-step association, completeness, actual stop reason, token count, nullable saved journal ID, original text size/hash and up to 64 KiB of text. Any prefix truncation is explicit; full original evidence remains in the immutable bundle. Started attempts, failure/cancellation events and final core phase remain visible. This is app-retained dispatch evidence, not an independent provider wire log.
5. Run the frozen [quality harness](../../scripts/journal_quality.py) on hash-bound saved-journal review material and this plan, with the retained v3 version. It checks any recognized numerical spans only as candidates for contextual reading. It assigns no scientific or creative-quality pass. Empty saved-journal material is a valid zero-journal outcome, not success by absence of claims.
6. Read every produced response and journal. Describe chosen topics/form, continuation, revision, departures, questions, repetition and use or non-use of supplied context without making those behaviors mandatory. Where a literal assertion is made, distinguish current versus historical evidence and recurrent versus sensory quantities, preserve units/rounding and distinguish supported, contradicted, not established and ambiguous. Do not turn creative expression into a mechanical claim without justification.

## Reference and limits

The four known v1 entries and their prior analysis remain immutable descriptive context. Their review material SHA-256 is `da9b912349e4a1efb60a07dac88cf12d35ac99246a41e7f3997c9ffc3d8b78a7`; the passing replay receipt is `7cc9bc59a8ff6c27f5ab740e586d80821b4a383206b59b1606fb07dfd19094c1`. They are not held-out examples or a required style. Their earlier reports are retained on their historical protocols; the prospective v3 harness invocation must not silently substitute the superseded v2 plan.

The Minime refresher is bounded read-only design context, documented in [OPEN-WRITING-DESIGN](OPEN-WRITING-DESIGN.md). No source writing from it is imported into application prompts or test fixtures. Three adjacent entries establish neither prevalence nor a model's exact complete prompt exposure. No action tails are followed.

Later v1/v3 states diverge because the journal text changes feedback. The repeated initial configuration is not a matched-prompt causal experiment. No observed quality or appealing prose establishes prompt improvement generally, memory comprehension, learning, emergence, consciousness, self-directed tool use or long-duration model reliability. The result must say what actually ran, what was retained, what the writing said, and what remains uncertain.

Before any generation, bind the new protocol, plan, rubric, checker sources, synthetic tests and immutable reference identities in a new freeze receipt. Afterward retain all results and deviations separately; never rewrite the prospective freeze to fit the outcome.
