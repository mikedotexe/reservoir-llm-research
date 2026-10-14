#!/usr/bin/env python3
"""Offline scope probe against the pinned0.15 verifier. Original exports stay read-only.
Negative copies add optional evidence only to a saved journal response and re-anchor
byte hashes; the matching event/candidate intentionally remains absent.
"""
import argparse,datetime,hashlib,json,shutil,stat,subprocess,time
from pathlib import Path
EXPECTED_OLD='18949732cf48c926003ffcf7b5b216bccc32ea071d0bff8a411e841eaba123d5'
def digest(b):return hashlib.sha256(b).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def inventory(root):
 result={};total=0
 for p in sorted(root.rglob('*')):
  if p.is_symlink():raise ValueError('linked member')
  if p.is_dir():continue
  if not stat.S_ISREG(p.stat().st_mode):raise ValueError('nonordinary member')
  b=p.read_bytes();total+=len(b)
  if len(b)>4*1024*1024 or total>16*1024*1024 or len(result)>1000:raise ValueError('bound exceeded')
  result[str(p.relative_to(root))]={'bytes':len(b),'sha256':digest(b)}
 return result
def encoded(v):return (json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n').encode()
def make_case(original,out,value):
 shutil.copytree(original,out)
 candidates=sorted((out/'journals').glob('journal-30-*.json'));assert len(candidates)==1
 journal=candidates[0];obj=json.loads(journal.read_bytes());entry=obj['pending']['entry']['id']
 obj['pending']['response']['providerPromptEvaluation']=value
 journal.write_bytes(encoded(obj));journal_sha=digest(journal.read_bytes())
 previous=None
 for p in sorted((out/'segments').glob('*.json')):
  link=json.loads(p.read_bytes());link['previousSha256']=previous
  if entry in link['journalSha256s']:link['journalSha256s'][entry]=journal_sha
  raw=encoded(link);p.write_bytes(raw);previous=digest(raw)
 manifest=out/'manifest.json';m=json.loads(manifest.read_bytes());m['lastSegmentSha256']=previous;manifest.write_bytes(encoded(m))
 return {'entryId':entry,'addedJournalOnlyEvidence':value,'negativeMeaning':'Journal metadata lacks matching retained response-event/candidate evidence. No actual provider report is asserted.'}
def main():
 a=argparse.ArgumentParser();a.add_argument('--original',type=Path,required=True);a.add_argument('--old-executable',type=Path,required=True);a.add_argument('--output-directory',type=Path,required=True);a.add_argument('--receipt',type=Path,required=True);p=a.parse_args()
 p.original=p.original.resolve();p.old_executable=p.old_executable.resolve();p.output_directory=p.output_directory.resolve();p.receipt=p.receipt.resolve()
 assert not p.receipt.exists() and not p.output_directory.exists()
 assert digest(p.old_executable.read_bytes())==EXPECTED_OLD
 before=inventory(p.original);p.output_directory.mkdir(parents=True)
 start=utc();cases=[]
 for name,value in [('journal-only-reported',{'status':'reported','count':9007199254740993}),('journal-only-malformed',{'status':'reported','count':'invented-not-an-integer'})]:
  case=p.output_directory/name;description=make_case(p.original,case,value);inv=inventory(case)
  command=[str(p.old_executable),'--verify-sustained',str(case)];began=utc();clock=time.monotonic();r=subprocess.run(command,capture_output=True,timeout=30);elapsed=time.monotonic()-clock
  (p.output_directory/(name+'.stdout.json')).write_bytes(r.stdout);(p.output_directory/(name+'.stderr.txt')).write_bytes(r.stderr)
  report=json.loads(r.stdout);assert r.returncode==0 and report['status']=='passed',(name,r.stdout,r.stderr)
  assert inventory(case)==inv
  cases.append({'name':name,**description,'command':command,'startedUtc':began,'elapsedSeconds':elapsed,'exitCode':r.returncode,'oldReaderResult':report,'negativeBundleInventory':inv,'negativeCopyUnchangedByReader':True})
 assert before==inventory(p.original);assert digest(p.old_executable.read_bytes())==EXPECTED_OLD
 result={'status':'old-reader-limitation-reproduced','scope':'Offline adversarial copies only. Passing old0.15 results do not validate new provider metadata. No models/services/appUI contacted.','startedUtc':start,'endedUtc':utc(),'scriptSha256':digest(Path(__file__).read_bytes()),'oldExecutable':str(p.old_executable),'oldExecutableSha256BeforeAndAfter':EXPECTED_OLD,'originalBundle':str(p.original),'originalInventoryBeforeAndAfter':before,'originalUnchanged':True,'cases':cases}
 with p.receipt.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({'receipt':str(p.receipt),'sha256':digest(p.receipt.read_bytes()),'status':result['status'],'cases':len(cases)}))
if __name__=='__main__':main()
