# Synthetic v6 qualification harness

The two provider files are exact copies from the 0.17 continuing-writing qualification. The model identity and five fixed replies are unchanged. The checker adds exact version-6 scope placement to the existing full-text memory, HTTP-body hash, typed provider evidence, save/readback and once-only application joins. It requires the action-scope sentences in SESSION CONTEXT before OPTIONAL READOUT. Quoted historical prose cannot satisfy that requirement and remains intact even if it contains the same words or apparent headings.

Pure helper qualification passed **26 tests: 7 provider tests and 19 checker tests**. The tests include the independently retained first/later v6 core prompt fixtures, missing/mutated/misplaced/duplicated scope, Unicode and historical instruction-like prose. Fixture tests check structural compatibility; the exact pinned production CLI remains responsible for numerical replay and exact rendered prompts. See [copy provenance](synthetic-helper-copy-01.json), [test receipt](synthetic-harness-tests-01.json) and [full test output](synthetic-harness-tests-01.log).

No provider, native app, model or production replay was launched for this helper qualification. It supplies no writing-quality or full-context-coverage result.

## Parent-operated commands

Run from the desktop directory of the selected managed worktree. The following is a launch template; the parent must first choose a new ordinary output directory and freeze the package/configuration. The provider creates that directory exclusively beneath this worktree's `target/qa`, binds an ephemeral loopback port, permits at most five chat requests, and ends on its stop-request file or the 900-second limit.

```sh
python3 -B validation/2026-10-14-writing-scope-0.18.0/owned_provider.py target/qa/0.18-writing-scope-provider-01 --lifetime-seconds 900
```

Use the returned `endpoint.json` identity in the explicit native configuration. The checker expects seed 20261013, v6, cadence 10, 51 maximum steps, 5 maximum attempts, 180 active seconds, 32 MiB, pace 1000 ms, output 1024, request deadline 180 seconds, context 8192 and temperature zero. The fifth response is deliberately incomplete; the expected final numerical cursor is held at step 50 with four saved journals and applications at 11, 21, 31 and 41. No retry is part of this protocol.

The parent must create `prospective-freeze-01.json` with a `files` entry binding this exact `owned_provider.py` before launch. After immutable native export, supply the actual pinned CLI and its qualified hash:

```sh
python3 -B validation/2026-10-14-writing-scope-0.18.0/check_fixture_export.py EXPORTED_BUNDLE --fixture target/qa/0.18-writing-scope-provider-01 --cli PINNED_CLI --expected-cli-sha256 QUALIFIED_SHA256 --output validation/2026-10-14-writing-scope-0.18.0/original-export-evidence-01.json
```

The checker reads only those explicit inputs, requires a new result path, invokes `--verify-sustained` without restoring or running the session, and compares source bytes before/after. Actual wrapper phase, core phase and any terminal cleanup events are reported separately; a paused recovered wrapper does not imply accepted fifth-response feedback. Recovered export should receive a separate receipt and exact file comparison.
