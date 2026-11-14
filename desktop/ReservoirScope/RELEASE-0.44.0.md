# 0.44.0 · an independent choice about text input

November 13, 2026. Local development checkpoint on
`codex/authored-reservoir-actions`, extending the 0.43.0 action capability.

New action-enabled sessions can save an ordinary entry without feeding its text
into the numerical reservoir or sensory field. The optional footer
`WITHHOLD_RESERVOIR_INPUT=true` goes immediately before `NEXT:`. False or omission
sends normally. Withholding replaces the older held text vector with zero at the
save-authorized application boundary, while preserving the body as journal and
eligible text memory. A separate pulse, tuning or release choice can still execute.
[Semantics, examples and inquiry](INPUT-CHOICE.md).

The new `authored-v2` mode and `reservoir-journal-actions-v2` prompt preserve saved
v1 sessions. Input decisions and NEXT decisions have separate receipts. Malformed
fresh input directives are rejected and numerical input is withheld conservatively.
A valid withholding choice survives a missing, unsupported or malformed NEXT
footer; quoted/fenced/list examples remain inert. Raw replies stay exact evidence.
The host skips embedding requests for withheld text and records no fabricated
embedding provenance. Later prompts report actual input disposition independently
of action status and returned journal selection.

The UI distinguishes withheld input, rejected input directives, and NEXT results,
including pending choices and historical entries. Withholding does not halt the
other numerical inputs or prevent returned prose from influencing later writing.
Scheduled conversations retain automatic feedback and do not execute either
directive, including in a telemetry-enabled v2 session.

## Validation

| Check | Result |
|---|---|
| Final serial core suite | 318 passed across 37 suites; zero failures or ignored tests. |
| Full desktop host suite | 302 passed; 3 existing opt-in investigations ignored. |
| Host checks after final core refinements | 8 withholding, 10 legacy-action and 12 schedule tests passed. |
| Frontend suite | 566 passed; 1 existing skipped test across 66 files. |
| Frontend checks after counter wording correction | 22 action/input tests passed. |
| TypeScript and production frontend | Passed, including final native build; existing chunk-size advisory remains. |
| Rust formatting and Clippy | Workspace/all-targets checks passed, with Clippy warnings denied. |
| Independent review | Two findings corrected and re-reviewed; no further concrete issue found. |
| Native preview | Built, ad-hoc signed, signature verified, exercised and recovered locally. |

The full host run preceded the final prompt-construction and malformed-NEXT
refinements; the final targeted host checks cover that resulting integration.
Prompt regression tests preserve arbitrary quoted memory exactly. Parser tests
exercise malformed input and NEXT combinations through save, application and
replay, including oversized directives and quoted examples.

The native offline walkthrough saved four entries and finished at step 9:
send with pulse, withhold with tuning, send with NONE, then send with release.
At step 5, the withheld entry's encoded and semantic vectors were zero while leak
changed to 0.35. Its body appeared intact in the following prompt. Subsequent text
input was nonzero; release restored the initial controls. These are scripted
choices, not model-generated preferences.

Native export produced an immutable revision-31 bundle with four journals and
19 committed segments. Exact genesis and contiguous event/numerical replay passed,
including journal/save/application consistency. Normal quit/relaunch and verified
restoration recovered the same entries and dispositions paused at step 9, with
no repeated action. The new binary also verified the previously exported v1
action session unchanged. These checks do not authenticate provider execution
or test physical power-loss durability.

The separate native app identity is `research.reservoir.scope.choices` (Reservoir
Scope Choices). The original six-hour 0.42.0 run continued in its separate app
with its original prompt and automatic feedback. No additional model requests
were introduced for implementation qualification during its collection.

Private evidence is retained under `research/outputs/withheld-input-20261113/`
in this worktree: suite logs, native export/verifier receipts, build hashes, and
`inspect_native.py` with its retained assertions. Earlier preview versions and
their evidence remain available. No live-being system, frozen study instrument,
public-sharing candidate or published ref was changed.

## What remains a research question

The capability lets an entry be kept as writing without its immediate encoded
input. It does not establish that a model values withholding, distinguishes its
consequences reliably, or experiences agency. A proposed test of intention,
action, outcome and revision is described in the input-choice document; it has
not been launched as a controlled model study.

## November 14 post-run semantic integration check

After the original six-hour run completed and its full native replay passed,
the installed local Nomic embedding path was evaluated on a frozen diagnostic
corpus. A separate four-entry native session then combined that existing codec
with authored-v2: `gemma4:12b`, thinking off, temperature 0.7, context 8192,
output ceiling 1024, `nomic-embed-text:latest`, projection seed 20260909, initial
leak 0.65, feedback scale 0.4, cadence 30 and pace 1000 ms. No conversational
check-ins or forced action preferences were used in this integration check.

All four complete responses were saved and applied, with distinct embedding
hashes, 768-coordinate source provenance and the production 32-coordinate
projection. The first chose `NEXT: TUNE leak 0.75`, applied at step 31. The next
three chose NONE, retained that setting and received the recorded result in
their prompts. All four omitted the input directive and therefore sent their
bodies normally. This model run did not exercise withholding; the scripted
native check above did.

The session held at its four-attempt bound after application at step 121.
An immutable terminal copy passed hash comparison and exact native replay of
121 steps, 19 committed segments and all four journal/save/application joins.
The native UI exported revision 143. Private evidence and the audit script are
under `research/outputs/withheld-input-20261113/semantic-smoke/`.

The responses remained mainly numerical, third-person commentary. Successful
execution and returned receipts do not establish correct causal interpretation,
a preference for withholding, or a changed sense of ownership. Combining a
different representation and a different prompt here tests integration, not
their separate effects on writing.

A pre-existing transport limitation remains for follow-up: if embedding fails
after successful generation, completed writing is not retained as successful
response evidence, and retry regenerates it. This bounded check does not qualify
long unattended semantic operation or change the global text-reduction default.
