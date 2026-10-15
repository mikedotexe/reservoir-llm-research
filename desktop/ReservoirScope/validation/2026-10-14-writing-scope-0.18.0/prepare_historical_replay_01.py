#!/usr/bin/env python3
"""Freeze eight selected old export inventories; never execute an application."""
from __future__ import annotations
import ast
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PRIMARY_REPO = Path('/Users/v/other/reservoir-llm-research')
SPEC = importlib.util.spec_from_file_location('historical_replay', HERE / 'replay_historical.py')
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


def main():
    receipt_path = HERE / 'historical-replay-preparation-01.json'
    selection_path = HERE / 'historical-replay-cases-01.json'
    prior_dir = HERE.parent / '2026-10-13-continuing-writing-0.17.0'
    old_selection = prior_dir / 'historical-replay-cases-01.json'
    prior = HELPER.decode(old_selection.read_bytes())
    cases = prior['cases']
    HELPER.require(len(cases) == 6, 'Previous fixed selection changed')
    for case in cases:
        basis = case['basisReceipt']
        copied = REPO / Path(basis['path']).relative_to(PRIMARY_REPO)
        actual = HELPER.identity(copied)
        HELPER.require(actual['sha256'] == basis['sha256'] and actual['bytes'] == basis['bytes'],
                       'Worktree copy of historical receipt differs')
        case['basisReceipt'] = actual
    v5_dir = HERE.parent / '2026-10-13-v5-writing-episode01'
    original_path = v5_dir / 'real-model-export-01/receipt.json'
    recovery_path = v5_dir / 'recovery-equality-01.json'
    original = HELPER.decode(original_path.read_bytes())
    recovery = HELPER.decode(recovery_path.read_bytes())
    HELPER.require(original['status'] == recovery['status'] == 'passed'
                   and original['originalUnchanged'] and recovery['originalUnchanged']
                   and recovery['recoveredUnchanged'], 'V5 qualification is not preserved/passing')
    HELPER.require(original['inventoryBefore'] == recovery['exportComparison']['originalInventory'],
                   'V5 original/recovery bases disagree')
    cases.extend([
        {'name': 'v5-twelve-entry-original', 'bundle': original['bundle'],
         'promptVersion': 'reservoir-journal-v5', 'step': 361, 'journalCount': 12,
         'basisReceipt': HELPER.identity(original_path), 'expectedInventory': original['inventoryBefore']},
        {'name': 'v5-twelve-entry-paused-recovery', 'bundle': recovery['exportComparison']['recovered'],
         'promptVersion': 'reservoir-journal-v5', 'step': 361, 'journalCount': 12,
         'basisReceipt': HELPER.identity(recovery_path),
         'expectedInventory': recovery['exportComparison']['recoveredInventory']},
    ])
    receipt = {'schema': 'reservoir-historical-replay-preparation-v1', 'startedAtUtc': HELPER.utc(),
               'status': 'running', 'applicationsOrModelsInvoked': False,
               'script': HELPER.identity(Path(__file__).resolve()),
               'replayHelper': HELPER.identity(HERE / 'replay_historical.py'),
               'priorSelection': HELPER.identity(old_selection), 'cases': []}
    # An exclusive receipt records any first failure; preparation cannot quietly
    # substitute regenerated files or drop a nonmatching case.
    with receipt_path.open('x', encoding='utf-8') as out:
        try:
            ast.parse((HERE / 'replay_historical.py').read_text())
            receipt['helperSyntaxParsed'] = True
            for case in cases:
                bundle = Path(case['bundle'])
                HELPER.require(bundle.is_relative_to(HELPER.PRIMARY_QA), 'Bundle is outside approved primary QA')
                before = HELPER.inventory(bundle)
                HELPER.require(before == case['expectedInventory'], f"Historical bytes changed: {case['name']}")
                manifest = HELPER.decode((bundle / 'manifest.json').read_bytes())
                HELPER.require(manifest['config'].get('promptVersion', 'reservoir-journal-v1') == case['promptVersion'],
                               'Historical version differs')
                HELPER.require(manifest['step'] == case['step'] and manifest['journalCount'] == case['journalCount'],
                               'Historical counts differ')
                receipt['cases'].append({'name': case['name'], 'bundle': str(bundle),
                                         'files': len(before), 'bytes': sum(v['bytes'] for v in before.values()),
                                         'inventoryBefore': before, 'basisReceipt': case['basisReceipt']})
            selected = {'schema': 'reservoir-historical-replay-selection-v2', 'selectedAtUtc': HELPER.utc(),
                        'scope': 'Eight exact retained positive exports from the approved primary QA tree. No regeneration, relabeling, restore or continuation. Awaiting pinned 0.18 production binary.',
                        'basisSelection': receipt['priorSelection'],
                        'v2HistoricalExportCoverage': 'No historical v2 export is selected. The prior 0.17 preparation reported no v2 bundle in its bounded manifest scan; this preparation does not repeat or broaden that scan. Generated v2 core/desktop tests are separate from historical export replay.',
                        'applicationsOrModelsInvoked': False, 'cases': cases}
            for case, row in zip(cases, receipt['cases']):
                after = HELPER.inventory(Path(case['bundle']))
                row['inventoryAfter'] = after
                row['originalUnchanged'] = after == row['inventoryBefore'] == case['expectedInventory']
                HELPER.require(row['originalUnchanged'], 'Historical bytes changed during preparation')
                HELPER.require(HELPER.identity(Path(case['basisReceipt']['path'])) == case['basisReceipt'],
                               'Historical basis receipt changed during preparation')
            HELPER.require(HELPER.identity(old_selection) == receipt['priorSelection'], 'Original selection changed')
            HELPER.require(HELPER.identity(HERE / 'replay_historical.py') == receipt['replayHelper'], 'Replay helper changed')
            with selection_path.open('x', encoding='utf-8') as target:
                json.dump(selected, target, indent=2)
                target.write('\n')
            receipt.update(status='passed', selection=HELPER.identity(selection_path),
                           allOriginalsUnchanged=True, productionReplayExecuted=False)
        except Exception as error:
            receipt.update(status='failed', error=f'{type(error).__name__}: {error}')
        receipt['endedAtUtc'] = HELPER.utc()
        json.dump(receipt, out, indent=2)
        out.write('\n')
    print(json.dumps({'status': receipt['status'], 'receipt': HELPER.identity(receipt_path)}))
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
