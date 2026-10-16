"""Runner tests use synthetic evidence, clocks and processes; never models or waits."""
from contextlib import ExitStack
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_activation_pilot as pilot


def protocol(preparation=False):
    value = {"schema": "activation-pilot-v1", "id": "synthetic-protocol",
             "arms": ["decaying_trace", "no_steering", "recurrent"], "seed": 1,
             "temperature": 0.0, "requestDeadlineSeconds": 180,
             "observations": ["Synthetic observation"] * 12, "stepsBetweenObservations": 10,
             "journalEveryObservations": 2, "outputTokens": 1024,
             "readingQuestions": ["Read everything"], "interpretation": "Synthetic test only",
             "stoppingRule": "Stop on the first failure or refusal"}
    if preparation:
        value["resourcePreparation"] = dict(pilot.RESOURCE_PREPARATION)
    return value


class Clock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds

    def utc(self):
        return f"synthetic-clock-{self.now}"


HEALTHY = {"pressure": 1, "freePercent": 25}
UNHEALTHY = {"pressure": 2, "freePercent": 32}


class ProtocolTests(unittest.TestCase):
    def test_original_and_approved_preparation_are_valid(self):
        for value in (protocol(), protocol(True)):
            self.assertEqual(pilot.validate_protocol(value), value)

    def test_bounds_cannot_be_weakened_or_mistyped(self):
        for key, bad in (("maximumSeconds", 121), ("pollSeconds", 1),
                         ("consecutiveHealthySamples", 2), ("minimumFreePercent", 24),
                         ("requiredPressureLevel", 2), ("requiredPressureLevel", True)):
            with self.subTest(key=key, value=bad):
                value = protocol(True)
                value["resourcePreparation"][key] = bad
                with self.assertRaises(ValueError):
                    pilot.validate_protocol(value)
        for key, bad in (("schema", "other"), ("temperature", 0.1), ("outputTokens", 1024.0),
                         ("requestDeadlineSeconds", 181), ("observations", ["one"]),
                         ("arms", ["decaying_trace"] * 3), ("seed", True), ("resourcePreperation", {})):
            with self.subTest(key=key):
                value = protocol()
                value[key] = bad
                with self.assertRaises(ValueError):
                    pilot.validate_protocol(value)


class ResourcePreparationTests(unittest.TestCase):
    def prepare(self, directory, sampler, clock):
        return pilot.prepare_resources(directory, 0, "decaying_trace", pilot.RESOURCE_PREPARATION,
                                       sampler=sampler, monotonic=clock.monotonic,
                                       sleep=clock.sleep, utc_clock=clock.utc)

    def test_healthy_streak_resets_after_unhealthy_sample(self):
        clock = Clock()
        sampler = Mock(side_effect=[HEALTHY, HEALTHY, UNHEALTHY, HEALTHY, HEALTHY, HEALTHY])
        with tempfile.TemporaryDirectory() as tmp:
            result = self.prepare(Path(tmp), sampler, clock)
            rows = [json.loads(line) for line in (Path(tmp) / result["samplesFile"]).read_text().splitlines()]
        self.assertEqual([r["consecutiveHealthySamples"] for r in rows], [1, 2, 0, 1, 2, 3])
        self.assertEqual([r["elapsedSeconds"] for r in rows], [0, 10, 20, 30, 40, 50])
        self.assertTrue(all(r["sampledAtUtc"] and r["completedAtUtc"] for r in rows))
        self.assertTrue(result["ready"])
        self.assertEqual(result["elapsedSeconds"], 50)
        self.assertEqual(clock.sleeps, [10] * 5)

    def test_unknown_samples_never_count_as_healthy(self):
        clock = Clock()
        sampler = Mock(side_effect=[HEALTHY, {"pressure": None, "freePercent": 80},
                                    HEALTHY, {"pressure": 1, "freePercent": None}, HEALTHY, HEALTHY, HEALTHY])
        with tempfile.TemporaryDirectory() as tmp:
            result = self.prepare(Path(tmp), sampler, clock)
        self.assertTrue(result["ready"])
        self.assertEqual(result["sampleCount"], 7)
        self.assertEqual(result["elapsedSeconds"], 60)

    def test_timeout_is_bounded_without_real_waiting(self):
        clock = Clock()
        sampler = Mock(return_value=UNHEALTHY)
        with tempfile.TemporaryDirectory() as tmp:
            result = self.prepare(Path(tmp), sampler, clock)
        self.assertFalse(result["ready"])
        self.assertEqual(result["reason"], "preparation_deadline_reached")
        self.assertEqual(result["elapsedSeconds"], 120)
        self.assertEqual(sampler.call_count, 12)
        self.assertTrue(all(0 < c.args[0] <= 120 for c in sampler.call_args_list))

    def test_sample_finishing_after_deadline_cannot_admit(self):
        clock, calls = Clock(), []
        def sample(remaining):
            calls.append(remaining)
            if len(calls) == 3:
                clock.now += remaining + 1
            return HEALTHY
        with tempfile.TemporaryDirectory() as tmp:
            result = self.prepare(Path(tmp), sample, clock)
        self.assertFalse(result["ready"])
        self.assertEqual(result["sampleCount"], 3)

    def test_sampler_parses_only_successful_read_only_commands(self):
        responses = [SimpleNamespace(returncode=0, stdout="1\n", stderr=""),
                     SimpleNamespace(returncode=0, stdout="System-wide memory free percentage: 32%\n", stderr="")]
        with patch.object(pilot.subprocess, "run", side_effect=responses) as dispatch:
            result = pilot.sample_resources(20)
        self.assertEqual((result["pressure"], result["freePercent"]), (1, 32))
        self.assertEqual(dispatch.call_args_list[0].args[0], ["/usr/sbin/sysctl", "-n", "kern.memorystatus_vm_pressure_level"])
        self.assertEqual(dispatch.call_args_list[1].args[0], ["/usr/bin/memory_pressure", "-Q"])
        self.assertTrue(all(0 < c.kwargs["timeout"] <= 5 for c in dispatch.call_args_list))
        responses[0].returncode = 1
        responses[1].stdout = "System-wide memory free percentage: 101%\n"
        with patch.object(pilot.subprocess, "run", side_effect=responses):
            result = pilot.sample_resources(20)
        self.assertIsNone(result["pressure"])
        self.assertIsNone(result["freePercent"])

    def test_sampler_keeps_timeouts_as_unknown_evidence(self):
        with patch.object(pilot.subprocess, "run", side_effect=pilot.subprocess.TimeoutExpired("synthetic", 5)):
            result = pilot.sample_resources(20)
        self.assertIsNone(result["pressure"])
        self.assertIsNone(result["freePercent"])
        self.assertTrue(all("TimeoutExpired" in r["error"] for r in result["commands"]))


class Harness:
    def __init__(self, root, preparation=False, failed_arm=2):
        self.root, self.failed_arm = root, failed_arm
        self.app = root / "desktop/ReservoirScope"
        self.app.mkdir(parents=True)
        (self.app / "activation-requirements.lock").touch()
        self.fixture = root / "shared/reservoir-scope/activation-pilot.json"
        self.fixture.parent.mkdir(parents=True)
        pilot.save(self.fixture, protocol())
        self.selected = root / "new-protocol.json" if preparation else self.fixture
        if preparation:
            pilot.save(self.selected, protocol(True))
        self.binary = root / "binary"
        self.binary.touch()
        self.qualification = root / "qualification"
        self.qualification.mkdir()
        self.manifest, self.calibration = {"sha256": "M"}, {"sha256": "C"}
        plan = {"manifest": self.manifest}
        pilot.save(self.qualification / "plan.json", plan)
        pilot.save(self.qualification / "initialization.json", {"manifest": self.manifest, "calibration": self.calibration})
        pilot.save(self.qualification / "calibration.json", self.calibration)
        pilot.save(self.qualification / "result.json", {
            "passed": True, "checks": {"parity": True}, "planSha256": pilot.canonical_hash(plan),
            "planFileSha256": pilot.sha256_file(self.qualification / "plan.json"), "calibrationSha256": "C",
            "calibrationFileSha256": pilot.sha256_file(self.qualification / "calibration.json")})
        self.args = SimpleNamespace(output=str(root / "attempt"), binary=str(self.binary),
                                    qualification=str(self.qualification), model="unused",
                                    protocol=str(self.selected) if preparation else None)
        self.calls, self.arm_calls = [], []
        self.release = Mock(return_value={"status": "no_matching_process_visible", "synthetic": True})

    def dispatch(self, command, **kwargs):
        self.calls.append(command)
        if "--verify-activation" in command:
            return SimpleNamespace(returncode=0, stdout='{"status":"passed"}', stderr="")
        self.arm_calls.append(command)
        number = len(self.arm_calls)
        if number == self.failed_arm:
            kwargs["stdout"].write('{"status":"failed","reason":"synthetic refusal"}')
            return SimpleNamespace(returncode=1)
        directory = self.root / f"retained-{number}"
        directory.mkdir()
        pilot.save(directory / "calibration.json", self.calibration)
        json.dump({"directory": str(directory), "sessionId": f"synthetic-{number}", "status": "completed",
                   "journalCount": 6, "step": 121,
                   "journals": [{"text": f"Synthetic entry {n}", "observedStep": n*20} for n in range(1, 7)]}, kwargs["stdout"])
        return SimpleNamespace(returncode=0)

    def run(self, **kwargs):
        with ExitStack() as stack:
            stack.enter_context(patch.object(pilot, "APP", self.app))
            stack.enter_context(patch.object(pilot, "ROOT", self.root))
            stack.enter_context(patch.object(pilot, "inspect_model", return_value={"manifest": self.manifest, "modelPath": "unused"}))
            stack.enter_context(patch.object(pilot, "validate_calibration", return_value=self.calibration))
            stack.enter_context(patch.object(pilot.subprocess, "run", side_effect=self.dispatch))
            return pilot.run(self.args, release_observer=self.release, **kwargs)


class PilotStoppingTests(unittest.TestCase):
    def test_failed_qualification_never_dispatches(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp))
            report = pilot.read(h.qualification / "result.json")
            report["passed"] = False
            (h.qualification / "result.json").write_text(json.dumps(report))
            result = h.run()
            self.assertEqual(h.calls, [])
            self.assertIn("Real-model qualification has not passed", result["error"])
            self.assertEqual(result["status"], "held")
            self.assertTrue((h.root / "attempt/result.json").is_file())

    def test_original_second_arm_failure_retains_first_and_never_prepares_or_dispatches_third(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp))
            sampler = Mock(side_effect=AssertionError("Original protocol must not sample preparation"))
            result = h.run(resource_sampler=sampler)
            sampler.assert_not_called()
            self.assertEqual(len(h.calls), 3)
            self.assertEqual(h.release.call_count, 2)
            self.assertEqual(len(result["arms"]), 2)
            self.assertEqual(result["status"], "held")
            self.assertEqual(result["automaticRetries"], 0)
            self.assertTrue((h.root / "attempt/reading-A.json").is_file())
            self.assertTrue((h.root / "attempt/condition-2-stdout.json").is_file())
            self.assertFalse((h.root / "attempt/condition-3.json").exists())

    def test_preparation_timeout_holds_entire_comparison_without_model_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            h, clock = Harness(Path(tmp), preparation=True), Clock()
            result = h.run(resource_sampler=lambda remaining: UNHEALTHY, monotonic=clock.monotonic,
                           sleep=clock.sleep, utc_clock=clock.utc)
            self.assertEqual(h.calls, [])
            self.assertEqual(result["arms"], [])
            self.assertEqual(result["status"], "held")
            self.assertEqual(result["resourcePreparations"][0]["elapsedSeconds"], 120)
            self.assertFalse((h.root / "attempt/condition-1.json").exists())
            self.assertFalse((h.root / "attempt/condition-2-resource-samples.jsonl").exists())
            frozen = pilot.read(h.root / "attempt/frozen-plan.json")
            self.assertEqual(frozen["protocolPath"], str(h.selected.resolve()))
            self.assertEqual(frozen["protocolSha256"], pilot.sha256_file(h.selected))
            self.assertEqual(frozen["runnerSha256"], pilot.sha256_file(Path(pilot.__file__)))

    def test_actual_admission_refusal_after_healthy_preparation_is_not_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            h, clock = Harness(Path(tmp), preparation=True, failed_arm=1), Clock()
            result = h.run(resource_sampler=lambda remaining: HEALTHY, monotonic=clock.monotonic,
                           sleep=clock.sleep, utc_clock=clock.utc)
            self.assertEqual(len(h.arm_calls), 1)
            self.assertEqual(len(result["resourcePreparations"]), 1)
            self.assertTrue(result["resourcePreparations"][0]["ready"])
            self.assertEqual(result["status"], "held")
            self.assertEqual(result["automaticRetries"], 0)
            self.assertEqual(h.release.call_count, 1)
            self.assertFalse((h.root / "attempt/condition-2-resource-samples.jsonl").exists())

    def test_each_arm_gets_fresh_preparation_and_original_sequence_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            h, clock = Harness(Path(tmp), preparation=True, failed_arm=None), Clock()
            result = h.run(resource_sampler=lambda remaining: HEALTHY, monotonic=clock.monotonic,
                           sleep=clock.sleep, utc_clock=clock.utc)
            self.assertEqual(result["status"], "completed-awaiting-reading")
            self.assertEqual(len(h.arm_calls), 3)
            self.assertEqual([r["sampleCount"] for r in result["resourcePreparations"]], [3, 3, 3])
            self.assertEqual([r["arm"] for r in result["arms"]], protocol()["arms"])
            self.assertEqual(h.release.call_count, 3)
            self.assertEqual(clock.now, 60)

    def test_binary_change_during_preparation_prevents_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            h, clock = Harness(Path(tmp), preparation=True), Clock()
            def sample(remaining):
                h.binary.write_text("changed after freeze")
                return HEALTHY
            result = h.run(resource_sampler=sample, monotonic=clock.monotonic,
                           sleep=clock.sleep, utc_clock=clock.utc)
            self.assertEqual(h.calls, [])
            self.assertIn("Pilot binary changed", result["error"])

    def test_protocol_change_during_preparation_prevents_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            h, clock = Harness(Path(tmp), preparation=True), Clock()
            def sample(remaining):
                h.selected.write_text(json.dumps(protocol()))
                return HEALTHY
            result = h.run(resource_sampler=sample, monotonic=clock.monotonic,
                           sleep=clock.sleep, utc_clock=clock.utc)
            self.assertEqual(h.calls, [])
            self.assertIn("Pilot protocol changed", result["error"])

    def test_visible_matching_command_observation_does_not_change_stop_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp), failed_arm=None)
            h.release.return_value = {"status": "matching_process_visible", "synthetic": True}
            result = h.run()
            self.assertEqual(result["status"], "completed-awaiting-reading")
            self.assertEqual(h.release.call_count, 3)


class WorkerObservationTests(unittest.TestCase):
    def test_exact_command_matches_are_observed_without_process_action(self):
        reply = SimpleNamespace(returncode=0, stdout=" 10 1 /python -B /owned/worker.py\n 11 1 /python -B /other/worker.py\n", stderr="")
        with patch.object(pilot.subprocess, "run", return_value=reply) as dispatch:
            result = pilot.observe_worker_release("/python", "/owned/worker.py")
        self.assertEqual(result["status"], "matching_process_visible")
        self.assertEqual(result["matchingProcesses"], [{"pid": 10, "parentPid": 1}])
        self.assertIn("does not independently prove ownership", result["limitation"])
        self.assertEqual(dispatch.call_args.args[0], ["/bin/ps", "-ww", "-axo", "pid=,ppid=,command="])


if __name__ == "__main__":
    unittest.main()
