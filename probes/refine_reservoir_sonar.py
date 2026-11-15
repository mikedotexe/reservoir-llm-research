#!/usr/bin/env python3
"""Qualify finer local response maps and question-directed input probes offline.

NumPy supplies batch linear algebra; Matplotlib is used by the separate renderer.
Reads six native scan receipts only, never sessions, model services or journals.
Protocol: research/studies/2026-11-15-sonar-resolution.md. Output must be new.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import platform
import subprocess

import numpy as np

from map_sustained_response import SplitMix64, model

LABELS = [f"{cohort}-{name}" for cohort in ("independent", "paused")
          for name in ("gemma", "glm", "mistral")]
AMPLITUDES = [0.0001, 0.0003, 0.001, 0.003, 0.01, 0.03, 0.1]
HORIZONS = [1, 2, 4, 8, 16]
OFFSETS = list(range(0, 29, 4))
CALIBRATION = 0.001
FLOOR = 1e-9


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(error, target):
    denominator = float(np.linalg.norm(target))
    return float(np.linalg.norm(error) / denominator) if denominator > FLOOR else None


def metrics(predicted, observed):
    norms = np.linalg.norm(observed, axis=-1)
    errors = np.linalg.norm(predicted - observed, axis=-1)
    valid = norms > FLOOR
    return {"aggregateRelativeError": relative(predicted - observed, observed),
            "absoluteErrorL2": float(np.linalg.norm(predicted - observed)),
            "observedAggregateL2": float(np.linalg.norm(observed)),
            "medianResponseL2": float(np.median(norms)),
            "resolvedDirections": int(valid.sum()), "directions": len(norms),
            "perDirectionRelativeError": [float(e / n) if n > FLOOR else None
                                           for e, n in zip(errors, norms)]}


def forcing(step, dt):
    u = np.zeros(66)
    if (step - 1) % 30 < 12:
        t = (step - 1) * dt
        for i in range(8):
            u[i] = .45 + .35 * np.sin(t * (.19 + i * .07) + i)
        for i in range(8, 16):
            u[i] = .3 + .25 * np.sin(t * (.31 + (i - 8) * .11) + i * .7)
    return u


class Frozen:
    """Independent reconstruction of the native copied recurrence.

    A batch shares exact future noise/forcing; each impulse acts at its first step.
    No writer, action, sensory, clock or checkpoint mutation occurs.
    """
    def __init__(self, origin):
        self.origin = copy.deepcopy(origin)
        self.w, self.win = model(int(origin["seed"]))
        self.w *= origin["controls"]["recurrentGain"]
        self.a = origin["controls"]["leak"]
        self.b = self.win[:, 18:66]

    def inputs(self, horizon):
        origin = self.origin
        rng = SplitMix64(int(origin["rngState"]))
        inputs, noise, rng_states = [], [], [rng.state]
        for offset in range(1, horizon + 1):
            u = forcing(origin["step"] + offset, origin["dt"])
            u[18:] = np.array(origin["heldVector"]) * origin["controls"]["feedbackScale"]
            inputs.append(u)
            noise.append([rng.signed() * origin["noiseAmplitude"] for _ in range(32)])
            rng_states.append(rng.state)
        return np.array(inputs), np.array(noise), rng_states

    def rollout(self, impulses, horizon=16):
        impulses = np.asarray(impulses, dtype=float).reshape(-1, 48)
        assert np.isfinite(impulses).all()
        inputs, noise, _ = self.inputs(horizon)
        x = np.repeat([self.origin["state"]], len(impulses), axis=0)
        path, masks = [], []
        for i in range(horizon):
            drive = self.win[:, :66] @ inputs[i] + self.win[:, 66] + x @ self.w.T
            if i == 0:
                drive += impulses @ self.b.T
            z = (1 - self.a) * x + self.a * np.tanh(drive) + noise[i]
            masks.append(np.abs(z) >= 1)
            x = np.clip(z, -1, 1)
            path.append(x.copy())
        return np.stack(path, axis=1), np.stack(masks, axis=1)

    def at_offset(self, offset):
        origin = copy.deepcopy(self.origin)
        if offset:
            path, _ = self.rollout(np.zeros((1, 48)), offset)
            _, _, rng = self.inputs(offset)
            origin.update(step=origin["step"] + offset, state=path[0, -1].tolist(),
                          rngState=str(rng[-1]))
        return Frozen(origin)

    def zero_state(self):
        origin = copy.deepcopy(self.origin)
        origin["state"] = [0.0] * 32
        return Frozen(origin)

    def analytic(self):
        inputs, noise, _ = self.inputs(1)
        x = np.array(self.origin["state"])
        act = np.tanh(self.win[:, :66] @ inputs[0] + self.win[:, 66] + self.w @ x)
        before = (1 - self.a) * x + self.a * act + noise[0]
        gates = self.a * (1 - act ** 2) * (np.abs(before) < 1)
        return gates[:, None] * self.b, gates, before


def coordinate_maps(engine, amplitude, horizon=16):
    impulses = np.concatenate([np.eye(48), -np.eye(48)]) * amplitude
    paths, clipped = engine.rollout(impulses, horizon)
    # horizon, state coordinate, input coordinate
    matrices = ((paths[:48] - paths[48:]) / (2 * amplitude)).transpose(1, 2, 0)
    return matrices, paths, clipped


def qualify_native(engine, scan):
    baseline, _ = engine.rollout(np.zeros((1, 48)), 64)
    baseline_error = float(np.max(np.abs(baseline[0] - [p["state"] for p in scan["baseline"]])))
    matrices, _, _ = coordinate_maps(engine, scan["epsilon"], 64)
    matrix_error = float(np.max(np.abs(matrices[0] - scan["immediateResponseMatrix"])))
    errors = []
    for candidate in scan["candidates"]:
        unit = np.array(candidate["unitInput"])
        paths, _ = engine.rollout(np.array([unit, -unit]) * scan["epsilon"], 64)
        for i, sign in enumerate(("positive", "negative")):
            curve = np.linalg.norm(paths[i] - baseline[0], axis=1)
            errors.append(float(np.max(np.abs(curve - candidate[f"{sign}ResponseL2"])) ))
    passed = max([baseline_error, matrix_error] + errors) < 1e-10
    result = {"baselineMaxAbsError": baseline_error, "matrixMaxAbsError": matrix_error,
              "candidateCurveMaxAbsError": max(errors), "passed": passed}
    if not passed:
        raise ValueError(f"Native qualification failed: {result}")
    return result


def endpoint(label, scan, directions, permutation, output):
    engine = Frozen(scan["origin"])
    qualification = qualify_native(engine, scan)
    baseline, baseline_clip = engine.rollout(np.zeros((1, 48)))
    signed = np.concatenate([directions, -directions])
    analytical, gates, preclip = engine.analytic()
    arrays = {"heldOutDirections": signed, "inputColumnPermutation": permutation,
              "analyticMap": analytical, "rowGates": gates, "baseline": baseline,
              "preclipState": preclip, "inputWiring": engine.b}
    maps, responses, clip_counts = {}, {}, {}
    for amplitude in AMPLITUDES:
        matrices, coord_paths, clipped = coordinate_maps(engine, amplitude)
        paths, test_clipped = engine.rollout(signed * amplitude)
        maps[amplitude], responses[amplitude] = matrices, paths - baseline
        clip_counts[amplitude] = {"coordinateFirstStepBoundarySwitches": int(np.count_nonzero(clipped[:, 0] != baseline_clip[0, 0])),
                                 "heldOutFirstStepBoundarySwitches": int(np.count_nonzero(test_clipped[:, 0] != baseline_clip[0, 0]))}
        arrays[f"maps_{amplitude}"] = matrices
        arrays[f"heldoutResponse_{amplitude}"] = responses[amplitude]
        arrays[f"coordinateFirstResponse_{amplitude}"] = coord_paths[:, 0] - baseline[0, 0]
    calibrated = maps[CALIBRATION]
    wiring_scale = float(np.sum(calibrated[0] * engine.b) / np.sum(engine.b ** 2))
    scale_results = []
    for i, amplitude in enumerate(AMPLITUDES):
        matrix = maps[amplitude][0]
        plus = arrays[f"coordinateFirstResponse_{amplitude}"][:48]
        minus = arrays[f"coordinateFirstResponse_{amplitude}"][48:]
        row = {"amplitude": amplitude, **clip_counts[amplitude],
               "analyticMapRelativeError": relative(matrix - analytical, analytical),
               "neighboringScaleRelativeChange": None if i == 0 else relative(matrix - maps[AMPLITUDES[i - 1]][0], maps[AMPLITUDES[i - 1]][0]),
               "signedResponseAsymmetry": float(np.linalg.norm(plus + minus) / (np.linalg.norm(plus) + np.linalg.norm(minus))),
               "horizons": []}
        for h in HORIZONS:
            actual = responses[amplitude][:, h - 1]
            predictions = {"calibrated": amplitude * signed @ calibrated[h - 1].T,
                           "scrambled": amplitude * signed @ calibrated[h - 1][:, permutation].T,
                           "zero": np.zeros_like(actual)}
            if h == 1:
                predictions["scaledWiring"] = amplitude * signed @ (wiring_scale * engine.b).T
                predictions["analytic"] = amplitude * signed @ analytical.T
            row["horizons"].append({"horizon": h, **{k: metrics(p, actual) for k, p in predictions.items()}})
        scale_results.append(row)

    # Time samples are a frozen continuation, never additional historical records.
    temporal, time_maps, time_responses = [], [], []
    for offset in OFFSETS:
        shifted = engine.at_offset(offset)
        matrices, _, _ = coordinate_maps(shifted, CALIBRATION, 1)
        base, _ = shifted.rollout(np.zeros((1, 48)), 1)
        paths, _ = shifted.rollout(signed * CALIBRATION, 1)
        j, gate, pre = shifted.analytic()
        singular = np.linalg.svd(matrices[0], compute_uv=False)
        energy = singular ** 2
        temporal.append({"offset": offset, "step": shifted.origin["step"],
                         "historicalEndpoint": offset == 0,
                         "nextForcingPhase": shifted.origin["step"] % 30,
                         "nextForcingOn": shifted.origin["step"] % 30 < 12,
                         "clippedCoordinates": int(np.sum(np.abs(pre) >= 1)),
                         "singularEnergyParticipation": float(energy.sum() ** 2 / (energy @ energy)),
                         "resolvedSingularDirections": int(np.sum(singular > max(FLOOR, singular[0] * 1e-6))),
                         "analyticMapRelativeError": relative(matrices[0] - j, j)})
        time_maps.append(matrices[0]); time_responses.append(paths[:, 0] - base[0, 0])
    for index, row in enumerate(temporal):
        other_mean = np.mean([m for i, m in enumerate(time_maps) if i != index], axis=0)
        actual = time_responses[index]
        row["currentMap"] = metrics(CALIBRATION * signed @ time_maps[index].T, actual)
        row["otherTimesMeanMap"] = metrics(CALIBRATION * signed @ other_mean.T, actual)
        row["currentToOtherMeanMapDistance"] = relative(time_maps[index] - other_mean, time_maps[index])
    arrays.update(temporalMaps=np.array(time_maps), temporalResponses=np.array(time_responses),
                  temporalOffsets=np.array(OFFSETS))

    # Choose a direction from competing calibration maps, then measure its effect.
    zero = engine.zero_state()
    null_base, _ = zero.rollout(np.zeros((1, 48)), 1)
    null_maps, _, _ = coordinate_maps(zero, CALIBRATION, 1)
    delta = calibrated[0] - null_maps[0]
    _, singular, vt = np.linalg.svd(delta, full_matrices=False)
    bespoke = vt[0]
    bespoke *= 1 if bespoke[np.argmax(abs(bespoke))] >= 0 else -1
    arrays.update(zeroStateMap=null_maps[0], bespokeUnitInput=bespoke, mapDifference=delta)
    question_results = []
    for amplitude in (CALIBRATION, .01):
        chosen = np.array([bespoke, -bespoke])
        actual_paths, _ = engine.rollout(chosen * amplitude, 1)
        null_paths, _ = zero.rollout(chosen * amplitude, 1)
        observed_gap = (actual_paths[:, 0] - baseline[0, 0]) - (null_paths[:, 0] - null_base[0, 0])
        predicted_gap = amplitude * chosen @ delta.T
        random_null, _ = zero.rollout(signed * amplitude, 1)
        random_gap = responses[amplitude][:, 0] - (random_null[:, 0] - null_base[0, 0])
        gap_norms = np.linalg.norm(observed_gap, axis=1)
        random_norms = np.linalg.norm(random_gap, axis=1)
        question_results.append({"amplitude": amplitude, "prediction": metrics(predicted_gap, observed_gap),
                                 "positiveGapL2": float(gap_norms[0]), "negativeGapL2": float(gap_norms[1]),
                                 "randomMedianGapL2": float(np.median(random_norms)),
                                 "randomMaximumGapL2": float(random_norms.max()),
                                 "gainOverMedianRandom": float(gap_norms.mean() / np.median(random_norms)),
                                 "gainOverMaximumRandom": float(gap_norms.mean() / random_norms.max())})
        arrays[f"bespokeObservedGap_{amplitude}"] = observed_gap
        arrays[f"bespokePredictedGap_{amplitude}"] = predicted_gap
        arrays[f"randomObservedGap_{amplitude}"] = random_gap

    np.savez_compressed(output / f"{label}-arrays.npz", **arrays)
    temporal_current = np.sqrt(sum(r["currentMap"]["absoluteErrorL2"] ** 2 for r in temporal))
    temporal_other = np.sqrt(sum(r["otherTimesMeanMap"]["absoluteErrorL2"] ** 2 for r in temporal))
    temporal_ratio = float(temporal_other / temporal_current)
    small = scale_results[2]["horizons"][0]
    result = {"label": label, "sourceScanId": scan["id"], "origin": scan["origin"],
              "nativeQualification": qualification, "calibrationAmplitude": CALIBRATION,
              "staticWiringFittedScalar": wiring_scale, "resolution": scale_results,
              "temporalSamples": temporal, "temporalOtherToCurrentErrorRatio": temporal_ratio,
              "questionProbe": {"hypotheses": "actual vs zero starting state; same input/phase/noise/controls",
                                "leadingMapDifferenceGain": float(singular[0]), "trials": question_results},
              "targets": {"unseenDirectionErrorAtMost5Percent": small["calibrated"]["aggregateRelativeError"] <= .05,
                          "currentMapAtLeastTwiceAsAccurateAsOtherTimes": temporal_ratio >= 2,
                          "questionPredictionWithin5Percent": question_results[0]["prediction"]["aggregateRelativeError"] <= .05,
                          "questionAtLeastTwiceMedianRandom": question_results[0]["gainOverMedianRandom"] >= 2}}
    print(json.dumps({"label": label, "native": qualification,
                      "unseenError": small["calibrated"]["aggregateRelativeError"],
                      "wiringError": small["scaledWiring"]["aggregateRelativeError"],
                      "temporalErrorRatio": temporal_ratio,
                      "question": question_results[0], "targets": result["targets"]}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    sources = [args.reports / f"{label}-scan.json" for label in LABELS]
    if args.output.resolve().is_relative_to(args.reports.resolve()):
        parser.error("Output must be outside native report directory")
    before = {str(p): sha(p) for p in sources}
    reports = [json.loads(p.read_text()) for p in sources]
    if not all(r["status"] == "scanned" and r["modelsContacted"] is False for r in reports):
        parser.error("Expected native copied-scan receipts")
    args.output.mkdir(parents=True, exist_ok=False)
    repo = Path(__file__).resolve().parent.parent
    rng = np.random.Generator(np.random.PCG64(20261116))
    directions = rng.standard_normal((32, 48))
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    permutation = rng.permutation(48)
    source_paths = [Path(__file__), repo / "probes/map_sustained_response.py",
                    repo / "research/studies/2026-11-15-sonar-resolution.md"]
    source_paths += [repo / "desktop/ReservoirScope/crates/reservoir-core/src" / name
                     for name in ("math.rs", "sustained_sonar.rs", "sustained_actions.rs")]
    protocol = {"sourceCommit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
                "sourceHashes": {str(p.relative_to(repo)): sha(p) for p in source_paths},
                "inputHashes": before, "numpyVersion": np.__version__, "pythonVersion": platform.python_version(),
                "amplitudes": AMPLITUDES, "horizons": HORIZONS, "temporalOffsets": OFFSETS,
                "heldOutSeed": 20261116, "heldOutDirections": directions.tolist(),
                "inputColumnPermutation": permutation.tolist(), "modelsContacted": False,
                "scope": "Six native endpoints plus frozen numerical continuations. Recurrent response only; no global topology or model ranking."}
    (args.output / "protocol.json").write_text(json.dumps(protocol, indent=2, allow_nan=False) + "\n")
    results = [endpoint(label, report["scan"], directions, permutation, args.output)
               for label, report in zip(LABELS, reports)]
    unchanged = before == {str(p): sha(p) for p in sources}
    if not unchanged:
        raise ValueError("Source report changed during analysis")
    result = {**protocol, "sourceUnchanged": unchanged, "endpoints": results}
    (args.output / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    (args.output / "artifact-hashes.json").write_text(json.dumps({p.name: sha(p) for p in sorted(args.output.iterdir())
                                                               if p.is_file()}, indent=2) + "\n")


if __name__ == "__main__":
    main()
