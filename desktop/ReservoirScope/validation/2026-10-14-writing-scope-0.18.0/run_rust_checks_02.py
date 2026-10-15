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
env=os.environ.copy();env.update(DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer',SDKROOT='/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk',CARGO_INCREMENTAL='0',CARGO_BUILD_JOBS='2',PATH='/Users/v/.cargo/bin:/Users/v/.nvm/versions/node/v20.20.1/bin:'+os.environ['PATH'])
report={'schema':'writing-scope-rust-checks-v1','startedAt':utc(),'scope':'Rust core and desktop tests plus strict Clippy; only owned ephemeral loopback fixtures, no model/app/service launch. Includes v6 exact prompts, preserved v1–v5 contracts, same-reply numerical continuation, altered-prompt rejection and exact save/recovery gates.','environment':{k:env[k] for k in ['DEVELOPER_DIR','SDKROOT','CARGO_INCREMENTAL','CARGO_BUILD_JOBS']},'sourceBefore':source(),'checks':[]}
commands=[('desktop-tests',['cargo','test','--locked','-p','reservoir-scope-desktop']),('core-clippy',['cargo','clippy','--locked','-p','reservoir-core','--all-targets','--','-D','warnings']),('desktop-clippy',['cargo','clippy','--locked','-p','reservoir-scope-desktop','--all-targets','--','-D','warnings'])]
prior=json.loads((OUT/'rust-checks-01.json').read_text())
core=next(c for c in prior['checks'] if c['name']=='core-tests')
assert core['exitCode']==0 and prior['sourceUnchanged']
core_inputs=[e for e in prior['sourceAfter'] if e['path'].startswith('crates/reservoir-core/') or e['path'] in ['Cargo.toml','Cargo.lock']]
for e in core_inputs: assert digest(ROOT/e['path'])==e['sha256'],e['path']
core=dict(core);core['reuseReason']='All 200 core tests passed in run01; all core and workspace lock inputs unchanged. Run02 corrects only desktop test setup/default expectations after the retained run01 failures.'
report['checks'].append(core);report['reusedCoreInputs']=core_inputs
for name,cmd in commands:
    log=OUT/(name+'-02.log');began=time.monotonic();entry={'name':name,'command':cmd,'startedAt':utc(),'log':log.name}
    with log.open('x') as f:result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
    entry.update(endedAt=utc(),elapsedSeconds=time.monotonic()-began,exitCode=result.returncode,sha256=digest(log))
    counts=re.findall(r'test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored;',log.read_text());entry['passedTests']=sum(int(x[0]) for x in counts);entry['ignoredTests']=sum(int(x[2]) for x in counts)
    report['checks'].append(entry);print(json.dumps(entry),flush=True)
    if result.returncode:break
report.update(endedAt=utc(),sourceAfter=source());report['sourceUnchanged']=report['sourceBefore']==report['sourceAfter'];report['passed']=len(report['checks'])==4 and all(c['exitCode']==0 for c in report['checks']) and report['sourceUnchanged']
with (OUT/'rust-checks-02.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'receipt':'rust-checks-02.json','passed':report['passed'],'sourceUnchanged':report['sourceUnchanged']}),flush=True)
raise SystemExit(0 if report['passed'] else 1)
