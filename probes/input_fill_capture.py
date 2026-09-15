#!/usr/bin/env python3
"""Capture a <=1h bridge interval through indexed ordinary read-only SQLite.

Standard library only. Source-host worker goes over SSH stdin; no remote files,
runtime imports, locks bypasses, writes, or live inputs. Hard row/time/output caps.
Study S-003: local raw capture, not a claim of causal input-to-state linkage.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import sqlite3
import subprocess
import sys
import time


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def worker(args):
    path = Path(args.remote_base) / 'astrid/capsules/spectral-bridge/workspace/bridge.db'
    result = {'schema_version': 1, 'kind': 'input_fill_bridge_capture',
              'captured_at_utc': datetime.now(timezone.utc).isoformat(),
              'since': args.since, 'until': args.until, 'source_path': str(path),
              'access': 'ordinary SQLite mode=ro on source host; no writes',
              'tables': {}}
    conn = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=3)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('BEGIN')
        for table, index in [('bridge_messages', 'idx_bridge_ts'), ('codec_impact', 'idx_codec_impact_ts')]:
            sql = f'SELECT * FROM {table} INDEXED BY {index} WHERE timestamp>=? AND timestamp<? ORDER BY timestamp,id LIMIT ?'
            params = [args.since, args.until, 10001]
            plan = [list(row) for row in conn.execute('EXPLAIN QUERY PLAN '+sql, params)]
            if not any('SEARCH ' in row[3] for row in plan):
                raise ValueError('Refusing an unindexed query')
            started = time.monotonic()
            conn.set_progress_handler(lambda: int(time.monotonic()-started > 5), 10000)
            try:
                rows = [dict(row) for row in conn.execute(sql, params)]
            finally:
                conn.set_progress_handler(None, 0)
            result['tables'][table] = {'sql': sql, 'parameters': params, 'query_plan': plan,
                'limit': 10000, 'truncated': len(rows)>10000, 'rows': rows[:10000],
                'n': min(len(rows),10000)}
    finally:
        conn.close()
    raw = dump(result)
    if len(raw.encode()) > 32*1024*1024:
        raise ValueError('Capture exceeds 32 MiB; choose a smaller interval')
    print(raw)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--since', type=float, required=True, help='inclusive epoch seconds')
    p.add_argument('--until', type=float, required=True, help='exclusive epoch seconds')
    p.add_argument('--source-host', default='volya')
    p.add_argument('--remote-base', default='/Users/v/other')
    p.add_argument('--out', type=Path)
    p.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    a = p.parse_args()
    if not 0 < a.until-a.since <= 3600:
        p.error('Select a positive interval of at most one hour')
    if a.worker:
        worker(a)
        return
    root = Path(__file__).resolve().parents[1]
    if a.out is None or not a.out.resolve().is_relative_to(root):
        p.error('Output must be a new file inside this research repository')
    if a.out.exists() or a.out.is_symlink():
        p.error('Refusing to replace existing output')
    if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*', a.source_host):
        p.error('Invalid source host')
    code = Path(__file__).read_bytes()
    remote = ['python3', '-B', '-', '--worker', '--since', str(a.since), '--until', str(a.until), '--remote-base', a.remote_base]
    r = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','StrictHostKeyChecking=yes', a.source_host, shlex.join(remote)],
                       input=code, capture_output=True, timeout=30, check=True)
    result = json.loads(r.stdout)
    result['driver_sha256'] = hashlib.sha256(code).hexdigest()
    result['source_host'] = a.source_host
    result['remote_stderr'] = r.stderr.decode() or None
    a.out.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with a.out.open('x') as f:
        os.chmod(a.out, 0o600)
        f.write(dump(result)+'\n')
    print(dump({'out': str(a.out.resolve()), 'sha256': hashlib.sha256(a.out.read_bytes()).hexdigest(),
                'tables': {k:{'n':v['n'],'truncated':v['truncated']} for k,v in result['tables'].items()}}))


if __name__ == '__main__':
    main()
