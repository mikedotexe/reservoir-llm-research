#!/usr/bin/env python3
"""Qualify preparation metadata with all process and network calls mocked.

This does not verify a numerical fixture or attempt model inventory/generation.
It checks that an inherited old prompt contract cannot leak into a new protocol.
"""
import contextlib
import io
import json
import pathlib
import runpy
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "record-guided-observation.py"


class GuidedRecordingPreparationTests(unittest.TestCase):
    def check_unavailable(self, inherited_prompt_version):
        with tempfile.TemporaryDirectory(prefix="guided-protocol-mock-") as temporary:
            root = pathlib.Path(temporary)
            cli = root / "fixture-cli"
            cli.write_bytes(b"Mock identity only: never executed.\n")
            fixture = root / "fixture.json"
            specification = dict(forcingProfile="continuousSensoryV1", comparisonKind="observation",
                                 stage=4, mode="independentGeneration", comparePrevious=True,
                                 steps=120, turnEvery=30, language={"backend": "scripted"})
            if inherited_prompt_version is not None:
                specification["promptVersion"] = inherited_prompt_version
            fixture.write_text(json.dumps(dict(specification=specification,
                right={"frames": [{"state": [0.5] * 32} for _ in range(120)]})))
            original_fixture = fixture.read_bytes()
            output = root / "new-preparation"
            args = [str(SCRIPT), "--cli", str(cli), "--fixture", str(fixture),
                    "--output", str(output), "--endpoint", "http://127.0.0.1:12345"]
            process_calls = []
            inventory_snapshots = []

            def process(command, **kwargs):
                process_calls.append(command)
                self.assertEqual(command, [str(cli), "verify", str(fixture)],
                                 "Unavailable inventory must prevent any generation command.")
                return subprocess.CompletedProcess(command, 0)

            def unavailable(url, **kwargs):
                recipe = json.loads((output / "active-observation.recipe.json").read_text())
                manifest = json.loads((output / "guided-observation-recording.json").read_text())
                inventory_snapshots.append((url, recipe, manifest))
                raise urllib.error.URLError("Mock unavailable inventory; no socket was opened.")

            with mock.patch.object(sys, "argv", args), \
                    mock.patch("subprocess.run", side_effect=process), \
                    mock.patch("urllib.request.urlopen", side_effect=unavailable) as inventory, \
                    contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as stopped:
                    runpy.run_path(str(SCRIPT), run_name="__main__")
                self.assertEqual(stopped.exception.code, 0)
            self.assertEqual(inventory.call_count, 1)
            self.assertEqual(len(process_calls), 1)
            self.assertEqual(len(inventory_snapshots), 1, "Recipe and manifest must exist before inventory is checked.")
            inventory_url, frozen_recipe, frozen_manifest = inventory_snapshots[0]
            self.assertEqual(inventory_url, "http://127.0.0.1:12345/api/tags")
            self.assertEqual(frozen_recipe["promptVersion"], 2)
            self.assertEqual(frozen_manifest["prompt_version"], 2)
            self.assertEqual(frozen_manifest["word_instruction"], 40)
            self.assertEqual(frozen_manifest["specification"], frozen_recipe)
            self.assertEqual(frozen_manifest["status"], "registered")
            manifest = json.loads((output / "guided-observation-recording.json").read_text())
            self.assertEqual(manifest["status"], "unavailable")
            self.assertEqual(manifest["attempts"], [])
            self.assertEqual(manifest["specification"]["promptVersion"], 2)
            self.assertEqual(manifest["prompt_version"], 2)
            self.assertEqual(manifest["word_instruction"], 40)
            self.assertEqual(manifest["maximum_model_requests"], 6)
            self.assertEqual(fixture.read_bytes(), original_fixture)
            self.assertFalse((output / "example-model-observation-active.json").exists())
            self.assertFalse((output / "active-observation.log").exists())

    def test_old_fixture_is_frozen_as_prompt_v2_before_unavailable_inventory(self):
        self.check_unavailable(1)

    def test_missing_fixture_prompt_version_is_also_frozen_as_v2(self):
        self.check_unavailable(None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
