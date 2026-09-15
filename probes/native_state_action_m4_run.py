#!/usr/bin/env python3
"""Finite M4 native-only replication from retained executables and source manifests.

Run on volya after building the explicitly named, isolated baseline and candidate.
Writes new research evidence only; has no runtime, socket, journal or live-control path.
"""
from __future__ import annotations
import argparse, datetime, hashlib, json, os, platform, subprocess
from pathlib import Path

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path, value): Path(path).write_text(json.dumps(value, indent=2)+'\n')
def require(condition, message):
    if not condition: raise RuntimeError(message)
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--root',type=Path,required=True); args=parser.parse_args(); root=args.root
    output=root/'m4-validation'; require(not output.exists(), 'M4 validation output must be new'); output.mkdir()
    baseline_stage=root/'m4-baseline-stage'; candidate_stage=root/'m4-stage'
    baseline_binary=Path('/Users/v/.cache/reservoir-research/native-state-actions/baseline-b16c451/target/release/native-state-action-baseline')
    candidate_binary=Path('/Users/v/.cache/reservoir-research/native-state-actions/83a601f4ddc8f1a4/target/release/native-state-action-replay')
    template=json.loads((root/'m4-candidate-build-template.json').read_text())
    require(template['source_identity']=='83a601f4ddc8f1a46d6b9369d3197aa2f8805d9da6a102bb1e5209245c59f94f','unexpected candidate source identity')
    for record in template['files']:
        if record['path']=='Cargo.lock': continue
        if record['path'].startswith('src/bin/'):
            source=(candidate_stage/'src/main.rs').read_text().replace('extern crate self as minime;\npub mod esn; pub mod gpu; pub mod buffer_pool;\n','',1)
            actual=hashlib.sha256(source.encode()).hexdigest()
        else: actual=sha(candidate_stage/record['path'])
        require(actual==record['sha256'], 'candidate source mismatch: '+record['path'])
    require(sha(baseline_stage/'src/esn.rs')=='b4c7d43582f11818408cfd2a6ecfd866a02a3c2c8dfcc5e832da50f5e0486a03','baseline source differs')
    manifest={'started_at_utc':now(),'host':platform.platform(),'cpu':subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),
        'rust':subprocess.check_output(['rustc','--version'],text=True).strip(),'cargo':subprocess.check_output(['cargo','--version'],text=True).strip(),
        'script_sha256':sha(__file__),'baseline_binary':str(baseline_binary),'baseline_binary_sha256':sha(baseline_binary),
        'candidate_binary':str(candidate_binary),'candidate_binary_sha256':sha(candidate_binary),
        'source_checks_passed':True,'baseline_source_sha256':sha(baseline_stage/'src/esn.rs'),
        'candidate_source_identity':template['source_identity'],'comparison':'Both baseline and candidate execute on this M4 Pro; no cross-chip floating-point identity assumption.',
        'baseline_stage_files':{str(p.relative_to(baseline_stage)):sha(p) for p in baseline_stage.rglob('*') if p.is_file()},
        'candidate_stage_files':{str(p.relative_to(candidate_stage)):sha(p) for p in candidate_stage.rglob('*') if p.is_file()}}
    save(output/'replication.json',manifest)
    (output/'rehearsal-protocol.json').write_bytes((root/'rehearsal-protocol.json').read_bytes())
    template.update(stage=str(candidate_stage),binary=str(candidate_binary),binary_sha256=sha(candidate_binary),exit_code=0,
        scope='Same frozen native source, built and run on M4 Pro with a host-specific pre-action baseline.', build_log='../m4-build-final.log')
    save(output/'candidate-build-manifest.json',template)
    baseline_command=[str(baseline_binary),str(output/'baseline')]
    started=now(); result=subprocess.run(baseline_command,capture_output=True,text=True,timeout=120)
    (output/'baseline-run.log').write_text(result.stdout+'\n'+result.stderr)
    baseline_receipt={'started_at_utc':started,'finished_at_utc':now(),'command':baseline_command,'exit_code':result.returncode,'binary_sha256':sha(baseline_binary)}
    if result.returncode==0: baseline_receipt['baseline_sha256']=sha(output/'baseline/baseline.json')
    save(output/'baseline-run.json',baseline_receipt); require(result.returncode==0,'M4 baseline failed')
    command=[str(candidate_binary),'--baseline',str(output/'baseline/baseline.json'),'--output',str(output/'candidate-run')]
    started=now(); result=subprocess.run(command,capture_output=True,text=True,timeout=120)
    (output/'candidate-run.log').write_text(result.stdout+'\n'+result.stderr)
    execution={'started_at_utc':started,'finished_at_utc':now(),'command':command,'exit_code':result.returncode,'binary_sha256':sha(candidate_binary),'protocol_sha256':sha(output/'rehearsal-protocol.json')}
    save(output/'candidate-run/execution.json',execution); require(result.returncode==0,'M4 candidate failed')
    manifest.update(finished_at_utc=now(),baseline_exit_code=0,candidate_exit_code=0)
    save(output/'replication.json',manifest); print(json.dumps({'baseline':0,'candidate':0,'output':str(output)},indent=2))
if __name__=='__main__': main()
