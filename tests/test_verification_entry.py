"""Verification grouping never turns missing or stale coverage into a pass."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from reservoir_research import cli, verification

class VerificationEntryChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_package_without_app_is_incomplete(self):
        out = self.root / "receipt"
        with patch.object(cli.store, "connect", side_effect=AssertionError("database opened")), \
             patch.object(cli, "default_sources", side_effect=AssertionError("source discovery")), \
             contextlib.redirect_stdout(io.StringIO()):
            code = cli.main(["verify", "--group", "package", "--out", str(out)])
        self.assertEqual(code, 2)
        result = json.loads((out / "verification.json").read_bytes())
        self.assertEqual(result["groups"][0]["status"], "incomplete")
        self.assertFalse(result["models_contacted"])
        self.assertFalse(result["live_sources_read"])

    def test_research_without_inputs_is_incomplete(self):
        out = self.root / "receipt"
        with contextlib.redirect_stdout(io.StringIO()):
            code = cli.main(["verify", "--group", "research-replay", "--out", str(out)])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads((out / "verification.json").read_bytes())["outcome"], "incomplete")

    def test_inheritance_requires_exact_source_identity(self):
        receipt = self.root / "old.json"
        receipt.write_text(json.dumps(dict(schema="reservoir-research-verification-v1",
            groups=[dict(group="python", outcome="passed", source_identity={"source": "old"})])))
        self.assertIsNone(verification.inherited_group("python", {"source": "new"}, [receipt]))
        inherited = verification.inherited_group("python", {"source": "old"}, [receipt])
        self.assertEqual(inherited["status"], "inherited")
        self.assertEqual(inherited["commands"], [])

    def test_runtime_evidence_cannot_inherit(self):
        receipt = self.root / "old.json"
        receipt.write_text(json.dumps(dict(schema="reservoir-research-verification-v1",
            groups=[dict(group="research-replay", outcome="passed", source_identity={}),
                    dict(group="package", outcome="passed", source_identity={})])))
        self.assertIsNone(verification.inherited_group("research-replay", {}, [receipt]))
        self.assertIsNone(verification.inherited_group("package", {}, [receipt]))

    def test_incomplete_coverage_cannot_inherit(self):
        receipt = self.root / "old.json"
        receipt.write_text(json.dumps(dict(schema="reservoir-research-verification-v1",
            groups=[dict(group="python", outcome="incomplete", source_identity={})])))
        self.assertIsNone(verification.inherited_group("python", {}, [receipt]))

    def test_archive_cli_uses_separate_api(self):
        with patch("reservoir_research.archive.verify", return_value={"status": "verified"}) as call, \
             patch.object(cli.store, "connect", side_effect=AssertionError("database opened")), \
             contextlib.redirect_stdout(io.StringIO()):
            code = cli.main(["archive", "verify", str(self.root)])
        self.assertEqual(code, 0)
        call.assert_called_once_with(self.root)

    def test_geometry_checks_use_correct_groups_and_output_paths(self):
        native = self.root / "native/ReservoirScope"
        native.mkdir(parents=True)
        for name in ("check-geometry-bookmarks.sh", "check-geometry-bookmark-presentation.sh"):
            (native / name).touch()
        args = SimpleNamespace(app=None, daily_manifest=None, daily_report=None, data_root=None,
                               inherit=[], timeout=30, group=["native-model", "native-presentation"],
                               out=self.root / "geometry-verification")
        def execute(command, root, env, log, timeout):
            return dict(command=command, exit_code=0, outcome="passed")
        with patch.object(verification.platform, "system", return_value="Darwin"), \
             patch.object(verification.shutil, "which", return_value="/tool"), \
             patch.object(verification, "source_identity", return_value={"fixture": "stable"}), \
             patch.object(verification, "_execute", side_effect=execute):
            receipt, code = verification.run(args, root=self.root)
        self.assertEqual(code, 0)
        model, presentation = receipt["groups"]
        model_commands = [item["command"] for item in model["commands"]]
        presentation_commands = [item["command"] for item in presentation["commands"]]
        expected_model = ["bash", str((native / "check-geometry-bookmarks.sh").resolve()),
                          str((args.out / "check-geometry-bookmarks").resolve())]
        expected_presentation = ["bash", str((native / "check-geometry-bookmark-presentation.sh").resolve()),
                                 str((args.out / "check-geometry-bookmark-presentation").resolve())]
        self.assertIn(expected_model, model_commands)
        self.assertNotIn(expected_model, presentation_commands)
        self.assertEqual(presentation_commands, [expected_presentation])

if __name__ == "__main__":
    unittest.main()
