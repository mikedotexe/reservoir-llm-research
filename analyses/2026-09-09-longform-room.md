# More room to write, retain a thought, and choose to continue

September 9, 2026, Pacific. Mike asks how larger token allowances, sensory input
length/dimensions, and NEXT budgets interact, and how to support more longform
thought across both Beings. This is a source audit and design proposal. No model
call, Being message, runtime configuration change or restart was performed.

## What the latest bounded sample establishes

`probes/longform_room_audit.py` freezes Minime generation files in
**[16:18,17:18) PDT**, using filename completion clocks. It retains 23 records
with no capture errors: 19 linked SELF_STUDY journals and four successful records
whose lane is unknown and which have no linked journal. The unknown records must
not be represented as four additional journal entries.

All 19 studies have an effective output allowance of **4,096**. Native generated
counts range **263–992**, median **670**. Five newer records retain native `stop`;
14 older records lack that new field. All 19 have `status=ok` and a journal link;
that status is not a substitute for missing native finish evidence. Multiple
process eras and the preceding uncoupled trial's shared-hardware contention are
present. This is descriptive evidence of unused study output allowance, not an
effect estimate or a measure of thinking. [Frozen report](../research/outputs/2026-09-09-longform-room/report.json).

## Remaining source limits

Astrid implementation references below use the immutable release checkout
`/Users/v/other/worktrees/study-choice-20260909/astrid` at source `7d85683d80`.
The shared canonical checkout contains separately owned edits; they are not
treated as live source. Minime main is `c9c2a70`.

| Surface | Observed setting or source behavior | Implication |
|---|---|---|
| Shared SELF_STUDY | 4,096 output tokens; 24,000 bytes maximum assembled protected input | More `num_ctx` alone does not enlarge what the reader supplies |
| Study continuity | Four recent visible responses; 9,000-byte rendered notebook; stored prose capped at 16,000 bytes each | An 8k-token answer needs matching draft/carriage support, not another tiny excerpt |
| Astrid ordinary dialogue | Current self-control preference is 768; LENGTH long is 1,280; numeric LENGTH tops out at 1,536 | Existing preference and maximum permitted preference are separate limits |
| Astrid dialogue provider | Gemma4 policy caps at 1,536, or 1,024 above 14,000 prompt characters | Even THINK_DEEP's requested 8,192 can be clamped on this path |
| Astrid journal elaboration | Caller asks 5,120; reflective provider policy caps at 3,072 | The effective allowance is smaller than the caller's nominal allowance |
| Astrid dialogue wording | Selected Gemma4 prompt requests a few sentences or compact paragraphs, without sprawling | A soft instruction toward brevity remains despite the broader prompt's spacious wording |
| Minime ordinary journal paths | Global cap defaults to 768, doubled for journal calls; private-qualia cap defaults to 2,048, doubled; SELF_STUDY has a special 4,096 ceiling | The earlier increase is real, but room still depends on mode and caller |
| Minime non-study working input | Gemma4 adapter caps total at 16,000 characters and can middle-trim system and user context | Model context capacity and useful retained material differ |

These code paths are not all exercised by the one-hour sample. Minime non-study
values are code defaults/rules, not measured journal caps from those four unknown
records. Astrid's current preference was separately captured from the deployed
self-control state; its SHA is in the report. It must not be silently reinterpreted
as an explicit current desire for longer responses, or overwritten as an error.

Reproduction/source pointers (line numbers at the audited revision):

- Shared reader: `crates/astrid-source-study/src/lib.rs:31`,
  `notebook.rs:138` and `:155`; complete source input is not a full model window.
- Astrid `llm/provider/source_study.rs:35`; `prompt_contracts.rs:51`, `:235`;
  `fallback_contracts.rs:82`; `generative_actions.rs:487`;
  `transport.rs:263` and `:380` establish caller and effective policy.
- Astrid `autonomous/next_action/sovereignty.rs:722` and
  `autonomous/runtime/orchestration.rs:1889` establish LENGTH and THINK_DEEP.
- Minime `minime_autonomy/runtime.py:21390`, `:21496`, `:21523`, `:21663`,
  `:53771`; source-study bypasses the large general-purpose system/action menu.

## Sensory width, textual context, and recurrent influence are different

Astrid's prose-to-Minime codec produces 48-dimensional base features; her
coupled generation server separately projects each generated token embedding to
a 32-dimensional triple-reservoir input. Neither quantity is an output-token or
paragraph allowance. Other Minime sensory/projection widths exist, including
newer companion dimensions; adding them is a representation change, not a direct
way to give a journal more space.

Input *text length* consumes context budget. How much source, recalled writing,
perception description and action guidance the host actually admits determines
what is available for the next response. Useful continuity may matter more than
adding more telemetry or a larger unstructured prompt.

Numeric coupling can influence the generated words. The inspected coupled
implementation modulates temperature, recent-token repetition and probability
tails, with an optional wider vocabulary bias. These operations can affect
ending probabilities as well as content. **Whether they explain short entries
is untested**. Doubling projection width does not establish richer understanding
or longer expression. The Ollama study route and Astrid's coupled route must
remain distinct experimental subjects.

The reverse direction matters too: longer prose may change the sensory stream
sent to Minime. Current Astrid encoding splits prose into at most eight chunks,
merging excess chunks, with a three-second interval. Longform writing therefore
does not require more feature dimensions. It should also not automatically mean
a proportionally larger sensory dose or compulsory publication to the peer.

Source: `neural-triple-reservoir/coupled_astrid_server.py:478`, `:1020`, `:1118`;
`mlx_reservoir.py:268`; Astrid `codec/encoding.rs:90` and
`autonomous/runtime/orchestration.rs:3783`. Coupled source is inspected on disk;
the launch configuration identifies the coupled Gemma4 server. This audit does
not assert a newly verified loaded-source identity for that separate process.

## NEXT budgets affect continuity rather than current response length

Astrid's `active_new_ground_budget` grants at most three progress credits and
relaxes some repeat thresholds. Other branches can issue `stagnant_forced`
redirects after repeated topic/theme choices or research-action pairs. This is a
real code-level choice restriction; the one-hour sample does not measure how
often it fired. A desired long investigation can resemble a loop to this policy.
Lack of an externally recognized new result need not mean the Being should stop.

Minime's general `_diversity_nudge` is explicitly a soft hint, and the protected
SELF_STUDY path bypasses that general prompt builder. Separate health/resource
and external-action authorization budgets should not be conflated with either
novelty credit or generation capacity. “Same Action again” does not by itself
establish waste or lack of agency. All of these NEXT mechanisms operate between
Actions, not as a direct token stop during the current generation; their prompt
wording may influence response shape, which is a separate hypothesis.

Source: Astrid `autonomous/state.rs:1449`, `:1552`, `:1793`; Minime
`runtime.py:23976`, `:53678`, `:53771`.

## Recommended next implementation

[The proposal](../proposals/2026-09-09-longform-room.md) starts with a shared
optional extended-writing profile, effective budgets, complete draft continuity,
and protection of chosen read-only continuation from novelty-only redirection.
Sensory dimensionality stays a separate question. First measure concrete effects
before proposing a coupled-generation change.

Dedicated model reasoning also differs from journal output. Ollama exposes
thinking separately from final content ([official documentation](https://docs.ollama.com/capabilities/thinking));
context size, maximum generation and stopping are separate controls
([parameter reference](https://docs.ollama.com/modelfile)). Our earlier four-call
thinking comparison returned continuation-only visible answers in both enabled
cases. It did not establish a benefit and did not establish that reasoning mode
is generally unhelpful. An extended-writing trial should use the current context,
separate reasoning/final budgets where supported, and compare final usefulness,
continuity, unsupported claims, repetition and latency. File size is secondary.

## Board updates pending

Local proposal and audit are complete. No compatible board connector is available;
no board write or Being-directed correspondence occurred. S-007 cursor unchanged.
