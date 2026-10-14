# Tauri 0.17 public source checkpoint

This checkpoint preserves the Tauri implementation, contracts, tests, roadmap and
app-owned qualification evidence on `codex/tauri-0.17-checkpoint`. It starts at public
main `ef5a543c66bd6dfd4ab451a22edca6c6eccba8e2`. The 38 later commits on the original
research branch are excluded from this publication and remain intact locally.

The original native reference commit is still recorded as
`96b60ed1d1fe9bdd3a5f50dec3a66a4754ad7f95`. All 221 unique canonical native/resource
inputs already exist on public main with the same bytes; the additional shared
reference-scenes fixture travels with this checkpoint. Hashes establish this
compatibility without publishing or rewriting the original research history.

## Checks and small corrections

The [local receipt](local-checks.json) records checks in a separate main-based
worktree: frozen reference and resource staging passed, all 70 Python checks and
362 frontend tests passed, and TypeScript/Vite built successfully. The existing
large frontend bundle warning remains. The 105 Rust and 123 frontend inputs still
match the qualified 0.17 receipts. Rust tests, native UI acceptance, real-model
requests and package builds were not repeated for this save point.

Two bootstrap README sections now place resource staging before Rust compilation.
Two test files received platform guards: POSIX descriptor/symlink tests do not run
on Windows, and a journal-quality symlink test skips only if Windows denies its
creation with privilege error 1314. Other errors continue to fail. Neither change
modifies the production sampler, journal checker or app. Remote CI and packaged
acceptance are separate evidence; Windows/Linux acceptance remains pending.

## Publication scope

The review covered all 1,826 desktop candidate files, including all nine validation
screenshots, plus the shared contracts, roadmap and workflow. No credential content,
private Being journal capture, executable, model blob or database was found in the
Git-eligible set. The screenshots show this app or scoped resource plots. Historical
local paths, process metadata, hashes, app-owned prompts/journals and test failures
remain intentional provenance. Key/config references contain metadata only.
Private research packets under `research/outputs/` remain excluded.

Dated receipts retain their original paths and limitations. Their one-off scripts
may depend on the original machine or ignored captures. For a new checkout, use
[the application README](../../README.md) and CI bootstrap commands. Standard Python
tests intentionally include two retained validation JSON fixtures.

## Local preservation

A separate ignored archive preserves **32,620 files**, including the source
snapshot, QA evidence, current app, 23 historical package archives, eight additional
pinned verifiers and this Tauri app's three writable stores. Every archive member
was verified against its original SHA-256, size and permission mode, with no source
changes during capture. The [preservation summary](preservation-summary.json) records
the exact archive identity. Cached model files and rebuildable dependencies/caches
were excluded and left intact. The original research branch also has a verified
complete Git bundle in the same private checkpoint directory.

The archive is on this computer's existing volume. It protects against accidental
cleanup, but does not provide redundancy against device loss. Original packages,
exports, app stores and historical receipts remain in place. The [restore check](restore-replay.json) recovered 149 files, including the current
package, executable and both 73-file exports. Both restored twelve-journal exports
passed the restored verifier offline. That check launches no model and establishes
no new writing result.

The next product tranche remains a concise, versioned clarification of what writing
can change, with open subject and form. The twelve-entry v5 episode proves delivery,
saving and continuity; its invented actions and readings still require attention.
See [the retained next-tranche proposal](../2026-10-13-v5-writing-episode01/NEXT-WRITING-ENVIRONMENT.md).
