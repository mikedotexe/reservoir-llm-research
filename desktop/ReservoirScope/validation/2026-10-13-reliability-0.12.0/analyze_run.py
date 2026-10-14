#!/usr/bin/env python3
"""Read-only capture analysis; no process control, app IPC, or provider contact."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import macos_reliability as sampler


def digest(path):
    return hashlib.sha256(sampler.read_regular(path, 64 * 1024 * 1024)).hexdigest()


def epoch(value):
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def overlaps(start, end, windows):
    return any(start <= hi and end >= lo for lo, hi in windows)


def summarize(rows, lo, hi, load_windows):
    selected = [r for r in rows if lo <= r["elapsedSeconds"] <= hi]
    metrics = {}
    for group, names in {"process": ["rssBytes", "cpuIntervalPercent", "threadCount", "fdCount"], "disk": ["logicalBytes", "allocatedBytes", "fileCount", "volumeAvailableBytes"]}.items():
        for name in names:
            points, excluded, cpu_weighted, cpu_duration = [], 0, 0.0, 0.0
            for row in selected:
                obj = row.get(group)
                if not isinstance(obj, dict) or not isinstance(obj.get(name), (int, float)) or isinstance(obj[name], bool):
                    continue
                if group == "disk" and not obj.get("complete"):
                    continue
                start_wall = end_wall = int(row["wallEpochNs"]) / 1e9
                if name == "cpuIntervalPercent":
                    previous = row.get("_previousCpu")
                    if previous is None or previous["elapsedSeconds"] < lo:
                        continue
                    start_wall = int(previous["wallEpochNs"]) / 1e9
                elif group == "disk":
                    end_wall += row.get("sampleSeconds", 0)
                if overlaps(start_wall, end_wall, load_windows):
                    excluded += 1
                    continue
                points.append((row["elapsedSeconds"], obj[name]))
                if name == "cpuIntervalPercent":
                    duration = row["elapsedSeconds"] - previous["elapsedSeconds"]
                    if duration > 0:
                        cpu_duration += duration
                        cpu_weighted += obj[name] * duration
            result = sampler.distribution(points)
            metrics[name] = {"statistics": result, "excludedByDocumentedLoadCount": excluded,
                             "firstMeasuredElapsedSeconds": points[0][0] if points else None,
                             "lastMeasuredElapsedSeconds": points[-1][0] if points else None}
            if name == "cpuIntervalPercent":
                metrics[name]["durationWeightedMeanPercent"] = cpu_weighted / cpu_duration if cpu_duration else None
                metrics[name]["coveredCpuIntervalSeconds"] = cpu_duration
            if group == "disk" and len(points) > 1:
                span = points[-1][0] - points[0][0]
                metrics[name]["netChange"] = points[-1][1] - points[0][1]
                metrics[name]["netChangePerHour"] = (points[-1][1] - points[0][1]) * 3600 / span if span > 0 else None
    manifests = [(r["elapsedSeconds"], r["manifest"]) for r in selected if isinstance(r.get("manifest"), dict)]
    phases = {}
    for _, manifest in manifests:
        name = str(manifest.get("phase"))
        phases[name] = phases.get(name, 0) + 1
    return {"window": {"fromElapsedSeconds": lo, "toElapsedSeconds": hi}, "sampleCount": len(selected),
            "firstSampleElapsedSeconds": selected[0]["elapsedSeconds"] if selected else None,
            "lastSampleElapsedSeconds": selected[-1]["elapsedSeconds"] if selected else None,
            "metrics": metrics, "manifestProgressUnfiltered": {"first": manifests[0] if manifests else None, "last": manifests[-1] if manifests else None, "phaseSampleCounts": phases},
            "note": "Only resource summaries exclude documented load; functional gaps, errors and progress remain in the unfiltered base analysis."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--markers", type=Path, required=True)
    parser.add_argument("--load-receipt", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    raw = sampler.read_regular(args.input, 64 * 1024 * 1024)
    rows = [json.loads(line) for line in raw.splitlines()]
    base = sampler.analyze_file(args.input, markers=args.markers)
    if base["inputSha256"] != hashlib.sha256(raw).hexdigest():
        raise ValueError("Capture changed between bounded reads; retry or analyze a retained immutable prefix")
    if base["coverage"]["footer"] is None and not args.allow_incomplete:
        raise ValueError("No final footer. Use --allow-incomplete only for an explicitly interim summary")
    samples = [r for r in rows if r.get("type") == "sample"]
    if not samples:
        raise ValueError("No samples")
    previous = None
    for row in samples:
        if isinstance(row.get("process"), dict) and row["process"].get("cpuTotalNanoseconds") is not None:
            row["_previousCpu"] = previous
            previous = row
    loads = []
    for path in args.load_receipt:
        data = sampler.read_regular(path, 1048576)
        value = json.loads(data)
        start = next((value[k] for k in ("startedAtUtc", "startedAt") if k in value), None)
        end = next((value[k] for k in ("finishedAtUtc", "endedAtUtc", "endedAt") if k in value), None)
        if start is None or end is None or epoch(end) < epoch(start):
            raise ValueError(f"Load receipt lacks a closed ordered UTC interval: {path.name}")
        loads.append({"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "startUtc": start, "endUtc": end})
    mask = [(epoch(v["startUtc"]), epoch(v["endUtc"])) for v in loads]
    first, last = samples[0]["elapsedSeconds"], samples[-1]["elapsedSeconds"]
    windows = []
    intervals = base["operatorPhases"]["intervals"]
    for i, phase in enumerate(intervals):
        lo = max(first, phase["fromElapsedSeconds"])
        hi = min(last, phase["toElapsedSeconds"] if phase["toElapsedSeconds"] is not None else last)
        if lo <= hi:
            windows.append((f"operator-{i}-{phase['phase']}", lo, hi, "Operator-declared phase; last open phase is truncated to the latest sampled instant"))
    visible = next((p for p in intervals if p["phase"] == "visible"), None)
    if visible:
        for name, a, b in (("prospective-early-minutes10-25", 600, 1500), ("prospective-late-minutes110-125", 6600, 7500)):
            lo, hi = visible["fromElapsedSeconds"] + a, visible["fromElapsedSeconds"] + b
            phase_covers = any(p["phase"] == "minimized" and p["fromElapsedSeconds"] <= lo and (p["toElapsedSeconds"] is None or p["toElapsedSeconds"] >= hi) for p in intervals)
            if hi <= last and phase_covers:
                windows.append((name, lo, hi, "Predeclared relative-to-observed-Start window lies within a declared minimized interval; continuity still requires raw evidence"))
            else:
                windows.append((name, lo, hi, "INCOMPLETE: requested window not yet fully sampled and/or not entirely declared minimized; do not compare as a completed window"))
    result = {"schema": "reservoir-reliability-report-workflow-v1", "status": "measurement-summary-not-acceptance", "base": base,
              "source": {"wrapperSha256": digest(Path(__file__)), "analyzerSha256": digest(Path(sampler.__file__))}, "documentedBackgroundLoadIntervals": loads,
              "windows": [{"id": name, "qualificationNote": note, "allObservedResources": summarize(samples, lo, hi, []), "documentedLoadExcludedResources": summarize(samples, lo, hi, mask)} for name, lo, hi, note in windows],
              "limits": ["Load exclusion is a descriptive sensitivity analysis; thermal/caching effects may persist and unrecorded host work remains unknown.", "Never delete a functional stall or missing measurement when excluding resource-load samples.", "Marker state is operator-declared; no continuous window-state instrumentation or independent GPU attribution.", "Wall-clock-to-load matching is uncertain if base coverage records wall-clock jumps; review those before interpreting excluded summaries.", "Observed-Start marker follows the UI action and is a conservative time origin, not an exact HTTP or numerical admission timestamp.", "Incomplete early/late windows retain partial statistics for inspection only and cannot satisfy the prospective comparison."]}
    with args.output.open("x") as output:
        json.dump(result, output, indent=2, allow_nan=False)
        output.write("\n")


if __name__ == "__main__":
    main()
