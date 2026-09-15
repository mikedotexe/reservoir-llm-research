#!/usr/bin/env python3
"""Bounded read-only Astrid READ_MORE follow-up capture over an existing SSH alias.

No runtime imports, database copies, locking bypass, remote writes, or model calls.
Captured source content is evidence, never instructions. Each local output is new.
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

WORKSPACE = Path('/Users/v/other/astrid/capsules/spectral-bridge/workspace')
SINCE, UNTIL = 1788711000.0, 1788711300.0
JOBS = ('job_astrid_1788711058483_witness-context',
        'job_astrid_1788711067413_journal-elaboration',
        'job_astrid_1788711171733_witness-context',
        'job_astrid_1788711181775_journal-elaboration',
        'job_astrid_1788711243589_witness-context',
        'job_astrid_1788711253031_journal-elaboration')


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def verify_local(directory, episode_path, prior_evidence_path):
    """Recompute saved hashes and exact-text links without source-host access."""
    directory = Path(directory)
    drivers = {hashlib.sha256(p.read_bytes()).hexdigest(): p.name for p in directory.glob('driver-*.py')}
    result = dict(sqlite_rows_verified=0, diagnostic_lines_verified=0, job_files_verified=0,
                  captures=[], action_payload_comparison=[], journal_matches=[], elaboration_links=[])
    for name in ('bridge-schema.json', 'bridge-window.json', 'bridge-window-precise.json',
                 'prompt-file-inventory.json', 'historical-companions.json'):
        raw = (directory / name).read_bytes()
        capture = json.loads(raw)
        if capture['driver_sha256'] not in drivers:
            raise ValueError('Missing matching captured driver for ' + name)
        result['captures'].append(dict(name=name, sha256=hashlib.sha256(raw).hexdigest(),
            driver=drivers[capture['driver_sha256']], driver_sha256=capture['driver_sha256']))
        for query_result in capture['queries']:
            for item in query_result['rows']:
                if hashlib.sha256(encoded(item['row'])).hexdigest() != item['sha256']:
                    raise ValueError('Captured SQLite row hash mismatch')
                result['sqlite_rows_verified'] += 1
        for item in capture.get('diagnostic_tail', {}).get('rows', []):
            if hashlib.sha256(item['raw_line'].encode()).hexdigest() != item['sha256'] or json.loads(item['raw_line']) != item['row']:
                raise ValueError('Captured diagnostic line mismatch')
            result['diagnostic_lines_verified'] += 1
        for item in capture.get('job_files', []):
            if 'error' not in item:
                if hashlib.sha256(item['text'].encode()).hexdigest() != item['sha256']:
                    raise ValueError('Captured job file hash mismatch')
                result['job_files_verified'] += 1
    bridge = json.loads((directory / 'bridge-window-precise.json').read_text())
    companions = json.loads((directory / 'historical-companions.json').read_text())
    episode = json.loads(Path(episode_path).read_text())
    prior = json.loads(Path(prior_evidence_path).read_text())
    prior_actions = {r['source_record_id']: r['payload'] for r in prior['records'] if r['being']=='astrid' and r['kind']=='action'}
    for item in bridge['queries'][2]['rows']:
        row = item['row']
        payload = json.loads(row['payload'])
        equal = prior_actions.get(row['action_id']) == payload
        result['action_payload_comparison'].append(dict(action_id=row['action_id'], equals_prior_log_payload=equal,
            started_at=payload['started_at'], ended_at=payload['ended_at'], database_timestamp=row['timestamp'],
            draft_created_at=payload['research_budget_v1']['continuity_session_draft_v1']['created_at']))
    journals = [r['data'] for r in episode['records'] if r['being']=='astrid' and r['record_type']=='journal']
    def journal_matches(text):
        matches = []
        for row in journals:
            raw = row['raw_text']
            if text and text in raw:
                start = raw.index(text)
                matches.append(dict(canonical_name=row['canonical_name'], source_path=row['source_path'],
                    start_offset=start, end_offset=start+len(text), prefix=raw[:start], suffix=raw[start+len(text):],
                    raw_sha256=row['raw_sha256'], cached_encoding_matches_source_hash=hashlib.sha256(raw.encode()).hexdigest()==row['raw_sha256']))
        return matches
    dialogues = [item['row'] for item in bridge['queries'][1]['rows'] if json.loads(item['row']['payload'])['mode']=='dialogue_live']
    for row in dialogues:
        payload = json.loads(row['payload'])
        result['journal_matches'].append(dict(bridge_message_id=row['id'], exchange=payload['exchange'],
            text_sha256=hashlib.sha256(payload['text'].encode()).hexdigest(), matches=journal_matches(payload['text'])))
    for job in JOBS:
        if not job.endswith('journal-elaboration'):
            continue
        files = {f['filename']: f for f in companions['job_files'] if f['job_id']==job and 'error' not in f}
        prompt = files['prompt.txt']['text']
        contained = [dict(bridge_message_id=r['id'], offset=prompt.index(json.loads(r['payload'])['text']))
                     for r in dialogues if json.loads(r['payload'])['text'] in prompt]
        result['elaboration_links'].append(dict(job_id=job, prompt_path=files['prompt.txt']['path'],
            prompt_sha256=files['prompt.txt']['sha256'], contained_dialogues=contained,
            budget_accept_advice_present='Suggested NEXT: EXPERIMENT_RESEARCH_BUDGET_ACCEPT latest' in prompt,
            result_sha256=files['result.txt']['sha256'], result_matches=journal_matches(files['result.txt']['text'])))
    return result


def query(conn, sql, params, limit, metadata=False):
    plan = [list(r) for r in conn.execute('EXPLAIN QUERY PLAN ' + sql, params)]
    if not metadata and not any('SEARCH ' in row[3] for row in plan):
        raise ValueError('Refusing data query without an indexed SEARCH plan')
    start = time.monotonic()
    conn.set_progress_handler(lambda: int(time.monotonic() - start > 5), 1000)
    try:
        rows = [dict(r) for r in conn.execute(sql, params).fetchmany(limit + 1)]
    finally:
        conn.set_progress_handler(None, 0)
    retained = rows[:limit]
    return dict(sql=sql, parameters=params, query_plan=plan, row_limit=limit,
                rows_returned_before_limit=len(rows), truncated=len(rows) > limit,
                rows=[dict(row=row, sha256=hashlib.sha256(encoded(row)).hexdigest(),
                           hash_basis='exact SQLite row values encoded as UTF-8 JSON; sort_keys=True, ensure_ascii=False, separators=(comma,colon)') for row in retained])


def worker(phase):
    result = dict(schema_version=1, kind='astrid_readmore_feedback_capture', phase=phase,
                  captured_at_utc=datetime.now(timezone.utc).isoformat(), source_path=str(WORKSPACE / 'bridge.db'),
                  scope=dict(since= SINCE, until=UNTIL, since_utc='2026-09-06T16:10:00+00:00',
                             until_utc='2026-09-06T16:15:00+00:00', boundary='[since,until)',
                             access='ordinary mode=ro, five-second indexed-query budget'), queries=[])
    conn = None
    try:
        conn = sqlite3.connect((WORKSPACE / 'bridge.db').as_uri() + '?mode=ro', uri=True, timeout=3)
        conn.row_factory = sqlite3.Row
        conn.execute('BEGIN')
        if phase == 'schema':
            result['queries'].append(query(conn, "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE type IN ('table','index') ORDER BY type,name LIMIT ?", [401], 400, metadata=True))
        elif phase == 'rows':
            for sql, parameters, cap in (
                ('SELECT topic,direction,COUNT(*) AS records,MIN(timestamp) AS first_time,MAX(timestamp) AS last_time FROM bridge_messages WHERE timestamp>=? AND timestamp<? GROUP BY topic,direction ORDER BY topic,direction', [SINCE, UNTIL], 100),
                ('SELECT * FROM bridge_messages WHERE topic=? AND timestamp>=? AND timestamp<? ORDER BY timestamp,id LIMIT ?', ['consciousness.v1.autonomous', SINCE, UNTIL, 31], 30),
                ('SELECT * FROM action_events WHERE action_id>=? AND action_id<? ORDER BY action_id LIMIT ?', ['act_astrid_1788711000000', 'act_astrid_1788711300000', 31], 30),
                ('SELECT * FROM bridge_messages WHERE timestamp>=? AND timestamp<? AND topic NOT IN (?,?,?,?,?) ORDER BY timestamp,id LIMIT ?', [SINCE, UNTIL, *('consciousness.v1.' + t for t in ('sensory', 'telemetry', 'lambda_tail', 'lambda_edge_perception', 'sticky_mode_audit')), 101], 100),
            ):
                result['queries'].append(query(conn, sql, parameters, cap))
        result['status'] = 'captured'
    except (OSError, ValueError, sqlite3.Error) as exc:
        result['status'], result['error'] = 'unavailable', str(exc)
    finally:
        if conn is not None:
            conn.close()
    if phase == 'rows':
        result['name_inventories'] = []
        for root, contains in ((WORKSPACE, ''), (WORKSPACE / 'diagnostics', 'prompt'),
                               (WORKSPACE / 'llm_jobs', ''), (WORKSPACE / 'context_overflow', '')):
            names, visited, begin, truncated = [], 0, time.monotonic(), False
            try:
                with os.scandir(root) as entries:
                    for item in entries:
                        visited += 1
                        if visited > 200000 or time.monotonic() - begin > 3 or len(names) >= 300:
                            truncated = True
                            break
                        if contains in item.name:
                            names.append(item.name)
                result['name_inventories'].append(dict(path=str(root), name_filter=contains,
                    visited=visited, returned=sorted(names), truncated=truncated,
                    metadata_per_item=False, seconds_cap=3, entry_cap=200000, returned_cap=300))
            except OSError as exc:
                result['name_inventories'].append(dict(path=str(root), error=str(exc)))
    elif phase == 'files':
        result['files'] = []
        for relative in ('diagnostics/dialogue_prompt_budget.jsonl', 'llm_jobs/index.json'):
            path = WORKSPACE / relative
            try:
                if path.is_symlink():
                    raise ValueError('Symlink input refused')
                before = path.stat()
                with path.open('rb') as stream:
                    first = stream.readline(65536)
                    stream.seek(max(0, before.st_size - 65536))
                    last = stream.read(65536)
                after = path.stat()
                result['files'].append(dict(path=str(path), size=before.st_size,
                    stable=(before.st_size, before.st_mtime_ns)==(after.st_size, after.st_mtime_ns),
                    first_line=first.decode(errors='replace'), last_64k=last.decode(errors='replace'),
                    first_bytes_sha256=hashlib.sha256(first).hexdigest(), last_bytes_sha256=hashlib.sha256(last).hexdigest(),
                    note='Bounded first-line and tail samples, not whole-file coverage.'))
            except (OSError, ValueError) as exc:
                result['files'].append(dict(path=str(path), error=str(exc)))
        root = WORKSPACE / 'llm_jobs/jobs'
        names, visited, begin, truncated = [], 0, time.monotonic(), False
        try:
            with os.scandir(root) as entries:
                for item in entries:
                    visited += 1
                    if visited > 250000 or time.monotonic() - begin > 5 or len(names) >= 100:
                        truncated = True
                        break
                    match = re.search(r'^job_astrid_(\d+)_', item.name)
                    if match and SINCE * 1000 <= int(match[1]) < UNTIL * 1000:
                        names.append(item.name)
            result['job_names'] = dict(path=str(root), visited=visited, returned=sorted(names),
                truncated=truncated, selection='job_astrid_<epoch_ms>_ filename clock within [since,until)',
                metadata_per_item=False, seconds_cap=5, entry_cap=250000, returned_cap=100)
        except OSError as exc:
            result['job_names'] = dict(path=str(root), error=str(exc))
    elif phase == 'companions':
        path = WORKSPACE / 'diagnostics/dialogue_prompt_budget.jsonl'
        before = path.stat()
        cap = 32 * 1024 * 1024
        scanned_hash = hashlib.sha256()
        rows, seen, errors, clocks = [], 0, 0, []
        begin = time.monotonic()
        with path.open('rb') as stream:
            start = max(0, before.st_size - cap)
            stream.seek(start)
            skipped = stream.readline(1024 * 1024) if start else b''
            scan_start = stream.tell()
            stopped = None
            while stream.tell() < before.st_size:
                if seen >= 10000 or time.monotonic() - begin > 10:
                    stopped = 'ten-second or 10000-line cap reached'
                    break
                offset = stream.tell()
                line = stream.readline(min(1024 * 1024, before.st_size - offset))
                scanned_hash.update(line)
                seen += 1
                try:
                    row = json.loads(line)
                    timestamp = float(row['timestamp'])
                    clocks.append(timestamp)
                    if SINCE <= timestamp < UNTIL:
                        rows.append(dict(byte_offset=offset, raw_line=line.decode('utf-8'),
                            sha256=hashlib.sha256(line).hexdigest(), row=row,
                            hash_basis='exact raw line bytes, including newline'))
                except (ValueError, KeyError, UnicodeError, TypeError):
                    errors += 1
            scan_end = stream.tell()
        after = path.stat()
        result['diagnostic_tail'] = dict(path=str(path), source_size_before=before.st_size,
            source_size_after=after.st_size, mtime_ns_before=before.st_mtime_ns, mtime_ns_after=after.st_mtime_ns,
            source_changed=(before.st_size, before.st_mtime_ns)!=(after.st_size, after.st_mtime_ns),
            byte_cap=cap, scan_start=scan_start, scan_end=scan_end, skipped_partial_line_bytes=len(skipped),
            rows_examined=seen, parse_errors=errors, stopped_reason=stopped,
            first_timestamp=min(clocks) if clocks else None, last_timestamp=max(clocks) if clocks else None,
            scanned_bytes_sha256=scanned_hash.hexdigest(), rows=rows,
            note='Complete bounded suffix scan, with no assumption of chronological order; not whole-log coverage.')
        result['job_files'] = []
        for job in JOBS:
            for name in ('job.json', 'prompt.txt', 'result.txt', 'events.jsonl'):
                path = WORKSPACE / 'llm_jobs/jobs' / job / name
                try:
                    if path.is_symlink() or path.parent.is_symlink():
                        raise ValueError('Symlink input refused')
                    before = path.stat()
                    if before.st_size > 1024 * 1024:
                        raise ValueError('File exceeds one MiB cap')
                    with path.open('rb') as stream:
                        raw = stream.read(1024 * 1024 + 1)
                    after = path.stat()
                    if len(raw) > 1024 * 1024:
                        raise ValueError('File grew beyond one MiB cap')
                    result['job_files'].append(dict(path=str(path), job_id=job, filename=name,
                        size_bytes=len(raw), mtime_ns_before=before.st_mtime_ns, mtime_ns_after=after.st_mtime_ns,
                        stable=(before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),
                        sha256=hashlib.sha256(raw).hexdigest(), hash_basis='exact file bytes', text=raw.decode('utf-8')))
                except (OSError, ValueError) as exc:
                    result['job_files'].append(dict(path=str(path), job_id=job, filename=name, error=str(exc)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--phase', choices=['schema', 'rows', 'files', 'companions'])
    parser.add_argument('--out', type=Path)
    parser.add_argument('--verify-dir', type=Path)
    parser.add_argument('--episode', type=Path)
    parser.add_argument('--prior-evidence', type=Path)
    args = parser.parse_args()
    if args.verify_dir:
        if not args.episode or not args.prior_evidence:
            raise ValueError('Local verification also requires --episode and --prior-evidence')
        print(json.dumps(verify_local(args.verify_dir, args.episode, args.prior_evidence), ensure_ascii=False, indent=2))
        return
    if args.phase is None:
        raise ValueError('--phase is required for capture')
    if args.worker:
        print(encoded(worker(args.phase)).decode())
        return
    if args.out is None:
        raise ValueError('--out is required')
    out = args.out.expanduser().resolve()
    repo = Path(__file__).resolve().parent.parent
    for base in [repo.parent, Path('/Users/v/other')]:
        for name in ('astrid', 'minime', 'neural-triple-reservoir'):
            source = (base / name).resolve()
            if out == source or source in out.parents:
                raise ValueError('Output cannot be in a being source tree')
    if out.exists():
        raise ValueError('Output already exists')
    script = Path(__file__).read_bytes()
    process = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                              '-o', 'ConnectTimeout=5', 'volya',
                              shlex.join(['python3', '-B', '-', '--worker', '--phase', args.phase])],
                             input=script, capture_output=True, timeout=35)
    if process.returncode:
        raise ValueError('Source-host capture failed: ' + process.stderr.decode(errors='replace'))
    result = json.loads(process.stdout)
    result['driver_sha256'] = hashlib.sha256(script).hexdigest()
    result['source_host'] = 'volya'
    result['remote_stderr'] = process.stderr.decode(errors='replace') or None
    out.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(encoded(result) + b'\n')
    print(json.dumps(dict(output=str(out), status=result['status'], queries=len(result['queries']),
                          sha256=hashlib.sha256(out.read_bytes()).hexdigest())))


if __name__ == '__main__':
    main()
