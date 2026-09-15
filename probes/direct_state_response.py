#!/usr/bin/env python3
"""Bounded, research-local state-impulse replay of retained esn-divide evidence.

Requires Python 3.12+ and numpy for matrix algebra. Reads eight immutable binary
arrays; writes only under the chosen research output directory. Never imports,
launches, or contacts a being or mutates a sibling. This is a conditional replay
of a simulated parent, not native ESN/controller parity or a live intervention.
Protocol is saved before outcomes in research/outputs/2026-09-07-direct-shaping.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_inputs(bundle: Path, protocol: dict, output: Path) -> tuple[dict, dict]:
    manifest_bytes = (bundle / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    retained = output / "inputs"
    retained.mkdir(parents=True, exist_ok=True)
    (retained / "source-manifest.json").write_bytes(manifest_bytes)
    arrays, records = {}, {}
    for index, name in enumerate(protocol["arrays"]):
        blob = manifest["blobs"][name]
        metadata = manifest["array_metadata"][name]
        source = (bundle / blob["path"]).resolve()
        if not source.is_relative_to(bundle.resolve()):
            raise ValueError("blob path leaves bundle")
        data = source.read_bytes()
        if digest(data) != blob["sha256"] or len(data) != blob["byte_length"]:
            raise ValueError(f"input integrity failure: {name}")
        value = np.frombuffer(data, dtype=metadata["dtype"]).reshape(metadata["shape"])
        if not np.all(np.isfinite(value)):
            raise ValueError(f"nonfinite input: {name}")
        filename = f"{index:02d}-{name.replace('/', '_')}.bin"
        (retained / filename).write_bytes(data)
        arrays[name] = value.astype(np.float64)
        records[name] = {"source": str(source), "retained": f"inputs/{filename}",
                         "sha256": digest(data), "bytes": len(data), **metadata}
    return arrays, {"manifest_sha256": digest(manifest_bytes), "arrays": records,
                    "capture": manifest["capture"], "source": manifest["source"]}


def step(x, u, leak, wres, win, bridge, residual):
    activation = np.tanh(win @ np.append(u, 1.0) + wres @ x + bridge)
    preclip = (1 - leak) * x + leak * activation
    y = np.clip(preclip, -1, 1)
    before_final_clip = y + residual
    result = np.clip(before_final_clip, -1, 1)
    derivative = ((1 - leak) * np.eye(x.size)
                  + leak * (1 - activation ** 2)[:, None] * wres)
    mask = (np.abs(preclip) < 1) & (np.abs(before_final_clip) < 1)
    return result, derivative * mask[:, None], bool(np.any(~mask))


def run(protocol_path: Path, bundle: Path, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    protocol_bytes = protocol_path.read_bytes()
    protocol = json.loads(protocol_bytes)
    arrays, provenance = load_inputs(bundle, protocol, output)
    wres, win = arrays["model/parent/wres"], arrays["model/parent/win"]
    states = arrays["raw/parent/state_boundaries"]
    inputs, leaks = arrays["raw/parent/inputs"], arrays["raw/parent/leak_used"]
    bridges = arrays["raw/parent/bridge_drives"]
    residuals = arrays["raw/parent/transition_residual_after_noiseless_clip"]
    original_steps = arrays["raw/parent/transition_steps"]
    horizon = protocol["horizon_steps"]
    if wres.shape != (128, 128) or win.shape != (128, 67) or inputs.shape != (600, 66):
        raise ValueError("protocol's declared parent workload no longer matches")

    def rollout(start, displacement):
        unclipped = states[start] + displacement
        x = np.clip(unclipped, -1, 1)
        actual = x - states[start]
        path, jacobians = [x.copy()], []
        clipped = bool(np.any(x != unclipped))
        for offset in range(horizon):
            index = start + offset
            x, jacobian, was_clipped = step(x, inputs[index], leaks[index], wres,
                                           win, bridges[index], residuals[index])
            path.append(x.copy())
            jacobians.append(jacobian)
            clipped = clipped or was_clipped
        return np.asarray(path), jacobians, actual, clipped

    zero = np.zeros(states.shape[1])
    rng = np.random.Generator(np.random.PCG64(20260907))
    random_direction = rng.standard_normal(states.shape[1])
    random_direction /= np.linalg.norm(random_direction)
    coordinate = zero.copy()
    coordinate[0] = 1
    traces, controls, outcomes, derivative_checks, baseline_checks = {}, {}, [], [], []
    directions_record = {}
    for start in protocol["start_indices"]:
        control, jacobians, _, control_clipped = rollout(start, zero)
        repeated, _, _, _ = rollout(start, zero)
        max_error = float(np.max(np.abs(control - states[start:start + horizon + 1])))
        parity = bool(np.array_equal(control, repeated))
        baseline_checks.append({"start_index": start, "original_transition_step": int(original_steps[start]),
                                "noop_bit_identical": parity, "max_abs_reference_error": max_error,
                                "retained_reference_gate_pass": max_error <= 0.0002})
        controls[f"start_{start}"] = control
        product = np.eye(states.shape[1])
        for jacobian in jacobians[:16]:
            product = jacobian @ product
        _, _, right = np.linalg.svd(product, full_matrices=False)
        leading = right[0]
        if leading[np.argmax(np.abs(leading))] < 0:
            leading = -leading
        directions = dict(zip(protocol["directions"], [coordinate, random_direction, leading]))
        for name, direction in directions.items():
            direction_id = f"start_{start}:{name}"
            directions_record[direction_id] = direction.tolist()
            paths, clipped_by_dose = {}, {}
            for epsilon in protocol["signed_requested_l2_amplitudes"]:
                path, _, actual, clipped = rollout(start, epsilon * direction)
                delta = path - control
                separation = np.linalg.norm(delta, axis=1)
                actual_norm = float(np.linalg.norm(actual))
                threshold = protocol["return_threshold_fraction"] * actual_norm
                dwell = protocol["return_dwell_boundaries"]
                returned = next((i for i in range(1, len(separation) - dwell + 1)
                                 if np.all(separation[i:i + dwell] <= threshold)), None)
                run_id = f"s{start}:{name}:dose{epsilon:+.4g}"
                traces[run_id] = path
                paths[epsilon], clipped_by_dose[epsilon] = path, clipped
                outcomes.append({"run_id": run_id, "start_index": start, "direction_id": direction_id,
                                 "requested_signed_l2": epsilon, "actual_initial_l2": actual_norm,
                                 "initial_clipping_l2_loss": float(np.linalg.norm(epsilon * direction - actual)),
                                 "any_transition_or_initial_clipping": clipped,
                                 "separation_l2": separation.tolist(),
                                 "peak_gain_over_initial": float(np.max(separation) / actual_norm),
                                 "final_separation_l2": float(separation[-1]),
                                 "return_boundary": returned,
                                 "return_status": "observed" if returned is not None else "not_returned_within_64_steps"})
            epsilon = 0.0001
            finite_difference = (paths[epsilon][16] - paths[-epsilon][16]) / (2 * epsilon)
            predicted = product @ direction
            relative_error = float(np.linalg.norm(finite_difference - predicted)
                                   / max(float(np.linalg.norm(predicted)), 1e-12))
            differentiable = not (control_clipped or clipped_by_dose[epsilon] or clipped_by_dose[-epsilon])
            derivative_checks.append({"direction_id": direction_id, "relative_h16_error": relative_error,
                                      "unclipped_window": differentiable,
                                      "pass": relative_error < 0.01 if differentiable else None})

    eligible_derivatives = [r for r in derivative_checks if r["pass"] is not None]
    summary = {"runs": len(outcomes), "starts": len(controls), "derivative_comparisons": len(derivative_checks),
               "noop_checks_pass": all(r["noop_bit_identical"] for r in baseline_checks),
               "reference_checks_pass": all(r["retained_reference_gate_pass"] for r in baseline_checks),
               "eligible_derivative_comparisons": len(eligible_derivatives),
               "tested_derivative_checks_pass": (all(r["pass"] for r in eligible_derivatives)
                                                   if eligible_derivatives else None),
               "clipping_excluded_checks": sum(r["pass"] is None for r in derivative_checks),
               "returned_within_window": sum(r["return_boundary"] is not None for r in outcomes),
               "peak_gain_min": min(r["peak_gain_over_initial"] for r in outcomes),
               "peak_gain_max": max(r["peak_gain_over_initial"] for r in outcomes),
               "clipped_runs": sum(r["any_transition_or_initial_clipping"] for r in outcomes)}
    np.savez_compressed(output / "trajectories.npz", **{f"control:{k}": v for k, v in controls.items()}, **traces)
    result = {"schema": "research.direct_state_response.result.v1", "subject": protocol["subject"],
              "scope": protocol["source_authority"], "protocol_sha256": digest(protocol_bytes),
              "probe_sha256": digest(Path(__file__).read_bytes()),
              "runtime": {"python": platform.python_version(), "numpy": np.__version__},
              "inputs": provenance, "summary": summary, "baseline_checks": baseline_checks,
              "derivative_checks": derivative_checks, "directions": directions_record,
              "runs": outcomes, "trajectory_sha256": digest((output / "trajectories.npz").read_bytes())}
    (output / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=Path("../esn-divide/artifacts/bounded-production-benchmark.analysis"))
    parser.add_argument("--output", type=Path, default=Path("research/outputs/2026-09-07-direct-shaping"))
    parser.add_argument("--protocol", type=Path, default=Path("research/outputs/2026-09-07-direct-shaping/protocol.json"))
    args = parser.parse_args()
    run(args.protocol, args.bundle, args.output)
