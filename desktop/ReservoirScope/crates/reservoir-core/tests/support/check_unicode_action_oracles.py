"""Offline Unicode action qualification against independent retained Swift runner.
Derives ephemeral terminal stage-4 journal mutations from a public recording;
this is a verifier probe, never a new model/provider result. Original files are
unchanged. Encoded vectors come from the separately retained native codec oracle.
"""
import argparse, copy, hashlib, json, platform, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def invoke(cmd):
 r=subprocess.run([str(v) for v in cmd],capture_output=True,text=True,timeout=60)
 return dict(command=[str(v) for v in cmd],exitCode=r.returncode,stdout=r.stdout.strip(),stderr=r.stderr.strip())
def feedback(features,m):
 out=features.copy(); clamp=lambda x:max(0.0,min(1.0,x))
 damping=clamp(0.6*clamp((m['headShare']-.55)/.45)+0.4*clamp((.45-m['entropy'])/.45))
 lift=clamp(.45*min(1.,m['shoulderShare']/.35)+.35*min(1.,m['tailShare']/.30)+.20*clamp((m['entropy']-.55)/.45))
 out[26]*=1-.18*damping;out[27]*=1-.14*damping;out[31]*=1-.12*damping
 out[17]+=.18*lift;out[26]+=.22*lift;out[27]+=.18*lift;out[31]+=.16*lift
 return [max(-5.,min(5.,x)) for x in out[:32]]+[0.]*16

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rust-runner',required=True,type=Path);p.add_argument('--swift-runner',required=True,type=Path);p.add_argument('--output',required=True,type=Path);args=p.parse_args()
 if args.output.exists():p.error('output exists; keep receipts append-only')
 crate=Path(__file__).resolve().parents[2];repo=crate.parents[3]
 original=repo/'essentials/examples/portable/example-model-4.json';oracle=crate/'tests/fixtures/unicode-codec-v1.json'
 native=json.loads(oracle.read_text());base=json.loads(original.read_text());cases=[]
 selected=[6,7,8,10,11,12,13,14,15,16,17,18,19,20,21]
 selected += [next(i for i,row in enumerate(native["vectors"]) if row["text"]==text) for text in ["कि", "क्ष", "क्\u200dष"]]
 with tempfile.TemporaryDirectory(prefix='reservoir-unicode-action-') as tmp:
  for index in selected:
   row=native['vectors'][index];text=row['text'];record=copy.deepcopy(base)
   a=record['right']['actions'][-1];j=record['right']['journals'][-1]
   digest=hashlib.sha256(text.encode()).hexdigest();identity=f"journal-{a['observedStep']}-{a['id']}-{digest}"
   j.update(id=identity,text=text,sha256=digest)
   a['journalEntryID']=identity;a['saveReceipt'].update(entryID=identity,sha256=digest,relativePath=f'right/{identity}.json')
   a['rawReply']=json.dumps({'action':'WRITE_JOURNAL','text':text},ensure_ascii=False,separators=(',',':'))
   a['rawReplyByteCount']=len(a['rawReply'].encode());a['encodedFeatures']=row['features']
   m=record['right']['frames'][a['observedStep']-1]['spectral'];a['semanticVector']=feedback(row['features'],m)
   path=Path(tmp)/f'unicode-{index}.json';path.write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8')
   checks=[invoke([args.swift_runner.resolve(),'verify',path]),invoke([args.rust_runner.resolve(),'verify',path,'--json'])]
   # U+FB00 and the unlisted complex namaste cluster remain unqualified.
   expected=[0,2] if index in (10,16) else [0,0]
   cases.append(dict(vector=index,text=text,derivedRecordingSha256=sha(path),expectedExitCodes=expected,checks=checks,passed=[r['exitCode'] for r in checks]==expected))
   if index==6:
    for mutation in ('features','journal-hash','raw-text'):
     damaged=copy.deepcopy(record)
     if mutation=='features':damaged['right']['actions'][-1]['encodedFeatures'][0]+=.1
     elif mutation=='journal-hash':damaged['right']['journals'][-1]['sha256']='0'*64
     else:
      r=damaged['right']['actions'][-1];r['rawReply']=json.dumps({'action':'WRITE_JOURNAL','text':'Different é'});r['rawReplyByteCount']=len(r['rawReply'].encode())
     bad=Path(tmp)/f'unicode-tampered-{mutation}.json';bad.write_text(json.dumps(damaged,ensure_ascii=False),encoding='utf-8')
     checks=[invoke([args.swift_runner.resolve(),'verify',bad]),invoke([args.rust_runner.resolve(),'verify',bad,'--json'])]
     cases.append(dict(kind='negativeMutation',mutation=mutation,derivedRecordingSha256=sha(bad),expectedExitCodes=[1,1],checks=checks,passed=all(r['exitCode']==1 for r in checks)))
 cached_sources=args.swift_runner.resolve().parents[1]/'sources'
 bindings=[]
 for name in ('spectral_bridge/TextCodec.swift','actions/ActionMechanisms.swift','actions/ActionVerification.swift'):
  source=repo/'essentials'/name;cached=cached_sources/name
  bindings.append(dict(path=str(source.relative_to(repo)),sha256=sha(source),cachedPath=str(cached),cachedSha256=sha(cached),matches=sha(source)==sha(cached)))
 receipt=dict(swiftSourceBindings=bindings,schema='reservoir-unicode-action-oracles-v1',createdAtUTC=datetime.now(timezone.utc).isoformat(),host=platform.platform(),
  scope='Terminal stage-4 journal verifier mutations; native codec features; no new provider results or broad Unicode/JSON parser parity',modelsContacted=False,originalFilesModified=False,
  rustRunner=dict(path=str(args.rust_runner.resolve()),sha256=sha(args.rust_runner)),swiftRunner=dict(path=str(args.swift_runner.resolve()),sha256=sha(args.swift_runner)),
  inputs=[dict(path=str(p.relative_to(repo)),sha256=sha(p)) for p in (original,oracle,Path(__file__).resolve(),crate/'src/codec.rs',crate/'src/codec_unicode_data.rs',crate/'src/actions.rs')],
  outcome='passed' if all(c['passed'] for c in cases) and all(b['matches'] for b in bindings) else 'failed',cases=cases)
 with args.output.open('x') as f:json.dump(receipt,f,ensure_ascii=True,indent=2);f.write('\n')
 print(json.dumps({'output':str(args.output),'outcome':receipt['outcome'],'cases':len(cases)}))
 return 0 if receipt['outcome']=='passed' else 1
if __name__=='__main__':raise SystemExit(main())
