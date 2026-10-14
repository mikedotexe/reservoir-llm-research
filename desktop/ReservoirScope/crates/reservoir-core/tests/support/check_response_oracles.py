"""Compare unchanged Swift response readers with Rust; never contact live sources."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('swift-oracle', 'rust-oracle', 'receipt'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--resources', type=Path)
    a = p.parse_args()
    if a.receipt.exists():
        raise SystemExit('Refusing to overwrite historical receipt')
    crate = Path(__file__).resolve().parents[2]
    repo = crate.parents[3]
    resources = a.resources or repo / 'desktop/ReservoirScope/src-tauri/resources'
    native = resources / 'native-action-response.json'
    simulation = resources / 'state-response.json'
    binaries = [a.swift_oracle.resolve(), a.rust_oracle.resolve()]
    sources = [repo / 'native/ReservoirScope/Sources/ReservoirScope/NativeActionResponse.swift',
               repo / 'native/ReservoirScope/Sources/ReservoirScope/StateResponseExperience.swift',
               crate / 'src/response.rs', crate / 'examples/response_oracle.rs',
               Path(__file__), Path(__file__).with_name('response_oracle.swift')]
    receipt = {'schema': 'reservoir-response-conformance-v1', 'createdAtUTC': datetime.now(timezone.utc).isoformat(),
               'scope': 'All retained response coordinates, declared scales, boundaries and reader/replacement rejections; no rerun of native dynamics or simulated model',
               'modelsContacted': False, 'liveSourcesRead': False, 'outcome': 'incomplete', 'checks': [],
               'sources': [{'path': str(x.relative_to(repo)), 'sha256': sha(x.read_bytes())} for x in sources],
               'executables': [{'path': str(x), 'sha256': sha(x.read_bytes())} for x in binaries],
               'resources': [{'name': x.name, 'sha256': sha(x.read_bytes())} for x in (native, simulation)]}

    def check(name, mode, file, extra=None, rejected=False):
        runs = []
        for binary in binaries:
            command = [str(binary), mode, str(file)] + ([str(extra)] if extra is not None else [])
            r = subprocess.run(command, capture_output=True, timeout=30)
            runs.append(r)
        passed = all(r.returncode == 1 for r in runs) if rejected else all(r.returncode == 0 for r in runs) and json.loads(runs[0].stdout) == json.loads(runs[1].stdout)
        entry = {'name': name, 'passed': passed, 'expected': 'reject' if rejected else 'identical decoded evidence',
                 'inputSha256': sha(file.read_bytes()), 'runs': [{'exitCode': r.returncode, 'stdoutSha256': sha(r.stdout), 'stderr': r.stderr.decode(errors='replace')[:1000]} for r in runs]}
        if not rejected and runs[1].returncode == 0:
            decoded = json.loads(runs[1].stdout)
            entry['counts'] = {k:v for k,v in decoded.items() if k.endswith('Count')}
        receipt['checks'].append(entry)

    try:
        check('canonical-native-all-values', 'native', native)
        check('canonical-simulation-all-values', 'simulation', simulation)
        check('unchanged-native-replacement', 'native', native, native)
        with tempfile.TemporaryDirectory(prefix='reservoir-response-conformance-') as tmp:
            root = Path(tmp)
            n = json.loads(native.read_bytes()); s = json.loads(simulation.read_bytes())
            def encoded(name, value):
                file = root / (name + '.json'); file.write_text(json.dumps(value, ensure_ascii=False)); return file
            # All native clocks/step ids must survive beyond JavaScript's exact integer range.
            wide = deepcopy(n)
            for r in wide['receipts']:
                r['observed_at_unix_ms'] = 18446744073709551615
                if r.get('successful_step_id') is not None: r['successful_step_id'] += 9007199254740992
                if r.get('boundary_wait_us') is not None: r['boundary_wait_us'] = 18446744073709551615
            check('native-wide-integers', 'native', encoded('wide',wide))
            for label, token in [('decimal', '18446744073709551615.0'), ('exponent', '18446744073709551615e0')]:
                raw=json.dumps(wide).replace('18446744073709551615',token)
                file=root / ('wide-'+label+'.json');file.write_text(raw)
                check('native-wide-'+label,'native',file,rejected=True)
            for label, value in [('above-js-safe',9007199254740993),('above-signed-range',9223372036854775808),('largest-floating-safe',18446744073709549568)]:
                v=deepcopy(n)
                for r in v['receipts']: r['observed_at_unix_ms']=value
                file=root / (label+'.json');file.write_text(json.dumps(v).replace(str(value),str(value)+'.0'))
                check('native-integral-decimal-'+label,'native',file)
            mutations = {
                'unmeasured-fill': lambda v: v.update(fill=68),
                'unverified-basis': lambda v: v.update(reference_basis='invented PCA'),
                'live-relabel': lambda v: v.update(subject='live Minime'),
                'empty-receipts': lambda v: v.update(receipts=[]),
                'incorrect-delta': lambda v: v['receipts'][1]['delta'].__setitem__(0,0.5),
                'incorrect-l2': lambda v: v['receipts'][1].update(actual_l2=1),
                'incorrect-maximum': lambda v: v['receipts'][1].update(max_abs_delta=1),
                'missing-noise': lambda v: v['receipts'][1].pop('realized_noise'),
                'failed-step-with-state': lambda v: v['receipts'][1].update(status='step_failed'),
                'no-op-with-change': lambda v: v['receipts'][1].update(status='no_op'),
                'duplicate-boundary': lambda v: v['receipts'].insert(2,deepcopy(v['receipts'][1])),
                'reverse-step': lambda v: v['receipts'][2].update(successful_step_id=1),
                'overflow-direction': lambda v: v['receipts'][0]['direction'].__setitem__(0,1e40),
                'unknown-wrapper': lambda v: v.update(measured_seconds=2),
                'unknown-receipt': lambda v: v['receipts'][1].update(fill=68),
            }
            for name, mutate in mutations.items():
                v=deepcopy(n); mutate(v); check(name,'native',encoded(name,v),rejected=True)
            for name, mutate in {
                'changed-overlap': lambda v: v['receipts'][1].update(observed_at_unix_ms=v['receipts'][1]['observed_at_unix_ms']+1),
                'older-complete-batch': lambda v: v.update(receipts=v['receipts'][:3]),
                'changed-source': lambda v: v.update(source_hashes={'esn_rs':'a'*64}),
            }.items():
                v=deepcopy(n); mutate(v); check(name,'native',encoded(name,v),native,rejected=True)
            new=deepcopy(n)
            for r in new['receipts']: r['identity']['engine_session_id']='different-isolated-session'
            check('new-session-separate-replacement','native',encoded('new-session',new),native)
            previous=deepcopy(n)
            for r in previous['receipts']: r['identity']['engine_session_id']='session-café'
            prior=encoded('unicode-session-prior',previous)
            changed=deepcopy(previous)
            for r in changed['receipts']: r['identity']['engine_session_id']='session-cafe\u0301'
            changed['source_hashes']={k:'a'*64 for k in changed['source_hashes']}
            check('canonical-session-cannot-bypass-source-identity','native',encoded('unicode-session-next',changed),prior,rejected=True)
            previous=deepcopy(n)
            for r in previous['receipts']: r['command_id']='command-café'
            prior=encoded('unicode-command-prior',previous)
            changed=deepcopy(previous)
            for r in changed['receipts']: r['command_id']='command-cafe\u0301'
            changed['receipts'][1]['reason']='changed-boundary'
            check('canonical-command-cannot-bypass-immutable-boundary','native',encoded('unicode-command-next',changed),prior,rejected=True)
            previous=deepcopy(n);previous['receipts'][1]['reason']='café'
            prior=encoded('unicode-reason-prior',previous)
            changed=deepcopy(previous);changed['receipts'][1]['reason']='cafe\u0301'
            check('canonically-equivalent-receipt-reason','native',encoded('unicode-reason-next',changed),prior)
            changed=deepcopy(n)
            for i,r in enumerate(changed['receipts']): r['identity']['engine_session_id']='session-café' if i%2 else 'session-cafe\u0301'
            check('canonical-identity-across-boundaries','native',encoded('unicode-within-bundle',changed))
            for name, mutate in {
                'simulation-fill': lambda v:v.update(fill=68),
                'simulation-clock':lambda v:v.update(clock='measured seconds'),
                'simulation-delta':lambda v:v['frames'][1]['delta'].__setitem__(0,0.01),
                'simulation-distance':lambda v:v['frames'][1].update(separation_l2=1),
                'simulation-boundary':lambda v:v['frames'][1].update(original_boundary_step=205),
                'simulation-return':lambda v:v['result_summary'].update(return_boundary=1),
                'simulation-peak':lambda v:v['result_summary'].update(peak_gain_over_initial=2),
            }.items():
                v=deepcopy(s); mutate(v); file=encoded(name,v)
                # Rebind the identity solely in this test to exercise semantic validation.
                check(name,'simulation',file,sha(file.read_bytes()),rejected=True)
            altered=encoded('different-original-bytes',s)
            check('simulation-original-hash','simulation',altered,rejected=True)
        receipt['outcome']='passed' if all(c['passed'] for c in receipt['checks']) else 'failed'
    finally:
        a.receipt.parent.mkdir(parents=True,exist_ok=True)
        with a.receipt.open('x') as f: json.dump(receipt,f,indent=2); f.write('\n')
    print(json.dumps({'outcome':receipt['outcome'],'checks':len(receipt['checks']),'failed':[c['name'] for c in receipt['checks'] if not c['passed']],'receipt':str(a.receipt)}))
    raise SystemExit(0 if receipt['outcome']=='passed' else 1)

if __name__=='__main__': main()
