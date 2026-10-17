#!/usr/bin/env python3
"""Launch the exact 0.25.0 package once into an isolated writable Library."""
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
    parser.add_argument('--expected-archive-check-sha256',required=True)
    args=parser.parse_args()
    assert sha(HERE.parent/'2026-10-15-journal-first-0.25.0/archive-check-01.json')==args.expected_archive_check_sha256, 'Explicit archive-check identity changed'
    receipt=HERE/'ui-launch-01.json'
    assert not receipt.exists()
    build=json.loads((HERE.parent/'2026-10-15-journal-first-0.25.0/archive-check-01.json').read_text())
    app=Path(build['app']);assert package_inventory(app)==build['package']
    assert build['package']['version']=='0.25.0' and build['package']['build']=='0.25.0'
    assert build['package']['bundleIdentifier']=='research.reservoir.scope.tauri'
    assert sha(Path(build['archive']))==build['archiveSha256']
    assert sha(Path(build['pinnedExecutable']))==build['executableSha256']
    exe=app/'Contents/MacOS/reservoir-scope-desktop'
    assert sha(exe)==build['executableSha256']
    run=ROOT/'target/qa/0.25-journal-flow-ui01';run.mkdir()
    library=run/'library';library.mkdir()
    env=os.environ.copy();env['RESERVOIR_SCOPE_TAURI_LIBRARY']=str(library)
    with (run/'stdout.log').open('x') as out,(run/'stderr.log').open('x') as err:
        child=subprocess.Popen([str(exe)],cwd=run,env=env,stdout=out,stderr=err,start_new_session=True)
    result={'startedUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'pid':child.pid,'executable':str(exe),'executableSha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'archiveCheckSha256':hashlib.sha256((HERE.parent/'2026-10-15-journal-first-0.25.0/archive-check-01.json').read_bytes()).hexdigest(),'library':str(library),'runDirectory':str(run),'scope':'Owned journal-first real-model UI check in an exclusive QA Library. Only the separately admitted owned endpoint is authorized; no shared service or Being. Launch starts no session; lead sets frozen plan through UI.'}
    with receipt.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
if __name__=='__main__':main()
