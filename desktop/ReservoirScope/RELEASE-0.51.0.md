# Reservoir Scope 0.51.0 · parameterized copied experiments

Local development checkpoint, November 15, 2026, on
`codex/reservoir-experiments`, based on `35b340a`. This adds an opt-in
`experiments-v3` capability and a distinct **Reservoir Experiments** native app.
The ongoing Gemma4/GLM/Ministral 0.50.0 cohort was neither restarted nor upgraded.
The live beings were not contacted. No refs were published.

## Behavior

`NEXT: EXPERIMENT` accepts a named question with numerical arguments: custom,
measured or mixed input directions; amplitudes/signs; impulses, pulse trains or
oscillations; conditions varying held input, leak, recurrent gain or saved state;
and selected observation times/coordinates. Every condition has its own copied
no-probe comparison sharing forcing and noise. The default origin is the state
seen at the requesting turn, before that entry's SEND/WITHHOLD decision.

Results retain exact origin, resolved arguments, response curves, asymmetry,
amplitude scaling and between-condition differences. Four identified results
are available for follow-ups. `latest` is bound to its exact ID in each saved
argument; evicted/unavailable references are rejected. Zero excitation and no
contrast are explicit outcomes. Copied tests never automatically change live
controls. Their cost is bounded at 896 recurrence steps.

`PROBE_EXPERIMENT` separately applies one measured impulse, requiring existing
real-probe permission, a previously measured amplitude/sign and a fresh
application-time bound/forecast. Trains and oscillations remain copied-only.
The native panel distinguishes copied measurements, observed immediate effects
and conditional future forecasts. Existing v1/v2 scanner contracts are retained.
See [the contract and examples](EXPERIMENTS.md).

## Qualification

Private evidence is retained in
`research/outputs/parameterized-experiments-20261115/` in this worktree.

- 382 core unit/integration tests passed, including eight new experiment tests.
  The final eight-test suite also passed after a mathematically equivalent lint
  correction. Coverage includes native signed-curve parity, origin timing,
  waveform behavior, mixtures, saved states, immutable references/eviction,
  degenerate contrasts, bounded cost, authority and exact replay.
- The host run had **328 passes, one failure and three ignored tests**. The
  existing long-text worker test exceeded its five-second `wait_for` bound during
  the parallel run. An unchanged isolated rerun passed, including export/recovery.
  Both logs are retained; this is not reported as a clean broad-suite pass.
- The new host integration test passed save-failure injection, retry, origin
  timing, next-prompt visibility, real impulse, follow-up, export and restoration.
- 611 frontend tests passed; one skipped. Native-generated synthetic fixtures
  exercise request/report/receipt validation, opt-in gating and outcome rendering.
- TypeScript/production build, workspace formatting and strict all-target Clippy
  passed. Vite retains the existing large-chunk warning.

The actual native app completed six scripted entries through step 19. It scanned,
compared leak 0.65 versus 0.2 on copies, applied a measured real impulse, and
reused the step-6 origin for a pulse-train follow-up. The immediate real effect
was **0.0026163580429291416**, equal to its refreshed forecast; live leak remained
0.65. The copied impulse returned below 10% of peak for five consecutive boundaries
starting at step 4 for leak 0.65 and step 12 for leak 0.2. These are this fixture's
conditional responses, not a general leak recommendation.

Native accessibility and screenshot inspection confirmed the comparison table,
real receipt and named follow-up. Export, normal quit, fresh launch, verification
and paused restoration preserved both result IDs at step 19 with six journals.
The qualification app was then closed. Only the three original exploration apps
remained running. No model service was called for qualification.

The 0.51.0 export and the frozen v1/v2 native scanner exports all passed the native
verification and scan CLIs, with every source file hash unchanged. This turn did
not repeat the earlier seven multi-hour independent/peer export checks. Native
fixture arithmetic and prompt visibility are reproducible using
`probes/audit_parameterized_fixture.py`; maximum prompt size was 21,488 bytes,
export payload 5,349,013 bytes. This is not an endurance/storage qualification.

The preserved app is `app/Reservoir Experiments.app` beneath the private packet,
identifier `research.reservoir.scope.experiments`. Binary SHA-256:
`b4d9d1eb2b957a22c30332dd5be77892bfab8361f865efcdd1330480a025624e`.
Ad hoc signature verification passed. The Apple-silicon debug build is not a
new sharing candidate or notarized distribution.

## Research boundary

This establishes the apparatus path from a question to a test, returned evidence
and a follow-up. Whether a language model uses it competently is untested. A short
controlled inquiry should assess null-result recognition and evidence-responsive
revision before another long run. The companion
[spectral reading](../../analyses/2026-11-15-spectral-motion-and-parameterized-experiments.md)
keeps recurrent trajectory covariance, the separate sensory spectrum and model
interpretation distinct. No global topology or experiential claim is established.
