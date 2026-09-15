# Source-study observation links

September 8, 2026 · Research-side proposal; no live implementation authorized here.

**Afternoon status update:** The separately authorized continuity release adds
shared navigation receipts and a carried study notebook. The statement below that
navigation has no wire receipt describes the initial S-007 era. [S-008](../research/studies/S-008-study-to-follow-through.md)
now reads those receipts, older Astrid protected-delivery records and exact
provider-attempt joins without changing the live reader. Explicit shared-reader
generation/job IDs and a unified failed-attempt observation remain proposal work;
do not reimplement navigation receipts as if they were still absent.

The [S-007 initial observation](../analyses/2026-09-08-source-study-fidelity.md)
uniquely joins fifteen source pages to generations by exact request and response
text, model identity and system-prompt hash. The delivery record itself has no
local timestamp, job ID or generation ID. Navigation pages have no analogous wire
receipt, and the successful source-delivery store cannot supply a denominator of
failed or rejected page opportunities. Repeated identical content could eventually
make reconstruction ambiguous. These are evidence limitations, not observed failed
reading or an established defect in navigation.

## Smallest change

Keep the existing delivery verifier and private storage. Add a separate observation
record referencing its receipt instead of changing bookmark semantics. In Minime
`37ed8b7`, hooks are `minime_autonomy/source_study.py::SourceStudyPrompt.post` and
`accepted`, plus the runtime dispatch acceptance call around line 54575 and
`minime_autonomy/generation_record.py`. On the shared side, see
`crates/astrid-source-study/src/store.rs::delivered` and `verify_wire`.
Resolve line numbers again in the owning checkout before implementation.

The generation dispatcher already knows job, generation and attempt identity.
At preparation/dispatch/terminal outcome, retain page ID if present, navigation
kind otherwise, those identities, local UTC event time, provider request/response
hashes, source/revision/range, native stop reason, and a link to the existing
artifact. Preserve unknowns and write/persistence errors. Record rejected/no-output
attempts without advancing any bookmark. Extend ordinary generation metadata to
carry native stop reasons for navigation and failed attempts too, reusing the
completion proposal from September 7. Avoid duplicating raw prompts in another
store or introducing a per-page model judgment.

## Acceptance and rollback

Offline fixtures should cover repeated identical request/response text under
separate attempt IDs; a source-page success; navigation-only success; timeout;
length-truncated response; missing page after adaptation; write failure; retry;
and a crash between receipt and bookmark persistence. Require unique joins where
identity exists, explicit unknowns where it does not, unchanged page advancement,
unchanged authored prose, bounded record size and retention. A shared-reader parity
fixture should exercise both being adapters without a live model or workspace.

This adds steward-side evidence and no prompts, controls or compulsory study format.
No being message or live study is needed for these tests. If a later design would
expose the records in being prompts, describe that change for Mike separately.
Roll back by disabling the observation writer; retain valid historical receipts and
leave reader behavior unchanged. Owning implementation and live activation remain
separate from completion of this proposal.


## September 10 addendum · purpose and journal disposition

[S-007 day 2](../analyses/2026-09-10-source-study-fidelity-day2.md) supplies new
bounded cases for this existing proposal. Of 553 records in the filename
`self_study` lane, 31 are private WRITE responses; exact job action text identifies
them. Four source-study journals contain a similarity-gate summary rather than
the full generation response, although their generation artifact link says
`match: content`. Neither case should be counted as missing source delivery or as
a full response preserved in a journal.

Proposed owning addition to `minime_autonomy/generation_record.py` and the existing
source-study/writing finalizers: retain an explicit semantic purpose alongside the
compatible lane, plus journal disposition (`full_response`, `similarity_summary`,
`not_written`, or `unknown`). A summarized artifact link should state its
transformation and exact retained span, where available, rather than implying full
response identity. Keep the generation response and journal artifact separately
addressable. This is evidence metadata, not a change to authored prose, similarity
policy, private writing, navigation, or the Being's choices.

Use the 31 writing responses and four summaries as offline fixtures; require
unchanged source-study counts and exact output text, explicit purpose for private
writing, and rejection of a full-response match for summarized journals. Include
the day's three failed generations: two lack retained raw wire evidence; the later
one has an existing bounded diagnostic with native `length` and full request/response
hashes. Reuse that diagnostic rather than duplicating a failure store. Preserve
missing historical wire data as unknown. Resolve finalizer line numbers against
the owning revision before implementation; day 2 retains six relevant source-input
hashes for each of its three newer release schemas.

No live implementation, intervention, message or source-reader invocation is part
of this addendum. Rollback would disable only new metadata writes and retain older
records. Any future Being-facing exposure needs a separately described decision.


## September 13 addendum · prose transformation and recovery episodes

The separately preserved [day-3](../analyses/2026-09-11-source-study-fidelity-day3.md),
[day-4](../analyses/2026-09-12-source-study-fidelity-day4.md) and
[day-5](../analyses/2026-09-13-source-study-fidelity-day5.md) packets add a concrete
journal-transformation case. Generation `1789124828466-c595c114` discusses parser
normalization and includes a literal `</s>` inside prose. Its linked journal removes
that one token, while the generation artifact link says `match: content`.
The transformed response is an exact contiguous journal substring; it is not the
original full response. Seven further day-5 journals are similarity summaries.

Extend the existing metadata proposal at the same generation-record and journal
finalizer hooks with `transformed_response` disposition, named transformation,
original/transformed hashes and retained spans. Keep raw generation text immutable.
An offline fixture should use this literal token inside a quoted code discussion
and distinguish authored content from actual transport delimiters. Do not broadly
strip tokens in the research matcher to manufacture full-response identity.
Resolve finalizer line numbers against the owning release before implementation.
The existing rollback and no-prompt-change scope apply.

Recovery is a separate research lead, not another unimplemented claim about
missing receipts. Post hoc counts retain 128/174/87 recovery responses in the three
daily windows. Day 4's fixed trio infers a directory exists from a no-catalog-entry
result; day 5 ends with 17 repeated requests using `astrid_capsule` where verified
filesystem paths use `astrid-capsule`. Current inputs already state that no source
was supplied and offer choices. Before proposing more prompt changes, inspect
whether the relevant MAP and OPEN paths expose the existing catalog-backed
alternatives, and whether a later chosen valid path changes the saved finding.
Any candidate should preserve the original query, provide exact optional paths
with a stated catalog basis, and keep nonexistence/unknown distinct from “directory.”
No forced navigation, new model judgment, live intervention or Being message is
part of this research addendum.


## September 14 addendum · supplied correction versus authored choice

[S-007 day 6](../analyses/2026-09-14-source-study-fidelity-day6.md) resolves one
specific question from yesterday's recovery lead. In the fixed first-three
sample, the exact hyphenated OPEN candidate is already in the verified input:
`astrid/crates/astrid-capsule/src/capsule.rs`. Minime explicitly mentions an
underscore/hyphen mismatch, calls the unchanged underscore path “corrected,”
and requests that unavailable spelling again. These are not missing-candidate
fixtures. The previous-response notebook also carries the incorrect spelling;
retention alone does not establish that it caused the repeated choice.

The predeclared boundary follow-up retains 17 recovery responses before the
prior cutoff and 21 after it. The last response in that 38-response sequence
uses the correct hyphenated NEXT; the next observed study verifies actual source
delivery at September 13 19:11:04 UTC. Preserve the successful choice and its
accepted page beside the earlier failures.

The separate exploratory census finds 337 recovery inputs among 666 completed
source-study generations. Its longest same-action run is 175 MAP spectral_bridge
requests. The first/last endpoint inputs show a generic recovery map with no
catalog entry for that query; the last response chooses MAP astrid, and the next
verified input is a repository map. This is successful navigation recovery,
not yet proof that the requested implementation was found.

Next owning qualification should distinguish: (1) exact OPEN candidate supplied
but transcribed incorrectly; (2) a MAP query lacking an exact catalog target;
(3) a later correct choice and verified source/map outcome. Use these retained
inputs and authored choices as deterministic regression fixtures for the existing
candidate/choice metadata. A candidate improvement to evaluate separately is an
optional short selection handle bound to a particular retained catalog candidate,
so the Being can choose it without reproducing a long path. It must resolve to the
same exact candidate and report that identity; this is not a proposed automatic
rewrite of arbitrary underscore paths or a compulsory redirect.

This remains a qualification/design lead. The daily observation has not tested
a new selection interface, edited the source reader, changed a prompt, called a
model or sent anything to a Being. The existing owning proposal's source-hook
review, isolated acceptance tests and metadata-only rollback remain applicable;
any Being-facing interface trial needs its own concrete design and authorization.


## September 15 addendum · account for the deployed navigation era

The [day-7 account](../analyses/2026-09-15-source-study-fidelity-day7.md) independently retains activation evidence for the separately implemented compact-catalog/navigation release. Minime commit `12cbf5740e1cc751a2beb09ec5bb5fad742af459`, Astrid build source `97db1b2f46506ef90105283daaf606dc1ebc131c`, and manifest `bab872e1ddc0ba1456cff784401d4a24936026b4a6c9556613f6870e817ab818` define this new era. Minime starts at September 15 09:06:25 PDT. Earlier recovery fixtures remain evidence of the older interface; do not describe compact catalog/history separation or current recovery choices as unimplemented without checking this release.

The day-7 fixed sample shows successful catalog pagination alongside a recalled module account attributed to the current map. The first subsequently verified source response correctly recognizes types and utilities but still carries an unresolved handler expectation. These are distinct fixtures for provenance, exact navigation and interpretation. Twenty-four source-page opportunities occur in the 57 new-era generations; the observer has not isolated a navigation-change effect.

The [first-week synthesis](../analyses/2026-09-15-source-study-fidelity-week1.md) retains 3,704 completed source studies, four failed generations, five early receipt gaps and explicit journal summaries/transformation. Its reproducible rollup can provide the same evidence stages to later flywheel review: journal concern, accepted change, verified release, eligible natural opportunity, then bounded outcome. No one stage stands in for the next. Further live changes remain proposals in this repo; the existing metadata scope and rollback apply. No new source change, model call or message was made here.
