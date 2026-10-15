#!/usr/bin/env python3
"""Post-unmask file audit; preserves all supplied contexts, never scores prose."""
import datetime as dt
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / '2026-10-14-v8-writing-episode01/real-model-export-01/quality-review-material.json'


def identity(path):
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def main():
    # Both notes must already exist; no masked reader needs these paired outputs.
    root_notes = HERE / 'root-masked-reading-01.md'
    independent_notes = HERE / 'independent-masked-reading-01.md'
    assert root_notes.is_file() and independent_notes.is_file()
    assert identity(SOURCE)['sha256'] == '12d0a9f863f1471e5eeb08a11f941b34a486abbee3946f6383e337a3e6e260e0'
    entries = {j['observation']['step']: j for j in json.loads(SOURCE.read_text())['journals']}
    inputs = json.loads((HERE / 'frozen-inputs.json').read_text())
    ledger = json.loads((HERE / 'run-output-01/ledger.json').read_text())
    mapping = json.loads((HERE / 'sealed-map-01.json').read_text())
    ids = {m['sourceSlot']['slot']: m['reading']['readingId'] for m in mapping['slots']}
    rows = []
    for slot, frozen in zip(ledger['slots'], inputs['slots']):
        number, step, condition = slot['slot'], slot['anchorStep'], slot['condition']
        request_file = HERE / f'run-output-01/slot-{number:02d}-request.json'
        text_file = HERE / f'run-output-01/slot-{number:02d}-text.txt'
        assert identity(request_file)['sha256'] == slot['request']['sha256']
        assert identity(text_file)['sha256'] == slot['text']['sha256']
        request = json.loads(request_file.read_text())
        assert len(request['messages']) == 1 and request['messages'][0]['role'] == 'user'
        prompt = request['messages'][0]['content']
        text = text_file.read_text()
        assert prompt.encode() == Path(frozen['prompt']['path']).read_bytes()
        source = entries[step]
        original = source['exactPrompt']
        original_prefix = original.split('\n\nOPTIONAL READOUT\n')[0]
        original_tail = original.split('\n\nPREVIOUS JOURNAL\n', 1)[1]
        assert prompt.split('\n\nOPTIONAL READOUT\n')[0] == original_prefix
        assert prompt.split('\n\nPREVIOUS JOURNAL\n', 1)[1] == original_tail
        if condition == 'A':
            assert prompt == original
        observation = source['observation']
        prior_step = observation['previousObservationStep']
        prior = entries[prior_step]['observation'] if prior_step is not None else None
        rows.append(dict(slot=number, readingId=ids[number], anchorStep=step, condition=condition,
            status=slot['status'], request=identity(request_file), responseText=identity(text_file),
            exactSuppliedPrompt=prompt, exactResponseText=text, exactPreviousProse=source['memory']['entry']['text'] if source['memory'] else None,
            observation=observation, precedingObservation=prior,
            originalHistoricalReplySha256=hashlib.sha256(source['journalText'].encode()).hexdigest(),
            replyEqualsHistorical= text == source['journalText'],
            optionalReadout=prompt.split('\n\nOPTIONAL READOUT\n', 1)[1].split('\n\nPREVIOUS JOURNAL\n', 1)[0],
            prefixMemoryBoundaryInvitationUnchanged=True,
            scope='Full source material for human claims audit; no automatic factuality or creativity score.'))
    result = dict(schema='reservoir-time-direction-source-context-audit-v1', atUtc=dt.datetime.now(dt.timezone.utc).isoformat(),
        source=identity(SOURCE), inputs=identity(HERE/'frozen-inputs.json'), mapping=identity(HERE/'sealed-map-01.json'),
        fixedReaderNotes=[identity(root_notes), identity(independent_notes)], rows=rows,
        controlRepliesEqualHistorical=sum(r['condition']=='A' and r['replyEqualsHistorical'] for r in rows),
        candidateRepliesEqualHistorical=sum(r['condition']=='B' and r['replyEqualsHistorical'] for r in rows),
        limits='Fresh receipt-bound outputs; historical identity is not substitution. No output fed later requests or reservoir.')
    with (HERE/'source-context-audit-01.json').open('x') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print(json.dumps(dict(rows=len(rows), controlRepliesEqualHistorical=result['controlRepliesEqualHistorical'],
        candidateRepliesEqualHistorical=result['candidateRepliesEqualHistorical'], receipt=identity(HERE/'source-context-audit-01.json'))))


if __name__ == '__main__':
    main()
