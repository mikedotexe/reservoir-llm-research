# Reservoir Scope shared reference

This directory records the fixed reference for the parallel Tauri implementation.
It does not replace the native app, its canonical resources, or its release identity.
The baseline is commit `96b60ed1d1fe9bdd3a5f50dec3a66a4754ad7f95`, native version
**0.15.0 build 21**, an unreleased local candidate. A source match does not establish
that any native or Tauri package has passed human acceptance.

[reference-manifest.json](reference-manifest.json) binds 180 selected native,
build and numerical source inputs and all 43 resources from the native canonical
[resource manifest](../../native/ReservoirScope/resource-manifest.json).
The `sourcePatterns` are the recorded input selection; both changed bytes and new
or missing selected source files fail the check. Source paths are repository relative.
The commit anchors the initial capture; runtime checks do not require Git history.

[fixtures/reference-scenes.json](fixtures/reference-scenes.json) contains two bounded
rendering fixtures derived from existing public tracked data:

| Scene | Input | Selection | Meaning |
| --- | --- | --- | --- |
| `stage-1-32` | `essentials/examples/essentials-stage-1.json` | `frames[0].state`, step 1 | Offline lab numerical example, 32 coordinates |
| `retained-128` | Native `state-replay.bin` | First 128 little-endian float32 values | Historical retained Minime activation row, 128 coordinates |

The second fixture has no invented step or timestamp. Its capture time describes the
observed file, not a row. There is no authenticated node layout/session/successful-step
identity or paired fill/controller join. The array order is preserved; a rendered
layout is explanatory geometry. The full original replay manifest and geometry are
staged alongside these fixtures so their source and limits remain inspectable.
No live database, sibling repository, model service or network is needed.

From the repository root:

```sh
python3 desktop/ReservoirScope/scripts/check_reference.py
python3 -m unittest discover -s desktop/ReservoirScope/scripts -p 'test_*.py'
python3 desktop/ReservoirScope/scripts/stage_resources.py
```

Use `python` in environments where that selects Python 3.12 or newer. The scripts
resolve the repository from their own location, so the caller's working directory
does not affect source or output selection. Their optional `--repo` exists for
isolated verification tests, never for selecting a live-system workspace.

The checker verifies SHA-256, byte length, complete source inventory, native identity,
canonical resource declarations, and exact fixture derivation. It never rewrites the
manifest or sources. Staging verifies first, then writes only the generated
`desktop/ReservoirScope/src-tauri/resources/` directory. It includes the two manifests,
the fixture, and the selected canonical originals declared in
`desktop/ReservoirScope/scripts/reference_support.py` (36 generated files in the
0.4 evidence tranche, including all 22 authored Library recordings). `resource-index.json` binds those
staged original files and the reference manifest/fixture hashes. Original files are
copied byte for byte; recordings are not regenerated.

A future intentional reference change requires a reviewed new baseline and matching
fixtures. Do not make a failed check pass by silently rehashing current inputs. Keep
native improvements, reference capture and Tauri parity claims separate in the
[roadmap](../../TAURI-ROADMAP.md).
