#!/usr/bin/env python3
"""Capture bounded read-only ESN state evidence and derive frozen 3D PCA.

Requires NumPy for symmetric eigendecomposition of the measured 128D states.
Only writes inside this research repository. No database or runtime interaction.
Raw snapshots are retained with SHA-256 references; rows have no assigned times.
Run with Python 3.12+ and NumPy. --replay verifies an existing export's raw inputs.
Moved replay exports can resolve missing snapshots beside the export by filename;
every snapshot must still match its recorded full SHA-256 hash.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import numpy as np

REPO = Path(__file__).resolve().parents[1]
DEFAULT_CAPACITY = REPO.parent / 'minime/workspace/capacity'
DEFAULT_OUTPUT = REPO / 'visualizations/reservoir-3d/state-geometry.json'
MAX_STATE_BYTES = 2 * 1024 * 1024
MAX_META_BYTES = 16 * 1024


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def bounded_read(path, limit):
    with Path(path).open('rb') as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise ValueError(f'Bounded read exceeds {limit} bytes: {path}')
    return raw


def file_stamp(path):
    value = Path(path).stat()
    return {'size': value.st_size, 'mtime_ns': value.st_mtime_ns,
            'inode': value.st_ino, 'device': value.st_dev}


def validate_states(raw, metadata):
    if metadata.get('dtype') != '<f4' or metadata.get('layout') != 'row_major':
        raise ValueError('Expected row-major little-endian float32 state dump')
    rows, columns = metadata.get('esn_window_rows'), metadata.get('esn_window_cols')
    if not isinstance(rows, int) or not isinstance(columns, int):
        raise ValueError('State dimensions must be integers')
    if rows < 2 or columns < 3 or rows * columns * 4 > MAX_STATE_BYTES:
        raise ValueError('Invalid or oversized state dimensions')
    if columns != metadata.get('esn_n') or len(raw) != rows * columns * 4:
        raise ValueError('State dimensions do not match raw byte size or reservoir size')
    state = np.frombuffer(raw, dtype='<f4').reshape(rows, columns).astype(np.float64)
    if not np.all(np.isfinite(state)):
        raise ValueError('State snapshot contains non-finite activations')
    return state


def capture(capacity_dir, attempts=3, settle_seconds=0.1):
    """Bracket state and metadata reads; reject visible replacement or writer overlap.

    Files are independently renamed by the producer. Stable reads and ordering
    checks establish observed stability, not a transactional producer guarantee.
    """
    directory = Path(capacity_dir)
    state_path = directory / 'esn_state_window.bin'
    meta_path = directory / 'capacity_dump_meta.json'
    failures = []
    for attempt in range(1, attempts + 1):
        try:
            stamps_before = [file_stamp(meta_path), file_stamp(state_path)]
            meta_raw = bounded_read(meta_path, MAX_META_BYTES)
            state_raw = bounded_read(state_path, MAX_STATE_BYTES)
            time.sleep(settle_seconds)
            state_after = bounded_read(state_path, MAX_STATE_BYTES)
            meta_after = bounded_read(meta_path, MAX_META_BYTES)
            stamps_after = [file_stamp(meta_path), file_stamp(state_path)]
            if stamps_before != stamps_after or meta_raw != meta_after or state_raw != state_after:
                raise ValueError('Source changed during bracketed reads')
            if stamps_after[1]['mtime_ns'] > stamps_after[0]['mtime_ns']:
                raise ValueError('State is newer than metadata; possible partial dump generation')
            metadata = json.loads(meta_raw)
            validate_states(state_raw, metadata)
            source = {
                'captured_at_utc': utc_now(), 'meta': metadata,
                'files': {
                    'states': {'path': str(state_path.resolve()), 'sha256': digest(state_raw),
                               'stat': stamps_after[1]},
                    'metadata': {'path': str(meta_path.resolve()), 'sha256': digest(meta_raw),
                                 'stat': stamps_after[0]},
                },
                'consistency': {
                    'status': 'stable_bracketed_read', 'attempt': attempt,
                    'attempts_allowed': attempts, 'prior_failures': failures,
                    'settle_seconds': settle_seconds, 'identical_bytes_before_after': True,
                    'identical_stats_before_after': True, 'state_not_newer_than_metadata': True,
                    'producer_transactional_pair_guarantee': False,
                    'limitation': 'Producer independently renames state, secondary covariance, then metadata; metadata does not contain a state hash or generation identifier. Matching dump generation cannot be proven from these files alone.',
                },
            }
            return state_raw, meta_raw, source
        except (OSError, ValueError, json.JSONDecodeError) as error:
            failures.append(str(error))
            if attempt < attempts:
                time.sleep(settle_seconds)
    raise ValueError('Could not capture stable bounded state input: ' + '; '.join(failures))


def analyze(state):
    matrix = np.asarray(state, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] < 2 or matrix.shape[1] < 3:
        raise ValueError('PCA needs a 2D matrix with at least 2 rows and 3 columns')
    if not np.all(np.isfinite(matrix)):
        raise ValueError('Non-finite activation')
    n, dimensions = matrix.shape
    mean = matrix.mean(axis=0)
    centered = matrix - mean
    covariance = centered.T @ centered / (n - 1)
    values, vectors = np.linalg.eigh(covariance)
    order = np.argsort(values)[::-1]
    values, vectors = values[order], vectors[:, order]
    tolerance = np.finfo(np.float64).eps * max(float(np.linalg.norm(covariance, ord=2)), 1.0) * dimensions * 10
    if float(values.min()) < -tolerance:
        raise ValueError('Sample covariance has materially negative eigenvalues')
    minimum_before_clip = float(values.min())
    values = np.maximum(values, 0.0)
    total = float(values.sum())
    if total <= 0:
        raise ValueError('Captured states have zero temporal variance; PCA directions undefined')
    # Fix sign ambiguity without refitting across animation frames.
    components = vectors[:, :3].T.copy()
    for component in components:
        if component[np.argmax(np.abs(component))] < 0:
            component *= -1
    scores = centered @ components.T
    reconstructed_centered = scores @ components
    residual = centered - reconstructed_centered
    state_rms = np.sqrt(np.mean(matrix * matrix, axis=1))
    centered_norm = np.linalg.norm(centered, axis=1)
    projected_norm = np.linalg.norm(scores, axis=1)
    residual_norm = np.linalg.norm(residual, axis=1)
    fractions = values / total
    participation_ratio = total * total / float(np.square(values).sum())
    pythagorean_error = float(np.max(np.abs(centered_norm ** 2 - projected_norm ** 2 - residual_norm ** 2)))
    pca = {
        'method': 'Centered sample covariance eigendecomposition in float64',
        'fit_scope': 'entire_captured_window_retrospective', 'frozen': True,
        'rows': n, 'dimensions': dimensions, 'covariance_denominator': n - 1,
        'mean': mean.tolist(), 'eigenvalues': values.tolist(),
        'components': components.tolist(), 'component_orientation': 'component_by_neuron',
        'component_sign_rule': 'largest absolute loading is positive',
        'explained_variance_ratio': fractions.tolist(),
        'retained_fraction': float(fractions[:3].sum()),
        'omitted_fraction': float(fractions[3:].sum()),
        'total_sample_variance': total, 'participation_ratio': participation_ratio,
        'reconstruction_rmse': float(np.sqrt(np.mean(residual ** 2))),
        'relative_reconstruction_error': float(np.linalg.norm(residual) / np.linalg.norm(centered)),
        'normalization': {
            'reference_radius': float(centered_norm.max()),
            'definition': 'Maximum full-state distance from this window mean; empirical envelope, not a stability or capacity boundary',
            'point_radius_definition': 'Euclidean norm of three PCA scores divided by reference_radius',
            'distance_units': 'reservoir activation units',
        },
        'metric_distinction': 'Centered sample covariance eigenvalues describe variation in this captured window. They are not the live uncentered EWMA covariance eigenvalues, sensory EigenFill, recurrent-weight eigenvalues, or physical neuron positions.',
        'checks': {
            'explained_variance_sum': float(fractions.sum()),
            'covariance_trace': float(np.trace(covariance)),
            'component_orthogonality_max_error': float(np.max(np.abs(components @ components.T - np.eye(3)))),
            'max_pythagorean_error': pythagorean_error,
            'minimum_eigenvalue_before_roundoff_clip': minimum_before_clip,
            'eigenvalue_clip_tolerance': tolerance,
        },
    }
    samples = []
    root_dim = np.sqrt(dimensions)
    for index in range(n):
        samples.append({
            'index': index, 'pc': scores[index].tolist(),
            'state_rms': float(state_rms[index]),
            'centered_rms': float(centered_norm[index] / root_dim),
            'projected_rms': float(projected_norm[index] / root_dim),
            'reconstruction_rmse': float(residual_norm[index] / root_dim),
            'centered_norm': float(centered_norm[index]),
            'projected_norm': float(projected_norm[index]),
            'residual_norm': float(residual_norm[index]),
        })
    return pca, samples


def trace_source(capacity_dir):
    path = Path(capacity_dir).parent.parent / 'minime/src/runtime/orchestration.rs'
    raw = bounded_read(path, 1024 * 1024)
    text = raw.decode()
    anchors = {
        'row_order': 'esn_state_ring.push_back(esn.x.clone());',
        'ring_limit': 'const ESN_STATE_RING_CAP: usize = 1024;',
        'iteration_sleep': 'sleep(Duration::from_millis(331)).await;',
        'batch_sampling': 'for (mut z, _meta) in batch.iter().take(esn_sample_limit)',
        'elapsed_origin': 'let start = Instant::now();',
        'dump_cadence': 'if now_ms.saturating_sub(prev) > 30_000 && !esn_state_ring.is_empty()',
        'state_atomic_rename': 'std::fs::rename(&tmp, cap_dir.join("esn_state_window.bin"))',
        'metadata_atomic_rename': 'std::fs::rename(&tmp, cap_dir.join("capacity_dump_meta.json"))',
    }
    citations = {}
    for key, anchor in anchors.items():
        position = text.find(anchor)
        if position < 0:
            raise ValueError(f'Producer source changed; missing anchor: {key}')
        citations[key] = text[:position].count('\n') + 1
    return {'path': str(path.resolve()), 'sha256': digest(raw), 'lines': citations,
            'status': 'current source inspection; loaded producer binary revision unverified'}


def repo_path(path):
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(REPO.resolve()):
        raise ValueError('All outputs must remain within this research repository')
    return resolved


def save_raw(output, raw, meta_raw, source):
    for key, data, suffix in [('states', raw, '.bin'), ('metadata', meta_raw, '.json')]:
        path = repo_path(output.parent / f'captured-{key}-{digest(data)[:16]}{suffix}')
        if path.exists():
            if bounded_read(path, MAX_STATE_BYTES) != data:
                raise ValueError(f'Unexpected existing snapshot content: {path}')
        else:
            with path.open('xb') as handle:
                handle.write(data)
        source['files'][key]['snapshot_path'] = str(path)


def read_replay_snapshot(replay, source, key, limit):
    """Read recorded bytes, allowing a moved export without altering provenance."""
    reference = source['files'][key]
    recorded = Path(reference['snapshot_path'])
    if not recorded.is_absolute():
        recorded = Path(replay).parent / recorded
    try:
        raw = bounded_read(recorded, limit)
    except FileNotFoundError:
        local = Path(replay).parent / recorded.name
        raw = bounded_read(local, limit)
    if digest(raw) != reference['sha256']:
        raise ValueError(f'Retained {key} snapshot hash mismatch')
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capacity-dir', type=Path, default=DEFAULT_CAPACITY)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--replay', type=Path, help='Verify and recompute using an existing export and its retained raw snapshots')
    args = parser.parse_args()
    output = repo_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.replay:
        previous = json.loads(bounded_read(args.replay, 2 * 1024 * 1024))
        source = previous['source']
        raw = read_replay_snapshot(args.replay, source, 'states', MAX_STATE_BYTES)
        meta_raw = read_replay_snapshot(args.replay, source, 'metadata', MAX_META_BYTES)
        if json.loads(meta_raw) != source['meta']:
            raise ValueError('Retained metadata does not match the export')
        producer = previous['producer_source']
    else:
        raw, meta_raw, source = capture(args.capacity_dir)
        producer = trace_source(args.capacity_dir)
        save_raw(output, raw, meta_raw, source)
    matrix = validate_states(raw, source['meta'])
    pca, samples = analyze(matrix)
    payload = {
        'schema': 'reservoir.state_geometry.v1',
        'subject': 'Minime native ESN reservoir activation states',
        'source': source, 'producer_source': producer,
        'timing': {
            'row_order': 'oldest_to_newest', 'row_unit': 'one successfully recorded ESN step',
            'per_row_timestamps_available': False, 'per_row_wall_time': None,
            'dump_elapsed_ms': source['meta'].get('t_ms'),
            'dump_elapsed_origin': 'sensory processing loop Instant; no session identifier in dump metadata',
            'iteration_sleep_ms_in_current_source': 331,
            'dump_check_interval_ms_in_current_source': 30000,
            'cadence_notes': 'Rows are successful ESN steps over admitted batches. The loop sleep is not a measured row interval; batches, gating, processing time and step failures can alter cadence. No row-to-wall-time or fill/controller alignment is inferred.',
            'file_mtime_role': 'filesystem observations of file writes, not authenticated row timestamps',
        },
        'missing_fields': ['per-row wall time', 'per-row elapsed time', 'session id',
                           'per-row leak', 'per-row PI state', 'recurrent weights', 'input weights'],
        'pca': pca, 'samples': samples,
        'reproduction': {'probe': str(Path(__file__).resolve()),
                         'python_numpy': np.__version__,
                         'replay_arguments': ['--replay', str(output), '--output', str(output)]},
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')
    print(json.dumps({'output': str(output), 'bytes': output.stat().st_size,
                      'n_rows': len(samples), 'n_neurons': pca['dimensions'],
                      'retained_variance_fraction': pca['retained_fraction'],
                      'participation_ratio': pca['participation_ratio'],
                      'capture_consistency': source['consistency']['status'],
                      'raw_state_sha256': source['files']['states']['sha256']}))


if __name__ == '__main__':
    main()
