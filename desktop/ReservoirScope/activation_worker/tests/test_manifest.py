from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from activation_worker import MODEL_ID, MODEL_REVISION
from activation_worker.manifest import inspect_model
from activation_worker.math_core import sha256_file
from activation_worker.qualify import dtype_rounding_allowance


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "config.json").write_text(json.dumps({"model_type": "qwen3", "hidden_size": 2560,
                                                        "num_hidden_layers": 36, "quantization": {"bits": 4}}))
        (self.root / "tokenizer.json").write_text("{}")
        (self.root / "model.safetensors").write_bytes(b"fixture, never loaded")
        self.rebind()

    def rebind(self):
        files = [{"path": p.name, "sha256": sha256_file(p)} for p in sorted(self.root.iterdir())
                 if p.is_file() and p.name != "model-provenance.json"]
        (self.root / "model-provenance.json").write_text(json.dumps({"modelId": MODEL_ID,
                                                                   "revision": MODEL_REVISION, "files": files}))

    def test_local_actual_assets_are_bound_without_loading_model(self):
        # Installed source metadata can be inspected without importing/loading MLX.
        result = inspect_model(str(self.root))
        self.assertEqual(result["manifest"]["hiddenDim"], 2560)
        self.assertEqual(result["manifest"]["tapBlockIndex"], 17)
        self.assertEqual(len(result["manifest"]["sha256"]), 64)
        self.assertEqual(len(result["manifest"]["runtimeSources"]), 5)

    def test_asset_tampering_rejected(self):
        (self.root / "model.safetensors").write_bytes(b"different")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            inspect_model(str(self.root))

    def test_new_unmanifested_tokenizer_asset_rejected(self):
        (self.root / "tokenizer_config.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "unmanifested"):
            inspect_model(str(self.root))

    def test_revision_and_architecture_checked(self):
        receipt = json.loads((self.root / "model-provenance.json").read_text())
        receipt["revision"] = "a" * 40
        (self.root / "model-provenance.json").write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "pinned model"):
            inspect_model(str(self.root))
        (self.root / "config.json").write_text(json.dumps({"model_type": "qwen3", "hidden_size": 3840,
                                                        "num_hidden_layers": 36, "quantization": {"bits": 4}}))
        self.rebind()
        with self.assertRaisesRegex(ValueError, "architecture"):
            inspect_model(str(self.root))

    def test_manifest_path_escape_rejected(self):
        receipt = json.loads((self.root / "model-provenance.json").read_text())
        receipt["files"][0]["path"] = "../outside.json"
        (self.root / "model-provenance.json").write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "path"):
            inspect_model(str(self.root))


class QualificationContractTests(unittest.TestCase):
    def test_bfloat_rounding_bound_is_predeclared_and_below_half_percent(self):
        bound = dtype_rounding_allowance("mlx.core.bfloat16")
        self.assertLess(bound, .005)
        self.assertGreater(bound, 0)
        self.assertLess(dtype_rounding_allowance("mlx.core.float16"), .0005)
        with self.assertRaisesRegex(ValueError, "unqualified"):
            dtype_rounding_allowance("unknown")


if __name__ == "__main__":
    unittest.main()
