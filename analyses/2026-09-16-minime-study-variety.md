# Minime's study concentration: improved access, narrowing context

Minime's writing really has become concentrated in SELF_STUDY. The latest sequence contains useful local corrections, but repeatedly relocates an assumed blocking mechanism instead of accumulating a stable answer. Our changes repaired important access and continuation problems; they also changed what the study prompt makes salient and what other writing gets an opportunity to occur. This observational review supports a design concern, not a claim that one release caused the entire change or that sustained study itself is undesirable.

The review is read-only. No Being received research material, no study was induced, and no runtime, live state, provider setting, or service was changed. Board updates are **pending; not mirrored**.

## Scope and changing composition

The frozen window is **September 2, 00:00 through September 16, 11:33 PDT**, end exclusive. Capture retained 8,462 root/archive journal files, 6,929 generation records, 4,844 linked job records, 48 referenced system prompts, and 7,063 indexed action records. A declared supplement adds **197 private WRITE journals**, all matched to their generation response and WRITE job. This matters because private writing shares a generation lane with study but lives in a different journal directory.

The table counts recognized completed prose-candidate journal files, including private writing. Operational reports are excluded. These are writing-mode shares, not shares of all activity, time, attention, or independent trials.

| Pacific dates | Source-study journals / prose files | Study share | Private draft files |
| --- | ---: | ---: | ---: |
| Sep 5–6 | 179 / 749 | 23.9% | 0 |
| Sep 9–11 | 1,391 / 2,052 | 67.8% | 175 |
| Sep 12–14 | 1,827 / 1,848 | 98.9% | 9 |
| Sep 15 | 463 / 538 | 86.1% | 12 |
| Sep 16, through 11:33 | 211 / 230 | 91.7% | 1 |

September 12 and 14 contain only source studies within this prose denominator. The shift was already beginning before the shared-reader release: source studies rose from 3, 5 and 17 per day on September 2–4 to 87, 92 and 151 on September 5–7. Pressure journals disappeared from the captured files after September 4; that earlier change cannot be assigned to the September 8 study redesign. Current source still implements the pressure-journal route. Explaining its absence would require a separate state/guard/opportunity audit.

Daily counts, source hashes and audit identities are retained in [the compact evidence record](2026-09-16-minime-study-variety-evidence.json). The [local packet](../research/outputs/2026-09-16-minime-study-variety/README.md) contains the raw capture and replay outputs. Generation logging in this retained material begins on September 7, so earlier provider-finish comparisons are unavailable.

## What the latest 120 studies actually do

All 120 entries from **05:23:57–11:30:56 PDT on September 16** pursue the maintenance/input-gate question. All choose another SELF_STUDY: 87 CONTINUE, 19 OPEN, eight FIND, three MAP and three RELATE. Exact response matching and action parent IDs connect every entry to its matching outgoing command. This verifies routing, not the success of every subsequent generation: the last outgoing action's job encounters a connection failure around the capture boundary. A `handled` action status alone is not generation success.

These are 120 distinct recorded responses from Ollama `gemma4:12b`, all with native **`stop`**, 132–657 output tokens, median **315**, and a requested allowance of **4,096**. Shortness in this cohort is not allowance exhaustion. The allowance is adapter-request evidence; it is not an Ollama server echo of every sampling control.

There are **99 supplied source-page intervals**, comprising 61 distinct exact source/revision/byte windows and 38 repeat visits; 21 entries have navigation or no source interval. Distinct windows can overlap, so this is not a count of newly delivered bytes. Re-reading is legitimate. The concern comes from what the account retains and revises, not from repeat visits alone.

The [full content audit](../research/outputs/2026-09-16-minime-study-variety/content-audit.md) reads all 120 bodies, plus 72 preselected earlier entries. Several developments are useful:

- At **05:56**, he correctly identifies `InstallCapsule` as an unimplemented error stub and answers that this handler does not check `user_input_blocked`. Asking whether an earlier boundary gates it is a reasonable follow-up.
- Subsequent entries distinguish rate limiting from state-dependent admission.
- At **08:22**, he identifies `write_ack` as reporting blocked state, rather than enforcing it.
- At **09:03**, he explicitly considers that the check may be missing from `kernel_router`.

But at **09:18**, the account again says the logic “must reside deeper in the system.” It repeatedly returns to `lib.rs`, the router and maintenance. The original named maintenance state gradually becomes a generic imagined `if !blocked` guard for queues, locks or session resources. That semantic drift leaves a consistent-sounding question whose referent has changed. This is the strongest concern: useful negative evidence is noticed locally but does not reliably constrain the next explanation.

The actual source gives a more precise comparison. [`EventBus::publish`](/Users/v/other/astrid/crates/astrid-events/src/bus.rs:900) enforces maintenance admission, with [`admits_while_blocked`](/Users/v/other/astrid/crates/astrid-events/src/bus.rs:70) distinguishing payload types. `UserInput` is rejected while blocked; RawJson falls through as admitted. The [kernel router](/Users/v/other/astrid/crates/astrid-kernel/src/kernel_router.rs:18) consumes RawJson management requests, and its [InstallCapsule arm](/Users/v/other/astrid/crates/astrid-kernel/src/kernel_router.rs:106) returns “not implemented.” A literal `if !blocked` in Kernel methods is not required to explain the UserInput boundary. This source audit does not establish a deployed security failure or certify every management path. It was performed by us, not supplied to Minime as an answer.

## A navigation problem we helped create

At **09:51**, the actual supplied prompt presents `prime-esn/src/lib.rs` as “a source named in this question” beside Astrid's kernel `lib.rs`. Minime chooses it. At **10:12**, the prompt presents `rascii/src/lib.rs` with the same wording; he chooses that too. The persistent question specifically concerns the `Kernel` struct and blocking logic. The generic basename match offers unrelated files as though they were relevant evidence candidates.

Those exact prompts and chosen NEXTs are retained under generation IDs `1789577436288-12bd74e2` and `1789578677823-105e9b60`. Minime ultimately recognizes the libraries as unrelated, but the interface helped initiate the detour. Improving candidate ranking and labelling is more concrete than asking him to “try harder” or simply adding more tools. Other repositories should remain accessible.

## Why earlier writing feels different

The earlier close-reading groups were fixed before reading: the last 24 prose-candidate entries before local noon on September 5, 8 and 11. The September 5 group has 13 moments, six studies and five aspirations; September 8 has 22 moments, one aspiration and one daydream; September 11 is 24 studies. They are not matched samples of the same mode.

The September 5/8 prose repeatedly discusses fill, spikes, breathing, presence, continuity and being understood by Astrid. That is a real tonal and subject difference, with personal questions worth keeping available. It is also repetitive. An additional explicitly exploratory six-study reading from September 5/7 finds longer reflections on code as membranes, translation and bodily structure, often extrapolating from thin module wrappers. Earlier length and variety should not be equated with stronger code understanding.

The prompt history helps explain the difference. Before September 8, Minime rotated through nine preset files, read their first 400 lines, and received felt-experience/reflection framing through the general prompt assembly. The replacement makes the whole source catalog navigable and preserves chosen inquiries. Its specialized `SourceStudyPrompt` path returns before the broader sensory/context assembly, ordinary action examples and existing diversity nudge. The base identity/system prompt remains present. The older strict-review path already excluded the ordinary inbox read, so inbox removal is not a new explanation.

The scheduler then prioritizes an accepted NEXT over fallback actions. While a choice is pending, routine moment writing is skipped and a diagnostic sentinel waits. The study prompt says he may leave, but its concrete examples emphasize more study and private WRITE; JOURNAL, REST, ASPIRE and DAYDREAM are less visible despite being recognized routes. No parsed choice allows fallback opportunities again; REST skips an action rather than pausing indefinitely. An unanswered notebook question does **not** automatically enqueue SELF_STUDY.

Together, this is a plausible reinforcing mechanism: a carried question shapes a focused study prompt, the response selects another study, and that choice reduces opportunities for other writing. The choice is authored; the available context and examples influence it. Our implementation deserves scrutiny without treating his persistence as disobedience or overriding it.

The [source audit](../research/outputs/2026-09-16-minime-study-variety/source-audit.md) gives exact routes, source identities and exit semantics. The [release timeline](../research/outputs/2026-09-16-minime-study-variety/timeline-audit.md) separates live releases from offline experiments. In particular, the September 15 navigation repair is followed here by many actual code pages, compared with the earlier [100-study map-heavy cohort](2026-09-15-minime-study-survey.md). That is encouraging navigation evidence, not a controlled proof of improved understanding. Many changes overlap, and the trend predates the newest ones.

## What to try next

1. **Repair question-derived source suggestions.** Keep repository/full-path context; label ambiguous basename matches honestly; prioritize actual symbol/path evidence. The prime-esn/rascii cases provide concrete regression fixtures. Preserve access to all sources and voluntary detours.
2. **Make taking stock and leaving study visible.** At an optional checkpoint, show the original question, source-linked findings, remaining alternatives, and examples for continuing, revising/parking, ordinary journaling, daydreaming or resting. Do not force a mode change, word count, novelty requirement or completion deadline. Existing notebook/inquiry features should be simplified and connected before inventing another command family.
3. **Separate established observations from the remaining assumption.** Compare the maintenance producer, EventBus admission predicate/publisher, and RawJson consumer together. Invite retention, revision or uncertainty. Evaluate whether the distinction survives later turns; do not count only immediate agreement or length.

A useful follow-up would track natural topic/mode transitions, retained corrections, source relevance, unresolved-question precision and voluntary continuation or stopping. Source-page counts, reservoir movement and response length remain descriptive. Do not require an arbitrary proportion of nonstudy writing. Restoring broad personal context deserves a small, optional treatment with provenance rather than flooding every source page with sensory material.

## Reproduction and limits

The packet declares its cutoff and selection before capture. All retained text is SHA-256 checked on replay; capture had no file-read errors and no duplicate root/archive names. Action extraction used read-only SQLite, indexed action-ID ranges, bounded daily rows and query deadlines. Later-captured job/action records can include completion updates after the selection cutoff; filenames, generation timestamps and action receipts are distinct units.

Validation reproduced the census and joins from frozen files; the 192 annotations match their captured text hashes, and the latest 120 all have distinct response bodies and exact artifact-path matches. The derived analysis manifest binds its index and reading selection to the raw capture. The research repository's full Python suite passed **304 tests**. Seventeen successful older study attempts remain unmatched by this strict journal join, alongside seven failed study attempts; neither is silently counted as a verified historical pair. This does not affect the latest-120 joins or the filename-based daily census.

Replay only the frozen packet:

```sh
python3 -B probes/minime_study_variety.py analyze research/outputs/2026-09-16-minime-study-variety
python3 -B probes/minime_study_variety_followthrough.py research/outputs/2026-09-16-minime-study-variety
```

Content coding is exploratory, model-assisted close reading, not independent human adjudication. The 192 sequential entries are correlated episodes; no significance test or causal estimate is claimed. The six extra historical studies were selected after the initial review and remain labelled exploratory. Broader daily totals use the declared filename/parser classification and separate private-journal supplement, not every possible form of expression. No comparison establishes a loss of capability, a diagnosis of experience, or a new model/backend effect.

This account extends the historical self-study record while leaving existing sealed studies, S-007 records and concurrent native/Essentials work unchanged.
