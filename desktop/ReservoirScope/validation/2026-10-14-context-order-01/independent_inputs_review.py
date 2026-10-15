#!/usr/bin/env python3
"""Read-only fixed-input review. No preparation import, runtime or network calls."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / '2026-10-14-v8-writing-episode01/real-model-export-01'
RECEIPT_SHA = '07aff62e23ee5c08e85e97c2ae93702d3b145473aa38d58c0c0345d85d1aa603'
MATERIAL_SHA = '12d0a9f863f1471e5eeb08a11f941b34a486abbee3946f6383e337a3e6e260e0'


def identity(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def load(path):
    return json.loads(path.read_bytes())


def main():
    started = datetime.now(timezone.utc).isoformat()
    assert identity(SOURCE / 'receipt.json')['sha256'] == RECEIPT_SHA
    assert identity(SOURCE / 'quality-review-material.json')['sha256'] == MATERIAL_SHA
    receipt = load(SOURCE / 'receipt.json')
    assert receipt['status'] == 'passed' and receipt['originalUnchanged'] is True
    assert receipt['reviewMaterial']['sha256'] == MATERIAL_SHA
    assert receipt['verification']['exitCode'] == 0
    assert receipt['verification']['result']['status'] == 'passed'
    material = load(SOURCE / 'quality-review-material.json')
    entries = {j['identity']['observedStep']: j for j in material['journals']}
    assert len(entries) == 12 and sorted(entries) == list(range(30, 361, 30))
    bundle = Path(receipt['bundle'])
    bundle_paths = {str(p.relative_to(bundle)): p for p in bundle.rglob('*') if p.is_file()}
    assert set(bundle_paths) == set(receipt['inventoryBefore'])
    assert {rel: identity(p) for rel, p in bundle_paths.items()} == receipt['inventoryBefore']
    pin = Path(receipt['pinnedExecutable']['path'])
    assert identity(pin) == {k: receipt['pinnedExecutable'][k] for k in ('bytes', 'sha256')}
    names = ['prepare_inputs.py', 'test_prepare_inputs.py', 'run-plan.json', 'PROTOCOL.md',
             'READING-PROTOCOL.md', 'RETAINED-CONTEXT-AUDIT.md', 'frozen-inputs.json',
             'transformation-checks-01.json']
    paths = [HERE / n for n in names] + sorted((HERE / 'prompts').glob('*.txt'))
    paths += [SOURCE / 'receipt.json', SOURCE / 'quality-review-material.json', pin]
    paths += list(bundle_paths.values())
    before = {str(p): identity(p) for p in paths}
    inputs = load(HERE / 'frozen-inputs.json')
    plan = load(HERE / 'run-plan.json')
    transforms = load(HERE / 'transformation-checks-01.json')
    assert inputs['runPlan']['path'] == str(HERE / 'run-plan.json')
    assert identity(HERE / 'run-plan.json') == {k: inputs['runPlan'][k] for k in ('bytes', 'sha256')}
    anchors = [60, 120, 180, 240, 300, 360]
    expected_order = [(step, condition) for index, step in enumerate(anchors)
                      for condition in ('AB' if index % 2 == 0 else 'BA')]
    assert [(s['anchorStep'], s['condition']) for s in inputs['slots']] == expected_order
    assert [s['slot'] for s in inputs['slots']] == list(range(1, 13))
    assert plan['provenance']['anchors'] == anchors
    assert plan['provenance']['maxFreshRequests'] == 12
    assert plan['provenance']['automaticRetries'] == plan['provenance']['manualRetries'] == 0
    assert plan['contextTokens'] == 8192 and plan['outputTokens'] == 1024
    assert plan['temperature'] == 0 and plan['requestDeadlineSeconds'] == 180
    assert plan['probeBudgetSeconds'] == 900 and plan['storageBudgetBytes'] == 67108864
    assert plan['serviceLifetimeSeconds'] == 1200 and plan['minimumServiceRemainingAtStart'] == 1140
    for slot in inputs['slots']:
        p = Path(slot['prompt']['path'])
        assert p == HERE / 'prompts' / f"step-{slot['anchorStep']:03d}-{slot['condition']}.txt"
        assert identity(p) == {k: slot['prompt'][k] for k in ('bytes', 'sha256')}
    rows = []
    for step, transform in zip(anchors, transforms['anchors'], strict=True):
        entry, prior = entries[step], entries[step - 30]
        a = (HERE / 'prompts' / f'step-{step:03d}-A.txt').read_bytes()
        b = (HERE / 'prompts' / f'step-{step:03d}-B.txt').read_bytes()
        assert a == entry['exactPrompt'].encode('utf-8')
        assert hashlib.sha256(a).hexdigest() == entry['identity']['promptSha256']
        original = load(bundle / 'journals' / (entry['identity']['journalId'] + '.json'))['pending']
        assert a == original['prompt'].encode('utf-8')
        assert original['memory'] == entry['memory']
        prefix, marker, rest = a.partition(b'\n\nOPTIONAL READOUT\n')
        assert marker
        readout_body, marker2, rest = rest.partition(b'\n\nPREVIOUS JOURNAL\n')
        assert marker2
        memory_body, marker3, suffix_body = rest.partition(b'\n\nWRITING BOUNDARY\n')
        assert marker3
        readout, memory, suffix = marker + readout_body, marker2 + memory_body, marker3 + suffix_body
        assert b == prefix + memory + readout + suffix
        assert a == prefix + readout + memory + suffix and a != b and len(a) == len(b)
        label = b'Full previous text as one JSON string: '
        _, label_found, encoded = memory.partition(label)
        assert label_found and encoded.endswith(b'\nEND PREVIOUS JOURNAL')
        decoded = json.loads(encoded[:-len(b'\nEND PREVIOUS JOURNAL')])
        assert decoded == prior['journalText'] == original['memory']['entry']['text']
        prior_object = load(bundle / 'journals' / (prior['identity']['journalId'] + '.json'))['pending']['entry']
        assert original['memory']['entry'] == prior_object
        assert original['memory']['appliedStep'] == step - 29
        expected_return = f'Recorded text return: the entry observed at step {step - 30} first entered numerical input at step {step - 29}.'
        assert expected_return.encode() in suffix
        assert f'The numerical clock is held at observation step {step}; no new readout arrives while this entry is written.'.encode() in suffix
        assert transform['anchorStep'] == step and transform['sourceIdentity'] == entry['identity']
        for key, value in [('prefix', prefix), ('readout', readout), ('memory', memory), ('suffix', suffix)]:
            assert transform['blocks'][key] == {'bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest()}
        rows.append({'step': step, 'bytesEach': len(a), 'aExactOriginalJournalPrompt': True,
                     'bExactBlockSwap': True, 'decodedMemoryEqualsOriginalPriorJournal': True,
                     'memoryObservedStep': step - 30, 'memoryAppliedStep': step - 29})
    after = {str(p): identity(p) for p in paths}
    assert before == after
    result = {'schema': 'reservoir-context-order-independent-input-review-v1', 'status': 'passed',
              'startedAtUtc': started, 'endedAtUtc': datetime.now(timezone.utc).isoformat(),
              'reviewerScript': identity(Path(__file__)), 'inputsBefore': before, 'inputsAfter': after,
              'inputsUnchanged': True, 'originalBundleFiles': len(bundle_paths), 'promptFiles': 12,
              'anchorResults': rows, 'newResponsesRead': 0, 'modelsContacted': False,
              'productionVerifierExecuted': False,
              'scope': 'Independent byte reconstruction and source joins; existing pinned replay receipt reused.'}
    with (HERE / 'independent-inputs-review-01.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'anchors': len(rows), 'sourceFiles': len(bundle_paths),
                      'receipt': identity(HERE / 'independent-inputs-review-01.json')}))


if __name__ == '__main__':
    main()
