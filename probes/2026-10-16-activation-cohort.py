#!/usr/bin/env python3
"""Read-only mechanical analysis of one retained single-worker activation cohort.

Uses NumPy only, in the qualified Python environment. Imports the earlier readonly
pilot probe to reuse its projection, ledger, token-boundary and exact-memory checks;
never imports MLX, activation_worker, a model, or a live-system service. Prose is
compared and hashed but never emitted. Optional output is exclusive and outside the
cohort evidence tree. A held prefix remains a partial comparison.
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import os
from pathlib import Path
import platform
import sys

import numpy as np

SOURCE = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("activation_pilot_analysis", SOURCE.with_name("2026-10-15-activation-pilot.py"))
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
require, load, sha_file = prior.require, prior.load, prior.sha_file
POLICY = {"schemaVersion": "activation-mlx-memory-policy/1", "freeCacheLimitBytes": 67108864,
          "clearEveryGeneratedContentTokens": 64, "scope": "owned-worker-MLX-allocator-only",
          "memoryLimitChanged": False, "wiredLimitChanged": False}
CHECKS = {"boundedCaptures", "cacheOffsetParity", "clearedSteering", "independentProbeIsolation",
          "logitParity", "noStaleSteering", "perPositionNorms", "quietZeroSamples", "samePassContentToken",
          "zeroAdditionBitwiseParity", "configuredFreeCacheLimit", "perOperationMemoryCleanup",
          "crossArmGenerationIsolation", "crossArmLogitTokenCaptureIsolation"}


def memory_summary(receipt, label, *, load_scope=False, allow_incomplete=False):
    policy = receipt["policy"]
    require(all(policy.get(key) == value and type(policy.get(key)) is type(value)
                for key, value in POLICY.items()), f"{label}: memory policy differs")
    rows = receipt["snapshots"]
    expected = (["before-model-load", "model-loaded", "load-cache-cleared"] if load_scope else
                ["operation-start", "prefill-complete", "operation-end", "cleanup-complete"])
    phases = [row["phase"] for row in rows]
    if allow_incomplete and not rows:
        require(receipt["operationReleased"] is True and receipt["peakResetBoundary"] is None,
                f"{label}: unexplained empty allocator receipt")
        return {"scope": policy["scope"], "peakResetBoundary": None, "snapshots": [],
                "cleanupFreeCacheBytes": None, "peakActiveBytes": None,
                "periodicCacheClears": 0, "operationStarted": False}
    require(phases == expected or (allow_incomplete and phases ==
            ["operation-start", "operation-end", "cleanup-complete"]), f"{label}: incomplete allocator phase evidence")
    for row in rows:
        require(all(type(row[key]) is int and row[key] >= 0 for key in
                    ("activeBytes", "freeCacheBytes", "peakActiveBytesSinceReset")), f"{label}: invalid allocator counter")
    require(rows[-1]["freeCacheBytes"] == 0, f"{label}: unused cache survived cleanup")
    if not load_scope:
        require(receipt["operationReleased"] is True, f"{label}: operation not released")
    return {"scope": policy["scope"], "peakResetBoundary": receipt["peakResetBoundary"],
            "snapshots": rows, "cleanupFreeCacheBytes": rows[-1]["freeCacheBytes"],
            "peakActiveBytes": max(row["peakActiveBytesSinceReset"] for row in rows),
            "periodicCacheClears": receipt.get("periodicCacheClears", 0), "operationStarted": True}


def qualification_identity(frozen, calibration):
    directory = Path(frozen["qualificationDirectory"])
    report, plan = load(directory / "result.json"), load(directory / "plan.json")
    require(sha_file(directory / "result.json") == frozen["qualificationResultSha256"], "Qualification result bytes differ")
    require(report["passed"] is True and report["status"] == "passed"
            and CHECKS.issubset(report["checks"]) and all(x is True for x in report["checks"].values()),
            "Qualification did not pass the required fourteen checks")
    require(prior.canonical_hash(plan) == report["planSha256"]
            and sha_file(directory / "plan.json") == report["planFileSha256"], "Qualification plan differs")
    require(plan["manifest"] == frozen["modelManifest"]
            and report["modelManifestSha256"] == calibration["modelManifestSha256"]
            and report["calibrationSha256"] == calibration["sha256"]
            and load(directory / "calibration.json") == calibration
            and sha_file(directory / "calibration.json") == report["calibrationFileSha256"],
            "Qualification model or calibration differs")
    return {"resultSha256": sha_file(directory / "result.json"), "checks": report["checks"],
            "memoryPolicy": report["memoryPolicy"], "status": "passed"}


def retained_reply(directory, outcome):
    path = directory / "cohort/cohort-result.json"
    if not path.exists():
        require(outcome["status"] == "held", "Completed attempt lacks a retained cohort result")
        return None, {"status": "no-retained-cohort-result", "source": None}
    reply = load(path)
    if outcome.get("cohortResultFileSha256"):
        require(sha_file(path) == outcome["cohortResultFileSha256"], "Retained cohort result hash differs")
    try:
        printed = load(directory / "cohort-stdout.json")
    except (ValueError, OSError) as exc:
        require(outcome.get("cohortResultSource") == "cohort/cohort-result.json"
                and isinstance(outcome.get("stdoutDiagnostic"), str),
                "Unreadable stdout lacks the runner's retained-result fallback receipt")
        return reply, {"status": "retained-result-after-unreadable-stdout", "source": outcome["cohortResultSource"],
                       "stdoutDiagnostic": outcome["stdoutDiagnostic"], "analysisDiagnostic": f"{type(exc).__name__}: {exc}"}
    require(printed == reply, "Valid CLI output differs from retained cohort result")
    return reply, {"status": "printed-and-retained-results-match", "source": outcome.get("cohortResultSource", "cohort-stdout.json")}


def compare_arms(order, private):
    comparisons = []
    for left_arm, right_arm in itertools.combinations(order, 2):
        left, right = (next((item for item in private if item["arm"] == arm),
                           {"journals": [], "attempts": []}) for arm in (left_arm, right_arm))
        pairs = [{"journalNumber": index,
                  "textIdentical": a["text"] == b["text"],
                  "tokensIdentical": a["generatedTokenIds"] == b["generatedTokenIds"],
                  "activationIdentical": a["response"]["activation"] == b["response"]["activation"],
                  "firstDifferingContentTokenIndex": prior.first_difference(a["generatedTokenIds"], b["generatedTokenIds"]),
                  "firstDifferingTextCharacterIndex": prior.first_difference(a["text"], b["text"])}
                 for index, (a, b) in enumerate(zip(left["journals"], right["journals"]), 1)]
        a = left["attempts"][0] if left["attempts"] else {}
        b = right["attempts"][0] if right["attempts"] else {}
        comparisons.append({"arms": [left_arm, right_arm], "pairedCompleteJournals": len(pairs),
            "firstJournalPromptIdentical": a["promptSha256"] == b["promptSha256"] if a and b else None,
            "firstJournalPromptTokensIdentical": (a["promptTokenIdsSha256"] == b["promptTokenIdsSha256"]
                if a.get("promptTokenIdsSha256") and b.get("promptTokenIdsSha256") else None),
            "status": "assessed" if pairs else "unassessed", "journals": pairs})
    return comparisons


def inspect_session_wire(session, manifest, record, initialization, policy):
    memory, sequences, bounded_positions = [], [], 0
    accepted = {event["request_id"] for event in record["events"] if event["kind"] in ("quietReceived", "journalReceived")}
    requests = [event["request"] for event in record["events"] if event["kind"] == "requestStarted"]
    wire_paths = sorted(session.glob("cohort-protocol-*-request.json"),
                        key=lambda path: int(path.name.split("-")[2]))
    require(len(wire_paths) <= len(requests) <= len(wire_paths) + 1, "Wire/core request counts differ")
    for path, core in zip(wire_paths, requests):
        sequence = int(path.name.split("-")[2])
        sequences.append(sequence)
        request = load(path)
        expected = {**load(session / f'{core["id"]}-request.json'), "id": f"worker-{sequence}", "command": core["kind"]}
        require(request == expected, "Actual worker request differs from session request")
        response_path = path.with_name(path.name.replace("-request.json", "-response.json"))
        if not response_path.exists():
            require(core["id"] not in accepted, "Accepted result lacks wire response")
            continue
        response = load(response_path)
        require(response["id"] == request["id"] and response["command"] == request["command"], "Wire association differs")
        if response["type"] != "result":
            continue
        require(response["workerIdentity"] == initialization["workerIdentity"]
                and response["protocolVersion"] == initialization["protocolVersion"], "Shared worker identity differs")
        payload = response["result"]
        if core["id"] in accepted:
            require(payload == load(session / f'{core["id"]}-response.json'), "Accepted/wire result differs")
        receipt = payload["receipt"]
        require(receipt["memory"]["policy"] == policy, "Operation cache policy changed")
        measured = memory_summary(receipt["memory"], f'{session.name}/{sequence}',
                                  allow_incomplete=core["id"] not in accepted)
        measured.update({"sequence": sequence, "command": request["command"], "acceptedForFeedback": core["id"] in accepted})
        generated_processed = max(0, receipt["processedTokenCount"] - len(payload["promptTokenIds"]))
        require(measured["periodicCacheClears"] == generated_processed // 64, "Periodic cache clear count differs")
        memory.append(measured)
        norm_payload = payload
        if core["id"] not in accepted:
            # Failed processing can retain a sampled token whose forward failed.
            # Check only the explicitly measured processed-token prefix.
            count = len(payload["norms"]["perPosition"])
            require(count == receipt["processedTokenCount"], "Failed result norm/processed count differs")
            norm_payload = {**payload, "promptTokenIds": payload["promptTokenIds"][:count],
                            "generatedTokenIds": payload.get("generatedTokenIds", [])[:max(0, count-len(payload["promptTokenIds"]))]}
        norms = prior.norm_summary(norm_payload, f'{session.name}/{sequence}')
        dtype = norms["dtype"].removeprefix("mlx.core.")
        if norms["actual"]:
            require(dtype in {"bfloat16", "float16", "float32"}, "Unqualified residual dtype")
            u = {"bfloat16": 2**-8, "float16": 2**-11, "float32": 2**-24}[dtype]
            allowance = u * .01 + u * (1 + .01 + u * .01)
            require(all(abs(actual - requested) <= allowance for actual, requested in
                        zip(norms["actual"], norms["requested"])), "Actual residual delta exceeds qualified dtype bound")
        bounded_positions += len(norms["actual"])
    member = manifest["cohort"]
    if sequences:
        require(sequences == list(range(member["firstOperationSequence"], member["firstOperationSequence"] + len(sequences))),
                "Global worker sequence is discontinuous inside arm")
    if member.get("operationBoundarySha256"):
        boundary_path = session / "cohort-operation-boundary.json"
        require(sha_file(boundary_path) == member["operationBoundarySha256"], "Operation boundary hash differs")
        boundary = load(boundary_path)
        require(boundary["recordSha256"] == manifest["recordSha256"]
                and boundary["firstSequence"] == member["firstOperationSequence"]
                and boundary["lastSequence"] == member["firstOperationSequence"] - 1 + len(sequences),
                "Operation boundary differs from final record/sequences")
    return {"operations": memory, "sequences": sequences, "dtypeBoundedPositions": bounded_positions}


def analyze(directory: Path, previous_calibration: Path | None = None):
    frozen, outcome = load(directory / "frozen-plan.json"), load(directory / "result.json")
    require(frozen["schema"] == "activation-cohort-pilot-freeze-v1", "Unsupported cohort freeze")
    protocol, configs, calibration = frozen["protocol"], load(directory / "cohort-configs.json"), load(directory / "calibration.json")
    require(load(directory / "protocol.json") == protocol and sha_file(directory / "protocol.json") == frozen["protocolSha256"], "Frozen protocol differs")
    require(sha_file(directory / "cohort-configs.json") == frozen["configsSha256"]
            and [config["arm"] for config in configs] == protocol["arms"], "Frozen cohort configurations differ")
    require(sha_file(directory / "calibration.json") == frozen["calibrationFileSha256"]
            and calibration["sha256"] == frozen["calibrationSha256"]
            and calibration["modelManifestSha256"] == frozen["modelManifest"]["sha256"], "Frozen calibration identity differs")
    require(prior.canonical_hash({key: value for key, value in frozen["modelManifest"].items() if key != "sha256"})
            == frozen["modelManifest"]["sha256"], "Model manifest semantic identity differs")
    qualification = qualification_identity(frozen, calibration)
    checker = prior.ProjectionCheck(calibration)
    root = directory / "cohort"
    reply, result_binding = retained_reply(directory, outcome)
    arms, private, all_memory, all_sequences = [], [], [], []
    initialization = initialization_receipt = load_memory = None
    initialization_evidence = {"status": "not-started", "actualResponseFiles": 0}
    borrowed_copies = positions = 0
    if reply is not None:
        require(reply["modelsLoaded"] in (0, 1) and reply["workerStarts"] in (0, 1)
                and reply["workerReleased"] is True, "Cohort did not retain bounded ownership/release")
        cohort_plan = load(root / "cohort-plan.json")
        require(cohort_plan["configs"] == configs, "Rust cohort configs differ from freeze")
        if (root / "shared-worker-1-response.json").exists():
            initialization_evidence.update({"actualResponseFiles": 1,
                "responseFileSha256": sha_file(root / "shared-worker-1-response.json")})
        if reply["modelsLoaded"] and not (root / "shared-initialization.json").exists():
            require(reply["status"] == "failed" and outcome["status"] == "held",
                    "Incomplete shared initialization was reported as completed")
            initialization_evidence["status"] = "incomplete-boundary-unassessed"
        elif reply["modelsLoaded"]:
            initialization_receipt = load(root / "shared-initialization.json")
            require(initialization_receipt["requestSha256"] == sha_file(root / "shared-worker-1-request.json")
                    and initialization_receipt["responseSha256"] == sha_file(root / "shared-worker-1-response.json"), "Shared initialization file binding differs")
            init_request = load(root / "shared-worker-1-request.json")
            initialization = load(root / "shared-worker-1-response.json")
            require(init_request["command"] == initialization["command"] == "initialize"
                    and init_request["id"] == initialization["id"] == "worker-1"
                    and initialization["type"] == "result"
                    and initialization["workerIdentity"]["modelManifestSha256"] == calibration["modelManifestSha256"]
                    and init_request["existingCalibration"] == initialization["result"]["calibration"] == calibration
                    and initialization["result"]["manifest"] == frozen["modelManifest"], "Shared initialization identity differs")
            require(len(list(root.glob("shared-worker-*-request.json"))) == 1, "More than one shared initialization request")
            load_memory = memory_summary(initialization["result"]["memory"]["modelLoad"], "shared-load", load_scope=True)
            initialization_evidence["status"] = "verified-shared-initialization"
        elif reply["workerStarts"]:
            initialization_evidence["status"] = "initialization-unsuccessful"
    for index, (arm, config) in enumerate(zip(protocol["arms"], configs)):
        retained = next((item for item in outcome.get("arms", []) if item["arm"] == arm), None)
        if retained is None:
            arms.append({"arm": arm, "status": "not_started_after_stop", "quietCaptures": 0, "completeJournals": 0})
            continue
        session = Path(retained["directory"]).resolve(strict=True)
        require(session.is_relative_to(root.resolve()), "Session escapes cohort evidence tree")
        manifest = load(session / "latest.json")
        record = load(session / manifest["recordFile"])
        require(sha_file(session / manifest["recordFile"]) == manifest["recordSha256"]
                and sha_file(session / f'manifest-{manifest["revision"]:06d}.json') == sha_file(session / "latest.json")
                and manifest["config"] == config, "Session record, immutable manifest or config differs")
        require(manifest["format"] == "activation-cohort-session-v1" and manifest["cohort"]["index"] == index,
                "Session format or cohort allocation differs")
        require(sha_file(session / "cohort-plan.json") == sha_file(root / "cohort-plan.json") == manifest["cohort"]["planSha256"], "Borrowed cohort plan differs")
        if initialization is None:
            require(not any(event["kind"] == "requestStarted" for event in record["events"]), "Operation occurred without initialization")
            arms.append({"arm": arm, "status": manifest["status"], "quietCaptures": 0, "completeJournals": 0,
                         "reason": "Shared initialization proof is absent or incomplete; no operation outcome assessed"})
            continue
        require(load(session / "shared-initialize-response.json") == initialization
                and sha_file(session / "shared-initialize-request.json") == initialization_receipt["requestSha256"]
                and sha_file(session / "shared-initialization.json") == sha_file(root / "shared-initialization.json")
                == manifest["cohort"]["initializationSha256"], "Borrowed initialization differs")
        borrowed_copies += 1
        summary, retained_private = prior.arm_analysis(directory, index, arm, outcome, calibration, checker,
            session_override=session, frozen_config=config, wire_prefix="cohort-protocol-",
            ignored_response_files=("shared-initialize-response.json",))
        require(summary["protocolResponses"]["initializations"] == 0, "Borrowed initialization counted as execution")
        wire = inspect_session_wire(session, manifest, record, initialization, qualification["memoryPolicy"])
        all_memory.extend(wire["operations"])
        all_sequences.extend(wire["sequences"])
        positions += wire["dtypeBoundedPositions"]
        summary["allocator"] = {"operations": len(wire["operations"]),
                                "peakActiveBytes": prior.numeric_range([item["peakActiveBytes"] for item in wire["operations"] if item["operationStarted"]]),
                                "allStartedCleanupFreeCacheBytesZero": all(item["cleanupFreeCacheBytes"] == 0 for item in wire["operations"] if item["operationStarted"])}
        if summary["status"] == "completed":
            verification = load(directory / retained["verificationFile"])
            verified = json.loads(verification["stdout"])
            require(retained["verified"] is True and verification["returnCode"] == 0
                    and verified["status"] == "passed" and verified["modelsContacted"] is False
                    and verified["sessionId"] == manifest["sessionId"]
                    and verified["steps"] == summary["finalStep"] == 121
                    and verified["journals"] == summary["completeJournals"] == 6,
                    "Retained offline Rust replay did not verify final numerical state")
            summary["offlineNumericalReplay"] = {"status": "passed", "evidenceSha256": sha_file(directory / retained["verificationFile"])}
        arms.append(summary)
        private.append(retained_private)
    require(all_sequences == list(range(2, 2 + len(all_sequences))), "Global worker operations are duplicated or discontinuous")
    previous = None
    if previous_calibration:
        old = load(previous_calibration)
        fields = sorted(set(old) | set(calibration))
        changed = [key for key in fields if old.get(key) != calibration.get(key)]
        numerical_fields = [key for key in fields if key not in {"sha256", "modelManifestSha256"}]
        previous = {"previousFileSha256": sha_file(previous_calibration), "changedFields": changed,
                    "allFieldsExceptModelIdentityAndOuterHashEqual": all(old.get(key) == calibration.get(key) for key in numerical_fields)}
    artifacts = [{"path": item["path"], "expectedSha256": item["sha256"],
                  "actualSha256": sha_file(Path(item["path"])) if Path(item["path"]).is_file() else None}
                 for item in frozen["frozenSources"]]
    for item in frozen["modelManifest"]["workerSources"]:
        path = prior.APP / "activation_worker" / item["path"]
        artifacts.append({"path": str(path), "expectedSha256": item["sha256"],
                          "actualSha256": sha_file(path) if path.is_file() else None})
    for item in artifacts:
        item["matches"] = item["expectedSha256"] == item["actualSha256"]
    return {"schema": "activation-cohort-mechanical-summary/1", "sourceCohort": directory.name,
            "cohortStatus": outcome["status"], "scope": "complete-comparison" if all(arm["status"] == "completed" for arm in arms) else "partial-comparison",
            "evidenceConsistency": "passed", "modelCalls": 0, "evidenceFilesModified": False,
            "analysisSourceSha256": sha_file(SOURCE), "ledgerHelperSourceSha256": sha_file(Path(prior.__file__)),
            "pythonVersion": platform.python_version(), "numpyVersion": np.__version__,
            "frozenPlanSha256": sha_file(directory / "frozen-plan.json"), "resultSha256": sha_file(directory / "result.json"),
            "modelManifestSha256": calibration["modelManifestSha256"], "calibrationSha256": calibration["sha256"],
            "qualification": qualification, "previousCalibration": previous, "currentFrozenSources": artifacts,
            "modelsLoaded": reply["modelsLoaded"] if reply else 0,
            "workerStarts": reply["workerStarts"] if reply else 0,
            "resultBinding": result_binding, "initializationEvidence": initialization_evidence,
            "actualInitializationResponses": initialization_evidence["actualResponseFiles"],
            "verifiedSharedInitializations": int(initialization is not None), "borrowedInitializationCopies": borrowed_copies,
            "globalOperationCount": len(all_sequences), "arms": arms,
            "betweenArmComparisons": compare_arms(protocol["arms"], private),
            "independentProjection": {"method": "Float64 column products with math.fsum; tanh((Q^T h - mean)/scale)",
                "absoluteTolerance": prior.PROJECTION_ATOL, "activationCaptures": len(checker.errors),
                "coordinates": 32 * len(checker.errors), "maxAbsoluteCoordinateError": max(checker.errors, default=None)},
            "allocator": {"scope": "Owned MLX allocator counters, not process or host RAM",
                          "sharedModelLoad": load_memory, "operationCount": len(all_memory), "operations": all_memory,
                          "peakActiveBytes": prior.numeric_range([item["peakActiveBytes"] for item in all_memory if item["operationStarted"]]),
                          "allStartedCleanupFreeCacheBytesZero": all(item["cleanupFreeCacheBytes"] == 0 for item in all_memory if item["operationStarted"])},
            "dtypeBoundedResidualPositions": positions,
            "limitations": ["One shared model initialization is copied as provenance into each fresh session; copies are not additional loads.",
                "Scalar norm receipts do not preserve full residual matrices; projections are independently recomputed from retained activations.",
                "The retained Rust verification owns full recurrent-state replay; this probe checks its identity and reconstructs save/application order.",
                "First-journal prompts are matched before prose history diverges; later journals combine residual intervention and their differing prior prose.",
                "No prose interpretation, semantic quality or benefit claim follows from token differences or exact repetition.",
                "Free-cache policy reclaims excess on allocation; peak active MLX allocation is not a process or host memory cap."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cohortdir", type=Path)
    parser.add_argument("--previous-calibration", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    directory = args.cohortdir.expanduser().resolve(strict=True)
    summary = analyze(directory, args.previous_calibration.expanduser().resolve(strict=True) if args.previous_calibration else None)
    payload = json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        output = args.output.expanduser().resolve()
        require(not output.is_relative_to(directory), "Summary output must be outside immutable cohort evidence")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        print(json.dumps({"output": str(output), "sha256": prior.sha_bytes(payload.encode()), "scope": summary["scope"],
                          "evidenceConsistency": summary["evidenceConsistency"], "modelCalls": 0}))
    else:
        sys.stdout.write(payload)


if __name__ == "__main__":
    main()
