#!/usr/bin/env python3
import datetime,hashlib,json,os,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parents[2]
v=Path(__file__).resolve().parent
receipt=v/'core-focused-01.json';log=v/'core-focused-01.log'
assert not receipt.exists() and not log.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory():
 base=root/'crates/reservoir-core'
 return {str(p.relative_to(root)):sha(p) for p in sorted(base.rglob('*')) if p.is_file() and (p.suffix in ('.rs','.md','.toml') or 'tests/fixtures' in str(p))}
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
command=['cargo','test','--locked','-p','reservoir-core','--test','sustained_provider_evidence','--test','sustained_generation_budget','--test','sustained_prompts','--test','sustained_measurement_reference']
env=os.environ.copy();selected={'DEVELOPER_DIR':'/Applications/Xcode.app/Contents/Developer','SDKROOT':'/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk'};env.update(selected)
before=inventory();start=utc();clock=time.monotonic()
with log.open('xb') as f:r=subprocess.run(command,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT)
after=inventory()
result={'status':'passed' if r.returncode==0 and before==after else 'failed','command':command,'environment':selected,'startedUtc':start,'endedUtc':utc(),'wallSeconds':time.monotonic()-clock,'exitCode':r.returncode,'sourceBefore':before,'sourceAfter':after,'sourceUnchanged':before==after,'logSha256':sha(log),'scope':'Focused core tests only; no provider, service, appUI or Being access. Supplied response values are test data.'}
with receipt.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'receipt':str(receipt),'sha256':sha(receipt)}))
raise SystemExit(0 if result['status']=='passed' else 1)
