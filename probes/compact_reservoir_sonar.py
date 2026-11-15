#!/usr/bin/env python3
"""Test two-branch calibration of known-wiring local sensitivity on copied states.

NumPy is needed for linear algebra. Separate follow-up protocol in the sonar
resolution study. Never writes native receipts or calls models/services.
"""
import argparse
import json
from pathlib import Path
import subprocess

import numpy as np

from refine_reservoir_sonar import (CALIBRATION, Frozen, LABELS, OFFSETS,
                                  coordinate_maps, metrics, qualify_native, relative, sha)


def calibrate(engine, candidates):
    projections = candidates @ engine.b.T
    conditioning = np.min(np.abs(projections) / np.linalg.norm(engine.b, axis=1), axis=1)
    best = int(np.argmax(conditioning))
    direction = candidates[best]
    drive = engine.b @ direction
    if np.min(np.abs(drive)) < 1e-9:
        raise ValueError("Unresolved calibration direction")
    paths, _ = engine.rollout(np.array([direction, -direction]) * CALIBRATION, 1)
    gates = np.clip((paths[0, 0] - paths[1, 0]) / (2 * CALIBRATION * drive), 0, engine.a)
    return gates[:, None] * engine.b, gates, direction, float(conditioning[best])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.reports.resolve()):
        parser.error("Output must be outside native reports")
    sources = [args.reports / f"{label}-scan.json" for label in LABELS]
    before = {str(p): sha(p) for p in sources}
    args.output.mkdir(parents=True, exist_ok=False)
    calibration_rng = np.random.Generator(np.random.PCG64(20261117))
    candidates = calibration_rng.standard_normal((256, 48))
    candidates /= np.linalg.norm(candidates, axis=1, keepdims=True)
    test_rng = np.random.Generator(np.random.PCG64(20261118))
    test = test_rng.standard_normal((32, 48))
    test /= np.linalg.norm(test, axis=1, keepdims=True)
    signed = np.concatenate([test, -test])
    rows, arrays, checks = [], {"calibrationCandidates": candidates, "freshTestDirections": signed}, []
    for label, path in zip(LABELS, sources):
        report = json.loads(path.read_text())
        assert report["status"] == "scanned" and report["modelsContacted"] is False
        engine = Frozen(report["scan"]["origin"])
        checks.append({"label": label, **qualify_native(engine, report["scan"])})
        for offset in OFFSETS:
            shifted = engine.at_offset(offset)
            compact, gates, direction, condition = calibrate(shifted, candidates)
            full, _, _ = coordinate_maps(shifted, CALIBRATION, 1)
            analytic, true_gates, preclip = shifted.analytic()
            baseline, _ = shifted.rollout(np.zeros((1, 48)), 1)
            paths, _ = shifted.rollout(signed * CALIBRATION, 1)
            actual = paths[:, 0] - baseline[0, 0]
            compact_prediction = CALIBRATION * signed @ compact.T
            full_prediction = CALIBRATION * signed @ full[0].T
            key = f"{label}_offset{offset}"
            arrays.update({f"{key}_compact": compact, f"{key}_full": full[0],
                           f"{key}_analytic": analytic, f"{key}_gates": gates,
                           f"{key}_trueGates": true_gates, f"{key}_calibrationDirection": direction,
                           f"{key}_response": actual, f"{key}_compactPrediction": compact_prediction,
                           f"{key}_fullPrediction": full_prediction})
            rows.append({"label": label, "offset": offset, "step": shifted.origin["step"],
                         "historicalEndpoint": offset == 0, "sourceScanId": report["scan"]["id"],
                         "minimumNormalizedCalibrationDrive": condition,
                         "clippedCoordinates": int(np.sum(np.abs(preclip) >= 1)),
                         "compactToFullMapRelativeError": relative(compact - full[0], full[0]),
                         "compactToAnalyticMapRelativeError": relative(compact - analytic, analytic),
                         "maximumGateAbsoluteError": float(np.max(np.abs(gates - true_gates))),
                         "compact": metrics(compact_prediction, actual),
                         "full": metrics(full_prediction, actual)})
    np.savez_compressed(args.output / "arrays.npz", **arrays)
    unchanged = before == {str(p): sha(p) for p in sources}
    if not unchanged:
        raise ValueError("Source receipts changed")
    pooled_ratio = float(np.sqrt(sum(r["compact"]["absoluteErrorL2"] ** 2 for r in rows) /
                                sum(r["full"]["absoluteErrorL2"] ** 2 for r in rows)))
    targets = {"all48WithinOnePercent": all(r["compact"]["aggregateRelativeError"] <= .01 for r in rows),
               "pooledCompactErrorAtMostTwiceFull": pooled_ratio <= 2}
    repo = Path(__file__).resolve().parent.parent
    script_files = [Path(__file__), repo / "probes/refine_reservoir_sonar.py", repo / "probes/map_sustained_response.py",
                    repo / "research/studies/2026-11-15-sonar-resolution.md"]
    result = {"scope": "Known-wiring two-branch first-step calibration on copies; subsequent test, same six endpoints.",
              "sourceCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
              "modelsContacted": False, "sourceUnchanged": unchanged, "inputHashes": before,
              "sourceHashes": {str(p.relative_to(repo)): sha(p) for p in script_files},
              "numpyVersion": np.__version__, "calibrationSeed": 20261117, "testSeed": 20261118,
              "amplitude": CALIBRATION, "nativeChecks": checks,
              "pooledCompactToFullErrorRatio": pooled_ratio, "targets": targets, "rows": rows}
    (args.output / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"targets": targets, "origins": len(rows), "pooledErrorRatio": pooled_ratio,
                      "maximumCompactError": max(r["compact"]["aggregateRelativeError"] for r in rows),
                      "maximumMapError": max(r["compactToFullMapRelativeError"] for r in rows)}))


if __name__ == "__main__":
    main()
