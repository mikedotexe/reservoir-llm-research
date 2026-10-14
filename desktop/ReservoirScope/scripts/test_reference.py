"""Mutation checks run only in disposable copies of the frozen public inputs."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from reference_support import ROOT, REFERENCE, STAGED_NAMES, verify
from stage_resources import stage


class ReferenceChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="scope-reference-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        manifest = verify(ROOT)
        paths = {item["path"] for group in ("sources", "resources", "fixtures") for item in manifest[group]}
        paths.add(REFERENCE.as_posix())
        for relative in paths:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        self.original_manifest = (self.root / REFERENCE).read_bytes()

    def test_stage_preserves_inputs_and_derives_source_values(self):
        verify(self.root)
        self.assertEqual(stage(self.root)["files"], len(STAGED_NAMES) + 3)
        staged = self.root / "desktop/ReservoirScope/src-tauri/resources"
        scenes = json.loads((staged / "reference-scenes.json").read_text())["scenes"]
        self.assertEqual([len(scene["values"]) for scene in scenes], [32, 128])
        self.assertNotIn("step", scenes[1])
        self.assertEqual((self.root / REFERENCE).read_bytes(), self.original_manifest)
        index = json.loads((staged / "resource-index.json").read_text())
        for item in index["resources"]:
            self.assertEqual((staged / item["name"]).read_bytes(), (self.root / item["source"]).read_bytes())
        verify(self.root)

    def test_changed_resource_fails_before_staging(self):
        source = self.root / "essentials/examples/essentials-stage-1.json"
        source.write_bytes(source.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "Frozen reference drift"):
            stage(self.root)
        self.assertFalse((self.root / "desktop").exists())
        self.assertEqual((self.root / REFERENCE).read_bytes(), self.original_manifest)

    def test_added_native_source_is_detected(self):
        (self.root / "native/ReservoirScope/Sources/ReservoirScope/New.swift").write_text("// changed\n")
        with self.assertRaisesRegex(ValueError, "source inventory drift"):
            verify(self.root)

    def test_changed_fixture_is_detected(self):
        path = self.root / "shared/reservoir-scope/fixtures/reference-scenes.json"
        value = json.loads(path.read_text())
        value["scenes"][0]["values"][0] = 123.0
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "Frozen reference drift"):
            verify(self.root)

    def test_stage_refuses_non_file_output(self):
        directory = self.root / "desktop/ReservoirScope/src-tauri/resources/unexpected"
        directory.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "Unexpected non-file"):
            stage(self.root)
        self.assertTrue(directory.exists())


if __name__ == "__main__":
    unittest.main()
