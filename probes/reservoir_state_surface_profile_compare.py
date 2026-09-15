#!/usr/bin/env python3
"""Validate and compare six retained native state-surface profiles.

Standard library only. Reads completed reports, never performs a benchmark or
contacts either host. Requires the predeclared three numbered runs on each host.
All descriptive summaries are independently recomputed from raw measured frames.
Output files stay in the research repository. No fastest-run selection or pooling.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = [("signed_color", 0.0, False), ("signed_relief", 0.14, False),
             ("signed_relief_cutaway", 0.14, True)]
HOSTS = ["m1-max", "m4-pro"]
NAMES = [f"{host}-run{run}.json" for host in HOSTS for run in range(1, 4)]
METRICS = ["cpuUpdateMs", "cpuEncodeSubmitMs", "gpuCommandMs", "waitWallMs", "serialFrameWallMs"]
RAW_STATE_SHA256 = "09ea4db8212809085aa2e07a040975f3095d7ef79d06eb8ba7404cc2424e282f"
GEOMETRY_SHA256 = "5e90207e7dfd1d395b249d3bb5d668afa0f86b6d3e0e6383eda7b9eb52514317"
RESOURCE_NAMES = ["data.json", "state-geometry.json", "state-replay.bin", "state-replay.json"]
WORKLOAD = {"widthPixels": 1280, "heightPixels": 800, "warmupsPerScene": 8,
            "measuredFramesPerScene": 30, "caseCount": 3, "stateSampleCount": 1024,
            "stateDimensions": 128, "previewFillPct": 68, "previewFillIsObserved": False,
            "lower": -1, "upper": 1, "showSites": True, "selectedNode": 0,
            "atlasVersion": "index-fibonacci-128-v1", "renderingBudgetSeconds": 45}
# Atlas v1: 1,986 unique mesh vertices, 3,968 triangles, 64 cut-boundary
# segments, 1,728 reference-line vertices; 128 exact sites (65 on z <= 0).
# SurfaceVertex stride is 48 bytes; weights = 1986*128*4; observations=128*4.
GEOMETRY_COUNTS = {False: (13760, 1677824), True: (7937, 1398320)}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def number(value: Any, label: str, *, positive: bool = False) -> float:
    require(type(value) in (int, float) and math.isfinite(value)
            and (value > 0 if positive else value >= 0), f"{label}: expected finite {'positive' if positive else 'nonnegative'} number")
    return value


def sha(value: Any, label: str) -> str:
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
            f"{label}: invalid SHA-256")
    return value


def timestamp(value: Any, label: str) -> datetime:
    require(isinstance(value, str), f"{label}: timestamp is not text")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.tzinfo is not None, f"{label}: timestamp lacks a timezone")
    return result


def distribution(values: list[float]) -> dict[str, float | int]:
    require(bool(values), "Cannot summarize zero frames")
    ordered = sorted(number(v, "frame timing") for v in values)
    def quantile(p: float) -> float:
        position = (len(ordered) - 1) * p
        lower, upper = math.floor(position), math.ceil(position)
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
    return {"count": len(values), "min": ordered[0], "median": quantile(0.5),
            "p95": quantile(0.95), "max": ordered[-1]}


def identity(report: dict[str, Any], label: str) -> dict[str, Any]:
    p = report["provenance"]
    executable = sha(p["executableSHA256"], f"{label} executable")
    resources = p["resourceSHA256"]
    require(isinstance(resources, dict) and sorted(resources) == RESOURCE_NAMES, f"{label}: expected the four evidence resources")
    for name, value in resources.items(): sha(value, f"{label}/{name}")
    sources = p["sourceSHA256"]
    required_sources = {"StateSurface.swift", "StateSurfaceScene.swift", "StateSurfaceProfiling.swift", "Evidence.swift", "ResourceBundle.swift"}
    require(isinstance(sources, dict) and required_sources <= sources.keys(), f"{label}: essential Swift source hashes unavailable")
    for name, value in sources.items():
        require(isinstance(name, str) and name.endswith(".swift") and "/" not in name and "\\" not in name,
                f"{label}: Swift source hash keys must be basenames")
        sha(value, f"{label}/{name}")
    require(p["retainedActivationSHA256"] == resources["state-replay.bin"] == RAW_STATE_SHA256,
            f"{label}: raw activation capture changed")
    require(p["frozenGeometrySHA256"] == resources["state-geometry.json"] == GEOMETRY_SHA256,
            f"{label}: frozen geometry resource changed")
    # Host-local directory/executable paths are deliberately omitted. Available
    # source contents, executable, resources and all fixed workload values match.
    w = report["workload"]
    return {"executableSHA256": executable, "sourceSHA256": sources,
            "resourceSHA256": resources, "workload": {key: w[key] for key in [*WORKLOAD, "sampleCount"]}}


def summarize(report: dict[str, Any], filename: str, digest: str, raw_bytes: int) -> dict[str, Any]:
    require(report["schemaVersion"] == "reservoir-scope-state-surface-profile-v1" and report["status"] == "completed",
            f"{filename}: wrong schema or incomplete run")
    started = timestamp(report["startedAtUTC"], filename)
    completed = timestamp(report["completedAtUTC"], filename)
    require(completed >= started, f"{filename}: completion clock precedes start")
    w = report["workload"]
    for key, value in WORKLOAD.items():
        require(w[key] == value and (type(w[key]) is bool if type(value) is bool else type(w[key]) is not bool),
                f"{filename}: workload differs at {key}")
    require(type(w["sampleCount"]) is int and w["sampleCount"] in (1, 4), f"{filename}: invalid MSAA sample count")
    elapsed = number(w["elapsedRenderingWorkMs"], filename, positive=True)
    require(elapsed < 45000, f"{filename}: completed run exceeded the rendering budget")
    number(w["pipelineAndAtlasConstructionMs"], filename)
    match = re.fullmatch(r"(m1-max|m4-pro)-run([123])\.json", filename)
    require(match is not None, f"{filename}: does not match the predeclared host/run naming")
    host, run_number = match.group(1), int(match.group(2))
    device = report["device"]
    require(("M1 Max" if host == "m1-max" else "M4 Pro") in device["name"], f"{filename}: device does not match filename host")
    require(device["hasUnifiedMemory"] is True, f"{filename}: expected the specified Apple silicon unified-memory device")
    for key in ["recommendedMaxWorkingSetBytes", "physicalMemoryBytes"]: number(device[key], f"{filename}/{key}", positive=True)
    for key in ["hardwareModel", "cpuDescription"]:
        require(isinstance(device[key], str) and device[key] not in ("", "unavailable"), f"{filename}: missing device {key}")
    for phase in ["environmentBefore", "environmentAfter"]:
        environment = report[phase]
        require(environment["thermalState"] in ("nominal", "fair"), f"{filename}: unsupported thermal state at {phase}")
        require(type(environment["lowPowerModeEnabled"]) is bool, f"{filename}: missing low-power snapshot")
        require(isinstance(environment["osVersion"], str) and environment["osVersion"], f"{filename}: missing OS snapshot")
    memory = report["memory"]
    for key in ["allocatedBeforeRendererBytes", "peakSampledMetalResourceBytes", "allocatedAtEndBytes"]:
        number(memory[key], f"{filename}/{key}")
    require(memory["peakSampledMetalResourceBytes"] >= memory["allocatedAtEndBytes"], f"{filename}: sampled memory peak below final allocation")
    require([case["mode"] for case in report["scenes"]] == [s[0] for s in SCENARIOS], f"{filename}: scenarios differ")
    cases = []
    for scene, (mode, relief, cutaway) in zip(report["scenes"], SCENARIOS):
        require(scene["requestedRelief"] == relief and scene["cutaway"] is cutaway, f"{filename}/{mode}: scenario controls differ")
        frames = scene["frames"]
        require(len(frames) == 30, f"{filename}/{mode}: expected 30 measured raw frames")
        expected_vertices, expected_bytes = GEOMETRY_COUNTS[cutaway]
        for ordinal, frame in enumerate(frames):
            label = f"{filename}/{mode}/{ordinal}"
            require(type(frame["ordinal"]) is int and frame["ordinal"] == ordinal
                    and type(frame["stateRowIndex"]) is int and frame["stateRowIndex"] == ordinal * 1023 // 29,
                    f"{label}: frame ordinal/retained-row selection changed")
            require(frame["changedObservation"] is True, f"{label}: measured a duplicate cached observation")
            require(frame["vertexCount"] == expected_vertices and frame["geometryBufferBytes"] == expected_bytes,
                    f"{label}: geometry/buffer counts differ from fixed atlas v1 and marker/reference workload")
            require(frame["requestedRelief"] == relief and frame["meshFallback"] is None, f"{label}: unexpected relief request or mesh fallback")
            actual_relief = number(frame["appliedRelief"], f"{label}/appliedRelief")
            require(actual_relief == 0 if relief == 0 else 0 < actual_relief <= relief * 4 * 0.68 * 0.32 + 1e-12,
                    f"{label}: actual relief violates its fixed endpoint envelope")
            # The exact triangulated sphere has slightly less volume than 4π/3.
            # Using the enclosing analytic sphere here is an explicit conservative
            # tolerance; the renderer validates against its exact triangle volume.
            require(number(frame["volumeError"], label) <= 0.68 * (4 * math.pi / 3) * 2e-6,
                    f"{label}: reported complete-mesh volume error exceeds tolerance")
            for key in METRICS: number(frame[key], f"{label}/{key}")
            component_wall = frame["cpuUpdateMs"] + frame["cpuEncodeSubmitMs"] + frame["waitWallMs"]
            require(math.isclose(component_wall, frame["serialFrameWallMs"], rel_tol=1e-9, abs_tol=1e-6),
                    f"{label}: serial wall does not equal its recorded contiguous CPU/wait intervals")
        distributions = {key: distribution([f[key] for f in frames]) for key in METRICS}
        distributions["cpuPreparationMs"] = distribution([f["cpuUpdateMs"] + f["cpuEncodeSubmitMs"] for f in frames])
        cases.append({"mode": mode, "distributions": distributions,
                      "maximumVolumeError": max(f["volumeError"] for f in frames),
                      "appliedReliefRange": [min(f["appliedRelief"] for f in frames), max(f["appliedRelief"] for f in frames)],
                      "vertexCount": expected_vertices, "geometryBufferBytes": expected_bytes})
    return {"report": filename, "sha256": digest, "bytes": raw_bytes, "host": host, "run": run_number,
            "startedAtUTC": report["startedAtUTC"], "completedAtUTC": report["completedAtUTC"],
            "device": device, "environmentBefore": report["environmentBefore"], "environmentAfter": report["environmentAfter"],
            "memory": memory, "pipelineAndAtlasConstructionMs": w["pipelineAndAtlasConstructionMs"],
            "elapsedRenderingWorkMs": elapsed, "scenes": cases}


def compare_documents(documents: list[tuple[str, dict[str, Any], str, int]]) -> dict[str, Any]:
    require(len(documents) == 6 and sorted(item[0] for item in documents) == sorted(NAMES),
            "Exactly the six predeclared named reports are required, with no duplicates")
    documents = sorted(documents, key=lambda item: NAMES.index(item[0]))
    reference = None
    runs = []
    for name, report, digest, byte_count in documents:
        runs.append(summarize(report, name, digest, byte_count))
        current = identity(report, name)
        if reference is None: reference = current
        require(current == reference, f"{name}: executable, Swift sources, resources or fixed workload differ")
    for host in HOSTS:
        group = [r for r in runs if r["host"] == host]
        require(all(r["device"] == group[0]["device"] for r in group), f"{host}: device properties changed between runs")
        for previous, current in zip(group, group[1:]):
            require(timestamp(current["startedAtUTC"], host) >= timestamp(previous["completedAtUTC"], host),
                    f"{host}: numbered run clocks overlap or reverse")
    return {"schema": "reservoir-state-surface-profile-comparison-v1", "status": "verified",
            "verification": "All six complete reports match executable, Swift sources, four resources, fixed workload, selected rows and atlas geometry; raw timings independently summarized",
            "reportCount": 6, "measuredFrameCount": 540, "warmupFrameCount": 144,
            "identity": reference, "runs": runs,
            "quantiles": "Sorted raw frames, linear interpolation at (n-1)*p; n=30 measured frames per scenario per run",
            "limitations": ["All three consecutive runs per host remain separate, including run 1; no fastest-run selection or pooled frame inference.",
                "68 percent fill is a fixed preview parameter; native state rows have no paired fill or row timestamps.",
                "Report clocks establish within-host ordering only; cross-host clocks are not authenticated synchronization.",
                "Offscreen serial measurements do not establish presented FPS, input latency, energy, memory bandwidth or a general chip ranking.",
                "Background work is uncontrolled; source hashes describe inspected staged files, separately from executable identity.",
                "Mesh error comparison uses a conservative analytic-sphere tolerance; the native renderer separately checks its exact closed triangle volume."]}


def compare_files(paths: list[Path]) -> dict[str, Any]:
    require(len(set(p.resolve() for p in paths)) == len(paths), "Duplicate input path")
    documents = []
    for path in paths:
        with path.open("rb") as handle: raw = handle.read(2 * 1024 * 1024 + 1)
        require(raw and len(raw) <= 2 * 1024 * 1024, f"{path}: empty report or exceeds 2 MiB bound")
        documents.append((path.name, json.loads(raw), hashlib.sha256(raw).hexdigest(), len(raw)))
    return compare_documents(documents)


def markdown(result: dict[str, Any]) -> str:
    lines = ["# State surface: retained offscreen comparison", "",
             "Verified **6 reports and 540 measured frames**: three consecutive retained runs per host, three scenarios per run, 30 measured frames per scenario. Each scenario also rendered 8 unmeasured warmup frames (144 across the six reports).", "",
             "Executable, Swift source, evidence-resource, fixed-workload and geometry checks passed. All values below are **milliseconds, median / p95**, independently recomputed from raw frames. Run 1 remains included.", "",
             "| Host | Run | Scenario | CPU update | CPU encode / submit | GPU command | Completion wait | Serial wall |",
             "|---|---:|---|---:|---:|---:|---:|---:|"]
    for run in result["runs"]:
        for scene in run["scenes"]:
            cells = [f"{scene['distributions'][m]['median']:.3f} / {scene['distributions'][m]['p95']:.3f}" for m in METRICS]
            lines.append(f"| {run['host']} | {run['run']} | {scene['mode']} | " + " | ".join(cells) + " |")
    lines += ["", "| Report | Thermal before → after | Low power before → after | Peak sampled Metal MiB | Construction ms | Rendering work ms |",
              "|---|---|---|---:|---:|---:|"]
    for run in result["runs"]:
        before, after = run["environmentBefore"], run["environmentAfter"]
        lines.append(f"| {run['report']} | {before['thermalState']} → {after['thermalState']} | "
                     f"{before['lowPowerModeEnabled']} → {after['lowPowerModeEnabled']} | "
                     f"{run['memory']['peakSampledMetalResourceBytes']/2**20:.3f} | "
                     f"{run['pipelineAndAtlasConstructionMs']:.3f} | {run['elapsedRenderingWorkMs']:.3f} |")
    lines += ["", "The geometry uses **68% preview fill**. This is a fixed rendering parameter, not an observation paired with these state rows.", "",
              "Quantiles use sorted raw frames and linear interpolation at `(n − 1) × p`. The JSON companion retains all per-run distributions, report hashes, device/environment snapshots and common artifact identity.", "",
              "## Input receipt", "", "| Retained report | SHA-256 |", "|---|---|"]
    for run in result["runs"]: lines.append(f"| {run['report']} | `{run['sha256']}` |")
    lines += ["", "## Scope", ""] + [f"- {limitation}" for limitation in result["limitations"]]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs=6, type=Path, help="The six named report files")
    parser.add_argument("--output-prefix", type=Path, required=True,
                        help="Research-local prefix; writes PREFIX.json and PREFIX.md")
    args = parser.parse_args()
    result = compare_files(args.reports)
    prefix = args.output_prefix.resolve()
    require(prefix.is_relative_to(ROOT.resolve()), "Comparison outputs must stay inside the research repository")
    prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path, markdown_path = Path(str(prefix) + ".json"), Path(str(prefix) + ".md")
    inputs = {path.resolve() for path in args.reports}
    require(json_path not in inputs and markdown_path not in inputs, "Comparison output cannot replace an input report")
    json_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    markdown_path.write_text(markdown(result))
    print(json.dumps({"status": "verified", "reportCount": 6, "measuredFrameCount": 540,
                      "json": str(json_path), "markdown": str(markdown_path)}))


if __name__ == "__main__":
    main()
