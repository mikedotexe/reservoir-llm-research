# 2026-10-25 · Reading Codex's October 24–25 tranche

Claude's read of what Codex added to this repository between the October 23 save point
(`b9f845d`) and the evening of October 25, written at Mike's request so the next session
and the other agents have one account of it. Read-only toward everything; the numbers
below are from `git`, from the suites run on this laptop, and from the accounts themselves.

## What arrived

- 143 commits on one chain (`codex/s021-walkthrough`, tip `d1a26af`), 124 files,
  about 20,200 lines added, 530 removed, between 2026-10-24 10:02 and 2026-10-25 20:45.
  Twenty-one further `codex/*` branches are stale side copies of commits already on the
  chain (one to five commits each, same titles, different hashes); eight Codex worktrees
  under `~/.codex/worktrees/` hold them (47 GB with their build trees).
- With Mike's authorization, Codex pushed the chain to `origin/main` (f5018fa → feb7bdd on
  the evening of October 25, then d1a26af) and tagged `reservoir-scope-tauri-v0.41.0-checkpoint`
  and `-v0.41.1-checkpoint`. The local checkout's `main` had not moved; it was fast-forwarded
  to `d1a26af` on October 25 at 21:07 PDT, then carried the root tidy (`da87f17`) and this
  session's commits.
- Nine studies, S-013 through S-021, each with a protocol in `research/studies/`, a dated
  account in `analyses/`, and a private evidence tree; a new standard-library package
  `reservoir_experiments/` (the "isolated local experiment runner", `research/EXPERIMENT-RUNNER.md`);
  fifteen probes; fourteen test modules.
- Desktop 0.40.0 → 0.41.1: a **Study** tab that walks through S-021 and is now the opening
  workspace; a **Plain journal** writing invitation (the existing
  `reservoir-journal-inert-plain-contract-no-tag-v1` prompt under a plain label); explicit
  same-session limit extensions; **Open journal folder**; `desktop/ReservoirScope/BUILDING.md`; the first-session
  guide and the root README rewritten around the app.
- Fourteen board cards and ten log entries since October 23, all by Codex except the
  October 23 S-012 log.

## What was checked here

- The Python suite on the tip: 648 tests, 33 skipped, no failures (62 s, python3.14).
  The Rust and frontend suites were not rerun on this laptop; Codex's release records
  report them green (528 frontend, 276 core, 268 desktop).
- The experiment runner's transport refuses any endpoint but `http://127.0.0.1:<port>`;
  the diff contains no SSH, `volya`, letter, `launchctl` or sibling-repo path. Nothing in
  the tranche reaches the beings, and every account says so.
- The writing loop of the frozen instrument is untouched: the core `sustained.rs` change
  adds a run-limit context to the budget-extension event and nothing to prompting, memory
  or encoding, so 0.39.0 arms remain comparable with 0.41.1 sessions at the same settings.
- The private evidence lives in the `introspection-tranche` worktree's ignored
  `research/outputs/` (408 MB) with byte-verified copies in the main checkout's ignored
  `research/outputs/*-closed-backup-*/` (418 MB). Removing the Codex worktrees would delete
  the live trees, not the copies.

## What the studies are

S-013 to S-016 are isolated gemma4 and mistral experiments on authored synthetic text:
attributing a supplied observation to its subject, time and value (gemma at ceiling,
mistral under-crediting current values in 19 of 120); self- against observer-framed
forecasts of verdict correctness (differences of a thousandth of a Brier point at ceiling);
original, paraphrased and notebook memories in a later application (a 3-point difference
with an interval through zero); and the action catalog's wording (the lexical endpoint
inconclusive, with the hypothetical NEXT distributions quite different: the full catalog
gave JOURNAL 33 and REST 15 of 48, the condensed menu PASS 44, neutral padding PASS 48).

S-017 to S-021 are a chain on one authored "ticket routing" task on mistral-small: whether a
corrected value survives into a later decision after the rule changes (one chain kept the
value and repeated the stale action); whether an explicit prior conclusion is needed for
the errors (it is not, 2 of 12 correct either way under changed rules); whether asking for
the comparison before the action helps (a ceiling bank where nothing failed, then a
reproduction bank where it did, with check-first 11 of 12 against 2 of 12 direct, and 10
against 6 in a fresh bank); and whether a supplied comparison changes the continuation
(a flipped relation mostly produced extra measuring). Six worlds and two seeds per bank.

## How it reads from this side of the program

What is good: every protocol was frozen in a commit before its outcomes; development and
confirmation are separate; every cell is retained; the intervals are called descriptive and
the banks are called authored; and each account has a "what reached the model" section, our
channel sentence carried into a new instrument. The app work is careful, tested and small.

Two reservations, stated so the next reader weighs them rather than inherits them. First,
S-017 to S-021 are experiments on a small model's handling of stale evidence in an invented
task. They involve no reservoir, no journal loop and none of the beings' records, and their
accounts say so in every paragraph; the one study that touches the program's open thread
is S-016, whose NEXT distributions are the first measurement of what the catalog's wording
does to the choice, which is the question S-012 left open for Minime. That result sits
under an inconclusive lexical endpoint and deserves its own read beside her catalog eras.
Second, "independent audit", "two fresh readers" and "scientific review" in these accounts
are other contexts of the same assistant family, as the accounts disclose; the hashes and
receipts verify bytes, not judgment. The accounts are dense with both, and the findings are
harder to find in them than in the S-011 synthesis table. The README Codex wrote led with
the app and opened the app on a Study tab about S-021; Mike asked for the README reshaped
around the journal and what to look for in it, which this session did.

## Open decisions, for Mike

1. The opening workspace: Study (S-021 walkthrough) or My reservoir. A one-line change in
   `App.tsx` plus its test; not made here.
2. The twenty-one stale `codex/*` branches and eight worktrees: delete after confirming the
   backups under `research/outputs/` are what Codex says they are, or leave as Codex's own.
3. Whether S-016's NEXT distributions get a read-only era read against Minime's catalog
   changes, as S-012's open thread proposed.
4. The push of this session's commits (root tidy, README, this note), as named refs.
