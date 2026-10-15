#!/usr/bin/env python3
"""Offline equality check of two explicit already-verified native v8 exports.

No CLI/process/service/UI/live-store calls. Supplied verification receipt hashes
and pin must match; all 27 non-manifest files must be byte-identical. Only the
observed +1 generation, +1 revision, attemptBlocked→paused wrapper change is allowed.
"""
import argparse
import json
import os
from pathlib import Path
import re

import check_fixture_export as C

HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1]


def counter(value):
    if type(value) is int:
        C.require(value >= 0, 'Negative manifest counter')
        return value
    C.require(type(value) is str and re.fullmatch(r'0|[1-9][0-9]*', value), 'Invalid manifest counter')
    return int(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('original', 'recovered', 'original-receipt', 'recovered-receipt', 'cli', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('original-receipt', 'recovered-receipt', 'cli'):
        parser.add_argument('--expected-' + name + '-sha256', required=True)
    args = parser.parse_args()
    paths = [args.original.absolute(), args.recovered.absolute()]
    receipts = [args.original_receipt.absolute(), args.recovered_receipt.absolute()]
    cli, output = args.cli.absolute(), args.output.absolute()
    expected_receipts = [args.expected_original_receipt_sha256, args.expected_recovered_receipt_sha256]
    for digest in expected_receipts + [args.expected_cli_sha256]:
        C.require(re.fullmatch(r'[0-9a-f]{64}', digest), 'Exact expected SHA-256 required')
    qa = DESKTOP / 'target/qa/0.20-reading-measurements/exports'
    C.require(paths[0] != paths[1] and all(p.is_relative_to(qa) and p == p.resolve(strict=True) for p in paths),
              'Distinct explicit exports must be in the current owned 0.20 export directory')
    C.require(cli == DESKTOP / 'target/qa/0.20-pinned/reservoir-scope-desktop'
              and cli == cli.resolve(strict=True), 'Unexpected pinned verifier path')
    C.require(output.parent == HERE and all(p.parent == HERE for p in receipts),
              'Receipts and new output must stay in this validation directory')
    result = {'schema': 'reservoir-v8-native-recovery-comparison-v1', 'startedAtUtc': C.utc(),
              'status': 'running', 'script': C.identity(Path(__file__).resolve()),
              'checkerDependency': C.identity(HERE / 'check_fixture_export.py'),
              'scope': 'Already-verified immutable export files only; no new verifier, service, process, UI or managed-store action.',
              'servicesContacted': False, 'modelsContacted': False}
    inputs, receipt_ids = [], []
    with output.open('x') as stream:
        json.dump(result, stream, indent=2); stream.flush(); os.fsync(stream.fileno())
        try:
            binary = C.identity(cli)
            C.require(binary['sha256'] == args.expected_cli_sha256, 'Actual pinned executable differs')
            result['executable'] = binary
            records, manifests = [], []
            for index, (path, receipt_path) in enumerate(zip(paths, receipts)):
                receipt_id = C.identity(receipt_path)
                receipt_ids.append(receipt_id)
                C.require(receipt_id['sha256'] == expected_receipts[index], 'Handed-off receipt hash differs')
                record = C.decode(C.read(receipt_path))
                C.require(record['schema'] == 'reservoir-fixed-provider-export-review-v1'
                          and record['status'] == 'passed' and record['servicesContacted'] is False
                          and record['realModelsUsed'] is False and record['writingQualityAssessed'] is False,
                          'Expected passing model-free fixture verification receipt')
                C.require(record['executable'] == record['executableAfter'] == binary,
                          'Verification used a different or changed executable')
                C.require(record['script'] == result['checkerDependency'], 'Checker source differs from passing receipt')
                replay = record['productionReplay']
                C.require(replay['returncode'] == 0 and replay['command'] == [str(cli), '--verify-sustained', str(path)],
                          'Missing exact selected-bundle offline replay')
                replay_result = C.decode(replay['stdout'].encode())
                C.require(replay_result['status'] == 'passed' and replay_result['modelsContacted'] is False,
                          'Production replay did not report model-free pass')
                joins = record['staticJoins']
                before = C.inventory(path)
                inputs.append((path, before))
                C.require(joins['status'] == 'passed' and joins['originalUnchanged']
                          and joins['bundle'] == str(path) and C.exact(joins['inventory'], before),
                          'Export differs from its qualified inventory')
                C.require(replay_result['report']['manifestSha256'] == before['manifest.json']['sha256'],
                          'Replay did not bind the actual manifest')
                manifest = C.decode(C.read(path / 'manifest.json'))
                C.require(manifest['config']['promptVersion'] == C.PROMPT_VERSION
                          and manifest['step'] == manifest['durableStep'] == 50
                          and manifest['journalCount'] == 4 and manifest['segmentCount'] == 22,
                          'Expected v8 held50/four-journal/22-segment export')
                C.require(C.exact({key: manifest[key] for key in joins['manifest']}, joins['manifest']),
                          'Checked and actual manifests differ')
                checkpoint = C.decode(C.read(path / 'checkpoints' / (manifest['checkpointSha256'] + '.json')))
                C.check_protocol_events(joins['eventCounts'], checkpoint['state'])
                C.require(joins['finalCorePhase'] == 'blocked' and not joins['cleanupEvents']
                          and joins['fifthIncompleteHasNoJournalOrApplication'] is True
                          and joins['lastSavedFeedbackHeldThroughStep50'] is True,
                          'Held fifth/save gates differ')
                attempts = joins['attempts']
                C.require(len(attempts) == 5
                          and [a['attemptId'] for a in attempts] == [1, 2, 3, 4, 5]
                          and [a['saved'] for a in attempts] == [True, True, True, True, False]
                          and [a['complete'] for a in attempts] == [True, True, True, True, False]
                          and [a['firstAppliedStep'] for a in attempts] == [11, 21, 31, 41, None],
                          'Five fixed opportunities/four applications differ')
                records.append(record); manifests.append(manifest)
            a, b = [row for _, row in inputs]
            C.require(a.keys() == b.keys() and len(a) == 28, 'Expected same 28 exported files')
            changed = sorted(name for name in a if a[name] != b[name])
            C.require(changed == ['manifest.json'], 'A non-manifest file changed')
            identical = [name for name in sorted(a) if name != 'manifest.json'
                         and C.read(paths[0] / name) == C.read(paths[1] / name)]
            C.require(len(identical) == 27, 'Expected 27 byte-identical non-manifest files')
            old, new = manifests
            C.require(old.keys() == new.keys(), 'Manifest fields were added or removed')
            differences = {key: {'original': old[key], 'recovered': new[key]}
                           for key in sorted(old) if not C.exact(old[key], new[key])}
            C.require(set(differences) == {'generation', 'revision', 'phase'}, 'Unexpected manifest changes')
            for key in ('generation', 'revision'):
                C.require(type(old[key]) is type(new[key]) and counter(new[key]) == counter(old[key]) + 1,
                          'Expected exactly one increment with unchanged counter representation: ' + key)
            C.require(old['phase'] == 'attemptBlocked' and new['phase'] == 'paused', 'Unexpected wrapper phase change')
            for key in ('attempts', 'eventCounts', 'cleanupEvents', 'responseFiles', 'fixtureEndpoint', 'prospectiveFreeze'):
                C.require(C.exact(records[0]['staticJoins'][key], records[1]['staticJoins'][key]),
                          'Retained verification evidence differs: ' + key)
            result.update(status='passed', original=str(paths[0]), recovered=str(paths[1]),
                          verificationReceipts=receipt_ids, inventoryOriginal=a, inventoryRecovered=b,
                          filesEach=28, identicalNonManifestFiles=27, byteIdenticalFiles=identical,
                          changedFiles=changed, manifestDifferences=differences, otherManifestFieldsExact=True,
                          finalCorePhase='blocked', journalCount=4, receivedResponses=5, step=50,
                          fifthIncompleteHasNoJournalOrApplication=True,
                          limits=['Native quit/relaunch/Restore controls are parent UI observations; this verifies retained files only.',
                                  'Paused wrapper retains the blocked fifth response; no retry, skip or new application is implied.',
                                  'No crash/power-loss, real-model quality or full-context-processing qualification.'])
        except Exception as error:
            result.update(status='failed', error=f'{type(error).__name__}: {error}')
        finally:
            try:
                result['inputsUnchanged'] = len(inputs) == 2 and all(C.inventory(p) == inv for p, inv in inputs)
                result['receiptsUnchanged'] = len(receipt_ids) == 2 and [C.identity(p) for p in receipts] == receipt_ids
                result['helpersUnchanged'] = (C.identity(Path(__file__).resolve()) == result['script']
                                              and C.identity(HERE / 'check_fixture_export.py') == result['checkerDependency'])
                result['executableUnchanged'] = C.identity(cli) == result.get('executable')
                if not all(result[k] for k in ('inputsUnchanged', 'receiptsUnchanged', 'helpersUnchanged', 'executableUnchanged')):
                    result['status'] = 'failed'
            except Exception as error:
                result.update(status='failed', preservationError=f'{type(error).__name__}: {error}')
            result['endedAtUtc'] = C.utc()
            stream.seek(0); stream.truncate(); json.dump(result, stream, indent=2)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({'status': result['status'], 'output': str(output), 'error': result.get('error')}))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
