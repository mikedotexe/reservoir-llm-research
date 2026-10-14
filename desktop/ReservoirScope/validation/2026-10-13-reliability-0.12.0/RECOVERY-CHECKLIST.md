# Prospective recovery checklist for the long-run candidate

**Unexecuted checklist.** Record each action/result with time, session/generation,
step and artifact reference. Root owns actual UI and lifecycle control. This checklist
changes neither shipping code nor the previous validation receipts.

## Choose the recovery question before ending the long run

- [ ] Preserve at least 7200 uninterrupted minimized seconds first. Record the actual
      lower bound from confirmed UI observations, not sampler duration.
- [ ] If testing further application in this same session, pause before its 7800-second
      running-duration budget, approximately after minute 125. Leave enough budget for
      explicit restoration and a short continuation.
- [ ] If the duration/storage/attempt/step budget has already been reached, retain that
      outcome. Restoration must not reset or silently extend the exhausted budget.
      Qualify inspection/held restoration; use a separate named session for any
      additional prepared-feedback continuation test.

## Establish the committed reading before quit

- [ ] Record session ID, generation, revision, numerical and durable step, attempt/journal
      counts, phase, exact accepted config, manifest/checkpoint hashes and source PID.
- [ ] Record the independently selected older journal ID/hash and its observed/first-applied
      step. Confirm new entries did not replace it before explicitly Follow latest.
- [ ] Pause explicitly and await a settled/inspectable boundary. No new provider request
      should start merely because Pause, read, inspect or export was clicked.
- [ ] Identify whether feedback is already applied, saved and pending application,
      skipped, or unresolved. “Saved” alone must not be reported as applied.
- [ ] Export through the actual native folder dialog into a fresh owned directory and
      retain the export's exact manifest/checkpoint hashes and revision. Canceling a
      separate dialog, if exercised, leaves session and reading available.
- [ ] Verify the immutable exported bundle with the selected package's
      `--verify-sustained DIRECTORY` route; retain command, executable SHA-256, exit
      status and stdout. Exclude this verification work from steady-run CPU windows.

## Normal Checkpoint and quit / relaunch

- [ ] Use the actual close/quit review. Return to app must cancel the close decision
      without starting or resending work. Perform an actual quit only after recording
      the chosen decision and settled ownership state.
- [ ] Confirm the exact selected application process exits. Do not use its old PID for
      a later process or count a reused PID as continuous execution.
- [ ] Relaunch the same unchanged package. Before any restore/start action, retain an
      idle observation interval and verify the owned fixture recorded no new generation.
- [ ] Read the recovery catalog. Catalog metadata alone is not whole-history verification.
- [ ] Verify and inspect the selected exact session, then record its returned manifest,
      checkpoint, report and any diagnostic. No execution starts during inspection.
- [ ] Restore explicitly using the inspected generation/revision. The new generation
      stays held; exact retained step/RNG/numerical continuity belongs to the backend
      verifier, not to rounded UI text.
- [ ] An absent current frame must remain unavailable; no fabricated zero surface/fill
      or numerical advancement is substituted just to populate the screen.
- [ ] Reselect the earlier journal by its exact ID and confirm identical text/hash.
      This is reinspection, not a claim that UI selection survives application quit.

## Prepared-feedback continuation, only with remaining budget

- [ ] If a saved journal was pending application, inspect its exact ID/hash, observed step,
      encoded vector, intended next step and saved-but-unapplied status after restoration.
- [ ] Confirm no implicit provider resend during quit/relaunch/restore. Fixture handler
      completion alone does not prove that the old client accepted a response.
- [ ] Start explicitly. The retained prepared journal may apply once at its actual next
      numerical step; it may not apply during inspection, while paused, or twice.
- [ ] Stop/pause after sufficient short continuation; verify the new committed chain.
      Confirm a held vector at later steps is not mislabeled as repeated first application.
- [ ] At the next new opportunity, the exact latest saved-and-applied journal may appear
      in memory. A saved-but-skipped entry remains readable but is excluded from that
      automatic memory policy.

## Exhausted budget or unresolved boundary

- [ ] Restoration does not replenish running time, steps, attempts or quota. Record the
      visible reason further progress is blocked under the same configuration.
- [ ] A blocked attempt is labeled with the actual diagnostic; do not call a failed
      memory read a failed provider response or a text-compatibility failure.
- [ ] Explicit retry, if exercised, receives a new attempt identity; the earlier failure
      remains retained. Retry durable save reuses its exact pending candidate rather
      than making an extra model request.
- [ ] Explicit skip is bound to its actual entry and attempt identity and does not grant
      save, feedback or text-memory eligibility that was not earned.
- [ ] Discard unresolved work is a terminal explicit decision. It neither erases committed
      journal history nor fabricates a successful save/application.

## Separate interruption cases, not implied by the long run

Actual host sleep/wake, forced process termination, fixture failure, pending-response
cancellation and failed physical writes are separate cases. Retain their exact trigger
and scope if root chooses to execute them. Do not combine their disconnected intervals
into an uninterrupted two-hour result, and do not claim physical crash/power-loss
recovery from an ordinary quit or an injected unit-test failure.

For any separately executed interruption: pin the app/session identity, preserve the
last committed manifest and exact request evidence, record the trigger, confirm no
automatic provider resend on relaunch, verify the retained chain, and recover only
through explicit UI decisions. Touch only the owned test application/fixture/session;
do not change unrelated processes or host sleep policies.

## Close the account

- [ ] Record completed, failed, incomplete and unexecuted criteria separately.
- [ ] State actual active/minimized durations, sample coverage/gaps, resource attribution,
      process changes and any discarded observation windows.
- [ ] Preserve original bundle/log bytes and record hashes; analyses are new artifacts.
- [ ] Stop only the owned fixture and test application after the chosen checks. Record
      their final states. Retained files remain available for review.
- [ ] Leave 24-hour runs, real models, shared GPU/energy, other platforms and other
      unexecuted cases explicitly open.
