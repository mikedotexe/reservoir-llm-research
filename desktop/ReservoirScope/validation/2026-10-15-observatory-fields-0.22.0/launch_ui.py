#!/usr/bin/env python3
"""Launch the exact 0.22 package once into an isolated writable Library."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from qualification_receipt import package_inventory

def main():
    receipt=HERE/'ui-launch-01.json'
    assert not receipt.exists()
    build=json.loads((HERE/'archive-check-01.json').read_text())
    app=Path(build['app']);assert package_inventory(app)==build['package']
    exe=app/'Contents/MacOS/reservoir-scope-desktop'
    run=ROOT/'target/qa/0.22-observatory-ui01';run.mkdir()
    library=run/'library';library.mkdir()
    env=os.environ.copy();env['RESERVOIR_SCOPE_TAURI_LIBRARY']=str(library)
    with (run/'stdout.log').open('x') as out,(run/'stderr.log').open('x') as err:
        child=subprocess.Popen([str(exe)],cwd=run,env=env,stdout=out,stderr=err,start_new_session=True)
    result={'startedUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'pid':child.pid,'executable':str(exe),'executableSha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'archiveCheckSha256':hashlib.sha256((HERE/'archive-check-01.json').read_bytes()).hexdigest(),'library':str(library),'runDirectory':str(run),'scope':'Owned offline Observatory UI. No readiness, model, experiment, feed or Being connection authorized by this launch.'}
    with receipt.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
if __name__=='__main__':main()
