"""The frozen pilot stops across arms, retaining completed and failed attempts."""
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import run_activation_pilot as pilot


class PilotStoppingTests(unittest.TestCase):
    def test_failed_qualification_never_dispatches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / "binary"
            binary.touch()
            qualification = root / "qualification"
            qualification.mkdir()
            for name, value in (("result", {"passed": False}), ("plan", {}), ("initialization", {})):
                pilot.save(qualification / f"{name}.json", value)
            with patch.object(pilot.subprocess, "run") as dispatch:
                result = pilot.run(SimpleNamespace(output=str(root / "attempt"), binary=str(binary), qualification=str(qualification), model="unused"))
            dispatch.assert_not_called()
            self.assertEqual(result["status"], "held")
            self.assertTrue((root / "attempt/result.json").is_file())

    def test_second_arm_failure_retains_first_and_never_dispatches_third(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app = root / "desktop/ReservoirScope"
            app.mkdir(parents=True)
            (app / "activation-requirements.lock").touch()
            fixture = root / "shared/reservoir-scope/activation-pilot.json"
            fixture.parent.mkdir(parents=True)
            pilot.save(fixture, {"arms": ["decaying_trace", "no_steering", "recurrent"], "seed": 1,
                                 "temperature": 0.0, "requestDeadlineSeconds": 180,
                                 "observations": ["a"] * 12, "stepsBetweenObservations": 10,
                                 "journalEveryObservations": 2, "outputTokens": 1024, "readingQuestions": ["Read everything"]})
            binary = root / "binary"
            binary.touch()
            qualification = root / "qualification"
            qualification.mkdir()
            manifest, calibration = {"sha256": "M"}, {"sha256": "C"}
            plan = {"manifest": manifest}
            pilot.save(qualification / "plan.json", plan)
            pilot.save(qualification / "initialization.json", {"manifest": manifest, "calibration": calibration})
            pilot.save(qualification / "calibration.json", calibration)
            pilot.save(qualification / "result.json", {"passed": True, "checks": {"parity": True}, "planSha256": pilot.canonical_hash(plan),
                       "planFileSha256": pilot.sha256_file(qualification / "plan.json"), "calibrationSha256": "C",
                       "calibrationFileSha256": pilot.sha256_file(qualification / "calibration.json")})
            calls = []

            def dispatch(command, **kwargs):
                calls.append(command)
                if "--verify-activation" in command:
                    return SimpleNamespace(returncode=0, stdout='{"status":"passed"}', stderr="")
                if len(calls) == 1:
                    directory = root / "retained"
                    directory.mkdir()
                    pilot.save(directory / "calibration.json", calibration)
                    json.dump({"directory": str(directory), "sessionId": "synthetic", "status": "completed",
                               "journalCount": 6, "step": 121,
                               "journals": [{"text": f"Synthetic entry {n}", "observedStep": n*20} for n in range(1, 7)]}, kwargs["stdout"])
                    return SimpleNamespace(returncode=0)
                kwargs["stdout"].write('{"status":"failed","reason":"synthetic refusal"}')
                return SimpleNamespace(returncode=1)

            with patch.object(pilot, "APP", app), patch.object(pilot, "ROOT", root), \
                 patch.object(pilot, "inspect_model", return_value={"manifest": manifest, "modelPath": "unused"}), \
                 patch.object(pilot, "validate_calibration", return_value=calibration), \
                 patch.object(pilot.subprocess, "run", side_effect=dispatch):
                result = pilot.run(SimpleNamespace(output=str(root / "attempt"), binary=str(binary), qualification=str(qualification), model="unused"))
            self.assertEqual(len(calls), 3)  # First run, its replay, second run only.
            self.assertEqual(len(result["arms"]), 2)
            self.assertEqual(result["status"], "held")
            self.assertEqual(result["automaticRetries"], 0)
            self.assertTrue((root / "attempt/reading-A.json").is_file())
            self.assertTrue((root / "attempt/condition-2-stdout.json").is_file())
            self.assertFalse((root / "attempt/condition-3.json").exists())


if __name__ == "__main__":
    unittest.main()
