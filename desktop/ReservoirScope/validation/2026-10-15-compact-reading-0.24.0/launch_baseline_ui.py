#!/usr/bin/env python3
"""Optional exact preserved0.23.0 baseline launch in a new Library; lead invokes only."""
import argparse
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

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-preservation-sha256',required=True)
    args=parser.parse_args()
    preservation=HERE/'prior-package-preserved-01.json'
    assert sha(preservation)==args.expected_preservation_sha256, 'Explicit preservation receipt changed'
    prior=json.loads(preservation.read_bytes())
    assert prior['passed'] and prior['copiesByteExact'] and prior['originalsUnchanged']
    receipt=HERE/'baseline-ui-launch-01.json'
    assert not receipt.exists()
    app=Path(prior['preservedApp']);package=package_inventory(app)
    assert package==prior['package'] and package['version']==package['build']=='0.23.0'
    assert package['bundleIdentifier']=='research.reservoir.scope.tauri'
    for field in ('preservedArchive','preservedPin','basis'):
        value=prior[field];assert sha(Path(value['path']))==value['sha256']
    exe=app/'Contents/MacOS/reservoir-scope-desktop'
    assert sha(exe)==prior['preservedPin']['sha256']
    run=ROOT/'target/qa/0.24-baseline-ui01';run.mkdir()
    library=run/'library';library.mkdir()
    env=os.environ.copy();env['RESERVOIR_SCOPE_TAURI_LIBRARY']=str(library)
    with (run/'stdout.log').open('x') as out,(run/'stderr.log').open('x') as err:
        child=subprocess.Popen([str(exe)],cwd=run,env=env,stdout=out,stderr=err,start_new_session=True)
    result={'startedUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'pid':child.pid,'executable':str(exe),'executableSha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'preservationReceiptSha256':sha(preservation),'priorArchiveCheckSha256':prior['basis']['sha256'],'packageInventorySha256':package['inventorySha256'],'library':str(library),'runDirectory':str(run),'scope':'Optional preserved0.23.0 baseline compact-window/journal-reading inspection in an exclusive QA Library. No provider/server/readiness, live feed or Being connection authorized. Launch alone starts no session; lead controls any subsequent scripted UI actions.'}
    with receipt.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
if __name__=='__main__':main()
