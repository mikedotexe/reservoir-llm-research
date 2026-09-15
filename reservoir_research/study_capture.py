"""Bounded local evidence capture for study sequences; no sibling code imports.

All source access is read-only. Outputs are restricted to this research project's
outputs directory. A capture is individually stable files plus a read transaction
per database, not an atomic snapshot of both live systems.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time

from .parsing import filename_timestamp

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent
SCHEMA = "study_sequence_capture_v1"
WORKSPACES = {"astrid": ROOT / "astrid/capsules/spectral-bridge/workspace",
              "minime": ROOT / "minime/workspace"}
RELEASE_FILES = (
    "astrid/docs/steward-notes/source-study-continuity-validation/live-rollout.json",
    "astrid/.runtime/bridge-deployment/transactions/5296e20ca9e3480b9742a2f905580363/receipt.json",
    "worktrees/self-study-continuity-live-20260908/evidence/minime-reload.jsonl",
    "worktrees/self-study-continuity-live-20260908/bridge-stage-01/manifest.json",
    "worktrees/provider-observation-live-20260908/bridge-stage-01/manifest.json",
    "astrid/docs/steward-notes/source-study-v1-validation/live-rollout.json",
)
FOLLOW_THROUGH_FILES = (
    "astrid/docs/steward-notes/self-study-follow-through-validation/live-rollout.json",
    "astrid/.runtime/bridge-deployment/transactions/0061e464c05b4750b5b3ce1abf1ab0bd/receipt.json",
    "worktrees/self-study-follow-through-20260908/evidence/minime-reload.jsonl",
    "worktrees/self-study-follow-through-20260908/bridge-stage-01/manifest.json",
)
EVIDENCE_VIEW_FILES = (
    "astrid/docs/steward-notes/study-evidence-validation/live-rollout.json",
    "astrid/.runtime/bridge-deployment/transactions/aea15d045e544ebea4e732a77d560ea3/receipt.json",
    "worktrees/study-evidence-20260908/evidence/minime-reload.jsonl",
    "worktrees/study-evidence-20260908/bridge-stage-01/manifest.json",
)
JOURNAL_ROOM_FILES = (
    "astrid/docs/steward-notes/journal-room-validation/live-rollout.json",
    "astrid/.runtime/bridge-deployment/transactions/2c3d20e64bfc4afcb9526f072c355157/receipt.json",
    "worktrees/journal-room-20260909/evidence/minime-reload.jsonl",
    "worktrees/journal-room-20260909/bridge-stage-01/manifest.json",
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def encoded(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode()


def epoch(value: str) -> float:
    when = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if when.tzinfo is None:
        raise ValueError("An explicit UTC offset is required")
    return when.timestamp()


def iso(value: float) -> str:
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


class Collector:
    def __init__(self, since: float, until: float, release_profile="continuity"):
        if release_profile not in {"continuity", "follow-through", "evidence-views", "journal-room", "study-inquiries", "study-context", "study-choice"}:
            raise ValueError("Unknown release profile")
        self.release_profile = release_profile
        if not 0 < until - since <= 86400:
            raise ValueError("Capture windows must be positive and at most 24 hours")
        if until > time.time():
            raise ValueError("Freeze a completed window; the requested end is in the future")
        self.lo, self.hi = since, until
        self.records, self.errors, self.inventories = [], [], []
        self.total_bytes = 0
        self.started = time.monotonic()

    def error(self, path, error):
        self.errors.append({"path": str(path), "error": str(error)})

    def names(self, folder: Path, cap=250000):
        result, visited, complete = [], 0, False
        started = time.monotonic()
        try:
            with os.scandir(folder) as entries:
                for entry in entries:
                    visited += 1
                    if visited > cap or time.monotonic() - started > 10:
                        raise ValueError("Enumeration ceiling; inventory is partial")
                    result.append(entry.name)
            complete = True
        except (OSError, ValueError) as exc:
            self.error(folder, exc)
        self.inventories.append({"directory": str(folder), "enumerated": len(result),
                                 "complete": complete, "recursive": False})
        return sorted(result)

    def add(self, path: Path, kind: str, being=None, stamp=None):
        try:
            if time.monotonic() - self.started > 150:
                raise ValueError("Total capture time ceiling")
            if path.resolve() != path or path.is_symlink():
                raise ValueError("Symlink or noncanonical source refused")
            before = path.stat()
            if before.st_size > 8 * 1024 * 1024:
                raise ValueError("Per-file 8 MiB ceiling")
            with path.open("rb") as stream:
                raw = stream.read(8 * 1024 * 1024 + 1)
            after = path.stat()
            attrs = ("st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
            if any(getattr(before, k) != getattr(after, k) for k in attrs):
                raise ValueError("Source changed while reading")
            if len(raw) != after.st_size:
                raise ValueError("Incomplete source read")
            self.total_bytes += len(raw)
            if self.total_bytes > 160 * 1024 * 1024:
                raise ValueError("Total capture byte ceiling")
            row = dict(path=str(path), kind=kind, being=being, text=raw.decode("utf-8"),
                       sha256=sha(raw), bytes=len(raw), filename_time=stamp,
                       mtime_ns=after.st_mtime_ns)
            self.records.append(row)
            return row
        except (OSError, ValueError, UnicodeError) as exc:
            self.error(path, exc)
            return None

    def linked_study_failure(self, workspace, pointer, being):
        """Follow only a generation's bounded, local diagnostic reference."""
        if not isinstance(pointer, str) or not pointer:
            return
        path = Path(pointer)
        directory = workspace / "diagnostics/source_study_attempts"
        if path.parent != directory or not re.fullmatch(r"attempt_[a-f0-9]{32}\.json", path.name):
            self.error(path, "Out-of-scope source-study diagnostic reference refused")
            return
        if not any(row["path"] == str(path) for row in self.records):
            self.add(path, "source_study_failure", being)

    def database(self, being, workspace):
        path = workspace / "bridge.db" if being == "astrid" else ROOT / "minime/minime_consciousness.db"
        conn = None
        try:
            conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=3)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA query_only=ON")
            conn.execute("BEGIN")
            # Primary key's epoch prefix avoids scanning the large active database.
            sql = "SELECT * FROM action_events WHERE action_id>=? AND action_id<? ORDER BY action_id LIMIT ?"
            params = [f"act_{being}_{int((self.lo - 1800) * 1000)}",
                      f"act_{being}_{int(self.hi * 1000)}", 5001]
            plan = [list(r) for r in conn.execute("EXPLAIN QUERY PLAN " + sql, params)]
            if not any("SEARCH " in r[3] for r in plan):
                raise ValueError("Refusing nonindexed action query")
            start = time.monotonic()
            conn.set_progress_handler(lambda: int(time.monotonic() - start > 5), 1000)
            rows = [dict(r) for r in conn.execute(sql, params)]
            if len(rows) > 5000:
                raise ValueError("Action row ceiling")
            self.inventories.append(dict(directory=str(path), kind="action_query", sql=sql,
                                         parameters=params, plan=plan, complete=True, rows=len(rows)))
            for row in rows:
                raw = encoded(row)
                self.records.append(dict(kind="action", being=being,
                    path=f"{path}#action_events/{row['action_id']}", text=raw.decode(),
                    sha256=sha(raw), bytes=len(raw), filename_time=None))
        except (sqlite3.Error, ValueError, OSError) as exc:
            self.error(path, exc)
        finally:
            if conn:
                conn.close()

    def collect(self):
        for being, workspace in WORKSPACES.items():
            # A 30-minute lead-in preserves crossing attempts and incoming parentage.
            lo = self.lo - 1800
            for kind in ("journal", "introspections"):
                for name in self.names(workspace / kind, 50000):
                    stamp = filename_timestamp(name, being)
                    if name.endswith(".txt") and stamp is not None and lo <= stamp < self.hi:
                        self.add(workspace / kind / name, kind, being, stamp)
            day = datetime.fromtimestamp(lo, timezone.utc).date()
            last = datetime.fromtimestamp(self.hi, timezone.utc).date()
            while day <= last:
                folder = workspace / "generations" / str(day)
                for name in self.names(folder, 50000):
                    match = re.fullmatch(r"gen_(\d+)_(.+)_a\d+\.json", name)
                    if match and lo <= int(match[1]) / 1000 < self.hi:
                        self.add(folder / name, "generation", being, int(match[1]) / 1000)
                day += timedelta(days=1)
            jobs = workspace / "llm_jobs/jobs"
            for name in self.names(jobs):
                match = re.fullmatch(r"job_" + being + r"_(\d+)_.+", name)
                if match and lo <= int(match[1]) / 1000 < self.hi:
                    for companion in ("job.json", "events.jsonl", "result.txt", "prompt.txt"):
                        path = jobs / name / companion
                        if path.exists():
                            self.add(path, "job_" + companion, being, int(match[1]) / 1000)
            reader = workspace / "diagnostics/source_first_v3/shared_reader"
            self.add(reader / "reader-v1.json", "reader_state", being)
            for kind in ("deliveries", "navigation"):
                base = reader / kind
                if not base.exists():
                    self.inventories.append(dict(directory=str(base), complete=False, absent=True))
                    continue
                count = 0
                for name in self.names(base, 10000):
                    if not (base / name).is_dir() or (base / name).is_symlink():
                        continue
                    for leaf in self.names(base / name, 100):
                        if not re.fullmatch(r"[a-f0-9]{64}\.json", leaf):
                            continue
                        count += 1
                        if count > 10000:
                            raise ValueError("Reader receipt ceiling")
                        self.add(base / name / leaf, "delivery" if kind == "deliveries" else "navigation", being)
            self.database(being, workspace)
            hashes = set()
            for row in list(self.records):
                if row["kind"] == "generation" and row["being"] == being:
                    try:
                        data = json.loads(row["text"])
                        hashes.update(m["content_sha256"] for m in data.get("messages", [])
                                      if re.fullmatch(r"[a-f0-9]{64}", m.get("content_sha256", "")))
                        timing = data.get("backend_timing")
                        if isinstance(timing, dict):
                            self.linked_study_failure(workspace,
                                timing.get("source_study_diagnostic_path"), being)
                    except (ValueError, KeyError, TypeError) as exc:
                        self.error(row["path"], exc)
            for digest in sorted(hashes):
                self.add(workspace / "generations/system_prompts" / f"{digest}.txt", "system_prompt", being)

        # Older Astrid navigation predates shared navigation receipts, but its
        # protected-delivery store still retains the actual admitted wire input.
        protected = WORKSPACES["astrid"] / "diagnostics/accepted_deliveries"
        for partition in self.names(protected, 10000):
            if re.fullmatch(r"[a-f0-9]{64}", partition):
                for name in self.names(protected / partition, 100):
                    if re.fullmatch(r"[a-f0-9]{64}\.json", name):
                        self.add(protected / partition / name, "accepted_delivery", "astrid")

        spool = WORKSPACES["astrid"] / "provider_observations/20260908-live-01/events"
        for name in self.names(spool, 100000):
            match = re.fullmatch(r"(?:provider|decision)-(\d+)-.+\.json", name)
            if match and self.lo - 1800 <= int(match[1]) / 1000 < self.hi:
                self.add(spool / name, "provider_event", "astrid", int(match[1]) / 1000)
        files = RELEASE_FILES + (FOLLOW_THROUGH_FILES if self.release_profile in {"follow-through", "evidence-views", "journal-room", "study-inquiries", "study-context", "study-choice"} else ())
        if self.release_profile in {"evidence-views", "journal-room", "study-inquiries", "study-context", "study-choice"}:
            files += EVIDENCE_VIEW_FILES
        if self.release_profile in {"journal-room", "study-inquiries", "study-context", "study-choice"}:
            files += JOURNAL_ROOM_FILES
        for rel in files:
            self.add(ROOT / rel, "release")
        extensions = {"study-inquiries": ["study-inquiries"],
                      "study-context": ["study-inquiries", "study-context"],
                      "study-choice": ["study-inquiries", "study-context", "study-choice"]}.get(self.release_profile, [])
        for extension in extensions:
            rollout_path = ROOT / f"astrid/docs/steward-notes/{extension}-validation/live-rollout.json"
            self.add(rollout_path, "release")
            rollout = json.loads(rollout_path.read_text())
            activation = Path(rollout["bridge"]["activation_receipt"])
            if not activation.is_relative_to(ROOT / "astrid/.runtime/bridge-deployment/transactions"):
                raise ValueError("Unexpected activation receipt location")
            reload = Path(rollout["minime"]["receipt"])
            if not reload.is_relative_to(ROOT / f"worktrees/{extension}-20260909"):
                raise ValueError("Unexpected Minime reload receipt location")
            for path in [activation, reload,
                ROOT / f"worktrees/{extension}-20260909/bridge-stage-01/manifest.json"]:
                self.add(path, "release")
        return dict(schema=SCHEMA, captured_at=iso(time.time()),
                    selection=dict(since=iso(self.lo), until_exclusive=iso(self.hi),
                        release_profile=self.release_profile,
                        context_since=iso(self.lo - 1800), followup_seconds=1800,
                        journals="root only; filename clock; archives excluded",
                        generations="all lanes by filename completion clock with 30-minute lead-in",
                        reader="all retained source/navigation receipts; time joins offline",
                        actions="all verbs; indexed action-id clock; 30-minute lead-in",
                        atomic_snapshot=False),
                    inventories=self.inventories, errors=self.errors, records=self.records)


def new_output(path: Path):
    target = path.resolve()
    if not target.is_relative_to(REPO / "research/outputs"):
        raise ValueError("Output must be beneath this research project's research/outputs")
    target.mkdir(mode=0o700, parents=False, exist_ok=False)
    return target


def private_write(path: Path, raw: bytes):
    with path.open("xb") as stream:
        os.chmod(path, 0o600)
        stream.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", required=True)
    parser.add_argument("--until", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--release-profile", choices=("continuity", "follow-through", "evidence-views", "journal-room", "study-inquiries", "study-context", "study-choice"), default="continuity")
    parser.add_argument("--protocol", type=Path, default=REPO / "research/studies/S-008-study-to-follow-through.md")
    args = parser.parse_args()
    collector = Collector(epoch(args.since), epoch(args.until), args.release_profile)
    protocol = args.protocol.resolve()
    if not protocol.is_relative_to(REPO / "research"):
        raise ValueError("Protocol must be within this research project")
    out = new_output(args.out)
    private_write(out / "protocol.md", protocol.read_bytes())
    packet = collector.collect()
    packet["protocol_sha256"] = sha((out / "protocol.md").read_bytes())
    packet["collector_sha256"] = sha(Path(__file__).read_bytes())
    parser_source = Path(__file__).with_name("parsing.py").read_bytes()
    packet["parser_sha256"] = sha(parser_source)
    private_write(out / "parsing.py", parser_source)
    private_write(out / "collector.py", Path(__file__).read_bytes())
    raw = encoded(packet)
    private_write(out / "capture.json", raw)
    print(json.dumps(dict(path=str(out / "capture.json"), sha256=sha(raw),
                          counts=dict(Counter(r["kind"] for r in packet["records"])),
                          errors=packet["errors"]), indent=2))


if __name__ == "__main__":
    main()
