#!/usr/bin/env python3
"""Final file-only preservation/current-doc check after a refused bounded window."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]

def identity(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p.resolve()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def main():
 frozen=json.loads((HERE/'evaluation-freeze-01.json').read_text())
 for ref in frozen['files']:assert identity(ref['path'])==ref,ref['path']
 prior=json.loads((HERE/'runtime-copy-01.json').read_text())['priorDirectoryAfter']
 for ref in prior:assert identity(ref['path'])==ref,ref['path']
 plan=json.loads((HERE/'run-plan.json').read_text());admission=json.loads((HERE/'host-admission-01.json').read_text());outcome=json.loads((HERE/'outcome-01.json').read_text())
 assert admission['admitted'] is False and admission['freePercent']==31
 assert len(outcome['slots'])==12 and all(s['status']=='unstarted' for s in outcome['slots'])
 assert all(outcome[k]==0 for k in ['serviceLaunchInvocations','probeInvocations','inventoryRequests','generationRequests'])
 assert not Path(plan['ownedServiceDirectory']).exists() and not Path(plan['provenance']['resultsDirectory']).exists()
 docs=[ROOT/'TAURI-ROADMAP.md',ROOT/'shared/reservoir-scope/PARITY.md',ROOT/'desktop/ReservoirScope/README.md',ROOT/'desktop/ReservoirScope/STATUS.md',HERE/'README.md',HERE/'PROTOCOL.md',HERE.parent/'2026-10-15-housekeeping-0.20.0/README.md']
 checked=0;missing=[]
 for p in docs:
  for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   target=target.strip('<>')
   if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target):continue
   part=unquote(target.split('#')[0]);dest=(p.parent/part).resolve() if part else p
   checked+=1
   if not dest.exists():missing.append(dict(source=str(p),target=target))
 assert not missing,missing
 check=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True);assert check.returncode==0,check.stdout
 receipt=dict(atUtc=dt.datetime.now(dt.timezone.utc).isoformat(),status='passed',frozenFilesUnchanged=len(frozen['files']),priorFilesUnchanged=len(prior),slotOutcomes='12 unstarted',ownedDirectoriesAbsent=True,currentDocumentLocalTargetsChecked=checked,currentDocuments=[identity(p) for p in docs],sourceDiffCheckExit=check.returncode,script=identity(Path(__file__).resolve()),scope='Exact file checks only; no repeated host admission, model call, cleanup or production source change.')
 with (HERE/'closeout-01.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
 print(json.dumps({k:receipt[k] for k in ['status','frozenFilesUnchanged','priorFilesUnchanged','currentDocumentLocalTargetsChecked']}))
if __name__=='__main__':main()
