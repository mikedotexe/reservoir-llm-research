#!/usr/bin/env python3
"""Freeze and compile the isolated native replay with explicit executable lineage."""
import argparse, datetime, hashlib, json, os, shutil, subprocess, tomllib
from pathlib import Path

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path, value): path.write_text(json.dumps(value, indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seed-target',type=Path)
    args=parser.parse_args(); root=args.output.resolve(); src=args.source.resolve()
    paths=['src/esn.rs','src/gpu.rs','src/buffer_pool.rs','src/state_action.rs','shaders/esn.metal','shaders/spectral.metal','shaders/nn.metal','src/bin/native_state_action_replay.rs','Cargo.lock']
    payloads={p:(src/'minime'/p).read_bytes() for p in paths}
    owning_manifest=(src/'minime/Cargo.toml').read_bytes()
    json_dependency=tomllib.loads(owning_manifest.decode())['dependencies']['serde_json']
    json_features=json_dependency.get('features',[]) if isinstance(json_dependency,dict) else []
    generated_manifest='''[package]
name="native-state-action-replay"
version="0.1.0"
edition="2021"
[features]
division-rehearsal=[]
[dependencies]
anyhow="1"
metal="0.29"
serde={version="1",features=["derive"]}
SERDE_JSON_DEPENDENCY
fastrand="2"
sha2="0.10"
clap={version="4",features=["derive"]}
[profile.release]
opt-level=3
'''.replace('SERDE_JSON_DEPENDENCY','serde_json={version="1",features='+json.dumps(json_features)+'}')
    payloads['owning/Cargo.toml']=owning_manifest
    payloads['Cargo.toml']=generated_manifest.encode()
    files=[{'path':p,'sha256':hashlib.sha256(data).hexdigest()} for p,data in payloads.items()]
    identity=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    stage=Path.home()/'.cache/reservoir-research/native-state-actions'/identity[:16]
    stage.mkdir(parents=True,exist_ok=True)
    for p,data in payloads.items():
        destination=stage/p; destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(data)
    harness=(stage/'src/bin/native_state_action_replay.rs').read_text()
    (stage/'src/main.rs').write_text(harness.replace('use anyhow::','extern crate self as minime;\npub mod esn; pub mod gpu; pub mod buffer_pool;\nuse anyhow::',1))
    shutil.rmtree(stage/'src/bin')
    target=stage/'target'
    if args.seed_target and not target.exists():
        # Dependency reuse is isolated; changed source identity is embedded and audited.
        shutil.copytree(args.seed_target,target)
    env=dict(os.environ,CARGO_TARGET_DIR=str(target),STATE_ACTION_SOURCE_SHA256=identity)
    result={'source_identity':identity,'files':files,'stage':str(stage),'started_at_utc':now(),
      'scope':'Standalone compile of exact native modules plus the owning-repository rehearsal binary; excludes surrounding runtime.',
      'build_probe_sha256':sha(Path(__file__))}
    manifest=root/'candidate-build-manifest.json'; log=root/'candidate-build.log'
    if manifest.exists():
        prior=json.loads(manifest.read_text()); suffix=prior['source_identity'][:16]
        shutil.copyfile(manifest,root/('candidate-build-'+suffix+'.json'))
        if log.exists(): shutil.copyfile(log,root/('candidate-build-'+suffix+'.log'))
    save(manifest,result)
    with log.open('w') as stream:
        try:
            completed=subprocess.run(['cargo','+1.94.1','build','--release','--offline','--features','division-rehearsal'],cwd=stage,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=1200)
            result['exit_code']=completed.returncode
        except subprocess.TimeoutExpired:
            result['exit_code']=124; result['failure']='bounded compile timeout; no numerical execution'
    result['finished_at_utc']=now()
    if result['exit_code']==0:
        binary=target/'release/native-state-action-replay'
        result.update(binary=str(binary),binary_sha256=sha(binary))
        shutil.copyfile(stage/'Cargo.lock',root/'candidate.Cargo.lock')
    save(manifest,result); print(json.dumps(result,indent=2)); return result['exit_code']

if __name__=='__main__': raise SystemExit(main())
