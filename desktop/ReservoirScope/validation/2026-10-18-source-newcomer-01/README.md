# Preparing the source-to-journal newcomer check

**October 18, 2026 · preparation, not human acceptance**

The selected journey is compile → existing local Ollama model → create/start a
reservoir → read incoming journals → export and local paused recovery. It is
separate from the candidate-04 Activation task card and its standalone Qwen setup.
No participant was contacted or represented as having completed this check.

The participant receives the [short task card](../../SOURCE-NEWCOMER-CHECK.md),
[Getting started](../../GETTING-STARTED.md) and the identified source handoff.
The [observer template](../../SOURCE-NEWCOMER-NOTES.md) stays blank. The four-attempt
trial uses 121 numerical steps, cadence 30, 1,000-ms requested pace, 900 seconds,
64 MiB, 8,192 context tokens, 1,024 output tokens and a 180-second request deadline.
It stops on the first failure/incomplete response or normal bound. No retry or
extension is part of that human check. Topic and form remain open; there is no
writing-quality gate.

## A fresh-source blocker, reproduced

The published source is `3459d7867eacaf6ceb4a48a0b0f539bd52d68c37`. A
[tracked-source export](source-before-01.json) excluded all ignored caches, model
files and runtime captures. In that copy, npm installation, canonical resource
preparation and the production frontend build passed. Rust's Tauri build script
then failed because the declared CPython bootstrap archive was missing. The
[before-build account](before-build-01.json) retains all four commands and logs,
including the original failure. The uv executable was also untracked and absent.

The base bundle declares both files even when the user only wants ordinary Ollama
writing. Existing development caches hid this fresh-checkout dependency. This was
an executed build failure, not a hypothetical usability concern.

## Build-only repair

[Bootstrap staging](../../scripts/stage_activation_bootstrap.py) reads the unchanged
frozen setup manifest. It obtains only the two public upstream bootstrap archives,
checks hashes and sizes, and extracts only the verified uv executable. It never
queries wheels, downloads a model, refreezes dependencies, installs a runtime or
executes the downloaded tools. A matching cache is reused without rewriting bytes
or metadata. Mismatched files and unsafe paths are refused rather than overwritten.

Each download is byte-bounded and has a hard 180-second deadline around the directly
owned system-Python I/O child. Timeout kills and reaps that child; only its unique
temporary file is removed. Publication uses a complete verified file and cannot
replace an existing destination. `--check` performs no download or write. No retry
loop is added.

The existing npm preparation wrapper now stages both canonical resources and these
bootstrap artifacts. CI also stages them before the independent Rust package tests.
The standard bundle keeps its existing optional Activation resources. This repair
does not change app code, prompts, numerical calculations, storage contracts, model
transport or dependency locks. The app version remains 0.27.1; the build is bound
by its source and executable identities rather than being treated as the earlier
0.27.1 package or the private 0.27.0 candidate.

## Checks and scope

- [17 focused synthetic tests](bootstrap-tests-01.json) pass. They cover cached
  reuse, missing/corrupt files, read-only checking, paths/links, concurrent
  publication, byte/hash/length failures, short reads, child timeout and hostile
  archive entries. The independent review caught a weakness in a between-read
  timeout; the owned-child deadline is the qualified correction.
- [Affected qualification](affected-tests-01.json) independently records those
  17 tests plus five frozen-reference tests passing, with tested hashes unchanged.
  These tests mock downloads and do not run a model or downloaded runtime.
- [After-build execution](after-build-01.json) starts from a second clean source
  export plus the four identified build files. It uses npm's lockfile, obtains the
  two real public artifacts from an initially absent cache, verifies them, and
  repeats the previously failing Rust check. The package command also exercises
  the updated preparation hook and verified warm cache.
- The standard Apple-silicon package build passes in 167.73 seconds. Its
  [identity receipt](package-identity-01.json) records a pinned 137-file copy and
  verified local ad-hoc signature. [All 137 files match](package-equivalence-01.json)
  the previously checked standard 0.27.1 package in bytes and modes, including the
  executable. That earlier scoped UI evidence is retained by exact package
  equivalence, not rerun or extended to a new human/model session. The existing
  Vite large-chunk warning remains; notarization is not claimed.

The existing host's Node/Rust/Python/SDK installations and Cargo registry/build cache
are reused, with at most two build jobs. This is a clean **source and bootstrap**
rehearsal on the development Mac, not a clean-machine installation or a second-Mac
result. Dependency-network access is distinct from model execution. No Ollama
inventory or generation request was made in this tranche, no app window was opened,
and no Minime/Astrid process, service or workspace was accessed.

## What the human check will answer

Can a new user follow the supplied documentation, identify their compiled app,
connect their exact installed model, understand Check/Create/Start, keep an older
entry selected during arrival, and find it again after export and local paused
recovery? Use of the supplied guide counts as uncoached within this packet; live
help is recorded separately. A failure remains useful evidence. Agent checks cannot
supply the participant's expectations, understanding or acceptance.

The guide now names the short pre-Create settings, complete-entry delivery,
single-instance behavior, normal saved-limit wording and local-only recovery.
Current fill and selected-entry measurements stay distinct. The 68% target is a
controller setting, not a proven special state. The ordinary app has no external
session-import control; the task does not substitute Activation import for it.

The private candidate-04 package/tag and every earlier receipt remain unchanged.
The standard build still lacks the optional historical Activation reading collection;
its existing collection-opening control is outside this ordinary-route check.
Windows/Linux builds, transferred installation, broader graphics/accessibility,
endurance and an actual first-time human session remain unqualified by this work.

## Prepared local handoff

The [handoff identity](handoff-01.json) binds a clean source directory, the build-only
overlay, guide/card/notes and the pinned standard app. The source directory contains
tracked source plus those named updates and preparation records, with no installed
dependencies, bootstrap cache, model, private capture or Git metadata. Its
`SOURCE-HANDOFF.json` identifies the supplied snapshot for an archive-based build.
The rehearsal uses identical build inputs. Human source/build/model fields remain
blank until observed on the participant's own machine.

This is a local, identified preparation. No new commit/push, app publication,
participant delivery or model execution is included. Publish the reviewed build
repair before directing an external newcomer to clone the branch; the existing
published baseline alone still has the reproduced failure. A local participant
can instead receive the prepared source directory and this packet.

The [runtime-source comparison](runtime-source-reuse-01.json) confirms 513 tracked
application, core, optional runtime, manifest and lockfile inputs are unchanged
from the published source and byte-equal in the rehearsal copy. Prior frontend
and backend test results are reused at that scope, not reported as new test runs.
The current commands recheck compilation and the changed build preparation.
