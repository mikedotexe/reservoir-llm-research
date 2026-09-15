#!/usr/bin/env python3
"""Export evidence for the steward-side reservoir viewer; standard library only.

Uses an existing bounded episode capture, without touching any live database.
Optionally reads one small health snapshot and five Rust sources, read-only.
Every historical pair must share the exact engine session and timestamp; no
nearest-time matching, interpolation, controller replay, or eigenvector invention.
Outputs are restricted to this research repository. Run --help for reproduction.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

REPO = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO / 'research/outputs/2026-09-06-around-0919/source/episode-evidence.json'
MAX_INPUT_BYTES = 16 * 1024 * 1024


def utc(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def read_small(path, limit):
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError(f'Bounded read exceeded {limit} bytes: {path}')
    return raw


def number(value):
    if value is None:
        return None
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Non-finite metric')
    return round(value, 8)


def source_reference(path, raw, line):
    return {'path': str(path.resolve()), 'sha256': digest(raw), 'line': line,
            'status': 'current working source read; historical loaded binary revision unverified'}


def trace_sources(root):
    definitions = {
        'esn_geometry': ('minime/src/esn.rs', 'let radius = (norm_sq / self.res_size as f32).sqrt();'),
        'esn_covariance': ('minime/src/esn.rs', 'self.eig1 = vv_dot(&v, &y)'),
        'fill_estimator': ('minime/src/spectral/eigenfill.rs', 'pub fn update(&mut self, lambdas:'),
        'structural_pi': ('minime/src/rescue_scaffold.rs', 'let error_pct = fill_pct - STABILITY_PI_TARGET_FILL_PCT;'),
        'stage_guards': ('minime/src/rescue_overfill.rs', 'pub const HOLD_RELEASE_THRESHOLD'),
        'gate_filter_pi': ('minime/src/regulator/core/pi.rs', 'pub struct PIRegState'),
        'controller_previous_tick': ('minime/src/runtime/orchestration.rs', 'stable_core_structural_pi_output = stable_core_structural_pi.step('),
        'generic_pi_reset': ('minime/src/runtime/orchestration.rs', 'if stable_core_runtime.enabled {\n                        pi.reset();'),
    }
    result, contents = {}, {}
    for key, (relative, anchor) in definitions.items():
        path = root / relative
        if relative not in contents:
            contents[relative] = read_small(path, 1024 * 1024)
        raw = contents[relative]
        text = raw.decode()
        pos = text.find(anchor)
        if pos < 0:
            raise ValueError(f'Source anchor changed: {path}: {anchor}')
        result[key] = source_reference(path, raw, text[:pos].count('\n') + 1)
    def constant(relative, name):
        text = contents[relative].decode()
        match = re.search(r'\bconst\s+' + re.escape(name) + r'\s*:\s*f32\s*=\s*([\d.]+)\s*;', text)
        if not match:
            raise ValueError(f'Expected numeric source constant missing: {name}')
        return float(match.group(1))
    structural = 'minime/src/rescue_scaffold.rs'
    guards = 'minime/src/rescue_overfill.rs'
    cfg = {key: constant(structural, symbol) for key, symbol in {
        'target_fill_pct': 'STABILITY_PI_TARGET_FILL_PCT', 'deadband_pct': 'STABILITY_PI_DEADBAND_PCT',
        'kp': 'STABILITY_PI_KP', 'ki': 'STABILITY_PI_KI', 'max_output': 'STABILITY_PI_MAX_OUTPUT',
        'integral_decay_per_step': 'STABILITY_PI_INTEGRAL_DECAY',
    }.items()}
    bands = {key: constant(guards, symbol) for key, symbol in {
        'shelf_min_pct': 'HOLD_RELEASE_THRESHOLD', 'shelf_entry_pct': 'HOLD_ENTRY_THRESHOLD',
        'shelf_max_pct': 'ELEVATED_ENTRY_THRESHOLD', 'elevated_release_pct': 'ELEVATED_RELEASE_THRESHOLD',
        'strong_rail_pct': 'ELEVATED_STRONG_RAIL_THRESHOLD', 'force_rail_pct': 'FORCE_RAIL_THRESHOLD',
    }.items()}
    bands['target_pct'] = cfg['target_fill_pct']
    bands['status'] = 'Source-defined reference bands; historical per-tick controller mode was not captured.'
    bands['note'] = 'Shelf is a configured hold range, not a measured subjective comfort score. Actual stages have hysteresis: hold enters at 60%, releases at 58%; elevated enters at 72%, releases at 71.5%.'
    return result, cfg, bands


def historical_samples(evidence):
    tables = {'eigenvalue_timeline': {}, 'esn_metrics': {}}
    for record in evidence['records']:
        table = record['source']['locator'].get('table')
        if table not in tables or record.get('kind') != 'telemetry' or record.get('being') != 'minime':
            continue
        payload = record['payload']
        if digest(encoded(payload)) != record['source']['sha256']:
            raise ValueError('Cached record payload hash mismatch: ' + record['source_record_id'])
        key = (payload['session_id'], payload['timestamp'])
        if key in tables[table]:
            raise ValueError(f'Duplicate engine tick in {table}: {key}')
        tables[table][key] = record
    cascade = tables['eigenvalue_timeline']
    esn = tables['esn_metrics']
    if not cascade:
        raise ValueError('No Minime cascade telemetry in bounded evidence')
    samples, unmatched = [], 0
    first = min(record['occurred_at'] for record in cascade.values())
    previous = None
    for key, record in sorted(cascade.items(), key=lambda item: item[1]['occurred_at']):
        p = record['payload']
        other = esn.get(key)
        q = other['payload'] if other else {}
        if other is None:
            unmatched += 1
        if other and abs(record['occurred_at'] - other['occurred_at']) > 1e-6:
            raise ValueError('Paired engine tick has conflicting wall-time conversion')
        t = record['occurred_at']
        session = record['source']['locator']['session']
        expected = session['start_time'] + p['timestamp']
        if abs(t - expected) > 1e-6:
            raise ValueError('Invalid session-relative wall-time conversion')
        fill = p['fill_ratio'] * 100
        if not 0 <= fill <= 100:
            raise ValueError('Fill is outside estimator range')
        rate = None
        if previous and previous['session_id'] == key[0]:
            elapsed = t - previous['t']
            if elapsed <= 0:
                raise ValueError('Non-increasing sample time')
            rate = (fill - previous['fill']) / elapsed
        samples.append({
            't_utc': utc(t), 't_s': number(t - first), 'session_id': key[0],
            'fill_pct': number(fill), 'fill_rate_pct_per_s': number(rate),
            'cascade': [number(p[f'lambda{i}']) for i in (1, 2, 3)],
            'esn_cov_lambda1': number(q.get('esn_eig1')),
            'geom_radius': number(q.get('esn_geom_radius')), 'geom_rel': number(q.get('esn_geom_rel')),
            'esn_leak': number(q.get('esn_leak')), 'esn_lambda': number(q.get('esn_lambda')),
            'source_ids': [p['id'], q.get('id')],
        })
        previous = {'session_id': key[0], 't': t, 'fill': fill}
    intervals = [b['t_s'] - a['t_s'] for a, b in zip(samples, samples[1:])]
    stats = {
        'n': len(samples), 'n_cascade': len(cascade), 'n_esn': len(esn),
        'n_exact_pairs': len(samples) - unmatched, 'n_unmatched_cascade': unmatched,
        'first_t_utc': samples[0]['t_utc'], 'last_t_utc': samples[-1]['t_utc'],
        'duration_s': samples[-1]['t_s'],
        'median_interval_s': number(statistics.median(intervals)) if intervals else None,
        'min_interval_s': number(min(intervals)) if intervals else None,
        'max_interval_s': number(max(intervals)) if intervals else None,
        'fill_min_pct': min(s['fill_pct'] for s in samples), 'fill_max_pct': max(s['fill_pct'] for s in samples),
        'fill_mean_pct': number(statistics.mean(s['fill_pct'] for s in samples)),
    }
    return samples, stats


def controller_snapshot(path, cfg):
    raw = read_small(path, 1024 * 1024)
    state = json.loads(raw)
    structural = state.get('stable_core', {}).get('structural_pi', {})
    provenance = state.get('provenance', {})
    at = provenance.get('wall_clock_unix_ms')
    derived = None
    if structural.get('active') and not any(structural.get(k) for k in ['recovery_impulse_active', 'reentry_active', 'low_fill_escape_active']):
        if structural.get('error_pct') is not None and structural.get('integral') is not None:
            normal_error = min(1, max(0, (structural['error_pct'] - cfg['deadband_pct']) / 20))
            p = cfg['kp'] * normal_error
            i = cfg['ki'] * structural['integral']
            controller_fill = structural['target_fill_pct'] + structural['error_pct']
            derived = {'p_term': number(p), 'i_term': number(i),
                'pi_output': number(min(cfg['max_output'], max(0, p + i))),
                'controller_input_fill_pct': number(controller_fill),
                'snapshot_minus_controller_fill_pct': number(state.get('fill_pct', controller_fill) - controller_fill),
                'status': 'Algebraic reconstruction from recorded structural error/integral and current source constants; not logged P/I, not historical replay.',
                'units': 'P, I and output are dimensionless controller contributions; fill is percent.',
                'note': 'Current source is not proof of the loaded binary revision. Drain policy and final applied weights can override the raw PI output.'}
    return {'t_utc': utc(at / 1000) if at else None,
        'captured_at_utc': utc(datetime.now(timezone.utc).timestamp()),
        'source': {'path': str(path.resolve()), 'sha256': digest(raw), 'bytes_read': len(raw)},
        'provenance': provenance, 'observed_fill_pct': state.get('fill_pct'),
        'mode': state.get('stable_core', {}).get('controller_mode'),
        'stage': state.get('stable_core', {}).get('stage'),
        'structural_pi': structural, 'gate_filter_pi': state.get('pi'),
        'gate': state.get('gate'), 'filter': state.get('filt'), 'derived': derived,
        'note': 'One separate current snapshot. Source invokes structural PI with last_fill_pct before the next fill estimate: controller input is an earlier tick than snapshot fill. Its individual measurement timestamp is unavailable.'}


def build(args):
    raw = read_small(args.input, MAX_INPUT_BYTES)
    evidence = json.loads(raw)
    samples, stats = historical_samples(evidence)
    refs, cfg, bands = trace_sources(args.source_root)
    if args.reuse_controller_from:
        prior = json.loads(read_small(args.reuse_controller_from, MAX_INPUT_BYTES))
        snapshot = prior['controller']['snapshot']
    else:
        snapshot = controller_snapshot(args.controller_file, cfg) if args.controller_file else None
    selected_coverage = [c for c in evidence['coverage'] if c.get('being') == 'minime' and c.get('table') in ['eigenvalue_timeline', 'esn_metrics']]
    return {
        'schema_version': 1, 'kind': 'reservoir_3d_evidence',
        'subject': {'being': 'Minime', 'subsystems': ['native ESN state', 'sensory-field covariance'],
            'esn_nodes': 128, 'sensory_field_dimensions': 512,
            'note': 'Steward-side system telemetry. No language-model activation measurement or individual neuron positions.'},
        'capture': {'input_path': str(args.input.resolve()), 'input_sha256': digest(raw),
            'original_capture': evidence['capture'], 'coverage': selected_coverage,
            'selection': 'All cached telemetry rows in the previously chosen 20-minute clock window; no decimation or selection for dramatic fill.',
            'join': 'Exact equality of engine session_id and timestamp. Source IDs are [eigenvalue_timeline.id, esn_metrics.id].',
            'access': 'Reads cached evidence and optionally one bounded current health JSON; no live database access or sibling writes.'},
        'stats': stats, 'bands': bands,
        'definitions': {
            'fill_pct': '100 × recorded system fill_ratio, derived from the temporally smoothed sensory-spectrum active-rank estimator. Current source can add sensory/geometric bias outside stable-core (orchestration.rs:2552-2601); per-tick historical mode is unavailable. Not a literal fraction of neurons or memories occupied.',
            'fill_rate_pct_per_s': 'Backward difference between consecutive recorded fill samples in percentage points per second; first sample and session boundaries are null. This is not the engine-reported smoothed dfill_dt.',
            'cascade': 'First three recorded sensory-covariance direction estimates, in stored slot order. Current source uses orthonormal block-power directions and Rayleigh quotients without a final eigensolve or sort (orchestration.rs:2461-2477,2529-2531). These are not certified top-three eigenvalues or tracked eigenmodes. Other five directions and all vectors are absent here.',
            'esn_cov_lambda1': 'Top eigenvalue of native ESN state covariance; distinct from cascade λ1 and recurrent-weight spectral radius.',
            'geom_radius': 'RMS state norm sqrt(sum(x_i²)/N), with states clipped to [-1,1]. Dimensionless; no neuron coordinates.',
            'geom_rel': 'RMS state norm divided by its runtime EMA baseline.',
            'esn_leak': 'Recorded ESN leak coefficient.',
            'esn_lambda': 'Recorded RLS forgetting coefficient; not an eigenvalue.',
            't_s': 'Seconds from the first captured sample. UTC = session.start_time + engine timestamp.',
            'display_precision': 'Numeric metrics rounded to 8 decimals; cached input and record hashes preserve source evidence.',
        },
        'visual_mapping': {
            'fill_volume': 'For an illustrative unit sphere, filled radius = cbrt(fill_pct/100), so volume fraction matches estimator percentage. Reference band radii use the same transform.',
            'spectral_spokes': 'Three schematic spokes have lengths sqrt(recorded Rayleigh estimate) on a fixed scale. Their displayed directions are arbitrary. Without vectors and projected off-diagonal terms these values do not reconstruct a covariance ellipsoid.',
            'spectral_distance': 'No spectral distance metric is established in these records. A covariance amplitude or RMS radius is not a distance to a stability boundary.',
            'animation': 'Recorded sample values only. Any smooth transition between frames is display interpolation, not an observed intermediate state.',
        },
        'controller': {'historical_status': 'No controller P/I, gate/filter, stage or mode sequence was retained with this historical sample sequence.',
            'structural_config': cfg, 'snapshot': snapshot,
            'gate_filter_status': 'Current stable-core stage guards freeze and reset generic gate/filter PI integrators; the separate structural PI acts on scaffold drainage.',
            'formulas': {'normalized_error': 'clamp(max(error_pct - deadband_pct, 0) / 20, 0, 1)',
                'p_term': 'kp * normalized_error', 'i_term': 'ki * recorded integral',
                'pi_output': 'clamp(p_term + i_term, 0, max_output)',
                'integral': 'During ordinary active structural control: add normalized_error and clamp to [0,1]; otherwise decay by 0.85 per step. Recovery/reentry paths differ.'}},
        'sources': refs, 'samples': samples,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT)
    parser.add_argument('--source-root', type=Path, default=REPO.parent / 'minime')
    parser.add_argument('--controller-file', type=Path, default=None,
        help='Optional small health.json. Omit to leave the separate current snapshot unavailable.')
    parser.add_argument('--reuse-controller-from', type=Path,
        help='Reuse the frozen controller snapshot in an earlier viewer dataset.')
    parser.add_argument('--out', type=Path, default=REPO / 'visualizations/reservoir-3d/data.json')
    args = parser.parse_args()
    if args.controller_file and args.reuse_controller_from:
        parser.error('Choose --controller-file or --reuse-controller-from')
    output = args.out.resolve()
    if REPO not in output.parents:
        parser.error('Output must stay inside this research repository')
    result = build(args)
    samples = result.pop('samples')
    head = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    content = head[:-2] + ',\n  "samples": [\n' + ',\n'.join('    ' + json.dumps(s, ensure_ascii=False, separators=(',', ':'), allow_nan=False) for s in samples) + '\n  ]\n}\n'
    json.loads(content)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content)
    print(json.dumps({'output': str(output), 'bytes': len(content.encode()), **result['stats']}, indent=2))


if __name__ == '__main__':
    main()
