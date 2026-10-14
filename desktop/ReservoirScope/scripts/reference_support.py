"""Shared, standard-library-only reference validation; never updates the baseline."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
REFERENCE = Path("shared/reservoir-scope/reference-manifest.json")
FIXTURES = Path("shared/reservoir-scope/fixtures/reference-scenes.json")
STAGED_NAMES = ("native-action-response.json", "state-response.json",
                "guided-observation-recording.json", "guided-observation-amendment.json",
                "guided-observation-retry-20260916.json",
                "essentials-stage-1.json", "essentials-stage-2.json", "essentials-stage-3.json",
                "essentials-stage-4.json", "data.json", "state-replay.bin", "state-replay.json", "state-geometry.json",
                *(f"example-component-{n}.json" for n in range(1, 9)), "example-observation-active-scripted.json",
                *(f"example-model-{n}.json" for n in range(4, 9)), "guided-lessons.json", "examples-index.json",
                "research-cases-v1.json", "synthetic-geometry-example.json",
                "example-observation-scripted.json", "example-regulation-controller.json",
                "example-model-observation-active.json", "example-model-observation.json",
                *(f"example-preparation-{n}.json" for n in range(1, 5)))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_local(root: Path, value: str) -> bytes:
    relative = PurePosixPath(value)
    if relative.is_absolute() or not relative.parts or any(p in (".", "..") for p in relative.parts) or "\\" in value:
        raise ValueError(f"Unsafe repository path: {value}")
    path = root.joinpath(*relative.parts)
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Missing or nonlocal reference input: {value}")
    return path.read_bytes()


def source_paths(root: Path, patterns: list[str]) -> list[str]:
    return sorted({p.relative_to(root).as_posix() for pattern in patterns for p in root.glob(pattern)
                   if p.is_file() and "__pycache__" not in p.parts})


def verify(root: Path = ROOT) -> dict:
    manifest = json.loads(read_local(root, REFERENCE.as_posix()))
    if manifest.get("schema") != "reservoir-scope.reference.v1":
        raise ValueError("Unsupported reference manifest")
    expected = {item["path"] for item in manifest["sources"]}
    actual = set(source_paths(root, manifest["sourcePatterns"]))
    if expected != actual:
        raise ValueError(f"Native source inventory drift; added={sorted(actual - expected)}, missing={sorted(expected - actual)}")
    for item in manifest["sources"] + manifest["resources"] + manifest["fixtures"]:
        data = read_local(root, item["path"])
        if len(data) != item["bytes"] or sha256(data) != item["sha256"]:
            raise ValueError(f"Frozen reference drift: {item['path']}")
    native = json.loads(read_local(root, "native/ReservoirScope/resource-manifest.json"))
    if native["release"] != {"version": manifest["baseline"]["nativeVersion"], "build": manifest["baseline"]["nativeBuild"]}:
        raise ValueError("Native identity differs from reference")
    declared = {item["name"]: (item["source"], item["sha256"]) for item in native["resources"]}
    frozen = {item["name"]: (item["path"], item["sha256"]) for item in manifest["resources"]}
    if declared != frozen:
        raise ValueError("Native resource declaration differs from frozen reference")
    verify_scenes(root)
    return manifest


def expected_scenes(root: Path = ROOT) -> dict:
    """Derive the two M0 scenes from public, hash-bound canonical examples."""
    import struct
    stage_path = "essentials/examples/essentials-stage-1.json"
    stage_bytes = read_local(root, stage_path)
    frame = json.loads(stage_bytes)["frames"][0]
    bin_path = "native/ReservoirScope/Sources/ReservoirScope/Resources/state-replay.bin"
    binary = read_local(root, bin_path)
    return {"schema": "reservoir-scope.reference-scenes.v1", "scenes": [
        {"id": "stage-1-32", "title": "Stage 1 · 32 coordinates", "nodeCount": 32,
         "description": "First recorded stage-one frame from the public offline lab example.",
         "provenance": "Bundled offline numerical experiment, step 1. This is a recorded lab example, not a live being state.",
         "values": frame["state"], "sourcePath": stage_path, "sourceSha256": sha256(stage_bytes), "step": frame["step"]},
        {"id": "retained-128", "title": "Retained native state · 128 coordinates", "nodeCount": 128,
         "description": "First retained activation row from the public historical Minime state replay.",
         "provenance": "Historical retained capture, row 0 (oldest to newest), observed 2026-09-07T05:11:52.328Z. No per-row timestamp, authenticated node layout, session identity, successful-step identifier, or paired fill/controller join is available. Array order is preserved; displayed geometry is an explanatory layout.",
         "values": list(struct.unpack("<128f", binary[:128 * 4])), "sourcePath": bin_path, "sourceSha256": sha256(binary)}]}


def verify_scenes(root: Path = ROOT) -> None:
    actual = json.loads(read_local(root, FIXTURES.as_posix()))
    if actual != expected_scenes(root):
        raise ValueError("Reference scene derivation differs from canonical source rows")
