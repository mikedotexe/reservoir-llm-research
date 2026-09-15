#!/usr/bin/env python3
"""S-007 bounded read-only capture over SSH; offline report. No live imports/writes.

Only the capture subcommand writes, exclusively beneath research/outputs. The
remote collector reads allowlisted evidence and prints a hashed packet to stdout.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from zoneinfo import ZoneInfo

SCHEMA='source_study_fidelity_v1'
PDT=ZoneInfo('America/Los_Angeles')
FIX='37ed8b7f153043521cc89fe881ed55fd56b5700f'
ASTRID_FIX='542c006040381ef7673cc0c5f5154da5edd6ca90'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def epoch(s): return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def iso(t): return datetime.fromtimestamp(t,timezone.utc).isoformat()
def collect(since,until):
    lo,hi=epoch(since),epoch(until)
    root=Path('/Users/v/other'); w=root/'minime/workspace'
    records=[]; errors=[]; inventories=[]
    def add(p,kind,stamp=None):
        try:
            if p.is_symlink(): raise ValueError('symlink')
            before=p.stat()
            if before.st_size>8*1024*1024: raise ValueError('size ceiling')
            raw=p.read_bytes(); after=p.stat()
            if (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns): raise ValueError('unstable read')
            records.append(dict(path=str(p),kind=kind,sha256=sha(raw),bytes=len(raw),mtime_ns=after.st_mtime_ns,filename_time=stamp,text=raw.decode()))
        except (OSError,ValueError,UnicodeError) as e: errors.append(dict(path=str(p),error=str(e)))
    def entries(folder,ceiling=50000):
        items=list(os.scandir(folder))
        if len(items)>ceiling: raise ValueError('enumeration ceiling '+str(folder))
        inventories.append(dict(directory=str(folder),enumerated=len(items),recursive=False))
        return items
    for e in entries(w/'journal'):
        m=re.fullmatch(r'!*self_study_(\d{4}-\d\d-\d\d)T(\d\d)-(\d\d)-(\d\d)(\.\d+)?\.txt',e.name)
        if m:
            t=datetime.fromisoformat(f'{m[1]}T{m[2]}:{m[3]}:{m[4]}{m[5] or ""}').replace(tzinfo=PDT).timestamp()
            if lo<=t<hi: add(Path(e.path),'journal',t)
    day=datetime.fromtimestamp(lo,timezone.utc).date()
    while day<=datetime.fromtimestamp(hi,timezone.utc).date():
        folder=w/'generations'/str(day)
        if folder.exists():
            for e in entries(folder):
                m=re.fullmatch(r'gen_(\d+)_self_study_a\d+\.json',e.name)
                if m and lo<=int(m[1])/1000<hi: add(Path(e.path),'generation',int(m[1])/1000)
        else: errors.append(dict(path=str(folder),error='missing day directory'))
        day+=timedelta(days=1)
    for e in entries(w/'llm_jobs/jobs'):
        m=re.match(r'job_minime_(\d+)_self-study(?:-|$)',e.name)
        if m and lo<=int(m[1])/1000<hi:
            for name in ('job.json','events.jsonl','prompt.txt','result.txt'):
                if (Path(e.path)/name).exists(): add(Path(e.path)/name,'job_'+name,int(m[1])/1000)
    # Reader receipts are a separate captured inventory: filter by recorded time offline.
    reader=w/'diagnostics/source_first_v3/shared_reader'
    if reader.exists():
        add(reader/'reader-v1.json','reader_state')
        delivery_files=list((reader/'deliveries').glob('*/*.json'))
        if len(delivery_files)>10000: raise ValueError('delivery enumeration ceiling')
        inventories.append(dict(directory=str(reader/'deliveries'),enumerated=len(delivery_files),recursive='two levels'))
        for p in delivery_files: add(p,'delivery')
    gens=[json.loads(r['text']) for r in records if r['kind']=='generation']
    system_hashes={m['content_sha256'] for g in gens for m in g.get('messages',[]) if m.get('role')=='system' and re.fullmatch('[a-f0-9]{64}',m.get('content_sha256',''))}
    for h in sorted(system_hashes): add(w/'generations/system_prompts'/f'{h}.txt','system_prompt')
    for rel in (
      'astrid/docs/steward-notes/source-study-v1-validation/live-rollout.json',
      'astrid/docs/steward-notes/2026-09-08-self-study-parity-live-rollout.md',
      'astrid/.runtime/minime-reloads/2026-09-08-self-study-parity-retry.jsonl',
      'astrid/.runtime/bridge-deployment/transactions/902a5eb47bae453eba674052f9401e66/receipt.json',
      'worktrees/self-study-parity-live-20260908/bridge-stage-01/manifest.json',
      'worktrees/provider-observation-live-20260908/bridge-stage-01/manifest.json',
      'astrid/.runtime/bridge-deployment/active.json'):
        add(root/rel,'release')
    for repo,rev,path in [('minime',FIX,'minime_autonomy/source_study.py'),('minime',FIX,'minime_autonomy/runtime.py'),('minime',FIX+'^','minime_autonomy/runtime.py'),('astrid',ASTRID_FIX,'docs/architecture/source-study-v1.md'),('astrid',ASTRID_FIX,'crates/astrid-source-study/src/store.rs'),('astrid',ASTRID_FIX,'crates/astrid-source-study/src/page.rs'),('astrid',ASTRID_FIX,'crates/astrid-source-study/prompt.txt')]:
        raw=subprocess.check_output(['git','-C',str(root/repo),'show',f'{rev}:{path}'])
        records.append(dict(kind='source',path=f'git:{repo}@{rev}:{path}',sha256=sha(raw),bytes=len(raw),text=raw.decode()))
    for repo,rev in [('minime',FIX),('astrid',ASTRID_FIX)]:
        raw=subprocess.check_output(['git','-C',str(root/repo),'show','-s','--format=fuller',rev])
        records.append(dict(kind='commit',path=f'git:{repo}@{rev}',sha256=sha(raw),bytes=len(raw),text=raw.decode()))
    return dict(schema=SCHEMA,captured_at=datetime.now(timezone.utc).isoformat(),selection=dict(since=since,until_exclusive=until,journal_scope='root only; no archives',generation_scope='filename lane self_study; UTC daily folders',job_scope='filename self-study prefix, queued within window',reader_scope='all retained deliveries captured; report joins exact request and response to time-selected generations; reader state is capture-time only',close_reading='last three pre / first three post status-ok nonempty responses, chronological'),inventories=inventories,errors=errors,records=records)

def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='cmd',required=True)
    for name in ('collect','capture'):
        q=sub.add_parser(name); q.add_argument('--since',required=True); q.add_argument('--until',required=True)
        if name=='capture': q.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.cmd=='collect': print(json.dumps(collect(a.since,a.until),ensure_ascii=False)); return
    repo=Path(__file__).resolve().parents[1]; out=a.out.resolve()
    if not out.is_relative_to(repo/'research/outputs'): raise ValueError('research output required')
    out.mkdir(mode=0o700)
    source=Path(__file__).read_text()
    cp=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','volya','/opt/homebrew/bin/python3','-','collect','--since',a.since,'--until',a.until],input=source,text=True,capture_output=True,timeout=180,check=True)
    b=json.loads(cp.stdout)
    for r in b['records']:
        if sha(r['text'].encode())!=r['sha256']: raise ValueError('hash mismatch')
    target=out/'capture.json'; target.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n'); target.chmod(0o600)
    protocol=repo/'research/studies/S-007-source-study-fidelity.md'
    (out/'protocol.md').write_bytes(protocol.read_bytes())
    print(json.dumps(dict(path=str(target),sha256=sha(target.read_bytes()),counts=dict(Counter(r['kind'] for r in b['records'])),errors=b['errors'])))
if __name__=='__main__': main()
