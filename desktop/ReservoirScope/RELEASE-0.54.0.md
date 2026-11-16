# 0.54.0 · Research integration and experiment preflight

November 15, 2026. Isolated development candidate on `codex/research-integration`.
This joins the completed journal UI checkpoint `2eb8c48` and research API checkpoint
`b558a07`, preserving both histories and their separate worktrees. It is not the
sharing candidate and has not been deployed to the three existing experiments.

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
[isolated API workflow](validation/2026-11-15-research-integration/black-box.json).

- Core suite: 392 passed. Final affected action/configuration/experiment checks:
  47 passed; compact scanner checks: 6 passed.
- Frontend: 628 passed, 1 pre-existing skipped; TypeScript and production build passed.
- Full host run: 341 passed, 3 ignored, one new growth test exceeded its 30-second
  operation wait under concurrent suite load. The bounded wait is now 90 seconds,
  and the test counts entries from the actual committed change boundary. All 11
  affected API, navigation, configuration, recipe, and growth tests passed afterward.
  The entire host suite was not repeated after that focused correction.
- CLI: 5 passed. Real CLI preflight returned 0 for valid input and 1 for invalid input.
- The isolated black-box workflow used three fake-provider arms and a separate
  scripted v4 growth arm. It checked prefix-stable pagination, step-scheduled growth,
  a custom prompt, encoding transition, stop superseding a pending change, matching
  journal evidence, four verified exports, and zero provider requests on restart.
  Provider concurrency remained at the configured maximum of one.
- Native 0.54 debug bundle built and signed ad hoc. A separate 48-node scripted
  preview saved three entries; its copied measurements loaded by exact identity and
  preflight displayed all malformed-command issues. The preview app was then quit.
  No real model was called for these checks.

The development app is `target/debug/bundle/macos/Reservoir Research Integration.app`
under this worktree, with identifier `research.reservoir.scope.integration`. Its data
is separate from the other app profiles. The binary hash is recorded in checks.json.

## Remaining qualification

Warm/cold OS custom-scheme launching remains unqualified: the verification browser
blocked the earlier handoff. Parsing and in-app navigation are covered. This work
also makes no claim about model competence with the new prompt or long-run storage
behavior; that needs an explicitly selected, bounded model study. Existing runs,
live beings, private study assets, and published refs were not changed.
