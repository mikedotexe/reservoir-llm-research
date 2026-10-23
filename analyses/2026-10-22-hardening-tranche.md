# Hardening tranche 1 (October 22, 2026): the living documents against the dated records

Written at 2026-10-22 21:09 PDT, before any change in this tranche. The criteria below were fixed
first; the report at the end says what was checked, what was changed and what remains.

## Why now

Sixty-nine commits on `main` since October 17 and nothing pushed; two corrections placed
today beside earlier claims (the older-entry register effect, the primer); the app renamed
during the stretch; S-011's apparatus tier closed this evening
([synthesis](2026-10-22-s011-apparatus-synthesis.md)). Before anything is shared, one bounded
pass over the pages that summarize current status, against the dated records they summarize.

## Scope

Living documents: `CLAUDE.md`, `AGENTS.md`, `README.md`, `RESEARCH.md`, `TRACE.md`
(its current sections; the dated addenda are sources), `research/NOW.md`,
`research/METHODS.md`, `research/QUESTIONS.md`, `research/CURRENT-RELEASE.md`,
`research/arms/README.md`, `research/readings/README.md`, `research/TOOLS.md`,
`TAURI-ROADMAP.md` (its status text), `desktop/ReservoirScope/README.md`, `STATUS.md`,
`GETTING-STARTED.md`, `PREVIEW-START.md`, `SUSTAINED-SESSIONS.md`,
`crates/reservoir-core/SUSTAINED.md`, `native/ReservoirScope/HANDOFF.md`,
`shared/reservoir-scope/PARITY.md`, `board/README.md`. Out of scope: the dated accounts
(they are the sources), the history files, the release records, proposals, exercises, probes
and tests (except a bug a test exposes), and anything about the beings' live systems.

## Acceptance criteria

1. Every number in a living document resolves to a dated account under `analyses/`, a study
   progress entry that names its probe, a probe output named in an account, a release record,
   or a dated TRACE section, or is marked as a dated observation with its date.
2. No living document carries a claim that a later dated correction contradicts without the
   correction beside it. Test cases: the older-entry register effect (corrected 2026-10-22
   evening: beside a shown number); "the primer did its job" (corrected: it did not control
   the first entries); "an effect of the returned entry" (corrected to "of the returned entry
   beside a shown number"); the fork rate (2 of 117 on October 21, 1 of 52 on October 22);
   "the latest entry's presence restores nothing" (now "while a number is shown").
3. The app's names and version roles agree everywhere: the Tauri app is Reservoir Scope
   (installed under its earlier name, Reservoir Scope Tauri Preview, for the 0.27.0 handoff);
   the native SwiftUI app is the earlier ReservoirScope 0.15 candidate; 0.27.0 candidate 04 is
   the sharing candidate; 0.28.0 through 0.39.0 are unqualified local candidates and 0.39.0 is
   the frozen research instrument.
4. The suites are green at the tranche's closing commit: the Python tests, `cargo test` for
   `reservoir-core` and `reservoir-scope-desktop`, `npm test`, `npm run build`,
   `cargo fmt --all --check`, `cargo clippy`. Counts recorded in the report.
5. The board is an honest record: the `board/*-pending.json` files are resolved (historical,
   reconciled 2026-10-06, stated in `board/README.md` and the synthesis log); no card is
   marked `active` without an agent on it; the S-011 cards point at the synthesis.

## Rules

No feature work, no new arms, no new app version, no change to a probe unless a test exposes
a bug in it; corrections go beside earlier claims, never in their place; every edit is listed
in the report with the criterion it serves; one pass; the suites run at the end; the push after
the tranche is Mike's decision, as a named ref.

## Method

A read-only cross-check of every quantitative claim in the scope against its source, by a
subagent reporting to the session scratchpad (no edits by it); a grep over the scope for
names and versions; fixes by hand; the suites; this report.

## Report (2026-10-22 21:30 PDT)

**Cross-check.** A read-only subagent checked 482 quantitative claims across the 22 documents
in scope against the dated records (its report is retained as
[the cross-check](2026-10-22-hardening-tranche-cross-check.md); all commit hashes and tags in
the living documents resolve in this checkout). It found 10 mismatches, 3 unsourced numbers and
2 weakly sourced ones; everything else resolves to a dated account, a study entry with its
probe, a release record, a validation receipt or a source constant. None of the mismatches is
in a dated account; all are living pages lagging their records.

**Edits, each beside the claim it corrects (criterion in parentheses):**

1. `research/NOW.md`, October 22 focus: "the latest entry's presence ... restores none" gained
   the bracketed correction "while a number is shown; without one the older-entry slot writes
   at the `latest` arms' rates" (2).
2. `research/NOW.md`: "her journal elaborations carry no number at all" → "no readout number
   (and, but for five of 1,097, no percentage at all)", the audit's count (1).
3. `research/NOW.md`: "her own aspiration and witness readouts held one value all week" →
   "her own aspiration readout, and every witness quantity but the live λ₁" (1).
4. `research/NOW.md`: the afternoon's "reading sessions pending" gained "[the evening parked
   the 0.37.0 and 0.36.0 samples as superseded; the 0.39.0 sample waits]" (2).
5. `desktop/ReservoirScope/STATUS.md`, the 0.38.0 paragraph: "an effect over seven arms"
   gained the bracketed correction "of the returned older entry beside a shown number" (2).
6. `CLAUDE.md`, key paths: "181k LLM jobs" → "181k on 2026-09-06, 213k on 2026-10-22" with the
   TRACE pointers (1).
7. `CLAUDE.md`, data fact 6: "about a third of the time" now says it is the September 6 reading
   in MOVES.md and that no probe has measured it with n (1).
8. `CLAUDE.md`, "What this repo is": one sentence that the apparatus tier closed with the
   synthesis, that 0.39.0 is the frozen instrument and 0.27.0 candidate 04 the sharing
   candidate (3).
9. `desktop/ReservoirScope/SUSTAINED-SESSIONS.md`: "Temperature remains zero", a 0.14-era
   sentence, → "zero unless the language configuration sets one (0.29.0; fresh Ollama setups
   propose 0.7)" (2).
10. `research/arms/README.md`: the "Embedding codec arms (0.30.0)" family (runner 0.33.0, two
    gemma4 arms no account named) is now "Embedding codec twins without the effect clause
    (0.33.0)", read in S-011's 2026-10-21 20:10 entry as the twins of `inert-effect-gemma4` (1).
11. `shared/reservoir-scope/PARITY.md`: the banner names the instrument freeze and the pointer
    date is October 22; the two platform rows record the October 16 run that executed on all
    three hosts and failed exact replay; "Next tranches" opens with the parked note (2, 3).
12. `desktop/ReservoirScope/README.md`: the banner says 0.39.0 is frozen as the research
    instrument; the CI sentence records the October 16 run (2, 3).
13. `RESEARCH.md`: the guided tour is the native ReservoirScope 0.15 app's, not "Reservoir
    Scope's", which since October 22 names the Tauri app (3).
14. `desktop/ReservoirScope/PREVIEW-START.md`: the 2.23 GiB download figure is marked as an
    observed figure not retained in a dated validation record (1).
15. `research/readings/README.md`: seed 37 is marked as recorded in the sample's key file in the
    scratchpad, not in a dated record (1).
16. `research/TOOLS.md`: "all 15 report fields unchanged" now points at the SELF_STUDY history
    that records the replay (1).
17. `research/NOW.md`, next-session list: the tranche's bullet marked done (bookkeeping).

**Board (criterion 5).** The 29 `board/*-pending.json` files are historical: all 29 are named
in `board/2026-10-06-reconciliation.json` and `board/README.md` says their filenames do not
mean republication; stated in the synthesis log entry, nothing republished. Four cards marked
`active` since September 6–7 with no agent on them (`d-flicker-reference`,
`d-roadmap-moves`, `d-protect-list`, `f-fill-is-field`) were returned to `open` with a dated
note and their content unchanged. The nine S-011 cards point at the synthesis.

**Suites (criterion 4), run 21:11–21:19 PDT on this tree** (logs in the session scratchpad
under `hardening/`): Python 427 tests OK, 31 skipped (the count includes the two tests of the
S-012 probe written in the same tree and committed in the next step); `cargo fmt --all
--check` clean; `cargo test --locked -p reservoir-core` 275 passed across its binaries;
`cargo test --locked -p reservoir-scope-desktop` 262 passed, 3 ignored (the headless arm
runner and its kin); `cargo clippy --locked --workspace --all-targets` clean; `npm test` 508
tests in 60 files; `npm run build` complete. The edits above change no code.

**Remains (not done in this tranche).** The cross-check could not resolve three items:
`STATUS.md`'s "three preceding apparatus commits" (not checked against the log); the Node
20.20.1 pin in the guides, sourced only by the CI workflow while the laptop runs Node 24; and
`research/TOOLS.md`'s probe-bound numbers, checked for internal consistency only. The 108
open cards from the September agenda are untouched. The push, as a named ref, is Mike's.
