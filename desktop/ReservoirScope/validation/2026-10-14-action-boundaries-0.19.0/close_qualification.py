#!/usr/bin/env python3
"""Read-only final identity continuity; no test rerun, provider or GUI launch."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
HERE=Path(__file__).resolve().parent
DESKTOP=HERE.parents[1]
ROOT=DESKTOP.parents[1]
sys.path.insert(0,str(DESKTOP/'scripts'))
from qualification_receipt import source_inventory,package_inventory

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def read(n):return json.loads((HERE/n).read_text())
def same_inputs(items):
 for row in items:assert sha(DESKTOP/row['path'])==row['sha256'],row['path']
r={'schema':'reservoir-v7-qualification-close-v1','capturedAtUtc':datetime.now(timezone.utc).isoformat(),'scope':'Final identity/receipt continuity; no new tests, GUI, provider, numerical or writing-quality acceptance.'}
try:
 rust=read('rust-checks-01.json');assert rust['passed'] and rust['sourceUnchanged'];same_inputs(rust['sourceAfter'])
 front=read('frontend-checks-01.json');assert front['status']=='passed' and not front['sourceChangesDuringChecks']
 for name,digest in front['sourceInputsSha256'].items():assert sha(DESKTOP/name)==digest,name
 archive=read('archive-check-01.json');assert sha(Path(archive['archive']))==archive['archiveSha256'];assert sha(Path(archive['pinnedExecutable']))==archive['executableSha256']
 assert package_inventory(Path(archive['app']))==archive['package']
 prior=read('prior-package-preserved-01.json')
 assert sha(Path(prior['archive']))==prior['archiveSha256'];assert sha(Path(prior['pinnedExecutable']))==prior['executableSha256']
 oldcopy=DESKTOP/'target/qa/0.18-preserved/Reservoir Scope Tauri Preview.app';assert package_inventory(oldcopy)==prior['package']
 before={x['path']:x for x in read('source-before-build-01.json')['sourceBefore']};after={x['path']:x for x in source_inventory()}
 changes=[k for k in sorted(before.keys()|after.keys()) if before.get(k)!=after.get(k)]
 assert changes==['desktop/ReservoirScope/README.md','shared/reservoir-scope/PARITY.md'],changes
 freeze=read('prospective-freeze-01.json')
 for row in freeze['files']:assert sha(HERE/row['path'])==row['sha256'],row['path']
 provider=read('provider-stopped-01.json')
 for name,item in provider['files'].items():assert sha(Path(provider['fixtureDirectory'])/name)==item['sha256'],name
 for n in ('original-export-evidence-01.json','recovered-export-evidence-01.json'):
  e=read(n);assert e['status']=='passed'
  for name,item in e['staticJoins']['inventory'].items():assert sha(Path(e['staticJoins']['bundle'])/name)==item['sha256'],name
 assert read('historical-replay-01.json')['status']=='passed'
 assert read('reanchored-tamper-01.json')['status']=='passed'
 assert read('recovery-comparison-01.json')['status']=='passed'
 names=['rust-checks-01.json','frontend-checks-01.json','synthetic-harness-tests-01.json','tamper-helper-tests-02.json','package-build-01.json','archive-check-01.json','qualification-before-ui-01.json','historical-replay-01.json','original-export-evidence-01.json','recovered-export-evidence-01.json','recovery-comparison-01.json','reanchored-tamper-01.json','provider-stopped-01.json','native-recovery-01.json']
 r.update(status='passed',checkedReceipts=[identity(HERE/n) for n in names],productionInputsAndPackagesUnchanged=True,prospectiveInputsUnchanged=True,exportAndStoppedProviderFilesUnchanged=True,postBuildDocumentationChanges=[{'path':n,'before':before[n],'after':after[n]} for n in changes],roadmap=identity(ROOT/'TAURI-ROADMAP.md'),script=identity(Path(__file__).resolve()))
except Exception as e:r.update(status='failed',error=f'{type(e).__name__}: {e}')
with (HERE/'qualification-close-01.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({k:r[k] for k in ('status','error') if k in r}))
raise SystemExit(0 if r['status']=='passed' else 1)
