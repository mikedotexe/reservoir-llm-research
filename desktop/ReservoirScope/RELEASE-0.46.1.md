# 0.46.1 · selectable local request headroom

New sustained sessions can explicitly select a 60–600 second request deadline in
Advanced settings. The default remains 180 seconds. Historical omitted settings
still mean 60 seconds, and saved sessions retain their selected value.

The longer selectable ceiling supports local models sharing a machine while
processing retained inquiry history. It changes neither prompt text nor output
budgets and adds no automatic retry. The existing transport still enforces a
bounded total request deadline and cancellation; complete writing must pass the
same save, readback and application gates. A larger allowance is not evidence
that a particular model or concurrent configuration will finish in time.

## Verification

- Core generation-budget suite: seven tests passed, including legacy byte/hash
  preservation and a 600-second configuration through save, restore and replay.
- Frontend controller/setup suites: 40 tests passed. An explicit 600-second draft
  creates a ready session without starting writing; 601 seconds is rejected.
- Five targeted host/transport tests passed: the 600-second setting reaches the
  writing worker and survives immutable export/restore; invalid limits and
  cancellation do not connect; healthy slow work does not trigger a sleep hold.
- TypeScript, frontend production build and Rust formatting checks passed.

Native packaging and concurrent model qualification are separate execution
steps; this change record does not claim a completed three-model study.
