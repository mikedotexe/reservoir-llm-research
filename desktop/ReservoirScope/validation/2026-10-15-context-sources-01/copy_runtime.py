#!/usr/bin/env python3
"""Exclusive preparation copies only. No runtime/admission/host actions."""
import datetime as dt
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'2026-10-15-time-direction-03'
PARAGRAPH='The readout reports recorded observations; any quoted previous journal is remembered writing. You may imagine what follows, but an imagined continuation is not a new observation or an executed action.'

def identity(path):
    path=Path(path).resolve(strict=True);raw=path.read_bytes()
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def write(name,raw):
    with (HERE/name).open('xb') as stream:stream.write(raw)

def write_json(name,value):write(name,(json.dumps(value,indent=2)+'\n').encode())

def main():
    cleanup=identity(HERE/'cleanup-result-01.json')
    previous=json.loads((OLD/'runtime-copy-01.json').read_text())
    old_paths=[p for p in OLD.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths=sorted(set(old_paths+[Path(r['path']) for r in previous['priorDirectoryAfter']]))
    before=[identity(p) for p in paths]
    exact=['owned_model.py','test_owned_model.py']
    changed=['run_probe.py','test_run_probe.py','render_blind_pack.py','test_render_blind_pack.py','admit_once.py']
    for name in exact:write(name,(OLD/name).read_bytes())
    for name in changed:
        text=(OLD/name).read_text().replace('time-direction','context-sources')
        if name in ('run_probe.py','test_run_probe.py'):
            text=text.replace('context-sources-gemma3-4b-run03','context-sources-gemma3-4b-run01')
        if name=='admit_once.py':text=text.replace('"context-sources-03"','"context-sources-01"')
        write(name,text.encode())
    plan=json.loads((OLD/'run-plan.json').read_text())
    plan['schema']='reservoir-context-sources-plan-v1';plan['episodeId']='context-sources-01'
    desktop=HERE.parents[1]
    plan['ownedServiceDirectory']=str(desktop/'target/qa/0.20-context-sources-gemma3-4b-run01')
    old_provenance=plan['provenance']
    plan['provenance']=dict(scope='Standalone source-label diagnostic; no application session, numerical advance or feedback. Retained v8 context refers to its original session.',anchors=old_provenance['anchors'],selection=old_provenance['selection'],conditions={'A':'Exact original v8 prompt; control bytes reused from time-direction-03 A slots.','B':'Insert the approved source-distinction paragraph immediately before the final invitation; all original bytes otherwise unchanged. Diagnostic only, not a valid production-v8 record.'},candidateId='context-sources-01',candidateParagraph=PARAGRAPH,productionPromptChanged=False,maxFreshRequests=12,automaticRetries=0,manualRetries=0,replaceFailedSamples=False,hostAdmission=old_provenance['hostAdmission'],authorization='Fresh explicit user authorization for one source-label comparison under unchanged bounds; no automatic retry or threshold relaxation.',resultsDirectory=str(desktop/'target/qa/0.20-context-sources-results01'),priorDiagnostic=identity(OLD/'run-analysis-01.json'),priorInputs=identity(OLD/'frozen-inputs.json'),sourcePromptVersion='reservoir-journal-v8',sourceEpisode='v8-writing-episode01',otherApplicationsChangedDuringProbe=False,BeingsOrSharedServicesTouched=False,preAdmissionCleanupReceipt=cleanup)
    write_json('run-plan.json',plan)
    after=[identity(p) for p in paths];assert before==after
    write_json('runtime-copy-01.json',dict(schema='reservoir-context-sources-runtime-copy-v1',atUtc=dt.datetime.now(dt.timezone.utc).isoformat(),priorEpisodes=previous['priorEpisodes']+[str(OLD)],priorDirectoryBefore=before,priorDirectoryAfter=after,priorFilesUnchanged=True,sourceEpisodeFileCount=len(old_paths),inheritedPriorFileCount=len(previous['priorDirectoryAfter']),sources=[identity(OLD/n) for n in exact+changed],copies=[identity(HERE/n) for n in exact+changed],exactCopies=exact,changedScope='Namespace/schema/owned run basename only; order, bounds, transport, supervision and masking logic unchanged.',priorQualification=previous['priorQualification']+[identity(OLD/'runtime-checks-01.json')],priorInputs=identity(OLD/'frozen-inputs.json'),priorFreeze=identity(OLD/'evaluation-freeze-01.json'),noRuntimeCalls=True))
    print(json.dumps(dict(priorFiles=len(before),sourceEpisodeFiles=len(old_paths),plan=identity(HERE/'run-plan.json'))))

if __name__=='__main__':main()
