#!/usr/bin/env python3
"""Replay supplied action records and targeted mutations in unchanged Swift and Rust.

The only writes are a new receipt and temporary negative controls. No model or
historical path is opened. Mutation coverage is reported; --require refuses a
qualification corpus that never exercises a required mechanism.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile

from check_fresh_conformance import DESKTOP, ROOT, execute, identity


def mutations(record: dict):
    def changed(label, transform):
        value = deepcopy(record)
        transform(value)
        return label, value

    yield changed('seeded-weight', lambda r: r['right']['model']['inputWeights'].__setitem__(
        0, r['right']['model']['inputWeights'][0] + 0.125))
    arm = record['right']
    for i, action in enumerate(arm['actions']):
        if action.get('memoryText') is not None:
            yield changed('memory-text', lambda r, i=i: r['right']['actions'][i].__setitem__(
                'memoryText', action['memoryText'] + ' altered memory'))
            break
    for i, action in enumerate(arm['actions']):
        if action.get('chosenAction') == 'WAIT':
            def grant_wait_feedback(r, i=i):
                r['right']['actions'][i]['semanticVector'] = [0.125] * 48
                r['right']['actions'][i]['applicationStep'] = r['right']['actions'][i]['observedStep'] + 1
            yield changed('wait-feedback', grant_wait_feedback)
            break
    for i, frame in enumerate(arm['frames']):
        if frame.get('control') is not None:
            def alter_control(r, i=i):
                c = r['right']['frames'][i]['control']
                c['appliedRetention'] += 0.0005 if c['appliedRetention'] < 0.99 else -0.0005
            yield changed('controller-retention', alter_control)
            break
    if (record.get('tape') or {}).get('packets'):
        yield changed('tape-vector', lambda r: r['tape']['packets'][0]['semanticVector'].__setitem__(
            0, r['tape']['packets'][0]['semanticVector'][0] + 0.125))
    for i, action in enumerate(arm['actions']):
        if action.get('applicationStep') is not None:
            yield changed('application-boundary', lambda r, i=i: r['right']['actions'][i].__setitem__(
                'applicationStep', r['right']['actions'][i]['observedStep']))
            break
    if arm['journals']:
        yield changed('journal-content', lambda r: r['right']['journals'][0].__setitem__(
            'text', r['right']['journals'][0]['text'] + ' altered journal'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--swift', required=True, type=Path)
    parser.add_argument('--rust', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--require', action='append', default=[])
    parser.add_argument('records', nargs='+', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Receipt exists; choose a new output path.')
    paths = [args.swift, args.rust, *args.records]
    for path in paths:
        if path.is_symlink() or not path.is_file():
            parser.error(f'Expected an explicit regular file: {path}')
    before = [identity(p) for p in paths]
    coverage = Counter()
    checks = []
    with tempfile.TemporaryDirectory(prefix='scope-action-controls-') as temporary:
        for number, path in enumerate(args.records):
            original_bytes = path.read_bytes()
            record = json.loads(original_bytes)
            if record.get('format') != 'essentials-actions-v3' or record.get('left') is not None:
                parser.error(f'Expected a standalone current action record: {path}')
            original = {'swift': execute(args.swift, path, False), 'rust': execute(args.rust, path, True)}
            negatives = []
            for label, altered in mutations(record):
                control = Path(temporary) / f'{number}-{label}.json'
                control.write_text(json.dumps(altered, ensure_ascii=False), encoding='utf-8')
                results = {'swift': execute(args.swift, control, False), 'rust': execute(args.rust, control, True)}
                negatives.append({'mutation': label, **results, 'rejectedByBoth': all(r['exitCode'] == 1 for r in results.values())})
                coverage[label] += 1
            row = {'record': identity(path), 'stage': record['specification']['stage'],
                   'mode': record['specification']['mode'], 'original': original, 'negativeControls': negatives,
                   'originalBytesUnchanged': original_bytes == path.read_bytes()}
            row['passed'] = (row['originalBytesUnchanged'] and all(r['exitCode'] == 0 for r in original.values())
                             and all(r['rejectedByBoth'] for r in negatives))
            checks.append(row)
    stable = before == [identity(p) for p in paths]
    missing = sorted(set(args.require) - coverage.keys())
    sources = [Path(__file__).resolve(), Path(__file__).with_name('check_fresh_conformance.py'),
               *sorted((ROOT / 'essentials').glob('*/*.swift')),
               *sorted((DESKTOP / 'crates/reservoir-core/src').glob('*.rs'))]
    receipt = {'schema': 'reservoir-scope.standalone-action-conformance.v1',
               'executedAtUtc': datetime.now(timezone.utc).isoformat(), 'executables': before[:2],
               'sources': [identity(p) for p in sources], 'inputsStable': stable,
               'checks': checks, 'mutationCoverage': dict(coverage), 'requiredCoverageMissing': missing,
               'passed': stable and not missing and all(c['passed'] for c in checks),
               'modelsContacted': False, 'historicalPathsRead': False,
               'limits': 'Independent portable replay only. File save/read behavior, lifecycle, UI, platform and scientific-benefit claims require separate evidence.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(receipt, output, indent=2)
        output.write('\n')
    print(json.dumps({'passed': receipt['passed'], 'records': len(checks), 'mutationCoverage': dict(coverage),
                      'missing': missing, 'receipt': str(args.output)}))
    if not receipt['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
