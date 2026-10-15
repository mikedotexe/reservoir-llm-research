# V7 episode02: fresh window refused before launch

The user requested safe memory cleanup and a fresh attempt with the same limits,
preserving [episode01](../2026-10-14-v7-writing-episode01/README.md). That refusal
remains unchanged. This distinct window also **did not start**: its single
[admission](host-admission-01.json) at2026-10-14 18:09:35 UTC reported pressurelevel2
(required1),34% free memory (required at least35%) and528,458,579,968 free disk bytes
(disk passed). All twelve writing opportunities are unstarted. No model service,
readiness request, new session, Start, generation, journal, export or recovery
occurred; no writing-quality or continuity result follows.

[Cleanup inspection](cleanup-inspection-01.json) found no additional runtime that
could safely be identified as disposable work from this task. The prior owned
app/model were already stopped. Repository-matched Codex automation workers were
left running because their current ownership/use was unknown. Other shared or
unknown model processes, personal apps and evidence were preserved. No process
signal, cache deletion, purge or shared-model unload occurred. The change from31%
to34% reported free memory is **not attributed to our actions**.

The [freeze](evaluation-freeze-01.json) binds117 inputs, verifies the prior
refusal unchanged and keeps every limit, prompt, model and evaluation criterion.
Only episode/provenance identifiers changed. [Reuse evidence](reuse-preparation-01.json)
binds byte-exact helpers and prior37 checker,55 reading-helper and37 supervisor
tests; those tests were not rerun and supply no new runtime acceptance. The native
form was configured without an endpoint/session and [closed cleanly](native-close-01.json)
after refusal.

No automatic resampling or replacement window is authorized by this outcome.
The user was asked whether Brave may be quit normally before one further fresh
attempt because its tabs may contain unsaved work. The user subsequently authorized normal Brave quit and one further fresh attempt;
that cleanup and episode03 will be recorded separately. No Brave action occurred
in this refused episode. Any subsequent window must retain both
refusals and the same limits. Minime and Astrid remain untouched.
