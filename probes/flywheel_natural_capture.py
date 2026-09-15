#!/usr/bin/env python3
"""Read-only fixed-window deployment and natural-output capture for S-006.

Python standard library. Only writes new research/outputs directories. Retained
release inventories are checked as bytes, never imported or executed. Live JSONL
reads freeze a byte prefix; stable standalone files use before/after stat checks.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = {'before': ('2026-09-07T20:30:00+00:00','2026-09-07T22:20:00+00:00'),
           'after': ('2026-09-07T22:25:00+00:00','2026-09-08T03:30:00+00:00')}
BOUNDS = {k:tuple(datetime.fromisoformat(v).timestamp() for v in pair) for k,pair in WINDOWS.items()}
PROVIDER = 'astrid/capsules/spectral-bridge/src/llm/provider/'


def sha(b): return hashlib.sha256(b).hexdigest()
def era(t): return next((k for k,(start,end) in BOUNDS.items() if start <= t < end),None)
def stable(p, limit=8*1024*1024):
    if p.is_symlink(): raise ValueError('Unexpected symlink: '+str(p))
    a=p.stat()
    if a.st_size>limit: raise ValueError('Oversized: '+str(p))
    b=p.read_bytes();z=p.stat()
    if (a.st_size,a.st_mtime_ns)!=(z.st_size,z.st_mtime_ns) or len(b)!=a.st_size:
        raise ValueError('Changed during capture: '+str(p))
    return b

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--base',type=Path,default=ROOT.parent);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    out=a.out.resolve();base=a.base.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'research/outputs'): ap.error('Need new research/outputs directory')
    out.mkdir(parents=True,mode=0o700);items=[];errors=[]
    def save(name,raw,source,**extra):
        p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);p.chmod(0o600)
        row={'capture':name,'source':str(source),'bytes':len(raw),'sha256':sha(raw),**extra};items.append(row);return row
    def jsave(name,obj,source='research calculation',**extra):return save(name,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode(),source,**extra)
    def cap(name,p,**extra):return save(name,stable(p),p,**extra)
    cap('protocol.md',ROOT/'research/studies/S-006-natural-outcome-protocol.md')
    transaction=base/'astrid/.runtime/bridge-deployment/transactions/d49684f40eb54d8baf984c6945567f95'
    raw=stable(transaction/'receipt.json');receipt=json.loads(raw)
    # Do not retain the unrelated signed self-control envelope.
    projected={k:v for k,v in receipt.items() if k!='new_process'}
    projected['new_process']={k:v for k,v in receipt['new_process'].items() if k!='startup'}
    projected['startup_checkpoint']=receipt['new_process']['startup']['checkpoint']
    jsave('deployment/activation-projected.json',projected,transaction/'receipt.json',original_sha256=sha(raw),projection='new_process.startup excluded except checkpoint')
    cap('deployment/active-selection.json',base/'astrid/.runtime/bridge-deployment/active.json')
    audits={};inventories={}
    trace_files=['dialogue_runtime.rs','fallback_contracts.rs','generation_record.rs','dialogue_generation.rs','provider_execution.rs','protected_delivery.rs','runtime_feedback.rs']
    for label,folder in [('before','afterimages-live-20260907'),('after','marker-rollout-20260907')]:
        stage=base/'worktrees'/folder/'bridge-stage-01';manifest_raw=stable(stage/'manifest.json');manifest=json.loads(manifest_raw)
        save('deployment/'+label+'-manifest.json',manifest_raw,stage/'manifest.json')
        input_raw=stable(stage/'source-inputs.json');inv=json.loads(input_raw);save('deployment/'+label+'-inputs.json',input_raw,stage/'source-inputs.json')
        expected_manifest=receipt['old_identity']['manifest_sha256'] if label=='before' else receipt['manifest_sha256']
        expected_binary=receipt['old_identity']['binary_sha256'] if label=='before' else receipt['binary_sha256']
        binary=stage/'spectral-bridge-server';binary_raw=stable(binary,512*1024*1024)
        checks=[];norm={};prefix='/Users/v/other/worktrees/'+folder+'/'
        for f in inv['files']:
            original=f['path']
            if not original.startswith(prefix): raise ValueError('Unexpected source root '+original)
            rel=original.removeprefix(prefix);p=base/'worktrees'/folder/rel
            b=stable(p,32*1024*1024);norm[rel]=sha(b)
            checks.append({'path':rel,'sha256':sha(b),'expected':f['sha256'],'bytes':len(b),'matches':sha(b)==f['sha256'] and len(b)==f['size']})
        inventories[label]=norm
        audits[label]={'manifest_matches_activation':sha(manifest_raw)==expected_manifest,'binary_matches_activation':sha(binary_raw)==expected_binary,'binary_sha256':sha(binary_raw),'binary_bytes':len(binary_raw),'source_inputs_match_manifest':sha(input_raw)==manifest['source_inputs']['sha256'],'source_count':len(checks),'all_source_bytes_match':all(x['matches'] for x in checks),'source_checks':checks}
        for f in trace_files:
            cap('source/'+label+'-'+f,base/'worktrees'/folder/PROVIDER/f)
        if label=='after': cap('source/after-control_marker_annotation_tests.rs',base/'worktrees'/folder/PROVIDER/'control_marker_annotation_tests.rs')
    old,new=inventories['before'],inventories['after']
    audits['diff']={'changed':[k for k in old.keys()&new.keys() if old[k]!=new[k]],'added':sorted(new.keys()-old.keys()),'removed':sorted(old.keys()-new.keys())}
    audits['diff']['changed'].sort();jsave('deployment/audit.json',audits)
    ws=base/'astrid/capsules/spectral-bridge/workspace'
    # Full small diagnostic prefixes retain every outcome and parse failure.
    for name in ['control_marker_cleanup.jsonl','dialogue_live_attempts.jsonl','llm_request_events.jsonl']:
        p=ws/'diagnostics'/name;n=p.stat().st_size
        if n>16*1024*1024:raise ValueError('Diagnostic exceeds fixed cap')
        with p.open('rb') as f:b=f.read(n)
        save('diagnostics/'+name,b,p,prefix_bytes=n,complete_last_line=b.endswith(b'\n'),size_after=p.stat().st_size)
    generation_inventory=[]
    for day in ['2026-09-07','2026-09-08']:
        directory=ws/'generations'/day
        for e in sorted(os.scandir(directory),key=lambda e:e.name):
            if not e.name.startswith('gen_') or not e.name.endswith('.json'):continue
            p=Path(e.path)
            try:b=stable(p);j=json.loads(b);t=j['created_at_unix_ms']/1000;period=era(t)
            except Exception as ex:errors.append({'source':str(p),'error':str(ex)});continue
            row={'source':str(p),'sha256':sha(b),'generation_id':j.get('generation_id'),'attempt_index':j.get('attempt_index'),'created_at_unix_ms':j['created_at_unix_ms'],'era':period}
            if period: row['capture']=cap('generations/'+day+'/'+e.name,p,era=period)['capture']
            generation_inventory.append(row)
    jsave('generation-inventory.json',generation_inventory)
    # The dated archive inventory ends September 5; inspect later archive dirs if present.
    jroot=ws/'journal';archives=sorted(e.name for e in os.scandir(jroot/'archive') if e.is_dir(follow_symlinks=False))
    directories=[jroot]+[jroot/'archive'/name for name in archives if name>='until_2026-09-07']
    journal_inventory=[];names_scanned=0
    for d in directories:
        for e in os.scandir(d):
            names_scanned+=1;m=re.search(r'_(\d{10})\.txt$',e.name)
            if not m:continue
            t=int(m.group(1));period=era(t)
            if not period:continue
            p=Path(e.path)
            try:r=cap('journals/'+str(p.relative_to(jroot)),p,era=period,filename_unix=t);journal_inventory.append(r)
            except Exception as ex:errors.append({'source':str(p),'error':str(ex)})
    jsave('journal-scope.json',{'directories':[str(x) for x in directories],'archive_directory_inventory':archives,'selection':'filename Unix seconds, half-open frozen windows; no content selection','names_scanned':names_scanned,'captured':len(journal_inventory)})
    # Raw provider bodies can exist for accepted protected/runtime-feedback delivery.
    # Capture the fixed directory without following artifact-supplied paths. Exact
    # response hashes later associate them to timestamped generations; mtime is not event time.
    accepted=ws/'diagnostics/accepted_deliveries';delivery_inventory=[]
    if accepted.exists():
        dirs=[accepted]+[Path(e.path) for e in os.scandir(accepted) if e.is_dir(follow_symlinks=False)]
        for d in dirs:
            for e in os.scandir(d):
                if not re.fullmatch(r'[0-9a-f]{64}\.json',e.name):continue
                p=Path(e.path)
                try:
                    b=stable(p,2*1024*1024);j=json.loads(b)
                    if len(delivery_inventory)>=3000:raise ValueError('Accepted artifact count cap reached')
                    r=save('accepted/'+str(p.relative_to(accepted)),b,p,filename_hash_matches=sha(b)==p.stem);delivery_inventory.append(r)
                except Exception as ex:errors.append({'source':str(p),'error':str(ex)})
    jsave('accepted-inventory.json',delivery_inventory)
    # Only two identified deployment stack receipts, not the full environment ledger.
    env=ws/'environment_receipts/environment_receipts.jsonl';n=env.stat().st_size
    if n>8*1024*1024:raise ValueError('Environment ledger exceeds fixed cap')
    with env.open('rb') as f:env_bytes=f.read(n)
    selected=[]
    for i,line in enumerate(env_bytes.splitlines()):
        if any(x in line for x in [b'env_receipt_1788819460520_834000',b'env_receipt_1788819912209_462000']):
            selected.append({'line':i+1,'sha256':sha(line),'record':json.loads(line)})
    jsave('deployment/environment-selected.json',selected,env,prefix_sha256=sha(env_bytes),prefix_bytes=n)
    jsave('errors.json',errors)
    summary={'captured_at_utc':datetime.now(timezone.utc).isoformat(),'windows':WINDOWS,'generation_files':dict(Counter(r['era'] for r in generation_inventory if r['era'])),'journal_files':dict(Counter(r['era'] for r in journal_inventory)),'accepted_artifacts':len(delivery_inventory),'errors':len(errors),'source_audit':{k:{f:v for f,v in audit.items() if f!='source_checks'} for k,audit in audits.items()}}
    jsave('summary.json',summary)
    (out/'manifest.json').write_text(json.dumps(items,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
