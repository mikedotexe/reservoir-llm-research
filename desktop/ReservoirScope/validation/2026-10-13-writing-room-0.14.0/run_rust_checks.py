#!/usr/bin/env python3
"""Local Rust qualification; no app build, launch, model, or existing-service access."""
import datetime, hashlib, json, os, pathlib, re, subprocess, time
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=pathlib.Path(__file__).resolve().parent

def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def source():
    paths=set()
    for base in ['crates/reservoir-core','src-tauri/src']:
        paths.update((ROOT/base).rglob('*.rs'))
    paths.update(ROOT/p for p in ['Cargo.toml','Cargo.lock','crates/reservoir-core/Cargo.toml','src-tauri/Cargo.toml','crates/reservoir-core/SUSTAINED.md'])
    paths.update((ROOT/'crates/reservoir-core/tests/fixtures/sustained-prompts').iterdir())
    return [{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(paths) if p.is_file()]
env=os.environ.copy();env.update(DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer',SDKROOT='/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk')
report={'schema':'writing-room-rust-checks-v1','startedAt':utc(),'scope':'Rust core and desktop tests plus strict Clippy; only owned ephemeral loopback fixtures, no model/app/service launch. A61-second test exercises the production sustained transport beyond the legacy60-second cap.','environment':{k:env[k] for k in ['DEVELOPER_DIR','SDKROOT']},'sourceBefore':source(),'checks':[]}
commands=[('core-tests',['cargo','test','--locked','-p','reservoir-core','--all-targets']),('desktop-tests',['cargo','test','--locked','-p','reservoir-scope-desktop']),('strict-clippy',['cargo','clippy','--locked','-p','reservoir-core','-p','reservoir-scope-desktop','--all-targets','--','-D','warnings'])]
for name,cmd in commands:
    log=OUT/(name+'-01.log');began=time.monotonic();entry={'name':name,'command':cmd,'startedAt':utc(),'log':log.name}
    with log.open('x') as f:result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
    entry.update(endedAt=utc(),elapsedSeconds=time.monotonic()-began,exitCode=result.returncode,sha256=digest(log))
    counts=re.findall(r'test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored;',log.read_text());entry['passedTests']=sum(int(x[0]) for x in counts);entry['ignoredTests']=sum(int(x[2]) for x in counts)
    report['checks'].append(entry);print(json.dumps(entry),flush=True)
    if result.returncode:break
report.update(endedAt=utc(),sourceAfter=source());report['sourceUnchanged']=report['sourceBefore']==report['sourceAfter'];report['passed']=len(report['checks'])==3 and all(c['exitCode']==0 for c in report['checks']) and report['sourceUnchanged']
with (OUT/'rust-checks-01.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'receipt':'rust-checks-01.json','passed':report['passed'],'sourceUnchanged':report['sourceUnchanged']}),flush=True)
raise SystemExit(0 if report['passed'] else 1)
