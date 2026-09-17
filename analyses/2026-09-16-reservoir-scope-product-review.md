# Reservoir Scope · product review, September 16

Decision recommendation: make the next release a guided, observable research walkthrough. Existing offline mechanisms and evidence preservation are substantial. The product risk is that correct behavior is difficult to recognize, and a newcomer can mistake a valid no-change result for a broken experiment.

Audience assumption: an interested researcher who is new to reservoir computing. This is a source/example/presentation review, not an observed usability study. Inspected release: 0.12.0 build 16. The local installed package's source files match the current research checkout for ScopeWorkspace, ActionComparisonExperience and ActionComparisonViewModel.

## Current surface

Four work areas are visible: the A–H Actions & comparisons ladder (plus the separate observation comparison), Explore, original Stage experiments, and Minime & Astrid's recorded observatory. The observatory has six lenses. Runs & examples presents nineteen records in one bundled section, including duplicate stage titles differentiated by provenance and four model-preparation attempts. Headless tools and research studies provide an additional specialist surface outside the app.

The useful product center is A–H. Explore is a good sandbox. Original stage recipes deserve a secondary location. Recorded Beings and synthetic demonstrations need clearly separate entry points and a small explanation of their relationship. Evidence verification, failed-save recovery, import/export and offline operation are prudent infrastructure to retain.

## Concrete findings

The [read-only audit probe](../probes/reservoir_scope_product_audit.py) reads packaged records. Its [result](../research/outputs/2026-09-16-reservoir-scope-product-review.json) retains exact source identity and computed observations. No generation, live reader, production change or newly sampled Being journal was involved.

- **Replay Step semantics interrupt the intended walkthrough.** ActionComparisonViewModel.open detaches the session and loads a record. step advances an active session, otherwise calls begin with forceNew=true. Consequently Step on an opened example starts a fresh experiment instead of moving its recorded cursor. Next journal does move the recorded cursor. Fix this before using “journal at 30, then Step to 31” as an onboarding instruction. This is a code-path finding; no new presented-app execution test was performed in this review.
- **The primary visual often shows the wrong result for the lesson.** In the scripted comparisons, C, D, F and H have identical reservoir-state trajectories across arms. That is valid. C adds a separate observer; D adds text; F changes prompt memory with fixed replies; H changes sensory retention/fill. The central state display remains dominant while sensory values and prompts are secondary. Make the relevant component prominent for each lesson.
- **The strongest current demonstration is E.** Matched states remain identical through step 30; the first difference is at 31 when saved journal feedback is applied. This provides a concrete first walkthrough milestone.
- **F demonstrates memory delivery, not improved writing.** At step 60 the earlier journal is in the memory-enabled prompt; the fixed replies and reservoir states remain identical. The recorded model F example is single-arm, so it is not a controlled memory-effect comparison.
- **G's choice demonstration depends on provenance.** Its scripted example waits at step 90; the current recorded model G and H examples write at all three opportunities. A model choosing WRITE is a valid outcome. Do not repeat model calls until a desired WAIT appears.
- **H does not demonstrate target attainment in its current bundled recipe.** At step 120 the unregulated and regulated reduced fills are approximately 15.19% and 15.34%, while the controller target is 68% and regulated retention has reached its 0.995 limit. It does demonstrate changed sensory behavior and a bounded controller. A separate 600-step qualification fixture in MechanismTests demonstrates lower target error under matched sustained random input; that is a different fixture and evaluation window.
- **The observation comparison samples a quiet reservoir.** Its actual 32 coordinates reach a maximum magnitude about 0.847 during the run, but at journal steps 30/60/90 their largest magnitudes are about 1.14e-6, 4.36e-7 and 1.08e-6. The forcing recipe is twelve steps on/eighteen off, so every journal occurs at the quiet end. The recorded comparison remains valid, but gives a weak range of state observations. Specify a new matched-input example with active state at writing opportunities before generating it; preserve the original protocol and recordings.
- **The architecture needs a visible explanation.** The ordinary ladder's prompt observes the separate sensory field fed by input. The large reservoir picture is not implicitly sent to the model. Show the actual information paths and explicitly mark the extra state channel in the separate controlled comparison.

## One clear demonstration for each step

| Step | Expected observable | Walkthrough focus |
|---|---|---|
| A | State responds while input is on and decays while it is off | Input/state traces with marked on/off interval |
| B | Matched initial state, then recurrence changes the trajectory from step 2 | Highlight preceding-state contribution |
| C | Added sensory measurements; reservoir remains matched | Observer field/spectrum beside a small state view |
| D | A saved journal at step 30; state still matched | Prompt and journal, with provenance |
| E | Journal saved at 30 is applied at 31 | Pause on both sides of the application boundary |
| F | Earlier journal enters the prompt at 60 | Highlight exact added memory; fixed response may stay identical |
| G | Scripted WAIT at 90 creates no journal and retains prior semantic input | Requested action, choice and actual outcome |
| H | Controller changes retention and sensory measurements | Target/error/retention; distinguish lower error from reaching a limit |

Different model prose is not an improvement criterion. The walkthrough should identify mechanically unchanged results explicitly rather than add visual motion to imply an effect.

## Recommended next release

1. **Repair replay navigation and add a guided route through the existing examples.** One primary action per moment; distinguish Continue replay, Step, Next journal and Start new experiment. Open at A as already specified. Use predetermined observation stops, not a requirement to watch every simulated tick. Existing direct stage access remains available.
2. **Give every lesson a question, a concrete instruction and a computed observation.** For E: “Does writing change state immediately?” → journal at 30 → step 31 → “First difference: step 31.” Offer “Show evidence” for prompts, coordinates and receipts. Expected result, observed result and interpretation must remain separate.
3. **Make the view follow the component.** Promote sensory measures at C, prompt/journal at D, feedback timing at E, prompt differences at F, choices at G and controller traces at H. Add a small persistent information-flow diagram. Preserve shared numerical scales; label any magnification.
4. **Reduce decisions in the introduction.** Move Explore and original recipes behind an advanced entry. Put seed, fixed-tape/independent mode, endpoint/model settings and display controls in appropriate optional sections. Keep a simple persistent Scripted / Recorded model / Fresh local label. Group qualification failures under Preparation history while retaining access and exports.
5. **Curate two additional numerical demonstrations before any new model batch.** A bounded regulation example with a predeclared lower-error expectation, and a state-observation example with nontrivial state at the writing opportunities. Preserve the saturation/quiet cases as useful contrasting examples. No fresh model run should promise a particular conclusion or be selected for pleasing prose.

A later small research-results page could connect these mechanisms to two or three reviewed real cases: exact journal, supplied evidence, supported/unresolved claim, any linked code change, verified activation and later observations. S-006 and S-007 remain observational work with separate evidence. A comprehensive study-management UI is not necessary for the next release.

Avoid adding more stages, providers, dashboards, agent loops or a single fidelity score in this pass. The existing checks and retained failures are valuable; exposing all their details simultaneously is unnecessary.

## Proposed product acceptance test

A newcomer on a disconnected Mac, without coaching, should be able to complete an approximately fifteen-minute route, locate the first journal, explain the step-30/31 distinction, identify what memory adds to the prompt, recognize a WAIT, identify what regulation actually changed, and export/reopen a comparison. Ask the person to point to the evidence for each answer. This test has not yet been run; it tests understandability beyond the existing numerical, transport and persistence qualification.

## Board updates pending

Artifact and authenticated board-control capabilities are unavailable. Pending planning payload only:

- c-reservoir-scope-replay-step: change, open, system. Step should advance an opened recording's cursor; preserve an explicit new-experiment action. Evidence: view-model open/step code paths.
- design-reservoir-scope-guided-route: design, open, system. Deliver A–H instructions, stage-appropriate views, observable stops and plain expected/observed summaries. Keep advanced access and scientific boundaries.
- t-reservoir-scope-newcomer-route: test, open, system. Disconnected uncoached walkthrough with evidence-pointing tasks and export/reopen.
- q-reservoir-scope-example-contrast: question, open, system. Specify active-state observation and bounded regulation examples before new generation; preserve current quiet/saturation examples.
- Log 2026-09-16-reservoir-scope-product-review: audited current source, saved presentation evidence and bundled numerical records. Product changes are recommendations, not implemented by this review.
