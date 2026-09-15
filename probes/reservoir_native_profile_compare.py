#!/usr/bin/env python3
"""Compare retained Reservoir Scope profile reports; standard library, read-only.

Recomputes descriptive timings from every raw frame, verifies exported summaries,
and refuses comparisons with different binaries, resources, scene geometry or
workload settings. No live reads, network connections, or performance runs occur.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "research/outputs/2026-09-06-native-profiling"
DEFAULT_NAMES = [
    "m1-max.json", "m1-max-run2.json", "m1-max-run3.json",
    "m4-pro.json", "m4-pro-run2.json", "m4-pro-run3.json",
]
SCENES = ["fill", "zones", "trajectory", "spectral"]
METRICS = ["cpuUpdateMs", "cpuEncodeSubmitMs", "gpuCommandMs",
           "waitWallMs", "serialFrameWallMs"]
WORKLOAD_TIMINGS = {"elapsedRenderingWorkMs", "pipelineConstructionMs"}
GEOMETRY_FIELDS = ["ordinal", "historicalRowIndex", "stateRowIndex",
                   "drawCount", "vertexCount", "geometryBufferBytes"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def distribution(values: list[float]) -> dict[str, Any]:
    require(bool(values), "Cannot summarize an empty sample")
    require(all(isinstance(v, (int, float)) and not isinstance(v, bool)
                and math.isfinite(v) and v >= 0 for v in values),
            "Timing values must be finite and nonnegative")
    ordered = sorted(values)

    def quantile(p: float) -> float:
        position = (len(ordered) - 1) * p
        lower = math.floor(position)
        upper = math.ceil(position)
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

    return {"count": len(ordered), "min": ordered[0], "median": quantile(0.5),
            "p95": quantile(0.95), "max": ordered[-1]}


def comparison_identity(report: dict[str, Any]) -> dict[str, Any]:
    provenance = report["provenance"]
    resources = sorted(provenance["resources"], key=lambda value: value["name"])
    require([item["name"] for item in resources] == ["data.json", "state-geometry.json"],
            "Expected exactly the two bundled evidence resources")
    for item in [provenance["executable"], *resources]:
        require(isinstance(item["bytes"], int) and item["bytes"] > 0,
                "Artifact size must be positive")
        digest = item["sha256"]
        require(isinstance(digest, str) and len(digest) == 64
                and all(c in "0123456789abcdef" for c in digest),
                "Artifact SHA-256 must have 64 lowercase hex digits")
    return {
        "schemaVersion": report["schemaVersion"],
        "appVersion": provenance["appVersion"], "appBuild": provenance["appBuild"],
        "executable": provenance["executable"], "resources": resources,
        "workload": {k: v for k, v in report["workload"].items()
                     if k not in WORKLOAD_TIMINGS},
        "sceneSelectionsAndGeometry": [{
            "mode": scene["mode"],
            "frames": [{k: frame[k] for k in GEOMETRY_FIELDS}
                       for frame in scene["frames"]],
        } for scene in report["scenes"]],
    }


def summarize_report(report: dict[str, Any], name: str, digest: str) -> dict[str, Any]:
    require(report["schemaVersion"] == "reservoir-scope-profile-v1",
            f"{name}: unsupported report schema")
    require(report["status"] == "completed", f"{name}: report did not complete")
    require([scene["mode"] for scene in report["scenes"]] == SCENES,
            f"{name}: expected all four scenes in the audited order")
    workload = report["workload"]
    count = workload["measuredFramesPerScene"]
    require(isinstance(count, int) and count > 0, f"{name}: invalid frame count")
    scenes = []
    for scene in report["scenes"]:
        frames = scene["frames"]
        require(len(frames) == count, f"{name}/{scene['mode']}: wrong raw count")
        for ordinal, frame in enumerate(frames):
            require(frame["ordinal"] == ordinal, f"{name}: frame order changed")
            for row_key, sample_key in [("historicalRowIndex", "historicalSampleCount"),
                                        ("stateRowIndex", "stateSampleCount")]:
                expected = ordinal * (workload[sample_key] - 1) // max(count - 1, 1)
                require(frame[row_key] == expected,
                        f"{name}/{scene['mode']}: {row_key} violates selection rule")
        computed = {}
        for metric in METRICS:
            values = [frame[metric] for frame in frames if frame.get(metric) is not None]
            require(len(values) == count, f"{name}/{scene['mode']}: incomplete {metric}")
            stats = distribution(values)
            for key, value in stats.items():
                exported = scene[metric][key]
                require(isinstance(exported, (int, float)) and not isinstance(exported, bool)
                        and math.isfinite(exported)
                        and math.isclose(value, exported, rel_tol=1e-9, abs_tol=1e-8),
                        f"{name}/{scene['mode']}: exported {metric}.{key} disagrees with raw data")
            computed[metric] = stats
        # Sum at each frame before taking quantiles; adding component medians
        # would not produce the median of total measured preparation work.
        computed["cpuPreparationMs"] = distribution([
            frame["cpuUpdateMs"] + frame["cpuEncodeSubmitMs"] for frame in frames])
        scenes.append({"mode": scene["mode"], "distributions": computed})
    return {"report": name, "sha256": digest, "startedAtUTC": report["startedAtUTC"],
            "completedAtUTC": report["completedAtUTC"], "device": report["device"],
            "environmentBefore": report["environmentBefore"],
            "environmentAfter": report["environmentAfter"], "memory": report["memory"],
            "pipelineConstructionMs": workload["pipelineConstructionMs"],
            "elapsedRenderingWorkMs": workload["elapsedRenderingWorkMs"], "scenes": scenes}


def compare_documents(documents: list[tuple[str, dict[str, Any], str]]) -> dict[str, Any]:
    require(len(documents) >= 2, "Comparison requires at least two reports")
    reference = comparison_identity(documents[0][1])
    runs = []
    for name, report, digest in documents:
        runs.append(summarize_report(report, name, digest))
        require(comparison_identity(report) == reference,
                f"{name}: executable, resources, workload, row selection or geometry differs")
    return {
        "schema": "reservoir-native-profile-comparison-v1",
        "verification": "All reports completed; identical executable/resources/workload/rows/geometry; all raw timing summaries recomputed",
        "reportCount": len(runs),
        "measuredFrameCount": sum(len(scene["frames"]) for _, report, _ in documents for scene in report["scenes"]),
        "identity": reference, "runs": runs,
        "interpretation": "Run-wise descriptive observations only; no fastest-run selection, pooled inference, FPS, energy or general chip ranking",
    }


def compare_files(paths: list[Path]) -> dict[str, Any]:
    require(len(set(path.resolve() for path in paths)) == len(paths), "Duplicate input report")
    documents = []
    for path in paths:
        require(path.stat().st_size <= 2 * 1024 * 1024, f"{path}: report exceeds 2 MiB bound")
        raw = path.read_bytes()
        documents.append((path.name, json.loads(raw), hashlib.sha256(raw).hexdigest()))
    return compare_documents(documents)


def markdown(report: dict[str, Any]) -> str:
    per_scene = report["identity"]["workload"]["measuredFramesPerScene"]
    lines = [f"Verified {report['reportCount']} reports and {report['measuredFrameCount']} measured frames.", "",
             f"All times below are **milliseconds, median / p95**, recalculated from each run's {per_scene} raw frames per scene.", "",
             "| Report | Scene | CPU geometry/update | CPU encode/submit | GPU command | Serial wall |",
             "|---|---|---:|---:|---:|---:|"]
    for run in report["runs"]:
        for scene in run["scenes"]:
            cells = []
            for metric in ["cpuUpdateMs", "cpuEncodeSubmitMs", "gpuCommandMs", "serialFrameWallMs"]:
                stats = scene["distributions"][metric]
                cells.append(f"{stats['median']:.3f} / {stats['p95']:.3f}")
            lines.append(f"| {run['report']} | {scene['mode']} | " + " | ".join(cells) + " |")
    lines.extend(["", "| Report | Thermal before → after | Low power before → after | Peak sampled Metal MiB | Pipeline construction ms | Rendering work ms |",
                  "|---|---|---|---:|---:|---:|"])
    for run in report["runs"]:
        before, after = run["environmentBefore"], run["environmentAfter"]
        lines.append(f"| {run['report']} | {before['thermalState']} → {after['thermalState']} | "
                     f"{before['lowPowerModeEnabled']} → {after['lowPowerModeEnabled']} | "
                     f"{run['memory']['peakSampledMetalResourceBytes'] / 2**20:.4f} | "
                     f"{run['pipelineConstructionMs']:.3f} | {run['elapsedRenderingWorkMs']:.3f} |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="*", type=Path,
                        help="Explicit reports, or all six declared retained reports by default")
    parser.add_argument("--markdown", action="store_true", help="Print concise tables instead of JSON")
    args = parser.parse_args()
    result = compare_files(args.reports or [REPORT_DIR / name for name in DEFAULT_NAMES])
    print(markdown(result) if args.markdown else json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
