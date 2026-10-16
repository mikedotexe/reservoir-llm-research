#!/usr/bin/env python3
"""After owned normal quit, verify one retained 0.25 scripted QA session offline.

No UI/provider launch or signal. The only process inspection is the launch
receipt's exact PID. The pinned --verify-sustained mode never starts a session.
Plan shortfalls are retained as booleans and a verified_partial outcome, not
discarded by a hard-coded 36-journal assertion. All outputs are exclusive.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = ROOT / 'target/qa/0.25-journal-first-ui01'
PIN = ROOT / 'target/qa/0.25.0-pinned/reservoir-scope-desktop'
sys.path.insert(0, str(ROOT / 'scripts'))
from qualification_receipt import package_inventory


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def ordinary(path, directory=False):
    mode = path.lstat().st_mode
    if not (stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode)):
        raise ValueError(f'Expected an ordinary {"directory" if directory else "file"}: {path}')


def identity(path):
    ordinary(path)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def load_bound(path, expected):
    proof = identity(path)
    if not re.fullmatch('[a-f0-9]{64}', expected) or proof['sha256'] != expected:
        raise ValueError(f'Explicit receipt identity mismatch: {path.name}')
    return json.loads(path.read_bytes()), proof


def inventory(directory):
    ordinary(directory, True)
    rows = []
    total = 0
    for base, dirs, files in os.walk(directory, followlinks=False):
        base = Path(base)
        if len(base.relative_to(directory).parts) > 3:
            raise ValueError('Unexpected session directory depth')
        for name in dirs:
            ordinary(base / name, True)
        for name in files:
            p = base / name
            row = identity(p)
            total += row['bytes']
            if len(rows) >= 10000 or total > 512 * 1024 * 1024:
                raise ValueError('Session inventory exceeds the bounded offline scan')
            row['path'] = p.relative_to(directory).as_posix()
            rows.append(row)
    return sorted(rows, key=lambda row: row['path'])


def discover_session(store):
    """Allow only the regular owner lock and one ordinary session directory."""
    ordinary(store, True)
    entries = sorted(store.iterdir())
    owner = store / 'owner'
    owner_proof = identity(owner)
    sessions = []
    for entry in entries:
        if entry.name == 'owner':
            continue
        if not re.fullmatch(r'sustained-[0-9]+-[0-9]+', entry.name):
            raise ValueError(f'Unexpected entry in exclusive QA store: {entry.name}')
        ordinary(entry, True)
        sessions.append(entry)
    if len(sessions) != 1:
        raise ValueError('Expected exactly one session in the exclusive QA Library')
    return sessions[0], owner_proof, [entry.name for entry in entries]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-launch-sha256', required=True)
    parser.add_argument('--expected-plan-sha256', required=True)
    parser.add_argument('--expected-archive-check-sha256', required=True)
    parser.add_argument('--close-receipt', type=Path, help='Optional retained UI quit witness; bound as evidence, not inferred from PID absence')
    parser.add_argument('--attempt', default='01')
    args = parser.parse_args()
    if not re.fullmatch('[0-9]{2}', args.attempt):
        raise ValueError('Use a two-digit exclusive attempt ID')
    output = HERE / f'ui-session-check-{args.attempt}.json'
    stdout = HERE / f'ui-session-verify-{args.attempt}.log'
    stderr = HERE / f'ui-session-verify-{args.attempt}.stderr.log'
    if any(p.exists() for p in (output, stdout, stderr)):
        raise FileExistsError('Attempt output already exists; select a fresh attempt')
    report = {'schema': 'reservoir-journal-first-ui-session-check-v1',
              'startedAtUtc': utc(), 'helper': identity(Path(__file__)),
              'verificationPassed': False, 'plannedOutcomeComplete': False,
              'status': 'failed', 'errors': [],
              'scope': 'Offline same-build replay and file preservation after exact owned PID absence. Native interactions and normal-quit causation require the separate UI witness. No model, provider, export, restore, GPU or endurance qualification.'}
    session = None
    before = None
    pin_before = None
    owner_before = None
    bound = []
    with output.open('x') as receipt:
        try:
            launch, launch_id = load_bound(HERE / 'ui-launch-01.json', args.expected_launch_sha256)
            plan, plan_id = load_bound(HERE / 'ui-plan-01.json', args.expected_plan_sha256)
            archive, archive_id = load_bound(HERE / 'archive-check-01.json', args.expected_archive_check_sha256)
            bound = [launch_id, plan_id, archive_id]
            report['inputs'] = bound
            if args.close_receipt:
                close = args.close_receipt.resolve()
                if close.parent != HERE:
                    raise ValueError('Quit witness must belong to this validation directory')
                report['closeWitness'] = identity(close)
                bound.append(report['closeWitness'])
            if plan['version'] != '0.25.0' or archive['package']['version'] != '0.25.0' or archive['package']['build'] != '0.25.0':
                raise ValueError('Expected the qualified 0.25.0 plan and package')
            if launch['archiveCheckSha256'] != archive_id['sha256']:
                raise ValueError('Launch did not bind this archive receipt')
            if Path(launch['runDirectory']) != RUN or Path(launch['library']) != RUN / 'library':
                raise ValueError('Launch is outside the exclusive 0.25 QA directory')
            for p in (RUN, RUN / 'library'):
                ordinary(p, True)
                if p.resolve() != p:
                    raise ValueError('QA directory path contains a symlink')
            if Path(archive['pinnedExecutable']) != PIN:
                raise ValueError('Unexpected pinned executable path')
            app = Path(archive['app'])
            exe = app / 'Contents/MacOS/reservoir-scope-desktop'
            pin_before = identity(PIN)
            report['pinnedExecutable'] = pin_before
            if Path(launch['executable']) != exe or not (pin_before['sha256'] == sha(exe) == launch['executableSha256'] == archive['executableSha256']):
                raise ValueError('Launch/package/pinned executable identities differ')
            if package_inventory(app) != archive['package'] or sha(Path(archive['archive'])) != archive['archiveSha256']:
                raise ValueError('Qualified package or archive changed')
            report['qualifiedPackageMatched'] = True
            pid = launch['pid']
            if type(pid) is not int or pid <= 0:
                raise ValueError('Invalid owned launch PID')
            command = ['/bin/ps', '-p', str(pid), '-o', 'pid=,comm=']
            checked = subprocess.run(command, capture_output=True, text=True, timeout=10)
            report['ownedProcessCheck'] = {'checkedAtUtc': utc(), 'command': command,
                                          'exitCode': checked.returncode, 'stdout': checked.stdout, 'stderr': checked.stderr,
                                          'absent': checked.returncode == 1 and not checked.stdout.strip() and not checked.stderr.strip()}
            if not report['ownedProcessCheck']['absent']:
                raise ValueError('Owned launch PID is not proven absent; no replay dispatched')
            store = RUN / 'library/sustained-v1'
            session, owner_before, store_entries = discover_session(store)
            report['storeEntriesBefore'] = store_entries
            report['storeOwnerBefore'] = owner_before
            report['sessionDirectoryNames'] = [session.name]
            before = inventory(session)
            report.update(sessionDirectory=str(session), filesBefore=before,
                          fileCount=len(before), logicalBytes=sum(row['bytes'] for row in before))
            manifest = json.loads((session / 'manifest.json').read_bytes())
            report['manifest'] = manifest
            if manifest['sessionId'] != session.name:
                raise ValueError('Manifest/session directory identity mismatch')
            journals = []
            for row in before:
                if not row['path'].startswith('journals/'):
                    continue
                value = json.loads((session / row['path']).read_bytes())
                pending = value['pending']; entry = pending['entry']
                journals.append({'path': row['path'], 'objectSha256': row['sha256'],
                                 'entryId': entry['id'], 'turnId': entry['turnId'], 'attemptId': entry['attemptId'],
                                 'observedStep': entry['observedStep'], 'textSha256': entry['sha256'],
                                 'textBytes': len(entry['text'].encode()), 'promptSha256': hashlib.sha256(pending['prompt'].encode()).hexdigest(),
                                 'requestStarted': value['requestStarted'], 'configuredModel': value['configuredModel'],
                                 'responseComplete': pending['response']['complete']})
            report['journals'] = sorted(journals, key=lambda row: row['attemptId'])
            wanted = plan['session']; config = manifest['config']
            config_checks = {key: config.get(key) == wanted[key] for key in
                             ('promptVersion', 'seed', 'turnEvery', 'maximumSteps', 'maximumTurns',
                              'maximumDurationSeconds', 'storageBudgetBytes', 'paceMs')}
            config_checks['backend'] = config.get('language', {}).get('backend') == wanted['backend'] == 'scripted'
            expected_count = min(wanted['maximumTurns'], wanted['maximumSteps'] // wanted['turnEvery'])
            report['plannedChecks'] = {'specifiedConfiguration': config_checks,
                                       'naturalStepBound': manifest['step'] == wanted['maximumSteps'],
                                       'durableStepAtBound': manifest['durableStep'] == wanted['maximumSteps'],
                                       'budgetReached': manifest['phase'] == 'budgetReached',
                                       'expectedJournalCount': expected_count,
                                       'journalCountAtExpectedBound': manifest['journalCount'] == expected_count,
                                       'atLeastThreeJournals': manifest['journalCount'] >= 3,
                                       'journalFilesMatchCommittedCount': len(journals) == manifest['journalCount'],
                                       'noRecordedProviderDispatch': all(row['requestStarted'] is False for row in journals),
                                       'noConfiguredProviderModel': all(row['configuredModel'] is None for row in journals)}
            report['planLimits'] = 'Only explicitly specified configuration is compared. Unchanged UI defaults and actual navigation/zoom/resize claims require their separate source/UI witnesses.'
            command = [str(PIN), '--verify-sustained', str(session)]
            verification = {'command': command, 'startedAtUtc': utc(), 'executableSha256': pin_before['sha256']}
            report['verification'] = verification
            started = time.monotonic()
            try:
                with stdout.open('x') as out, stderr.open('x') as err:
                    result = subprocess.run(command, cwd=ROOT, stdout=out, stderr=err, timeout=180)
                verification['exitCode'] = result.returncode
            finally:
                verification.update(endedAtUtc=utc(), elapsedSeconds=time.monotonic() - started)
                verification['outputFiles'] = [identity(p) for p in (stdout, stderr) if p.exists()]
            payload = json.loads(stdout.read_bytes())
            verification['result'] = payload
            if result.returncode != 0 or payload.get('status') != 'passed' or payload.get('modelsContacted') is not False:
                raise ValueError('Same-build offline verification did not pass')
            verified = payload['report']
            for key in ('sessionId', 'step', 'journalCount', 'segmentCount'):
                if verified[key] != manifest[key]:
                    raise ValueError(f'Verifier/manifest mismatch: {key}')
            if verified['manifestSha256'] != sha(session / 'manifest.json'):
                raise ValueError('Verifier manifest hash differs')
            report['verificationPassed'] = True
        except Exception as error:
            report['errors'].append(f'{type(error).__name__}: {error}')
        finally:
            try:
                if session is not None and before is not None:
                    after = inventory(session)
                    report.update(filesAfter=after, allFilesUnchangedByVerification=after == before)
                    if after != before:
                        raise ValueError('Retained session files changed during verification')
                if pin_before and identity(PIN) != pin_before:
                    raise ValueError('Pinned executable changed during verification')
                if owner_before:
                    selected, owner_after, store_entries = discover_session(session.parent)
                    report['storeOwnerAfter'] = owner_after
                    report['storeEntriesAfter'] = store_entries
                    report['storeOwnerAndEnumerationUnchanged'] = (owner_after == owner_before and selected == session and store_entries == report['storeEntriesBefore'])
                    if not report['storeOwnerAndEnumerationUnchanged']:
                        raise ValueError('Store owner or session enumeration changed during verification')
                for proof in bound:
                    if identity(Path(proof['path'])) != proof:
                        raise ValueError('A bound input/witness changed during verification')
            except Exception as error:
                report['errors'].append(f'Preservation: {type(error).__name__}: {error}')
            checks = report.get('plannedChecks', {})
            report['plannedOutcomeComplete'] = bool(checks) and all(checks.get('specifiedConfiguration', {}).values()) and all(
                value for key, value in checks.items() if key not in ('specifiedConfiguration', 'expectedJournalCount'))
            if not report['errors'] and report['verificationPassed']:
                report['status'] = 'verified_complete' if report['plannedOutcomeComplete'] else 'verified_partial'
            report['endedAtUtc'] = utc()
            json.dump(report, receipt, indent=2); receipt.write('\n')
    print(json.dumps({'receipt': str(output), 'sha256': sha(output), 'status': report['status'],
                      'verificationPassed': report['verificationPassed'], 'plannedOutcomeComplete': report['plannedOutcomeComplete'],
                      'fileCount': report.get('fileCount'), 'errors': report['errors']}))
    return 0 if report['status'].startswith('verified_') else 1


if __name__ == '__main__':
    raise SystemExit(main())
