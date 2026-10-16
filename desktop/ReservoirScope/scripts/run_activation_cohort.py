#!/usr/bin/env python3
"""Run one prospectively frozen, bounded cohort with one admitted model worker.

Use the qualified environment with ``python -B``. Preparation reads pressure only;
Rust owns model admission, the 900-second deadline, child termination and reaping.
No retry, restart, extension, system purge or live-system endpoint is used here.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import run_activation_pilot as prior

APP, ROOT = prior.APP, prior.ROOT
inspect_model = prior.inspect_model
validate_calibration = prior.validate_calibration
canonical_hash, sha256_file = prior.canonical_hash, prior.sha256_file
save, read, utc_now = prior.save, prior.read, prior.utc_now

ARMS = ["no_steering", "recurrent", "decaying_trace"]
RESOURCE_PREPARATION = {"maximumSeconds": 600, "pollSeconds": 10,
                        "consecutiveHealthySamples": 3, "minimumFreePercent": 25,
                        "requiredPressureLevel": 1}
MEMORY_POLICY = {"mlxCacheLimitBytes": 64 * 1024 * 1024, "sharedModelLoads": 1,
                 "freshNumericalStatePerCondition": True, "freshProseHistoryPerCondition": True,
                 "freshKVCachePerOperation": True}
WORKER_MEMORY_POLICY = {"schemaVersion": "activation-mlx-memory-policy/1", "freeCacheLimitBytes": 67108864,
                        "clearEveryGeneratedContentTokens": 64, "scope": "owned-worker-MLX-allocator-only",
                        "memoryLimitChanged": False, "wiredLimitChanged": False}
RESIDENT_WORKER_GUARD = {"allowedPressureLevels": [1, 2], "stopOnCriticalOrUnknown": True,
                         "scope": "Before each request and condition boundary while the sole admitted worker remains resident; never authorizes another model load."}
QUALIFICATION_CHECKS = {"boundedCaptures", "cacheOffsetParity", "clearedSteering", "independentProbeIsolation",
                        "logitParity", "noStaleSteering", "perPositionNorms", "quietZeroSamples",
                        "samePassContentToken", "zeroAdditionBitwiseParity", "configuredFreeCacheLimit",
                        "perOperationMemoryCleanup", "crossArmGenerationIsolation", "crossArmLogitTokenCaptureIsolation"}
OUTER_WATCHDOG_SECONDS = 930  # Rust's 900 seconds plus receipt/termination allowance.
TERMINATION_GRACE_SECONDS = 10


def run_owned_cohort(command, *, stdout, stderr, check=False, popen_factory=None, kill_group=None):
    """Only the freshly created process group can receive termination signals.

    The Rust bound stops work at 900 seconds. This outer bound handles a stuck or
    interrupted supervisor and gives it a bounded opportunity to retain receipts.
    """
    if check:
        raise ValueError("Cohort failure must be returned with its evidence")
    popen_factory, kill_group = popen_factory or subprocess.Popen, kill_group or os.killpg
    process = popen_factory(command, stdout=stdout, stderr=stderr, start_new_session=True)
    # start_new_session creates a session/process group whose ID is this child PID.
    lifecycle = {"pid": process.pid, "processGroupId": process.pid, "startNewSession": True,
                 "outerWatchdogSeconds": OUTER_WATCHDOG_SECONDS, "terminationGraceSeconds": TERMINATION_GRACE_SECONDS,
                 "terminationReason": None, "signals": [], "reaped": False}
    try:
        code = process.wait(timeout=OUTER_WATCHDOG_SECONDS)
        lifecycle["reaped"] = True
    except (KeyboardInterrupt, subprocess.TimeoutExpired) as exc:
        lifecycle["terminationReason"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "outer_watchdog_expired"
        code = None
        for sig in (signal.SIGTERM, signal.SIGKILL):
            evidence = {"processGroupId": process.pid, "signal": sig.name}
            try:
                kill_group(process.pid, sig)
                evidence["sent"] = True
            except ProcessLookupError:
                evidence["sent"] = False
                evidence["reason"] = "owned_process_group_already_absent"
            except OSError as signal_error:
                evidence["sent"] = False
                evidence["error"] = f"{type(signal_error).__name__}: {signal_error}"
            lifecycle["signals"].append(evidence)
            try:
                code = process.wait(timeout=TERMINATION_GRACE_SECONDS)
                lifecycle["reaped"] = True
                break
            except (KeyboardInterrupt, subprocess.TimeoutExpired) as wait_error:
                evidence["waitError"] = type(wait_error).__name__
        if not lifecycle["reaped"]:
            lifecycle["cleanupError"] = "Owned child did not reap within the bounded signal escalation"
    return SimpleNamespace(returncode=code, cohort_lifecycle=lifecycle)


def validate_protocol(value):
    if not isinstance(value, dict) or value.get("schema") != "activation-cohort-pilot-v1":
        raise ValueError("Unsupported activation cohort protocol schema")
    extra = {"cohortDeadlineSeconds", "memoryPolicy", "predecessors", "allocationRationale", "residentWorkerGuard"}
    # Reuse unchanged validation of observations, request bounds and reading fields.
    common = {k: v for k, v in value.items() if k not in extra | {"resourcePreparation"}}
    common["schema"] = "activation-pilot-v1"
    prior.validate_protocol(common)
    if value["arms"] != ARMS:
        raise ValueError("Cohort order must be no_steering, recurrent, decaying_trace")
    if type(value.get("cohortDeadlineSeconds")) is not int or value["cohortDeadlineSeconds"] != 900:
        raise ValueError("Cohort deadline must be 900 seconds")
    preparation = value.get("resourcePreparation")
    if (preparation != RESOURCE_PREPARATION or not isinstance(preparation, dict)
            or any(type(v) is not int for v in preparation.values())):
        raise ValueError("Cohort preparation must use the approved 600/10/3/25/1 bounds")
    policy = value.get("memoryPolicy")
    if (policy != MEMORY_POLICY or not isinstance(policy, dict)
            or any(type(policy[k]) is not type(v) for k, v in MEMORY_POLICY.items())):
        raise ValueError("Cohort memory policy differs from the approved one-load/64-MiB/fresh-state policy")
    guard = value.get("residentWorkerGuard")
    if (guard != RESIDENT_WORKER_GUARD or not isinstance(guard, dict)
            or guard["stopOnCriticalOrUnknown"] is not True
            or any(type(x) is not int for x in guard["allowedPressureLevels"])):
        raise ValueError("Cohort resident-worker guard differs from the approved critical/unknown stop policy")
    if not isinstance(value.get("allocationRationale"), str) or not value["allocationRationale"].strip():
        raise ValueError("Cohort requires an allocation rationale")
    predecessors = value.get("predecessors")
    if not isinstance(predecessors, list) or not predecessors or any(not isinstance(x, str) or not x.strip() for x in predecessors):
        raise ValueError("Cohort requires predecessor identifiers")
    return value


def save_bytes(path, data):
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def prepare_resources(output, preparation, *, sampler=None, monotonic=None, sleep=None, utc_clock=None):
    sampler, monotonic = sampler or prior.sample_resources, monotonic or time.monotonic
    sleep, utc_clock = sleep or time.sleep, utc_clock or utc_now
    start = monotonic()
    deadline = start + preparation["maximumSeconds"]
    streak = count = 0
    summary = {"schema": "activation-cohort-resource-preparation-v1", "preparation": preparation,
               "startedAtUtc": utc_clock(), "ready": False, "samplesFile": "resource-samples.jsonl"}
    with (output / summary["samplesFile"]).open("x", encoding="utf-8") as stream:
        while monotonic() < deadline:
            sampled_at = utc_clock()
            sample = sampler(max(0.0, deadline - monotonic()))
            completed = monotonic()
            healthy = (type(sample.get("pressure")) is int
                       and sample["pressure"] == preparation["requiredPressureLevel"]
                       and type(sample.get("freePercent")) is int
                       and preparation["minimumFreePercent"] <= sample["freePercent"] <= 100)
            streak = streak + 1 if healthy else 0
            count += 1
            row = {"sample": count, "sampledAtUtc": sampled_at, "completedAtUtc": utc_clock(),
                   "elapsedSeconds": completed-start, "healthy": healthy,
                   "consecutiveHealthySamples": streak, "resource": sample}
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            if completed <= deadline and streak >= preparation["consecutiveHealthySamples"]:
                summary["ready"] = True
                break
            remaining = deadline - monotonic()
            if remaining > 0:
                sleep(min(preparation["pollSeconds"], remaining))
    summary.update({"finishedAtUtc": utc_clock(), "elapsedSeconds": monotonic()-start,
                    "sampleCount": count, "consecutiveHealthySamples": streak,
                    "reason": "three_consecutive_healthy_samples" if summary["ready"] else "preparation_deadline_reached"})
    save(output / "resource-preparation.json", summary)
    return summary


def validate_runtime(lock):
    for line in lock.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        package, version = line.split("==", 1)
        if importlib.metadata.version(package) != version:
            raise ValueError(f"Runtime differs from frozen dependency lock: {package}")


def qualified_identity(qualification, model):
    report = read(qualification / "result.json")
    plan = read(qualification / "plan.json")
    initialization = read(qualification / "initialization.json")
    checks = report.get("checks")
    if (report.get("passed") is not True or report.get("status") != "passed"
            or not isinstance(checks, dict) or not checks or not all(v is True for v in checks.values())):
        raise ValueError("Real-model qualification has not passed")
    if not QUALIFICATION_CHECKS.issubset(checks):
        raise ValueError("Qualification lacks the required memory and cross-arm isolation checks")
    policy = report.get("memoryPolicy")
    if (not isinstance(policy, dict) or initialization.get("memoryPolicy") != policy
            or any(policy.get(k) != v or type(policy.get(k)) is not type(v)
                   for k, v in WORKER_MEMORY_POLICY.items())):
        raise ValueError("Qualification memory policy differs from the cohort policy")
    if report["planSha256"] != canonical_hash(plan) or report["planFileSha256"] != sha256_file(qualification / "plan.json"):
        raise ValueError("Qualification plan identity differs")
    inspected = inspect_model(model)
    manifest = inspected["manifest"]
    if (manifest != plan["manifest"] or manifest != initialization["manifest"]
            or report.get("modelManifestSha256") != manifest["sha256"]
            or report.get("workerSources") != manifest["workerSources"]):
        raise ValueError("Qualified model, worker, or runtime identity changed")
    calibration = validate_calibration(initialization["calibration"], manifest["sha256"])
    if (calibration != read(qualification / "calibration.json")
            or calibration["sha256"] != report["calibrationSha256"]
            or sha256_file(qualification / "calibration.json") != report["calibrationFileSha256"]):
        raise ValueError("Calibration differs from the qualified artifact")
    validate_runtime(APP / "activation-requirements.lock")
    return inspected, calibration


def source_receipt(path):
    path = path.resolve(strict=True)
    return {"path": str(path), "sha256": sha256_file(path)}


def check_sources(sources):
    for item in sources:
        if sha256_file(Path(item["path"])) != item["sha256"]:
            raise ValueError(f"Frozen source changed before dispatch: {item['path']}")


def collect_sessions(reply, configs, output, cohort_directory, calibration, manifest, binary, protocol, dispatch, result):
    if (reply.get("schema") != "activation-cohort-result-v1"
            or reply.get("status") not in {"completed", "failed"}
            or type(reply.get("modelsLoaded")) is not int or reply["modelsLoaded"] not in {0, 1}):
        raise ValueError("Cohort CLI returned an invalid result envelope")
    if Path(reply["cohortDirectory"]).resolve() != cohort_directory.resolve():
        raise ValueError("Cohort CLI returned a different output directory")
    snapshots = reply.get("sessions")
    if not isinstance(snapshots, list) or len(snapshots) != 3:
        raise ValueError("Cohort CLI must retain exactly three session snapshots")
    stopped = False
    directories = set()
    result["modelsLoaded"] = reply["modelsLoaded"]
    result["workerReleased"] = reply.get("workerReleased")
    result["cohortStatus"] = reply["status"]
    result["cohortDiagnostic"] = reply.get("diagnostic")
    for index, (snapshot, config) in enumerate(zip(snapshots, configs)):
        if snapshot.get("config") != config:
            raise ValueError("Retained session config differs from its frozen arm")
        directory = Path(snapshot["directory"]).resolve(strict=True)
        if not directory.is_relative_to(cohort_directory.resolve()) or directory in directories:
            raise ValueError("Session directory escapes or duplicates the cohort directory")
        directories.add(directory)
        arm = {"arm": config["arm"], "sessionId": snapshot["sessionId"], "directory": str(directory),
               "status": snapshot["status"], "journalCount": snapshot["journalCount"], "step": snapshot["step"],
               "verified": False}
        result["arms"].append(arm)
        if snapshot["status"] != "completed":
            stopped = True
            continue
        if stopped:
            raise ValueError("Completed session appears after a stopped condition")
        if (reply["modelsLoaded"] != 1 or snapshot["journalCount"] != 6 or snapshot["step"] != 121
                or snapshot.get("observationIndex") != 12 or len(snapshot["journals"]) != 6):
            raise ValueError("Completed condition did not reach the frozen boundary")
        if (snapshot.get("calibrationSha256") != calibration["sha256"]
                or snapshot.get("modelManifestSha256") != manifest["sha256"]
                or read(directory / "calibration.json") != calibration
                or read(directory / "model-manifest.json") != manifest):
            raise ValueError("Completed condition did not use the frozen model and calibration")
        verification = dispatch([str(binary), "--verify-activation", str(directory)],
                                capture_output=True, text=True, check=False, timeout=30)
        verification_file = f"condition-{index+1}-verification.json"
        save(output / verification_file, {"returnCode": verification.returncode,
                                          "stdout": verification.stdout, "stderr": verification.stderr})
        arm["verificationFile"] = verification_file
        if verification.returncode:
            raise RuntimeError("Completed condition failed offline replay")
        verified = json.loads(verification.stdout)
        if (verified.get("status") != "passed" or verified.get("modelsContacted") is not False
                or verified.get("sessionId") != snapshot["sessionId"]
                or verified.get("steps") != 121 or verified.get("journals") != 6):
            raise ValueError("Offline verification did not confirm the completed session")
        arm["verified"] = True
        packet_file = f"reading-{chr(65+index)}.json"
        save(output / packet_file, {
            "label": f"Reading {chr(65+index)}", "questions": protocol["readingQuestions"],
            "entries": [{"number": n+1, "text": journal["text"], "observedStep": journal["observedStep"]}
                        for n, journal in enumerate(snapshot["journals"])],
        })
        arm["readingPacketFile"] = packet_file


def run(args, *, resource_sampler=None, monotonic=None, sleep=None, utc_clock=None,
        release_observer=None, process_runner=None, cohort_runner=None):
    dispatch = process_runner or subprocess.run
    cohort_dispatch = cohort_runner or process_runner or run_owned_cohort
    clock = utc_clock or utc_now
    output = Path(args.output).expanduser().absolute()
    output.mkdir(parents=True, exist_ok=False)
    result = {"schema": "activation-cohort-pilot-result-v1", "status": "held", "scope": "none",
              "startedAtUtc": clock(), "arms": [], "automaticRetries": 0,
              "cohortDispatches": 0, "readingComplete": False}
    try:
        protocol_path = Path(args.protocol).expanduser().resolve(strict=True)
        protocol_bytes = protocol_path.read_bytes()
        save_bytes(output / "protocol.json", protocol_bytes)
        protocol = validate_protocol(json.loads(protocol_bytes))
        binary = Path(args.binary).expanduser().resolve(strict=True)
        qualification = Path(args.qualification).expanduser().resolve(strict=True)
        inspected, calibration = qualified_identity(qualification, args.model)
        manifest = inspected["manifest"]
        calibration_path = output / "calibration.json"
        save(calibration_path, calibration)
        sources = [source_receipt(path) for path in (
            Path(__file__), Path(prior.__file__), protocol_path, binary,
            APP / "activation-requirements.lock",
            *(qualification / name for name in ("result.json", "plan.json", "initialization.json", "calibration.json")))]
        configs = [{"pythonPath": sys.executable, "workerPath": str(APP / "activation_worker/__main__.py"),
                    "modelPath": inspected["modelPath"], "arm": arm, "seed": protocol["seed"],
                    "observations": protocol["observations"], "stepsBetween": protocol["stepsBetweenObservations"],
                    "journalEvery": protocol["journalEveryObservations"], "maxJournalTokens": protocol["outputTokens"],
                    "gain": 0.01} for arm in protocol["arms"]]
        config_path = output / "cohort-configs.json"
        save(config_path, configs)
        sources += [source_receipt(calibration_path), source_receipt(config_path), source_receipt(output / "protocol.json")]
        save(output / "frozen-plan.json", {
            "schema": "activation-cohort-pilot-freeze-v1", "protocol": protocol,
            "protocolPath": str(protocol_path), "protocolSha256": hashlib.sha256(protocol_bytes).hexdigest(),
            "runnerPath": str(Path(__file__).resolve()), "runnerSha256": sha256_file(Path(__file__)),
            "helperRunnerPath": str(Path(prior.__file__).resolve()), "helperRunnerSha256": sha256_file(Path(prior.__file__)),
            "frozenSources": sources, "calibrationSha256": calibration["sha256"],
            "calibrationFileSha256": sha256_file(calibration_path), "modelManifest": manifest,
            "python": sys.executable, "binary": str(binary), "binarySha256": sha256_file(binary),
            "lockSha256": sha256_file(APP / "activation-requirements.lock"),
            "qualificationResultSha256": sha256_file(qualification / "result.json"),
            "qualificationDirectory": str(qualification), "configsSha256": sha256_file(config_path),
            "readingAllocation": {f"Reading {chr(65+i)}": arm for i, arm in enumerate(protocol["arms"])},
            "deadlineOwner": "Rust cohort supervisor: one 900-second bound; each request uses at most 180 seconds and the remaining cohort budget",
            "outerWatchdogSeconds": OUTER_WATCHDOG_SECONDS,
            "outerTerminationPolicy": "Own new process group only: SIGTERM then at most 10 seconds, SIGKILL then at most 10 seconds; no work extension or retry",
        })
        prepared = prepare_resources(output, protocol["resourcePreparation"], sampler=resource_sampler,
                                     monotonic=monotonic, sleep=sleep, utc_clock=utc_clock)
        result["resourcePreparation"] = prepared
        if not prepared["ready"]:
            raise RuntimeError("Cohort held: bounded resource preparation did not become ready")
        check_sources(sources)
        # Preparation can take ten minutes: identity must still hold at dispatch.
        current, current_calibration = qualified_identity(qualification, args.model)
        if current != inspected or current_calibration != calibration:
            raise ValueError("Qualified identity changed during preparation")
        check_sources(sources)
        cohort_directory = output / "cohort"
        command = [str(binary), "--activation-cohort", str(config_path), "--output", str(cohort_directory),
                   "--activation-calibration", str(calibration_path)]
        receipt = {"schema": "activation-cohort-dispatch-v1", "command": command, "startedAtUtc": clock(),
                   "cohortDeadlineSeconds": 900, "requestDeadlineSeconds": 180, "automaticRetries": 0,
                   "outerWatchdogSeconds": OUTER_WATCHDOG_SECONDS}
        save(output / "dispatch.json", receipt)
        result["cohortDispatches"] = 1
        result["command"] = command
        try:
            with (output / "cohort-stdout.json").open("x", encoding="utf-8") as stdout, (output / "cohort-stderr.txt").open("x", encoding="utf-8") as stderr:
                completed = cohort_dispatch(command, stdout=stdout, stderr=stderr, check=False)
            result["returnCode"] = completed.returncode
            lifecycle = getattr(completed, "cohort_lifecycle", None)
            if lifecycle is not None:
                save(output / "process-lifecycle.json", lifecycle)
                result["processLifecycle"] = lifecycle
        finally:
            release = (release_observer or prior.observe_worker_release)(configs[0]["pythonPath"], configs[0]["workerPath"])
            save(output / "worker-release-observation.json", release)
            result["workerReleaseObservationFile"] = "worker-release-observation.json"
            save(output / "dispatch-finished.json", {"finishedAtUtc": clock(), "returnCode": result.get("returnCode"),
                                                     "workerReleaseObservationFile": "worker-release-observation.json"})
        # Rust writes this receipt before printing, so interrupted stdout need not
        # discard an independently replayable completed prefix.
        retained_reply_path = cohort_directory / "cohort-result.json"
        retained_reply = read(retained_reply_path) if retained_reply_path.exists() else None
        if retained_reply is not None:
            result["cohortResultFileSha256"] = sha256_file(retained_reply_path)
        try:
            reply = read(output / "cohort-stdout.json")
            result["cohortResultSource"] = "cohort-stdout.json"
        except (ValueError, OSError) as stdout_error:
            if retained_reply is None:
                raise
            reply = retained_reply
            result["cohortResultSource"] = "cohort/cohort-result.json"
            result["stdoutDiagnostic"] = f"{type(stdout_error).__name__}: {stdout_error}"
        if retained_reply is not None and reply != retained_reply:
            raise ValueError("Printed and retained cohort results differ")
        check_sources(sources)
        # Nonzero results can still contain a fully verified, completed prefix.
        collect_sessions(reply, configs, output, cohort_directory, calibration, manifest,
                         binary, protocol, dispatch, result)
        if (completed.returncode != 0 or reply["status"] != "completed"
                or reply.get("workerReleased") is not True
                or (lifecycle is not None and (lifecycle["terminationReason"] is not None or not lifecycle["reaped"]))
                or len(result["arms"]) != 3 or not all(x["verified"] for x in result["arms"])):
            raise RuntimeError("Cohort stopped on its first failure/refusal; no retry or continuation")
        result["status"] = "completed-awaiting-reading"
    except (Exception, KeyboardInterrupt) as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["verifiedCompletedSessions"] = sum(x["verified"] for x in result["arms"])
    result["scope"] = ("complete" if result["status"] == "completed-awaiting-reading" else
                       "partial" if result["verifiedCompletedSessions"] else "none")
    result["finishedAtUtc"] = clock()
    save(output / "result.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("binary", "model", "qualification", "output", "protocol"):
        parser.add_argument(f"--{name}", required=True)
    result = run(parser.parse_args())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "completed-awaiting-reading" else 1)
