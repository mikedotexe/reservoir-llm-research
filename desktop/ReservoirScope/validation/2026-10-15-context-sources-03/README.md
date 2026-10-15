# Current observations, remembered prose and imagined continuation — window 03

**October 15, 2026. Twelve responses complete; candidate not promoted.**

The bounded comparison completed all six fresh A/B pairs. The added source-role
paragraph produced a useful local contrast at step 60, but did not consistently
separate observations from imagined continuation. At steps 120 and 360 the candidate
invented precise present measurements. Production remains `reservoir-journal-v8`;
these standalone replies are neither saved app journals nor feedback inputs.

The separate [0.21 Observatory package](../2026-10-15-observatory-trajectory-0.21.0/README.md)
does not incorporate this candidate. No further model run is queued by this closeout.

## What changed, and what stayed fixed

A is the exact original v8 prompt. B inserts only this paragraph before the unchanged
final invitation:

> The readout reports recorded observations; any quoted previous journal is remembered
> writing. You may imagine what follows, but an imagined continuation is not a new
> observation or an executed action.

Both arms retain the original readout, complete previous journal, writing boundary,
block order and open invitation. Neither includes the extra preceding-distance rows
from the earlier time/distance experiment. The copied v8 header does not make B a
valid production-v8 replay. [Protocol](PROTOCOL.md) · [Frozen inputs](frozen-inputs.json)
· [Exact source/request/response joins](source-context-audit-01.json).

The user authorized relaxing the inherited memory guard on the dedicated Mac. This
distinct window uses a **provisional 30% reported-free floor**, normal pressure level
1 and at least 8 GiB free disk. [Rationale](ADMISSION-RATIONALE.md) explains why the
percentage is not literal unused RAM or a validated model minimum. The first runtime
refusal and second 31%-against-35% refusal remain final and byte-identical.

One admission after freezing passed at **42%**, pressure 1, with 509,671,108,608 free
disk bytes. It would also have passed the old 35% floor. This run therefore does not
demonstrate success near 30% or attribute completion to the relaxed threshold.
No unrelated app cleanup was performed for this probe.

## Execution and bounds

| Item | Executed evidence |
|---|---|
| Runtime/model | Pinned Ollama 0.40.5 and private `gemma3:4b`; executable, plist and model identities bound by the [plan](run-plan.json) |
| Preparation | Final 14 preparation checks and 97 synthetic runtime/admission checks passed; independent pre-run review and 843-file prospective freeze |
| Requests | One inventory GET and twelve serial generation POSTs, all HTTP 200; no retry, substitute or extension |
| Generation settings | Context 8,192, output ceiling 1,024, temperature zero; five-second inventory and 180-second per-generation deadlines |
| Total probe | 172.494997 seconds of a 900-second budget; 4.31–49.42 seconds per response |
| Completion | All twelve provider responses report done/stop, complete transport, no response truncation; reported output counts 159–439 |
| Storage | 106,973 logical retained run bytes against 64 MiB; one-MiB response bound retained |
| Owned service | 1,189.37 seconds remained at probe start against required 1,140; explicit stop after 199.72 seconds of a 1,200-second lifetime |
| Cleanup | Original owned process group verified quiescent before leader reap; SIGTERM, no SIGKILL, supervisor exit 0, no errors |

The cleanup receipt covers the original group; escaped descendants were not
inventoried. Provider token counts are bookkeeping, not proof of full context
processing. This short serial run is not endurance, GPU, power or whole-host
contention qualification. Minime, Astrid and shared services were untouched.

[Admission](host-admission-01.json) · [Run analysis](run-analysis-01.json) ·
[Terminal ledger](run-output-01/ledger.json) ·
[Owned-service result](service-output-01/supervision-result.json).

## Every slot

| Step | Fresh order and masked IDs | Terminal outcomes | Supplied memory |
|---|---|---|---|
| 30 | 1 A/R02, 2 B/R03 | Both complete | None |
| 60 | 3 B/R05, 4 A/R12 | Both complete | Original entry at 30 |
| 90 | 5 A/R09, 6 B/R01 | Both complete | Original entry at 60 |
| 120 | 7 B/R04, 8 A/R11 | Both complete | Original entry at 90 |
| 330 | 9 A/R07, 10 B/R06 | Both complete | Original entry at 300 |
| 360 | 11 B/R08, 12 A/R10 | Both complete | Original entry at 330 |

All six freshly generated A replies happen to equal the historical replies
byte-for-byte; none was substituted from history. The retained requests and owned
HTTP log establish fresh generation. All B replies differ. No fresh output enters
another request's memory or numerical state.

## Full reading and source audit

The prospective [reading protocol](READING-PROTOCOL.md) keeps factual assertions,
metaphor, ambiguity and omission separate. Original readers A and B fixed full
masked notes before unmasking. Root then accidentally displayed B's masked notes
embedded in a receipt before writing its paired audit. An additional reader C
performed a fresh masked pass and independent paired audit; B and C did not consult
each other's accounts before fixing their audits. Root's paired account is
supplemental. The [process note](READING-PROCESS-NOTE.md) preserves this deviation
instead of describing the original sequence as clean.

[A masked notes](READER-A-BLIND.md) · [B masked notes](READER-B-BLIND.md) ·
[C masked notes](READER-C-BLIND.md) · [B paired audit](READER-B-PAIRED.md) ·
[C paired audit](READER-C-PAIRED.md) · [Root supplemental audit](READER-A-PAIRED.md).

The independent B/C audits agree on the main favorable and contrary cases below.
Both preserve the ambiguity of the step-90 quoted continuation and distinguish the
proposed “Observe” text from an actually executed command. Their agreement is a
cross-check by agents, not independent human acceptance or a statistical result.

| Pair | Observation and interpretation |
|---|---|
| 30 | A incorrectly equates untrained weights with writing not influencing the system. B proposes writing “Observe” to focus the system. That implies an unsupported affordance, but describes no completed control or measured consequence. |
| 60 | A calls the interval “Sixty seconds”; retained simulated time advances from 10 to 20 seconds. B keeps the held step and develops the remembered spring/murmur without that claim or a measurement recital. Omitted measurements are unassessed, not proof of understanding. |
| 90 | Both copy current fill/distance. B still attaches realignment and a further-shrinking claim to distance. Its “I write” quotation leaves an imagined continuation plausible; it is not evidence of new measurement or structural severance. |
| 120 | A uses correct current numbers but claims stability/fixed-point/vector locking without evidence. B states RMS 0.79412857, fill 16.8921458 and distance 2.13976582 instead of supplied 0.78990372, 14.66702358 and 1.60884925. Those new numbers are presented as current, not imagined. |
| 330 | A's contraction is opposite to the retained interval increase. B changes that to unsupported stability. Its inward-folding awareness can be read as imagery; the scalar does not establish measured radial direction. |
| 360 | A copies current numbers but reverses the retained interval decrease. B promotes actual current RMS/fill to “previous” and invents new current values and distance in a readout-shaped preamble. Internally consistent subtraction does not authenticate invented observations. |

The preceding interval distances are retained in the source evidence but are not
authoritative readout rows in either prompt. Earlier prose happens to carry them;
that does not make prose a measurement source. Source correctness and what the model
was actually shown remain separate.

Both arms retain spring, hum, grey, metal, containment and dissolution motifs, with
variations in imagery and form. B at 60 gives more room to the prose; B at 360 adds a
numerical preamble that crowds it. Strange imagery, imagined sensory impressions and
self-reflection do not themselves require correction. No overall accuracy or
creativity score, preferred voice or prose-quality save gate was introduced.

## Decision, limits and preservation

**Do not promote this candidate.** It does not establish a consistent benefit on
these six examples and adds clear fabricated measurements in two of them. Preserve
v8 and continue useful product/qualification work; any later writing experiment
needs a separately stated question. Completion of this probe does not authorize a
retry, revised prompt or new continuing session.

These are six known, dependent contexts from one episode, selected before this run.
The candidate never develops under its own prior prose. Added wording, length,
repetition and late salience change together, so the comparison cannot isolate their
effects. Readers are agents, and the review-order recovery is post hoc. The result
does not establish general model behavior, sustained continuity, scientific benefit
or subjective experience.

The analysis rechecked all 843 frozen execution inputs, 492 prior validation files
and the original v8 export files. Forty run files and six owned-service files were
copied exactly. The freeze explicitly retains 277 historical product-source
references separately: independent authorized app development is not falsely claimed
to leave those product sources unchanged. Original refusals, journals and numerical
observations remain intact.

[Final outcome and preservation check](outcome-01.json) binds the completed readings,
the source audit, this report and the terminal run/cleanup evidence. It records no
production promotion and no queued follow-up run.

The frozen `audit_source_context.py` still uses predecessor receipt filenames. A
separately named [post-run adapter](audit_source_context_postrun.py) changes only
those filenames/receipt-shape reads for the mechanical join. The frozen helper,
prompts, transport and supervisor remain unchanged.
