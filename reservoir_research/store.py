"""SQLite research cache. Source trees are only read, never used as database destinations."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timezone

SCHEMA_VERSION = 1
PARSER_VERSION = 2
REPO = Path(__file__).resolve().parent.parent


def default_db() -> Path:
    """Keep SQLite off the SMB source mount and isolate separate repo copies."""
    key = hashlib.sha256(str(REPO).encode()).hexdigest()[:12]
    return Path.home() / ".cache" / "reservoir-research" / key / "index.sqlite3"


def protected_roots() -> list[Path]:
    return [p.resolve() for base in (REPO.parent, Path('/Users/v/other'))
            for name in ('minime', 'astrid', 'neural-triple-reservoir')
            if (p := base / name).exists()]


def guard_output(path: Path, source_roots=()) -> Path:
    target = path.expanduser().resolve()
    for root in [*protected_roots(), *(Path(p).resolve() for p in source_roots)]:
        if target == root or root in target.parents:
            raise ValueError(f'Research output cannot be inside a source tree: {root}')
    return target


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_text(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def connect(path: Path, *, writable=False, source_roots=()) -> sqlite3.Connection:
    path = guard_output(path, source_roots)
    if writable:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not path.exists():
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        conn = sqlite3.connect(path, timeout=15)
    else:
        if not path.is_file():
            raise ValueError(f'No index at {path}. Run the index command first.')
        conn = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if names and 'research_meta' not in names:
        conn.close()
        raise ValueError('This database is not a reservoir-research index; refusing to modify it.')
    if names:
        version = conn.execute('PRAGMA user_version').fetchone()[0]
        if version != SCHEMA_VERSION:
            conn.close()
            raise ValueError(f'Unsupported index schema {version}; expected {SCHEMA_VERSION}.')
    elif not writable:
        conn.close()
        raise ValueError('Index has no schema. Run the index command first.')
    if writable and 'sources' in names:
        try:
            guard_output(path, [r[0] for r in conn.execute('SELECT root FROM sources')])
        except ValueError:
            conn.close()
            raise
    if writable:
        # DELETE journaling also tolerates a user-selected destination without WAL support.
        conn.execute('PRAGMA journal_mode=DELETE')
        conn.executescript(SCHEMA)
        conn.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
        conn.execute("INSERT OR IGNORE INTO research_meta VALUES ('created_at', ?)", (utc_now(),))
        conn.commit()
    return conn


SCHEMA = '''
CREATE TABLE IF NOT EXISTS research_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sources(
 id INTEGER PRIMARY KEY, being TEXT NOT NULL, root TEXT NOT NULL, kind TEXT NOT NULL,
 UNIQUE(being,root,kind));
CREATE TABLE IF NOT EXISTS runs(
 id INTEGER PRIMARY KEY, started_at TEXT NOT NULL, finished_at TEXT, kind TEXT NOT NULL,
 options_json TEXT NOT NULL, summary_json TEXT, status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS entries(
 id TEXT PRIMARY KEY, being TEXT NOT NULL, canonical_name TEXT NOT NULL,
 occurred_at REAL, time_source TEXT, lane TEXT, entry_type TEXT, content_kind TEXT NOT NULL,
 header_text TEXT NOT NULL, body_text TEXT NOT NULL, raw_text TEXT NOT NULL,
 raw_sha256 TEXT NOT NULL, body_sha256 TEXT NOT NULL, next_raw TEXT, next_verb TEXT,
 contract TEXT, metadata_json TEXT NOT NULL, warnings_json TEXT NOT NULL,
 parser_version INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS entries_time ON entries(being,occurred_at,id);
CREATE INDEX IF NOT EXISTS entries_body_hash ON entries(being,body_sha256);
CREATE INDEX IF NOT EXISTS entries_name ON entries(being,canonical_name);
CREATE TABLE IF NOT EXISTS files(
 id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL REFERENCES sources(id),
 relative_path TEXT NOT NULL, entry_id TEXT NOT NULL REFERENCES entries(id),
 size_bytes INTEGER NOT NULL, mtime_ns INTEGER NOT NULL, ctime_ns INTEGER NOT NULL,
 mike_flag INTEGER NOT NULL, last_seen_run INTEGER REFERENCES runs(id),
 present INTEGER NOT NULL DEFAULT 1, UNIQUE(source_id,relative_path));
CREATE INDEX IF NOT EXISTS files_entry ON files(entry_id,present);
CREATE TABLE IF NOT EXISTS candidates(
 entry_id TEXT NOT NULL REFERENCES entries(id), ordinal INTEGER NOT NULL,
 kind TEXT NOT NULL, text TEXT NOT NULL, start_offset INTEGER, end_offset INTEGER,
 PRIMARY KEY(entry_id,ordinal));
CREATE VIRTUAL TABLE IF NOT EXISTS entry_fts USING fts5(entry_id UNINDEXED,body_text);
CREATE TABLE IF NOT EXISTS ingest_issues(
 id INTEGER PRIMARY KEY,run_id INTEGER NOT NULL REFERENCES runs(id),
 source_id INTEGER REFERENCES sources(id),path TEXT NOT NULL,error TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS generations(
 id TEXT PRIMARY KEY,being TEXT NOT NULL,occurred_at REAL,lane TEXT,backend TEXT,
 status TEXT,prompt_text TEXT,prompt_available INTEGER NOT NULL,response_text TEXT,
 response_sha256 TEXT,journal_refs_json TEXT NOT NULL,metadata_json TEXT NOT NULL,
 warnings_json TEXT NOT NULL,source_path TEXT NOT NULL,source_sha256 TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS generation_links(
 generation_id TEXT NOT NULL REFERENCES generations(id),entry_id TEXT NOT NULL REFERENCES entries(id),
 method TEXT NOT NULL, PRIMARY KEY(generation_id,entry_id));
CREATE INDEX IF NOT EXISTS generation_links_entry ON generation_links(entry_id);
DROP VIEW IF EXISTS catalog;
CREATE VIEW catalog AS
 SELECT e.*,
 (SELECT MAX(f.mike_flag) FROM files f WHERE f.entry_id=e.id AND f.present=1) AS mike_flag,
 (SELECT s.root || '/' || f.relative_path FROM files f JOIN sources s ON s.id=f.source_id
  WHERE f.entry_id=e.id AND f.present=1 ORDER BY f.last_seen_run DESC,f.id DESC LIMIT 1) AS source_path,
 (SELECT CASE WHEN COUNT(*)=1 THEN MAX(g.backend) ELSE NULL END
  FROM generations g JOIN generation_links l ON l.generation_id=g.id WHERE l.entry_id=e.id) AS backend,
 COALESCE((SELECT CASE WHEN COUNT(*)=1 THEN MAX(g.prompt_available) ELSE 0 END FROM generations g JOIN generation_links l
  ON l.generation_id=g.id WHERE l.entry_id=e.id),0) AS prompt_available
 FROM entries e WHERE EXISTS(SELECT 1 FROM files f WHERE f.entry_id=e.id AND f.present=1);
'''
