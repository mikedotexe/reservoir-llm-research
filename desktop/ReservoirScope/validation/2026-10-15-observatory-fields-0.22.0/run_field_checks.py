#!/usr/bin/env python3
"""Focused offline core/desktop field contract checks. Never builds or launches the app bundle."""
import argparse,datetime,hashlib,json,os,pathlib,subprocess
HERE=pathlib.Path(__file__).resolve().parent;DESKTOP=HERE.parents[1]
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def identity(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def main():
 p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);a=p.parse_args();assert a.attempt.isdigit()
 source=[DESKTOP/x for x in ['crates/reservoir-core/src/observatory.rs','crates/reservoir-core/tests/observatory.rs','src-tauri/src/observatory.rs','src-tauri/src/observatory_tests.rs','crates/reservoir-core/tests/fixtures/swift-state-fields-v1.json','crates/reservoir-core/tests/fixtures/swift-state-fields-v1.provenance.json']]
 env=os.environ.copy();env.update(DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer',SDKROOT='/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX26.2.sdk',CARGO_INCREMENTAL='0',CARGO_BUILD_JOBS='2',CARGO_TARGET_DIR=str(DESKTOP/'target'))
 jobs=[('core',['cargo','test','--manifest-path','crates/reservoir-core/Cargo.toml','--test','observatory']),('desktop',['cargo','test','--manifest-path','src-tauri/Cargo.toml','observatory::tests','--','--test-threads=2'])]
 report={'schema':'focused-reference-field-tests-v1','startedAtUtc':utc(),'sourceBefore':[identity(x) for x in source],'environment':{k:env[k] for k in ['DEVELOPER_DIR','SDKROOT','CARGO_INCREMENTAL','CARGO_BUILD_JOBS','CARGO_TARGET_DIR']},'helper':identity(pathlib.Path(__file__).resolve()),'commands':[],'passed':False}
 receipt=HERE/f'field-checks-{a.attempt}.json'
 with receipt.open('x') as out:
  json.dump(report,out,indent=2);out.flush()
  try:
   for name,cmd in jobs:
    path=HERE/f'field-{name}-{a.attempt}.log';started=utc()
    with path.open('xb') as log:run=subprocess.run(cmd,cwd=DESKTOP,env=env,stdout=log,stderr=subprocess.STDOUT)
    row={'name':name,'command':cmd,'startedAtUtc':started,'endedAtUtc':utc(),'exitCode':run.returncode,'log':identity(path)};report['commands'].append(row);print(json.dumps(row),flush=True)
    if run.returncode:break
  finally:
   report.update(endedAtUtc=utc(),sourceAfter=[identity(x) for x in source]);report['sourceUnchanged']=report['sourceBefore']==report['sourceAfter'];report['passed']=len(report['commands'])==len(jobs) and all(x['exitCode']==0 for x in report['commands']) and report['sourceUnchanged'];out.seek(0);json.dump(report,out,indent=2);out.write('\n');out.truncate();out.flush()
 print(json.dumps({'passed':report['passed'],'receipt':str(receipt)}));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
