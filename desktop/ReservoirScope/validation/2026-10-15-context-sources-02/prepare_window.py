#!/usr/bin/env python3
"""Prepare one new window using unchanged candidate bytes and a new explicit runtime.
File operations only. Does not admit, execute a binary, or contact a provider.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'2026-10-15-context-sources-01'
SOFTWARE=HERE.parent/'2026-10-15-runtime-0.40.5/software-selection.json'

def identity(path):
    path=Path(path).resolve(strict=True); raw=path.read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def write(name,raw):
    with (HERE/name).open('xb') as stream:stream.write(raw)

def write_json(name,value):write(name,(json.dumps(value,indent=2)+'\n').encode())

def replacements(software):
    previous=json.loads((OLD/'run-plan.json').read_text())
    former=json.loads(Path(previous['softwareSelectionPath']).read_text())['installedSoftware']
    now=software['installedSoftware']
    return [('context-sources-01','context-sources-02'),('context-sources-gemma3-4b-run01','context-sources-gemma3-4b-run02'),('context-sources-results01','context-sources-results02'),
            (previous['softwareSelectionSha256'],identity(SOFTWARE)['sha256']),
            (former['executableSha256'],now['executableSha256']),(former['plistSha256'],now['plistSha256']),
            (str(former['executableSizeBytes']),str(now['executableSizeBytes'])),
            (str(former['plistSizeBytes']),str(now['plistSizeBytes'])),
            (former['CFBundleShortVersionString'],now['CFBundleShortVersionString'])]

def main():
    software=json.loads(SOFTWARE.read_text())
    assert software['installedSoftware']['CFBundleShortVersionString']=='0.40.5'
    previous=json.loads((OLD/'runtime-copy-01.json').read_text())
    old_paths=[p for p in OLD.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths=sorted(set(old_paths+[Path(r['path']) for r in previous['priorDirectoryAfter']]))
    before=[identity(p) for p in paths]
    exact=['owned_model.py','test_owned_model.py','render_blind_pack.py','test_render_blind_pack.py','test_prepare_inputs.py','audit_source_context.py']
    changed=['run_probe.py','test_run_probe.py','admit_once.py','prepare_inputs.py','freeze_inputs.py','retain_and_analyze.py']
    edits=replacements(software)
    for name in exact:write(name,(OLD/name).read_bytes())
    for name in changed:
        value=(OLD/name).read_text()
        for old,new in edits:value=value.replace(old,new)
        if name=='prepare_inputs.py':value=value.replace("candidateId='context-sources-02'","candidateId='context-sources-01'")
        if name=='retain_and_analyze.py':value=value.replace("len(prior)==385",f"len(prior)=={len(before)}")
        write(name,value.encode())
    write('READING-PROTOCOL.md',(OLD/'READING-PROTOCOL.md').read_bytes())
    write_json('cleanup-result-01.json',dict(status='no_cleanup_requested_or_performed',atUtc=dt.datetime.now(dt.timezone.utc).isoformat(),scope='New user-authorized window after housekeeping. No app closure, cache cleanup, Being or shared-service action. Prior refusal retained.'))
    plan=json.loads((OLD/'run-plan.json').read_text())
    plan['episodeId']='context-sources-02'
    plan['ownedServiceDirectory']=str(HERE.parents[1]/'target/qa/0.20-context-sources-gemma3-4b-run02')
    plan['softwareSelectionPath']=str(SOFTWARE)
    plan['softwareSelectionSha256']=identity(SOFTWARE)['sha256']
    p=plan['provenance']
    p['candidateId']='context-sources-01'  # The intervention itself is unchanged.
    p['authorization']='October 15 user approved housekeeping then the first natural tranche: separate runtime qualification and one distinctly identified comparison with frozen source-role prompts and unchanged bounds. No automatic retry.'
    p['resultsDirectory']=str(HERE.parents[1]/'target/qa/0.20-context-sources-results02')
    p['preAdmissionCleanupReceipt']=identity(HERE/'cleanup-result-01.json')
    p['priorAttempt']=identity(OLD/'outcome-01.json')
    p['priorFrozenInputs']=identity(OLD/'frozen-inputs.json')
    p['runtimeQualificationDirectory']=str(SOFTWARE.parent)
    p['runtimeInterpretation']='New explicit installed software selection; source/synthetic preflight is conditional. Actual owned startup/inventory/response behavior is assessed only within this window and its fixed bounds.'
    write_json('run-plan.json',plan)
    after=[identity(p) for p in paths];assert before==after
    write_json('runtime-copy-01.json',dict(schema='reservoir-context-sources-runtime-copy-v1',atUtc=dt.datetime.now(dt.timezone.utc).isoformat(),priorEpisodes=previous['priorEpisodes']+[str(OLD)],priorDirectoryBefore=before,priorDirectoryAfter=after,priorFilesUnchanged=True,sourceEpisodeFileCount=len(old_paths),inheritedPriorFileCount=len(previous['priorDirectoryAfter']),sources=[identity(OLD/n) for n in exact+changed],copies=[identity(HERE/n) for n in exact+changed],exactCopies=exact,changedScope='Episode/owned paths plus explicit runtime version/hash/size guards only. Transport, supervisor, model, prompts and bounds unchanged.',substitutions=edits,priorQualification=previous['priorQualification']+[identity(OLD/'runtime-checks-01.json'),identity(OLD/'preparation-checks-01.json')],priorInputs=identity(OLD/'frozen-inputs.json'),priorFreeze=identity(OLD/'evaluation-freeze-01.json'),softwareSelection=identity(SOFTWARE),noRuntimeCalls=True))
    print(json.dumps(dict(priorFiles=len(before),plan=identity(HERE/'run-plan.json'),software=identity(SOFTWARE))))

if __name__=='__main__':main()
