# Natural studies after the graceful restart: real navigation, new evidence boundaries

September 8, 2026 evening · [S-008 protocol](../research/studies/S-008-follow-through-repair-protocol.md)
· [Living history](../research/histories/self-study.md)

**Minime completed fifteen shared-reader studies, thirteen beyond the two already
retained in the rollout.** He followed the requested capsule OPEN into its actual
file, moved into the manifest and WIT interfaces, and received nine new code pages
without repeating source bytes. Recovery from an unusable command and explicit
empty-search feedback both worked naturally. His notebook was present throughout.

**Astrid had no SELF_STUDY attempt in this window.** She did choose READ_MORE six
times, and eleven completed provider turns demonstrably received saved reading
pages. Those pages were prompt-overflow documents, not repository code. This
distinction matters both to understanding her journals and to deciding what to
improve next.

## Window, release and retained evidence

The window was fixed before inspecting new outcomes: **September 8,
17:42:46–18:14:00 PDT**, or **[September 9, 00:42:46Z, 01:14:00Z)**. Astrid's
verified start was 00:42:46Z, PID 84971, implementation `a202cfd`; Minime's was
00:44:54Z, PID 85778, implementation `1022244`. Each is bound to retained
activation/reload receipts and the shared release manifest, rather than inferred
from current Git HEAD. Thirty minutes of leading context is retained separately.

The [capture](../research/outputs/2026-09-08-study-after-follow-through/capture.json)
contains **871 records**, no reported capture errors, 32 primary-window actions
and 22 reading actions. One of those reading actions is a Minime INTROSPECT block
at 17:43:46, **before his reload**, from the old PID 54938. It must not be counted
as failure of the repaired route. After reload there were fifteen SELF_STUDY
actions and no source INTROSPECT opportunity in this window.

[Machine report](../research/outputs/2026-09-08-study-after-follow-through-report/report.json)
· [Verified outcomes](../research/outputs/2026-09-08-study-after-follow-through-final/outcomes.json)
· [All fifteen original journals and actual inputs](../research/outputs/2026-09-08-study-after-follow-through-final/studies.md).
The first two entries overlap HSS-07; they are retained for sequence continuity
and are not presented as new discoveries.

## Minime: access is turning into a connected reading sequence

| Natural result | Count / exact scope |
|---|---|
| Completed shared studies and linked terminal jobs | 15; all on Ollama / `gemma4:12b`, new PID 85778 |
| Exact provider receipts and saved journal matches | 15/15 |
| Current notebook included in actual input | 15/15 |
| New optional STUDY_NOTE / STUDY_QUESTION fields authored | 0 / 0; previous words are carried automatically |
| Source versus navigation | 9 source pages, 5 maps (including 1 recovery map), 1 search |
| Newly delivered code bytes / repeated code bytes | 36,094 / 0 in the retained-history comparison |
| Unique source files | 3, all Astrid-owned source |

The source sequence is concrete:

- At **17:48:50**, the requested `astrid/crates/astrid-capsule/src/lib.rs` arrives
  in full: 650 bytes, 24 lines. Minime recognizes its Manifest-First module layout,
  marks several inferred roles as “likely,” and asks for `manifest.rs`.
  [Original journal](../research/outputs/2026-09-08-study-after-follow-through-final/03-journal.txt).
  This is also a useful distinction from the legacy facade problem: a short module
  entry point now leads to a successfully opened implementation file.
- At **17:51:02**, `manifest.rs` supplies bytes 0–4,446 of 21,414, through part of
  line 113. Minime accurately identifies supplied `CapsuleManifest` fields and
  wants to continue. Assertions about automatic runtime discovery still require
  callers and runtime evidence beyond those declarations.
- At **17:54:20**, a later map response says the manifest defines structure while
  execution mediation remains to be traced. He asks for `astrid-capsule.wit` to
  inspect the host/guest contract. Seven pages then deliver bytes 0–30,998 of its
  34,842-byte revision, through part of line 805. A map detour preserves the source
  position; the next CONTINUE resumes at byte 12,918 rather than restarting.

This is a coherent development from kernel supervision to capsule structure to
interface definitions. It establishes successful access, continuation and useful
question-driven source choices. It does not establish that every interpretation
is correct, that declarations describe the active implementation, or that learning
persists beyond the supplied notebook. Minime still has not studied his own
repository's implementation in this window.

Follow-through is not one uninterrupted chain of obedience to every study NEXT.
Later non-study generations chose `SELF_STUDY MAN`, MAP and a spectral-tuning
search where the preceding study had requested CONTINUE. Those later choices
are present in the captured inputs/responses and action parent chain. They are
not evidence that the source reader randomly rewrote a command. The final search's
MAP request has no subsequent action before the cutoff; the horizon ends too
soon to classify that as a failure.

## Two repaired usability paths were exercised naturally

`SELF_STUDY MAN` is not a source identity or supported command. At **17:53:21**,
its completed study received a clearly labelled recovery map, the requested target
and a statement that no requested source bytes were delivered. The map retained
the partially read manifest's RESUME position. Minime used it to choose MAP kernel
and then the WIT source. This directly exercises the new recovery behavior;
the earlier invalid-target cases failed before any study generation.

At **18:13:35**, `SELF_STUDY FIND "spectral tuning"` received an explicit zero-match
result and shorter-query/map suggestions. Minime recognized the lack of an exact
match and chose MAP. This is an observable difference from the earlier ambiguous
search result, where he asked the operator to supply a missing list. The samples
and queries differ, so it is not an isolated causal comparison.

One usability caveat remains: the reader treats the outer quotation marks as
literal query characters. The response discusses the phrase as if searching for
its words. Preserve this as a lower-priority search-syntax question, not proof
that the unquoted phrase would have matched or that source is missing.

## A map response added unsupported facts; the peer then repeated one

The first-three-after selection was retained without swapping in interesting
examples. The following is an **additional exploratory counterexample**.

At **18:02:01**, generation `1788915699263-dcd36fd6` receives a system map plus
the previous source-response excerpt. It describes “the current segment” as if
the source page were still present, then adds `identity-context` at line 348 and
`auth-token` at line 355. Neither symbol occurs anywhere in the matching WIT
revision, nor in the current map/notebook input. Line 348 is a comment in
`identity-unlink-request`; line 355 declares `identity-create-user-request`.
[Original journal](../research/outputs/2026-09-08-study-after-follow-through-final/10-journal.txt)
· [Actual map input](../research/outputs/2026-09-08-study-after-follow-through-final/10-input.txt).

The previous source response had accurately named the identity resolution and
mutation types. Its carried excerpt ended before that part of the discussion.
The later map response continued the topic and filled in unsupported names.
This is consistent with a vulnerability when partial recalled prose is treated
as current code, but one episode does not identify the cause of the error.

At **18:03:58**, Astrid's dialogue generation `1788915770498-84971-128` received
the exact body of that Minime account, labelled “Minime wrote,” and repeated
`identity-context` in her response. The shared text also said verified delivery
did not establish understanding. This is a documented path from a source-study
claim into peer language, **not independent confirmation from a second reader**.
The [outcome probe](../probes/study_follow_through_outcomes.py) checks exact text
inclusion and the source counterexamples. It does not claim a propagation rate.

## Astrid: READ_MORE really read, but it read saved prompt overflow

The six READ_MORE actions are `handled`; that status alone would be insufficient.
The retained protected-delivery receipts add eleven unique provider request/body
joins, exact source-byte matches and completed responses on the new release.
Those responses also match retained journal text. Eleven pages are not eleven
READ_MORE decisions: foreground reading continues through provider turns.

The exact saved sources are:

| Saved prompt-overflow document | Delivered in this window |
|---|---|
| `context_overflow_84971_1788914807621896000.txt` | Entire 23,271 bytes, 6 pages |
| `context_overflow_84971_1788915723273931000.txt` | Bytes 0–20,000 of 47,891, 5 pages |

Both originals are retained in the [supplement](../research/outputs/2026-09-08-study-after-follow-through/supplement/manifest.json).
They contain omitted prompt sections: spectral context, visual rendering,
continuity and guidance. This is actual reading access, not a SELF_STUDY action
or proof that Astrid sought these documents specifically when saying READ_MORE.

The representation is costly: **20,274 of 43,271 delivered bytes are complete
ANSI control sequences**, counted conservatively within page boundaries. Six of
the eleven pages contain them. Two late pages each devote more than 3,800 of
4,000 bytes to such sequences. Astrid's corresponding responses discuss colored
blocks, punctuation and escape-code values. That is responsive to the material
we supplied; it should not be mistaken for reading implementation code.

The protected message says “chosen reading” and displays an opaque activity-source
digest, but not the source filename/type in that protected heading. Other prompt
context can contain overflow filenames; that does not identify the selected page
reliably. Pinned source confirms that generic wrapper and verbatim overflow-section
writing. Source-labelled, readable saved context is the clearest next usability task.

## Actionable follow-up and open observations

The [bounded proposal](../proposals/2026-09-08-study-evidence-labels-and-readable-overflow.md)
separates two changes:

1. **Make saved reading identifiable and readable.** Carry the actual source name,
   source kind, revision and position beside the protected READ_MORE page. Provide
   a plain-text view of terminal-rendered overflow while retaining its exact raw
   original and explicit view provenance. Keep source code and letters untouched.
2. **Make navigation and recalled notes visibly distinct from current source.**
   Both shared-reader adapters should expose the same current-turn kind and an
   explicit no-new-code notice on maps/search/EOF/recovery. Keep earlier words and
   their source links, and make returning to the cited source easy. Do not force
   a report format, score comprehension, or treat verified delivery as verified claims.

Neither proposal is claimed to eliminate false assertions. The retained map/peer
episode is the regression example for source provenance, and the overflow pages
are the regression examples for readable presentation. I would do those before
adding more notebook machinery. Optional note/question uptake and quoted-search
syntax remain observations to follow rather than reasons to add a new service.

Astrid's repaired study-authorship gate and Minime's repaired source INTROSPECT
admission had **no eligible post-repair natural opportunity here**. They remain
tested mechanisms awaiting direct natural use. No study is induced to fill that gap.
All fifteen studies lack a complete thirty-minute follow-up horizon at this cutoff;
immediate successful outcomes are visible, but later silence cannot be inferred.

## Reproduction and research status

The collector now accepts an explicit release profile and a frozen protocol file.
Old packets retain their original continuity-era interpretation. The report checks
source and response hashes; the supplement binds the two exact overflow originals
and deployed source used for the mechanism review.

```sh
/opt/homebrew/bin/python3.14 -B probes/study_sequences_verify.py \
  research/outputs/2026-09-08-study-after-follow-through/capture.json \
  research/outputs/2026-09-08-study-after-follow-through-report/report.json \
  --out research/outputs/another-verification.json

/opt/homebrew/bin/python3.14 -B probes/study_follow_through_outcomes.py \
  research/outputs/2026-09-08-study-after-follow-through/capture.json \
  research/outputs/2026-09-08-study-after-follow-through-report/report.json \
  research/outputs/2026-09-08-study-after-follow-through/supplement/manifest.json \
  --out research/outputs/another-outcome-replay
```

[Verification](../research/outputs/2026-09-08-study-after-follow-through-report/verification.json)
checks 871 captured records, 37 exact writing links and source reconstruction.
[Additional checks](../research/outputs/2026-09-08-study-after-follow-through-final/checks.json)
confirm that the earlier frozen report replays unchanged, a wrong era leaves all
fifteen studies unverified, an altered manifest is rejected and the supplemental
outcomes replay identically. The research suite passes **211 tests**.

This account is HSS-08. Research changes remain local and uncommitted. S-007's
daily ledger/schedule and all earlier frozen captures are unchanged. No live
system was changed, restarted, prompted or contacted during this sweep.

## Board updates pending

The Artifact connector remains unavailable and the prior sign-in barrier is
unresolved. [Pending board update](../board/study-after-follow-through-pending.json)
retains the completed sweep, findings, proposal and session log. No publication
is claimed.
