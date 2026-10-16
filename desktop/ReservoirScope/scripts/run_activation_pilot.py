#!/usr/bin/env python3
"""Run the frozen three-arm pilot once, serially, after real-model qualification.

Uses the same Rust supervisor/store as the app. No live-system endpoints, retries,
or automatic extensions. Incomplete attempts and prior arms remain on disk.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parents[1]
sys.path.insert(0, str(APP))
from activation_worker.manifest import inspect_model
from activation_worker.math_core import canonical_hash, sha256_file, validate_calibration


def save(path: Path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run(args) -> dict:
    output = Path(args.output).expanduser().absolute()
    output.mkdir(parents=True, exist_ok=False)
    result = {"schema": "activation-pilot-result-v1", "status": "held", "arms": [],
              "automaticRetries": 0, "readingComplete": False}
    try:
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
        fixture_path = ROOT / "shared/reservoir-scope/activation-pilot.json"
        fixture = read(fixture_path)
        if fixture.get("temperature") != 0.0 or fixture.get("requestDeadlineSeconds") != 180:
            raise ValueError("Pilot decoding or request bounds differ from the qualified supervisor")
        binary_sha256 = sha256_file(binary)
        save(output / "frozen-plan.json", {
            "schema": "activation-pilot-freeze-v1", "pilot": fixture,
            "fixtureSha256": sha256_file(fixture_path),
            "calibrationSha256": calibration["sha256"],
            "modelManifest": manifest, "python": sys.executable,
            "binary": str(binary), "binarySha256": binary_sha256,
            "lockSha256": sha256_file(lock),
            "qualificationResultSha256": sha256_file(qualification / "result.json"),
            "qualificationDirectory": str(qualification),
            "readingAllocation": {f"Reading {chr(65+i)}": arm for i, arm in enumerate(fixture["arms"])},
        })
        for index, arm in enumerate(fixture["arms"]):
            if sha256_file(binary) != binary_sha256:
                raise ValueError("Pilot binary changed between conditions")
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
    result = run(parser.parse_args())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "completed-awaiting-reading" else 1)
