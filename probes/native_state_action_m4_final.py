#!/usr/bin/env python3
"""Qualify the final JSON-exact native build against the retained M4 baseline.

Research artifacts only. The explicit binary runs a finite numerical rehearsal,
with no runtime, socket, journal or model-call entry point.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, platform, shutil, subprocess, sys, tomllib
from pathlib import Path

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path, value): Path(path).write_text(json.dumps(value,indent=2)+'\n')
def require(condition, message):
    if not condition: raise RuntimeError(message)
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--root',type=Path,required=True); args=parser.parse_args(); root=args.root
    final=root/'final'; output=final/'m4-validation'; require(not output.exists(),'final M4 output must be new'); output.mkdir()
    stage=final/'m4-stage'; binary=Path('/Users/v/.cache/reservoir-research/native-state-actions/0c1a8c602996cfa1/target/release/native-state-action-replay')
    build=json.loads((final/'candidate-build-manifest.json').read_text())
    identity='0c1a8c602996cfa15a50905a1b805686c5dc3f656ce26d03ca981f90f20f8c4e'
    require(build['source_identity']==identity,'unexpected final source identity')
    require(hashlib.sha256(json.dumps(build['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==identity,'manifest identity digest')
    for record in build['files']:
        if record['path']=='Cargo.lock': continue
        if record['path'].startswith('src/bin/'):
            source=(stage/'src/main.rs').read_text().replace('extern crate self as minime;\npub mod esn; pub mod gpu; pub mod buffer_pool;\n','',1)
            actual=hashlib.sha256(source.encode()).hexdigest()
        else: actual=sha(stage/record['path'])
        require(actual==record['sha256'],'final source differs: '+record['path'])
    cargo=tomllib.loads((stage/'Cargo.toml').read_text())
    require('float_roundtrip' in cargo['dependencies']['serde_json']['features'],'exact JSON feature missing')
    origin=root/'m4-validation'; origin_manifest=json.loads((origin/'replication.json').read_text())
    require(origin_manifest['cpu']=='Apple M4 Pro','baseline host differs')
    shutil.copytree(origin/'baseline',output/'baseline'); shutil.copy2(origin/'baseline-run.json',output/'baseline-run.json')
    shutil.copy2(final/'rehearsal-protocol.json',output/'rehearsal-protocol.json'); shutil.copy2(final/'qualification-amendment.json',output/'qualification-amendment.json')
    baseline_receipt=json.loads((output/'baseline-run.json').read_text())
    require(sha(output/'baseline/baseline.json')==baseline_receipt['baseline_sha256'],'baseline reference differs')
    build.update(stage=str(stage),binary=str(binary),binary_sha256=sha(binary),exit_code=0,build_log='../m4-build.log',
        scope='Final JSON-feature-matched frozen native build on M4 Pro; retained host-specific pre-action baseline reused without numerical changes.')
    save(output/'candidate-build-manifest.json',build)
    receipt={'started_at_utc':now(),'host':platform.platform(),'cpu':subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),
        'rust':subprocess.check_output(['rustc','--version'],text=True).strip(),'python':sys.version,'script_sha256':sha(__file__),
        'source_identity':identity,'source_checks_passed':True,'serde_json_features':cargo['dependencies']['serde_json']['features'],
        'candidate_binary_sha256':sha(binary),'baseline_reused_from':str(origin),'baseline_sha256':sha(output/'baseline/baseline.json'),
        'baseline_replication_sha256':sha(origin/'replication.json'),'candidate_cargo_lock_sha256':sha(stage/'Cargo.lock'),
        'comparison':'M4 Pro candidate versus unchanged M4 Pro pre-action baseline; no cross-chip equality assumption.'}
    save(output/'replication.json',receipt); shutil.copy2(__file__,output/'run-script.py')
    command=[str(binary),'--baseline',str(output/'baseline/baseline.json'),'--output',str(output/'candidate-run')]
    started=now(); run=subprocess.run(command,text=True,capture_output=True,timeout=120)
    (output/'candidate-run.log').write_text(run.stdout+'\n'+run.stderr)
    execution={'started_at_utc':started,'finished_at_utc':now(),'command':command,'exit_code':run.returncode,'binary_sha256':sha(binary),'protocol_sha256':sha(output/'rehearsal-protocol.json')}
    save(output/'candidate-run/execution.json',execution); require(run.returncode==0,'final M4 numerical run failed')
    receipt.update(finished_at_utc=now(),candidate_exit_code=0);save(output/'replication.json',receipt)
    print(json.dumps({'exit_code':0,'source_identity':identity,'output':str(output)},indent=2))
if __name__=='__main__':main()
