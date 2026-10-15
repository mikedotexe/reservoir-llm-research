#!/usr/bin/env python3
"""Freeze the newly authorized window; original refusal and all limits remain intact."""
from pathlib import Path
import datetime as dt
import hashlib,json

def identity(p):
    return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()}

def main():
    here=Path(__file__).resolve().parent;old=here.parent/'2026-10-14-v7-writing-episode01'
    assert not(here/'host-admission-01.json').exists()
    freeze=json.loads((old/'evaluation-freeze-01.json').read_text())
    paths=[]
    for item in freeze['files']:
        p=Path(item['path']);assert identity(p)['sha256']==item['sha256'],str(p);paths.append(p)
    oldclose=json.loads((old/'closeout-01.json').read_text())
    for item in oldclose['files']:
        p=Path(item['path']);assert identity(p)['sha256']==item['sha256'],str(p);paths.append(p)
    paths += [old/'closeout-01.json',old/'evaluation-freeze-01.json']
    paths += sorted(p for p in here.iterdir() if p.is_file())
    plan=json.loads((here/'run-plan.json').read_text());original=json.loads((old/'run-plan.json').read_text())
    changed=[k for k in original if plan[k]!=original[k]]
    assert set(changed)=={'revision','episodeId','authorizationScope','newSupervisionDirectory','priorEpisode'}
    files=[identity(p)for p in sorted(set(paths))]
    result={'schema':'reservoir-v7-episode-preparation-freeze-v1','frozenAtUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'prospective-before-admission','episodeId':plan['episodeId'],'priorRefusalUnchanged':True,'changedPlanFields':changed,'allLimitsUnchanged':True,'plannedSlots':12,'newSessionCreated':False,'newModelCalls':0,'files':files}
    with(here/'evaluation-freeze-01.json').open('x')as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'frozenFiles':len(files),'sameLimits':True,'priorRefusalUnchanged':True}))
if __name__=='__main__':main()
