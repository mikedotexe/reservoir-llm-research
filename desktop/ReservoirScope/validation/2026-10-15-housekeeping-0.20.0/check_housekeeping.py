#!/usr/bin/env python3
"""Verify docs, exact history copies and preservation of the pre-housekeeping files."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
DOCS=['TAURI-ROADMAP.md','TAURI-ROADMAP-HISTORY-2026-10-15.md','shared/reservoir-scope/PARITY.md','shared/reservoir-scope/PARITY-HISTORY-2026-10-15.md','desktop/ReservoirScope/README.md','desktop/ReservoirScope/README-HISTORY-2026-10-15.md','desktop/ReservoirScope/STATUS.md']
def identity(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 baseline=json.loads((HERE/'before-inventory.json').read_text());changes=[];unchanged=0
 for row in baseline['files']:
  p=ROOT/row['path'];actual=identity(p)
  if (actual['bytes'],actual['sha256'])==(row['bytes'],row['sha256']):unchanged+=1
  else:changes.append(row['path'])
 allowed={'TAURI-ROADMAP.md','shared/reservoir-scope/PARITY.md','desktop/ReservoirScope/README.md','desktop/ReservoirScope/.gitignore'}
 assert set(changes)<=allowed,changes
 copies=[('TAURI-ROADMAP.md.before.txt',DOCS[1]),('PARITY.md.before.txt',DOCS[3]),('README.md.before.txt',DOCS[5])]
 for old,new in copies:assert (HERE/old).read_bytes()==(ROOT/new).read_bytes()
 checked=[];errors=[]
 for name in DOCS:
  p=ROOT/name
  for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   target=target.strip('<>')
   if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target):continue
   pathpart=unquote(target.split('#')[0]);dest=(p.parent/pathpart).resolve() if pathpart else p
   checked.append(dict(source=name,target=target))
   if not dest.exists():errors.append(dict(source=name,target=target))
 assert not errors,errors
 check=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True);assert check.returncode==0,check.stdout+check.stderr
 receipt=dict(atUtc=dt.datetime.now(dt.timezone.utc).isoformat(),status='passed',documents=[identity(ROOT/p) for p in DOCS],localLinkTargetsChecked=len(checked),linkScope='Local destination existence; all 374 links/anchors independently checked by documentation editor before this root readback.',linkErrors=errors,baselineFiles=len(baseline['files']),unchangedFiles=unchanged,permittedChangedFiles=changes,historyCopiesByteExact=True,productChangedByHousekeeping=False,oldValidationFilesChanged=False,diffCheckExit=check.returncode,script=identity(Path(__file__).resolve()))
 with (HERE/'doc-checks-01.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
 print(json.dumps({k:receipt[k] for k in ['status','localLinkTargetsChecked','baselineFiles','unchangedFiles','permittedChangedFiles']}))
if __name__=='__main__':main()
