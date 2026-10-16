"""Download and identify the isolated, pinned activation experiment model.

Run with the activation virtualenv. This prepares files; it never imports MLX,
loads model weights, contacts a Being endpoint, or starts an experiment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

MODEL = "mlx-community/Qwen3-4B-4bit"
REVISION = "4dcb3d101c2a062e5c1d4bb173588c54ea6c4d25"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path,
                        default=Path(__file__).resolve().parents[1] / ".activation-models/qwen3-4b")
    args = parser.parse_args()
    root = args.destination.resolve()
    if (root / "model-provenance.json").exists():
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from activation_worker.manifest import inspect_model
        inspected = inspect_model(str(root))
        print(json.dumps({"status": "already-present-and-verified", "modelPath": str(root),
                          "manifestSha256": inspected["manifest"]["sha256"]}))
        return
    if root.exists() and any(root.iterdir()):
        raise ValueError("Destination contains unverified files. Preserve them and choose a new empty destination.")
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id=MODEL, revision=REVISION, local_dir=root,
                      allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt", "*.jinja"])
    config = json.loads((root / "config.json").read_text())
    expected = {"model_type": "qwen3", "num_hidden_layers": 36, "hidden_size": 2560}
    if any(config.get(k) != value for k, value in expected.items()):
        raise ValueError("Pinned model configuration differs from the experiment contract")
    files = [{"path": str(p.relative_to(root)), "sha256": digest(p)}
             for p in sorted(root.rglob("*"))
             if p.is_file() and ".cache" not in p.relative_to(root).parts
             and p.name != "model-provenance.json"]
    if not any(row["path"].endswith(".safetensors") for row in files):
        raise ValueError("No model weights were downloaded")
    receipt = {"modelId": MODEL, "revision": REVISION, "files": files}
    (root / "model-provenance.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"modelId": MODEL, "revision": REVISION,
                      "destination": str(root), "files": len(files),
                      "provenanceSha256": digest(root / "model-provenance.json")}))


if __name__ == "__main__":
    main()
