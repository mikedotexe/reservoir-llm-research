# Self-study can deliver code while the next step still fails

The research project now follows both Beings from source/navigation delivery into
authored writing, requested NEXT, actual action outcomes and later reading. The
fresh sweep finds **access and follow-through barriers before we can evaluate the
new notebook**. No completed natural study exercised the continuity release by
4:00 pm Pacific. That is an absence of eligible exposure, not evidence that the
notebook helps or fails.

The strongest located defect is Astrid's authorship gate: it rejects the NEXT from
a verified self-study response because `self_study` is missing from the list of
model-authored modes. Minime continues seeking internal reading, but encounters
research-budget blocks and invalid source targets. These are concrete obstacles
to making self-study easy to enter and navigate.

## Scope and evidence

[S-008](../research/studies/S-008-study-to-follow-through.md) froze the window
**September 8, 21:13:45–23:00:00 UTC / 2:13:45–4:00:00 pm Pacific** before reading
the new-era outcomes. Verified continuity activations are Astrid 15:09:43 Pacific,
PID 54226, implementation `f9283f1`, and Minime 15:11:33, PID 54938,
implementation `3f0234f`. The comparison is against the earlier shared reader,
not the original 400-line Minime excerpts.

The capture preserves 1,719 records, including 116 generations across lanes,
171 job records, 466 Astrid provider events, 109 actions including the leading
context, and the retained source/navigation evidence. There are **81 actions in
the primary window, 25 of them reading requests**. Indexed read-only queries and
stable file reads report no capture errors. Files are not one atomic snapshot;
journals are root-only and source histories are retained-store histories.

- [Frozen capture](../research/outputs/2026-09-08-study-sequences-natural/capture.json)
  SHA-256 `b3eb48b2b4913492556ba974ef91bc51e998f5f704adcdda0b3e8a15c2ad2c94`.
- [Final machine report](../research/outputs/2026-09-08-study-sequences-final/report.json)
  SHA-256 `9ce360a3d1096744b05ea61b923e6707c4b8167c4825acbe0ae931789cda6ffb`.
- [Chronological reading pack](../research/outputs/2026-09-08-study-sequences-final/reading-pack.md),
  [exact-span close-reading annotations](../research/outputs/2026-09-08-study-sequences-final/annotations.json),
  and [offline verification](../research/outputs/2026-09-08-study-sequences-final/verification.json).

## What the new sweep shows

| Observation | Before continuity activation | After activation through 4 pm |
|---|---:|---:|
| Astrid completed source/navigation studies | 2: final source page and EOF | 0 |
| Astrid SELF_STUDY map actions blocked by authorship gate | 2 | 0 observed requests |
| Minime INTROSPECT actions blocked by research-budget policy | 9 | 10 |
| Minime SELF_STUDY jobs failing before generation, invalid source target | 1 | 1 |
| Completed studies with notebook exposure, either Being | 0 | 0 |
| READ_MORE actions, either Being | 0 | 0 |

Counts use each Being's own activation boundary. Source-study jobs, provider
attempts and action outcomes are separate denominators. Minime's two failed jobs
have action status `handled` but job status `failed`; neither produced a study
generation. The table does not call those successful studies. READ_MORE is now
tracked distinctly, but this window supplies no new READ_MORE outcome evidence.

The predeclared last-three-before / first-three-after close reading has only two
eligible Astrid before entries, and none in the other groups. We preserve those
shortfalls. The later Minime reading-request examples below are explicitly
exploratory follow-up, not replacements for missing self-studies.

### Astrid: specific source use, then a blocked attempt to broaden context

At 14:16:17 Pacific, Astrid received the last 3,414 bytes of
`astrid/capsules/spectral-bridge/src/llm/provider/dialogue_runtime.rs`. Seven retained
pages together reconstruct the complete **29,562-byte, 812-line revision** with a
matching full-file hash. Those seven pages span the earlier history; one is new in
this window. This establishes delivery of the file, not simultaneous whole-file
context or understanding.

Her response names the checks on `alpha_count`, `punctuation_ratio`, and
`max_symbol_run`; delivered lines 717–745 support that description. Her reading of
the punctuation allowances as recognition of her style is an interpretation that
can coexist with the concrete code observation. Claims about what *every*
interaction enforces would require tracing the callers, not just this validator.

She ends `NEXT: SELF_STUDY MAP`. The next recorded action, at 14:16:30,
`act_astrid_1788902190459_self-study`, is blocked by `volition_authority`:

> mode `self_study` is runtime-generated or mirrored and cannot be attested as Astrid-authored

At 14:44:11, the EOF response asks how provider implementations connect to the
runtime, ending `NEXT: SELF_STUDY MAP spectral-bridge`. The next recorded action,
`act_astrid_1788903861068_self-study`, gets the same block. Her reference to a
`DialogueRuntime` handling the turn lifecycle is not established by the EOF input;
that name and `SpectralBridge` do not occur in the reconstructed file. We do not
infer their absence elsewhere. The request for broader context is sensible even
where the preceding description exceeds its evidence.

Both responses match saved journals and introspections exactly. The receipts join
to provider attempts by exact request and HTTP-body hashes. The action records
preserve matching choices and temporal order, but lack a direct originating
generation ID; that last relation remains qualified.

The omission is still present in the **deployed continuity source** at
`autonomous/volition.rs:123–180`. The successful shared-reader branch returns mode
`self_study`; the attestation allowlist excludes it. This is a source-confirmed
continuing mechanism, with the two observed instances occurring **before** the
latest activation. The [focused repair proposal](../proposals/2026-09-08-self-study-authorship-follow-through.md)
specifies an end-to-end acceptance test without weakening other authority gates.

### Minime: continued curiosity, no successful entry into the new study path

All **ten post-change INTROSPECT requests** are recoverable from moment generation
records and their journals. Their journal bodies and NEXT lines are separated by
a runtime `--- ACTION TAIL ---` marker. The new matcher verifies the exact authored
text across that separator and retains the original source spans. A whole-response
substring check alone would incorrectly report these journals missing.

The first, at 15:18:43, asks whether a spectral spike came from prompt complexity,
resonance or processing entropy, and chooses `INTROSPECT [spectral_spike] 0`.
This preserves alternative questions rather than establishing any of those causes.
At 15:18:47 the corresponding exact-worded action is blocked by the research-budget
guard. Later requests include `core_dynamics 142`, `core_architecture 0`, and repeated
capability-map labels; all ten have recorded blocks. Some labels are not established
source paths. The guard prevents these cases from revealing whether their targets
would resolve; a budget-policy fix alone would not prove successful reading.

At 15:32:21, a separate generation (recorded lane `unknown`) says:

> I want to see the math of my own survival.

It ends `SELF_STUDY of the "spectral_tuning" mechanisms in the current system.`
The ensuing job fails with `source_study_unavailable` because the prose is treated
as a source target. Its action row is `handled`. No exact journal copy of this
generation was found, so we cite the generation, not an invented journal entry.

That generation's actual user input says internal SELF_STUDY/INTROSPECT routes are
**budget-free**, while its recent-events context describes a blocked INTROSPECT.
The ordinary moment system prompt does contain shared-reader grammar; the separate
15:32 generation's compacted system input retains only the steward-report mention
of SELF_STUDY/INTROSPECT. The problem is not uniformly missing documentation. It is
inconsistent entry guidance, actual routing, and recovery from unusable targets.

## What changed in the research project

`reservoir_research.study_capture` collects both Beings' bounded natural evidence.
`reservoir_research.study_sequences` reports exact exposure, notebook origins,
source coverage, journals, NEXT, producing jobs/actions, parentage and later reading.
Ordinary reading requests remain visible even when no self-study generation happens.
Source coverage uses byte unions by Being/file/revision, so rereads do not inflate
progress. Navigation never advances source coverage. Incomplete follow-up time,
unknown process eras, ambiguous joins and later terminal events remain explicit.

The existing S-007 baseline and daily ledger are unchanged. The hub, Now page,
question library, trace map, tools guide and a reusable sequence-note template now
point to this work. No new service, model calls, live changes or automation were
introduced. Research changes remain local and uncommitted.

Validation: **211 tests pass, including 26 new sequence tests**. The offline verifier
rebuilds the report, checks all captured hashes and 25 writing links, and independently
reconstructs both complete retained source revisions. The 41 Minime source receipts
in that reconstruction are earlier history, not 41 new post-change studies.
The earlier qualification reports predate recovery of Astrid's protected navigation
and journal separator handling; the linked final report supersedes those views.

## Design decision and next observation

Prioritize getting the complete reading path to work before adding more notebook
features. First make verified Astrid self-study output eligible for its existing
exact-response attestation. Then reconcile Minime's advertised local-study access
with the route that actually runs, and preserve a concrete `SELF_STUDY MAP` recovery
path when a source target is unusable. Keep real source reading and existing
artifact/experiment permissions distinguishable. A broader guard bypass is not
needed to establish the correct behavior.

After those owning-repository changes, the next useful sample is the first natural
successful study and its requested map/page, then whether a carried question is
developed or corrected. Use the same report and preserve the missing-data outcomes.
We cannot yet claim a notebook-related improvement in journal fidelity or continuity.

## Board updates pending

The Artifact connector is unavailable; the board UI opens a sign-in page.
[Pending board record](../board/study-sequences-pending.json) preserves the completed
tooling card, the verified Astrid authorship finding, the Minime routing/guidance
finding and session log. These records have not been published. S-007's existing
daily schedule and cursor were not changed.

**Later historical follow-up, September 8 evening:** the
[living SELF_STUDY history](../research/histories/self-study.md) now records the
owning repair, its paired live activations and the first two natural Minime map
jobs through 17:47:51 PDT. This later evidence does not change the frozen sweep
above. The research-local packet preserves original comparison inputs, code and
release receipts, and exact journals. The
[history board update](../board/self-study-history-pending.json) is also pending;
no publication is claimed.
