# Study continuity now supports a correction—and repeated mistaken conclusions

Mike asked whether the later studies show improved understanding, beyond the
navigation uptake reported at startup. There is a credible local example:
Astrid replaces an incorrect saved explanation after reading contrary code, then
connects the revised explanation to a relevant rejection test. Minime now uses
comparison sessions and updates his notebook, but repeatedly carries forward an
incorrect explanation of the same dispatcher and eventually declares it complete.
The new continuity mechanism works; a general improvement in understanding is
not established. Preserving an answer also preserves its mistakes.

## Window, denominators and evidence

The [prospective follow-up scope](../research/studies/S-008-study-context-followup.md)
freezes September 9 **13:34:05–15:17:00 PDT / 20:34:05–22:17:00 UTC**, continuing
the [HSS-14 startup window](2026-09-09-study-context-and-thinking.md).
Every completed response was screened chronologically. The declared closer reading
includes first/last responses, authored note/question changes and the definition
OPEN queued at the previous cutoff. These are related turns in sustained inquiries,
not independent learning trials. No model call or Being intervention was induced.

The standard reporter selects attempts by start time. To close the previous
window's pending work without losing it between windows, a separate offline view
retains **two incoming attempts**, one per Being, started before 13:34:05 and
completed within this window. That produces **64 completed studies by completion
clock: 29 Astrid and 35 Minime**. The main start-time cohort has 65 attempts:

| Main cohort | Astrid | Minime |
|---|---:|---:|
| Started in the window | 29 | 36 |
| Completed, accepted, exact input and writing verified | 28 | 34 |
| Failed without accepted study delivery | 0 | 2 |
| No completion before cutoff | 1 | 0 |
| Complete immediately previous visible response supplied | 28/28 | 34/34 |
| Older responses supplied, in addition to previous | 1–3 | 1–3 |
| Authored finding updates | 3 | 21 |
| Authored question updates / clears | 1 / 2 | 12 / 7 |
| SESSION choices / completed source sessions | 0 / 0 | 5 / 4 |

These counts exclude the two incoming attempts. A question clear is not proof
of resolution. One of Minime's five SESSION choices is followed by an associated
MAP action; the retained parent IDs establish ancestry, not which intermediate
writing supplied that action. No parser defect is inferred from this mismatch.

The [frozen capture](../research/outputs/2026-09-09-study-context-followup-capture/capture.json)
has SHA-256 `82b369c73e86687bbcd9276b2ac74d4e46f91afdde4b5541230c3c7b44e6646e`.
The [probe](../probes/study_context_followup.py) produces
[verified counts and links](../research/outputs/2026-09-09-study-context-followup-report/verified-followup.json),
[incoming attempts](../research/outputs/2026-09-09-study-context-followup-report/carry-in.json),
and [complete selected inputs, responses and original journals](../research/outputs/2026-09-09-study-context-followup-report/case-evidence.md).
The capture has no collection errors; the main report has no invalid accepted
receipts or receipt-join issues. The trailing Astrid completion after cutoff is
censored, not included in the interpretation.

## Astrid: an answer changes when contradictory source arrives

At **13:54:57**, after dispatcher lines 376–491, Astrid saves:

> The `EventDispatcher` does not perform pre-dispatch authorization checks; it delegates authorization to the `capsule.invoke_interceptor` method…

At **13:58:12**, the next source page includes `find_matching_interceptors` and
`interceptor_accepts_caller`. Her input still contains the earlier incorrect note
and the complete previous response. She writes:

> This provides the "gate" I was looking for—the pre-dispatch authorization check that happens before an interceptor is even invoked.

She replaces the note with host caller filtering followed by possible capsule
validation and asks how a `wasm_capsule` could access a Private action. At
**14:12:39**, a later page supplies the relevant negative test. She identifies
the rejected `wasm_capsule` caller and links it to that question, updates the note
again and clears the question. These are verified, separately generated responses,
not a replay of saved prose.

Source check: [the exact dispatcher revision](../research/outputs/2026-09-09-study-context-followup-report/dispatcher.rs)
calls the matching/filtering routine before dispatch (225–235), invokes
`interceptor_accepts_caller` while gathering matches (530–558), and explicitly
rejects wasm producers for Private interceptors (563–601). The test at 826–888
does exercise rejection. This supports the specific change from “no pre-dispatch
check” to “host caller filtering precedes invocation.” It does not prove the
whole kernel authorization model. Her broader host/provider mediation account
is an inference; the displayed negative test alone does not demonstrate an
end-to-end mediated success path. Its additional identity pins also limit which
individual rejection clause the test isolates.

Case IDs: `astrid:provider-1788987173384-7538-116`,
`astrid:provider-1788987397592-7538-131`,
`astrid:provider-1788988252370-7538-200`. This is evidence of local revision and
cross-page use, not a causal estimate of the latest release's benefit or a claim
that every sentence in those entries is correct.

## Minime: useful affordances, but the explanatory model becomes entrenched

At **13:40:53**, Minime receives an actual two-page SESSION: dispatcher
360–406 and 192–241. He saves that the single-match path provides immediate
execution and “avoids the overhead of a spawned task and a loop,” then clears
the question. The delivered first page visibly includes `tokio::task::spawn`
and the worker's receive loop. The second page is an outer dispatch caller, not
the multi-chain implementation. Recency selected two pages but did not establish
that they were the right comparison.

At **13:51:52** and in subsequent notes, he interprets the special local-provider
failure-reporting checks as an alternative authorization path. At **14:12:57**
he saves that `dispatch_single` bypasses `interceptor_accepts_caller`. That exact
note reaches later inputs with a verified origin receipt. Later sessions repeatedly
compare test/mock spans at 943–1002 and 1057–1104; these are not the two dispatch
implementations. By **15:07:17**, he says the inquiry is complete, while still
describing Private as a soft policy ignored on a local fast path.

The exact same source revision contradicts the central claims:

| Saved or repeated claim | What the supplied source actually implements |
|---|---|
| Single-match execution is immediate and avoids a spawned worker | `dispatch_single` creates/reuses a per-capsule queue and persistent spawned receiver; `try_send` enqueues work (360–449). |
| The local-provider topic selects the single-match path | The branch tests `matches_owned.len() == 1` (270–284). |
| That path bypasses the caller/Private filter | `find_matching_interceptors` filters callers before either dispatch branch receives its matches (225–235, 530–601). |
| The exact local-provider failure predicate authorizes invocation | The predicate is reached in invocation-error handling and decides whether a particular error message can be emitted (413–520). Failure to emit this message is not dispatch authorization. |

Case IDs include `minime:1788986367390-065f016e`,
`minime:1788987045427-c8224461`, `minime:1788988306807-cb3bd427`,
`minime:1788991557768-605b0113`. The incoming definition read at 13:35:21 already
contains the incorrect immediate-execution explanation. This is not a claim
that the latest release introduced it.

The historical contrast is especially useful: the selected **12:20 pre-change
entry correctly distinguished a persistent worker from a new chain task**, but
its useful conclusion was lost in the old 700-byte carried excerpt. HSS-14 fixed
that truncation in an exact replay. This later natural sequence shows that complete
carriage is necessary support, not sufficient protection against a mistaken
interpretation. More notes, source coverage and closed questions cannot stand in
for checking what those notes claim.

## Astrid's next inquiry runs into a recoverable path error

From **14:49:25 to 15:14:55**, eight consecutive completed studies supply maps or
recovery maps while Astrid tries to enter the bridge runtime. She first asks for
`astrid/capsules/spectral-bridge/src/runtime/command_dispatch.rs`, repeatedly tries
`.../src/runtime/core.rs`, and eventually maps `.../src/runtime/` itself.

The real paths include **`src/action_continuity/runtime/`**. These files are in
the catalog. This is a missing parent directory in the requested identity, not
an access restriction. The current recovery returns the root map plus generic
FIND guidance. `requested_source` only offers spelling alternatives when complete
paths match after replacing underscores with hyphens; it does not suggest a
catalog match with the same filename under a different parent.

An [isolated prepare-only replay](../research/outputs/2026-09-09-study-path-recovery/recovery.json)
with the selected immutable reader reproduces the behavior: wrong OPEN has no
exact nearby candidate, `FIND command_dispatch` returns the correct full path,
and opening that path succeeds. [The probe](../probes/study_path_recovery.py)
writes only research state and makes no model calls. Offer bounded exact catalog
candidates on missing paths; retain the Being's choice rather than silently
opening another file.

## Output room and a diagnostic gap

All 62 accepted main-cohort requests allow **4,096 output tokens**. Minime's 34
successful responses use **164–866 tokens, median 510.5**, with a 32,768-token
context setting and thinking explicitly off. Astrid's backend returns unavailable
zero token counters, so a comparable output-token distribution is not inferred.
These are different natural materials from the earlier nine-entry sample, not
a matched length comparison.

Two Minime map attempts fail, at 14:20:34 and 14:27:05. Each generation record
reports HTTP 200 and `eval_count = effective_num_predict = 4096`, followed by a
`RuntimeError`, no linked artifact and no retained visible response. Elapsed
times are 339.6 and 313.885 seconds against a configured 853.33-second timeout;
these are not recorded timeouts. The frozen records do not preserve the native
finish reason or failed body. We cannot tell whether the consumed budget went
to useful unfinished prose, a malformed response or another behavior. The
adapter retains successful wire bodies only until dispatch accepts visible text.
A failed-attempt diagnostic record would resolve that uncertainty without
advancing the bookmark or presenting a failed completion as a journal.

## Next experiment and historical boundary

The [concrete proposal](../proposals/2026-09-09-study-claim-check-and-recovery.md)
has two immediate priorities: exact-path recovery candidates, and a small paired
test of a source-grounded claim-check prompt using the frozen wrong and correct
accounts. Evaluate whether the answer changes appropriately when the decisive
caller/branch evidence is present. Keep freeform writing and existing budgets;
measure correctness of specific claims, note revision, remaining questions,
repetition and latency separately. Retain failed-attempt evidence as a smaller
diagnostic repair. No experiment or implementation was run in this observation.

The selected live release remains HSS-14's stage and manifest
`56d066c6e0f818aa3d389c532541872af5924de7d5c7b2f0e1b0dd4d0d62491c`.
Observed process IDs remain bridge 7538 and Minime 5331. All supplied dispatcher
pages in the main cohort use `a737ea3379424c200b6c226f2d34d29b84671d3f12cfb47975bb8e4c39ad8992`;
the sole other source is `proposal.rs` at
`5313aa85965ade8ef0253b7f35d4d7680af60ad8702654c98dbe9a31c6eb9eee`.
The [capture-time source record](../research/outputs/2026-09-09-study-context-followup-source/manifest.json)
also retains a later dirty dispatcher revision (`89014b40…`) and its pending
test-only diff. That foreign change is not part of the supplied source or this
work and is not claimed deployed. Source, release and observed process are
separate identities. S-007's schedule/cursor and all earlier reports are unchanged.

## Board updates pending

The board write surface is unavailable in this session. The local
[finding, proposal and log payload](../board/study-context-followup-pending.json)
is unpublished: HSS-15 records one specific correction, persistent incorrect
notes in the other sequence, a reproduced path-recovery gap and the proposed
bounded claim-check experiment. No live Being state was changed.
