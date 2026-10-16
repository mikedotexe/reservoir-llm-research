# Observatory fields 0.22: prospective qualification

This directory prepares qualification of the reference-field and state-spectrum
inspection tranche. It is not evidence that checks or measurements have run.
The lead owns final source freeze, app shutdown, builds, native UI and capture.
No model/readiness/service request, live feed or Being access is part of this plan.

The source checkpoint observed during preparation was
`0001b7a8967c44c80201ed9ada035eaaf5695d63`. Product implementation is proceeding
separately; this checkpoint is not represented as the final 0.22 build source.

## Preserve 0.21 before replacement

After the lead finishes any use of the old app, invoke from `desktop/ReservoirScope`:

```sh
python3 validation/2026-10-15-observatory-fields-0.22.0/protect_prior_package.py
```

The helper checks all 46 package entries against the original 0.21 archive receipt,
its `c4b51f57…130128` executable and `33409bd6…ccd0f` archive, then exclusively copies
the full app, archive and pin into `target/qa/0.22-prior-0.21-preserved`. It requires
available volume bytes greater than the copy size plus 1 GiB, leaves partial files
on failure, and verifies originals and copies afterward. It deletes nothing. A
prospective copy script is not a preserved package; only its successful receipt
establishes that step. Filesystem availability is not a reservation for a build.

The old archive, old verifier pin, all dated receipts and real-model/diagnostic
evidence remain immutable. The full old app copy remains independently usable.

## Exact-source checks and package

After product source is frozen, use exclusive numbered receipts. Do not run two
Cargo pipelines concurrently:

```sh
python3 validation/2026-10-15-observatory-fields-0.22.0/run_frontend_checks.py --attempt 01
python3 validation/2026-10-15-observatory-fields-0.22.0/run_rust_checks.py --attempt 01
python3 validation/2026-10-15-observatory-fields-0.22.0/run_sampler_checks.py --attempt 01
python3 validation/2026-10-15-observatory-fields-0.22.0/build_package.py \
  --rust-receipt validation/2026-10-15-observatory-fields-0.22.0/rust-checks-01.json \
  --frontend-receipt validation/2026-10-15-observatory-fields-0.22.0/frontend-checks-01.json \
  --attempt 01
```

These wrappers are adapted from 0.21; [the copy receipt](helper-copy-preparation-01.json)
records their bases. Frontend runs Vitest and TypeScript. Rust runs reference and
resource checks, formatting, full core/desktop tests and strict all-target Clippy.
Tests may create their owned synthetic loopback fixtures; they do not start a real
model. The SDK-bound build requires passing matching source receipts, verified old
preservation, the expected 0.22 package version, and exclusive archive/pin paths.
It verifies resources/archive members and records signing/qualification metadata.
Signing remains the actual local signature reported by the receipt, not a public
notarized distribution claim. Preserve earlier failed receipts if repairs require
a new attempt.

Final implementation tests should cover retained provenance/units; full-capture
fixed scales; invalid/missing/stale data; current row binding; independent state
and sensory data; field/spectrum selection; keyboard/table alternatives; disposal
and hidden scheduling. Source tests alone do not validate native pointer mapping,
WebGL drivers, VoiceOver, frame latency or GPU load.

## Native package inspection

The lead may explicitly invoke `launch_ui.py` after the new package is qualified.
It opens the exact package with an exclusive owned Library at
`target/qa/0.22-observatory-ui01`, without model calls. Record actual checks and
untested cases separately: source/provenance labels and units; full-capture scales;
row/field selection; state-spectrum values and limits; resize; keyboard/pointer
controls; table fallback; track switches; visibility pause and return. Do not
manufacture a clock joining independent recordings or describe a reduced spectrum
as complete. Context-loss handling is only claimed tested if exercised.

The passive main-process plan and exact command templates are in
[RESOURCE-PROTOCOL.md](RESOURCE-PROTOCOL.md). It is a separate short measurement,
not a GPU or endurance qualification. Root records native boundaries and renderer
counter witnesses; the sampler does not automate the app.

Before native measurement, bind the final sampler/test/plan hashes, successful
synthetic sampler checks, exact-source frontend/Rust receipts, package inventory,
archive, pin and launch receipt in the lead's prospective measurement receipt.
No numerical CPU/RSS acceptance threshold is added after seeing results. Unexpected
errors, identity changes, incomplete coverage or unexplained growth remain visible
for review; low main-PID CPU cannot prove low WebKit/GPU cost.
