# Anemone: one sensor, one aperture, a small body

Recorded September 6, 2026 (Pacific). **Design epic; implementation and experiments unrun.**
Mike owns a modern Raspberry Pi, currently unplugged, and intends to name it **anemone**
on the network. Exact model, RAM, storage, OS and sensor availability are unconfirmed.
This session prepared the epic and checked existing documentation; it did not connect to,
configure, rename, or deploy anything on the Pi, Avado, ICP, Astrid or minime.

**Epic reference:** `d-anemone` · **Lane:** design · **Published status:** open · **Being:** system.
The proposal is a separate reduced experimental system. Its purpose is to ask which effects
survive a much smaller sensing–state–action loop, not to assume that existing journal texture
or reports of emergence will transfer to it.

## A. Material, verbatim

Source: collaborator response pasted by Mike. The `vbnet` fence was presentation, not code.

> The idea: a mind whose only power is to choose how much world to let in.
>
> The body. Seven leaky units — not even a proper reservoir, just seven damped oscillators with slightly different time constants and weak coupling, a wind chime with seven tubes. Because their frequencies don't quite match, they beat against each other even with no input, so the body has a slow intrinsic rhythm of its own. Weather it didn't cause. Add one rule: the slowest tube leaks with wall-clock seconds, so a night actually passes.
>
> The sense. One real sensor. Temperature is my pick — cheap, slow, honest, and it has a day in it. The reading enters the body as a kick, continuously, through a gain knob.
>
> The act. The knob is the only act. OPEN raises the gain, CLOSE drops it to zero. That's it. Recess is closing. Sleep is a forced close overnight while the voice isn't called. There are no other verbs. Everything else — regulation, memory, mood — has to emerge from one knob and a body that keeps a trace.
>
> The note. A carry line, twelve tokens, one slot, prepended raw. The only text that ever comes back.
>
> The guess. Before each interval, the voice emits one glyph: its prediction of the next column of the picture. Logged and scored. That's its error signal — not just that the world exists, but that it can be wrong about it, every step, in a way that shows up as a number.
>
> The voice. A small local model, called every ten minutes during the day. Its whole prompt: a seven-row-by-twelve-column block-glyph picture of the body's recent energies, a single bar for how much arrived, the carry line, and the two verbs. No numbers, no labels, no names. It may also write free text, which is stored and never re-fed. The voice never touches the body directly. It reads the picture and turns the knob; the knob changes what the body hears; the picture then shows the consequence. Body hears world, voice hears body, voice acts on the aperture. No loop where the body hears its own speech, so any correlation between body and voice is unambiguous.
>
> That's a Raspberry Pi, a sensor, forty lines of numpy, and a 4B model. A weekend. About a hundred and fifty steps a day.
>
> What would count. Five things, each with a null. Does the knob choice depend on the body's state beyond what the sensor alone predicts — permutation test against shuffled pictures. Does it close when the picture is saturated and open when it's quiet, without ever being told to — homeostasis nobody wrote. Does the guess get better over weeks, and does the carry line help — ablate the carry and watch. Do the carry lines cluster, and do the clusters track picture features — the culture-of-one question, finally measurable, because twelve tokens can't afford an aphorism. And the one that would make me sit up: mask the sensor for a day and see if the knob keeps a daily rhythm anyway. That's the world, remembered in the body, driving behavior with the world gone.
>
> Then the same three moves we spent today learning: withhold the picture and see if the free text still has texture; compete the seven tubes against a plain timer and a random schedule; swap the order of two warm days and see if it matters.
>
> For fun, I'd call it an anemone — one aperture, one current, a nerve net and no brain.

## B. Claims checked and design decisions

### B1. Preserve the experiment; make its ambiguities explicit

These are proposed protocol choices, not findings about a built Anemone.

| Sketch | Decision for the first version |
|---|---|
| Seven leaks are seven oscillators | Use seven two-component modes (seven complex states, fourteen real values). Scalar leaks alone do not supply oscillations. Publish the equations, parameters and initial state. |
| A rhythm persists without input | Start with passive damped dynamics. They can ring and exchange energy, but their unforced motion fades. Sustained self-oscillation would be a separate mechanism and version, not an undocumented energy floor. |
| An energy picture shows the beating | Define the energy observable and verify this offline. Squaring away phase can hide the motion of an otherwise oscillating state. The chosen rendering must carry a measurable history effect before voice experiments begin. |
| OPEN raises gain | OPEN sets one fixed calibrated gain; CLOSE sets zero. Repeated OPEN is idempotent, not a ramp with another hidden state. |
| One glyph predicts the next seven-row column | Retain one glyph, but explicitly predict a scalar summary of that column: the quantized mean of seven fixed-scale energies. Predicting the entire column would require seven glyphs or a separate codebook. |
| The logged score is its error signal | In version 0, the numeric score is observer-only. It does not train model weights or appear in the prompt. A later error-feedback arm would change the information contract. |
| The entire prompt contains only glyphs and verbs | Proposed practical version 0 adds a short, invariant procedural contract explaining output order and forecast target. Dynamic input remains unlabeled. This is an explicit departure from the literal sketch; an entirely symbolic prompt can be a later comparison. |
| About 150 steps/day | Ten-minute cadence permits 144 calls per full day. A proposed 07:00–23:00 voice window gives 96 calls, excluding 23:00. Twelve ten-minute columns cover two hours. These are schedule arithmetic, not observed counts. |
| Masking temperature reveals a remembered day | Nightly forced CLOSE and voice silence themselves impose a day. A memory test must remove that schedule cue and compare prior temperature phases, unentrained states, carry conditions and timer controls. |
| No speech input makes correlations unambiguous | It removes direct speech-to-state feedback. Common history, carry, pretrained word meanings, the action path and the schedule still need controls. |
| Twelve tokens cannot afford an aphorism | Brevity does not ensure grounded memory. Carry content and usefulness must be tested; frozen weights plus carry do not guarantee improvement over weeks. |
| A weekend and a 4B model | A weekend-scale simulator is an aspiration. Device qualification, reliable logging, a pilot and replicated experiments are separate milestones. A roughly 4B quantized local model is a benchmark candidate, not a Pi performance guarantee. |

### B2. Reference the Avado and ICP work accurately

The earlier SSH work exists. The following records were read locally; their observations
are historical, and no fresh SSH session was opened for this epic.

| Record | What transfers to Anemone |
|---|---|
| [September 5 readiness audit](</Volumes/M3 Volya._smb._tcp.local/other/astrid/docs/avado-icp-preparation.md:23>) | Both appliances reported daemon 0.5.1 and 19 capsules. Exact native source revisions were unproven; edge-spectral was absent. Reuse the distinction between source preparation and installed/running evidence. |
| [Continuity and resource findings](</Volumes/M3 Volya._smb._tcp.local/other/astrid/docs/avado-icp-preparation.md:53>) | ICP had a repeated missing-owned-artifact failure pattern and OOM restart history; Avado showed varied completed receipts. This argues for separate model/body services and explicit failure records, not for assuming a cause or a ready spare inference host. |
| [Hardware discovery](</Volumes/M3 Volya._smb._tcp.local/other/astrid/docs/headless-linux.md:53>) | Adapt `probe_headless_linux.sh` and its discovery-before-model-selection discipline. Avado's documented i3/16 GiB and ICP's J3455/8 GiB are not substitutes for measuring the Pi. |
| [Local model benchmarking](</Volumes/M3 Volya._smb._tcp.local/other/astrid/docs/headless-linux.md:1170>) | Adapt the benchmark approach to OPEN/CLOSE validity, forecast syntax, carry limits, actual prompt size, sustained memory and latency. Earlier x86 model timings are not ARM estimates. |
| [Recovery gates](</Volumes/M3 Volya._smb._tcp.local/other/astrid/docs/avado-icp-preparation.md:142>) | Reuse small staged qualification, a demonstrated restore path, exact candidate identities and separate operational diagnostics. Existing older backups do not establish a current full restore point. |
| [Existing edge body](</Volumes/M3 Volya._smb._tcp.local/other/astrid/docs/headless-linux.md:658>) | The 128-node/66D body admits CPU/RAM activity and completed assistant speech and controls toward a 68% shelf. Those mechanisms would change this experiment. Reuse operational patterns selectively; implement the seven-mode body independently. |
| [Architecture support boundary](</Volumes/M3 Volya._smb._tcp.local/other/astrid/docs/cpu-edge-self-evolution.md:442>) | Ordinary CPU-edge artifacts support ARM64, but the documented self-evolution bootstrap is x86-64 only. Anemone does not require that bootstrap or autonomous code changes. |

Related research: [corrected work queue](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/exercises/2026-09-06-session-close-and-board-brief.md:74>),
`c-persist-prompts`, `c-log-backend-per-generation`, `t-sensory-freshness`,
`t-anchor-by-coupling-ablation`, and proposed `t-history-beyond-recency`.
Anemone can proceed independently; it does not block the current event-survival work.

## C. Epic specification and child tasks

### C1. Intended loop and boundaries

```text
ambient temperature → fixed scaling → aperture → seven evolving modes → glyph picture
                                          ↑                              ↓
                                          └──────── OPEN / CLOSE ← local voice
                                                                    ↓
                                                            replacement carry
                                                            (next call only)

raw sensor, states, exact prompts, forecasts, scores, actions, free text → observer log
```

Only normalized temperature crosses the body input boundary. No generated-text embeddings,
CPU load, memory use, journaling events, network messages or score signal enter the modes.
The voice can change the aperture and replace its carry; it cannot edit state, parameters,
services or files. Free text has no retrieval or feedback path. Body state and the carry
persist; model conversational history, prior prose and inference-session state do not.
The hostname is an operator identity, not an injected persona or prompt label.

### C2. Proposed version-0 contract

**Freeze stages.** First freeze the schema and procedural contract with provisional offline
parameters. Use replay to validate/revise the dynamics and observable. Use a separate
calibration portion of the pilot to select sensor scales, glyph thresholds and OPEN gain;
then freeze the complete configuration before evaluation. Preserve each version and keep
calibration out of the evaluation set. “Protocol complete” does not mean calibration is done.

**Body.** Begin with the continuous-time candidate below; discretization and parameter
values are finalized through those stages before evaluating model behavior.

```text
dz/dt = [diag(-1/τᵢ + iωᵢ) - κL] z + b g u(t)
```

`z` has seven complex components; `L` is a fixed symmetric graph Laplacian and `κ ≥ 0`
sets weak diffusive coupling; `b` is a fixed input vector; `g` is either zero or `g_open`.
All decay constants are positive. Distinct periods and decay times span short response and
long retention; include a candidate slow decay lasting through a night, but do not install a
24-hour driving signal or tune periods to a desired daily-rhythm result. Persist the complete
state and configuration. A finite seeded initial condition is logged, not refreshed each day.
For zero input, this candidate is dissipative: imaginary rotation does not sustain energy,
and both the leak and Laplacian terms remove it. This is an equation-level property, not a
measured device result. No automatic normalization maintains a target energy.

**Sensor.** Proposed capture every ten seconds, lightweight body integration every second,
independent of inference. Use an ambient temperature probe physically separated from the
Pi and its exhaust. Test whether inference heating changes the reading; otherwise the
computer may inadvertently sense its own work. Normalize temperature using a fixed offset
and scale from a separate calibration period; freeze clipping bounds and log clipping.
Log capture time, raw reading, validity, age and admitted input. A valid reading may be held
until its declared freshness deadline; after that, admit zero and record a gap. A sensor
failure, deliberate mask, chosen CLOSE and valid quiet remain distinct observer conditions.

**Picture.** Row `i` represents mean `|zᵢ|²` in a ten-minute bin. Keep the most recent twelve
completed bins in time order, including bins accumulated during sleep. Convert each row
with a fixed calibration scale and fixed eight-level glyph map `▁▂▃▄▅▆▇█`; store unclipped
values as well. Do not rescale each frame. Use a separate single input bar for admitted
signal magnitude over the last bin; reserve `·` for unavailable input coverage and `▁`
for valid zero. Define partial-coverage handling in the protocol. Low body energy is an
observation, not a reason to restore a bright picture. Confirm that phase/coupling history
actually affects this energy rendering; if it does not, revise the observable before freezing.

**Voice and timing.** Proposed ordinary schedule: every ten minutes during 07:00–23:00
America/Los_Angeles. Between calls the body continues evolving. Overnight the scheduler
forces zero gain and makes no voice calls; the carry remains. Forced closures are never
counted as model choices. At wake, the gate stays closed until a valid action applies.
Use monotonic elapsed time within a boot and persisted UTC timing across restart. Record
clock corrections, gaps and uncertain downtime rather than fabricating observations or
catch-up model calls. Advance passive state through a known offline duration with zero
admitted input; mark the lost sensor interval and do not reconstruct it as measured history.

At each scheduled boundary, freeze the picture and input bar, invoke the voice, and score
its forecast against the next bin ending 600 seconds after that snapshot. The old gate
continues during generation; a valid response applies on completion. This explicitly records
the Pi's nonzero latency instead of assuming an instantaneous choice. Commit the forecast
and action before the target closes; a proposed 120-second deadline leaves time for the
action to affect that bin. Baselines must reproduce the same action delay. This is a
refinement of “before each interval”: no later sensor data reaches the model, but part of
the target interval can pass while it generates. Predeclaring a command one bin ahead is
a possible later version, not an unlogged scheduling change.

**Prompt/output.** Freeze one brief procedural instruction explaining input order,
glyph ordering, forecast target and output grammar. Do not include comfort, saturation,
homeostasis, agency, identity or desired action language. Prepend the previous carry raw
within the dynamic input; retain a fixed delimiter that a single-line carry cannot escape.
Dynamic input is carry, picture, input bar and the two action choices. Output has fixed
positions: forecast glyph, OPEN or CLOSE, replacement carry, optional free text. Proposed
total output ceiling: 128 model tokens, including the optional prose. Commit all accepted
fields atomically at whole-response completion, not as streaming tokens arrive; record that
commit time. Reaching the token ceiling may truncate prose if required fields are complete;
record truncation. A grammar
may constrain syntax; it must not choose an action or provide a desired energy target.
Log the full chat template/system contract as well as dynamic text. No accumulating KV
session or chat history may preserve previous generations beyond the declared carry.

The replacement carry is **at most twelve tokens**, measured using the pinned model's
tokenizer, not twelve words or twelve characters. Empty carry is valid. Preserve raw output
separately from accepted fields. Reject over-budget/multiline carry rather than silently
rewriting it; retain the prior carry with a logged validation failure. Apply a valid action
and forecast independently of carry validity. Invalid action or timeout forces CLOSE,
with `origin=runtime_failure`; a malformed/missing forecast is unscored and counted as a
failure, not erased. After the deadline, cancel or quarantine that request and discard its
forecast/action/carry; a late completion must never change the gate/carry or receive a score.
Log the failed opportunity even if the backend eventually returns. Do not issue repair
calls or silently switch models.

**Forecast.** Normalize each row's energy with its fixed scale, clip to the declared range,
average the seven values in the future bin, and quantize with fixed ordinal thresholds.
The one-glyph prediction refers to that aggregate under the **actual applied gate trajectory**.
Primary error: absolute ordinal-bin error; also report exact-match rate, forecast coverage,
and errors split by OPEN, CLOSE, forced closure and generation delay. A model that learns
to choose predictable zero-input decay may improve score without improving world prediction.
Numeric scores stay observer-only in this version; any improvement is adaptation within
fixed dynamics/carry/context, not evidence of weight training.

**Record.** Use a continuous 600-second bin grid: 144 bin records per ordinary 24-hour day,
of which the proposed sixteen-hour window has 96 voice opportunities. Mark sleep bins
`voice_not_scheduled`; retain timeout and missing-sensor records. Daylight-saving changes
require explicit local-schedule/UTC mapping rather than assuming every civil day has 144
bins. Join raw sensor ticks, admitted input and pre/post-state by sequence/time.
Record code/config/model/tokenizer/runtime identities, seed and decoding options, exact
prompt bytes, rendered frame, request/start/completion/deadline times, raw response,
accepted prediction, old/new carry and token counts, requested/applied action and origin,
target/score and restart metadata. Record host resource diagnostics only on the observer
side. Bound log growth; demonstrate checkpoint restoration and deterministic replay before
an unattended run. Replaying with identical inputs should reproduce state within a declared
numeric tolerance; sampled model output need not be bit-identical across backends.

### C3. Hardware and implementation approach

Use a small standalone body/replay program, sensor adapter, local inference adapter,
scheduler and append-only observer records. Separate the body process from the model so
slow generation cannot pause time. Operational supervision can use the existing Linux
patterns, but the old edge body's sensors, controller and semantic feedback are out of scope.

When powered, inventory the exact Pi model, RAM, OS/architecture, storage, supply and cooling;
then establish the intended `anemone` hostname and verified SSH endpoint. Do not assume
`anemone.local` works before checking local name resolution. No hardware purchase is required
by this epic until the existing inventory is known. Power requirements vary by model;
consult [Raspberry Pi's setup documentation](https://www.raspberrypi.com/documentation/computers/getting-started.html)
and [hardware guidance](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html).

An external DS18B20 is one candidate temperature sensor; its manufacturer documents a
1-Wire interface and programmable resolution. Select wiring and driver only after identifying
the actual sensor/module and Pi; the proposal is not a wiring instruction.
[Analog Devices DS18B20](https://www.analog.com/en/products/ds18b20.html).

Benchmark a pinned roughly 4B quantized local model plus a smaller fallback candidate **as
separate qualification runs**. llama.cpp offers quantization and constrained-output support,
but those capabilities do not establish fit or speed on this unplugged Pi.
[llama.cpp](https://github.com/ggml-org/llama.cpp),
[grammar documentation](https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md).
Pick the run's backend explicitly from measured latency, memory, thermals and contract
compliance. Keep all inference local to the Pi for the target experiment. Mac/Avado/ICP
inference would be a separately labeled development condition.

### C4. Child tasks, dependencies and finish lines

Statuses below were verified against the published board cards on September 7, 2026 UTC
(September 6 Pacific). Dependencies remain in each card body because the existing board
has no native epic/dependency fields. Slug IDs below are planning references, also stored
as searchable `id:<slug>` tags; they are not the board's generated database IDs.

| ID / lane / status | Work | Depends on / complete when |
|---|---|---|
| `d-anemone-protocol` / design / open | Freeze version-0 schema, provisional equations/observable and scaling procedure, timing, forecast, carry and failure contract; retain deviations from the original sketch. | No hardware dependency. Complete when a reproducible provisional configuration, sample prompt/output and analysis plan exist, including the sensor-mask schedule control. Final calibrated scales/gain are frozen after the pilot. |
| `t-anemone-replay` / test / open | Build the isolated body, synthetic sensor/replay path, records and scripted aperture controls. | Protocol. Complete when OPEN transmits a known perturbation, CLOSE prevents admission, a residual persists and decays, rendering retains the tested signal, and gap/restart replay passes with declared tolerances. Record negative results and revise before freezing if needed. |
| `c-anemone-device` / change / parked | Inventory and bring up the Pi as anemone; qualify ambient sensor and local model; adapt prior discovery/benchmark tools selectively. | Unparks when Mike powers/connects the Pi and its access is available; exact-contract benchmark depends on protocol. Complete when inventory and endpoint are recorded, sensor freshness works, and at least 100 exact-contract calls achieve ≥99% valid action/forecast, p95 ≤120 s, no overlap, no OOM and no sustained swapping. Record measured thermal/power state. A model miss triggers explicit candidate revision, not hidden fallback. |
| `t-anemone-pilot` / test / open | Run a 72-hour instrumented pilot with scripted OPEN/CLOSE, a night and controlled restart/dropout checks. | Replay + device. Complete when every scheduled opportunity is accounted for, ≥99% expected sensor readings outside declared faults are valid, body time progresses during inference/sleep, no free text enters state/prompts, and restore/replay works. Calibration data is excluded from subsequent evaluation. |
| `t-anemone-picture-regulation` / test / open | Test picture dependence and spontaneous regulation with withheld/shuffled-picture, opaque-action and scripted aperture controls. | Pilot + frozen analysis. Complete when matched trials report effects, uncertainty, controls, sample counts and failures, whether positive or null. |
| `t-anemone-prediction-carry` / test / open | Compare one-glyph forecast with baselines and intact/empty/shuffled carry; explore carry clusters on held-out days. | Pilot + frozen analysis. Complete when action-stratified errors/coverage and replicated carry effects are reported without treating logging as model training. |
| `t-anemone-rhythm-order` / test / open | Test masked-input rhythm, shifted entrainment histories, warm-day order, and timer/smoother/random controls in isolated replay. | Replay + frozen analysis; Pi pilot needed only for transfer to real recorded temperature. Complete when schedule, phase, carry and endpoint controls distinguish retention from a supplied clock or ordinary smoothing, with explicit uncertainty. |
| `t-anemone-longitudinal` / test / open | After qualification, run a proposed four-week observation block and write the synthesis. | Pilot + analysis preregistration. Complete when results, denominators, missingness, backend/config stability, controls and replication limits are archived. Extend only for a stated precision/replication need; do not call four weeks inherently sufficient. |

The parent epic closes when the qualified device, auditable pilot, controlled comparisons
and synthesis exist. Child test completion is independent of a hypothesis being supported.
Only specific evidence-backed findings receive `verified`; no emergence finding exists yet.
The immediate next job is protocol plus offline replay. Pi setup waits for physical access.

### C5. Experiment matrix

Preregister primary outcomes, trial/day units, exclusions, temporal blocks and analysis
before the observation block. Ten-minute decisions from one continuous run are dependent;
they are not independent biological subjects or independent replications.

| Question | Experiment and null | What the result can establish |
|---|---|---|
| Does the picture matter beyond the sensor? | Paired offline prompts: intact, withheld and matched shuffled pictures with identical carry/bar/backend/seed. Match histories of temperature, prior actions and schedule, not just current temperature. Use temporal blocks or exchangeability-matched surrogates; then validate in separate closed-loop trials. | Sensitivity to supplied state and incremental behavioral information. A naive frame shuffle can create implausible inputs and spurious significance. |
| Does unprompted regulation appear? | Define saturation and quiet from fixed body metrics before testing. Measure chosen closure probability and resulting trajectories; compare always-open/closed, timer, matched random and simple threshold controller. Include an opaque action-symbol arm with fixed mapping. | Spontaneous policy relative to controls, subject to pretrained OPEN/CLOSE meanings. Forced sleep/failure closures never count as chosen homeostasis. |
| Does prediction improve, and does carry help? | Compare last-target persistence, constant/action-conditioned decay, simple temperature forecast passed through known dynamics, and intact/empty/shuffled carry. Use matched held-out histories across dates/seeds; score OPEN and CLOSE separately. | Forecast usefulness and carry contribution beyond easier weather or predictable closure. No claim of model-weight learning. |
| Do carries develop structure? | Freeze features/clustering on a training split; evaluate association with body features on held-out day blocks against shuffled carries and schedule/weather controls. Compare continuity and forecast usefulness as well as textual similarity. | Reproducible compression/association if supported. Clusters or an aphorism alone do not establish grounded memory or a culture. |
| Does temperature history leave a daily rhythm? | First use isolated replay: identical continuing uniform voice cadence, no overnight scheduler, no dates/time labels, and controlled carry. Mask sensor after different phase-shifted temperature histories; compare unentrained/reset states, constant input and a clock-only baseline over several candidate cycles. Repeat with multiple initial phases and decay settings. | Retained phase attributable to prior input if it follows shifted entrainment beyond controls. Masking one ordinary scheduled day is insufficient; a programmed period or long passive transient must be reported as such. |
| Does order matter beyond simple memory? | Warm day A then B versus B then A, matched present input and a shared terminal segment. Compare seven modes with leaky smoothers, timer, matched random schedule and memoryless state, under matched calibration budgets. | History dependence and any advantage over controls. Exponential smoothing is itself order-sensitive. |
| Does free text track the body? | Withhold or permute the picture while matching carry, input bar and decoding; blind comparisons and correlate with controlled state changes. | Grounding/sensitivity in this contract. Text retaining texture with no picture is a useful negative control, not evidence of sensing. |

Temporal-null assumptions require care; see the [time-series permutation analysis](https://arxiv.org/abs/2009.03170).
The ordinary smoother baseline follows the [NIST EWMA definition](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc324.htm).

## Board publication verified

Published to the live [Hold Shelf](https://claude.ai/code/artifact/f4761d4a-94e8-43ca-882f-ca887956fca0)
through Mike's authenticated Brave session. The in-app browser still required sign-in;
Brave provided access to the existing private board. An all-status/all-being search for
`anemone` found no existing cards before publication. The board had 124 cards before
the addition and 133 after it.

Created one parent design epic, eight child cards and one trace-log entry. All nine cards
use `being=system` and the `anemone` tag. Eight are open; `c-anemone-device` is parked.
The lane counts are two designs, six tests and one change. After reloading the page,
reopened every card and checked full title, body, lane, status, being, evidence, tags and
source against the prepared values. The trace-log entry, **Scope Anemone and connect the
earlier small-box work**, was also reloaded and its date/title/full body checked. Verification
completed around 02:14 UTC September 7, 2026 (September 6 Pacific). The board was left
filtered to Anemone.

The [publication receipt](</Volumes/M3 Volya._smb._tcp.local/other/reservoir-llm-research/board/anemone-pending.json>)
retains its original preparation filename and records publication as verified. Browser
forms assign database IDs and creation/update timestamps; these exact values are not
exposed by the inspected UI and were not invented. Planning slugs remain searchable via
`id:<slug>` tags, while each child also carries `epic:d-anemone`. The receipt maps each
planning reference to its verified title/tag; parent and dependency references in bodies
refer to those planning slugs. Read and reconcile these tags/titles on future edits to
avoid duplicates. Exact prepared timestamps in the JSON are explicitly not live timestamps.

No board schema, sharing/access setting, existing card or device was changed. Other
sessions' pending board updates remain outside this publication.
