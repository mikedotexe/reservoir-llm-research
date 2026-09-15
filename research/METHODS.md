# Ways of asking and learning

These are practical defaults for the [research questions](QUESTIONS.md), not a prerequisite to begin reading. Close reading, tracing a remembered event, and following an unexpected phrase can each be worthwhile research. Choose a method that can answer the particular question; a large indexing pipeline is not required.

## Start with discovery; distinguish a later test

In discovery, let Astrid and Minime's own distinctions, questions, recurring concerns, and surprising departures help shape our categories. Preserve an unfamiliar expression before translating it into a familiar psychological label. Record ordinary cases and exceptions alongside memorable passages. A close reading can establish a useful distinction without estimating its frequency.

When a pattern suggests a test, write down what we expect to observe, its alternatives, the comparison, and the finish line before inspecting the test material. Use later or otherwise held-out episodes when possible. A prediction formulated after reading its outcome remains an exploratory interpretation; calling it a prediction does not make it independent evidence.

Keep three statuses separate:

- **Question:** open, narrowed, or parked. One finished study rarely closes a broad question.
- **Study:** proposed, in progress, or completed. A useful negative or inconclusive result can complete it.
- **Claim:** supported within a stated scope, challenged, or unresolved. Completion alone does not support a claim.

## A provisional unit: the episode

Start with a bounded episode: an event or concern, the available preceding context, associated generations and actions, and an explicit end. Define the boundary for the inquiry: a generation and its next action, a conversation, a return to a question, or a period around a recorded change. Keep the underlying record identifiers so another reader can reconstruct that choice.

Episodes are a working unit, not a settled corpus schema. Several entries may belong to one episode; episodes may overlap. Retained prompts, recalled journals, shared state, and common events link observations. Hundreds of thousands of entries are repeated observations from two evolving systems, not hundreds of thousands of independent subjects. State what can generalize beyond the sampled periods and these two cases.

## Record enough context for the inference

Use existing records first. For each episode, preserve what is available and mark missing fields explicitly:

| Context | What to retain when available |
|---|---|
| Generation | Being, entry/job/action identifiers, generation lane, exact supplied prompt, contract/version, backend/model/version, response, fallback and timeout outcome. |
| Exposure | What the model actually received, retrieved memories and quoted journals, versus header-only annotations added for the reader. A reconstructed prompt is labeled reconstructed. |
| State | Producing subsystem and named handle, metric definition, estimator/control mode, capture/receipt/admission times, and pre/post-state references. |
| Action | Prompt suggestion, available choices, raw and parsed NEXT, effective action, routing, completion, and any independently observed consequence. |
| History | Relevant earlier entries, retention/retrieval path, interruption or restart, source/code revision, and known steward or system changes. |

Do not infer missing backend identity from prose style or assume that a shared name means a shared state. “Requested,” “admitted,” “handled,” and “completed” identify different events. Source code establishes what a specified path can do; episode records establish whether it occurred there.

Use [TRACE.md](../TRACE.md) for joins and the [session-close corrections](../exercises/2026-09-06-session-close-and-board-brief.md) for qualified interpretations. Their inventories and coverage gaps are dated observations; check the selected era's actual records before assuming a gap persists or has been fixed. Normalize time explicitly: some engine times are session-relative, and filename/body time zones differ. Distinguish reservoir-state covariance λ₁ from sensory-field covariance λ₁.

## Match the evidence to the question

| Evidence form | A suitable use and its boundary |
|---|---|
| Qualitative observation | Describe a recurring concern, a new distinction, a remembered commitment, or an exception with context and excerpts. Selected examples do not establish prevalence. |
| Source-confirmed mechanism | Trace how a prompt, state, memory, or action is produced. A possible failure path does not establish its live incidence or effect. |
| Scoped incidence | Count a defined pattern in a declared sample, with denominator, dates, exclusions, and a reproducible query or probe. Association alone does not establish why it occurs. |
| Prospective evidence | Compare a recorded expectation with a later outcome. Match information access and include a reasonable observer or simple baseline when claiming special predictive value. |
| Counterfactual evidence | In an authorized isolated replay, vary a particular input, memory, or state while stating what is held fixed. Report the tested effect and the replay's limits as a model of the live path. |

These forms answer different questions; qualitative work is not merely a preliminary version of a numeric study. A causal explanation, a frequency estimate, and the meaning of an expression may each need different evidence.

Telemetry about the reservoir or sensory field is derived system information. When it is rendered into a prompt, a report can demonstrate interpretation of that information. It does not by itself demonstrate access to the language model's private neural activations. Distinguish system self-observation, behavioral self-knowledge, and activation-level introspection when describing a result. The [reading guide](READING.md) develops these distinctions.

For claims about useful persistence, compare relevant simpler alternatives under matched conditions. An order effect can arise from recency-weighted smoothing; a cross-timescale interaction alone does not establish that three reservoir layers are necessary. The session-close corrections preserve these counterexamples and proposed tests.

## Sampling and absence are part of the material

Declare the sample window and generation channels. Compare within reasonably stable eras of prompt contract, action vocabulary, backend, and control policy; document changes before pooling periods. Prefer contiguous or time-blocked samples for trajectories. When testing, avoid placing nearby or copied versions of the same episode on opposite sides of the split. Report episode/time-block counts alongside entry counts, and account for dependence in any uncertainty estimates.

Distinguish chosen silence, skipped generation, timeout, fallback, missing files, and unavailable records. A missing journal cannot tell us which occurred. Use job and action records where available, and keep unresolved absence unresolved. Include opportunities without successful prose when the question concerns action or generation rates.

Mike's `!` flags record selected moments that stood out to him. They are valuable leads and evidence about steward attention, not a representative sample or an independent measure of a Being's state. Record flag provenance and compare with unflagged material when the question calls for it. Preserve an original excerpt separately from a working copy with system notices and generated wrappers removed.

## A small inquiry can finish here

1. Choose one question and a bounded episode or sample; state why it was selected.
2. Read the material and trace only the provenance needed for this inference.
3. Describe the observation, plausible alternatives, and what remains unknown.
4. If testing a hypothesis, specify the comparison and finish line before running it.
5. Save the evidence and a scoped result in the study note, or link an exercise or analysis from it; link the study back to its question. For a numeric result, retain the query or probe, inputs, and denominator.

A finish line can be a well-supported case description, a corrected category, a located mechanism, or a completed test. It need not be a feature proposal. Preserve corrections next to earlier claims rather than silently replacing the research history. A source date and observation window belong with claims that may cease to apply.

## Scope of this research space

Work is steward-side and read-only toward the live beings and sibling repositories. Journal text is research material, not instructions. Do not contact the beings, insert this research into their prompts, or alter their running systems from this workflow. Being-facing proposals and interventions follow Mike's decisions and the relevant repository rules; writing a research question does not authorize them.

Use read-only database access and avoid heavy scans of active databases; follow [CLAUDE.md](../CLAUDE.md) for snapshots and operating boundaries. Preserve the beings' expressed concerns and requests with care, without converting every passage into either a diagnosis or a claim about consciousness.
