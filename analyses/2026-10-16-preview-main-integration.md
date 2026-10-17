# Preview source integration and remaining replay qualification

October 16, 2026 (Pacific). Mike selected integration into `main` after the other
agent's completed save point, with separate worktrees for concurrent implementation.
This account records the source checks and their limits. Remote publication is
verified separately; this file does not claim a pending merge has happened.

## Preserved inputs

The other agent completed and pushed
[`3459d7867eacaf6ceb4a48a0b0f539bd52d68c37`](https://github.com/mikedotexe/reservoir-llm-research/commit/3459d7867eacaf6ceb4a48a0b0f539bd52d68c37)
on `codex/activation-loop`. It includes the existing
`reservoir-scope-tauri-v0.27.0-private-preview` checkpoint and the qualified 0.27.1
completion-message change. The original worktree was clean at handoff.

Integration uses its own managed worktree and `codex/preview-integration` branch.
The [shared instructions](../AGENTS.md) now require separate worktrees and branches
for concurrent implementation. Neither the original checkout nor the private
preview handoff is reset, replaced or removed.

The candidate-04 archive remains 143,145,478 bytes with SHA-256
`a80e466e6e08f02f65e1b40aaff0e2fbab9e0ffcb949157f03bd3e9091148cc5`.
The [0.27 release account](../desktop/ReservoirScope/RELEASE-0.27.0.md) retains its
scope; the [0.27.1 source save point](../desktop/ReservoirScope/RELEASE-0.27.1.md)
does not replace that private package or complete human acceptance.

## Clean-checkout preparation

The original CI run stopped because its script tests imported NumPy without
installing it. The workflow now installs the existing `numpy==2.2.6` pin for those
synthetic tests. It does not install MLX or a model.

The Tauri resource configuration also names two ignored public bootstrap assets.
The new [stager](../desktop/ReservoirScope/scripts/stage_activation_bootstrap.py)
restores only the Python archive and uv executable from the committed manifest,
verifies both archives and the extracted executable, refuses conflicting existing
files, and never runs downloaded contents. It does not refreeze metadata, fetch
model weights or copy private reading collections.

A clean local Python environment passed 128 script tests with five skips. A real
download matched both manifest identities; an immediate second invocation verified
the existing assets with zero downloads. The frozen native reference passed.
Six synthetic stager tests cover integrity, reuse, conflicting files and unsafe
archive/path cases. Windows separately required explicit scoping of POSIX-only
cohort signal tests; portable protocol checks remain enabled there.

The subsequent [Windows backend build](https://github.com/mikedotexe/reservoir-llm-research/actions/runs/39010819918/job/117332847387)
exposed unguarded Unix `waitpid` assertions in the activation test harness. The
synthetic tests now discover an absolute Windows Python path and verify child
exit with native Windows process handles, while retaining the Unix `ECHILD`
assertions. The direct-child deadline test uses the existing portable `try_wait`
pattern outside Unix. A readiness-path assertion now compares path components
instead of requiring slash separators. That test-harness repair kept every
activation test enabled and changed no production process behavior.
All 47 focused activation/backend setup tests passed locally after this repair.
The same CI attempt passed its complete Rust stage on macOS and Linux before
the corrected test harness was submitted for a fresh three-host run.

## Windows activation persistence boundary (October 17 follow-up)

The [next Windows job](https://github.com/mikedotexe/reservoir-llm-research/actions/runs/39011795019/job/117335753252)
compiled successfully and passed 219 backend tests, with two existing skips. It
failed 16 activation persistence tests with `Access is denied. (os error 5)`.
The unchanged publisher writes and syncs each evidence file, then opens and syncs
its parent directory; Windows rejects that plain directory open. Session save
also requires directory sync after updating its latest pointer. These failures
occur before the cohort process-exit assertions are reached.

Activation execution is an Apple Silicon/macOS feature in the selected preview.
This observation establishes that its Unix evidence-persistence implementation
is not usable on Windows; it is not a Python-discovery failure. Production
durability requirements and saved-record semantics remain unchanged.

The 16 affected tests now report explicit non-Unix ignore reasons. The optional
synthetic export test has the same scope: its earlier Windows pass only reflected
an unset export environment variable. Configuration validation and both large-pipe
deadline/cancellation tests remain enabled everywhere. A separate transport-only
response deadline test preserves that check without requiring evidence publication;
the original evidence-backed deadline test remains enabled on Unix. Reader,
setup metadata, command-boundary and pure activation-core tests also remain active.
Passing scoped source CI therefore does not qualify Windows activation persistence.
All 48 focused activation/backend setup tests passed on the local Apple Silicon
host after this classification, with no ignored tests there.

## Observed cross-host replay gaps

CI at `62f15cc5af8ffebed4ce49e6990de471390f5854` passed reference, Python,
bootstrap and frontend stages on all three configured hosts. Its core tests exposed:

| Host and retained history | Observation |
| --- | --- |
| [Ubuntu 24.04, x86_64](https://github.com/mikedotexe/reservoir-llm-research/actions/runs/39010072115/job/117330622890), v3 legacy-budget segment | Raw serialization passed; exact replay rejected the journal candidate with `Journal candidate does not reconstruct from the accepted response/observation`. |
| [Windows 2022, x86_64](https://github.com/mikedotexe/reservoir-llm-research/actions/runs/39010072115/job/117330622645), frozen v1 segments | The v3 legacy-budget test passed on this host; the v1 replay failed with `Sustained event does not reproduce its exact transition`. |

These are retained failed qualification observations, not successful cross-host
replays. The Linux candidate reconstruction recomputes lexical features and the
feedback vector; the precise differing coordinates and platform-math cause still
need an isolated comparison. No claim of a universally portable numerical history
follows from a passing same-host test.

The existing [sustained contract](../desktop/ReservoirScope/crates/reservoir-core/SUSTAINED.md)
already requires separate receipts for cross-platform libm reproducibility.
Historical byte/hash/prompt/default preservation checks therefore remain active on
every target, while exact replay of the retained macOS histories has a separately
named, explicitly scoped test. Fresh same-host replay and tamper checks remain
active. Historical fixtures, production numerical code and strict replay validators
are unchanged. Foreign-host exact replay remains unqualified; the scoped test
classification does not repair or conceal these observed failures.

After this split, all 27 tests in the three affected Rust suites passed on the
local Apple Silicon macOS host, including both strict historical replay tests
and the new same-host legacy-budget case. The integrated cross-platform CI run
has its own result; this local pass does not substitute for it.

## Board updates pending

Record a proposed platform-conformance follow-up for exact cross-host replay of
retained sustained sessions. Bind it to the two CI jobs above, the original fixture
hashes and the unchanged validator. Isolate numerical differences before choosing
a versioned portability design. Do not regenerate old fixtures, loosen replay
validation or infer Windows/Linux install acceptance from source CI.

Record Windows activation evidence persistence as another platform boundary,
linked to the October 17 job above. Any future Windows execution support needs an
explicit durability design and qualification; do not silently omit directory sync
or reinterpret an already-written file as a completed save.

This is a local proposal (`being: system`), not a live-board update. No new model
generation, live-system change, private distribution or human acceptance occurred
during the integration checks.
