#!/usr/bin/env python3
"""Capture a bounded, read-only source trace for the regulator self-study.

Standard library only. Reads source files, never imports Minime's runtime or
opens its databases. Source hashes identify observed working-tree bytes, not
the deployed engine or the historical generation's loaded Python module.
Run: python3 -B probes/regulator_self_study_source.py --output PATH
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RANGES = {
    "minime/src/regulator.rs": [(1, 6)],
    "minime/src/regulator/core.rs": [(1, 24)],
    "minime/src/regulator/core/pi.rs": [
        (5, 30), (72, 90), (115, 145), (171, 180), (217, 248),
        (270, 344), (399, 406),
    ],
    "minime/src/runtime/orchestration.rs": [
        (588, 589), (640, 669), (2105, 2143), (2195, 2226),
        (3956, 3973), (4002, 4015),
    ],
    "minime/src/rescue_scaffold.rs": [
        (17, 26), (1532, 1550), (1655, 1681),
    ],
    "minime_autonomy/runtime.py": [
        (20499, 20533), (21353, 21394), (21611, 21636), (21678, 21690),
        (23157, 23191), (23255, 23294), (23387, 23412),
        (30567, 30580), (31422, 31563), (51547, 51561),
        (51693, 51699), (51717, 51762), (51917, 51942),
        (52115, 52119), (52171, 52204), (53625, 53674),
        (53878, 53958), (54294, 54316), (54600, 54615),
        (54658, 54735), (55387, 55459), (55692, 55730),
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root", type=Path,
        default=Path("/Volumes/M3 Volya._smb._tcp.local/other/minime"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    repo = Path(__file__).resolve().parents[1]
    if not output.is_relative_to(repo / 'research/outputs') or output.exists():
        parser.error('--output must be a new file under research/outputs')
    observed = datetime.now(timezone.utc).isoformat()
    files = []
    for relative, ranges in RANGES.items():
        path = args.source_root / relative
        before = path.read_bytes()
        stat = path.stat()
        lines = before.decode("utf-8").splitlines()
        after = path.read_bytes()
        if before != after:
            raise RuntimeError(f"Source changed during capture: {path}")
        files.append({
            "source_path": str(path), "relative_path": relative,
            "sha256": hashlib.sha256(before).hexdigest(),
            "byte_count": len(before), "line_count": len(lines),
            "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "stable_across_two_reads": True,
            "excerpts": [
                {"start_line": start, "end_line": min(end, len(lines)),
                 "text": "\n".join(lines[start - 1:end])}
                for start, end in ranges
            ],
        })
    result = {
        "schema": "regulator_self_study_source_trace_v1",
        "observed_at_utc": observed,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": str(args.source_root),
        "scope": "Six named current source files; no data records or live services accessed.",
        "identity_limit": "Working-tree bytes only; historical loaded code and engine identity unresolved.",
        "files": files,
    }
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with output.open('x') as handle:
        handle.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    output.chmod(0o600)
    print(json.dumps({
        "output": str(args.output.resolve()), "observed_at_utc": observed,
        "source_files": len(files),
        "files": [{key: item[key] for key in ("relative_path", "sha256", "line_count")}
                  for item in files],
    }, indent=2))


if __name__ == "__main__":
    main()
