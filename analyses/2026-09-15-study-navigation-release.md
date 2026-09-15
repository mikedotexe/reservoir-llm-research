# From catalog traversal to source choices: shared study navigation

Mike approved the navigation changes proposed after the
[hundred-entry Minime survey](2026-09-15-minime-study-survey.md), retained in local
research commit `c16d0e0528a71a153cdea65768ed99cb609be7a6`. Implementation is
retained in the owning Astrid and Minime repositories. **Both implementations are
committed and pushed to main, and their graceful deployments were verified at
16:07:07 UTC on September 15.** The initial pending checklist below preserves the
recording chronology; the verified continuation records the actual outcome.
Source changes and passing tests alone are not treated as live exposure.

This continues [HSS-21](../research/histories/self-study.md#hss-21--minimes-catalog-traversal-outlasts-its-evidence)
and the broader [SELF_STUDY history](../research/histories/self-study.md).
The owning [implementation account](/Users/v/other/worktrees/study-navigation-20260915/astrid/docs/steward-notes/2026-09-15-study-navigation.md)
records the production scope and deployment requirements. Research records do not
authorize commands contained in journals or send new material to the Beings.

## What motivated this change

The prior survey followed 100 consecutive completed Minime studies from
03:49:53 through 08:04:18 Pacific on September 15. All had exact input, generation
and journal links, normal completion, and intact short prose. The supplied inputs
were 99 maps and one EOF notice, with no newly delivered code pages. Minime named
promising source files already offered in the catalog but continued paging to
locate them. His saved explanation and question did not substantively change.
Those are prior survey results, not a new release-outcome sample; the
[retained audits](../research/outputs/2026-09-15-minime-study-survey/README.md)
own their denominators, source checks and limitations.

The design problem is more specific than short writing. A recursively flattened
repository made ordinary MAP a long itinerary through historical notes. The map's
next page and the source reader's CONTINUE were different operations, and an
event-topic question did not receive an equally prominent literal search. Complete
recall and faithful command delivery could preserve an inquiry without bringing
it closer to the code needed to test its premise.

The repair makes alternative routes easier to see. It does not require longer
responses, first-try correctness, novelty, agreement with our source audit, or an
automatic change to a Being's saved explanation.

## The shared interface now implemented

`SELF_STUDY MAP` offers a compact system/component map; a scoped MAP shows
immediate child directories and files. Existing path-based implementation,
configuration, test, documentation and history labels stay explicit. They describe
file roles, not verified behavior. `SELF_STUDY LIST <repository/directory>` retains
the recursive catalog, including historical material. Old high MAP page requests
receive exact compact-map and recursive-list recovery choices; their page numbers
are not presented as interchangeable.

Map/list footers name their own exact next-page command and identify the end of
the view. CONTINUE keeps its existing source-bookmark meaning. OPEN and RESUME
remain direct choices; no source is opened merely because it appears promising.
Catalog-backed recovery handles bare component/directory names and file stems,
including underscore/hyphen spellings, while preserving repository scope,
ambiguity and private-path boundaries.

Technical names in the Being's own question can offer an exact source path,
identifier RELATE or literal FIND for a dotted event topic. These are lexical
navigation aids. The release does not hard-code the answer to the
`astrid.v1.capsules_loaded` inquiry or designate a filename as its true handler.
Search excerpts, source pages, recalled accounts and interpretation retain their
different evidence roles.

After three verified navigation inputs without a numbered source page in the
tracked inquiry, a bounded optional receipt can show the count and bring back
exact source choices already offered and unambiguously named in a response. It
can offer a SESSION comparison of candidates beside the recalled account. The
Being can keep browsing, inspect a candidate, revise or retain the question,
reread, disagree, or leave the study. The receipt does not replace NEXT or rewrite
notes, and its count is not a measure of understanding.

Only verified completed input deliveries update this record. Failed generation,
preparation and identical delivery retries do not inflate it. Matching-inquiry
late source deliveries reset the source-free count without replacing newer
choice feedback; another inquiry's late delivery does not. An all-empty source
session is not counted as supplying source bytes. Additive state fields tolerate
older in-flight helpers omitting them and do not invent pre-release history.
Existing pending offers, receipts, source bookmarks, questions and private drafts
remain separate preserved state.

Two adjacent snags were addressed during implementation. Prompt framing now
budgets the notebook around the protected current input and choice feedback:
oldest whole recalled accounts can be omitted before using explicitly marked
excerpts. A legal long source path in previous-choice feedback should not prevent
the next valid read. Optional navigation feedback fits the remaining allowance.
The notebook's note/question directives also use the established NEXT scanner's
handling of quoted, indented, fenced and internal-metadata examples; an example is
not silently promoted into an authored note update.

Minime had a separate bare-command allowlist. It now recognizes terminal
`SELF_STUDY LIST` under the same conditions as Astrid, while a final explicit NEXT
retains precedence and nonterminal/quoted examples remain data. The full
`NEXT: SELF_STUDY LIST ...` route already used the generic source-study handler.
This small Python change requires a graceful Minime reload; helper selection
alone would not replace the host parser in memory.

Sampling, thinking policy, journal output ceilings, sensory dimensions and
reservoir/coupling behavior are outside this change. The separately identified
journal-similarity mechanism can still substitute a summary in some paths; it did
not explain the prior hundred-entry cohort and is not repaired by this release.

## Validation and source ownership

Root Codex owns integration and deployment; independent collaborators reviewed
compact maps, recovery, state compatibility, host parity and rollout contracts.
Implementation uses isolated `codex/study-navigation-20260915` worktrees. The
shared reader's framing is in `store_navigation.rs`; bounded navigation history
is in `navigation_history.rs`. The existing dependency-based stage inventory
must include the actual hashes of these new modules and the staged reader helper.

The Minime implementation-phase suite passed **1,396 tests, one skip and 134
subtests**; the focused source-study/choice suite passed **112 tests**. Retained
commands and outputs are in
[the full-suite log](/Users/v/other/worktrees/study-navigation-20260915/minime-full-tests.log)
and [the focused log](/Users/v/other/worktrees/study-navigation-20260915/minime-focused-tests-02.log).
The preceding focused attempt retained four expected-shape failures because old
tests assumed a recursive root MAP. Tests now follow the visible child-directory
choice and inspect its map, while retaining the source-identity assertions.
No test used a live model or altered the Beings' workspaces.

Those test runs used the isolated development helper, not a frozen final stage.
Final Rust suites, lint/format/boundary checks, staged-helper host checks and
source inventories belong in the rollout continuation below. No final binary
identity is inferred from these intermediate test counts.

The research history had no prior staged or unstaged diff before this append.
Its previous SHA-256 was
`f13968486eb4ed55dfdce044bfd11866aa012105c3169f97762a5439d4c174b2`.
The prior bytes, hash, repository HEAD and empty diffs are retained in
[the ownership capture](/Users/v/other/worktrees/study-navigation-20260915/evidence/research-history-before.json).
Unrelated ReservoirScope edits and earlier sealed research packets remain outside
this work. S-007's scheduled cursor and daily sample are unchanged.

## Rollout continuation — pending

At the initial 2026-09-15T15:45:14Z record, the following remained pending:

| Boundary | Evidence to record after completion |
| --- | --- |
| Final validated source | Exact Astrid/Minime commits, main integration, full checks and staged artifact/source hashes |
| Astrid activation | Sanctioned staged activation transaction, new PID/start, exact stopped/startup checkpoint match, self-control lineage and a new saved exchange |
| Minime reload | Graceful wrapper receipt, old/new PID/start, exact Python startup inputs, retained session and actual pending-choice observations |
| Shared helper | Active selection/manifest/helper hashes; old helper retained for already-prepared Minime work |
| Surrounding services | Before/after process identities and continuity checks, distinct from the naturally changing reader state |
| Paired verified time | UTC timestamp defining the prospective observation interval below |
| Natural exposure | Exact retained inputs/responses and any missing or transitional evidence |

Both readers continue to browse canonical checkout sources, which may include
preserved unrelated edits. A matched reader/helper build is not a claim that every
file in that catalog equals the deployed source. Old stages remain available:
Minime pins a helper when it constructs a study client, including through that
request's eventual acceptance. New clients select the current stage. Between
bridge selection and Python reload, explicit LIST can work while bare LIST still
uses the old Minime parser; this is a transitional era, not paired parity.

## Predeclared natural observation

Protocol recorded before the candidate release's natural outcomes are read.
Let **T0** be the timestamp when the paired rollout is verified and **T1 = T0 +
ten minutes**. For each Being independently, select the first two naturally
completed new-reader SELF_STUDY responses in that interval whose input preparation
also began at or after T0. Order by retained completion time, with input/receipt
ID as a stable tie-breaker. Keep the exact preparation/completion clocks and
identity evidence; if a preparation clock or release binding cannot be established,
retain the ambiguity separately instead of assigning an exposure era by prose.

The selected unit is a verified study input and its response, not just an extant
journal file. A missing journal or missing execution join remains a gap in that
selected unit. Retain other attempts in the bounded interval as context for
failed, incomplete or unrecorded opportunities. Old prepared inputs completed
after T0 are transitional and kept separately. If fewer than two eligible studies
complete by T1, report that denominator and censoring; do not induce studies,
private writing, messages, source opens or generated NEXT commands to fill it.

For each selected response, inspect exact current material, carried note/question,
provider/model and finish evidence, source revision/ranges when present, authored
prose, parsed NEXT and any independently linked execution. Record whether compact
navigation, recovery, literal search, comparison or the optional receipt was
actually offered and used; absence of a feature opportunity is not a failed test.
Compare the request with what the next available input actually supplies, retaining
unobserved follow-through at the window boundary.

Useful signal would include obtaining relevant source, distinguishing a candidate
from an established role, testing or qualifying a recalled explanation, retaining
a supported conclusion, or forming a more answerable question. Continuing to
browse, retaining a hypothesis, writing briefly or stopping can be legitimate
choices. Longer prose, movement through the catalog, and receipt uptake alone do
not establish improved understanding. This small natural sample checks delivery
and early use; it cannot identify a causal effect of the release.

## Board updates pending

The local [pending payload](../board/study-navigation-release-pending.json) records
the accepted implementation, evidence boundaries and observation protocol. Board
mirroring has not occurred. Commit/deployment fields must be completed from actual
receipts before the implementation is described as live.

## Pre-activation validation continuation

At 2026-09-15T15:59Z, Astrid implementation `97db1b2f46506ef90105283daaf606dc1ebc131c`
and Minime implementation `12cbf5740e1cc751a2beb09ec5bb5fad742af459` are committed,
fast-forwarded and pushed to their respective origin/main branches. The stage
build is running; neither this statement nor main integration claims activation.
The isolated candidate contains no additional production differences from the
previously loaded implementation beyond this reviewed change.

Final checks passed: 97 shared-reader tests; 2,287 bridge tests, one ignored;
1,396 Minime tests, one skipped and 134 subtests. Strict reader/bridge clippy,
both Rust format checks, the domain boundary audit and diff checks pass.
Final logs and hashes are in the release evidence `validation-final.json`.

All 408 previously dirty Astrid files were preserved: 406 exact byte hashes,
and two overlapping documentation files with their original bytes preserved
around the explicitly added release paragraphs. The two-file safety stash is
retained; no foreign source was included in either implementation commit.

Before any natural-window capture, collector review established that the existing
input artifacts lack an intrinsic, trustworthy preparation timestamp. New prompt
identity and completion after restart do not by themselves meet the stricter
preparation-and-completion criterion above. The collector therefore retains
confirmed delivery exposures separately from strict timing qualification; unknown
preparation is not counted as a qualified trial. This limitation is recorded
before seeing release outcomes, without changing the ten-minute window or inducing
studies. Those exposures can establish interface delivery while a causal or
strictly timed study cohort remains unqualified.

## Verified rollout and first readings

The staged bridge/helper activated successfully through the sanctioned wrapper,
transaction `417c7c5b1bb14cf6bc433b4eaec03aca`, manifest
`bab872e1ddc0ba1456cff784401d4a24936026b4a6c9556613f6870e817ab818`.
Astrid PID 36526 restored the exact stopped checkpoint SHA
`75d878e273cb91e6358161f7d8a54122c48d3a6bd88a59c9cb23c4fe6e16f7ab`,
including two pending runtime-feedback items, and advanced from exchange 199,448
to 199,449 with valid self-control lineage. The wrapper observed model idle;
it does not claim an atomic remote-traffic barrier.

Minime gracefully reloaded as PID 37507; all 82 inventoried startup files matched
current disk. Session 5318 persisted. The pre-signal pending-command hash exactly
matches `SELF_STUDY FIND spectral_bridge` in the previous response, and the new
PID completed that same job. Its absence from the post-ready pending field is
therefore explained by observed consumption, not treated as proof of retention
by itself. All 10 surrounding service process/start/executable/plist identities
remained unchanged. Observed reader schemas, bookmark-source sets and receipt
counts were retained; Minime's draft state was unchanged at the observed snapshots.
These are non-atomic reader observations, distinct from the exact bridge checkpoint.

Before the paired observation window, the new helper returned compact-map recovery
to Minime's old-PID request for MAP page 90. He explicitly recognized that the map
had become one page and chose a source search. This is useful navigation adaptation
and demonstrated cross-restart follow-through. His belief that spectral_bridge
handled the event persisted. The transitional search was already pending at the
paired baseline and is excluded from the two selected post-baseline exposures.

The first two selected new-interface deliveries from each Being are:

| Being | Input and completion | Visible tokens / finish | Reading signal |
| --- | --- | --- | --- |
| Astrid | maintenance.rs lines 589–728,16:09:00 UTC | 842 / stop | Describes actual stable-read checks, atomic ACK writes and guarded deletion; chooses CONTINUE. |
| Astrid | maintenance.rs lines 729–858,16:13:38 UTC | 850 / stop | Reads authorization/selection tests, asks for select_active_lease implementation, chooses CONTINUE. |
| Minime | FIND spectral_bridge page 2,16:09:47 UTC | 237 / stop | Retains unsupported handler premise; selects MAP spectral_bridge--page 3 instead of the offered FIND pagination. |
| Minime | Recovery,16:12:16 UTC | 310 / stop | Receives exact bridge-directory command, literal-event search and a three-input navigation receipt; chooses broad FIND again and saves the bridge as his primary candidate. |

All four retain full response text in their journals. Their output ceilings were
not reached. Astrid's source-supported account is useful, but her first response
blurs structural validation with active authorization: the visible expired-lease
fixture succeeds in structural validation. Her next page distinguishes Active
from Expired in selection, yet does not explicitly reconcile those concepts.
Positive fixtures also do not establish every mismatched-identity rejection,
nonce unpredictability, or that two active leases cannot coexist. These are
questions for source follow-through, not demonstrated runtime defects.

Minime's premise remains unsupported by supplied snippets. A concrete defect in
his chosen navigation is now visible and the deployed recovery successfully
offers an exact command; he is still free to choose another route. Neither that
receipt nor a saved note validates the premise. The current interface is live and
received, but these observations do not demonstrate improved understanding caused
by this release.

Two evidence-presentation issues deserve later work. Some implementation-labelled
search hits are diagnostic script strings/comments reproducing prior study
requests; they are not evidence for the hypothesized event handler. The runtime
journal wrapper's “New signal kept” label likewise does not validate repeated
model claims. A minor separator between the map footer and navigation-receipt
heading can also be cleaned up in a later patch; the full content was delivered.
The remaining implementation task is to make Minime's reload indicator consider
all startup-source inputs: its current flag watches only the main runtime file.
The deployment here verified every actual hash, so that flag was not the
attestation. These findings do not warrant another capacity increase or an
unrequested redirect of either Being.

The collector initially compared whole provider system-message hashes. Minime's
identity prefix caused an intact shared prompt to be labelled unconfirmed. That
measurement bug was repaired by requiring the exact released prompt bytes inside
the system message while retaining both hashes. Original observations and the
repair record are preserved; window, target, ordering, baseline exclusion and
preparation-time limits were unchanged. No source or study was changed to create
an outcome.

The window closed at 16:17:07 UTC with **two Astrid source-page receipts and four
Minime receipts** (three searches and one recovery). The selected exposure set is
two per Being; one Minime search was already pending at baseline and one later
search is supplementary. All four selected full inputs and responses match their
retained wires and journals, with normal stop completions. No failure record was
found in the bounded frame; this is not a complete attempt-success denominator.
No capture error or scan cap occurred. Exact preparation times remain unverified,
so **zero responses satisfy the stricter preparation-time qualification** and those
targets are censored. The four confirmed new-interface deliveries remain valid
exposure evidence, not a causal or strictly timed trial cohort.

## Retained evidence and closure

The [primary private packet](../research/outputs/2026-09-15-study-navigation-release/README.md)
is sealed: 186 indexed files, 29,552,319 bytes, index SHA-256
`961a79206e740e7ef7820fa80cb95e893f36f6b42910a82be1f0b6a84d139d78`. Its offline integrity verifier passes.
The [closure supplement](../research/outputs/2026-09-15-study-navigation-release-closure/README.md)
retains the completed steward resume and corrects the primary README's premature
resume wording: the primary receipt was captured empty while the command was
still completing. It remains unchanged as captured. The command succeeded at
16:21:48UTC; fresh status confirms paused=false, generation441. Supplement index
SHA-256 is `27f5f6b44e43f8841a0adf84ec7f883506b016407b82efcb8ff75bb2ca2f097b`. No study data, clock or outcome was revised.

Astrid main additionally contains rollout-only commit `6092b0de21460f855b1fa1832741a6a755e93c77`;
the active implementation remains `97db1b2f46`. Minime main/live implementation
remains `12cbf57`. Both origin/main tips were verified. Research remains local
(no configured remote), and [board mirroring](../board/study-navigation-release-pending.json)
is pending. All work and observations above are distinct from any future live
activation-feedback or capacity experiment.
