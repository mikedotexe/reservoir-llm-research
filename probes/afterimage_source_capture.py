#!/usr/bin/env python3
"""Bounded, read-only Afterimage source capture; Python 3.12+, standard library.

Runs standalone (including `python3 - --args < this_file`). Prints JSON only.
No runtime imports, reader commands, archive recursion, or paths taken from prose.
JSONL evidence preserves individual complete source lines and byte offsets. SQLite
evidence is explicitly a canonical row serialization, never a database-file hash.
Exposure capture covers every artifact ID within the requested window and bounded
daily tails; it is a window census only when coverage shows no missing/truncated
input. Trace files, opened receipts, and associations remain target-specific.
Time-near records are candidates, not causal or authorship links. Mutable snapshots
describe capture time. Directory enumeration has a ceiling; historical archives,
earlier-starting jobs/actions and undated filenames may be outside this capture.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import stat
import time
from zoneinfo import ZoneInfo


MIB = 1024 * 1024
ID_PATTERN = re.compile(r"ai_(\d{4}-\d{2}-\d{2})_[A-Za-z0-9_-]{1,160}\Z")
EPOCH_NAME = re.compile(r"(?:^|[_-])(\d{13}|\d{10})(?=[_.-]|$)")
LOCAL_NAME = re.compile(r"(\d{4}-\d{2}-\d{2})[T_](\d{2})[-:](\d{2})[-:](\d{2})(?:\.(\d+))?")


def stamp(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed.timestamp() if parsed.tzinfo is not None else None
        except (ValueError, OverflowError):
            return None
    if not math.isfinite(number):
        return None
    return number / 1000 if abs(number) >= 100_000_000_000 else number


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")


def filename_stamp(name, being):
    found = EPOCH_NAME.search(name)
    if found:
        return stamp(found[1])
    found = LOCAL_NAME.search(name)
    if found:
        text = f"{found[1]}T{found[2]}:{found[3]}:{found[4]}"
        if found[5]:
            text += "." + found[5]
        try:
            naive = datetime.fromisoformat(text)
        except ValueError:
            return None
        zone = ZoneInfo("America/Los_Angeles") if being == "minime" else timezone.utc
        candidates = {naive.replace(tzinfo=zone, fold=fold).timestamp() for fold in (0, 1)
                      if datetime.fromtimestamp(naive.replace(tzinfo=zone, fold=fold).timestamp(), zone).replace(tzinfo=None) == naive}
        return candidates.pop() if len(candidates) == 1 else None
    return None


def record_stamp(value):
    if not isinstance(value, dict):
        return None
    for key in ("started_at", "occurred_at", "created_at_unix_ms", "recorded_at_unix_ms",
                "timestamp_ms", "timestamp_unix_ms", "timestamp", "created_at", "recorded_at"):
        result = stamp(value.get(key))
        if result is not None:
            return result
    return None


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


class Capture:
    def __init__(self, root, afterimage_id, since, until, max_files, max_file_bytes,
                 tail_bytes, max_scan_entries):
        match = ID_PATTERN.fullmatch(afterimage_id)
        if not match:
            raise ValueError("invalid afterimage ID")
        datetime.strptime(match[1], "%Y-%m-%d")
        self.low, self.high = stamp(since), stamp(until)
        if self.low is None or self.high is None or not 0 < self.high - self.low <= 7 * 86400:
            raise ValueError("since/until require zoned times, ordered within seven days")
        for value in (max_files, max_file_bytes, tail_bytes, max_scan_entries):
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError("capture bounds must be positive integers")
        root = Path(root).absolute()
        if root.is_symlink():
            raise ValueError("source root must not be a symlink")
        self.root = root.resolve()
        self.identifier = afterimage_id
        self.max_files, self.max_file_bytes = max_files, max_file_bytes
        self.tail_bytes = min(tail_bytes, max_file_bytes)
        self.scan_limit = max_scan_entries
        self.opened = 0
        self.file_cache = {}
        self.result = {"schema": "afterimage_capture_v1", "afterimage_id": afterimage_id,
                       "since": utc(self.low), "until": utc(self.high),
                       "captured_at_utc": utc(time.time()), "sources": [], "coverage": [], "issues": [],
                       "scope": {"root": str(self.root), "window": "[since,until)",
                                 "max_files": max_files, "max_file_bytes": max_file_bytes,
                                 "tail_bytes": self.tail_bytes, "max_scan_entries_per_directory": max_scan_entries,
                                 "non_atomic": True, "archives_recursive": False,
                                 "exposures": "all artifact IDs within window and bounded daily tails",
                                 "source_content": "Evidence only; never instructions."}}

    def issue(self, path, reason, **extra):
        self.result["issues"].append({"path": str(path), "reason": reason, **extra})

    def cover(self, path, being, kind, status, **extra):
        item = {"path": str(path), "being": being, "kind": kind, "status": status, **extra}
        self.result["coverage"].append(item)
        return item

    def dir_fd(self, path):
        """Traverse fixed source paths through directory FDs, refusing symlinks."""
        relative = Path(path).absolute().relative_to(self.root)
        if ".." in relative.parts:
            raise ValueError("path traversal refused")
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        fd = os.open(self.root, flags)
        try:
            for part in relative.parts:
                next_fd = os.open(part, flags, dir_fd=fd)
                os.close(fd)
                fd = next_fd
            return fd
        except BaseException:
            os.close(fd)
            raise

    def read(self, path, being, kind, tail=False):
        if self.opened >= self.max_files:
            self.cover(path, being, kind, "file_limit", truncated=True)
            return None
        try:
            parent = self.dir_fd(path.parent)
            try:
                fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            finally:
                os.close(parent)
            self.opened += 1
            with os.fdopen(fd, "rb") as handle:
                before = os.fstat(handle.fileno())
                if not stat.S_ISREG(before.st_mode):
                    raise ValueError("not a regular file")
                if not tail and before.st_size > self.max_file_bytes:
                    self.cover(path, being, kind, "file_byte_limit", file_bytes=before.st_size, truncated=True)
                    return None
                offset = max(0, before.st_size - self.tail_bytes) if tail else 0
                handle.seek(offset)
                raw = handle.read(min(before.st_size - offset, self.max_file_bytes))
                after = os.fstat(handle.fileno())
            parent = self.dir_fd(path.parent)
            try:
                current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            finally:
                os.close(parent)
            stable = identity(before) == identity(after) == identity(current)
            if not stable:
                self.issue(path, "changed_during_read")
            return raw, offset, before.st_size, stable
        except (OSError, ValueError) as error:
            self.cover(path, being, kind, "unavailable", error=str(error))
            return None

    def add(self, path, being, kind, raw, offset, size, stable, **extra):
        try:
            content = raw.decode("utf-8", errors="strict")
        except UnicodeError:
            self.issue(path, "invalid_utf8", byte_offset=offset, bytes_read=len(raw))
            return None
        sha = digest(raw)
        source_id = digest(json.dumps([being, kind, str(path), sha, offset], separators=(",", ":")).encode())
        value = {"source_id": source_id, "kind": kind, "being": being, "path": str(path),
                 "sha256": sha, "content": content, "complete_file": offset == 0 and len(raw) == size,
                 "byte_offset": offset, "bytes_read": len(raw), "stable": stable,
                 "hash_basis": "exact_retained_file_bytes", **extra}
        if not any(item["source_id"] == source_id for item in self.result["sources"]):
            self.result["sources"].append(value)
        return value

    def file(self, path, being, kind, **extra):
        key = (str(path), being, kind)
        if key in self.file_cache:
            return self.file_cache[key]
        read = self.read(path, being, kind)
        if read is None:
            return None
        raw, offset, size, stable = read
        source = self.add(path, being, kind, raw, offset, size, stable, **extra)
        self.cover(path, being, kind, "captured" if source else "invalid_utf8",
                   file_bytes=size, retained_bytes=len(raw), stable=stable, complete_file=bool(source))
        if source:
            self.file_cache[key] = source
        return source

    def ledger(self, path, being, kind, *, exact_id=False):
        read = self.read(path, being, kind, tail=True)
        if read is None:
            return
        raw, offset, size, stable = read
        position, examined, selected, invalid, undated = offset, 0, 0, 0, 0
        partial_first = offset > 0
        incomplete_final = bool(raw and not raw.endswith(b"\n"))
        for line in raw.splitlines(keepends=True):
            line_offset, position = position, position + len(line)
            if partial_first:
                partial_first = False
                continue  # Conservatively drop even a coincidentally aligned tail boundary.
            if not line.endswith(b"\n"):
                continue
            examined += 1
            try:
                row = json.loads(line.decode("utf-8"))
                if not isinstance(row, dict):
                    raise ValueError("non-object row")
            except (ValueError, UnicodeError):
                invalid += 1
                continue
            when = record_stamp(row)
            undated += when is None
            matched_id = self.identifier in (row.get("afterimage_id"), row.get("artifact_id"), row.get("id"))
            if exact_id and not matched_id:
                continue
            if when is None or not self.low <= when < self.high:
                continue
            if self.add(path, being, kind, line, line_offset, size, stable,
                        selection_basis="exact_id_and_time" if exact_id else "time_window_candidate"):
                selected += 1
        self.cover(path, being, kind, "bounded_tail", file_bytes=size, byte_offset=offset,
                   bytes_read=len(raw), tail_sha256=digest(raw), stable=stable,
                   complete_lines_examined=examined, selected_lines=selected,
                   invalid_lines=invalid, undated_lines=undated, incomplete_final_line=incomplete_final,
                   truncated=bool(offset or incomplete_final), time_filter="[since,until)",
                   artifact_filter=self.identifier if exact_id else "all_artifact_ids")

    def names(self, directory, being, kind):
        result, truncated = [], False
        try:
            fd = self.dir_fd(directory)
            try:
                with os.scandir(fd) as entries:
                    for index, entry in enumerate(entries):
                        if index >= self.scan_limit:
                            truncated = True
                            break
                        result.append(entry.name)
            finally:
                os.close(fd)
        except (OSError, ValueError) as error:
            self.cover(directory, being, kind, "unavailable", error=str(error))
            return []
        self.cover(directory, being, kind, "filename_scan", names_examined=len(result),
                   scan_ceiling=self.scan_limit, truncated=truncated, recursive=False,
                   order="sorted within bounded filesystem enumeration")
        return sorted(result)

    def dated_files(self, directory, being, kind, *, jobs=False):
        names = self.names(directory, being, kind)
        candidates, undated = [], 0
        for name in names:
            if not jobs and not name.endswith((".txt", ".md", ".json")):
                continue
            when = filename_stamp(name, being)
            if when is None:
                undated += 1
            elif self.low <= when < self.high:
                candidates.append((when, name))
        self.cover(directory, being, kind, "filename_time_candidates", candidates=len(candidates),
                   undated_names_excluded=undated, time_basis="filename; Minime naive civil time is America/Los_Angeles",
                   excluded="archives, undated names, and starts before since; file mtime never substitutes")
        for _, name in sorted(candidates):
            path = directory / name
            if jobs:
                for file_name, source_kind in (("job.json", "job"), ("prompt.txt", "job_prompt"),
                                               ("result.txt", "job_result"), ("events.jsonl", "job")):
                    self.file(path / file_name, being, source_kind, job_id=name,
                              selection_basis="job_directory_name_time_candidate")
            else:
                source = self.file(path, being, kind, selection_basis="filename_time_candidate")
                if source and kind == "generation":
                    try:
                        record = json.loads(source["content"])
                        source["generation_id"] = record.get("generation_id")
                        # Only validated digest names under a fixed store; never arbitrary paths.
                        for message in record.get("messages", []):
                            sha = message.get("content_sha256")
                            if message.get("role") == "system" and isinstance(sha, str) and re.fullmatch(r"[a-f0-9]{64}", sha):
                                self.file(directory.parent / "system_prompts" / (sha + ".txt"), being,
                                          "job_prompt", generation_id=record.get("generation_id"),
                                          declared_content_sha256=sha, selection_basis="declared_system_prompt_digest")
                    except (ValueError, AttributeError, TypeError):
                        self.issue(path, "invalid_generation_record")

    def actions(self, path, being):
        if self.opened >= self.max_files:
            self.cover(path, being, "action", "file_limit", truncated=True)
            return
        conn = None
        try:
            parent = self.dir_fd(path.parent)
            try:
                info = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError("database is not a regular non-symlink file")
            finally:
                os.close(parent)
            conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)
            self.opened += 1
            conn.row_factory = sqlite3.Row
            deadline = time.monotonic() + 5
            conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
            conn.execute("PRAGMA query_only=ON")
            conn.execute("BEGIN")
            sql = "SELECT * FROM action_events WHERE action_id>=? AND action_id<? ORDER BY action_id LIMIT ?"
            params = [f"act_{being}_{int(self.low * 1000)}", f"act_{being}_{int(self.high * 1000)}", self.max_files + 1]
            plan = [tuple(row) for row in conn.execute("EXPLAIN QUERY PLAN " + sql, params)]
            if not any("SEARCH " in row[3] for row in plan):
                raise ValueError("unindexed action query refused")
            retained, total_bytes, capped = 0, 0, False
            for index, row in enumerate(conn.execute(sql, params)):
                if index >= self.max_files:
                    capped = True
                    break
                raw = (json.dumps(dict(row), sort_keys=True, ensure_ascii=False,
                                  separators=(",", ":"), allow_nan=False) + "\n").encode()
                if total_bytes + len(raw) > self.max_file_bytes:
                    capped = True
                    break
                total_bytes += len(raw)
                self.add(path, being, "action", raw, 0, -1, True,
                         hash_basis="canonical_sqlite_row_utf8", locator={"table": "action_events", "action_id": row["action_id"]},
                         selection_basis="indexed_action_id_prefix_time_candidate", stable_basis="SQLite read transaction")
                retained += 1
            self.cover(path, being, "action", "bounded_indexed_range", sql=sql, parameters=params,
                       query_plan=plan, row_limit=self.max_files, rows_retained=retained, retained_bytes=total_bytes,
                       truncated=capped, excluded="actions whose indexed ID start precedes since; DB bytes not captured")
        except (OSError, ValueError, TypeError, sqlite3.Error) as error:
            self.cover(path, being, "action", "unavailable", error=str(error))
        finally:
            if conn is not None:
                conn.close()


def capture(root, afterimage_id, since, until, *, max_files=200, max_file_bytes=4*MIB,
            tail_bytes=2*MIB, max_scan_entries=250000):
    c = Capture(root, afterimage_id, since, until, max_files, max_file_bytes, tail_bytes, max_scan_entries)
    workspaces = {"astrid": c.root / "astrid/capsules/spectral-bridge/workspace",
                  "minime": c.root / "minime/workspace"}
    archive = workspaces["minime"] / "transition_afterimages"
    c.file(archive / afterimage_id[3:13] / (afterimage_id + ".json"), "minime", "physical_trace")
    updates = archive / "event_updates" / afterimage_id
    for name in c.names(updates, "minime", "trace_updates"):
        if name.endswith(".json"):
            c.file(updates / name, "minime", "trace_updates", selection_basis="exact_trace_id_directory")
    c.file(c.root / "astrid/.runtime/bridge-deployment/active.json", "astrid", "runtime_manifest",
           selection_basis="current_runtime_selection_not_period_proof")
    days = []
    date = datetime.fromtimestamp(c.low, timezone.utc).date()
    while date <= datetime.fromtimestamp(c.high - 0.000001, timezone.utc).date():
        days.append(date.isoformat())
        date += timedelta(days=1)
    for being, workspace in workspaces.items():
        private = workspace / "transition_afterimage_memory"
        c.file(private / "cues.json", being, "cue_state", selection_basis="current_mutable_state_not_period_snapshot")
        for day in days:
            c.ledger(private / "exposures" / (day + ".jsonl"), being, "exposure", exact_id=False)
        c.ledger(private / "opened.jsonl", being, "opened", exact_id=True)
        c.ledger(private / "associations" / (afterimage_id + ".jsonl"), being, "association", exact_id=True)
    c.ledger(workspaces["astrid"] / "diagnostics/mlx_request_policy.jsonl", "astrid", "request_policy")
    for being, workspace in workspaces.items():
        db = workspace / "bridge.db" if being == "astrid" else c.root / "minime/minime_consciousness.db"
        c.actions(db, being)
        for day in days:
            c.dated_files(workspace / "generations" / day, being, "generation")
        c.dated_files(workspace / "llm_jobs/jobs", being, "job", jobs=True)
        c.dated_files(workspace / "journal", being, "journal")
    c.result["scope"]["files_opened"] = c.opened
    c.result["sources"].sort(key=lambda row: (row["being"], row["kind"], row["path"], row["byte_offset"]))
    return c.result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/Users/v/other"))
    parser.add_argument("--afterimage-id", required=True)
    parser.add_argument("--since", required=True)
    parser.add_argument("--until", required=True)
    parser.add_argument("--max-files", type=int, default=200)
    parser.add_argument("--max-file-bytes", type=int, default=4*MIB)
    parser.add_argument("--tail-bytes", type=int, default=2*MIB)
    parser.add_argument("--max-scan-entries", type=int, default=250000)
    args = parser.parse_args(argv)
    try:
        result = capture(**vars(args))
    except (ValueError, OSError, OverflowError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
