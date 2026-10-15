# Retained first-check failures

The first full source checks are retained unchanged in `rust-checks-01.json` and
`frontend-checks-01.json`, with their logs. They were not packaging acceptance.

- Core: all 219 tests passed. Their unchanged source, dependency and fixture inputs
  are explicitly rebound by the second Rust receipt rather than rerunning them.
- Desktop: 197 passed, one failed and two opt-in tests were ignored. The long-text
  worker test still asserted the old fresh default `WritingBoundaryJournalV7`.
  It now asserts `MeasurementMeaningJournalV8`; its save, memory, output and restore
  expectations are unchanged. The existing paired-measurement restore matrix was
  also extended to include v8.
- Frontend: 374 passed and one failed. The independent-reading test still required
  the old sentence “reading position never moves the live clock”; the shorter
  visible sentence says “reading never moves the live clock”. The selected-journal
  and new-arrival assertions remain unchanged.

These corrections change test expectations and add explicit version coverage.
They change no product code, prompt bytes, runtime limits or scientific acceptance
thresholds. Second checks use exclusive `-02` logs and receipts. Their actual
outcomes, including strict Clippy and TypeScript, are recorded separately.
