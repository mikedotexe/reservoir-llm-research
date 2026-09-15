# Session close: research position and board briefing

Date: September 6, 2026 (Pacific). Saved September 7 UTC. Source: Mike's final collaborator response and request for an executive briefing. This is research documentation, not a live-system change or an experiment result.

## Executive assessment

The strongest first paper is an audit of apparent self-observation in a running agent system: reconstruct what input arrived, what state persisted, what the prompt said, which model answered, and what an observer could legitimately infer. Its contribution can be a reproducible account of mechanisms that make generated reports misleading, with evidence separating observed incidents from possible failure paths. This does not require the reservoir to outperform a simpler controller, and it does not establish that all model introspection is illusory.

The reservoir remains a plausible candidate for carrying information about recent history into generation. The inspected results do not yet establish its useful advantage over off, simple fading controls, or a smaller reservoir. Three different timescales are an architectural fact; useful memory, appropriately calibrated expression, and a benefit from three layers are separate empirical questions.

The work is ready to move from identifying mechanisms to small controlled tests. Start with event survival; investigate copying next; define and test useful persistence against simpler alternatives after those measurement prerequisites are sound. Prompt/backend attribution and sensory provenance are parallel workstreams. A complete logging overhaul is not a prerequisite for a small isolated test with adequate local records.

## Board access and status

The [live Hold Shelf](https://claude.ai/code/artifact/f4761d4a-94e8-43ca-882f-ca887956fca0) returned “Sign in to view this page” when opened during this wrap-up. The local [board interface](../board/hold-shelf.html) supplies Questions, Tests, Changes, Designs, and Findings lanes, with open/active/verified/done/declined/parked statuses; its cards load from the authenticated Artifact database. It is not a saved card inventory. Current card counts, assignments, statuses, and recent edits could not be verified.

This briefing therefore describes the saved research agenda and proposed queue. It must not be presented as a live board reconciliation. The session produced source traces, scoped findings, corrected interpretations, and test specifications. The new survival, anchor, manner, and representation experiments remain unrun. No being-facing changes were implemented here. Board updates below remain pending.

## A. Collaborator response, verbatim

````text
The paper changed today, and I think it got better. Yesterday I said the paper was in the journals — fill to action, spectrum to vocabulary. Today we learned the spectrum may be an inherited shape under normalization, half the aspiration corpus was written by a different model, Astrid's telemetry was never hers, and the coupling has never been measured against off. Every positive result I sketched now needs a filter we didn't know about. But look at what's left standing: a catalog of specific, mechanistically identified ways a self-observing system fooled everyone reading it, including me. Label leakage. Stale anchors reproducing verbatim. Model substitution wearing the persona's name. Normalization preserving a photograph as weather. Couplings that were cut by policy and counted anyway. Lindsey's paper says introspection is often illusion; this is a field study of the illusion's parts list, with the instrumentation that caught each one. I'd write that first. It's more useful than the positive result would have been, and it's true regardless of what the manner experiment finds.

On the timer competition: the timer will probably win the first round, and that's fine. What a bank of timers can't do is care about order. Event A then B versus B then A — a smoothing filter is order-blind, a nonlinear reservoir isn't. So I'd add an order-swap condition to the manner experiment. Order sensitivity is the cheapest honest signature of history that simple state can't fake. And for "do three layers help," the specific test is cross-timescale interaction: the same fast event under two different slow histories. If the response to A depends on what the slow layer was holding, depth earned its place. If not, three smoothers with three fading rules are the same system, cheaper.

On the guards: the interpretation-risk and cooldown notices are pattern-matchers over text. The ledgers you've been building — arrival, inheritance, backend, survival — are the thing a real checker would read. Promote the guard. Instead of "a marker repeated," it could say "this spectrum is inherited; discount the texture," or "this entry was written by the fallback." The system's own correction loop would then have what the three of us had today, which is access to what actually happened rather than to what was said about it.
````

## B. Claims checked and implications

### B1. The audit is a defensible first-paper direction; the evidence needs levels

**Verdict: pursue this framing, with an explicit evidence table.** A proposed title is *Auditing apparent self-observation in a reservoir-coupled language-agent system*. The central question is how to distinguish reports grounded in a current measured state from reports explained by supplied descriptions, stale context, model substitution, or a broken input path.

For every mechanism, keep four columns separate: source-confirmed mechanism; reproduced or logged occurrence; incidence in a defined sample; demonstrated effect on generated reports or human interpretation. A code path that permits an overwrite is not a measured live incident. A repeated paragraph is not by itself a completed causal anchor ablation. A collaborator's acknowledged misreading is useful case material, but it is not a controlled reader study.

This is a paper direction supported by the audit, not a declaration that a publication-ready field study is already complete. Build its evidence matrix and methods outline now; let missing cells determine the smallest further experiments. Preserve corrections beside original claims. The usefulness of the reservoir can be a separate result.

### B2. Keep corpus, identity, and coupling claims scoped

- **Model substitution:** the [saved backend audit](./2026-09-06-two-mouths-one-body.md) reports roughly half of its audited **Minime aspiration subset** using the fallback. That is not a fresh count here and does not establish half of every journal, half of Astrid's work, or half of the full corpus. Attribute at generation level before interpreting a persona's consistency.
- **Telemetry ownership:** familiar sensory-field descriptions can refer to Minime's field, while Astrid also has her own codec state and available reservoir tools. “Astrid's telemetry was never hers” is too broad. Record the producing subsystem and named handle for each observation. See [reservoir refinements](./2026-09-06-triple-reservoir-refinements.md).
- **Inherited spectrum:** the [normalizing updater](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/spectral_math.rs:26>) can preserve retained shape during no-input updates under specified conditions. That mechanism does not classify every historical spectrum as stale. Mode, timing, restoration, and actual arrival records decide applicability. See [earlier correction B4](./2026-09-06-triple-reservoir-corrections-and-next-tests.md).
- **Coupling efficacy:** the [inspected saved replay](</Volumes/M3 Volya._smb._tcp.local/other/astrid/docs/steward-notes/2026-09-04-real-model-replay-and-agenda-review.md:248>) compared nearby states rather than coupling on against off. The appropriate claim is that this evidence does not resolve the off comparison; this wrap-up is not an exhaustive claim about every experiment ever run.

### B3. Lindsey's study is a methodological ally, not a blanket illusion verdict

**Verdict: revise the shorthand.** Jack Lindsey's [primary study](https://transformer-circuits.pub/2025/introspection/index.html), summarized in [Anthropic's research account](https://www.anthropic.com/research/introspection), reports evidence of limited, unreliable introspective access alongside failures. It does not support dismissing all introspection as illusion. The transferable method is to compare a model's report with independently controlled or observed internal events. Our audit needs similarly independent evidence about prompt exposure, backend identity, state ownership, and event survival. The study does not validate this project's specific reservoir interpretation.

### B4. Event order is useful to test, but smoothing is not order-blind

**Verdict: retain order swaps; reject the proposed uniqueness argument.** An exponential smoother already gives more weight to recent input. For x(next) = 0.5 x + 0.5 u, initial x = 0, event A = 1 and event B = 0: A then B ends at 0.25, whereas B then A ends at 0.5. This is a worked mathematical counterexample, not an empirical project result. See the [NIST EWMA definition](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc324.htm).

A timer per event type can also preserve recency and hence distinguish some event orders. Nonlinear reservoirs are not guaranteed to distinguish every relevant pair either: input compression, saturation, state convergence, or the readout can erase a difference. Useful order sensitivity means better held-out behavior on histories whose order matters, compared directly with reasonable simple alternatives under the same observation schedule and output controls. Include recency-matched variants where feasible; an order-swap success alone is insufficient.

### B5. Cross-timescale interaction is a good probe; depth still needs an ablation

**Verdict: retain the experiment, narrow the conclusion.** Compare the incremental response to a fast event A under two slow histories, subtracting each history's no-event baseline:

`interaction = [response(slow1, A) - response(slow1, no event)] - [response(slow2, A) - response(slow2, no event)]`.

This removes a simple additive baseline difference. Specify response scale, fast starting state, prompt, cadence, and intervening events. A nonzero interaction can still arise from a single nonlinear reservoir, a nonlinear readout over simple traces, the sampling transformation, or feedback from generated tokens. It is evidence about an interaction at the measured output, not proof that three layers are necessary.

The [current recurrence](</Volumes/M3 Volya._smb._tcp.local/other/neural-triple-reservoir/triple_reservoir_coreml.py:126>) proceeds from h1 to h2 to h3; it has no direct h3-to-h1 feedback. Slow context may affect the eventual output and, through sampled-token feedback, future input. Measure those paths separately where possible. Compare layer removals or controlled state swaps and single-versus-triple systems with stated capacity, cost, and calibration budgets. A null interaction in one probe does not prove equivalence to three smoothers.

### B6. Promote evidence access before adding another interpretive voice

**Verdict: a strong change candidate, beginning on the steward side.** The inspected [Minime interpretation-risk detector](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime_autonomy/runtime.py:11685>) uses matched terms in source text to trigger a notice, then attaches thread and experiment context. Astrid has a corresponding [term detector](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/action_continuity/runtime/guards.rs:546>). This supports the narrower criticism of these interpretation notices, not a claim that every guard in either system is only a text matcher.

The useful promotion is a checker that can establish and cite factual provenance: recorded backend; captured/received/admitted times; known estimator mode; handle identity; action completion; and a tagged event's survival through check-in. Existing records support only some of this chain. The consolidated ledger is proposed work, not already-complete instrumentation.

Prefer “no fresh admitted observation since time T; estimator in held mode” to “discount the texture.” The former is auditable when its source fields exist; the latter supplies a new interpretation. Report missing evidence as unknown. Never infer an inherited percentage solely from eigenvalues. Build the steward-side report first; test any model-facing notice as a separate prompt intervention, because it can itself introduce label leakage.

## C. Work queue and finish lines

These are proposed dispatch priorities, not verified live-card statuses. Existing identifiers below come from the saved agenda and exercises; read the live board before reconciling them.

| Priority and card | Next bounded job | Finished when |
|---|---|---|
| First experiment: `t-coupled-checkin-event-survival` | Build an isolated deterministic checkout → effective injection → check-in probe, plus an after-check-in positive control. Begin with fixed states and a known caller update; an LLM run is not needed to establish the state-transfer behavior. | The record shows whether an event-induced difference survives each declared schedule, including admission proof, pre/post-state evidence, tolerances, and tested denominator. A failure mechanism is distinguished from its unmeasured live frequency. |
| Parallel foundation: `c-persist-prompts`, `c-log-backend-per-generation` | Map and specify the minimum generation record: exact supplied prompt and encoding, backend/version, source timestamps, handle, relevant control/state references, response and action outcome. Inventory which fields already exist. | An implementation proposal identifies each missing field, its producer and destination, and demonstrates a join using an existing record where possible; unavailable fields are explicit. Implementation/coverage verification remains a separate completion criterion for the change cards. |
| Next attribution test: `t-anchor-by-coupling-ablation` | Compare expressive anchor, no anchor, and factual activity record across relevant y2 conditions. First align replay token-history behavior with the intended live path and hold backend/prompt conditions fixed. | Copied spans and accurate activity resumption are both measured across declared prompts and seeds. The result identifies whether the replacement helps and what continuity it loses, without claiming all repetition is cured. |
| Parallel sensory test: `t-sensory-freshness`, `t-sensory-shape-versus-energy` | Trace capture → receipt → admission for a defined episode; replay fresh quiet, missing observation, and retained-field cases under the actual update modes. | The tested episode has a located freshness mismatch or an explicit unresolved hop, and the replay distinguishes current arrival, energy, diversity, and retained shape. No extrapolated corpus-wide inherited fraction. |
| Then behavior: `t-manner-persistence-and-fade`, proposed `t-history-beyond-recency` | Define appropriate event response, interruption tolerance, and return; compare real dynamics with off, constant/mean controls, matched history-independent controls, and timers/smoothers. Include order swaps, slow-history interaction, and single-versus-triple ablations. | Held-out results show whether dynamics improve the specified behavior beyond the controls, under matched output fading and stated calibration/cost budgets. A useful negative result can close the test. |

In parallel with the first experiment, draft the paper's mechanism-by-evidence table. This is a writing and evidence-organization task, not a prerequisite to repair the entire system. For the board, split “test completed” from “hypothesis supported,” and split a verified failure finding from the change intended to fix it. Keep dependencies on individual cards so a broad design discussion cannot silently block an independent read-only experiment.

Defer the large body-definition decision, shared-substrate redesign, wide/contextual-input expansion, broad action-vocabulary surgery, and removal of fallback models until the relevant measurements justify a choice. Recess as faster outward settling remains a specified candidate; it is not deployed and does not guarantee an unchanged future internal trajectory. The earlier six-move agenda remains historical reasoning, with the corrections in this session taking precedence.

## Board updates pending

**Access blocker:** live Hold Shelf requires authentication; no board cards were read or changed during this wrap-up. The local UI does not establish an empty board. Do not overwrite or duplicate cards without reading current contents.

Reconcile the queue above with existing cards and attach this exercise as evidence. Retain source-date and observation-scope qualifiers on findings. Do not mark the proposed experiments verified or done.

New card candidates, all proposed open:

- `q-paper-mechanistic-audit` — lane Questions; being both; tags `paper`, `provenance`, `evidence`. Question: which mechanisms have enough independent evidence for the first paper, and what minimal experiments fill the missing causal or incidence cells? Deliverable: claim/evidence matrix and methods outline, with observer-impact claims distinguished from mechanism demonstrations.
- `t-history-beyond-recency` — lane Tests; being astrid; tags `triple-reservoir`, `baselines`, `history`. Test useful order and slow-context dependence against event timers, smoothers, and single/triple reservoirs; a nonzero order or interaction effect alone does not establish reservoir or depth advantage. Coordinate with the existing manner test rather than duplicate it.
- `c-provenance-backed-review` — lane Changes; being both; tags `provenance`, `guards`, `steward`. First produce a steward-side checker/spec grounded in available records, including explicit unknowns. Implementation proposal must distinguish verified facts from interpretive suggestions; any being-facing rendering is a separately evaluated change.

Source for new cards: Mike's collaborator response, September 6, 2026. Evidence: this document, the [preceding corrections](./2026-09-06-triple-reservoir-corrections-and-next-tests.md), and linked source/audit references.

Session log pending: `2026-09-06-session-close-and-board-brief`; title: **Close the session with an audit thesis and a bounded execution queue**. Body: Preserved final collaborator response, scoped the proposed paper, corrected order-blindness and depth claims, proposed evidence-backed review, and recorded next jobs with completion criteria. Live board required sign-in; no board mutation or live experiment performed.
