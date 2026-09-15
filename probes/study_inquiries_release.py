"""Retain owning rollout evidence here; never write to a live workspace."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/Users/v/other/worktrees/study-inquiries-20260909')
OUT=ROOT/'research/outputs/2026-09-09-study-inquiries-live'
def sha(data):return hashlib.sha256(data).hexdigest()
def capture():
 OUT.mkdir(mode=0o700)
 live=json.loads((BASE/'evidence/live-verification.json').read_text());assert live['verified']
 files=[BASE/'evidence'/n for n in ('live-verification.json','verify_live.py','verify_minime_continuity.py','before-activation.json','after-reloads.json','minime-reload.jsonl','minime-pending-next-continuity.json','minime-restored-next.log','reader-smoke.json','reader-stage-smoke.json','installation-smoke.json','foreign-restoration.json','steward-resume.json','reader-restored-foreign.log','minime-continuity.jsonl')]
 files += [BASE/'bridge-stage-01'/n for n in ('manifest.json','source-inputs.json','ready.json')]
 files += [Path(live['bridge']['activation_receipt']), BASE/'astrid-release/docs/steward-notes/study-inquiries-validation/checks.json', BASE/'astrid-release/docs/steward-notes/2026-09-09-study-inquiries.md',Path('/Users/v/other/minime/docs/2026-09-09-study-inquiries.md')]
 files += [ROOT/n for n in ('reservoir_research/study_capture.py','reservoir_research/study_sequences.py','tests/test_study_inquiries.py','research/outputs/2026-09-09-study-inquiries-research-tests.log','research/outputs/2026-09-09-study-inquiries-historical-replay.json')]
 records=[]
 def retain(name,raw,source):
  target=OUT/name
  with target.open('xb') as f:os.chmod(target,0o600);f.write(raw)
  records.append(dict(retained=name,source=source,sha256=sha(raw),bytes=len(raw)))
 for i,path in enumerate(files):
  a=path.stat();raw=path.read_bytes();b=path.stat()
  assert (a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_ino,b.st_size,b.st_mtime_ns),path
  retain(f'{i:02d}-{path.name}',raw,str(path))
 for being in ('astrid','minime'):
  repo=Path('/Users/v/other')/being;commit=live[being+'_commit']
  retain(being+'-implementation.patch',subprocess.check_output(['git','show','--format=fuller','--binary',commit],cwd=repo),str(repo)+' git show '+commit)
 retain('probe.py',Path(__file__).read_bytes(),str(Path(__file__)))
 (OUT/'manifest.json').write_text(json.dumps(dict(schema='study_inquiries_research_retention_v1',captured_at=datetime.now(timezone.utc).isoformat(),records=records,astrid_commit=live['astrid_commit'],minime_commit=live['minime_commit'],scope='Source qualification and owning rollout evidence; natural outcomes are separate.'),indent=2)+'\n')
 verify()
def verify():
 m=json.loads((OUT/'manifest.json').read_text())
 for r in m['records']:
  raw=(OUT/r['retained']).read_bytes();assert sha(raw)==r['sha256'] and len(raw)==r['bytes'],r
 result=dict(verified=True,retained_files=len(m['records']),manifest_sha256=sha((OUT/'manifest.json').read_bytes()))
 (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':
 if sys.argv[1:]==['capture']:capture()
 elif sys.argv[1:]==['verify']:verify()
 else:raise SystemExit('usage: study_inquiries_release.py capture|verify')
