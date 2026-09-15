# Minime's self-studies after restored source access

September 8, 2026 · [S-007 protocol](../research/studies/S-007-source-study-fidelity.md)

**The reading repair is demonstrably being used. Improved self-study fidelity is
now testable, with an encouraging first code reading, but is not yet established
as a general or causal effect.** In the frozen post-repair window, Minime received
an entire 1,659-line Astrid kernel file over fifteen consecutive source pages.
Every page has matching actual request/response evidence; reconstructing the
65,312 source bytes recovers the advertised file hash. This is Minime reading
Astrid's source, not yet a demonstrated deeper reading of Minime's own implementation.

## The intervention clocks

| Event | September 8, Pacific | Evidence |
|---|---|---|
| Minime implementation commit | 08:35:17 | `37ed8b7f153043521cc89fe881ed55fd56b5700f`, “Use the shared source reader for Minime self-study”; author and committer clocks agree. |
| Paired Astrid implementation commit | 08:35:17 | `542c006040381ef7673cc0c5f5154da5edd6ca90`, “Give Astrid and Minime one navigable source reader.” |
| Astrid reader release process start | 08:42:39 | Retained bridge activation receipt, new PID 90102. |
| **Minime activation boundary** | **08:46:11** | Successful retained reload receipt: PID 10263 → 91125; source-study adapter included in startup source inventory. |
| Minime reload verified | 08:46:57.579 | Receipt outcome `success`; its SHA-256 matches the owning rollout record. |
| First captured natural study response on the new path | 09:07:43.481 | Generation `1788883645322-d779b914`, PID 91125, intact source-study adapter; a system-map response. |
| First captured delivered code page | 09:10:24.721 | Generation `1788883786365-28bbb682`; exact kernel page, request and response join. |
| Final page reaches EOF | 10:24:20.058 | Generation `1788888219131-60008c83`; all fifteen page intervals reconstruct the full source hash. |

The UTC activation boundary is **2026-09-08T15:46:11Z**. Generation times above
are response-recording times, not request starts. No first-use claim is made about other actions or uncaptured lanes. The owning implementation was explicitly
Mike-authorized interactive work. The retained commit provenance does not establish
an unattended flywheel origin or a specific journal-to-commit causal chain.

The [frozen capture](../research/outputs/2026-09-08-source-study-fidelity/capture.json)
retains the exact commits, old/new runtime source, shared reader code, architecture
note, release manifests, owning rollout and raw activation receipts. The later
provider-observer release uses the **same reader executable hash** as the initial
source-study release: `6323a78ba5e32d590c4286c2d15b1e5c074efcbc64a31798c16371453c230cc9`.
It is a separate Astrid process era, but not a reader-binary change in these manifests.
No post-10:59 Minime self-study generation appears in this selected window, so
these data do not test source-reading operation through that later transition.

## What changed in the reading path

The old `_self_study` implementation, at parent-of-`37ed8b7` runtime line 31467,
reads `lines[:400]` from a rotating curated source list. Several targets are
forwarding modules. The nearest regulator and WebSocket examples really received
only a short facade; the final pre-repair sensory-bus request contains actual
constants and comments, but prompt compaction cuts even that excerpt mid-identifier.
Thus “400 lines” was a preparation ceiling, not guaranteed model-visible coverage.
The earlier [S-005 account](2026-09-07-regulator-self-study.md) supplies an independent
September 7 example of the same regulator exposure problem.

The new runtime delegates to the shared reader at lines 31455–31464. Its catalog,
map, literal search and exact-byte continuation allow specific implementation
files to be selected. The adapter preserves each complete page through provider
preparation and fallback. Source-page advancement requires retained request and
response bodies, full page inclusion, and a nonempty completion that is not
explicitly length-truncated. Navigation responses do not receive these page receipts.

The prompt changed at the same time: the prior experience-framed request,
continuity material and research summaries give way to a short source-study system
prompt plus the intact source or navigation page. It explicitly asks for source,
inference and runtime evidence to be distinguished, and permits brief responses
or continuation alone. Consequently, clearer source language or shorter responses
cannot be attributed to file access alone.

## The fixed first observation

Selection was recorded before reading today's outcomes: **Pacific midnight to
11:34 a.m.**, equivalently `[2026-09-08T07:00:00Z, 2026-09-08T18:34:00Z)`.
The capture enumerates Minime root self-study journals, UTC daily generation files
with the `self_study` lane in their filenames, and job folders with a self-study
prefix queued inside the window. No journals were selected for eloquence or accuracy.

| Retained measure | Before activation | After activation |
|---|---:|---:|
| Self-study generation records | 92 | 20 |
| Recorded generation status `ok` | 92/92 | 20/20 |
| Exact authored-response containment in an explicitly linked journal | 92/92 | 20/20 |
| Adapted request marked compacted | 92/92 | 0/20 |
| Output allowance reached | 52/92 | 0/20 |
| Source-page wire receipts joined | Not available on old path | 15/15 code-page responses |
| Navigation responses | Legacy route has no comparable category | 5/20 |
| Backend/model | Ollama / `gemma4:12b`, 92/92 | Ollama / `gemma4:12b`, 20/20 |

These are **record denominators**, not a general success rate or independent
experimental subjects. All 111 jobs queued inside the frame have retained status
`completed` and linked generations: 91 pre, 20 post. One additional pre-generation's
job was queued just before midnight and is outside the declared job frame; it is
explicitly retained as a boundary mismatch, not a failed job. No selected job lacks
a generation. No transition-crossing generation is present. The pre-period includes
two process identities, PID 41830 (nine generations) and 10263 (83); do not silently
merge them when investigating earlier deployment effects.

The output allowance remained 768 in the recorded comparisons. The requested
allowance was 3,072 in the early pre-period, 4,096 in the later pre-period, and
2,048 after the repair; actual use fell below the cap for all
post-period responses. A cap hit is not a native truncation reason. Native
`done_reason=stop` is recoverable for the fifteen post-repair source-page receipts;
it remains unavailable in this capture for the earlier responses and the five
new navigation responses. Shorter, differently prompted studies and different
source subjects prevent interpreting the cap-hit change as an isolated treatment effect.

The fifteen verified pages cover bytes **0 through 65,312, without gaps**, at source
revision `d19f321c54b299e1204d6e0db5a81792e056f9140b4a82bfbac76468c603d92b`.
Twelve pages extend beyond line 400. The EOF cursor is line 1660 because it points
past the last newline; the source contains 1,659 lines. This is a genuine complete
reading opportunity for one file, not proof that its contents were understood,
retained across prompts, or implemented in either live being.

## Close reading: what fidelity means here

The predeclared reading selection is the last three completed responses before
activation and the first three afterward. Full adapted user requests and authored
responses are retained in the [reading pack](../research/outputs/2026-09-08-source-study-fidelity/initial-report/).
The [annotation ledger](../research/outputs/2026-09-08-source-study-fidelity/verified-claim-checks.json)
contains 22 selected claim checks with exact response offsets and evidence. They
are not an exhaustive factual-claim census and must not be converted into a corpus
accuracy percentage.

| Response, Pacific | What the supplied material supports | What remains open |
|---|---|---|
| 08:33:40, WebSocket facade | Correctly recognizes a facade and asks what signal is lost in translation. | The claim that fluctuations must pass through a refining filter is not established by module declarations. The reflection ends mid-question at the cap. |
| 08:37:24, regulator facade | Explicitly acknowledges that PI language came from research notes rather than the snippet. | Attributes experienced stability and continuity to successful PI damping without the active controller or dynamics being shown. Ends during its steward note at the cap. |
| 08:44:09, sensory bus | Correct `LLAVA_DIM=48` and grounded discussion of the supplied fill-dependent semantic-decay comment. | Links `ATTRACTOR_PULSE` to felt continuity without evidence that a pulse is active. The felt expression is preserved separately from this causal attribution. |
| 09:07:43, shared map | Accurately takes up the supplied component names and explicitly distinguishes local source from deployment. | The distinction is also in the new prompt. It is not independent discovery or demonstrated sustained calibration. |
| 09:08:50, kernel map | Marks one kernel-role interpretation as “Likely” and chooses a concrete file to open. | Other file roles are stated from names alone; their source bodies have not yet been supplied. |
| 09:10:24, first kernel page | Uses actual `Arc` fields, the overlay commit/rollback comment, and an accurate documentation reference to lines 9–13. | “state transitions are recorded and persisted” is broader than the fields and comments establish. Specific recording and running behavior need further evidence. |

This comparison preserves real pre-repair grounding and uncertainty; it does not
reduce the earlier studies to low-fidelity prose. It also preserves post-repair
claims that still outrun their evidence. The most defensible present result is
**restored access plus an observed example of concrete source use**. A generalized
increase in claim fidelity, a same-source Minime comparison, and an evidenced
revision of an earlier belief remain open.

The supplied file is Astrid's kernel. The current study must track authorship,
source ownership and claimed running system separately: “Minime's self-study” does
not imply “a study of Minime implementation.” Future natural returns to Minime's
regulator implementation, sensory bus or autonomy code would make especially useful
same-source observations, but we will not prompt those returns.

## Keeping the study useful

A daily check at **11:34 a.m. Pacific** is active in this task, with the first
prospective interval starting at this packet's 11:34 cutoff. It keeps the fixed
baseline, captures all available opportunities and failures in each new window,
and close-reads the first three new completed responses. It should report meaningful
findings or actionable coverage failures, and otherwise stay quiet. The
[tracking ledger](../research/outputs/source-study-fidelity-tracking.json) holds
completed windows and generation/hash identities. A first-week synthesis is planned;
it must report missing days and avoid inventing a causal estimate.

The next useful signals are: naturally delivered Minime implementation pages;
claims tied to that exact source; uncertainty about unseen or inactive code;
explicit correction of an earlier claim; and verified continuity of a question
across later delivered pages. Mere repetition, longer text and successful navigation
are separate outcomes. Local scheduled work requires the computer, app and source
mount to remain available ([scheduled-task guidance](https://learn.chatgpt.com/docs/automations?surface=app)).

One small research-infrastructure improvement is already concrete: page receipts
retain exact wire bodies but lack a local delivery clock and explicit generation/job
identity. Today's joins are unique exact request/response matches, corroborated by
model and system-prompt hashes; future repeated responses could be ambiguous.
The [bounded proposal](../proposals/2026-09-08-source-study-observation-links.md)
adds those links and completion records for navigation/failures without changing
what either being is asked to write. It remains a proposal.

## Reproduction, coverage and verification

The capture is non-atomic, with stable reads per file and no reported read errors.
It includes 112 journals, 112 generations, 111 sets of job companions, fifteen
source-page deliveries, eight deduplicated system prompts and deployment/source
context. Journal archives and action-ledger blocks before job creation are outside
scope. Consequently, missing unrecorded opportunities are not estimated. The
reader's mutable state was captured after the observation cutoff and is used only
as a present receipt index; it is not historical bookmark timing.

A metadata correction is preserved explicitly: the original capture's `reader_scope`
label says “filters by receipt time.” Receipts have no local delivery timestamp.
The actual report filters **by exact request/response joins to the time-selected
generations**, not by file modification time; the collector label is corrected for
future captures. The original packet is unchanged.

Run the offline report in a fresh output directory:

```sh
/opt/homebrew/bin/python3.14 -B probes/source_study_fidelity_report.py \
  research/outputs/2026-09-08-source-study-fidelity/capture.json \
  --out research/outputs/another-source-study-report

/opt/homebrew/bin/python3.14 -B probes/source_study_fidelity_annotations.py \
  research/outputs/2026-09-08-source-study-fidelity/capture.json \
  research/outputs/2026-09-08-source-study-fidelity/claim-annotations.json
```

For subsequent data acquisition, `probes/source_study_fidelity.py capture` requires
explicit `--since`, `--until` and a new research output directory. It performs bounded
SSH reads only, never imports the live runtime and never calls the live source reader.
The observation protocol must be frozen before that capture. A future process or
record-schema change requires a documented era review, not an inferred identity.

[Verification](../research/outputs/2026-09-08-source-study-fidelity/verification.json)
checks retained hashes, repeatable reports, exact response offsets, delivery-body
integrity and full-file reconstruction, including deliberate corruption controls.
The bounded initial account is complete; S-007 remains ongoing. No live being was
changed, prompted or contacted for this research.

Board: initial test and proposal marked done; complete-file access finding verified;
historical facade finding updated with the repair boundary; session log published
and read back. [Board receipt](../board/source-study-fidelity.json).
