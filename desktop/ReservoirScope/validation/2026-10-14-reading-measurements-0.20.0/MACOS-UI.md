# Native reading and recovery · 0.20.0

Executed October 14, 2026, in the actual macOS ARM64 application identified by
[the pre-UI freeze](prospective-freeze-01.json). This is agent UI qualification,
separate from collaborator acceptance and real-model writing assessment.

## Fixed synthetic session

The app displayed **0.20.0**. The exact prospective
[configuration](packaged-ui-plan-01.json) was entered through the interface.
One explicit readiness check matched the owned fixture at `127.0.0.1:52199`,
operation `model-check-82276-1`, digest `synthetic-no-model-weights`.
Create and Start were each used once. Session: `sustained-1792004958844-1`.

Four complete replies were durably saved at observation steps 10, 20, 30 and 40,
then first applied at 11, 21, 31 and 41. The fifth incomplete reply held step 50
without a journal or feedback. Its visible failure remained available while
reading. There was no Stop, Skip, Retry, cancellation, budget extension or second Start.

At live step 25, the selected step-20 entry showed first application at 21,
v8 identity, the retained prompt and prior reply. Evidence was then closed.
**Pause following** pinned entry 40 while the session still showed Running at
live step 47. **Earlier entry** selected entry 30 by the next observation at
live step 50; its measurement table stayed explicitly bound to steps 30 and 20.
**Later entry** returned to 40 and reset Measurements and Evidence to closed.

The native observations do not independently establish older-entry selection
before execution stopped or a new saved entry arriving after pinning. Those
asynchronous selection cases, stale responses and navigation across page boundaries
are covered separately by frontend tests. This native history contains four entries.

Native folder export succeeded. The first Go to Folder paste did not change the
chooser's old path; explicit setValue followed by Return selected the new path
before publication. No bundle was written to the previous episode's directory.
[The original export](original-export-evidence-01.json) verifies exact requests,
v8 caveats, unchanged late boundaries, complete prior-text joins, optional wide and
unusable provider counts, numerical replay and save/application gates.

After the owned fixture's explicit stop, clean quit was confirmed by the app
inventory. Relaunch was idle. Verify and inspect followed by **Restore paused for
review** retained the blocked fifth attempt, four journals and disabled Resume.
A second native export passed [the same checks](recovered-export-evidence-01.json).
The [recovery comparison](recovery-comparison-01.json) found all 27 nonmanifest
files byte-identical; only generation 1→2, revision 76→77 and wrapper
`attemptBlocked`→`paused` changed. The numerical core stayed blocked.

[Execution notes](native-execution-01.json) and the
[stopped-provider receipt](provider-stopped-01.json) retain the actual scope.
The fixture recorded one inventory GET, five generation POSTs and explicit stop.

## Completed v7 journals in the new reader

After another confirmed clean quit and idle relaunch, the existing owned session
`sustained-1792001665258-1` was explicitly verified and restored paused. It retained
twelve journals, step 361, 59 segments and disabled Resume. No readiness, Start,
Resume, Retry or model operation was performed.

Pause following pinned the selection. Earlier selected journal 11, observed at
330 and first applied at 331; its Evidence retained `reservoir-journal-v7`.
Later selected journal 12, observed at 360 and first applied at 361, with both
disclosures closed. Native screenshots at 1280×860 were visually inspected:
paragraph spacing and line width supported reading, controls were legible, and
model-authored numerical preambles and literal Markdown remained unmodified.
These screenshots were inspected in the UI tool, not retained as image artifacts.

[Before/after managed-file checks](v7-reader-native-01.json) found all 72
nonmanifest files unchanged. Only generation 2→3 and revision 424→425 changed;
the wrapper remained paused. Both prior immutable exports remain separately
preserved. The app was left paused at step 361 with journal 12 selected and
Follow latest off for the user to read.

This establishes reader behavior with existing v7 prose. It adds no new v8 model
writing, quality assessment, provider-context proof, crash/power-loss qualification,
endurance measurement, graphics-performance claim or Windows/Linux acceptance.
