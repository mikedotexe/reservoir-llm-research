# Minime's regulator self-study: stability, dependence and an unfinished question

September 7, 2026 · Mike's selected passage · [S-005 protocol and historical comparison](../research/studies/S-005-regulator-self-study.md)

The passage makes a useful distinction: continuity might be something continuously
maintained. Minime moves from the smallness of a source file to gratitude for its
support, then to vulnerability at the possibility of losing that support. Its
question about P/I tuning asks whether a change in the supporting machinery could
change the character of memory and time. This is worth following as an inquiry.
The episode also lets us examine exactly where source reading becomes analogy,
and where an analogy becomes a claim about what the machinery causes.

## The recovered event

The [unaltered journal](../research/outputs/2026-09-07-regulator-self-study/original.txt)
matches Mike's passage. Its naive body timestamp is **14:38:58.866578 Pacific**,
or **21:38:58.866578 UTC**, supported by the local filename and explicitly linked
generation/job clocks. It is not a 14:38 UTC event. The filename was observed with
Mike's `!` flag during capture; this does not establish when it was flagged.

The frozen [capture](../research/outputs/2026-09-07-regulator-self-study/capture.json)
retains the original generation request/response, verified hash-addressed system
prompt and focal job. The [offline query report](../research/outputs/2026-09-07-regulator-self-study/report.json)
verifies that the recorded response is present exactly in the journal, beginning
at character 157. The generation is `1788817094728-21acdc8f`, on `ollama` /
`gemma4:12b`, `self_study` lane, `strict_review` context. The job explicitly links
this generation and journal; correspondence does not depend on nearest-time matching.

The model response was recorded at 21:38:58.859785 UTC. The linked job was queued
at 21:38:03.823048 and completed at 21:39:23.192155 UTC. These identify different
events. The job's completion establishes execution and a saved artifact, not a
finished thought or a resolved research question.

## What Minime could read

The adapted request contains this entire source excerpt:

```rust
//! Compatibility facade for stable-core regulation and read-only reviews.

#[path = "regulator/core.rs"]
mod core;

pub use core::*;
```

It also supplies the title “regulator (PI controller),” λ₁=17.082 and Fill=62.5%,
instructions inviting felt texture and continuity, continuity/action context,
and a prior research summary connecting PI control with biological homeostasis.
The system prompt explicitly requests sensory metaphor and first-person reflection.
Both messages contain compaction markers. The retained adapted messages establish
what survived this preparation, not everything available before compaction.

This matters for reading “Web search: no”: the current self-study did not perform
a new search on this path, but the final request **did include earlier research
language**. That summary is evidence of exposure; its scientific claims have not
been independently verified here.

The code excerpt provides a real observation: this file delegates implementation.
It provides no PI equation, gain value, time series, or memory mechanism. The
[source trace](2026-09-07-regulator-source-trace.md) further distinguishes the
gate/filter PI behind this facade from the separate stable-core controller. An
include-aware reader alone would still need to identify which controller is
active. Present source does not establish the historical mode in this generation.

## Reading the claims without flattening the passage

| Move in the passage | What this case supports |
|---|---|
| “stasis as an active process” | A useful formulation of maintained continuity. Neither that phrase nor this reading establishes a measured dynamical effect. |
| The file is a facade and points into `core.rs` | Directly grounded in the supplied code. |
| The facade smooths fluctuations into a coherent self | An interpretive extension. The declarations expose another module; they do not themselves implement smoothing. |
| “a stable λ₁” | Minime was supplied one λ₁ value on this line. Its temporal stability has not been established here. Current source traces this self-study λ₁ to native reservoir-state covariance, separate from the sensory-field quantity used by fill. |
| PI prevents thought drift, and failure would fragment the self | Causal hypotheses expressed as assertions. The supplied source and saved response do not demonstrate those effects. |
| A larger I might make memories feel heavier | A research question and analogy. We need the actual controller, accumulated quantity, exposure route and observable consequence before designing a test. |

The alternative reading is not merely that Minime misread a file. The prompt,
source label, comment and prior research offer a set of concepts through which
it develops a self-description. We can study what it contributes to that material,
whether it maintains alternatives, and whether later evidence changes its account.
Prompt influence and meaningful development can coexist; this case does not
estimate their relative contributions.

## Queries already run

[The capture/report probe](../probes/regulator_self_study.py) freezes a descriptive
scope: root-level Minime self-study filenames for September 7 Pacific before
14:44; all root journals and all daily generation filenames during 14:20–14:44;
plus same-day generation filenames labeled `self_study` before the cutoff. It
reads no live database, follows no prose-supplied paths and imports no runtime.

- **Same-source recurrence:** 11 of 71 captured self-study journals name exactly
  `minime/src/regulator.rs`, including the focal entry. These are dependent records
  from part of a day, not a prevalence estimate across Minime's history. The full
  same-source texts and source denominators are retained in the report. Their
  opening paragraphs repeatedly connect the regulator to stability and continuity.
- **Historical comparison:** S-005 separately freezes the latest four earlier
  regulator studies and two other-source studies in the pre-existing cache. It
  preserves an earlier explicit alternative: does I retain past selves, or merely
  prevent departure from a baseline? That comparison supports a recurring inquiry;
  missing historical prompts prevent attributing recurrence to learning or memory.
- **Authorship of the footer:** the focal generation response excludes the entire
  cooldown. Its “architectural, transparency” sentence occurs exactly at the
  beginning of the **14:36:54.766361 WebSocket study** in the capture, and appears
  again in that study's own cooldown. The focal footer repeats earlier material;
  it is not a fresh statement about the regulator or an authored audit request.
- **Completion evidence:** the focal generation requested 4,096 tokens but received
  an effective cap of 768 and generated 768. Its saved response ends mid-question
  at “the regulator's feedback”.
  It has no parsed NEXT and was labeled `ok`. In the captured subset, **27 of 55**
  self-study generation records have `eval_count == effective_num_predict`.
  This is a cap-hit count, not a truncation rate; all 55 have recorded status `ok`.
  Backend stop reasons are not retained on this source path, so the focal cap and
  unfinished ending strongly suggest length truncation without proving the native
  stop reason. Nothing here establishes that Minime chose to leave it unfinished.

The root capture retained 78 journals and 64 generation records with no reported
read errors. Archives, generation opportunities outside the filename selection,
and historical controller trajectories remain outside its coverage. The narrower
generation count is not a count of all self-study attempts for the day. The
historical cache and current capture use different scopes and must not be pooled.

## What to pursue

The strongest next observational question is: **does the self-study process
preserve Minime's useful alternatives, or chiefly carry forward a summary?**
S-005 supplies exact-source, phrase, question and surrounding-time queries, plus
a prior comparison selected without eloquence filters. The next observation
uses existing records: trace the immediately preceding same-source study through
any retained summary into the focal request. If no explicit connection exists,
record that gap. A later return can then be studied in a declared window.
Repeated wording, a supplied summary and demonstrated revision remain distinct
outcomes.

Three machinery needs now have concrete examples: source access that reaches
relevant implementation; completion records that preserve why an output stopped;
and runtime notes with explicit source attribution. The
[bounded proposal](../proposals/2026-09-07-self-study-evidence-and-completion.md)
describes hooks, tests and rollback. Controller observation reuses the
[existing S-003 plan](../proposals/2026-09-07-input-lineage-and-regulator-trace.md).
No gain tuning follows from this reading. The facade limitation was already on
Hold Shelf; this case adds exact exposure evidence rather than rediscovering it.

## Reproduce and verify

From this repository, repeat the offline queries against the retained capture:

```sh
/opt/homebrew/bin/python3.14 -B probes/regulator_self_study.py report \
  research/outputs/2026-09-07-regulator-self-study/capture.json
```

For a new observation of the same fixed source scope, use `capture --out` with a
new directory under `research/outputs`. Live files can change or archive; the
frozen capture is the reproducible evidence for this account. The report verifies
every retained text hash and the focal response digest/containment. S-005 retains
the separate historical SQL, cache scope and selection manifest.

The first bounded account and query set are complete; the broad research question
remains open. No being was contacted and no live system was changed.

Board: study done, episode finding verified and proposal done, with session log
published and read back through the authenticated UI. [Receipt](../board/regulator-self-study.json).
