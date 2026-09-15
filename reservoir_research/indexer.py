"""Incremental ingestion with exact source hashes, aliases, and explicit scan scope."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sqlite3

from .store import PARSER_VERSION, json_text, utc_now

MAX_BYTES = 4 * 1024 * 1024


def discover_journals(root: Path, recursive=True):
    """Use scandir; never follow links into a live workspace or unrelated directory."""
    with os.scandir(root) as iterator:
        items = sorted(iterator, key=lambda e: e.name)
    for item in items:
        if item.is_symlink():
            continue
        if item.is_dir(follow_symlinks=False):
            if recursive and not item.name.startswith('.'):
                yield from discover_journals(Path(item.path), recursive=True)
        elif item.name.endswith('.txt') and item.is_file(follow_symlinks=False):
            yield Path(item.path)


def source_id(conn, being, root, kind):
    conn.execute('INSERT OR IGNORE INTO sources(being,root,kind) VALUES (?,?,?)',
                 (being, str(root), kind))
    return conn.execute('SELECT id FROM sources WHERE being=? AND root=? AND kind=?',
                        (being, str(root), kind)).fetchone()[0]


def read_stable(path: Path):
    before = path.stat(follow_symlinks=False)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Source is not a regular non-symlink file')
    if before.st_size > MAX_BYTES:
        raise ValueError(f'Source exceeds the {MAX_BYTES}-byte file limit')
    with path.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    after = path.stat(follow_symlinks=False)
    if len(raw) > MAX_BYTES or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Source changed during read; retry on next index run')
    return raw, after


def _observe_unimported(conn, old, run, changed):
    """Retain history without presenting a known changed source as its old body."""
    if old is None:
        return 0
    conn.execute('UPDATE files SET last_seen_run=?,present=CASE WHEN ? THEN 0 ELSE present END WHERE id=?',
                 (run, int(changed), old['id']))
    return int(changed and old['present'])


def ingest_journals(conn: sqlite3.Connection, sources, *, since=None, until=None,
                    limit=None, recursive=True, rehash=False, progress=None):
    from .parsing import parse_journal
    from .explore import candidate_questions

    options = dict(sources=[(b, str(p)) for b, p in sources], since=since, until=until,
                   limit_per_source=limit, recursive=recursive, rehash=rehash,
                   parser_version=PARSER_VERSION)
    run = conn.execute('INSERT INTO runs(started_at,kind,options_json,status) VALUES (?,?,?,?)',
                       (utc_now(), 'journals', json_text(options), 'running')).lastrowid
    conn.commit()
    total = Counter()
    per_source = []
    try:
        for being, source in sources:
            root = source.expanduser().resolve()
            if not root.is_dir():
                raise ValueError(f'Journal directory not found: {root}')
            sid = source_id(conn, being, root, 'journal')
            stats = Counter()
            exhausted = True
            for path in discover_journals(root, recursive):
                if limit is not None and stats['visited'] >= limit:
                    exhausted = False
                    break
                stats['visited'] += 1
                rel = str(path.relative_to(root))
                old = None
                source_changed = False
                read_completed = False
                try:
                    old = conn.execute('''SELECT f.*,e.occurred_at,e.parser_version,e.raw_sha256
                        FROM files f JOIN entries e ON e.id=f.entry_id
                        WHERE f.source_id=? AND f.relative_path=?''', (sid, rel)).fetchone()
                    stat = path.stat(follow_symlinks=False)
                    source_changed = bool(old and (old['size_bytes'] != stat.st_size or
                                                   old['mtime_ns'] != stat.st_mtime_ns))
                    same = (old and not source_changed and
                            old['parser_version'] == PARSER_VERSION)
                    if same and old['present'] and not rehash:
                        conn.execute('UPDATE files SET last_seen_run=?,present=1,ctime_ns=?,mike_flag=? WHERE id=?',
                                     (run, stat.st_ctime_ns, int(path.name.startswith('!')), old['id']))
                        stats['unchanged'] += 1
                        continue
                    raw, stat = read_stable(path)
                    read_completed = True
                    raw_sha = hashlib.sha256(raw).hexdigest()
                    # A successful read supersedes an mtime-only change signal.
                    source_changed = bool(old and old['raw_sha256'] != raw_sha)
                    decode_warning = []
                    try:
                        text = raw.decode('utf-8-sig')
                    except UnicodeDecodeError:
                        text = raw.decode('utf-8-sig', errors='replace')
                        decode_warning = ['Invalid UTF-8 replaced for display; raw byte hash retained.']
                    entry = parse_journal(text, being, path.name)
                    when = entry['occurred_at']
                    if when is not None and ((since is not None and when < since) or
                                             (until is not None and when >= until)):
                        stats['outside_window'] += 1
                        stats['stale_mappings_invalidated'] += _observe_unimported(
                            conn, old, run, source_changed)
                        continue
                    if when is None and (since is not None or until is not None):
                        stats['unknown_time_excluded'] += 1
                        conn.execute('INSERT INTO ingest_issues(run_id,source_id,path,error) VALUES (?,?,?,?)',
                                     (run, sid, str(path), 'Unknown time excluded from time-bounded ingestion'))
                        stats['stale_mappings_invalidated'] += _observe_unimported(
                            conn, old, run, source_changed)
                        continue
                    name = path.name.lstrip('!')
                    eid = hashlib.sha256(f'{being}\0{name}\0{raw_sha}'.encode()).hexdigest()
                    body = entry['body_text']
                    warnings = entry['warnings'] + decode_warning
                    values = (eid, being, name, when, entry['time_source'], entry['lane'],
                              entry['entry_type'], entry['content_kind'], entry['header_text'], body,
                              text, raw_sha, hashlib.sha256(body.encode()).hexdigest(), entry['next_raw'],
                              entry['next_verb'], entry['contract'], json_text(entry['metadata']),
                              json_text(warnings), PARSER_VERSION)
                    existing = conn.execute('SELECT parser_version FROM entries WHERE id=?', (eid,)).fetchone()
                    if not existing or existing[0] != PARSER_VERSION or rehash:
                        conn.execute('''INSERT INTO entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                         ON CONFLICT(id) DO UPDATE SET occurred_at=excluded.occurred_at,
                         time_source=excluded.time_source,lane=excluded.lane,entry_type=excluded.entry_type,
                         content_kind=excluded.content_kind,header_text=excluded.header_text,
                         body_text=excluded.body_text,raw_text=excluded.raw_text,body_sha256=excluded.body_sha256,
                         next_raw=excluded.next_raw,next_verb=excluded.next_verb,contract=excluded.contract,
                         metadata_json=excluded.metadata_json,warnings_json=excluded.warnings_json,
                         parser_version=excluded.parser_version''', values)
                        if existing:
                            conn.execute('DELETE FROM entry_fts WHERE entry_id=?', (eid,))
                        conn.execute('INSERT INTO entry_fts(entry_id,body_text) VALUES (?,?)', (eid, body))
                        if existing:
                            conn.execute('DELETE FROM candidates WHERE entry_id=?', (eid,))
                        questions = candidate_questions(body) if entry['content_kind'] == 'prose' else []
                        for ordinal, q in enumerate(questions):
                            conn.execute('INSERT INTO candidates VALUES (?,?,?,?,?,?)',
                                         (eid, ordinal, q['kind'], q['text'], q['start_offset'], q['end_offset']))
                        stats['parsed'] += 1
                        stats['question_candidates'] += len(questions)
                    else:
                        stats['existing_content_aliases'] += 1
                    conn.execute('''INSERT INTO files(source_id,relative_path,entry_id,size_bytes,
                        mtime_ns,ctime_ns,mike_flag,last_seen_run,present) VALUES (?,?,?,?,?,?,?,?,1)
                        ON CONFLICT(source_id,relative_path) DO UPDATE SET entry_id=excluded.entry_id,
                        size_bytes=excluded.size_bytes,mtime_ns=excluded.mtime_ns,ctime_ns=excluded.ctime_ns,
                        mike_flag=excluded.mike_flag,last_seen_run=excluded.last_seen_run,present=1''',
                        (sid, rel, eid, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns,
                         int(path.name.startswith('!')), run))
                    stats['included_files'] += 1
                except (OSError, ValueError, TypeError) as exc:
                    stats['errors'] += 1
                    if old is not None and not read_completed:
                        # A write during read_stable can be newer than the stat
                        # checked above. A failed restat leaves uncertainty intact.
                        try:
                            current = path.stat(follow_symlinks=False)
                            source_changed = source_changed or (
                                old['size_bytes'] != current.st_size or
                                old['mtime_ns'] != current.st_mtime_ns)
                        except OSError:
                            pass
                    # Failed reads do not prove disappearance. Retire only mappings
                    # whose bytes or observed file fingerprint are known to differ.
                    stats['stale_mappings_invalidated'] += _observe_unimported(
                        conn, old, run, source_changed)
                    conn.execute('INSERT INTO ingest_issues(run_id,source_id,path,error) VALUES (?,?,?,?)',
                                 (run, sid, str(path), f'{type(exc).__name__}: {exc}'))
                if stats['visited'] % 250 == 0:
                    conn.commit()
                    if progress:
                        progress(being, dict(stats))
            # Only a complete, unbounded, error-free traversal establishes which old paths are absent.
            if exhausted and recursive and since is None and until is None and not stats['errors']:
                stats['paths_no_longer_seen'] = conn.execute(
                    'UPDATE files SET present=0 WHERE source_id=? AND last_seen_run<>? AND present=1',
                    (sid, run)).rowcount
            stats['limited'] = int(not exhausted)
            per_source.append(dict(being=being, root=str(root), counts=dict(stats)))
            total.update(stats)
            conn.commit()
        links = relink_generations(conn)
        summary = dict(run_id=run, counts=dict(total), sources=per_source, generation_links=links,
                       scope='Indexed files only; coverage is defined by source roots and run options.')
        conn.execute('UPDATE runs SET finished_at=?,summary_json=?,status=? WHERE id=?',
                     (utc_now(), json_text(summary), 'complete', run))
        conn.commit()
        return summary
    except BaseException as exc:
        conn.rollback()
        conn.execute('UPDATE runs SET finished_at=?,status=?,summary_json=? WHERE id=?',
                     (utc_now(), 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed',
                      json_text({'error': str(exc), 'partial_counts': dict(total)}), run))
        conn.commit()
        raise


def relink_generations(conn):
    """Candidate associations by unique exact body hash within the indexed scope.

    Record references are retained as evidence, never promoted by filename or time.
    Multiple generation candidates keep top-level attribution unknown in catalog.
    """
    conn.execute('DELETE FROM generation_links')
    linked = 0
    for g in conn.execute('SELECT * FROM generations').fetchall():
        if not g['response_sha256']:
            continue
        candidates = conn.execute('SELECT id FROM catalog WHERE being=? AND body_sha256=?',
                                  (g['being'], g['response_sha256'])).fetchall()
        if len(candidates) == 1:
            conn.execute('INSERT OR IGNORE INTO generation_links VALUES (?,?,?)',
                         (g['id'], candidates[0][0], 'unique_exact_body_hash'))
            linked += 1
    return linked


def reparse_cached(conn: sqlite3.Connection):
    """Atomically refresh all cached interpretations without reading source files.

    Current and historical entries retain their IDs, original raw text/byte hashes,
    and file mappings. Only derived parser fields, search/candidates, and generation
    associations change. A failed run is retained after rolling back every cache edit.
    The caller must finish any existing transaction before invoking this operation.
    """
    from .parsing import parse_journal
    from .explore import candidate_questions

    if conn.in_transaction:
        raise ValueError('Reparse requires a connection with no pending transaction.')
    options = {'parser_version': PARSER_VERSION, 'input': 'cached_raw_text',
               'include_historical': True, 'source_files_read': False}
    run = conn.execute('INSERT INTO runs(started_at,kind,options_json,status) VALUES (?,?,?,?)',
                       (utc_now(), 'reparse', json_text(options), 'running')).lastrowid
    conn.commit()
    counts = {'entries': 0, 'current_entries': 0, 'historical_entries': 0,
              'reparsed': 0, 'question_candidates': 0, 'generation_links': 0}
    try:
        conn.execute('BEGIN IMMEDIATE')
        # Keep only identities in memory; individual cached texts can be large.
        ids = [row[0] for row in conn.execute('SELECT id FROM entries ORDER BY id')]
        counts['entries'] = len(ids)
        counts['current_entries'] = conn.execute('SELECT COUNT(*) FROM catalog').fetchone()[0]
        counts['historical_entries'] = counts['entries'] - counts['current_entries']
        # Rebuilding all rows: clear once, avoiding an unindexed FTS entry-id scan
        # for every entry. The transaction preserves the prior index on failure.
        conn.execute('DELETE FROM entry_fts')
        conn.execute('DELETE FROM candidates')
        for eid in ids:
            old = conn.execute('SELECT being,canonical_name,raw_text,warnings_json FROM entries WHERE id=?',
                               (eid,)).fetchone()
            entry = parse_journal(old['raw_text'], old['being'], old['canonical_name'])
            # Decoding happened at ingestion. Re-parsing Unicode text cannot
            # rediscover invalid source bytes, so preserve that specific warning.
            decode_warnings = [warning for warning in json.loads(old['warnings_json'])
                               if warning == 'Invalid UTF-8 replaced for display; raw byte hash retained.']
            warnings = list(dict.fromkeys(entry['warnings'] + decode_warnings))
            body = entry['body_text']
            conn.execute('''UPDATE entries SET occurred_at=?,time_source=?,lane=?,entry_type=?,
                content_kind=?,header_text=?,body_text=?,body_sha256=?,next_raw=?,next_verb=?,
                contract=?,metadata_json=?,warnings_json=?,parser_version=? WHERE id=?''',
                         (entry['occurred_at'], entry['time_source'], entry['lane'], entry['entry_type'],
                          entry['content_kind'], entry['header_text'], body,
                          hashlib.sha256(body.encode()).hexdigest(), entry['next_raw'], entry['next_verb'],
                          entry['contract'], json_text(entry['metadata']), json_text(warnings),
                          PARSER_VERSION, eid))
            conn.execute('INSERT INTO entry_fts(entry_id,body_text) VALUES (?,?)', (eid, body))
            questions = candidate_questions(body) if entry['content_kind'] == 'prose' else []
            for ordinal, question in enumerate(questions):
                conn.execute('INSERT INTO candidates VALUES (?,?,?,?,?,?)',
                             (eid, ordinal, question['kind'], question['text'],
                              question['start_offset'], question['end_offset']))
            counts['reparsed'] += 1
            counts['question_candidates'] += len(questions)
        counts['generation_links'] = relink_generations(conn)
        summary = {'run_id': run, 'parser_version': PARSER_VERSION, 'counts': counts,
                   'scope': 'Cached current and historical entries; no source reads or freshness verification.'}
        conn.execute('UPDATE runs SET finished_at=?,summary_json=?,status=? WHERE id=?',
                     (utc_now(), json_text(summary), 'complete', run))
        conn.commit()
        return summary
    except BaseException as exc:
        conn.rollback()
        conn.execute('UPDATE runs SET finished_at=?,status=?,summary_json=? WHERE id=?',
                     (utc_now(), 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed',
                      json_text({'error': str(exc), 'rolled_back': True, 'attempted_counts': counts}), run))
        conn.commit()
        raise


def ingest_generations(conn, sources, *, limit=None, progress=None):
    from .generations import discover_generation_files, read_generation
    options = {'sources': [(b, str(p)) for b, p in sources], 'limit_per_source': limit}
    run = conn.execute('INSERT INTO runs(started_at,kind,options_json,status) VALUES (?,?,?,?)',
                       (utc_now(), 'generations', json_text(options), 'running')).lastrowid
    counts = Counter()
    conn.commit()
    try:
        for being, root in sources:
            root = root.expanduser().resolve()
            if not root.is_dir():
                raise ValueError(f'Generation source directory not found: {root}')
            sid = source_id(conn, being, root, 'generation')
            for number, path in enumerate(discover_generation_files(root)):
                if limit is not None and number >= limit:
                    counts['limited_sources'] += 1
                    break
                counts['visited'] += 1
                try:
                    source_raw, _ = read_stable(path)
                    g = read_generation(path, being)
                    checked_raw, _ = read_stable(path)
                    if source_raw != checked_raw:
                        raise ValueError('Generation record changed during import; retry next run')
                    conn.execute('''INSERT INTO generations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        ON CONFLICT(id) DO UPDATE SET occurred_at=excluded.occurred_at,lane=excluded.lane,
                        backend=excluded.backend,status=excluded.status,prompt_text=excluded.prompt_text,
                        prompt_available=excluded.prompt_available,response_text=excluded.response_text,
                        response_sha256=excluded.response_sha256,journal_refs_json=excluded.journal_refs_json,
                        metadata_json=excluded.metadata_json,warnings_json=excluded.warnings_json,
                        source_path=excluded.source_path,source_sha256=excluded.source_sha256''',
                        (g['id'], g['being'], g['occurred_at'], g['lane'], g['backend'], g['status'],
                         g['prompt_text'], g['prompt_available'], g['response_text'], g['response_sha256'],
                         json_text(g['journal_refs']), json_text(g['metadata']), json_text(g['warnings']),
                         str(path.resolve()), hashlib.sha256(source_raw).hexdigest()))
                    counts['records'] += 1
                except (OSError, ValueError, TypeError) as exc:
                    counts['errors'] += 1
                    conn.execute('INSERT INTO ingest_issues(run_id,source_id,path,error) VALUES (?,?,?,?)',
                                 (run, sid, str(path), f'{type(exc).__name__}: {exc}'))
                if counts['visited'] % 100 == 0:
                    conn.commit()
                    if progress:
                        progress(being, dict(counts))
        counts['links'] = relink_generations(conn)
        summary = {'run_id': run, 'counts': dict(counts)}
        conn.execute('UPDATE runs SET finished_at=?,summary_json=?,status=? WHERE id=?',
                     (utc_now(), json_text(summary), 'complete', run))
        conn.commit()
        return summary
    except BaseException as exc:
        conn.rollback()
        conn.execute('UPDATE runs SET finished_at=?,status=?,summary_json=? WHERE id=?',
                     (utc_now(), 'failed', json_text({'error': str(exc)}), run))
        conn.commit()
        raise
