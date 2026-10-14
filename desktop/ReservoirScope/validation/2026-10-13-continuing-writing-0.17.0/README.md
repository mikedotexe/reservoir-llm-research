# 0.17.0 · Continuing writing context

New sessions use `reservoir-journal-v5`. The model receives a compact optional
readout followed by the complete previous saved-and-applied entry and a final open
invitation. Topic and form remain open; there is no prescribed persona, feeling,
reflection, metric recital, heading or length. Full observations and the eight-row
measurement reference remain available to the human reader in Evidence.

The [context account](CONTEXT-CHANGE.md) distinguishes the two return paths: reduced
textual features become reservoir input, while full prior prose returns separately
as memory. Neither path is new in this tranche. The [versioned contract](../../../../shared/reservoir-scope/continuing-writing.md)
preserves codec, numerical mechanisms, generation bounds and durable save/readback/
next-step application rules. Historical v1–v4 prompts remain exact, and omitted
historical versions still mean v1. Existing sessions are never upgraded in place.

## Source qualification

- [Frontend receipt](frontend-checks-01.json): 362 tests across 39 files and the
  TypeScript/Vite production build passed against unchanged inventoried inputs.
- [Rust receipt](rust-checks-04.json): 190 core tests passed in run03 and are reused
  only after exact core input comparison; 192 desktop tests and strict Clippy for
  both crates passed in run04. Two existing opt-in tests remain ignored.
- [Focused checks](focused-core-01.json): 33 prompt, budget and optional-evidence
  tests passed before the final full checks; these overlap the core suite.
- [Independent source review](V5-REVIEW.md), [test correction addendum](V5-REVIEW-ADDENDUM.md)
  and [integration review](INDEPENDENT-REVIEW.md) remain distinct from execution.
- [Synthetic helper tests](synthetic-harness-tests-01.json): seven provider and
  fifteen checker tests passed without a socket, model or native app.

The initial runner syntax error is retained in [preflight](runner-preflight-01.json).
Runs01–03 retain test failures caused by old default-v4 label/array/hash expectations
and an overly broad `journal-` absence assertion that matched the required version
header. Only those test expectations changed; production v5 code was unchanged.
The final checks retain exact text/ID/hash evidence assertions with the new layout.

## Package and native workflow

The [prospective protocol](PROTOCOL.md), [frozen candidate](PROMPT-V5-TEMPLATE.txt),
[synthetic plan](NATIVE-QUALIFICATION-PLAN.md) and [freeze](prospective-freeze-01.json)
precede native execution. Prior 0.16 r2 app, archive and pinned verifier matched all
48 inventoried files before replacement: [preservation](prior-package-preserved-01.json).
The [source-bound build](package-build-01.json), [archive readback](archive-check-01.json)
and [after-UI receipt](qualification-after-ui-01.json) passed for distinct **0.17.0**.
Local ad-hoc signature verification passed. [Native checks](MACOS-UI.md) saved/applied
four fixed replies, held the incomplete fifth, exported through the actual dialog,
and restored paused after provider shutdown. Both exports passed exact replay and
request/prompt/response joins. [Recovery](RECOVERY-RESULTS.md) preserved all 27
non-manifest files; only wrapper phase/generation/revision changed. The owned fixture
stopped explicitly. The app remains paused on its journal reader.

[Six historical exports](HISTORICAL-REPLAY.md) passed without changing any bytes,
including both twelve-journal v4 exports. The retained corpus covers v1/v3/v4; no
historical v2 bundle was found. V2 is covered by the separately generated desktop
save/export/restore tests, not an invented historical export.

## Interpretation and next work

This implementation gives continuing prose more room in the request. Exact matched
fixtures shrink from 4,445 to 1,437 UTF-8 bytes for the first request, and from 4,829
to 1,627 with the same prior text. These are byte counts, not tokens or evidence of
provider attention. Synthetic replies cannot establish a better voice, factual
accuracy, self-reflection or emergence.

The next writing-quality task is a separately bounded real-model episode with frozen
budgets, fresh resource admission and review of every response and exact continuity
join. The completed twelve-entry v4 episode remains historical reference material,
not an unseen control. No real model or Being is contacted in this qualification.
Windows/Linux, measured GPU/energy, broader accessibility, physical crash/sleep and
long-duration real-model acceptance remain independent work.
