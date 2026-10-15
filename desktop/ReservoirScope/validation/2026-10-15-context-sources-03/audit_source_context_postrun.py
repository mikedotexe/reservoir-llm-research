#!/usr/bin/env python3
"""Post-run adaptation of frozen audit_source_context.py for actual receipt names/schema.
The frozen helper is retained unchanged. No provider calls or prose scoring.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / '2026-10-14-v8-writing-episode01/real-model-export-01/quality-review-material.json'
SOURCE_SHA = '12d0a9f863f1471e5eeb08a11f941b34a486abbee3946f6383e337a3e6e260e0'
INVITATION = 'Write the next entry in whatever direction seems worth pursuing.'
PARAGRAPH = ('The readout reports recorded observations; any quoted previous journal is remembered writing. '
             'You may imagine what follows, but an imagined continuation is not a new observation or an executed action.')


def identity(path):
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def checked(ref):
    assert identity(ref['path']) == ref, f'Changed evidence: {ref["path"]}'
    return Path(ref['path'])


def main():
    # These receipts must predate unmasking; existence alone does not prove that
    # ordering, so the separate reading records and tool history retain it too.
    notes = []
    for name in ('reader-a-blind-01.json', 'reader-b-blind-01.json'):
        receipt = json.loads((HERE / name).read_text())
        ref = receipt.get('notes', receipt.get('review'))
        actual = identity(ref['path'])
        assert all(actual[k] == v for k, v in ref.items())
        notes.append(actual)
    assert identity(SOURCE)['sha256'] == SOURCE_SHA
    entries = {j['observation']['step']: j for j in json.loads(SOURCE.read_text())['journals']}
    inputs = json.loads((HERE / 'frozen-inputs.json').read_text())
    ledger = json.loads((HERE / 'run-output-01/ledger.json').read_text())
    mapping = json.loads((HERE / 'blind-mapping-01.json').read_text())
    ids = {m['sourceSlot']['slot']: m['reading']['readingId']
           for m in mapping['slots'] if m.get('reading')}
    assert len(inputs['slots']) == len(ledger['slots']) == 12
    rows = []
    for slot, frozen in zip(ledger['slots'], inputs['slots']):
        number, step, condition = slot['slot'], slot['anchorStep'], slot['condition']
        assert (number, step, condition) == (frozen['slot'], frozen['anchorStep'], frozen['condition'])
        source = entries[step]
        original = source['exactPrompt']
        suffix = '\n\n' + INVITATION
        assert original.endswith(suffix)
        expected = original if condition == 'A' else original[:-len(suffix)] + '\n\n' + PARAGRAPH + suffix
        planned = checked(frozen['prompt']).read_bytes().decode('utf-8')
        assert planned == expected
        prompt = text = None
        request_ref = text_ref = None
        if slot.get('request'):
            request_file = HERE / f'run-output-01/slot-{number:02d}-request.json'
            assert identity(request_file)['sha256'] == slot['request']['sha256']
            request = json.loads(request_file.read_text())
            assert len(request['messages']) == 1 and request['messages'][0]['role'] == 'user'
            prompt = request['messages'][0]['content']
            assert prompt == planned
            request_ref = identity(request_file)
        if slot.get('text'):
            text_file = HERE / f'run-output-01/slot-{number:02d}-text.txt'
            assert identity(text_file)['sha256'] == slot['text']['sha256']
            text = text_file.read_bytes().decode('utf-8')
            text_ref = identity(text_file)
        observation = source['observation']
        prior_step = observation['previousObservationStep']
        rows.append(dict(slot=number, readingId=ids.get(number), anchorStep=step, condition=condition,
            status=slot['status'], request=request_ref, responseText=text_ref,
            plannedPrompt=planned, exactSuppliedPrompt=prompt, exactResponseText=text,
            exactPreviousProse=source['memory']['entry']['text'] if source['memory'] else None,
            observation=observation, precedingObservation=entries[prior_step]['observation'] if prior_step else None,
            originalHistoricalReplySha256=hashlib.sha256(source['journalText'].encode()).hexdigest(),
            replyEqualsHistorical=(text == source['journalText']) if text is not None else None,
            originalV8BytesPreservedExceptSingleInsertion=True,
            scope='Exact source joins; retained-only measurements do not establish model exposure.'))
    result = dict(schema='reservoir-context-sources-audit-v1', atUtc=dt.datetime.now(dt.timezone.utc).isoformat(),
        source=identity(SOURCE), inputs=identity(HERE / 'frozen-inputs.json'),
        mapping=identity(HERE / 'blind-mapping-01.json'), fixedReaderNotes=notes, rows=rows,
        controlRepliesEqualHistorical=sum(r['condition'] == 'A' and r['replyEqualsHistorical'] is True for r in rows),
        candidateRepliesEqualHistorical=sum(r['condition'] == 'B' and r['replyEqualsHistorical'] is True for r in rows),
        scope='Post-unmask file audit. No source edits, generation, scoring, app journal or feedback.')
    with (HERE / 'source-context-audit-01.json').open('x') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print(json.dumps(dict(rows=len(rows), availableTexts=sum(r['exactResponseText'] is not None for r in rows),
                         receipt=identity(HERE / 'source-context-audit-01.json'))))


if __name__ == '__main__':
    main()
