#!/usr/bin/env python3
"""Freeze this one prospective episode. No admission, process, service or UI calls.

Root executes once after peer review. Only explicit package files and selected
metadata/receipts are read; no model blobs or credential contents are inspected.
An exclusive partial receipt is preserved if validation fails.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json
import stat

HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1]
QUALIFIED = HERE.parent / '2026-10-14-reading-measurements-0.20.0'
BINARY_SHA = 'cc5d3dce19076dbc1ff3b850cd99a72a410c8fa797d951cb11f4068ecaab1cfd'
ARCHIVE_SHA = '23fe012b90bca660773c63f58bd1bc916c26c9b74a0081b7e59d0603ec117e25'
SUPERVISOR_SHA = '415a585dfa4502e555331b4472cf08b6afbd3207944e6d02d952e133175f8c1b'
SUPERVISOR_TEST_SHA = 'da68770ceed2999ef55d9a17149b244dde639bf21f0a5aa43e06aab73d57bb5d'
SOFTWARE_SHA = 'f86c9011ed33881ffae71679a3c96755c3d7d1cfbd434b0b9535a3493192a127'
EXPECTED_CONFIG = {'seed':'20261013','promptVersion':'reservoir-journal-v8',
 'outputTokens':1024,'requestDeadlineSeconds':180,'turnEvery':30,
 'maximumSteps':361,'maximumTurns':12,'maximumDurationSeconds':900,
 'storageBudgetBytes':67108864,'paceMs':1000,'leak':0.65,'noiseAmplitude':0.02,
 'initialRetention':0.955,'regulationEnabled':True}
LOCAL = ('PROTOCOL.md','run-plan.json','EVALUATION.md','RUBRIC.md',
 'owned_model.py','test_owned_model.py','admit_once.py','freeze_episode.py',
 'check_real_model_export.py','test_real_model_export.py','checker-tests-01.json',
 'checker-tests-01.log','helper-copy-01.json','journal_quality.py','test_journal_quality.py',
 'quality-checks-01.json','quality-checks-01.log','form-prepared-01.json',
 'render_received_journals.py','compare_recovery_01.py','sample_manifest.py',
 'reader-tools-preparation-01.json','preparation-checks-01.json','PRE-RUN-REVIEW.md')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def identity(path):
    path = Path(path).absolute()
    for parent in path.parents:
        require(stat.S_ISDIR(parent.lstat().st_mode), f'Nonordinary ancestor: {parent}')
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), f'Not an ordinary file: {path}')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    after = path.lstat()
    require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)
            == (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),
            f'Changed while hashing: {path}')
    return {'path':str(path),'bytes':after.st_size,'sha256':digest}


def read(path):
    require(Path(path).stat().st_size < 8*1024*1024, 'JSON receipt too large')
    return json.loads(Path(path).read_text())


def expected_identity(row):
    require(identity(row['path']) == {k:row[k] for k in ('path','bytes','sha256')},
            f'Qualified input changed: {row["path"]}')
    return Path(row['path'])


def validate():
    require(not (HERE/'host-admission-01.json').exists(), 'Admission already attempted')
    plan = read(HERE/'run-plan.json')
    require(plan['episodeId']=='v8-writing-0.20.0-episode01'
            and plan['packageSha256']==BINARY_SHA and plan['packageVersion']=='0.20.0'
            and plan['promptVersion']=='reservoir-journal-v8'
            and plan['config']==EXPECTED_CONFIG, 'Episode/package/configuration differs')
    require(plan['contextTokens']==8192 and plan['maximumOutputTokens']==1024
            and plan['requestDeadlineSeconds']==180 and plan['temperature']==0
            and plan['serviceLifetimeSeconds']==1200
            and plan['minimumRemainingServiceSecondsAtStart']==1140
            and plan['minimumFreeDiskBytes']==8*1024**3
            and plan['hostAdmission']['minimumFreePercent']==35
            and plan['hostAdmission']['requiredPressureLevel']==1, 'Bound or admission changed')
    require(all(plan[k]==0 for k in ('automaticRetries','explicitRetries','skips','additionalComparisonRequests'))
            and plan['replaceMissingOrFailedSamples'] is False, 'Retry/extension scope changed')
    repo = DESKTOP.parents[1]
    supervision = repo/plan['newSupervisionDirectory']
    exports = repo/plan['exportParent']
    require(supervision==DESKTOP/'target/qa/0.20-v8-writing-gemma3-4b-run01'
            and exports==DESKTOP/'target/qa/0.20-v8-writing-episode01/exports', 'Unexpected owned paths')
    require(not supervision.exists(), 'Proposed supervision directory already exists')
    require(not exports.exists() or (exports.is_dir() and not exports.is_symlink() and not any(exports.iterdir())),
            'Proposed export parent contains outputs')
    paths = [HERE/name for name in LOCAL]
    for name,digest in [('owned_model.py',SUPERVISOR_SHA),('test_owned_model.py',SUPERVISOR_TEST_SHA)]:
        require(identity(HERE/name)['sha256']==digest, 'Supervisor must remain byte-exact')
    for name,count in [('checker-tests-01.json',40),('quality-checks-01.json',66)]:
        receipt = read(HERE/name)
        require(receipt['status']=='passed' and receipt['sourceUnchanged'] is True
                and receipt['testCount']==count, f'Qualification failed: {name}')
        for row in receipt['sourceAfter']:
            paths.append(expected_identity(row))
        paths.append(expected_identity(receipt['log']))
    copied = read(HERE/'helper-copy-01.json')
    for row in copied['copies']:
        paths.append(expected_identity(row['source']))
    for key in ('supervisorReusedQualification','softwareSelection','modelSelection'):
        paths.append(expected_identity(copied[key]))
    software_path = repo/plan['softwareSelection']
    require(identity(software_path)['sha256']==SOFTWARE_SHA==plan['softwareSelectionSha256'],
            'Software selection overlay changed')
    software = read(software_path)
    stage = Path(software['stageReceiptPath'])
    require(identity(stage)['sha256']==software['stageReceiptSha256'], 'Original private stage receipt changed')
    paths.extend([software_path,stage])
    basis = QUALIFIED/'archive-check-01.json'
    record = read(basis); package = record['package'];app=Path(record['app'])
    require(package['version']=='0.20.0' and package['build']=='0.20.0'
            and package['bundleIdentifier']=='research.reservoir.scope.tauri'
            and record['executableSha256']==BINARY_SHA and record['archiveSha256']==ARCHIVE_SHA,
            'Qualified package identity differs')
    expected = {x['path']:x for x in package['files']}
    actual = []
    for child in app.rglob('*'):
        require(not child.is_symlink(), 'Symlink in app package')
        if child.is_file():actual.append(str(child.relative_to(app)))
        else:require(child.is_dir(), 'Special package member')
    require(set(actual)==set(expected) and len(actual)==46, 'App file set differs')
    for relative,row in expected.items():
        child=app/relative;now=identity(child)
        require(now['sha256']==row['sha256'] and now['bytes']==row['bytes']
                and oct(stat.S_IMODE(child.stat().st_mode))==row['mode'], f'Package changed: {relative}')
        paths.append(child)
    pin=Path(record['pinnedExecutable']);archive=Path(record['archive'])
    require(identity(pin)['sha256']==BINARY_SHA and identity(archive)['sha256']==ARCHIVE_SHA,
            'Pin or archive changed')
    paths.extend([pin,archive,basis,QUALIFIED/'closeout-01.json',QUALIFIED/'prospective-freeze-01.json',
                  QUALIFIED/'package-build-01.json',QUALIFIED/'qualification-before-ui-01.json'])
    for name in ('v8-observation-10.txt','v8-memory-20.txt','v8-provenance.json'):
        paths.append(DESKTOP/'crates/reservoir-core/tests/fixtures/sustained-prompts'/name)
    prior=HERE.parent/'2026-10-14-v7-writing-episode03'
    for name in ('run-plan.json','PROTOCOL.md','evaluation-freeze-01.json','closeout-01.json',
                 'real-model-export-01/receipt.json','recovered-export-01/receipt.json'):
        paths.append(prior/name)
    form=read(HERE/'form-prepared-01.json')
    require(form['packageVersion']=='0.20.0' and form['model']=='gemma3:4b'
            and form['endpoint']=='' and form['created'] is False and form['started'] is False
            and form['readinessCheckExecuted'] is False, 'Prepared-form scope differs')
    observed=form['configObserved']
    for key,value in EXPECTED_CONFIG.items():
        if key not in ('promptVersion','regulationEnabled','storageBudgetBytes'):
            require(observed[key]==value, f'Prepared form differs: {key}')
    require(observed['contextTokens']==8192 and observed['storageBudgetMiB']==64
            and observed['regulation']=='Regulate separate sensory fill', 'Prepared advanced controls differ')
    before=[identity(path) for path in sorted(set(paths))]
    after=[identity(Path(row['path'])) for row in before]
    require(before==after, 'Preparation changed during freeze')
    return {'schema':'reservoir-v8-real-episode-freeze-v1',
            'frozenAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'status':'prospective-before-admission','episodeId':plan['episodeId'],
            'packageVersion':'0.20.0','packageFiles':46,'plannedSlots':12,
            'serviceLifetimeSeconds':1200,'minimumRemainingSecondsAtStart':1140,
            'newSessionCreated':False,'newModelCalls':0,'sourceUnchanged':True,
            'files':before,
            'scope':'File identity checks only. No resource admission, model blobs, installed runtime execution, endpoint, process or UI calls. Root owns all subsequent actions.'}


def main():
    destination=HERE/'evaluation-freeze-01.json'
    with destination.open('x') as stream:
        try:
            receipt=validate()
        except BaseException as exc:
            json.dump({'status':'failed','atUtc':dt.datetime.now(dt.timezone.utc).isoformat(),
                       'error':str(exc),'noAdmissionOrServiceAction':True},stream,indent=2)
            stream.write('\n')
            raise
        json.dump(receipt,stream,indent=2);stream.write('\n')
    print(json.dumps({'status':receipt['status'],'frozenFiles':len(receipt['files']),
                      'sha256':identity(destination)['sha256']}))

if __name__=='__main__':main()
