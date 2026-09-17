"""Command line entry point for local, reproducible journal research."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import __version__
from . import store


def date(value):
    if value is None:
        return None
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)
        return result.timestamp()
    except ValueError as exc:
        raise argparse.ArgumentTypeError('Use YYYY-MM-DD or an ISO timestamp; naive dates mean UTC.') from exc


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError('Must be at least 1')
    return number


def nonnegative(value):
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError('Cannot be negative')
    return number


def around_window(at, timezone_name, before_minutes=10, after_minutes=10):
    """Resolve an explicit clock query; never guess a DST fold or local timezone."""
    if before_minutes < 0 or after_minutes < 0 or before_minutes + after_minutes <= 0:
        raise ValueError('The surrounding interval must have a positive duration.')
    try:
        moment = datetime.fromisoformat(at.replace('Z', '+00:00'))
    except (ValueError, TypeError) as exc:
        raise ValueError('--at needs a full date and time, for example 2026-09-06T09:19:00.') from exc
    if 'T' not in at and ' ' not in at:
        raise ValueError('--at needs a full date and time, not a date alone.')
    try:
        zone = ZoneInfo(timezone_name) if timezone_name else None
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise ValueError('Use an IANA timezone such as America/Los_Angeles or UTC.') from exc
    if moment.tzinfo is None:
        if zone is None:
            raise ValueError('A local --at time requires --timezone; an explicit UTC offset also works.')
        candidates = set()
        for fold in (0, 1):
            aware = moment.replace(tzinfo=zone, fold=fold)
            if aware.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) == moment:
                candidates.add(aware.timestamp())
        if len(candidates) != 1:
            raise ValueError('That local time is ambiguous or nonexistent at a daylight-saving change; supply an explicit UTC offset.')
        center = candidates.pop()
    else:
        center = moment.timestamp()
    since, until = center - before_minutes * 60, center + after_minutes * 60
    try:
        datetime.fromtimestamp(since, timezone.utc)
        datetime.fromtimestamp(until, timezone.utc)
    except (ValueError, OverflowError, OSError) as exc:
        raise ValueError('The surrounding interval is outside the supported calendar range.') from exc
    return since, until, timezone_name or 'UTC'


def source(value):
    being, sep, path = value.partition('=')
    if not sep or being.lower() not in ('astrid', 'minime') or not path:
        raise argparse.ArgumentTypeError('Use astrid=/path/to/source or minime=/path/to/source')
    return being.lower(), Path(path).expanduser().resolve()


def default_sources():
    base = store.REPO.parent
    sources = [('minime', base / 'minime/workspace/journal'),
               ('astrid', base / 'astrid/capsules/spectral-bridge/workspace/journal')]
    if not all(p.is_dir() for _, p in sources):
        base = Path('/Users/v/other')
        sources = [('minime', base / 'minime/workspace/journal'),
                   ('astrid', base / 'astrid/capsules/spectral-bridge/workspace/journal')]
    return sources


def parser():
    p = argparse.ArgumentParser(description='Local research tools for Astrid and Minime. No source writes or model calls.')
    p.add_argument('--version', action='version', version=__version__)
    p.add_argument('--db', type=Path, default=store.default_db(), help='Local research SQLite cache (default: %(default)s)')
    sub = p.add_subparsers(dest='command', required=True)
    from .daily.cli import configure as configure_daily
    from .verification import configure as configure_verification
    configure_daily(sub)
    configure_verification(sub)
    archive = sub.add_parser("archive", help="Snapshot, verify or restore a private research archive")
    archive_sub = archive.add_subparsers(dest="archive_command", required=True)
    for name, argument in (("snapshot", "source"), ("verify", "snapshot"), ("restore", "snapshot")):
        command = archive_sub.add_parser(name)
        command.add_argument(argument, type=Path)
        if name != "verify":
            command.add_argument("--out", type=Path, required=True)
    index = sub.add_parser('index', help='Incrementally index source journals and question candidates')
    index.add_argument('--source', type=source, action='append', help='Repeat being=/journal/path; default discovers both siblings')
    index.add_argument('--live-only', action='store_true', help='Scan root files only; omit archive subdirectories')
    index.add_argument('--limit', type=positive, help='Maximum visited files PER SOURCE; marks partial scope')
    index.add_argument('--rehash', action='store_true', help='Reread unchanged metadata and rebuild extracted text')
    index.add_argument('--since', type=date)
    index.add_argument('--until', type=date, help='Exclusive UTC boundary')
    gen = sub.add_parser('generations', help='Import captured generation records and legacy job companions')
    gen.add_argument('--source', type=source, action='append', required=True)
    gen.add_argument('--limit', type=positive)
    evidence = sub.add_parser('evidence', help='Index a captured action/telemetry evidence bundle')
    evidence.add_argument('bundle', type=Path, help='Versioned local capture JSON; referenced source paths are never followed')
    afterimage = sub.add_parser('afterimage-trace', help='Build an inspectable Afterimage account from a bounded capture; no index required')
    afterimage.add_argument('afterimage_id', help='Exact physical Afterimage ID')
    afterimage.add_argument('--capture', type=Path, required=True, help='Local afterimage_capture_v1 JSON; source paths are evidence only')
    afterimage.add_argument('--out', type=Path, required=True, help='A new private research report directory')
    around = sub.add_parser('around', help='Reconstruct both beings around a date and time without a search term')
    around.add_argument('--at', required=True, help='Full ISO date and time; naive local times require --timezone')
    around.add_argument('--timezone', help='IANA timezone for local input and displayed times')
    around.add_argument('--before-minutes', type=nonnegative, default=10)
    around.add_argument('--after-minutes', type=nonnegative, default=10)
    around.add_argument('--limit', type=positive, default=1000, help='Maximum retained records per being and evidence kind (default: 1000)')
    around.add_argument('--out', type=Path, required=True, help='A new research report directory')
    sub.add_parser('reparse', help='Rebuild parsed fields and candidates from cached originals without source reads')
    trail = sub.add_parser('trail', help='Follow literal references through cached originals and generation records')
    trail.add_argument('--term', action='append', required=True, help='Literal case-sensitive reference; repeat to match any')
    trail.add_argument('--being', choices=['astrid','minime'], required=True)
    trail.add_argument('--since', type=date, required=True)
    trail.add_argument('--until', type=date, required=True, help='Exclusive UTC boundary')
    trail.add_argument('--limit', type=positive, default=100)
    trail.add_argument('--out', type=Path, required=True, help='A new research output directory')
    for command, help_text in [('search','Search cleaned text using a quoted FTS phrase'),
                               ('questions','List heuristic question candidates for human reading'),
                               ('recurrence','Trace exact phrase recurrence over indexed writing')]:
        s = sub.add_parser(command, help=help_text)
        if command != 'questions':
            s.add_argument('query')
        s.add_argument('--being', choices=['astrid','minime'])
        s.add_argument('--since', type=date)
        s.add_argument('--until', type=date)
        if command != 'recurrence':
            s.add_argument('--limit', type=positive, default=20)
        if command == 'questions':
            s.add_argument('--kind', choices=['explicit_question','implicit_question'])
    show = sub.add_parser('show', help='Inspect an indexed entry, source aliases, and linked provenance')
    show.add_argument('id', help='Full entry id or unique prefix (at least 8 characters)')
    show.add_argument('--raw', action='store_true', help='Include full original text rather than cleaned body alone')
    cov = sub.add_parser('coverage', help='Report actual indexed scope, missingness, duplicates, and ingestion runs')
    cov.add_argument('--output', type=Path, help='Also write report JSON locally')
    sample = sub.add_parser('sample', help='Create a reproducible reading manifest and Markdown evidence pack')
    sample.add_argument('--per-being', type=nonnegative, default=4, help='Ordinary temporal midpoint entries per being')
    sample.add_argument('--curated', action='append', default=[], help='Full id or unique prefix; repeat for curated focal entries')
    sample.add_argument('--since', type=date)
    sample.add_argument('--until', type=date)
    sample.add_argument('--context', type=nonnegative, default=2)
    sample.add_argument('--seed', default='0', help='Recorded run label; midpoint selection is deterministic')
    sample.add_argument('--out', type=Path, required=True)
    sample.add_argument('--label', default='exploratory reading', help='Human name included in the command result')
    export = sub.add_parser('export', help='Re-export a saved manifest, rejecting any indexed content drift')
    export.add_argument('manifest', type=Path)
    export.add_argument('--out', type=Path, required=True)
    return p


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=str))


def resolve_id(conn, prefix):
    if len(prefix) < 8:
        raise ValueError('Entry id prefixes must contain at least 8 characters')
    found = conn.execute('SELECT id FROM catalog WHERE id LIKE ? LIMIT 2', (prefix+'%',)).fetchall()
    if len(found) != 1:
        raise ValueError(f'Entry id {prefix!r} is missing or ambiguous')
    return found[0][0]


def query_conditions(args, alias='c'):
    parts = []; values = []
    for name, op in [('being','='), ('since','>='), ('until','<')]:
        value = getattr(args, name, None)
        if value is not None:
            parts.append(f'{alias}.{"occurred_at" if name in ("since","until") else name} {op} ?')
            values.append(value)
    return parts, values


def research_output(conn, destination):
    """Protect registered and declared source paths without opening evidence pointers."""
    roots = [r[0] for r in conn.execute('SELECT root FROM sources')]
    out = store.guard_output(destination, roots)
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if 'evidence_imports' in names:
        for row in conn.execute('SELECT coverage_json,bundle_path FROM evidence_imports'):
            declarations = [row['bundle_path']]
            declarations.extend(item.get('source_path') for item in json.loads(row['coverage_json']))
            for path in declarations:
                if isinstance(path, str) and path.startswith('/'):
                    source = Path(os.path.normpath(path))
                    if out == source or source in out.parents:
                        raise ValueError(f'Research output cannot be inside a declared evidence source: {path}')
    return out


def coverage(conn):
    grouped = [dict(r) for r in conn.execute('''SELECT being,lane,content_kind,
        strftime('%Y-%m',occurred_at,'unixepoch') AS month,COUNT(*) AS entries,
        SUM(mike_flag) AS flagged, SUM(occurred_at IS NULL) AS unknown_time,
        SUM(backend IS NULL) AS unknown_backend,SUM(prompt_available) AS exact_prompt_entries
        FROM catalog GROUP BY being,lane,content_kind,month ORDER BY being,month,lane''')]
    counts = dict(conn.execute('''SELECT COUNT(*) AS entries,
        SUM(content_kind='prose') AS prose_entries,SUM(mike_flag) AS flagged_entries,
        SUM(occurred_at IS NULL) AS unknown_time,SUM(backend IS NULL) AS unknown_backend,
        SUM(prompt_available) AS exact_prompt_entries, MIN(occurred_at) AS first_time,
        MAX(occurred_at) AS last_time FROM catalog''').fetchone())
    for key in ('prose_entries','flagged_entries','unknown_time','unknown_backend','exact_prompt_entries'):
        counts[key] = counts[key] or 0
    counts['question_candidates'] = conn.execute('SELECT COUNT(*) FROM candidates q JOIN catalog c ON c.id=q.entry_id').fetchone()[0]
    counts['question_bearing_entries'] = conn.execute('SELECT COUNT(DISTINCT entry_id) FROM candidates q JOIN catalog c ON c.id=q.entry_id').fetchone()[0]
    counts['generation_records'] = conn.execute('SELECT COUNT(*) FROM generations').fetchone()[0]
    counts['generation_links'] = conn.execute('SELECT COUNT(*) FROM generation_links').fetchone()[0]
    counts['exact_body_duplicate_groups'] = conn.execute('''SELECT COUNT(*) FROM
        (SELECT being,body_sha256 FROM catalog WHERE content_kind='prose'
         GROUP BY being,body_sha256 HAVING COUNT(*)>1)''').fetchone()[0]
    counts['source_aliases'] = conn.execute('SELECT COUNT(*) FROM files WHERE present=1').fetchone()[0]
    runs = []
    for r in conn.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 20'):
        item = dict(r)
        item['options'] = json.loads(item.pop('options_json'))
        item['summary'] = json.loads(item.pop('summary_json') or 'null')
        runs.append(item)
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    captured_evidence = {'available': 'observations' in names,
                         'note': 'Captured source slices, not live action or telemetry coverage.'}
    if captured_evidence['available']:
        captured_evidence['imports'] = conn.execute('SELECT COUNT(*) FROM evidence_imports').fetchone()[0]
        captured_evidence['records_by_being_kind'] = [dict(r) for r in conn.execute('''
            SELECT being,kind,COUNT(*) AS records,MIN(occurred_at) AS first_time,
            MAX(occurred_at) AS last_time,SUM(occurred_at IS NULL) AS unknown_time
            FROM observations GROUP BY being,kind ORDER BY being,kind''')]
    return {'schema_version': store.SCHEMA_VERSION, 'as_of_utc': store.utc_now(), 'counts': counts,
            'scope_note': 'Counts describe the indexed sources and run filters, not the entire corpus. No inferred backend, implied prompt completeness, or validated introspection labels.',
            'question_note': 'Candidate extraction is a lexical aid; rhetorical, quoted, or supplied questions may remain. Human interpretation is required.',
            'source_presence_note': 'Paths are observed during scans; only successful full unbounded recursive scans mark missing paths. ctime is not an authenticated flag time.',
            'groups': grouped, 'captured_evidence': captured_evidence,
            'sources': [dict(r) for r in conn.execute('SELECT * FROM sources')],
            'generation_statuses': [dict(r) for r in conn.execute('SELECT being,status,prompt_available,COUNT(*) AS n FROM generations GROUP BY being,status,prompt_available')],
            'recent_runs': runs, 'ingest_issues': [dict(r) for r in conn.execute('SELECT * FROM ingest_issues ORDER BY id DESC LIMIT 100')]}


def main(argv=None):
    args = parser().parse_args(argv)
    conn = None
    try:
        if args.command == "study":
            from .daily.cli import run
            emit(run(args))
            return 0
        if args.command == "verify":
            from .verification import run
            result, code = run(args)
            emit(result)
            return code
        if args.command == "archive":
            from . import archive
            try:
                if args.archive_command == "snapshot":
                    result = archive.snapshot(args.source, args.out)
                elif args.archive_command == "restore":
                    result = archive.restore(args.snapshot, args.out)
                else:
                    result = archive.verify(args.snapshot)
            except archive.ArchiveError as exc:
                raise ValueError(str(exc)) from exc
            emit(result)
            return 0
        if args.command == 'afterimage-trace':
            from .afterimages import build_afterimage_trace, export_afterimage_trace
            if args.capture.stat().st_size > 128 * 1024 * 1024:
                raise ValueError('Afterimage capture exceeds the 128 MiB input limit')
            with args.capture.open(encoding='utf-8') as stream:
                captured = json.load(stream)
            if captured.get('afterimage_id') != args.afterimage_id:
                raise ValueError('Requested Afterimage ID does not match the capture')
            result = build_afterimage_trace(captured)
            emit(export_afterimage_trace(result, args.out))
            return 0
        if args.command == 'around':
            args.since, args.until, args.timezone = around_window(
                args.at, args.timezone, args.before_minutes, args.after_minutes)
        if getattr(args,'since',None) is not None and getattr(args,'until',None) is not None and args.since >= args.until:
            raise ValueError('--since must be earlier than --until')
        writing = args.command in ('index','generations','reparse','evidence')
        sources = (args.source or default_sources()) if args.command == 'index' else args.source if args.command == 'generations' else []
        conn = store.connect(args.db, writable=writing, source_roots=[p for _,p in sources])
        from . import explore
        if args.command == 'index':
            from .indexer import ingest_journals
            result = ingest_journals(conn, sources, since=args.since, until=args.until, limit=args.limit,
                     recursive=not args.live_only, rehash=args.rehash,
                     progress=lambda b,n: print(f'{b}: {n}', file=sys.stderr, flush=True))
            result['database'] = str(args.db.expanduser().resolve())
            emit(result)
        elif args.command == 'generations':
            from .indexer import ingest_generations
            emit(ingest_generations(conn,sources,limit=args.limit))
        elif args.command == 'evidence':
            from .evidence import import_evidence
            emit(import_evidence(conn,args.bundle))
        elif args.command == 'around':
            from .episodes import collect_episode, export_episode
            out = research_output(conn,args.out)
            result = collect_episode(conn,args.since,args.until,args.timezone,args.limit)
            emit(export_episode(result,out))
        elif args.command == 'reparse':
            from .indexer import reparse_cached
            emit(reparse_cached(conn))
        elif args.command == 'trail':
            from .trails import collect_trail, export_trail
            out = research_output(conn,args.out)
            result = collect_trail(conn,args.term,args.being,args.since,args.until,args.limit)
            emit(export_trail(result,out))
        elif args.command == 'search':
            rows = explore.search(conn,args.query,args.being,args.since,args.until,args.limit)
            results = []
            for row in rows:
                item = {k:row[k] for k in ('id','being','occurred_at','lane','source_path','mike_flag',
                                          'backend','prompt_available','content_kind','rank')}
                body = row['body_text']
                position = body.casefold().find(args.query.casefold())
                start = max(0, position - 100) if position >= 0 else 0
                item['snippet'] = ('…' if start else '') + body[start:start+600] + ('…' if len(body)>start+600 else '')
                results.append(item)
            emit(results)
        elif args.command == 'recurrence':
            emit(explore.recurrence(conn,args.query,args.being,args.since,args.until))
        elif args.command == 'questions':
            where, values = query_conditions(args)
            if args.kind:
                where.append('q.kind=?'); values.append(args.kind)
            clause = ' AND '.join(where) if where else '1=1'
            rows = conn.execute(f'''SELECT c.id,c.being,c.occurred_at,c.lane,c.source_path,
                c.mike_flag,c.backend,c.prompt_available,c.body_text,q.ordinal,q.kind,q.text,
                q.start_offset,q.end_offset
                FROM candidates q JOIN catalog c ON c.id=q.entry_id WHERE {clause}
                ORDER BY c.occurred_at,c.id,q.ordinal LIMIT ?''', [*values,args.limit])
            from .segments import split_channels
            candidates = []
            for row in rows:
                item = dict(row)
                segments = split_channels(item.pop('body_text'))
                matches = [s for s in segments if s['start_offset'] <= item['start_offset']
                           and s['end_offset'] >= item['end_offset']]
                item['channel'] = matches[0]['channel'] if len(matches)==1 else 'mixed_or_unknown'
                item['reply_target'] = matches[0]['reply_target'] if len(matches)==1 else None
                candidates.append(item)
            emit({'label':'Heuristic candidates; not verified self-originated questions',
                  'channel_note':'Structural text spans, not reconstructed generation or delivery boundaries.',
                  'candidates':candidates})
        elif args.command == 'show':
            eid = resolve_id(conn,args.id)
            item = dict(conn.execute('SELECT * FROM catalog WHERE id=?',(eid,)).fetchone())
            if not args.raw: item.pop('raw_text')
            item['metadata'] = json.loads(item.pop('metadata_json'))
            item['warnings'] = json.loads(item.pop('warnings_json'))
            from .segments import split_channels
            item['segments'] = split_channels(item['body_text'])
            item['sources'] = [dict(r) for r in conn.execute('SELECT f.*,s.root FROM files f JOIN sources s ON s.id=f.source_id WHERE f.entry_id=?',(eid,))]
            item['generation_records'] = [dict(r) for r in conn.execute('SELECT g.*,l.method FROM generations g JOIN generation_links l ON l.generation_id=g.id WHERE l.entry_id=?',(eid,))]
            emit(item)
        elif args.command == 'coverage':
            result = coverage(conn)
            if args.output:
                path = research_output(conn,args.output)
                path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
                fd = os.open(path,os.O_WRONLY | os.O_CREAT | os.O_EXCL,0o600)
                with os.fdopen(fd,'w',encoding='utf-8') as stream:
                    stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            emit(result)
        elif args.command in ('sample','export'):
            out = research_output(conn,args.out)
            if args.command == 'sample':
                curated = [resolve_id(conn,i) for i in args.curated]
                manifest = explore.sample(conn,args.per_being,args.since,args.until,args.seed,args.context,curated)
                # Keep the selection fingerprint untouched; label lives with the CLI result.
            else:
                manifest = json.loads(args.manifest.read_text())
            paths = explore.export_pack(conn,manifest,out)
            emit({'label':getattr(args,'label','saved manifest'),'files':paths})
        return 0
    except (ValueError,OSError,sqlite3.Error) as exc:
        print(f'Error: {exc}',file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        message = ('Interrupted. Existing evidence is retained; incomplete outputs are not verification.'
                   if args.command in ('verify', 'study', 'archive') else
                   'Reparse interrupted. Parser edits were rolled back; cached originals are retained.'
                   if args.command == 'reparse' else
                   'Interrupted. Committed index batches are retained; rerun to resume.')
        print(message,file=sys.stderr)
        return 130
    finally:
        if conn is not None: conn.close()
