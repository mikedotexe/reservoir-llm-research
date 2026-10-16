"""Inspect only the explicitly supplied local model and owned runtime."""
from __future__ import annotations

import importlib.metadata
import json
import platform
from pathlib import Path

from . import HIDDEN_DIM, LAYER_COUNT, MODEL_ID, MODEL_REVISION, TAP_BLOCK_INDEX
from .math_core import canonical_hash, sha256_file


def inspect_dependencies() -> dict:
    """Check the whole qualified lock using metadata only, without loading MLX."""
    lock = Path(__file__).resolve().parent.parent / "activation-requirements.lock"
    versions = {}
    for line in lock.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, expected = line.split("==", 1)
        actual = importlib.metadata.version(name)
        if actual != expected:
            raise ValueError(f"Activation dependency mismatch: {name} requires {expected}, found {actual}")
        versions[name] = actual
    if len(versions) != 34:
        raise ValueError("Activation dependency lock does not contain the qualified 34 packages")
    return versions


def inspect_model(model_path: str) -> dict:
    root = Path(model_path).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("modelPath must name a local model directory")
    receipt_path = root / "model-provenance.json"
    provenance = json.loads(receipt_path.read_text())
    if provenance.get("modelId") != MODEL_ID or provenance.get("revision") != MODEL_REVISION:
        raise ValueError("model provenance does not identify the approved pinned model")
    declared = provenance.get("files")
    if not isinstance(declared, list) or not declared:
        raise ValueError("model provenance requires a nonempty files manifest")
    files = []
    seen = set()
    for entry in declared:
        relative = entry.get("path")
        if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("invalid model provenance path")
        if relative in seen or relative == "model-provenance.json":
            raise ValueError("duplicate or recursive model provenance entry")
        seen.add(relative)
        path = (root / relative).resolve(strict=True)
        if not path.is_relative_to(root):
            raise ValueError("model provenance path escapes the owned directory")
        digest = sha256_file(path)
        if digest != entry.get("sha256"):
            raise ValueError(f"model asset hash mismatch: {relative}")
        files.append({"path": relative, "sha256": digest, "bytes": path.stat().st_size})
    relevant = {str(p.relative_to(root)) for p in root.rglob("*")
                if p.is_file() and (p.suffix in {".safetensors", ".json", ".model", ".jinja"})
                and p.name != "model-provenance.json" and ".cache" not in p.parts}
    if not relevant.issubset(seen):
        raise ValueError("unmanifested model/tokenizer assets: " + ", ".join(sorted(relevant - seen)))
    if "config.json" not in seen or "tokenizer.json" not in seen or not any(x.endswith(".safetensors") for x in seen):
        raise ValueError("model config, tokenizer and safetensors must all be manifested")
    config = json.loads((root / "config.json").read_text())
    if (config.get("model_type"), config.get("hidden_size"), config.get("num_hidden_layers")) != ("qwen3", HIDDEN_DIM, LAYER_COUNT):
        raise ValueError("model architecture does not match Qwen3 36 layers / 2560 hidden dimensions")
    quant = config.get("quantization", config.get("quantization_config", {}))
    if quant.get("bits") != 4:
        raise ValueError("model quantization must be 4-bit")
    versions = inspect_dependencies()
    runtime_sources = []
    distribution = importlib.metadata.distribution("mlx-lm")
    for relative in ("mlx_lm/models/qwen3.py", "mlx_lm/models/cache.py", "mlx_lm/sample_utils.py", "mlx_lm/tokenizer_utils.py", "mlx_lm/utils.py"):
        source = Path(distribution.locate_file(relative))
        runtime_sources.append({"path": relative, "sha256": sha256_file(source)})
    worker_sources = [{"path": p.name, "sha256": sha256_file(p)}
                      for p in sorted(Path(__file__).parent.glob("*.py"))]
    body = {
        "schemaVersion": "activation-model-manifest/1", "modelId": MODEL_ID,
        "revision": MODEL_REVISION, "hiddenDim": HIDDEN_DIM,
        "layerCount": LAYER_COUNT, "tapBlockIndex": TAP_BLOCK_INDEX,
        "tapBoundary": "after-block-before-steering", "captureDtype": "float32",
        "quantization": quant, "files": sorted(files, key=lambda x: x["path"]),
        "provenanceSha256": sha256_file(receipt_path), "runtimeVersions": versions,
        "pythonVersion": platform.python_version(), "platform": platform.machine(),
        "runtimeSources": runtime_sources, "workerSources": worker_sources,
    }
    body["sha256"] = canonical_hash(body)
    # Absolute path is not part of identity: copying identical assets is allowed.
    return {"modelPath": str(root), "manifest": body}
