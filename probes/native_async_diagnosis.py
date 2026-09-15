#!/usr/bin/env python3
"""Preregister, build and serially run bounded research-only native async ablation.

Python 3.12+, Cargo/Rust and Metal. Never runs Minime's service entry point.
Native variants and diffs are retained locally; targets use steward temp paths.
"""
from __future__ import annotations
import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'research/outputs/2026-09-07-native-shaping-rehearsal'
OUT=ROOT/'research/outputs/2026-09-07-native-async'
VARIANTS=['cov_untracked','cov_tracked','fused_fence','both']


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def now():return dt.datetime.now(dt.timezone.utc).isoformat()


def changed_source(source, tracked, fence, chain=False, drain=False, inline_rho=False):
    if tracked:
        old='let cov = gpu.new_shared((d * d * mem::size_of::<f32>()) as u64);'
        new='''// Research repair candidate: let Metal track dependencies on persistent covariance.
        let covariance_bytes = (d * d * mem::size_of::<f32>()) as u64;
        let covariance_aligned = (covariance_bytes + 16383) & !16383;
        let cov = gpu.dev.new_buffer(covariance_aligned,
            MTLResourceOptions::StorageModeShared | MTLResourceOptions::HazardTrackingModeTracked);'''
        if source.count(old)!=1:raise RuntimeError('covariance anchor mismatch')
        source=source.replace(old,new)
    if fence:
        old='''        // Encode rank1_ewma (writes cov)
        let enc = cmd.new_compute_command_encoder();
        self.encode_rank1_ewma(enc);
        enc.end_encoding();'''
        new='''        // Research ablation: explicit GPU dependency at the fused write/read boundary.
        let covariance_fence = gpu.dev.new_fence();
        let enc = cmd.new_compute_command_encoder();
        self.encode_rank1_ewma(enc);
        enc.update_fence(&covariance_fence);
        enc.end_encoding();'''
        if source.count(old)!=1:raise RuntimeError('fused rank1 anchor mismatch')
        source=source.replace(old,new)
        old='''        let enc2 = cmd.new_compute_command_encoder();
        self.encode_matvec(enc2);'''
        new='''        let enc2 = cmd.new_compute_command_encoder();
        enc2.wait_for_fence(&covariance_fence);
        self.encode_matvec(enc2);'''
        if source.count(old)!=1:raise RuntimeError('fused matvec anchor mismatch')
        source=source.replace(old,new)
    if chain:
        old='    pending_rank1: VecDeque<PendingRank1>,'
        new='''    pending_rank1: VecDeque<PendingRank1>,
    research_rank1_fence: Fence,
    research_rank1_fence_initialized: bool,'''
        if source.count(old)!=1:raise RuntimeError('chain field anchor mismatch')
        source=source.replace(old,new)
        old='            pending_rank1: VecDeque::new(),'
        new='''            pending_rank1: VecDeque::new(),
            research_rank1_fence: gpu.dev.new_fence(),
            research_rank1_fence_initialized: false,'''
        if source.count(old)!=1:raise RuntimeError('chain constructor anchor mismatch')
        source=source.replace(old,new)
        begin=source.index('    fn submit_rank1_background(')
        end=source.index('    /// GPU-accelerated rank-1 EWMA update',begin)
        function=source[begin:end]
        function=function.replace('        enc.set_compute_pipeline_state(&self.pso_rank1);','''        if self.research_rank1_fence_initialized {
            enc.wait_for_fence(&self.research_rank1_fence);
        }
        enc.set_compute_pipeline_state(&self.pso_rank1);''')
        function=function.replace('        enc.end_encoding();','''        enc.update_fence(&self.research_rank1_fence);
        enc.end_encoding();''')
        function=function.replace('        cmd.commit();','''        cmd.commit();
        self.research_rank1_fence_initialized = true;''')
        source=source[:begin]+function+source[end:]
    if drain:
        begin=source.index('    fn submit_rank1_background(')
        end=source.index('    /// GPU-accelerated rank-1 EWMA update',begin)
        function=source[begin:end]
        old='        Ok(())'
        if function.count(old)!=1:raise RuntimeError('diagnostic drain anchor mismatch')
        function=function.replace(old,'''        // Diagnostic only: same payload/pool path, immediate completion.
        self.wait_for_pending_rank1s(false)?;
        Ok(())''')
        source=source[:begin]+function+source[end:]
    if inline_rho:
        old='        enc.set_buffer(2, Some(&self.rho_buf), 0);'
        new='''        // Capture this dispatch's rho; later setters cannot rewrite an in-flight scalar.
        enc.set_bytes(2, mem::size_of::<f32>() as u64, &self.rho as *const f32 as *const _);'''
        if source.count(old)!=3:raise RuntimeError('rho encoder sites do not match expected three')
        source=source.replace(old,new)
        old='''        // Metal automatically inserts barriers between encoders in the
        // same command buffer, so the updated cov is visible to the matvec.'''
        new='''        // Covariance is a tracked buffer directly bound by both encoders.
        // Metal tracks the rank1 write -> matvec read dependency on that resource.'''
        if source.count(old)!=1:raise RuntimeError('fused dependency comment anchor mismatch')
        source=source.replace(old,new)
    return source


def prepare(output,stage='primary'):
    if (output/'protocol.json').exists():raise RuntimeError('Protocol already exists')
    output.mkdir(parents=True,exist_ok=True)
    source_manifest=json.loads((OLD/'source-manifest.json').read_text())
    for entry in source_manifest['files']:
        if sha(OLD/entry['retained'])!=entry['sha256']:raise RuntimeError('retained native source changed')
    esn_entry=next(v for v in source_manifest['files'] if v['retained']=='source/src/esn.rs')
    current=Path(esn_entry['source'])
    if sha(current)!=esn_entry['sha256']:raise RuntimeError('Current native esn source no longer matches retained source')
    inputs=output/'inputs'; inputs.mkdir()
    checkpoints=[]
    for start in [24,96,192]:
        name=f'checkpoint-asynchronous_default-{start}.json'
        shutil.copyfile(OLD/name,inputs/name)
        checkpoints.append({'boundary':start,'retained':f'inputs/{name}','sha256':sha(inputs/name)})
    source=(OLD/'source/src/esn.rs').read_text()
    variants=[]
    names=(VARIANTS if stage=='primary' else ['cov_untracked','cov_tracked','cov_tracked_rho_inline'] if stage=='qualification'
           else ['cov_untracked','chain_fence','chain_tracked','drain_diagnostic'])
    for name in names:
        target=output/'variants'/name
        shutil.copytree(OLD/'source',target)
        tracked=name in ['cov_tracked','both','chain_tracked','cov_tracked_rho_inline']
        fence=name in ['fused_fence','both','chain_fence','chain_tracked']
        chain=name in ['chain_fence','chain_tracked']
        drain=name=='drain_diagnostic'
        inline_rho=name=='cov_tracked_rho_inline'
        updated=changed_source(source,tracked,fence,chain,drain,inline_rho)
        (target/'src/esn.rs').write_text(updated)
        patch=''.join(difflib.unified_diff(source.splitlines(True),updated.splitlines(True),fromfile='native-original/src/esn.rs',tofile=f'{name}/src/esn.rs'))
        (target/'patch.diff').write_text(patch)
        gpu_original=(target/'src/gpu.rs').read_text()
        if inline_rho:
            old='''    // page-aligned pointers). HazardTrackingModeUntracked tells Metal we manage
    // barriers manually (via separate command encoders), avoiding automatic
    // hazard tracking overhead.'''
            new='''    // page-aligned pointers). HazardTrackingModeUntracked disables automatic
    // dependency tracking. Callers must encode explicit dependencies or allocate
    // tracked resources; separate encoders alone do not establish that contract.'''
            if gpu_original.count(old)!=1:raise RuntimeError('gpu dependency comment anchor mismatch')
            gpu_updated=gpu_original.replace(old,new)
            (target/'src/gpu.rs').write_text(gpu_updated)
            (target/'gpu-comment.patch.diff').write_text(''.join(difflib.unified_diff(gpu_original.splitlines(True),gpu_updated.splitlines(True),fromfile='native-original/src/gpu.rs',tofile=f'{name}/src/gpu.rs')))
        shutil.copyfile(OLD/'harness-Cargo.toml',target/'Cargo.toml')
        manifest=(target/'Cargo.toml').read_text().replace('native-shaping-rehearsal','native-async-diagnosis')
        (target/'Cargo.toml').write_text(manifest)
        shutil.copyfile(ROOT/'probes/native_async_diagnosis.rs',target/'src/main.rs')
        variants.append({'id':name,'esn_sha256':sha(target/'src/esn.rs'),'patch_sha256':sha(target/'patch.diff'),
            'harness_sha256':sha(target/'src/main.rs'), 'tracked_covariance':tracked,
            'explicit_fused_fence':fence,'explicit_background_fence_chain':chain,'immediate_drain_diagnostic_only':drain,
            'rho_captured_per_dispatch':inline_rho,'gpu_sha256':sha(target/'src/gpu.rs')})
    orders=([['cov_untracked','cov_tracked','fused_fence','both'],['fused_fence','both','cov_untracked','cov_tracked'],['both','cov_tracked','fused_fence','cov_untracked']]
            if stage=='primary' else [names,list(reversed(names)),names])
    shutil.copyfile(Path(__file__),output/'retained-runner.py')
    protocol={'schema':'research.native_async_diagnosis.protocol.v1','registered_at_utc':now(),
        'subject':'four native ESN copies restored from the same retained newly-constructed research checkpoint bytes; no live checkpoint or service',
        'source_esn_sha256':esn_entry['sha256'],'current_source_hash_verified':str(current),
        'dimensions':{'state':128,'input':66},'checkpoints':checkpoints,'variants':variants,
        'horizon_steps':100,'checkpoint_successful_boundaries':[24,96,192],
        'constructor_seed':3517018368,'checkpoint_input_dir':str(inputs),
        'forcing':'0.15f32*sin(((native_tick*7+input_index*3)as f32)*0.071f32); ordinary realized noise and alpha supplied to two shadow copies',
        'stage':stage,'runner_sha256':sha(output/'retained-runner.py'),
        'fresh_construct':stage=='qualification',
        'build_identity_gate':'separate Cargo target directory per variant; binary --identity returns compile-time variant and source hash; all compiled identities and distinct binary hashes verified before GPU runs',
        'repeat_variant_orders':orders,
        'primary_measurement_enabled':False,'profiling_enabled':False,'max_pending_rank1_unchanged':2,
        'measurement_diagnostic':{'repeat':0,'starts':[96],'variant_order':names,'async_measurement_enabled':True,'profiling_enabled':False},
        'prefix_diagnostic':({'starts':[24],'horizons':[1,2,6,7],'variants':['cov_untracked','drain_diagnostic'],'repeats':3,
            'scope':'separate terminal covariance snapshots at each finite horizon; no per-step snapshot insertion; native first introspection at boundary7'} if stage=='chain' else None),
        'rho_qualification':({'schedules':['fixed snapshot rho','alternating 0.82,0.999 each successful step'],
            'whole_trajectory_order':['async_a','async_b','synchronous_reference'],
            'snapshot_exclusions':['spectral.last_profile','spectral.profiling_enabled','spectral.async_measurement_enabled'],
            'comparison':'all states, noise, effective leak and final numerical checkpoint contents exact; complete async trajectory and final snapshot precede next trajectory; no interleaved synchronous reference',
            'capture_restore':'fresh ESN constructors warm asynchronously at24/96/192, capture JSON snapshot and continue parent/restored/two forced shadows100steps; distinct from rho retained-checkpoint comparison'} if stage=='qualification' else None),
        'parity':{'state_max_abs_tolerance':1e-6,'effective_noise_leak_tolerance':0,
            'primary_gate':'exact numerical final snapshots excluding last_profile and parent/shadow RNG; state paths exact; native ordinary noise and effective alpha exact; old tolerance errors retained'},
        'observation':'per-step CPU state/scalars/profile only; snapshots at initial and final boundaries, never per step; snapshot_v2 drains for final exact covariance',
        'finish_line':'identify whether covariance tracking or fused GPU fence restores exact asynchronous internal continuation without per-step CPU waiting; retain all failures and primary/measurement outcomes separately',
        'followup_not_in_primary':'mutable rho buffer scalar ownership under changing rho; constant rho cannot diagnose it',
        'limits':['original retained checkpoint inputs are research-created, not live','same GPU service for interleaved copies','no full surrounding controller or active readout training','not a speed benchmark']}
    save(output/'protocol.json',protocol)
    save(output/'source-manifest.json',source_manifest)
    print(json.dumps({'prepared':str(output),'protocol_sha256':sha(output/'protocol.json')}),flush=True)


def execute(command,cwd,env,log,timeout):
    proc=subprocess.run(command,cwd=cwd,env=env,capture_output=True,text=True,timeout=timeout)
    log.write_text(proc.stdout+proc.stderr)
    if proc.returncode:raise RuntimeError(f'Command failed: {command}; see {log}: {proc.stderr[-3000:]}')
    return proc


def run(output):
    p=json.loads((output/'protocol.json').read_text())
    if (output/'summary.json').exists():raise RuntimeError('Completed output exists; refuse overwrite')
    for entry in p['checkpoints']:
        if sha(output/entry['retained'])!=entry['sha256']:raise RuntimeError('checkpoint changed')
    build=Path(tempfile.mkdtemp(prefix='reservoir-native-async-'))
    env=os.environ.copy()
    receipt={'started_at_utc':now(),'protocol_sha256':sha(output/'protocol.json'),'build_directory':str(build),'steps':[],'harness_sha256':sha(ROOT/'probes/native_async_diagnosis.rs'),
        'runner_sha256':sha(Path(__file__))}
    binaries={}
    for variant in p['variants']:
        name=variant['id'];native=output/'variants'/name
        if sha(native/'src/esn.rs')!=variant['esn_sha256'] or sha(native/'src/main.rs')!=variant['harness_sha256']:raise RuntimeError('variant source changed')
        crate=build/name;shutil.copytree(native,crate)
        env['CARGO_TARGET_DIR']=str(crate/'target')
        env['RESEARCH_BUILD_VARIANT']=name
        env['RESEARCH_SOURCE_SHA256']=variant['esn_sha256']
        command=['cargo','build','--offline','--release','--features','division-rehearsal']
        begin=now();execute(command,crate,env,output/f'build-{name}.log',300)
        binary=build/f'native-async-{name}';shutil.copyfile(crate/'target/release/native-async-diagnosis',binary);binary.chmod(0o755)
        identity=json.loads(subprocess.check_output([str(binary),'--identity'],text=True,timeout=10))
        if identity!={'compiled_variant':name,'compiled_esn_sha256':variant['esn_sha256']}:raise RuntimeError('Compiled identity gate failed')
        binaries[name]=binary
        shutil.copyfile(crate/'Cargo.lock',native/'resolved-Cargo.lock')
        receipt['steps'].append({'kind':'build','variant':name,'started_at_utc':begin,'finished_at_utc':now(),'binary_sha256':sha(binary),
            'resolved_lock_sha256':sha(native/'resolved-Cargo.lock'),'crate_directory':str(crate),'target_directory':str(crate/'target'),
            'binary_path':str(binary)})
        receipt['steps'][-1]['compiled_identity']=identity
        save(output/'execution-receipt.json',receipt)
        print(f'Built {name}',flush=True)
    if len({sha(v) for v in binaries.values()})!=len(binaries):raise RuntimeError('Distinct binary identity gate failed')
    receipt['pre_gpu_identity_gate_passed']=True
    receipt['pre_gpu_identity_gate_at_utc']=now()
    save(output/'execution-receipt.json',receipt)
    schedule=[(False,repeat,name,p['checkpoint_successful_boundaries'],p['horizon_steps'],False) for repeat,order in enumerate(p['repeat_variant_orders']) for name in order]
    schedule += [(True,0,name,[96],p['horizon_steps'],False) for name in p['measurement_diagnostic']['variant_order']]
    if p.get('prefix_diagnostic'):
        d=p['prefix_diagnostic']
        schedule += [(False,repeat,name,d['starts'],horizon,True) for repeat in range(d['repeats']) for horizon in d['horizons'] for name in d['variants']]
    reports=[]
    for measurement,repeat,name,starts,horizon,prefix in schedule:
        label=f"{'prefix-h'+str(horizon) if prefix else 'measured' if measurement else 'primary'}-r{repeat}-{name}"
        destination=output/'runs'/label;destination.mkdir(parents=True)
        job={**p,'variant':name,'repeat':repeat,'measurement':measurement,'prefix_diagnostic_run':prefix,'horizon_steps':horizon,'checkpoint_successful_boundaries':starts,
            'expected_binary_sha256':sha(binaries[name]),
            'parity_modes':['asynchronous_measured' if measurement else 'asynchronous_default']}
        save(destination/'run-protocol.json',job)
        begin=now();execute([str(binaries[name]),str(destination/'run-protocol.json'),str(destination)],build,env,destination/'execution.log',120)
        report=json.loads((destination/'results.json').read_text())
        reports.append({'id':label,'prefix_diagnostic_run':prefix,**report})
        receipt['steps'].append({'kind':'run','variant':name,'repeat':repeat,'measurement':measurement,'started_at_utc':begin,'finished_at_utc':now(),'results_sha256':sha(destination/'results.json'),
            'binary_path':str(binaries[name]),'binary_sha256':sha(binaries[name]),'run_protocol_sha256':sha(destination/'run-protocol.json')})
        save(output/'execution-receipt.json',receipt)
        save(output/'progress.json',reports)
        print(label,json.dumps(report['summary']),flush=True)
    summary={'schema':'research.native_async_diagnosis.summary.v1','reports':reports,'by_variant':{}}
    for name in [v['id'] for v in p['variants']]:
        primary=[r for r in reports if r['variant']==name and not r['measurement'] and not r.get('prefix_diagnostic_run')]
        cases=[c for r in primary for c in r['cases']]
        summary['by_variant'][name]={'primary_cases':len(cases),'primary_exact_passed':sum(v['passed'] for v in cases),
            'state_max_abs':max(v['ordinary_restored_state_max_abs'] for v in cases),
            'snapshot_numeric_max_abs':max(v['final_snapshot_numeric_max_abs'] for v in cases),
            'max_pending_depth':max(v['max_pending_depth'] for v in cases)}
        rho_cases=[c for r in primary for c in r.get('rho_cases',[])]
        if rho_cases:
            summary['by_variant'][name]['rho_cases']=len(rho_cases)
            summary['by_variant'][name]['rho_passed']=sum(c['passed'] for c in rho_cases)
            summary['by_variant'][name]['rho_schedule_passed']={schedule:sum(c['passed'] for c in rho_cases if c['schedule']==schedule) for schedule in ['fixed','alternating']}
    save(output/'summary.json',summary)
    receipt['finished_at_utc']=now();receipt['summary_sha256']=sha(output/'summary.json');save(output/'execution-receipt.json',receipt)
    print(json.dumps(summary['by_variant'],indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');parser.add_argument('--output',type=Path,default=OUT)
    parser.add_argument('--stage',choices=['primary','chain','qualification'],default='primary')
    args=parser.parse_args();output=args.output.resolve()
    if not output.is_relative_to(ROOT):parser.error('Output must remain in research repository')
    prepare(output,args.stage) if args.prepare else run(output)
