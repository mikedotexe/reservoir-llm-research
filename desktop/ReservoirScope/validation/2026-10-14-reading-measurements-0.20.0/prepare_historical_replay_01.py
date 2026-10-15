#!/usr/bin/env python3
"""Prospective 0.20 preparation: bind fourteen old exports without executing a CLI.

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
    old = HERE.parent / '2026-10-14-action-boundaries-0.19.0'
    real = HERE.parent / '2026-10-14-v7-writing-episode03'
    basis_selection = old / 'historical-replay-cases-01.json'
    previous = HELPER.decode(basis_selection.read_bytes())
    cases = previous['cases']
    HELPER.require(len(cases) == 12, 'Previous twelve-case selection changed')
    for name, path in [
        ('v7-twelve-entry-original', real / 'real-model-export-01/receipt.json'),
        ('v7-twelve-entry-paused-recovery', real / 'recovered-export-01/receipt.json'),
    ]:
        receipt = HELPER.decode(path.read_bytes())
        HELPER.require(receipt['status'] == 'passed' and receipt['originalUnchanged'],
                       'Prior verification or preservation did not pass')
        manifest = receipt['evidence']['manifest']
        HELPER.require(manifest['step'] == 361 and manifest['journalCount'] == 12,
                       'Expected completed twelve-entry v7 export')
        cases.append({'name': name, 'bundle': receipt['bundle'],
                      'promptVersion': 'reservoir-journal-v7', 'step': 361,
                      'journalCount': 12, 'basisReceipt': HELPER.identity(path),
                      'expectedInventory': receipt['inventoryBefore']})

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
                         'scope': 'Fourteen fixed owned exports; new 0.20 production replay not yet executed.',
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
