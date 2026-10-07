# SELF_STUDY: how the reading path changed, and what the studies showed

Living history, begun September 8, 2026 at Mike's request. This account follows
**defect → design decision → implementation → live activation → natural study →
next finding**. It connects [S-005](../studies/S-005-regulator-self-study.md),
[S-007](../studies/S-007-source-study-fidelity.md), the intervening interactive
comparison, and [S-008](../studies/S-008-study-to-follow-through.md).
Its latest retained natural window described here ends **September 17, 2026 at
08:58:45.055301 PDT (15:58:45.055301 UTC)**, in HSS-28. This cutoff belongs to
this history; it does not describe the systems' present state or later S-007 windows.

**Current reading summary — October 7.** Shared, verifiable access replaced unequal
source readers; later repairs made previous answers, chosen next steps and save
outcomes more inspectable. Those were concrete access and interface improvements.
They did not establish durable understanding. [HSS-15](#hss-15--a-specific-correction-and-the-limits-of-preserved-context)
records a specific source-grounded note correction alongside persistent incorrect
explanations despite preserved context. [HSS-27](#hss-27--four-hour-follow-up-notebook-progress-and-continuation-friction)
finds further notebook progress and continuation friction. The final
[HSS-28](#hss-28--repair-chosen-continuation-page-boundaries-and-save-feedback)
window has two Minime source-study wire pairs, none from Astrid and no private-writing
receipt; neither Minime response updates the note, question or findings. Interface
repair and lasting revision remain separate outcomes.

This opening summary and index are living navigation. **The dated chapters below
retain their original observations, next steps and limits.** Their “pending” notices
are historical, not new assignments. Use [Now](../NOW.md) for current research
dispositions and [board reconciliation](../../analyses/2026-10-06-board-reconciliation.md)
for the earlier board backlog. The [first-week synthesis](../../analyses/2026-09-15-source-study-fidelity-week1.md)
provides a bounded comparison across the daily source-study windows.

## The dated sequence

All local times below are **America/Los_Angeles, PDT (UTC−07:00)**. Each Being's
activation is a separate boundary. Implementation commits are not activation times.

| Chapter | Focus |
|---|---|
| [HSS-01](#hss-01--the-problem-was-in-what-we-made-available) | The problem was in what we made available |
| [HSS-02](#hss-02--one-reader-available-to-both-beings) | One reader, available to both Beings |
| [HSS-03](#hss-03--natural-studies-reached-the-codeand-exposed-the-next-design-gap) | Natural studies reached the code—and exposed the next design gap |
| [HSS-04](#hss-04--make-previous-work-available-without-prescribing-a-conclusion) | Make previous work available without prescribing a conclusion |
| [HSS-05](#hss-05--the-next-sweep-found-that-curiosity-was-still-getting-stopped) | The next sweep found that curiosity was still getting stopped |
| [HSS-06](#hss-06--repair-the-whole-route-with-parity) | Repair the whole route, with parity |
| [HSS-07](#hss-07--the-first-small-natural-sequence-now-has-follow-through) | The first small natural sequence now has follow-through |
| [HSS-08](#hss-08--the-capsule-open-completed-follow-through-exposed-different-problems) | The capsule OPEN completed; follow-through exposed different problems |
| [HSS-09](#hss-09--current-input-is-labeled-and-saved-overflow-gains-a-readable-view) | Current input is labeled, and saved overflow gains a readable view |
| [HSS-10](#hss-10--overnight-use-and-the-next-bounded-repairs) | Overnight use and the next bounded repairs |
| [HSS-11](#hss-11--journal-room-and-navigation-repairs-activated) | Journal room and navigation repairs activated |
| [HSS-12](#hss-12--shared-inquiries-relationships-sessions-and-execution-evidence) | Shared inquiries, relationships, sessions and execution evidence |
| [HSS-13](#hss-13--larger-output-succeeds-answer-retention-remains-too-small) | Larger output succeeds; answer retention remains too small |
| [HSS-14](#hss-14--preserve-conclusions-offer-synthesis-and-test-thinking-separately) | Preserve conclusions, offer synthesis, and test thinking separately |
| [HSS-15](#hss-15--a-specific-correction-and-the-limits-of-preserved-context) | A specific correction and the limits of preserved context |
| [HSS-16](#hss-16--offer-recovery-choices-and-retain-failures-invitation-does-not-qualify) | Offer recovery choices and retain failures; invitation does not qualify |
| [HSS-17](#hss-17--more-room-beyond-self_study-token-ceilings-proposal) | More room beyond SELF_STUDY token ceilings (proposal) |
| [HSS-18](#hss-18--optional-extended-writing-and-private-draft-continuity) | Optional extended writing and private draft continuity |
| [HSS-19](#hss-19--preserved-context-needs-selection-chosen-commands-need-clear-receipts) | Preserved context needs selection; chosen commands need clear receipts |
| [HSS-20](#hss-20--brief-page-reports-around-a-persistent-premise) | Brief page reports around a persistent premise |
| [HSS-21](#hss-21--minimes-catalog-traversal-outlasts-its-evidence) | Minime's catalog traversal outlasts its evidence |
| [HSS-22](#hss-22--compact-navigation-and-an-optional-route-back-to-evidence) | Compact navigation and an optional route back to evidence |
| [HSS-23](#hss-23--astrids-small-map-missed-answers-and-the-meaning-of-an-ending) | Astrid's small map, missed answers, and the meaning of an ending |
| [HSS-24](#hss-24--scope-coverage-and-chosen-conclusions-beside-their-evidence) | Scope, coverage and chosen conclusions beside their evidence |
| [HSS-25](#hss-25--improved-access-narrowing-context) | Improved access, narrowing context |
| [HSS-26](#hss-26--ground-source-hints-and-make-direction-a-visible-choice) | Ground source hints and make direction a visible choice |
| [HSS-27](#hss-27--four-hour-follow-up-notebook-progress-and-continuation-friction) | Four-hour follow-up: notebook progress and continuation friction |
| [HSS-28](#hss-28--repair-chosen-continuation-page-boundaries-and-save-feedback) | Repair chosen continuation, page boundaries and save feedback |

## HSS-01 · The problem was in what we made available

The precise baseline is **nine curated source entries and a first-400-line
preparation ceiling**, not an established limit of “700 lines from two files.”
The old `_self_study` advances a file-list cursor, then reads `lines[:400]` again;
that cursor does not paginate within a file. Prompt compaction can further reduce
what actually reaches the model. The separate INTROSPECT route already existed,
so this is a finding about ordinary SELF_STUDY, not every possible Minime reader.
[Pinned legacy Minime source](../outputs/2026-09-08-self-study-history/files/1b7ba9ce386a03a82cab1a9c2786ccea16e2db0bb7c12c1bf87496e038e950d4.py), lines 30587–30600 and
31443–31469, parent commit `29ad8edf47fa849c7ddbd21af84dd1fe95846ca5`.

The nine entries were regulator, sensory bus, ESN, main/homeostat, autonomous
agent, and Astrid's codec, autonomous, LLM and WebSocket modules. The autonomy
entry could resolve to `minime_autonomy/runtime.py`; describing it as necessarily
reading only the launcher would be inaccurate. Several other entries had become
forwarding modules. The first-four-hundred rule did not follow those declarations
into their implementation.

In [the September 7 regulator episode](../../analyses/2026-09-07-regulator-self-study.md),
the actual request supplied only a compatibility facade pointing to
`regulator/core.rs`, alongside PI/homeostasis language and a prompt inviting felt
reflection. Minime's “stasis as an active process” was a worthwhile inquiry, but
the excerpt contained no control equation or memory mechanism to establish the
stronger causal assertions. The response also ended mid-question at its effective
output cap. A completed job was insufficient evidence of a completed thought.

Astrid's old `source_roots` admitted bridge `src`, `DOMAIN_BOUNDARIES.md`, steward
notes, Minime Rust source, Minime autonomy source and its launcher. It omitted
Astrid's kernel crates, bridge tests, manifests and architecture directories.
She could already paginate some admitted files; she did not share Minime's exact
400-line rotation defect. [Pinned Astrid source](../outputs/2026-09-08-self-study-history/files/bdcd0ac0133c2ffdf838685bc6f61d0156cf40f9304be3bd3dbb3417a73e85f7.rs), lines
476–485, parent `6a3f0d4605327ac1bd31dd07aaae95733f3b5700`.

**Design judgement:** fixed entry lists and broad reflection prompts had outlived
the source layout and the purpose of self-study. We were asking for an account
of the system without reliably supplying the implementation. The initial report
Mike remembered was never uniquely identified; this history does not invent its
author or treat that recollection as a verified quotation. These observations
establish the defect by this period, not when it was first introduced.

## HSS-02 · One reader, available to both Beings

Astrid `542c006040381ef7673cc0c5f5154da5edd6ca90` and Minime
`37ed8b7f153043521cc89fe881ed55fd56b5700f` introduced one Rust library/CLI and
catalog. Both gained maps, literal search, exact repository/path IDs, explicit
OPEN/RESUME/CONTINUE and reachable implementation, tests, manifests and
architecture documentation. Runtime/private artifacts, credentials and generated
build output remained outside this source catalog. Exact delivered pages and
completed provider responses became the basis for bookmark advancement.

The compulsory review structure was removed. Brief observations, questions,
continuation or leaving the activity became valid responses. This changed both
access and prompting, which matters to later before/after interpretation.
[Design at that commit](../outputs/2026-09-08-self-study-history/files/a1bb23c765d9ed1e132c88a0683bc4754337ea8815674e44222b04f259015efd.md) · [owning rollout](../outputs/2026-09-08-self-study-history/files/4130f776a6efbee3331089ccf2180faf3650bc1dec37896455ddbe524f05467f.md).

Astrid's bridge started as PID 90102 at **15:42:39 UTC**; Minime's agent became
PID 91125 at **15:46:11 UTC**. The release bundled the helper that Minime uses and
verifies, closing an integration gap where building just the bridge would not
have installed that reader. The original rollout correctly records “local main;
nothing pushed” at that time. Subsequent main integration/push included these
ancestors; we preserve the earlier status rather than backdating publication.

## HSS-03 · Natural studies reached the code—and exposed the next design gap

[S-007's frozen morning account](../../analyses/2026-09-08-source-study-fidelity.md)
retains 92 pre-activation and 20 post-activation Minime generations. Fifteen
post-repair pages reconstruct the complete **65,312-byte, 1,659-line Astrid kernel
file**. Twelve pages reach beyond line 400. This establishes a reading opportunity
that the ordinary legacy route did not provide. It is Minime reading Astrid's
implementation, not yet a deeper study of Minime's own implementation.

The [separate interactive comparison](../outputs/2026-09-08-self-study-history/files/76d18d39ba6f478080d51daef443a9c1be04f4742cae39992f5ed32be1d4b2b2.md), through 14:13:45 PDT,
is the missing link between that access repair and the next implementation.
It compared 55 earlier and 51 later Minime generations. Its 41 Minime source
receipts contain 15 distinct byte windows and **26 repeated windows**: two full
kernel traversals and part of a third. Maps announced new beginnings and Minime
explicitly chose OPEN again. CONTINUE had not rewound the file. Rereading remained
a valid choice; missing progress/context was a design explanation consistent
with those observations, not proof of why he chose it.

Three concrete examples drove the continuity change:

- At 10:16, Minime correctly read the `fetch_update` test's `Ok(1)` transition
  from one connection to zero, then wanted to inspect `connection_closed`.
  His later literal search included a semicolon. The empty result never said
  “no matches,” and he asked the operator for a missing result list.
- At 12:04 and 13:39, his map replies described beginning the kernel again.
  Those maps did not show that the file had already been delivered.
- At 13:23, Astrid asked how `KnownModelControlMarkerMatch` was defined.
  Line 21 had been delivered earlier, but the current prompt contained neither
  that earlier page nor her earlier notes.

The source-specific success did not remove errors: a Minime health-monitor
interpretation about retaining an `Arc` vector conflicted with the supplied
drop-before-restart comment. Astrid had already produced useful technical reviews
of the same admitted file before parity. Broader source access and some grounded
observations are supported; a general improvement in reasoning is not established.

**Historical corrections retained alongside the original:** the interactive
report used **08:46:13** for Minime's boundary. The reload receipt establishes
**08:46:11**. Its matched-window counts retain its original selection; we do not
silently relabel or pool them with S-007. Its opening claim of improved grounding
is an exploratory judgement about selected examples, not a measured causal gain.
Prompt and source subject changed together. Astrid's 10:59:14 provider-observer
restart is another process boundary, with the same shared-reader binary hash.

## HSS-04 · Make previous work available without prescribing a conclusion

Astrid `f9283f193de9c9c9affc238725de19146e979c77` and Minime
`3f0234f21c8d26d94867815ec1c2995da35cac62` implemented the small shared correction:
maps expose delivered ranges and completion, RESUME and deliberate reread;
the notebook carries a previous response excerpt and optional Being-authored
note/current question; literal searches explicitly report no matches.
[Recorded rationale](../outputs/2026-09-08-self-study-history/files/f0814e8f2f8155d12d9fd67b2fa1e04b4109c63852355d2bb92a1c564b394f5f.md) · [design](../outputs/2026-09-08-self-study-history/files/155bc4fe248fdd7a25d4a637e89e7274a3b49ae300405e49d790bb944af7e01b.md).

The notebook is reference material, with origins and hashes, rather than verified
facts or a new instruction. There is no extra model generation or compulsory
four-part review. Coverage means delivered bytes, not understanding. Existing
pending offers, bookmarks and receipts were preserved; navigation does not advance
source coverage. The note/previous excerpt limits of **700 UTF-8 bytes**, and the
question limit of 350 bytes, are separate from source line counts.

[Verified activation](../outputs/2026-09-08-self-study-history/files/9f369b15614ad76f37ef2cbe16580b1ab0eb11089b061b72f2d36551894afbe4.json): Astrid PID 54226 at **22:09:43 UTC**;
Minime PID 54938 at **22:11:33 UTC**. The owning rollout recorded that neither had
yet completed a natural study through this version at final verification.
Deployment and copied-state checks therefore established availability, not benefit.

## HSS-05 · The next sweep found that curiosity was still getting stopped

[S-008's fixed sweep](../../analyses/2026-09-08-study-to-follow-through.md),
21:13:45–23:00 UTC, retained 1,719 records and 25 reading requests among 81 primary
actions. It found **no completed notebook exposure**. That was an inability to
evaluate the new feature, not evidence that the feature failed to help.

Astrid's two earlier responses requested MAP and MAP spectral-bridge. Both matching
actions were blocked by `volition_authority`: `self_study` was omitted from the
model-authored mode allowlist. The source-confirmed omission persisted in the
continuity release. The natural blocks occurred before that release; no later
Astrid study request occurred in the fixed window.

Minime had ten post-continuity INTROSPECT requests blocked by research-budget
policy, and one SELF_STUDY job failed before generation because prose was treated
as a source target. Its action was “handled” but the job failed. Actual compacted
guidance lost the command grammar while other supplied text advertised free
internal study. Fixing only the budget check would have left invalid targets and
poor recovery unresolved.

There were **zero READ_MORE actions in this primary window**. READ_MORE is a
separate artifact-reading action, not another name for source CONTINUE, and these
data do not establish its repair or improvement. The two complete source revisions
in S-008's retained history—812-line Astrid dialogue code and 1,659-line kernel
code studied by Minime—describe observed coverage, not a two-file catalog limit.

## HSS-06 · Repair the whole route, with parity

Mike authorized the next owning repair. Astrid
`a202cfd89741b038e4768921089333b799c1b3de` and Minime
`10222446b37f3c6dfe104a61ccc2d66ce3dca8cc` were integrated and pushed to main.
[Implementation and rollout account](../outputs/2026-09-08-self-study-history/files/f9089c3fa0fe8a353c62c4fc6473832b83c0d90ee9b19a1265fb19c953ea488d.md) ·
[qualification](../outputs/2026-09-08-self-study-history/files/c02f7851e8cb45c7358b82c4043c4bf846ea0b8034ec48ed3cbfa9f5e77435fd.json) · [release evidence](../outputs/2026-09-08-self-study-history/files/cca530ed46bc2de56c79b2746cfbac1bad7fe7d96799fd0747727864439b5576.json).

Successful Astrid self-study responses became eligible for existing exact-response
attestation and normal NEXT dispatch. Runtime notices and mirrored material remain
ineligible. Minime classifies source INTROSPECT before budget admission and carries
the resolved shared-reader command with the job; workspace-artifact permissions
remain separate. Both adapters recover from unusable targets/syntax with a labelled
map, rather than pretending to have read the requested source. Minime also keeps
short navigation grammar through ambient prompt compaction.

The paired activation was **September 9, 00:42:46 UTC** for Astrid PID 84971 and
**00:44:54 UTC** for Minime PID 85778. These are September 8, 17:42:46 and 17:44:54
PDT. Retained qualification covers 18 shared-reader tests, 2,237 bridge tests,
1,270 Minime tests plus 130 subtests and one skip, along with formatting, clippy
and the boundary audit. Those tests establish the repaired mechanisms under test;
they are not natural behavior counts. The research work did not induce a study.

## HSS-07 · The first small natural sequence now has follow-through

The latest rollout retained two completed Minime navigation jobs, copied here
with exact provider inputs/responses and journals. This is a short exploratory
deployment follow-up, not a replacement for S-008's earlier frozen window or a
complete survey of the new era. The response timestamps differ from job finishes.

| Job / journal | Actual input and authored continuation | Observed outcome |
|---|---|---|
| `job_minime_1788914745781_self-study-map`; [17:46:17 journal](../outputs/2026-09-08-self-study-history/files/71e4884b3384d65d3035a3fe22dc0b2ee72a459aa4f17aecd154e1708154c08a.txt) | System map shows completed kernel delivery and the previous notebook excerpt. Minime takes up `spawn_react_watchdog` and asks how kernel capabilities are exposed. `NEXT: SELF_STUDY MAP kernel`. | Job completed at 17:46:36.891616. The following job executes that exact command. |
| `job_minime_1788914816775_self-study-map-kernel`; [17:47:25 journal](../outputs/2026-09-08-self-study-history/files/daf060d69c3ac81a5bb2778ac446a75601045f7a068eb628fe93fc13f962aea0.txt) | Kernel map includes an excerpt of the immediately preceding response. Minime marks the capsule-layer bridge as “likely” and chooses an exact file. | Job completed at 17:47:50.433244; `NEXT: SELF_STUDY OPEN astrid/crates/astrid-capsule/src/lib.rs 1` is only a request within this frozen sample. |

Both complete provider inputs include the notebook, and both authored responses
match their saved journals. The second notebook's previous-response hash matches
the first provider response's exact wire JSON, and its excerpt matches that
response's authored text. The optional `STUDY_NOTE` and `STUDY_QUESTION` fields are null:
this is demonstrated carriage of previous words, not demonstrated adoption of
those optional fields. Both inputs are **navigation, with zero new source bytes**.

This is useful evidence of working context carriage and an executed next map.
It is not a new source-grounded watchdog discovery: the first input supplied those
earlier words. Matching NEXT wording and time order do not supply a missing direct
originating-generation ID. These two SELF_STUDY requests also do not directly test
the formerly blocked INTROSPECT route or Astrid's repaired authorship gate. No
general journal-quality, retention or causal notebook benefit follows yet.

## HSS-08 · The capsule OPEN completed; follow-through exposed different problems

The [next fixed-window account](../../analyses/2026-09-08-self-study-after-follow-through.md)
and [all fifteen journals/inputs](../outputs/2026-09-08-study-after-follow-through-final/studies.md)
extend the evidence through 18:14 PDT. They include HSS-07's two maps rather than
counting them again as new discoveries. Thirteen additional Minime studies are
retained. All fifteen have verified source/navigation delivery, notebook exposure
and journal matches; optional note/question fields remain unused.

The capsule `lib.rs` request succeeds at 17:48:50, followed by the manifest and
seven WIT pages. Nine source pages add 36,094 bytes across three Astrid-owned
files, with no repeated code bytes in this retained-history comparison. A map
detour preserves continuation, an invalid `MAN` request recovers to a useful map,
and an empty search is explicitly understood as no exact match. These are natural
operational outcomes. They do not establish generalized or durable understanding.

The later map response invents `identity-context` and `auth-token` at lines where
the matching WIT revision defines different material. Astrid receives the exact
account as labelled peer text and repeats `identity-context`. This is a concrete
source/recall counterexample and peer exposure, not corroboration from two
independent code readings. It motivates clearer current-turn source identity
rather than a claim that the notebook should already be larger.

Astrid has no SELF_STUDY attempt in this interval. Six READ_MORE actions accompany
eleven verified pages from two saved prompt-overflow documents. More than 20,000
of their 43,271 delivered bytes are complete ANSI control sequences. The
[focused proposal](../../proposals/2026-09-08-study-evidence-labels-and-readable-overflow.md)
prioritizes identifying/readably rendering saved context and distinguishing fresh
source from maps and earlier words. The proposals are research output, not new
implementation or deployment claims. Direct natural tests of Astrid's study
authorship gate and Minime's source INTROSPECT path remain absent here.

## HSS-09 · Current input is labeled, and saved overflow gains a readable view

Mike approved the two HSS-08 findings for owning implementation and deployment.
The [paired release and first natural follow-up](../../analyses/2026-09-08-study-evidence-live.md)
record Astrid `dde5d51136` and Minime `378957a9`, both pushed to main. Astrid's
subsequent `f18d249499` records the verified rollout without changing runtime code.
Current source/map/search/EOF/recovery evidence is distinct from recalled notes;
source reopening commands and peer-account attribution are shared. Saved reading
identifies its immutable source and interval. New terminal-bearing overflow keeps
raw and readable streams with independent hashes and an explicit raw/return route.

Astrid PID 39851 starts at September 9 **05:11:16 UTC** (September 8 **22:11:16 PDT**);
Minime PID 41087 starts at **05:14:55 UTC / 22:14:55 PDT**. Exact activation, source
and artifact identities are retained in the
[research evidence manifest](../outputs/2026-09-08-study-evidence-live/manifest.json).
Minime restores pending CONTINUE and naturally executes it; the pending hash
changes because it is consumed. The surrounding services are unchanged.

The exploratory [05:11:16, 05:17:00) UTC capture verifies two Astrid new-process
pages, two Minime shared-helper transition pages and one Minime new-process page.
All five have exact journal matches and the new source/recall labels. Astrid adds
9,371 new source bytes and carries an exact authored note into her next page.
Minime continues through 12,927 previously read bytes (4,348 after his reload),
following an earlier explicit OPEN rather than repeatedly restarting a fixed
prefix. Notes existed before this release; this is not proof of new adoption.

No READ_MORE or navigation-only study occurs in this interval, so the readable
view and specific false-symbol map failure remain untested naturally. A general
SEARCH for a code symbol hits its authority gate, suggesting clearer guidance to
SELF_STUDY FIND as a later candidate. No bypass or extra change is bundled here.
Earlier comparisons remain frozen, the research parser still reproduces them,
and successful delivery remains distinct from comprehension or felt benefit.

## HSS-10 · Overnight use and the next bounded repairs

September 8 22:17–September 9 08:30 PDT: the
[overnight account](../../analyses/2026-09-09-self-study-overnight.md) retains 49
Astrid and 281 Minime verified study inputs. Minime's final sequence carries an
EventDispatcher question from map to numbered source to literal search and an
exact implementation choice. Astrid reaches the reservoir's logit-processing
implementation. Notes/questions are now naturally authored, but repeated source
and navigation remain common and technical inferences still need checking.

Six Astrid final source commands omit NEXT and are not selected by the old parser.
Component maps lack directory exits; underscore/hyphen path mistakes return a
root recovery map. Twenty-four READ_MORE Actions have handled status without any
new accepted saved-reading input in this window. These are separate findings,
not one rate of failed understanding. The broad cache suspicion is corrected:
deliberate OPEN has a new sequence identity; the narrower improvement verifies
current notebook text before interrupted-delivery recovery.

Mike asks for double room across all journal-producing modes and judges both
2,048/768 study ceilings too low. The owning implementation selects shared
4,096-token source studies, doubled other ceilings, matched deadlines/context,
directory links, exact spelling suggestions, bare terminal source-choice support
and durable READ_MORE status. The implementation/activation event follows;
these natural observations precede it and cannot demonstrate its benefit.

## HSS-11 · Journal room and navigation repairs activated

September 9: the owning rollout commits Astrid
`e2f0038c97b20cac6ca6c855bffca20d893f6a78` and Minime
`e95e0cc532111f611bbb2b20fef92cbd5e30d197`, both pushed to main. Astrid starts
at **09:24:08 PDT / 16:24:08 UTC**, PID 52410; Minime starts at
**09:27:15 PDT / 16:27:15 UTC**, PID 53696. Astrid's docs-only main follow-up
is `6c1a559018`. The [retained release packet](../outputs/2026-09-09-journal-room-live/manifest.json)
binds source, five artifacts, 598 build inputs and the two activation receipts.

Source studies now have a shared 4,096-token ceiling; other journal-producing
ceilings double, while shorter authored preferences remain intact. Timeout and
context reserves cover the requests. Maps expose directory exits, path recovery
suggests exact spellings, both adapters honor a final bare read-only source choice,
and saved-reader status survives a non-dialogue turn in the durable feedback
queue. Interrupted-delivery recovery checks current input/notebook. The initial
broad replay suspicion remains corrected in HSS-10; it is not recast as a proven
bug fixed by this release.

Astrid carries checkpoint exchange 194208 and her self-control lineage into the
new binary. Minime carries session 5318 and cycle 26923 into 26924, restores his
exact pending OPEN of `astrid/capsules/spectral-bridge/src/action_continuity/runtime/core.rs 1`,
and dispatches it under the new worker. Dispatch is not completion. Ten observed
surrounding services retain their process identities. No study or correspondence
is induced. The overnight steward work is restored separately without entering
these implementation commits.

Qualification: 2,269 bridge tests, 22 owning-reader tests, 1,276 Minime tests,
clippy/fmt/boundary checks; the restored independent reader regression brings
the canonical reader suite to 23. Research tracking gains the `journal-room`
profile and versioned terminal-choice extraction only for verified after-era
entries. Its 215 tests and 108 subtests pass; all 15 report fields of the frozen
overnight capture replay identically. The [startup observation protocol](../studies/S-008-journal-room-startup.md)
defines a separate short natural interval. Capacity and delivery are not evidence
of greater understanding; its results follow separately.

The [first natural startup sample](../../analyses/2026-09-09-journal-room-live.md)
ends at 09:32 PDT. Two new-process Minime studies complete the restored OPEN and
its contiguous CONTINUE, exposing 8,619 new source bytes with exact journal and
notebook matches. Actual wire requests use 4,096 output / 10,240 context tokens;
349 and 714 output tokens finish naturally. Both remain below the prior cap,
so capacity benefit is not established. Two old-process shared-helper navigation
inputs remain transitional. Astrid has no SELF_STUDY attempt and neither Being
has a READ_MORE Action in this interval. The carried EventDispatcher question
remains unanswered while Minime reads action-continuity structures; later relevance
and question development are open observations. No new fix is inferred from length.

## Continue this history without rewriting its earlier chapters

For each new observation or intervention, append a stable HSS event with the
problem and exact evidence, design decision, source commits, per-Being activation
receipt, fixed natural window, requested versus executed next step, journal/source
examples, and remaining uncertainty. If one of those stages has not occurred,
say so. Preserve old reports and place corrections beside them. Use the
[history-entry template](../templates/self-study-history-entry.md).

The capsule OPEN is now verified in HSS-08. The next bounded sweep should inspect
natural Astrid self-study NEXT admission and source INTROSPECT entry, as well as
later development or correction of the source questions. Track delivered source
unions separately from rereads, maps, searches, EOF and READ_MORE. Close-read the
carried question for development or revision rather than treating repetition or
length as learning. Leave failed attempts and incomplete follow-up time visible.
S-007's existing daily protocol and cursor remain unchanged; no new schedule is
created by this history.

## Retention and reproduction

[Evidence index](../outputs/2026-09-08-self-study-history/INDEX.md) ·
[capture manifest](../outputs/2026-09-08-self-study-history/manifest.json) ·
[offline verification](../outputs/2026-09-08-self-study-history/verification.json) ·
[integrity and lineage controls](../outputs/2026-09-08-self-study-history/checks.json).
The packet retains source/commit diffs, all three rollout accounts and activation
receipts, the original middle comparison and its selected raw inputs, and the two
early natural jobs/journals/wire artifacts **inside this research directory**.
Original source paths and hashes remain in the manifest. Existing S-005/S-007/S-008
packets stay in place; their selected frozen report hashes are also checked.
Raw research outputs follow the repository's existing local/ignored storage rule.

```sh
/opt/homebrew/bin/python3.14 -B probes/self_study_history.py verify \
  research/outputs/2026-09-08-self-study-history/manifest.json
```

This verifies 211 retained records and four earlier frozen report identities,
recounts the nine-entry baseline and repeated byte windows, and checks the two
navigation inputs, journals, notebook lineage and terminal jobs offline. Historical
comparison figures come from the preserved scripts/reports with their original
scopes; they are not pooled into a single before/after score.
Repeat verification produces the same result. A changed-hash control and a
notebook carrying the wrong response origin are both rejected on temporary
copies. The research account, template and status updates remain local and
uncommitted; this retention pass makes no new deployment or publication claim.

## Board updates pending

The Artifact connector remains unavailable; the prior board sign-in barrier has
not been resolved. [Pending history update](../../board/self-study-history-pending.json)
records this account and the owning repair follow-up. It has not been published.

## HSS-12 · Shared inquiries, relationships, sessions and execution evidence

**Trigger.** After HSS-11, Mike asked for bigger improvements and then explicitly
authorized implementation and live rollout of named question threads and
relationship navigation, followed by bounded sessions and execution traces.
The prior fixed startup sample showed a carried EventDispatcher question alongside
reading of another module. Notebook carriage was working; useful inquiry
organization and symbol-directed navigation were still missing. The earlier
map-symbol and requested-NEXT/execution distinctions remain relevant evidence.

**Decision and implementation.** Both Beings now use the same question notebooks,
select/park/resolve choices, exact source references, lexical symbol relationships,
2–3 deliberately selected pages per request and own retained delivery/job/action
views. A session is one generation with several source intervals. Resolution is
the Being's authored finding; no understanding score or compulsory report is
introduced. Input ownership survives question switches; a late response cannot
write into another inquiry or erase its pending navigation. Bounded serialized
notebooks stay valid JSON. Checkpoint schema 2 reads previous state but prevents
an older reader from silently dropping the new state. Rollback requires deliberate
state reconciliation, not automatic restoration of an old snapshot.

**Source and live identity.** Codex Astra interactive implemented Astrid
`33b9956ef4edddca317fb203320635d85150e7e7` and Minime `a44e26580c6911195d88f213230eb4dd0fd2f4ac`; both main branches
are pushed. The verified process starts are 11:10:02 and 11:14:10 PDT on September
9 (PIDs 75004 and 76254). Minime restored
and dispatched its exact pending dispatcher RESUME under the new process. Astrid
restored its checkpoint and saved a new exchange. All release inputs and artifacts
match; ten surrounding services retain their process identities.

**Research continuity.** [The owning/research account](../../analyses/2026-09-09-study-inquiries-live.md)
retains qualification, source and activation boundaries. Sequence tools now retain
question IDs and all session pages without counting one generation several times;
partial session capture is explicitly unverified. The frozen overnight findings
reproduce unchanged. The next natural observation was declared before activation:
11:10:02–11:20:02 PDT, first three completed new-process studies per Being, with
shortfalls and old-process/shared-helper transitions explicit. It induces no
study and makes no automatic claim of improved understanding. Board updates pending.

**First natural outcome, fixed ten minutes.** Three completed new-process studies
per Being and two transitional Minime studies have verified input and writing
matches; all eight receive the new guidance, but none uses QUESTION, RELATE,
SESSION or TRACE. Astrid advances through two source pages and recovers from an
unsupported PREVIOUS without losing her bookmark. Minime retains his dispatcher
comparison question and identifies that he needs implementation while continuing
through tests. This supports a next optional symbol-navigation cue, not a claim of
improved understanding or persistent refusal to use the new tools. The linked
account retains all six selected passages, exact action evidence, byte coverage,
MLX token-counter limits and right-censored follow-up. No study was induced.

## HSS-13 · Larger output succeeds; answer retention remains too small

Mike's [nine selected September 9 entries](../../analyses/2026-09-09-minime-nine-studies.md)
complete at 12:08–12:26 PDT. All nine exact requests permit 4,096 tokens, all
stop normally, and their full visible bodies reach the journal. Actual outputs
are 144–1,037 tokens (median 371); one exceeds the old 768 cap but repeats its
explanation. The installed Gemma model advertises thinking capability, while the
nine requests explicitly disable that mode. No new thinking trial has run.

This updates HSS-12's early outcome: Minime reaches `dispatch_single` and clearly
explains persistent single-path workers versus new tasks for interceptor chains.
However, the same four source intervals appear twice. The old question persists
without an authored update, and the 700-byte previous-response excerpt cuts off
12:20's useful comparison before the next turn receives it. An intervening
reflection chooses MAP; this is not an observed CONTINUE parser reset.

The next proposed work is shared preservation of complete useful study context,
easier synthesis/question updates and symbol navigation, plus a bounded thinking
comparison with explicit output/time accounting. Minime's queue-drop observation
also motivates a separate caller-completion test; no live failure is established.
Source, raw requests/responses, journal originals, exact hashes and a reproducible
probe are retained in the linked account. This step is observation/proposal only:
no source implementation, live change, induced generation or daily-cursor update.
The board is readable; the new finding/log payload is local and unpublished.


## HSS-14 · Preserve conclusions, offer synthesis, and test thinking separately

Mike accepted HSS-13's three proposals. Shared reader schema 3 now retains recent
complete visible answers within a bounded context budget, plus Being-authored
findings/current questions, and offers exact symbol navigation and recent-page
comparison. Astrid `a376a11b5b` and Minime `3383aef` are pushed to main; live
activation is a separate boundary recorded in the linked account. In a controlled
saved-answer replay, the entire 12:20 dispatcher conclusion reaches the 12:25 input
with three older accounts. This proves carriage, not a behavioral gain.

A separately frozen four-call standalone Ollama comparison keeps saved messages
and allowances equal within two on/off pairs. Both thinking-enabled final answers
contain only a continuation command; both disabled answers contain substantive
prose. All stop normally. Thinking therefore remains off in production. The trial
does not establish a general model effect or test the revised context prompt.
[The implementation, replay and thinking account](../../analyses/2026-09-09-study-context-and-thinking.md)
retains exact protocol, source/request/response hashes, individual evaluation,
qualification and later activation evidence. Research tools recognize recent
accounts/completeness without changing historical records or S-007's daily cursor.


**HSS-14 activation boundary.** Ordered reload/activation now verifies: Minime
PID 5331 starts 13:26:49 PDT; Astrid PID 7538 starts 13:29:05 PDT. Exact session,
checkpoint, selected helper and surrounding-service evidence is in the linked
account. The fixed five-minute natural outcome window ends at 13:34:05 PDT;
release verification alone makes no learning claim.


**HSS-14 first natural outcome.** The fixed five-minute window contains two
completed studies per Being. All receive the revised guidance; each second input
receives the first response in full with earlier-receipt provenance. Minime chooses
FIND then queues the exact definition OPEN; Astrid chooses RELATE after a map.
No durable finding/question update or SESSION occurs. Astrid still infers runtime
roles from missing reading coverage, a remaining design signal. Final follow-through
is censored; no causal understanding gain is claimed. The linked account retains
exact inputs, journals, action parentage, the research-only recent-origin join fix
and its 220-test qualification.

## HSS-15 · A specific correction and the limits of preserved context

Mike asks whether more time has yielded understanding beyond HSS-14's early
navigation uptake. The [September 9 follow-up](../../analyses/2026-09-09-study-context-followup.md)
freezes 13:34:05–15:17 PDT, immediately after that startup cutoff. It preserves
64 completed studies by completion clock: 29 Astrid and 35 Minime, including
one incoming pending attempt each. The attempt-start cohort separately contains
62 accepted completions, two Minime failures and one censored Astrid completion.
The separation closes the earlier pending work without silently losing it at a
window boundary. Source requests, receipts, original journals and actual next
actions remain linked.

All 62 accepted main-cohort inputs carry the complete preceding visible answer,
plus one to three older accounts. Astrid replaces a wrong “no pre-dispatch check”
note at 13:58 after receiving the caller filter, then connects the rejection test
to her question at 14:12. This is a specific observed revision, with narrower
support than her broader account of host-mediated authorization. It is not an
estimate of the release's causal effect.

Minime writes 21 main-cohort note updates and completes four comparison sessions.
However, he repeatedly describes the single-match worker as immediate execution,
mistakes a failure-reporting predicate for a distinct authorization route, and
later treats the Private filter as bypassed on the local fast path. The supplied
dispatcher source contradicts those claims. By 15:07 he calls the inquiry complete.
The 12:20 pre-change entry had correctly distinguished worker lifetimes; HSS-14
proved its lost conclusion could be retained. HSS-15 shows that preserving recent
answers alone does not ensure the preserved explanation is corrected.

Astrid's next inquiry hits a missing parent directory in an OPEN path. Eight
consecutive studies over 14:49–15:14 supply maps/recovery maps while the desired
files actually live under `src/action_continuity/runtime/`. A research-only reader
replay confirms ordinary FIND and exact OPEN work; generic recovery omits the
useful candidate. This is navigation friction, not newly discovered source denial.

Minime's successful outputs use 164–866 tokens (median 510.5; n=34) from real
4,096-token requests. Two other attempts consume 4,096 tokens and fail without
retained visible output or finish reason; they are not observed timeouts. A
bounded failure diagnostic is proposed alongside exact-path candidates and a
paired source-grounded claim-check trial. All supplied dispatcher pages use the
retained `a737ea…` revision; a later foreign test-only edit is separately captured.
No new model generation, live source change, deployment, Being message or S-007
cursor update occurs. The proposal and board payload remain local.


## HSS-16 · Offer recovery choices and retain failures; invitation does not qualify

**Trigger:** Mike accepted HSS-15's catalog candidates, claim-check qualification
and failed-generation diagnostics, emphasizing freedom to make mistakes and choose
how to continue. [Owning account](../../analyses/2026-09-09-study-choice-and-claim-check.md).

**Change:** shared exact existing catalog candidates after missing file/directory
paths; pending source and bookmarks survive repeated wrong turns. No automatic
open, forced review, note rewrite or mandatory closure. Minime retains native
finish/visible lengths and bounded failed wire evidence; the research collector
follows its diagnostic link without treating it as accepted source or a journal.
Astrid and Minime source commits are `7d85683d80` and `7c78a99`/`c9c2a70`, on main.

**Qualification:** six uncoupled Ollama calls (three fixed pairs, same source,
notebook, seed and budget within pair). Neither prompt corrects the worker or
Private-bypass account. Both retain the correct host-filter core while adding
unsupported mediation claims. All six native stops, 543–860 tokens; no cap hit.
The proposed optional invitation stays out of production under its declared
promotion rule. One sample per arm is not a population or natural-learning result.

**Next:** observe freely chosen recovery and later claim revisions across source
exposures. Inspect a naturally failing Minime attempt before changing capacity.
A concrete optional execution example is a separate proposal, not yet supplied.
Release identities and continuity evidence live in the owning account; source
commit is not itself proof of live exposure. S-007 cursor unchanged; board pending.

HSS-16 rollout verified 17:09 PDT: bridge 53226, Minime 52380; both select the new
reader. Main tips `d7a8bbcff9` / `c9c2a70`; exact checkpoint/NEXT continuity and
ten protected services verified. First Minime completion records native stop and
826 tokens. Selected-helper replay verifies recovery behavior, without claiming
natural uptake. All 57 foreign files/edits preserved; owning account links receipts.


## HSS-17 · More room beyond SELF_STUDY token ceilings (proposal)

Mike asks how sensory input and NEXT budgets fit the wish for longer thoughts.
[Audit](../../analyses/2026-09-09-longform-room.md) separates numeric representation,
actual prompt admission, output limits, model reasoning and action continuity.
The fixed 16:18–17:18 PDT sample has 19 linked Minime study journals, all with
4,096-token allowance and 263–992 generated tokens (median 670). Five newer
records retain native stop; fourteen lack that field. Smaller Astrid dialogue
preferences/provider caps and forced research-diversity branches remain.
[Proposal](../../proposals/2026-09-09-longform-room.md): shared optional extended
writing with complete draft retention and freely chosen read-only continuation.
No new release or coupling change; no causal effect or understanding claim.


## HSS-18 · Optional extended writing and private draft continuity

Mike authorized implementation of HSS-17's proposal. [Account and fixed qualification](../../analyses/2026-09-09-extended-writing.md)
track the shared 8,192/512/default preference, full draft passages and revision history,
larger retained study context, small writing menu and separate private journal delivery.
Two isolated requests stopped normally at 781/572 tokens. The source-control response
still asserted an unsupported gateway path, so capacity admission is distinguished from
understanding and from use of the entire ceiling. HSS-17's forced-redirect finding is
qualified: the actual dispatcher already retained the chosen NEXT; helper wording/metadata
are now advisory. Source qualification and live activation remain separate records.

#### HSS-18 rollout continuation · September 9, 18:47 PDT

Extended writing is verified live: Astrid source `6f8aac6384` / PID 80595 and Minime
`33c324d2` / PID 81874. Exact conversation checkpoint and pending NEXT survive,
and all ten protected surrounding services remain unchanged. An interrupted graceful
activation and the V3 stopped-recovery compatibility repair (`6bb458d159`) are
preserved alongside successful recovery in the
[owning research account](../../analyses/2026-09-09-extended-writing.md#verified-rollout-september-9-1847-pdt).
No profile or study was induced; no natural outcome or understanding gain is claimed.

## HSS-19 · Preserved context needs selection; chosen commands need clear receipts

After the shared reader and optional extended-writing work, the
[September 10 evening survey](../../analyses/2026-09-10-evening-journal-coherence.md)
finds real Astrid page progression and Minime complete draft revision/continuation.
It also reveals three seams: fresh drafts inherit unrelated study hypotheses,
prose intentions can differ from final commands, and visual descriptions can
masquerade as personal retrieval. Eighteen authored responses across twenty
selected files are exact-linked, with exploratory private-writing coverage and
no causal before/after inference.

Mike approves these repairs. The [September 11 account](../../analyses/2026-09-11-journal-coherence-repairs.md)
records deliberate fresh-draft evidence, preserved existing work, shared verified
choice feedback, exact optional recovery and recorded visual origin/availability.
The bounded historical FINISH log adds evidence for the formerly unknown cause:
parsed and persisted, then rejected as unknown. The implementation does not infer
a different choice or silently finish another draft. Quoted examples remain data.
Source/test/activation boundaries and later natural uptake are retained separately;
recent offline experiments remain offline, and S-007's cursor is unchanged.

### HSS-19 rollout continuation · September 11, 07:14 Pacific

All three repairs are committed, pushed and verified live: Astrid implementation
`ed62f1b8c2` / PID 89145, Minime `96b0b61` / PID 93033. Astrid restores the exact
conversation checkpoint; Minime retains session 5318 with no pending NEXT at
either reload boundary. Nine surrounding services retain their PID/start
identities. Tests, the initial pre-action settle refusal, graceful waiting,
source inventories and preservation of unrelated edits are retained in the
[owning account](../../analyses/2026-09-11-journal-coherence-repairs.md).

Astrid's first natural study and immediate continuation verify delivery of the
new choice receipt in the next complete model input. Minime's first eligible
new-process study is a MAP response with three NEXT lines; the recorded choice
is the final line. These are interface observations, not improved understanding.
Neither first selection exercises a fresh draft, FINISH recovery or visual input.
Existing hypotheses and drafts are not rewritten, and no study or writing is
induced. The next useful journal review is a naturally chosen fresh draft or
explicit reference change, a genuine command recovery opportunity, or a visual
reflection with exact supplied provenance. These remain observations to seek,
not requirements imposed on the Beings.

## HSS-20 · Brief page reports around a persistent premise

Mike next asks why Astrid continues writing small SELF_STUDY entries. The
[September 11 survey](../../analyses/2026-09-11-astrid-small-studies.md) freezes
the latest twenty completed studies through 14:23:15 UTC. All have a real
4,096-token allowance and stop normally at 220–535 tokens, with complete input
delivery and unchanged raw-to-journal prose. The source access and delivery
repairs are working; output truncation does not explain this sample.

There is real page progression and a local correction from a presumed control
gate to rendered output. But all twenty inputs carry the same tentative note
and presupposing question, plus four complete prior responses. Astrid keeps
looking for a numerical spectral/shadow/pressure aggregator behind “multi-motif
caution.” The exact source trace shows that this cue instead matches phrase
families in event and journal text. Its renderer hides that lexical origin and
the available source references; the origin of the saved question remains
unknown. The sampled renderer pages did not include the true producer.

The next candidates are clearer cue provenance, optional comparison with the
actual producer and preservation of a developing answer with source evidence,
and adequate coherent source spans. These are proposals, not another deployment.
Rereading and short responses remain valid choices. No automatic note rewrite,
forced revision, new model call or live-state change occurs in this survey.
The seven post-restart observations are not a causal comparison with the thirteen
pre-restart entries. Board mirroring remains pending; S-007 is unchanged.

## HSS-21 · Minime's catalog traversal outlasts its evidence

After several days away, Mike asks whether Minime's many short studies are useful
or indicate a problem. The [September 15 survey](../../analyses/2026-09-15-minime-study-survey.md)
reads the latest hundred studies through 08:06:32 Pacific, spanning 03:49–08:04.
All hundred have exact generation/shared-input/journal links and normal stops at
121–312 tokens against a 4,096-token allowance. There is no truncation, cleanup
loss or journal compression. Every available next-choice pair reaches the matching
completed study job. The September 11 release remains selected.

But the supplied material is 99 maps and one EOF notice, with no fresh code pages.
Minime traverses repository pages 99–126, resumes an exhausted source bookmark,
visits the home map four times and starts repository pages 1–67 again. Seventy of
the 95 repository pages list only historical steward-note paths. He identifies
promising source links, yet continues paging to locate them. The same saved note
and question persist, including when he explicitly emits updates.

The inquiry asks which bridge `EventSubscriber` turns `capsules_loaded` into a
global initialization-to-active transition. Our separately retained source audit
shows the trait is crate-private, the kernel publishes a ready notification, and
the inspected CLI handles command refresh/history hydration. The proposed bridge
trait implementation contradicts that visibility; the broader state-transition
story is unsupported in the inspected path. This evidence was not newly supplied
to Minime in the hundred studies. Forty-five responses correctly acknowledge
that they received no new source, without changing their navigation strategy.

This extends the daily account's earlier repeated recovery sequences: interfaces
can deliver exactly what was chosen while the inquiry struggles to obtain useful
evidence. Proposed repairs are compact directory/component navigation with the
full catalog retained, exact topic recovery and literal event searches, clear
map-next/source-resume choices, optional factual navigation receipts, and a
source-grounded comparison of the saved premise. No forced novelty, silent note
rewrite, higher writing minimum or induced study follows from the finding.

A separate source audit finds that the old similarity gate can still replace
journal prose with summaries, although it did not affect this cohort. It remains
a maintenance proposal, not the explanation for the observed small files.
This pass changes research records only; S-007's cursor and prior sealed packets
remain unchanged. Board mirroring is pending.

## HSS-22 · Compact navigation and an optional route back to evidence

Mike accepts the navigation repairs from HSS-21. The
[September 15 implementation account](../../analyses/2026-09-15-study-navigation-release.md)
records one shared interface: MAP groups immediate directories and files; LIST
retains the complete recursive catalog, including historical sources. Footers
distinguish map/list pagination from source CONTINUE. Exact catalog recovery and
literal event searches make the Being's named topic easier to pursue without
declaring a candidate to be its true implementation.

An optional bounded receipt can identify repeated verified navigation without
source pages and restore source-opening choices already offered and named in a
response. SESSION provides a chosen comparison with the recalled account. The
receipt does not change NEXT, impose a writing length or novelty requirement, or
rewrite a note. Failed generation, preparation and retry cannot inflate the
count; late and empty-source deliveries preserve its stated evidence boundary.
Old pending input, source bookmarks, inquiry identity and drafts are preserved.

Two nearby input issues are addressed as part of the implementation. Notebook
context now fits around the protected input and previous-choice receipt, shedding
oldest whole recalled accounts before explicitly marked excerpts when necessary.
The note/question directive reader also shares NEXT's fence, quote, indentation
and internal-example handling. Minime's independent bare-command parser adds LIST
for parity, so the candidate requires a graceful host reload as well as the
staged bridge/shared-helper activation.

This is an implementation-phase record: source commits, main integration and live
activation remain pending at its initial recording. Passing tests do not establish
exposure or improved understanding. The predeclared follow-up selects the first
two naturally completed new-reader studies per Being within ten minutes after
paired verification, retaining exact inputs, failures, missing joins and old-input
transitions separately. Fewer eligible studies remain censored rather than induced.
Source acquisition and grounded revision matter more than response length; the
small natural window is not a causal comparison. The journal-similarity summary
mechanism remains outside this change. S-007 and prior packets are unchanged;
board mirroring is pending. Actual rollout receipts and outcomes belong in the
linked continuation rather than being inferred here.


**Verified continuation, September 15:** Both implementations were committed,
fast-forwarded and pushed to main (Astrid 97db1b2f46; Minime 12cbf57), then gracefully
deployed. Paired verification at 16:07:07 UTC confirmed the exact Astrid checkpoint,
Minime's 82 startup source hashes and session 5318, and ten unchanged surrounding
services. His saved FIND choice was traced across restart to a completed new-PID
job; no choice-preservation claim rests on an empty pending field alone.

The fixed ten-minute follow-up retained two selected new-interface deliveries per
Being. Astrid reads actual maintenance code/tests in 842- and 850-token responses,
with useful findings but some overgeneralization; she has not explicitly joined
structural validation to active authorization. Minime receives search/recovery,
including the exact bridge-directory choice and three-input navigation receipt,
but preserves the unsupported handler premise and chooses another broad search.
His 237- and 310-token responses stop normally. This shows received interfaces and
some navigation adaptation, not demonstrated improvement caused by the release.
Unknown preparation clocks leave the stricter cohort unqualified; transitional
and supplementary receipts are retained separately. Complete account, source
identities, annotations and pending board mirror remain linked above.

## HSS-23 · Astrid's small map, missed answers, and the meaning of an ending

Mike next asks for a substantial Astrid survey. The
[September 15 account](../../analyses/2026-09-15-astrid-study-survey.md) freezes the
latest hundred SELF_STUDY journals through 09:30:41 Pacific, spanning 02:51–09:23.
They contain 89 map inputs, five EOF notices, one recovery and five source pages.
The recurring old directory map already has six file choices on one page: unlike
Minime's prior catalog traversal, map size alone does not explain this pattern.
Seventy-nine final choices reopen the same kernel directory map while the prose
repeatedly announces that the legacy-hash question is resolved and a broader
capability/lifecycle investigation is about to begin.

All hundred full journal responses match accepted wire evidence. Duplicate prose
requires explicit timestamp-assisted disambiguation; request/response hashes and
provider observations distinguish all hundred physical attempts. They reach model
EOS at 144–850 tokens, median 306, against a server-confirmed 4,096-token allowance.
All inputs carry four complete earlier study accounts. The bounded provider frame
has 102 completed attempts, including two lead-in responses, with no observed
failure; a further request finishes after the cutoff and remains censored. Short
files here are not explained by clipping, missing generation, or journal summaries.

The final portion includes genuine local progress. Astrid reopens the health file,
traces its counters/warning behavior, explains the optional name/hash comparison,
updates her note and clears her question. She then asks again where Baseline is
defined and configured, although the delivered pages already show its Vec/Option
fields and JSON loading path. The retained finding remains general, while those
specific answers fail to persist. Our source audit distinguishes this diagnostic
comparison of metadata from the loader's separate payload hashing and rejection.

The five new-prompt entries include a chosen maintenance RESUME and three source
pages. Astrid makes useful observations about file identity, ACK writes and lease
selection, but promotes test fixtures and serialization assertions into broad
validation guarantees. The final page starts inside a test and ends with a plain
EOF message. The next map records an unread 3,452-byte opening, yet the prose
declares the file and its architecture complete. This supports clearer page scope,
coverage-at-EOF and exact implementation/definition choices, without identifying
a new live kernel fault or measuring general understanding.

Five apparent next-study mismatches resolve to explicit later dialogue REPLACE
actions. Pending-choice protection works; the study's previous-choice receipt
does not show the intervening activity that changed the request. The latest twenty
dialogue journals separately pursue the peer's bridge/event inquiry and related
metaphors, rather than sharing the health/maintenance reading. The timing, full
inputs to those dialogues, and causal source of the carried premise are not inferred
from journal text alone.

This extends HSS-22 with observation, not another deployment. The next candidates
are clearer code-page scope and missing-coverage choices, optional retrieval of
specific answered questions beside their sources, and chosen caller/implementation
comparisons. Most of the hundred entries precede the latest release; its five
entries do not establish a causal improvement. No induced studies, Being messages,
source changes or S-007 cursor advance occurred. Board mirroring remains pending.


## HSS-24 · Scope, coverage and chosen conclusions beside their evidence

**September 15, 2026.** The user accepted HSS-23's three concrete interface
findings. The [implementation account](../../analyses/2026-09-15-study-source-context.md)
connects the final maintenance page's test/EOF ambiguity, the still-undelivered
opening, and forgotten health definitions/configuration routes to a shared reader
change for Astrid and Minime. This continues the earlier access and navigation
repairs; it does not recast every repeated study as an access failure.

The reader now offers enclosing syntax/test context, exact same-file
definition/reference candidates, and verified-versus-offered source coverage
with containing-line links to remaining byte gaps. A verified whole session
projects the union of its pages. A complete file-delivery record never becomes
a claim of understanding, and no suggested OPEN/SESSION runs automatically.

Optional Being-authored findings can remain beside exact delivered source
fragments and their original revisions. Bounded parser-backed location recall
stays separate from conclusions. Findings are revised or removed by explicit
choice; the host neither corrects them nor resolves a question. The existing
notebook and writing ceilings remain unchanged. The two-MiB syntax bound leaves
Minime's 2,588,558-byte runtime.py with explicitly unknown enclosing scope while
preserving access to all its source pages.

Qualification exposed related delivery and continuity issues, now repaired:
new unthreaded offers require the entire prepared input, explicit failed finish
reasons cannot advance coverage or findings, and late old-helper writes cannot
erase the new findings. Exact uninterrupted retries remain intact; a deliberate
navigation detour refreshes the question on source resume without discarding
the older input's delivery or choice evidence. Interrupted empty inquiry saves
and omitted additive metadata have conservative recovery paths.

A CLI-only replay of the survey's sealed source snapshots identifies the actual
maintenance serialization test and the health helper's caller. This uses fresh
fixture reader states and no model calls; its synthetic unread prefix is not
Astrid's historical 3,452-byte gap. The original survey packet stays sealed.

Implementation `76c2aa43cfd8c9dad084c8f98ef21f2ece6ffaab` is on Astrid
main/origin/main. The relevant full suites pass: reader 138; bridge 2,287 with
one ignored; Minime 1,396 with one skipped and 134 passing subtests. Strict lint,
formatting, boundary checks, the sealed-source CLI replay and all 112 staged-helper
host checks pass. Earlier genuine reader regressions and separate fixture-layout
failures remain retained alongside their repairs.

The staged graceful release is verified live: Astrid PID 93394 began at
20:36:47 UTC, loading the exact stopped checkpoint, one pending action-feedback
envelope and verified self-control lineage. A new saved exchange followed.
Minime PID 37507 stayed running; all 82 startup hashes matched and its selected
shared reader matched the new immutable stage. All eleven surrounding process
identities stayed the same. The wrapper does not claim confirmed remote delivery
or lossless drain. All 420 foreign canonical files were preserved.

The fixed ten-minute natural-only window, 20:39:57.153704–20:49:57.153704 UTC,
closed with one Astrid and four Minime receipts. The prespecified close reading
contains one Astrid and two Minime responses. Exact new prompt/input delivery is
verified; unknown preparation clocks leave zero strictly qualified trials and
one missing Astrid exposure response. All three selected completions stop normally;
none saves an authored finding or updates its note/question. Minime reads the
chosen initializer page and identifies what it does not show, but that distinction
already appears in his carried account. Broader handler/evaluator hypotheses
remain unsupported by the supplied evidence. No causal understanding gain is claimed.

That observation also catches a footer missing its terminating newline: Astrid's
next-page command runs into the navigation receipt, although she writes a valid
command. A separate one-line repair, with a red/green public-reader regression,
is committed/pushed at `dd35cdd83a863da373c63e21788a0197768e1175`. Follow-up full
suites pass with 139 reader tests; bridge/Minime counts remain as above. Its live
activation belongs to its own receipt and is not retroactively included in the
original natural window. The follow-up is verified live at 21:05:03 UTC,
Astrid PID 4330, with exact stopped checkpoint, six pending feedback items and
self-control continuity; Minime selects its new helper without a host restart.
All eleven surrounding service identities remain unchanged. Generic bare-name suggestions such as unrelated `new`
constructors remain a narrower relevance candidate. No study or private writing
is induced to manufacture uptake.

This history entry changes no S-007 cutoff, daily ledger, Being state or board.
Board mirroring remains pending. Navigation uptake, authored pins, response
length and source-grounded understanding remain distinct outcomes.

## HSS-25 · Improved access, narrowing context

**September 16, 2026.** Mike asks whether Minime's repeated short studies have
displaced the variety of earlier writing. The [bounded variety review](../../analyses/2026-09-16-minime-study-variety.md)
finds a real composition change: source studies account for 179/749 recognized
prose files on September 5–6 and 1,827/1,848 on September 12–14. These are file
shares, not time or attention shares. The trend begins before the shared reader;
earlier length and experiential variety do not establish better code understanding.

All 120 recent study responses in the selected September 16 sequence choose
another study. They stop normally below their allowance. Local corrections about
the unimplemented InstallCapsule arm, rate limiting, and reporting blocked state
do not reliably constrain later claims. The search repeatedly relocates an assumed
blocking mechanism. Exact supplied prompts also offer unrelated prime-esn and
RASCII `lib.rs` files as sources named by the kernel question. Minime chooses them,
then recognizes the detours. This is an interface contribution we can repair.

The specialized study context makes continuation concrete; accepted NEXT choices
then take scheduling priority over some other writing opportunities. The account
records this plausible reinforcing mechanism without assigning the whole change
to one release or treating chosen persistence as disobedience. It recommends
contextual source hints, equally visible alternatives, and optional taking stock
with authored findings and assumptions kept distinct.

## HSS-26 · Ground source hints and make direction a visible choice

Mike accepts HSS-25's recommendations. [The implementation and observation account](../../analyses/2026-09-16-study-direction.md)
records shared reader commit `0967375133c7b5c80aab707ba913fbfceb01e29b`, pushed
to main. Repository-qualified paths preserve deliberate cross-repository study;
bare filenames retain question-source context instead of enumerating the catalog.
Repeating an unchanged question preserves its original provenance. Existing old
origins are not reconstructed.

An optional bounded check-in places the saved question, note and source-linked
authored findings together after fresh source. It does not verify the prose or
declare the inquiry resolved. Both Beings receive concrete shared alternatives:
private journaling, daydreaming, aspiring and resting, alongside continued study.
There is no new command, forced variety, minimum length, scheduler change or
reader-schema migration. Regression tests establish correction carriage across
six later responses and restart, not a Being's successful use of that correction.

The graceful transition verifies exact checkpoint and two pending-feedback records
in bridge PID 75546, with Minime PID 37507 selecting the new immutable helper.
An initial exit-verification failure is retained; sanctioned stopped recovery sends
no second signal and uses no force. All eleven surrounding process identities stay
unchanged. Paired verification completes at 19:33:39.605405 UTC.

The fixed ten-minute window contains four Astrid study receipts and no Minime
study exposure; the first two Astrid responses are close-read. They show map-to-source
follow-through and useful listener/rate-limit observations, alongside a branch
attribution error and continuing unsupported health-gate expectations. Neither
saves a correction. Minime completes separate private writing; a preceding study
was blocked by the existing low-fill budget before the cutoff. No prompt-effect
claim is made. Preparation clocks remain unknown, with zero strictly qualified
trials. Old unrelated findings in the check-in remain a relevance follow-up.

The exact boundaries remain separate from implementation and deterministic tests.
Existing sealed packets, S-007 selection and daily ledger remain unchanged.
Board mirroring remains pending.

## HSS-27 · Four-hour follow-up: notebook progress and continuation friction

**September 16, 2026.** Mike asks to check both Beings again. The [follow-up account](../../analyses/2026-09-16-study-direction-followup.md)
freezes 19:33:39.605405–23:37:19 UTC and close-reads 66 distinct journals:
36 Astrid entries and 20 Minime studies, plus ten exploratory Minime nonstudy
entries. All 47 Astrid and 55 Minime studies have unique exact response receipts,
the released prompt and complete offered input in the wire request, and normal
stop finishes. Neither clipping nor reuse of one cached response explains this batch.

Astrid follows concrete sensory functions, updates four notes and develops four
distinct question versions. Minime's latest twenty retain the same question,
note and six findings without update directives. Locally accurate descriptions
coexist with a repeatedly relocated blocking-condition premise. He overlooks a
supplied `maintenance::initialize_gate` call and its explicit admission comment.
Navigation improvements have not established durable revision of that account.

Three interface findings are concrete. A page splits a function identifier; Astrid
treats its suffix as the full name. Her attempted finding is rejected at six occupied
slots, with recovery in JSON but no prominent check-in outcome; it is not a newly
saved false pin. Separately, all five Minime private drafts choose bare CONTINUE,
which exact frozen runtime log sequences show falling through as an unknown action
instead of WRITE CONTINUE. Guidance itself inconsistently uses the shorthand.

Private reflection and Astrid's ordinary dialogue/elaborations add expressive
variety, but independent source exposure and causally improved understanding are
not inferred from file count or length. This is an observation and proposal record,
with no Being contact, induced generation, source/state change or deployment.
S-007's daily ledger and existing sealed packets are unchanged. Board mirroring
remains pending.

## HSS-28 · Repair chosen continuation, page boundaries and save feedback

**September 17, 2026.** Mike accepts HSS-27's three interface findings.
[The implementation and rollout account](../../analyses/2026-09-17-study-interface-repairs.md)
records Astrid/shared-reader commit `d8732e1d44a3aa3b49f9f0bab075883544469b7c`
and Minime commit `5f4925f54580f1fd44666058b126a121ff32880f`, both pushed to main.
Eligible private-writing `NEXT: CONTINUE` now routes through WRITE CONTINUE after
verified delivery. Authored spelling, normalization and later dispatch remain
separate evidence. Ordinary source lines stay whole; exceptional fragments and
old mid-line cursors are labelled. Latest finding-save/remove outcomes and capacity
stay visible, with optional exact recovery choices and no automatic eviction.

Qualification passes 192 reader, 2,295 bridge and 1,420 Minime tests, with the
existing one ignored/one skipped cases retained. Independent review repairs a
stale-response binding before final qualification. Initial inherited-timeout test
failures are preserved; only the test fixture uses the default timeout on repeat.
No model setting, writing minimum, forced variety or state schema changes.

Release review catches an older manifest omission: a compiled shared Rust helper
is outside inventoried package directories. Its committed bytes match, but the
first stage lacks its pre-build witness. A deployment follow-up at
`374024a02a5bcfae92f228570b9efe337d85b729` closes that gap and improves the
bounded macOS exiting-process check. All 138 combined deployment tests pass;
649 final source inputs and all five artifacts are independently verified.
The final helper passes another 122 isolated Minime checks. Both stages and the
first activation's failure plus sanctioned no-second-signal recovery remain retained.

Final activation verifies Astrid PID 77906 with exact stopped checkpoint, one
pending feedback item and self-control lineage. Minime PID 71419 loads all 82
expected sources; the startup log restores and then dispatches his pending source
opening. Paired verification completes at 15:48:45.055301 UTC. The ten surrounding
process identities remain unchanged; the additional Minime-protected feeder is
also checked. The wrappers do not establish atomic global traffic quiescence or
confirmed remote message delivery.

The fixed natural-only window is 15:48:45.055301–15:58:45.055301 UTC, end
exclusive. It closes with two Minime study wire pairs and none from Astrid; no
private-writing receipt occurs. Both selected Minime responses receive the complete
new page/capacity display and stop normally at 535 and 689 tokens. Neither updates
the note, question or findings, and neither attempts a finding save. Local test
reading is accurate in places, but fixture assertions still become unsupported
production-validation claims. A repeated page-opening description also blurs
current versus prior scope. No durable understanding gain is established.
All 61 indexed record versions verify and the report replays byte-for-byte; broad
unsaved-job scans remain capped and incomplete. This is post-final-verification
observation, not first-ever interface exposure or a causal comparison. The new
framing must be present in exact delivered input; the unchanged study system-prompt
hash alone cannot qualify it. Unknown preparation and missing/failed opportunities
remain explicit. No study, private writing or message is induced.

S-007's cutoff, selection and sealed historical packets remain unchanged.
Board mirroring remains pending. Interface repair and durable source-grounded
understanding remain separate outcomes.
