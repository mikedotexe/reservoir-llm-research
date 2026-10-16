"""Qualification admission tests: fake resources/processes, no model or sleeping."""
import json
from pathlib import Path
from types import SimpleNamespace
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

import run_activation_qualification as runner
from test_activation_pilot import Clock, HEALTHY, UNHEALTHY


class QualificationAdmissionTests(unittest.TestCase):
    def run_case(self, root, sampler, execute):
        clock = Clock()
        args = SimpleNamespace(model=str(root), output=str(root / "attempt"))
        return runner.run(args, sampler=sampler, execute=execute,
                          monotonic=clock.monotonic, sleep=clock.sleep, utc_clock=clock.utc)

    def test_no_dispatch_after_preparation_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            execute = Mock()
            result = self.run_case(Path(tmp), Mock(return_value=UNHEALTHY), execute)
            self.assertEqual(result["preparation"]["elapsedSeconds"], 600)
            self.assertFalse(result["dispatched"])
            execute.assert_not_called()

    def test_fresh_admission_refusal_does_not_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            execute = Mock()
            sampler = Mock(side_effect=[HEALTHY] * 3 + [UNHEALTHY])
            result = self.run_case(Path(tmp), sampler, execute)
            self.assertTrue(result["preparation"]["ready"])
            self.assertFalse(result["dispatched"])
            self.assertEqual(sampler.call_count, 4)
            execute.assert_not_called()

    def test_single_timeout_is_retained_without_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            execute = Mock(side_effect=subprocess.TimeoutExpired("synthetic", 900))
            result = self.run_case(Path(tmp), Mock(return_value=HEALTHY), execute)
            self.assertTrue(result["dispatched"])
            self.assertEqual(result["status"], "held")
            self.assertIn("TimeoutExpired", result["error"])
            self.assertEqual(execute.call_count, 1)
            self.assertEqual(execute.call_args.kwargs["timeout"], 900)
            self.assertTrue((Path(tmp) / "attempt/result.json").is_file())

    def test_pass_requires_retained_checks_not_just_exit_zero(self):
        for passed in (True, False):
            with self.subTest(passed=passed), tempfile.TemporaryDirectory() as tmp:
                def execute(command, **kwargs):
                    output = Path(command[-1])
                    output.mkdir()
                    (output / "result.json").write_text(json.dumps({"passed": passed,
                                                                    "checks": {"parity": passed}}))
                    return SimpleNamespace(returncode=0)
                result = self.run_case(Path(tmp), Mock(return_value=HEALTHY), execute)
                self.assertEqual(result["status"], "passed" if passed else "held")


if __name__ == "__main__":
    unittest.main()
