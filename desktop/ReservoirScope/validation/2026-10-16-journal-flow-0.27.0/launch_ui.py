#!/usr/bin/env python3
"""Launch only the exact user-selected 0.27 candidate into a new QA Library."""
from pathlib import Path
import datetime,json,os,subprocess,sys,hashlib
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent
D=V.parents[1]
sys.path.insert(0,str(D/'scripts'))
from qualification_receipt import package_inventory
plan=json.loads((V/'run-plan.json').read_bytes())
before=json.loads((V/'package-before-01.json').read_bytes())
assert hashlib.sha256((V/'package-before-01.json').read_bytes()).hexdigest()==plan['packageBefore']['sha256']
assert plan['version']=='0.27.0' and plan['episodeId']=='journal-flow-027-01'
app=Path(before['app']);assert package_inventory(app)==before['package']
check=subprocess.run(['/usr/bin/pgrep','-fl','reservoir-scope-desktop'],capture_output=True,text=True)
assert check.returncode==1 and not check.stdout.strip(), 'Another preview is running; no launch'
run=Path(plan['appRunDirectory']);assert run==D/'target/qa/0.27-journal-flow-ui01';run.mkdir()
library=run/'library';library.mkdir()
env=os.environ.copy();env['RESERVOIR_SCOPE_TAURI_LIBRARY']=str(library)
exe=app/'Contents/MacOS/reservoir-scope-desktop'
with (run/'stdout.log').open('x') as out,(run/'stderr.log').open('x') as err:
 child=subprocess.Popen([str(exe)],cwd=run,env=env,stdout=out,stderr=err,start_new_session=True)
receipt={'startedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':child.pid,'app':str(app),'executable':str(exe),'executableSha256':before['package']['binary']['sha256'],'runDirectory':str(run),'library':str(library),'planSha256':hashlib.sha256((V/'run-plan.json').read_bytes()).hexdigest(),'scope':'Spawn only; surviving exact PID and native window must be confirmed before controls. New Library, no session or model starts automatically.'}
with (V/'ui-launch-01.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps(receipt))
