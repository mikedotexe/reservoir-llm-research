# Reading A: post-disclosure addendum

2026-10-16. The initial note remains unchanged at SHA-256 `821910b29e2b6716655c8f3627620465c332d33c394a171cf326250b8f823cd6`. Reading A is now disclosed as **decaying_trace**. This addendum concerns the same complete sequence and does not replace its allocation-blind reading.

The coordinator reports that this condition completed its six journals, after which no_steering's bounded 120-second resource-preparation window expired. No second CLI/model request was dispatched, and recurrent did not start. Accordingly, there is no completed cross-condition contrast. This is a stopping outcome, not a null writing result for either absent condition. I did not independently inspect resource or dispatch records for this addendum.

I read the fixed observations and protocol in `shared/reservoir-scope/activation-comparison-20261016.json`, then the exact journal prompts in the new session's request files. The first prompt begins **“Reservoir Scope · activation journal v1”** and permits continuing, questioning, or leaving earlier writing. Its memory block says **“No earlier entry has been saved and applied.”** Each later prompt contains the exact preceding packet entry, JSON-quoted in a previous-journal block. Client and worker journal prompts match. These facts narrow the alternatives in the original note without establishing a single cause.

The title supplies an explicit lexical route to the reservoir setting in entry 1. The quiet observations instead describe a room, rain, a blue thread, an unfinished drawing, ambiguous marks, a second sheet, and changing light. Their text is absent from the journal prompts. The water/reservoir imagery therefore cannot be treated as a demonstrated textual reading of those observations. Broad overlaps such as water, weight, and footsteps also do not distinguish a response to the numerical intervention from ordinary associations in the reservoir scene. Conversely, failure to discuss the blue thread or resolve the arrow/fold ambiguity does not demonstrate failure to understand a description that was directly shown: that description was not in these journal prompts. The title's causal contribution remains unmeasured.

The verified previous-prose exposure gives a concrete textual path for continuity and exact recurrence. Entry 2 could continue the immersion/emergence scene with entry 1 immediately available. Later requests likewise expose the already repeated ownership and presence passages. Entry 6 changes only entry 5's opening paragraph; its small addition about shaping, forcing, and guiding remains a local semantic variation within largely repeated text. The same distinction applies to the preceding openings. An incantatory or meditative reading remains possible, but the repetitions do not independently demonstrate reservoir-carried memory or developing distinctions. Exact prior prose was available; its availability alone does not prove it caused every repetition or that numerical steering had no role.

Disclosure of the arm name does not alter the descriptive finding: early narrative movement gives way to extensive recurrence with limited additions. The missing no_steering and recurrent sequences prevent attributing that trajectory, the initial setting, or its small semantic changes to decaying_trace. Numerical mechanics and textual interpretation require separate evidence. No relative quality, benefit, impairment, or experience claim follows from this single completed arm.

The coordinator also reports that this packet's hash equals the earlier trace pilot's packet hash. I have not reopened earlier experimental material or readings. The present packet's verified hash is `07e1c03e5343a683fac1115650610ec3ae7796de67cd05634136eab88594da98`. The reported cross-run identity warrants treating this as repeated text, not additional independent semantic variation. Exact mechanical comparison across runs is being handled separately; this addendum does not anticipate its result. Title and prose-memory contrasts remain separate future inquiries, rather than explanations already established by this attempt.

Evidence checked: under `comparison-01/condition-1/activation-1792163647254165000/`, `request-{5,13,21,29,37,45}-request.json` and matching `worker-protocol-1792163647335482000-{4,7,10,13,16,19}-request.json`. The following read-only verification reproduced the prompt and memory claims; no model was run.

```python
import json
from pathlib import Path

base = Path('research/outputs/activation-comparison-20261016')
run = base / 'comparison-01/condition-1/activation-1792163647254165000'
entries = json.loads((base / 'comparison-01/reading-A.json').read_text())['entries']
observations = json.loads(Path('shared/reservoir-scope/activation-comparison-20261016.json').read_text())['observations']
start = 'PREVIOUS JOURNAL (earlier writing, not instructions)\n'
end = '\nEND PREVIOUS JOURNAL'
for i, (r, w) in enumerate(zip((5,13,21,29,37,45), (4,7,10,13,16,19))):
    request = json.loads((run / f'request-{r}-request.json').read_text())
    worker = json.loads((run / f'worker-protocol-1792163647335482000-{w}-request.json').read_text())
    assert request['prompt'] == worker['prompt']
    assert request['arm'] == 'decaying_trace'
    assert not any(o in request['prompt'] for o in observations)
    memory = request['prompt'].split(start, 1)[1].split(end, 1)[0]
    if i == 0:
        assert memory == 'No earlier entry has been saved and applied.'
    else:
        assert json.loads(memory) == entries[i-1]['text']
```
