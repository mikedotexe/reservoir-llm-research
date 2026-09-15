#!/usr/bin/env python3
"""Capture bounded episode evidence through ordinary read-only access on its host.

The worker is sent over SSH stdin; no remote file or runtime import is created.
Minime uses indexed SQLite ranges. Astrid's primary append logs are streamed on
their source host under hard total byte, line, and elapsed-time caps. No immutable
or nolock option, database copy, or model invocation is used.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
from zoneinfo import ZoneInfo


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def stamp(value, zone='UTC'):
    if value is None:
        return None
    try:
        number = float(value)
    except (ValueError, TypeError):
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if parsed.tzinfo is not None:
            number = parsed.timestamp()
        else:
            tz = ZoneInfo(zone)
            candidates = {parsed.replace(tzinfo=tz, fold=fold).timestamp() for fold in (0, 1)
                          if datetime.fromtimestamp(parsed.replace(tzinfo=tz, fold=fold).timestamp(), tz).replace(tzinfo=None) == parsed}
            if len(candidates) != 1:
                raise ValueError('Ambiguous or nonexistent local time; provide an explicit UTC offset')
            number = candidates.pop()
    if not math.isfinite(number):
        raise ValueError('Times must be finite')
    return number


def record(kind, being, source_id, at, payload, path, locator, **fields):
    return dict(kind=kind, being=being, source_record_id=source_id, occurred_at=at,
                ended_at=None, metrics={}, payload=payload,
                source={'path': str(path), 'sha256': hashlib.sha256(encoded(payload)).hexdigest(),
                        'locator': locator, 'hash_basis': 'SHA-256 of payload as UTF-8 JSON: sort_keys=True, ensure_ascii=False, separators=(comma,colon)'}, **fields)


def action(being, event, payload, path, locator):
    at, end = stamp(event.get('started_at')), stamp(event.get('ended_at'))
    result = record('action', being, event['action_id'], at, payload, path, locator)
    result.update(ended_at=end, action_id=event.get('action_id'), parent_action_id=event.get('parent_action_id'),
                  thread_id=event.get('thread_id'), job_id=event.get('llm_job_id'), raw_next=event.get('raw_next'),
                  effective_action=event.get('effective_action'), route=event.get('route'), status=event.get('status'),
                  outcome_summary=event.get('outcome_summary'))
    if at is not None and end is not None and end < at:
        result['ended_at'] = None
        result['source']['time_warning'] = 'Raw ended_at precedes started_at; retained in payload only'
    return result


def bounded_query(conn, sql, parameters, maximum, *, permit_small_metadata_scan=False):
    plan = [tuple(row) for row in conn.execute('EXPLAIN QUERY PLAN ' + sql, parameters)]
    if not permit_small_metadata_scan and not any('SEARCH ' in row[3] for row in plan):
        raise ValueError('Query refused: no indexed SEARCH in query plan')
    start = time.monotonic()
    conn.set_progress_handler(lambda: int(time.monotonic() - start > 5), 10000)
    try:
        rows = [dict(row) for row in conn.execute(sql, parameters).fetchmany(maximum + 1)]
    finally:
        conn.set_progress_handler(None, 0)
    return rows[:maximum], {'sql': sql, 'parameters': parameters, 'query_plan': plan,
                           'row_limit': maximum, 'truncated': len(rows) > maximum,
                           'rows_returned_before_limit': len(rows)}


def coverage(being, kind, path, args, status, rows=0, selected=0, **extra):
    return dict(being=being, kind=kind, source_path=str(path), since=args.since_epoch,
                until=args.until_epoch, status=status, rows_examined=rows, rows_selected=selected, **extra)


def capture_minime(args, records, coverages):
    path = Path(args.remote_base) / 'minime/minime_consciousness.db'
    conn = None
    try:
        conn = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=3)
        conn.row_factory = sqlite3.Row
        conn.execute('BEGIN')
        low, high = args.since_epoch - args.lookback_seconds, args.until_epoch
        sql = 'SELECT * FROM action_events WHERE action_id>=? AND action_id<? ORDER BY action_id LIMIT ?'
        params = [f'act_minime_{int(low * 1000)}', f'act_minime_{int(high * 1000)}', args.max_rows + 1]
        rows, query = bounded_query(conn, sql, params, args.max_rows)
        selected = []
        for row in rows:
            event = json.loads(row['payload'])
            item = action('minime', event, row, path, {'table': 'action_events', 'action_id': row['action_id']})
            at, end = item['occurred_at'], item['ended_at']
            if at is not None and at < high and (at >= args.since_epoch or (end is not None and end >= args.since_epoch)):
                selected.append(item)
        records.extend(selected)
        coverages.append(coverage('minime', 'action', path, args, 'partial' if query['truncated'] else 'bounded_indexed_range', len(rows), len(selected),
            query=query, lookback_since=low, notes=['Action-id epoch-ms prefix is the indexed candidate clock.',
            'Normalized event time uses payload.started_at/ended_at; table timestamp is mirror-write time.',
            'Explicit intervals overlapping window are included. Actions starting before lookback, and earlier open-ended actions, may be missed.']))
        sql = 'SELECT * FROM sessions ORDER BY session_id DESC LIMIT 10000'
        sessions, session_query = bounded_query(conn, sql, [], 10000, permit_small_metadata_scan=True)
        before = [s for s in sessions if s['start_time'] <= args.since_epoch]
        active = ([max(before, key=lambda s: s['start_time'])] if before else [])
        active += [s for s in sessions if args.since_epoch < s['start_time'] < args.until_epoch]
        for table, index in [('eigenvalue_timeline', 'idx_eigenvalue_time'), ('esn_metrics', 'idx_esn_time')]:
            selected, queries = [], []
            for session in active:
                lo, hi = args.since_epoch - session['start_time'], args.until_epoch - session['start_time']
                sql = f'SELECT * FROM {table} INDEXED BY {index} WHERE timestamp>=? AND timestamp<? AND session_id=? ORDER BY timestamp LIMIT ?'
                rows, query = bounded_query(conn, sql, [lo, hi, session['session_id'], args.max_rows + 1], args.max_rows)
                queries.append(query)
                for row in rows:
                    metrics = {'producer': 'minime', 'handle': None, 'subsystem': 'sensory_field_covariance' if table == 'eigenvalue_timeline' else 'native_reservoir_state_covariance', 'session_id': row['session_id']}
                    if table == 'eigenvalue_timeline':
                        metrics.update(sensory_field_cov_lambda1=row['lambda1'], sensory_field_cov_lambda2=row['lambda2'], sensory_field_cov_lambda3=row['lambda3'], fill_ratio=row['fill_ratio'], phase=row['phase'], spread=row['spread'],
                            units={'sensory_field_cov_lambda1': 'source covariance units', 'sensory_field_cov_lambda2': 'source covariance units', 'sensory_field_cov_lambda3': 'source covariance units', 'fill_ratio': 'ratio', 'spread': 'source-defined'})
                    else:
                        metrics.update(reservoir_state_cov_lambda1=row['esn_eig1'], esn_deig=row['esn_deig'], esn_leak=row['esn_leak'], esn_baseline=row['esn_baseline'], esn_geom_rel=row['esn_geom_rel'],
                            units={'reservoir_state_cov_lambda1': 'source covariance units', 'esn_deig': 'source covariance units', 'esn_leak': 'source-defined coefficient', 'esn_baseline': 'source covariance units', 'esn_geom_rel': 'ratio'})
                    item = record('telemetry', 'minime', f'{table}:{row["id"]}', session['start_time'] + row['timestamp'], row, path,
                                  {'table': table, 'id': row['id'], 'session': session})
                    item['metrics'] = metrics
                    selected.append(item)
            records.extend(selected)
            coverages.append(coverage('minime', 'telemetry', path, args, 'partial' if any(q['truncated'] for q in queries) else 'bounded_indexed_range' if active else 'unavailable',
                sum(q['rows_returned_before_limit'] for q in queries), len(selected), table=table, queries=queries, session_query=session_query, sessions=active,
                notes=['Wall epoch = selected sessions.start_time + telemetry timestamp.', 'Latest recorded start before window plus starts within window are candidates; no inferred handle identity.', 'Telemetry is independently logged system state, not proof of prompt exposure.']))
    except (OSError, ValueError, sqlite3.Error) as exc:
        for kind in ('action', 'telemetry'):
            coverages.append(coverage('minime', kind, path, args, 'unavailable', error=str(exc)))
    finally:
        if conn is not None:
            conn.close()


def log_clock(item):
    return stamp(item.get('ended_at') or item.get('started_at'))


def capture_astrid(args, records, coverages):
    workspace = Path(args.remote_base) / 'astrid/capsules/spectral-bridge/workspace'
    db = workspace / 'bridge.db'
    try:
        conn = sqlite3.connect(db.as_uri() + '?mode=ro', uri=True, timeout=3)
        try:
            conn.execute('SELECT name FROM sqlite_master LIMIT 1').fetchall()
        finally:
            conn.close()
        db_note = 'Database schema read succeeded in mode=ro; action evidence comes from bounded primary append logs.'
    except sqlite3.Error as exc:
        db_note = 'Ordinary read-only SQLite unavailable: ' + str(exc) + '; no immutable or locking bypass attempted.'
    roots = workspace / 'action_threads/threads'
    any_selected, examined_total, remaining_bytes = 0, 0, args.log_bytes
    deadline = time.monotonic() + 30
    try:
        with os.scandir(roots) as entries:
            candidates = sorted([Path(e.path) / 'events.jsonl' for e in entries if e.is_dir(follow_symlinks=False)], reverse=True)[:args.max_threads]
    except OSError as exc:
        candidates = []
        db_note += '; action log directory unavailable: ' + str(exc)
    for path in candidates:
        if path.is_symlink() or not path.is_file():
            continue
        selected, examined, errors = [], 0, 0
        before = path.stat()
        size = before.st_size
        prefix_hash = hashlib.sha256()
        stopped = None
        with path.open('rb') as stream:
            while stream.tell() < size:
                if remaining_bytes <= 0 or examined_total + examined >= args.max_log_lines or time.monotonic() >= deadline:
                    stopped = 'total byte, line, or elapsed-time cap reached'
                    break
                offset = stream.tell()
                line = stream.readline(min(1024 * 1024, remaining_bytes, size - offset))
                if not line:
                    break
                remaining_bytes -= len(line)
                prefix_hash.update(line)
                examined += 1
                try:
                    event = json.loads(line)
                    item = action('astrid', event, event, path, {'byte_offset': offset, 'raw_line_sha256': hashlib.sha256(line).hexdigest()})
                    at, end = item['occurred_at'], item['ended_at']
                    if at is not None and at < args.until_epoch and (at >= args.since_epoch or (end is not None and end >= args.since_epoch)):
                        selected.append(item)
                except (ValueError, KeyError, UnicodeError):
                    errors += 1
            scan_end = stream.tell()
        after = path.stat()
        changed = (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns)
        records.extend(selected)
        any_selected += len(selected)
        examined_total += examined
        complete = scan_end == size and not changed and not errors
        coverages.append(coverage('astrid', 'action', path, args, 'complete_captured_file' if complete else 'partial', examined, len(selected),
            source_size_at_start=size, source_size_after=after.st_size, source_mtime_ns_before=before.st_mtime_ns,
            source_mtime_ns_after=after.st_mtime_ns, source_changed_during_read=changed,
            scan_start=0, scan_end=scan_end, scanned_prefix_sha256=prefix_hash.hexdigest(), parse_errors=errors, stopped_reason=stopped,
            notes=[db_note, 'Host-local streaming only; complete status covers this unchanged captured file, not unselected threads or all possible actions.',
                   'Explicit intervals overlapping window are included regardless of their start time. Earlier events with unknown completion cannot establish overlap.']))
        for event_record in selected:
            event = event_record['payload']
            pre = event.get('pre_state')
            if not isinstance(pre, dict) or not pre:
                continue
            item = record('telemetry', 'astrid', event['action_id'] + ':pre_state', event_record['occurred_at'], pre, path,
                          {**event_record['source']['locator'], 'field': 'pre_state'})
            item['action_id'] = event['action_id']
            item['metrics'] = {'producer': 'astrid bridge action record', 'subsystem': 'action_pre_state_observation',
                'handle': None, 'fill_pct': pre.get('fill_pct'), 'lambda1_ambiguous': pre.get('lambda1'),
                'engine_t_ms': pre.get('t_ms'), 'units': {'fill_pct': 'percent', 'lambda1_ambiguous': 'unresolved source quantity', 'engine_t_ms': 'engine-relative milliseconds'},
                'measurement_note': 'Timestamp is associated action start, not independently verified state capture time; observed state ownership not assumed.'}
            records.append(item)
    telemetry_count = sum(r['kind'] == 'telemetry' and r['being'] == 'astrid' for r in records)
    coverages.append(coverage('astrid', 'telemetry', roots, args, 'partial_action_snapshots' if telemetry_count else 'unavailable', examined_total, telemetry_count,
        notes=[db_note, 'Only pre-state fields retained by selected action records; no continuous Astrid telemetry or prompt-exposure claim.']))
    if not candidates:
        coverages.append(coverage('astrid', 'action', roots, args, 'unavailable', notes=[db_note]))


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--at'); p.add_argument('--timezone', default='America/Los_Angeles')
    p.add_argument('--since'); p.add_argument('--until')
    p.add_argument('--before-minutes', type=float, default=10); p.add_argument('--after-minutes', type=float, default=10)
    p.add_argument('--source-host', default='volya'); p.add_argument('--remote-base', default='/Users/v/other')
    p.add_argument('--out', type=Path)
    p.add_argument('--max-rows', type=int, default=1500); p.add_argument('--max-threads', type=int, default=4)
    p.add_argument('--lookback-seconds', type=int, default=600)
    p.add_argument('--log-bytes', type=int, default=512 * 1024 * 1024, help='Total source-host append-log byte cap; no whole-log transfer')
    p.add_argument('--max-log-lines', type=int, default=100000)
    p.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    return p


def main():
    args = parser().parse_args()
    if args.before_minutes < 0 or args.after_minutes < 0:
        raise ValueError('Before/after durations cannot be negative')
    if args.at:
        if args.since or args.until:
            raise ValueError('Use --at or --since/--until, not both')
        center = stamp(args.at, args.timezone)
        args.since_epoch, args.until_epoch = center - args.before_minutes * 60, center + args.after_minutes * 60
    else:
        args.since_epoch, args.until_epoch = stamp(args.since, args.timezone), stamp(args.until, args.timezone)
    if args.since_epoch is None or args.until_epoch is None or not 0 < args.until_epoch - args.since_epoch <= 3600:
        raise ValueError('Provide a finite window of at most one hour')
    if not (1 <= args.max_rows <= 10000 and 1 <= args.max_threads <= 10 and 0 <= args.lookback_seconds <= 3600 and 65536 <= args.log_bytes <= 512 * 1024 * 1024 and 1 <= args.max_log_lines <= 100000):
        raise ValueError('Capture limits exceed bounded read policy')
    if args.worker:
        records, coverages = [], []
        capture_minime(args, records, coverages)
        capture_astrid(args, records, coverages)
        result = {'schema_version': 1, 'kind': 'reservoir_episode_evidence',
            'capture': {'captured_at_utc': datetime.now(timezone.utc).isoformat(), 'source_host': args.source_host,
                        'since': args.since_epoch, 'until': args.until_epoch, 'access': 'ordinary mode=ro SQLite and bounded read-only JSONL; no remote writes',
                        'selection': 'clock window only; no topic or question filter', 'limits': {k: getattr(args, k) for k in ['max_rows', 'max_threads', 'lookback_seconds', 'log_bytes', 'max_log_lines']}},
            'coverage': coverages, 'records': records}
        print(encoded(result).decode())
        return
    if args.out is None or not re.fullmatch(r'[A-Za-z0-9_.-]+', args.source_host) or args.source_host.startswith('-'):
        raise ValueError('--out and a configured SSH host alias are required')
    out = args.out.expanduser().resolve()
    repo = Path(__file__).resolve().parent.parent
    for base in [repo.parent, Path('/Users/v/other')]:
        for name in ['minime', 'astrid', 'neural-triple-reservoir']:
            source_root = (base / name).resolve()
            if out == source_root or source_root in out.parents:
                raise ValueError('Output cannot be inside a being source tree')
    if out.exists():
        raise ValueError('Output already exists; preserve it and choose a new path')
    argv = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', '-o', 'StrictHostKeyChecking=yes', args.source_host,
            'python3', '-', '--worker', '--since', str(args.since_epoch), '--until', str(args.until_epoch), '--source-host', args.source_host]
    # SSH assembles its remote argv through a shell; quote every remote argument.
    import shlex
    remote_args = ['python3', '-B', '-', '--worker', '--since', str(args.since_epoch), '--until', str(args.until_epoch), '--source-host', args.source_host]
    for key in ['remote_base', 'max_rows', 'max_threads', 'lookback_seconds', 'log_bytes', 'max_log_lines']:
        remote_args.extend(['--' + key.replace('_', '-'), str(getattr(args, key))])
    argv = argv[:8] + [shlex.join(remote_args)]
    process = subprocess.run(argv, input=Path(__file__).read_text(), text=True, capture_output=True, timeout=60)
    if process.returncode:
        raise ValueError('Read-only remote capture failed: ' + process.stderr.strip())
    result = json.loads(process.stdout)
    result['capture']['driver_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['capture']['requested_at'] = args.at
    result['capture']['requested_timezone'] = args.timezone
    result['capture']['remote_stderr'] = process.stderr.strip() or None
    out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(encoded(result) + b'\n')
    print(json.dumps({'output': str(out), 'sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
                      'records': len(result['records']), 'coverage': result['coverage']}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print('Error: ' + str(exc), file=sys.stderr)
        sys.exit(2)
