#!/usr/bin/env python3
"""Research-local, inspectable native-state pattern plans; NEVER a live sender.

Requires NumPy for full-vector projection and rotation. All arithmetic is float64
geometry at a retained reference state, not native replay, native dtype parity,
controller prediction, or evidence that an action occurred. Output stays in this
repository. CLI supports a retained native-capture demo or a JSON plan request.

API: make_registry(identity, reference, patterns, source); make_plan(registry,
state_evidence, gesture, limits); cancel_sequence(offsets, completed, cancel_at).
Registry hashes identify exact vectors, their fixed signs and provenance. Dynamic
operations resolve once against the named retained sample into explicit deltas;
a finite gesture does not pretend to know future ordinary native states.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import platform

import numpy as np

REPO = Path(__file__).resolve().parents[1]
MAX_DIMENSION = 4096
MAX_STEPS = 64
MAX_STEP_OFFSET = 10000
MAX_JSON_BYTES = 8 * 1024 * 1024
IDENTITY_KEYS = ("target", "dimensions", "capture_column_order_id",
                 "node_layout_id", "model_sha256")
NATIVE_KEYS = ("node_layout_id", "model_sha256", "native_engine_id",
               "deployment_id", "session_id", "successful_step_id")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number")
    return result


def integer(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def vector(value, dimensions, name):
    try:
        result = np.asarray(value, dtype=np.float64)
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError(f"invalid {name}") from error
    if result.shape != (dimensions,) or not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must have {dimensions} finite coordinates")
    return result.copy()


def norm(value):
    result = math.hypot(*value)
    if not math.isfinite(result):
        raise ValueError("vector norm overflow")
    return result


def vector_hash(value):
    # Explicit little-endian float64 bytes; signed zero is retained in identity.
    return digest(np.asarray(value, dtype="<f8").tobytes())


def sealed(value, field):
    result = copy.deepcopy(value)
    result.pop(field, None)
    result[field] = digest(canonical(result))
    return result


def check_seal(value, field):
    if value.get(field) != sealed(value, field)[field]:
        raise ValueError(f"{field} integrity mismatch")


def check_identity(identity):
    if not isinstance(identity, dict):
        raise ValueError("identity must be an object")
    dimensions = integer(identity.get("dimensions"), "dimensions", 1, MAX_DIMENSION)
    for key in ("target", "capture_column_order_id"):
        if not isinstance(identity.get(key), str) or not identity[key].strip():
            raise ValueError(f"explicit {key} is required")
    for key in ("node_layout_id", "model_sha256"):
        if key not in identity:
            raise ValueError(f"identity must retain {key}, even when null/unknown")
    return dimensions


def make_registry(identity, reference, patterns, source):
    """Register already fixed unit vectors; no automatic sign flip or refitting."""
    n = check_identity(identity)
    mean = vector(reference, n, "reference")
    if not isinstance(patterns, dict) or not 1 <= len(patterns) <= MAX_DIMENSION:
        raise ValueError("registry needs a bounded nonempty pattern map")
    entries = {}
    for name, value in patterns.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("pattern names must be nonempty strings")
        direction = vector(value["vector"], n, name)
        if not math.isclose(norm(direction), 1.0, rel_tol=0, abs_tol=1e-10):
            raise ValueError("registry patterns must be nonzero unit-L2 vectors")
        if not value.get("provenance"):
            raise ValueError("each fixed pattern requires provenance")
        entries[name] = sealed({"version": 1, "vector": direction.tolist(),
                                "vector_sha256": vector_hash(direction),
                                "vector_encoding": "little-endian float64",
                                "provenance": value["provenance"]}, "pattern_sha256")
    return sealed({"schema": "research.substrate_pattern_registry.v1",
                   "identity": identity, "source": source,
                   "reference": mean.tolist(), "reference_sha256": vector_hash(mean),
                   "units": "reservoir activation units; directions unit L2",
                   "patterns": entries}, "registry_sha256")


def validate_registry(registry):
    if not isinstance(registry, dict) or registry.get("schema") != "research.substrate_pattern_registry.v1":
        raise ValueError("unsupported registry schema")
    check_seal(registry, "registry_sha256")
    if not isinstance(registry.get("patterns"), dict) or not 1 <= len(registry["patterns"]) <= MAX_DIMENSION:
        raise ValueError("registry needs a bounded nonempty pattern map")
    n = check_identity(registry["identity"])
    reference = vector(registry["reference"], n, "reference")
    if vector_hash(reference) != registry["reference_sha256"]:
        raise ValueError("reference integrity mismatch")
    for value in registry["patterns"].values():
        if not isinstance(value, dict) or value.get("version") != 1:
            raise ValueError("unsupported pattern entry")
        check_seal(value, "pattern_sha256")
        v = vector(value["vector"], n, "pattern")
        if vector_hash(v) != value["vector_sha256"] or not math.isclose(norm(v), 1, abs_tol=1e-10, rel_tol=0):
            raise ValueError("pattern vector integrity or unit-length failure")
    return n, reference


def selected(registry, names, orthonormal=False):
    if not isinstance(names, list) or not names or len(set(names)) != len(names):
        raise ValueError("select distinct named registry patterns")
    try:
        basis = np.asarray([registry["patterns"][name]["vector"] for name in names])
    except (KeyError, TypeError) as error:
        raise ValueError("unknown pattern") from error
    if orthonormal and not np.allclose(basis @ basis.T, np.eye(len(names)), rtol=0, atol=1e-10):
        raise ValueError("selected modes must be orthonormal; no implicit repair")
    return basis


def resolve(registry, state, reference, request):
    """Resolve full requested delta, preserving explicit signs and exact no-op."""
    kind = request.get("kind")
    n = state.size
    if kind == "coordinate":
        index = integer(request.get("index"), "coordinate index", 0, n - 1)
        direction = np.zeros(n)
        direction[index] = 1.0
        amount = finite(request.get("amount"), "signed amount")
        delta = amount * direction
        detail = {"signed_amount": amount, "direction": direction.tolist()}
    elif kind == "combine":
        terms = request.get("terms")
        if not isinstance(terms, dict) or not terms:
            raise ValueError("combination requires explicit named signed coefficients")
        basis = selected(registry, list(terms))
        coefficients = np.asarray([finite(v, "coefficient") for v in terms.values()])
        with np.errstate(over="ignore", invalid="ignore"):
            raw = coefficients @ basis
        if not np.all(np.isfinite(raw)):
            raise ValueError("combination overflow")
        length = norm(raw)
        if length == 0:
            raise ValueError("zero combination has no direction, even at zero amount")
        direction = raw / length
        amount = finite(request.get("amount"), "signed amount")
        delta = amount * direction
        detail = {"signed_amount": amount, "raw_combination_l2": length,
                  "direction": direction.tolist(), "fixed_signs": True}
    elif kind == "suppress":
        names = request.get("modes")
        basis = selected(registry, names, orthonormal=True)
        fraction = finite(request.get("fraction"), "suppression fraction")
        if not 0 <= fraction <= 1:
            raise ValueError("suppression fraction must be in [0, 1]")
        scores = basis @ (state - reference)
        delta = -fraction * (scores @ basis)
        detail = {"fraction": fraction, "scores_before": scores.tolist(),
                  "meaning": "subtract only the named reference-centered component"}
    elif kind == "rotate":
        names = request.get("modes")
        if not isinstance(names, list) or len(names) != 2:
            raise ValueError("rotation requires an ordered two-mode plane")
        basis = selected(registry, names, orthonormal=True)
        angle = finite(request.get("angle_radians"), "signed angle")
        if abs(angle) > 2 * math.pi:
            raise ValueError("rotation angle must lie in [-2pi, 2pi]")
        scores = basis @ (state - reference)
        c, s = math.cos(angle), math.sin(angle)
        rotated = np.array([c * scores[0] - s * scores[1], s * scores[0] + c * scores[1]])
        delta = (rotated - scores) @ basis
        detail = {"angle_radians": angle, "scores_before": scores.tolist(),
                  "scores_after_requested": rotated.tolist(),
                  "meaning": "rotate only the named reference-centered plane; complement unchanged"}
    else:
        raise ValueError("unknown operation kind")
    if not np.all(np.isfinite(delta)):
        raise ValueError("requested delta overflow")
    return delta, detail


def headroom_preview(state, delta, policy):
    """Use one scalar; per-coordinate clipping is never a requested operation."""
    if policy not in ("reject", "attenuate"):
        raise ValueError("headroom policy must be reject or explicitly attenuate")
    if np.any(np.abs(state) > 1):
        raise ValueError("reference state lies outside native [-1,1] bounds")
    if np.all(delta == 0):
        return {"status": "exact_noop", "attenuation_factor": 1.0,
                "maximum_feasible_factor": 1.0, "delta": np.zeros_like(delta).tolist(),
                "intended_scaled_delta": delta.tolist(), "preview_state": state.tolist(),
                "numerical_backstop_clipped": False}
    positive, negative = delta > 0, delta < 0
    ratios = np.concatenate(((1 - state[positive]) / delta[positive],
                             (-1 - state[negative]) / delta[negative]))
    beta = min(1.0, float(ratios.min())) if ratios.size else 1.0
    fits = beta >= 1
    if not fits and policy == "reject":
        return {"status": "rejected_headroom", "attenuation_factor": 0.0,
                "maximum_feasible_factor": beta, "delta": np.zeros_like(delta).tolist(),
                "preview_state": state.tolist(), "numerical_backstop_clipped": False}
    after = state + beta * delta
    # Retain float64 numerical rounding separately from scalar attenuation.
    bounded = np.clip(after, -1, 1)
    actual = bounded - state
    status = ("unapplied_zero_headroom" if beta == 0
              else "unapplied_rounding" if np.all(actual == 0)
              else "preview_unattenuated" if fits else "preview_attenuated")
    return {"status": status, "attenuation_factor": beta,
            "maximum_feasible_factor": beta, "delta": actual.tolist(),
            "intended_scaled_delta": (beta * delta).tolist(),
            "preview_state": bounded.tolist(),
            "numerical_backstop_clipped": bool(np.any(bounded != after))}


def cancel_sequence(offsets, completed=(), cancel_at=None):
    """Cancellation is processed before the named offset; no inverse is emitted.

    completed is caller-supplied rehearsal bookkeeping, never a native receipt.
    Completed entries remain completed even if cancellation is later requested.
    """
    if not isinstance(offsets, list) or not 1 <= len(offsets) <= MAX_STEPS:
        raise ValueError("gesture needs 1..64 finite step offsets")
    for offset in offsets:
        integer(offset, "successful-step offset", 0, MAX_STEP_OFFSET)
    if offsets != sorted(set(offsets)):
        raise ValueError("step offsets must be unique and strictly increasing")
    completed = list(completed)
    for offset in completed:
        integer(offset, "completed offset", 0, MAX_STEP_OFFSET)
    if len(set(completed)) != len(completed) or any(v not in offsets for v in completed):
        raise ValueError("completed offsets must be distinct scheduled offsets")
    if sorted(completed) != offsets[:len(completed)]:
        raise ValueError("completed offsets must form a prefix of the scheduled sequence")
    if cancel_at is not None:
        integer(cancel_at, "cancellation offset", 0, MAX_STEP_OFFSET + 1)
        if any(v >= cancel_at for v in completed):
            raise ValueError("completed offset conflicts with before-boundary cancellation")
        if any(v < cancel_at and v not in completed for v in offsets):
            raise ValueError("past offsets need explicit completion evidence in cancellation rehearsal")
    return [{"success_step_offset": offset,
             "status": "hypothetically_completed" if offset in completed else
             "cancelled_pending" if cancel_at is not None and offset >= cancel_at else "pending"}
            for offset in offsets]


def make_plan(registry, state_evidence, gesture, limits):
    n, reference = validate_registry(registry)
    check_identity(state_evidence["identity"])
    if any(state_evidence["identity"].get(k) != registry["identity"].get(k) for k in IDENTITY_KEYS):
        raise ValueError("target/layout/model/capture coordinate compatibility mismatch")
    state = vector(state_evidence["vector"], n, "reference state")
    if state_evidence.get("vector_sha256") != vector_hash(state):
        raise ValueError("reference state hash mismatch")
    if np.any(np.abs(state) > 1):
        raise ValueError("reference state lies outside native [-1,1] bounds")
    limits = copy.deepcopy(limits)
    for key in ("max_step_l2", "max_coordinate_delta", "max_total_requested_l2"):
        limits[key] = finite(limits.get(key), key)
        if limits[key] <= 0:
            raise ValueError("explicit positive geometric limits are required")
    steps = gesture.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("gesture requires a finite steps list")
    statuses = cancel_sequence([s["success_step_offset"] for s in steps],
                               gesture.get("completed_offsets", ()), gesture.get("cancel_at_offset"))
    items, total = [], 0.0
    for step, status in zip(steps, statuses):
        delta, detail = resolve(registry, state, reference, step["operation"])
        length = norm(delta)
        total += length
        if length > limits["max_step_l2"] or float(np.max(np.abs(delta))) > limits["max_coordinate_delta"]:
            raise ValueError("requested delta exceeds geometric envelope; no silent dose attenuation")
        headroom = headroom_preview(state, delta, step.get("headroom_policy", "reject"))
        planned_delta = np.asarray(headroom["delta"])
        items.append({**status, "request": copy.deepcopy(step), "resolution": detail,
                      "requested_delta": delta.tolist(), "requested_delta_sha256": vector_hash(delta),
                      "requested_l2": length, "headroom_preview": headroom,
                      "preview_realized_l2": norm(planned_delta),
                      "preview_realized_delta_sha256": vector_hash(planned_delta),
                      "would_dispatch_in_sequence": status["status"] == "pending" and
                          headroom["status"] in ("preview_unattenuated", "preview_attenuated")})
    if total > limits["max_total_requested_l2"]:
        raise ValueError("gesture exceeds cumulative requested L2 budget, including cancelled steps")
    identity = state_evidence["identity"]
    missing = [key for key in NATIVE_KEYS if identity.get(key) in (None, "", "unknown")]
    return sealed({"schema": "research.substrate_pattern_plan.v1",
                   "scope": "reference-state geometry only; no transition simulation or native action",
                   "registry_sha256": registry["registry_sha256"], "identity": identity,
                   "source": state_evidence, "limits": limits,
                   "limits_authority": "research preview parameters; not a validated live envelope",
                   "gesture": copy.deepcopy(gesture), "steps": items,
                   "total_requested_l2": total,
                   "native_identity_complete": not missing,
                   "unresolved_native_identity": missing,
                   "apply_eligible": False,
                   "apply_blockers": [f"unknown:{k}" for k in missing] +
                       ["research_planner_has_no_native_adapter_or_authority",
                        "fresh_ordinary_state_headroom_regulator_expiry_and_successful_boundary_checks_required"],
                   "sequence_semantics": {
                       "clock": "relative successful native-step offsets; no wall time inferred",
                       "preview_baseline": "each step independently uses the same named retained reference state",
                       "resolution": "deltas are frozen to this retained sample; no prediction of future ordinary states",
                       "cancellation": "cancel only pending offsets; completed effects and subsequent trajectory remain",
                       "undo": "none; opposite signs at later steps are new interventions",
                       "failed_step": "no successful-step advance; no application claimed",
                       "restart_ambiguity": "application_unknown; no automatic retry",
                       "expiry": "native wall-clock expiry required before admission; none supplied by this preview"}},
                  "plan_sha256")


def local_path(path):
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(REPO):
        raise ValueError("file path must remain inside this research repository")
    return resolved


def read_json(path):
    path = local_path(path)
    with path.open("rb") as stream:
        raw = stream.read(MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("oversized JSON input")
    return json.loads(raw), raw


def demo(output):
    """Reuse fixed existing PCA and raw capture; never fit or contact a source."""
    geometry_path = REPO / "visualizations/reservoir-3d/state-geometry.json"
    geometry, geometry_raw = read_json(geometry_path)
    source, pca = geometry["source"], geometry["pca"]
    retained = {}
    for key in ("states", "metadata"):
        record = source["files"][key]
        path = local_path(record["snapshot_path"])
        limit = 2 * 1024 * 1024 if key == "states" else 16384
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
        if len(raw) > limit or digest(raw) != record["sha256"]:
            raise ValueError(f"retained {key} integrity/size mismatch")
        retained[key] = raw
    metadata = json.loads(retained["metadata"])
    if metadata != source["meta"] or metadata["dtype"] != "<f4" or metadata["layout"] != "row_major":
        raise ValueError("retained metadata incompatible")
    n, rows = metadata["esn_window_cols"], metadata["esn_window_rows"]
    if len(retained["states"]) != rows * n * 4 or n != metadata["esn_n"]:
        raise ValueError("retained state shape mismatch")
    states = np.frombuffer(retained["states"], dtype="<f4").reshape(rows, n).astype(np.float64)
    if not np.all(np.isfinite(states)) or not pca["frozen"] or pca["dimensions"] != n or pca["rows"] != rows:
        raise ValueError("invalid state or fixed PCA compatibility")
    components = np.asarray(pca["components"])
    mean = vector(pca["mean"], n, "fixed PCA mean")
    if components.shape != (3, n) or not np.allclose(components @ components.T, np.eye(3), rtol=0, atol=1e-10):
        raise ValueError("retained PCA is not an orthonormal three-mode basis")
    if not np.allclose(states.mean(axis=0), mean, rtol=0, atol=1e-12):
        raise ValueError("retained PCA reference does not match raw capture")
    capture_id = source["files"]["states"]["sha256"]
    identity = {"target": "minime.native_esn", "dimensions": n,
                "capture_column_order_id": f"sha256:{capture_id}:zero-based-binary-columns",
                "node_layout_id": None, "model_sha256": None, "native_engine_id": None,
                "deployment_id": None, "session_id": None, "successful_step_id": None}
    provenance = {"geometry_path": str(geometry_path.relative_to(REPO)),
                  "geometry_sha256": digest(geometry_raw), "source_state_sha256": capture_id,
                  "source_metadata_sha256": digest(retained["metadata"]),
                  "capture_time_utc": source["captured_at_utc"],
                  "compatibility": "same retained binary column order only; native layout/model identity unknown",
                  "pca_fit_scope": pca["fit_scope"], "pca_refitted": False,
                  "producer_transactional_pair_guarantee": False}
    patterns = {f"pc{i + 1}": {"vector": v.tolist(), "provenance": {
        **provenance, "component_index": i, "sign_rule": pca["component_sign_rule"]}}
        for i, v in enumerate(components)}
    coordinate = np.zeros(n)
    coordinate[0] = 1
    patterns["coordinate_0"] = {"vector": coordinate.tolist(), "provenance": {
        **provenance, "definition": "exact zero-based retained binary column 0"}}
    registry = make_registry(identity, mean, patterns, provenance)
    # First row selected by index, not by numerical response or headroom.
    state = states[0]
    evidence = {"identity": identity, "vector": state.tolist(), "vector_sha256": vector_hash(state),
                "retained_row_index": 0, "row_time": None, "source": provenance}
    gesture = {"id": "retained-native-pattern-demo", "steps": [
        {"success_step_offset": 0, "operation": {"kind": "coordinate", "index": 0, "amount": -0.001}},
        {"success_step_offset": 2, "operation": {"kind": "combine", "terms": {"pc1": 1, "pc2": -0.5}, "amount": 0.001}},
        {"success_step_offset": 4, "operation": {"kind": "suppress", "modes": ["pc1"], "fraction": 0.01}},
        {"success_step_offset": 6, "operation": {"kind": "rotate", "modes": ["pc1", "pc2"], "angle_radians": 0.01}, "headroom_policy": "attenuate"}]}
    limits = {"max_step_l2": 0.1, "max_coordinate_delta": 0.1, "max_total_requested_l2": 0.4}
    plan = make_plan(registry, evidence, gesture, limits)
    cancelled = copy.deepcopy(gesture)
    cancelled.update({"completed_offsets": [0, 2], "cancel_at_offset": 4})
    cancellation = make_plan(registry, evidence, cancelled, limits)
    output = local_path(output)
    output.mkdir(parents=True, exist_ok=True)
    artifacts = {"pattern-demo-registry.json": registry, "pattern-demo-request.json": {
        "registry": registry, "state_evidence": evidence, "gesture": gesture, "limits": limits},
        "pattern-demo-plan.json": plan, "pattern-demo-cancelled.json": cancellation}
    for name, value in artifacts.items():
        (output / name).write_bytes(json.dumps(value, indent=2, allow_nan=False).encode() + b"\n")
    summary = {"subject": "retained native state geometry; no rollout", "reference_row_index": 0,
               "probe_sha256": digest(Path(__file__).read_bytes()),
               "runtime": {"python": platform.python_version(), "numpy": np.__version__, "arithmetic": "float64"},
               "dimensions": n, "fixed_patterns": len(patterns), "planned_steps": len(plan["steps"]),
               "apply_eligible": plan["apply_eligible"], "unknown_native_identity": plan["unresolved_native_identity"],
               "previews": [{"offset": s["success_step_offset"], "kind": s["request"]["operation"]["kind"],
                             "requested_l2": s["requested_l2"], "status": s["headroom_preview"]["status"],
                             "beta": s["headroom_preview"]["attenuation_factor"]} for s in plan["steps"]],
               "cancellation_statuses": [s["status"] for s in cancellation["steps"]],
               "files": {name: digest((output / name).read_bytes()) for name in artifacts}}
    (output / "pattern-demo-summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, help="JSON with registry, state_evidence, gesture, limits")
    parser.add_argument("--output", type=Path, default=REPO / "research/outputs/2026-09-07-substrate-agency")
    args = parser.parse_args()
    if args.request:
        request, _ = read_json(args.request)
        result = make_plan(**request)
        destination = local_path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"output": str(destination), "plan_sha256": result["plan_sha256"], "apply_eligible": False}))
    else:
        print(json.dumps(demo(args.output), indent=2, allow_nan=False))
