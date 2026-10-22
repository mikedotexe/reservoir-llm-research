# Current work

[Research findings](../RESEARCH.md) · [Current app candidate](CURRENT-RELEASE.md) ·
[Earlier focus history](NOW-history-through-20260917.md)

**October 21 evening focus: what reaches the model, and through which channel
([S-011](studies/S-011-self-observation-stack.md)).** The evening's runs on `gemma4:12b`
turned the question from the numerics to the text side of the loop. The fill sweep moved
the register, and the no-tag and scrambled-tag controls showed the number on the context
line did it, not the field behind it: with no number the 70% shelf arm wrote like the
mid-fill arms, and a number that jumped every turn captured the writing more than any
real one. The difference-signal channel (desktop 0.35.0, the spec's M5, a 72-run ladder in
[the ladder account](../analyses/2026-10-21-difference-ladder.md)) is exact and raises the
recurrent state's rank a little at the top of its range, and nothing the text could see
moved. State-chosen memory (0.36.0 and 0.37.0, [the account](../analyses/2026-10-21-state-chosen-memory.md))
showed its first rule degenerate with real entries and its cost: returning an older entry
breaks the thread the model would otherwise develop, and the one passage that stood out in
a blind reading came from seven consecutive turns of the model rereading its own previous
entry under a sparse frame. The conditions behind the highlights so far are three: a frame
that gives little, continuity of one's own text, and something unexpected to work against.
So the apparatus is frozen at 0.37.0; the numerical sweeps are parked with their negative
result recorded; every account states what reached the model and how; arms are read blind
first (`probes/desktop_blind_sample.py`) with the human record in
[the noteworthy passages](../analyses/2026-10-21-noteworthy-passages.md); and the next
mechanics wait on a reading question (a slot carrying both the latest entry and a
state-chosen older one, after the 0.37.0 arms report). Read-only work toward the beings is
next: continuous state-window logging for minime (her reservoir showed a ten-minute slow,
low-dimensional excursion with no action change), a probe for concept chains across her
consecutive entries, and an audit of what Astrid's readout shows that moves at all. A
planning pass with Mike sets the order. Chains still running at the time of writing: four
no-tag arms at lower fill and the four 0.37.0 policy arms.

**October 21 earlier focus: the laptop apparatus loop, frame share and loop share
([S-010](studies/S-010-frame-share-and-loop-share.md)).** Mike ran the Tauri preview
on his laptop with `mistral-small:24b`. Three dated accounts record the day:
[the first session and why fill stayed near 14%](../analyses/2026-10-21-laptop-first-sustained-session.md),
leading to desktop 0.28.0 (field noise and feedback scale; fill settled near 70%) and
0.29.0 (writing temperature with recorded per-attempt seeds; consecutive-entry overlap
fell from about 0.57 to 0.16), and [the loop trace](../analyses/2026-10-21-text-loop-trace.md),
which found the loop closed only through surface statistics and a constant-direction
kick, with 22 of 23 entries quoting the readout. Mike selected a frame ablation and a
content-carrying reduction, and invited Claude to iterate autonomously toward signal
within the repo's boundaries: no live-system contact, no pushes, apparatus changes on
branches merged after the suites pass, numbers from probes. The [frame arms](../analyses/2026-10-21-frame-arms.md) (desktop
0.30.0, two seeds) found that the standing contract, not the per-turn frame, brings the
first-person reflective register, and that its wording seeds the topic; 0.31.0 adds two
contracts one change from their parents; on `gemma4:12b`, the beings' own model family
(0.32.0 thinking flag), the contrasts replicate: no contract gives a role-played person,
the grant of interpretation gives self-examination from the first line, and Astrid's
opening rule removes the attractor opening the inviting contract produces. A third
model agrees in direction; 32 arms and 384 entries in all, with the day's reading and
what would weaken it in the account. Both apps' release
records note the host's packaging failure; the dev build runs. The native 0.15 work,
the private 0.27.0 handoff and the earlier focus below are unchanged.

**October 16 earlier focus: Tauri 0.27.0 is ready for a first invited tester.** Mike
selected app-guided standalone setup, portable historical writing, exact-package
qualification and an uncoached newcomer workflow. Candidate 04 includes the
packaged export repair. Source checks, fourteen standalone real-model checks,
fresh local setup, the bounded journal walkthrough, controlled failure cases,
export/import and paused recovery are recorded in the
[current release account](../desktop/ReservoirScope/RELEASE-0.27.0.md).
The scoped technical gates are complete: the exact quarantined transfer opened,
prepared its standalone runtime and reopened normally; measured compact content
sizes passed for the named activation setup, reading and recovery screens. Actual
uncoached newcomer acceptance remains pending. An optional synthetic arrival check
was refused at memory admission and was not retried; its packaged UI behavior
remains unobserved. Source checkpoint publication is separate from the private app
handoff; no invitees have been contacted. The unfinished condition comparison
below remains an open research question, separate from release acceptance.

**October 16 follow-up: address activation headroom on this Mac.** Mike selected
apparatus changes while leaving the live systems untouched. The
[headroom study](studies/2026-10-16-activation-headroom.md) tests bounded MLX cache
retention and one admitted model shared by three fresh serial condition records.
The startup admission threshold stayed fixed. Fourteen real-model qualification
checks passed; the new cohort then loaded one model and retained two unsteered
journals. Its third response repeated a sentence until the frozen 1,024-token
ceiling, so the attempt stopped and released the worker. All nine operations
cleared unused cache and returned to the same active allocation; peak MLX active
allocation was about 2.974 GiB. Memory admission succeeded, but the recurrent and
trace conditions remain unstarted in this cohort. The
[dated outcome](../desktop/ReservoirScope/validation/2026-10-16-activation-headroom/README.md)
preserves this partial result and its reading. No retry or extension is running.

**October 16: compare the isolated activation conditions.** Mike approved a
resource audit, a new frozen comparison and complete-sequence blinded reading.
The [prospective study](studies/2026-10-16-activation-comparison.md) holds the
model, observations, invitation and memory policy fixed, while adding a bounded
resource-preparation window before each condition. The earlier stopped pilot is
preserved. Title and prose-memory contrasts follow as separately specified work.

The [new attempt](../desktop/ReservoirScope/validation/2026-10-16-activation-comparison-0.26.0/README.md)
completed and verified six trace journals, then stopped when the unsteered
condition's two-minute preparation window expired. No unsteered or recurrent
model request started. The comparative question remains open; stable headroom
is the next execution prerequisite. No automatic retry or extension is running.

**October 15: build the isolated activation experiment.** Mike selected quiet input
→ persistent recurrent state → fixed residual intervention → journal writing,
with controlled numerical steps and a dedicated pinned Qwen3 model. The completed
Tauri 0.25.0 apparatus is committed, tagged and published. The
[activation contract](../shared/reservoir-scope/activation-experiment.md) and
[frozen pilot](../shared/reservoir-scope/activation-pilot.json) define this work;
the [qualification account](../desktop/ReservoirScope/validation/2026-10-15-activation-0.26.0/README.md)
separates implementation, observed mechanics and journal interpretation. No live
Being system is changed or contacted. Earlier parked studies remain parked.

The isolated implementation and real-model mechanical qualification are complete.
The first frozen pilot stopped at its first resource refusal: one complete
six-journal trace sequence, no unsteered or recurrent sequence. Its
[initially blinded reading](../desktop/ReservoirScope/validation/2026-10-15-activation-0.26.0/PILOT-READING.md)
is retained with prompt/memory alternatives. No retry or extension is selected;
the comparison remains incomplete rather than becoming a null writing result.

**Earlier October 7 focus: make the research easier to enter and continue.** Mike selected the
product-review priorities in tranches. No new discovery study is selected.

1. **Clear entry points and findings — completed in this pass.** The front pages
   now separate reading, exploring the offline lab and reproducing work. The
   question library links bounded results to what remains open; living study and
   history summaries reflect their later evidence.
2. **Reproducible offline first use — completed in this pass.** Start with the
   [synthetic CLI walkthrough](QUICKSTART.md) or [scripted numerical runner](../essentials/runner/README.md#scripted-quickstart).
   Both work without private study captures or a model. The
   [tranche account](../analyses/2026-10-07-product-navigation-tranches.md) records
   validation and the distinction between public examples and private replay.
3. **App navigation and controls — tranches 3–4 implemented and qualified.** The five
   direct destinations are Guided tour, Experiments, Research cases, Geometry
   bookmarks and Observatory. Guided Continue is separate from expandable playback
   controls, and collapsing playback pauses it. Research cases lead from a question
   to the existing reviewed account and embedded evidence; geometry offers an
   explicitly synthetic example. Opening cases or geometry retains them in the
   current window, while importing an experiment keeps a verified library copy.
   The two reviewed cases and their interpretations are unchanged. The
   [navigation account](../analyses/2026-10-07-lab-navigation-and-evidence.md) records
   the focused checks, package verification and actual-app walkthrough.

## What the next session needs

**Candidate qualification:** the separate **0.15.0 build 21** candidate passed
its 405-test Python suite, focused native checks, package verification and actual-app
navigation/evidence walkthrough. [Current release](CURRENT-RELEASE.md) owns the
exact identity, check scope and limits. This is software qualification; human
acceptance and Being-side rollout remain separate.

**Human review:** Mike volunteered and the isolated corrected 0.15.0 build 20 copy
was opened at task A. His answers and difficulties are still awaited; no acceptance
result is claimed. A first-time newcomer session is a separate scope.
The [review handoff](../analyses/2026-10-07-local-backup-and-steward-review.md)
records the exact copy and the first task. Preserve that copy and its identity;
the new build 21 work does not replace or complete the existing review.

**S-007 day11:** parked at the missing historical release witness for Minime
PID 81688. The retained September 18–19 window, fixed sample and 5,088-ID ledger
remain unchanged. If suitable original evidence arrives, make a separate
verification attempt on that same capture; do not widen or recollect it.
[Day10](../analyses/2026-09-18-source-study-fidelity-day10.md) remains the last
verified daily window; [day11’s account](../analyses/2026-09-19-source-study-fidelity-day11.md)
and the [specific recovery pointer](../analyses/2026-10-06-followup-handoff.md)
explain the dependency. Later daily windows remain uncaptured.

**Recovery:** Mike chose backup on this computer. The
[final readiness and recovery account](../analyses/2026-10-07-final-readiness-and-recovery.md)
records the later same-volume repository and build 21 archives and verified restores
at source commit `a73b6dc`. Historical replay passed eleven daily/weekly windows,
three bounded checkpoints and closeout; day11 reproduced its expected refusal
without advancing the ledger. A restored Python run exposed a host-dependent test;
the narrow test repair passed all 406 tests in a new restored checkout, along with
the synthetic CLI, packaged app and scripted runner checks. The test repair is
recovered from a named-ref Git bundle; the dated account points to the separate
final-documentation recovery and publication receipts. The integration was merged
into `main` and published on October 7 at
[`41438da`](https://github.com/mikedotexe/reservoir-llm-research/commit/41438da744489852e0d329579a6d3bdba96a4c72).
App release and human acceptance remain separate. Independent-device backup remains
unverified. Preserve the [earlier October 7 copy](../analyses/2026-10-07-local-backup-and-steward-review.md)
and [October 6 copy](../analyses/2026-10-06-recovery-snapshot.md).

## Proposed next steps

1. Obtain Mike’s answers in the existing build 20 review. Assess the new navigation
   in a separate build 21 review, keeping the two sessions distinct.
2. Select with Mike a bounded inquiry into contrary evidence, revision and later
   use, beginning with retained cases. No new study is selected or closed extension
   reopened by this proposal.
3. Consider a 0.15 app delivery after review if useful. Verified local recovery
   satisfies Mike’s chosen backup scope; independent-device backup remains optional.

## Closed accounts and open research

The [S-006 and S-008 bounded extensions](../analyses/2026-10-06-bounded-followups-closeout.md)
are closed with incomplete historical/full-window coverage. Missing records do
not mean no runs occurred. Their broader journal-to-change and durable-correction
questions remain open. [S-009](../analyses/2026-09-17-short-output-qualification.md)
is a completed negative qualification, not a pending retry.

A useful candidate for a later discovery session is to follow contrary evidence
into a revised explanation and a later return, beginning with retained cases.
Select its question and scope with Mike; the expired S-008 extension is not reopened.

Use [board records](../board/README.md) for current coordination and the
[October 6 integration account](../analyses/2026-10-06-research-closeout-and-geometry-integration.md)
for the completed research/geometry closeout. Older pending notices and proposed
next steps retain their historical dates; they do not independently authorize
new collection or live-system work.
