#!/usr/bin/env python3
"""Freeze clock-selected copied records for S-013–016 relevance reading.

Explicit local scratchpad only; no network, source runtime imports or model calls.
Copies the first and midpoint eligible October Astrid record in four lanes, and
the first and midpoint copied Minime record in four lanes (flags ignored in sort).
This is a descriptive sample, not a random sample or verified historical capture.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path


def capture(scratch, out):
    scratch = Path(scratch).resolve(strict=True)
    out = Path(out).absolute()
    if "research" not in out.parts or "outputs" not in out.parts or out.exists():
        raise ValueError("requires a new research/outputs destination")
    selections = []
    start = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc).timestamp() * 1000
    end = dt.datetime(2026, 10, 24, tzinfo=dt.timezone.utc).timestamp() * 1000
    astrid = scratch / "s012/astrid-jobs"
    for lane in ("journal-elaboration", "witness-context", "moment-capture", "daydream"):
        candidates = sorted(p for p in astrid.iterdir() if p.name.endswith("_" + lane)
                            and start <= int(p.name.split("_")[2]) < end
                            and (p / "prompt.txt").is_file() and (p / "result.txt").is_file())
        for position in sorted({0, len(candidates) // 2}) if candidates else []:
            p = candidates[position]
            selections.append({"being": "astrid", "lane": lane, "id": p.name,
                               "candidate_count": len(candidates), "selected_position": position,
                               "prompt_scope": "copied prompt.txt; separate system message not verified",
                               "files": [f for f in (p / "prompt.txt", p / "result.txt", p / "job.json") if f.is_file()]})
    minime = scratch / "beings-sample/minime-week"
    for lane in ("journal", "introspect", "daydream", "moment"):
        candidates = sorted((p for p in minime.iterdir() if p.name.lstrip("!").startswith(lane + "_")),
                            key=lambda p: p.name.lstrip("!"))
        for position in sorted({0, len(candidates) // 2}) if candidates else []:
            p = candidates[position]
            selections.append({"being": "minime", "lane": lane, "id": p.name,
                               "candidate_count": len(candidates), "selected_position": position,
                               "prompt_scope": "journal only; not exact generation input", "files": [p]})
    # Validate and read once before creating any destination.
    retained = []
    total = 0
    for item in selections:
        rows = []
        for source in item["files"]:
            if source.is_symlink() or not source.resolve().is_relative_to(scratch):
                raise ValueError("source escapes explicit scratchpad")
            before = source.stat()
            if before.st_size > 1024 * 1024:
                raise ValueError("record exceeds 1 MiB")
            data = source.read_bytes()
            after = source.stat()
            if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
                raise ValueError("source changed during capture")
            total += len(data)
            if total > 32 * 1024 * 1024:
                raise ValueError("snapshot exceeds 32 MiB")
            relative = f"records/{item['being']}/{item['id']}/{source.name}"
            retained.append((relative, data))
            rows.append({"source": str(source), "path": relative, "bytes": len(data),
                         "sha256": hashlib.sha256(data).hexdigest()})
        item["files"] = rows
    out.mkdir(parents=True)
    for relative, data in retained:
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as f:
            f.write(data)
    manifest = {"schema_version": 1, "selection": "first and midpoint by clock; never by outcome or hand flag",
                "source_root": str(scratch), "source_binding": "locally retained copy; historical capture hashes unavailable",
                "records": selections, "record_count": len(selections), "file_count": len(retained), "bytes": total,
                "s008": "two anchors specified in S-008-durable-correction-protocol.md; sealed raw packets unavailable in this checkout"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = capture(args.scratch, args.out)
    print(json.dumps({k: result[k] for k in ("record_count", "file_count", "bytes", "source_binding")}))
