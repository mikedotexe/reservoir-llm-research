#!/usr/bin/env python3
"""Read-only comparison of the two explicitly selected native v7 exports."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p): return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def inventory(root):
 result={}
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink()
  if p.is_file():result[str(p.relative_to(root))]={'bytes':p.stat().st_size,'sha256':sha(p)}
 return result
original=ROOT/'target/qa/0.19-action-boundaries/exports/sustained-1791997601433-1-1-76'
recovered=ROOT/'target/qa/0.19-action-boundaries/exports/sustained-1791997601433-1-2-77'
receipts=[HERE/'original-export-evidence-01.json',HERE/'recovered-export-evidence-01.json']
a,b=inventory(original),inventory(recovered)
for path,expected in zip(receipts,(a,b)):
 receipt=json.loads(path.read_text());assert receipt['status']=='passed';assert receipt['staticJoins']['inventory']==expected;assert receipt['staticJoins']['finalCorePhase']=='blocked'
assert a.keys()==b.keys() and len(a)==28
assert [name for name in a if a[name]!=b[name]]==['manifest.json']
x,y=[json.loads((p/'manifest.json').read_text()) for p in (original,recovered)]
changes={k:{'original':x.get(k),'recovered':y.get(k)} for k in x.keys()|y.keys() if x.get(k)!=y.get(k)}
assert changes=={'generation':{'original':1,'recovered':2},'revision':{'original':76,'recovered':77},'phase':{'original':'attemptBlocked','recovered':'paused'}}
assert x['config']['promptVersion']==y['config']['promptVersion']=='reservoir-journal-v7'
provider=json.loads((HERE/'provider-stopped-01.json').read_text())
for name,item in provider['files'].items():
 p=Path(provider['fixtureDirectory'])/name;assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256']
assert inventory(original)==a and inventory(recovered)==b
report={'schema':'reservoir-v7-native-recovery-byte-comparison-v1','capturedAtUtc':datetime.now(timezone.utc).isoformat(),'status':'passed','original':str(original),'recovered':str(recovered),'verificationReceipts':[identity(p) for p in receipts],'originalInventory':a,'recoveredInventory':b,'identicalNonManifestFiles':27,'manifestDifferences':changes,'finalCorePhase':'blocked','stoppedProviderFilesUnchanged':True,'originalUnchanged':True,'script':identity(Path(__file__).resolve()),'scope':'Clean-quit and explicit paused restore; no crash/power-loss or model quality claim.'}
with (HERE/'recovery-comparison-01.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({k:report[k] for k in ('status','identicalNonManifestFiles','manifestDifferences','stoppedProviderFilesUnchanged')}))
