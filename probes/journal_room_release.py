"""Retain and verify the owning journal-room rollout; read-only outside this research repo."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/Users/v/other/worktrees/journal-room-20260909')
OUT=ROOT/'research/outputs/2026-09-09-journal-room-live'
def sha(data):return hashlib.sha256(data).hexdigest()
def capture():
 OUT.mkdir(mode=0o700)
 live=json.loads((BASE/'evidence/live-verification.json').read_text())
 assert live['verified'] is True
 files=[BASE/'evidence'/n for n in ('live-verification.json','verify_live.py','before-activation.json','after-reloads.json','minime-reload.jsonl','minime-pending-next-continuity.json','minime-restored-next.log','reader-smoke.json','foreign-restoration.json','steward-resume.json')]
 files += [BASE/'bridge-stage-01'/n for n in ('manifest.json','source-inputs.json','ready.json')]
 files += [Path(live['bridge']['activation_receipt'])]
 files += [BASE/'astrid-release/docs/steward-notes'/n for n in ('2026-09-09-journal-room-and-study-navigation.md','journal-room-validation/checks.json')]
 files += [Path('/Users/v/other/minime/docs/2026-09-09-journal-room.md'), Path('/Users/v/other/astrid/docs/steward-notes/2026-09-09-journal-room-and-study-navigation.md')]
 files += [BASE/'evidence/minime-continuity.jsonl', BASE/'evidence/reader-restored-foreign-02.log']
 files += [ROOT/name for name in ('reservoir_research/study_capture.py','reservoir_research/study_sequences.py','tests/test_study_sequences.py','research/outputs/2026-09-09-journal-room-research-tests.log','research/outputs/2026-09-09-journal-room-historical-replay.json')]
 records=[]
 def retain(name,data,source):
  target=OUT/name
  with target.open('xb') as f:os.chmod(target,0o600);f.write(data)
  records.append({'retained':name,'source':source,'sha256':sha(data),'bytes':len(data)})
 for i,path in enumerate(files):
  a=path.stat();data=path.read_bytes();b=path.stat()
  assert (a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_ino,b.st_size,b.st_mtime_ns),path
  retain(f'{i:02d}-{path.name}',data,str(path))
 for being in ('astrid','minime'):
  repo=Path('/Users/v/other')/being;commit=live[f'{being}_commit']
  data=subprocess.check_output(['git','show','--format=fuller','--binary',commit],cwd=repo)
  retain(f'{being}-implementation.patch',data,f'{repo} git show {commit}')
 retain('probe.py',Path(__file__).read_bytes(),str(Path(__file__)))
 manifest={'schema':'journal_room_research_retention_v1','captured_at':datetime.now(timezone.utc).isoformat(),'astrid_commit':live['astrid_commit'],'minime_commit':live['minime_commit'],'records':records,'scope':'Owning activation and source evidence, not a natural outcome or comprehension claim.'}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 verify()
def verify():
 m=json.loads((OUT/'manifest.json').read_text())
 for r in m['records']:
  raw=(OUT/r['retained']).read_bytes()
  assert sha(raw)==r['sha256'] and len(raw)==r['bytes'],r['retained']
 live=json.loads((OUT/'00-live-verification.json').read_text())
 assert live['verified'] is True
 assert all(live[f'{b}_commit']==m[f'{b}_commit'] for b in ('astrid','minime'))
 result={'verified':True,'retained_files':len(m['records']),'manifest_sha256':sha((OUT/'manifest.json').read_bytes())}
 (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result))
if __name__=='__main__':
 if sys.argv[1:] == ['capture']:capture()
 elif sys.argv[1:] == ['verify']:verify()
 else:raise SystemExit('usage: journal_room_release.py capture|verify')
