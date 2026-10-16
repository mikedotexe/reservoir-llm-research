#!/usr/bin/env python3
"""Run the frozen three-arm pilot once, serially, after real-model qualification.

Uses the same Rust supervisor/store as the app. No live-system endpoints, retries,
or automatic extensions. Incomplete attempts and prior arms remain on disk.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parents[1]
sys.path.insert(0, str(APP))
from activation_worker.manifest import inspect_model
from activation_worker.math_core import canonical_hash, sha256_file, validate_calibration

RESOURCE_PREPARATION = {"maximumSeconds": 120, "pollSeconds": 10,
                        "consecutiveHealthySamples": 3, "minimumFreePercent": 25,
                        "requiredPressureLevel": 1}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def validate_protocol(value):
    """Only the approved preparation can vary the qualified pilot's execution."""
    if not isinstance(value, dict) or value.get("schema") != "activation-pilot-v1":
        raise ValueError("Unsupported activation pilot protocol schema")
    allowed = {"schema", "id", "seed", "temperature", "requestDeadlineSeconds", "arms",
               "stepsBetweenObservations", "journalEveryObservations", "outputTokens",
               "observations", "readingQuestions", "interpretation", "stoppingRule",
               "resourcePreparation", "predecessor", "analysisPriorities", "resourceInterpretation"}
    if value.keys() - allowed:
        raise ValueError(f"Unknown protocol fields: {sorted(value.keys() - allowed)}")
    for name in ("id", "interpretation", "stoppingRule"):
        if not isinstance(value.get(name), str) or not value[name].strip():
            raise ValueError(f"Protocol requires nonempty {name}")
    arms = value.get("arms")
    if (not isinstance(arms, list) or len(arms) != 3 or any(not isinstance(x, str) for x in arms)
            or set(arms) != {"decaying_trace", "no_steering", "recurrent"}):
        raise ValueError("Protocol requires each of the three approved arms exactly once")
    if type(value.get("seed")) is not int or not 0 <= value["seed"] <= 2**64-1:
        raise ValueError("Protocol seed must be an unsigned 64-bit integer")
    bounds = {"temperature": 0.0, "requestDeadlineSeconds": 180,
              "stepsBetweenObservations": 10, "journalEveryObservations": 2,
              "outputTokens": 1024}
    for name, expected in bounds.items():
        actual = value.get(name)
        if isinstance(actual, bool) or not isinstance(actual, (int, float)) or actual != expected:
            raise ValueError(f"Protocol {name} differs from the qualified supervisor")
        if name != "temperature" and type(actual) is not int:
            raise ValueError(f"Protocol {name} must be an integer")
    observations = value.get("observations")
    if (not isinstance(observations, list) or len(observations) != 12
            or any(not isinstance(x, str) or not x.strip() for x in observations)):
        raise ValueError("Protocol requires twelve nonempty observations")
    questions = value.get("readingQuestions")
    if not isinstance(questions, list) or not questions or any(not isinstance(x, str) or not x.strip() for x in questions):
        raise ValueError("Protocol requires nonempty reading questions")
    if "resourcePreparation" in value:
        preparation = value["resourcePreparation"]
        if (not isinstance(preparation, dict) or preparation != RESOURCE_PREPARATION
                or any(type(x) is not int for x in preparation.values())):
            raise ValueError("resourcePreparation differs from the approved 120/10/3/25/1 bounds")
    return value


def sample_resources(timeout_seconds):
    """Read macOS admission inputs; command failures remain unknown, never healthy."""
    deadline = time.monotonic() + timeout_seconds
    evidence = []
    for command in (["/usr/sbin/sysctl", "-n", "kern.memorystatus_vm_pressure_level"],
                    ["/usr/bin/memory_pressure", "-Q"]):
        remaining = deadline - time.monotonic()
        try:
            if remaining <= 0:
                raise TimeoutError("Resource sample deadline reached")
            reply = subprocess.run(command, capture_output=True, text=True, check=False,
                                   timeout=min(5.0, remaining))
            evidence.append({"command": command, "returnCode": reply.returncode,
                             "stdout": reply.stdout, "stderr": reply.stderr})
        except (OSError, subprocess.TimeoutExpired, TimeoutError) as exc:
            evidence.append({"command": command, "error": f"{type(exc).__name__}: {exc}"})
    pressure = free = None
    if evidence[0].get("returnCode") == 0:
        try:
            pressure = int(evidence[0]["stdout"].strip())
        except ValueError:
            pass
    if evidence[1].get("returnCode") == 0:
        for line in evidence[1]["stdout"].splitlines():
            if line.startswith("System-wide memory free percentage: "):
                try:
                    parsed = int(line.split(":", 1)[1].strip().removesuffix("%"))
                    free = parsed if 0 <= parsed <= 100 else None
                except ValueError:
                    pass
                break
    return {"pressure": pressure, "freePercent": free, "commands": evidence}


def prepare_resources(output, index, arm, preparation, *, sampler=None, monotonic=None,
                      sleep=None, utc_clock=None):
    sampler, monotonic = sampler or sample_resources, monotonic or time.monotonic
    sleep, utc_clock = sleep or time.sleep, utc_clock or utc_now
    start = monotonic()
    deadline = start + preparation["maximumSeconds"]
    streak = count = 0
    summary = {"arm": arm, "preparation": preparation, "startedAtUtc": utc_clock(),
               "ready": False, "samplesFile": f"condition-{index+1}-resource-samples.jsonl"}
    with (output / summary["samplesFile"]).open("x", encoding="utf-8") as stream:
        while monotonic() < deadline:
            sampled_at = utc_clock()
            sample = sampler(max(0.0, deadline - monotonic()))
            completed = monotonic()
            healthy = (type(sample.get("pressure")) is int
                       and sample["pressure"] == preparation["requiredPressureLevel"]
                       and type(sample.get("freePercent")) is int
                       and preparation["minimumFreePercent"] <= sample["freePercent"] <= 100)
            streak = streak + 1 if healthy else 0
            count += 1
            row = {"sample": count, "sampledAtUtc": sampled_at, "completedAtUtc": utc_clock(),
                   "elapsedSeconds": completed-start, "healthy": healthy,
                   "consecutiveHealthySamples": streak, "resource": sample}
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            if completed <= deadline and streak >= preparation["consecutiveHealthySamples"]:
                summary["ready"] = True
                break
            remaining = deadline - monotonic()
            if remaining > 0:
                sleep(min(preparation["pollSeconds"], remaining))
    summary.update({"finishedAtUtc": utc_clock(), "elapsedSeconds": monotonic()-start,
                    "sampleCount": count, "consecutiveHealthySamples": streak,
                    "reason": "three_consecutive_healthy_samples" if summary["ready"] else "preparation_deadline_reached"})
    save(output / f"condition-{index+1}-resource-preparation.json", summary)
    return summary


def observe_worker_release(python_path, worker_path):
    """Observe exact launch-command absence; the unchanged supervisor owns reaping."""
    result = {"observedAtUtc": utc_now(), "pythonPath": python_path, "workerPath": worker_path,
              "scope": "Exact configured Python -B workerPath command after CLI exit",
              "limitation": "No owned worker PID is exported; command identity does not independently prove ownership or reaping."}
    try:
        reply = subprocess.run(["/bin/ps", "-ww", "-axo", "pid=,ppid=,command="],
                               capture_output=True, text=True, check=False, timeout=5)
        matches = []
        expected = f"{python_path} -B {worker_path}"
        for line in reply.stdout.splitlines():
            parts = line.strip().split(None, 2)
            if len(parts) == 3 and parts[2] == expected:
                matches.append({"pid": int(parts[0]), "parentPid": int(parts[1])})
        result.update({"returnCode": reply.returncode, "matchingProcesses": matches,
                       "status": "unavailable" if reply.returncode else "matching_process_visible" if matches else "no_matching_process_visible",
                       "stderr": reply.stderr})
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        result.update({"status": "unavailable", "error": f"{type(exc).__name__}: {exc}"})
    return result


def save(path: Path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run(args, *, resource_sampler=None, monotonic=None, sleep=None, utc_clock=None,
        release_observer=None) -> dict:
    output = Path(args.output).expanduser().absolute()
    output.mkdir(parents=True, exist_ok=False)
    result = {"schema": "activation-pilot-result-v1", "status": "held", "arms": [],
              "automaticRetries": 0, "readingComplete": False}
    try:
        fixture_path = Path(getattr(args, "protocol", None) or ROOT / "shared/reservoir-scope/activation-pilot.json").expanduser().resolve(strict=True)
        fixture_bytes = fixture_path.read_bytes()
        fixture = validate_protocol(json.loads(fixture_bytes))
        protocol_sha256 = hashlib.sha256(fixture_bytes).hexdigest()
        runner_path = Path(__file__).resolve()
        runner_sha256 = sha256_file(runner_path)
        binary = Path(args.binary).expanduser().resolve(strict=True)
        qualification = Path(args.qualification).expanduser().resolve(strict=True)
        report = read(qualification / "result.json")
        plan = read(qualification / "plan.json")
        initialization = read(qualification / "initialization.json")
        if report.get("passed") is not True or not report.get("checks") or not all(v is True for v in report["checks"].values()):
            raise ValueError("Real-model qualification has not passed")
        if report["planSha256"] != canonical_hash(plan):
            raise ValueError("Qualification plan identity differs")
        if report["planFileSha256"] != sha256_file(qualification / "plan.json"):
            raise ValueError("Qualification plan file differs")
        inspected = inspect_model(args.model)
        manifest = inspected["manifest"]
        if manifest != plan["manifest"] or manifest != initialization["manifest"]:
            raise ValueError("Qualified model, worker, or runtime identity changed")
        lock = APP / "activation-requirements.lock"
        for line in lock.read_text().splitlines():
            if not line or line.startswith("#"):
                continue
            package, version = line.split("==", 1)
            if importlib.metadata.version(package) != version:
                raise ValueError(f"Runtime differs from frozen dependency lock: {package}")
        calibration = validate_calibration(initialization["calibration"], manifest["sha256"])
        if (calibration != read(qualification / "calibration.json")
                or calibration["sha256"] != report["calibrationSha256"]
                or sha256_file(qualification / "calibration.json") != report["calibrationFileSha256"]):
            raise ValueError("Calibration differs from the qualified artifact")
        calibration_path = output / "calibration.json"
        save(calibration_path, calibration)
        binary_sha256 = sha256_file(binary)
        save(output / "frozen-plan.json", {
            "schema": "activation-pilot-freeze-v1", "pilot": fixture,
            "fixtureSha256": protocol_sha256,
            "protocolPath": str(fixture_path), "protocolSha256": protocol_sha256,
            "runnerPath": str(runner_path), "runnerSha256": runner_sha256,
            "calibrationSha256": calibration["sha256"],
            "modelManifest": manifest, "python": sys.executable,
            "binary": str(binary), "binarySha256": binary_sha256,
            "lockSha256": sha256_file(lock),
            "qualificationResultSha256": sha256_file(qualification / "result.json"),
            "qualificationDirectory": str(qualification),
            "readingAllocation": {f"Reading {chr(65+i)}": arm for i, arm in enumerate(fixture["arms"])},
        })
        for index, arm in enumerate(fixture["arms"]):
            if "resourcePreparation" in fixture:
                prepared = prepare_resources(output, index, arm, fixture["resourcePreparation"],
                                             sampler=resource_sampler, monotonic=monotonic,
                                             sleep=sleep, utc_clock=utc_clock)
                result.setdefault("resourcePreparations", []).append(prepared)
                if not prepared["ready"]:
                    raise RuntimeError(f"Comparison held before condition {index+1}: bounded resource preparation did not become ready")
            if sha256_file(binary) != binary_sha256:
                raise ValueError("Pilot binary changed between conditions")
            if sha256_file(runner_path) != runner_sha256:
                raise ValueError("Pilot runner changed after protocol freeze")
            if sha256_file(fixture_path) != protocol_sha256:
                raise ValueError("Pilot protocol changed after freeze")
            config = {"pythonPath": sys.executable,
                      "workerPath": str(APP / "activation_worker/__main__.py"),
                      "modelPath": inspected["modelPath"], "arm": arm,
                      "seed": fixture["seed"], "observations": fixture["observations"],
                      "stepsBetween": fixture["stepsBetweenObservations"],
                      "journalEvery": fixture["journalEveryObservations"],
                      "maxJournalTokens": fixture["outputTokens"], "gain": 0.01}
            config_path = output / f"condition-{index+1}.json"
            save(config_path, config)
            command = [str(binary), "--activation-run", str(config_path),
                       "--output", str(output / f"condition-{index+1}"),
                       "--activation-calibration", str(calibration_path)]
            with (output / f"condition-{index+1}-stdout.json").open("x") as stdout, (output / f"condition-{index+1}-stderr.txt").open("x") as stderr:
                # Each model request is independently bounded to 180 seconds by Rust.
                completed = subprocess.run(command, stdout=stdout, stderr=stderr, check=False)
            arm_result = {"arm": arm, "returnCode": completed.returncode, "command": command}
            result["arms"].append(arm_result)
            release = (release_observer or observe_worker_release)(config["pythonPath"], config["workerPath"])
            release_file = f"condition-{index+1}-worker-release-observation.json"
            save(output / release_file, release)
            arm_result["workerReleaseObservationFile"] = release_file
            if completed.returncode != 0:
                raise RuntimeError(f"Pilot stopped at the first failed/refused condition: {arm}")
            snapshot = read(output / f"condition-{index+1}-stdout.json")
            directory = Path(snapshot["directory"])
            if snapshot["status"] != "completed" or snapshot["journalCount"] != 6 or snapshot["step"] != 121:
                raise RuntimeError("Completed condition did not reach the frozen boundary")
            if read(directory / "calibration.json") != calibration:
                raise RuntimeError("Condition did not use the frozen calibration")
            verify = subprocess.run([str(binary), "--verify-activation", str(directory)], capture_output=True, text=True, check=False)
            save(output / f"condition-{index+1}-verification.json", {"returnCode": verify.returncode, "stdout": verify.stdout, "stderr": verify.stderr})
            if verify.returncode:
                raise RuntimeError("Completed condition failed offline replay")
            arm_result.update({"sessionId": snapshot["sessionId"], "directory": str(directory), "journalCount": snapshot["journalCount"]})
            # A separate prose-only packet permits a fresh reader to stay blind.
            save(output / f"reading-{chr(65+index)}.json", {
                "label": f"Reading {chr(65+index)}", "questions": fixture["readingQuestions"],
                "entries": [{"number": n+1, "text": journal["text"], "observedStep": journal["observedStep"]}
                            for n, journal in enumerate(snapshot["journals"])],
            })
        result["status"] = "completed-awaiting-reading"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    save(output / "result.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--qualification", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--protocol", help="Explicit frozen activation-pilot-v1 protocol; defaults to the original pilot")
    result = run(parser.parse_args())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "completed-awaiting-reading" else 1)
