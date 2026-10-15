#!/usr/bin/env python3
"""Prepare exact, standalone block-order diagnostic inputs; no network or model calls."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1]
SOURCE = HERE.parent / '2026-10-14-v8-writing-episode01/real-model-export-01'
RECEIPT_SHA = '07aff62e23ee5c08e85e97c2ae93702d3b145473aa38d58c0c0345d85d1aa603'
MATERIAL_SHA = '12d0a9f863f1471e5eeb08a11f941b34a486abbee3946f6383e337a3e6e260e0'
MARKERS = ('\n\nOPTIONAL READOUT\n', '\n\nPREVIOUS JOURNAL\n', '\n\nWRITING BOUNDARY\n')
ANCHORS = (60, 120, 180, 240, 300, 360)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(path):
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': sha(raw)}


def split_prompt(prompt, previous):
    if not prompt.startswith('Reservoir Scope · ongoing journal · reservoir-journal-v8\n'):
        raise ValueError('Unexpected source prompt version')
    if any(prompt.count(marker) != 1 for marker in MARKERS):
        raise ValueError('Missing or ambiguous outer headings')
    a, b, c = [prompt.index(marker) for marker in MARKERS]
    if not 0 < a < b < c:
        raise ValueError('Unexpected block order')
    prefix, readout, memory, suffix = prompt[:a], prompt[a:b], prompt[b:c], prompt[c:]
    label = 'Full previous text as one JSON string: '
    if memory.count(label) != 1 or not memory.endswith('\nEND PREVIOUS JOURNAL'):
        raise ValueError('Unexpected memory envelope')
    encoded = memory.split(label, 1)[1].removesuffix('\nEND PREVIOUS JOURNAL')
    if json.loads(encoded) != previous:
        raise ValueError('Decoded previous writing differs')
    if not suffix.endswith('Write the next entry in whatever direction seems worth pursuing.'):
        raise ValueError('Final invitation differs')
    swapped = prefix + memory + readout + suffix
    if len(swapped.encode()) != len(prompt.encode()) or swapped == prompt:
        raise ValueError('Swap invariant failed')
    return swapped, {'prefix': prefix, 'readout': readout, 'memory': memory, 'suffix': suffix}


def save_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def main():
    assert identity(SOURCE/'receipt.json')['sha256'] == RECEIPT_SHA
    receipt = json.loads((SOURCE/'receipt.json').read_text())
    assert receipt['status'] == 'passed' and receipt['originalUnchanged'] is True
    assert identity(SOURCE/'quality-review-material.json')['sha256'] == MATERIAL_SHA == receipt['reviewMaterial']['sha256']
    journals = json.loads((SOURCE/'quality-review-material.json').read_text())['journals']
    by_step = {j['identity']['observedStep']: j for j in journals}
    assert sorted(by_step) == list(range(30, 361, 30))
    prompt_dir = HERE/'prompts'
    prompt_dir.mkdir(exist_ok=False)
    slots, transformations = [], []
    for index, step in enumerate(ANCHORS):
        entry = by_step[step]
        prior = by_step[step - 30]
        prompt = entry['exactPrompt']
        memory = entry['memory']['entry']
        assert entry['identity']['promptVersion'] == 'reservoir-journal-v8'
        assert sha(prompt.encode()) == entry['identity']['promptSha256']
        assert memory['text'] == prior['journalText'] and memory['id'] == prior['identity']['journalId']
        assert sha(memory['text'].encode()) == memory['sha256'] == prior['identity']['textSha256']
        swapped, parts = split_prompt(prompt, memory['text'])
        refs = {}
        for condition, text in [('A', prompt), ('B', swapped)]:
            path = prompt_dir/f'step-{step:03d}-{condition}.txt'
            with path.open('xb') as stream:
                stream.write(text.encode())
            refs[condition] = identity(path)
        transformations.append({'anchorStep': step, 'sourceIdentity': entry['identity'],
            'memoryIdentity': {'journalId': memory['id'], 'sha256': memory['sha256'], 'bytes': len(memory['text'].encode())},
            'blocks': {k: {'sha256': sha(v.encode()), 'bytes': len(v.encode())} for k,v in parts.items()},
            'aExactSource': True, 'bOnlyBlockSwap': True, 'equalUtf8Bytes': True})
        for condition in ('AB' if index % 2 == 0 else 'BA'):
            slots.append({'slot': len(slots)+1, 'anchorStep': step, 'condition': condition, 'prompt': refs[condition]})
    save_json(HERE/'transformation-checks-01.json', {'schema':'reservoir-context-order-transform-v1',
        'status':'passed', 'sourceReceipt': identity(SOURCE/'receipt.json'),
        'sourceMaterial': identity(SOURCE/'quality-review-material.json'), 'anchors': transformations,
        'scope':'Exact bytes and decoded prior writing; not proof of model tokenization or processing.'})
    save_json(HERE/'frozen-inputs.json', {'schema':'reservoir-context-order-inputs-v1',
        'episodeId':'context-order-01', 'runPlan':identity(HERE/'run-plan.json'), 'slots':slots,
        'provenance': {'sourceReceipt':identity(SOURCE/'receipt.json'), 'sourceMaterial':identity(SOURCE/'quality-review-material.json'),
          'diagnosticOnly':True,'productionPromptUnchanged':True,'outputsEnterReservoir':False}})
    print(json.dumps({'slots':len(slots),'anchors':len(ANCHORS),'inputs':identity(HERE/'frozen-inputs.json')}))

if __name__ == '__main__':
    main()
