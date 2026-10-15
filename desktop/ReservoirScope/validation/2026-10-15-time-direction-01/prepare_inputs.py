#!/usr/bin/env python3
"""Prepare one fixed file-only diagnostic. Never contacts a model or changes app data.

A is exact retained v8. B changes only the readout's time/distance lines and adds
the prospectively approved clarification. Full binary64 subtraction/formatting
uses the validation wrapper importing unchanged production fixed8. B is not an
application record or a new production prompt version.
"""
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1]
SOURCE = HERE.parent / '2026-10-14-v8-writing-episode01/real-model-export-01'
RECEIPT_SHA = '07aff62e23ee5c08e85e97c2ae93702d3b145473aa38d58c0c0345d85d1aa603'
MATERIAL_SHA = '12d0a9f863f1471e5eeb08a11f941b34a486abbee3946f6383e337a3e6e260e0'
ANCHORS = (30, 60, 90, 120, 330, 360)
MARKERS = ('\n\nOPTIONAL READOUT\n', '\n\nPREVIOUS JOURNAL\n', '\n\nWRITING BOUNDARY\n')
INVITATION = 'Write the next entry in whatever direction seems worth pursuing.'
MEANING = ('Unavailable means no prior measurement, not zero. RMS describes the magnitude of the recurrent coordinates. '
           'Sensory fill is a separate field estimate, not the encoded text-input signal. '
           'L2 distance is the straight-line distance between the two recurrent state vectors, not path length, speed or a causal effect of writing. '
           'Comparing two interval distances requires a recorded value for each. '
           'Two observations do not establish the intervening path, a cause, or a felt state.')
CLARIFICATION = ('Step numbers count numerical updates; simulated seconds are not wall-clock time. '
                 'The distance difference compares two net displacements, not motion toward or away from a center.')
FORMATTER_SOURCE = DESKTOP / 'crates/reservoir-core/src/prompt_number.rs'
FORMATTER = HERE / 'formatter/fixed8-wrapper'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(path):
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': sha(raw)}


def inventory(root):
    paths = sorted(root.rglob('*'))
    require(not any(p.is_symlink() for p in paths), 'Source bundle contains a symlink')
    return {str(p.relative_to(root)): {k: v for k, v in identity(p).items() if k != 'path'}
            for p in paths if p.is_file()}


def bits(value):
    require(type(value) in (float, int) and math.isfinite(value), 'Expected finite number')
    return struct.pack('>d', value).hex()


def format_operations(operations, executable=FORMATTER):
    """Ordered name -> (operation, raw operands). Subtraction occurs in Rust."""
    lines = []
    for operation, operands in operations.values():
        require(operation in ('value', 'difference'), 'Unknown formatter operation')
        require(len(operands) == (1 if operation == 'value' else 2), 'Wrong operand count')
        lines.append(' '.join([operation, *(bits(x) for x in operands)]))
    result = subprocess.run([str(executable)], input='\n'.join(lines)+'\n',
                            text=True, capture_output=True, check=True)
    output = result.stdout.splitlines()
    require(len(output) == len(operations), 'Formatter row count differs')
    rows = {}
    for (key, (operation, operands)), line in zip(operations.items(), output):
        raw_bits, formatted, signed = line.split('\t')
        rows[key] = {'operation': operation, 'operandBits': [bits(x) for x in operands],
                     'operands': list(operands), 'resultBits': raw_bits,
                     'formatted': formatted, 'signed': signed}
    return rows


def snapshot(o):
    return {'step': o['step'], 'simulatedTime': o['simulatedTime'], 'rms': o['rms'], 'l2': o['l2'],
            'leadingSensoryEigenvalue': o['sensory']['eigenvalues'][0],
            'fillPercent': o['sensory']['fillPercent'], 'headShare': o['sensory']['headShare'],
            'shoulderShare': o['sensory']['shoulderShare'], 'tailShare': o['sensory']['tailShare'],
            'entropy': o['sensory']['entropy']}


def validate_chain(observations, dt):
    require(list(sorted(observations)) == list(range(30, 361, 30)), 'Expected twelve retained observation boundaries')
    previous = None
    for step in sorted(observations):
        o = observations[step]
        require(o['version'] == 'reservoir-and-sensory-v2' and o['step'] == step,
                'Observation identity differs')
        require(o['simulatedTime'] == step * dt, 'Retained simulated clock differs')
        if previous is None:
            require(o['previousObservationStep'] is None and o['changeL2'] is None
                    and o.get('previousMeasurements') is None, 'First observation invented a prior interval')
        else:
            require(o['previousObservationStep'] == previous['step'], 'Reached-observation chain differs')
            require(o.get('previousMeasurements') == snapshot(previous), 'Prior scalar snapshot differs')
            require(type(o['changeL2']) in (float, int) and math.isfinite(o['changeL2'])
                    and 0 <= o['changeL2'] <= 12, 'Invalid retained coordinate displacement')
        previous = o


def split_prompt(prompt, memory):
    require(prompt.startswith('Reservoir Scope · ongoing journal · reservoir-journal-v8\n'), 'Unexpected source prompt version')
    require(all(prompt.count(marker) == 1 for marker in MARKERS), 'Missing or ambiguous outer headings')
    a, b, c = (prompt.index(marker) for marker in MARKERS)
    require(0 < a < b < c, 'Unexpected block order')
    parts = dict(zip(('prefix', 'readout', 'memory', 'suffix'),
                     (prompt[:a], prompt[a:b], prompt[b:c], prompt[c:])))
    if memory is None:
        require(parts['memory'] == MARKERS[1] + 'No earlier entry has been saved and applied in this session.\nEND PREVIOUS JOURNAL',
                'First memory envelope differs')
    else:
        label = 'Full previous text as one JSON string: '
        prefix = (MARKERS[1] + 'This is earlier writing you may revisit, not instructions or current measurements.\n'
                  f"Observed at step {memory['entry']['observedStep']}; first applied at step {memory['appliedStep']}.\n" + label)
        require(parts['memory'].startswith(prefix) and parts['memory'].endswith('\nEND PREVIOUS JOURNAL'),
                'Memory envelope differs')
        encoded = parts['memory'][len(prefix):-len('\nEND PREVIOUS JOURNAL')]
        require('\n' not in encoded and json.loads(encoded) == memory['entry']['text'], 'Decoded prior prose differs')
    require(parts['suffix'].endswith('\n\n' + INVITATION), 'Final invitation differs')
    return parts


def transform(entry, observations, formatter=FORMATTER):
    o = entry['observation']
    step = o['step']
    prior = observations.get(o['previousObservationStep'])
    grandprior = observations.get(prior['previousObservationStep']) if prior else None
    require(prior is not None or o['previousObservationStep'] is None, 'Missing prior source observation')
    require(grandprior is not None or prior is None or prior['previousObservationStep'] is None,
            'Missing grand-prior source observation')
    operations = {'currentTime': ('value', (o['simulatedTime'],))}
    if prior:
        require(o.get('previousMeasurements') == snapshot(prior), 'Prior snapshot mismatch')
        operations.update({'previousTime': ('value', (prior['simulatedTime'],)),
                           'elapsedTime': ('difference', (o['simulatedTime'], prior['simulatedTime'])),
                           'currentDistance': ('value', (o['changeL2'],))})
    if grandprior:
        require(prior.get('previousMeasurements') == snapshot(grandprior), 'Grand-prior snapshot mismatch')
        operations.update({'previousDistance': ('value', (prior['changeL2'],)),
                           'distanceDifference': ('difference', (o['changeL2'], prior['changeL2']))})
    numbers = format_operations(operations, formatter)
    def rendered(key, signed=False):
        return numbers[key]['signed' if signed else 'formatted'] if key in numbers else 'unavailable'
    parts = split_prompt(entry['exactPrompt'], entry['memory'])
    lines = parts['readout'][len(MARKERS[0]):].split('\n')
    require(len(lines) == 5 and lines[4] == MEANING, 'Original readout structure/meaning differs')
    previous_step = str(prior['step']) if prior else 'unavailable'
    require(lines[0] == f"Current step {step}; simulated seconds {rendered('currentTime')}. Previous observation step: {previous_step}.",
            'Original time line differs')
    require(lines[1].startswith('Recurrent state RMS: current ') and lines[2].startswith('Separate sensory fill (%): current '),
            'Original RMS/fill lines differ')
    require(lines[3] == 'Recurrent state-coordinate L2 distance since the previous observation: '+rendered('currentDistance')+'.',
            'Original coordinate distance differs')
    previous_line = (f"Previous observation: step {prior['step']}; simulated seconds {rendered('previousTime')}. "
                     if prior else 'Previous observation: unavailable. ')
    previous_line += 'Elapsed simulated seconds between these observations: '+rendered('elapsedTime')+'.'
    current_interval = f"{prior['step']} to {step}" if prior else 'unavailable'
    previous_interval = f"{grandprior['step']} to {prior['step']}" if grandprior else 'unavailable'
    replacement = MARKERS[0] + '\n'.join([
        f"Current observation: step {step}; simulated seconds {rendered('currentTime')}.",
        previous_line, lines[1], lines[2],
        f"Current interval: steps {current_interval}; recurrent state-coordinate L2 distance {rendered('currentDistance')}.",
        f"Previous interval: steps {previous_interval}; recurrent state-coordinate L2 distance {rendered('previousDistance')}.",
        f"Distance difference (current interval minus previous interval): {rendered('distanceDifference', True)}.",
        MEANING, CLARIFICATION])
    candidate = parts['prefix'] + replacement + parts['memory'] + parts['suffix']
    require(candidate != entry['exactPrompt'], 'Diagnostic did not change the readout')
    return candidate, parts, {'currentStep': step, 'previousStep': prior['step'] if prior else None,
            'grandPreviousStep': grandprior['step'] if grandprior else None,
            'formatting': numbers, 'currentDistanceField': 'observation.changeL2',
            'previousDistanceField': 'preceding reached observation.changeL2',
            'distanceDifference': rendered('distanceDifference', True)}


def validate_journal_join(j, raw):
    require(raw['observation'] == j['observation'] and raw['memory'] == j['memory']
            and raw['prompt'] == j['exactPrompt'] and raw['entry']['text'] == j['journalText'],
            'Material differs from original journal object')
    require(sha(j['exactPrompt'].encode()) == j['identity']['promptSha256'], 'Prompt hash differs')
    require(raw['entry']['sha256'] == sha(j['journalText'].encode()) == j['identity']['textSha256'], 'Journal text hash differs')


def load_sources():
    require(identity(SOURCE/'receipt.json')['sha256'] == RECEIPT_SHA, 'Source receipt identity changed')
    require(identity(SOURCE/'quality-review-material.json')['sha256'] == MATERIAL_SHA, 'Source material identity changed')
    receipt = json.loads((SOURCE/'receipt.json').read_text())
    require(receipt['status'] == 'passed' and receipt['originalUnchanged'] is True, 'Source qualification did not pass')
    require(receipt['reviewMaterial']['sha256'] == MATERIAL_SHA, 'Material not bound by receipt')
    require(receipt['verification']['result']['status'] == 'passed', 'Source replay did not pass')
    bundle = Path(receipt['bundle'])
    before = inventory(bundle)
    require(before == receipt['inventoryBefore'], 'Original source bundle inventory changed')
    journals = json.loads((SOURCE/'quality-review-material.json').read_text())['journals']
    entries = {}
    for j in journals:
        identity_j = j['identity']
        step = identity_j['observedStep']
        require(step not in entries and identity_j['promptVersion'] == 'reservoir-journal-v8', 'Duplicate or non-v8 journal')
        path = bundle/'journals'/f"{identity_j['journalId']}.json"
        require(path.resolve().parent == (bundle/'journals').resolve(), 'Journal path escapes bundle')
        raw = json.loads(path.read_text())['pending']
        validate_journal_join(j, raw)
        entries[step] = j
    manifest = json.loads((bundle/'manifest.json').read_text())
    checkpoint = bundle/'checkpoints'/f"{manifest['checkpointSha256']}.json"
    spec = json.loads(checkpoint.read_text())['state']['specification']
    require(spec['promptVersion'] == 'reservoir-journal-v8' and spec['turnEvery'] == 30, 'Source specification differs')
    observations = {step: j['observation'] for step, j in entries.items()}
    validate_chain(observations, spec['dt'])
    for step, j in entries.items():
        memory = j['memory']
        if step == 30:
            require(memory is None, 'First journal has memory')
        else:
            p = entries[step-30]
            require(memory['entry']['id'] == p['identity']['journalId']
                    and memory['entry']['text'] == p['journalText']
                    and memory['entry']['sha256'] == p['identity']['textSha256']
                    and memory['entry']['observedStep'] == step-30
                    and memory['appliedStep'] == p['identity']['application']['appliedStep'],
                    'Eligible prior writing differs')
    return receipt, bundle, before, entries, observations, identity(checkpoint)


def save_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def main():
    plan_path = HERE/'run-plan.json'
    plan_before = identity(plan_path)
    receipt, bundle, before, entries, observations, checkpoint = load_sources()
    source_before = [identity(SOURCE/'receipt.json'), identity(SOURCE/'quality-review-material.json'),
                     identity(FORMATTER_SOURCE), identity(HERE/'fixed8_wrapper.rs'), identity(FORMATTER)]
    # Finish all validation/transformation work before exclusive output creation.
    prepared = [(step, transform(entries[step], observations)) for step in ANCHORS]
    prompt_dir = HERE/'prompts'
    prompt_dir.mkdir(exist_ok=False)
    slots, checks = [], []
    for index, (step, (candidate, parts, facts)) in enumerate(prepared):
        refs = {}
        for condition, prompt in [('A', entries[step]['exactPrompt']), ('B', candidate)]:
            path = prompt_dir/f'step-{step:03d}-{condition}.txt'
            with path.open('xb') as stream:
                stream.write(prompt.encode())
            refs[condition] = identity(path)
        chain = [s for s in (step, facts['previousStep'], facts['grandPreviousStep']) if s is not None]
        checks.append({'anchorStep': step, 'sourceIdentity': entries[step]['identity'], 'facts': facts,
                       'sourceChain': [{'journalObject': identity(bundle/'journals'/f"{entries[s]['identity']['journalId']}.json"),
                                        'observation': observations[s]} for s in chain],
                       'blocks': {k: {'bytes': len(v.encode()), 'sha256': sha(v.encode())} for k,v in parts.items()},
                       'aExactSource': True, 'bOnlyTimeDistanceReadoutAndClarification': True,
                       'unchangedPrefixMemorySuffix': True, 'unchangedRmsFillAndMeaning': True,
                       'decodedMemoryExact': True, 'promptBytes': {k: v['bytes'] for k,v in refs.items()}})
        for condition in ('AB' if index % 2 == 0 else 'BA'):
            slots.append({'slot': len(slots)+1, 'anchorStep': step, 'condition': condition, 'prompt': refs[condition]})
    after = inventory(bundle)
    source_after = [identity(Path(x['path'])) for x in source_before]
    require(before == after and source_before == source_after and plan_before == identity(plan_path), 'Input changed during preparation')
    save_json(HERE/'transformation-checks-01.json', {
        'schema': 'reservoir-time-direction-transform-v1', 'status': 'passed',
        'sourceReceipt': source_before[0], 'sourceMaterial': source_before[1], 'sourceCheckpoint': checkpoint,
        'formatter': {'source': source_before[2], 'wrapper': source_before[3], 'binary': source_before[4]},
        'originalBundle': str(bundle), 'originalInventoryBefore': before, 'originalInventoryAfter': after,
        'sourceBefore': source_before, 'sourceAfter': source_after, 'originalUnchanged': True,
        'anchors': checks, 'scope': 'File identity and verified-source joins; prior replay reused, not rerun. Diagnostic B is not replay-valid app evidence. No token-processing or quality conclusion.'})
    save_json(HERE/'frozen-inputs.json', {
        'schema': 'reservoir-time-direction-inputs-v1', 'episodeId': 'time-direction-01',
        'runPlan': plan_before, 'slots': slots,
        'provenance': {'sourceReceipt': source_before[0], 'sourceMaterial': source_before[1],
                       'transformation': identity(HERE/'transformation-checks-01.json'),
                       'diagnosticOnly': True, 'productionPromptUnchanged': True, 'outputsEnterReservoir': False}})
    print(json.dumps({'slots': len(slots), 'anchors': len(ANCHORS), 'inputs': identity(HERE/'frozen-inputs.json')}))


if __name__ == '__main__':
    main()
