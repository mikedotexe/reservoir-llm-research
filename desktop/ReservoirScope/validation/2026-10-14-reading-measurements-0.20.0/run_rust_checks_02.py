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
report={'schema':'reading-measurement-rust-checks-v1','startedAt':utc(),'scope':'Rust core and desktop tests plus strict Clippy; only owned ephemeral loopback fixtures, no model/app/service launch. Includes v8 exact measurement interpretation, preserved v1–v7 contracts, same-reply numerical continuation, altered-prompt rejection and exact save/recovery gates.','environment':{k:env[k] for k in ['DEVELOPER_DIR','SDKROOT','CARGO_INCREMENTAL','CARGO_BUILD_JOBS']},'sourceBefore':source(),'checks':[]}
prior_path = OUT / 'rust-checks-01.json'
prior = json.loads(prior_path.read_text())
assert prior['sourceUnchanged'] and prior['checks'][0]['name'] == 'core-tests' and prior['checks'][0]['exitCode'] == 0
# Only desktop test expectations changed; core source/dependencies/fixtures retain the passing inputs.
for entry in prior['sourceAfter']:
    if entry['path'] == 'src-tauri/src/sustained_tests.rs':
        continue
    assert digest(ROOT / entry['path']) == entry['sha256'], entry['path']
assert digest(OUT / prior['checks'][0]['log']) == prior['checks'][0]['sha256']
report['reusedCoreTests'] = {'receipt': str(prior_path), 'receiptSha256': digest(prior_path), 'check': prior['checks'][0], 'reason': 'Core inputs unchanged; first full run passed 219 core tests. Only desktop test expectations and a v8 comparison-coverage case changed.'}
commands=[('desktop-tests',['cargo','test','--locked','-p','reservoir-scope-desktop']),('core-clippy',['cargo','clippy','--locked','-p','reservoir-core','--all-targets','--','-D','warnings']),('desktop-clippy',['cargo','clippy','--locked','-p','reservoir-scope-desktop','--all-targets','--','-D','warnings'])]
for name,cmd in commands:
    log=OUT/(name+'-02.log');began=time.monotonic();entry={'name':name,'command':cmd,'startedAt':utc(),'log':log.name}
    with log.open('x') as f:result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
    entry.update(endedAt=utc(),elapsedSeconds=time.monotonic()-began,exitCode=result.returncode,sha256=digest(log))
    counts=re.findall(r'test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored;',log.read_text());entry['passedTests']=sum(int(x[0]) for x in counts);entry['ignoredTests']=sum(int(x[2]) for x in counts)
    report['checks'].append(entry);print(json.dumps(entry),flush=True)
    if result.returncode:break
report.update(endedAt=utc(),sourceAfter=source());report['sourceUnchanged']=report['sourceBefore']==report['sourceAfter'];report['passed']=len(report['checks'])==3 and all(c['exitCode']==0 for c in report['checks']) and report['sourceUnchanged']
with (OUT/'rust-checks-02.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'receipt':'rust-checks-02.json','passed':report['passed'],'sourceUnchanged':report['sourceUnchanged']}),flush=True)
raise SystemExit(0 if report['passed'] else 1)
