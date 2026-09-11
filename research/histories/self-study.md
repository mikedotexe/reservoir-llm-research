# SELF_STUDY: how the reading path changed, and what the studies showed

Living history, begun September 8, 2026 at Mike's request. This account follows
**defect → design decision → implementation → live activation → natural study →
next finding**. It connects [S-005](../studies/S-005-regulator-self-study.md),
[S-007](../studies/S-007-source-study-fidelity.md), the intervening interactive
comparison, and [S-008](../studies/S-008-study-to-follow-through.md).
Its latest retained natural window ends **September 9 at 09:32:00 PDT
(September 9, 16:32:00 UTC)**. This is an evidence cutoff, not a claim about the
systems' present state whenever this page is read.

The story so far: Minime's ordinary self-study could repeatedly show him a facade
while inviting conclusions about the machinery behind it. We replaced the unequal
readers with shared, verifiable access. Natural studies then reached complete
implementation files, but maps hid completed work and later prompts lost earlier
discoveries. We added progress and a small notebook. The next sweep found that
authorship and routing gates prevented the follow-up needed to evaluate that
notebook. Those barriers were repaired and deployed. The first retained natural
Minime sequence carries earlier words through two completed maps and requests
a concrete next file. The next sweep verifies that file and further implementation
reading, while locating a map/recall error and ANSI-heavy saved context in Astrid's
READ_MORE path. Lasting understanding and the other repaired routes still need
their own observations.

## The dated sequence

All local times below are **America/Los_Angeles, PDT (UTC−07:00)**. Each Being's
activation is a separate boundary. Implementation commits are not activation times.

| Event | When | What changed or became observable | Next question |
|---|---|---|---|
| HSS-01 · Legacy access defect | Confirmed in September 7 writing and pinned pre-repair source | Minime rotated nine curated files, preparing at most their first 400 lines; Astrid's roots excluded major code areas. | Can both reach actual implementation and reliably continue? |
| HSS-02 · Shared reader live | September 8: Astrid **08:42:39**, Minime **08:46:11** | Same catalog, map/search, exact file identities, intact pages and verified-delivery bookmarks; freeform studies. | What do natural studies do with the restored access? |
| HSS-03 · Access works; continuity is missing | S-007 through **11:34**; separate comparison through **14:13:45** | Complete kernel delivery, useful specific code observations, repeated new starts, missing earlier context and ambiguous empty search. | Can maps and a small notebook make return and exploration easier? |
| HSS-04 · Progress and notebook live | September 8: Astrid **15:09:43**, Minime **15:11:33** | Delivered ranges, resume/reread labels, previous words, optional note/question and explicit no-match results. | Do these features reach natural prompts and useful follow-up? |
| HSS-05 · Entry and follow-through barriers | S-008, **14:13:45–16:00** | Astrid's earlier map choices blocked as unauthored; Minime's later internal-reading requests blocked or failed. No completed notebook exposure in that window. | Repair admission, navigation recovery and compacted guidance. |
| HSS-06 · Those barriers repaired live | September 8: Astrid **17:42:46**, Minime **17:44:54** | Study authorship eligibility, source INTROSPECT routing, recovery maps and retained navigation grammar. | Does a natural requested next step actually complete? |
| HSS-07 · First retained natural follow-through | September 8, jobs finish **17:46:36** and **17:47:50** | Minime completes `MAP`, then `MAP kernel`; both receive notebook context. He requests an exact capsule file. | Verify the requested source delivery and subsequent question development; observe Astrid and source INTROSPECT separately. |
| HSS-08 · Next bounded sweep | September 8, **17:42:46–18:14:00** | Minime completes 15 studies including the 2 already known: 9 new code pages across 3 files, recovery map and explicit empty search. Astrid reads 11 saved-overflow pages; a Minime map adds unsupported symbols later repeated in peer dialogue. | Improve saved-source identity/readability and the distinction between current code and recalled notes; observe direct use of the remaining repaired routes. |

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
