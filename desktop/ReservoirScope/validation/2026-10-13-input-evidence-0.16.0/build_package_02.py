"""Build this candidate once after source qualification; retain exact inputs and outputs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, shutil, subprocess, sys, tarfile, time
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
from qualification_receipt import source_inventory, inventory_digest, package_inventory

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat()
env=os.environ.copy();env.update(DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer',SDKROOT='/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk')
rust=json.loads((OUT/'rust-checks-01.json').read_text());assert rust['status']=='passed' and rust['sourceUnchanged']
frontend=json.loads((OUT/'frontend-checks-05.json').read_text());assert frontend['tests']['exitCode']==0 and frontend['build']['exitCode']==0
for p,d in frontend['files'].items(): assert sha(ROOT/p)==d,p
rust_sources=json.loads((OUT/'rust-source-before-01.json').read_text())
for e in rust_sources['files']: assert sha(ROOT.parents[1]/e['path'])==e['sha256'],e['path']
before=source_inventory();report={'startedUtc':utc(),'sourceBefore':before,'sourceInventorySha256':inventory_digest(before),'environment':{k:env[k] for k in ['DEVELOPER_DIR','SDKROOT']},'checks':[]}
with (OUT/'source-before-build-02.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
for name,cmd in [('reference',['python3','scripts/check_reference.py']),('macos-package',['npm','run','tauri','--','build','--bundles','app','--','--locked'])]:
    start=time.monotonic();log=OUT/(name+'-02.log');stamp=utc()
    with log.open('x') as f:r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
    report['checks'].append({'name':name,'command':cmd,'startedUtc':stamp,'elapsedSeconds':time.monotonic()-start,'exitCode':r.returncode,'logSha256':sha(log)})
    print(json.dumps(report['checks'][-1]),flush=True)
    if r.returncode: break
report['sourceUnchanged']=source_inventory()==before
report['finishedUtc']=utc()
with (OUT/'package-build-02.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
assert report['sourceUnchanged'] and all(c['exitCode']==0 for c in report['checks'])
app=ROOT/'target/release/bundle/macos/Reservoir Scope Tauri Preview.app'
archive=app.parent/'ReservoirScopeTauriPreview-0.16.0-r2-macos-arm64.tar.gz'
assert not archive.exists()
with tarfile.open(archive,'x:gz') as f:f.add(app,arcname=app.name)
entries=[]
with tarfile.open(archive,'r:gz') as f:
    for m in f.getmembers():
        relative=Path(m.name).relative_to(app.name); original=app/relative
        if m.isfile():
            d=hashlib.sha256(f.extractfile(m).read()).hexdigest(); assert d==sha(original)
            entries.append({'path':str(relative),'sha256':d,'bytes':m.size})
        elif m.issym():assert original.is_symlink() and os.readlink(original)==m.linkname
        else:assert m.isdir() and original.is_dir()
pinned=ROOT/'target/qa/0.16-r2-pinned';pinned.mkdir(exist_ok=False)
exe=app/'Contents/MacOS/reservoir-scope-desktop';shutil.copy2(exe,pinned/exe.name)
receipt={'createdUtc':utc(),'app':str(app),'package':package_inventory(app),'archive':str(archive),'archiveSha256':sha(archive),'members':entries,'executableSha256':sha(exe),'pinnedExecutable':str(pinned/exe.name)}
with (OUT/'archive-check-02.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps({k:receipt[k] for k in ['archiveSha256','executableSha256','pinnedExecutable']}),flush=True)
r=subprocess.run(['python3','scripts/qualification_receipt.py','--app',str(app),'--archive',str(archive),'--output',str(OUT/'qualification-before-ui-02.json'),'--note','Source checks, build and archive evidence are retained separately in this directory; actual UI/model execution follows this receipt.'],cwd=ROOT,env=env)
raise SystemExit(r.returncode)
