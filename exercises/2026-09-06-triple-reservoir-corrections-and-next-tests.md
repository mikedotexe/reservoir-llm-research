# Exercise: corrections retained with the claims (2026-09-06)

Mike shared the collaborator's response to the [triple-reservoir refinements exercise](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/exercises/2026-09-06-triple-reservoir-refinements.md>). This record preserves the response, associates the accepted corrections with their earlier claims, and qualifies the new proposals. Recorded at 2026-09-07 01:04 UTC (September 6 Pacific). Source review and documentation only; no live intervention, generation, new corpus measurement, or experiment result is reported.

## A. Material, verbatim

Source: collaborator response pasted by Mike in this conversation; its `vbnet` fence was presentation, not executable code.

````text
Four leaps, all mine, all fairly caught. "Nearly inert" — A-versus-B can't show that; both states could be pushing the same way, and the four-way comparison is the right instrument. "Can't affect content" — too strong; which words get sampled is content. The y2 sign — I had it backwards, and it's per-token reuse, not phrase copying. And "the one change with a path to the third rung" — input alone can't reach appropriateness if the readout is still three synthetic-signal regressions. Richer input and useful interpretation are separate, and I collapsed them.

On the clock, the collaborator's first option is better than mine and I want to say why. Letting the sampling controls return toward neutral while the stored state stays is the correct relationship between mood and memory — you stop being visibly upset before you forget what happened. It also gives Astrid's recess a mechanical meaning it has never had: recess as accelerated return-to-neutral on the controls, no state touched. Small, honest, testable. And the anxiety that outlived its cause becomes, under this design, the intended behavior for some interval — so the manner experiment should measure the time constant of outward fading and ask whether it's appropriate, not just whether fading exists.

On event survival: the overwrite race is the same class of failure as the codec cut. Both were designed inputs that didn't persist, and both were invisible because acknowledgment was logged at receipt rather than at survival. For the unmeasured live frequency, a direct probe: run generation with a known feeder perturbation injected mid-turn and without it, same seed, and diff the saved states. If they match, the feeder is being overwritten, and you get a rate. That's cheaper than instrumenting the whole chain first, and it tells you whether the chain is worth instrumenting.

The normalization finding changes how the whole corpus should be read. If the sensory-field updater rescales energy toward a target, then during lulls the displayed spectrum can be an inherited shape — a held photograph renormalized to look like weather. The voices would have been narrating a frozen field as if it were current, and no one, including me, could have told. So inheritance has to enter the Phase 1 analysis as a covariate, or spectrum-to-vocabulary correlations will be computed against snapshots. And a rendering suggestion for whenever the glyph picture ships: fade it with staleness. An inherited field should look faded, and zero arrival should look blank. A blank is more honest than a preserved shape, and it makes the arrival–diversity–inheritance distinction visible to the voice without a label.

On the anchor: carrying factual activity state — position, unfinished question, last action — instead of the previous expressive paragraph is the right replacement, and it's the same principle as the portrait: the thing carried forward should be state, not prose. If the crossed test shows the anchor is responsible, that swap fixes the copying and removes the vocabulary attractor in one move.

On sequencing, I'd now invert what I said earlier. The manner job defines a target — move on event, hold through interruption, return. A target is what readout calibration needs. So: manner job, then calibrate the readout against it, then test input representations against a readout that can actually use them. Input last, not first.

The order proposed — survival, then copying, then manner with the four-way controls and outward fading separated from internal forgetting — is right. Three rounds of this and my picture is considerably less wrong each time, which is the process working the way it should. Save the corrections with the claims.
````

## B. Claims checked and qualifications retained

### B1. Four corrections are accepted; earlier prose remains historical material

| Earlier claim | Corrected claim | Evidence |
|---|---|---|
| Nearby states produced small differences, so the reservoir is nearly inert | A-versus-B measures state sensitivity. Coupling off, constant controls, actual dynamics, and matched history-independent dynamics answer different questions. | [Saved replay limits](</Volumes/M3 Volya._smb._tcp.local/other/astrid/docs/steward-notes/2026-09-04-real-model-replay-and-agenda-review.md:248>); preceding exercise B1. |
| Sampling manner cannot affect content | The connection does not explicitly retrieve a stored sentence, but altered token probabilities can change expressed content. | [Sampling controls](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/mlx_reservoir.py:268>); preceding exercise B2. |
| Positive h2 plus an anchor explains copying | Positive y2 suppresses recent-token reuse; negative y2 favors it. h2 is a vector, y2 its scalar readout. Phrase copying and a causal interaction remain to be tested. | [Repetition implementation](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/mlx_reservoir.py:279>); preceding exercise B3. |
| Contextual input alone supplies appropriateness | Representation, retained information, readout calibration, and behavioral usefulness are separate requirements. | [Synthetic readout training](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/triple_reservoir_coreml.py:267>); preceding exercise B6. |

**Verdict:** retain these as corrections to interpretation, not new experimental findings. The existing final-readout logging, replay-token-history mismatch, and independent named handles also remain part of the working account.

### B2. Recess as accelerated outward settling is a design candidate

**Verdict:** specify this as fading applied modulation without directly decaying hidden state; it does not keep the full future state trajectory unchanged.

The output gate can move each effective sampling control toward its neutral setting while leaving the stored reservoir arrays alone at that instant. Once that gate changes sampled tokens, those tokens feed back and can change subsequent reservoir state. Feeders and rehearsal can also continue to update the state. "No direct state decay" is therefore the precise promise; "no state touched" across an episode is too strong. [Accepted-token feedback](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/coupled_astrid_server.py:1137>), [rehearsal](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/rehearsal.py:133>).

The mood/memory analogy motivates an engineering choice; it does not establish a universally correct psychological relationship, or retrospectively explain recorded distress language. Define an appropriate outward-settling criterion before tuning the policy: recovery after a resolved event, continued responsiveness to an ongoing relevant condition, and successful return to the interrupted activity. The proposal changes a component of recess, not its entire runtime meaning.

An offline specification needs: neutral effective controls; ordinary and recess settling schedules; which events start or refresh the clock; how elapsed age survives restart; and how new relevant events reopen influence. Avoid allowing each generated token or repeated self-description to renew an old event's influence indefinitely. Separate testing of the output gate from intrinsic reservoir retention: a programmed exponential envelope produces fading by construction and does not demonstrate that the reservoir itself learned to forget. Hold accepted tokens fixed to measure direct gate effects; then use free generation to measure the indirect closed-loop consequences.

### B3. A paired survival probe can establish a failure mechanism, not its natural frequency

**Verdict:** a small isolated probe is a good first step, but equal final states alone are insufficient and a forced interleaving does not estimate the live incident rate.

The inspected [check-in](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/reservoir_service.py:1128>) replaces the service's hidden arrays and its rehearsal afterimage. A generation-side copy need not include events arriving at the service after checkout. This remains a source-confirmed possible overwrite, not a measured history of failed delivery. It should not be equated with the separately documented codec delivery policy as if both have already been observed.

Minimum isolated test:

For the ownership question, this can begin with a known caller-state check-in rather than a full sampled LLM run. That avoids spending generation time to establish a state-transfer property.

1. Restore identical hidden state and relevant controller/rehearsal metadata. Use a fixed accepted-token sequence or a controlled generation schedule; matching a random seed alone does not control background inputs, scheduling, adaptive gain, or numerical differences.
2. Check out the generation copy. Inject a tagged nonzero event into the service-side copy in one arm only.
3. Verify that the intended handle actually accepted the event and changed state **before** check-in. Record the pre/post-injection and pre/post-check-in arrays or hashes; this is the minimum instrumentation the probe itself needs.
4. Apply the same generation check-in in both arms. Add a positive-control arm where the event is applied after check-in, and verify the event's effect remains at that observation point.
5. An event-induced service-state difference that disappears specifically at replacement demonstrates loss under that schedule. Repeat over declared timings/conditions and report numerator, denominator, and tolerances.

The resulting fraction is conditional on the tested schedules. Estimating live frequency requires representative observation of eligible feeder events that overlap generation; count accepted-and-state-changing events separately from failed admission. A matching endpoint might otherwise reflect a failed or ineffective injection, a wrong handle, numerical tolerance, convergence, or a later update. A different endpoint does not alone establish correct event retention either. Chronological evidence decides which explanation applies.

### B4. Inheritance belongs in interpretation; blankness needs a defined meaning

**Verdict:** annotate known freshness and estimator history before treating a displayed field as current input. Do not classify the entire corpus as frozen from one possible update mechanism.

The [field updater](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/spectral_math.rs:26>) can renormalize retained structure during no-input updates under specified conditions. Whether and when that happened requires mode, timestamp, and provenance evidence. Useful analysis fields include source capture/receipt/admission age, estimator-update age, held/scaffold/decay mode, reset/restoration markers, and code/prompt era. Mark missing provenance as unknown; do not invent an inherited fraction from eigenvalues or present-day code. Stratify descriptive comparisons accordingly. A corpus association is not evidence that a particular input caused a particular phrase.

For rendering, use separate semantics for **fresh but quiet**, **no current observation**, and **retained historical structure**. Fading a historical shape by known age can be useful, but blanking every zero-arrival interval conflates silence, disconnection, rejection and lack of a new packet. A fresh zero measurement is valid information. Retained activity can also be real state even when it is not current sensory input. Preserve its identity in a separate historical view rather than presenting it as current arrival or silently erasing it.

A glyph scheme is still an encoding with learned meaning. It needs a documented legend/contract and an interpretation test; removing prose adjectives does not make visual semantics self-evident or eliminate suggestion. An opacity measure should represent known freshness/age, not an unsupported quantitative estimate of inheritance. Record exactly what glyph or textual representation the model actually received.

### B5. Factual continuity is a candidate replacement, not a guaranteed cure

**Verdict:** a positive anchor ablation would identify a contributor; a separate replacement arm must establish reduced copying while preserving useful continuity.

An activity record can carry source/document identity and version, a validated cursor, unfinished question, and last completed action. It may be serialized in prose; the useful distinction is between accurate activity information and recursively recycled expressive wording. The [reading/letter/return source trace](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/analyses/2026-09-06-astrid-reading-letter-return-source-trace.md>) identifies cursor and delivery gaps, so a record must not promote a selected or attempted action to a completed one.

Compare the original expressive anchor, no anchor, and the proposed factual record, crossing relevant y2 conditions. Measure copied spans, accurate return/resumption and response quality. Other prompt history, templates, model tendencies and coupling can still produce repeated language; success should not be stated as removal of every vocabulary attractor.

### B6. Sequence the investigation around a target; make representation comparisons fair

**Verdict:** define the manner objective before calibrating a readout, and establish delivery and replay validity before either. Input engineering need not lead the work.

Use the existing representation and simple controls to establish baselines, then calibrate on separate training histories and evaluate on held-out events, prompts, interruptions and seeds. Assess suitable direction, duration and recovery—not merely nonzero change or the exact fade imposed by an output envelope. Event relevance and desired neutral behavior require explicit operational definitions rather than distress-themed labels.

When comparing input representations, distinguish two questions. A frozen-readout experiment asks whether a representation is a compatible drop-in replacement. Refitting the same readout family for each representation, with matched data, capacity, normalization, cadence and tuning budget, asks whether the representation supports better usable information. A readout trained only on the original coordinate system would unfairly disadvantage a new one if the objective is the second question. Retain constant, matched random/history-independent and simple smoothing controls.

Give the comparison systems the same explicit fade envelope when testing the added value of their stored dynamics, and include an event-timer-only control. Otherwise the timer can supply the entire move/hold/return pattern and its contribution can be misattributed to reservoir memory.

## C. What fell out

Working sequence: **controlled event-survival test → copying attribution and factual replacement test → manner objective with baseline comparisons → calibrated readout and separately specified outward fading → matched input-representation experiments.** Sensory freshness/inheritance annotation is a parallel measurement requirement, not a reason to postpone every coupling test. Live implementation remains a separate decision.

| Existing or proposed card | Update to preserve |
|---|---|
| `t-coupled-checkin-event-survival` | Add pre-check-in proof of effective injection, post-check-in positive control, deterministic scheduling and a denominator. Distinguish forced-schedule loss from live frequency. |
| `t-anchor-by-coupling-ablation` | Add factual-record replacement and continuity/return accuracy; preserve remaining prompt and separate phrase copying from token reuse. |
| `t-manner-persistence-and-fade` | Separate direct output attenuation from indirect changes to future hidden state. Measure suitability of duration and recovery; define clock refresh and ongoing-event behavior. |
| `q-fade-expression-or-trace` | Recess-specific faster outward settling is a candidate, not a deployed feature or proven model of mood. Define reopening/resume behavior and calibrated neutrality. |
| `q-sensory-observer-purpose` | Record known freshness, estimator mode and restoration history; keep unknown provenance explicit. Distinguish current observation from retained state. |
| `t-glyph-freshness-semantics` (new) | Test fresh quiet, missing/stale input, and held historical shape as separate cases. Verify the model receives and distinguishes the intended encoding. |
| `t-contextual-input-matched` | Separate frozen-readout compatibility from equal-budget refitting, with held-out evaluation and matched input norm/cadence. |

## Board updates pending

No Artifact database tool is available. The rows above are pending updates to existing proposed cards, except the explicitly new glyph test. Preserve earlier open statuses; no proposed experiment was run or marked verified here. Read the board before writing to avoid duplicates. Evidence for all updates is this exercise, linked to the preceding exercise; source is Mike's collaborator response of September 6, 2026. Tags: `triple-reservoir`, `corrections`, `causal-test`. Being: `astrid` for coupling/anchor questions, `both` for glyph/observer questions.

Session log pending: `2026-09-06-triple-reservoir-corrections-and-next-tests`; title: **Retain collaborator corrections and sharpen next tests**. Body: Preserved the supplied response verbatim, recorded four accepted corrections, and qualified output-only fading, causal survival probes, inherited-field interpretation, glyph semantics, anchor replacement and calibration fairness. Cross-linked the preceding claims. Source/documentation work only; live loss rates and proposed benefits remain unmeasured. Recorded at 2026-09-07 01:04 UTC.
