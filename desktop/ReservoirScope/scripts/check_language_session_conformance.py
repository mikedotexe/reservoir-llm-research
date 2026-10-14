#!/usr/bin/env python3
"""Independently replay explicit supplied-response records and negative controls.

The Swift binary and native source identities must match an earlier retained
receipt. Records, binaries, baseline and relevant source files are checked again
after execution. Only temporary controls and a new exclusive receipt are written.
No provider, historical record path, app store or live system is contacted.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile

from check_action_session_conformance import mutations as action_mutations
from check_pair_session_conformance import mutations as pair_mutations
from check_fresh_conformance import DESKTOP, ROOT, execute, identity


def mutations(record: dict):
    def changed(label, alter):
        value = deepcopy(record)
        alter(value)
        return label, value

    stage = record.get('recipeVersion') == 'essentials-v1'
    if stage:
        yield changed('seeded-weight', lambda r: r['model']['inputWeights'].__setitem__(
            0, r['model']['inputWeights'][0] + 0.125))
        arms = [(None, record['turns'])]
    else:
        yield from (pair_mutations(record) if record.get('left') else action_mutations(record))
        arms = [(arm, record[arm]['actions']) for arm in ['left', 'right'] if record.get(arm)]

    for arm, turns in arms:
        prefix = 'stage' if arm is None else arm

        def at(r, i, arm=arm):
            return r['turns'][i] if arm is None else r[arm]['actions'][i]

        if turns:
            yield changed(f'{prefix}-prompt', lambda r: at(r, 0).__setitem__(
                'prompt', at(r, 0)['prompt'] + '\nAltered observation.'))
        for i, turn in enumerate(turns):
            if turn['status'] == 'completed':
                yield changed(f'{prefix}-accepted-length', lambda r, i=i:
                              at(r, i).__setitem__('stopReason', 'length'))
                yield changed(f'{prefix}-accepted-negative-tokens', lambda r, i=i:
                              at(r, i).__setitem__('tokenCount', -1))
                if stage:
                    yield changed('stage-response-codec', lambda r, i=i:
                                  at(r, i)['encodedFeatures'].__setitem__(
                                      0, at(r, i)['encodedFeatures'][0] + 0.125))
                    if turn.get('applicationStep') is not None:
                        yield changed('stage-application-boundary', lambda r, i=i:
                                      at(r, i).__setitem__('applicationStep', at(r, i)['observedStep']))
                else:
                    yield changed(f'{prefix}-accepted-incomplete', lambda r, i=i:
                                  at(r, i).__setitem__('providerComplete', False))
                    yield changed(f'{prefix}-accepted-undispatched', lambda r, i=i:
                                  at(r, i).__setitem__('requestStarted', False))
                break
        for i, turn in enumerate(turns):
            if turn['status'] in ('failed', 'cancelled'):
                yield changed(f'{prefix}-failed-feedback', lambda r, i=i:
                              at(r, i).__setitem__('semanticVector', [0.125] * 48))
                if turn['status'] == 'cancelled':
                    # Native stage records allow inert raw diagnostics on failed
                    # or cancelled turns; accepted reply/feedback remains forbidden.
                    field = 'reply' if stage else 'rawReply'
                    label = 'accepted-text' if stage else 'response'
                    yield changed(f'{prefix}-cancelled-{label}', lambda r, i=i, field=field:
                                  at(r, i).__setitem__(field, 'Unaccepted late response.'))
                break


def expected_counts(record):
    if record.get('recipeVersion') == 'essentials-v1':
        return len(record['frames']), len(record['turns'])
    arms = [record[arm] for arm in ['left', 'right'] if record.get(arm)]
    return sum(len(a['frames']) for a in arms), sum(len(a['actions']) for a in arms)


def accepted(outcomes, record):
    if any(value['exitCode'] != 0 for value in outcomes.values()):
        return False
    try:
        report = json.loads(outcomes['rust']['stdout'])
    except (ValueError, KeyError):
        return False
    steps, turns = expected_counts(record)
    return (report.get('status') == 'passed' and report.get('modelsContacted') is False
            and report.get('checkedSteps') == steps and report.get('checkedTurns') == turns)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--swift', type=Path, required=True)
    parser.add_argument('--rust', type=Path, required=True)
    parser.add_argument('--swift-baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require', action='append', default=[])
    parser.add_argument('records', nargs='+', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Receipt exists; select a new output path.')
    paths = [args.swift, args.rust, args.swift_baseline, *args.records]
    for path in paths:
        if path.is_symlink() or not path.is_file():
            parser.error(f'Expected an explicit regular file: {path}')
    if len({p.resolve() for p in args.records}) != len(args.records):
        parser.error('Duplicate input records would inflate coverage.')
    before = [identity(p) for p in paths]
    baseline = json.loads(args.swift_baseline.read_text(encoding='utf-8'))
    prior_swift = next((e for e in baseline.get('executables', [])
                        if Path(e['path']).name == 'essentials-run'), None)
    native_paths = sorted((ROOT / 'essentials').glob('*/*.swift'))
    prior_native = {str(Path(s['path']).resolve()): s
                    for s in baseline.get('sources', []) if s['path'].endswith('.swift')}
    native = [identity(p) for p in native_paths]
    native_match = bool(native) and all(
        n['sha256'] == prior_native.get(n['path'], {}).get('sha256') for n in native)
    swift_match = prior_swift is not None and before[0]['sha256'] == prior_swift['sha256']
    if not native_match or not swift_match:
        parser.error('Swift binary/native sources differ from the supplied frozen baseline.')
    sources = [Path(__file__).resolve(), Path(__file__).with_name('check_fresh_conformance.py'),
               Path(__file__).with_name('check_action_session_conformance.py'),
               Path(__file__).with_name('check_pair_session_conformance.py'),
               *native_paths, *sorted((DESKTOP / 'crates/reservoir-core/src').glob('*.rs')),
               DESKTOP / 'crates/reservoir-core/examples/language_session_fixtures.rs',
               DESKTOP / 'crates/reservoir-core/tests/session_language.rs',
               DESKTOP / 'Cargo.lock', DESKTOP / 'crates/reservoir-core/Cargo.toml']
    source_before = [identity(p) for p in sources]
    checks, coverage = [], Counter()
    with tempfile.TemporaryDirectory(prefix='scope-language-controls-') as temporary:
        for number, path in enumerate(args.records):
            original_bytes = path.read_bytes()
            record = json.loads(original_bytes)
            family = record.get('recipeVersion', record.get('format'))
            if (family not in ('essentials-v1', 'essentials-actions-v3')
                    or record['specification']['language']['backend'] != 'ollama'):
                parser.error(f'Expected an explicit supported local-model record: {path}')
            original = {'swift': execute(args.swift, path, False), 'rust': execute(args.rust, path, True)}
            negatives = []
            for label, altered in mutations(record):
                control = Path(temporary) / f'{number}-{label}.json'
                control.write_text(json.dumps(altered, ensure_ascii=False), encoding='utf-8')
                outcomes = {'swift': execute(args.swift, control, False), 'rust': execute(args.rust, control, True)}
                negatives.append({'mutation': label, **outcomes,
                                  'rejectedByBoth': all(v['exitCode'] == 1 for v in outcomes.values())})
                coverage[label] += 1
            compatibility = []
            if family == 'essentials-v1':
                for i, turn in enumerate(record['turns']):
                    if turn['status'] == 'cancelled':
                        retained = deepcopy(record)
                        retained['turns'][i]['rawReply'] = 'Unaccepted late response.'
                        control = Path(temporary) / f'{number}-stage-cancelled-raw-diagnostic.json'
                        control.write_text(json.dumps(retained, ensure_ascii=False), encoding='utf-8')
                        outcomes = {'swift': execute(args.swift, control, False),
                                    'rust': execute(args.rust, control, True)}
                        compatibility.append({'case': 'stage-cancelled-inert-raw-diagnostic', **outcomes,
                                              'acceptedByBoth': accepted(outcomes, retained)})
            row = {'input': identity(path), 'family': family, 'recordedStatus': record['status'],
                   'original': original, 'expectedCounts': dict(zip(('steps', 'turns'), expected_counts(record))),
                   'negativeControls': negatives, 'compatibilityControls': compatibility,
                   'originalBytesUnchanged': original_bytes == path.read_bytes()}
            row['passed'] = (row['originalBytesUnchanged'] and accepted(original, record)
                             and all(n['rejectedByBoth'] for n in negatives)
                             and all(n['acceptedByBoth'] for n in compatibility))
            checks.append(row)
    stable = before == [identity(p) for p in paths]
    sources_stable = source_before == [identity(p) for p in sources]
    missing = sorted(set(args.require) - coverage.keys())
    receipt = {'schema': 'reservoir-scope.supplied-language-session-conformance.v1',
               'executedAtUtc': datetime.now(timezone.utc).isoformat(),
               'executables': before[:2], 'swiftBaseline': before[2],
               'swiftBinaryMatchesBaseline': swift_match, 'nativeSourcesMatchBaseline': native_match,
               'sources': source_before, 'sourcesStable': sources_stable, 'inputsStable': stable,
               'modelsContacted': False, 'historicalPathsRead': False,
               'checks': checks, 'mutationCoverage': dict(coverage), 'requiredCoverageMissing': missing,
               'passed': stable and sources_stable and not missing and all(c['passed'] for c in checks),
               'limits': 'Numerical/text replay and bounded corruption controls of supplied-response records. '
                         'Provider metadata does not authenticate an actual model or dispatch. '
                         'Durable app storage, HTTP cancellation, UI and platform behavior need separate evidence. '
                         'Unsupported-response fixtures retain explicit cancellation in the portable format; '
                         'unaccepted raw diagnostic evidence belongs to local checkpoints.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(receipt, output, indent=2)
        output.write('\n')
    print(json.dumps({'passed': receipt['passed'], 'records': len(checks),
                      'mutations': sum(coverage.values()), 'mutationCoverage': dict(coverage),
                      'acceptedCompatibilityControls': sum(len(c['compatibilityControls']) for c in checks),
                      'missing': missing, 'receipt': str(args.output)}))
    if not receipt['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
