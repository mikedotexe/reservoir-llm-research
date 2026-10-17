# Journal-first local-model walkthrough — preserved 0.25 preparation

**Closeout, October 16:** the user selected 0.27 for the check. This 0.25 attempt
remains unexecuted; no model service or request ran here. The separately identified
[0.27 account](../2026-10-16-journal-flow-0.27.0/README.md)
records the completed four-journal session. No further 0.25 attempt is queued.
The preparation-era account below is retained; its pending choice is now resolved.

**October 16, 2026. No model admission, service or request has executed.**

The user requested a bounded local-model session through the new journal-first
flow, including whether setup is straightforward and prose remains easy to follow
as entries arrive. This folder prepares that check against the preserved **0.25.0**
package; it is not a new product release or prompt experiment.

## Proposed bounded execution

[Run plan](run-plan.json) selects the already qualified private `gemma3:4b` and exact
Ollama 0.40.5 runtime. It proposes four writing opportunities at 30/60/90/120 and
next-step application at 31/61/91/121, with a natural numerical limit of 121.
The attempt ceiling is four, with no retries. Source review confirmed that the
last prepared vector may still be applied after the attempt limit; the numerical
cap also permits at most four requests. The earlier five-attempt draft and its
incorrect rationale are retained in `run-plan.pre-review.json`; no admission,
freeze or execution used that draft.
Context is 8,192, output ceiling 1,024, temperature zero, generation deadline
180 seconds, inventory deadline five seconds, session duration 900 seconds,
storage 64 MiB and response bound one MiB. The owned service is limited to 1,200
seconds, with at least 1,140 remaining at Start.

The new 20% admission helper implements the already authorized provisional policy:
normal pressure level 1, at least 20% reported free memory and 8 GiB free disk,
with one attempt after a prospective input freeze. Its
[14 synthetic tests](admission-tests-01.json) pass. This is a policy-boundary test,
not a host-capacity observation. The original 30%/35% refusals are unchanged.

The unchanged supervisor and its 97-test qualification, original private model
selection/stage, installed software selection and 0.25 package identities remain
separate references. No diagnostic comparison runner will be used: any generation
must be initiated by the actual app session.

## Native entry obstacle

The [owned launch](ui-launch-01.json) produced PID 13340, which exited with no output
and an empty exclusive Library. Two exact-path desktop observations timed out;
bundle-ID resolution then reported multiple installed previews. A narrow process
inventory identified an already running **0.27.0** preview at PID 95075 from a
separate transferred candidate. This is consistent with the app's single-instance
behavior; it is not evidence of a failed model request or lost journal.

The [entry result](ui-entry-result-01.json) retains those observations. No controls
were sent to the other preview, and it was not closed. The user has been asked to
choose whether to quit that instance normally for this 0.25 check, leave the test
pending, or qualify the 0.27 build instead. It may hold active or unsaved work, so
its cleanup cannot be inferred from authorization for this isolated attempt.

An execution freeze and the one host admission remain unperformed while that
choice is pending. No result is labeled successful. There are no journals to read
from this attempt. Minime, Astrid and their services were untouched.

## Save point

The existing 0.25 source is already checkpointed at
`3cfbf1b7fba9ceacba2c5ad84bd9636c04496909` on
`codex/tauri-0.17-checkpoint`, with annotated tag
`reservoir-scope-tauri-v0.25.0-checkpoint`. A read-only remote check confirms the
branch and tag resolve to that commit; parent `0001b7a` is published through its
ancestry. Living checkpoint wording is corrected separately; historical receipts
are not rewritten.

Only this new preparation/entry account and the status corrections need a new
checkpoint so far. Once a selected bounded run is performed, retain every outcome,
verify saved evidence and owned cleanup, then review the new account before saving.
Actual compact-window geometry, current-build endurance/GPU attribution,
Windows/Linux and collaborator acceptance remain later qualification work. Those
open areas do not block an accurately scoped source-and-evidence checkpoint.
