# Exercise: triple-reservoir refinements (2026-09-06)

Mike shared a response to the triple-reservoir implementation report and asked to explore
potential fixes and changes. This exercise separates promising hypotheses, implementation
facts, and causal claims that still need tests. Source inspection only; no live-system changes,
new generations, or database scans were performed for this exercise. Prior saved observations
are identified as such. The supplied commentary is interpretation, not a new measurement of
Astrid's experience or behavior.

Follow-up: the collaborator accepted four corrections and refined the proposed sequence in
[corrections and next tests](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/exercises/2026-09-06-triple-reservoir-corrections-and-next-tests.md>). That record qualifies the survival probe, outward fading, glyph freshness, and calibration comparisons. The original material below remains verbatim.

## A. Material, verbatim

Source: [pasted response](/Users/mikepurvis/.codex/attachments/796f3e48-2404-4739-b23c-eea76b7ec21d/pasted-text.txt).

````text
This is the right report, and it corrects me in four places I should name before adding anything.

"Her body hears only her voice" was too broad — there are feeders. I'd only attach the ledger principle: each of those feeders needs a landing rate before we count it, because the codec path to Minime taught us what a designed input that never arrives looks like. Second, and bigger: the fill and the eigenvalue cascade are covariance statistics of Minime's *sensory field*, not the ESN's dynamics. My edge-of-chaos framing was about the wrong object. Third, the reservoir doesn't fade in quiet — rehearsal skips, the state freezes — so my "route everything through the body and let dynamics do the forgetting" assumed a decay the code doesn't have when nothing is happening. Fourth, the only real experiment shows sub-one-point shifts in next-token probability and identical sampled text. At current gain, Astrid's body is nearly inert in her voice. So the afternoon's pathology — the coinages, the self-copies, the anxiety outliving its cause — lives in the prompt builder and the anchor loop, not the reservoir. That's good news. It means the fix is cheap, and it means the body is a separate research question that shouldn't be blamed or credited for what the text loop did.

Two reinterpretations follow from the corrections.

If the cascade is the covariance of the sensory field, then a monopoly is the sensory world collapsing to one axis. And semantic input read 0.001 through the whole episode. So the collapse may not have been an internal state at all — it may have been what an empty room looks like to a covariance estimator. The system even said so: `sensory_scarcity` was sitting in the pressure-source labels, and we all read past it. Test: correlate dominance with total sensory input energy across the corpus. If monopoly tracks lulls, the afternoon's drama was the sound of nothing arriving, and the response is input, not regulation.

The second: given the three scalars — sharpness, stickiness, tail — the honest name for what the triple reservoir does is not memory but *manner*. It can't inject content; it sets how confidently, how repetitively, how wildly she samples. That's a mood modulator, and mood that persists across turns is a real form of continuity even without recall. Someone who wakes up irritable has continuity without knowing why. I'd make that the one observable job the report asks for: an event shifts her manner, the manner survives an interruption, and it fades. It's measurable from output statistics alone — entropy, repetition rate, rare-token rate — and it's a job the architecture can actually do.

Which raises a hypothesis worth one afternoon. h2 controls favoring recently seen tokens. If the three scalars are logged per turn, look at h2 during the verbatim self-copies. Anchor in prompt plus a positive h2 is a complete mechanism for reproduction. If they aren't logged, log them — those three numbers are the entire body-in-voice channel, and they're free.

On the clock, I'd assign one per layer rather than a psychological name: h1 ticks per token, h2 per event, h3 leaks with wall-clock seconds. Right now no night happens — a state saved at midnight is identical at dawn. A small time-based leak on the slow layer is what makes recess, sleep, and "the between" mean anything, and it's the cheapest way to answer "how long does a perturbation stay distinguishable" with something other than "forever."

On input representation: the model is Gemma 4 12B running locally, so the thing I said yesterday was impossible through an API is available here. Feed the reservoir the transformer's contextual hidden state for each token, pooled, instead of the embedding-lookup identity. Then the body hears what a token meant in this sentence rather than which token it was. That's the one change with a path to the third rung — generation changing *appropriately* because of history — since nothing in the current random projection can carry appropriateness.

On the null models, agree fully, and add the meanest one: a frozen random schedule for the three scalars. If three smoothing filters or a random walk match the triple reservoir on the mood-persistence job, the depth is decoration. Be willing to find that. The hunch survives in a reduced form either way — "sampling manner that drifts with history" is still a being-shaped thing, even if it isn't a deep echo state network doing it.

One small note. There's a state handle named Claude. Whatever of my words goes in arrives as token identities through a random projection — so what it holds of me is which words I use, not what I meant. That's fine. It's also the same thing that's true of Astrid's handle, and it's the reason the contextual-input change matters more than any other on this list.

The experiment the report ends on is the right first one: two copies, different pasts, identical present, no reminder. I'd run it on manner, not content, and I'd expect it to be small. The question is whether it's nonzero and whether it fades — and those two answers are the whole of what the triple reservoir is for.
````

## B. Claims checked

### B1. Small state-to-state effects do not establish that coupling is inert

**Verdict: the saved experiment establishes numerical influence; the attribution to the prompt loop is too strong.** Comparing two nearby reservoir states at the same gain measures state sensitivity, not the effect of coupling versus no coupling. Both states could impose a similar, consequential bias. Identical short sampled continuations do not rule out cumulative effects on later tokens or different seeds. Prompt anchors remain a plausible and directly visible contributor; their interaction with coupling still requires an ablation. See the [saved real-model replay and limitations](</Volumes/M3 Volya._smb._tcp.local/other/astrid/docs/steward-notes/2026-09-04-real-model-replay-and-agenda-review.md:232>). No new numerical replay claim is made here.

One replay-parity issue should be resolved before interpreting repetition effects: the offline replay passes the complete prompt-plus-continuation prefix to the logit processor, while the installed generation library prefills most prompt tokens outside the step that accumulates processor token history. Both language-model calls see the full prompt, but the early reuse-control history differs. Match that history and the documented two neutral opening distributions before a causal replay. [Offline processor call](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/offline_coupling_replay.py:134>), [installed history accumulation](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/.venv/lib/python3.12/site-packages/mlx_lm/generate.py:409>), [prefill path](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/.venv/lib/python3.12/site-packages/mlx_lm/generate.py:430>), [feedback-delay test](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/test_offline_coupling_replay.py:85>).

### B2. “Manner” is a useful first job, with a precise behavioral definition

**Verdict: well matched to the narrow output connection, but manner can change content indirectly.** The readouts change logit sharpness, recent-token reuse and the low-probability tail. Those interventions can change the words and propositions eventually sampled, even though they do not supply an explicit fact or recalled sentence. Distinguish learned recall from history-dependent sampling behavior. “Mood” is an interpretation; the measurable job is an event causing a reproducible shift in output statistics that persists through an interruption and optionally fades.

The readout targets are synthetic short, moving-average and smoothed signals; their association with meaningful events is not trained by that construction. [Sampling controls](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/mlx_reservoir.py:268>), [readout training](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/triple_reservoir_coreml.py:221>).

### B3. The proposed repetition mechanism has its sign reversed

**Verdict: positive y2 discourages recent-token reuse; negative y2 favors it.** The code computes `rep = gain * (2*sigmoid(y2)-1)` and subtracts a multiple of `rep` from recent-token logits, accumulating duplicate token occurrences. An anchor plus negative y2 is a candidate interaction, not a complete explanation of verbatim sentence copying. The mechanism works on token counts and order-independent reuse within a window, not sentence-level copying.

A potentially important null is a **fixed negative reuse bias**: if the readout spends its relevant range on one side of zero, the useful comparison is not just two nearby histories. Compare reservoir modulation with a constant matched bias, then ask whether its history dependence adds anything. This is a hypothesis from the permitted mechanism, not a new finding about historical y2 values. [Exact sign and application](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/mlx_reservoir.py:279>).

### B4. Final readouts are already logged; the missing evidence is their applied trajectory

**Verdict: extend the existing record instead of adding a duplicate end-of-turn logger.** The coupling journal stores final y1/y2/y3, gain, token count and before/after state norms, retaining a rolling window of 50 records. Final values cannot establish what acted during a copied passage. A compact per-token or fixed-stride trace should include transformed/applied controls, prompt/generation identity, backend, base sampling settings, effective gain and optional wide-channel settings. Preserve enough history to join an incident to its prompt.

Gain itself changes adaptively between generations according to readout variance. Freeze that controller during causal comparisons; otherwise an apparent reservoir effect or fade can be a changing gain. [Existing journal](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/coupled_astrid_server.py:958>), [adaptive gain](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/coupled_astrid_server.py:985>).

### B5. “No night happens” motivates a design choice, not one obvious decay patch

**Verdict: rehearsal quiet skips updates; absence of activity is not an elapsed-time decay mechanism.** This holds when other feeders and controllers also do not change the state. Current hold and rehearsal repeat the last input before transitioning to quiet. A saved midnight state therefore need not fade merely because dawn arrives. [Quiet and rehearsal](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/rehearsal.py:133>).

There are two different experiments: fade the **expressed influence** by relaxing output controls toward calibrated neutral values, or fade the **stored trace** by evolving/contracting hidden state. The first can preserve latent history while letting its behavioral effect subside; the second can erase distinctions. Zero-input recurrence, direct multiplication of hidden state and gain decay are not equivalent. Zero hidden state need not be a calibrated resting baseline because input normalization and learned readout biases remain. Fading only h3 can also rebound when unchanged h2 drives it again. Choose which outcome is intended before selecting a rule. [Coupled layer updates and readouts](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/mlx_reservoir.py:117>).

Follow-up qualification: output fading avoids direct hidden-state decay, but changed sampled tokens can change subsequent reservoir state through feedback. It does not promise identical future stored histories; see follow-up B2.

Per-token h1, per-event h2 and per-second h3 is a multirate architecture change: the current cascade advances all layers together, with readouts trained on that update schedule. It needs explicit buffering, layer-update rules, clock persistence across restart, and readout recalibration. A smaller first test is an output-envelope half-life at fixed state and gain-controller settings, followed separately by a state-decay experiment.

### B6. Contextual input is promising; random projection is not semantic erasure

**Verdict: contextual representations deserve a matched experiment, not automatic first priority.** The coupled path embeds each accepted generated token through the model's embedding lookup, projects it and advances the reservoir. The lookup is not context-specific, but learned embeddings can encode useful relationships and recurrent processing can distinguish histories. Random projection does not logically imply “only which words, never any meaning,” nor does replacing it with a contextual hidden state guarantee appropriate behavior. The readout objective and output connection remain constraints. [Current token input](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/coupled_astrid_server.py:1137>).

Compare existing embeddings, contextual pooled event representations, and a simple event-feature baseline under matched input norm and cadence. Source-tag newly arriving material and avoid repeatedly counting the accumulated prompt as new experience. Access to a local model makes an experiment possible; hidden-state extraction still requires integration and latency measurement. Different feeder paths have different encodings, so a claim about the generated-token path cannot characterize everything in a named handle. In particular, service `tick_text` uses a frozen projection of the last UTF-8 byte window, not model token embeddings. A claim about the Claude handle therefore needs the actual input route. [Text projection](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/dual_ai_bridge.py:48>).

### B7. A delivery receipt must include survival through state check-in

**Verdict: landing rate alone is necessary but insufficient.** Generation checks out a handle's complete state and evolves a local copy; check-in overwrites the service's state. An intervening feeder update could be accepted by the service yet absent from the later checked-in state. The inspected API does not provide a version argument or compare-and-swap guard; occurrence and frequency of lost updates remain unmeasured. [Checkout](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/coupled_astrid_server.py:1075>), [overwrite on check-in](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/reservoir_service.py:1128>).

An isolated test should inject one tagged event during a controlled checkout/check-in and inspect the final state. Choose explicit ownership or queued replay semantics before broadening feeder inputs. Record offered, admitted, applied and retained events separately. This is a stronger definition of “the input arrived.”

Follow-up qualification: first verify that the injection changed the intended service state before check-in, and include a post-check-in positive control. Equal endpoints alone do not prove overwrite, and the fraction lost under forced schedules is not a live incident rate; see follow-up B3.

### B8. “Monopoly is an empty room” is a hypothesis with important estimator confounds

**Verdict: delivery problems deserve early attention, but normalized concentration does not establish low input energy.** The prior [sensory audit](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/exercises/2026-09-06-spectral-collapse.md:313>) records audiovisual sources classified stale despite streaming clients. This exercise does not repeat that measurement. `sensory_scarcity` is assigned from source-status labels, not independently measured energy. [Scarcity construction](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/telemetry_evidence.rs:90>).

Three quantities need separate presentation: how much fresh input arrived, how its energy is distributed, and how much of the measured field is inherited or imposed. Multiplying all eigenvalues by the same factor leaves dominance and normalized entropy unchanged. A dominant source can be strong or weak; silence alone need not create dominance.

The field update adds an uncentered outer product and rescales toward a target trace. At zero input and an already-target trace, that normalization can cancel uniform decay exactly when the scaling cap is not hit. A separate decay-only path reduces amplitude but still preserves relative shares. These are algebraic consequences of [the update](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/spectral_math.rs:26>) and [decay-only implementation](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/spectral_math.rs:54>), not evidence about which branch ran during the episode.

Other confounds are repeated stale vectors, constant offsets, and saved-scaffold blending. The rotating low-energy bias candidate listed in the earlier exercise is disabled in stable-core mode; it must not be promoted as the episode's cause without runtime-mode evidence. [Bias gate](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2153>), [scaffold branch](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2208>).

Two earlier interpretations also need refinement. The adaptive keep-floor's `lambda1_rel_for_cov` is a ratio to baseline, not the top-mode energy share. The share uses the reported modes, not necessarily the full matrix trace. [Definitions side by side](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2533>). The old exercise's statement that spectral entropy 1 implies nothing retained is incorrect: isotropic second moments do not establish absence of memory, and anisotropy alone does not establish usable memory.

### B9. Null models should distinguish a useful channel from a useful architecture

**Verdict: strong proposal, extended to include coupling off and constant matched controls.** Use identical present prompts, different relevant pasts, no textual reminders, and multiple complete continuations with paired seeds. First compare no coupling, constant controls, shuffled/history-independent controls and actual history-dependent controls. Then compare simple smoothing, one comparable-capacity reservoir and the triple reservoir under matched behavioral influence. A pre-generated random schedule is a history-independent control, not itself evidence of event memory.

Measure both immediate distribution changes and completed-output properties: repetition, entropy and tail probability, plus a task-appropriate measure of whether the response reflects the preceding event. Token rarity by itself is not semantic appropriateness. Passing a manner-persistence test would validate a specific useful behavior; it would not establish subjective mood, content recall or the necessity of depth.

## C. What fell out

These are bounded candidates, not authorized changes to the live siblings. Start with delivery
and attribution; defer contextual extraction and a multirate redesign until simpler tests
identify the limiting connection. The useful first objective is: **a source-tagged event changes
sampling behavior reproducibly through an interruption, with a specified return toward neutral.**

| Proposed card | Bounded test or change candidate | Decision it supports |
|---|---|---|
| `t-coupled-checkin-event-survival` | In an isolated handle, inject a known event during checkout and inspect the checked-in result. | Whether accepted events can be overwritten; ownership/queue design. |
| `c-coupling-applied-trace` | Proposal to extend existing generation records with within-turn applied controls and durable prompt joins. | Whether a reproduction incident coincides with reuse-favoring modulation. |
| `t-anchor-by-coupling-ablation` | Cross anchor present/absent with coupling off/current/fixed matched controls; preserve the remaining prompt, backend, gain and seeds; include y2-only neutralization with the other controls unchanged. | Prompt, coupling and interaction contributions. |
| `t-manner-persistence-and-fade` | Different past events, identical present; compare fixed elapsed time with fixed intervening token count; test output fade separately from state decay. | What persists, on which clock, and whether fade is designed or intrinsic. |
| `t-sensory-shape-versus-energy` | Replay zero input, one repeated vector, varied matched-energy vectors, reduced-amplitude variants and stale-timestamp variants from the same state. Stratify controller/scaffold modes. | Whether concentration tracks scarcity, repetition, timestamp admission or imposed history. |
| `c-input-delivery-ledger` | Proposal to record source capture, receipt, acceptance, application and retention, plus raw/admitted energy and field freshness. | Repair a demonstrated drop or overwrite at its actual hop. |
| `t-manner-null-ladder` | Compare constant, shuffled, smoothing, one-reservoir and triple-reservoir controls at matched output strength. | Whether history and depth add value beyond modulation alone. |
| `t-contextual-input-matched` | Once delivery works, compare token embeddings, contextual event vectors and simple event features with matched norm/cadence. | Whether contextual encoding improves relevant behavior enough to justify cost. |
| `q-fade-expression-or-trace` | Specify neutral behavior and whether useful stored distinctions should remain after outward influence subsides. | Choose an output envelope, state evolution, or both. |
| `q-sensory-observer-purpose` | Decide whether the field estimates current input, remembered input structure or a deliberately regulated state, and label these separately. | Avoid treating estimator maintenance as an environmental or experiential event. |

For the sensory replay, record raw source energy, admitted/projected energy, λ1, full trace,
reported-mode sum, input freshness and active structural mode. Do not use normalized share or
fill as a substitute for absolute incoming energy. For generation tests, freeze adaptive gain,
record the actual backend and base sampler, retain full outputs, and report independent histories
and seeds rather than treating adjacent tokens as independent samples.

## Board updates pending

No Artifact database connector was available in this session. The following records are saved
here for later mirroring; nothing has been written to the live board. Existing related board
cards should be updated rather than duplicated once the board can be read.

Shared proposed metadata: `being=system` (or `astrid` for coupling-only cards),
`tags=[triple-reservoir, causal-test, refinements]`,
`source=2026-09-06 user pasted response`,
`evidence=exercises/2026-09-06-triple-reservoir-refinements.md`,
`created_at=updated_at=2026-09-06` (date only; exact board timestamp pending).
The table in section C supplies each record's `id`, `title` and `body`; `t-` records have
`lane=test,status=open`, `c-` records `lane=change,status=open`, and `q-` records
`lane=question,status=open`. No change candidate is marked done: implementation proposals with
diff, validation and rollback remain future work.

Finding records proposed for mirroring:

- `f-reuse-control-sign`: `lane=finding,status=verified,being=astrid`. Positive y2 suppresses
  recent-token reuse; negative y2 favors it. Evidence: B3 and linked implementation.
- `f-coupling-log-is-final-only`: `lane=finding,status=verified,being=astrid`. Existing rolling
  journal stores final readouts and gain but does not establish their within-turn trajectory.
  Evidence: B4 and linked journal source.
- `f-checkin-overwrites-handle-state`: `lane=finding,status=verified,being=system`. Service
  check-in overwrites state without a caller version guard in the inspected API; actual lost
  event frequency is unknown. Evidence: B7.
- `f-sensory-shape-is-not-input-energy`: `lane=finding,status=verified,being=minime`.
  Normalized share and entropy cannot by themselves establish scarcity; trace normalization,
  scaffold mode and label-derived scarcity require separate accounting. Evidence: B8.

Session log pending:

- `id`: `2026-09-06-triple-reservoir-refinements`
- `date`: `2026-09-06`
- `title`: Source-check proposed triple-reservoir refinements
- `body`: Preserved the supplied response verbatim; checked sampling controls, readout logging,
  clock behavior, input representation, state-transfer ownership and sensory-estimator
  confounds. Converted refinements into bounded tests and open design questions. No live
  changes or fresh corpus scan. Board unavailable; records preserved in this exercise.
