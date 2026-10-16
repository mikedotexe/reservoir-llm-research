from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from activation_worker import MODEL_ID, MODEL_REVISION
from activation_worker.manifest import inspect_dependencies, inspect_model
from activation_worker.math_core import sha256_file
from activation_worker.qualify import bounded_capture, dtype_rounding_allowance, save


class ManifestTests(unittest.TestCase):
    def test_full_dependency_lock_is_checked_without_model_loading(self):
        import importlib.metadata
        original = importlib.metadata.version
        self.assertEqual(len(inspect_dependencies()), 34)
        with patch("activation_worker.manifest.importlib.metadata.version", side_effect=lambda name: "wrong" if name == "filelock" else original(name)):
            with self.assertRaisesRegex(ValueError, "filelock"):
                inspect_dependencies()

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
    def test_capture_result_is_a_native_json_boolean_and_saves(self):
        capture = {"activation": [0.5] * 2560, "projection": [0.1] * 32}
        outcome = bounded_capture(capture)
        self.assertIs(type(outcome), bool)
        self.assertIs(outcome, True)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result.json"
            save(path, {"checks": {"boundedCaptures": outcome}, "passed": outcome})
            self.assertEqual(json.loads(path.read_text()),
                             {"checks": {"boundedCaptures": True}, "passed": True})
        for bad_capture in ({**capture, "activation": [0.0] * 2559},
                            {**capture, "activation": [float("nan")] * 2560},
                            {**capture, "projection": [1.1] * 32}):
            outcome = bounded_capture(bad_capture)
            self.assertIs(type(outcome), bool)
            self.assertIs(outcome, False)

    def test_bfloat_rounding_bound_is_predeclared_and_below_half_percent(self):
        bound = dtype_rounding_allowance("mlx.core.bfloat16")
        self.assertLess(bound, .005)
        self.assertGreater(bound, 0)
        self.assertLess(dtype_rounding_allowance("mlx.core.float16"), .0005)
        with self.assertRaisesRegex(ValueError, "unqualified"):
            dtype_rounding_allowance("unknown")


if __name__ == "__main__":
    unittest.main()
