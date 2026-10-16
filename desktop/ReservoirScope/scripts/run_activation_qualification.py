#!/usr/bin/env python3
"""Admit one bounded mechanical qualification; no inference retries or host changes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from run_activation_pilot import (APP, prepare_resources, sample_resources, save,
                                  sha256_file, utc_now)

PREPARATION = {"maximumSeconds": 600, "pollSeconds": 10,
               "consecutiveHealthySamples": 3, "minimumFreePercent": 25,
               "requiredPressureLevel": 1}
QUALIFICATION_SECONDS = 900


def source_identity():
    paths = [Path(__file__), APP / "scripts/run_activation_pilot.py",
             APP / "activation-requirements.lock", *(APP / "activation_worker").glob("*.py")]
    return {str(p.relative_to(APP)): sha256_file(p) for p in sorted(paths)}


def run(args, *, sampler=None, monotonic=None, sleep=None, utc_clock=None, execute=None):
    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    sampler, execute = sampler or sample_resources, execute or subprocess.run
    result = {"schema": "activation-qualified-admission/1", "status": "held",
              "automaticRetries": 0, "dispatched": False, "startedAtUtc": utc_now()}
    try:
        sources = source_identity()
        command = [sys.executable, "-B", "-m", "activation_worker.qualify", "--model",
                   str(Path(args.model).expanduser().resolve(strict=True)), "--output",
                   str(output / "qualification")]
        save(output / "launch-plan.json", {"command": command, "cwd": str(APP),
             "preparation": PREPARATION, "qualificationDeadlineSeconds": QUALIFICATION_SECONDS,
             "sourceSha256": sources, "retry": False})
        preparation = prepare_resources(output, 0, "mechanical_qualification", PREPARATION,
                                         sampler=sampler, monotonic=monotonic, sleep=sleep,
                                         utc_clock=utc_clock)
        result["preparation"] = preparation
        if not preparation["ready"]:
            raise RuntimeError("Preparation expired; no model qualification dispatched")
        admission = sampler(10.0)
        admitted = (type(admission.get("pressure")) is int and admission["pressure"] == 1
                    and type(admission.get("freePercent")) is int
                    and 25 <= admission["freePercent"] <= 100)
        save(output / "admission.json", {"capturedAtUtc": utc_now(), "admitted": admitted,
                                         "resource": admission})
        if not admitted:
            raise RuntimeError("Fresh admission refused; no model qualification dispatched")
        if source_identity() != sources:
            raise RuntimeError("Qualification source changed during preparation")
        with (output / "stdout.json").open("x") as stdout, (output / "stderr.txt").open("x") as stderr:
            result["dispatched"] = True
            completed = execute(command, cwd=APP, stdout=stdout, stderr=stderr,
                                check=False, timeout=QUALIFICATION_SECONDS)
        result["returnCode"] = completed.returncode
        report_path = output / "qualification/result.json"
        if report_path.is_file():
            result["qualificationResultSha256"] = sha256_file(report_path)
        if completed.returncode != 0:
            raise RuntimeError("Mechanical qualification failed; attempt retained without retry")
        report = json.loads(report_path.read_text())
        if report.get("passed") is not True or not report.get("checks") or not all(
                value is True for value in report["checks"].values()):
            raise RuntimeError("Qualification did not retain a fully passed result")
        if source_identity() != sources:
            raise RuntimeError("Qualification source changed during execution")
        result["status"] = "passed"
    except (Exception, KeyboardInterrupt) as exc:
        # subprocess.run kills and waits for its own direct child on timeout or
        # interruption. We never kill by executable name or touch another service.
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["finishedAtUtc"] = utc_now()
    save(output / "result.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True)
    outcome = run(parser.parse_args())
    print(json.dumps(outcome, indent=2))
    raise SystemExit(0 if outcome["status"] == "passed" else 1)
