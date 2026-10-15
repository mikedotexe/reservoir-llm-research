#!/usr/bin/env python3
"""Compare the two explicitly handed-off immutable episode02 exports offline.

No model, service, process, UI or live-store access. Both exports must already
have passed the frozen checker. Never edits exports or earlier receipts.
"""
from pathlib import Path
import datetime as dt
import json

import check_real_model_export as check

BASE = Path(__file__).resolve().parent
EXPECTED_EXECUTABLE = 'fe14eeb2f921a541644a900d3397d973d81a6f70de66347f485cc0851fecafb0'


def main():
    output = BASE / 'recovery-comparison-01.json'
    if output.exists():
        raise FileExistsError(output)
    result = {'schema': 'reservoir-v6-episode-recovery-comparison-v1',
              'startedAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'status': 'failed', 'script': check.identity(Path(__file__).resolve()),
              'scope': 'Read-only exported files and existing verification receipts; no runtime, model, process, network or UI actions.'}
    paths = [BASE / 'real-model-export-01/receipt.json', BASE / 'recovered-export-01/receipt.json']
    receipts_before = [check.identity(path) for path in paths]
    inputs = []
    try:
        records = [check.read(path) for path in paths]
        for record in records:
            check.require(record['status'] == 'passed' and record['originalUnchanged'] is True,
                          'Both frozen checker runs must pass and preserve originals')
            check.require(record['pinnedExecutable']['sha256'] == EXPECTED_EXECUTABLE,
                          'Unexpected pinned verifier')
            replay = record['verification']
            check.require(replay['exitCode'] == 0 and replay['result']['status'] == 'passed'
                          and replay['result']['modelsContacted'] is False,
                          'Missing successful offline production replay')
            bundle = Path(record['bundle'])
            before = check.inventory(bundle)
            inputs.append((bundle, before))
            check.require(before == record['inventoryBefore'], 'Export differs from its verification inventory')
        original, recovered = [record['evidence']['manifest'] for record in records]
        a, b = [before for _, before in inputs]
        check.require(a.keys() == b.keys(), 'Export file names differ')
        changed = sorted(key for key in a if a[key] != b[key])
        check.require(changed == ['manifest.json'], 'A non-manifest retained file changed')
        differences = {key: {'original': original.get(key), 'recovered': recovered.get(key)}
                       for key in sorted(original.keys() | recovered.keys())
                       if not check.exact(original.get(key), recovered.get(key))}
        expected = {'generation': {'original': '1', 'recovered': '2'},
                    'revision': {'original': '281', 'recovered': '282'},
                    'phase': {'original': 'attemptBlocked', 'recovered': 'paused'}}
        check.require(check.exact(differences, expected), 'Unexpected manifest change')
        check.require(check.exact(records[0]['evidence']['continuity'], records[1]['evidence']['continuity']),
                      'Twelve-slot outcome changed during recovery')
        check.require(check.exact(records[0]['evidence']['finalCorePhase'], records[1]['evidence']['finalCorePhase'])
                      and records[1]['evidence']['finalCorePhase']['kind'] == 'blocked',
                      'Held core opportunity changed during recovery')
        result.update(original=str(inputs[0][0]), recovered=str(inputs[1][0]),
                      verificationReceipts=receipts_before,
                      inventoryOriginal=a, inventoryRecovered=b,
                      filesEach=len(a), identicalNonManifestFiles=len(a) - 1,
                      changedFiles=changed, manifestDifferences=differences,
                      otherManifestFieldsExact=True,
                      retainedCorePhase='blocked',
                      unchangedCheckpointSha256=original['checkpointSha256'],
                      continuity=records[1]['evidence']['continuity'],
                      step=recovered['step'], journalCount=recovered['journalCount'],
                      segmentCount=recovered['segmentCount'],
                      elapsedMillis=recovered['elapsedMillis'],
                      limits=['Native quit, idle relaunch, explicit Restore and disabled Resume are parent UI observations; this file verifies retained results only.',
                              'Paused wrapper does not complete, retry, save or apply the incomplete eighth response.',
                              'This is clean-quit recovery evidence, not crash or power-loss qualification, new generation, or writing-quality evidence.'])
        result['status'] = 'passed'
    except Exception as error:
        result['error'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        result['receiptsUnchanged'] = [check.identity(path) for path in paths] == receipts_before
        result['inputsUnchanged'] = all(check.inventory(path) == before for path, before in inputs)
        if not result['receiptsUnchanged'] or not result['inputsUnchanged']:
            result['status'] = 'failed'
        result['endedAtUtc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        check.write_new(output, result)
    print(json.dumps({'status': result['status'], 'receipt': str(output), 'error': result.get('error')}))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
