#!/usr/bin/env python3
"""Independent native-field vectors; compiles unchanged native source, no app/live data."""
import datetime, hashlib, json, os, pathlib, struct, subprocess
HERE=pathlib.Path(__file__).resolve().parent
DESKTOP=HERE.parents[1]; REPO=DESKTOP.parents[1]
SOURCE=REPO/'native/ReservoirScope/Sources/ReservoirScope/StateSurface.swift'
GEOMETRY=REPO/'visualizations/reservoir-3d/state-geometry.json'
RAW=REPO/'native/ReservoirScope/Sources/ReservoirScope/Resources/state-replay.bin'
WRAPPER=HERE/'StateFieldsOracle.swift'
BINARY=DESKTOP/'target/qa/0.22-field-oracle/state-fields-oracle'
FIXTURE=DESKTOP/'crates/reservoir-core/tests/fixtures/swift-state-fields-v1.json'
def ident(p):
 b=p.read_bytes(); return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def exclusive(p,data):
 with p.open('xb') as f:f.write(data)
def main():
 sources=[SOURCE,GEOMETRY,RAW,WRAPPER,pathlib.Path(__file__).resolve()]
 before=[ident(p) for p in sources]; start=utc()
 BINARY.parent.mkdir(parents=True,exist_ok=True)
 assert not BINARY.exists() and not FIXTURE.exists()
 p=json.loads(GEOMETRY.read_bytes())['pca']; raw=RAW.read_bytes()
 subsets=[[i for i in range(3) if mask&(1<<i)] for mask in range(8)]
 basis=[[float(i==j) for i in range(4)] for j in range(3)]
 cases=[{'name':'synthetic-offset-orthogonal','activations':[.5,.6,.2,.7],'mean':[.2]*4,'components':basis,'selections':subsets},
        {'name':'synthetic-signed-unclamped','activations':[-3.,2.,-1.,0.],'mean':[.2]*4,'components':basis,'selections':subsets},
        {'name':'synthetic-sign-flipped','activations':[.5,.6,.2,.7],'mean':[.2]*4,'components':[[-v for v in c] for c in basis],'selections':subsets}]
 for row in [0,1,511,1023]:
  values=list(struct.unpack_from('<128f',raw,row*128*4))
  cases.append({'name':f'bundled-row-{row}','activations':values,'mean':p['mean'],'components':p['components'],'selections':subsets})
 inp=HERE/'native-field-inputs-01.json';exclusive(inp,(json.dumps({'cases':cases},indent=2,allow_nan=False)+'\n').encode())
 env=os.environ.copy();env['DEVELOPER_DIR']='/Applications/Xcode.app/Contents/Developer';env['SDKROOT']='/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk'
 command=['/usr/bin/xcrun','swiftc',str(SOURCE),str(WRAPPER),'-o',str(BINARY)]
 compiled=subprocess.run(command,capture_output=True,env=env)
 exclusive(HERE/'native-field-compile-01.log',compiled.stdout+compiled.stderr)
 report={'schema':'native-state-field-oracle-v1','startedAtUtc':start,'sourceBefore':before,'compile':{'command':command,'exitCode':compiled.returncode},'passed':False}
 if compiled.returncode==0:
  run=subprocess.run([str(BINARY),str(inp)],capture_output=True,env=env)
  exclusive(HERE/'native-field-run-01.stderr',run.stderr)
  report['run']={'command':[str(BINARY),str(inp)],'exitCode':run.returncode}
  if run.returncode==0:
   value=json.loads(run.stdout);assert len(value['cases'])==7
   exclusive(FIXTURE,run.stdout+b'\n')
   report.update(cases=7,selections=56,fixture=ident(FIXTURE),binary=ident(BINARY),inputs=ident(inp))
 report.update(endedAtUtc=utc(),sourceAfter=[ident(p) for p in sources])
 report['sourceUnchanged']=report['sourceBefore']==report['sourceAfter']
 report['passed']=report.get('selections')==56 and report['sourceUnchanged']
 exclusive(HERE/'native-field-oracle-01.json',(json.dumps(report,indent=2)+'\n').encode())
 print(json.dumps({'passed':report['passed'],'fixture':report.get('fixture'),'receipt':str(HERE/'native-field-oracle-01.json')}))
 return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
