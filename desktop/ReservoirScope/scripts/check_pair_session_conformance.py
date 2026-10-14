#!/usr/bin/env python3
"""Replay explicit fresh paired records with unchanged Swift and current Rust.

Writes only a new receipt and temporary mutation controls. No model connections,
record provenance-path reads or changes to original records/native sources occur.
The --require controls bind declared mutation coverage, not exhaustive correctness.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile

from check_action_session_conformance import mutations as right_mutations
from check_fresh_conformance import DESKTOP, ROOT, execute, identity


def mutations(record: dict):
    yield from right_mutations(record)

    def changed(label, transform):
        value = deepcopy(record)
        transform(value)
        return label, value

    yield changed('left-seeded-weight', lambda r: r['left']['model']['inputWeights'].__setitem__(
        0, r['left']['model']['inputWeights'][0] + 0.125))
    yield changed('arm-identity', lambda r: r['left'].__setitem__('arm', 'right'))
    if record['left']['frames']:
        yield changed('paired-clock', lambda r: r['left']['frames'][-1].__setitem__(
            'step', r['left']['frames'][-1]['step'] + 1))
    if record['left']['actions']:
        yield changed('unmatched-opportunity', lambda r: r['left']['actions'].pop())
    for arm in ['left', 'right']:
        for i, action in enumerate(record[arm]['actions']):
            if action.get('requestStarted') and action.get('requestOrder') is not None:
                yield changed(f'{arm}-request-order', lambda r, arm=arm, i=i:
                    r[arm]['actions'][i].__setitem__('requestOrder', 3 - r[arm]['actions'][i]['requestOrder']))
                break
        for i, action in enumerate(record[arm]['actions']):
            receipt = action.get('saveReceipt') or {}
            if receipt.get('status') == 'saved':
                other = 'right' if arm == 'left' else 'left'
                yield changed(f'{arm}-save-namespace', lambda r, arm=arm, i=i, other=other:
                    r[arm]['actions'][i]['saveReceipt'].__setitem__(
                        'relativePath', f"{other}/{r[arm]['actions'][i]['saveReceipt']['entryID']}.json"))
                break
    for i, action in enumerate(record['left']['actions']):
        if action.get('memoryText') is not None:
            yield changed('left-memory-text', lambda r, i=i: r['left']['actions'][i].__setitem__(
                'memoryText', r['left']['actions'][i]['memoryText'] + ' altered memory'))
            break
    if record['specification']['comparisonKind'] == 'observation':
        yield changed('observation-channel', lambda r: r['right'].__setitem__('observationChannel', 'sensory'))
        for i, action in enumerate(record['right']['actions']):
            if 'x[31]=' in action.get('prompt', ''):
                yield changed('observation-coordinate-prompt', lambda r, i=i:
                    r['right']['actions'][i].__setitem__('prompt', r['right']['actions'][i]['prompt'].replace('x[31]=', 'x[32]=')))
                break


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--swift', type=Path, required=True)
    parser.add_argument('--rust', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require', action='append', default=[])
    parser.add_argument('records', nargs='+', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Receipt exists; select a new output path.')
    paths = [args.swift, args.rust, *args.records]
    for path in paths:
        if path.is_symlink() or not path.is_file():
            parser.error(f'Expected an explicit regular file: {path}')
    before = [identity(p) for p in paths]
    coverage = Counter()
    checks = []
    with tempfile.TemporaryDirectory(prefix='scope-pair-controls-') as directory:
        for number, path in enumerate(args.records):
            original_bytes = path.read_bytes()
            record = json.loads(original_bytes)
            if record.get('format') != 'essentials-actions-v3' or not record.get('left'):
                parser.error(f'Expected a current paired action record: {path}')
            original = {'swift': execute(args.swift, path, False), 'rust': execute(args.rust, path, True)}
            negatives = []
            for label, altered in mutations(record):
                temporary = Path(directory) / f'{number}-{label}.json'
                temporary.write_text(json.dumps(altered, ensure_ascii=False), encoding='utf-8')
                outcomes = {'swift': execute(args.swift, temporary, False), 'rust': execute(args.rust, temporary, True)}
                negatives.append({'mutation': label, **outcomes, 'rejectedByBoth': all(x['exitCode'] == 1 for x in outcomes.values())})
                coverage[label] += 1
            row = {'record': identity(path), 'stage': record['specification']['stage'],
                   'mode': record['specification']['mode'], 'kind': record['specification']['comparisonKind'],
                   'recordedOutcome': record['status'], 'original': original, 'negativeControls': negatives,
                   'originalBytesUnchanged': path.read_bytes() == original_bytes}
            row['passed'] = (row['originalBytesUnchanged'] and all(x['exitCode'] == 0 for x in original.values())
                             and all(x['rejectedByBoth'] for x in negatives))
            checks.append(row)
    missing = sorted(set(args.require) - coverage.keys())
    stable = before == [identity(p) for p in paths]
    sources = [Path(__file__).resolve(), Path(__file__).with_name('check_fresh_conformance.py'),
               Path(__file__).with_name('check_action_session_conformance.py'),
               *sorted((ROOT / 'essentials').glob('*/*.swift')),
               *sorted((DESKTOP / 'crates/reservoir-core/src').glob('*.rs'))]
    receipt = {'schema': 'reservoir-scope.paired-session-conformance.v1',
               'executedAtUtc': datetime.now(timezone.utc).isoformat(), 'executables': before[:2],
               'sources': [identity(p) for p in sources], 'inputsStable': stable, 'checks': checks,
               'mutationCoverage': dict(coverage), 'requiredCoverageMissing': missing,
               'passed': stable and not missing and all(c['passed'] for c in checks),
               'modelsContacted': False, 'historicalPathsRead': False,
               'limits': 'Portable numerical/text replay and individual mutation cases. Some controls alter more than one invariant. Filesystem receipts, partial-boundary checkpoints, UI, platform and scientific-benefit claims require separate evidence.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(receipt, output, indent=2)
        output.write('\n')
    print(json.dumps({'passed': receipt['passed'], 'records': len(checks), 'mutations': sum(coverage.values()),
                      'mutationCoverage': dict(coverage), 'missing': missing, 'receipt': str(args.output)}))
    if not receipt['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
