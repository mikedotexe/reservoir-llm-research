# 0.54.0 · Research integration and experiment preflight

November 15, 2026. Locally qualified development package on `codex/research-integration`.
This joins the completed journal UI/theme checkpoint `2a04436` and research API checkpoint
`b558a07`, preserving both histories and their separate worktrees. It is not the
sharing candidate and has not been deployed to the three existing experiments.

## November 16 finalization

macOS cold and warm URL dispatch is now qualified for the extracted integration
app and its registered `reservoirscope-dev` handler. Run, exact journal entry,
experiment and settings links reached their intended native views. A mutation URL
was ignored without creating an operation or advancing the retained run. The app
was closed after verification; no models were called and existing experiments
were unchanged. [Navigation evidence](validation/2026-11-16-research-finalization/deep-links.json).

Mike authorized publication of the merged `main` history. The local signing
identity check returned zero valid identities, no Apple environment credentials
were configured, and the repository Actions secret list was empty. Notarization
has therefore not been submitted. [Signing prerequisite record](validation/2026-11-16-research-finalization/notarization.json)
· [Notarization handoff](NOTARIZATION.md). Earlier package/check receipts remain
historical records of what was known on November 15.

## Result

The API, CLI, and native Research runs workspace now work with parameterized
experiments and the current journal presentation. The shared journal projection
retains the producing configuration, raw reply, action choice, receipt, measurements,
and exact verified journal object. Entry selection remains stable during polling;
matching saved results are looked up by run/generation and result ID/origin step.
Unavailable results are reported rather than replaced with a newer measurement.

New experiment opt-ins select `experiments-v4` and produce `parameterized-v2`
reports for 32–128 recurrent nodes. A 32→48 transition preserves every existing
coordinate and connection, adds zero-valued nodes and deterministic connections,
and clears dimension-dependent result caches. The sensory field remains 32-dimensional
and text input remains 48-dimensional. Historical events, journals, and v3 parser
and prompt behavior remain unchanged. A v3 run needs an explicit v4 transition
before growth.

`POST /v1/validate`, `reservoirctl validate`, and native preflight controls validate
configuration patches, recipe arms, or ordinary-turn action text without creating
operations, loading retained run owners, advancing state, or calling models. The
same parser checks execution and preflight. New prompts include a complete runnable
example, and structured issues explain the screenshot's malformed inquiry, unknown
`feedbackScale` condition, misplaced `observe`, and missing amplitudes. Failed
writing stays intact; nothing silently repairs or guesses the intended request.

[API usage and contracts](RESEARCH-API.md) ·
[Scripted growth recipe](../../research/recipes/growth-experiments-v4.json).

## Qualification

[Machine-readable checks](validation/2026-11-15-research-integration/checks.json) and
[final isolated API workflow](validation/2026-11-15-research-integration/black-box-qualified.json),
[bounded real-model workflow](validation/2026-11-15-research-integration/real-model.json),
and [initial qualification history](validation/2026-11-15-research-integration/checks-initial.json).

- Core suite: 392 passed. Final affected action/configuration/experiment checks:
  47 passed; compact scanner checks: 6 passed.
- Frontend: 628 passed, 1 pre-existing skipped; TypeScript and production build passed.
- The repeated host suite before the final race fix passed all 342 tests (3 ignored).
  The real-model workflow then exposed a scheduled resize resuming after Pause.
  Commit `4e5a02e` makes lifecycle intent authoritative under the run gate, also
  protecting prompt admission and cancellation cleanup. A deterministic regression
  passed. The final full host suite passed 343 tests, with 3 ignored and
  zero failures.
- CLI: 5 passed. Real CLI preflight returned 0 for valid input and 1 for invalid input.
- The isolated black-box workflow used three fake-provider arms and a separate
  scripted v4 growth arm. It checked prefix-stable pagination, step-scheduled growth,
  a custom prompt, encoding transition, stop superseding a pending change, matching
  journal evidence, four verified exports, and zero provider requests on restart.
  Provider concurrency remained at the configured maximum of one.
- Native 0.54 debug bundle built and signed ad hoc. A separate 48-node scripted
  preview saved three entries; its copied measurements loaded by exact identity and
  preflight displayed all malformed-command issues. The preview app was then quit.
  The final blue-theme bundle reopened that same retained run and loaded its exact
  step-6 measurements. The GUI was then closed; this did not dispatch model work.
- The final bounded model check used the existing laptop loopback service and
  `ministral-3:8b-instruct-2512-q4_K_M`, in a new app data root. It saved three
  complete responses, paused and explicitly resumed, grew from 32 to 48 nodes at
  step 4, admitted an exact passive prompt at step 5, retrieved every journal
  through the CLI, stopped at step 7, and verified its three-entry export. Two
  ordinary v4 prompts and one custom prompt reached the model. The earlier attempt
  saved one entry before detecting the race and was stopped; its data is retained.
  No model-writing retry or change to the three existing experiments occurred.

The development app is `target/debug/bundle/macos/Reservoir Research Integration.app`
under this worktree, with identifier `research.reservoir.scope.integration`. Its data
is separate from the other app profiles. The binary hash is recorded in checks.json.

## Package and source

[Exact archive identity and extraction checks](validation/2026-11-15-research-integration/package.json).

The local arm64 ZIP includes the ad-hoc-signed debug app, `reservoirctl.pyz`
(Python 3.12+, standard library only), API guide, this record, and a scripted growth
recipe. `IDENTITY.json` binds the source checkpoint, binary and CLI. `SHA256SUMS`
and the adjacent qualification receipt identify the exact archive. The archive is
extracted again for signature and file-inventory comparison before acceptance.
The packaging command is `scripts/package_research_api.py --app APP --output NEW_DIR`;
it never builds, starts models, changes signing, or copies app profiles.

The November 15 qualification committed and merged the work locally without
publishing it. Mike authorized publishing `main` on November 16; no release tag is
part of this finalization. The package is not notarized for public distribution.
The existing three model sessions keep their original app binaries and data.

## Remaining qualification

The integration profile passed macOS cold/warm custom-scheme dispatch on November
16. Other platforms and the normal-profile scheme still need separate qualification.
Notarization awaits the Apple certificate and credentials described above. This work
makes no claim about model competence with the new prompt or long-run storage
behavior; the three-response check establishes only the software workflow. Existing runs,
live beings and private study assets were not changed by qualification.
