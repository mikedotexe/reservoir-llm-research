#!/usr/bin/env python3
"""Prospective, bounded main-PID sampler. No UI, network, journal or process discovery.

The root operator explicitly invokes capture after package/launch qualification.
Only the already qualified libproc metric/identity implementation is reused.
Analysis is descriptive, never a GPU, total-app performance or leak verdict.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import statistics
import sys
import threading
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
METRICS_SOURCE = ROOT / 'scripts/macos_reliability.py'
METRICS_SHA = '326fb72a668f1cac1f32585e0b61e791a56a959b1ac0ae32560fcebd0fba5215'
SCHEMA = 'reservoir-observatory-main-process-v1'
MAX_BYTES = 2 * 1024 * 1024
PHASES = ('visible-idle', 'playback', 'minimized', 'restored-idle')
LIMITS = [
    'Only the explicit main PID; WebKit/render helpers, model processes and GPU are excluded.',
    'No GPU utilization, energy, thermals, frame latency or total application footprint is measured.',
    'CPU is task time / monotonic interval; 100 percent means one CPU core. RSS is not a leak diagnosis.',
    'Window states and draw counters are separate operator observations, not inferred by this sampler.',
    'Minimizing intentionally pauses recorded playback; minimized and playback phases are different workloads.',
    'Short descriptive samples do not qualify endurance, other operating systems or minimum hardware.',
]


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bounded(path, limit=MAX_BYTES):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError('Expected bounded ordinary input file')
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Input byte bound exceeded')
    return data


def identity(path):
    data = bounded(path)
    return {'path': str(Path(path).resolve()), 'bytes': len(data), 'sha256': digest(data)}


def load_metrics():
    if digest(bounded(METRICS_SOURCE)) != METRICS_SHA:
        raise ValueError('Qualified metrics implementation changed')
    spec = importlib.util.spec_from_file_location('qualified_macos_metrics', METRICS_SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capture(args):
    if not 1 <= args.duration_seconds <= 600:
        raise ValueError('Capture duration must be within 1–600 seconds')
    launch_bytes = bounded(args.launch_receipt, 131072)
    if digest(launch_bytes) != args.expected_launch_sha256:
        raise ValueError('Explicit launch receipt hash mismatch')
    launch = json.loads(launch_bytes)
    pid = launch['pid']
    if type(pid) is not int or not 0 < pid < 2**31:
        raise ValueError('Invalid exact owned PID')
    metrics = load_metrics()
    executable = metrics.ordinary_path(launch['executable'])
    if metrics.hash_file(executable) != launch['executableSha256']:
        raise ValueError('Launched executable bytes changed')
    process = metrics.MacProcess(pid)
    owner = process.identity()
    if owner['executablePath'] != str(executable):
        raise ValueError('Owned PID executable does not match launch receipt')
    # The launch wrapper records immediately after Popen. Refuse a later reuse
    # of this PID even if another instance happens to execute the same binary.
    launched = dt.datetime.fromisoformat(launch['startedUtc']).timestamp()
    started = int(owner['startSeconds']) + int(owner['startMicroseconds']) / 1e6
    if not launched - 10 <= started <= launched + 1:
        raise ValueError('Process start does not match the explicit launch witness')
    executable_stat = metrics.file_identity(executable)
    if process.identity() != owner:
        raise ValueError('PID identity changed before capture')
    stop = threading.Event()
    reason = ['completed']
    def interrupted(signum, _frame):
        reason[0] = f'sampler-signal-{signum}'
        stop.set()
    handlers = {}
    count, used, previous = 0, 0, None
    began = time.monotonic_ns()
    footer_errors = []
    # Exclusive output; neither the target app nor its files are changed.
    with Path(args.output).open('xb', buffering=0) as output:
        def write(row, footer=False):
            nonlocal used
            data = (json.dumps(row, separators=(',', ':'), allow_nan=False) + '\n').encode()
            if len(data) > 65536 or used + len(data) > MAX_BYTES - (0 if footer else 65536):
                raise ValueError('Sampler output bound reached')
            output.write(data)
            os.fsync(output.fileno())
            used += len(data)
        write({'type': 'header', 'schema': SCHEMA, 'wallUtc': utc(), 'monotonicNs': str(began),
               'process': {**owner, 'executableSha256': launch['executableSha256']},
               'launchReceipt': identity(args.launch_receipt), 'sampler': identity(__file__),
               'metricsSource': identity(METRICS_SOURCE), 'machTimebase': process.timebase,
               'intervalSeconds': 5, 'durationSeconds': args.duration_seconds,
               'maxOutputBytes': MAX_BYTES, 'limitations': LIMITS})
        try:
            handlers = {s: signal.signal(s, interrupted) for s in (signal.SIGINT, signal.SIGTERM)}
            while not stop.is_set():
                at = time.monotonic_ns()
                if process.identity() != owner or metrics.file_identity(executable) != executable_stat:
                    raise ValueError('Owned process or executable identity changed')
                row = {'type': 'sample', 'sequence': count, 'wallUtc': utc(), 'monotonicNs': str(at),
                       'elapsedSeconds': (at - began) / 1e9, 'process': None, 'errors': []}
                try:
                    value = process.metrics()
                    if process.identity() != owner:
                        raise ValueError('Process identity changed during metric read')
                    cpu = int(value['cpuTotalNanoseconds'])
                    value.update(identityVerified=True, cpuIntervalPercent=None,
                                 cpuIntervalStartMonotonicNs=None, cpuDeltaNanoseconds=None)
                    if previous:
                        interval = at - previous[0]
                        delta = cpu - previous[1]
                        if interval > 0 and delta >= 0:
                            value.update(cpuIntervalStartMonotonicNs=str(previous[0]),
                                         cpuDeltaNanoseconds=str(delta), cpuIntervalPercent=100 * delta / interval)
                        else:
                            row['errors'].append({'component': 'cpu', 'message': 'Counter/clock regression'})
                    previous = (at, cpu)
                    row['process'] = value
                except OSError as error:
                    # Keep the last valid CPU origin. Analysis excludes a bridge
                    # across a missed sample rather than assigning it to a phase.
                    row['errors'].append({'component': 'process', 'errno': error.errno})
                write(row)
                count += 1
                remaining = args.duration_seconds - (time.monotonic_ns() - began) / 1e9
                if remaining <= 0:
                    break
                stop.wait(min(remaining, max(0, 5 - (time.monotonic_ns() - at) / 1e9)))
        except Exception as error:
            reason[0] = 'capture-failed'
            footer_errors.append({'kind': type(error).__name__, 'message': str(error)[:512]})
        finally:
            final_sha = None
            try:
                final_sha = metrics.hash_file(executable)
                if final_sha != launch['executableSha256']:
                    reason[0] = 'capture-failed'
                    footer_errors.append({'message': 'Final executable hash mismatch'})
            except (OSError, ValueError) as error:
                reason[0] = 'capture-failed'
                footer_errors.append({'kind': type(error).__name__, 'message': str(error)[:512]})
            write({'type': 'footer', 'status': reason[0], 'wallUtc': utc(),
                   'monotonicNs': str(time.monotonic_ns()), 'sampleCount': count,
                   'finalExecutableSha256': final_sha, 'errors': footer_errors}, footer=True)
            for signum, handler in handlers.items():
                signal.signal(signum, handler)
    return 0 if reason[0] == 'completed' else 2


def mark(args):
    path = Path(args.output)
    if path.exists():
        data = bounded(path, 131072)
        if len(data.splitlines()) >= 32:
            raise ValueError('Marker count bound reached')
    row = {'phase': args.phase, 'wallUtc': utc(), 'monotonicNs': str(time.monotonic_ns()),
           'source': 'operator-declared UI boundary; not automatic window detection'}
    with path.open('ab') as stream:
        stream.write((json.dumps(row) + '\n').encode())
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(row))


def distribution(values):
    values = sorted(values)
    return None if not values else {'count': len(values), 'minimum': values[0],
                                    'median': statistics.median(values), 'maximum': values[-1]}


def analyze_rows(rows, markers):
    if not rows or rows[0].get('schema') != SCHEMA or rows[0].get('type') != 'header':
        raise ValueError('Missing supported capture header')
    samples = [r for r in rows if r.get('type') == 'sample']
    footer = rows[-1] if rows[-1].get('type') == 'footer' else None
    issues = []
    if not footer:
        issues.append('Missing terminal footer: capture incomplete or still active')
    elif footer.get('status') != 'completed':
        issues.append('Capture did not finish normally')
    if footer and footer.get('sampleCount') != len(samples):
        issues.append('Footer sample count mismatch')
    if footer and footer.get('finalExecutableSha256') != rows[0]['process']['executableSha256']:
        issues.append('Final executable identity not confirmed')
    for a, b in zip(markers, markers[1:]):
        if int(b['monotonicNs']) <= int(a['monotonicNs']):
            raise ValueError('Markers must be strictly monotonic')
    if any(m.get('phase') not in (*PHASES, 'settling', 'end') for m in markers):
        raise ValueError('Unknown operator phase')
    windows = []
    for index, marker in enumerate(markers):
        if marker['phase'] not in PHASES:
            continue
        lo = int(marker['monotonicNs'])
        hi = int(markers[index + 1]['monotonicNs']) if index + 1 < len(markers) else None
        selected = [r for r in samples if int(r['monotonicNs']) >= lo and (hi is None or int(r['monotonicNs']) <= hi)]
        cpu_time = interval_time = cpu_count = 0
        for row in selected:
            p = row.get('process') or {}
            start = p.get('cpuIntervalStartMonotonicNs')
            delta = p.get('cpuDeltaNanoseconds')
            if start is None or delta is None or not p.get('identityVerified'):
                continue
            start, end, delta = int(start), int(row['monotonicNs']), int(delta)
            if start >= lo and hi is not None and end <= hi and 0 < end - start <= 7_500_000_000 and delta >= 0:
                cpu_time += delta
                interval_time += end - start
                cpu_count += 1
        summaries = {}
        for key in ('rssBytes', 'threadCount', 'fdCount'):
            values = [(r.get('process') or {}).get(key) for r in selected]
            summaries[key] = distribution([v for v in values if type(v) in (int, float) and math.isfinite(v)])
        windows.append({'phase': marker['phase'], 'source': 'operator-declared', 'fromMonotonicNs': str(lo),
                        'toMonotonicNs': None if hi is None else str(hi), 'closed': hi is not None,
                        'declaredSeconds': None if hi is None else (hi - lo) / 1e9,
                        'sampleCount': len(selected), 'metrics': summaries,
                        'cpuIntervalCount': cpu_count, 'cpuCoveredSeconds': interval_time / 1e9,
                        'cpuWeightedPercent': None if not interval_time else 100 * cpu_time / interval_time})
    return {'schema': SCHEMA + '-analysis', 'measurementOnly': True, 'windows': windows,
            'sampleCount': len(samples), 'footer': footer, 'issues': issues,
            'allSampleErrors': [{'sequence': r['sequence'], 'errors': r['errors']} for r in samples if r.get('errors')],
            'limitations': LIMITS + ['CPU excludes crossing intervals, unclosed phases and intervals over 7.5 s. Missing samples are not zero CPU.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    sample = commands.add_parser('sample')
    sample.add_argument('--launch-receipt', type=Path, required=True)
    sample.add_argument('--expected-launch-sha256', required=True)
    sample.add_argument('--output', type=Path, required=True)
    sample.add_argument('--duration-seconds', type=int, default=600)
    marker = commands.add_parser('mark')
    marker.add_argument('--output', type=Path, required=True)
    marker.add_argument('--phase', choices=(*PHASES, 'settling', 'end'), required=True)
    analysis = commands.add_parser('analyze')
    analysis.add_argument('--input', type=Path, required=True)
    analysis.add_argument('--markers', type=Path, required=True)
    analysis.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'sample':
        return capture(args)
    if args.command == 'mark':
        mark(args)
        return 0
    data = bounded(args.input)
    marker_data = bounded(args.markers, 131072)
    rows = [json.loads(line) for line in data.splitlines()]
    markers = [json.loads(line) for line in marker_data.splitlines()]
    if len(rows) > 512 or len(markers) > 32 or not data.endswith(b'\n') or not marker_data.endswith(b'\n'):
        raise ValueError('Record count bound or incomplete final record')
    result = analyze_rows(rows, markers)
    result.update(input=identity(args.input), markers=identity(args.markers), analyzer=identity(__file__))
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
