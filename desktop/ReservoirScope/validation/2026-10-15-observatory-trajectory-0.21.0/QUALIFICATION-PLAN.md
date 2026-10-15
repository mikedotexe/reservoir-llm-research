# 0.21 Observatory trajectory qualification

Preparation only until the lead freezes integrated source and invokes these commands.
This tranche reads existing bundled recordings. It adds no model request, live feed,
new observation or synchronized clock between independent recordings.

## Preserved baseline

`protect_prior_package.py` has already copied and verified the qualified 0.20 full
app, archive and pinned verifier into `target/qa/0.21-prior-0.20-preserved`.
`prior-package-preserved-01.json` binds all 46 package files, the exact archive and
executable, and unchanged originals. The separate read-only exact-path process
snapshot is dated evidence only; it does not authorize quitting or replacing an app.
The lead must finish any application use before building.

## Final source checks

Run from `desktop/ReservoirScope`, after integration is frozen. The wrappers set
Node 20.20.1, Cargo's configured 1.94.1 toolchain, the qualified Xcode/SDK paths,
`CARGO_INCREMENTAL=0` and two Cargo build jobs. Do not overlap Cargo executions.

```sh
python3 validation/2026-10-15-observatory-trajectory-0.21.0/run_frontend_checks.py --attempt 01
python3 validation/2026-10-15-observatory-trajectory-0.21.0/run_rust_checks.py --attempt 01
```

Frontend runs the complete Vitest suite and TypeScript without emitting a build.
Rust verifies references, stages checked resources, checks formatting, runs full
core and desktop suites, then strict all-target Clippy for both packages. Rust unit
tests may use their own ephemeral loopback fixtures; no model service or GUI is
started. No older test pass is reused. Receipts bind code, configuration and fixtures;
documentation is outside these test inventories. Source changes during checks fail
qualification. Use a new two-digit attempt for a correction, retaining earlier logs.

The source tests should cover the final selected trajectory contract: exact retained
PC rows and immutable normalization; fixed full-capture variance evidence; selected
ordinal binding; bounded complete timeline coverage; missing/stale reads; track
switch/hidden playback; exact fallback and accessible selection. No timestamp,
paired fill, live variance or physical trajectory is manufactured.

## Distinct package

After passing exact-source receipts and coordinated application shutdown:

```sh
python3 validation/2026-10-15-observatory-trajectory-0.21.0/build_package.py \
  --rust-receipt validation/2026-10-15-observatory-trajectory-0.21.0/rust-checks-01.json \
  --frontend-receipt validation/2026-10-15-observatory-trajectory-0.21.0/frontend-checks-01.json \
  --attempt 01
```

The build wrapper checks final receipt inputs and preservation, binds the global
source inventory before/after, builds without launching, verifies version and bundle
identity, makes a new exclusive 0.21 archive and verifier pin, verifies archive
members, rechecks preserved 0.20 copies and captures a separate qualification receipt.
The archive/pin must not already exist. A retry is not permission to overwrite them.
Post-build documentation changes must be recorded separately from the qualified
source; no older receipt is rewritten.

## Actual package boundary

The lead owns native opening, source/ordinal/scale inspection, exact selected-row
values, trajectory/surface coordination, keyboard/pointer use, hidden playback and
graphics fallback. Record whether any cross-page, resize or context-loss check was
actually performed. A build or source test does not establish hardware acceleration,
GPU/power savings, minimum-OS, Windows/Linux or collaborator acceptance. The prior
0.20 lifecycle and real-writing receipts remain historical; this presentation tranche
must not claim a new model or long-duration run.
