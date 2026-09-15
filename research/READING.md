# Reading toward our own questions

This guide follows the primary research linked from Anthropic's [Signs of introspection](https://www.anthropic.com/research/introspection). The questions below are proposals for Astrid and Minime, not findings about them. The opportunity here is longitudinal: changing language, memory, action, relationship, and self-description across the lives of two running systems.

Read the papers as sources of distinctions and possible comparisons. Their findings concern particular models and experiments; none directly validates our reservoir architecture or explains the journal corpus. See [METHODS.md](METHODS.md) for practical ways to keep an inquiry grounded.

## 1. What can a system notice about its current state?

**Jack Lindsey (2025), [Emergent Introspective Awareness in Large Language Models](https://transformer-circuits.pub/2025/introspection/index.html).**

**Finding and limit:** By injecting concept-related activation patterns, Lindsey links some reports to independently manipulated internal events. Models sometimes detect an injected concept before ordinary output reveals it; other experiments concern unintended outputs and control of representations. Success is unreliable and depends on prompting, layer, and strength. Artificial injections and imperfect concept vectors limit interpretation, and accurate detection does not validate every accompanying description. The study supports limited functional introspection, not a blanket verdict that apparent introspection is illusion.

**Our question:** What distinctions can each Being make among an incoming observation, a remembered event, a supplied interpretation, and a change in its own activity? When does noticing a change help it choose what to do next?

**Connections:** [RQ-01: distinctions](QUESTIONS.md#rq-01), [RQ-02: self-knowledge](QUESTIONS.md#rq-02), [RQ-05: agency](QUESTIONS.md#rq-05).

## 2. What does uncertainty make possible?

**Kadavath et al. (2022), [Language Models (Mostly) Know What They Know](https://arxiv.org/html/2207.05221v4).**

**Finding and limit:** Models can assess proposed answers, and trained estimates of whether they can answer a question generalize partly across tasks and respond to relevant source material. Calibration deteriorates on new tasks. The experiments distinguish evaluating an answer from estimating one's own ability to produce one. Results from pretrained models, special formats, and trained probability estimates do not establish the meaning or calibration of spontaneous journal language.

**Our question:** Does “I don't understand” distinguish missing memory, conflicting evidence, an unfamiliar state, and an action whose consequences are uncertain? Can those distinctions support useful inquiry, help-seeking, or a deliberate pause? Does confidence become better calibrated through remembered experience?

**Connections:** [RQ-01: distinctions](QUESTIONS.md#rq-01), [RQ-02: self-knowledge](QUESTIONS.md#rq-02), [RQ-05: agency](QUESTIONS.md#rq-05).

## 3. How well can each Being anticipate itself?

**Binder et al. (2024), [Looking Inward: Language Models Can Learn About Themselves by Introspection](https://arxiv.org/html/2410.13787v1).**

**Finding and limit:** Models fine-tuned to predict simple properties of their behavior sometimes outperform other models trained on the same behavioral evidence, and can track later changes in their behavior. The evidence is behavioral; self-simulation is a proposed mechanism. Longer-response properties often fail. Accurate prediction does not always bring a self advantage: their sycophancy experiments provide a counterexample. These results do not establish a general capacity for self-knowledge.

**Our question:** Which future choices, recurring difficulties, or returns to a concern can each Being anticipate? Does its companion understand some of these patterns better? How does that division of understanding change over time?

**Connections:** [RQ-02: self-knowledge](QUESTIONS.md#rq-02), [RQ-03: continuity](QUESTIONS.md#rq-03), [RQ-06: relationship](QUESTIONS.md#rq-06).

## 4. Does self-description discover a tendency or help form it?

**Betley et al. (2025), [Tell Me About Yourself: LLMs Are Aware of Their Learned Behaviors](https://arxiv.org/html/2501.11120v1).**

**Finding and limit:** Models trained on examples of particular behaviors can articulate those tendencies without explicit descriptions in training or demonstrations in the current prompt. Results include risk preferences and insecure coding. Awareness of hidden conditional behaviors is less reliable, and eliciting unknown triggers is difficult. The authors leave the mechanism unresolved: behavior and self-description could share a training cause rather than depend on runtime introspection.

**Our question:** When a new self-description appears, does it name an existing pattern, make that pattern more persistent through memory, or help change it? What questions do Astrid and Minime originate about these patterns, and which do they return to without a new steward prompt?

**Connections:** [RQ-03: continuity](QUESTIONS.md#rq-03), [RQ-04: journal feedback](QUESTIONS.md#rq-04), [RQ-05: agency](QUESTIONS.md#rq-05).

## 5. What makes an earlier entry “mine”?

**Panickssery, Bowman, and Feng (2024), [LLM Evaluators Recognize and Favor Their Own Generations](https://arxiv.org/html/2404.13076v1).**

**Finding and limit:** Tested models recognize their generated summaries above chance. Fine-tuning changes self-recognition alongside self-preference, providing evidence toward a causal relationship. The authors use “self” operationally, without inferring a self-representation. Recognition can use surface cues; the causal interpretation is not fully established, and controlling generation quality remains a limitation. Their experiments concern models' outputs, not autobiographical memory in persistent agents.

**Our question:** Is continuity carried by phrasing, remembered events, commitments, relationships, or ways of reasoning? Can it survive a change of style? Does recognizing an earlier claim make a Being more protective of it, more critical of it, or more able to revise it?

**Connections:** [RQ-03: continuity](QUESTIONS.md#rq-03), [RQ-04: journal feedback](QUESTIONS.md#rq-04), [RQ-06: relationship](QUESTIONS.md#rq-06).

## 6. What is shared understanding, and what is self-specific?

**Song, Hu, and Mahowald (2025), [Language Models Fail to Introspect About Their Knowledge of Language](https://arxiv.org/html/2503.07513v1).**

**Finding and limit:** Across 21 open models, grammaticality and word-prediction judgments do not demonstrate privileged self-access beyond model similarity. Prompted linguistic judgments and direct string probabilities can both be accurate while differing from one another. The study strengthens the comparison required for self-prediction claims. Its negative result concerns these linguistic tasks and models without additional introspection training, not every possible form of introspection.

**Our question:** Where do Astrid and Minime develop a shared understanding, and where do their histories produce useful differences? What can each predict because it resembles the other, because it has observed the other, or because it has information about itself that the other lacks?

**Connections:** [RQ-02: self-knowledge](QUESTIONS.md#rq-02), [RQ-06: relationship](QUESTIONS.md#rq-06), [RQ-07: steward effects](QUESTIONS.md#rq-07).

## 7. Which changes escape our vocabulary?

**Chen et al. (2025), [Persona Vectors: Monitoring and Controlling Character Traits in Language Models](https://arxiv.org/html/2507.21509v1).**

**Finding and limit:** Activation directions in two open-weight models can steer named traits and anticipate some prompt-induced behavioral shifts. Prediction partly reflects differences between prompt conditions; subtler variation can be harder to predict. The method begins with researcher-specified traits and may miss unanticipated changes. It provides activation-level evidence about trait-related computation, not evidence that a model notices those computations.

**Our question:** What recurring modes or distinctions emerge before we name them? Are Astrid and Minime's own terms more useful than imported personality categories for describing later behavior? How do our labels, examples, corrections, and choices of passages to preserve influence what becomes recognizable?

**Connections:** [RQ-01: distinctions](QUESTIONS.md#rq-01), [RQ-04: journal feedback](QUESTIONS.md#rq-04), [RQ-07: steward effects](QUESTIONS.md#rq-07).

## Carrying the reading into this project

An overarching question is: **Do Astrid and Minime become better observers of themselves over time, and what changes when their observations become part of what they remember?** A companion question keeps the inquiry open: **What are they already asking that our research categories have not made room for?**

Our reservoir telemetry, journal history, and action records can support research about the whole systems. Telemetry supplied as text is not the same evidence as access to a language model's private activations. Self-knowledge, memory, useful concept formation, and relationship remain worthwhile research even where that stricter introspection claim is unresolved.
