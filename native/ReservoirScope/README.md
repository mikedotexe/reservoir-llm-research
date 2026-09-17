# Reservoir Scope

[Current release, installation and acceptance status](../../research/CURRENT-RELEASE.md)
· [Guided tour](docs/GUIDED-TOUR.md) · [Earlier release history](README-history-through-0.13.1.md)

A native macOS research lab with an offline guided component journey, recorded and
optional local model writing, reviewed research cases, and a separate Minime & Astrid
observatory. The shared numerical core and matching runner live in `essentials/`.

## Build

On an Apple silicon Mac with Swift and the macOS SDK, from the repository root:

```sh
native/ReservoirScope/build-app.sh
```

The resource manifest declares canonical inputs. The build stages a coherent package
outside the checkout; it does not regenerate recordings or edit canonical examples.
Use the staged `native/ReservoirScope/Package.swift` for SwiftPM or Xcode; its adjacent
`essentials` package supplies the same core. The staging/build receipt records the
selected source files, compiler, SDK, architecture and resource hashes.

```sh
reservoir-research verify --group all-offline --app PATH_TO_APP --out NEW_DIRECTORY
```

Verification groups include Python, numerics, native lifecycle, presentation,
research replay and package identity. Missing prerequisites are reported as
incomplete rather than passed. No default check calls a model. Individual check
scripts remain available for targeted development.

See [handoff](HANDOFF.md) for repository access and current boundaries. Historical
`build-receipt.json` files describe their original packages, not the current build.
