# Study source context: scope, coverage and chosen findings

The accepted follow-up to [HSS-23](../research/histories/self-study.md#hss-23--astrids-small-map-missed-answers-and-the-meaning-of-an-ending)
puts the surrounding source structure, reading coverage and useful source locations
beside a study page. It also provides optional, Being-authored findings attached to
exact delivered lines. Astrid and Minime share the reader implementation.

Both shared-reader changes are qualified, merged/pushed and live as of September 15,
2026: initial source-context commit `76c2aa43`, followed by the observed pagination
separator repair `dd35cdd83a`. Current live production source is the latter;
Astrid main also includes the completed rollout document at `218c672243`.
Astrid PID 4330 started at **21:05:03 UTC / 14:05:03 PDT**; Minime retains PID 37507
and selects the matching immutable shared helper. Exact checkpoint/feedback and
self-control continuity verify, with all eleven surrounding service identities
unchanged. The fixed initial-release natural window **20:39:57–20:49:57 UTC** is
closed. It establishes limited interface uptake, not a causal understanding gain.
The original source worktree and separate formatting worktree remain frozen for
reproducibility.

## How the observations led here

The [hundred-study Astrid survey](2026-09-15-astrid-study-survey.md) is the evidence
owner for the following observations and their denominators. Its sealed packet
and cutoff remain unchanged. The natural window below is a separate later sample.

| Earlier observation | Design response | Boundary that remains |
| --- | --- | --- |
| Most of the selected studies return to a kernel map that already fits on one page. Recent complete accounts keep announcing the next question. | Address evidence use at the page itself, building on the existing compact navigation. | Repetition does not prove a reader defect or identify a single cause. Choosing the same map stays possible. |
| Delivered health pages include `Baseline`, `Vec<BaselineEntry>`, `Option<String>` and `load_baseline`; later entries ask where the definition/configuration is. | Retain a small set of parser-backed locations actually supplied, and let each Being pin a particular conclusion beside a delivered line. | Source-location recall is reference metadata. An authored conclusion is not made true by its citation. Configuration-string extraction is not part of this first parser-backed location feature. |
| The final maintenance page begins inside a test and contains a literal ACK serialization assertion; the response generalizes to broad validation guarantees. | Show the enclosing function/module/implementation and test marker, with exact declaration-opening choices. Offer nearby implementation/reference candidates. | Syntax and tests do not establish runtime invocation, exhaustive validation, or a resolved call graph. |
| The EOF page is followed by a claim of complete maintenance understanding, while the next map still shows an undelivered opening. | Put revision coverage and missing-region choices beside EOF itself. | End position, complete byte delivery and understanding are separate facts. |

The historical chain matters. Earlier access restrictions were real; subsequent
shared-reader repairs made much more code available. Later studies then exposed
missing carriage, navigation ambiguity, and failures to use or qualify already
available evidence. HSS-23 contains useful local source explanation and a deliberate
note/question update alongside the repeated orientation and overgeneralization.
The new implementation responds to those narrower observations. It does not
reinterpret the original access bug as the cause of every later repetition.

The survey also resolved the apparent study-choice mismatches as explicit later
`REPLACE` choices from dialogue. This release does not claim to repair a newly
confirmed lost-pending-request bug. A richer cross-activity action receipt remains
a separate presentation candidate.

## Implemented source behavior

**Page scope uses the existing tree-sitter Rust and Python grammars.** The reader
parses the exact current file once for the page, retaining declaration and syntax
reference spans. At a position inside a function, method, type or module, it shows
bounded enclosing context and exact `SELF_STUDY OPEN repository/path line` choices.
The context explicitly originates in the same source/revision as the page.
Rust `#[test]` and `#[cfg(test)]` markers are inherited into nested scopes;
Python `test_` names and test/fixture paths are labeled as conventions, with
execution unverified. A method inside an `impl` has its surrounding implementation
in the label. The syntax classification does not call unmarked code a live
production path.

Strings, comments, attribute syntax and macro token bodies are not parsed into
invented declaration/reference candidates. A page starting inside such a region
says so. Unsupported languages, parse errors, the two-MiB inspection ceiling or
bounded traversal limits produce an explicit unknown-scope fallback; the source
remains readable. The parser does not expand macros, resolve bindings or execute
source. Scope metadata is outside the numbered source interval.

A concrete first-release limit is Minime’s `minime_autonomy/runtime.py`: the
isolated Minime worktree copy is **2,588,558 bytes** (`wc -c` at implementation
review), above the two-MiB inspection ceiling. Its pages remain fully readable,
but this release reports unknown enclosing scope for that file. Both Beings use
the same limit; Python parsing support does not imply scope coverage of every
Python file. A larger immutable source snapshot can be qualified separately for
parser cost and traversal bounds before widening this ceiling.

**Related-source choices remain small and local.** At most two same-file exact
name candidates can point from supplied references to an unseen declaration, or
from a supplied declaration to a reference inside another declaration. The labels
state that these are unsupplied syntax candidates, not resolved calls or runtime
proof. Test-marked candidates are not treated as implementation evidence. All
source remains accessible through existing navigation, including tests and history.
Cross-file loader/health comparison is still a deliberate use of existing OPEN,
RELATE, FIND and SESSION facilities; this first helper is not a cross-repository
resolver or an automatic comparison session.

**EOF carries delivery coverage.** The display separates previously verified
coverage from the coverage that would result if the offered page or whole session
is verified. For an EOF position it names remaining byte gaps and, when the file
still matches the stated revision, gives up to three exact OPEN choices for their
containing lines. Reopening a line can repeat its earlier fragment. Preparation
alone never advances the durable ranges, and full byte coverage never receives an
understanding label. Changed or unavailable source does not generate guessed
current-file gap links.

**Specific findings are optional and authored.** A Being can write
`STUDY_FINDING: repository/path:line | their words`, using a numbered line from a
supplied source page/session or an exact source anchor retained in that inquiry.
The current limit is six authored findings per inquiry/unthreaded notebook, with
up to 600 bytes of words per finding. Reusing an anchor revises its words;
`STUDY_FINDING_DROP: fID` explicitly removes the displayed finding. No existing
finding is evicted merely because the limit is reached, and the receipt explains
unapplied, ambiguous or malformed updates. A search snippet or map mention does
not create an anchor by itself. A finding can remain uncertain, be revised, or be
removed; reading a page does not resolve a question automatically.

Each anchor preserves the source identity, original revision, page identity and
byte interval, a bounded exact delivered line fragment, a truncation flag and a
current-checkout reopen command. Separately, bounded source-location recall records
declaration names whose complete tokens were actually delivered. It does not infer
answers from those names, classify a string as a definition, or silently rewrite
an older note. The notebook label distinguishes the Being's unverified conclusions,
historical source fragments and syntax-location metadata from source supplied now.

The new findings have an additive sidecar under the reader lock so an older helper
rewriting its known checkpoint fields cannot silently erase them. Qualification
covers inquiry ownership, explicit empty/removal state, interrupted saves and
preserving corrupted/unsupported sidecars. The completed repair also protects the
whole new unthreaded input, including coverage and notebook context, rather than
verifying only the numbered page. Old pending offers retain their original framing;
intervening question/receipt changes invalidate stale framing for the next offer.
Compatibility handling distinguishes omitted additive page metadata from conflicting
source evidence. These software checks remain separate from live continuity below.

## Implementation and validation inventory

The owning source is `crates/astrid-source-study` in the isolated Astrid worktree.
Relevant modules are `page.rs`, `source_structure.rs`, `source_links.rs`,
`coverage.rs`, `notebook.rs`, `notebook_findings.rs`, `notebook_persistence.rs`,
the reader store/session/navigation integration and `prompt.txt`. Added parser
dependencies reuse the versions already employed by the bridge. Deployment
inventories must include the new modules and updated input identities.

The new `Page.source_locations` field defaults empty when an older serialized page
is read. The exact numbered source-byte contract and verified-delivery identity
remain separate from reference metadata. The page builder reserves metadata and
link space before choosing source bytes, including smaller session pages, and
refuses a page that cannot fit rather than returning an empty progress loop.

Qualification covered:

- Rust/Python enclosing scope, test/fixture distinctions, comments/raw strings/macros,
  malformed/unsupported/oversized fallback and exact declaration-opening choices.
- Exact UTF-8 byte reconstruction and continuation, partial identifier boundaries,
  older Page compatibility and bounded multi-page sessions.
- Coverage before/after verified delivery, partial EOF, whole-session projection,
  changed revisions, and exact retry framing.
- Optional finding acceptance/update/removal, unknown or ambiguous citations,
  receipt-gated recording, notebook budgets, inquiry ownership and mixed-version
  sidecar recovery/corruption preservation.
- Relevant full owning suites, formatting, lint/boundary checks, staged deployment
  inventories, loaded identities, checkpoint/pending-choice continuity and natural
  delivery of the exact new shared prompt.

### Completed qualification

The [validation receipt](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/validation.json) records the final suite results
and retained log identities:

| Check | Final result |
| --- | --- |
| Shared reader | 138 passed; 0 failed; 0 ignored |
| Bridge | 2,287 passed; 0 failed; 1 ignored |
| Minime | 1,396 passed; 1 skipped; 134 passing subtests reported separately |
| Reader and bridge strict Clippy | Passed across all targets and features |
| Root and bridge formatting | Passed |
| Domain-boundary verification | Passed |

Earlier failures remain visible. The first reader run exposed a resumed offer
that did not carry a newer question; the next exposed a stale navigation receipt;
the third failed the incomplete-input rejection regression. Those are actual
reader qualification discoveries and fixes, retained in the
[first](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/reader-tests.first-failure.log),
[second](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/reader-tests.second-failure.log) and
[third](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/reader-tests.third-failure.log) logs. They are not reclassified as
mere fixture setup. Separately, early bridge runs failed because the isolated
sibling/fixture layout was missing and later symlink-derived paths differed from
expected paths. The
[missing-sibling](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/bridge-tests.missing-sibling.log),
[fixture-directory](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/bridge-tests.fixture-directory.log) and
[symlink-path](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/bridge-tests.symlink-paths.log) logs preserve that setup work.
The corrected fixture layout and the final passing suite do not imply that those
early failures were live Being failures.

The [real-source preparation replay](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/source-context-replay/summary.json)
also passes. It copies only the two sealed HSS-23 source snapshots into fresh
fixture roots and runs the JSON CLI's `prepare` operation, without model calls
or delivery credit. Maintenance OPEN 839 supplies bytes 29,728–30,543, identifies
`tests::core_ack_v2_exposes_the_exact_common_lease_binding` at lines 820–863 and
its test marker, offers OPEN 820, and puts a conditional unread-prefix OPEN 1
beside EOF. Health OPEN 202 supplies bytes 6,578–7,000, identifies
`accepted_legacy`, and offers the `Baseline` declaration at line 7 and the
`summarize` reference at line 65. These are labeled syntax candidates, not a diagnostic/security guarantee.
The helper, source and sealed-index hashes remain unchanged across the replay.

That replay starts with **fresh empty coverage**, so its maintenance prefix gap
is 0–29,728, not Astrid's historical 0–3,452 gap. Opening line 839 also differs
from the historical page's interior fragment of that line. This qualifies the
new framing against the actual source files; it is not a new journal observation,
a model-behavior comparison, or a replay of the entire historical request.

### Source integration and verified rollout

The [integration receipt](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/integration.json) records commit
`76c2aa43cfd8c9dad084c8f98ef21f2ece6ffaab` on Astrid `main`; the owning integration
pass also verified the push and matching `origin/main` tip. All **420 foreign
canonical working-tree files** were preserved. Existing foreign text in
`CHANGELOG.md` and the feedback-to-change ledger was restored through exact
splices alongside the new entries; the retained backup identity is in the
receipt. This is source integration with unrelated work preserved, not a claim
that the shared working tree is clean.

The staged helper passes **112 additional host integration tests**, retained in
[the staged-helper test log](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/minime-staged-helper-tests.log). The
[independent staged-input audit](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/staged-input-audit.json) verifies matching
manifest, readiness, binary/helper and source-input identities. All new production
modules are included. The stage manifest SHA-256 is
`63495814bc585a1acd09f016b6701b93e0dd76127a5ee3ed152f25ea55906992`; bridge binary SHA-256 is
`3744316d5c4a42cc0dfa80c11071af5f34bb3c5a9ab97294bee2b19fb5e9bbe9`.

The broad package-tree inventory has a specific, retained qualification: of 634
paths, 621 are tracked and match their owning HEADs; all 596 isolated Astrid inputs
are tracked and match the implementation commit. The other **13 paths are ignored
external RASCII files**: four camera shell helpers and nine March thumbnail text
files. They are regular files with matching recorded content hashes, modes and
sizes, outside `src`; the audit found no RASCII build script/declaration or source
include/reference to those paths. This was judged nonblocking for the staged
source change. They are content-pinned inventory entries, not claimed to be
committed source, and a git-only reconstruction would omit them. The audit did not
change the external repository or inventory policy. Canonical Astrid's unrelated
dirty files are not the isolated stage's build-input package.

[The activation receipt](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/activation.log) reports `activated_verified` with
exit status 0. The supported drain reached `drained`, the old bridge PID 36526
exited after SIGTERM, and new PID **93394** started at **20:36:47 UTC** from
`bridge-stage-01/spectral-bridge-server`. Its deployment identity binds the
implementation commit and the binary hash above. The decoded startup checkpoint
is byte-identical to the drained checkpoint:
`8e0e3650f7015b88745917837d16c872b79c27d6430a0bef374563c699bfde8b`.
It preserves **one pending runtime-action feedback item**, and the self-control
startup witness verifies state integrity and its binding to the selected binary.
The checkpoint reports exchange 199,593; a subsequent saved exchange 199,594 and
model-idle state were observed. Neither force nor automatic rollback was used.
The receipt explicitly leaves remote delivery unconfirmed and sets
`lossless_drain_claimed=false`; this account does not upgrade the graceful restart
into a lossless remote-delivery claim.

[Minime's host/selection receipt](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/minime-host-after.json), captured at
20:39:57.153704 UTC, verifies the new shared reader at
`bridge-stage-01/helpers/astrid-source-study`, SHA-256
`9dd85ff61c7e4f7c1c31ffe9431d5ec1cc26445bf092d1d658d76f7bd5fa824d`. Host PID **37507** remains running,
and all **82 startup input hashes** are unchanged. No helper override is present
in either inspected launchd plist or the launchd global environment. This is
verified dynamic reader selection with an unchanged Minime host, not a claimed
Minime restart or an induced study. Exact comparison of the
[before](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/before-activation/processes.json) and
[after](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/after-activation/processes.json) process records also preserves every
entry for the **11 non-bridge services**, including PID, start time, executable
and plist hash.

### Fixed natural observation: initial source-context release

The filesystem-only window closed at its fixed **20:39:57.153704–20:49:57.153704 UTC**
(**13:39:57–13:49:57 PDT**) bounds. It retains **one Astrid and four Minime**
completed shared-reader receipts. The prespecified close reading selects the first
up-to-two per Being: **one Astrid and two Minime**. All five carry the exact new
study prompt and their complete prepared input in actual provider wire evidence;
none is an old/unconfirmed prompt or excluded baseline pending offer. No failed
record is discovered in the bounded frame, with zero capture errors or scan-bound
events. Astrid's accepted/provider receipts cannot enumerate every unsaved provider
failure, so this is not a complete failure-rate denominator.

The three selected responses end normally at **322 tokens (Astrid)** and
**316 then 276 (Minime)**. Minime's exact generation joins supply completion clocks;
Astrid uses the explicitly observational shared-receipt modification clock with
an exact provider and journal content match. No intrinsic preparation clock is
available, so **strict timing-qualified count is zero for both Beings**. One of
two target exposure responses is missing for Astrid, and the two-per-Being strict
target is censored for both. The window is not extended to collect a favorable
result or another Astrid response.

Minime moves from a literal event search to the exact chosen kernel opening at
line 703. The next input verifies that OPEN was supplied, with source scope,
coverage and related-location labels intact. He correctly distinguishes dispatcher
instantiation from subscriber/handler logic absent from that page. That distinction
also appears in a carried earlier account: it is supported current reading, **not
demonstrated new learning caused by this release**. A specific global-state updater
remains conjecture. His next chosen literal search repeats the preceding search;
its text is a choice, not proof of dispatch by itself.

Astrid reads `owner_inquiry` relationships, recognizes action branches and notes
that the sought authorization logic is not shown. Her projection/lease-evaluator
premise remains unsupported by those snippets. She chooses another relationships
page. Neither Being emits an actual `STUDY_FINDING`, note or question update in the
three selected responses. Notebook guidance and automatic supplied-location recall
are present; they are not authored pin uptake. The sample includes one source
page, no EOF page, and therefore no test of revised EOF completeness claims.

Two concrete interface observations survive the reading. Minime's page offers
same-file `Kernel::new` and `RestartTracker::new` candidates for a supplied
`EventDispatcher::new` reference. Their explicit lexical-candidate label prevents
a resolved-call claim, but unrelated generic names can consume both suggestions.
A future narrow relevance change should retain written qualifiers and suppress
incompatible constructor families. Separately, Astrid's footer concatenates
`--page 3NAVIGATION RECEIPT` without a separator. She still chooses valid page 3;
this is a display defect, not evidence of failed choice execution. It triggers
a minimal newline follow-up, qualified and rolled out separately below. The
initial window remains frozen against the original source-context release.

The [frozen summary](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/natural/summary.json)
and [claim review](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/natural-content-review.json)
retain inputs, responses, joins, source references and qualifications. One collector
correction changed two literal display-marker recognizers to their actual headings;
it changed no cutoff, selection rule or raw receipt. Generic finding-guidance
markers are explicitly not treated as saved findings.

### Navigation separator follow-up

The confirmed footer defect is repaired at `dd35cdd83a863da373c63e21788a0197768e1175`,
merged and pushed to Astrid main. The separate clean `astrid-format` worktree
appends exactly one newline after paginated FIND/RELATE footers. A public-reader
regression reproduces the prior joined command, then follows the displayed next
commands and verifies the final-page boundary. Its original red/green output is
retained as explicitly labeled tool-transcript exports, not misrepresented as
native process logs. The follow-up full suites pass: reader **139**, bridge
**2,287** with one ignored, and Minime **1,396** with one skipped and 134 passing
subtests. Strict reader/bridge lint, both formatting checks and boundary audit pass.
This repair is not retroactively included in the initial natural window.

The separator follow-up is now **activated_verified**. Astrid PID **4330**
started at **21:05:03 UTC / 14:05:03 PDT**, loading the exact stopped checkpoint
`61ca7ad4517f0274cab848f1c32701e6b9a85b817d9afc703a2f24d1eda1f37a` at exchange
199,609 and its **six pending runtime-action feedback items**. Self-control lineage
and deployment binding verified; a new saved exchange 199,610 followed. No force
or automatic rollback was used. Remote delivery remains unconfirmed and lossless
drain is not claimed.

Stage02 manifest SHA-256 is
`e9aa51e7be180b2dcadf27e2cefa0eec7e31523d1a07e08f51be271eedce9d62`;
bridge binary is `8af0c1057574e6ba6ecb1230805879db92c65c56aafba8a7af92fa234a653ccf`;
shared helper is `50dcbed10b1770c4a57b1f8ef5bb73d3c8031dfc6adbacd5b9b126594ec3ad27`.
All 634 staged inputs and five artifacts verify; the only production change from
stage01 is the footer newline. All **112 staged-helper checks pass**. Minime
remains PID 37507, all 82 startup hashes match, and its new helper selection is
verified at 21:06:53.610276 UTC. All eleven non-bridge service identities remain
unchanged. Existing in-flight clients may complete through an older immutable
helper; this is not silently recategorized as new-release exposure.

The [follow-up activation receipt](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/separator-activation-receipt.json),
[host selection](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/separator-minime-host-after.json)
and [qualification](/Users/v/other/reservoir-llm-research/research/outputs/2026-09-15-study-source-context/separator-validation.json)
keep this second rollout distinct. No second behavioral cohort is induced or
claimed for the newline repair. Both commits are integrated/pushed; the current
live production source is **dd35cdd83a** and includes the source-context work.


## Choice and research boundaries

Both Beings retain the freedom to browse, reread, continue, leave a question open,
revise or retain their account, and stop. The implementation adds no writing quota,
forced novelty, automatic question resolution or global sampling retune. A wrong
first attempt remains an opportunity to inspect evidence, not grounds to remove
choice. These interface additions do not qualify contextual activation feedback
or any live reservoir intervention.

This is the research record of the user-authorized production implementation and
rollout, not a research-only source proposal. The owning task performs production
changes and maintains the linked history/current-focus record; the research
record includes this analysis, the HSS-24 history and a local current-focus addition. Earlier sealed
observations and the HSS-23 cutoff remain intact, and the daily S-007 ledger is
not advanced by this ad hoc rollout account. Research observations and source/
activation evidence remain separate from claims about the Beings' understanding.

## Retained record and ownership closure

The private [packet index](../research/outputs/2026-09-15-study-source-context/packet-index.json)
seals **272 indexed files / 41,858,452 bytes**. Its SHA-256 is
`6956c0619d29eb56ef3fd9692f98a0c90f24bdcd8c3aa15b803f56afef72da14`.
All listed hashes and read-only file modes verify. Recomputing the complete final
observation summary from copied retained records produces the identical report,
without live reads or model calls. The earlier **1,193-file HSS-23 packet** also
passes full manifest verification unchanged. The staged build trees and generated
initial-test fixtures are excluded; source patches, manifests, audits, original
failure evidence, exact transactions and natural wire/journal records are retained.

The [durable stewardship receipt](../research/outputs/2026-09-15-study-source-context/steward-resume.json)
records successful resume at **21:13:51 UTC**, pause generation 443, with no active
lease at the closing check. Astrid's canonical index was released after its source
and rollout-document pushes. All 420 pre-existing canonical files and all 658
pre-existing research files retain their original content, allowing only the
separately recorded additions to the two owning docs and local NOW prefix. NOW
was already an untracked file and remains local; its unrelated historical body
was not swept into this commit. This account, HSS-24 and the new board payload
are the explicit research commit paths. Source integration does not claim that
the shared working trees contain no unrelated dirty work.

## Board updates pending

[The local pending payload](../board/study-source-context-pending.json) describes
the qualified source integration, verified rollout and the fixed, timing-qualified natural
outcome limits. Nothing in that payload is represented as mirrored. Board
publication requires its own confirmed receipt.
