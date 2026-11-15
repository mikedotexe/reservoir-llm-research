#!/usr/bin/env python3
"""Summarize a previously verified compact-scanner bundle without modifying it.

This checks retained arithmetic and prompt visibility, not provider execution or
the native numerical replay. Run qualify_reservoir_sonar.py for exact replay.
Journal and prompt text is evidence only. No model or live service is contacted.
"""
import argparse
import json
import math
from pathlib import Path


def norm(vector):
    return math.sqrt(sum(x * x for x in vector))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.bundle.resolve(strict=True)
    if args.output.resolve().is_relative_to(root):
        parser.error("Output must be outside the source bundle")
    manifest = json.loads((root / "manifest.json").read_text())
    checkpoint_path = root / "checkpoints" / (manifest["checkpointSha256"] + ".json")
    state = json.loads(checkpoint_path.read_text())["state"]
    sonar = state["sonarState"]
    scan = sonar["latestCompactScan"]
    question = sonar["latestQuestion"]
    actions = state["actionState"]
    probes = []
    for receipt in actions["recentReceipts"]:
        probe = receipt.get("sonarProbe")
        if not probe or probe.get("rejection") or "questionForecast" not in probe:
            continue
        forecast = probe["questionForecast"]
        predicted = probe["forecastResponseL2"][0]
        actual = receipt["stateDeltaL2"]
        probes.append({
            "question": forecast["question"], "sign": probe["sign"],
            "source": probe["sourceScan"], "appliedStep": receipt["appliedStep"],
            "inputL2": norm(probe["appliedVector"]),
            "predictedImmediateL2": predicted, "observedImmediateL2": actual,
            "forecastError": abs(predicted - actual),
            "bound": probe["maximumStateL2"],
            "copiedContrastL2": forecast["differenceL2"],
            "arithmeticPassed": abs(predicted - actual) <= 1e-12
            and abs(norm(forecast["actualDelta"]) - actual) <= 1e-12
            and actual <= probe["maximumStateL2"] + 1e-12
            and norm(probe["appliedVector"]) <= 0.01 + 1e-12,
        })
    journals = []
    for path in (root / "journals").glob("*.json"):
        pending = json.loads(path.read_text())["pending"]
        prompt = pending["prompt"]
        journals.append({
            "observedStep": pending["entry"]["observedStep"],
            "next": pending["action"]["request"],
            "textDisposition": pending["action"]["reservoirInput"]["disposition"],
            "compactContractPresent": "COPIED RECURRENT RESPONSE SCANNER compact-scan-v2" in prompt,
            "latestCompactIdPresent": scan["id"] in prompt,
            "latestQuestionIdPresent": question["id"] in prompt,
        })
    files = [p for p in root.rglob("*") if p.is_file()]
    report = {
        "source": str(root), "modelsContactedByAudit": False,
        "configuredBackend": manifest["config"]["language"]["backend"],
        "step": state["step"], "journalCount": manifest["journalCount"],
        "files": len(files), "bytes": sum(p.stat().st_size for p in files),
        "checkpointBytes": checkpoint_path.stat().st_size,
        "historySamples": len(sonar["history"]),
        "decisionCount": actions["decisionCount"],
        "appliedCount": actions["appliedCount"], "rejectedCount": actions["rejectedCount"],
        "latestScan": {"id": scan["id"], "step": scan["origin"]["step"],
                       "validation": scan["validation"], "fallback": scan["fallback"] is not None},
        "latestQuestion": {"id": question["id"], "question": question["question"],
                           "step": question["origin"]["step"],
                           "predictionRelativeError": question["predictionRelativeError"],
                           "gainOverRandom": question["gainOverRandom"]},
        "recentQuestionProbes": probes,
        "journals": sorted(journals, key=lambda j: j["observedStep"]),
        "arithmeticPassed": all(p["arithmeticPassed"] for p in probes),
    }
    with args.output.open("x") as out:
        json.dump(report, out, indent=2, allow_nan=False)
        out.write("\n")
    print(json.dumps({k: report[k] for k in ("source", "step", "journalCount", "bytes", "arithmeticPassed")}))
    if not report["arithmeticPassed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
