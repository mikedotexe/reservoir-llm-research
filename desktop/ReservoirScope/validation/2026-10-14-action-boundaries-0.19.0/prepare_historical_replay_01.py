#!/usr/bin/env python3
"""Prospective 0.19 preparation: bind twelve old exports without executing a CLI.

Run only when the lead authorizes qualification. Prior selection and verification
receipts are the basis; a missing or changed export fails instead of narrowing
the denominator. No regeneration, app data discovery, model or service access.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('historical_replay', HERE / 'replay_historical.py')
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


def main():
    old = HERE.parent / '2026-10-14-writing-scope-0.18.0'
    real = HERE.parent / '2026-10-14-v6-writing-episode02'
    basis_selection = old / 'historical-replay-cases-01.json'
    previous = HELPER.decode(basis_selection.read_bytes())
    cases = previous['cases']
    HELPER.require(len(cases) == 8, 'Previous eight-case selection changed')
    for name, path, shape in [
        ('v6-synthetic-held', old / 'original-export-evidence-01.json', 'synthetic'),
        ('v6-synthetic-paused-recovery', old / 'recovered-export-evidence-01.json', 'synthetic'),
        ('v6-real-partial', real / 'real-model-export-01/receipt.json', 'real'),
        ('v6-real-partial-paused-recovery', real / 'recovered-export-01/receipt.json', 'real'),
    ]:
        receipt = HELPER.decode(path.read_bytes())
        HELPER.require(receipt['status'] == 'passed', 'Prior qualification did not pass')
        if shape == 'synthetic':
            value = receipt['staticJoins']
            HELPER.require(value['originalUnchanged'], 'Prior original changed')
            bundle, inventory = value['bundle'], value['inventory']
            step, count = value['manifest']['step'], value['manifest']['journalCount']
        else:
            HELPER.require(receipt['originalUnchanged'], 'Prior original changed')
            bundle, inventory = receipt['bundle'], receipt['inventoryBefore']
            step = receipt['evidence']['manifest']['step']
            count = receipt['evidence']['manifest']['journalCount']
        cases.append({'name': name, 'bundle': bundle,
                      'promptVersion': 'reservoir-journal-v6', 'step': step,
                      'journalCount': count, 'basisReceipt': HELPER.identity(path),
                      'expectedInventory': inventory})

    report = {'schema': 'reservoir-historical-replay-preparation-v2',
              'startedAtUtc': HELPER.utc(), 'status': 'running',
              'script': HELPER.identity(Path(__file__).resolve()),
              'replayHelper': HELPER.identity(HERE / 'replay_historical.py'),
              'priorSelection': HELPER.identity(basis_selection),
              'applicationsOrModelsInvoked': False, 'cases': []}
    with (HERE / 'historical-replay-preparation-01.json').open('x') as output:
        try:
            for case in cases:
                bundle = Path(case['bundle'])
                HELPER.require(any(bundle.is_relative_to(p) for p in HELPER.APPROVED_QA),
                               'Export outside approved owned QA roots')
                HELPER.require(HELPER.identity(Path(case['basisReceipt']['path'])) == case['basisReceipt'],
                               'Prior verification receipt changed')
                before = HELPER.inventory(bundle)
                HELPER.require(before == case['expectedInventory'], 'Historical bytes changed: ' + case['name'])
                manifest = HELPER.decode((bundle / 'manifest.json').read_bytes())
                HELPER.require(manifest['config'].get('promptVersion', 'reservoir-journal-v1') == case['promptVersion'],
                               'Historical prompt version differs')
                HELPER.require(manifest['step'] == case['step'] and manifest['journalCount'] == case['journalCount'],
                               'Historical cursor/count differs')
                report['cases'].append({'name': case['name'], 'files': len(before),
                                        'bytes': sum(x['bytes'] for x in before.values()),
                                        'inventoryBefore': before})
            for case, row in zip(cases, report['cases']):
                HELPER.require(HELPER.inventory(Path(case['bundle'])) == row['inventoryBefore'],
                               'Historical source changed during preparation')
                HELPER.require(HELPER.identity(Path(case['basisReceipt']['path'])) == case['basisReceipt'],
                               'Prior basis receipt changed during preparation')
                row['originalUnchanged'] = True
            HELPER.require(HELPER.identity(basis_selection) == report['priorSelection'], 'Selection changed')
            HELPER.require(HELPER.identity(HERE / 'replay_historical.py') == report['replayHelper'], 'Helper changed')
            selection = {'schema': 'reservoir-historical-replay-selection-v3',
                         'selectedAtUtc': HELPER.utc(), 'basisSelection': report['priorSelection'],
                         'scope': 'Twelve fixed owned exports; new 0.19 production replay not yet executed.',
                         'v2HistoricalExportCoverage': previous['v2HistoricalExportCoverage'],
                         'applicationsOrModelsInvoked': False, 'cases': cases}
            selected = HERE / 'historical-replay-cases-01.json'
            with selected.open('x') as stream:
                json.dump(selection, stream, indent=2)
                stream.write('\n')
            report.update(status='passed', selection=HELPER.identity(selected),
                          productionReplayExecuted=False, allOriginalsUnchanged=True)
        except Exception as error:
            report.update(status='failed', error=f'{type(error).__name__}: {error}')
        report['endedAtUtc'] = HELPER.utc()
        json.dump(report, output, indent=2)
        output.write('\n')
    print(json.dumps({'status': report['status']}))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
