#!/usr/bin/env python3
"""Bounded, read-only Afterimages metadata snapshot; stdlib, no runtime imports.

Run on the source host via stdin. Writes JSON only to stdout. Reads status,
recent-list and at most five immutable traces; per-being cue state and at most
the last 100 complete exposure lines within a 1 MiB tail. No journal prose,
private notes, database scans, reader commands or generation requests.
These are file observations, not an atomic cross-service snapshot or a census.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


def read_json(path, limit=4 * 1024 * 1024):
    evidence = {"path": str(path), "exists": path.exists()}
    if not evidence["exists"]:
        return None, evidence
    before = path.stat()
    if path.is_symlink() or before.st_size > limit:
        return None, {**evidence, "error": "symlink_or_size_limit"}
    raw = path.read_bytes()
    after = path.stat()
    evidence.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                    stable=(before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns))
    if not evidence["stable"]:
        return None, {**evidence, "error": "changed_during_read"}
    try:
        return json.loads(raw), evidence
    except (ValueError, UnicodeError):
        return None, {**evidence, "error": "invalid_json"}


def exposure_tail(path):
    if not path.exists():
        return {"path": str(path), "exists": False, "retained_rows": []}
    if path.is_symlink():
        return {"path": str(path), "error": "symlink"}
    with path.open("rb") as handle:
        size = handle.seek(0, 2)
        offset = max(0, size - 1024 * 1024)
        handle.seek(offset)
        raw = handle.read(size - offset)
    lines = raw.splitlines(keepends=True)
    if offset and lines:
        lines = lines[1:]
    complete = [line for line in lines if line.endswith(b"\n")]
    fields = ("afterimage_id", "opportunity_id", "receiver", "attempt_id", "backend", "model",
              "content_fingerprint", "final_messages_fingerprint", "included", "outcome", "reason",
              "recorded_at_unix_ms", "generation_id", "action_id", "job_id", "request_id")
    rows, invalid = [], 0
    for line in complete[-100:]:
        try:
            value = json.loads(line)
            rows.append({key: value[key] for key in fields if key in value})
        except (ValueError, UnicodeError, TypeError):
            invalid += 1
    return {"path": str(path), "exists": True, "bytes_at_open": size,
            "tail_offset": offset, "tail_sha256": hashlib.sha256(raw).hexdigest(),
            "complete_lines_in_tail": len(complete), "row_limit": 100,
            "truncated": bool(offset or len(complete) > 100), "invalid_retained_lines": invalid,
            "incomplete_final_line": bool(lines and not lines[-1].endswith(b"\n")),
            "retained_rows": rows,
            "outcome_counts": dict(Counter(str(row.get("outcome")) for row in rows)),
            "included_counts": dict(Counter(str(row.get("included")) for row in rows))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/Users/v/other"))
    parser.add_argument("--day", default=datetime.now(timezone.utc).date().isoformat())
    args = parser.parse_args()
    datetime.strptime(args.day, "%Y-%m-%d")
    workspaces = {"minime": args.root / "minime/workspace",
                  "astrid": args.root / "astrid/capsules/spectral-bridge/workspace"}
    archive = workspaces["minime"] / "transition_afterimages"
    worker, worker_source = read_json(archive / "status.json")
    recent, recent_source = read_json(archive / "recent.json")
    result = {"schema": "afterimage_research_readiness_v1",
              "observed_at_utc": datetime.now(timezone.utc).isoformat(),
              "day": args.day, "scope": "five recent-list traces and daily bounded exposure tails; non-atomic",
              "worker": worker, "worker_source": worker_source, "recent_source": recent_source,
              "recent_list_count": len(recent) if isinstance(recent, list) else None,
              "artifacts": [], "readers": {}}
    for row in (recent or [])[:5]:
        identifier = row.get("id", "")
        if not re.fullmatch(r"ai_\d{4}-\d{2}-\d{2}_[A-Za-z0-9_]+", identifier):
            result["artifacts"].append({"error": "invalid_id"})
            continue
        artifact, source = read_json(archive / identifier[3:13] / (identifier + ".json"))
        item = {"id": identifier, "source": source}
        if artifact:
            for key in ("origin", "status", "reasons", "session_id", "anchor_unix_ms", "measurements"):
                item[key] = artifact.get(key)
            coverage = artifact.get("coverage", {})
            item["coverage"] = {"pre_window_clipped_at_session_start": coverage.get("pre_window_clipped_at_session_start"),
                                "channels": {name: {**{k: v for k, v in value.items() if k != "gaps"},
                                                    "gap_count": len(value.get("gaps", []))}
                                             for name, value in coverage.get("channels", {}).items()}}
            item["sample_count"] = len(artifact.get("samples", []))
            item["event_sequences"] = [event.get("sequence") for event in artifact.get("events", [])]
        result["artifacts"].append(item)
    for being, workspace in workspaces.items():
        private = workspace / "transition_afterimage_memory"
        cues, source = read_json(private / "cues.json")
        opportunities = (cues or {}).get("opportunities", {})
        selections = []
        for identifier, value in opportunities.items():
            selection = value.get("selection")
            selections.append({"opportunity_id": identifier, "created_at_unix_ms": value.get("created_at_unix_ms"),
                               "selection": {k: selection.get(k) for k in ("id", "receiver", "fingerprint")} if selection else None})
        result["readers"][being] = {"cue_source": source, "enabled": (cues or {}).get("enabled"),
                                    "eligible_count": (cues or {}).get("eligible_count"),
                                    "retained_opportunities": selections,
                                    "exposure_tail": exposure_tail(private / "exposures" / (args.day + ".jsonl"))}
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
