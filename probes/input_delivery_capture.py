#!/usr/bin/env python3
"""Read a bounded primary sensory-delivery ledger slice for captured delivery IDs.

Standard library only. Sends this reader via SSH stdin to python3 -B; creates no
remote files and imports no being runtime. Byte bisection assumes approximate
recorded-time ordering, so missing matches are unknown outside the declared scan.
The source file is statted before any content read; the total read cap is 16 MiB.
"""
import argparse
import base64
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import time


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stat_dict(s):
    return {"size": s.st_size, "mtime_ns": s.st_mtime_ns,
            "inode": s.st_ino, "device": s.st_dev}


def collect(args):
    requests = json.loads(base64.b64decode(args.requests_b64))
    wanted = {r["delivery_id"]: r for r in requests}
    lower = min(r["sent_at_unix_ms"] for r in requests) - 60000
    upper = max(r["sent_at_unix_ms"] for r in requests) + 60000
    started, began = utc(), time.monotonic()
    result = {"schema_version": 1, "kind": "input_delivery_capture",
              "source_path": args.source_path, "started_at_utc": started,
              "requested_ids": requests, "records": [], "seek_probes": [],
              "scope": {"recorded_at_target_start_ms": lower,
                        "recorded_at_target_end_ms": upper,
                        "max_bytes": args.max_bytes, "max_seconds": 30,
                        "search_method": "recorded_at_unix_ms byte bisection with 256 KiB padding",
                        "limitation": "Approximate file time ordering is assumed for location only. Exact IDs select records. No whole-ledger completeness or causal application claim."}}
    count = 0
    with open(args.source_path, "rb") as f:
        before = os.fstat(f.fileno())
        result["source_stat_before"] = stat_dict(before)

        def read_line():
            nonlocal count
            if time.monotonic() - began > 30:
                raise RuntimeError("capture time cap reached")
            allowance = min(131072, args.max_bytes - count)
            if allowance <= 0:
                raise RuntimeError("capture byte cap reached")
            raw = f.readline(allowance)
            count += len(raw)
            if raw and not raw.endswith(b"\n") and f.tell() < before.st_size:
                raise RuntimeError("oversize/incomplete line in selected bytes")
            return raw

        def sample(offset):
            f.seek(offset)
            if offset:
                read_line()  # discard the intersected line; offsets below are exact
            pos = f.tell()
            raw = read_line()
            if not raw:
                return pos, None
            payload = json.loads(raw)
            stamp = payload.get("recorded_at_unix_ms")
            if not isinstance(stamp, (int, float)):
                raise RuntimeError("sample lacks numeric recorded_at_unix_ms")
            result["seek_probes"].append({"byte_start": pos, "byte_end": f.tell(),
                                          "recorded_at_unix_ms": stamp,
                                          "raw_line_sha256": sha(raw)})
            return pos, stamp

        def locate(target):
            lo, hi = 0, before.st_size
            for _ in range(32):
                if hi - lo <= 262144:
                    break
                mid = (lo + hi) // 2
                pos, stamp = sample(mid)
                if stamp is None or stamp >= target:
                    hi = mid
                else:
                    lo = max(mid + 1, pos)
            return lo, hi

        lo, _ = locate(lower)
        _, hi = locate(upper)
        start, stop = max(0, lo - 262144), min(before.st_size, hi + 262144)
        if stop - start > args.max_bytes - count:
            result["scope"]["candidate_byte_start"] = start
            result["scope"]["candidate_byte_end"] = stop
            result["status"] = "candidate_region_exceeds_remaining_byte_cap"
        else:
            f.seek(start)
            if start:
                read_line()
            scan_start = f.tell()
            digest = hashlib.sha256()
            lines, errors, backwards = 0, 0, 0
            previous, earliest, latest = None, None, None
            while f.tell() < stop:
                offset = f.tell()
                raw = read_line()
                if not raw:
                    break
                digest.update(raw)
                lines += 1
                try:
                    payload = json.loads(raw)
                except (ValueError, UnicodeDecodeError):
                    errors += 1
                    continue
                stamp = payload.get("recorded_at_unix_ms")
                if isinstance(stamp, (int, float)):
                    backwards += int(previous is not None and stamp < previous)
                    previous = stamp
                    earliest = stamp if earliest is None else min(earliest, stamp)
                    latest = stamp if latest is None else max(latest, stamp)
                identity = payload.get("delivery_id")
                if identity not in wanted:
                    continue
                result["records"].append({
                    "row_id": "sensory-delivery:byte:" + str(offset),
                    "source_locator": {"byte_start": offset, "byte_end": f.tell(),
                                       "line_number_within_scanned_region": lines,
                                       "absolute_line_number": None},
                    "bridge_row_ids": wanted[identity]["bridge_row_ids"],
                    "raw_line_utf8": raw.decode("utf-8"),
                    "raw_line_sha256": sha(raw), "payload": payload,
                    "payload_hash_matches_bridge": payload.get("payload_sha256")
                        == wanted[identity]["payload_sha256"]})
            result["scope"].update({"byte_start": scan_start, "byte_end": f.tell(),
                "scan_sha256": digest.hexdigest(), "scan_hash_basis": "exact bytes in [byte_start, byte_end)",
                "scanned_lines": lines, "json_decode_errors": errors,
                "backwards_recorded_time_steps": backwards,
                "scanned_recorded_time_min_ms": earliest, "scanned_recorded_time_max_ms": latest})
            result["status"] = "bounded_region_captured"
        result["source_stat_after"] = stat_dict(os.fstat(f.fileno()))
    result["bytes_read_including_seek_probes"] = count
    result["finished_at_utc"] = utc()
    result["elapsed_seconds"] = time.monotonic() - began
    events, statuses, per_id = Counter(), Counter(), defaultdict(list)
    for r in result["records"]:
        p = r["payload"]
        events[p.get("event", "missing")] += 1
        if p.get("event") == "receipt_verified":
            statuses[p.get("status", "missing")] += 1
        per_id[p["delivery_id"]].append(r)
    summary = {"requested_delivery_ids": len(wanted), "matched_delivery_ids": len(per_id),
               "matched_event_rows": len(result["records"]), "event_rows_by_event": dict(events),
               "receipt_rows_by_status": dict(statuses),
               "missing_delivery_ids": sorted(set(wanted) - set(per_id)),
               "payload_hash_mismatch_rows": sum(not r["payload_hash_matches_bridge"] for r in result["records"])}
    summary["ids_with_verified_receipt"] = sum(any(r["payload"].get("event") == "receipt_verified" for r in rs) for rs in per_id.values())
    result["summary"] = summary
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bridge", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--source-host", default="volya")
    p.add_argument("--source-path", default="/Users/v/other/astrid/capsules/spectral-bridge/workspace/diagnostics/sensory_delivery_v1/events.jsonl")
    p.add_argument("--max-bytes", type=int, default=16 * 1024 * 1024)
    p.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--requests-b64", help=argparse.SUPPRESS)
    args = p.parse_args()
    if not 0 < args.max_bytes <= 16 * 1024 * 1024:
        p.error("max-bytes must be 1 through 16777216")
    if args.worker:
        collect(args)
        return
    if not args.bridge or not args.out:
        p.error("--bridge and --out are required")
    repo = Path(__file__).resolve().parents[1]
    out = args.out.resolve()
    if repo / "research" / "outputs" not in out.parents:
        p.error("output must be under this repository's research/outputs")
    if out.exists():
        p.error("output exists; select a new output")
    raw = args.bridge.read_bytes()
    data = json.loads(raw)
    requests = {}
    for row in data["tables"]["bridge_messages"]["rows"]:
        payload = json.loads(row["payload"])
        delivery = payload.get("delivery_v1")
        if not isinstance(delivery, dict):
            continue
        identity = delivery["delivery_id"]
        if identity not in requests:
            requests[identity] = {"delivery_id": identity, "bridge_row_ids": [],
                                  "payload_sha256": delivery["payload_sha256"],
                                  "sent_at_unix_ms": delivery["sent_at_unix_ms"]}
        if requests[identity]["payload_sha256"] != delivery["payload_sha256"]:
            raise ValueError("conflicting bridge hashes for delivery identity")
        requests[identity]["bridge_row_ids"].append(row["id"])
    if not requests:
        raise ValueError("no delivery IDs in captured bridge messages")
    encoded = base64.b64encode(json.dumps(list(requests.values())).encode()).decode()
    command = ["python3", "-B", "-", "--worker", "--requests-b64", encoded,
               "--source-path", args.source_path, "--max-bytes", str(args.max_bytes)]
    code = Path(__file__).read_bytes()
    process = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
                              "-o", "StrictHostKeyChecking=yes", args.source_host,
                              shlex.join(command)], input=code, capture_output=True,
                             timeout=40, check=True)
    result = json.loads(process.stdout)
    result.update({"source_host": args.source_host, "driver_sha256": sha(code),
                   "bridge_capture_path": str(args.bridge.resolve()), "bridge_capture_sha256": sha(raw),
                   "remote_stderr": process.stderr.decode(errors="replace") or None,
                   "access": "SSH stdin Python -B, source-file reads only, no remote writes"})
    out.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"out": str(out), "status": result["status"],
                      "summary": result["summary"], "scope": result["scope"]}))


if __name__ == "__main__":
    main()
