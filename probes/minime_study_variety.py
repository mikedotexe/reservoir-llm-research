"""Frozen Minime journal/generation census; source access is read-only.

Capture only named-date files in a declared window, using stable bounded reads.
Analysis is descriptive: journal files, generation attempts and actions are not
interchangeable denominators. Never import live runtime code or execute NEXT.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import sqlite3
import sys
import time
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reservoir_research.parsing import filename_timestamp, parse_journal

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent / "minime/workspace"
LOCAL = ZoneInfo("America/Los_Angeles")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def stable(path):
    before = path.stat()
    if path.is_symlink() or before.st_size > 8 * 1024 * 1024:
        raise ValueError("Unbounded or linked source refused")
    raw = path.read_bytes()
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("File changed during capture")
    return raw


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def capture(out, since, until):
    if out.exists() and (out / "capture-manifest.json").exists():
        raise ValueError("Capture already exists; replay it instead")
    if not out.resolve().is_relative_to(ROOT / "research/outputs"):
        raise ValueError("Output must be inside research/outputs")
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "protocol.json", dict(
        since_utc=since.isoformat(), until_exclusive_utc=until.isoformat(),
        local_timezone=str(LOCAL), selection="All timestamped journal files in root and archive; all retained generation records in UTC date directories; linked jobs.",
        interpretation="Observational, overlapping interventions; no causal attribution from before/after rates alone.",
        close_reading="Latest 120 SELF-STUDY files; preceding 24 prose-candidate journals before noon local on September 5, 8 and 11. Choice follows filenames before reading content.",
        scope="No live writes, model calls, messages, interventions, or S-007 ledger changes."))
    errors, inventories, manifests = [], [], {}

    def retain(paths, name, kind):
        count = size = 0
        with (out / name).open("w") as stream:
            for path, stamp in paths:
                try:
                    raw = stable(path)
                    size += len(raw)
                    if size > 384 * 1024 * 1024:
                        raise ValueError("Capture byte ceiling")
                    row = dict(path=str(path), name=path.name, timestamp=stamp,
                               sha256=digest(raw), bytes=len(raw), text=raw.decode())
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                    count += 1
                except (OSError, UnicodeError, ValueError) as exc:
                    errors.append(dict(path=str(path), error=str(exc)))
        manifests[name] = dict(count=count, source_bytes=size, sha256=digest((out / name).read_bytes()), kind=kind)

    journal = WORKSPACE / "journal"
    dirs = [journal] + sorted(Path(e.path) for e in os.scandir(journal / "archive") if e.is_dir(follow_symlinks=False))
    selected = []
    for folder in dirs:
        seen = 0
        for entry in os.scandir(folder):
            seen += 1
            stamp = filename_timestamp(entry.name, "minime")
            if entry.is_file(follow_symlinks=False) and entry.name.endswith(".txt") and stamp is not None and since.timestamp() <= stamp < until.timestamp():
                selected.append((Path(entry.path), stamp))
        inventories.append(dict(path=str(folder), enumerated=seen, complete=True))
    retain(sorted(selected, key=lambda row: (row[1], str(row[0]))), "journals.jsonl", "journal")
    selected = []
    for folder in sorted((WORKSPACE / "generations").iterdir()):
        if not folder.is_dir() or not re.fullmatch(r"2026-\d\d-\d\d", folder.name):
            continue
        if not since.date().isoformat() <= folder.name <= until.date().isoformat():
            continue
        seen = 0
        for entry in os.scandir(folder):
            seen += 1
            match = re.fullmatch(r"gen_(\d+)_.+\.json", entry.name)
            if entry.is_file(follow_symlinks=False) and match:
                stamp = int(match[1]) / 1000
                if since.timestamp() <= stamp < until.timestamp():
                    selected.append((Path(entry.path), stamp))
        inventories.append(dict(path=str(folder), enumerated=seen, complete=True))
    retain(sorted(selected, key=lambda row: row[1]), "generations.jsonl", "generation")
    job_ids, system_hashes = set(), set()
    for row in load(out / "generations.jsonl"):
        record = json.loads(row["text"])
        if record.get("job_id"):
            job_ids.add(record["job_id"])
        system_hashes.update(m["content_sha256"] for m in record.get("messages", []) if re.fullmatch(r"[a-f0-9]{64}", m.get("content_sha256", "")))
    retain([(WORKSPACE / "llm_jobs/jobs" / job / "job.json", None) for job in sorted(job_ids) if re.fullmatch(r"job_minime_[A-Za-z0-9_-]+", job)], "jobs.jsonl", "job")
    retain([(WORKSPACE / "generations/system_prompts" / (sha + ".txt"), None) for sha in sorted(system_hashes)], "system-prompts.jsonl", "system_prompt")
    write_json(out / "capture-manifest.json", dict(captured_at_utc=datetime.now(timezone.utc).isoformat(), files=manifests, inventories=inventories, errors=errors))


def load(path):
    with path.open() as stream:
        for line in stream:
            row = json.loads(line)
            assert digest(row["text"].encode()) == row["sha256"], row["path"]
            yield row


def capture_actions(out):
    """Bounded indexed extraction, never a scan of the large live database."""
    if (out / "actions.jsonl").exists():
        raise ValueError("Actions already captured")
    protocol = json.loads((out / "protocol.json").read_text())
    lo = datetime.fromisoformat(protocol["since_utc"]).timestamp()
    hi = datetime.fromisoformat(protocol["until_exclusive_utc"]).timestamp()
    database = WORKSPACE.parent / "minime_consciousness.db"
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=3)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    connection.execute("BEGIN")
    inventories, count = [], 0
    try:
        with (out / "actions.jsonl").open("w") as stream:
            while lo < hi:
                end = min(lo + 86400, hi)
                sql = "SELECT * FROM action_events WHERE action_id>=? AND action_id<? ORDER BY action_id LIMIT 5001"
                params = [f"act_minime_{int(lo * 1000)}", f"act_minime_{int(end * 1000)}"]
                plan = [list(row) for row in connection.execute("EXPLAIN QUERY PLAN " + sql, params)]
                assert any("SEARCH " in row[3] for row in plan), plan
                started = time.monotonic()
                connection.set_progress_handler(lambda: int(time.monotonic()-started > 5), 1000)
                rows = [dict(row) for row in connection.execute(sql, params)]
                assert len(rows) < 5001, "Action count ceiling"
                inventories.append(dict(sql=sql, parameters=params, plan=plan, rows=len(rows)))
                for row in rows:
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                count += len(rows)
                lo = end
    finally:
        connection.close()
    write_json(out / "actions-manifest.json", dict(database=str(database), rows=count,
        sha256=digest((out / "actions.jsonl").read_bytes()), queries=inventories,
        captured_at_utc=datetime.now(timezone.utc).isoformat(),
        boundary="Indexed epoch-prefixed action IDs; later capture may contain completion updates after cutoff. Not a denominator for unrecorded actions."))
    print("captured indexed actions", count)


def capture_private(out):
    """Declared supplemental channel: WRITE journals live outside root journal/."""
    if (out / "private-journals.jsonl").exists():
        raise ValueError("Private writing already captured")
    protocol = json.loads((out / "protocol.json").read_text())
    lo = datetime.fromisoformat(protocol["since_utc"]).timestamp()
    hi = datetime.fromisoformat(protocol["until_exclusive_utc"]).timestamp()
    root = WORKSPACE / "private_writing/journal"
    selected, errors = [], []
    for entry in os.scandir(root):
        stamp = filename_timestamp(entry.name, "minime")
        if entry.is_file(follow_symlinks=False) and stamp and lo <= stamp < hi:
            selected.append((Path(entry.path), stamp))
    with (out / "private-journals.jsonl").open("w") as stream:
        for path, stamp in sorted(selected, key=lambda row: row[1]):
            try:
                raw = stable(path)
                stream.write(json.dumps(dict(path=str(path), name=path.name, timestamp=stamp,
                    sha256=digest(raw), bytes=len(raw), text=raw.decode()), ensure_ascii=False)+"\n")
            except (OSError, ValueError, UnicodeError) as exc:
                errors.append(dict(path=str(path), error=str(exc)))
    write_json(out / "private-manifest.json", dict(path=str(root), count=len(selected)-len(errors),
        sha256=digest((out / "private-journals.jsonl").read_bytes()), errors=errors,
        rationale="Generation/job audit identified separate WRITE storage. Add its completed files to broader writing denominators; initial root-journal close-reading selection remains unchanged.",
        captured_at_utc=datetime.now(timezone.utc).isoformat()))


def analyze(out):
    manifest = json.loads((out / "capture-manifest.json").read_text())
    for name, record in manifest["files"].items():
        assert digest((out / name).read_bytes()) == record["sha256"], name
    rows, duplicates, seen = [], [], {}
    for row in load(out / "journals.jsonl"):
        key = row["name"].lstrip("!")
        if key in seen:
            duplicates.append(dict(name=key, identical=seen[key] == row["sha256"]))
            if seen[key] == row["sha256"]:
                continue
        seen[key] = row["sha256"]
        parsed = parse_journal(row["text"], "minime", row["name"])
        row.update(parsed)
        row["day"] = datetime.fromtimestamp(row["timestamp"], LOCAL).date().isoformat()
        row["prefix"] = re.split(r"_2026-", key, maxsplit=1)[0]
        row["prose_candidate"] = parsed["content_kind"] == "prose" or row["prefix"] in {"self_study", "moment", "pressure", "aspiration", "daydream", "boredom", "notice", "drift", "reservoir_read", "decompose", "reservoir_resonance"}
        row["word_count"] = len(parsed["body_text"].split())
        row["question"] = re.findall(r"^STUDY_QUESTION:\s*(.*)$", parsed["body_text"], re.M)
        rows.append(row)
    by_day = defaultdict(list)
    for row in rows:
        by_day[row["day"]].append(row)
    summary = dict(schema="minime_study_variety_v1", daily=[], duplicate_files=duplicates, capture_errors=manifest["errors"])
    for day, entries in sorted(by_day.items()):
        prose = [r for r in entries if r["prose_candidate"]]
        studies = [r for r in entries if r["prefix"] == "self_study"]
        summary["daily"].append(dict(day=day, all_files=len(entries), prose_candidates=len(prose),
            file_prefix_counts=dict(Counter(r["prefix"] for r in entries)), study_files=len(studies),
            study_median_words=statistics.median(r["word_count"] for r in studies) if studies else None,
            explicit_next_counts=dict(Counter(r["next_verb"] or "none" for r in prose)),
            study_next_counts=dict(Counter(r["next_raw"] or "none" for r in studies)),
            study_title_counts=dict(Counter(r["metadata"]["title"] for r in studies))))
    studies = [r for r in rows if r["prefix"] == "self_study"]
    recent = studies[-120:]
    selected = [("latest120", r) for r in recent]
    for day in [5, 8, 11]:
        cutoff = datetime(2026, 9, day, 12, tzinfo=LOCAL).timestamp()
        selected.extend((f"sep{day:02d}_before_noon", r) for r in rows if r["prose_candidate"] and cutoff-86400 <= r["timestamp"] < cutoff)
    groups = defaultdict(list)
    for group, row in selected:
        groups[group].append(row)
    for group in groups:
        if group != "latest120":
            groups[group] = groups[group][-24:]
    with (out / "reading-pack.jsonl").open("w") as stream:
        for group, entries in groups.items():
            for row in entries:
                stream.write(json.dumps(dict(group=group, **row), ensure_ascii=False) + "\n")
    summary["reading_selection"] = {k:len(v) for k,v in groups.items()}
    summary["latest120"] = dict(start=recent[0]["name"], end=recent[-1]["name"],
        titles=dict(Counter(r["metadata"]["title"] for r in recent)),
        next=dict(Counter(r["next_raw"] or "none" for r in recent)),
        median_words=statistics.median(r["word_count"] for r in recent),
        blocked_literal_mentions=sum("blocked" in r["body_text"] for r in recent))
    write_json(out / "summary.json", summary)
    with (out / "journal-index.jsonl").open("w") as stream:
        for row in rows:
            stream.write(json.dumps({k:v for k,v in row.items() if k not in {"text","body_text","header_text"}}, ensure_ascii=False) + "\n")
    write_json(out / "analysis-manifest.json", dict(
        capture_manifest_sha256=digest((out / "capture-manifest.json").read_bytes()),
        files={name: digest((out / name).read_bytes()) for name in
               ("summary.json", "journal-index.jsonl", "reading-pack.jsonl")}))
    print(json.dumps(dict(journals=len(rows), reading_selection=summary["reading_selection"], errors=len(manifest["errors"]))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["capture", "analyze", "actions", "private"])
    parser.add_argument("out", type=Path)
    parser.add_argument("--since", default="2026-09-02T07:00:00+00:00")
    parser.add_argument("--until", default="2026-09-16T18:33:00+00:00")
    args = parser.parse_args()
    if args.mode == "capture":
        capture(args.out, datetime.fromisoformat(args.since), datetime.fromisoformat(args.until))
    if args.mode == "actions":
        capture_actions(args.out)
    elif args.mode == "private":
        capture_private(args.out)
    else:
        analyze(args.out)
