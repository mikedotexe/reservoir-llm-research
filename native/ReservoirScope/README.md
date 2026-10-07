# Reservoir Scope

[Current release, installation and acceptance status](../../research/CURRENT-RELEASE.md)
· [Guided tour](docs/GUIDED-TOUR.md) · [Earlier release history](README-history-through-0.13.1.md)

A native macOS research lab with an offline guided component journey, recorded and
optional local model writing, reviewed research cases, and a separate Minime & Astrid
observatory. The shared numerical core and matching runner live in `essentials/`.

The working source is an **unreleased 0.15.0 build 20 local candidate**, adding
[Geometry bookmarks](docs/GEOMETRY-BOOKMARKS.md). The linked 0.14.0 release and its
acceptance status remain separate from new local builds.

## Build from source

On an Apple silicon Mac running macOS 14 or later, install Xcode or its command-line
tools for Swift and the macOS SDK. The build also uses `python3`. From the repository root:

```sh
zsh native/ReservoirScope/build-app.sh
```

The final output line is the new app's absolute path on your Mac. Open that app
to begin **Essentials → Guided tour**; no model service is needed. Use
**Essentials → Experiments → Explore**, **Stage experiments**, or
**Actions & comparisons** for new experiments. **Runs & examples → Reviewed research
cases** opens the two evidence walkthroughs. Building from source creates a new
local package; it does not establish the existing candidate's acceptance result.

The resource manifest declares canonical inputs. The build stages a coherent package
outside the checkout; it does not regenerate recordings or edit canonical examples.
Use the staged `native/ReservoirScope/Package.swift` for SwiftPM or Xcode; its adjacent
`essentials` package supplies the same core. The staging/build receipt records the
selected source files, compiler, SDK, architecture and resource hashes.

## Verification

For the small numerical run-and-verify path, use the
[scripted runner quickstart](../../essentials/runner/README.md#scripted-quickstart).
For broader checks from a checkout, use Python 3.12 or later with SQLite FTS5
and the optional `[test]` dependencies, including NumPy, already installed in that
same Python environment. Follow the [test environment setup](../../research/TOOLS.md#reproduce-and-maintain)
before selecting the `python` group; the standard-library CLI quickstart alone
does not prepare the full test suite.
The following selects the groups that do not require a private daily research
packet. Replace `/absolute/path/to/Reservoir Scope.app` with the path printed by
your build, and use an installed compatible Python if `python3` is older:

```sh
task_app='/absolute/path/to/Reservoir Scope.app'
task_checks="$(mktemp -d "${TMPDIR:-/tmp}/reservoir-scope-checks.XXXXXX")"
python3 -B -m reservoir_research verify \
  --group python --group numerics --group native-model \
  --group native-presentation --group package \
  --app "$task_app" --out "$task_checks/checks"
```

These groups cover Python, numerics, native lifecycle, presentation and package
identity. They require the source checkout and macOS toolchain; the bundled runner's
record verification works independently of the checkout. The broader groups can
take substantially longer than the quickstart and create additional build outputs.
The `package` group verifies the sealed app without `--stage`; it does not compare
that app's captured source identity with today's checkout. A fresh build binds its
own staged source inputs and verifies that binding during the build.

`--group all-offline` also selects `research-replay`, which needs an explicitly
supplied private daily manifest and report (and their retained data root when
needed). Follow [research tools](../../research/TOOLS.md) for that separate workflow.
Without the required evidence, that group is **incomplete**, never passed. Default
verification makes no model requests, and human acceptance remains a separate
observation. Individual check scripts remain available for targeted development.

See [handoff](HANDOFF.md) for repository access and current boundaries. Historical
`build-receipt.json` files describe their original packages, not the current build.
