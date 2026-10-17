"""Synthetic cohort receipts and fake clocks/processes; no model or host probes."""
from contextlib import ExitStack
import copy
import json
from pathlib import Path
import signal
import subprocess
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_activation_cohort as cohort


def protocol():
    return {"schema": "activation-cohort-pilot-v1", "id": "synthetic-cohort", "arms": list(cohort.ARMS),
            "seed": 20261015, "temperature": 0.0, "requestDeadlineSeconds": 180,
            "cohortDeadlineSeconds": 900, "stepsBetweenObservations": 10,
            "journalEveryObservations": 2, "outputTokens": 1024,
            "observations": ["Synthetic observation"] * 12, "readingQuestions": ["Read the complete sequence"],
            "resourcePreparation": dict(cohort.RESOURCE_PREPARATION), "memoryPolicy": dict(cohort.MEMORY_POLICY),
            "residentWorkerGuard": copy.deepcopy(cohort.RESIDENT_WORKER_GUARD),
            "interpretation": "Synthetic fixture only", "stoppingRule": "Stop at first failure",
            "predecessors": ["synthetic-earlier-study"], "allocationRationale": "Prospectively fixed order"}


class Clock:
    def __init__(self):
        self.now, self.sleeps = 0.0, []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds

    def utc(self):
        return f"synthetic-{self.now}"


HEALTHY = {"pressure": 1, "freePercent": 25}
UNHEALTHY = {"pressure": 2, "freePercent": 70}


class ProtocolTests(unittest.TestCase):
    def test_valid_and_repository_protocols(self):
        value = protocol()
        self.assertEqual(cohort.validate_protocol(value), value)
        real = cohort.read(cohort.ROOT / "shared/reservoir-scope/activation-cohort-20261016.json")
        self.assertEqual(cohort.validate_protocol(real), real)

    def test_reject_changed_bounds_order_unknown_fields_and_coerced_types(self):
        edits = [("schema", "activation-pilot-v1"), ("arms", list(reversed(cohort.ARMS))),
                 ("cohortDeadlineSeconds", 901), ("cohortDeadlineSeconds", 900.0),
                 ("temperature", 0.1), ("requestDeadlineSeconds", 181), ("outputTokens", 1024.0),
                 ("extra", 1), ("seed", True), ("observations", ["one"])]
        for key, value in edits:
            with self.subTest(key=key, value=value):
                candidate = protocol()
                candidate[key] = value
                with self.assertRaises(ValueError):
                    cohort.validate_protocol(candidate)
        for group, key, value in [
                ("resourcePreparation", "maximumSeconds", 601),
                ("resourcePreparation", "requiredPressureLevel", 2),
                ("resourcePreparation", "requiredPressureLevel", True),
                ("resourcePreparation", "minimumFreePercent", 24),
                ("resourcePreparation", "consecutiveHealthySamples", 2),
                ("memoryPolicy", "mlxCacheLimitBytes", 67108865),
                ("memoryPolicy", "freshProseHistoryPerCondition", 1),
                ("residentWorkerGuard", "allowedPressureLevels", [1, 2, 4]),
                ("residentWorkerGuard", "allowedPressureLevels", [True, 2]),
                ("residentWorkerGuard", "stopOnCriticalOrUnknown", 1)]:
            with self.subTest(group=group, key=key):
                candidate = protocol()
                candidate[group][key] = value
                with self.assertRaises(ValueError):
                    cohort.validate_protocol(candidate)


class PreparationTests(unittest.TestCase):
    def prepare(self, path, sampler, clock):
        return cohort.prepare_resources(path, cohort.RESOURCE_PREPARATION, sampler=sampler,
                                        monotonic=clock.monotonic, sleep=clock.sleep, utc_clock=clock.utc)

    def test_reset_and_unknown_dont_admit(self):
        sampler = Mock(side_effect=[HEALTHY, HEALTHY, UNHEALTHY, HEALTHY,
                                    {"pressure": None, "freePercent": 80}, HEALTHY, HEALTHY, HEALTHY])
        clock = Clock()
        with tempfile.TemporaryDirectory() as tmp:
            result = self.prepare(Path(tmp), sampler, clock)
            rows = [json.loads(x) for x in (Path(tmp) / "resource-samples.jsonl").read_text().splitlines()]
        self.assertTrue(result["ready"])
        self.assertEqual(result["elapsedSeconds"], 70)
        self.assertEqual([x["consecutiveHealthySamples"] for x in rows], [1, 2, 0, 1, 0, 1, 2, 3])
        self.assertTrue(all(x["sampledAtUtc"] and x["completedAtUtc"] for x in rows))

    def test_exact600second_timeout_without_waiting(self):
        clock, sampler = Clock(), Mock(return_value=UNHEALTHY)
        with tempfile.TemporaryDirectory() as tmp:
            result = self.prepare(Path(tmp), sampler, clock)
        self.assertFalse(result["ready"])
        self.assertEqual((result["sampleCount"], result["elapsedSeconds"]), (60, 600))
        self.assertEqual(clock.sleeps, [10] * 60)
        self.assertTrue(all(0 < call.args[0] <= 600 for call in sampler.call_args_list))

    def test_third_healthy_sample_finishing_late_does_not_admit(self):
        clock, calls = Clock(), []
        def sampler(remaining):
            calls.append(remaining)
            if len(calls) == 3:
                clock.now += remaining + 1
            return HEALTHY
        with tempfile.TemporaryDirectory() as tmp:
            result = self.prepare(Path(tmp), sampler, clock)
        self.assertFalse(result["ready"])
        self.assertEqual(result["sampleCount"], 3)


@unittest.skipUnless(hasattr(signal, "SIGKILL"), "POSIX process-group escalation for the macOS cohort")
class OwnedProcessTests(unittest.TestCase):
    def run_process(self, waits, signal_error=None):
        process = Mock(pid=424242)
        process.wait.side_effect = waits
        popen = Mock(return_value=process)
        kill_group = Mock(side_effect=signal_error)
        result = cohort.run_owned_cohort(["synthetic-binary", "--activation-cohort", "synthetic-config"],
                                          stdout="synthetic-out", stderr="synthetic-err",
                                          popen_factory=popen, kill_group=kill_group)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        self.assertTrue(all(call.args[0] == process.pid for call in kill_group.call_args_list))
        return result, process, kill_group

    def test_success_reaps_without_any_signal(self):
        result, process, signals = self.run_process([0])
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.cohort_lifecycle["reaped"])
        self.assertIsNone(result.cohort_lifecycle["terminationReason"])
        self.assertEqual(process.wait.call_args.kwargs["timeout"], 930)
        signals.assert_not_called()

    def test_interrupt_sends_term_only_to_new_group_then_reaps(self):
        result, process, signals = self.run_process([KeyboardInterrupt(), 1])
        self.assertEqual(result.cohort_lifecycle["terminationReason"], "interrupted")
        self.assertTrue(result.cohort_lifecycle["reaped"])
        self.assertEqual([c.args for c in signals.call_args_list], [(424242, signal.SIGTERM)])
        self.assertEqual([c.kwargs["timeout"] for c in process.wait.call_args_list], [930, 10])

    def test_watchdog_escalates_term_to_kill_then_reaps_without_retry(self):
        expired = subprocess.TimeoutExpired("synthetic", 1)
        result, process, signals = self.run_process([expired, expired, -9])
        self.assertEqual(result.cohort_lifecycle["terminationReason"], "outer_watchdog_expired")
        self.assertTrue(result.cohort_lifecycle["reaped"])
        self.assertEqual([c.args for c in signals.call_args_list], [(424242, signal.SIGTERM), (424242, signal.SIGKILL)])
        self.assertEqual([c.kwargs["timeout"] for c in process.wait.call_args_list], [930, 10, 10])

    def test_second_interrupt_still_escalates_and_absent_group_is_retained(self):
        result, _, signals = self.run_process([KeyboardInterrupt(), KeyboardInterrupt(), -9])
        self.assertTrue(result.cohort_lifecycle["reaped"])
        self.assertEqual(signals.call_count, 2)
        result, _, _ = self.run_process([KeyboardInterrupt(), -15], ProcessLookupError())
        self.assertFalse(result.cohort_lifecycle["signals"][0]["sent"])
        self.assertTrue(result.cohort_lifecycle["reaped"])


class Harness:
    def __init__(self, root, completed=3, failure=None):
        self.root, self.completed, self.failure = root, completed, failure
        self.app = root / "app"
        self.app.mkdir()
        (self.app / "activation-requirements.lock").touch()
        self.protocol_path = root / "protocol.json"
        cohort.save(self.protocol_path, protocol())
        self.binary = root / "binary"
        self.binary.write_text("synthetic executable")
        self.qualification = root / "qualification"
        self.qualification.mkdir()
        self.manifest = {"sha256": "M", "workerSources": []}
        self.calibration = {"sha256": "C"}
        plan = {"manifest": self.manifest}
        cohort.save(self.qualification / "plan.json", plan)
        cohort.save(self.qualification / "initialization.json", {
            "manifest": self.manifest, "calibration": self.calibration,
            "memoryPolicy": cohort.WORKER_MEMORY_POLICY})
        cohort.save(self.qualification / "calibration.json", self.calibration)
        cohort.save(self.qualification / "result.json", {
            "passed": True, "status": "passed", "checks": dict.fromkeys(cohort.QUALIFICATION_CHECKS, True),
            "planSha256": cohort.canonical_hash(plan),
            "planFileSha256": cohort.sha256_file(self.qualification / "plan.json"),
            "calibrationSha256": "C", "calibrationFileSha256": cohort.sha256_file(self.qualification / "calibration.json"),
            "modelManifestSha256": "M", "workerSources": [], "memoryPolicy": cohort.WORKER_MEMORY_POLICY})
        self.args = SimpleNamespace(output=str(root / "attempt"), binary=str(self.binary), model="unused",
                                    qualification=str(self.qualification), protocol=str(self.protocol_path))
        self.clock = Clock()
        self.calls, self.cohort_calls = [], []
        self.release = Mock(return_value={"status": "no_matching_process_visible", "synthetic": True})

    def update_json(self, path, callback):
        value = cohort.read(path)
        callback(value)
        path.write_text(json.dumps(value))

    def dispatch(self, command, **kwargs):
        self.calls.append(command)
        if "--verify-activation" in command:
            number = int(Path(command[-1]).name.removeprefix("condition-"))
            return SimpleNamespace(returncode=1 if self.failure == "verification" and number == 1 else 0,
                                   stdout=json.dumps({"status": "passed", "modelsContacted": False,
                                                      "sessionId": f"s{number}", "steps": 121, "journals": 6}), stderr="")
        self.cohort_calls.append(command)
        if self.failure == "launch":
            raise OSError("synthetic launch failure")
        directory = Path(command[command.index("--output") + 1])
        directory.mkdir()
        configs = cohort.read(Path(command[command.index("--activation-cohort") + 1]))
        self.assert_calibration = cohort.read(Path(command[command.index("--activation-calibration") + 1]))
        snapshots = []
        for index, config in enumerate(configs):
            session = directory / f"condition-{index+1}"
            session.mkdir()
            complete = index < self.completed
            if complete:
                cohort.save(session / "calibration.json", self.calibration)
                cohort.save(session / "model-manifest.json", self.manifest)
            snapshots.append({"sessionId": f"s{index+1}", "directory": str(session), "config": config,
                              "status": "completed" if complete else "failed" if index == self.completed else "paused",
                              "step": 121 if complete else 0, "observationIndex": 12 if complete else 0,
                              "journalCount": 6 if complete else 0, "calibrationSha256": "C", "modelManifestSha256": "M",
                              "journals": [{"text": f"Synthetic passage {j}", "observedStep": j*20} for j in range(1, 7)] if complete else []})
        reply = {"schema": "activation-cohort-result-v1", "cohortDirectory": str(directory),
                 "status": "completed" if self.completed == 3 else "failed", "sessions": snapshots,
                 "modelsLoaded": 1 if self.completed else 0, "workerReleased": self.failure != "not_reaped",
                 "diagnostic": None if self.completed == 3 else "synthetic stop"}
        if self.failure == "wrong_config":
            snapshots[0]["config"]["seed"] += 1
        if self.failure == "wrong_boundary":
            snapshots[0]["step"] = 120
        if self.failure == "wrong_calibration":
            (directory / "condition-1/calibration.json").write_text('{"sha256":"wrong"}')
        if self.failure == "completed_after_failure":
            snapshots[0]["status"] = "failed"
        if self.failure == "interrupted_stdout":
            cohort.save(directory / "cohort-result.json", reply)
            kwargs["stdout"].write('{"schema":')
            return SimpleNamespace(returncode=1, cohort_lifecycle={"terminationReason": "interrupted", "reaped": True})
        if self.failure == "inconsistent_stdout":
            retained = copy.deepcopy(reply)
            retained["diagnostic"] = "different retained receipt"
            cohort.save(directory / "cohort-result.json", retained)
        if self.failure == "malformed_stdout":
            kwargs["stdout"].write("not JSON")
        else:
            json.dump(reply, kwargs["stdout"])
        kwargs["stderr"].write("synthetic stderr retained\n")
        return SimpleNamespace(returncode=0 if self.completed == 3 else 1)

    def run(self, sampler=None, inspector=None):
        with ExitStack() as stack:
            stack.enter_context(patch.object(cohort, "APP", self.app))
            inspect = stack.enter_context(patch.object(cohort, "inspect_model", side_effect=inspector,
                                                       return_value={"manifest": self.manifest, "modelPath": str(self.root / "model")}))
            stack.enter_context(patch.object(cohort, "validate_calibration", return_value=self.calibration))
            result = cohort.run(self.args, resource_sampler=sampler or (lambda remaining: HEALTHY),
                                monotonic=self.clock.monotonic, sleep=self.clock.sleep, utc_clock=self.clock.utc,
                                release_observer=self.release, process_runner=self.dispatch)
            self.inspect_calls = inspect.call_count
            return result


class RunnerTests(unittest.TestCase):
    def test_success_has_one_dispatch_one_preparation_exact_configs_and_blind_packets(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp))
            result = h.run()
            self.assertEqual((result["status"], result["scope"]), ("completed-awaiting-reading", "complete"))
            self.assertEqual((len(h.cohort_calls), h.release.call_count, h.inspect_calls), (1, 1, 2))
            self.assertEqual(len(h.calls), 4)
            self.assertEqual(result["resourcePreparation"]["sampleCount"], 3)
            self.assertEqual(h.clock.now, 20)
            self.assertEqual(h.assert_calibration, h.calibration)
            self.assertEqual(result["verifiedCompletedSessions"], 3)
            frozen = cohort.read(h.root / "attempt/frozen-plan.json")
            self.assertEqual(frozen["protocolSha256"], cohort.sha256_file(h.protocol_path))
            self.assertEqual(frozen["runnerSha256"], cohort.sha256_file(Path(cohort.__file__)))
            self.assertEqual(frozen["helperRunnerSha256"], cohort.sha256_file(Path(cohort.prior.__file__)))
            self.assertEqual((h.root / "attempt/protocol.json").read_bytes(), h.protocol_path.read_bytes())
            for index, arm in enumerate(cohort.ARMS):
                self.assertEqual(result["arms"][index]["arm"], arm)
                packet = cohort.read(h.root / f"attempt/reading-{chr(65+index)}.json")
                self.assertEqual(set(packet), {"label", "questions", "entries"})
                self.assertEqual(len(packet["entries"]), 6)

    def test_preparation_timeout_dispatches_nothing_and_retains_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp))
            result = h.run(sampler=lambda remaining: UNHEALTHY)
            self.assertEqual((result["cohortDispatches"], result["scope"]), (0, "none"))
            self.assertEqual(h.calls, [])
            self.assertEqual(h.release.call_count, 0)
            self.assertEqual(result["resourcePreparation"]["elapsedSeconds"], 600)
            self.assertTrue((h.root / "attempt/frozen-plan.json").exists())
            self.assertFalse((h.root / "attempt/dispatch.json").exists())

    def test_actual_admission_refusal_after_healthy_preparation_never_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp), completed=0)
            result = h.run()
            self.assertEqual((len(h.cohort_calls), len(h.calls), h.release.call_count), (1, 1, 1))
            self.assertEqual((result["status"], result["scope"], result["modelsLoaded"]), ("held", "none", 0))
            self.assertEqual(result["automaticRetries"], 0)
            self.assertFalse((h.root / "attempt/reading-A.json").exists())

    def test_nonzero_failure_retains_verified_completed_prefix_and_no_later_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp), completed=1)
            result = h.run()
            self.assertEqual((result["status"], result["scope"], result["verifiedCompletedSessions"]), ("held", "partial", 1))
            self.assertEqual((len(h.cohort_calls), len(h.calls)), (1, 2))
            self.assertEqual([a["status"] for a in result["arms"]], ["completed", "failed", "paused"])
            self.assertTrue((h.root / "attempt/reading-A.json").exists())
            self.assertFalse((h.root / "attempt/reading-B.json").exists())
            self.assertTrue((h.root / "attempt/cohort-stderr.txt").exists())

    def test_interrupted_stdout_uses_retained_result_for_completed_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp), completed=1, failure="interrupted_stdout")
            result = h.run()
            self.assertEqual((result["status"], result["scope"], result["verifiedCompletedSessions"]), ("held", "partial", 1))
            self.assertEqual(result["cohortResultSource"], "cohort/cohort-result.json")
            self.assertEqual(result["processLifecycle"]["terminationReason"], "interrupted")
            self.assertEqual(len(h.cohort_calls), 1)
            self.assertTrue((h.root / "attempt/reading-A.json").exists())
            self.assertFalse((h.root / "attempt/reading-B.json").exists())

    def test_successful_sessions_without_confirmed_worker_release_remain_held(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp), failure="not_reaped")
            result = h.run()
            self.assertEqual((result["status"], result["scope"], result["verifiedCompletedSessions"]), ("held", "partial", 3))
            self.assertIs(result["workerReleased"], False)
            self.assertEqual(len(h.cohort_calls), 1)
            self.assertTrue((h.root / "attempt/reading-C.json").exists())

    def test_interrupt_during_preparation_retains_a_held_result_without_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp))
            result = h.run(sampler=Mock(side_effect=KeyboardInterrupt()))
            self.assertEqual(result["status"], "held")
            self.assertIn("KeyboardInterrupt", result["error"])
            self.assertEqual(h.calls, [])
            self.assertTrue((h.root / "attempt/result.json").exists())

    def test_invalid_or_failed_qualification_never_prepares_or_dispatches(self):
        mutations = [lambda r: r.update(passed=False), lambda r: r["checks"].update(logitParity=False),
                     lambda r: r["checks"].pop("crossArmGenerationIsolation"),
                     lambda r: r.update(planSha256="wrong"), lambda r: r.update(planFileSha256="wrong"),
                     lambda r: r.update(modelManifestSha256="wrong"), lambda r: r.update(workerSources=[{}]),
                     lambda r: r.update(calibrationSha256="wrong"), lambda r: r.update(calibrationFileSha256="wrong"),
                     lambda r: r["memoryPolicy"].update(freeCacheLimitBytes=0),
                     lambda r: r["memoryPolicy"].update(memoryLimitChanged=0)]
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                h = Harness(Path(tmp))
                h.update_json(h.qualification / "result.json", mutation)
                sampler = Mock(side_effect=AssertionError("must not prepare"))
                result = h.run(sampler=sampler)
                sampler.assert_not_called()
                self.assertEqual(h.calls, [])
                self.assertEqual(result["status"], "held")
                self.assertTrue((h.root / "attempt/result.json").exists())

    def test_dependency_lock_mismatch_never_dispatches(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp))
            (h.app / "activation-requirements.lock").write_text("synthetic-package==1.0\n")
            with patch.object(cohort.importlib.metadata, "version", return_value="2.0"):
                result = h.run()
            self.assertIn("Runtime differs", result["error"])
            self.assertEqual(h.calls, [])

    def test_source_change_during_preparation_never_dispatches(self):
        for changed in ("binary", "protocol", "calibration", "configs"):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as tmp:
                h = Harness(Path(tmp))
                paths = {"binary": h.binary, "protocol": h.protocol_path,
                         "calibration": h.qualification / "calibration.json",
                         "configs": h.root / "attempt/cohort-configs.json"}
                def sampler(remaining):
                    paths[changed].write_text("changed during preparation")
                    return HEALTHY
                result = h.run(sampler=sampler)
                self.assertIn("Frozen source changed", result["error"])
                self.assertEqual(h.calls, [])

    def test_current_manifest_is_reinspected_after_preparation(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp))
            result = h.run(inspector=[{"manifest": h.manifest, "modelPath": str(h.root / "model")},
                                      {"manifest": {"sha256": "changed", "workerSources": []}, "modelPath": str(h.root / "model")}])
            self.assertIn("identity changed", result["error"])
            self.assertEqual(h.calls, [])

    def test_bad_retained_result_or_verification_does_not_get_a_packet_or_retry(self):
        for failure in ("wrong_config", "wrong_boundary", "wrong_calibration", "verification", "malformed_stdout", "completed_after_failure", "launch", "inconsistent_stdout"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                h = Harness(Path(tmp), failure=failure)
                result = h.run()
                self.assertEqual(result["status"], "held")
                self.assertEqual(len(h.cohort_calls), 1)
                self.assertEqual(h.release.call_count, 1)
                self.assertFalse((h.root / "attempt/reading-A.json").exists())
                self.assertTrue((h.root / "attempt/cohort-stdout.json").exists())
                self.assertTrue((h.root / "attempt/worker-release-observation.json").exists())

    def test_existing_output_is_never_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Harness(Path(tmp))
            (h.root / "attempt").mkdir()
            with self.assertRaises(FileExistsError):
                h.run()
            self.assertEqual(h.calls, [])


if __name__ == "__main__":
    unittest.main()
