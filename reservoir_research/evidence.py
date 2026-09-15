"""Import bounded episode evidence without opening any encoded source pointer.

The extension preserves captured assertions and their provenance; importing does
not verify the original source, execution, metric ownership, or clock semantics.
Different lifecycle records and conflicting captures are retained, never replaced.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

from .store import guard_output, json_text, utc_now

EXTENSION_VERSION = 1
EXTENSION_KEY = "episode_evidence_schema_version"
MAX_BUNDLE_BYTES = 64 * 1024 * 1024
_STRINGS = ("action_id", "parent_action_id", "thread_id", "job_id", "raw_next",
            "effective_action", "route", "status", "outcome_summary")
_KINDS = {"action", "telemetry"}
_BEINGS = {"astrid", "minime"}
_DDL = (
    """CREATE TABLE IF NOT EXISTS evidence_imports(
        id TEXT PRIMARY KEY, bundle_path TEXT NOT NULL, bundle_sha256 TEXT NOT NULL,
        imported_at TEXT NOT NULL, capture_json TEXT NOT NULL, coverage_json TEXT NOT NULL,
        bundle_json TEXT NOT NULL, run_id INTEGER NOT NULL REFERENCES runs(id))""",
    """CREATE TABLE IF NOT EXISTS observations(
        id TEXT PRIMARY KEY, import_id TEXT NOT NULL REFERENCES evidence_imports(id),
        being TEXT NOT NULL, kind TEXT NOT NULL, source_record_id TEXT NOT NULL,
        occurred_at REAL, ended_at REAL, action_id TEXT, parent_action_id TEXT,
        thread_id TEXT, job_id TEXT, raw_next TEXT, effective_action TEXT, route TEXT,
        status TEXT, outcome_summary TEXT, source_path TEXT NOT NULL,
        source_sha256 TEXT NOT NULL, record_json TEXT NOT NULL)""",
    "CREATE INDEX IF NOT EXISTS observations_time ON observations(being,kind,occurred_at,ended_at)",
    "CREATE INDEX IF NOT EXISTS observations_action ON observations(being,action_id)",
)


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _identity(prefix, value):
    return prefix + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _nonblank(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonblank string.")


def _time(value, label, nullable=False):
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite epoch number{' or null' if nullable else ''}.")
    try:
        numeric = float(value)
    except OverflowError as exc:
        raise ValueError(f"{label} is outside the numeric range.") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{label} must be finite.")
    try:
        datetime.fromtimestamp(numeric, timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise ValueError(f"{label} must be within the supported calendar range.") from exc
    return numeric


def _known_pair(item):
    return (isinstance(item, dict) and isinstance(item.get("being"), str)
            and item["being"] in _BEINGS and isinstance(item.get("kind"), str)
            and item["kind"] in _KINDS)


def validate_bundle(bundle: dict) -> dict:
    """Return a normalized copy, preserving extra capture/record/provenance fields.

Optional action strings and record times become null when absent; metrics and
payload become empty objects. No source hash is recomputed from a guessed basis.
Coverage is a capture declaration, not an independently verified census.
"""
    if not isinstance(bundle, dict) or type(bundle.get("schema_version")) is not int or bundle["schema_version"] != 1:
        raise ValueError("Expected episode evidence schema_version 1.")
    if bundle.get("kind") != "reservoir_episode_evidence":
        raise ValueError("Expected kind reservoir_episode_evidence.")
    try:
        encoded = _canonical(bundle)
        encoded.encode("utf-8")
        result = json.loads(encoded)
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError("Evidence must contain finite JSON values and valid Unicode.") from exc
    if not isinstance(result.get("capture"), dict):
        raise ValueError("capture must be an object.")
    coverage = result.get("coverage")
    records = result.get("records")
    if not isinstance(coverage, list) or not coverage:
        raise ValueError("coverage must be a nonempty list.")
    if not isinstance(records, list):
        raise ValueError("records must be a list.")
    covered = set()
    for number, item in enumerate(coverage):
        label = f"coverage[{number}]"
        if not _known_pair(item):
            raise ValueError(f"{label} requires a known being and action/telemetry kind.")
        for key in ("source_path", "status"):
            _nonblank(item.get(key), f"{label}.{key}")
        item["since"] = _time(item.get("since"), f"{label}.since")
        item["until"] = _time(item.get("until"), f"{label}.until")
        if item["since"] >= item["until"]:
            raise ValueError(f"{label}.since must precede until.")
        for key in ("rows_examined", "rows_selected"):
            if type(item.get(key)) is not int or item[key] < 0:
                raise ValueError(f"{label}.{key} must be a nonnegative integer.")
        if item["rows_selected"] > item["rows_examined"]:
            raise ValueError(f"{label}.rows_selected exceeds rows_examined.")
        covered.add((item["being"], item["kind"]))
    for number, record in enumerate(records):
        label = f"records[{number}]"
        if not _known_pair(record):
            raise ValueError(f"{label} requires a known being and action/telemetry kind.")
        if (record["being"], record["kind"]) not in covered:
            raise ValueError(f"{label} has no corresponding being/kind coverage declaration.")
        _nonblank(record.get("source_record_id"), f"{label}.source_record_id")
        for key in ("occurred_at", "ended_at"):
            record[key] = _time(record.get(key), f"{label}.{key}", nullable=True)
        if record["occurred_at"] is not None and record["ended_at"] is not None and record["ended_at"] < record["occurred_at"]:
            raise ValueError(f"{label}.ended_at precedes occurred_at.")
        for key in _STRINGS:
            record.setdefault(key, None)
            if record[key] is not None and not isinstance(record[key], str):
                raise ValueError(f"{label}.{key} must be a string or null.")
        for key in ("metrics", "payload"):
            record.setdefault(key, {})
            if not isinstance(record[key], dict):
                raise ValueError(f"{label}.{key} must be an object.")
        source = record.get("source")
        if not isinstance(source, dict):
            raise ValueError(f"{label}.source must be an object.")
        for key in ("path", "hash_basis"):
            _nonblank(source.get(key), f"{label}.source.{key}")
        if not isinstance(source.get("sha256"), str) or not re.fullmatch(r"[0-9a-fA-F]{64}", source["sha256"]):
            raise ValueError(f"{label}.source.sha256 must contain 64 hexadecimal characters.")
        locator = source.get("locator")
        if not ((isinstance(locator, str) and locator.strip()) or (isinstance(locator, dict) and locator)):
            raise ValueError(f"{label}.source.locator must be a nonempty string or object.")
    return result


def _load_bundle(path, max_bytes):
    if type(max_bytes) is not int or max_bytes <= 0:
        raise ValueError("max_bytes must be a positive integer.")
    path = Path(os.path.abspath(Path(path).expanduser()))
    descriptors = []
    try:
        directory = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
        descriptors.append(directory)
        for component in path.parts[1:-1]:
            directory = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            descriptors.append(directory)
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        descriptors.append(descriptor)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
            raise ValueError("Evidence input must be a regular file within the byte limit.")
        with os.fdopen(os.dup(descriptor), "rb") as stream:
            raw = stream.read(max_bytes + 1)
        after = os.fstat(descriptor)
        if len(raw) > max_bytes or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError("Evidence input exceeded its limit or changed during read.")
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
    try:
        bundle = json.loads(raw.decode("utf-8-sig"), parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"Invalid JSON constant {token}")))
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ValueError(f"Invalid evidence JSON: {exc}") from exc
    return validate_bundle(bundle), raw, path


def read_bundle(path, max_bytes=MAX_BUNDLE_BYTES) -> dict:
    """Read and validate only the named bundle; encoded source paths stay inert."""
    return _load_bundle(path, max_bytes)[0]


def _guard_connection(conn, declared_paths=()):
    names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {"research_meta", "runs"}.issubset(names):
        raise ValueError("Episode evidence requires an existing reservoir-research cache.")
    roots = [row[0] for row in conn.execute("SELECT root FROM sources")] if "sources" in names else []
    database = next((row[2] for row in conn.execute("PRAGMA database_list") if row[1] == "main"), "")
    if database:
        target = guard_output(Path(database), roots)
        # Declared pointers can refer to remote hosts. Compare absolute local
        # spellings lexically without resolving or opening those source pointers.
        for source in declared_paths:
            if isinstance(source, str) and source.startswith("/"):
                root = Path(os.path.normpath(source))
                if target == root or root in target.parents:
                    raise ValueError(f"Research cache cannot be inside a declared evidence source: {source}")


def ensure_schema(conn) -> dict:
    """Idempotently add the versioned extension; preserve the base user_version."""
    _guard_connection(conn)
    version = conn.execute("SELECT value FROM research_meta WHERE key=?", (EXTENSION_KEY,)).fetchone()
    names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if version is not None and version[0] != str(EXTENSION_VERSION):
        raise ValueError("Unsupported episode evidence extension version.")
    if version is None and names.intersection({"evidence_imports", "observations"}):
        raise ValueError("Unversioned evidence tables already exist; refusing to replace them.")
    conn.execute("SAVEPOINT episode_evidence_schema")
    try:
        for statement in _DDL:
            conn.execute(statement)
        conn.execute("INSERT OR IGNORE INTO research_meta(key,value) VALUES (?,?)", (EXTENSION_KEY, str(EXTENSION_VERSION)))
        conn.execute("RELEASE episode_evidence_schema")
    except BaseException:
        conn.execute("ROLLBACK TO episode_evidence_schema")
        conn.execute("RELEASE episode_evidence_schema")
        raise
    return {"extension": EXTENSION_KEY, "version": EXTENSION_VERSION}


def import_evidence(conn, path) -> dict:
    """Validate first, then atomically append a capture and its unique observations.

Validation failures leave the database untouched. Failures after a valid import
starts roll back the capture/observations and retain a failed runs record. Existing
observations retain their first import_id; later containing bundles remain stored.
"""
    if conn.in_transaction:
        raise ValueError("Evidence import requires a connection with no pending transaction.")
    _guard_connection(conn)
    bundle, raw, path = _load_bundle(path, MAX_BUNDLE_BYTES)
    declared = [str(path), *(item["source_path"] for item in bundle["coverage"]),
                *(record["source"]["path"] for record in bundle["records"])]
    _guard_connection(conn, declared)
    ensure_schema(conn)
    import_id = _identity("evidence_", bundle)
    digest = hashlib.sha256(raw).hexdigest()
    options = {"path": str(path), "bundle_sha256": digest, "import_id": import_id,
               "extension_version": EXTENSION_VERSION, "source_pointers_followed": False}
    run = conn.execute("INSERT INTO runs(started_at,kind,options_json,status) VALUES (?,?,?,?)",
                       (utc_now(), "evidence_import", json_text(options), "running")).lastrowid
    conn.commit()
    counts = {"records_in_bundle": len(bundle["records"]), "imports_added": 0,
              "observations_added": 0, "observations_existing": 0}
    try:
        conn.execute("BEGIN IMMEDIATE")
        counts["imports_added"] = conn.execute("INSERT OR IGNORE INTO evidence_imports VALUES (?,?,?,?,?,?,?,?)",
            (import_id, str(path), digest, utc_now(), _canonical(bundle["capture"]),
             _canonical(bundle["coverage"]), _canonical(bundle), run)).rowcount
        for record in bundle["records"]:
            observation_id = _identity("observation_", record)
            values = (observation_id, import_id, record["being"], record["kind"], record["source_record_id"],
                      record["occurred_at"], record["ended_at"], *(record[key] for key in _STRINGS),
                      record["source"]["path"], record["source"]["sha256"], _canonical(record))
            added = conn.execute("INSERT OR IGNORE INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values).rowcount
            counts["observations_added" if added else "observations_existing"] += 1
        summary = {"run_id": run, "import_id": import_id, "bundle_sha256": digest, "counts": counts,
                   "coverage": bundle["coverage"], "source_verification": "declared_not_recomputed",
                   "scope": "Captured assertions imported; source pointers, declared source hashes, and historical deployment were not verified."}
        conn.execute("UPDATE runs SET finished_at=?,status=?,summary_json=? WHERE id=?",
                     (utc_now(), "complete", json_text(summary), run))
        conn.commit()
        return summary
    except BaseException as exc:
        conn.rollback()
        conn.execute("UPDATE runs SET finished_at=?,status=?,summary_json=? WHERE id=?",
                     (utc_now(), "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                      json_text({"error": str(exc), "rolled_back": True, "attempted_counts": counts}), run))
        conn.commit()
        raise
