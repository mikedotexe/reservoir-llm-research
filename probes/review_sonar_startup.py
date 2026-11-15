#!/usr/bin/env python3
"""Capture a bounded startup reading and compare leak only on a saved scan copy.

Requires NumPy for paired numerical continuations saved as JSON.
Reads named local session stores; writes only a new output directory. No model
calls, source writes or live interventions. Captures are not full native exports.
The independent recurrence must reproduce native signed curves/calibration first.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

from observe_sonar_exploration import read_regular, utc_now
from refine_reservoir_sonar import Frozen


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def capture(root):
    for _ in range(5):
        raw = read_regular(root / "manifest.json")
        manifest = json.loads(raw)
        checkpoint = read_regular(root / "checkpoints" / (manifest["checkpointSha256"] + ".json"))
        assert hashlib.sha256(checkpoint).hexdigest() == manifest["checkpointSha256"]
        if raw == read_regular(root / "manifest.json"):
            return manifest, json.loads(checkpoint)["state"], raw, checkpoint
    raise ValueError("No stable manifest/checkpoint boundary captured")


def return_step(curve):
    if curve[0] <= 1e-9:
        return None
    return next((i + 1 for i in range(len(curve) - 4)
                 if np.all(curve[i:i + 5] <= .1 * curve[0])), None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("protocol", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--entries", type=int, default=3)
    args = parser.parse_args()
    assert 1 <= args.entries <= 10
    protocol = json.loads(args.protocol.read_text())
    for arm in protocol["arms"]:
        assert not args.output.resolve().is_relative_to(Path(arm["sessionPath"]).resolve())
    args.output.mkdir(parents=True, exist_ok=False)
    summaries, states = [], {}
    for arm in protocol["arms"]:
        name, root = arm["arm"], Path(arm["sessionPath"])
        manifest, state, raw, checkpoint = capture(root)
        states[name] = state
        folder = args.output / name
        folder.mkdir()
        (folder / "manifest.capture.json").write_bytes(raw)
        (folder / "checkpoint.capture.json").write_bytes(checkpoint)
        receipts = {r["journalId"]: r for r in state["actionState"]["recentReceipts"]}
        journals = []
        for path in (root / "journals").glob("*.json"):
            content = read_regular(path)
            journal = json.loads(content)
            journals.append((journal["pending"]["entry"]["observedStep"], path, content, journal))
        rows = []
        for _, path, content, journal in sorted(journals)[:args.entries]:
            pending = journal["pending"]
            entry, response = pending["entry"], pending["response"]
            receipt = receipts.get(entry["id"])
            (folder / path.name).write_bytes(content)
            rows.append({
                "journalId": entry["id"], "observedStep": entry["observedStep"],
                "fileSha256": hashlib.sha256(content).hexdigest(),
                "body": entry["body"], "next": pending["action"]["request"],
                "input": pending["action"]["reservoirInput"],
                "receipt": receipt, "timing": journal.get("timing"),
                "response": {k: v for k, v in response.items() if k != "text"},
                "scannerContractSupplied": "COPIED RECURRENT RESPONSE SCANNER compact-scan-v2" in pending["prompt"],
            })
        summaries.append({
            "arm": name, "sessionId": manifest["sessionId"], "phase": manifest["phase"],
            "capturedStep": state["step"], "savedJournals": manifest["journalCount"],
            "elapsedMillis": manifest["elapsedMillis"], "controls": state["actionState"]["controls"],
            "heldInputL2": float(np.linalg.norm(state["heldVector"])),
            "diagnostics": manifest["diagnostics"], "entries": rows,
        })
    scan = states["gemma"]["sonarState"]["latestCompactScan"]
    save(args.output / "source-compact-scan.json", scan)
    engine = Frozen(scan["origin"])
    baseline = engine.rollout(np.zeros((1, 48)), 64)[0][0]
    errors = []
    for candidate in scan["candidates"]:
        direction = np.array(candidate["unitInput"])
        paths = engine.rollout(np.array([direction, -direction]) * scan["epsilon"], 64)[0]
        for i, sign in enumerate(("positive", "negative")):
            curve = np.linalg.norm(paths[i] - baseline, axis=1)
            errors.append(float(np.max(np.abs(curve - candidate[sign + "ResponseL2"]))))
    calibration = np.array(scan["calibrationDirection"]) * scan["epsilon"]
    paths = engine.rollout(np.array([calibration, -calibration]), 1)[0]
    for i, key in enumerate(("calibrationPositive", "calibrationNegative")):
        errors.append(float(np.max(np.abs(paths[i, 0] - baseline[0] - scan[key]))))
    assert errors and max(errors) < 1e-10, errors
    unit = np.array(next(c for c in scan["candidates"] if c["direction"] == "strongest")["unitInput"])
    comparisons = []
    for leak in (.2, .4, .65, .85):
        origin = copy.deepcopy(scan["origin"])
        origin["controls"]["leak"] = leak
        frozen = Frozen(origin)
        control = frozen.rollout(np.zeros((1, 48)), 64)[0][0]
        paths = frozen.rollout(np.array([unit, -unit]) * .001, 64)[0]
        curves = np.linalg.norm(paths - control, axis=2)
        absent = copy.deepcopy(origin)
        absent["heldVector"] = [0.] * 48
        no_text = Frozen(absent).rollout(np.zeros((1, 48)), 64)[0][0]
        comparisons.append({
            "leak": leak, "positiveCurve": curves[0].tolist(), "negativeCurve": curves[1].tolist(),
            "firstL2": curves[:, 0].tolist(), "returnBelow10PercentForFiveSteps": [return_step(c) for c in curves],
            "fractionRemainingAtStep30": (curves[:, 29] / curves[:, 0]).tolist(),
            "heldVersusWithdrawnL2": np.linalg.norm(control - no_text, axis=1).tolist(),
        })
    result = {"observedAtUtc": utc_now(), "scope": "Startup observations plus one saved Gemma origin; no live parameters changed. Copied futures hold text, controls and noise fixed; no future writer or sensory feedback is simulated.",
              "modelsContactedByReview": False, "arms": summaries,
              "leakComparison": {"sourceScanId": scan["id"], "origin": scan["origin"],
                                 "nativeCurveAndCalibrationMaxError": max(errors),
                                 "probeL2": .001, "rows": comparisons}}
    save(args.output / "review.json", result)
    print(json.dumps({"nativeMatchMaxError": max(errors), "arms": [{k: a[k] for k in ("arm", "phase", "savedJournals", "controls")} for a in summaries],
                      "leakRows": [{k: r[k] for k in ("leak", "firstL2", "returnBelow10PercentForFiveSteps", "fractionRemainingAtStep30")} for r in comparisons]}))


if __name__ == "__main__":
    main()
