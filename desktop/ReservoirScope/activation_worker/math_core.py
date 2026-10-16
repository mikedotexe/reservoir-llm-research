"""Frozen projection and calibration math; no inference/runtime imports."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from . import HIDDEN_DIM, STATE_DIM

FIXTURES = Path(__file__).parent / "fixtures"
PROJECTION_SEED = 20261015
SCALE_FLOOR = 1e-6


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode("utf-8")).hexdigest()


def array_hash(value) -> str:
    return hashlib.sha256(np.asarray(value, dtype="<f4").tobytes(order="C")).hexdigest()


def finite_array(value, shape: tuple[int, ...], name: str) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError(f"{name} must be finite with shape {shape}")
    return result


def load_projection() -> np.ndarray:
    # This committed artifact, not a per-run QR, defines the actual basis.
    q = np.load(FIXTURES / "projection-q.npy", allow_pickle=False)
    q = finite_array(q, (HIDDEN_DIM, STATE_DIM), "projection")
    if not np.allclose(np.einsum("di,dj->ij", q, q, optimize=False), np.eye(STATE_DIM), atol=1e-6, rtol=0):
        raise ValueError("committed projection is not orthonormal")
    return q


def calibration_texts() -> list[str]:
    texts = json.loads((FIXTURES / "calibration-texts.json").read_text())
    if len(texts) != 32 or any(not isinstance(x, str) or not x for x in texts):
        raise ValueError("exactly 32 nonempty calibration observations are required")
    return texts


def make_calibration(activations, manifest_sha256: str) -> dict:
    q = load_projection()
    h = finite_array(activations, (32, HIDDEN_DIM), "calibration activations")
    projected = np.einsum("nd,dr->nr", h, q, optimize=False)
    body = {
        "schemaVersion": "activation-calibration/1",
        "projection": q.tolist(),
        "mean": projected.mean(axis=0).tolist(),
        "scales": np.maximum(projected.std(axis=0, ddof=0), SCALE_FLOOR).tolist(),
        "projectionSha256": sha256_file(FIXTURES / "projection-q.npy"),
        "textsSha256": sha256_file(FIXTURES / "calibration-texts.json"),
        "modelManifestSha256": manifest_sha256,
        "observationsSha256": array_hash(h),
        "projectionSeed": PROJECTION_SEED,
        "scaleFloor": SCALE_FLOOR,
    }
    body["sha256"] = canonical_hash(body)
    return body


def validate_calibration(value: dict, manifest_sha256: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError("existingCalibration must be an object")
    body = {k: v for k, v in value.items() if k != "sha256"}
    if value.get("sha256") != canonical_hash(body):
        raise ValueError("calibration digest mismatch")
    if value.get("schemaVersion") != "activation-calibration/1":
        raise ValueError("unsupported calibration schema")
    if value.get("modelManifestSha256") != manifest_sha256:
        raise ValueError("calibration belongs to a different model/runtime manifest")
    for key, path in (("projectionSha256", "projection-q.npy"),
                      ("textsSha256", "calibration-texts.json")):
        if value.get(key) != sha256_file(FIXTURES / path):
            raise ValueError(f"calibration {key} differs from the committed fixture")
    q = finite_array(value.get("projection"), (HIDDEN_DIM, STATE_DIM), "projection")
    if not np.array_equal(q, load_projection()):
        raise ValueError("calibration projection differs from the committed basis")
    finite_array(value.get("mean"), (STATE_DIM,), "mean")
    scales = finite_array(value.get("scales"), (STATE_DIM,), "scales")
    if np.any(scales < SCALE_FLOOR):
        raise ValueError("calibration scale is below the floor")
    return value


def project(activation, calibration: dict) -> np.ndarray:
    h = finite_array(activation, (HIDDEN_DIM,), "activation")
    q = np.asarray(calibration["projection"], dtype=np.float64)
    raw = np.einsum("d,dr->r", h, q, optimize=False)
    return np.tanh((raw - np.asarray(calibration["mean"])) /
                   np.asarray(calibration["scales"]))


def steering_direction(state, q=None) -> np.ndarray:
    r = finite_array(state, (STATE_DIM,), "steeringState")
    if np.any(np.abs(r) > 1.000001):
        raise ValueError("steeringState must be bounded to [-1, 1]")
    v = np.einsum("dr,r->d", load_projection() if q is None else q, r, optimize=False)
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else np.zeros(HIDDEN_DIM, dtype=np.float64)


def steer_numpy(residual: np.ndarray, direction: np.ndarray, gain: float) -> np.ndarray:
    """Reference math and exact zero path for independent backend conformance."""
    if gain == 0 or not np.any(direction):
        return residual
    norms = np.linalg.norm(residual.astype(np.float64), axis=-1, keepdims=True)
    return residual + (gain * norms * direction).astype(residual.dtype)
