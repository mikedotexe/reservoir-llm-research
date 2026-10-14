#!/usr/bin/env python3
"""Passive selected-PID/session sampling. No app control, HTTP, or journal reads."""
import argparse
import ctypes as C
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import signal
import stat
import statistics
import sys
import threading
import time
import uuid

SCHEMA = "reservoir-macos-reliability-v1"
MANIFEST_LIMIT = 131072
LINE_LIMIT = 262144
KNOWN_DIRS = {"segments", "checkpoints", "journals"}
LIMITATIONS = [
    "Only the explicitly selected main PID is measured; WebKit, GPU, provider and other helper processes are excluded.",
    "No GPU utilization, energy, battery, thermal, total application footprint or UI responsiveness is measured.",
    "RSS is resident memory, not a leak diagnosis. CPU is interval task CPU time / monotonic elapsed time; 100% means one core.",
    "Disk scans are metadata-only, bounded and non-atomic while the app writes; allocated blocks may be shared on APFS.",
    "Manifest fields describe a sampled publication, not independent chain/numerical verification or proof of hardware crash durability.",
    "The sampler adds measurement overhead; missing metrics and incomplete scans remain explicit.",
]


def utc(ns=None):
    return dt.datetime.fromtimestamp((time.time_ns() if ns is None else ns) / 1e9, dt.timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ordinary_path(path, directory=False):
    path = Path(os.path.abspath(path))
    for part in [*reversed(path.parents), path]:
        s = part.lstat()
        if stat.S_ISLNK(s.st_mode):
            raise ValueError("Symlink path component is not permitted")
    s = path.stat()
    if not (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode)):
        raise ValueError("Expected ordinary directory" if directory else "Expected regular file")
    return path


def file_identity(path):
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode):
        raise ValueError("Expected regular file")
    return {"device": s.st_dev, "inode": s.st_ino, "bytes": s.st_size, "mtimeNs": str(s.st_mtime_ns)}


def read_regular(path, limit):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise ValueError("Not a bounded regular file")
        chunks, total = [], 0
        while True:
            chunk = os.read(fd, min(65536, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > limit:
                raise ValueError("File exceeded byte bound")
        after = os.fstat(fd)
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError("File changed during read")
        return b"".join(chunks)
    finally:
        os.close(fd)


def hash_file(path):
    # Executable hash is read only at admission and completion, not every sample.
    return sha(read_regular(path, 512 * 1024 * 1024))


class BSDInfo(C.Structure):
    _fields_ = [(n, C.c_uint32) for n in ("flags", "status", "xstatus", "pid", "ppid", "uid", "gid", "ruid", "rgid", "svuid", "svgid", "reserved")] + [
        ("comm", C.c_char * 16), ("name", C.c_char * 32)] + [(n, C.c_uint32) for n in ("nfiles", "pgid", "jobc", "tdev", "tpgid")] + [
        ("nice", C.c_int32), ("start_seconds", C.c_uint64), ("start_microseconds", C.c_uint64)]


class TaskInfo(C.Structure):
    _fields_ = [(n, C.c_uint64) for n in ("virtual", "resident", "user", "system", "threads_user", "threads_system")] + [(n, C.c_int32) for n in (
        "policy", "faults", "pageins", "cow_faults", "messages_sent", "messages_received", "syscalls_mach", "syscalls_unix", "switches", "thread_count", "running_threads", "priority")]


class Timebase(C.Structure):
    _fields_ = [("numer", C.c_uint32), ("denom", C.c_uint32)]


class MacProcess:
    def __init__(self, pid):
        if sys.platform != "darwin":
            raise ValueError("Sampling requires macOS; analysis and fixture tests are portable")
        self.pid = pid
        self.lib = C.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        self.lib.proc_pidinfo.argtypes = [C.c_int, C.c_int, C.c_uint64, C.c_void_p, C.c_int]
        self.lib.proc_pidinfo.restype = C.c_int
        self.lib.proc_pidpath.argtypes = [C.c_int, C.c_void_p, C.c_uint32]
        self.lib.proc_pidpath.restype = C.c_int
        system = C.CDLL("/usr/lib/libSystem.B.dylib")
        system.mach_timebase_info.argtypes = [C.POINTER(Timebase)]
        tb = Timebase()
        if system.mach_timebase_info(C.byref(tb)) or not tb.denom:
            raise ValueError("Cannot read Mach clock conversion")
        self.timebase = {"numer": tb.numer, "denom": tb.denom}

    def info(self, flavor, cls):
        value = cls()
        n = self.lib.proc_pidinfo(self.pid, flavor, 0, C.byref(value), C.sizeof(value))
        if n != C.sizeof(value):
            raise OSError(C.get_errno(), "Selected PID information unavailable or ABI size mismatch")
        return value

    def identity(self):
        bsd = self.info(3, BSDInfo)
        buf = C.create_string_buffer(4096)
        if self.lib.proc_pidpath(self.pid, buf, len(buf)) <= 0:
            raise OSError(C.get_errno(), "Selected PID executable path unavailable")
        return {"pid": self.pid, "startSeconds": str(bsd.start_seconds), "startMicroseconds": str(bsd.start_microseconds), "executablePath": os.fsdecode(buf.value)}

    def metrics(self):
        task = self.info(4, TaskInfo)
        ticks = task.user + task.system
        result = {"rssBytes": task.resident, "virtualBytes": task.virtual, "cpuTotalTicks": str(ticks),
                  "cpuTotalNanoseconds": str(ticks * self.timebase["numer"] // self.timebase["denom"]),
                  "threadCount": task.thread_count, "runningThreads": task.running_threads, "fdCount": None}
        # Count descriptors only: never ask libproc for their paths or contents.
        needed = self.lib.proc_pidinfo(self.pid, 1, 0, None, 0)
        if needed <= 0:
            result["fdError"] = "Descriptor count unavailable"
        elif needed > 65536 * 8:
            result["fdError"] = "Descriptor count exceeds 65536 bound"
        else:
            buf = C.create_string_buffer(min(65536 * 8, needed + 256))
            size = self.lib.proc_pidinfo(self.pid, 1, 0, buf, len(buf))
            if size <= 0 or size >= len(buf) or size % 8:
                result["fdError"] = "Descriptor enumeration failed or reached buffer bound"
            else:
                result["fdCount"] = size // 8
        return result


def manifest_snapshot(session):
    data = read_regular(session / "manifest.json", MANIFEST_LIMIT)
    obj = json.loads(data)
    if obj.get("format") != "reservoir-sustained-bundle-v1" or obj.get("sessionId") != session.name:
        raise ValueError("Selected manifest format/session identity mismatch")
    result = {"sha256": sha(data), "bytes": len(data)}
    for key in ("format", "sessionId", "generation", "revision", "phase", "step", "durableStep", "elapsedMillis", "journalCount", "segmentCount", "lastSegmentSha256", "checkpointSha256"):
        value = obj.get(key)
        if value is not None and (isinstance(value, (dict, list, bool)) or not isinstance(value, (str, int))):
            raise ValueError("Unexpected manifest scalar type")
        if isinstance(value, str) and len(value) > 128:
            raise ValueError("Manifest scalar exceeded bound")
        result[key] = value
    # Never retain prompt, journal, configuration, endpoint or diagnostic text.
    return result


def disk_snapshot(session, max_entries=120100, max_seconds=5):
    started = time.monotonic()
    result = {"logicalBytes": 0, "allocatedBytes": 0, "fileCount": 0, "directoryCount": 0, "entryCount": 0, "complete": True, "errors": []}
    def fail(message):
        result["complete"] = False
        if len(result["errors"]) < 16:
            result["errors"].append(message)
    def scan(directory, child=False):
        with os.scandir(directory) as entries:
            for entry in entries:
                result["entryCount"] += 1
                if result["entryCount"] > max_entries or time.monotonic() - started > max_seconds:
                    fail("Disk scan entry/time bound reached")
                    return False
                try:
                    s = entry.stat(follow_symlinks=False)
                    if stat.S_ISREG(s.st_mode):
                        result["fileCount"] += 1
                        result["logicalBytes"] += s.st_size
                        result["allocatedBytes"] += s.st_blocks * 512
                    elif stat.S_ISDIR(s.st_mode) and not child and entry.name in KNOWN_DIRS:
                        result["directoryCount"] += 1
                        # Open relative to the known directory without following a swapped symlink.
                        fd = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                        try:
                            if not scan(fd, True):
                                return False
                        finally:
                            os.close(fd)
                    else:
                        fail("Symlink, special file or unexpected nested directory excluded")
                except OSError as exc:
                    fail(f"Metadata read failed (errno {exc.errno})")
        return True
    fd = os.open(session, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        scan(fd)
        vfs = os.fstatvfs(fd)
        result["volumeAvailableBytes"] = vfs.f_bavail * vfs.f_frsize
        result["volumeFreeBytes"] = vfs.f_bfree * vfs.f_frsize
    finally:
        os.close(fd)
    result["scanSeconds"] = time.monotonic() - started
    return result


def error(component, exc):
    # Avoid including arbitrary filesystem contents or command lines in diagnostics.
    return {"component": component, "kind": type(exc).__name__, "message": str(exc)[:512]}


def sample(args):
    session = ordinary_path(args.session, True)
    executable = ordinary_path(args.executable)
    if Path(args.output).absolute().is_relative_to(session):
        raise ValueError("Sampler output must be outside the measured session")
    process = MacProcess(args.pid)
    identity = process.identity()
    if identity["executablePath"] != str(executable):
        raise ValueError("Selected PID executable does not match explicit executable path")
    executable_stat = file_identity(executable)
    if hash_file(executable) != args.expected_sha256.lower():
        raise ValueError("Executable SHA-256 mismatch")
    if process.identity() != identity or file_identity(executable) != executable_stat:
        raise ValueError("Identity changed during admission")
    manifest_snapshot(session)  # Require selected owned manifest before creating output.
    root_identity = (session.stat().st_dev, session.stat().st_ino)
    stop = threading.Event()
    stop_reason = [None]
    def interrupted(signum, _frame):
        stop_reason[0] = f"sampler-signal-{signum}"
        stop.set()
    old_handlers = {s: signal.signal(s, interrupted) for s in (signal.SIGINT, signal.SIGTERM)}
    start = time.monotonic_ns()
    header = {"type": "header", "schema": SCHEMA, "runId": str(uuid.uuid4()), "wallUtc": utc(), "monotonicNs": str(start),
              "process": {**identity, "executableSha256": args.expected_sha256.lower(), "executableStat": executable_stat},
              "sessionPath": str(session), "sampler": {"pid": os.getpid(), "scriptSha256": hash_file(Path(__file__)), "python": platform.python_version(), "os": platform.platform(), "architecture": platform.machine(), "machTimebase": process.timebase},
              "durationSeconds": args.duration_seconds, "intervalSeconds": args.interval_seconds, "diskEvery": args.disk_every,
              "maxOutputBytes": args.max_output_bytes, "limits": {"manifestBytes": MANIFEST_LIMIT, "diskEntries": 120100, "diskScanSeconds": 5}, "limitations": LIMITATIONS}
    count, byte_count, previous = 0, 0, None
    status = "completed"
    with open(args.output, "xb", buffering=0) as output:
        def write(obj, reserve=True):
            nonlocal byte_count
            line = (json.dumps(obj, separators=(",", ":"), allow_nan=False) + "\n").encode()
            if len(line) > LINE_LIMIT or byte_count + len(line) > args.max_output_bytes - (4096 if reserve else 0):
                return False
            output.write(line)
            os.fsync(output.fileno())
            byte_count += len(line)
            return True
        write(header)
        try:
            while True:
                began = time.monotonic_ns()
                wall = time.time_ns()
                if process.identity() != identity or file_identity(executable) != executable_stat:
                    status = "identity-changed"
                    break
                if (session.stat().st_dev, session.stat().st_ino) != root_identity:
                    status = "session-directory-changed"
                    break
                row = {"type": "sample", "sequence": count, "wallUtc": utc(wall), "wallEpochNs": str(wall), "monotonicNs": str(began), "elapsedSeconds": (began - start) / 1e9, "errors": [], "process": None, "manifest": None, "disk": None}
                try:
                    metrics = process.metrics()
                    if process.identity() != identity:
                        status = "identity-changed"
                        break
                    metrics["identityVerified"] = True
                    metrics["cpuIntervalPercent"] = None
                    cpu = int(metrics["cpuTotalNanoseconds"])
                    if previous:
                        delta = cpu - previous[1]
                        if delta >= 0:
                            metrics["cpuIntervalPercent"] = 100 * delta / (began - previous[0])
                        else:
                            row["errors"].append({"component": "cpu", "kind": "CounterRegression", "message": "CPU counter decreased"})
                    previous = (began, cpu)
                    row["process"] = metrics
                except OSError as exc:
                    row["errors"].append(error("process", exc))
                try:
                    row["manifest"] = manifest_snapshot(session)
                except (OSError, ValueError) as exc:
                    row["errors"].append(error("manifest", exc))
                if count % args.disk_every == 0:
                    try:
                        row["disk"] = disk_snapshot(session)
                        after = manifest_snapshot(session)
                        row["disk"]["manifestUnchangedDuringScan"] = bool(row["manifest"] and after["sha256"] == row["manifest"]["sha256"])
                    except (OSError, ValueError) as exc:
                        row["errors"].append(error("disk", exc))
                row["sampleSeconds"] = (time.monotonic_ns() - began) / 1e9
                if not write(row):
                    status = "output-bound"
                    break
                count += 1
                remaining = args.duration_seconds - (time.monotonic_ns() - start) / 1e9
                if remaining <= 0:
                    break
                if stop.wait(min(remaining, max(0, args.interval_seconds - row["sampleSeconds"]))):
                    status = stop_reason[0]
                    break
        except OSError as exc:
            status = "process-or-path-unavailable"
            final_error = error("identity", exc)
        except Exception as exc:
            status = "sampler-error"
            final_error = error("sampler", exc)
        finally:
            footer = {"type": "footer", "status": status, "wallUtc": utc(), "monotonicNs": str(time.monotonic_ns()), "elapsedSeconds": (time.monotonic_ns() - start) / 1e9, "sampleCount": count, "errors": []}
            if "final_error" in locals():
                footer["errors"].append(final_error)
            try:
                footer["finalExecutableSha256"] = hash_file(executable)
            except (OSError, ValueError) as exc:
                footer["errors"].append(error("executable", exc))
            write(footer, False)
            for sig, handler in old_handlers.items():
                signal.signal(sig, handler)
    return 0 if status == "completed" else 2


def distribution(points):
    if not points:
        return None
    values = sorted(y for _, y in points)
    avg_x = statistics.mean(x for x, _ in points)
    avg_y = statistics.mean(values)
    variance = sum((x - avg_x) ** 2 for x, _ in points)
    slope = sum((x - avg_x) * (y - avg_y) for x, y in points) / variance * 3600 if variance else None
    return {"count": len(values), "first": points[0][1], "last": points[-1][1], "minimum": values[0], "maximum": values[-1], "median": statistics.median(values), "p95NearestRank": values[max(0, math.ceil(len(values) * .95) - 1)], "leastSquaresChangePerHour": slope}


def phase_intervals(marker_path, header, samples, window_start=0):
    data = read_regular(marker_path, 131072)
    markers = []
    for line in data.splitlines():
        obj = json.loads(line)
        if not isinstance(obj, dict) or not isinstance(obj.get("phase"), str) or not 1 <= len(obj["phase"]) <= 80:
            raise ValueError("Invalid operator phase marker")
        stamp = str(obj.get("monotonicNs", ""))
        if not stamp.isdigit() or len(stamp) > 24:
            raise ValueError("Marker requires decimal monotonicNs from this host boot")
        if markers and int(stamp) < int(markers[-1]["monotonicNs"]):
            raise ValueError("Operator markers must be monotonic")
        markers.append({"phase": obj["phase"], "monotonicNs": stamp, "wallUtc": str(obj.get("wallUtc", ""))[:80], "note": str(obj.get("note", ""))[:1024]})
        if len(markers) > 128:
            raise ValueError("Operator marker count exceeds 128")
    start = int(header["monotonicNs"])
    intervals = []
    for index, marker in enumerate(markers):
        lo = (int(marker["monotonicNs"]) - start) / 1e9
        hi = (int(markers[index + 1]["monotonicNs"]) - start) / 1e9 if index + 1 < len(markers) else None
        selected = [row for row in samples if row["elapsedSeconds"] >= lo and (hi is None or row["elapsedSeconds"] < hi)]
        metrics = {}
        for key in ("rssBytes", "cpuIntervalPercent", "fdCount", "threadCount"):
            # CPU's measurement interval must lie entirely within the declared phase.
            points = [(row["elapsedSeconds"], row["process"][key]) for row in selected if isinstance(row.get("process"), dict) and isinstance(row["process"].get(key), (int, float)) and (key != "cpuIntervalPercent" or row.get("cpuIntervalStartElapsedSeconds", row["elapsedSeconds"] - header["intervalSeconds"]) >= max(lo, window_start))]
            metrics[key] = distribution(points)
        intervals.append({**marker, "source": "operator-declared, not measured window state", "fromElapsedSeconds": lo, "toElapsedSeconds": hi, "sampleCount": len(selected), "firstSampleElapsedSeconds": selected[0]["elapsedSeconds"] if selected else None, "lastSampleElapsedSeconds": selected[-1]["elapsedSeconds"] if selected else None, "metrics": metrics})
    return {"sha256": sha(data), "intervals": intervals, "clockRequirement": "Marker monotonic clock must use the same host and boot as sampler"}


def analyze_file(path, from_elapsed=0, to_elapsed=None, markers=None):
    data = read_regular(path, 64 * 1024 * 1024)
    rows, errors = [], []
    for index, line in enumerate(data.splitlines()):
        if index >= 100000:
            raise ValueError("Input record bound exceeded")
        try:
            if len(line) > LINE_LIMIT:
                raise ValueError("Line byte bound exceeded")
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError("Expected object")
            rows.append(obj)
        except (ValueError, json.JSONDecodeError) as exc:
            errors.append({"line": index + 1, "message": str(exc)[:128]})
    if not rows or rows[0].get("type") != "header" or rows[0].get("schema") != SCHEMA:
        raise ValueError("Missing supported sampler header")
    header = rows[0]
    all_samples = [r for r in rows if r.get("type") == "sample"]
    previous_cpu_sample = None
    for row in all_samples:
        if isinstance(row.get("process"), dict) and row["process"].get("cpuTotalNanoseconds") is not None:
            if previous_cpu_sample is not None:
                row["cpuIntervalStartElapsedSeconds"] = previous_cpu_sample["elapsedSeconds"]
            previous_cpu_sample = row
    samples = [r for r in all_samples if isinstance(r.get("elapsedSeconds"), (int, float)) and r["elapsedSeconds"] >= from_elapsed and (to_elapsed is None or r["elapsedSeconds"] <= to_elapsed)]
    footer = rows[-1] if rows[-1].get("type") == "footer" else None
    issues = []
    if not data.endswith(b"\n"):
        issues.append("Input lacks final newline; last record may be partial")
    if footer is None:
        issues.append("No completion footer; coverage is incomplete or sampler still running")
    if footer and footer.get("finalExecutableSha256") and footer["finalExecutableSha256"] != header.get("process", {}).get("executableSha256"):
        issues.append("Executable hash changed between admission and completion")
    if footer and footer.get("sampleCount") != len(all_samples):
        issues.append("Footer sample count differs from parsed samples")
    gaps, wall_jumps = [], []
    for first, second in zip(all_samples, all_samples[1:]):
        delta = (int(second["monotonicNs"]) - int(first["monotonicNs"])) / 1e9
        wall_delta = (int(second["wallEpochNs"]) - int(first["wallEpochNs"])) / 1e9
        if delta > header["intervalSeconds"] * 1.5 or delta <= 0:
            gaps.append({"afterSequence": first["sequence"], "seconds": delta})
        if abs(wall_delta - delta) > 2:
            wall_jumps.append({"afterSequence": first["sequence"], "wallMinusMonotonicSeconds": wall_delta - delta})
        if second["sequence"] != first["sequence"] + 1:
            issues.append("Sample sequence discontinuity")
    metrics = {}
    for group, names in {"process": ["rssBytes", "cpuIntervalPercent", "threadCount", "fdCount"], "disk": ["logicalBytes", "allocatedBytes", "fileCount", "volumeAvailableBytes"]}.items():
        for name in names:
            points = [(r["elapsedSeconds"], r[group][name]) for r in samples if isinstance(r.get(group), dict) and isinstance(r[group].get(name), (int, float)) and not isinstance(r[group][name], bool) and (group != "disk" or r[group].get("complete") is True) and (name != "cpuIntervalPercent" or r.get("cpuIntervalStartElapsedSeconds", r["elapsedSeconds"] - header["intervalSeconds"]) >= from_elapsed)]
            metrics[name] = distribution(points)
    manifests = [r["manifest"] for r in samples if isinstance(r.get("manifest"), dict)]
    regressions = []
    for first, second in zip(manifests, manifests[1:]):
        if (first.get("sessionId"), first.get("generation")) != (second.get("sessionId"), second.get("generation")):
            regressions.append("Session/generation identity changed")
        for key in ("durableStep", "journalCount", "segmentCount"):
            if isinstance(first.get(key), int) and isinstance(second.get(key), int) and second[key] < first[key]:
                regressions.append(f"{key} decreased")
    return {"schema": SCHEMA + "-analysis", "inputSha256": sha(data), "inputBytes": len(data), "measurementOnly": True,
            "processIdentity": header.get("process"), "selection": {"fromElapsedSeconds": from_elapsed, "toElapsedSeconds": to_elapsed, "phase": "Not inferred; bind manually to retained UI phase evidence"},
            "coverage": {"allSampleCount": len(all_samples), "selectedSampleCount": len(samples), "firstElapsedSeconds": samples[0]["elapsedSeconds"] if samples else None, "lastElapsedSeconds": samples[-1]["elapsedSeconds"] if samples else None, "footer": footer, "gaps": gaps, "wallClockJumps": wall_jumps, "parseErrors": errors, "issues": sorted(set(issues)), "sampleErrorCount": sum(len(r.get("errors", [])) for r in samples), "incompleteDiskScans": sum(1 for r in samples if isinstance(r.get("disk"), dict) and not r["disk"].get("complete"))},
            "operatorPhases": phase_intervals(markers, header, samples, from_elapsed) if markers else None, "metrics": metrics, "manifestProgress": {"count": len(manifests), "first": manifests[0] if manifests else None, "last": manifests[-1] if manifests else None, "regressions": sorted(set(regressions))}, "limitations": LIMITATIONS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("sample")
    capture.add_argument("--pid", type=int, required=True)
    capture.add_argument("--executable", type=Path, required=True)
    capture.add_argument("--expected-sha256", required=True)
    capture.add_argument("--session", type=Path, required=True)
    capture.add_argument("--output", type=Path, required=True)
    capture.add_argument("--duration-seconds", type=float, default=9000)
    capture.add_argument("--interval-seconds", type=float, default=15)
    capture.add_argument("--disk-every", type=int, default=4)
    capture.add_argument("--max-output-bytes", type=int, default=16 * 1024 * 1024)
    analysis = sub.add_parser("analyze")
    analysis.add_argument("--input", type=Path, required=True)
    analysis.add_argument("--output", type=Path, required=True)
    analysis.add_argument("--from-elapsed", type=float, default=0)
    analysis.add_argument("--to-elapsed", type=float)
    analysis.add_argument("--markers", type=Path, help="Operator-declared phase JSONL from same host boot")
    args = parser.parse_args()
    if args.command == "sample":
        if not (0 < args.pid < 2**31 and 0 < args.duration_seconds <= 43200 and .1 <= args.interval_seconds <= 300 and 1 <= args.disk_every <= 1000 and 65536 <= args.max_output_bytes <= 64 * 1024 * 1024):
            parser.error("Sampling arguments outside supported bounds")
        if len(args.expected_sha256) != 64 or any(c not in "0123456789abcdefABCDEF" for c in args.expected_sha256):
            parser.error("Expected SHA-256 must be 64 hexadecimal characters")
        return sample(args)
    if args.from_elapsed < 0 or (args.to_elapsed is not None and args.to_elapsed < args.from_elapsed):
        parser.error("Invalid analysis elapsed window")
    result = analyze_file(args.input, args.from_elapsed, args.to_elapsed, args.markers)
    with open(args.output, "x") as output:
        json.dump(result, output, indent=2, allow_nan=False)
        output.write("\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print(f"reliability sampler: {exc}", file=sys.stderr)
        sys.exit(1)
