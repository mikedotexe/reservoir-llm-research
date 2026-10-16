#!/usr/bin/env python3
"""Bounded read-only host observations; never starts a model or retries admission.

The schedule is fixed before observation, including after an unhealthy sample.
Only process rows whose executable/arguments identify this research checkout (or
an explicit --owned-root) and its Python worker/app are retained. Other process
arguments are neither printed nor saved. Existing output files are never replaced.
This observation does not replace the Rust supervisor's immediate admission check.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
COMMAND_TIMEOUT_SECONDS = 5


def command(argv: list[str]) -> dict:
    try:
        result = subprocess.run(argv, capture_output=True, text=True,
                                timeout=COMMAND_TIMEOUT_SECONDS, check=False)
        return {"argv": argv, "returnCode": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"argv": argv, "returnCode": None, "error": str(exc)}


def owned_processes(roots: list[Path]) -> dict:
    result = command(["/bin/ps", "-axo", "pid=,ppid=,rss=,stat=,command="])
    if result.get("returnCode") != 0:
        return {"available": False, "error": result.get("error") or result.get("stderr")}
    rows = []
    for line in result["stdout"].splitlines():
        fields = line.strip().split(None, 4)
        if len(fields) != 5:
            continue
        try:
            pid, ppid, rss = map(int, fields[:3])
            args = shlex.split(fields[4])
        except ValueError:
            continue
        if not args or pid == os.getpid():
            continue
        app_suffix = "/reservoir-scope-desktop"
        app_prefix, app_separator, _ = fields[4].partition(app_suffix)
        app_executable = app_prefix + app_separator if app_separator else None
        executable = Path(args[0]).name.lower()
        app = bool(app_executable and fields[4].startswith("/")
                   and not executable.startswith("python")
                   and any(app_executable.startswith(str(root) + "/") for root in roots))
        matches = [str(root) for root in roots
                   if (app and app_executable.startswith(str(root) + "/"))
                   or any(arg == str(root) or arg.startswith(str(root) + "/") for arg in args)]
        if not matches:
            continue
        worker = executable.startswith("python") and any(
            "activation_worker/" in arg or arg == "activation_worker" for arg in args[1:])
        if not (worker or app):
            continue
        rows.append({"pid": pid, "ppid": ppid, "rssKiB": rss,
                     "state": fields[3], "kind": "activationWorker" if worker else "app",
                     "matchedRoots": matches, "executable": app_executable if app else args[0]})
    return {"available": True, "rows": sorted(rows, key=lambda row: row["pid"]),
            "activationWorkerCount": sum(row["kind"] == "activationWorker" for row in rows),
            "scope": "Research-root-matched direct Python workers and desktop executables only"}


def observe(roots: list[Path]) -> dict:
    captured = datetime.now(timezone.utc).isoformat()
    pressure = command(["/usr/sbin/sysctl", "-n", "kern.memorystatus_vm_pressure_level"])
    free = command(["/usr/bin/memory_pressure", "-Q"])
    pressure_text = pressure.get("stdout", "").strip()
    level = int(pressure_text) if pressure.get("returnCode") == 0 and pressure_text.isdigit() else None
    match = re.search(r"^System-wide memory free percentage:\s*(\d+)%\s*$",
                      free.get("stdout", ""), re.MULTILINE)
    percent = int(match.group(1)) if free.get("returnCode") == 0 and match else None
    processes = owned_processes(roots)
    return {"capturedAtUtc": captured, "pressureLevel": level, "freePercent": percent,
            "matchesRustThresholds": level == 1 and percent is not None and percent >= 25,
            "ownedProcesses": processes, "rawPressure": pressure, "rawFreePercent": free,
            "rawVmStat": command(["/usr/bin/vm_stat"]),
            "rawSwapUsage": command(["/usr/sbin/sysctl", "-n", "vm.swapusage"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, choices=range(1, 7), default=1)
    parser.add_argument("--interval-seconds", type=float, default=15.0)
    parser.add_argument("--owned-root", action="append", type=Path, default=[])
    args = parser.parse_args()
    if platform.system() != "Darwin":
        parser.error("This observation matches the macOS-only activation admission")
    if not 0 <= args.interval_seconds <= 60 or (args.samples > 1 and args.interval_seconds < 1):
        parser.error("Use intervals of 1–60 seconds for multiple samples")
    roots = sorted({ROOT, *(root.expanduser().resolve(strict=True) for root in args.owned_root)})
    # Reserve a new destination before observing; a pre-existing observation is evidence.
    with args.output.expanduser().open("x", encoding="utf-8") as stream:
        started = time.monotonic()
        samples = []
        for index in range(args.samples):
            scheduled = index * args.interval_seconds
            remaining = scheduled - (time.monotonic() - started)
            if remaining > 0:
                time.sleep(remaining)
            sample = observe(roots)
            sample.update(index=index, scheduledOffsetSeconds=scheduled,
                          completedOffsetSeconds=time.monotonic() - started)
            samples.append(sample)
        healthy = all(sample["matchesRustThresholds"]
                      and sample["ownedProcesses"]["available"]
                      and sample["ownedProcesses"]["activationWorkerCount"] == 0 for sample in samples)
        report = {"schema": "activation-resource-observation/1",
                  "scriptSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "modelCalls": 0, "processesChanged": False, "automaticRetries": 0,
                  "ownedRoots": [str(root) for root in roots],
                  "fixedSchedule": {"samples": args.samples, "intervalSeconds": args.interval_seconds},
                  "thresholds": {"pressureLevelEquals": 1, "minimumFreePercent": 25},
                  "samples": samples, "allSamplesHealthyAndNoOwnedWorker": healthy,
                  "limitation": "A bounded observation, not inference admission or proof of earlier cleanup; Rust rechecks immediately before loading."}
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({"output": str(args.output), "samples": len(samples),
                      "allSamplesHealthyAndNoOwnedWorker": healthy, "modelCalls": 0}))
    return 0 if healthy else 2


if __name__ == "__main__":
    raise SystemExit(main())
