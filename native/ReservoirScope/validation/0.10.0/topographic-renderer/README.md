# Topographic renderer qualification

The immutable [qualification receipt](receipt.json) records 43 passing checks,
23 offscreen renders and seven dense GPU field comparisons at 768 × 768 pixels,
sample count 1, on Apple M1 Max. Seven separate pristine renders support the exact
legacy pixel comparisons. Maximum GPU/CPU field error was 1.79 × 10⁻⁷.

[Packaged identity link](packaged-identity-link.json) binds the checked renderer/math
and input resource hashes to [Reservoir Scope 0.10.0 build 13](../artifact-identity.json).
It also lists SHA-256 hashes for every copied qualification artifact. The original
receipt, PNGs, raw pixel buffers and [log](run.log) were copied without alteration.
Presented-window appearance and responsiveness are qualified separately.

Compare the focal Stage 1 observation in [legacy surface](legacy-32-stage1-step1.png)
and [topography](topography-32-stage1-step1.png). All fixture values and their
synthetic or retained provenance are recorded in the receipt. The native128 fixture
has no paired fill; its legacy size uses an explicitly identified 68% preview.

The [previous](previous) directory preserves both pristine 0.9 renderer/math source
files; [pristine](pristine) preserves their PNGs and raw BGRA pixel buffers. The
retained test source and `runner-at-qualification.sh` document the exact checked
harness. Reproduce from the research repository root using the maintained runner:

```sh
native/ReservoirScope/check-topographic-renderer.sh /tmp/topographic-recheck \
  native/ReservoirScope/validation/0.10.0/topographic-renderer/previous
```

The second argument is optional. Without a baseline source directory, the current
renderer checks still run and the new receipt explicitly marks the legacy baseline
comparison unavailable. No temporary baseline directory is required for reproduction.
