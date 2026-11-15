#!/usr/bin/env python3
"""Offline geometry and paired perturbations of completed laptop session exports.

Reads immutable session files, uses NumPy, and writes only to --output. No model,
network or live-state access. Protocol: research/studies/2026-11-15-reservoir-response-mapping.md.
Numerical reconstruction must match every retained transition within 1e-12 before
counterfactual results are produced. Future recorded inputs/actions remain fixed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform

import numpy as np

from desktop_state_rank import frames

MASK = (1 << 64) - 1


class SplitMix64:
    def __init__(self, seed):
        self.state = seed

    def unit(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return ((z ^ (z >> 31)) >> 11) / 9007199254740992.0

    def signed(self):
        return 2 * self.unit() - 1


def model(seed):
    rng = SplitMix64(seed)
    win = np.empty((32, 67))
    for row in range(32):
        for col in range(67):
            boost = (1.6 if col >= 18 else 1.2 if col >= 16 else 1) if col < 66 else 1
            win[row, col] = rng.signed() * 0.5 * boost
    recurrent = np.zeros((32, 32))
    for row in range(32):
        for col in range(32):
            if rng.unit() < 0.1:
                recurrent[row, col] = rng.signed()
    maximum = max(sum(abs(float(x)) for x in row) for row in recurrent)
    recurrent = recurrent * 0.9 / maximum
    return recurrent, win


def advance(x, frame, controls, recurrent, win, impulse=None):
    u = np.array(frame["input"])
    if impulse is not None:
        u[18:] += impulse
    a, gain = controls["leak"], controls["recurrentGain"]
    activation = np.tanh(win[:, :66] @ u + win[:, 66] + (recurrent * gain) @ x)
    before = (1 - a) * x + a * activation + frame["noise"]
    y = np.clip(before, -1, 1)
    mask = np.abs(before) < 1
    request = (frame.get("actionReceipt") or {}).get("request") or {}
    if request.get("kind") == "pulse":
        direction = np.zeros(32)
        name = request["direction"]
        if name == "uniform":
            direction[:] = 1 / np.sqrt(32)
        elif name == "alternating":
            direction[:] = np.where(np.arange(32) % 2 == 0, 1, -1) / np.sqrt(32)
        else:
            assert name in ("axis0", "axis1")
            direction[int(name[-1])] = 1
        y += request["strength"] * direction
        mask &= np.abs(y) < 1
        y = np.clip(y, -1, 1)
    slope = a * (1 - activation ** 2)
    jx = ((1 - a) * np.eye(32) + slope[:, None] * (recurrent * gain)) * mask[:, None]
    ju = slope[:, None] * win[:, 18:66] * mask[:, None]
    return y, jx, ju, bool(np.any(~mask)), activation


def summarize(path, output):
    raw = (path / "manifest.json").read_bytes()
    manifest = json.loads(raw)
    assert manifest["phase"] == "scheduleComplete"
    checkpoint = json.loads((path / "checkpoints" / (manifest["checkpointSha256"] + ".json")).read_text())
    assert all(o["status"] == "applied" for o in checkpoint["state"]["checkInState"]["outcomes"])
    data = frames(path)
    assert [f["step"] for f in data] == list(range(1, manifest["step"] + 1))
    recurrent, win = model(int(manifest["config"]["seed"]))
    controls = dict(leak=manifest["config"]["leak"], recurrentGain=1.0, feedbackScale=manifest["config"]["feedbackScale"])
    controls_by_step, jacobians, input_maps, activations, replay_errors = [], [], [], [], []
    x = np.zeros(32)
    clipped_steps = 0
    for frame in data:
        if frame.get("actionReceipt"):
            controls = frame["actionReceipt"]["controlsAfter"]
        controls_by_step.append(controls.copy())
        y, jx, ju, clipped, act = advance(x, frame, controls, recurrent, win)
        replay_errors.append(float(np.max(np.abs(y - frame["state"]))))
        jacobians.append(jx)
        input_maps.append(ju)
        activations.append(act)
        clipped_steps += clipped
        x = np.array(frame["state"])
    assert max(replay_errors) <= 1e-12, (path, max(replay_errors))
    states = np.vstack([np.zeros(32), [f["state"] for f in data]])
    anchors = [int(len(data) * fraction) for fraction in (0.10, 0.25, 0.40, 0.55, 0.70, 0.85)]
    assert len(set(anchors)) == 6 and anchors[-1] + 64 <= len(data)
    random = np.random.Generator(np.random.PCG64(20261115)).standard_normal(32)
    random /= np.linalg.norm(random)
    coordinate = np.eye(32)[0]
    trials, input_trials, branches, checks = [], [], {}, []

    def rollout(anchor, displacement, impulse=None):
        initial = np.clip(states[anchor] + displacement, -1, 1)
        actual = initial - states[anchor]
        current = initial.copy()
        trajectory = [current.copy()]
        clipped = bool(np.any(initial != states[anchor] + displacement))
        for offset in range(64):
            index = anchor + offset
            current, _, _, clip, _ = advance(current, data[index], controls_by_step[index], recurrent, win,
                                             impulse if offset == 0 else None)
            trajectory.append(current.copy())
            clipped = clipped or clip
        return np.array(trajectory), actual, clipped

    for anchor in anchors:
        control, _, control_clipped = rollout(anchor, np.zeros(32))
        error = float(np.max(np.abs(control - states[anchor:anchor + 65])))
        assert error <= 1e-12
        product = np.eye(32)
        for jx in jacobians[anchor:anchor + 16]:
            product = jx @ product
        leading = np.linalg.svd(product, full_matrices=False)[2][0]
        leading *= 1 if leading[np.argmax(np.abs(leading))] >= 0 else -1
        for name, direction in (("coordinate0", coordinate), ("random", random), ("largest16Step", leading)):
            paths, clips = {}, {}
            for dose in (-0.1, -0.0001, 0.0001, 0.1):
                branch, actual, clipped = rollout(anchor, dose * direction)
                separation = np.linalg.norm(branch - control, axis=1)
                initial_norm = float(np.linalg.norm(actual))
                assert initial_norm > 0
                returned = next((i for i in range(1, 61) if np.all(separation[i:i + 5] <= 0.1 * initial_norm)), None)
                key = f"step{anchor}:{name}:{dose:+g}"
                branches[key] = branch
                trials.append({"id": key, "anchorStep": anchor, "direction": name, "dose": dose,
                               "actualInitialL2": initial_norm, "clipped": clipped,
                               "separationL2": separation.tolist(), "peakRelativeL2": float(separation.max() / initial_norm),
                               "returnBelow10PercentFiveSteps": returned})
                paths[dose], clips[dose] = branch, clipped
            estimated = (paths[0.0001][16] - paths[-0.0001][16]) / 0.0002
            # At an initial boundary of [-1,1], the imposed signed perturbations
            # may be clipped asymmetrically. Compare the analytic evolution with
            # the actual central displacement, not the unattainable request.
            central_direction = (paths[0.0001][0] - paths[-0.0001][0]) / 0.0002
            expected = product @ central_direction
            relative = float(np.linalg.norm(estimated - expected) / max(np.linalg.norm(expected), 1e-12))
            short_estimated = (paths[0.0001][1] - paths[-0.0001][1]) / 0.0002
            short_expected = jacobians[anchor] @ central_direction
            checks.append({"anchorStep": anchor, "direction": name, "baselineMaxAbsError": error,
                           "unclipped": not (control_clipped or clips[0.0001] or clips[-0.0001]),
                           "derivativeRelativeError": relative,
                           "derivativeExpectedL2": float(np.linalg.norm(expected)),
                           "derivativeAbsoluteError": float(np.linalg.norm(estimated - expected)),
                           "oneStepDerivativeAbsoluteError": float(np.linalg.norm(short_estimated - short_expected)),
                           "oneStepDerivativeRelativeError": float(np.linalg.norm(short_estimated - short_expected) / max(np.linalg.norm(short_expected), 1e-12))})
        matrices = {h: [] for h in (1, 2, 4, 8, 16, 30)}
        impulse_clip = False
        for coordinate_index in range(48):
            impulse = np.eye(48)[coordinate_index] * 0.01
            plus, _, cp = rollout(anchor, np.zeros(32), impulse)
            minus, _, cm = rollout(anchor, np.zeros(32), -impulse)
            impulse_clip = impulse_clip or cp or cm
            for horizon in matrices:
                matrices[horizon].append((plus[horizon] - minus[horizon]) / 0.02)
        predicted = input_maps[anchor]
        for horizon in range(1, 31):
            if horizon > 1:
                predicted = jacobians[anchor + horizon - 1] @ predicted
            if horizon not in matrices:
                continue
            response = np.array(matrices[horizon]).T
            rel = float(np.linalg.norm(response - predicted) / max(np.linalg.norm(predicted), 1e-12))
            key = f"input:step{anchor}:h{horizon}"
            branches[key] = response
            input_trials.append({"anchorStep": anchor, "horizon": horizon, "clippedWithin64Steps": impulse_clip,
                                 "matrixKey": key, "derivativeRelativeError": rel,
                                 "all48SingularValues": np.linalg.svd(response, compute_uv=False).tolist(),
                                 "semantic32SingularValues": np.linalg.svd(response[:, :32], compute_uv=False).tolist()})
    suffix = manifest["sessionId"]
    np.savez_compressed(output / (suffix + "-arrays.npz"), states=states, inputs=np.array([f["input"] for f in data]),
                        activations=np.array(activations), jacobians=np.array(jacobians), inputMaps=np.array(input_maps), **branches)
    norm_w = float(np.max(np.abs(recurrent).sum(axis=1)))
    bounds = np.array([1 - c["leak"] + c["leak"] * abs(c["recurrentGain"]) * norm_w for c in controls_by_step])
    local = np.linalg.svd(np.array(jacobians), compute_uv=False)[:, 0]
    act = np.array(activations)
    centered = states[1:] - states[1:].mean(axis=0)
    variance = np.linalg.svd(centered, compute_uv=False) ** 2
    available = [r["returnBelow10PercentFiveSteps"] for r in trials if r["returnBelow10PercentFiveSteps"] is not None]
    result = {"snapshot": str(path), "manifestSha256": hashlib.sha256(raw).hexdigest(),
              "sessionId": suffix, "model": manifest["config"]["language"]["model"],
              "frames": len(data), "anchors": anchors, "replayMaximumAbsoluteError": max(replay_errors),
              "recurrentMaximumAbsRowSum": norm_w, "recurrentSpectralRadius": float(np.max(np.abs(np.linalg.eigvals(recurrent)))),
              "worstCaseInfinityBound": {"min": float(bounds.min()), "max": float(bounds.max()), "stepsBelowOne": int((bounds < 1).sum())},
              "observedJacobianLargestSingularValue": {"min": float(local.min()), "median": float(np.median(local)), "max": float(local.max())},
              "activationAbsAbove095Fraction": float(np.mean(np.abs(act) > 0.95)), "clippedTransitions": clipped_steps,
              "stateCovarianceParticipationRatio": float(variance.sum() ** 2 / np.sum(variance ** 2)),
              "stateVarianceFirstThreeShare": (variance[:3] / variance.sum()).tolist(),
              "statePerturbations": {"n": len(trials), "returned": len(available), "returnMin": min(available) if available else None,
                                     "returnMedian": float(np.median(available)) if available else None, "returnMax": max(available) if available else None},
              "stateTrials": trials, "inputTrials": input_trials, "derivativeChecks": checks,
              "hourlySteps": [o["appliedStep"] for o in checkpoint["state"]["checkInState"]["outcomes"]]}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sessions", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    repo = Path(__file__).resolve().parent.parent
    sources = [repo / "desktop/ReservoirScope/crates/reservoir-core/src" / name
               for name in ("math.rs", "sustained.rs", "sustained_actions.rs")]
    result = {"scope": "conditional numerical continuations, future recorded inputs/noise/actions fixed",
              "probeSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "sourceHashes": {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
              "runtime": {"python": platform.python_version(), "numpy": np.__version__}, "sessions": []}
    for path in args.sessions:
        item = summarize(path, args.output)
        result["sessions"].append(item)
        print(json.dumps({k: v for k, v in item.items() if k not in ("stateTrials", "inputTrials", "derivativeChecks")}), flush=True)
    (args.output / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
