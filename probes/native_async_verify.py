#!/usr/bin/env python3
"""Independent retained-evidence audit for finite native async replay experiments.

This never launches an ESN, reads sibling source, or samples live systems. A
failed experimental parity gate is valid evidence and does not fail this audit;
missing/corrupt evidence or a disagreement with reported results does.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import tomllib


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    def reject(value):
        raise ValueError(f"Nonfinite JSON constant in {path}: {value}")
    def finite_float(value):
        result = float(value)
        return result if math.isfinite(result) else reject(value)
    return json.loads(path.read_text(), parse_constant=reject, parse_float=finite_float)


def f32(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Expected finite f32, got {value!r}")
    packed = struct.pack('<f', value)
    if not math.isfinite(struct.unpack('<f', packed)[0]):
        raise ValueError("Finite JSON number overflows f32")
    return packed


def first_diff(a, b, path='$'):
    """Preserve integer identity and signed float zero; do not coerce u64 to f64."""
    if isinstance(a, float) and isinstance(b, float):
        return None if f32(a) == f32(b) else {'path': path, 'left': a, 'right': b}
    if type(a) is not type(b):
        return {'path': path, 'left': a, 'right': b, 'reason': 'type mismatch'}
    if isinstance(a, dict):
        if set(a) != set(b):
            return {'path': path, 'left_keys': sorted(a), 'right_keys': sorted(b)}
        for key in sorted(a):
            found = first_diff(a[key], b[key], path + '.' + key)
            if found is not None:
                return found
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return {'path': path, 'left_length': len(a), 'right_length': len(b)}
        for i, (left, right) in enumerate(zip(a, b)):
            found = first_diff(left, right, f'{path}[{i}]')
            if found is not None:
                return found
        return None
    return None if a == b else {'path': path, 'left': a, 'right': b}


def numeric_max(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return 0. if a is b else math.inf
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a-b)
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return max((numeric_max(x, y) for x, y in zip(a, b)), default=0.)
    if isinstance(a, dict) and isinstance(b, dict) and set(a) == set(b):
        return max((numeric_max(a[k], b[k]) for k in a), default=0.)
    return 0. if a == b else math.inf


def clean_snapshot(value, omit_rng=False):
    value = copy.deepcopy(value)
    # Only the documented wall/profile diagnostics are excluded. Measurement
    # enable flags, estimator policy, counters, weights and adaptation stay in.
    value['spectral'].pop('last_profile')
    if omit_rng:
        value.pop('rng_state')
    return value


def expect(condition, description):
    if not condition:
        raise ValueError(description)


def audit_case(root, protocol, row):
    tag = f"{row['mode']}-{row['start_boundary']}"
    retained = read(root / f'parity-paths-{tag}.json')
    finals = read(root / f'final-checkpoints-{tag}.json')
    checkpoint = read(root / f'checkpoint-{tag}.json')
    names = ['ordinary', 'restored', 'shadow', 'shadow_duplicate']
    expect(retained['order'] == names, f'{tag}: path order')
    paths = retained['paths']
    observations = retained['observables']
    horizon = protocol['horizon_steps']
    dimension = checkpoint['res_size']
    expect(len(paths) == len(observations) == 4, f'{tag}: four paths required')
    expect(row['horizon_steps'] == horizon, f'{tag}: horizon disagrees with protocol')
    expect(len(retained['forcing']) == len(retained['inputs']) == horizon,
           f'{tag}: forcing/input horizon')
    expect(set(finals) == set(names), f'{tag}: four final snapshots required')
    for path, obs, name in zip(paths, observations, names):
        expect(len(path) == len(obs) == horizon + 1, f'{tag}: {name} path horizon')
        expect(all(len(state) == dimension for state in path), f'{tag}: state dimension')
        for state in path:
            for value in state:
                f32(value)
        expect(first_diff(path[0], checkpoint['state']) is None, f'{tag}: initial checkpoint state')
        expect(first_diff(path[-1], finals[name]['state']) is None, f'{tag}: final state link')
    for trace in retained['forcing']:
        expect(len(trace['noise']) == dimension, f'{tag}: forcing noise dimension')
        for number in trace['noise']:
            f32(number)
        f32(trace['leak'])
    pairs = [('ordinary_restored', 0, 1), ('ordinary_shadow', 0, 2), ('shadow_duplicate', 2, 3)]
    comparisons = {}
    for label, left, right in pairs:
        diff = first_diff(paths[left], paths[right])
        error = numeric_max(paths[left], paths[right])
        expect(error == row[label + '_state_max_abs'], f'{tag}: {label} state error report')
        comparisons[label] = {'state_bits_exact': diff is None, 'first_state_difference': diff,
                              'state_max_abs': error,
                              'first_observable_difference': first_diff(observations[left], observations[right])}
    all_bits = all(item['state_bits_exact'] for item in comparisons.values())
    expect(all_bits == row['all_state_paths_bit_identical'], f'{tag}: f32 bit identity report')
    cleaned = {name: clean_snapshot(finals[name]) for name in names}
    snapshot_comparisons = [
        ('ordinary_restored', cleaned['ordinary'], cleaned['restored'], 'final_snapshot_numeric_max_abs'),
        ('ordinary_shadow', clean_snapshot(finals['ordinary'], True), clean_snapshot(finals['shadow'], True),
         'final_shadow_snapshot_numeric_max_abs_excluding_rng'),
        ('shadow_duplicate', cleaned['shadow'], cleaned['shadow_duplicate'], 'final_duplicate_snapshot_numeric_max_abs')]
    for label, left, right, error_key in snapshot_comparisons:
        diff = first_diff(left, right)
        error = numeric_max(left, right)
        expect(error == row[error_key], f'{tag}: {label} final snapshot error report')
        comparisons[label].update({'snapshot_bits_exact': diff is None,
                                  'first_snapshot_difference': diff,
                                  'snapshot_numeric_max_abs': error})
    covariance_error = numeric_max(finals['ordinary']['spectral']['covariance'],
                                   finals['restored']['spectral']['covariance'])
    expect(covariance_error == row['final_covariance_max_abs'], f'{tag}: covariance error report')
    leak_error = max(abs(a['effective_leak_last_step']-b['effective_leak_last_step'])
                     for a, b in zip(observations[0][1:], observations[1][1:]))
    expect(leak_error == row['effective_leak_max_abs'], f'{tag}: effective leak error report')
    # Traces are optional in the original rehearsal schema. Do not pretend that
    # the parent's forcing alone verifies the restored copy's realized noise.
    noise_verified = False
    if 'traces' in retained or 'copy_forcing' in retained:
        traces = retained.get('traces', retained.get('copy_forcing'))
        expect(len(traces) == 4 and all(len(items) == horizon for items in traces), f'{tag}: trace shape')
        for copy_traces in traces:
            for trace in copy_traces:
                expect(len(trace['noise']) == dimension, f'{tag}: per-copy noise dimension')
                f32(trace['leak'])
                for number in trace['noise']:
                    f32(number)
        noise_error = max(numeric_max(a['noise'], b['noise']) for a, b in zip(traces[0], traces[1]))
        expect(noise_error == row['realized_noise_max_abs'], f'{tag}: realized noise error report')
        expect(first_diff(traces[0], retained['forcing']) is None, f'{tag}: forcing/parent trace identity')
        noise_verified = True
    profile_summary = None
    if 'profiles' in retained:
        profiles = retained['profiles']
        expect(len(profiles) == 4 and all(len(items) == horizon for items in profiles), f'{tag}: profile shape')
        flat = [item for items in profiles for item in items]
        profile_summary = {
            'async_submissions': sum(item['async_rank1_submitted'] is True for item in flat),
            'boundaries_with_pending_rank1': sum(item['pending_rank1_depth'] > 0 for item in flat),
            'max_pending_depth': max(item['pending_rank1_depth'] for item in flat)}
        for key, value in profile_summary.items():
            expect(value == row[key], f'{tag}: {key} profile count')
    independently_passed = all_bits and all(item['snapshot_bits_exact'] for item in comparisons.values())
    independently_passed &= leak_error == 0. and row['realized_noise_max_abs'] == 0.
    expect(independently_passed == row['passed'], f'{tag}: complete parity result')
    return {'case': tag, 'passed': independently_passed, 'comparisons': comparisons,
            'effective_leak_max_abs': leak_error, 'noise_recomputed_from_all_traces': noise_verified,
            'ordinary_restored_rng_exact': finals['ordinary']['rng_state'] == finals['restored']['rng_state'],
            'async_profiles': profile_summary}


def audit_rho_case(root, protocol, row):
    tag = f"{row['schedule']}-{row['start_boundary']}"
    retained = read(root / f'rho-paths-{tag}.json')
    finals = read(root / f'rho-final-checkpoints-{tag}.json')
    names = ['async_a', 'async_b', 'synchronous_reference']
    expect(retained['order'] == names and set(finals) == set(names), f'{tag}: rho copy ordering')
    expect(protocol['rho_qualification']['snapshot_exclusions'] == [
        'spectral.last_profile', 'spectral.profiling_enabled', 'spectral.async_measurement_enabled'],
        f'{tag}: unexpected rho snapshot exclusions')
    common = read(root.parent.parent / 'inputs' / f"checkpoint-asynchronous_default-{row['start_boundary']}.json")
    horizon, dimension = protocol['horizon_steps'], common['res_size']
    expect(row['horizon_steps'] == horizon, f'{tag}: rho horizon')
    paths, traces, profiles = retained['paths'], retained['copy_forcing'], retained['profiles']
    expect(len(paths) == len(traces) == len(profiles) == len(retained['observables']) == len(retained['rho_schedule']) == 3,
           f'{tag}: three rho trajectories required')
    expect(len(retained['inputs']) == horizon, f'{tag}: rho input horizon')
    snapshots = []
    for i, name in enumerate(names):
        expect(len(paths[i]) == len(retained['observables'][i]) == horizon+1, f'{tag}: rho path length')
        expect(len(traces[i]) == len(profiles[i]) == len(retained['rho_schedule'][i]) == horizon, f'{tag}: rho trace length')
        expect(all(len(state) == dimension for state in paths[i]), f'{tag}: rho state dimension')
        expect(first_diff(paths[i][0], common['state']) is None, f'{tag}: retained rho checkpoint state')
        expect(first_diff(paths[i][-1], finals[name]['state']) is None, f'{tag}: rho final snapshot link')
        for state in paths[i]:
            for value in state:
                f32(value)
        for offset, trace in enumerate(traces[i]):
            expect(len(trace['noise']) == dimension, f'{tag}: rho noise dimension')
            f32(trace['leak'])
            for number in trace['noise']:
                f32(number)
            expected_rho = common['spectral']['rho'] if row['schedule'] == 'fixed' else (0.82 if offset % 2 == 0 else 0.999)
            expect(f32(retained['rho_schedule'][i][offset]) == f32(expected_rho), f'{tag}: prescribed rho at step{offset}')
        expected_profile = name == 'synchronous_reference'
        expect(finals[name]['spectral']['profiling_enabled'] is expected_profile, f'{tag}: async/sync native mode')
        expect(finals[name]['spectral']['async_measurement_enabled'] is protocol['measurement'], f'{tag}: measurement mode')
        snapshot = clean_snapshot(finals[name])
        snapshot['spectral'].pop('profiling_enabled')
        snapshot['spectral'].pop('async_measurement_enabled')
        snapshots.append(snapshot)
    comparisons = {}
    for label, left, right in [('async_a_b', 0, 1), ('async_a_sync', 0, 2), ('async_b_sync', 1, 2)]:
        state_error = numeric_max(paths[left], paths[right])
        snapshot_error = numeric_max(snapshots[left], snapshots[right])
        expect(row['state_' + label + '_max_abs'] == state_error, f'{tag}: {label} rho state error')
        expect(row['snapshot_' + label + '_max_abs'] == snapshot_error, f'{tag}: {label} rho snapshot error')
        comparisons[label] = {'state_bits_exact': first_diff(paths[left], paths[right]) is None,
                              'snapshot_bits_exact': first_diff(snapshots[left], snapshots[right]) is None,
                              'state_max_abs': state_error, 'snapshot_numeric_max_abs': snapshot_error,
                              'first_state_difference': first_diff(paths[left], paths[right]),
                              'first_snapshot_difference': first_diff(snapshots[left], snapshots[right]),
                              'first_observable_difference': first_diff(retained['observables'][left], retained['observables'][right])}
    noise_error = max(numeric_max(a['noise'], b['noise']) for i in [1, 2] for a, b in zip(traces[0], traces[i]))
    leak_error = max(abs(a['leak']-b['leak']) for i in [1, 2] for a, b in zip(traces[0], traces[i]))
    expect(row['realized_noise_max_abs'] == noise_error and row['effective_leak_max_abs'] == leak_error,
           f'{tag}: rho noise/effective leak arithmetic')
    flat = profiles[0] + profiles[1]
    counts = {'async_submissions': sum(item['async_rank1_submitted'] is True for item in flat),
              'boundaries_with_pending_rank1': sum(item['pending_rank1_depth'] > 0 for item in flat),
              'max_pending_depth': max(item['pending_rank1_depth'] for item in flat)}
    expect(all(row[key] == value for key, value in counts.items()), f'{tag}: rho async profile counts')
    expect(all(item['pending_rank1_depth'] == 0 for item in profiles[2]), f'{tag}: synchronous reference pending work')
    exact = all(item['state_bits_exact'] and item['snapshot_bits_exact'] for item in comparisons.values())
    expect(row['all_states_and_numerical_snapshots_exact'] is exact, f'{tag}: rho bit identity report')
    passed = exact and noise_error == 0. and leak_error == 0.
    expect(row['passed'] is passed, f'{tag}: full rho gate')
    return {'case': tag, 'passed': passed, 'comparisons': comparisons,
            'effective_leak_max_abs': leak_error, 'realized_noise_max_abs': noise_error, 'async_profiles': counts}


def audit_run(root):
    protocol_path = root / 'run-protocol.json' if (root / 'run-protocol.json').exists() else root / 'protocol.json'
    protocol = read(protocol_path)
    results = read(root / 'results.json')
    rows = results.get('cases', results.get('parity'))
    expect(isinstance(rows, list), f'{root}: missing case list')
    expected = {(mode, start) for mode in protocol['parity_modes']
                for start in protocol['checkpoint_successful_boundaries']}
    actual = [(row['mode'], row['start_boundary']) for row in rows]
    expect(len(actual) == len(set(actual)) and set(actual) == expected,
           f'{root}: missing, duplicated or additional protocol case')
    cases = [audit_case(root, protocol, row) for row in rows]
    rho_rows = results.get('rho_cases', [])
    expected_rho = {(schedule, start) for schedule in ['fixed', 'alternating']
                    for start in protocol['checkpoint_successful_boundaries']} if protocol.get('stage') == 'qualification' else set()
    actual_rho = [(row['schedule'], row['start_boundary']) for row in rho_rows]
    expect(len(actual_rho) == len(set(actual_rho)) and set(actual_rho) == expected_rho, f'{root}: rho schedule coverage')
    rho_cases = [audit_rho_case(root, protocol, row) for row in rho_rows]
    if 'summary' in results:
        expect(results['summary']['cases'] == len(cases), f'{root}: summary denominator')
        expect(results['summary']['passed'] == sum(row['passed'] for row in cases), f'{root}: summary passed count')
        if 'rho_cases' in results['summary']:
            expect(results['summary']['rho_cases'] == len(rho_cases), f'{root}: rho summary denominator')
            expect(results['summary']['rho_passed'] == sum(row['passed'] for row in rho_cases), f'{root}: rho summary passed count')
    return {'directory': str(root), 'protocol_sha256': sha(protocol_path),
            'result_sha256': sha(root / 'results.json'),
            'cases': cases, 'case_count': len(cases), 'passed': sum(row['passed'] for row in cases),
            'failed': sum(not row['passed'] for row in cases), 'rho_cases': rho_cases,
            'rho_case_count': len(rho_cases), 'rho_passed': sum(row['passed'] for row in rho_cases),
            'rho_failed': sum(not row['passed'] for row in rho_cases)}


def audit_identity(root, runs):
    """Verify retained identity against frozen protocol and execution receipts."""
    protocol = read(root / 'protocol.json')
    receipt = read(root / 'execution-receipt.json')
    expect(sha(root / 'protocol.json') == receipt['protocol_sha256'], 'Top-level protocol receipt hash')
    manifest = read(root / 'source-manifest.json')
    files = {record['retained'].removeprefix('source/'): record for record in manifest['files']}
    checked = []
    for entry in protocol['checkpoints']:
        path = root / entry['retained']
        expect(sha(path) == entry['sha256'], f'Input checkpoint hash: {path}')
        checked.append(str(path.relative_to(root)))
    for variant in protocol['variants']:
        directory = root / 'variants' / variant['id']
        for relative, key in [('src/esn.rs', 'esn_sha256'), ('src/main.rs', 'harness_sha256'), ('patch.diff', 'patch_sha256')]:
            path = directory / relative
            expect(sha(path) == variant[key], f'Variant identity: {path}')
            checked.append(str(path.relative_to(root)))
        for relative in ['src/gpu.rs', 'src/buffer_pool.rs', 'shaders/esn.metal', 'shaders/spectral.metal', 'shaders/nn.metal', 'Cargo.lock']:
            path = directory / relative
            expected_hash = variant.get('gpu_sha256', files[relative]['sha256']) if relative == 'src/gpu.rs' else files[relative]['sha256']
            expect(sha(path) == expected_hash, f'Native dependency identity: {path}')
            checked.append(str(path.relative_to(root)))
    expected = []
    for repeat, order in enumerate(protocol['repeat_variant_orders']):
        expected.extend((f'primary-r{repeat}-{name}', name, repeat, False,
                         protocol['checkpoint_successful_boundaries'], protocol['horizon_steps'], False) for name in order)
    diagnostic = protocol.get('measurement_diagnostic')
    if diagnostic:
        expected.extend((f"measured-r{diagnostic['repeat']}-{name}", name, diagnostic['repeat'], True,
                         diagnostic['starts'], protocol['horizon_steps'], False) for name in diagnostic['variant_order'])
    prefix = protocol.get('prefix_diagnostic')
    if prefix:
        expected.extend((f'prefix-h{horizon}-r{repeat}-{name}', name, repeat, False,
                         prefix['starts'], horizon, True)
                        for horizon in prefix['horizons'] for repeat in range(prefix['repeats'])
                        for name in prefix['variants'])
    expect({Path(run['directory']).name for run in runs} == {row[0] for row in expected},
           'Full frozen run schedule coverage')
    run_steps = [step for step in receipt['steps'] if step.get('kind') == 'run']
    build_steps = {step['variant']: step for step in receipt['steps'] if step.get('kind') == 'build'}
    expect(len(run_steps) == len(expected), 'Execution receipt run count')
    for label, variant, repeat, measurement, starts, horizon, is_prefix in expected:
        directory = root / 'runs' / label
        job = read(directory / 'run-protocol.json')
        expected_job = {**protocol, 'variant': variant, 'repeat': repeat, 'measurement': measurement,
                        'checkpoint_successful_boundaries': starts,
                        'parity_modes': ['asynchronous_measured' if measurement else 'asynchronous_default']}
        if 'prefix_diagnostic_run' in job:
            expected_job.update(prefix_diagnostic_run=is_prefix, horizon_steps=horizon)
        if 'expected_binary_sha256' in job:
            expected_job['expected_binary_sha256'] = build_steps[variant]['binary_sha256']
        expect(job == expected_job, f'{label}: run protocol derived exactly from frozen schedule')
        matches = [step for step in run_steps if (step['variant'], step['repeat'], step['measurement'],step['results_sha256']) == (variant, repeat, measurement, sha(directory / 'results.json'))]
        expect(len(matches) == 1,
               f'{label}: result execution receipt hash')
    summary = read(root / 'summary.json')
    expect(sha(root / 'summary.json') == receipt['summary_sha256'], 'Summary execution receipt hash')
    expect(len(summary['reports']) == len(runs), 'Summary report coverage')
    for report in summary['reports']:
        raw_result = read(root / 'runs' / report['id'] / 'results.json')
        expect({key: value for key, value in report.items() if key in raw_result} == raw_result,
               f"Summary retained result link: {report['id']}")
    for name, aggregate in summary['by_variant'].items():
        cases = [case for report in summary['reports'] if report['variant'] == name and not report['measurement'] and not report.get('prefix_diagnostic_run') for case in report['cases']]
        expect(aggregate['primary_cases'] == len(cases), f'{name}: primary aggregate denominator')
        expect(aggregate['primary_exact_passed'] == sum(case['passed'] for case in cases), f'{name}: aggregate pass count')
        if 'rho_cases' in aggregate:
            rho_cases = [case for report in summary['reports'] if report['variant'] == name and not report['measurement'] and not report.get('prefix_diagnostic_run') for case in report['rho_cases']]
            expect(aggregate['rho_cases'] == len(rho_cases), f'{name}: rho aggregate denominator')
            expect(aggregate['rho_passed'] == sum(case['passed'] for case in rho_cases), f'{name}: rho aggregate pass count')
            expect(aggregate['rho_schedule_passed'] == {schedule: sum(case['passed'] for case in rho_cases if case['schedule'] == schedule) for schedule in ['fixed', 'alternating']}, f'{name}: rho schedule aggregates')
    supplement = None
    if (root / 'provenance-supplement.json').exists():
        supplement = read(root / 'provenance-supplement.json')
        expect(sha(root / supplement['runner_retained']) == supplement['runner_sha256'], 'Supplement retained runner hash')
        for lock in supplement['resolved_locks']:
            expect(sha(root / lock['retained']) == lock['sha256'], f"Resolved lock hash: {lock['variant']}")
            original = tomllib.loads((root / 'variants' / lock['variant'] / 'Cargo.lock').read_text())
            resolved = tomllib.loads((root / lock['retained']).read_text())
            packages = {(p['name'], p['version'], p.get('source'), p.get('checksum')) for p in original['package']}
            registry = [p for p in resolved['package'] if p.get('source', '').startswith('registry+')]
            expect(all((p['name'], p['version'], p.get('source'), p.get('checksum')) in packages for p in registry),
                   f"Resolved dependency differs from captured native lock: {lock['variant']}")
            lock['verified_registry_dependency_count'] = len(registry)
    return {'checked_input_and_source_files': checked, 'protocol_and_schedule_identity_passed': True,
            'execution_result_and_summary_hashes_passed': True,
            'execution_time_full_trajectory_hashes_available': 'outputs' in receipt,
            'runner_hash_available': 'runner_sha256' in receipt,
            'post_run_provenance_supplement': supplement,
            'limitations': ['Original primary receipt retains result/summary hashes, not every trajectory hash or a runner hash; audit-time hashes below establish current retained evidence identity.']
            if 'outputs' not in receipt or 'runner_sha256' not in receipt else []}


def audit_treatment_identity(root):
    protocol = read(root / 'protocol.json')
    receipt = read(root / 'execution-receipt.json')
    builds = [step for step in receipt['steps'] if step.get('kind') == 'build']
    if not receipt.get('pre_gpu_identity_gate_passed') or any('compiled_identity' not in step for step in builds):
        return {'passed': False,
                'reason': 'No complete prospective compiled-variant/source/binary identity gate. Numerical parity reports do not establish that the requested treatment executed.',
                'identical_binary_hashes': len({step['binary_sha256'] for step in builds}) < len(builds)}
    variants = {row['id']: row for row in protocol['variants']}
    expect(len(builds) == len(variants) and {row['variant'] for row in builds} == set(variants), 'Build identity coverage')
    expect(len({row['binary_sha256'] for row in builds}) == len(builds), 'Distinct treatments unexpectedly share binary bytes')
    expect(sha(root / 'retained-runner.py') == receipt['runner_sha256'] == protocol['runner_sha256'], 'Prospective runner identity')
    for build in builds:
        variant = variants[build['variant']]
        expected = {'compiled_variant': variant['id'], 'compiled_esn_sha256': variant['esn_sha256']}
        expect(build['compiled_identity'] == expected, f"Compiled source identity: {variant['id']}")
        path = root / 'variants' / variant['id'] / 'resolved-Cargo.lock'
        expect(sha(path) == build['resolved_lock_sha256'], f"Resolved build lock identity: {variant['id']}")
        captured = tomllib.loads((root / 'variants' / variant['id'] / 'Cargo.lock').read_text())
        resolved = tomllib.loads(path.read_text())
        packages = {(p['name'], p['version'], p.get('source'), p.get('checksum')) for p in captured['package']}
        expect(all((p['name'], p['version'], p.get('source'), p.get('checksum')) in packages for p in resolved['package'] if p.get('source', '').startswith('registry+')), f"Resolved registry versions/checksums: {variant['id']}")
    if all('target_directory' in build for build in builds):
        expect(len({build['target_directory'] for build in builds}) == len(builds), 'Distinct explicit Cargo target directories')
    run_checks = []
    for path in sorted((root / 'runs').glob('*/results.json')):
        result = read(path)
        job = read(path.parent / 'run-protocol.json')
        build = next(row for row in builds if row['variant'] == job['variant'])
        expect(job['expected_binary_sha256'] == build['binary_sha256'], f'{path.parent.name}: expected binary map')
        expect(result['compiled_variant'] == job['variant'], f'{path.parent.name}: executing compiled variant')
        expect(result['compiled_esn_sha256'] == variants[job['variant']]['esn_sha256'], f'{path.parent.name}: executing source SHA')
        step = next(row for row in receipt['steps'] if row.get('kind') == 'run' and row['results_sha256'] == sha(path))
        expect(step['started_at_utc'] >= receipt['pre_gpu_identity_gate_at_utc'], f'{path.parent.name}: numerical run preceded identity gate')
        if 'binary_sha256' in step:
            expect(step['binary_sha256'] == job['expected_binary_sha256'], f'{path.parent.name}: executed binary SHA')
        if 'run_protocol_sha256' in step:
            expect(step['run_protocol_sha256'] == sha(path.parent / 'run-protocol.json'), f'{path.parent.name}: execution-time run protocol identity')
        if 'binary_path' in step:
            expect(step['binary_path'] == build['binary_path'], f'{path.parent.name}: executing binary path')
        run_checks.append(path.parent.name)
    return {'passed': True, 'compile_time_variant_and_source_verified': True,
            'distinct_binary_hashes_verified': True, 'pre_gpu_gate_order_verified': True,
            'run_identity_checks': run_checks,
            'target_directory_evidence': 'Per-variant targets are constructed by the retained, hash-verified runner as build_directory/variant/target; earlier stages do not retain each target path separately.'}


def audit(root):
    directories = [root] if (root / 'results.json').exists() else sorted(
        path.parent for path in (root / 'runs').glob('*/results.json')
        if (path.parent / 'run-protocol.json').exists() or (path.parent / 'protocol.json').exists())
    expect(bool(directories), 'No completed protocol/results pairs found')
    runs = [audit_run(path) for path in directories]
    identity = audit_identity(root, runs) if (root / 'summary.json').exists() else None
    treatment = audit_treatment_identity(root) if (root / 'summary.json').exists() else None
    result = {'schema': 'research.native_async_verification.v1', 'verifier_sha256': sha(Path(__file__)),
              'root': str(root), 'runs': runs, 'run_count': len(runs),
              'case_count': sum(row['case_count'] for row in runs),
              'passed_cases': sum(row['passed'] for row in runs),
              'failed_cases': sum(row['failed'] for row in runs), 'evidence_audit_passed': True,
              'rho_case_count': sum(row['rho_case_count'] for row in runs),
              'rho_passed_cases': sum(row['rho_passed'] for row in runs),
              'rho_failed_cases': sum(row['rho_failed'] for row in runs),
              'identity': identity,
              'treatment_identity': treatment,
              'qualified_variant_comparison': treatment is not None and treatment['passed'],
              'audited_json_sha256': {str(path.relative_to(root)): sha(path)
                 for path in sorted(root.rglob('*.json'))
                 if path.name not in ['verification.json', 'verification-initial.json']
                 and (path.relative_to(root).parts[0] in ['runs', 'inputs'] or path.parent == root)},
              'meaning': 'Evidence agrees with its reports; experimental parity failures remain failures.'}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = audit(args.root.resolve())
    if args.output:
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
        (args.output.parent / ('retained-verifier-' + report['verifier_sha256'] + '.py')).write_bytes(Path(__file__).read_bytes())
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ['runs', 'identity', 'audited_json_sha256', 'treatment_identity']}, indent=2))
    if report['treatment_identity'] is not None and not report['treatment_identity']['passed']:
        raise SystemExit(1)
