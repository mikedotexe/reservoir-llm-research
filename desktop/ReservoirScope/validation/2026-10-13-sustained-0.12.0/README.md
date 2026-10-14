# 0.12.0 — My reservoir and automatic durable journals

Implementation and checks executed October 13, 2026 on this Apple-silicon Mac.
This is the first sustained personal-session implementation under M5b. Qualification
is bound to the exact source, package and short tasks recorded below; it is not a
multi-hour or 24-hour soak, real-model qualification, or acceptance of other platforms.

## Delivered behavior

My reservoir has its own continuous 32-node numerical state, current seeded RNG,
sensory covariance and controller state. Storage boundaries do not restart it. Every
writing opportunity retains a versioned observation containing recurrent coordinates
and separate sensory/fill measurements. The latest saved-and-applied journal is
physically reread as full-text memory. The reduced text vector is separate from that
memory and is not a learned embedding or model training.

Automatic saving publishes and reads back the exact journal before preparing its
next-step feedback. Immutable bounded event segments and content-addressed checkpoints
are committed through a small manifest. Save failure pauses; explicit recovery verifies
genesis and the whole committed chain. A crash-interrupted request is never resent
without a new explicit attempt. Historical finite formats and their limits are unchanged.

The journal reader has an independent selection and an explicit Follow latest action.
The Rust worker owns pacing while navigation/minimization suspend unneeded rendering.
Step, writing-attempt, running-duration and per-session disk budgets stop visibly;
old journals are not deleted to make room. macOS activity allows system/display sleep;
sleep/wake signals and long host-time gaps require explicit review. Close/Return
arbitrates both finite and personal lab owners.

## Executed automated evidence

- Frontend: 295 tests passed; production build passed. Earlier full runs had 292/293 tests;
  the final run includes blocked-snapshot export and immutable-frame regressions.
- Core: 150 tests passed; strict all-target Clippy passed. The 10 new sustained tests
  include 3,605 accelerated steps, 120 attempts and 85 verified segments. The measured
  30,221-byte checkpoint maximum was sampled at settled ready/prepared boundaries.
- Separate final core corpus: 180 steps across 36 verified segments; maximum 13 retained
  events and 35,599 checkpoint bytes measured at every transition. See
  [core qualification](core-qualification-final.json).
- Legacy interchange regression: all 63 retained finite records pass current Rust and
  unchanged Swift; 567 targeted alterations fail both, and six permitted raw diagnostic
  controls pass both. See [legacy conformance](legacy-conformance.json).
- Python resource/receipt tooling: 13 tests passed. Native reference check remains
  180 source files, 43 resources and one fixture. Native source is unchanged.

- Desktop: 154 full-suite tests passed, including the accelerated 1,001-step run.
  The final Checkpoint and quit improvement passed 20 sustained and 15 close-focused
  tests, plus strict all-target Clippy. Source continuity separates these executions.
- All three actual native-dialog exports pass whole-bundle verification; all 39 altered
  copies are rejected. Their exact fixture prompts, replies, journal memory and saved
  application boundaries agree. See [initial exports](actual-ui-export-qualification.md),
  [final export](final-ui-export-qualification.md), and `final-ui-recovery-continuity.json`.

The full suites total **612 tests** before the final quit improvement; its focused
checks include one new regression and rerun relevant existing tests. This is not a
claim that the entire final desktop suite was rerun after that narrow change.

## Actual package and delivery

The [packaged walkthrough](macos-ui.md) records automatic journals, independent old-entry
reading, short minimized progress, a held reply across Pause, next-step feedback,
cancellation with late fixture success, native exports and explicit recovery. The final
candidate additionally demonstrates Checkpoint and quit preserving prepared feedback at
9, idle relaunch and restoration, single application at 10, and a held vector at 11.
The test provider and application were stopped afterward. No real model was contacted.

Final binary SHA-256: `f68a3752a628edf11ac6161a26e6979bb22dcf4c3ee1c63f10add2cea86ab40d`.
Final archive: `ReservoirScopeTauriPreview-0.12.0-final-macos-arm64.tar.gz`, 102,477,475 bytes.
SHA-256: `aa2174162f8b1e9ff06d3beb2b8911afb6325ac612343a235afc7d3e80ceb601`.
All 46 archive files match shipping bytes/modes; 39 canonical and 42 packaged resources
are verified. Signing is local ad hoc, without notarization. The initial archive remains
separate, with its own source/package identities and checks.

[Qualification receipt](qualification.json), `source-before-final-build.json`,
`final-package-before-ui.json`, `final-archive-and-resource-check.json` and
`source-continuity.json` bind the candidate and distinguish initial/full checks from
the final targeted checks. Earlier test-helper/mock corrections remain in their logs;
none changes a native numerical threshold or a historical receipt.

## Qualification limits

The new versioned directory bundle uses Rust whole-history verification; the old Swift
verifier does not implement that new protocol. Segment-only verification has the
narrower declared-starting-checkpoint scope. Hashes and replay do not authenticate a
provider or prove historical physical disk durability.

Real-model interoperability/capacity, multi-hour and 24-hour wall-time runs, actual
system sleep/wake, physical power-loss/disk-full behavior, Windows/Linux execution,
minimum macOS 14, complete accessibility, measured GPU/power/memory efficiency and
collaborator acceptance remain separate gates. Fault hooks, accelerated steps and
short minimized checks cannot establish these claims. No Being workspace, service,
producer, prompts or research schedule was accessed or changed.

Next bounded tranche: long-duration and fault/lifecycle qualification, measured memory
and disk behavior, and deliberate budget-extension/recovery ergonomics. Selected
read-only feeds remain separate. Full M3 visualization parity and the cross-platform
matrix remain tracked in the roadmap.
