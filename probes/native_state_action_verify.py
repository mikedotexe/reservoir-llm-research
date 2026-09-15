#!/usr/bin/env python3
"""Audit retained native action evidence without running an engine or live I/O.

Uses the independently reviewed float/integer comparison from async qualification.
Recomputes coordinate, operation, identity and protocol relationships separately
from the Rust producer and Swift consumer; source hashes are not authenticity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from native_async_verify import clean_snapshot, expect, f32, first_diff, read, sha


def rounded(value):
    return struct.unpack('<f', f32(value))[0]


def model_identity(snapshot):
    model = hashlib.sha256(b'minime-native-model-f32-v1\0')
    model.update(struct.pack('<QQ', snapshot['res_size'], snapshot['in_size']))
    for value in snapshot['win'] + snapshot['wres']:
        model.update(f32(value))
    layout = hashlib.sha256(b'minime-native-index-layout-v1\0')
    layout.update(struct.pack('<Q', snapshot['res_size']))
    for index in range(snapshot['res_size']):
        layout.update(struct.pack('<Q', index))
    return model.hexdigest(), layout.hexdigest()


def direction_hash(direction):
    result = hashlib.sha256(b'native-state-direction-f32-v1\0')
    result.update(struct.pack('<Q', len(direction)))
    for value in direction:
        result.update(f32(value))
    return result.hexdigest()


def audit(root: Path, run: Path):
    baseline = read(root / 'baseline/baseline.json')
    baseline_run = read(root / 'baseline-run.json')
    build = read(root / 'candidate-build-manifest.json')
    execution = read(run / 'execution.json')
    summary = read(run / 'summary.json')
    protocol = read(root / 'rehearsal-protocol.json')
    expect(baseline_run['exit_code'] == build['exit_code'] == execution['exit_code'] == 0,
           'build/execution success missing')
    expect(sha(root / 'baseline/baseline.json') == baseline_run['baseline_sha256'] == summary['source_hashes']['reference_fixture'], 'reference bytes changed')
    expect(execution['protocol_sha256'] == sha(root / 'rehearsal-protocol.json'), 'executed protocol identity')
    expect(execution['binary_sha256'] == build['binary_sha256'] == summary['source_hashes']['executable'], 'executed binary identity')
    expect(build['source_identity'] == summary['source_hashes']['implementation_sources'], 'compiled source identity')
    expect(hashlib.sha256(json.dumps(build['files'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
           == build['source_identity'], 'source manifest digest')
    stage = Path(build['stage'])
    for record in build['files']:
        if record['path'].startswith('src/bin/'):
            harness = (stage / 'src/main.rs').read_text().replace('extern crate self as minime;\npub mod esn; pub mod gpu; pub mod buffer_pool;\n', '', 1)
            expect(hashlib.sha256(harness.encode()).hexdigest() == record['sha256'], 'compiled harness differs from owning replay source')
            continue
        if record['path'] == 'Cargo.lock':
            continue
        expect(sha(stage / record['path']) == record['sha256'], 'frozen source bytes changed: ' + record['path'])
    expect(sha(Path(build['binary'])) == build['binary_sha256'], 'retained executable changed')
    ordinary = read(run / 'ordinary-results.json')
    expected_keys = {(start, alternating) for start in protocol['starts'] for alternating in [False, True]}
    references = {(row['start'], row['alternating_rho']): row for row in baseline['cases']}
    actual = {(row['start'], row['alternating_rho']): row for row in ordinary}
    expect(len(ordinary) == len(actual) == len(references) == 6 and set(actual) == set(references) == expected_keys,
           'six unique ordinary comparisons required')
    for key, row in actual.items():
        ref = references[key]
        expect(row['passed'] is True, 'ordinary case did not pass')
        expect(len(row['path']) == 101 and len(row['traces']) == 100, 'ordinary horizon')
        expect(first_diff(row['path'], ref['path']) is None, 'ordinary state bits changed')
        expect(first_diff(row['traces'], ref['traces']) is None, 'ordinary noise/leak bits changed')
        expect(first_diff(clean_snapshot(row['final_snapshot']), clean_snapshot(ref['final_snapshot'])) is None,
               'ordinary complete numerical checkpoint changed')
        expect(first_diff(row['path'][-1], row['final_snapshot']['state']) is None, 'ordinary final state link')
    expected_steps = {'one_shot':[1], 'finite':list(range(1,9)), 'sparse':[1,4,8], 'cancel':[1,2],
                      'expired':[], 'suspended':[3], 'zero':[]}
    rows = summary['action_cases']
    expect(len(rows) == 21 and {(v['start'],v['scenario']) for v in rows} ==
           {(start,name) for start in protocol['starts'] for name in protocol['scenarios']}, 'action protocol coverage')
    applied_count = 0
    no_op_count = 0
    case_hashes = {}
    waits = []
    for index in rows:
        path = run / index['path']
        expect(path.resolve().parent == run.resolve(), 'case path escaped bundle')
        row = read(path)
        case_hashes[path.name] = sha(path)
        start, scenario = row['start'], row['scenario']
        expect((start,scenario) == (index['start'],index['scenario']) and row['passed'] is True, 'case identity')
        expect(row['duplicate']['status'] == 'duplicate', 'identical native command was not deduplicated')
        expect(len(row['frames']) == 20, 'action horizon')
        model, layout = model_identity(references[start,False]['checkpoint'])
        identity = row['identity']
        expect(identity['model_id'] == model and identity['node_layout_id'] == layout and identity['node_count'] == 128,
               'model/coordinate identity is not derived from native data')
        for ordinal, frame in enumerate(row['frames'], 1):
            expect(type(frame['successful_step_id']) is int and frame['successful_step_id'] == ordinal, 'successful step order')
            expect(first_diff(frame['input'], references[start,False]['inputs'][ordinal-1]) is None, 'input schedule changed')
            expect(len(frame['state']) == len(frame['trace']['noise']) == 128, 'native state/noise shape')
            for value in frame['state'] + frame['trace']['noise']:
                f32(value)
        applications = [r for r in row['receipts'] if r['status'] == 'applied']
        expect([r['successful_step_id'] for r in applications] == expected_steps[scenario], 'gesture applied at wrong boundaries')
        expect(row['applications'] == index['applications'] == len(applications), 'application count')
        expect(row['receipts'][0]['status'] == 'accepted', 'missing admission event')
        terminal = 'cancelled' if scenario == 'cancel' else 'expired' if scenario == 'expired' else 'completed'
        expect(row['receipts'][-1]['status'] == terminal, 'missing terminal event')
        if scenario == 'one_shot':
            expect(row['later_continuation_verified'] is True, 'actual result did not feed later native dynamics')
        for receipt in row['receipts']:
            expect(receipt['identity'] == identity, 'receipt changed native identity')
            expect(direction_hash(receipt['direction']) == receipt['pattern_sha256'], 'direction hash')
            expect(abs(math.sqrt(sum(v*v for v in receipt['direction'])) - 1.0) <= 1e-5, 'nonunit direction')
            if receipt['status'] not in ('applied','no_op'):
                continue
            frame = row['frames'][receipt['successful_step_id']-1]
            before, after, delta = receipt['before'], receipt['after'], receipt['delta']
            expect(len(before) == len(after) == len(delta) == 128, 'application shape')
            expect(first_diff(after,frame['state']) is None, 'receipt is not actual native result')
            expect(first_diff(receipt['realized_noise'],frame['trace']['noise']) is None, 'receipt noise not step noise')
            expect(f32(receipt['effective_leak']) == f32(frame['trace']['leak']), 'receipt leak not step leak')
            factor = rounded(receipt['attenuation'] * receipt['requested_amount'])
            for x,y,d,direction in zip(before,after,delta,receipt['direction']):
                expected = rounded(x + rounded(factor * direction))
                expected = min(1.0,max(-1.0,expected))
                expect(f32(y) == f32(expected), 'actual state is not the declared direct operation')
                expect(f32(y-x) == f32(d), 'actual Float32 delta mismatch')
            length = math.sqrt(sum(d*d for d in delta))
            expect(abs(length-receipt['actual_l2']) <= 1e-12, 'full-state displacement norm')
            expect(max(map(abs,delta)) == receipt['max_abs_delta'], 'largest coordinate delta')
            expect((length > 0) == (receipt['status'] == 'applied'), 'zero effect reported applied')
            waits.append(receipt['boundary_wait_us'])
            applied_count += receipt['status'] == 'applied'
            no_op_count += receipt['status'] == 'no_op'
        expect(first_diff(row['frames'][-1]['state'],row['final_snapshot']['state']) is None, 'final action state link')
    wrapper = read(run / 'native-action-response.json')
    expect(wrapper['schema'] == 'research.native_action_response.v1' and wrapper['fill'] is None
           and wrapper['reference_basis'] is None, 'viewer evidence scope')
    expect(wrapper['clock'] == 'successful native step ids; supplied rehearsal clock is not measured wall time', 'clock provenance')
    chosen = read(run / 'native-96-finite.json')
    expect(first_diff(wrapper['receipts'],chosen['receipts']) is None, 'viewer example was not the selected native run')
    expect(wrapper['source_hashes'] == summary['source_hashes'], 'viewer source identity')
    return {'schema':'research.native_state_actions.verification.v1', 'audit_passed':True,
            'ordinary_cases':6, 'ordinary_steps':600, 'action_cases':21, 'action_steps':420,
            'actual_applications':applied_count, 'zero_effect_receipts':no_op_count,
            'source_identity':build['source_identity'], 'binary_sha256':build['binary_sha256'],
            'case_sha256':case_hashes, 'viewer_sha256':sha(run/'native-action-response.json'),
            'boundary_wait_us':{'count':len(waits),'minimum':min(waits),'maximum':max(waits)},
            'verifier_sha256':sha(Path(__file__)), 'async_verifier_helpers_sha256':sha(Path(__file__).with_name('native_async_verify.py')),
            'limits':'Native deterministic-clock experiment; no live or controller replay and no general performance claim.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--run',type=Path,required=True)
    args=parser.parse_args()
    result=audit(args.root,args.run)
    (args.run/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='case_sha256'},indent=2))


if __name__=='__main__':main()
