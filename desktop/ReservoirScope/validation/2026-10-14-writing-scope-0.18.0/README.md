# Writing scope · 0.18.0

New sessions use `reservoir-journal-v6`. Two short sentences clarify that describing
an experiment does not execute it or produce a new reading during the reply.
The existing numerical-feedback and complete-prose memory paths remain explicit,
and the subject and form stay open. Historical v1–v5 sessions retain their exact
contracts. The [prospective protocol](PROTOCOL.md) defines this narrow change.

Implementation, local source checks, a distinct macOS package, historical replay
and the planned native synthetic export/recovery checks are complete. **No real
model ran in this tranche.** The known v5 writing motivates the change; synthetic
responses cannot establish its effect on actual writing.

## What changed

V6 preserves the v5 scaffold except its version header and these two sentences in
SESSION CONTEXT, before the optional readout:

> Writing is the only action available here. Describing a control change or experiment does not execute it, and no new readout arrives while this entry is written.

The subject, form, imagery and reflective stance remain open. Saved writing still
returns through the existing numerical encoding and full-text memory paths; it
does not execute prose-described commands or train weights. Numerical behavior,
save/readback gates, cadence and budgets are unchanged. Old v1–v5 prompts and
restored sessions keep their original contracts. Full observations remain available
in Evidence independently of the compact supplied readout.

## Executed evidence

| Check | Result and receipt |
| --- | --- |
| Rust core | 200 passed in [run 1](rust-checks-01.json); exact unchanged core inputs reused by run 2. |
| Desktop and strict lint | 194 passed, two explicitly ignored; core and desktop Clippy passed in [run 2](rust-checks-02.json). The initial two stale v5 assertions and their correction remain in [the failure account](rust-failure-analysis-01.json). |
| Frontend | 362 tests in 39 files and TypeScript passed; [receipt](frontend-checks-01.json), followed only by [a comment correction](frontend-comment-addendum-01.json). |
| Synthetic helper tests | 26 passed without sockets or models; [receipt](synthetic-harness-tests-01.json). |
| macOS build | Reference check, frontend production build, release app, exact archive member validation and local ad-hoc code-signature verification passed; [build](package-build-01.json), [archive](archive-check-01.json), [identity](qualification-before-ui-01.json). This is not notarized distribution acceptance. |
| Historical exports | Eight v1/v3/v4/v5 bundles replayed with all 371 original files unchanged; [receipt](historical-replay-01.json). V2 has generated persistence tests, but no historical export was available. |
| Native synthetic session | Four journals saved/applied at steps 11/21/31/41, fifth incomplete reply held at 50; exact v6 prompts and full prior-text joins verified; [UI](MACOS-UI.md), [original export](NATIVE-EXPORT-RESULTS.md). |
| Clean-quit recovery | Provider stopped; explicit paused restore and second native export passed. All 27 non-manifest files stayed identical; [recovery](RECOVERY-RESULTS.md). |

The app and archive live in this attached worktree's ignored `target` directory;
the earlier primary-checkout package is preserved separately. Current executable
SHA-256: `fe14eeb2f921a541644a900d3397d973d81a6f70de66347f485cc0851fecafb0`.
Archive SHA-256: `1a59336a35715cd3e5f532c7d5b933fc2e3216ec0241c839aca7d35abe758561`.
The [post-qualification identity check](closeout-integrity-01.json) separates the
later documentation closeout from the built and tested runtime inputs.

The [separate CI account](../2026-10-14-platform-ci-0.17.0/README.md) preserves the
first cross-platform result and its test-only covariance correction. A subsequent
build/test pass would still not establish packaged desktop acceptance on those OSes.

## Next bounded tranche

Select a prospective real-model v6 episode with explicit attempt, duration,
storage and output bounds. Review every completed reply for continuity, claimed
actions and measurements, keeping delivery/replay results separate from prose
assessment. Do not treat the already-read v5 episode as an unseen control or
prescribe self-reflection as a required style. No new GPU/energy, multi-hour,
minimized, sleep or crash/power-loss result is claimed here.
