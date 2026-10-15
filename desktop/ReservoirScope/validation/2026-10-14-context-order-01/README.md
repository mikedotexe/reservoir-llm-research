# Context and repetition: retained reading complete, model comparison unstarted

**October 14, 2026 · Closed at the single resource admission.** The retained-context investigation is complete. The prepared real-model comparison did not start: the Mac reported pressure level **2** and **29%** free memory, against the fixed requirement of level **1** and at least **35%**. Disk availability passed. All twelve request slots remain unstarted. No new model service, readiness request, generation, journal or feedback application occurred.

## What the retained writing shows

The [context audit](RETAINED-CONTEXT-AUDIT.md) reads the complete known v7 episode03 and v8 episode01 with their exact supplied prompts.

- V7 begins copying the readout block at step 150, before that layout appears in its previous journal. At the next turn, both the scaffold and inherited prose supply it.
- V8’s grey, metallic and containment imagery originates in its prose and then becomes available in exact previous-text memory. Its repeated composition still develops new images and interpretations.
- Both first entries focus on the held clock and telemetry before any journal memory exists. Memory alone therefore cannot explain that initial emphasis.

These observations distinguish possible sources of repetition; they do not prove which source caused a particular response. Repetition can support continuity. There is no creative score, mandatory novelty or new writing instruction.

## Prepared comparison and actual outcome

The [prospective protocol](PROTOCOL.md) fixes six evenly spaced snapshots from the completed v8 episode. Fresh A would use the exact original prompt; fresh B would only exchange the complete readout and prior-journal blocks. The same words, readings, memory and open invitation remain. Twelve standalone responses were planned, alternating AB/BA order, without any response entering the reservoir or another request.

[Independent input review](PRE-RUN-REVIEW.md) verified the exact transforms and six full memory joins. Six transform tests, [28 request-runner tests](runner-tests-02.json), and [12 masked-reader tests](blind-renderer-checks-02.json) passed. Earlier synthetic fixture failures remain recorded. The [reading protocol](READING-PROTOCOL.md) provides a condition-masked first pass, followed by exact-source comparisons; neither pass was performed because no new writing exists.

The [admission](host-admission-01.json) and [twelve-slot outcome](outcome-01.json) preserve the refusal. No retry, replacement, resource polling, application quit or memory cleanup followed. The [preservation check](preservation-01.json) confirms all 484 frozen files and both historical exports’ 146 files remain exact. No owned process required cleanup, and Minime and Astrid were not accessed or changed.

**Decision:** keep production v8 and the 0.20.0 package unchanged. There is no new evidence for promoting the reordered context. A later fresh resource window can use this prepared design in a distinctly identified attempt with the same bounds; this closed attempt must remain preserved. No automatic retry is scheduled.

This is preparation and exploratory reading, not a real block-order result, app-session qualification, long-term writing benefit, GPU measurement or new platform acceptance. The broader question remains open.

## Reproduce the outcome summary

From this directory, the following reads only retained receipts:

```sh
python3 - <<'PY'
import json
from pathlib import Path
outcome = json.loads(Path('outcome-01.json').read_text())
preserved = json.loads(Path('preservation-01.json').read_text())
print({key: outcome[key] for key in ('status', 'actualPressureLevel',
    'actualMemoryFreePercent', 'actualDiskFreeBytes', 'realGenerationRequests')})
print('planned', len(outcome['slots']), 'unstarted',
      sum(slot['status'] == 'unstarted' for slot in outcome['slots']))
print('frozen files', preserved['frozenFiles'], 'changed', preserved['changed'])
print('historical files', sum(row['files'] for row in preserved['historicalExports']))
PY
```
