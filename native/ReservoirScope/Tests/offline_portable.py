#!/usr/bin/env python3
"""Qualify a copied app and CLI with network and original checkout access denied."""
import argparse, datetime, getpass, hashlib, json, os, pathlib, shutil, subprocess, sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--app',type=pathlib.Path,required=True)
p.add_argument('--native-checks',type=pathlib.Path,required=True)
p.add_argument('--output',type=pathlib.Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
resources=a.app/'Contents/Resources';cli=a.app/'Contents/MacOS/essentials-run'
profile='(version 1)(allow default)(deny network*)(deny file-read* (subpath "/Volumes") (subpath "/Users/v/other") (subpath "/Users/mikepurvis/.cache/reservoir-research/portable-work"))'
(a.output/'disconnected.sb').write_text(profile+'\n')
def run(args,success=True,env=None):
    r=subprocess.run(['/usr/bin/sandbox-exec','-p',profile,*map(str,args)],capture_output=True,text=True,env=env,timeout=180)
    if success and r.returncode:raise RuntimeError(str(args)+'\n'+r.stdout+'\n'+r.stderr)
    return r
results=[]
for entry in json.loads((resources/'examples-index.json').read_text()):
    r=run([cli,'verify',resources/entry['file']])
    results.append(dict(file=entry['file'],result=r.stdout.strip()))
run([sys.executable,resources/'verify-package.py','verify','--app',a.app])
original=a.output/'original';original.mkdir()
exports=a.output/'exports';exports.mkdir()
for stage in range(1,9):
    spec=json.loads((resources/f'example-component-{stage}.json').read_text())['specification']
    spec['promptVersion']=2
    config=original/f'stage-{stage}.recipe.json';config.write_text(json.dumps(spec))
    output=original/f'stage-{stage}.json'
    r=run([cli,'actions','--config',config,'--output',output])
    record=json.loads(output.read_text())
    assert len(record['right']['frames'])==120
    assert [x['observedStep'] for x in record['right']['actions']]==([30,60,90] if stage>=4 else [])
    shutil.copy2(output,exports/output.name)
    results.append(dict(stage=stage,result=r.stdout.strip()))
# Replay with the original run/journal locations no longer present.
original.rename(a.output/'original-unavailable')
for file in exports.glob('*.json'):run([cli,'verify',file])
env=dict(os.environ,RESERVOIR_SCOPE_LIBRARY=str(a.output/'native-library'))
native=run([a.native_checks,resources,a.output/'native-exports'],env=env)
(a.output/'native-checks.log').write_text(native.stdout+native.stderr)
receipt=dict(schema='reservoir-scope.disconnected-qualification.v1',status='passed',
    at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),user=getpass.getuser(),uid=os.getuid(),
    app=str(a.app),cli_sha256=hashlib.sha256(cli.read_bytes()).hexdigest(),sandbox=profile,
    example_records=len(json.loads((resources/'examples-index.json').read_text())),fresh_stages=8,
    original_paths_unavailable=True,network_denied=True,results=results,
    native_store=json.loads((a.output/'native-exports/native-store-receipt.json').read_text()),
    scope='Copied packaged CLI and production native view-model/store checks. Presented app launch and visual review have separate evidence.')
(a.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ['results','sandbox','native_store']},indent=2))
