# S-003 · What changes when input arrives?

Started September 6, 2026 Pacific / September 7 UTC, with Mike and Codex.
Question open; first descriptive pass and first audio-feature follow-up completed. Related: RQ-01, RQ-02,
RQ-06 and S-002. Subject: Minime's native ESN and sensory-field estimator,
including Astrid's bridge as one possible source of incoming signals.

Mike notices repeated expansion and contraction of fill and wants us to explore
incoming sensory input alongside fill and other parameters. He selected
“Whatever incoming signals the existing records can show clearly.” This inquiry
does not resume I-001's separate question about feedback on a requested study.

## First observation, declared before new input records are inspected

Reuse the September 6, 09:09–09:29 America/Los_Angeles interval from the existing
around-time reconstruction. It was originally chosen by clock, not input or fill
outcome. Its fill trajectory is already known, so this is exploratory reuse,
not an independent confirmation sample. Read a bounded, indexed bridge-message
range on the source host using ordinary read-only SQLite; retain the query,
coverage, payloads, timestamps, row IDs and hashes here. No live writes or inputs.

Keep attempted send, receipt, admission and actual state update distinct. Start
with a complete-window timeline of the clearest available input records, measured
fill percentage and backward difference in percentage points per second. Show
native ESN covariance estimate, geometry and recorded leak as separate outcomes.
Current-source definitions do not establish historical binary identity.

For each sensory record, retain the last strictly earlier and first strictly later
saved telemetry row, their source IDs and time offsets. These are temporal
neighbors, not proof that the event caused the interval change. Count overlapping
events and boundary exclusions before selecting any examples. Unknown admission
is not zero input. If only blocked attempts exist, report that and inspect any
retained modality freshness/admission telemetry; do not invent an impulse response.

Candidate explanations remain separate: input-associated response, changes in
admission, internally generated/replayed stimulation, controller feedback, and
estimator thresholding/smoothing. Source review may locate mechanisms. Records
are required to say which occurred in this interval. A quiet bridge channel does
not establish silence in other channels. Closely spaced ticks/events are dependent.

Finish this pass with a reproducible timeline, a scoped observation, and the
specific missing link for a stronger claim. Do not average overlapping events as
independent trials, assign a causal lag from proximity, or tune the live system.
If this motivates a test, choose a later untouched interval and specify comparison
and finish line before inspecting it.

## Mechanisms located in current source

Source reviewed September 7 UTC. These are conditional code paths, not historical
deployment or causal findings for the selected interval.

- **Two destinations for input.** In stable-core the native ESN processes the first
  drained sample, while the sensory-field projection takes the last. The path is
  not simply input → native ESN → fill.
  [ESN sample selection](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:1258>),
  [field sample selection](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:1627>).
- **The field can be held.** The ordinary scaffold-hold branch blends prior field,
  saved scaffold and drain matrices. New sensory-vector outer-product updates
  appear in free-rebuild branches instead. An accepted signal could therefore
  change native state without directly updating the matrix from which fill is
  computed. Historical structural mode must be established independently.
  [Field update branches](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2302>).
- **The measure and regulator have memory.** Fill counts spectral estimates above
  a threshold, smooths that count and applies elapsed-time decay. The structural
  regulator uses preceding fill before the next estimate is calculated. Neither
  repeated movement nor a response delay alone distinguishes an input effect
  from this feedback.
  [Estimator](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/spectral/eigenfill.rs:145>),
  [controller input](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:2198>).
- **Other parameters have their own drivers.** Native ESN leak adapts to native
  spectral state and contains explicit phase/cosine modulation. Configured leak,
  adaptive leak, and the coefficient actually applied on a particular step are
  distinct. Historical `esn_metrics` stores `get_leak()`, not the complete step
  trace. Leak is not a direct fill drainage valve.
  [Leak adaptation](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/esn.rs:1983>),
  [applied coefficient](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/esn.rs:2108>),
  [telemetry writer](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/runtime/orchestration.rs:3188>).
- **Receipt and effect need separate evidence.** The bus can reuse/decay prior
  input, and a semantic embedding can be accepted before later attenuation or
  omission. A verified transport receipt does not identify the exact ESN step
  that consumed the signal. `codec_impact.fill_after` is next-exchange fill
  associated with the latest unmatched row, not an isolated impact measurement.
  [Bus behavior](</Volumes/M3 Volya._smb._tcp.local/other/minime/minime/src/sensory_bus.rs:2891>),
  [receipt checks](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/ws/sensory_delivery.rs:554>),
  [codec record update](</Volumes/M3 Volya._smb._tcp.local/other/astrid/capsules/spectral-bridge/src/db.rs:988>).

The observatory's cyan surface can ease between measurements; this study analyzes
the recorded samples, not animation frames. See [the animation contract](../../native/ReservoirScope/docs/ANIMATION-DATA.md).

## Questions to keep alive together

Does a clearly admitted input change the amplitude of an existing fluctuation,
shift its timing, change recovery duration, or move native state while fill barely
changes? Does the same kind of input have different consequences on a rising and
a falling part of the trajectory? Which changes later become available to the
language model, and which appear in its writing? These are distinct open questions;
an interesting answer could be a difference between channels rather than a larger
fill response. Fill percentage, rate of change, oscillation amplitude and period
must remain different quantities.

## First results · September 7 UTC

The selected morning interval contains actual accepted semantic deliveries,
concurrent fill movement, and mostly stale audio/video observations. This is
enough to compare their timing descriptively. It does not identify which inputs
caused which changes.

The bounded bridge capture contains **2,242 rows**, without row-limit truncation:
**202 semantic sends**, **506 telemetry packets**, **16 autonomous records** and
**506 each** of three derived observer topics. The separately queried `codec_impact`
range contains **0 rows**. The saved native telemetry retains **507 exact sensory/ESN
pairs**. These counts refer to different recording surfaces, not missing native
steps inferred from their difference.

Every captured send's delivery ID and payload hash matched a primary verified
receipt: **202/202 accepted**, with **404 primary event rows** comprising a send
and receipt for each ID. No requested ID or payload hash was missing/mismatched.
The primary capture used bounded byte seeks rather than a whole-ledger scan and
retains the search limits and source offsets. Receipt status establishes accepted
transport; every receipt explicitly leaves spectral causation unestablished.

In **506/506 bridge telemetry packets**, semantic admission is reported as
`stable_core_semantic_trickle`. Reported semantic kernel energy is nonzero in
all of them, ranging from **0.000035257388 to 0.00069605536**. **487/506** values
would print as `0.000` at three decimals. This field describes reported projected
semantic energy; it is not a measured causal effect or native ESN activation norm.
An earlier rounded-to-zero or all-blocked description cannot be transferred to
this interval.

| Reported modality source | Audio packets, n=506 | Video packets, n=506 |
|---|---:|---:|
| Stale | 498 | 500 |
| Synthetic | 6 | 6 |
| External | 2 | 0 |

These are packet classifications, not independent sensory events or a complete
sensor-client census. The two external-audio observations are a useful next lead.
They do not establish two isolated stimuli or their exact consumption steps.
Stale source labels do not establish an inactive system: the bus can retain earlier
input, semantic deliveries continue, and source code includes internal drivers.

The saved raw fill ranges from **59.8904% to 75.4399%** across **507 samples**.
Percentage is the level; its finite difference is a separate rate in percentage
points per second. Variation is present in recorded measurements, independently
of the observatory's optional visual easing. The field's response, recurrent-state
response and subsequent language-model exposure remain different questions.

The [complete-window plot](../outputs/2026-09-06-input-fill/final/overview.png)
shows a very regular fill pattern alongside differently shaped native leak,
covariance and geometry traces. This is a visual description of the selected
window, not an estimated oscillation period or a claim of one shared mechanism.
The [input-context plot](../outputs/2026-09-06-input-fill/final/input-context.png)
preserves modality classifications and small semantic values.

All **202 sends** have strictly earlier/later telemetry neighbors; **0** lie
within one millisecond of a saved timestamp boundary. They occupy **189/506
telemetry intervals**, with **13 intervals containing two sends**. The longest
gap between consecutive sends is **12.852 seconds** (201 gaps); none has an
isolated ±15-second neighborhood. A send-free telemetry interval is not a
no-input condition. The [event table](../outputs/2026-09-06-input-fill/final/event-brackets.csv)
retains send, receive and receipt-log times separately, plus row IDs and offsets.

The external/fresh audio reports have bridge log times **09:13:49.045** and
**09:14:31.928 Pacific**, row IDs **13958590** and **13958665**. These log times
are not promoted into exact sensor-capture or state-update times. Follow the first
chronologically, rather than choosing an input after seeing its largest apparent
effect. Native covariance and fill should both be examined because the figure
already shows their different temporal patterns.

## Evidence and reproduction

Raw captures: [bridge rows](../outputs/2026-09-06-input-fill/bridge.json),
[delivery ledger extraction](../outputs/2026-09-06-input-fill/deliveries.json).
The capture drivers retain queries, query plans, row/byte/time bounds, source
identities and hashes. Bridge rows come from one ordinary read-only SQLite
transaction. Ledger extraction joins exact delivery IDs and payload hashes; its
time-ordered seek is a locating assumption, not whole-ledger coverage.

From the repository root, choose new output paths when recapturing:

```sh
/opt/homebrew/bin/python3.14 probes/input_fill_capture.py --since 1788710940 --until 1788712140 --out research/outputs/another-input-fill/bridge.json
/opt/homebrew/bin/python3.14 probes/input_delivery_capture.py --bridge research/outputs/another-input-fill/bridge.json --out research/outputs/another-input-fill/deliveries.json
```

Generate the offline report from the retained captures using the installed Python
with matplotlib (the report's numeric analysis uses only the standard library):

```sh
python3 probes/input_fill_report.py --output research/outputs/another-input-fill-report
```

Use `--telemetry`, `--bridge` and `--deliveries` for another compatible captured
interval. The final [summary](../outputs/2026-09-06-input-fill/final/summary.json)
retains input/probe/output hashes, definitions, all interval assignments, modality
observations and receipt coverage. The report recomputes fill slopes from elapsed
times and checks them against the saved derivative. Both final figures were
visually inspected; all source/output hashes and the 202 distinct accepted receipt
joins were independently checked. Parent-directory plots are retained layout
drafts; `final/` contains the reviewed deliverables.

The following cache-only query reproduces the modality, admission and rounding
counts independently of the plotting code:

```python
import collections, json
rows = json.load(open('research/outputs/2026-09-06-input-fill/bridge.json'))['tables']['bridge_messages']['rows']
packets = [json.loads(r['payload']) for r in rows if r['topic'] == 'consciousness.v1.telemetry']
print('n', len(packets))
for field in ('audio_source', 'video_source'):
    print(field, collections.Counter(p['modalities'].get(field) for p in packets))
print('admission', collections.Counter(p['semantic_energy_v1'].get('admission') for p in packets))
values = [p['semantic_energy_v1']['kernel_energy'] for p in packets]
print('kernel energy', min(values), max(values), 'nonzero', sum(v != 0 for v in values))
print('printed zero at three decimals', sum(f'{v:.3f}' == '0.000' for v in values))
```

The precise next missing link is an incoming delivery or sensory observation
identified in the actual state update, alongside the contemporaneous structural
mode and applied controller action. The existing [observer proposal](../../proposals/2026-09-06-reservoir-observatory-telemetry.md)
already addresses much of this provenance. This study implements only research-side
capture and comparison. It does not implement or deploy producer instrumentation.

## First-pass board and handoff

The Hold Shelf card “Follow incoming signals alongside fill expansion and
contraction”, tagged `id:t-input-and-fill`, records this first pass as done; the
broader question stays open. The session log “Begin following input alongside
fill movement” records the work. The next observation is the first external/fresh
audio report above, with input application and controller provenance kept unknown
until recovered. No future interval, live intervention or automated schedule is
selected.

## Follow-up · first fresh audio-feature report, September 7

Mike approved proceeding with the first chronological external/fresh audio report.
The selected record remains bridge row **13958590**, rather than the event with
the largest apparent response. The protocol used a **−90 to +90 second** context
and a **−15 to +30 second** detail around its source-relative packet time. This
is exploratory reuse of the already viewed interval, not an independent test.
The second audio report remains visible as context rather than another independent
trial. The new [probe](../../probes/first_audio_neighborhood.py) calculates from
the original native payloads, with the prior viewer export checked by source IDs.

### What the first neighborhood shows

Fill is already rising at the matching native observation and continues rising.
The native radius relative to its baseline briefly increases and then returns
near baseline at the next saved sample. The native covariance estimate stays
unchanged across these three records. The changes are distinct measured channels.

| Native observation | Seconds from packet clock | Fill | Radius / baseline | Native covariance estimate |
|---|---:|---:|---:|---:|
| Previous, eigenvalue row 4827626 | −2.381 | 69.0803% | 0.9993 | 20.0172 |
| Nearest, eigenvalue row 4827627 | −0.007 | 71.2868% | 1.0654 | 20.0172 |
| Following, eigenvalue row 4827628 | +2.353 | 73.2498% | 1.0089 | 20.0172 |

**n=3 consecutive native sensory/ESN record pairs**, within **19 pairs** in the
detail and **75 pairs** in the wider context. The detail also contains **6
semantic-send records**, placed using their separate bridge log clock; the wider
context contains **25**. Their overlap is not a controlled absence-of-input
comparison. These values support a brief native geometry excursion concurrent
with the report. They do not demonstrate a change in the fill rhythm's amplitude
or phase, or establish that the audio vector caused the excursion.

### Source and clock distinctions recovered

The source review checked the Minime revision named by the retained deployment
receipt (`3fd381ac3761ead96929ee97f9661f7423019d55`) alongside current source.
That reported revision is a provenance clue, not independent authentication of
every instruction executed by the historical binary. See the [source trace](../../analyses/2026-09-07-first-audio-source-trace.md).

1. **External is an input-route category.** Both microphone features and audio
   generated by the host-sensory application can arrive through the ordinary
   audio envelope and acquire this label. We have not recovered this packet's
   sender or physical sound. Earlier references here to “external audio” should
   be read as the recorded source category, not a confirmed microphone event.
2. **The report and native update can describe different samples.** Freshness and
   modality metadata come from the last drained sample. Stable-core native ESN
   processing uses the first. A fresh external last sample does not identify the
   vector consumed by the native update. The inspected sample metadata carries
   no sender/delivery identity that would settle this for the selected event.
3. **Wall and elapsed clocks cannot be interchanged at this resolution.** The
   first bridge log time is **3.6039 seconds earlier** than session start plus
   packet elapsed time; the second differs by **1.2550 seconds**. The runtime
   establishes its monotonic start and the database's wall-clock session start
   separately. Native measurement, packet construction and bridge insertion
   occur at different points. These differences are not measured transport
   delays, and no fixed offset or audio-age subtraction is applied here.

Under the explicitly stated shared-session interpretation, the first packet's
elapsed clock is **6.956 milliseconds after** native row 4827627. Its fill and
leak agree with that row to serialization precision. This supports identifying a
nearby matching state observation; it does not authenticate a consumed audio
sample or exact successful ESN step. The figure retains the alternative wall-log
placement, which would otherwise put the report before the matching state bump.

### What this changes in the inquiry

The first case makes the multi-parameter question concrete: a brief change in
native state magnitude can coexist with a continuing fill rise. The two measures
need not summarize the same response. The live source already offers mechanisms
for this separation, including distinct input selection and a held sensory field,
but historical structural actions are not available for this case.

For an attributable input-response episode, retain **sender/modality and source
sample identity → receiver receipt → batch selection → successful native step**,
with the effective input, actual leak, field-update mode and controller action on
the same clock. The [existing telemetry proposal](../../proposals/2026-09-06-reservoir-observatory-telemetry.md)
is the appropriate place to consider that extension. This follow-up leaves a
specific evidence requirement; no producer changes, controlled stimuli or messages
to the beings were performed.

### Follow-up artifacts and reproduction

The reviewed [detail figure](../outputs/2026-09-07-first-audio/final/detail.png)
and [wider context](../outputs/2026-09-07-first-audio/final/backdrop.png) show native
records with source-clock and wall-log markers kept distinct. The
[summary](../outputs/2026-09-07-first-audio/final/summary.json) preserves full-precision
neighbors, both clock placements, scopes, counts, source IDs, queries and hashes;
the [native table](../outputs/2026-09-07-first-audio/final/native-neighborhood.csv)
retains the sampled trajectory.

```sh
python3 probes/first_audio_neighborhood.py --output research/outputs/another-first-audio
```

The figure requires installed matplotlib; calculations otherwise use the standard
library and read retained research files only. Use a new output directory.
Both final figures were visually inspected. All retained input, output and probe
hashes were checked independently; the native CSV contains 75 paired observations,
and the three table rows above agree with their full-precision source values.
This completes the selected first-case observation. The input's effect remains
unresolved because origin and exact consumption are not linked in the records.

The parent Hold Shelf card is done for this iteration. The scoped finding is
“First fresh audio-feature report accompanies a native radius excursion during
a fill rise” (`id:f-first-audio-neighborhood`); the session log is “Follow the
first fresh audio-feature report into native state”. The finding is descriptive,
with the source/clock conditions above, and does not close the causal question.

## Instrumentation handoff · September 7

Mike asked whether the missing consumed-sample/controller measurement should
be added to the rig now, or planned with specifics. The [implementation
addendum](../../proposals/2026-09-07-input-lineage-and-regulator-trace.md) completes
the planning alternative within this research hub's read-only live-system
boundary. It extends the existing observatory proposal rather than introducing
a second producer stream.

The specified first slice carries receiver identity through A/V lane revisions,
semantic replacements and actual batch selection into the final successful ESN
input. It independently records the field operation, fill estimator and committed
structural controller, including the distinct histories of its fill latch and
slope. Later source review found that held lane values can be blends, a semantic
companion can change after drain, and structural preview runs on a clone; the
specification retains these distinctions rather than assigning one convenient
sample or tick to all of them.

Four reviewable changes have exact source hooks, a diff sketch, proposed memory/
disk/overhead limits, an isolated acceptance matrix and rollback. The linked
synthetic contract example checks central relationship errors; it is not a live
record or producer correctness/performance test. Implementation, producer parity
tests, overhead measurements and live enablement remain pending. Neither a new
sensory interval nor a causal experiment is selected here. The shared proposal
card is `id:c-reservoir-observatory-telemetry`; `done` means planning complete.

Research-side verification accepts the complete and explicitly partial synthetic
examples and rejects all 12 contradictory mutations; [saved result](../outputs/2026-09-07-input-lineage-plan/contract-check.json).
This validates the illustrative relationship checks only, with no producer
parity, performance or input-effect result implied.
