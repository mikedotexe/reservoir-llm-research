#!/usr/bin/env python3
"""Offline exact 0.12.2 native regression export/owned-fixture qualification."""
from pathlib import Path
import collections
import datetime as dt
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
V = Path(__file__).resolve().parent
BASE = V.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
now = lambda: dt.datetime.now(dt.timezone.utc).isoformat()


def main():
    started = now()
    clock = time.monotonic_ns()
    expected = '2fa824855d1172ebf707b4f1ce5f50d2c3eb74ab4aeeb437d41dc566f818db8d'
    executable = BASE / 'target/release/bundle/macos/Reservoir Scope Tauri Preview.app/Contents/MacOS/reservoir-scope-desktop'
    bundle = BASE / 'target/qa/0.12.1-reading/exports/sustained-1791919137300-1-2-18'
    checker_path = BASE / 'validation/2026-10-13-sustained-0.12.0/check_sustained_ui_exports.py'
    assert sha(checker_path) == '5df124ea9d9443ebb52c7baa921026f9cc31a6265ab9308611645964c0576689'
    spec = importlib.util.spec_from_file_location('accepted_journal_checks', checker_path)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    before = checker.inventory(bundle)
    scratch = BASE / 'target/qa/0.12.2-reading/native-regression-verification-01'
    scratch.mkdir(parents=True, exist_ok=False)
    assert sha(executable) == expected
    pinned = scratch / 'reservoir-scope-desktop-0.12.2-pinned'
    pinned.write_bytes(executable.read_bytes()); pinned.chmod(0o755)
    assert sha(pinned) == sha(executable) == expected
    request_log = BASE / 'target/qa/0.12-reliability/provider/requests.jsonl'
    raw = request_log.read_bytes(); assert raw.endswith(b'\n')
    snapshot = scratch / 'requests.snapshot.jsonl'; snapshot.write_bytes(raw)
    rows = [json.loads(line) for line in raw.splitlines()]
    cli_start, cli_clock = now(), time.monotonic_ns()
    command = ['/usr/bin/time', '-l', str(pinned), '--verify-sustained', str(bundle)]
    result = subprocess.run(command, text=True, capture_output=True, timeout=180)
    cli_end, cli_wall = now(), time.monotonic_ns() - cli_clock
    stdout = V / 'native-regression-cli-stdout.json'; stdout.write_text(result.stdout)
    stderr = V / 'native-regression-cli-stderr-time.txt'; stderr.write_text(result.stderr)
    verification = json.loads(result.stdout)
    assert result.returncode == 0 and verification['status'] == 'passed'
    evidence = checker.request_evidence(bundle, [r for r in rows if r.get('request') != 247 and r.get('response') != 247])
    segments = [read(p) for p in checker.links(bundle)]
    events = [e for s in segments for e in s['segment']['events']]
    by_kind = lambda kind: [e for e in events if e['kind']['type'] == kind]
    manifest = read(bundle / 'manifest.json')
    checkpoint = read(bundle / 'checkpoints' / (manifest['checkpointSha256'] + '.json'))
    journal = read(next((bundle / 'journals').glob('*.json')))
    post247 = next(r for r in rows if r.get('request') == 247 and r.get('method') == 'POST')
    post248 = next(r for r in rows if r.get('request') == 248 and r.get('method') == 'POST')
    response248 = next(r for r in rows if r.get('response') == 248)
    applications = [e['kind']['data']['application'] for e in by_kind('advanced') if e['kind']['data']['application']]
    quit_receipt = read(V / 'native-regression-checkpoint-quit.json')
    restore_receipt = read(V / 'native-regression-restored.json')
    old_checkpoint = read(bundle / 'checkpoints' / (quit_receipt['manifest']['checkpointSha256'] + '.json')) if (bundle / 'checkpoints' / (quit_receipt['manifest']['checkpointSha256'] + '.json')).exists() else None
    prepared = segments[quit_receipt['manifest']['segmentCount'] - 1]['segment']['finalCheckpoint']
    checks = {
        'wholeFrozen0122ReplayPassed': verification['status'] == 'passed',
        'failed247FixtureAndRetained503': post247['mode'] == 'fail' and len(by_kind('languageFailed')) == 1 and by_kind('languageFailed')[0]['kind']['data'] == {'attempt_id': 1, 'reason': 'The configured service returned HTTP 503. Redirects are not followed.'},
        'retry248UsesSameHeldPrompt': post247['body'] == post248['body'] and post247['bodySha256'] == post248['bodySha256'],
        'explicitRetryOfAttempt1': len(by_kind('retried')) == 1 and by_kind('retried')[0]['kind']['data']['previous_attempt_id'] == 1,
        'twoAttemptsStartedOnce': [e['kind']['data']['attempt_id'] for e in by_kind('languageStarted')] == [1, 2],
        'noJournalAcceptedResponseOrApplicationFor247': [e['kind']['data']['attempt_id'] for e in by_kind('languageReceived')] == [2] and journal['pending']['entry']['attemptId'] == 2 and all(a['attemptId'] != 1 for a in applications),
        'oneExactAccepted248Join': len(evidence['exactMatchedRequests']) == 1 and evidence['exactMatchedRequests'][0]['request'] == 248,
        'oneSaveAndOneNextStepApplication': len(by_kind('journalSaved')) == len(applications) == 1 and applications[0]['observedStep'] == 1 and applications[0]['appliedStep'] == 2 and applications[0]['attemptId'] == 2,
        'firstJournalHasNoInventedMemory': journal['pending']['memory'] is None and not by_kind('memoryConfirmed'),
        'onlyTwoNumericalSteps': [e['step'] for e in by_kind('advanced')] == [1, 2],
        'quitCheckpointPrefixExactSegmentHash': sha(checker.links(bundle)[4]) == quit_receipt['manifest']['lastSegmentSha256'],
        'savedPreparedBoundaryRetainedBeforeRestart': prepared['state']['step'] == 1 and prepared['state']['phase']['kind'] == 'prepared',
        'nativeCheckpointQuitReportedProcessAbsence': quit_receipt['exactAppProcesses'] == [] and quit_receipt['manifest']['step'] == 1 and quit_receipt['manifest']['journalCount'] == 1,
        'restoredGenerationAndConfigurationPreserved': manifest == restore_receipt['manifest'] and manifest['generation'] == '2' and manifest['config'] == quit_receipt['manifest']['config'],
        'noFurtherSyntheticRequestReportedThroughRestoreResume': restore_receipt['providerPosts'] == 248,
        'historical503PreservedAfterSuccess': manifest['diagnostics'] == quit_receipt['manifest']['diagnostics'] == ['The configured service returned HTTP 503. Redirects are not followed.'],
        'attemptAndStepBoundsUnreplenished': checkpoint['state']['attemptCursor'] == manifest['config']['maximumTurns'] == 2 and manifest['step'] == manifest['durableStep'] == manifest['config']['maximumSteps'] == 2 and manifest['phase'] == 'budgetReached',
        'originalExportUnchanged': checker.inventory(bundle) == before,
        'originalFixtureLogPrefixUnchanged': request_log.read_bytes().startswith(raw),
        'pinnedBinaryUnchanged': sha(pinned) == expected,
    }
    evidence_files = ['native-regression-plan.json', 'native-regression-release.json', 'native-regression-checkpoint-quit.json', 'native-regression-restored.json', 'package-before-ui.json', 'qualification.json', 'source-before-build-final.json']
    receipt = {'schema': 'reservoir-0122-native-regression-offline-v1', 'startedAtUtc': started, 'endedAtUtc': now(), 'wallNanoseconds': time.monotonic_ns() - clock,
               'modelsContactedByChecker': False, 'scope': 'Pinned offline replay and owned synthetic request-log associations. UI claims are attributed to linked parent observations. No live store, UI, service, model or process-control access.',
               'checker': checker.identity(Path(__file__)), 'reusedChecker': checker.identity(checker_path), 'pinnedVerifier': checker.identity(pinned),
               'export': {'path': str(bundle), 'manifest': manifest, 'inventory': before}, 'requestLogPrefixSnapshot': checker.identity(snapshot),
               'cli': {'command': command, 'startedAtUtc': cli_start, 'endedAtUtc': cli_end, 'wallNanoseconds': cli_wall, 'peakRssBytes': int(re.search(r'(\d+)\s+maximum resident set size', result.stderr).group(1)), 'peakRssScope': 'Verifier process only, not GUI/model.', 'exitCode': result.returncode, 'result': verification, 'stdout': checker.identity(stdout), 'stderrAndTime': checker.identity(stderr)},
               'nativeEvidence': {name: checker.identity(V / name) for name in evidence_files}, 'failedRequest247': post247, 'acceptedRequest248': post248, 'fixtureResponse248': response248,
               'acceptedJournalEvidence': evidence, 'acceptedHelperScope': 'Failed request247 excluded only from the historical cancellation-specific helper and checked independently as HTTP503. Original log unchanged. No normal response row for fail mode is expected.',
               'eventCounts': dict(collections.Counter(e['kind']['type'] for e in events)), 'checks': checks, 'status': 'passed' if all(checks.values()) else 'failed',
               'limits': ['Synthetic provider regression, not the separate real-model run.', 'Parent UI observation establishes alert presentation; offline replay establishes retained history and application.', 'No full text memory progression with only one successful journal.', 'No physical power-loss or resource endurance claim.']}
    output = V / 'native-regression-export-evidence.json'
    with output.open('x') as f: json.dump(receipt, f, indent=2); f.write('\n')
    print(json.dumps({'status': receipt['status'], 'checks': checks, 'cliWallSeconds': cli_wall / 1e9, 'verifierPeakRssBytes': receipt['cli']['peakRssBytes'], 'receipt': str(output)}, indent=2))
    return 0 if receipt['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
