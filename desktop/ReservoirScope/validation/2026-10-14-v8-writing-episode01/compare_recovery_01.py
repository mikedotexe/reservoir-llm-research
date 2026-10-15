#!/usr/bin/env python3
"""Compare two explicit immutable exports already accepted by the v8 checker.

No verifier, app, model, service, process or live-store action. A valid partial
prefix remains partial. The caller supplies both exports, receipt hashes and the
qualified verifier identity after handoff; this helper discovers nothing.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import json

import check_real_model_export as check

BASE = Path(__file__).resolve().parent


def verified_receipt(path, expected_sha, bundle, expected_cli, session_id):
    identity = check.identity(path)
    check.require(identity['sha256'] == expected_sha, 'Explicit verification receipt hash differs')
    record = check.read(path)
    check.require(record['schema'] == 'reservoir-real-model-export-check-v8'
                  and record['status'] == 'passed' and record['originalUnchanged'] is True
                  and record['modelsContactedByChecker'] is False
                  and record['expectedPromptVersion'] == 'reservoir-journal-v8',
                  'Need passing v8 receipt preserving original files')
    check.require(record['pinnedExecutable']['sha256'] == expected_cli
                  and record['sourceExecutable']['sha256'] == expected_cli,
                  'Unexpected qualified verifier identity')
    replay = record['verification']
    check.require(replay['exitCode'] == 0 and replay['result']['status'] == 'passed'
                  and replay['result']['modelsContacted'] is False,
                  'Missing successful offline production replay')
    check.require(Path(record['bundle']) == bundle, 'Receipt export path differs from explicit handoff')
    inventory = check.inventory(bundle)
    check.require(check.exact(inventory, record['inventoryBefore']), 'Export differs from verified inventory')
    manifest = check.read(bundle / 'manifest.json')
    check.require(check.exact(manifest, record['evidence']['manifest'])
                  and manifest['sessionId'] == session_id
                  and manifest['config']['promptVersion'] == 'reservoir-journal-v8',
                  'Actual manifest/session/version differs from checked evidence')
    check.require(check.exact(check.continuity_summary(record['evidence']), record['evidence']['continuity'])
                  and record['evidence']['continuity']['plannedOpportunities'] == 12,
                  'Retained twelve-slot accounting differs')
    return record, identity, inventory


def compare(original_bundle, recovered_bundle, original, recovered, first, second):
    check.require(first.keys() == second.keys(), 'Export file sets differ')
    changed = sorted(name for name in first if first[name] != second[name])
    check.require(changed == ['manifest.json'], 'Expected only the Restore wrapper manifest to change')
    identical = []
    for name in sorted(first):
        if name == 'manifest.json':
            continue
        check.require(check.data(original_bundle / name) == check.data(recovered_bundle / name),
                      'Non-manifest file bytes differ: ' + name)
        identical.append(name)
    a, b = original['evidence']['manifest'], recovered['evidence']['manifest']
    check.require(a.keys() == b.keys(), 'Manifest field sets differ')
    for field in ('generation', 'revision'):
        check.require(type(a[field]) is str and re.fullmatch(r'[1-9][0-9]*', a[field])
                      and type(b[field]) is str and re.fullmatch(r'[1-9][0-9]*', b[field])
                      and int(a[field]) < (1 << 64) - 1 and int(b[field]) == int(a[field]) + 1,
                      'Expected exactly one Restore increment: ' + field)
    check.require(b['phase'] == 'paused', 'Restored wrapper must be paused')
    differences = {key: {'original': a[key], 'recovered': b[key]} for key in sorted(a)
                   if not check.exact(a[key], b[key])}
    check.require(set(differences) <= {'generation', 'revision', 'phase'},
                  'Unexpected manifest change outside Restore wrapper fields')
    check.require(check.exact({k: v for k, v in original['evidence'].items() if k != 'manifest'},
                              {k: v for k, v in recovered['evidence'].items() if k != 'manifest'}),
                  'Retained response, memory, numerical phase or twelve-slot evidence differs')
    return {'filesEach': len(first), 'identicalNonManifestFiles': len(identical),
            'byteIdenticalFiles': identical, 'changedFiles': changed,
            'manifestDifferences': differences, 'otherManifestFieldsExact': True,
            'retainedCorePhase': recovered['evidence']['finalCorePhase'],
            'continuity': recovered['evidence']['continuity'],
            'unchangedCheckpointSha256': a['checkpointSha256'],
            'step': b['step'], 'durableStep': b['durableStep'], 'journalCount': b['journalCount'],
            'segmentCount': b['segmentCount'], 'elapsedMillis': b['elapsedMillis']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for label in ('original-export', 'recovered-export', 'original-receipt', 'recovered-receipt', 'output'):
        parser.add_argument('--' + label, type=Path, required=True)
    for label in ('original-receipt-sha256', 'recovered-receipt-sha256', 'expected-cli-sha256', 'session-id'):
        parser.add_argument('--' + label, required=True)
    args = parser.parse_args()
    for value in (args.original_receipt_sha256, args.recovered_receipt_sha256, args.expected_cli_sha256):
        check.require(re.fullmatch(r'[a-f0-9]{64}', value), 'Explicit SHA-256 identities required')
    check.require(re.fullmatch(r'sustained-[0-9]+-[0-9]+', args.session_id), 'Explicit owned session identity required')
    bundles = [args.original_export, args.recovered_export]
    paths = [args.original_receipt, args.recovered_receipt]
    for path in bundles + paths + [args.output]:
        check.require(path.is_absolute() and '..' not in path.parts, 'Explicit absolute path without traversal required')
    for bundle in bundles:
        check.ordinary_path(bundle, directory=True)
    check.require(bundles[0] != bundles[1] and paths[0] != paths[1], 'Distinct original and recovered inputs required')
    check.require(not args.output.exists() and not args.output.is_symlink()
                  and args.output not in paths
                  and not any(args.output.is_relative_to(bundle) for bundle in bundles),
                  'New receipt must be outside inspected inputs')
    check.ordinary_path(args.output.parent, directory=True)
    report = {'schema': 'reservoir-v8-recovery-comparison-v1', 'status': 'failed', 'startedAtUtc': check.utc(),
              'script': check.identity(Path(__file__).resolve()),
              'checkerDependency': check.identity(BASE / 'check_real_model_export.py'),
              'modelsContacted': False,
              'scope': 'Read-only explicit exported files and passing verification receipts. No new replay, runtime, process, model, network, UI or live-store action.'}
    receipt_identities = [check.identity(path) for path in paths]
    inventories = []
    try:
        records = []
        for path, digest, bundle in zip(paths, [args.original_receipt_sha256, args.recovered_receipt_sha256], bundles):
            record, identity, inventory = verified_receipt(path, digest, bundle, args.expected_cli_sha256, args.session_id)
            records.append(record); inventories.append(inventory)
        result = compare(*bundles, *records, *inventories)
        report.update(result, original=str(bundles[0]), recovered=str(bundles[1]),
                      verificationReceipts=receipt_identities, expectedExecutableSha256=args.expected_cli_sha256,
                      inventoryOriginal=inventories[0], inventoryRecovered=inventories[1],
                      limits=['Native controls are separately observed; this checks retained files only.',
                              'A partial or blocked result remains partial or blocked. A paused wrapper creates no new response/application or renewed budget.',
                              'No crash, power-loss, provider-authentication, context-processing or prose-quality claim.'],
                      status='passed')
    except Exception as error:
        report['error'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        report['receiptsUnchanged'] = [check.identity(path) for path in paths] == receipt_identities
        report['inputsUnchanged'] = all(check.inventory(bundle) == before for bundle, before in zip(bundles, inventories))
        report['helpersUnchanged'] = (check.identity(Path(__file__).resolve()) == report['script']
                                      and check.identity(BASE / 'check_real_model_export.py') == report['checkerDependency'])
        if not all(report[key] for key in ('receiptsUnchanged', 'inputsUnchanged', 'helpersUnchanged')):
            report['status'] = 'failed'
        report['endedAtUtc'] = check.utc()
        check.write_new(args.output, report)
    print(json.dumps({'status': report['status'], 'receipt': str(args.output), 'error': report.get('error')}))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
